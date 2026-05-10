import os
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from .pinecone_store import EmbeddingProvider

load_dotenv()

VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./vectorstore/faiss_index")
EMBEDDING_MODEL   = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Use EmbeddingProvider for proper provider detection
embedding_provider = EmbeddingProvider(EMBEDDING_MODEL)
embeddings = embedding_provider.embeddings

def get_vectorstore() -> FAISS:
    """Load existing FAISS index or return None if not found."""
    if os.path.exists(VECTOR_STORE_PATH):
        return FAISS.load_local(
            VECTOR_STORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
    return None

def save_vectorstore(vectorstore: FAISS):
    """Persist FAISS index to disk."""
    os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)
    vectorstore.save_local(VECTOR_STORE_PATH)

def add_documents_to_vectorstore(docs: list):
    """Add new documents to existing or new FAISS index."""
    if not docs:
        return

    existing = get_vectorstore()
    if existing:
        existing.add_documents(docs)
        save_vectorstore(existing)
        return existing
    else:
        new_store = FAISS.from_documents(docs, embeddings)
        save_vectorstore(new_store)
        return new_store