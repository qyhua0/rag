"""
知识库管理 API
Package: top.modelx.rag
Author: hua
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models import KnowledgeBase, KBStatus
from app.schemas import KBCreate, KBUpdate, KBOut, ResponseModel, PageData
from app.services.vector_store import vector_service
from loguru import logger

router = APIRouter(prefix="/api/kb", tags=["知识库"])


@router.get("", response_model=ResponseModel)
def list_kbs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(KnowledgeBase)
    if keyword:
        query = query.filter(KnowledgeBase.name.like(f"%{keyword}%"))
    total = query.count()
    items = query.order_by(KnowledgeBase.created_at.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    return ResponseModel(data=PageData(
        total=total, items=[KBOut.model_validate(i) for i in items],
        page=page, page_size=page_size
    ))


@router.post("", response_model=ResponseModel)
def create_kb(body: KBCreate, db: Session = Depends(get_db)):
    kb = KnowledgeBase(**body.model_dump())
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return ResponseModel(data=KBOut.model_validate(kb))


@router.get("/{kb_id}", response_model=ResponseModel)
def get_kb(kb_id: int, db: Session = Depends(get_db)):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    stats = vector_service.get_kb_stats(kb_id)
    data = KBOut.model_validate(kb).model_dump()
    data.update(stats)
    return ResponseModel(data=data)


@router.put("/{kb_id}", response_model=ResponseModel)
def update_kb(kb_id: int, body: KBUpdate, db: Session = Depends(get_db)):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(kb, k, v)
    db.commit()
    db.refresh(kb)
    return ResponseModel(data=KBOut.model_validate(kb))


@router.delete("/{kb_id}", response_model=ResponseModel)
def delete_kb(kb_id: int, db: Session = Depends(get_db)):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    vector_service.delete_kb(kb_id)
    db.delete(kb)
    db.commit()
    return ResponseModel(message="删除成功")
