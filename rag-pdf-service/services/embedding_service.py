from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vectorstore.faiss_store import add_documents_to_vectorstore, get_vectorstore, VECTOR_STORE_PATH
import tempfile, os, shutil
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
    create embeddings and store in FAISS.
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