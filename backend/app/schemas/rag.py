from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import KnowledgeCategory


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


class RAGSource(BaseModel):
    title: str
    category: str


class RAGAnswerResponse(BaseModel):
    answer: str
    sources: list[RAGSource] = []
    safety_flags: list[Any] = []
    disclaimer: str


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    category: KnowledgeCategory
    source: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=10)
    metadata: dict[str, Any] = {}


class KnowledgeDocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    category: KnowledgeCategory | None = None
    source: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = Field(default=None, min_length=10)
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class KnowledgeChunkResponse(BaseModel):
    id: int
    chunk_text: str
    chunk_index: int
    metadata: dict[str, Any] = {}
    created_at: datetime | None = None


class KnowledgeDocumentResponse(BaseModel):
    id: int
    title: str
    category: KnowledgeCategory
    source: str
    content: str
    metadata: dict[str, Any] = {}
    is_active: bool
    chunks_count: int = 0
    chunks: list[KnowledgeChunkResponse] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
