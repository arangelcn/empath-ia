"""Document lifecycle and retrieval orchestration for the Knowledge Service."""

from datetime import datetime
from typing import Dict, List, Optional

from ..models.knowledge import (
    DocumentStatus,
    DocumentStatusUpdate,
    DocumentContentIngest,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeDocumentCreate,
    RetrievalCitation,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
    RetrievalScore,
)
from .chunking_service import SemanticChunkingService
from .file_ingestion_service import KnowledgeFileIngestionService


class KnowledgeDocumentService:
    """Coordinate document lifecycle operations for the Knowledge Service.

    The first implementation uses an in-memory repository so the service can be
    scaffolded, tested, and wired into Docker before storage decisions harden.
    Later, the public methods can keep the same shape while persistence moves
    to MongoDB and indexing moves to Qdrant/SQLite FTS5.
    """

    def __init__(self):
        """Create the service with an empty in-memory document store."""
        self._documents: Dict[str, KnowledgeDocument] = {}
        self._chunks: Dict[str, List[KnowledgeChunk]] = {}
        self._audit_events: List[dict] = []
        self._chunking_service = SemanticChunkingService()
        self._file_ingestion_service = KnowledgeFileIngestionService()

    def create_document(self, payload: KnowledgeDocumentCreate) -> KnowledgeDocument:
        """Register a document and keep it in `draft` until Admin advances it."""
        document = KnowledgeDocument(**payload.model_dump())
        self._documents[document.document_id] = document
        self._record_audit_event(
            action="document.created",
            document_id=document.document_id,
            actor=payload.created_by,
            details={"status": document.status.value},
        )
        return document

    def ingest_document_content(
        self,
        document_id: str,
        payload: DocumentContentIngest,
    ) -> Optional[KnowledgeDocument]:
        """Attach extracted text, generate chunks, and mark the document indexed.

        This method starts Track 1 by turning normalized document text into
        semantic chunks. It does not create embeddings yet; the resulting chunks
        are the future input for vector and lexical indexes.
        """
        document = self._documents.get(document_id)
        if not document:
            return None

        document.status = DocumentStatus.PROCESSING
        document.content_type = payload.content_type
        document.updated_at = datetime.utcnow()

        chunks = self._chunking_service.chunk_document(
            document=document,
            content=payload.content,
            section=payload.section,
        )
        warnings = sorted({warning for chunk in chunks for warning in chunk.quality.warnings})

        document.status = DocumentStatus.INDEXED
        document.content_hash = chunks[0].content_hash if chunks else None
        document.chunk_count = len(chunks)
        document.quality_warnings = warnings
        document.last_indexed_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        self._documents[document_id] = document
        self._chunks[document_id] = chunks

        self._record_audit_event(
            action="document.ingested",
            document_id=document.document_id,
            actor=payload.ingested_by,
            details={
                "chunk_count": len(chunks),
                "content_type": payload.content_type.value,
                "quality_warnings": warnings,
            },
        )
        return document

    def ingest_uploaded_file(
        self,
        document_id: str,
        filename: str,
        file_bytes: bytes,
        content_type: Optional[str],
        section: Optional[str],
        ingested_by: Optional[str],
    ) -> Optional[dict]:
        """Extract text from one uploaded file and ingest it into the document."""
        document = self._documents.get(document_id)
        if not document:
            return None

        extracted_upload = self._file_ingestion_service.extract_upload(
            document_id=document_id,
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )

        if not document.source_uri:
            document.source_uri = extracted_upload.stored_uri
        document.updated_at = datetime.utcnow()
        self._documents[document_id] = document

        indexed_document = self.ingest_document_content(
            document_id=document_id,
            payload=DocumentContentIngest(
                content=extracted_upload.content,
                content_type=extracted_upload.content_type,
                section=section,
                ingested_by=ingested_by,
            ),
        )

        self._record_audit_event(
            action="document.file_uploaded",
            document_id=document_id,
            actor=ingested_by,
            details={
                "filename": extracted_upload.original_filename,
                "stored_uri": extracted_upload.stored_uri,
                "byte_size": extracted_upload.byte_size,
                "content_type": extracted_upload.content_type.value,
                "section": section,
            },
        )

        return {
            "document": indexed_document,
            "upload": {
                "filename": extracted_upload.original_filename,
                "stored_uri": extracted_upload.stored_uri,
                "byte_size": extracted_upload.byte_size,
                "content_type": extracted_upload.content_type.value,
                "extracted_characters": len(extracted_upload.content),
            },
        }

    def list_documents(
        self,
        status: Optional[DocumentStatus] = None,
        scope: Optional[str] = None,
    ) -> List[KnowledgeDocument]:
        """Return documents filtered by lifecycle status and/or retrieval scope."""
        documents = list(self._documents.values())

        if status:
            documents = [document for document in documents if document.status == status]

        if scope:
            documents = [document for document in documents if scope in document.scopes]

        return sorted(documents, key=lambda document: document.updated_at, reverse=True)

    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        """Return one document by ID, or `None` when it does not exist."""
        return self._documents.get(document_id)

    def list_chunks(self, document_id: str) -> Optional[List[KnowledgeChunk]]:
        """Return chunks for one document, or `None` when the document is unknown."""
        if document_id not in self._documents:
            return None
        return list(self._chunks.get(document_id, []))

    def update_document_status(
        self,
        document_id: str,
        payload: DocumentStatusUpdate,
    ) -> Optional[KnowledgeDocument]:
        """Move a document to a new lifecycle state and record an audit event."""
        document = self._documents.get(document_id)
        if not document:
            return None

        previous_status = document.status
        document.status = payload.status
        document.updated_at = datetime.utcnow()
        self._documents[document_id] = document

        self._record_audit_event(
            action="document.status_changed",
            document_id=document.document_id,
            actor=payload.updated_by,
            details={
                "from": previous_status.value,
                "to": payload.status.value,
                "reason": payload.reason,
            },
        )
        return document

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Return retrieved chunks for a prompt-scoped query using lexical scoring.

        Filters eligible chunks (from INDEXED/APPROVED/ACTIVE documents whose scopes
        overlap with the requested allowed_scopes) and ranks them by token overlap
        with the query. Returns the top_k results sorted by lexical score.
        """
        warnings: list = []

        if not request.allowed_scopes:
            warnings.append(
                "No allowed scopes were provided by Prompt Control; retrieval skipped."
            )
            self._record_audit_event(
                action="retrieval.requested",
                document_id="retrieval",
                actor=request.prompt_key,
                details={
                    "chat_id": request.chat_id,
                    "prompt_version": request.prompt_version,
                    "allowed_scopes": request.allowed_scopes,
                    "top_k": request.top_k,
                    "trace_id": request.trace_id,
                    "result_count": 0,
                },
            )
            return RetrievalResponse(
                success=True,
                index_version="knowledge-index-lexical-v1",
                results=[],
                warnings=warnings,
            )

        eligible_statuses = {
            DocumentStatus.INDEXED,
            DocumentStatus.APPROVED,
            DocumentStatus.ACTIVE,
        }

        # Tokenize query: lowercase, split on whitespace/punctuation
        import re as _re
        query_tokens = [
            token
            for token in _re.split(r"[\s\.,;:!?\"'()\[\]{}/\\]+", request.query.lower())
            if len(token) > 2
        ]
        # Fallback: keep all tokens if none survived the length filter
        if not query_tokens:
            query_tokens = request.query.lower().split()

        scored: list = []

        for document_id, document in self._documents.items():
            if document.status not in eligible_statuses:
                continue
            if not any(scope in document.scopes for scope in request.allowed_scopes):
                continue

            chunks = self._chunks.get(document_id, [])
            for chunk in chunks:
                content_lower = chunk.content.lower()
                match_count = sum(1 for token in query_tokens if token in content_lower)
                if match_count == 0:
                    continue
                score = match_count / len(query_tokens)
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_results = scored[: request.top_k]

        results = []
        for score, chunk in top_results:
            results.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    citation=RetrievalCitation(
                        document_id=chunk.document_id,
                        document_version=chunk.document_version,
                        title=chunk.title,
                        section=chunk.section,
                    ),
                    scores=RetrievalScore(
                        lexical=round(score, 4),
                        final=round(score, 4),
                    ),
                    retrieval_reason="lexical_match",
                )
            )

        if not results:
            warnings.append(
                "No matching chunks found. Verify that documents have been ingested, "
                "their status is active/indexed/approved, and their scopes overlap "
                "with the requested allowed_scopes."
            )

        self._record_audit_event(
            action="retrieval.requested",
            document_id="retrieval",
            actor=request.prompt_key,
            details={
                "chat_id": request.chat_id,
                "prompt_version": request.prompt_version,
                "allowed_scopes": request.allowed_scopes,
                "top_k": request.top_k,
                "trace_id": request.trace_id,
                "result_count": len(results),
            },
        )

        return RetrievalResponse(
            success=True,
            index_version="knowledge-index-lexical-v1",
            results=results,
            warnings=warnings,
        )

    def get_audit_events(self) -> List[dict]:
        """Return lifecycle audit events recorded by this in-memory service."""
        return list(self._audit_events)

    def _record_audit_event(
        self,
        action: str,
        document_id: str,
        actor: Optional[str],
        details: dict,
    ) -> None:
        """Append one audit event to the in-memory audit log."""
        self._audit_events.append(
            {
                "action": action,
                "document_id": document_id,
                "actor": actor,
                "details": details,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
