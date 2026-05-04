from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_health_check_reports_foundation_dependencies():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "knowledge-service"
    assert body["storage"] == "in-memory"


def test_document_lifecycle_registers_and_updates_document():
    create_response = client.post(
        "/api/v1/documents",
        json={
            "title": "Rogers Source",
            "source": "upload",
            "language": "en",
            "tags": ["rogerian"],
            "scopes": ["rogerian_theory"],
            "created_by": "admin@example.com",
        },
    )

    assert create_response.status_code == 200
    document = create_response.json()["data"]
    assert document["status"] == "draft"

    update_response = client.patch(
        f"/api/v1/documents/{document['document_id']}/status",
        json={
            "status": "awaiting_validation",
            "updated_by": "admin@example.com",
            "reason": "Ready for ingestion checks.",
        },
    )

    assert update_response.status_code == 200
    updated_document = update_response.json()["data"]
    assert updated_document["status"] == "awaiting_validation"


def test_retrieval_contract_is_available_before_indexing():
    response = client.post(
        "/api/v1/retrieve",
        json={
            "query": "unconditional positive regard",
            "prompt_key": "therapeutic_chat",
            "prompt_version": 1,
            "allowed_scopes": ["rogerian_theory"],
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["results"] == []
    assert body["warnings"]


def test_content_ingestion_generates_traceable_chunks():
    create_response = client.post(
        "/api/v1/documents",
        json={
            "title": "Chunking Source",
            "source": "manual",
            "content_type": "markdown",
            "language": "en",
            "scopes": ["rogerian_theory"],
        },
    )
    document = create_response.json()["data"]

    ingest_response = client.post(
        f"/api/v1/documents/{document['document_id']}/content",
        json={
            "content": "# Chapter 1\n\nThis is a coherent paragraph about empathy. "
            "It should remain together as a meaningful unit.\n\n"
            "This is another paragraph about reflection and non-directive support.",
            "content_type": "markdown",
            "ingested_by": "admin@example.com",
        },
    )

    assert ingest_response.status_code == 200
    indexed_document = ingest_response.json()["data"]
    assert indexed_document["status"] == "indexed"
    assert indexed_document["chunk_count"] >= 1
    assert indexed_document["content_hash"].startswith("sha256:")

    chunks_response = client.get(f"/api/v1/documents/{document['document_id']}/chunks")
    chunks = chunks_response.json()["data"]["chunks"]
    assert chunks[0]["document_id"] == document["document_id"]
    assert chunks[0]["chunk_hash"].startswith("sha256:")
    assert "cohesion_score" in chunks[0]["quality"]
