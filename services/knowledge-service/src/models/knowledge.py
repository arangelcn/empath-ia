"""Data models for documents, retrieval, and service health.

These models are intentionally explicit because they are the contract between
the Admin Panel, Gateway Service, AI Service, and Knowledge Service.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Lifecycle states for an uploaded knowledge document."""

    DRAFT = "draft"
    AWAITING_VALIDATION = "awaiting_validation"
    PROCESSING = "processing"
    INDEXED = "indexed"
    APPROVED = "approved"
    ACTIVE = "active"
    FAILED = "failed"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class DocumentContentType(str, Enum):
    """Document formats accepted by the Knowledge Service foundation."""

    PDF = "pdf"
    MARKDOWN = "markdown"
    TXT = "txt"
    STRUCTURED = "structured"


class KnowledgeDocumentCreate(BaseModel):
    """Request body used by the Admin flow to register a document."""

    title: str = Field(..., min_length=1, description="Human-readable document title.")
    source: str = Field(..., min_length=1, description="Where the document came from, such as upload, url, or manual.")
    source_uri: Optional[str] = Field(default=None, description="Private URI or external source reference.")
    content_type: DocumentContentType = Field(default=DocumentContentType.TXT, description="Original document format.")
    language: str = Field(default="en", min_length=2, max_length=8, description="BCP-47-ish language code.")
    tags: List[str] = Field(default_factory=list, description="Admin-facing labels for filtering documents.")
    scopes: List[str] = Field(default_factory=list, description="Prompt-controlled retrieval scopes.")
    review_policy: Optional[str] = Field(default=None, description="How admins should review this document before activation.")
    created_by: Optional[str] = Field(default=None, description="Admin identifier responsible for the registration.")


class KnowledgeDocument(BaseModel):
    """Stored representation of a knowledge document."""

    document_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:12]}")
    document_version: int = 1
    title: str
    source: str
    source_uri: Optional[str] = None
    content_type: DocumentContentType = DocumentContentType.TXT
    language: str = "en"
    tags: List[str] = Field(default_factory=list)
    scopes: List[str] = Field(default_factory=list)
    review_policy: Optional[str] = None
    status: DocumentStatus = DocumentStatus.DRAFT
    content_hash: Optional[str] = None
    chunk_count: int = 0
    quality_warnings: List[str] = Field(default_factory=list)
    last_indexed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentStatusUpdate(BaseModel):
    """Request body used to move a document to a new lifecycle state."""

    status: DocumentStatus = Field(..., description="Target lifecycle state for the document.")
    updated_by: Optional[str] = Field(default=None, description="Admin identifier responsible for the change.")
    reason: Optional[str] = Field(default=None, description="Short audit explanation for the status change.")


class DocumentContentIngest(BaseModel):
    """Request body used to attach normalized text to a document.

    This is the first ingestion slice. The Admin can register a file/document and
    then send extracted text. Native PDF parsing and file storage will come next.
    """

    content: str = Field(..., min_length=1, description="Normalized text extracted from the source document.")
    content_type: DocumentContentType = Field(default=DocumentContentType.TXT, description="Content format after extraction.")
    section: Optional[str] = Field(default=None, description="Optional section label when ingesting one part of a document.")
    ingested_by: Optional[str] = Field(default=None, description="Admin or system actor responsible for ingestion.")


class ChunkQuality(BaseModel):
    """Quality metadata produced by local chunk cohesion checks."""

    cohesion_score: float = Field(default=0.0, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)


class KnowledgeChunk(BaseModel):
    """A semantically bounded text chunk traceable to a document version."""

    chunk_id: str
    document_id: str
    document_version: int
    source: str
    source_uri: Optional[str] = None
    title: str
    section: Optional[str] = None
    language: str
    content: str
    content_hash: str
    chunk_hash: str
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    status: DocumentStatus = DocumentStatus.INDEXED
    quality: ChunkQuality = Field(default_factory=ChunkQuality)


class RetrievalRequest(BaseModel):
    """Internal request from the AI Service when a prompt allows RAG."""

    query: str = Field(..., min_length=1, description="User or system query to retrieve knowledge for.")
    chat_id: Optional[str] = Field(default=None, description="Opaque chat identifier for audit correlation.")
    prompt_key: Optional[str] = Field(default=None, description="Prompt key that authorized this retrieval.")
    prompt_version: Optional[int] = Field(default=None, description="Prompt version that authorized this retrieval.")
    allowed_scopes: List[str] = Field(default_factory=list, description="Scopes allowed by Prompt Control.")
    language: Optional[str] = Field(default=None, description="Preferred retrieval language.")
    top_k: int = Field(default=6, ge=1, le=20, description="Maximum number of chunks to return.")
    trace_id: Optional[str] = Field(default=None, description="End-to-end trace identifier.")


class PromptRagPolicy(BaseModel):
    """Prompt Control metadata that governs whether retrieval may run."""

    enabled: bool = Field(default=False, description="Whether this prompt is allowed to use RAG.")
    allowed_scopes: List[str] = Field(default_factory=list, description="Knowledge scopes this prompt may retrieve from.")
    top_k: int = Field(default=6, ge=1, le=20, description="Maximum chunks the prompt may request.")
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum acceptable final retrieval score.")
    require_citations: bool = Field(default=True, description="Whether the final answer should cite retrieved sources.")
    fallback_behavior: str = Field(default="answer_without_sources", description="Safe behavior when retrieval is unavailable.")


class RetrievalScore(BaseModel):
    """Scores produced by the retrieval pipeline for a single result."""

    vector: Optional[float] = None
    lexical: Optional[float] = None
    rerank: Optional[float] = None
    final: Optional[float] = None


class RetrievalCitation(BaseModel):
    """Source metadata that lets Admin audit where a retrieved chunk came from."""

    document_id: str
    document_version: Optional[int] = None
    title: str
    section: Optional[str] = None


class RetrievalResult(BaseModel):
    """One retrieved chunk returned to the AI Service."""

    chunk_id: str
    content: str
    citation: RetrievalCitation
    scores: RetrievalScore = Field(default_factory=RetrievalScore)
    retrieval_reason: Optional[str] = None


class RetrievalResponse(BaseModel):
    """Knowledge retrieval response consumed by the AI Service."""

    success: bool
    index_version: Optional[str] = None
    results: List[RetrievalResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ServiceHealth(BaseModel):
    """Health payload returned by `/health`."""

    status: str
    service: str
    version: str
    storage: str
    vector_store: str
    lexical_index: str
