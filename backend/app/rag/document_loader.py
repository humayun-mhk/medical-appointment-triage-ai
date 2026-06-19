from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import KnowledgeCategory, KnowledgeChunk, KnowledgeDocument
from app.rag.embedding_service import get_embedding


FILENAME_CATEGORIES = {
    "specialty_descriptions": KnowledgeCategory.specialty_description,
    "emergency_red_flag_policy": KnowledgeCategory.emergency_policy,
    "appointment_policy": KnowledgeCategory.clinic_policy,
    "cancellation_policy": KnowledgeCategory.cancellation_policy,
    "patient_preparation_guidelines": KnowledgeCategory.patient_preparation,
    "faq": KnowledgeCategory.faq,
}


def chunk_document(content: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
    cleaned = " ".join((content or "").split())
    if not cleaned:
        return []
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def _title_from_markdown(path: Path, content: str) -> str:
    for line in content.splitlines():
        if line.strip().startswith("#"):
            return line.strip("# ").strip()
    return path.stem.replace("_", " ").title()


def _category_for_path(path: Path) -> KnowledgeCategory:
    for key, category in FILENAME_CATEGORIES.items():
        if key in path.stem:
            return category
    return KnowledgeCategory.safety_guideline


def load_documents_from_folder(folder_path: str) -> list[dict[str, Any]]:
    folder = Path(folder_path)
    documents = []
    for path in sorted(folder.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        documents.append(
            {
                "title": _title_from_markdown(path, content),
                "category": _category_for_path(path),
                "source": path.name,
                "content": content,
                "metadata": {"file_name": path.name},
            }
        )
    return documents


def save_document_to_db(title, category, source, content, metadata, db: Session) -> KnowledgeDocument:
    existing = db.query(KnowledgeDocument).filter(KnowledgeDocument.source == source).first()
    if existing:
        existing.title = title
        existing.category = category
        existing.content = content
        existing.document_metadata = metadata or {}
        existing.is_active = True
        document = existing
    else:
        document = KnowledgeDocument(
            title=title,
            category=category,
            source=source,
            content=content,
            document_metadata=metadata or {},
            is_active=True,
        )
        db.add(document)
    db.flush()
    return document


def save_chunks_to_db(document_id, chunks, db: Session) -> list[KnowledgeChunk]:
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document_id).delete()
    saved = []
    for index, chunk_text in enumerate(chunks):
        chunk = KnowledgeChunk(
            document_id=document_id,
            chunk_text=chunk_text,
            chunk_index=index,
            embedding=get_embedding(chunk_text),
            chunk_metadata={"chunk_size": len(chunk_text)},
        )
        db.add(chunk)
        saved.append(chunk)
    db.flush()
    return saved
