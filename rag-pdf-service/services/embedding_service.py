from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vectorstore.pinecone_store import add_documents_to_vectorstore, get_vectorstore
import tempfile, os
from pdf2image import convert_from_bytes
import pytesseract
from config import settings

# If a Tesseract path is specified in config, set it
if settings.TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

def _extract_text_from_scanned_pdf(file_bytes: bytes) -> list[Document]:
    """Extract text from a scanned PDF using OCR."""
    images = convert_from_bytes(file_bytes)
    documents = []
    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        if text.strip():
            doc = Document(
                page_content=text,
                metadata={"source": "scanned", "page": i}
            )
            documents.append(doc)
    return documents

def process_pdf(file_bytes: bytes, filename: str) -> dict:
    """
    Save PDF temporarily, load, split into chunks,
    create embeddings and store in Pinecone.
    Handles both text-based and scanned PDFs.
    """
    pages = []
    # Save to temp file (PyPDFLoader needs a file path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # 1. Try to load as a text-based PDF
        try:
            loader = PyPDFLoader(tmp_path)
            loaded_pages = loader.load()
            if loaded_pages:
                # Simple heuristic: check if there's meaningful content
                total_text = "".join(p.page_content for p in loaded_pages)
                if len(total_text.strip()) > 10 * len(loaded_pages): # at least 10 chars per page on avg
                    pages = loaded_pages
        except Exception:
            # PyPDFLoader can fail on some PDFs, so we'll just fall back to OCR
            pass

        # 2. If text extraction fails or is insufficient, use OCR
        if not pages:
            try:
                pages = _extract_text_from_scanned_pdf(file_bytes)
            except Exception as e:
                # This could be due to Tesseract not being installed, or other issues
                raise ValueError(
                    f"Failed to process PDF '{filename}' with both standard text extraction and OCR. "
                    f"If it's a scanned PDF, ensure Tesseract OCR is installed. OCR error: {e}"
                ) from e

        if not pages:
            raise ValueError(f"No pages or text could be extracted from '{filename}'. "
                             "The file may be empty or corrupted.")

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
    """Retrieve all unique document names from the Pinecone vector store."""
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            return []
        
        # Query Pinecone index to get all vectors with their metadata
        try:
            # Get actual embedding dimension from vector store
            embedding_dimension = vectorstore.embedding_dimension
            
            # Get all vectors from the index (limit to a reasonable number)
            query_response = vectorstore.index.query(
                vector=[0] * embedding_dimension,  # Dummy vector with correct dimension
                top_k=1000,  # Get up to 1000 results
                include_metadata=True
            )
            
            # Extract unique document names from metadata
            document_names = set()
            if query_response.matches:
                for match in query_response.matches:
                    metadata = match.metadata or {}
                    # Look for document name in various metadata fields
                    doc_name = (
                        metadata.get("source") or 
                        metadata.get("filename") or 
                        metadata.get("document_name") or 
                        metadata.get("title")
                    )
                    if doc_name:
                        document_names.add(doc_name)
            
            return sorted(list(document_names))
            
        except Exception as e:
            print(f"Error retrieving document names: {e}")
            return []
    except Exception as e:
        print(f"Error accessing vector store: {e}")
        return []

def reset_vector_store():
    """Delete all vectors from the Pinecone index."""
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            return False
        
        # Delete all vectors from the Pinecone index
        vectorstore.index.delete(delete_all=True)
        print("✅ All vectors deleted from the Pinecone index")
        return True
    except Exception as e:
        print(f"Error resetting vector store: {e}")
        return False

def delete_pinecone_index():
    """Delete the entire Pinecone index."""
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            return {"success": False, "message": "Vector store not found"}
        
        # Get index name before deletion
        index_name = vectorstore.index_name
        
        # Delete the entire index
        vectorstore.pinecone.delete_index(index_name)
        print(f"✅ Pinecone index '{index_name}' deleted successfully")
        return {"success": True, "index_name": index_name, "message": f"Pinecone index '{index_name}' deleted successfully"}
    except Exception as e:
        print(f"Error deleting Pinecone index: {e}")
        return {"success": False, "message": f"Error deleting Pinecone index: {e}"}