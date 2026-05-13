"""Runtime configuration for the gateway service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceUrls:
    ai: str
    emotion: str
    voice: str
    knowledge: str

    def as_dict(self) -> dict[str, str]:
        return {
            "ai": self.ai,
            "emotion": self.emotion,
            "voice": self.voice,
            "knowledge": self.knowledge,
        }


@dataclass(frozen=True)
class VoiceChunkSettings:
    max_chars: int
    max_wait_ms: int
    min_timed_flush_chars: int
    min_timed_flush_words: int


@dataclass(frozen=True)
class AdminSettings:
    username: str
    password: str
    email: str
    allowed_emails: set[str]


@dataclass(frozen=True)
class Settings:
    service_urls: ServiceUrls
    mongodb_url: str
    mongodb_database: str
    gateway_port: str
    debug: bool
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    admin: AdminSettings
    voice_chunks: VoiceChunkSettings


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _admin_allowed_emails(default_email: str) -> set[str]:
    raw = os.getenv("ADMIN_ALLOWED_EMAILS", default_email)
    return {email.strip().lower() for email in raw.split(",") if email.strip()}


def load_settings() -> Settings:
    admin_email = os.getenv("ADMIN_EMAIL", "admin@empat-ia.io")

    return Settings(
        service_urls=ServiceUrls(
            ai=os.getenv("AI_SERVICE_URL", "http://ai-service:8001"),
            emotion=os.getenv("EMOTION_SERVICE_URL", "http://emotion-service:8003"),
            voice=os.getenv("VOICE_SERVICE_URL", "http://voice-service:8004"),
            knowledge=os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8005"),
        ),
        mongodb_url=os.getenv(
            "MONGODB_URL",
            "mongodb://admin:password@mongodb:27017/empatia?authSource=admin",
        ),
        mongodb_database=os.getenv("MONGODB_DATABASE", os.getenv("DATABASE_NAME", "empatia")),
        gateway_port=os.getenv("GATEWAY_PORT", "8000"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        jwt_secret_key=(
            os.getenv("JWT_SECRET_KEY")
            or os.getenv("SECRET_KEY")
            or "changeme-must-be-at-least-32-characters-long!"
        ),
        jwt_algorithm=os.getenv("ALGORITHM", "HS256"),
        access_token_expire_minutes=_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 10080),
        admin=AdminSettings(
            username=os.getenv("ADMIN_USERNAME", "admin"),
            password=os.getenv("ADMIN_PASSWORD", "admin123"),
            email=admin_email,
            allowed_emails=_admin_allowed_emails(admin_email),
        ),
        voice_chunks=VoiceChunkSettings(
            max_chars=_int_env("VOICE_CHUNK_MAX_CHARS", 220),
            max_wait_ms=_int_env("VOICE_CHUNK_MAX_WAIT_MS", 1400),
            min_timed_flush_chars=_int_env("VOICE_CHUNK_MIN_TIMED_CHARS", 48),
            min_timed_flush_words=_int_env("VOICE_CHUNK_MIN_TIMED_WORDS", 6),
        ),
    )


settings = load_settings()
SERVICE_URLS = settings.service_urls.as_dict()


def get_google_client_id() -> str:
    """Read lazily so deployments can inject the variable after import time."""
    return (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
