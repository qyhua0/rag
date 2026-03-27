"""
知识库 Pydantic Schema
Package: top.modelx.rag
Author: hua
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class KBStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


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
