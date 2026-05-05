import asyncio

from src.services.llm_service import LLMService


class FakePromptClient:
    async def get_session_analysis_prompt(self, variables=None):
        return "prompt"


def test_generate_session_context_accepts_fenced_json(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

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
