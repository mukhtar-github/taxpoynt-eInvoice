"""
Integration tests for cryptographic endpoints.
"""
import os
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.cryptographic_stamping_service import CryptographicStampingService
from app.utils.certificate_manager import CertificateManager
from app.utils.key_management import KeyManager
from app.core.config import settings


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    client = TestClient(app)
    return client


@pytest.fixture
def auth_headers():
    """Create authentication headers for API calls."""
    # In a real test, this would use a valid JWT token or API key
    # For testing purposes, we use a mock header
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def test_invoice_data():
    """Sample invoice data for testing."""
    return {
        "invoice_number": "INV-2023-001",
        "date": "2023-10-15",
        "seller": {
            "name": "Test Company Ltd",
            "tax_id": "12345678901",
            "address": "123 Test Street, Lagos"
        },
        "buyer": {
            "name": "Test Customer",
            "tax_id": "98765432109",
            "address": "456 Sample Road, Abuja"
        },
        "items": [
            {
                "description": "Test Product 1",
                "quantity": 2,
                "unit_price": 5000.00,
                "total": 10000.00,
                "tax_rate": 7.5
            },
            {
                "description": "Test Service",
                "quantity": 1,
                "unit_price": 20000.00,
                "total": 20000.00,
                "tax_rate": 7.5
            }
        ],
        "total_amount": 30000.00,
        "total_tax": 2250.00,
        "currency": "NGN"
    }


