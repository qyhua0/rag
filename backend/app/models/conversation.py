"""
会话 & 消息 ORM 模型
Package: top.modelx.rag
Author: hua
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


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
