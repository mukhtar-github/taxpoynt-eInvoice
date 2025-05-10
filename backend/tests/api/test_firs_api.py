"""Test cases for FIRS API interactions with properly mocked endpoints.

This module contains comprehensive test cases for FIRS API interactions,
with mock endpoints that exactly match the FIRS API documentation.
"""

import pytest
import responses
import json
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta

from app.main import app
from app.core.config import settings

client = TestClient(app)

# Mock FIRS API endpoints and responses
# Following the official FIRS API documentation - uses sandbox URL
MOCK_FIRS_BASE_URL = "https://api.sandbox.firs.gov.ng"


def create_sample_invoice(business_id, irn):
    """Create a sample invoice that follows the FIRS documentation structure."""
    return {
        "business_id": business_id,
        "irn": irn,
        "issue_date": "2024-05-14",
        "due_date": "2024-06-14",
        "issue_time": "17:59:04",
        "invoice_type_code": "396",
        "payment_status": "PENDING",
        "note": "Test invoice for validation",
        "document_currency_code": "NGN",
        "tax_currency_code": "NGN",
        "accounting_supplier_party": {
            "party_name": "Test Supplier",
            "tin": "TIN-0099990001",
            "email": "supplier@test.com",
            "telephone": "+2348025400000",
            "business_description": "Test supplier business",
            "postal_address": {
                "street_name": "32, Test Street",
                "city_name": "Abuja",
                "postal_zone": "900001",
                "country": "NG"
            }
        },
        "accounting_customer_party": {
            "party_name": "Test Customer",
            "tin": "TIN-0088880001",
            "email": "customer@test.com",
            "telephone": "+2348025500000",
            "business_description": "Test customer business",
            "postal_address": {
                "street_name": "10, Customer Street",
                "city_name": "Lagos",
                "postal_zone": "101001",
                "country": "NG"
            }
        },
        "actual_delivery_date": "2024-05-14",
        "payment_means": [
            {
                "payment_means_code": "10",
                "payment_due_date": "2024-05-14"
            }
        ],
        "tax_total": [
            {
                "tax_amount": 56.25,
                "tax_subtotal": [
                    {
                        "taxable_amount": 750.00,
                        "tax_amount": 56.25,
                        "tax_category": {
                            "id": "VAT",
                            "percent": 7.5
                        }
                    }
                ]
            }
        ],
        "invoice_line": [
            {
                "hsn_code": "CC-001",
                "product_category": "Electronics",
                "discount_rate": 0,
                "description": "Test Product",
                "quantity": 3,
                "unit_price": 250.00,
                "line_extension_amount": 750.00,
                "tax_total": {
                    "tax_amount": 56.25,
                    "tax_subtotal": [
                        {
                            "taxable_amount": 750.00,
                            "tax_amount": 56.25,
                            "tax_category": {
                                "id": "VAT",
                                "percent": 7.5
                            }
                        }
                    ]
                }
            }
        ]
    }

# API credential fixtures
@pytest.fixture
def api_credentials():
    """Create mock API credentials for testing."""
    return {
        "x-api-key": f"test-api-key-{uuid4()}",
        "x-api-secret": f"test-api-secret-{uuid4()}"
    }

@pytest.fixture
def taxpayer_credentials():
    """Create mock taxpayer credentials for testing."""
    return {
        "email": "test@taxpayer.com",
        "password": "test-password"
    }

@pytest.fixture
def auth_headers(api_credentials):
    """Create mock auth headers with API credentials for testing."""
    return {
        "x-api-key": api_credentials["x-api-key"],
        "x-api-secret": api_credentials["x-api-secret"]
    }

