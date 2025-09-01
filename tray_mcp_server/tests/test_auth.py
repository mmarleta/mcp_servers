import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_url_generation():
    # Test without callback URL
    response = client.get("/api/v1/auth/tray/auth-url")
    assert response.status_code == 422  # Validation error for missing parameter
    
    # Test with callback URL
    response = client.get("/api/v1/auth/tray/auth-url?callback_url=https://example.com/callback")
    assert response.status_code == 200
    assert "auth_url" in response.json()
    
    # Check that the auth URL contains required parameters
    auth_url = response.json()["auth_url"]
    assert "response_type=code" in auth_url
    assert "consumer_key=" in auth_url
    assert "callback=" in auth_url

def test_token_endpoint_requires_data():
    response = client.post("/api/v1/auth/tray/token")
    assert response.status_code == 422  # Validation error for missing data
