import asyncio

from src.services.llm_service import LLMService


class FakePromptClient:
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
