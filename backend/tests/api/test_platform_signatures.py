"""
Integration tests for Signature Management API endpoints.

Tests signature verification, metrics collection, and settings management functionality.
"""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.utils.crypto_signing import verify_csid
from app.utils.signature_optimization import get_metrics as get_optimization_metrics
from app.utils.signature_caching import get_cache_metrics, clear_cache

client = TestClient(app)

# Test fixtures
@pytest.fixture
def auth_headers():
    """Generate mock authentication headers for test requests"""
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def sample_invoice():
    """Generate a sample invoice with signature for testing"""
    return {
        "invoice_number": "INV-2025-00123",
        "seller_name": "Test Company Ltd",
        "buyer_name": "Acme Corp",
        "total_amount": 1250.00,
        "currency": "NGN",
        "items": [
            {"description": "Test Product", "quantity": 2, "unit_price": 625.00}
        ],
        "issue_date": "2025-06-01",
        "csid": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2ZXJzaW9uIjoiMi4wIiwic2lnbmF0dXJlX3ZhbHVlIjoiYWJjZGVmMTIzIiwic2lnbmF0dXJlX2FsZ29yaXRobSI6IlJTQS1QU1MtU0hBMjU2Iiwia2V5X2luZm8iOnsidHlwZSI6InJzYSIsImtleV9pZCI6InRlc3Rfa2V5XzEiLCJjZXJ0aWZpY2F0ZSI6InRlc3RfY2VydC5jcnQifSwibWV0YWRhdGEiOnsiZ2VuZXJhdGVkX2F0IjoiMjAyNS0wNi0wMVQwMDowMDowMFoiLCJzaWduYXR1cmVfaWQiOiJ0ZXN0X3NpZ18xMjMifX0.test_signature"
    }

# Mock the authentication middleware for testing
@pytest.fixture(autouse=True)
def mock_auth():
    """Mock the authentication middleware to allow test requests"""
    with patch("app.core.security.get_current_active_user", return_value={"id": "test_user", "email": "test@example.com"}):
        yield

# Signature Verification Tests
class TestSignatureVerification:
    
    @patch("app.api.routes.platform.signatures.verify_csid")
    def test_verify_valid_signature(self, mock_verify_csid, auth_headers, sample_invoice):
        """Test signature verification with a valid signature"""
        # Mock the verification function to return success
        mock_verify_csid.return_value = (
            True, 
            "Signature verified successfully",
            {
                "algorithm": "RSA-PSS-SHA256",
                "version": "2.0",
                "timestamp": "2025-06-01T00:00:00Z",
                "signature_id": "test_sig_123"
            }
        )
        
        response = client.post(
            "/api/platform/signatures/verify",
            json=sample_invoice,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "Signature verified successfully" in data["message"]
        assert data["details"]["algorithm"] == "RSA-PSS-SHA256"
        
        # Verify the function was called with correct params
        mock_verify_csid.assert_called_once()
    
    @patch("app.api.routes.platform.signatures.verify_csid")
    def test_verify_invalid_signature(self, mock_verify_csid, auth_headers, sample_invoice):
        """Test signature verification with an invalid signature"""
        # Mock the verification function to return failure
        mock_verify_csid.return_value = (
            False, 
            "Invalid signature - data mismatch",
            {
                "algorithm": "RSA-PSS-SHA256",
                "version": "2.0",
                "error": "Signature does not match invoice data"
            }
        )
        
        # Modify the invoice to make signature invalid
        modified_invoice = sample_invoice.copy()
        modified_invoice["total_amount"] = 2000.00
        
        response = client.post(
            "/api/platform/signatures/verify",
            json=modified_invoice,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "Invalid signature" in data["message"]
        assert "error" in data["details"]
        
    def test_verify_missing_signature(self, auth_headers):
        """Test signature verification with missing signature"""
        invoice_without_signature = {
            "invoice_number": "INV-2025-00123",
            "total_amount": 1250.00
        }
        
        response = client.post(
            "/api/platform/signatures/verify",
            json=invoice_without_signature,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "No signature or CSID found" in data["message"]
        
    @patch("app.api.routes.platform.signatures.verify_csid")
    def test_verify_file_upload(self, mock_verify_csid, auth_headers, sample_invoice):
        """Test signature verification with file upload"""
        # Mock the verification function to return success
        mock_verify_csid.return_value = (
            True, 
            "Signature verified successfully",
            {
                "algorithm": "RSA-PSS-SHA256",
                "version": "2.0"
            }
        )
        
        # Create a file-like object containing the invoice JSON
        file_content = json.dumps(sample_invoice).encode()
        
        response = client.post(
            "/api/platform/signatures/verify-file",
            files={"file": ("invoice.json", file_content, "application/json")},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

# Metrics and Settings Tests
class TestMetricsAndSettings:
    
    @patch("app.api.routes.platform.signatures.get_optimization_metrics")
    @patch("app.api.routes.platform.signatures.get_cache_metrics")
    def test_get_metrics(self, mock_cache_metrics, mock_optimization_metrics, auth_headers):
        """Test getting performance metrics"""
        # Mock the metrics functions
        mock_optimization_metrics.return_value = {
            "total_signatures": 1000,
            "avg_time": 5.2,
            "min_time": 3.1,
            "max_time": 15.7,
            "total_time": 5200
        }
        
        mock_cache_metrics.return_value = {
            "hit_rate": 0.85,
            "hits": 850,
            "misses": 150,
            "entries": 500
        }
        
        response = client.get(
            "/api/platform/signatures/metrics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check metrics data structure
        assert "generation" in data
        assert "cache" in data
        assert "verification" in data
        
        # Check specific metrics values
        assert data["generation"]["total"] == 1000
        assert data["generation"]["avg_time"] == 5.2
        assert data["cache"]["hit_rate"] == 0.85
        assert data["cache"]["hits"] == 850
    
    def test_save_settings(self, auth_headers):
        """Test saving signature settings"""
        settings = {
            "algorithm": "ED25519",
            "version": "2.0",
            "enableCaching": True,
            "cacheSize": 2000,
            "cacheTtl": 7200,
            "parallelProcessing": True,
            "maxWorkers": 8
        }
        
        response = client.post(
            "/api/platform/signatures/settings",
            json=settings,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify the settings were saved by retrieving them
        get_response = client.get(
            "/api/platform/signatures/settings",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        saved_settings = get_response.json()
        assert saved_settings["algorithm"] == "ED25519"
        assert saved_settings["cacheSize"] == 2000
        
    @patch("app.api.routes.platform.signatures.clear_cache")
    def test_clear_cache(self, mock_clear_cache, auth_headers):
        """Test clearing the signature cache"""
        response = client.post(
            "/api/platform/signatures/clear-cache",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Cache cleared successfully" in data["message"]
        
        # Verify clear_cache was called
        mock_clear_cache.assert_called_once()
