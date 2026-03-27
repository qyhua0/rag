"""
知识库 ORM 模型
Package: top.modelx.rag
Author: hua
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class KBStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="知识库名称")
    description = Column(Text, comment="知识库描述")
    icon = Column(String(10), default="📚", comment="图标emoji")
    status = Column(Enum(KBStatus), default=KBStatus.ACTIVE)
    embedding_model = Column(String(100), default="qwen3-embedding-8b")
    doc_count = Column(Integer, default=0, comment="文档数量")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="knowledge_base", cascade="all, delete-orphan")
