"""Unit tests for Agno agent."""

import pytest
from agno.agent import Agent

from app.agent.agent import create_agent


def test_agent_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that agent instance is created successfully."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    
    # Clear cached settings
    import app.config as config_module
    config_module._settings = None
    
    agent = create_agent()
    
    assert isinstance(agent, Agent)
    assert agent.name == "PDF Bot Agent"
    assert agent.model is not None


def test_agent_has_openai_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that agent has OpenAI model configured."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-456")
    
    # Clear cached settings
    import app.config as config_module
    config_module._settings = None
    
    agent = create_agent()
    
    assert agent.model is not None
    assert hasattr(agent.model, "api_key")
    assert agent.model.api_key == "test-key-456"


def test_agent_uses_settings_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that agent uses API key from settings."""
    test_key = "test-settings-key-789"
    monkeypatch.setenv("OPENAI_API_KEY", test_key)
    
    # Clear cached settings
    import app.config as config_module
    config_module._settings = None
    
    agent = create_agent()
    
    # Verify the model uses the key from settings
    assert agent.model.api_key == test_key

