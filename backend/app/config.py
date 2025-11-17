"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables.
"""

from typing import List
from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Database
    database_url: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "meeting_ai"
    postgres_user: str = "postgres"
    postgres_password: str

    # Redis
    redis_url: str
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""

    # LiveKit
    livekit_url: str = "ws://livekit:7880"
    livekit_api_url: str = "http://livekit:7881"
    livekit_api_key: str
    livekit_api_secret: str

    # STT (Speech-to-Text)
    stt_url: str = "ws://stt:9090"
    stt_engine_type: str = "whisperlive"

    # LLM (Large Language Model)
    llm_api_base_url: str = "https://platform.moonshot.ai/v1"
    llm_api_key: str
    llm_model: str = "kimi-k2-instruct"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_request_timeout: int = 30
    llm_min_request_interval: int = 5

    # Authentication & Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440
    password_min_length: int = 8
    bcrypt_rounds: int = 12

    # Admin User (for seeding)
    admin_default_username: str = "admin"
    admin_default_password: str = "admin123"
    admin_default_email: str = "admin@example.com"

    # Feature Flags
    enable_video_analytics: bool = False
    enable_audio_analytics: bool = False
    enable_recording: bool = False


# Global settings instance
settings = Settings()
