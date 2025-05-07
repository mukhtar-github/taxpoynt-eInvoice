"""Test cases for FIRS API interactions."""

import pytest
import responses
import json
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from app.main import app
from app.core.config import settings

client = TestClient(app)

# Mock FIRS API endpoints and responses
MOCK_FIRS_BASE_URL = "https://api.sandbox.firs.gov.ng"

@pytest.fixture
def auth_headers():
    """Create mock auth headers for testing."""
    return {"Authorization": f"Bearer test-token-{uuid4()}"}

@responses.activate
def test_firs_api_authentication():
    """Test FIRS API authentication."""
    # Mock the authentication endpoint
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/auth/token",
        json={
            "access_token": "mock-firs-token",
            "token_type": "bearer",
            "expires_in": 3600
        },
        status=200
    )
    
    # Test with valid credentials
    response = client.post(
        "/api/v1/firs/auth",
        json={
            "client_id": "test-client-id",
            "client_secret": "test-client-secret"
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Test with invalid credentials
    responses.replace(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/auth/token",
        json={"error": "invalid_client", "error_description": "Invalid client credentials"},
        status=401
    )
    
    response = client.post(
        "/api/v1/firs/auth",
        json={
            "client_id": "invalid-id",
            "client_secret": "invalid-secret"
        }
    )
    
    assert response.status_code == 401

@responses.activate
def test_irn_generation(auth_headers):
    """Test generating an IRN number through FIRS API."""
    # Mock the IRN generation endpoint
    mock_irn = "INV001-94ND90NR-20240611"
    
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/irn/generate",
        json={
            "irn": mock_irn,
            "status": "unused",
            "generated_at": datetime.utcnow().isoformat(),
            "valid_until": datetime.utcnow().isoformat()
        },
        status=200
    )
    
    # Test generating an IRN
    response = client.post(
        "/api/v1/irn/generate",
        json={
            "integration_id": str(uuid4()),
            "invoice_number": "INV001",
            "timestamp": "20240611"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["irn"] == mock_irn

@responses.activate
def test_invoice_validation(auth_headers):
    """Test invoice validation against FIRS rules."""
    # Mock the validation endpoint
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/validate/invoice",
        json={
            "valid": True,
            "validation_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "rules_passed": 10,
            "rules_failed": 0,
            "warnings": []
        },
        status=200
    )
    
    # Sample invoice data - simplified for testing
    invoice_data = {
        "invoice_id": "INV001",
        "invoice_date": "2024-05-01",
        "seller": {
            "name": "Test Company",
            "tax_id": "12345678-9"
        },
        "buyer": {
            "name": "Test Customer",
            "tax_id": "98765432-1"
        },
        "items": [
            {
                "description": "Test Product",
                "quantity": 1,
                "unit_price": 100.00,
                "total": 100.00,
                "vat_rate": 7.5,
                "vat_amount": 7.50
            }
        ],
        "total_amount": 107.50
    }
    
    response = client.post(
        "/api/v1/validate/invoice",
        json=invoice_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["valid"] is True

    # Test with invalid invoice
    responses.replace(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/validate/invoice",
        json={
            "valid": False,
            "validation_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "rules_passed": 8,
            "rules_failed": 2,
            "errors": [
                {
                    "rule_id": "VAT-001",
                    "message": "VAT calculation incorrect",
                    "field": "items[0].vat_amount"
                },
                {
                    "rule_id": "TOTAL-001",
                    "message": "Invoice total does not match sum of items",
                    "field": "total_amount"
                }
            ]
        },
        status=200
    )
    
    # Modify the invoice to make it invalid
    invoice_data["items"][0]["vat_amount"] = 10.00  # Incorrect VAT amount
    invoice_data["total_amount"] = 200.00  # Incorrect total
    
    response = client.post(
        "/api/v1/validate/invoice",
        json=invoice_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert len(response.json()["errors"]) == 2
