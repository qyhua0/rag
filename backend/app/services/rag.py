"""
RAG 推理服务 - LangChain + Ollama LLM
Package: top.modelx.rag
Author: hua
"""
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Optional, AsyncGenerator, Tuple
from loguru import logger
from app.core.config import settings
from app.services.vector_store import vector_service


SYSTEM_PROMPT = """你是一个企业内部知识库智能助手，请根据以下参考文档内容回答用户问题。

规则：
1. 优先使用参考文档中的信息回答
2. 如果文档中没有相关信息，直接说明无法从知识库中找到相关内容
3. 引用信息时注明来源文件名
4. 回答要准确、简洁、专业
5. 使用中文回答

参考文档：
{context}
"""


class RAGService:
    """RAG 推理服务"""

    def __init__(self):
        self._llm = None

    def _get_llm(self, streaming: bool = False) -> ChatOllama:
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_LLM_MODEL,
            streaming=streaming,
            temperature=0.7,
        )

    def _format_context(self, results: List[Tuple]) -> Tuple[str, List[dict]]:
        """格式化检索结果为上下文字符串和来源列表"""
        context_parts = []
        sources = []

        for i, (doc, score) in enumerate(results):
            filename = doc.metadata.get("filename", "未知文件")
            page = doc.metadata.get("page", "")
            page_info = f" (第{page}页)" if page else ""

            context_parts.append(
                f"[文档{i+1}] 来源: {filename}{page_info}\n{doc.page_content}"
            )
            sources.append({
                "index": i + 1,
                "filename": filename,
                "page": page,
                "score": round(float(score), 4),
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "doc_id": doc.metadata.get("doc_id"),
            })

        return "\n\n---\n\n".join(context_parts), sources

    def _build_messages(self, history: List[dict]) -> List:
        """构建历史消息"""
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        return messages

    async def chat(
        self,
        kb_id: int,
        question: str,
        history: Optional[List[dict]] = None,
    ) -> Tuple[str, List[dict]]:
        """RAG 问答（非流式）"""
        history = history or []

        # 1. 向量检索
        results = vector_service.similarity_search(kb_id, question)
        if not results:
            logger.warning(f"No relevant docs found for kb_id={kb_id}")
            context = "未找到相关文档内容。"
            sources = []
        else:
            context, sources = self._format_context(results)

        # 2. 构建 Prompt
        llm = self._get_llm(streaming=False)
        prompt_messages = [("system", SYSTEM_PROMPT)]

        # 添加历史对话
        for msg in history[-6:]:  # 最近3轮对话
            if msg["role"] == "user":
                prompt_messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                prompt_messages.append(("ai", msg["content"]))

        prompt_messages.append(("human", "{question}"))
        prompt = ChatPromptTemplate.from_messages(prompt_messages)

        # 3. LLM 推理
        chain = prompt | llm | StrOutputParser()
        answer = await chain.ainvoke({
            "context": context,
            "question": question,
        })

        return answer, sources

    async def chat_stream(
        self,
        kb_id: int,
        question: str,
        history: Optional[List[dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """RAG 问答（流式）"""
        history = history or []

        # 1. 向量检索
        results = vector_service.similarity_search(kb_id, question)
        if not results:
            context = "未找到相关文档内容。"
            sources = []
        else:
            context, sources = self._format_context(results)

        # 2. 先返回来源信息
        import json
        yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"

        # 3. 构建 Prompt
        llm = self._get_llm(streaming=True)
        prompt_messages = [("system", SYSTEM_PROMPT)]

        for msg in (history or [])[-6:]:
            if msg["role"] == "user":
                prompt_messages.append(("human", msg["content"]))
            elif msg["role"] == "assistant":
                prompt_messages.append(("ai", msg["content"]))

        prompt_messages.append(("human", "{question}"))
        prompt = ChatPromptTemplate.from_messages(prompt_messages)
        chain = prompt | llm | StrOutputParser()

        # 4. 流式输出
        full_answer = ""
        async for chunk in chain.astream({"context": context, "question": question}):
            full_answer += chunk
            yield f"data: {json.dumps({'type': 'token', 'data': chunk})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'data': full_answer})}\n\n"

    def test_connection(self) -> bool:
        """测试 Ollama 连接"""
        try:
            import httpx
            resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


# 全局单例
rag_service = RAGService()
