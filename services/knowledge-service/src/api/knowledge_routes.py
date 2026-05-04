"""HTTP routes for document lifecycle and retrieval contracts."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models.knowledge import (
    DocumentStatus,
    DocumentStatusUpdate,
    DocumentContentIngest,
    KnowledgeDocumentCreate,
    RetrievalRequest,
)
from ..services.document_service import KnowledgeDocumentService


router = APIRouter(prefix="/api/v1", tags=["Knowledge"])
document_service = KnowledgeDocumentService()


@router.post("/documents")
async def create_document(request: KnowledgeDocumentCreate):
    """Register a knowledge document in draft state."""
    document = document_service.create_document(request)
    return {"success": True, "data": document}


@router.get("/documents")
async def list_documents(
    status: Optional[DocumentStatus] = Query(default=None),
    scope: Optional[str] = Query(default=None),
):
    """List registered documents, optionally filtered by status or scope."""
    documents = document_service.list_documents(status=status, scope=scope)
    return {"success": True, "data": {"documents": documents, "total": len(documents)}}


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Return one registered document by its stable document ID."""
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "data": document}


@router.post("/documents/{document_id}/content")
async def ingest_document_content(document_id: str, request: DocumentContentIngest):
    """Attach extracted text to a document and generate semantic chunks."""
    document = document_service.ingest_document_content(document_id, request)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "data": document}


@router.get("/documents/{document_id}/chunks")
async def list_document_chunks(document_id: str):
    """Return semantic chunks produced for a document."""
    chunks = document_service.list_chunks(document_id)
    if chunks is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "data": {"chunks": chunks, "total": len(chunks)}}


@router.patch("/documents/{document_id}/status")
async def update_document_status(document_id: str, request: DocumentStatusUpdate):
    """Move a document through its Admin-controlled lifecycle."""
    document = document_service.update_document_status(document_id, request)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "data": document}


@router.post("/retrieve")
async def retrieve_knowledge(request: RetrievalRequest):
    """Retrieve prompt-scoped knowledge chunks for the AI Service."""
    response = document_service.retrieve(request)
    return response


@router.get("/audit/events")
async def list_audit_events():
    """Return document lifecycle audit events for Admin inspection."""
    return {"success": True, "data": {"events": document_service.get_audit_events()}}
