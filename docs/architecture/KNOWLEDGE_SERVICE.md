# Knowledge Service Architecture

Status: accepted foundation decision. Initial FastAPI scaffold, Admin lifecycle proxy, retrieval contract, and semantic chunking foundation exist in `services/knowledge-service/`.

The Empat.IA RAG system will be implemented as a dedicated `knowledge-service`, not as code embedded inside the `ai-service`. The goal is to make knowledge ingestion, review, indexing, retrieval, provenance, and auditability controllable from the Admin Panel while keeping the AI Service focused on response generation.

## Decision

Create a new internal microservice named `knowledge-service`.

The service owns:

- document ingestion and validation;
- text extraction and normalization;
- semantic chunking;
- chunk quality checks;
- embedding generation or embedding orchestration;
- vector indexing;
- lexical indexing;
- hybrid retrieval;
- local re-ranking;
- document and index versioning;
- source provenance;
- retrieval audit records.

The service does not own:

- end-user authentication;
- admin authentication;
- prompt authoring;
- final LLM response generation;
- therapeutic session lifecycle;
- clinical or diagnostic decisions.

## Why A Dedicated Service

RAG has two very different workloads:

- ingestion path: slow, asynchronous, file-heavy, retryable, and admin-reviewed;
- retrieval path: fast, latency-sensitive, scoped by prompt and chat context.

Keeping both inside the AI Service would make the AI Service responsible for file handling, background jobs, vector search, lexical search, admin status, and generation. That would blur service ownership and make future LLM provider changes riskier.

A dedicated service gives us clean LLMOps boundaries:

- the Admin Panel controls what knowledge is active;
- the Gateway controls auth, permissions, and admin-facing APIs;
- the Knowledge Service controls knowledge state and retrieval;
- the AI Service consumes retrieved context through a stable internal contract.

## Component Ownership

| Component | Responsibility |
|---|---|
| Admin Panel | Upload, review, approve, activate, archive, reindex, inspect chunks, inspect retrieval audits. |
| Gateway Service | Admin auth, authorization, public API shape, request routing, service-to-service calls. |
| Knowledge Service | Document lifecycle, ingestion pipeline, indexes, retrieval, provenance, audit records. |
| AI Service | Builds prompts, calls LLM providers, consumes retrieval output, reports used sources. |
| MongoDB | Document metadata, versions, chunks metadata, ingestion jobs, audit logs. |
| Qdrant | Local-first vector store for chunk embeddings. |
| SQLite FTS5 | Local lexical index for BM25-like search in the first implementation. |
| Redis | Optional queue/cache for ingestion jobs and transient retrieval acceleration. |

## Storage Strategy

Initial local-first storage:

- MongoDB for authoritative metadata and audit records.
- Qdrant for vector similarity search.
- SQLite FTS5 inside the Knowledge Service volume for lexical retrieval.
- Local Docker volume for raw uploaded files and extracted normalized text.

This keeps the system local-first while avoiding MongoDB Atlas-only vector search assumptions. If production needs stronger operational guarantees later, Qdrant and SQLite FTS5 can be replaced by managed vector and search infrastructure behind the same service contract.

## Document Lifecycle

Documents move through explicit states:

```text
draft
awaiting_validation
processing
indexed
approved
active
failed
archived
superseded
```

Only `active` document versions are eligible for retrieval during chat.

No uploaded document should become available to the assistant automatically. An admin must explicitly approve and activate it.

## Ingestion Pipeline

The ingestion pipeline should run asynchronously:

1. Receive upload metadata from the Gateway.
2. Store the raw file in a local/private object store path.
3. Validate file type, size, hash, language, source, and required metadata.
4. Extract text with a parser appropriate to the file type.
5. Normalize text while preserving source boundaries.
6. Detect document structure: title, chapter, section, paragraph, quote blocks, and citations.
7. Produce semantic chunks with stable chunk IDs.
8. Run chunk quality checks.
9. Generate embeddings.
10. Write vector entries to Qdrant.
11. Write lexical entries to SQLite FTS5.
12. Persist document, version, chunk, index, and audit metadata in MongoDB.
13. Expose processing status and warnings to the Admin Panel.

## Chunk Metadata

Each chunk must be traceable without depending on its position in a mutable file.

Minimum metadata:

