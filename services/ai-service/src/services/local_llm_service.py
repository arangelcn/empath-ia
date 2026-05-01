"""Local GGUF model runtime for the AI service."""

import asyncio
import fnmatch
import logging
import os
import shutil
import threading
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)


class LocalLLMService:
    """Lazy loader for a locally served GGUF model using llama.cpp."""

    def __init__(self) -> None:
        self.repo_id = os.getenv("LOCAL_MODbora EL_REPO_ID", "ggml-org/gemma-4-E4B-it-GGUF")
        self.include_pattern = os.getenv("LOCAL_MODEL_INCLUDE", "gemma-4-E4B-it-Q4_K_M.gguf")
        self.model_dir = Path(os.getenv("LOCAL_MODEL_DIR", "/models/local-llm"))
        self.import_dir = Path(os.getenv("LOCAL_MODEL_IMPORT_DIR", "/host-lmstudio-models"))
        self.import_pattern = os.getenv("LOCAL_MODEL_IMPORT_PATTERN", self.include_pattern)
        self.model_path = self._resolve_model_path()
        self.model_name = os.getenv("LOCAL_LLM_MODEL", self.model_path.name if self.model_path else "gemma4:e4b")
        self.chat_format = os.getenv("LOCAL_LLM_CHAT_FORMAT", "").strip()
        self.n_ctx = int(os.getenv("LOCAL_LLM_N_CTX", "8192"))
        self.n_gpu_layers = int(os.getenv("LOCAL_LLM_N_GPU_LAYERS", "-1"))
        self.n_threads = int(os.getenv("LOCAL_LLM_N_THREADS", str(os.cpu_count() or 4)))
        self.verbose = os.getenv("LOCAL_LLM_VERBOSE", "false").lower() == "true"
        self._llm = None
        self._generation_lock = threading.Lock()
        self._load_error: Optional[str] = None
        self._runtime_load_failed = False

    def _resolve_model_path(self) -> Optional[Path]:
        configured_path = os.getenv("LOCAL_LLM_MODEL_PATH")
        if configured_path:
            path = Path(configured_path)
            return path if path.is_file() else None

        gguf_files = sorted(self.model_dir.rglob("*.gguf"))
        return gguf_files[0] if gguf_files else None

    def has_model_file(self) -> bool:
        if self.model_path is None:
            self.model_path = self._resolve_model_path()
        return self.model_path is not None and self.model_path.is_file()

    def is_available(self) -> bool:
        return self.has_model_file() and not self._runtime_load_failed

    def runtime_loadable(self) -> Optional[bool]:
        if self._llm is not None:
            return True
        if self._runtime_load_failed:
            return False
        if not self.has_model_file():
            return False
        return None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def _hf_token(self) -> Optional[str]:
        return (
            os.getenv("HF_TOKEN")
            or os.getenv("HUGGING_FACE_TOKEN")
            or os.getenv("HUGGIN_FACE_TOKEN")
            or None
        )

    def _format_bytes(self, size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{size} B"
            value /= 1024
        return f"{size} B"

    def _find_import_model(self) -> Optional[Path]:
        if not self.import_dir.is_dir():
            logger.info("Local model import directory not found: %s", self.import_dir)
            return None

        patterns = [self.import_pattern, self.include_pattern, "*.gguf"]
        candidates: List[Path] = []
        for pattern in patterns:
            matches = sorted(
                path
                for path in self.import_dir.rglob("*.gguf")
                if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(str(path), pattern)
            )
            candidates.extend(matches)

        unique_candidates = list(dict.fromkeys(candidates))
        if not unique_candidates:
            logger.info(
                "No importable local GGUF model found in %s using pattern %s",
                self.import_dir,
                self.import_pattern,
            )
            return None

        return unique_candidates[0]

    def _copy_import_model_if_available(self) -> bool:
        source = self._find_import_model()
        if source is None:
            return False

        self.model_dir.mkdir(parents=True, exist_ok=True)
        destination = self.model_dir / source.name
        if source.resolve() == destination.resolve():
            self.model_path = destination
            logger.info("Local LLM model already points to import source: %s", destination)
            return True

        size = source.stat().st_size
        temp_destination = destination.with_suffix(destination.suffix + ".tmp")
        logger.info(
            "📦 Copying local LLM model from LM Studio: source=%s target=%s size=%s",
            source,
            destination,
            self._format_bytes(size),
        )
        shutil.copy2(source, temp_destination)
        temp_destination.replace(destination)
        self.model_path = self._resolve_model_path()
        logger.info("📦 Local LLM model copied: %s", self.model_path or destination)
        return self.is_available()

    def ensure_model_available(self, download_if_missing: bool, required: bool) -> bool:
        """Ensure a GGUF model exists locally, importing it before downloading."""
        if self.has_model_file():
            logger.info("Local LLM model already available: %s", self.model_path)
            return True

        try:
            if self._copy_import_model_if_available():
                return True
        except Exception as exc:
            logger.warning(
                "Could not import local LLM model from %s: %s. Runtime will try Hugging Face download.",
                self.import_dir,
                exc,
            )

        if not download_if_missing:
            message = (
                "Local LLM model file was not found and runtime download is disabled. "
                "Set LOCAL_LLM_MODEL_PATH, mount LOCAL_MODEL_IMPORT_DIR, or enable runtime download."
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
        if not self.has_model_file():
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
            "file_available": self.has_model_file(),
            "runtime_loadable": self.runtime_loadable(),
            "load_error": self._load_error,
            "model_name": self.model_name,
            "model_path": str(self.model_path) if self.model_path else None,
            "model_repo_id": self.repo_id,
            "model_include": self.include_pattern,
            "model_dir": str(self.model_dir),
            "model_import_dir": str(self.import_dir),
            "model_import_pattern": self.import_pattern,
            "chat_format": self.chat_format or "auto",
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
            "n_threads": self.n_threads,
        }

    def _load_model(self):
        if self._llm is not None:
            return self._llm

        if not self.has_model_file():
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
        try:
            self._llm = Llama(**llama_kwargs)
        except Exception as exc:
            self._llm = None
            self._load_error = str(exc)
            self._runtime_load_failed = True
            raise

        self._load_error = None
        self._runtime_load_failed = False
        return self._llm

    def _uses_gemma_chat_template(self) -> bool:
        model_identity = " ".join(
            [
                self.model_name or "",
                self.repo_id or "",
                str(self.model_path or ""),
            ]
        ).lower()
        return "gemma" in model_identity

    def _prepare_messages_for_model(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Adapt chat messages for model families with limited role support."""
        normalized_messages: List[Dict[str, str]] = []
        system_chunks: List[str] = []

        for message in messages:
            role = message.get("role", "user")
            content = (message.get("content") or "").strip()
            if not content:
                continue

            if self._uses_gemma_chat_template() and role == "system":
                system_chunks.append(content)
                continue

            normalized_messages.append({"role": role, "content": content})

        if not system_chunks:
            return normalized_messages

        system_instructions = "\n\n".join(system_chunks)
        prefixed_content = (
            "INSTRUÇÕES DE COMPORTAMENTO PARA TODA A CONVERSA:\n"
            f"{system_instructions}\n\n"
            "MENSAGEM DO USUÁRIO:\n"
        )

        for index, message in enumerate(normalized_messages):
            if message["role"] == "user":
                normalized_messages[index] = {
                    "role": "user",
                    "content": f"{prefixed_content}{message['content']}",
                }
                return normalized_messages

        return [{"role": "user", "content": system_instructions}]

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
        with self._generation_lock:
            llm = self._load_model()
            prepared_messages = self._prepare_messages_for_model(messages)
            response = llm.create_chat_completion(
                messages=prepared_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        choices = response.get("choices", [])
        if not choices:
            return None

        message = choices[0].get("message", {})
        content = message.get("content", "")
        return content.strip() if content else None

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """Generate chat response deltas from the local model."""
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()
        sentinel = object()
        stop_event = threading.Event()

        def _emit(item: object) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, item)

        def _worker() -> None:
            try:
                with self._generation_lock:
                    llm = self._load_model()
                    prepared_messages = self._prepare_messages_for_model(messages)
                    stream = llm.create_chat_completion(
                        messages=prepared_messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=True,
                    )

                    for chunk in stream:
                        if stop_event.is_set():
                            break
                        delta = self._extract_stream_delta(chunk)
                        if delta:
                            _emit(delta)
            except Exception as exc:
                logger.error("❌ Local LLM streaming failed: %s", exc, exc_info=True)
                _emit(exc)
            finally:
                _emit(sentinel)

        thread = threading.Thread(target=_worker, name="local-llm-stream", daemon=True)
        thread.start()

        try:
            while True:
                item = await queue.get()
                if item is sentinel:
                    break
                if isinstance(item, Exception):
                    raise item
                yield str(item)
        finally:
            stop_event.set()

    def _extract_stream_delta(self, chunk: object) -> str:
        """Extract text delta from llama-cpp-python OpenAI-compatible chunks."""
        if not isinstance(chunk, dict):
            return ""

        choices = chunk.get("choices") or []
        if not choices:
            return ""

        choice = choices[0] or {}
        delta = choice.get("delta") or {}
        if isinstance(delta, dict):
            content = delta.get("content")
            if content:
                return str(content)

        text = choice.get("text")
        if text:
            return str(text)

        message = choice.get("message") or {}
        if isinstance(message, dict):
            content = message.get("content")
            if content:
                return str(content)

        return ""
