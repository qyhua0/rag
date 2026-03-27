"""
文档 ORM 模型
Package: top.modelx.rag
Author: hua
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class DocStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
