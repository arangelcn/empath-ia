"""Admin routes that proxy Knowledge Service operations."""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..config import SERVICE_URLS
from .auth import require_admin_permission


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin", "Knowledge"],
    dependencies=[Depends(require_admin_permission("read"))],
)


class KnowledgeDocumentCreateRequest(BaseModel):
    title: str
    source: str
    source_uri: Optional[str] = None
    content_type: str = "txt"
    language: str = "en"
    tags: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    review_policy: Optional[str] = None
    created_by: Optional[str] = None


class KnowledgeDocumentStatusUpdateRequest(BaseModel):
    status: str
    updated_by: Optional[str] = None
    reason: Optional[str] = None


class KnowledgeDocumentContentRequest(BaseModel):
    content: str
    content_type: str = "txt"
    section: Optional[str] = None
    ingested_by: Optional[str] = None


class KnowledgeRetrievalRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    prompt_key: Optional[str] = None
    prompt_version: Optional[int] = None
    allowed_scopes: list[str] = Field(default_factory=list)
    language: Optional[str] = None
    top_k: int = Field(default=6, ge=1, le=20)
    trace_id: Optional[str] = None


async def _call_knowledge_service(method: str, path: str, **kwargs):
    """Forward an Admin request to the internal Knowledge Service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(method, f"{SERVICE_URLS['knowledge']}{path}", **kwargs)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Knowledge Service indisponível: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()


@router.get("/knowledge/documents")
async def list_knowledge_documents(
    status: Optional[str] = None,
    scope: Optional[str] = None,
):
    """List Knowledge Service documents through the protected Admin API."""
    params = {}
    if status:
        params["status"] = status
    if scope:
        params["scope"] = scope
    return await _call_knowledge_service("GET", "/api/v1/documents", params=params)


@router.post("/knowledge/documents", dependencies=[Depends(require_admin_permission("write"))])
async def create_knowledge_document(request: KnowledgeDocumentCreateRequest):
    """Register a Knowledge Service document through the protected Admin API."""
    return await _call_knowledge_service("POST", "/api/v1/documents", json=request.model_dump())


@router.get("/knowledge/documents/{document_id}")
async def get_knowledge_document(document_id: str):
    """Fetch one Knowledge Service document through the protected Admin API."""
    return await _call_knowledge_service("GET", f"/api/v1/documents/{document_id}")


@router.post("/knowledge/documents/{document_id}/content", dependencies=[Depends(require_admin_permission("write"))])
async def ingest_knowledge_document_content(
    document_id: str,
    request: KnowledgeDocumentContentRequest,
):
    """Ingest extracted document text and generate chunks through the Admin API."""
    return await _call_knowledge_service(
        "POST",
        f"/api/v1/documents/{document_id}/content",
        json=request.model_dump(),
    )


@router.get("/knowledge/documents/{document_id}/chunks")
async def list_knowledge_document_chunks(document_id: str):
    """List generated Knowledge Service chunks through the protected Admin API."""
    return await _call_knowledge_service("GET", f"/api/v1/documents/{document_id}/chunks")


@router.patch("/knowledge/documents/{document_id}/status", dependencies=[Depends(require_admin_permission("write"))])
async def update_knowledge_document_status(
    document_id: str,
    request: KnowledgeDocumentStatusUpdateRequest,
):
    """Update a Knowledge Service document status through the protected Admin API."""
    return await _call_knowledge_service(
        "PATCH",
        f"/api/v1/documents/{document_id}/status",
        json=request.model_dump(),
    )


@router.get("/knowledge/audit/events")
async def list_knowledge_audit_events():
    """List Knowledge Service audit events through the protected Admin API."""
    return await _call_knowledge_service("GET", "/api/v1/audit/events")


@router.post("/knowledge/retrieve", dependencies=[Depends(require_admin_permission("write"))])
async def retrieve_knowledge_for_admin(request: KnowledgeRetrievalRequest):
    """Exercise the Knowledge retrieval contract through the protected Admin API."""
    return await _call_knowledge_service("POST", "/api/v1/retrieve", json=request.model_dump())


@router.post("/knowledge/documents/{document_id}/upload", dependencies=[Depends(require_admin_permission("write"))])
async def upload_knowledge_document_file(
    document_id: str,
    file: UploadFile = File(...),
    section: Optional[str] = Form(default=None),
    ingested_by: Optional[str] = Form(default=None),
):
    """Upload one raw file and forward it to the Knowledge Service extraction route."""
    file_bytes = await file.read()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['knowledge']}/api/v1/documents/{document_id}/upload",
                files={"file": (file.filename, file_bytes, file.content_type)},
                data={
                    "section": section or "",
                    "ingested_by": ingested_by or "",
                },
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Knowledge Service indisponível: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()
