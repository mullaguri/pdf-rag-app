from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, List
import json
from services.rag_service import get_rag_answer, get_rag_answer_stream, SUPPORTED_MODELS, ModelParams
from .auth import get_current_user


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


@router.post("/ask", summary="Ask a question against ingested PDFs")
async def ask_question(payload: QuestionRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
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
            model_params=model_params
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@router.post("/ask-stream", summary="Ask a question with streaming response")
async def ask_question_stream(payload: QuestionRequest):
    """Stream the RAG response in real-time using Server-Sent Events."""
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
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
                model_params=model_params
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