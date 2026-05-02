import os
from typing import Optional, Any
from langsmith import traceable
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from vectorstore.faiss_store import get_vectorstore
from prompts.rag_prompt import RAG_PROMPT
from dotenv import load_dotenv
from services.eval_service import evaluate_response


load_dotenv()


def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def is_all_documents_query(question: str) -> bool:
    """
    Detect if the question is asking for information from all documents.
    
    Args:
        question: The user's question
        
    Returns:
        True if query appears to be asking for all documents, False otherwise
    """
    keywords = [
        "all documents", "all pdfs", "all files",
        "summarize all", "summary of all",
        "each document", "every document", "every pdf",
        "across all", "all of them"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in keywords)


def get_unique_documents(vectorstore) -> set:
    """
    Extract unique document sources from the vectorstore.
    
    Args:
        vectorstore: FAISS vectorstore instance
        
    Returns:
        Set of unique source document names
    """
    unique_sources = set()
    try:
        # Access docstore to get all documents
        if hasattr(vectorstore, 'docstore'):
            for doc_id in vectorstore.index_to_docstore_id.values():
                doc = vectorstore.docstore.search(doc_id)
                if doc and hasattr(doc, 'metadata'):
                    source = doc.metadata.get("source", "unknown")
                    unique_sources.add(source)
    except Exception as e:
        print(f"Warning: Could not extract unique documents: {e}")
    
    return unique_sources


def retrieve_from_all_documents(vectorstore, question: str) -> list:
    """
    Retrieve relevant chunks from EACH document separately to ensure representation.
    Guarantees at least some chunks from every document.
    
    Args:
        vectorstore: FAISS vectorstore instance
        question: The user's question
        
    Returns:
        List of all retrieved documents combined from all sources
    """
    all_docs = []
    unique_sources = get_unique_documents(vectorstore)
    
    if not unique_sources:
        # Fallback: use standard MMR retrieval if we can't detect sources
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 15, "fetch_k": 30, "lambda_mult": 0.5}
        )
        return retriever.invoke(question)
    
    # Retrieve from each document separately
    chunks_per_doc = 3  # Get 3 chunks from each document
    
    for source in unique_sources:
        try:
            # Create retriever for this specific document
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": chunks_per_doc,
                    "fetch_k": chunks_per_doc * 2,
                    "lambda_mult": 0.6,
                    "filter": {"source": source}  # Filter by source if supported
                }
            )
            docs = retriever.invoke(question)
            all_docs.extend(docs)
        except Exception:
            # If filtering doesn't work, fall back to retrieving and manually filtering
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": chunks_per_doc * len(unique_sources),
                    "fetch_k": chunks_per_doc * len(unique_sources) * 2,
                    "lambda_mult": 0.6
                }
            )
            docs = retriever.invoke(question)
            # Manually filter by source
            for doc in docs:
                if doc.metadata.get("source") == source and len([d for d in all_docs if d.metadata.get("source") == source]) < chunks_per_doc:
                    all_docs.append(doc)
            if len(all_docs) >= chunks_per_doc * len(unique_sources):
                break
    
    # If we didn't get enough docs, do a general retrieval
    if not all_docs:
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 15, "fetch_k": 30, "lambda_mult": 0.5}
        )
        all_docs = retriever.invoke(question)
    
    return all_docs


# ── Model Registry ───────────────────────────────────────────────
# Format: "provider:model_name"
SUPPORTED_MODELS = {
    # Groq models
    "groq:llama-3.1-8b-instant": {"provider": "groq", "default": True},
    "groq:llama-3.1-70b-versatile": {"provider": "groq"},
    "groq:mixtral-8x7b-32768": {"provider": "groq"},
    # OpenAI models
    "openai:gpt-4o-mini": {"provider": "openai"},
    "openai:gpt-4o": {"provider": "openai"},
    "openai:gpt-4-turbo": {"provider": "openai"},
    # Hugging Face models
    "huggingface:meta-llama/Llama-3.1-8B-Instruct": {"provider": "huggingface"},
    "huggingface:meta-llama/Llama-3.2-1B-Instruct": {"provider": "huggingface"},
    "huggingface:mistralai/Mistral-7B-Instruct-v0.2": {"provider": "huggingface"},
    # Ollama models
    "ollama:llama3": {"provider": "ollama"},
    "ollama:mistral": {"provider": "ollama"},
    "ollama:phi3": {"provider": "ollama"},
}


