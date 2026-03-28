"""
 重建指定文件向量
"""
import sys, asyncio
sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models import Document, DocStatus
from app.services.vector_store import vector_service
from app.services.document import doc_service

async def reindex_doc(kb_id: int, doc_id: int):
    db = SessionLocal()
    try:
        # 删除旧向量
        vector_service.delete_documents(kb_id, doc_id)
        print(f"Deleted old vectors for doc_id={doc_id}")

        # 重置状态
        doc = db.query(Document).filter(Document.id == doc_id).first()
        doc.status = DocStatus.PENDING
        doc.chunk_count = 0
        doc.error_msg = None
        db.commit()

        # 重新处理
        await doc_service.process_document(db, doc_id)

        db.refresh(doc)
        print(f"Done: {doc.filename} | status={doc.status} | chunks={doc.chunk_count}")
    finally:
        db.close()

if __name__ == "__main__":
    # kb_id  = int(sys.argv[1])
    # doc_id = int(sys.argv[2])
    kb_id  = 6
    doc_id = 6
    asyncio.run(reindex_doc(kb_id, doc_id))