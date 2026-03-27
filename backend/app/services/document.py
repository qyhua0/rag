"""
文档处理服务 - 协调文档解析、分块、向量化
Package: top.modelx.rag
Author: hua
"""
import os
import shutil
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger
from app.core.config import settings
from app.models import Document, KnowledgeBase, DocStatus
from app.services.parser import parser
from app.services.vector_store import vector_service


class DocumentService:
    """文档处理服务"""

    def get_upload_path(self, kb_id: int, filename: str) -> str:
        """生成文件存储路径"""
        kb_dir = os.path.join(settings.UPLOAD_DIR, f"kb_{kb_id}")
        os.makedirs(kb_dir, exist_ok=True)
        return os.path.join(kb_dir, filename)

    def is_supported_file(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower().lstrip(".")
        return ext in settings.allowed_extensions_list

    async def process_document(
        self,
        db: Session,
        doc_id: int,
    ):
        """后台处理文档：解析 + 向量化"""
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            logger.error(f"Document not found: {doc_id}")
            return

        # 更新状态为处理中
        doc.status = DocStatus.PROCESSING
        db.commit()

        try:
            # 1. 解析文档
            documents, meta = parser.parse(doc.file_path, doc.filename)

            # 2. 向量化存储
            chunk_count = vector_service.add_documents(
                kb_id=doc.kb_id,
                documents=documents,
                doc_id=doc.id,
                filename=doc.filename,
            )

            # 3. 更新文档状态
            doc.status = DocStatus.COMPLETED
            doc.chunk_count = chunk_count
            doc.char_count = meta.get("total_chars", 0)
            doc.meta_info = meta
            db.commit()

            # 4. 更新知识库文档计数
            self._update_kb_doc_count(db, doc.kb_id)
            logger.info(f"Document processed: {doc.filename}, chunks={chunk_count}")

        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {e}")
            doc.status = DocStatus.FAILED
            doc.error_msg = str(e)[:500]
            db.commit()

    def _update_kb_doc_count(self, db: Session, kb_id: int):
        from app.models import DocStatus
        count = db.query(Document).filter(
            Document.kb_id == kb_id,
            Document.status == DocStatus.COMPLETED
        ).count()
        db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).update(
            {"doc_count": count}
        )
        db.commit()

    async def import_from_path(
        self,
        db: Session,
        kb_id: int,
        path: str,
        recursive: bool = True,
    ) -> list:
        """从本地路径导入文件"""
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        files = []
        if path_obj.is_file():
            files = [path_obj]
        elif path_obj.is_dir():
            pattern = "**/*" if recursive else "*"
            files = [f for f in path_obj.glob(pattern) if f.is_file()]
        else:
            raise ValueError(f"Invalid path: {path}")

        doc_ids = []
        for f in files:
            if not self.is_supported_file(f.name):
                logger.warning(f"Skipping unsupported file: {f.name}")
                continue

            # 复制文件到上传目录
            dest_path = self.get_upload_path(kb_id, f.name)
            if str(f) != dest_path:
                shutil.copy2(str(f), dest_path)

            # 创建文档记录
            doc = Document(
                kb_id=kb_id,
                filename=f.name,
                file_path=dest_path,
                file_type=parser.get_file_type(f.name),
                file_size=f.stat().st_size,
                source_type="local_path",
                status=DocStatus.PENDING,
            )
            db.add(doc)
            db.flush()
            doc_ids.append(doc.id)

        db.commit()

        # 异步处理所有文档
        for doc_id in doc_ids:
            await self.process_document(db, doc_id)

        return doc_ids

    def delete_document(self, db: Session, doc_id: int):
        """删除文档：删除文件、向量、数据库记录"""
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return

        kb_id = doc.kb_id

        # 删除向量
        vector_service.delete_documents(kb_id, doc_id)

        # 删除文件
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception as e:
                logger.error(f"Error deleting file: {e}")

        # 删除数据库记录
        db.delete(doc)
        db.commit()

        # 更新计数
        self._update_kb_doc_count(db, kb_id)


# 全局单例
doc_service = DocumentService()
