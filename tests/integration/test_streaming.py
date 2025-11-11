"""Integration tests for streaming functionality."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client fixture."""
    return TestClient(app)


def test_streaming_returns_multiple_chunks() -> None:
    """Test that streaming endpoint returns multiple chunks, not a single blob."""
    # Mock agent that returns an async generator with multiple chunks
    async def mock_stream():
        chunks = ["Hello", " ", "world", "!", " How", " can", " I", " help?"]
        for chunk in chunks:
            yield chunk
    
    mock_agent = MagicMock()
    # Make arun return the async generator when awaited
    async def mock_arun(*args, **kwargs):
        return mock_stream()
    mock_agent.arun = mock_arun
    
    with patch("app.api.chat.create_agent", return_value=mock_agent):
        client = TestClient(app)
        response = client.post("/api/chat/stream", json={"message": "Hello"})
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        # Read the streamed content
        content = response.text
        # Should contain multiple data chunks (SSE format)
        data_lines = [line for line in content.split("\n") if line.startswith("data:")]
        assert len(data_lines) > 1, "Stream should return multiple chunks, not a single blob"


def test_streaming_chunks_are_separate() -> None:
    """Test that streaming chunks are separate and not concatenated."""
    # Create mock that yields separate chunks
    async def mock_stream():
        yield "Chunk"
        yield "1"
        yield "Chunk"
        yield "2"
    
    mock_agent = MagicMock()
    # Make arun return the async generator when awaited
    async def mock_arun(*args, **kwargs):
        return mock_stream()
    mock_agent.arun = mock_arun
    
    with patch("app.api.chat.create_agent", return_value=mock_agent):
        client = TestClient(app)
        response = client.post("/api/chat/stream", json={"message": "Test"})
        
        assert response.status_code == 200
        content = response.text
        
        # Verify chunks are separate (SSE format: "data: <chunk>\n\n")
        chunks = [line.replace("data: ", "") for line in content.split("\n") if line.startswith("data:")]
        assert len(chunks) >= 2, "Should have multiple separate chunks"


def test_streaming_handles_errors_gracefully(client: TestClient) -> None:
    """Test that streaming endpoint handles errors gracefully."""
    with patch("app.api.chat.create_agent") as mock_create:
        mock_create.side_effect = Exception("Agent creation failed")
        
        response = client.post("/api/chat/stream", json={"message": "Hello"})
        
        # Should return error status, not crash
        assert response.status_code >= 400
        assert response.status_code < 600