@pytest.mark.integration
def test_generate_csid_endpoint(test_client, auth_headers, test_invoice_data, monkeypatch):
    """Test the CSID generation endpoint."""
    # Mock the auth dependency
    def mock_get_current_active_user():
        return {"id": 1, "username": "testuser", "is_superuser": True}
    
    monkeypatch.setattr("app.routers.crypto.get_current_active_user", mock_get_current_active_user)
    
    # Mock the sign_invoice function
    def mock_sign_invoice(invoice_data):
        return {
            **invoice_data,
            "cryptographic_stamp": {
                "csid": "test_csid_12345",
                "algorithm": "RSA_PSS_SHA256",
                "timestamp": "2023-10-15T12:00:00Z"
            }
        }
    
    monkeypatch.setattr("app.routers.crypto.sign_invoice", mock_sign_invoice)
    
    # Make the request
    response = test_client.post(
        "/api/crypto/generate-csid",
        json={"invoice_data": test_invoice_data},
        headers=auth_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["is_signed"] is True
    assert "cryptographic_stamp" in data
    assert data["cryptographic_stamp"]["csid"] == "test_csid_12345"


@pytest.mark.integration
def test_verify_csid_endpoint(test_client, auth_headers, test_invoice_data, monkeypatch):
    """Test the CSID verification endpoint."""
    # Mock the auth dependency
    def mock_get_current_active_user():
        return {"id": 1, "username": "testuser", "is_superuser": True}
    
    monkeypatch.setattr("app.routers.crypto.get_current_active_user", mock_get_current_active_user)
    
    # Mock the verify_csid function
    def mock_verify_csid(invoice_data, csid):
        return True, {"verified_at": "2023-10-15T12:30:00Z"}
    
    monkeypatch.setattr("app.routers.crypto.verify_csid", mock_verify_csid)
    
    # Make the request
    response = test_client.post(
        "/api/crypto/verify-csid",
        json={
            "invoice_data": test_invoice_data,
            "csid": "test_csid_12345"
        },
        headers=auth_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert "details" in data


@pytest.mark.integration
def test_generate_stamp_endpoint(test_client, auth_headers, test_invoice_data, monkeypatch):
    """Test the cryptographic stamp generation endpoint."""
    # Mock the auth dependency
    def mock_get_current_active_user():
        return {"id": 1, "username": "testuser", "is_superuser": True}
    
    monkeypatch.setattr("app.routers.crypto.get_current_active_user", mock_get_current_active_user)
    
    # Mock the cryptographic stamping service
    class MockCryptoStampingService:
        def stamp_invoice(self, invoice_data):
            return {
                **invoice_data,
                "cryptographic_stamp": {
                    "csid": "test_csid_12345",
                    "algorithm": "RSA_PSS_SHA256",
                    "timestamp": "2023-10-15T12:00:00Z",
                    "qr_code": "base64_encoded_qr_code_data",
                    "certificate_id": "test_cert_id"
                }
            }
    
    def mock_get_crypto_stamping_service():
        return MockCryptoStampingService()
    
    monkeypatch.setattr("app.routers.crypto.get_cryptographic_stamping_service", mock_get_crypto_stamping_service)
    
    # Make the request
    response = test_client.post(
        "/api/crypto/generate-stamp",
        json={"invoice_data": test_invoice_data},
        headers=auth_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "stamped_invoice" in data
    assert "stamp_info" in data
    assert data["stamp_info"]["csid"] == "test_csid_12345"
    assert "qr_code" in data["stamp_info"]


@pytest.mark.integration
def test_verify_stamp_endpoint(test_client, auth_headers, test_invoice_data, monkeypatch):
    """Test the cryptographic stamp verification endpoint."""
    # Mock the auth dependency
    def mock_get_current_active_user():
        return {"id": 1, "username": "testuser", "is_superuser": True}
    
    monkeypatch.setattr("app.routers.crypto.get_current_active_user", mock_get_current_active_user)
    
    # Mock the cryptographic stamping service
    class MockCryptoStampingService:
        def verify_stamp(self, invoice_data, stamp_data):
            return True, {
                "verified_at": "2023-10-15T12:30:00Z",
                "certificate_status": "valid"
            }
    
    def mock_get_crypto_stamping_service():
        return MockCryptoStampingService()
    
    monkeypatch.setattr("app.routers.crypto.get_cryptographic_stamping_service", mock_get_crypto_stamping_service)
    
    # Make the request
    stamp_data = {
        "csid": "test_csid_12345",
        "algorithm": "RSA_PSS_SHA256",
        "timestamp": "2023-10-15T12:00:00Z",
        "certificate_id": "test_cert_id"
    }
    
    response = test_client.post(
        "/api/crypto/verify-stamp",
        json={
            "invoice_data": test_invoice_data,
            "stamp_data": stamp_data
        },
        headers=auth_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert "details" in data
    assert data["details"]["certificate_status"] == "valid"


@pytest.mark.integration
def test_list_certificates_endpoint(test_client, auth_headers, monkeypatch):
    """Test the certificates listing endpoint."""
    # Mock the auth dependency
    def mock_get_current_active_user():
        return {"id": 1, "username": "testuser", "is_superuser": True}
    
    monkeypatch.setattr("app.routers.crypto.get_current_active_user", mock_get_current_active_user)
    
    # Mock the certificate manager
    class MockCertificateManager:
        def __init__(self):
            self.certs_dir = "/tmp/test_certs"
        
        def validate_certificate(self, cert_path):
            return True, {
                "subject": {"commonName": "test.example.com"},
                "issuer": {"organizationName": "Test CA"},
                "valid_from": "2023-01-01T00:00:00Z",
                "valid_until": "2024-01-01T00:00:00Z"
            }
    
    def mock_get_certificate_manager():
        return MockCertificateManager()
    
    monkeypatch.setattr("app.routers.crypto.get_certificate_manager", mock_get_certificate_manager)
    
    # Mock os.listdir
    def mock_listdir(path):
        return ["cert1.crt", "cert2.pem", "not_a_cert.txt"]
    
    monkeypatch.setattr("os.listdir", mock_listdir)
    
    # Mock os.path.join
    def mock_path_join(dir_path, filename):
        return f"{dir_path}/{filename}"
    
    monkeypatch.setattr("os.path.join", mock_path_join)
    
    # Make the request
    response = test_client.get(
        "/api/crypto/certificates",
        headers=auth_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "certificates" in data
    assert data["count"] == 2  # Only .crt and .pem files
    assert any(cert["filename"] == "cert1.crt" for cert in data["certificates"])
    assert any(cert["filename"] == "cert2.pem" for cert in data["certificates"])


@pytest.mark.integration
def test_upload_keys_endpoint(test_client, auth_headers, monkeypatch):
    """Test the crypto keys upload endpoint."""
    # Mock the auth dependency
    def mock_get_current_active_user():
        return {"id": 1, "username": "testuser", "is_superuser": True}
    
    monkeypatch.setattr("app.routers.crypto.get_current_active_user", mock_get_current_active_user)
    
    # Mock extract_keys_from_file
    def mock_extract_keys(file_path):
        return b"mock_public_key", b"mock_certificate"
    
    monkeypatch.setattr("app.routers.crypto.extract_keys_from_file", mock_extract_keys)
    
    # Mock certificate_manager
    class MockCertificateManager:
        def store_certificate(self, cert_data, name):
            return f"/tmp/certificates/{name}"
            
        def validate_certificate(self, cert_path):
            return True, {
                "subject": {"commonName": "test.example.com"},
                "issuer": {"organizationName": "FIRS CA"},
                "valid_from": "2023-01-01T00:00:00Z",
                "valid_until": "2024-01-01T00:00:00Z"
            }
    
    def mock_get_certificate_manager():
        return MockCertificateManager()
    
    monkeypatch.setattr("app.routers.crypto.get_certificate_manager", mock_get_certificate_manager)
    
    # Create a test file
    test_file_content = b"Mock certificate and key data"
    
    # Make the request
    response = test_client.post(
        "/api/crypto/upload-keys",
        files={"file": ("test_keys.p12", test_file_content)},
        headers=auth_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert data["filename"] == "test_keys.p12"
    assert "certificate_info" in data
    assert data["certificate_info"]["is_valid"] is True
