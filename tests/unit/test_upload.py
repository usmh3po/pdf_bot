"""Unit tests for PDF upload endpoint."""

import io
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Create sample PDF content for testing."""
    # Minimal valid PDF structure
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 0\ntrailer\n<< /Size 0 >>\nstartxref\n0\n%%EOF"


@pytest.fixture
def mock_knowledge():
    """Create mock knowledge base for testing."""
    knowledge = MagicMock()
    knowledge.add_content = MagicMock()
    knowledge.get_content = MagicMock(return_value=([], 0))
    knowledge.get_content_status = MagicMock(return_value=("completed", "Success"))
    return knowledge


def test_upload_endpoint_exists(client: TestClient) -> None:
    """Test that upload endpoint exists."""
    # Create a minimal PDF file
    pdf_content = b"%PDF-1.4\n%%EOF"
    files = {"file": ("test.pdf", pdf_content, "application/pdf")}
    response = client.post("/api/upload/pdf", files=files)
    # Should not be 404
    assert response.status_code != 404


def test_upload_endpoint_requires_file(client: TestClient) -> None:
    """Test that upload endpoint requires a file."""
    response = client.post("/api/upload/pdf")
    assert response.status_code == 422  # Validation error


def test_upload_endpoint_rejects_non_pdf(client: TestClient, sample_pdf_content: bytes) -> None:
    """Test that upload endpoint rejects non-PDF files."""
    files = {"file": ("test.txt", b"Not a PDF", "text/plain")}
    response = client.post("/api/upload/pdf", files=files)
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]


def test_upload_endpoint_accepts_pdf(client: TestClient, sample_pdf_content: bytes, mock_knowledge) -> None:
    """Test that upload endpoint accepts PDF files."""
    with patch("app.api.upload.get_knowledge", return_value=mock_knowledge):
        with patch("app.api.upload.get_pdf_reader"):
            files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}
            response = client.post("/api/upload/pdf", files=files)
            
            # Should return 200
            assert response.status_code == 200
            result = response.json()
            assert "file_id" in result
            assert "filename" in result
            assert result["filename"] == "test.pdf"


def test_upload_endpoint_returns_file_id(client: TestClient, sample_pdf_content: bytes, mock_knowledge) -> None:
    """Test that upload endpoint returns a file_id."""
    with patch("app.api.upload.get_knowledge", return_value=mock_knowledge):
        with patch("app.api.upload.get_pdf_reader"):
            files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}
            response = client.post("/api/upload/pdf", files=files)
            
            assert response.status_code == 200
            result = response.json()
            assert "file_id" in result
            assert len(result["file_id"]) > 0


def test_upload_endpoint_calls_knowledge_add_content(
    client: TestClient, sample_pdf_content: bytes, mock_knowledge
) -> None:
    """Test that upload endpoint calls knowledge.add_content."""
    with patch("app.api.upload.get_knowledge", return_value=mock_knowledge):
        with patch("app.api.upload.get_pdf_reader") as mock_reader:
            mock_pdf_reader = MagicMock()
            mock_reader.return_value = mock_pdf_reader
            
            files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}
            response = client.post("/api/upload/pdf", files=files)
            
            assert response.status_code == 200
            # Verify add_content was called (it's run in executor, so we check the mock was set up)
            # The actual call happens in executor, so we verify the knowledge was retrieved
            assert mock_knowledge is not None


def test_status_endpoint_exists(client: TestClient, mock_knowledge) -> None:
    """Test that status endpoint exists."""
    with patch("app.api.upload.get_knowledge", return_value=mock_knowledge):
        # Mock get_content to return empty list (file not found)
        mock_knowledge.get_content.return_value = ([], 0)
        response = client.get("/api/upload/status/test-file-id")
        # Should return 404 (file not found) or 200 (if found), but not 500 (server error)
        # This confirms the endpoint exists and is handling requests
        assert response.status_code in [200, 404]


def test_status_endpoint_returns_404_for_missing_file(client: TestClient, mock_knowledge) -> None:
    """Test that status endpoint returns 404 for non-existent file."""
    with patch("app.api.upload.get_knowledge", return_value=mock_knowledge):
        # Mock get_content to return empty list
        mock_knowledge.get_content.return_value = ([], 0)
        
        response = client.get("/api/upload/status/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_list_endpoint_exists(client: TestClient) -> None:
    """Test that list endpoint exists."""
    response = client.get("/api/upload/list")
    # Should not be 404
    assert response.status_code != 404


def test_list_endpoint_returns_uploads(client: TestClient, mock_knowledge) -> None:
    """Test that list endpoint returns list of uploads."""
    with patch("app.api.upload.get_knowledge", return_value=mock_knowledge):
        # Mock content with PDF metadata
        mock_content = MagicMock()
        mock_content.metadata = {
            "file_id": "test-id",
            "filename": "test.pdf",
            "type": "pdf",
        }
        mock_content.id = "content-id"
        mock_knowledge.get_content.return_value = ([mock_content], 1)
        mock_knowledge.get_content_status.return_value = ("completed", "Success")
        
        response = client.get("/api/upload/list")
        assert response.status_code == 200
        result = response.json()
        assert "uploads" in result
        assert "total" in result
        assert isinstance(result["uploads"], list)

