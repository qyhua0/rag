"""
数据库模型 - 知识库、文档、会话
Package: top.modelx.rag
Author: hua
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class KBStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DocStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False, comment="原始文件名")
    file_path = Column(String(1000), comment="存储路径")
    file_type = Column(String(50), comment="文件类型")
    file_size = Column(BigInteger, default=0, comment="文件大小(bytes)")
    status = Column(Enum(DocStatus), default=DocStatus.PENDING)
    error_msg = Column(Text, comment="错误信息")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    char_count = Column(Integer, default=0, comment="字符数量")
    meta_info = Column(JSON, comment="元数据")
    source_type = Column(String(20), default="upload", comment="来源: upload/local_path")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), default="新对话")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    knowledge_base = relationship("KnowledgeBase", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conv_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, comment="user/assistant")
    content = Column(Text, nullable=False)
    sources = Column(JSON, comment="引用来源")
    tokens = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