@responses.activate
def test_taxpayer_authentication(taxpayer_credentials, api_credentials):
    """Test FIRS API taxpayer authentication endpoint."""
    # Mock the authentication endpoint as per FIRS documentation
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/api/v1/utilities/authenticate",
        json={
            "status": "success",
            "message": "Authentication successful",
            "data": {
                "user_id": "usr_123456789",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 86400,
                "issued_at": datetime.utcnow().isoformat(),
                "user": {
                    "id": "usr_123456789",
                    "email": taxpayer_credentials["email"],
                    "name": "Test Taxpayer",
                    "role": "taxpayer"
                }
            }
        },
        status=200,
        match=[responses.matchers.json_params_matcher({
            "email": taxpayer_credentials["email"],
            "password": taxpayer_credentials["password"]
        })]
    )
    
    # Test with valid credentials
    response = client.post(
        "/api/v1/firs/authenticate",
        json=taxpayer_credentials,
        headers={
            "x-api-key": api_credentials["x-api-key"],
            "x-api-secret": api_credentials["x-api-secret"]
        }
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "access_token" in response.json()["data"]
    
    # Test with invalid credentials
    responses.replace(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/api/v1/utilities/authenticate",
        json={
            "status": "error",
            "message": "Invalid credentials",
            "error_code": "AUTH_001"
        },
        status=401,
        match=[responses.matchers.json_params_matcher({
            "email": "invalid@email.com",
            "password": "wrong-password"
        })]
    )
    
    response = client.post(
        "/api/v1/firs/authenticate",
        json={
            "email": "invalid@email.com",
            "password": "wrong-password"
        },
        headers={
            "x-api-key": api_credentials["x-api-key"],
            "x-api-secret": api_credentials["x-api-secret"]
        }
    )
    
    assert response.status_code == 401
    assert response.json()["status"] == "error"

@responses.activate
def test_validate_irn(auth_headers):
    """Test validating an IRN through FIRS API."""
    # Mock the IRN validation endpoint as per FIRS documentation
    mock_irn = "ITW20853450-6997D6BB-20240703"
    mock_business_id = "b1234567890"
    
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/irn/validate",
        json={
            "status": "success",
            "message": "IRN validation successful",
            "data": {
                "valid": True,
                "irn": mock_irn,
                "business_id": mock_business_id,
                "invoice_reference": "ITW001",
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
        },
        status=200,
        match=[responses.matchers.json_params_matcher({
            "invoice_reference": "ITW001",
            "business_id": mock_business_id,
            "irn": mock_irn
        })]
    )
    
    # Test validating an IRN
    response = client.post(
        "/api/v1/invoice/irn/validate",
        json={
            "invoice_reference": "ITW001",
            "business_id": mock_business_id,
            "irn": mock_irn
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["valid"] is True
    assert response.json()["data"]["irn"] == mock_irn
    
    # Test with invalid IRN
    invalid_irn = "ITW20853450-INVALID-20240703"
    
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/irn/validate",
        json={
            "status": "error",
            "message": "Invalid IRN format or IRN not found",
            "error_code": "IRN_001"
        },
        status=400,
        match=[responses.matchers.json_params_matcher({
            "invoice_reference": "ITW001",
            "business_id": mock_business_id,
            "irn": invalid_irn
        })]
    )
    
    response = client.post(
        "/api/v1/invoice/irn/validate",
        json={
            "invoice_reference": "ITW001",
            "business_id": mock_business_id,
            "irn": invalid_irn
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert response.json()["status"] == "error"

@responses.activate
def test_validate_invoice(auth_headers):
    """Test invoice validation against FIRS rules."""
    # Mock the validation endpoint as per FIRS documentation
    mock_business_id = "b1234567890"
    mock_irn = "ITW20853450-6997D6BB-20240703"
    
    # Create a sample invoice following the FIRS documentation structure
    valid_invoice = create_sample_invoice(mock_business_id, mock_irn)
    
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/validate",
        json={
            "status": "success",
            "message": "Invoice validation successful",
            "data": {
                "valid": True,
                "validation_id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "irn": mock_irn,
                "business_id": mock_business_id
            }
        },
        status=200
    )
    
    response = client.post(
        "/api/v1/invoice/validate",
        json=valid_invoice,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["valid"] is True

    # Test with invalid invoice structure
    invalid_invoice = create_sample_invoice(mock_business_id, mock_irn)
    # Remove required fields to make it invalid
    del invalid_invoice["accounting_supplier_party"]
    
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/validate",
        json={
            "status": "error",
            "message": "Invoice validation failed",
            "errors": [
                {
                    "field": "accounting_supplier_party",
                    "message": "accounting_supplier_party is required",
                    "code": "VAL_001"
                }
            ],
            "data": {
                "valid": False,
                "validation_id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        status=400
    )
    
    response = client.post(
        "/api/v1/invoice/validate",
        json=invalid_invoice,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert response.json()["status"] == "error"
    assert response.json()["data"]["valid"] is False
    assert len(response.json()["errors"]) == 1


@responses.activate
def test_sign_invoice(auth_headers):
    """Test signing an invoice through FIRS API."""
    # Mock the sign invoice endpoint as per FIRS documentation
    mock_business_id = "b1234567890"
    mock_irn = "ITW20853450-6997D6BB-20240703"
    mock_csid = "CSID1234567890"
    
    # Create a sample invoice following the FIRS documentation structure
    valid_invoice = create_sample_invoice(mock_business_id, mock_irn)
    
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/sign",
        json={
            "status": "success",
            "message": "Invoice signed successfully",
            "data": {
                "irn": mock_irn,
                "csid": mock_csid,
                "business_id": mock_business_id,
                "signed_at": datetime.utcnow().isoformat(),
                "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEU...",
                "signed_invoice_url": f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/download/{mock_irn}"
            }
        },
        status=200
    )
    
    response = client.post(
        "/api/v1/invoice/sign",
        json=valid_invoice,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["irn"] == mock_irn
    assert response.json()["data"]["csid"] == mock_csid
    assert "signed_invoice_url" in response.json()["data"]
    
    # Test with invalid invoice structure
    invalid_invoice = create_sample_invoice(mock_business_id, mock_irn)
    # Remove required fields to make it invalid
    del invalid_invoice["accounting_supplier_party"]
    
    responses.add(
        responses.POST,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/sign",
        json={
            "status": "error",
            "message": "Invalid invoice structure",
            "errors": [
                {
                    "field": "accounting_supplier_party",
                    "message": "accounting_supplier_party is required",
                    "code": "VAL_001"
                }
            ]
        },
        status=400
    )
    
    response = client.post(
        "/api/v1/invoice/sign",
        json=invalid_invoice,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert response.json()["status"] == "error"
    assert len(response.json()["errors"]) == 1


@responses.activate
def test_download_invoice(auth_headers):
    """Test downloading a signed invoice from FIRS API."""
    # Mock the download invoice endpoint as per FIRS documentation
    mock_irn = "ITW20853450-6997D6BB-20240703"
    mock_pdf_data = "JVBERi0xLjcKJeLjz9MKNyAwIG9iago8PCAvVHlwZSAvUGFnZSAvUGFyZ..."
    
    responses.add(
        responses.GET,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/download/{mock_irn}",
        json={
            "status": "success",
            "message": "Invoice downloaded successfully",
            "data": {
                "irn": mock_irn,
                "file_name": f"invoice_{mock_irn}.pdf",
                "content_type": "application/pdf",
                "file_content": mock_pdf_data
            }
        },
        status=200
    )
    
    response = client.get(
        f"/api/v1/invoice/download/{mock_irn}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["irn"] == mock_irn
    assert response.json()["data"]["file_content"] == mock_pdf_data
    
    # Test with invalid IRN
    invalid_irn = "INVALID-IRN-FORMAT"
    
    responses.add(
        responses.GET,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/download/{invalid_irn}",
        json={
            "status": "error",
            "message": "Invoice not found",
            "error_code": "INV_001"
        },
        status=404
    )
    
    response = client.get(
        f"/api/v1/invoice/download/{invalid_irn}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert response.json()["status"] == "error"


@responses.activate
def test_get_countries():
    """Test getting countries resource from FIRS API."""
    # Mock the countries endpoint as per FIRS documentation
    responses.add(
        responses.GET,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/resources/countries",
        json={
            "status": "success",
            "message": "Countries retrieved successfully",
            "data": [
                {
                    "id": "NG",
                    "name": "Nigeria"
                },
                {
                    "id": "GH",
                    "name": "Ghana"
                },
                {
                    "id": "KE",
                    "name": "Kenya"
                }
            ]
        },
        status=200
    )
    
    response = client.get("/api/v1/invoice/resources/countries")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["data"]) == 3


@responses.activate
def test_get_currencies():
    """Test getting currencies resource from FIRS API."""
    # Mock the currencies endpoint as per FIRS documentation
    responses.add(
        responses.GET,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/resources/currencies",
        json={
            "status": "success",
            "message": "Currencies retrieved successfully",
            "data": [
                {
                    "id": "NGN",
                    "name": "Nigerian Naira"
                },
                {
                    "id": "USD",
                    "name": "US Dollar"
                },
                {
                    "id": "EUR",
                    "name": "Euro"
                },
                {
                    "id": "GBP",
                    "name": "British Pound"
                }
            ]
        },
        status=200
    )
    
    response = client.get("/api/v1/invoice/resources/currencies")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["data"]) == 4


@responses.activate
def test_get_tax_categories():
    """Test getting tax categories resource from FIRS API."""
    # Mock the tax categories endpoint as per FIRS documentation
    responses.add(
        responses.GET,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/resources/tax-categories",
        json={
            "status": "success",
            "message": "Tax categories retrieved successfully",
            "data": [
                {
                    "id": "VAT",
                    "name": "Value Added Tax",
                    "default_percent": 7.5
                },
                {
                    "id": "WHT",
                    "name": "Withholding Tax",
                    "default_percent": 5.0
                },
                {
                    "id": "LOCAL_SALES_TAX",
                    "name": "Local Sales Tax",
                    "default_percent": 2.0
                }
            ]
        },
        status=200
    )
    
    response = client.get("/api/v1/invoice/resources/tax-categories")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["data"]) == 3


@responses.activate
def test_get_payment_means():
    """Test getting payment means resource from FIRS API."""
    # Mock the payment means endpoint as per FIRS documentation
    responses.add(
        responses.GET,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/resources/payment-means",
        json={
            "status": "success",
            "message": "Payment means retrieved successfully",
            "data": [
                {
                    "code": "10",
                    "name": "Cash"
                },
                {
                    "code": "20",
                    "name": "Check"
                },
                {
                    "code": "42",
                    "name": "Bank Account Transfer"
                },
                {
                    "code": "48",
                    "name": "Bank Card"
                }
            ]
        },
        status=200
    )
    
    response = client.get("/api/v1/invoice/resources/payment-means")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["data"]) == 4


@responses.activate
def test_get_invoice_types():
    """Test getting invoice types resource from FIRS API."""
    # Mock the invoice types endpoint as per FIRS documentation
    responses.add(
        responses.GET,
        f"{MOCK_FIRS_BASE_URL}/api/v1/invoice/resources/invoice-types",
        json={
            "status": "success",
            "message": "Invoice types retrieved successfully",
            "data": [
                {
                    "code": "380",
                    "name": "Commercial Invoice"
                },
                {
                    "code": "381",
                    "name": "Credit Note"
                },
                {
                    "code": "383",
                    "name": "Debit Note"
                },
                {
                    "code": "386",
                    "name": "Prepayment Invoice"
                },
                {
                    "code": "396",
                    "name": "Factored Invoice"
                }
            ]
        },
        status=200
    )
    
    response = client.get("/api/v1/invoice/resources/invoice-types")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert len(response.json()["data"]) == 5
