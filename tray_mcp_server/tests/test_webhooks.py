import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_webhook_get_endpoint():
    response = client.get("/api/v1/webhooks/tray/webhook")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "success"

def test_webhook_post_endpoint():
    # Test with empty payload
    response = client.post("/api/v1/webhooks/tray/webhook")
    assert response.status_code == 200
    assert "status" in response.json()
    
    # Test with sample webhook payload
    payload = {
        "seller_id": "123456",
        "scope_name": "order",
        "scope_id": "789012",
        "act": "update",
        "app_code": "718"
    }
    response = client.post("/api/v1/webhooks/tray/webhook", data=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
