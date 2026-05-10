import os
from typing import List, Optional, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_community.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings, OllamaEmbeddings
from langchain_community.vectorstores import Pinecone as PineconeLangchain
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

def get_embedding_dimension(embeddings_obj) -> int:
    """Get actual embedding dimension from embeddings object."""
    try:
        # Try to get dimension by embedding a test query
        test_embedding = embeddings_obj.embed_query("test")
        return len(test_embedding)
    except Exception as e:
        print(f"⚠️ Could not determine embedding dimension: {e}")
        # Fallback to environment variable or default
        env_dimension = os.getenv("EMBEDDING_DIMENSION")
        if env_dimension:
            try:
                return int(env_dimension)
            except ValueError:
                pass
        return 384  # Safe fallback

class EmbeddingProvider:
    """Static embedding provider configured via .env file."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.provider = self._detect_provider(model_name)
        self.is_free = self._is_free_model(model_name)
        
        # Debug output
        print(f"🔍 Embedding Provider Debug:")
        print(f"  Model: {model_name}")
        print(f"  Detected Provider: {self.provider}")
        print(f"  Is Free: {self.is_free}")
        
        # Create embeddings
        self.embeddings = self.create_embeddings()
        
        # Get actual dimension from embeddings object
        self.dimension = get_embedding_dimension(self.embeddings)
    
    def _detect_provider(self, model_name: str) -> str:
        """Detect embedding provider from model name using explicit mapping."""
        # Check for explicit provider configuration in environment
        explicit_provider = os.getenv("EMBEDDING_PROVIDER", "").lower()
        if explicit_provider:
            return explicit_provider
        
        # Use explicit model mapping for accurate detection
        return self._get_provider_by_model(model_name)
    
    def _get_provider_by_model(self, model_name: str) -> str:
        """Get provider by exact model name matching."""
        model_lower = model_name.lower()
        
        # OpenAI models - exact matching
        openai_models = {
            "text-embedding-3-small", "text-embedding-3-large", 
            "text-embedding-ada-002"
        }
        if model_lower in openai_models:
            return "openai"
        
        # Cohere models - exact matching
        cohere_models = {
            "embed-multilingual-v3.0", "embed-english-v3.0"
        }
        if model_lower in cohere_models:
            return "cohere"
        
        # Ollama models - exact matching
        ollama_models = {
            "llama2", "llama3", "mistral", "codellama", "phi", "gemma", 
            "qwen", "yi", "deepseek", "mixtral", "nomic-embed-text",
            "mxbai-embed-large", "all-minilm"
        }
        if model_lower in ollama_models:
            return "ollama"
        
        # HuggingFace models - check for sentence-transformers prefix or fallback
        if model_lower.startswith("sentence-transformers/") or model_lower.startswith("sentence-"):
            return "huggingface"
        
        # Default fallback
        return "huggingface"
    
        
    def _is_free_model(self, model_name: str) -> bool:
        """Check if model is free/locally hosted."""
        free_providers = ["huggingface", "ollama"]
        return self.provider in free_providers
    
    def create_embeddings(self):
        """Create appropriate embeddings instance."""
        try:
            if self.provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY required for OpenAI embeddings")
                return OpenAIEmbeddings(
                    model=self.model_name,
                    openai_api_key=api_key
                )
            elif self.provider == "cohere":
                api_key = os.getenv("COHERE_API_KEY")
                if not api_key:
                    raise ValueError("COHERE_API_KEY required for Cohere embeddings")
                # Note: Cohere would need different implementation
                raise NotImplementedError("Cohere embeddings not yet implemented")
            elif self.provider == "ollama":
                # Check if using cloud API or local
                ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                ollama_api_key = os.getenv("OLLAMA_API_KEY")
                
                if ollama_api_key and ("api.ollama.com" in ollama_base_url or "cloud" in ollama_base_url.lower()):
                    # Use Ollama Cloud API with proper Ollama endpoints
                    import requests
                    class OllamaCloudEmbeddings:
                        def __init__(self, model, api_key, base_url):
                            self.model = model
                            self.api_key = api_key
                            self.base_url = base_url.rstrip('/')
                        
                        def embed_documents(self, texts):
                            headers = {"Authorization": f"Bearer {self.api_key}"}
                            # Use Ollama's native API format
                            response = requests.post(
                                f"{self.base_url}/api/embeddings",
                                json={"model": self.model, "prompt": texts if len(texts) == 1 else texts},
                                headers=headers
                            )
                            response.raise_for_status()
                            result = response.json()
                            
                            # Handle Ollama's response format
                            if isinstance(result.get("embedding"), list):
                                # Single embedding result
                                return [result["embedding"]]
                            elif isinstance(result.get("embeddings"), list):
                                # Multiple embeddings result
                                return result["embeddings"]
                            else:
                                raise ValueError(f"Unexpected Ollama response format: {result}")
                        
                        def embed_query(self, text):
                            result = self.embed_documents([text])
                            return result[0]
                    
                    return OllamaCloudEmbeddings(self.model_name, ollama_api_key, ollama_base_url)
                else:
                    # Use local Ollama
                    return OllamaEmbeddings(
                        model=self.model_name,
                        base_url=ollama_base_url
                    )
            else:
                # Default to HuggingFace
                return HuggingFaceEmbeddings(model_name=self.model_name)
        except Exception as e:
            print(f"❌ Failed to create embeddings: {e}")
            raise

class PineconeVectorStore:
    """Pinecone-based vector store with dynamic embedding support."""
    
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp-free")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "pdf-rag-index")
        self.project_id = os.getenv("PINECONE_PROJECT_ID", "pdf-rag-app")
        
        # Get embedding configuration
        embedding_model = os.getenv("EMBEDDING_MODEL", "auto")
        self.embedding_provider = EmbeddingProvider(embedding_model)
        
        # Validate configuration
        self._validate_configuration()
        
        # Create embeddings dynamically
        self.embeddings = self.embedding_provider.embeddings
        self.embedding_dimension = self.embedding_provider.dimension
        
        # Initialize Pinecone
        self.pinecone = Pinecone(api_key=self.api_key)
        
        # Get or create index
        self.index = self._get_or_create_index()
    
    def _validate_configuration(self):
        """Validate embedding model and Pinecone configuration."""
        if not self.api_key:
            raise ValueError("❌ PINECONE_API_KEY is required")
        
        print(f"✅ Pinecone Configuration:")
        print(f"  Provider: {self.embedding_provider.provider}")
        print(f"  Model: {self.embedding_provider.model_name}")
        print(f"  Dimension: {self.embedding_provider.dimension}")
        print(f"  Free: {self.embedding_provider.is_free}")
        print(f"  Environment: {self.environment}")
        print(f"  Index: {self.index_name}")
        
        # Validate dimension from .env
        env_dimension = os.getenv("EMBEDDING_DIMENSION")
        if env_dimension:
            print(f"� Using dimension from .env: {env_dimension}")
        else:
            print(f"🔧 Using fallback dimension: {self.embedding_provider.dimension}")
    
        
    def _get_or_create_index(self):
        """Get existing index or create new one with dimension validation."""
        try:
            # Try to get existing index
            if self.index_name in self.pinecone.list_indexes():
                index = self.pinecone.Index(self.index_name)
                
                # Validate existing index dimension
                try:
                    index_stats = index.describe_index_stats()
                    existing_dimension = index_stats.dimension
                    
                    if existing_dimension != self.embedding_dimension:
                        raise ValueError(
                            f"❌ Dimension mismatch!\n"
                            f"  Pinecone index '{self.index_name}' has dimension: {existing_dimension}\n"
                            f"  Embedding model '{self.embedding_provider.model_name}' has dimension: {self.embedding_dimension}\n"
                            f"  Solution: Either recreate the Pinecone index or update EMBEDDING_MODEL/EMBEDDING_DIMENSION in .env"
                        )
                    
                    print(f"✅ Connected to existing Pinecone index: {self.index_name} (dimension: {existing_dimension})")
                    return index
                    
                except Exception as e:
                    raise
                
        except Exception as e:
            print(f"ℹ️ Index may not exist, attempting to create: {e}")
        
        try:
            # Create new index if doesn't exist
            self.pinecone.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            index = self.pinecone.Index(self.index_name)
            print(f"✅ Created new Pinecone index: {self.index_name} (dimension: {self.embedding_dimension})")
            return index
        except Exception as create_error:
            # Handle case where index already exists (409 ConflictError)
            if "already exists" in str(create_error).lower() or "409" in str(create_error):
                print(f"✅ Index '{self.index_name}' already exists, connecting to it")
                index = self.pinecone.Index(self.index_name)
                
                # Validate dimension for existing index
                try:
                    index_stats = index.describe_index_stats()
                    existing_dimension = index_stats.dimension
                    
                    if existing_dimension != self.embedding_dimension:
                        raise ValueError(
                            f"❌ Dimension mismatch!\n"
                            f"  Pinecone index '{self.index_name}' has dimension: {existing_dimension}\n"
                            f"  Embedding model '{self.embedding_provider.model_name}' has dimension: {self.embedding_dimension}\n"
                            f"  Solution: Either recreate the Pinecone index or update EMBEDDING_MODEL/EMBEDDING_DIMENSION in .env"
                        )
                    
                    print(f"✅ Connected to existing Pinecone index: {self.index_name} (dimension: {existing_dimension})")
                    return index
                    
                except Exception as validation_error:
                    if "Dimension mismatch" in str(validation_error):
                        raise
                    print(f"⚠️ Could not validate existing index dimension: {validation_error}")
                    print(f"✅ Connected to existing Pinecone index: {self.index_name}")
                    return index
            else:
                print(f"❌ Failed to create Pinecone index: {create_error}")
                raise
    
    def add_documents(self, documents: List[Document], user_id: Optional[str] = None, session_id: Optional[str] = None):
        """Add documents to Pinecone with metadata for user/session isolation."""
        if not documents:
            return
        
        # Prepare documents with enhanced metadata
        enhanced_docs = []
        for i, doc in enumerate(documents):
            metadata = doc.metadata.copy() if doc.metadata else {}
            
            # Add user and session metadata
            if user_id:
                metadata["user_id"] = user_id
            if session_id:
                metadata["session_id"] = session_id
            
            # Add document source and chunk info
            if not metadata.get("source"):
                metadata["source"] = f"document_{i}"
            metadata["chunk_index"] = i
            metadata["added_at"] = str(__import__('datetime').datetime.now())
            
            enhanced_docs.append(Document(
                page_content=doc.page_content,
                metadata=metadata
            ))
        
        try:
            # Create embeddings and prepare vectors for Pinecone
            from uuid import uuid4
            
            # Generate embeddings for all documents
            texts = [doc.page_content for doc in enhanced_docs]
            embeddings = self.embeddings.embed_documents(texts)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (doc, embedding) in enumerate(zip(enhanced_docs, embeddings)):
                vector_id = str(uuid4())
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "text": doc.page_content,
                        **doc.metadata
                    }
                })
            
            # Upsert vectors to Pinecone in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            print(f"✅ Added {len(documents)} documents to Pinecone ({len(vectors)} vectors)")
        except Exception as e:
            print(f"❌ Failed to add documents to Pinecone: {e}")
            raise
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 8,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search with user/session filtering and metadata support."""
        try:
            # Build filter for user and session isolation
            filter_conditions = {}
            
            if user_id:
                filter_conditions["user_id"] = {"$eq": user_id}
            if session_id:
                filter_conditions["session_id"] = {"$eq": session_id}
            
            # Combine with additional filters
            if filter_dict:
                filter_conditions.update(filter_dict)
            
            # Use LangChain's Pinecone integration
            vectorstore = PineconeLangchain(
                index=self.index,
                embedding=self.embeddings,
                text_key="text"
            )
            
            # Perform similarity search with filters
            results = vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter_conditions if filter_conditions else None
            )
            
            print(f"🔍 Found {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            print(f"❌ Pinecone search failed: {e}")
            return []
    
    def delete_by_user_session(self, user_id: str, session_id: Optional[str] = None):
        """Delete vectors by user and optionally by session."""
        try:
            filter_conditions = {"user_id": {"$eq": user_id}}
            if session_id:
                filter_conditions["session_id"] = {"$eq": session_id}
            
            # Delete vectors matching the filter
            self.index.delete(filter=filter_conditions)
            print(f"🗑️ Deleted vectors for user {user_id}" + (f", session {session_id}" if session_id else ""))
        except Exception as e:
            print(f"❌ Failed to delete vectors: {e}")
    
    def as_retriever(self, **kwargs):
        """Return a retriever compatible with LangChain."""
        try:
            from langchain_pinecone import Pinecone as PineconeLangchain
        except ImportError:
            # Fallback to deprecated version if new package not available
            from langchain_community.vectorstores import Pinecone as PineconeLangchain
        
        # Filter out unsupported parameters for Pinecone constructor
        supported_params = {
            'index', 'embedding', 'text_key', 'namespace', 'top_k',
            'alpha', 'k', 'filter'
        }
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params}
        
        return PineconeLangchain(
            index=self.index,
            embedding=self.embeddings,
            text_key="text",
            **filtered_kwargs
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_name": self.index_name,
                "environment": self.environment
            }
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {}

# Global instance for backward compatibility
_pinecone_store = None

def get_pinecone_store() -> PineconeVectorStore:
    """Get or create Pinecone store instance."""
    global _pinecone_store
    if _pinecone_store is None:
        _pinecone_store = PineconeVectorStore()
    return _pinecone_store

# For compatibility with existing FAISS interface
def get_vectorstore() -> PineconeVectorStore:
    """Get vector store (now Pinecone instead of FAISS)."""
    return get_pinecone_store()

def add_documents_to_vectorstore(docs: List[Document], user_id: Optional[str] = None, session_id: Optional[str] = None):
    """Add documents to vector store with user/session metadata."""
    store = get_pinecone_store()
    store.add_documents(docs, user_id, session_id)

def save_vectorstore(vectorstore):
    """Save vector store (no-op for Pinecone)."""
    pass  # Pinecone automatically persists
