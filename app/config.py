"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI configuration
    openai_api_key: str

    # Application settings
    app_name: str = "PDF Bot"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance (singleton)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get settings instance using singleton pattern."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

