import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - development fallback before dependencies are installed
    from sqlalchemy.types import JSON

    def Vector(dimensions: int):  # noqa: N802
        return JSON()

from app.db.database import Base


class KnowledgeCategory(str, enum.Enum):
    specialty_description = "specialty_description"
    clinic_policy = "clinic_policy"
    emergency_policy = "emergency_policy"
    doctor_service = "doctor_service"
    faq = "faq"
    cancellation_policy = "cancellation_policy"
    patient_preparation = "patient_preparation"
    safety_guideline = "safety_guideline"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(Enum(KnowledgeCategory, name="knowledge_category"), nullable=False, index=True)
    source = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    document_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    chunk_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("KnowledgeDocument", back_populates="chunks")

    __table_args__ = (
        Index("ix_knowledge_chunks_document_index", "document_id", "chunk_index", unique=True),
    )


class RAGQuery(Base):
    __tablename__ = "rag_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    triage_session_id = Column(Integer, ForeignKey("symptom_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    query_text = Column(Text, nullable=False)
    retrieved_chunks = Column(JSONB, nullable=False, default=list)
    response_text = Column(Text, nullable=False)
    safety_flags = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    triage_session = relationship("SymptomSession")
