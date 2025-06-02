"""
Test session management functionality
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test basic health check works"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_user_listing_pagination():
    """Test user listing with pagination works"""
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "users" in data["data"]
    assert "total_count" in data["data"]
    assert "limit" in data["data"]
    assert "offset" in data["data"]

def test_user_listing_with_params():
    """Test user listing with pagination parameters"""
    response = client.get("/api/v1/users/?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["limit"] == 5
    assert data["data"]["offset"] == 0
