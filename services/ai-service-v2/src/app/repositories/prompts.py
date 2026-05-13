"""Prompt repository contracts and file-backed implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..domain.prompts.models import PromptDescriptor


class PromptRepository(Protocol):
    """Persistence contract for prompt definitions."""

    async def get_active(self, prompt_key: str) -> PromptDescriptor | None:
        """Fetch the active prompt descriptor for a key."""


class FilePromptRepository:
    """Load canonical prompt definitions from ``src/prompts``."""

    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = prompts_dir
        self._index = {
            "system_rogers": "system_rogers.txt",
            "voice_short_response": "voice_short_response.txt",
        }

    async def get_active(self, prompt_key: str) -> PromptDescriptor | None:
        """Load one prompt from disk when available."""
        filename = self._index.get(prompt_key)
        if filename is None:
            return None

        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            return None

        return PromptDescriptor(
            prompt_key=prompt_key,
            version=1,
            content=prompt_path.read_text(encoding="utf-8").strip(),
            source=f"file:{prompt_path.name}",
        )
