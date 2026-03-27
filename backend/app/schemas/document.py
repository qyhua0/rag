"""
文档 Pydantic Schema
Package: top.modelx.rag
Author: hua
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DocStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
