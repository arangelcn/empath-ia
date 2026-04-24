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
        self.repo_id = os.getenv("LOCAL_MODEL_REPO_ID", "ggml-org/gemma-4-E4B-it-GGUF")
        self.include_pattern = os.getenv("LOCAL_MODEL_INCLUDE", "gemma-4-E4B-it-Q4_K_M.gguf")
        self.model_dir = Path(os.getenv("LOCAL_MODEL_DIR", "/models/local-llm"))
        self.model_path = self._resolve_model_path()
        self.model_name = os.getenv("LOCAL_LLM_MODEL", self.model_path.name if self.model_path else "gemma4:e4b")
        self.chat_format = os.getenv("LOCAL_LLM_CHAT_FORMAT", "").strip()
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

        gguf_files = sorted(self.model_dir.rglob("*.gguf"))
        return gguf_files[0] if gguf_files else None

    def is_available(self) -> bool:
        if self.model_path is None:
            self.model_path = self._resolve_model_path()
        return self.model_path is not None and self.model_path.is_file()

    def _hf_token(self) -> Optional[str]:
        return (
            os.getenv("HF_TOKEN")
            or os.getenv("HUGGING_FACE_TOKEN")
            or os.getenv("HUGGIN_FACE_TOKEN")
            or None
        )

    def ensure_model_available(self, download_if_missing: bool, required: bool) -> bool:
        """Ensure a GGUF model exists locally, optionally downloading it at runtime."""
        if self.is_available():
            logger.info("Local LLM model already available: %s", self.model_path)
            return True

        if not download_if_missing:
            message = (
                "Local LLM model file was not found and runtime download is disabled. "
                "Set ENABLE_LOCAL_LLM=true or provide LOCAL_LLM_MODEL_PATH."
            )
            if required:
                raise RuntimeError(message)
            logger.warning(message)
            return False

        self.model_dir.mkdir(parents=True, exist_ok=True)
        token = self._hf_token()
        logger.info("⬇️ Local LLM download starting")
        logger.info(
            "⬇️ Local LLM download details: repo=%s include=%s target=%s token=%s required=%s",
            self.repo_id,
            self.include_pattern,
            self.model_dir,
            "configured" if token else "not configured",
            required,
        )
        logger.info("⬇️ Hugging Face download progress will be printed below while the GGUF is fetched")

        try:
            from huggingface_hub import snapshot_download
            from huggingface_hub.errors import GatedRepoError
        except ImportError as exc:
            message = (
                "huggingface_hub is not installed. Build the AI service with ENABLE_LOCAL_LLM=true "
                "to enable runtime model downloads."
            )
            if required:
                raise RuntimeError(message) from exc
            logger.warning("%s Runtime can fall back to another provider.", message)
            return False

        try:
            snapshot_download(
                repo_id=self.repo_id,
                allow_patterns=[self.include_pattern],
                local_dir=str(self.model_dir),
                local_dir_use_symlinks=False,
                token=token,
            )
        except GatedRepoError as exc:
            message = (
                "Cannot download the configured gated Hugging Face model. "
                f"Request and accept access for {self.repo_id}, then restart ai-service. "
                "You can also set LOCAL_MODEL_REPO_ID to an accessible GGUF repository."
            )
            if required:
                raise RuntimeError(message) from exc
            logger.warning("%s Runtime will fall back to another provider.", message)
            return False
        except Exception as exc:
            message = f"Local LLM model download failed: {exc}"
            if required:
                raise RuntimeError(message) from exc
            logger.warning("%s Runtime will fall back to another provider.", message)
            return False

        self.model_path = self._resolve_model_path()
        if not self.is_available():
            message = f"No GGUF files found after download in {self.model_dir}"
            if required:
                raise RuntimeError(message)
            logger.warning(message)
            return False

        logger.info("Local LLM model downloaded: %s", self.model_path)
        return True

    def status(self) -> Dict[str, object]:
        return {
            "available": self.is_available(),
            "model_name": self.model_name,
            "model_path": str(self.model_path) if self.model_path else None,
            "model_repo_id": self.repo_id,
            "model_include": self.include_pattern,
            "model_dir": str(self.model_dir),
            "chat_format": self.chat_format or "auto",
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
        llama_kwargs = {
            "model_path": str(self.model_path),
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
            "n_threads": self.n_threads,
            "verbose": self.verbose,
        }
        if self.chat_format:
            llama_kwargs["chat_format"] = self.chat_format
        self._llm = Llama(**llama_kwargs)
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
