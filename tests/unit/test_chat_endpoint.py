"""Unit tests for chat endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_agent():
    """Create mock agent for testing."""
    agent = MagicMock()
    agent.arun = AsyncMock(return_value="Test response")
    return agent


def test_chat_endpoint_exists(client: TestClient) -> None:
    """Test that chat endpoint exists and accepts POST requests."""
    response = client.post("/api/chat/", json={"message": "Hello"})
    # Should not be 404 (endpoint exists)
    assert response.status_code != 404


def test_chat_endpoint_requires_message(client: TestClient) -> None:
    """Test that chat endpoint requires message field."""
    response = client.post("/api/chat/", json={})
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_accepts_optional_session_id(client: TestClient) -> None:
    """Test that chat endpoint accepts optional session_id."""
    response = client.post(
        "/api/chat/",
        json={"message": "Hello", "session_id": "test-session-123"},
    )
    # Should not be validation error
    assert response.status_code != 422


def test_stream_endpoint_exists(client: TestClient) -> None:
    """Test that stream endpoint exists."""
    response = client.post("/api/chat/stream", json={"message": "Hello"})
    # Should not be 404
    assert response.status_code != 404


def test_stream_endpoint_returns_streaming_response(client: TestClient) -> None:
    """Test that stream endpoint returns streaming response."""
    with patch("app.api.chat.create_agent") as mock_create:
        mock_agent = MagicMock()
        mock_agent.arun = AsyncMock(return_value="Test response")
        mock_create.return_value = mock_agent
        
        response = client.post("/api/chat/stream", json={"message": "Hello"})
        
        # Should return 200 with streaming content type
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

