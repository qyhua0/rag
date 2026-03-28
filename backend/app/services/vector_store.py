"""
向量存储服务 - ChromaDB + Qwen3-Embedding-8B
Package: top.modelx.rag
Author: hua
"""
import uuid
import asyncio
import time
from typing import List, Tuple, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

from app.core.config import settings
from app.services.cache import embedding_cache


class AsyncEmbeddingWrapper:
    """
    将同步 OllamaEmbeddings 包装为支持：
      1. EmbeddingCache 缓存
      2. 信号量控制并发
      3. 兼容 FastAPI 已有事件循环（不再用 run_until_complete）
    """

    def __init__(self):
        self._emb: Optional[OllamaEmbeddings] = None
        # 信号量在第一次异步调用时懒初始化，避免在事件循环外创建
        self._semaphore: Optional[asyncio.Semaphore] = None

    def _get_emb(self) -> OllamaEmbeddings:
        if self._emb is None:
            self._emb = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_EMBEDDING_MODEL,
            )
            logger.info(f"Embedding model loaded: {settings.OLLAMA_EMBEDDING_MODEL}")
        return self._emb

    def _get_semaphore(self) -> asyncio.Semaphore:
        """懒初始化信号量，确保在事件循环内创建"""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(settings.EMBEDDING_CONCURRENCY)
        return self._semaphore

    def _sync_embed_documents(self, texts: List[str]) -> List[List[float]]:
        """纯同步 embed，供 run_in_executor 调用"""
        return self._get_emb().embed_documents(texts)

    def _sync_embed_query(self, text: str) -> List[float]:
        """纯同步 embed query，供 run_in_executor 调用"""
        return self._get_emb().embed_query(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """带缓存的异步批量 embed（文档入库时使用）"""
        if not texts:
            return []

        # 批量查缓存
        cached_vectors, miss_indices = await embedding_cache.get_batch(texts)
        if not miss_indices:
            logger.debug(f"EmbeddingCache full hit: {len(texts)} texts")
            return cached_vectors  # type: ignore

        # 只请求未命中的
        miss_texts = [texts[i] for i in miss_indices]
        new_vectors = await self._async_batch_embed(miss_texts)

        # 写缓存
        await embedding_cache.set_batch(miss_texts, new_vectors)

        # 合并
        for idx, vec in zip(miss_indices, new_vectors):
            cached_vectors[idx] = vec

        logger.debug(
            f"EmbeddingCache: {len(texts)-len(miss_indices)} hits, "
            f"{len(miss_indices)} misses"
        )
        return cached_vectors  # type: ignore

    async def aembed_query(self, text: str) -> List[float]:
        """带缓存的异步单文本 embed（检索时使用）"""
        cached = await embedding_cache.get(text)
        if cached is not None:
            logger.debug("EmbeddingCache query HIT")
            return cached

        loop = asyncio.get_event_loop()
        async with self._get_semaphore():
            vec = await loop.run_in_executor(None, self._sync_embed_query, text)

        await embedding_cache.set(text, vec)
        return vec

    async def _async_batch_embed(self, texts: List[str]) -> List[List[float]]:
        """受信号量保护的实际 embed 调用，按批分组"""
        result: List[List[float]] = []
        loop = asyncio.get_event_loop()
        batch_size = settings.EMBED_BATCH_SIZE

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            async with self._get_semaphore():
                t0 = time.time()
                vecs = await loop.run_in_executor(
                    None, self._sync_embed_documents, batch
                )
                elapsed = (time.time() - t0) * 1000
                logger.debug(
                    f"Embed batch {i//batch_size + 1}: "
                    f"{len(batch)} texts in {elapsed:.1f}ms"
                )
            result.extend(vecs)
        return result

    # ── LangChain Embeddings 接口（同步，供 Chroma 内部调用）─────────────

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Chroma 入库时同步调用。
        此时已在 run_in_executor 的线程中，直接同步调用即可，无事件循环冲突。
        """
        batch_size = settings.EMBED_BATCH_SIZE
        result = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            t0 = time.time()
            vecs = self._sync_embed_documents(batch)
            elapsed = (time.time() - t0) * 1000
            logger.debug(f"sync embed_documents batch: {len(batch)} in {elapsed:.1f}ms")
            result.extend(vecs)
        return result

    def embed_query(self, text: str) -> List[float]:
        """
        Chroma similarity_search 内部同步调用此方法。
        直接走同步接口，完全避开事件循环嵌套问题。
        缓存通过 aembed_query 在外层异步检索流程中提前处理。
        """
        return self._sync_embed_query(text)

class VectorStoreService:
    """
    向量存储服务（生产级）
    - 异步 embedding（AsyncEmbeddingWrapper）
    - 多策略检索：similarity / mmr / hybrid
    - 相似度阈值过滤
    - 唯一 chunk ID 防止重复覆盖
    """

    def __init__(self):
        self._emb_wrapper = AsyncEmbeddingWrapper()
        self._client: Optional[chromadb.PersistentClient] = None
        self._stores: dict = {}

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _collection_name(self, kb_id: int) -> str:
        return f"kb_{kb_id}"

    def get_store(self, kb_id: int) -> Chroma:
        if kb_id not in self._stores:
            self._stores[kb_id] = Chroma(
                client=self._get_client(),
                collection_name=self._collection_name(kb_id),
                embedding_function=self._emb_wrapper,
            )
        return self._stores[kb_id]

    def _text_splitter(self) -> RecursiveCharacterTextSplitter:
        return RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""],
            length_function=len,
        )

    # ── 写入

    async def add_documents_async(
        self,
        kb_id: int,
        documents: List[Document],
        doc_id: int,
        filename: str,
    ) -> int:
        """
        异步文档入库：
        1. 文本分块
        2. 异步批量 embed（含缓存）
        3. 写入 ChromaDB（每块唯一 UUID，防止重复覆盖）
        """
        splitter = self._text_splitter()
        chunks = splitter.split_documents(documents)

        if not chunks:
            logger.warning(f"No chunks for doc_id={doc_id} filename={filename}")
            return 0

        # 设置元数据（全部 str，避免 ChromaDB filter 类型问题）
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "doc_id":      str(doc_id),
                "kb_id":       str(kb_id),
                "filename":    filename,
                "chunk_index": str(i),
            })

        # 异步批量 embed
        texts = [c.page_content for c in chunks]
        t0 = time.time()
        vectors = await self._emb_wrapper.aembed_documents(texts)
        embed_ms = (time.time() - t0) * 1000
        logger.info(
            f"[EMBED] doc_id={doc_id} | chunks={len(chunks)} | "
            f"embed_time={embed_ms:.1f}ms"
        )

        # 写入 ChromaDB（用唯一 UUID 作为 id）
        store = self.get_store(kb_id)
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]
            ids = [str(uuid.uuid4()) for _ in batch_chunks]
            store.add_documents(batch_chunks, ids=ids)

        logger.info(
            f"[VECTOR_STORE] Added kb={kb_id} doc_id={doc_id} "
            f"filename={filename} chunks={len(chunks)}"
        )
        return len(chunks)

    # ── 检索

    async def similarity_search_async(
        self,
        kb_id: int,
        query: str,
        k: int = None,
        strategy: str = "similarity",        # similarity | mmr | hybrid
        score_threshold: float = None,
        filter_doc_ids: Optional[List[int]] = None,
    ) -> Tuple[List[Tuple[Document, float]], int]:
        """
        异步相似度检索
        返回 (过滤后结果列表, 被阈值过滤掉的数量)
        """
        k = k or settings.TOP_K
        threshold = score_threshold if score_threshold is not None \
            else settings.RETRIEVAL_SCORE_THRESHOLD
        store = self.get_store(kb_id)

        where_filter = None
        if filter_doc_ids:
            if len(filter_doc_ids) == 1:
                where_filter = {"doc_id": str(filter_doc_ids[0])}
            else:
                where_filter = {"doc_id": {"$in": [str(d) for d in filter_doc_ids]}}

        try:
            loop = asyncio.get_event_loop()

            if strategy == "mmr":
                # MMR：最大边际相关性，减少结果冗余
                raw_docs = await loop.run_in_executor(
                    None,
                    lambda: store.max_marginal_relevance_search(
                        query, k=k, fetch_k=k * 3,
                        filter=where_filter,
                    )
                )
                # MMR 不返回 score，统一赋 1.0 占位
                raw = [(doc, 1.0) for doc in raw_docs]

            elif strategy == "hybrid":
                # Hybrid：similarity + mmr 结果合并去重，综合召回
                sim_results = await loop.run_in_executor(
                    None,
                    lambda: store.similarity_search_with_score(
                        query, k=k, filter=where_filter,
                    )
                )
                mmr_docs = await loop.run_in_executor(
                    None,
                    lambda: store.max_marginal_relevance_search(
                        query, k=k // 2 + 1, fetch_k=k * 2,
                        filter=where_filter,
                    )
                )
                # 合并：sim 结果优先，mmr 补充去重
                seen = {id(d) for d, _ in sim_results}
                raw = list(sim_results)
                for doc in mmr_docs:
                    if id(doc) not in seen and len(raw) < k:
                        raw.append((doc, 0.8))  # mmr 补充结果赋 0.8 分
                        seen.add(id(doc))

            else:
                # 默认 similarity
                raw = await loop.run_in_executor(
                    None,
                    lambda: store.similarity_search_with_score(
                        query, k=k, filter=where_filter,
                    )
                )

            # 相似度阈值过滤
            filtered = []
            filtered_out = 0
            for doc, score in raw:
                # ChromaDB 返回 L2 距离，用指数衰减转为 0~1 相似度
                import math
                sim = math.exp(-float(score))
                if sim >= threshold:
                    filtered.append((doc, sim))
                else:
                    filtered_out += 1
                    logger.debug(
                        f"[FILTER] score={score:.4f} sim={sim:.4f} < threshold={threshold} "
                        f"file={doc.metadata.get('filename', '?')} "
                        f"chunk={doc.metadata.get('chunk_index', '?')}"
                    )

            # 按相似度降序
            filtered.sort(key=lambda x: x[1], reverse=True)
            return filtered, filtered_out

        except Exception as e:
            logger.error(f"[VECTOR_STORE] Search error kb={kb_id}: {e}")
            return [], 0

    # ── 删除 ──────────────────────────────────────────────────────────────

    def delete_documents(self, kb_id: int, doc_id: int):
        try:
            col = self._get_client().get_collection(self._collection_name(kb_id))
            res = col.get(where={"doc_id": str(doc_id)})
            if res and res["ids"]:
                col.delete(ids=res["ids"])
                logger.info(
                    f"[VECTOR_STORE] Deleted {len(res['ids'])} vectors "
                    f"kb={kb_id} doc_id={doc_id}"
                )
            if kb_id in self._stores:
                del self._stores[kb_id]
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Delete doc error: {e}")

    def delete_kb(self, kb_id: int):
        try:
            self._get_client().delete_collection(self._collection_name(kb_id))
            self._stores.pop(kb_id, None)
            logger.info(f"[VECTOR_STORE] Deleted collection kb={kb_id}")
        except Exception as e:
            logger.error(f"[VECTOR_STORE] Delete KB error: {e}")

    def get_kb_stats(self, kb_id: int) -> dict:
        try:
            col = self._get_client().get_collection(self._collection_name(kb_id))
            return {"vector_count": col.count()}
        except Exception:
            return {"vector_count": 0}


# 全局单例
vector_service = VectorStoreService()