"""
系统状态 API
Package: top.modelx.rag
Author: hua
"""
from fastapi import APIRouter
from app.core.config import settings
from app.services.rag import rag_service
import httpx

router = APIRouter(prefix="/api/system", tags=["系统"])


@router.get("/health")
async def health_check():
    ollama_ok = rag_service.test_connection()
    return {
        "status": "healthy",
        "ollama": ollama_ok,
        "llm_model": settings.OLLAMA_LLM_MODEL,
        "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
        "version": settings.APP_VERSION,
    }


@router.get("/models")
async def list_ollama_models():
    """列出 Ollama 可用模型"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}
