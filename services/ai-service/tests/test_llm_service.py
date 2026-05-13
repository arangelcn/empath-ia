import asyncio

from src.services.llm_service import LLMService


class FakePromptClient:
    async def get_system_prompt(self, variables=None):
        return "system"

    async def get_session_analysis_prompt(self, variables=None):
        return "prompt"


def test_generate_session_context_accepts_fenced_json(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    service = LLMService(prompt_client=FakePromptClient())

    async def fake_call_llm(messages, max_tokens=1000, temperature=0.3):
        return {
            "content": """```json
{
  "summary": "Resumo da sessão",
  "main_themes": ["ansiedade no trabalho"],
  "emotional_state": {"initial": "tenso", "final": "mais calmo", "progression": "melhorou"},
  "key_insights": ["O usuário conectou ansiedade a cobranças profissionais"]
}
```"""
        }

    monkeypatch.setattr(service, "_call_llm", fake_call_llm)

    result = asyncio.run(service.generate_session_context("Conversa terapêutica", []))

    assert result["summary"] == "Resumo da sessão"
    assert result["main_themes"] == ["ansiedade no trabalho"]
    assert result["emotional_state"]["final"] == "mais calmo"


def test_openai_compat_base_url_from_completions_url(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_COMPLETIONS_URL", "http://localhost:1234/v1/chat/completions")
    monkeypatch.delenv("OPENAI_COMPAT_API_KEY", raising=False)

    service = LLMService(prompt_client=FakePromptClient())

    assert service.openai_base_url == "http://localhost:1234/v1"
    assert service.effective_api_key == "lm-studio"


def test_openai_base_url_takes_precedence_over_llm_base_url(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "http://host.docker.internal:11434/v1")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    service = LLMService(prompt_client=FakePromptClient())

    assert service.openai_base_url == "https://api.openai.com/v1"
    assert service.effective_api_key is None


def test_openai_model_alias_takes_precedence(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "none")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5-turbo")
    monkeypatch.setenv("MODEL_NAME", "gemma-4-e4b")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    service = LLMService(prompt_client=FakePromptClient())

    assert service.openai_model == "gpt-3.5-turbo"
    assert service.effective_api_key == "lm-studio"


def test_openai_cloud_without_api_key_disables_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.delenv("OPENAI_COMPLETIONS_URL", raising=False)

    service = LLMService(prompt_client=FakePromptClient())

    assert service.effective_api_key is None
    assert service.get_service_status()["openai_available"] is False


def test_active_mode_label_local_openai_compat(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "none")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    service = LLMService(prompt_client=FakePromptClient())

    assert service._active_mode_label() == "LOCAL_OPENAI_COMPAT"


def test_active_mode_label_openai_cloud(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "none")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_ENDPOINT", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    service = LLMService(prompt_client=FakePromptClient())

    assert service._active_mode_label() == "OPENAI_CLOUD"


def test_build_rag_context_uses_retrieve_contract(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    service = LLMService(prompt_client=FakePromptClient())
    captured_payload = {}

    async def fake_retrieve(payload):
        captured_payload.update(payload)
        return {
            "success": True,
            "results": [
                {
                    "chunk_id": "chunk-1",
                    "content": "Unconditional positive regard means acceptance.",
                    "citation": {
                        "document_id": "doc_1",
                        "document_version": 3,
                        "title": "On Becoming a Person",
                        "section": "Chapter 2",
                    },
                    "scores": {"final": 0.91},
                },
                {
                    "chunk_id": "chunk-2",
                    "content": "Low score chunk should be filtered.",
                    "citation": {"document_id": "doc_2", "title": "Discarded Source"},
                    "scores": {"final": 0.1},
                },
            ],
            "warnings": [],
        }

    monkeypatch.setattr(service.rag_client, "retrieve", fake_retrieve)

    rag_block = asyncio.run(
        service._build_rag_context(
            user_message="What is unconditional positive regard?",
            session_id="alice_session-2",
            rag_policy={
                "enabled": True,
                "allowed_scopes": ["rogerian_theory"],
                "top_k": 4,
                "min_confidence": 0.5,
                "require_citations": True,
            },
            prompt_key="therapeutic_chat",
            prompt_version=12,
            chat_id="chat_123",
            trace_id="trace_123",
            rag_language="en",
        )
    )

    assert captured_payload["query"] == "What is unconditional positive regard?"
    assert captured_payload["chat_id"] == "chat_123"
    assert captured_payload["prompt_key"] == "therapeutic_chat"
    assert captured_payload["prompt_version"] == 12
    assert captured_payload["allowed_scopes"] == ["rogerian_theory"]
    assert captured_payload["top_k"] == 4
    assert captured_payload["trace_id"] == "trace_123"
    assert "CONTEXTO RAG APROVADO" in rag_block
    assert "Unconditional positive regard means acceptance." in rag_block
    assert "Low score chunk should be filtered." not in rag_block


def test_build_rag_context_requires_scopes(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "none")
    service = LLMService(prompt_client=FakePromptClient())

    called = {"value": False}

    async def fake_retrieve(payload):
        called["value"] = True
        return {"success": True, "results": [], "warnings": []}

    monkeypatch.setattr(service.rag_client, "retrieve", fake_retrieve)

    rag_block = asyncio.run(
        service._build_rag_context(
            user_message="test",
            session_id="alice_session-2",
            rag_policy={"enabled": True, "allowed_scopes": []},
        )
    )

    assert rag_block == ""
    assert called["value"] is False
