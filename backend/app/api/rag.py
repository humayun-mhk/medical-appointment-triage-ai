from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user, require_admin
from app.db.database import get_db
from app.models import KnowledgeChunk, KnowledgeDocument, User
from app.rag.document_loader import chunk_document, save_chunks_to_db, save_document_to_db
from app.rag.rag_service import answer_policy_question
from app.schemas import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUpdate,
    RAGAnswerResponse,
    RAGQueryRequest,
)
from app.security.rate_limit import admin_rate_limit

router = APIRouter(tags=["RAG"])


def _document_response(document: KnowledgeDocument, include_chunks: bool = True) -> dict:
    chunks = sorted(document.chunks, key=lambda chunk: chunk.chunk_index)
    return {
        "id": document.id,
        "title": document.title,
        "category": document.category,
        "source": document.source,
        "content": document.content,
        "metadata": document.document_metadata or {},
        "is_active": document.is_active,
        "chunks_count": len(chunks),
        "chunks": [
            {
                "id": chunk.id,
                "chunk_text": chunk.chunk_text,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.chunk_metadata or {},
                "created_at": chunk.created_at,
            }
            for chunk in chunks
        ]
        if include_chunks
        else [],
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


def _get_document(db: Session, document_id: int) -> KnowledgeDocument:
    document = (
        db.query(KnowledgeDocument)
        .options(joinedload(KnowledgeDocument.chunks))
        .filter(KnowledgeDocument.id == document_id)
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge document not found")
    return document


@router.post("/rag/query", response_model=RAGAnswerResponse)
def query_rag(
    payload: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return answer_policy_question(current_user.id, payload.question, db)


@router.get("/admin/knowledge-base", response_model=list[KnowledgeDocumentResponse])
def list_knowledge_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    documents = (
        db.query(KnowledgeDocument)
        .options(joinedload(KnowledgeDocument.chunks))
        .order_by(KnowledgeDocument.updated_at.desc(), KnowledgeDocument.id.desc())
        .all()
    )
    return [_document_response(document, include_chunks=False) for document in documents]


@router.post("/admin/knowledge-base", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_document(
    payload: KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    document = save_document_to_db(payload.title, payload.category, payload.source, payload.content, payload.metadata, db)
    save_chunks_to_db(document.id, chunk_document(document.content), db)
    db.commit()
    document = _get_document(db, document.id)
    return _document_response(document)


@router.get("/admin/knowledge-base/{document_id}", response_model=KnowledgeDocumentResponse)
def get_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    return _document_response(_get_document(db, document_id))


@router.patch("/admin/knowledge-base/{document_id}", response_model=KnowledgeDocumentResponse)
def update_knowledge_document(
    document_id: int,
    payload: KnowledgeDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    document = _get_document(db, document_id)
    values = payload.model_dump(exclude_unset=True)
    needs_reindex = False
    if "title" in values:
        document.title = values["title"]
    if "category" in values:
        document.category = values["category"]
    if "source" in values:
        document.source = values["source"]
    if "metadata" in values:
        document.document_metadata = values["metadata"] or {}
    if "is_active" in values:
        document.is_active = values["is_active"]
    if "content" in values:
        document.content = values["content"]
        needs_reindex = True
    if needs_reindex:
        save_chunks_to_db(document.id, chunk_document(document.content), db)
    db.commit()
    return _document_response(_get_document(db, document_id))


@router.delete("/admin/knowledge-base/{document_id}")
def delete_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    document = _get_document(db, document_id)
    document.is_active = False
    db.commit()
    return {"message": "Knowledge document deactivated"}


@router.post("/admin/knowledge-base/{document_id}/reindex", response_model=KnowledgeDocumentResponse)
def reindex_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _limit: None = Depends(admin_rate_limit),
):
    document = _get_document(db, document_id)
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id).delete()
    save_chunks_to_db(document.id, chunk_document(document.content), db)
    db.commit()
    return _document_response(_get_document(db, document_id))
