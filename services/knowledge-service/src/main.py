"""Knowledge Service entrypoint.

This service will own the RAG control plane and retrieval pipeline for Empat.IA.
The first slice exposes stable lifecycle and retrieval contracts before adding
MongoDB persistence, Qdrant vector search, and SQLite FTS5 lexical search.
"""

import logging
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.knowledge_routes import router as knowledge_router
from .models.knowledge import ServiceHealth


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

SERVICE_VERSION = "0.1.0"


app = FastAPI(
    title="empatIA Knowledge Service",
    description="Document lifecycle, RAG retrieval contracts, and provenance for Empat.IA.",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(knowledge_router)


@app.get("/")
async def root():
    """Return basic service metadata for humans and smoke tests."""
    return {
        "message": "empatIA Knowledge Service",
        "description": "RAG control plane and retrieval service",
        "version": SERVICE_VERSION,
        "docs": "/docs",
    }


@app.get("/health", response_model=ServiceHealth)
async def health_check():
    """Return health information for Gateway and Admin status pages."""
    return ServiceHealth(
        status="healthy",
        service="knowledge-service",
        version=SERVICE_VERSION,
        storage=os.getenv("KNOWLEDGE_STORAGE_BACKEND", "in-memory"),
        vector_store=os.getenv("QDRANT_URL", "not-configured"),
        lexical_index=os.getenv("KNOWLEDGE_LEXICAL_INDEX", "sqlite-fts5-planned"),
    )


@app.get("/version")
async def version():
    """Return build/version metadata for operational diagnostics."""
    return {
        "service": "knowledge-service",
        "version": SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }
