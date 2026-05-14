"""Tests for voice-friendly streaming chunking."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from src.app.application.orchestration.agent_service import AgentService
from src.app.services.streaming_utils import SentenceChunker


class SentenceChunkerTest(unittest.TestCase):
    def test_keeps_colon_inside_sentence(self) -> None:
        chunker = SentenceChunker(max_chars=999, max_wait_ms=9_999)
        chunks = chunker.push(
            "Respire fundo: inspire pelo nariz e solte devagar. Depois me conte como se sente."
        )
        remaining = chunker.flush()
        if remaining:
            chunks.append(remaining)

        self.assertEqual(
            chunks,
            [
                "Respire fundo: inspire pelo nariz e solte devagar.",
                "Depois me conte como se sente.",
            ],
        )

    def test_discards_punctuation_only_fragments(self) -> None:
        chunker = SentenceChunker(max_chars=999, max_wait_ms=9_999)
        chunks = chunker.push("... Tudo bem com voce?")
        remaining = chunker.flush()
        if remaining:
            chunks.append(remaining)

        self.assertEqual(chunks, ["Tudo bem com voce?"])


class AgentServiceChunkSelectionTest(unittest.TestCase):
    def test_rechunks_native_stream_deltas_into_speakable_segments(self) -> None:
        agent = object.__new__(AgentService)
        response_text = "Oi, tudo bem? Posso te ajudar com isso."
        state = SimpleNamespace(generation_result={"text": response_text})

        chunks = agent._select_stream_text_chunks(
            state=state,
            response_text=response_text,
            native_generation_chunks=[
                "Oi",
                ",",
                " tudo",
                " bem",
                "?",
                " Pos",
                "so",
                " te",
                " ajudar",
                " com",
                " isso",
                ".",
            ],
        )

        self.assertEqual(chunks, ["Oi, tudo bem?", "Posso te ajudar com isso."])


if __name__ == "__main__":
    unittest.main()
