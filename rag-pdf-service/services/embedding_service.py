from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vectorstore.faiss_store import add_documents_to_vectorstore, get_vectorstore, VECTOR_STORE_PATH
import tempfile, os, shutil

def process_pdf(file_bytes: bytes, filename: str) -> dict:
    """
    Save PDF temporarily, load, split into chunks,
    create embeddings and store in FAISS.
    """
    # Save to temp file (PyPDFLoader needs a file path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # Load PDF
        loader = PyPDFLoader(tmp_path)
        pages  = loader.load()

        if not pages:
            raise ValueError(f"No pages could be extracted from '{filename}'. "
                             "It may be a scanned or image-based PDF.")

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(pages)

        # Tag source metadata
        for chunk in chunks:
            chunk.metadata["source"] = filename

        # Embed and store
        add_documents_to_vectorstore(chunks)

        return {
            "filename": filename,
            "pages":    len(pages),
            "chunks":   len(chunks)
        }
    finally:
        os.unlink(tmp_path)  # cleanup temp file

def get_all_document_names() -> list[str]:
    """Retrieve all unique document names from the vector store."""
    vectorstore = get_vectorstore()
    if not vectorstore:
        return []

    # Access the docstore to get all documents
    docstore = vectorstore.docstore._dict
    if not docstore:
        return []

    # Extract unique source filenames
    doc_names = set(doc.metadata.get("source") for doc in docstore.values())
    return sorted(list(doc_names))

def reset_vector_store():
    """Delete the entire vector store directory."""
    if os.path.exists(VECTOR_STORE_PATH):
        shutil.rmtree(VECTOR_STORE_PATH)
        return True
    return False