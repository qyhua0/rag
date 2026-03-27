"""
Pydantic 数据模式
Package: top.modelx.rag
Author: hua
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


class KBStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DocStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ===== Knowledge Base Schemas =====
class KBCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = "📚"
    embedding_model: Optional[str] = "qwen3-embedding-8b"


class KBUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[KBStatus] = None


class KBOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: str
    status: str
    embedding_model: str
    doc_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== Document Schemas =====
class DocOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    file_type: Optional[str]
    file_size: int
    status: str
    error_msg: Optional[str]
    chunk_count: int
    char_count: int
    source_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class LocalPathImport(BaseModel):
    kb_id: int
    path: str = Field(..., description="本地文件或目录路径")
    recursive: bool = Field(default=True, description="是否递归扫描子目录")


# ===== Chat Schemas =====
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


# ===== Response Schemas =====
class ResponseModel(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class PageData(BaseModel):
    total: int
    items: List[Any]
    page: int
    page_size: int
