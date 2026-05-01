"""Utilities for low-latency voice streaming."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional


SENTENCE_END_RE = re.compile(r"([.!?;:。！？]+)(\s+|$)")


class SentenceChunker:
    """Accumulate token deltas and flush speakable chunks."""

    def __init__(
        self,
        max_chars: int = 220,
        max_wait_ms: int = 700,
        min_timed_flush_chars: int = 48,
        min_timed_flush_words: int = 6,
    ) -> None:
        self.max_chars = max_chars
        self.max_wait_ms = max_wait_ms
        self.min_timed_flush_chars = min_timed_flush_chars
        self.min_timed_flush_words = min_timed_flush_words
        self._buffer = ""
        self._last_flush = time.perf_counter()

    def push(self, text: str) -> List[str]:
        if not text:
            return []

        self._buffer += text
        chunks: List[str] = []

        while True:
            chunk = self._next_sentence()
            if not chunk:
                break
            chunks.append(chunk)

        if len(self._buffer) >= self.max_chars or self._should_timed_flush():
            chunk = self.flush()
            if chunk:
                chunks.append(chunk)

        return chunks

    def flush(self) -> Optional[str]:
        chunk = self._buffer.strip()
        self._buffer = ""
        self._last_flush = time.perf_counter()
        return chunk or None

    def _next_sentence(self) -> Optional[str]:
        match = SENTENCE_END_RE.search(self._buffer)
        if not match:
            return None

        end = match.end()
        chunk = self._buffer[:end].strip()
        self._buffer = self._buffer[end:]
        self._last_flush = time.perf_counter()
        return chunk or None

    def _elapsed_ms(self) -> float:
        return (time.perf_counter() - self._last_flush) * 1000

    def _should_timed_flush(self) -> bool:
        if self._elapsed_ms() < self.max_wait_ms:
            return False

        speakable = self._buffer.strip()
        if len(speakable) < self.min_timed_flush_chars:
            return False

        return len(speakable.split()) >= self.min_timed_flush_words


def sse_event(event: str, data: Dict[str, Any]) -> str:
    """Serialize a Server-Sent Event frame."""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


def now_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
