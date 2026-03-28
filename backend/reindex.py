"""
重建指定知识库的所有向量索引
用法: python reindex.py <kb_id>
"""
import sys
import asyncio
sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models import Document, DocStatus
from app.services.vector_store import vector_service
from app.services.document import doc_service

async def reindex(kb_id: int):
    db = SessionLocal()
    try:
        # 清除旧向量
        vector_service.delete_kb(kb_id)
        print(f"Deleted old vectors for kb_id={kb_id}")

        # 重置所有文档状态
        docs = db.query(Document).filter(Document.kb_id == kb_id).all()
        for doc in docs:
            doc.status = DocStatus.PENDING
            doc.chunk_count = 0
            doc.error_msg = None
        db.commit()

        # 重新处理
        for doc in docs:
            print(f"Processing: {doc.filename}")
            await doc_service.process_document(db, doc.id)
            print(f"Done: {doc.filename}, chunks={doc.chunk_count}")

    finally:
        db.close()

if __name__ == "__main__":
    # kb_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    kb_id = 6
    asyncio.run(reindex(kb_id))