# ── Model Parameters Schema ───────────────────────────────────────
class ModelParams:
    """
    Container for LLM model parameters.
    
    Attributes:
        temperature: Controls randomness (0.0 - 2.0). Higher = more random.
        top_p: Nucleus sampling threshold (0.0 - 1.0). Higher = more diverse.
        top_k: Number of top tokens to consider. -1 = all tokens.
        max_tokens: Maximum tokens to generate. None = model default.
        frequency_penalty: Penalize repeated tokens (-2.0 - 2.0).
        presence_penalty: Penalize repeated topics (-2.0 - 2.0).
        stop: Stop sequences to end generation.
        seed: Random seed for reproducibility.
        timeout: Request timeout in seconds.
    """
    def __init__(
        self,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        max_tokens: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[list[str]] = None,
        seed: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_tokens = max_tokens
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop = stop
        self.seed = seed
        self.timeout = timeout

    def to_dict(self) -> dict[str, Any]:
        """Convert params to dictionary, excluding None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


def get_llm(
    model_name: Optional[str] = None,
    model_params: Optional[ModelParams] = None
):
    """
    Factory function to create an LLM instance based on the model name.
    
    Args:
        model_name: Model identifier in format "provider:model_name" 
                    (e.g., "groq:llama-3.1-8b-instant")
                    If None, uses default model from config.
        model_params: Optional ModelParams instance for tuning generation.
    
    Returns:
        LangChain LLM instance
    
    Raises:
        ValueError: If model is not supported or API key is missing
    """
    # Use default model if not specified
    if not model_name:
        model_name = next(
            (k for k, v in SUPPORTED_MODELS.items() if v.get("default")),
            "groq:llama-3.1-8b-instant"
        )
    
    model_name = model_name.lower()
    
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(
            f"Model '{model_name}' not supported. "
            f"Available models: {list(SUPPORTED_MODELS.keys())}"
        )
    
    config = SUPPORTED_MODELS[model_name]
    provider = config["provider"]
    params = model_params.to_dict() if model_params else {}
    
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        # Map common params to Groq-compatible names
        groq_params = {
            "model": model_name.replace("groq:", ""),
            "api_key": api_key,
        }
        if params.get("temperature") is not None:
            groq_params["temperature"] = params["temperature"]
        if params.get("max_tokens") is not None:
            groq_params["max_tokens"] = params["max_tokens"]
        if params.get("top_p") is not None:
            groq_params["top_p"] = params["top_p"]
        if params.get("stop") is not None:
            groq_params["stop"] = params["stop"]
        if params.get("seed") is not None:
            groq_params["seed"] = params["seed"]
        
        return ChatGroq(**groq_params)
    
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        openai_params = {
            "model": model_name.replace("openai:", ""),
            "api_key": api_key,
        }
        # OpenAI supports: temperature, top_p, max_tokens, frequency_penalty, presence_penalty, stop
        for key in ["temperature", "top_p", "max_tokens", "frequency_penalty", "presence_penalty", "stop"]:
            if params.get(key) is not None:
                openai_params[key] = params[key]
        
        return ChatOpenAI(**openai_params)
    
    elif provider == "huggingface":
        hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if not hf_token:
            raise ValueError("HUGGINGFACE_HUB_TOKEN not found in environment")
        
        hf_params = {
            "endpoint_url": f"https://api-inference.huggingface.co/models/{model_name.replace('huggingface:', '')}",
            "huggingfacehub_api_key": hf_token,
            "task": "text-generation",
        }
        # HuggingFace supports: temperature, top_k, top_p, max_new_tokens, do_sample
        if params.get("temperature") is not None:
            hf_params["temperature"] = params["temperature"]
        if params.get("top_k") is not None:
            hf_params["top_k"] = params["top_k"]
        if params.get("top_p") is not None:
            hf_params["top_p"] = params["top_p"]
        if params.get("max_tokens") is not None:
            hf_params["max_new_tokens"] = params["max_tokens"]
        
        return HuggingFaceEndpoint(**hf_params)
    
    elif provider == "ollama":
        ollama_params = {
            "model": model_name.replace("ollama:", ""),
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        }
        # Ollama supports: temperature, top_p, top_k, max_tokens, stop
        for key in ["temperature", "top_p", "top_k", "max_tokens", "stop"]:
            if params.get(key) is not None:
                ollama_params[key] = params[key]
        
        return ChatOllama(**ollama_params)
    
    raise ValueError(f"Unknown provider: {provider}")


@traceable(run_type="chain")
def get_rag_answer(
    question: str,
    evaluate: bool = True,
    model_name: Optional[str] = None,
    model_params: Optional[ModelParams] = None
) -> dict:
    """
    Retrieve relevant chunks from FAISS and send to LLM with prompt.
    Uses per-document retrieval for "all documents" queries to ensure all documents are included.
    Uses MMR (Maximal Marginal Relevance) for single-topic queries.
    
    Args:
        question: The question to ask
        evaluate: Whether to evaluate the response (default: True)
        model_name: Model identifier in format "provider:model_name"
                   Examples: "groq:llama-3.1-8b-instant", "openai:gpt-4o-mini",
                   "huggingface:meta-llama/Llama-3.1-8B-Instruct", "ollama:llama3"
        model_params: Optional ModelParams for tuning generation
    
    Returns:
        Dictionary with question, answer, sources, and evaluation
    """
    vectorstore = get_vectorstore()
    if not vectorstore:
        raise ValueError("Vector store is empty. Please ingest PDFs first.")

    # Detect if user is asking for all documents
    is_all_docs = is_all_documents_query(question)
    
    # Retrieve documents based on query type
    if is_all_docs:
        # All documents query: ensure chunks from EACH document
        docs = retrieve_from_all_documents(vectorstore, question)
    else:
        # Single query: use standard MMR retrieval
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 8,         # Return 8 chunks
                "fetch_k": 16,  # Consider 16 candidates
                "lambda_mult": 0.7  # 70% relevance, 30% diversity
            }
        )
        docs = retriever.invoke(question)

    # Format context from retrieved documents
    context = format_docs(docs)
    
    # Get LLM and create chain
    llm = get_llm(model_name, model_params)
    
    chain = (
        RAG_PROMPT
        | llm
        | StrOutputParser()
    )

    answer = chain.invoke({"context": context, "question": question})
    
    # Fetch sources for response
    sources = list({doc.metadata.get("source", "unknown") for doc in docs})

    result = {
        "question": question,
        "answer":   answer,
        "sources":  sources,
        "evaluation": None,
    }

    # ── Step 2: Evaluator LLM (judge) ────────────────────────────
    if evaluate:
        eval_result = evaluate_response(
            question=question,
            reference=context,   # retrieved chunks as ground truth
            answer=answer,
        )
        result["evaluation"] = {
            "verdict":    eval_result["verdict"],
            "is_correct": eval_result["is_correct"],
        }

    return result    