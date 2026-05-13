"""Configurações do ai-service-v2."""

from functools import lru_cache

from pydantic import AliasChoices, Field
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
    legacy_ai_service_url: str = Field(
        default="http://ai-service:8001",
        validation_alias=AliasChoices("AI_SERVICE_V2_LEGACY_AI_SERVICE_URL", "AI_SERVICE_URL"),
    )
    voice_service_url: str = Field(
        default="http://voice-service:8004",
        validation_alias=AliasChoices("AI_SERVICE_V2_VOICE_SERVICE_URL", "VOICE_SERVICE_URL"),
    )
    emotion_service_url: str = Field(
        default="http://emotion-service:8003",
        validation_alias=AliasChoices("AI_SERVICE_V2_EMOTION_SERVICE_URL", "EMOTION_SERVICE_URL"),
    )
    knowledge_service_url: str = Field(
        default="http://knowledge-service:8005",
        validation_alias=AliasChoices("AI_SERVICE_V2_KNOWLEDGE_SERVICE_URL", "KNOWLEDGE_SERVICE_URL"),
    )
    mongodb_url: str = Field(
        default="mongodb://admin:password@mongodb:27017/empatia?authSource=admin",
        validation_alias=AliasChoices("AI_SERVICE_V2_MONGODB_URL", "MONGODB_URL"),
    )
    mongodb_database: str = Field(
        default="empatia",
        validation_alias=AliasChoices("AI_SERVICE_V2_MONGODB_DATABASE", "MONGODB_DATABASE", "DATABASE_NAME"),
    )
    llm_primary_provider: str = Field(
        default="langchain_openai",
        validation_alias=AliasChoices("AI_SERVICE_V2_LLM_PRIMARY_PROVIDER", "LLM_PROVIDER"),
    )
    llm_fallback_provider: str = Field(
        default="legacy_ai",
        validation_alias=AliasChoices("AI_SERVICE_V2_LLM_FALLBACK_PROVIDER", "LLM_FALLBACK_PROVIDER"),
    )
    enable_legacy_runtime_fallback: bool = True
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AI_SERVICE_V2_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("AI_SERVICE_V2_OPENAI_BASE_URL", "OPENAI_BASE_URL", "OPENAI_API_BASE"),
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("AI_SERVICE_V2_OPENAI_MODEL", "OPENAI_MODEL"),
    )
    llm_temperature: float = 0.3
    llm_max_tokens: int = 700
    voice_chunk_max_chars: int = 220
    voice_chunk_max_wait_ms: int = 1400
    voice_chunk_min_timed_chars: int = 48
    voice_chunk_min_timed_words: int = 6


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
