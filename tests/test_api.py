"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test cases for health check endpoint."""

    def test_health_check(self, client):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestRootEndpoint:
    """Test cases for root endpoint."""

    def test_root(self, client):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestEmissionFactorsEndpoint:
    """Test cases for emission factors endpoint."""

    def test_get_emission_factors(self, client):
        """Test emission factors endpoint."""
        response = client.get("/emission-factors")
        assert response.status_code == 200
        data = response.json()
        assert "sedan" in data
        assert "suv" in data
        assert "truck" in data
        assert "bus" in data
        assert "bike" in data
        assert data["sedan"] == 192.0
        assert data["truck"] == 500.0


class TestAnalyzeVideoEndpoint:
    """Test cases for video analysis endpoint."""

    def test_no_file(self, client):
        """Test that endpoint rejects requests without file."""
        response = client.post("/analyze-video")
        assert response.status_code == 422

    def test_invalid_file_type(self, client):
        """Test that endpoint rejects invalid file types."""
        response = client.post(
            "/analyze-video",
            files={"video": ("test.txt", b"not a video", "text/plain")},
        )
        assert response.status_code == 415
