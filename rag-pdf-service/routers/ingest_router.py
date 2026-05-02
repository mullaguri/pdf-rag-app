from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.embedding_service import process_pdf, reset_vector_store, get_all_document_names
from typing import List
from .auth import get_current_user, get_current_user_object
import models
from datetime import datetime


router = APIRouter(prefix="/ingest", tags=["Ingest"], dependencies=[Depends(get_current_user)])

@router.post("/pdf", summary="Upload a single PDF and create embeddings")
async def ingest_pdf(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_object)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    
    contents = await file.read()
    result   = process_pdf(contents, file.filename)

    # Create a document record
    new_document = models.Document(
        filename=file.filename,
        chunk_count=result["chunks"],
        uploaded_at=datetime.utcnow(),
        size_bytes=len(contents),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.username,
        updated_by=current_user.username
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return {
        "message": f"PDF '{result['filename']}' ingested successfully.",
        "pages":   result["pages"],
        "chunks":  result["chunks"]
    }

@router.post("/pdfs", summary="Upload multiple PDFs at once")
async def ingest_multiple_pdfs(files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_object)):
    results = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            continue  # skip non-PDFs silently
        
        contents = await file.read()
        result   = process_pdf(contents, file.filename)
        
        # Create a document record
        new_document = models.Document(
            filename=file.filename,
            chunk_count=result["chunks"],
            uploaded_at=datetime.utcnow(),
            size_bytes=len(contents),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=current_user.username,
            updated_by=current_user.username
        )
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        results.append(result)

    return {
        "message":        f"{len(results)} PDF(s) ingested successfully.",
        "ingested_files": results
    }


@router.get("/documents", summary="Retrieve all document names from the vector store")
def get_documents():
    document_names = get_all_document_names()
    return {"documents": document_names}


@router.delete("/vector-store", summary="Reset the entire vector store")
def reset_datastore():
    if reset_vector_store():
        return {"message": "Vector store has been reset."}
    else:
        return {"message": "Vector store not found or already empty."}
