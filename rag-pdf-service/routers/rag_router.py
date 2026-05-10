from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, List
import json
from services.rag_service import get_rag_answer, get_rag_answer_stream, SUPPORTED_MODELS, ModelParams
from services.history_service import get_history_service
from .auth import get_current_user, get_current_user_object
from database import get_db


router = APIRouter(prefix="/rag", tags=["RAG"], dependencies=[Depends(get_current_user)])


class ModelParamsRequest(BaseModel):
    """Optional model parameters for tuning generation."""
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None
    seed: Optional[int] = None
    timeout: Optional[int] = None


class QuestionRequest(BaseModel):
    question: str
    evaluate: bool = True
    model_name: Optional[str] = None
    model_params: Optional[ModelParamsRequest] = None
    session_id: Optional[str] = None


@router.post("/ask", summary="Ask a question against ingested PDFs")
async def ask_question(
    payload: QuestionRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
        # Get user object from database
        from models import User
        user_obj = db.query(User).filter(User.username == current_user["username"]).first()
        user_id = user_obj.id if user_obj else None
        
        # Convert request params to ModelParams if provided
        model_params = None
        if payload.model_params:
            model_params = ModelParams(
                temperature=payload.model_params.temperature,
                top_p=payload.model_params.top_p,
                top_k=payload.model_params.top_k,
                max_tokens=payload.model_params.max_tokens,
                frequency_penalty=payload.model_params.frequency_penalty,
                presence_penalty=payload.model_params.presence_penalty,
                stop=payload.model_params.stop,
                seed=payload.model_params.seed,
                timeout=payload.model_params.timeout,
            )
        
        result = get_rag_answer(
            question=payload.question,
            evaluate=payload.evaluate,
            model_name=payload.model_name,
            model_params=model_params,
            user_id=user_id,
            session_id=payload.session_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@router.post("/ask-stream", summary="Ask a question with streaming response")
async def ask_question_stream(
    payload: QuestionRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Stream the RAG response in real-time using Server-Sent Events."""
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    # Get user object from database
    from models import User
    user_obj = db.query(User).filter(User.username == current_user["username"]).first()
    user_id = user_obj.id if user_obj else None
    
    # Convert request params to ModelParams if provided
    model_params = None
    if payload.model_params:
        model_params = ModelParams(
            temperature=payload.model_params.temperature,
            top_p=payload.model_params.top_p,
            top_k=payload.model_params.top_k,
            max_tokens=payload.model_params.max_tokens,
            frequency_penalty=payload.model_params.frequency_penalty,
            presence_penalty=payload.model_params.presence_penalty,
            stop=payload.model_params.stop,
            seed=payload.model_params.seed,
            timeout=payload.model_params.timeout,
        )
    
    async def event_generator():
        try:
            # Stream the answer chunks
            async for chunk in get_rag_answer_stream(
                question=payload.question,
                evaluate=payload.evaluate,
                model_name=payload.model_name,
                model_params=model_params,
                user_id=user_id,
                session_id=payload.session_id
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': f'LLM error: {str(e)}'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/models", summary="List all supported LLM models")
async def get_supported_models():
    """
    Returns all supported models grouped by provider.
    """
    models_by_provider = {}
    for model_key, config in SUPPORTED_MODELS.items():
        provider = config["provider"]
        if provider not in models_by_provider:
            models_by_provider[provider] = []
        models_by_provider[provider].append({
            "model": model_key,
            "is_default": config.get("default", False)
        })
    
    return {
        "providers": list(models_by_provider.keys()),
        "models": models_by_provider
    }

@router.get("/health", summary="Check if vector store is ready")
async def health_check():
    from vectorstore.faiss_store import get_vectorstore
    store = get_vectorstore()
    return {
        "vector_store_ready": store is not None
    }


@router.get("/history", summary="Get conversation history")
async def get_conversation_history(
    session_id: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get conversation history for the current user."""
    try:
        # Get user object from database
        from models import User
        user_obj = db.query(User).filter(User.username == current_user["username"]).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get conversation history
        history_service = get_history_service(db)
        history = history_service.get_conversation_history(
            user_id=user_obj.id,
            session_id=session_id,
            limit=limit
        )
        
        # Format response
        formatted_history = []
        for conv in history:
            sources = []
            if conv.sources:
                try:
                    import json
                    sources = json.loads(conv.sources)
                except:
                    pass
            
            formatted_history.append({
                "id": conv.id,
                "question": conv.question,
                "answer": conv.answer,
                "sources": sources,
                "session_id": conv.session_id,
                "created_at": conv.created_at.isoformat() if conv.created_at else None
            })
        
        return {
            "history": formatted_history,
            "total": len(formatted_history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.delete("/history", summary="Clear conversation history")
async def clear_conversation_history(
    session_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """Clear conversation history for the current user."""
    try:
        # Get user object from database
        from models import User
        user_obj = db.query(User).filter(User.username == current_user["username"]).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Clear conversation history
        history_service = get_history_service(db)
        deleted_count = history_service.clear_user_history(
            user_id=user_obj.id,
            session_id=session_id
        )
        
        return {
            "message": f"Successfully deleted {deleted_count} conversation entries",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")