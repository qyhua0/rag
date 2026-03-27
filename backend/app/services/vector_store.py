"""
向量存储服务 - ChromaDB + Qwen3-Embedding-8B
Package: top.modelx.rag
Author: hua
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Tuple, Optional
from loguru import logger
from app.core.config import settings


class VectorStoreService:
    """向量存储服务"""

    def __init__(self):
        self._embeddings = None
        self._client = None
        self._stores: dict = {}  # kb_id -> Chroma instance

    def _get_embeddings(self) -> OllamaEmbeddings:
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_EMBEDDING_MODEL,
            )
            logger.info(f"Embeddings initialized: {settings.OLLAMA_EMBEDDING_MODEL}")
        return self._embeddings

    def _get_chroma_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        return self._client

    def _get_collection_name(self, kb_id: int) -> str:
        return f"kb_{kb_id}"

    def get_store(self, kb_id: int) -> Chroma:
        """获取或创建指定知识库的向量存储"""
        if kb_id not in self._stores:
            collection_name = self._get_collection_name(kb_id)
            self._stores[kb_id] = Chroma(
                client=self._get_chroma_client(),
                collection_name=collection_name,
                embedding_function=self._get_embeddings(),
            )
        return self._stores[kb_id]

    def text_splitter(self) -> RecursiveCharacterTextSplitter:
        return RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""],
            length_function=len,
        )

    def add_documents(
        self,
        kb_id: int,
        documents: List[Document],
        doc_id: int,
        filename: str,
    ) -> int:
        """将文档分块后存入向量库，返回分块数量"""
        splitter = self.text_splitter()
        chunks = splitter.split_documents(documents)

        # 添加元数据
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "doc_id": str(doc_id),
                "kb_id": str(kb_id),
                "filename": filename,
                "chunk_index": i,
            })

        if not chunks:
            logger.warning(f"No chunks generated for doc_id={doc_id}")
            return 0

        store = self.get_store(kb_id)
        # 批量添加，避免单次过多
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            store.add_documents(batch)

        logger.info(f"Added {len(chunks)} chunks to kb={kb_id}, doc={doc_id}")
        return len(chunks)

    def similarity_search(
        self,
        kb_id: int,
        query: str,
        k: int = None,
        filter_doc_ids: Optional[List[int]] = None,
    ) -> List[Tuple[Document, float]]:
        """相似度搜索，返回 (document, score) 列表"""
        k = k or settings.TOP_K
        store = self.get_store(kb_id)

        where_filter = None
        if filter_doc_ids:
            where_filter = {"doc_id": {"$in": [str(d) for d in filter_doc_ids]}}

        try:
            results = store.similarity_search_with_score(
                query,
                k=k,
                filter=where_filter,
            )
            return results
        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            return []

    def delete_documents(self, kb_id: int, doc_id: int):
        """删除指定文档的所有向量"""
        try:
            client = self._get_chroma_client()
            collection_name = self._get_collection_name(kb_id)
            collection = client.get_collection(collection_name)
            results = collection.get(where={"doc_id": str(doc_id)})
            if results and results["ids"]:
                collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} vectors for doc_id={doc_id}")
                # 清除缓存
                if kb_id in self._stores:
                    del self._stores[kb_id]
        except Exception as e:
            logger.error(f"Delete vectors error: {e}")

    def delete_kb(self, kb_id: int):
        """删除整个知识库的向量集合"""
        try:
            client = self._get_chroma_client()
            collection_name = self._get_collection_name(kb_id)
            client.delete_collection(collection_name)
            if kb_id in self._stores:
                del self._stores[kb_id]
            logger.info(f"Deleted collection for kb_id={kb_id}")
        except Exception as e:
            logger.error(f"Delete KB collection error: {e}")

    def get_kb_stats(self, kb_id: int) -> dict:
        """获取知识库向量统计"""
        try:
            client = self._get_chroma_client()
            collection_name = self._get_collection_name(kb_id)
            collection = client.get_collection(collection_name)
            return {"vector_count": collection.count()}
        except Exception:
            return {"vector_count": 0}


# 全局单例
vector_service = VectorStoreService()
