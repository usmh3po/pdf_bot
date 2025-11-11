"""Unit tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client fixture."""
    return TestClient(app)


def test_root_endpoint(client: TestClient) -> None:
    """Test that root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data
    assert data["status"] == "ok"


def test_health_endpoint(client: TestClient) -> None:
    """Test that health endpoint returns service status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["status"] == "healthy"

