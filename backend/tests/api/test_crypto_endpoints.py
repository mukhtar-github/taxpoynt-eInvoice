"""
Tests for crypto endpoints.
"""

import base64
import json
import os
from unittest import mock

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    """Test that health check endpoint is working."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_crypto_keys():
    """Test downloading crypto keys."""
    response = client.get("/crypto/keys")
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "public_key" in data
    assert "-----BEGIN PUBLIC KEY-----" in data["public_key"]
    assert "-----END PUBLIC KEY-----" in data["public_key"]


def test_generate_irn():
    """Test IRN generation endpoint."""
    # Test with valid data
    payload = {
        "invoice_number": "INV001",
        "service_id": "94ND90NR",
        "timestamp": "20240611"
    }
    
    response = client.post("/crypto/generate-irn", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["irn"] == "INV001-94ND90NR-20240611"
    assert data["status"] == "Valid"
    assert data["timestamp"] == "20240611"
    
    # Test with invalid data
    invalid_payload = {
        "invoice_number": "INV-001",  # Invalid: contains hyphen
        "service_id": "94ND90NR",
        "timestamp": "20240611"
    }
    
    response = client.post("/crypto/generate-irn", json=invalid_payload)
    assert response.status_code == 400
    assert "Invalid invoice number" in response.json()["detail"]


def test_sign_irn():
    """Test IRN signing endpoint."""
    # Test with valid IRN
    payload = {
        "irn": "INV001-94ND90NR-20240611",
        "certificate": "TEST_CERTIFICATE"
    }
    
    response = client.post("/crypto/sign-irn", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["irn"] == payload["irn"]
    assert "encrypted_data" in data
    assert "qr_code_base64" in data
    assert data["qr_code_base64"].startswith("data:image/png;base64,")
    
    # Test with invalid IRN
    invalid_payload = {
        "irn": "INVALID-IRN-FORMAT",
        "certificate": "TEST_CERTIFICATE"
    }
    
    response = client.post("/crypto/sign-irn", json=invalid_payload)
    assert response.status_code == 400
    assert "Invalid IRN format" in response.json()["detail"]


def test_get_qr_code():
    """Test QR code generation endpoint."""
    # Test with valid IRN
    irn = "INV001-94ND90NR-20240611"
    response = client.get(f"/crypto/qr-code/{irn}")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0  # Ensure we got image data
    
    # Test with invalid IRN
    invalid_irn = "INVALID-IRN-FORMAT"
    response = client.get(f"/crypto/qr-code/{invalid_irn}")
    
    assert response.status_code == 400
    assert "Invalid IRN format" in response.json()["detail"] 