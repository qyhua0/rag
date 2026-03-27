"""
对话 API - RAG 问答与会话管理
Package: top.modelx.rag
Author: hua
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.models import Conversation, Message, KnowledgeBase
from app.schemas import ChatRequest, ConversationOut, MessageOut, ResponseModel, PageData
from app.services.rag import rag_service
from loguru import logger

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.get("/conversations", response_model=ResponseModel)
def list_conversations(
    kb_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Conversation).filter(Conversation.kb_id == kb_id)
    total = query.count()
    items = query.order_by(Conversation.updated_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    return ResponseModel(data=PageData(
        total=total, items=[ConversationOut.model_validate(i) for i in items],
        page=page, page_size=page_size
    ))


@router.get("/conversations/{conv_id}/messages", response_model=ResponseModel)
def get_messages(
    conv_id: int,
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = db.query(Message).filter(Message.conv_id == conv_id) \
        .order_by(Message.created_at.asc()).all()
    return ResponseModel(data=[MessageOut.model_validate(m) for m in messages])


@router.delete("/conversations/{conv_id}", response_model=ResponseModel)
def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete(conv)
    db.commit()
    return ResponseModel(message="删除成功")


@router.post("/send", response_model=ResponseModel)
async def send_message(body: ChatRequest, db: Session = Depends(get_db)):
    """发送消息（非流式）"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == body.kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 获取或创建会话
    conv = _get_or_create_conversation(db, body.kb_id, body.conv_id, body.question)

    # 获取历史消息
    history = _get_history(db, conv.id)

    # RAG 推理
    try:
        answer, sources = await rag_service.chat(body.kb_id, body.question, history)
    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")

    # 保存消息
    user_msg = Message(conv_id=conv.id, role="user", content=body.question)
    ai_msg = Message(conv_id=conv.id, role="assistant", content=answer, sources=sources)
    db.add_all([user_msg, ai_msg])
    db.commit()
    db.refresh(ai_msg)

    return ResponseModel(data={
        "conv_id": conv.id,
        "message": MessageOut.model_validate(ai_msg),
    })


@router.post("/stream")
async def stream_message(body: ChatRequest, db: Session = Depends(get_db)):
    """发送消息（流式 SSE）"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == body.kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    conv = _get_or_create_conversation(db, body.kb_id, body.conv_id, body.question)
    history = _get_history(db, conv.id)

    # 保存用户消息
    user_msg = Message(conv_id=conv.id, role="user", content=body.question)
    db.add(user_msg)
    db.commit()

    async def event_generator():
        import json
        full_answer = ""
        final_sources = []
        try:
            async for chunk in rag_service.chat_stream(body.kb_id, body.question, history):
                yield chunk
                # 解析最后的完整答案
                if '"type": "done"' in chunk or '"type":"done"' in chunk:
                    try:
                        data = json.loads(chunk.replace("data: ", "").strip())
                        full_answer = data.get("data", "")
                    except Exception:
                        pass
                elif '"type": "sources"' in chunk or '"type":"sources"' in chunk:
                    try:
                        data = json.loads(chunk.replace("data: ", "").strip())
                        final_sources = data.get("data", [])
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        finally:
            # 保存 AI 回复
            if full_answer:
                ai_msg = Message(
                    conv_id=conv.id, role="assistant",
                    content=full_answer, sources=final_sources
                )
                db.add(ai_msg)
                db.commit()

        # 返回 conv_id
        yield f"data: {json.dumps({'type': 'conv_id', 'data': conv.id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


def _get_or_create_conversation(db: Session, kb_id: int, conv_id: Optional[int], question: str) -> Conversation:
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv:
            return conv

    # 用问题前20字作为标题
    title = question[:20] + "..." if len(question) > 20 else question
    conv = Conversation(kb_id=kb_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _get_history(db: Session, conv_id: int) -> List[dict]:
    messages = db.query(Message).filter(Message.conv_id == conv_id) \
        .order_by(Message.created_at.asc()).limit(20).all()
    return [{"role": m.role, "content": m.content} for m in messages]
