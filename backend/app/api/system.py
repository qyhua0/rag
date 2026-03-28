"""
系统状态 API（含检索统计、缓存状态）
Package: top.modelx.rag
Author: hua
"""
import httpx
from fastapi import APIRouter
from app.core.config import settings
from app.services.rag import rag_service
from app.services.cache import query_cache, embedding_cache
from app.services.retrieval_log import RetrievalStats

router = APIRouter(prefix="/api/system", tags=["系统"])


@router.get("/health")
async def health_check():
    ollama_ok = rag_service.test_connection()
    return {
        "status":          "healthy",
        "ollama":          ollama_ok,
        "llm_model":       settings.OLLAMA_LLM_MODEL,
        "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
        "version":         settings.APP_VERSION,
    }


@router.get("/stats")
async def get_stats():
    """检索命中率 + 缓存状态"""
    return {
        "retrieval": RetrievalStats.summary(),
        "query_cache":     query_cache.stats(),
        "embedding_cache": embedding_cache.stats(),
    }


@router.post("/cache/clear")
async def clear_cache(kb_id: int = None):
    """手动清除缓存（文档更新后调用）"""
    if kb_id:
        await query_cache.invalidate_kb(kb_id)
    else:
        await query_cache._cache.clear_prefix("q:")
    return {"message": "缓存已清除"}


@router.get("/models")
async def list_models():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5
            )
            return {"models": [m["name"] for m in r.json().get("models", [])]}
    except Exception as e:
        return {"models": [], "error": str(e)}