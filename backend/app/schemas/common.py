"""
通用响应 Schema
Package: top.modelx.rag
Author: hua
"""
from pydantic import BaseModel
from typing import Optional, Any, List


class ResponseModel(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class PageData(BaseModel):
    total: int
    items: List[Any]
    page: int
    page_size: int
