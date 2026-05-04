# Knowledge Service

The Knowledge Service is the foundation for Empat.IA's Admin-controlled RAG system.

It owns the knowledge lifecycle:

- document registration;
- document lifecycle status;
- future ingestion jobs;
- future semantic chunking;
- future vector and lexical indexes;
- future retrieval audit records.

The first implementation intentionally uses an in-memory store. This lets the service expose stable contracts before MongoDB persistence, Qdrant vector indexing, and SQLite FTS5 lexical search are added.

## Local Endpoints

```http
GET  /health
GET  /api/v1/documents
POST /api/v1/documents
GET  /api/v1/documents/{document_id}
POST /api/v1/documents/{document_id}/content
GET  /api/v1/documents/{document_id}/chunks
PATCH /api/v1/documents/{document_id}/status
POST /api/v1/retrieve
GET  /api/v1/audit/events
```

## Learning Notes

- `models/knowledge.py` defines the API contract with Pydantic models.
- `services/chunking_service.py` wraps LangChain's `RecursiveCharacterTextSplitter` and adds traceable metadata.
- `services/document_service.py` contains business rules and lifecycle operations.
- `api/knowledge_routes.py` maps HTTP routes to service methods.
- `main.py` creates the FastAPI app and service health endpoints.

This separation keeps endpoint code thin and makes the business logic easier to test.
