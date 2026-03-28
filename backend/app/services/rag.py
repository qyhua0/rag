"""
RAG 推理服务（生产级）
- QueryCache 查询缓存
- 多检索策略（similarity / mmr / hybrid）
- 检索日志 + Prompt 日志 + 命中率统计
- Context 截断保护
- 异步非阻塞
Package: top.modelx.rag
Author: hua
"""
import json
import time
from typing import List, Optional, AsyncGenerator, Tuple

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger

from app.core.config import settings
from app.services.vector_store import vector_service
from app.services.cache import query_cache
from app.services.retrieval_log import (
    log_retrieval, log_prompt, RetrievalStats
)


SYSTEM_PROMPT = """你是企业内部知识库助手，请根据以下参考文档回答用户问题。

重要规则：
1. 参考文档是从向量数据库模糊检索出来的，内容可能与问题有一定相关性，请仔细阅读后作答
2. 即使文档标题与问题措辞不完全一致，只要内容相关就应提取并回答
3. 若文档中确实完全没有任何相关内容，才回复"未找到相关信息"
4. 引用内容时标注来源：【来源：文件名】
5. 回答清晰、专业、用中文

参考文档：
{context}
"""


class RAGService:

    def _get_llm(self, streaming: bool = False) -> ChatOllama:
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_LLM_MODEL,
            streaming=streaming,
            temperature=0.3,          # 生产环境降低随机性
            num_predict=2048,
        )

    # ── 检索（带缓存 + 日志）─────────────────────────────────────────────

    async def retrieve(
        self,
        kb_id: int,
        query: str,
        k: int = None,
        strategy: str = "similarity",
    ) -> Tuple[List[Tuple], bool]:
        """
        返回 (results, cache_hit)
        results = [(Document, score), ...]
        """
        k = k or settings.TOP_K
        t0 = time.time()

        # 1. 查 QueryCache
        cached = await query_cache.get(kb_id, query, k)
        if cached is not None:
            latency = (time.time() - t0) * 1000
            log_retrieval(kb_id, query, cached, latency,
                          cache_hit=True, strategy=strategy)
            return cached, True

        # 2. 向量检索
        results, filtered_out = await vector_service.similarity_search_async(
            kb_id=kb_id,
            query=query,
            k=k,
            strategy=strategy,
        )

        latency = (time.time() - t0) * 1000
        log_retrieval(kb_id, query, results, latency,
                      cache_hit=False, strategy=strategy,
                      filtered_count=filtered_out)

        # 3. 写 QueryCache
        if results:
            await query_cache.set(kb_id, query, k, results)

        return results, False

    # ── Context 构建

    def _build_context(self, results: List[Tuple]) -> Tuple[str, List[dict]]:
        # 只取前 RERANK_TOP_K 条（已按 sim 降序）
        top_results = results[:settings.RERANK_TOP_K]

        parts = []
        sources = []
        total_len = 0

        for i, (doc, score) in enumerate(top_results):
            filename = doc.metadata.get("filename", "未知文件")
            page = doc.metadata.get("page", "")
            page_info = f"·第{page}页" if page else ""
            content = doc.page_content

            if total_len + len(content) > settings.MAX_CONTEXT_LENGTH:
                remain = settings.MAX_CONTEXT_LENGTH - total_len
                if remain < 100:
                    break
                content = content[:remain] + "…"

            part = f"[{i + 1}] 【{filename}{page_info}】（相关度：{score:.2%}）\n{content}"
            parts.append(part)
            total_len += len(content)

            sources.append({
                "index": i + 1,
                "filename": filename,
                "page": page,
                "score": round(float(score), 4),
                "doc_id": doc.metadata.get("doc_id"),
                "content": doc.page_content[:300] + "…"
                if len(doc.page_content) > 300
                else doc.page_content,
            })

        return "\n\n---\n\n".join(parts), sources

    def _build_prompt_messages(self, history: List[dict]) -> list:
        msgs = [("system", SYSTEM_PROMPT)]
        for msg in history[-6:]:          # 最近 3 轮
            if msg["role"] == "user":
                msgs.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                msgs.append(("ai", msg["content"]))
        msgs.append(("human", "{question}"))
        return msgs

    # ── 非流式问答 ────────────────────────────────────────────────────────

    async def chat(
        self,
        kb_id: int,
        question: str,
        history: Optional[List[dict]] = None,
        strategy: str = "similarity",
    ) -> Tuple[str, List[dict]]:
        history = history or []

        results, _ = await self.retrieve(kb_id, question, strategy=strategy)
        context, sources = self._build_context(results)

        log_prompt(
            kb_id=kb_id,
            question=question,
            context_length=len(context),
            history_turns=len(history) // 2,
            prompt_tokens_est=len(context) // 2 + len(question) // 2,
        )

        llm = self._get_llm(streaming=False)
        prompt = ChatPromptTemplate.from_messages(
            self._build_prompt_messages(history)
        )
        chain = prompt | llm | StrOutputParser()
        answer = await chain.ainvoke({"context": context, "question": question})
        return answer, sources

    # ── 流式问答 ─────────────────────────────────────────────────────────

    async def chat_stream(
        self,
        kb_id: int,
        question: str,
        history: Optional[List[dict]] = None,
        strategy: str = "similarity",
    ) -> AsyncGenerator[str, None]:
        history = history or []

        #results, cache_hit = await self.retrieve(kb_id, question, strategy=strategy)

        results, cache_hit = await self.retrieve(
            kb_id, question,
            k=settings.TOP_K,
            strategy="hybrid",  # 改为 hybrid，similarity+mmr 双路召回
        )

        context, sources = self._build_context(results)

        log_prompt(
            kb_id=kb_id,
            question=question,
            context_length=len(context),
            history_turns=len(history) // 2,
            prompt_tokens_est=len(context) // 2 + len(question) // 2,
        )

        # 先推送来源
        yield f"data: {json.dumps({'type': 'sources', 'data': sources}, ensure_ascii=False)}\n\n"

        # 空结果时快速返回
        if not results:
            msg = "根据当前知识库内容，未找到与该问题相关的信息。"
            yield f"data: {json.dumps({'type': 'token', 'data': msg})}\n\n"
            yield f"data: {json.dumps({'type': 'done',  'data': msg})}\n\n"
            return

        llm = self._get_llm(streaming=True)
        prompt = ChatPromptTemplate.from_messages(
            self._build_prompt_messages(history)
        )
        chain = prompt | llm | StrOutputParser()

        full_answer = ""
        async for chunk in chain.astream({"context": context, "question": question}):
            full_answer += chunk
            yield f"data: {json.dumps({'type': 'token', 'data': chunk}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'data': full_answer}, ensure_ascii=False)}\n\n"

    # ── 工具方法 ──────────────────────────────────────────────────────────

    def test_connection(self) -> bool:
        try:
            import httpx
            r = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False


# 全局单例
rag_service = RAGService()