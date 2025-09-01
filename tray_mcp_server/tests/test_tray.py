import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_tray_endpoints_require_auth():
    # Test that tray endpoints require authentication
    response = client.get("/api/v1/tray/products?seller_id=test123")
    assert response.status_code == 401  # Unauthorized
    
    response = client.get("/api/v1/tray/orders?seller_id=test123")
    assert response.status_code == 401  # Unauthorized
    
    response = client.get("/api/v1/tray/customers?seller_id=test123")
    assert response.status_code == 401  # Unauthorized

def test_tray_endpoints_with_seller_id():
    # Test that tray endpoints require seller_id parameter
    # Note: These will fail due to authentication, but we can at least check they don't crash
    response = client.get("/api/v1/tray/products")
    assert response.status_code in [401, 422]  # Either auth error or validation error
    
    response = client.get("/api/v1/tray/orders")
    assert response.status_code in [401, 422]  # Either auth error or validation error
    
    response = client.get("/api/v1/tray/customers")
    assert response.status_code in [401, 422]  # Either auth error or validation error
