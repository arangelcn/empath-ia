"""Configurações do ai-service-v2."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic import field_validator
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
    google_client_id: str = Field(
        default="",
        validation_alias=AliasChoices("AI_SERVICE_V2_GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID"),
    )
    jwt_secret_key: str = Field(
        default="changeme-must-be-at-least-32-characters-long!",
        validation_alias=AliasChoices("AI_SERVICE_V2_JWT_SECRET_KEY", "JWT_SECRET_KEY", "SECRET_KEY"),
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias=AliasChoices("AI_SERVICE_V2_JWT_ALGORITHM", "ALGORITHM"),
    )
    access_token_expire_minutes: int = Field(
        default=10080,
        validation_alias=AliasChoices("AI_SERVICE_V2_ACCESS_TOKEN_EXPIRE_MINUTES", "ACCESS_TOKEN_EXPIRE_MINUTES"),
    )
    admin_username: str = Field(
        default="admin",
        validation_alias=AliasChoices("AI_SERVICE_V2_ADMIN_USERNAME", "ADMIN_USERNAME"),
    )
    admin_password: str = Field(
        default="admin123",
        validation_alias=AliasChoices("AI_SERVICE_V2_ADMIN_PASSWORD", "ADMIN_PASSWORD"),
    )
    admin_email: str = Field(
        default="admin@empat-ia.io",
        validation_alias=AliasChoices("AI_SERVICE_V2_ADMIN_EMAIL", "ADMIN_EMAIL"),
    )
    admin_allowed_emails: list[str] = Field(
        default_factory=lambda: ["admin@empat-ia.io"],
        validation_alias=AliasChoices("AI_SERVICE_V2_ADMIN_ALLOWED_EMAILS", "ADMIN_ALLOWED_EMAILS"),
    )
    gateway_service_url: str = Field(
        default="http://gateway:8000",
        validation_alias=AliasChoices("AI_SERVICE_V2_GATEWAY_SERVICE_URL", "GATEWAY_SERVICE_URL"),
    )
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
    enable_legacy_runtime_fallback: bool = False
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

    @field_validator("llm_primary_provider", mode="before")
    @classmethod
    def normalize_primary_provider(cls, value: object) -> object:
        """Accept legacy env aliases while keeping one canonical provider id."""
        if isinstance(value, str):
            normalized = value.strip().lower().replace("-", "_")
            if normalized in {"openai", "langchain_openai"}:
                return "langchain_openai"
        return value

    @field_validator("openai_base_url", mode="before")
    @classmethod
    def normalize_openai_base_url(cls, value: object) -> object:
        """Keep OpenAI base URL stable even when the env var exists but is blank."""
        if isinstance(value, str) and not value.strip():
            return "https://api.openai.com/v1"
        return value

    @field_validator("openai_model", mode="before")
    @classmethod
    def normalize_openai_model(cls, value: object) -> object:
        """Fall back to the default model when the env var is blank."""
        if isinstance(value, str) and not value.strip():
            return "gpt-4o-mini"
        return value

    @field_validator("google_client_id", mode="before")
    @classmethod
    def normalize_google_client_id(cls, value: object) -> object:
        """Treat blank Google client ids as disabled auth."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("admin_allowed_emails", mode="before")
    @classmethod
    def normalize_admin_allowed_emails(cls, value: object) -> object:
        """Accept comma-separated env strings for admin allow-lists."""
        if isinstance(value, str):
            emails = [email.strip().lower() for email in value.split(",") if email.strip()]
            return emails or ["admin@empat-ia.io"]
        if isinstance(value, list):
            normalized = [str(item).strip().lower() for item in value if str(item).strip()]
            return normalized or ["admin@empat-ia.io"]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
