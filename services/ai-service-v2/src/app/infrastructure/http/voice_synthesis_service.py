"""Voice Service client helpers for batch and streaming synthesis."""

from __future__ import annotations

import base64
import logging
from typing import Any, AsyncGenerator

import httpx

from ...services.streaming_utils import now_ms


logger = logging.getLogger(__name__)


class VoiceSynthesisService:
    """Small client for Voice Service synthesis endpoints."""

    def __init__(self, base_voice_url: str) -> None:
        self.base_voice_url = base_voice_url.rstrip("/")

    async def generate_audio(
        self,
        text: str,
        voice: str,
        is_voice_mode: bool = False,
    ) -> str | None:
        """Generate batch audio through the Voice Service."""
        try:
            timeout_seconds = 30.0 if is_voice_mode else 45.0
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_voice_url}/api/v1/synthesize",
                    json={
                        "text": text,
                        "voice_name": voice,
                        "speaking_rate": 1.1 if is_voice_mode else 1.0,
                    },
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("audio_url"):
                        return self.gateway_audio_url(data["audio_url"])
        except Exception as exc:
            logger.warning("Falha ao gerar audio no voice-service: %s", exc)
        return None

    def gateway_audio_url(self, audio_url: str) -> str:
        """Return the browser-safe proxy URL path."""
        if audio_url and "/api/v1/audio/" in audio_url:
            filename = audio_url.split("/api/v1/audio/")[-1]
            return f"/api/voice/audio/{filename}"
        return audio_url

    async def stream_tts_chunk(
        self,
        text: str,
        voice: str,
        trace_id: str,
        sequence: int,
        started_at: float,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Call the Voice Service streaming endpoint and emit base64 PCM chunks."""
        if not text.strip():
            return

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_voice_url}/api/v1/synthesize-stream",
                    json={
                        "text": text,
                        "voice_name": voice,
                        "language_code": "pt-BR",
                    },
                ) as response:
                    if response.status_code != 200:
                        detail = (await response.aread()).decode("utf-8", errors="ignore")
                        logger.warning("Voice streaming indisponivel: HTTP %s %s", response.status_code, detail)
                        yield {
                            "event": "error",
                            "data": {
                                "trace_id": trace_id,
                                "stage": "tts_stream",
                                "error": f"voice_stream_http_{response.status_code}",
                                "recoverable": True,
                            },
                        }
                        return

                    sample_rate = int(response.headers.get("X-Audio-Sample-Rate", "24000"))
                    encoding = response.headers.get("X-Audio-Encoding", "PCM")
                    chunk_sequence = sequence
                    async for chunk in response.aiter_bytes():
                        if not chunk:
                            continue
                        yield {
                            "event": "audio_chunk",
                            "data": {
                                "trace_id": trace_id,
                                "sequence": chunk_sequence,
                                "audio": base64.b64encode(chunk).decode("ascii"),
                                "sample_rate_hz": sample_rate,
                                "encoding": encoding,
                                "elapsed_ms": now_ms(started_at),
                            },
                        }
                        chunk_sequence += 1
        except Exception as exc:
            logger.warning("Falha no streaming TTS: %s", exc)
            yield {
                "event": "error",
                "data": {
                    "trace_id": trace_id,
                    "stage": "tts_stream",
                    "error": str(exc),
                    "recoverable": True,
                },
            }
