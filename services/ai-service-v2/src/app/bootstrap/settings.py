"""Configurações do ai-service-v2."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the unified service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AI_SERVICE_V2_",
        extra="ignore",
    )

    app_name: str = "empatIA Unified AI Service"
    app_slug: str = "ai-service-v2"
    app_version: str = "0.1.0"
    app_description: str = (
        "Boundary temporário da fusão entre gateway-service e ai-service."
    )
    environment: str = "development"
    public_api_prefix: str = "/api"
    admin_api_prefix: str = "/api/admin"
    internal_api_prefix: str = "/internal"
    default_language: str = "pt-BR"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    voice_service_url: str = "http://voice-service:8004"
    emotion_service_url: str = "http://emotion-service:8003"
    knowledge_service_url: str = "http://knowledge-service:8005"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
