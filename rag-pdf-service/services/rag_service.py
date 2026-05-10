import os
import asyncio
from typing import Optional, Any
from langsmith import traceable
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from vectorstore.pinecone_store import get_vectorstore
from prompts.rag_prompt import RAG_PROMPT
from dotenv import load_dotenv
from services.eval_service import evaluate_response
from services.history_service import get_history_service


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


def retrieve_from_all_documents(vectorstore, question: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> list:
    """
    Retrieve relevant chunks from EACH document separately to ensure representation.
    Guarantees at least some chunks from every document.
    
    Args:
        vectorstore: Pinecone vectorstore instance
        question: The user's question
        user_id: User ID for filtering
        session_id: Session ID for filtering
        
    Returns:
        List of all retrieved documents combined from all sources
    """
    try:
        # Use Pinecone's similarity search with user/session filtering
        results = vectorstore.similarity_search(
            query=question,
            k=15,  # Get more results for better coverage
            user_id=user_id,
            session_id=session_id
        )
        return results
    except Exception as e:
        print(f"Error in retrieve_from_all_documents: {e}")
        return []


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
    model_params: Optional[ModelParams] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None
) -> dict:
    """
    Retrieve relevant chunks from FAISS and send to LLM with prompt.
    Uses per-document retrieval for "all documents" queries to ensure all documents are included.
    Uses MMR (Maximal Marginal Relevance) for single-topic queries.
    Includes conversation history for context-aware responses.
    
    Args:
        question: The question to ask
        evaluate: Whether to evaluate the response (default: True)
        model_name: Model identifier in format "provider:model_name"
                   Examples: "groq:llama-3.1-8b-instant", "openai:gpt-4o-mini",
                   "huggingface:meta-llama/Llama-3.1-8B-Instruct", "ollama:llama3"
        model_params: Optional ModelParams for tuning generation
        user_id: User ID for conversation history (optional)
        session_id: Session ID for conversation history (optional)
    
    Returns:
        Dictionary with question, answer, sources, and evaluation
    """
    history_context = ""
    if user_id:
        try:
            history_service = get_history_service()
            history_context = history_service.get_conversation_context(
                user_id=user_id,
                session_id=session_id,
                max_history=5
            )
        except Exception as e:
            print(f"Warning: Could not retrieve conversation history: {e}")
    
    # Combine document context with history context
    full_context = document_context
    if history_context:
        full_context = f"{history_context}\n\nDocument context:\n{document_context}"
    
    # Get LLM and create chain
    llm = get_llm(model_name, model_params)
    
    chain = (
        RAG_PROMPT
        | llm
        | StrOutputParser()
    )

    answer = chain.invoke({"context": full_context, "question": question})
    
    # Fetch sources for response
    sources = list({doc.metadata.get("source", "unknown") for doc in docs})

    result = {
        "question": question,
        "answer":   answer,
        "sources":  sources,
        "evaluation": None,
    }
    
    # Save conversation to history if user_id is provided
    if user_id:
        try:
            history_service = get_history_service()
            history_service.add_conversation(
                user_id=user_id,
                question=question,
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            print(f"Warning: Could not save conversation to history: {e}")

    # ── Step 2: Evaluator LLM (judge) ────────────────────────────
    if evaluate:
        eval_result = evaluate_response(
            question=question,
            reference=document_context,   # retrieved chunks as ground truth
            answer=answer,
            history_context=history_context,  # pass conversation history to evaluator
        )
        result["evaluation"] = {
            "verdict":    eval_result["verdict"],
            "is_correct": eval_result["is_correct"],
        }

    return result    


async def get_rag_answer_stream(
    question: str,
    evaluate: bool = True,
    model_name: Optional[str] = None,
    model_params: Optional[ModelParams] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None
):
    """
    Async generator that streams RAG answer chunks in real-time.
    Yields JSON-serializable dictionaries with streaming data.
    
    Yields:
        dict: Event data with type and content
              - {"type": "start"} - Stream started
              - {"type": "chunk", "content": "..."} - Answer chunk
              - {"type": "sources", "sources": [...]} - Source documents
              - {"type": "evaluation", "evaluation": {...}} - Evaluation result
              - {"type": "end"} - Stream ended
              - {"type": "error", "error": "..."} - Error occurred
    """
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            raise ValueError("Vector store is empty. Please ingest PDFs first.")

        # Signal stream start
        yield {"type": "start", "message": "Starting RAG query..."}

        # Detect if user is asking for all documents
        is_all_docs = is_all_documents_query(question)
        
        # Retrieve documents based on query type
        if is_all_docs:
            docs = retrieve_from_all_documents(vectorstore, question)
        else:
            docs = vectorstore.similarity_search(
                query=question,
                k=8
            )

        # Yield sources
        sources = list({doc.metadata.get("source", "unknown") for doc in docs})
        yield {"type": "sources", "sources": sources}

        # Format context from retrieved documents
        document_context = format_docs(docs)
        
        # Get conversation history if user_id is provided
        history_context = ""
        if user_id:
            try:
                history_service = get_history_service()
                history_context = history_service.get_conversation_context(
                    user_id=user_id,
                    session_id=session_id,
                    max_history=5
                )
            except Exception as e:
                print(f"Warning: Could not retrieve conversation history: {e}")
        
        # Combine document context with history context
        full_context = document_context
        if history_context:
            full_context = f"{history_context}\n\nDocument context:\n{document_context}"
        
        # Get LLM and create chain
        llm = get_llm(model_name, model_params)
        
        # Create a streaming chain
        chain = (
            RAG_PROMPT
            | llm
            | StrOutputParser()
        )

        # Stream the response
        yield {"type": "message", "message": "Generating response..."}
        
        # Use asyncio to run the chain in a thread pool to avoid blocking
        answer_chunks = []
        
        # LangChain supports streaming via .stream()
        for chunk in chain.stream({"context": full_context, "question": question}):
            yield {"type": "chunk", "content": chunk}
            answer_chunks.append(chunk)

        # Combine all chunks to get the full answer for evaluation
        full_answer = "".join(answer_chunks)
        
        # Save conversation to history if user_id is provided
        if user_id:
            try:
                history_service = get_history_service()
                history_service.add_conversation(
                    user_id=user_id,
                    question=question,
                    answer=full_answer,
                    sources=sources,
                    session_id=session_id
                )
            except Exception as e:
                print(f"Warning: Could not save conversation to history: {e}")

        # Evaluate if requested
        if evaluate:
            yield {"type": "message", "message": "Evaluating response..."}
            eval_result = evaluate_response(
                question=question,
                reference=document_context,
                answer=full_answer,
                history_context=history_context,  # pass conversation history to evaluator
            )
            yield {
                "type": "evaluation",
                "evaluation": {
                    "verdict": eval_result["verdict"],
                    "is_correct": eval_result["is_correct"],
                }
            }

        # Signal completion
        yield {"type": "end", "message": "Stream complete"}

    except ValueError as e:
        yield {"type": "error", "error": str(e)}
    except Exception as e:
        yield {"type": "error", "error": f"LLM error: {str(e)}"}