```json
{
  "chunk_id": "doc_01:v3:chunk_00042",
  "document_id": "doc_01",
  "document_version": 3,
  "source": "uploaded_pdf",
  "source_uri": "private://knowledge/doc_01/v3/source.pdf",
  "title": "On Becoming a Person",
  "section": "Chapter 2 / The Helping Relationship",
  "language": "en",
  "content_hash": "sha256:...",
  "chunk_hash": "sha256:...",
  "ingested_at": "2026-05-04T00:00:00Z",
  "status": "active",
  "quality": {
    "cohesion_score": 0.92,
    "warnings": []
  }
}
```

## Retrieval Contract

The AI Service should not query vector stores directly. It should call the Knowledge Service.

Example request:

```json
{
  "query": "What does Rogers mean by unconditional positive regard?",
  "chat_id": "opaque-chat-id",
  "prompt_key": "therapeutic_chat",
  "prompt_version": 12,
  "allowed_scopes": ["rogerian_theory", "approved_psychoeducation"],
  "language": "en",
  "top_k": 8,
  "trace_id": "trace-123"
}
```

Example response:

```json
{
  "success": true,
  "index_version": "knowledge-index-2026-05-04-001",
  "results": [
    {
      "chunk_id": "doc_01:v3:chunk_00042",
      "content": "Relevant source excerpt...",
      "citation": {
        "document_id": "doc_01",
        "document_version": 3,
        "title": "On Becoming a Person",
        "section": "Chapter 2 / The Helping Relationship"
      },
      "scores": {
        "vector": 0.84,
        "lexical": 0.61,
        "rerank": 0.91,
        "final": 0.88
      },
      "retrieval_reason": "High semantic match with direct terminology overlap."
    }
  ],
  "warnings": []
}
```

## Prompt Control Integration

RAG must be prompt-scoped, not globally enabled.

Prompt metadata should define:

- whether retrieval is enabled;
- allowed knowledge scopes;
- maximum number of chunks;
- minimum retrieval confidence;
- citation requirements;
- fallback behavior when no source is found.

The AI Service should include retrieved context only when the active prompt permits it.

## Admin Control Plane

The Admin Panel should support:

- document upload;
- document metadata editing;
- validation status;
- ingestion status;
- chunk inspection;
- quality warnings;
- approval and activation;
- reindexing;
- version comparison;
- archival and rollback;
- retrieval audit inspection.

The Admin must expose real operational state. It should never silently display mock processing status as if it were production data.

## Audit Requirements

For every response that uses retrieved knowledge, the system should persist:

- `chat_id`;
- `message_id`;
- `trace_id`;
- `prompt_key`;
- `prompt_version`;
- `query`;
- `index_version`;
- retrieved `chunk_id` values;
- document versions used;
- vector, lexical, re-rank, and final scores;
- final selected chunks injected into the prompt;
- whether the response cited sources.

This makes RAG observable and reviewable rather than a hidden behavior inside generation.

## Failure Behavior

The system should degrade safely:

- If retrieval fails, the assistant continues without RAG and does not invent sources.
- If retrieval confidence is low, the assistant should avoid source-backed claims.
- If a document is inactive, archived, failed, or superseded, it must not be retrieved.
- If the Knowledge Service is unavailable, the Gateway and AI Service should emit structured telemetry and continue with non-RAG behavior where safe.

## First Implementation Slice

Recommended implementation order:

1. Scaffold `knowledge-service` with health checks and internal API skeleton.
2. Add Admin/Gateway metadata model for documents and document versions.
3. Add upload and document lifecycle endpoints behind admin auth.
4. Add asynchronous ingestion job model.
5. Implement semantic chunking and chunk metadata.
6. Add Qdrant and SQLite FTS5 indexes.
7. Add retrieval API with hybrid search and placeholder re-ranking.
8. Connect Prompt Control to retrieval permissions.
9. Add retrieval audit records.
10. Add Admin screens for lifecycle, chunks, and audit.

## Open Questions

- Should embeddings run inside Knowledge Service or through an internal embedding worker?
- Which local embedding model should be the default for Portuguese and English content?
- Should raw uploaded files be stored in MongoDB GridFS, a local volume, or an object-storage-compatible service like MinIO?
- What admin roles are needed for upload, approval, activation, and audit review?
- What retention policy applies to obsolete document versions and retrieval audit logs?
