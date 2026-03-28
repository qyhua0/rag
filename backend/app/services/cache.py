"""
缓存层 - QueryCache + EmbeddingCache
Package: top.modelx.rag
Author: hua
"""
import time
import hashlib
import asyncio
from collections import OrderedDict
from typing import Optional, List, Tuple
from loguru import logger
from app.core.config import settings


class LRUCache:
    """线程安全 LRU 缓存（基于 OrderedDict）"""

    def __init__(self, max_size: int, ttl: int = 0):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl          # 0 表示永不过期
        self._hits = 0
        self._misses = 0
        self._lock = asyncio.Lock()

    async def get(self, key: str):
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            value, ts = self._cache[key]
            if self._ttl > 0 and (time.time() - ts) > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None
            # LRU：移到末尾
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    async def set(self, key: str, value):
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, time.time())
            if len(self._cache) > self._max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug(f"Cache evicted key: {evicted_key[:32]}...")

    async def delete(self, key: str):
        async with self._lock:
            self._cache.pop(key, None)

    async def clear_prefix(self, prefix: str):
        """清除指定前缀的所有缓存（知识库更新时调用）"""
        async with self._lock:
            keys = [k for k in self._cache if k.startswith(prefix)]
            for k in keys:
                del self._cache[k]
            if keys:
                logger.info(f"Cache cleared {len(keys)} keys with prefix={prefix}")

    def stats(self) -> dict:
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
        }


class QueryCache:
    """
    查询结果缓存
    key = kb_id + query 文本的 hash
    value = (sources list, context str)
    """

    def __init__(self):
        self._cache = LRUCache(
            max_size=settings.QUERY_CACHE_MAX_SIZE,
            ttl=settings.QUERY_CACHE_TTL,
        )

    def _make_key(self, kb_id: int, query: str, k: int) -> str:
        raw = f"{kb_id}:{k}:{query.strip().lower()}"
        return "q:" + hashlib.md5(raw.encode()).hexdigest()

    async def get(self, kb_id: int, query: str, k: int):
        key = self._make_key(kb_id, query, k)
        result = await self._cache.get(key)
        if result is not None:
            logger.debug(f"QueryCache HIT | kb={kb_id} query={query[:30]!r}")
        return result

    async def set(self, kb_id: int, query: str, k: int, value):
        key = self._make_key(kb_id, query, k)
        await self._cache.set(key, value)

    async def invalidate_kb(self, kb_id: int):
        """知识库文档更新后清除对应缓存"""
        await self._cache.clear_prefix(f"q:")
        logger.info(f"QueryCache invalidated for kb_id={kb_id}")

    def stats(self) -> dict:
        return self._cache.stats()


class EmbeddingCache:
    """
    Embedding 向量缓存
    key = 文本 hash，value = embedding vector list
    embedding 是纯计算结果，TTL 设为永不过期（模型不变则结果不变）
    """

    def __init__(self):
        self._cache = LRUCache(
            max_size=settings.EMBEDDING_CACHE_MAX_SIZE,
            ttl=0,  # 永不过期
        )

    def _make_key(self, text: str) -> str:
        return "e:" + hashlib.sha256(text.encode()).hexdigest()

    async def get(self, text: str) -> Optional[List[float]]:
        return await self._cache.get(self._make_key(text))

    async def set(self, text: str, vector: List[float]):
        await self._cache.set(self._make_key(text), vector)

    async def get_batch(self, texts: List[str]) -> Tuple[List[Optional[List[float]]], List[int]]:
        """批量获取，返回 (vectors列表含None占位, 未命中的索引列表)"""
        results = []
        miss_indices = []
        for i, text in enumerate(texts):
            v = await self.get(text)
            results.append(v)
            if v is None:
                miss_indices.append(i)
        return results, miss_indices

    async def set_batch(self, texts: List[str], vectors: List[List[float]]):
        for text, vec in zip(texts, vectors):
            await self.set(text, vec)

    def stats(self) -> dict:
        return self._cache.stats()


# 全局单例
query_cache = QueryCache()
embedding_cache = EmbeddingCache()