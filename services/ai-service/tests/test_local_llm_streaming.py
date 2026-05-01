import asyncio
from pathlib import Path

from src.services.local_llm_service import LocalLLMService


class FakeLocalLLMService(LocalLLMService):
    def __init__(self):
        super().__init__()
        self.model_path = Path("/tmp/fake.gguf")

    def has_model_file(self) -> bool:
        return True

    def _load_model(self):
        class FakeLlama:
            def create_chat_completion(self, **kwargs):
                assert kwargs["stream"] is True
                yield {"choices": [{"delta": {"content": "Olá"}}]}
                yield {"choices": [{"delta": {"content": ", Toni"}}]}
                yield {"choices": [{"delta": {}}]}

        return FakeLlama()


def test_local_llm_generate_stream_emits_deltas():
    async def collect():
        service = FakeLocalLLMService()
        chunks = []
        async for chunk in service.generate_stream(
            messages=[{"role": "user", "content": "oi"}],
            max_tokens=32,
            temperature=0.3,
        ):
            chunks.append(chunk)
        return chunks

    assert asyncio.run(collect()) == ["Olá", ", Toni"]


def test_extract_stream_delta_supports_llama_shapes():
    service = FakeLocalLLMService()

    assert service._extract_stream_delta({"choices": [{"delta": {"content": "a"}}]}) == "a"
    assert service._extract_stream_delta({"choices": [{"text": "b"}]}) == "b"
    assert service._extract_stream_delta({"choices": [{"message": {"content": "c"}}]}) == "c"
