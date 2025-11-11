"""Integration tests for UI streaming functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from nicegui import ui

from app.main import app

# Initialize NiceGUI at module level before any tests run
# This must be done before creating TestClient instances
# Note: This may cause issues if the app has already been used elsewhere,
# but for integration tests this should work
try:
    ui.run_with(app)
except RuntimeError:
    # NiceGUI may already be initialized, which is fine
    pass


@pytest.fixture
def client() -> TestClient:
    """Create test client fixture."""
    return TestClient(app)


def test_ui_page_exists(client: TestClient) -> None:
    """Test that UI page endpoint exists."""
    # NiceGUI pages are mounted, so we check if the app has the route
    # The actual UI rendering is handled by NiceGUI, so we just verify
    # the endpoint doesn't return 404
    response = client.get("/")
    # Should not be 404 (endpoint exists)
    assert response.status_code != 404


def test_ui_can_access_chat_endpoint(client: TestClient) -> None:
    """Test that UI can access the chat streaming endpoint."""
    # Mock the agent to return a simple stream
    async def mock_stream():
        yield "Hello"
        yield " "
        yield "World"
    
    mock_agent = MagicMock()
    async def mock_arun(*args, **kwargs):
        return mock_stream()
    mock_agent.arun = mock_arun
    
    with patch("app.api.chat.create_agent", return_value=mock_agent):
        response = client.post("/api/chat/stream", json={"message": "Test"})
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        # Verify streaming content
        content = response.text
        assert "data:" in content

