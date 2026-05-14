"""Admin routes that proxy Knowledge Service operations."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ...bootstrap.dependencies import AppContainer, get_container
from ..security import require_admin_permission


router = APIRouter(
    prefix="/api/admin",
    tags=["admin-knowledge"],
    dependencies=[Depends(require_admin_permission("read"))],
)


class KnowledgeDocumentCreateRequest(BaseModel):
    title: str
    source: str
    source_uri: str | None = None
    content_type: str = "txt"
    language: str = "en"
    tags: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    review_policy: str | None = None
    created_by: str | None = None


class KnowledgeDocumentStatusUpdateRequest(BaseModel):
    status: str
    updated_by: str | None = None
    reason: str | None = None


class KnowledgeDocumentContentRequest(BaseModel):
    content: str
    content_type: str = "txt"
    section: str | None = None
    ingested_by: str | None = None


class KnowledgeRetrievalRequest(BaseModel):
    query: str
    chat_id: str | None = None
    prompt_key: str | None = None
    prompt_version: int | None = None
    allowed_scopes: list[str] = Field(default_factory=list)
    language: str | None = None
    top_k: int = Field(default=6, ge=1, le=20)
    trace_id: str | None = None


async def _call_knowledge_service(container: AppContainer, method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.request(method, f"{container.settings.knowledge_service_url}{path}", **kwargs)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Knowledge Service indisponivel: {exc}") from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/knowledge/documents")
async def list_knowledge_documents(
    status: str | None = None,
    scope: str | None = None,
    container: AppContainer = Depends(get_container),
):
    params = {}
    if status:
        params["status"] = status
    if scope:
        params["scope"] = scope
    return await _call_knowledge_service(container, "GET", "/api/v1/documents", params=params)


@router.post("/knowledge/documents", dependencies=[Depends(require_admin_permission("write"))])
async def create_knowledge_document(
    request: KnowledgeDocumentCreateRequest,
    container: AppContainer = Depends(get_container),
):
    return await _call_knowledge_service(container, "POST", "/api/v1/documents", json=request.model_dump())


@router.get("/knowledge/documents/{document_id}")
async def get_knowledge_document(document_id: str, container: AppContainer = Depends(get_container)):
    return await _call_knowledge_service(container, "GET", f"/api/v1/documents/{document_id}")


@router.post("/knowledge/documents/{document_id}/content", dependencies=[Depends(require_admin_permission("write"))])
async def ingest_knowledge_document_content(
    document_id: str,
    request: KnowledgeDocumentContentRequest,
    container: AppContainer = Depends(get_container),
):
    return await _call_knowledge_service(container, "POST", f"/api/v1/documents/{document_id}/content", json=request.model_dump())


@router.get("/knowledge/documents/{document_id}/chunks")
async def list_knowledge_document_chunks(document_id: str, container: AppContainer = Depends(get_container)):
    return await _call_knowledge_service(container, "GET", f"/api/v1/documents/{document_id}/chunks")


@router.patch("/knowledge/documents/{document_id}/status", dependencies=[Depends(require_admin_permission("write"))])
async def update_knowledge_document_status(
    document_id: str,
    request: KnowledgeDocumentStatusUpdateRequest,
    container: AppContainer = Depends(get_container),
):
    return await _call_knowledge_service(container, "PATCH", f"/api/v1/documents/{document_id}/status", json=request.model_dump())


@router.get("/knowledge/audit/events")
async def list_knowledge_audit_events(container: AppContainer = Depends(get_container)):
    return await _call_knowledge_service(container, "GET", "/api/v1/audit/events")


@router.post("/knowledge/retrieve", dependencies=[Depends(require_admin_permission("write"))])
async def retrieve_knowledge_for_admin(
    request: KnowledgeRetrievalRequest,
    container: AppContainer = Depends(get_container),
):
    return await _call_knowledge_service(container, "POST", "/api/v1/retrieve", json=request.model_dump())


@router.post("/knowledge/documents/{document_id}/upload", dependencies=[Depends(require_admin_permission("write"))])
async def upload_knowledge_document_file(
    document_id: str,
    container: AppContainer = Depends(get_container),
    file: UploadFile = File(...),
    section: str | None = Form(default=None),
    ingested_by: str | None = Form(default=None),
):
    file_bytes = await file.read()
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{container.settings.knowledge_service_url}/api/v1/documents/{document_id}/upload",
                files={"file": (file.filename, file_bytes, file.content_type)},
                data={"section": section or "", "ingested_by": ingested_by or ""},
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Knowledge Service indisponivel: {exc}") from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
