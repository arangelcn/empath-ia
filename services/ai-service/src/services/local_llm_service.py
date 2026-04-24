"""Local GGUF model runtime for the AI service."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalLLMService:
    """Lazy loader for a locally served GGUF model using llama.cpp."""

    def __init__(self) -> None:
        self.model_path = self._resolve_model_path()
        self.model_name = os.getenv("LOCAL_LLM_MODEL", self.model_path.name if self.model_path else "local-llm")
        self.chat_format = os.getenv("LOCAL_LLM_CHAT_FORMAT", "gemma")
        self.n_ctx = int(os.getenv("LOCAL_LLM_N_CTX", "8192"))
        self.n_gpu_layers = int(os.getenv("LOCAL_LLM_N_GPU_LAYERS", "-1"))
        self.n_threads = int(os.getenv("LOCAL_LLM_N_THREADS", str(os.cpu_count() or 4)))
        self.verbose = os.getenv("LOCAL_LLM_VERBOSE", "false").lower() == "true"
        self._llm = None

    def _resolve_model_path(self) -> Optional[Path]:
        configured_path = os.getenv("LOCAL_LLM_MODEL_PATH")
        if configured_path:
            path = Path(configured_path)
            return path if path.is_file() else None

        model_dir = Path(os.getenv("LOCAL_MODEL_DIR", "/models/local-llm"))
        gguf_files = sorted(model_dir.rglob("*.gguf"))
        return gguf_files[0] if gguf_files else None

    def is_available(self) -> bool:
        return self.model_path is not None and self.model_path.is_file()

    def status(self) -> Dict[str, object]:
        return {
            "available": self.is_available(),
            "model_name": self.model_name,
            "model_path": str(self.model_path) if self.model_path else None,
            "chat_format": self.chat_format,
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
            "n_threads": self.n_threads,
        }

    def _load_model(self):
        if self._llm is not None:
            return self._llm

        if not self.is_available():
            raise RuntimeError(
                "Local LLM model file was not found. Set LOCAL_LLM_MODEL_PATH or build with ENABLE_LOCAL_LLM=true."
            )

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed. Build the AI service with ENABLE_LOCAL_LLM=true."
            ) from exc

        logger.info("Loading local LLM model: %s", self.model_path)
        self._llm = Llama(
            model_path=str(self.model_path),
            n_ctx=self.n_ctx,
            n_gpu_layers=self.n_gpu_layers,
            n_threads=self.n_threads,
            chat_format=self.chat_format,
            verbose=self.verbose,
        )
        return self._llm

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Optional[str]:
        """Generate a chat response from the local model."""
        return await asyncio.to_thread(
            self._generate_sync,
            messages,
            max_tokens,
            temperature,
        )

    def _generate_sync(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Optional[str]:
        llm = self._load_model()
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        choices = response.get("choices", [])
        if not choices:
            return None

        message = choices[0].get("message", {})
        content = message.get("content", "")
        return content.strip() if content else None
