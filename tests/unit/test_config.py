"""Unit tests for configuration."""

import os
import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from app.config import Settings, get_settings


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that settings load from environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("DEBUG", "true")

    settings = Settings()
    assert settings.openai_api_key == "test-key-123"
    assert settings.debug is True


def test_settings_defaults() -> None:
    """Test that default values are correct."""
    # Set required env var
    os.environ["OPENAI_API_KEY"] = "test-key-defaults"

    settings = Settings()
    assert settings.app_name == "PDF Bot"
    assert settings.app_version == "0.1.0"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000

    # Cleanup
    del os.environ["OPENAI_API_KEY"]


def test_settings_missing_required_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing required key raises ValidationError."""
    # Remove the key from environment and don't load from .env
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    # Clear cached settings
    import app.config as config_module
    config_module._settings = None
    
    # Temporarily disable .env file loading
    original_config = Settings.model_config
    Settings.model_config = SettingsConfigDict(env_file=None)
    
    try:
        with pytest.raises(ValidationError):
            Settings()
    finally:
        # Restore original config
        Settings.model_config = original_config


def test_get_settings_singleton() -> None:
    """Test that get_settings returns the same instance (singleton pattern)."""
    os.environ["OPENAI_API_KEY"] = "test-singleton-key"

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
    assert id(settings1) == id(settings2)

    # Cleanup
    del os.environ["OPENAI_API_KEY"]

