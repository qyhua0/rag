"""
对话 Pydantic Schema
Package: top.modelx.rag
Author: hua
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    kb_id: int
    conv_id: Optional[int] = None
    question: str = Field(..., min_length=1)
    stream: bool = False


class MessageOut(BaseModel):
    id: int
    conv_id: int
    role: str
    content: str
    sources: Optional[List[Dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    kb_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
