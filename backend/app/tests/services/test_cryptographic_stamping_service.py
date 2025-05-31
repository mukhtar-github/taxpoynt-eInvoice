"""
Unit tests for the Cryptographic Stamping Service.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.cryptographic_stamping_service import CryptographicStampingService
from app.utils.certificate_manager import CertificateManager
from app.utils.key_management import KeyManager


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


@pytest.fixture
def mock_key_manager():
    """Mock key manager for testing."""
    mock = MagicMock(spec=KeyManager)
    
    # Mock the sign method
    mock.sign.return_value = b"mocked_signature_bytes"
    
    # Mock the verify method
    mock.verify.return_value = True
    
    return mock


@pytest.fixture
def mock_certificate_manager():
    """Mock certificate manager for testing."""
    mock = MagicMock(spec=CertificateManager)
    
    # Mock validate_certificate
    mock.validate_certificate.return_value = (True, {
        "subject": {"commonName": "test.example.com"},
        "issuer": {"commonName": "test.example.com"},
        "valid_from": datetime.now().isoformat(),
        "valid_until": datetime.now().isoformat()
    })
    
    return mock


@pytest.fixture
def stamping_service(mock_key_manager, mock_certificate_manager):
    """Create a cryptographic stamping service with mocked dependencies."""
    service = CryptographicStampingService(
        key_manager=mock_key_manager,
        certificate_manager=mock_certificate_manager
    )
    return service


def test_generate_csid(stamping_service, test_invoice_data, mock_key_manager):
    """Test CSID generation."""
    # Call the method
    csid, timestamp = stamping_service.generate_csid(test_invoice_data)
    
    # Verify key_manager.sign was called
    mock_key_manager.sign.assert_called_once()
    
    # Check that a CSID was generated
    assert csid is not None
    assert timestamp is not None


def test_verify_csid(stamping_service, test_invoice_data, mock_key_manager):
    """Test CSID verification."""
    # Generate a CSID
    csid, timestamp = stamping_service.generate_csid(test_invoice_data)
    
    # Now verify it
    is_valid, details = stamping_service.verify_csid(test_invoice_data, csid)
    
    # Verify key_manager.verify was called
    mock_key_manager.verify.assert_called_once()
    
    # Check that verification passed
    assert is_valid is True
    assert details is not None


def test_generate_qr_code(stamping_service, test_invoice_data):
    """Test QR code generation."""
    # Generate QR code
    qr_data = {
        "invoice_number": test_invoice_data["invoice_number"],
        "total_amount": test_invoice_data["total_amount"],
        "csid": "test_csid"
    }
    
    qr_code = stamping_service.generate_qr_code(qr_data)
    
    # Check that a QR code was generated
    assert qr_code is not None
    assert len(qr_code) > 0


def test_stamp_invoice_full_flow(stamping_service, test_invoice_data):
    """Test the full invoice stamping flow."""
    # Apply the stamp
    stamped_invoice = stamping_service.stamp_invoice(test_invoice_data)
    
    # Check the stamped invoice
    assert "cryptographic_stamp" in stamped_invoice
    assert "csid" in stamped_invoice["cryptographic_stamp"]
    assert "timestamp" in stamped_invoice["cryptographic_stamp"]
    assert "algorithm" in stamped_invoice["cryptographic_stamp"]
    assert "qr_code" in stamped_invoice["cryptographic_stamp"]
    
    # Original invoice data should be preserved
    assert stamped_invoice["invoice_number"] == test_invoice_data["invoice_number"]
    assert stamped_invoice["total_amount"] == test_invoice_data["total_amount"]


def test_verify_stamp(stamping_service, test_invoice_data):
    """Test stamp verification."""
    # Create a stamped invoice
    stamped_invoice = stamping_service.stamp_invoice(test_invoice_data)
    
    # Extract the stamp data
    stamp_data = stamped_invoice["cryptographic_stamp"]
    
    # Verify the stamp
    is_valid, details = stamping_service.verify_stamp(test_invoice_data, stamp_data)
    
    # Check verification result
    assert is_valid is True
    assert details is not None
    assert "timestamp" in details


@patch("app.services.cryptographic_stamping_service.datetime")
def test_timestamp_validation(mock_datetime, stamping_service, test_invoice_data):
    """Test timestamp validation during verification."""
    # Mock the current time
    current_time = datetime(2023, 10, 15, 12, 0, 0)
    mock_datetime.now.return_value = current_time
    
    # Create a stamped invoice
    stamped_invoice = stamping_service.stamp_invoice(test_invoice_data)
    
    # Extract the stamp data
    stamp_data = stamped_invoice["cryptographic_stamp"]
    
    # Advance the clock by 30 days (beyond the typical validity period)
    future_time = datetime(2023, 11, 15, 12, 0, 0)
    mock_datetime.now.return_value = future_time
    
    # Verification should fail due to timestamp expiration
    is_valid, details = stamping_service.verify_stamp(test_invoice_data, stamp_data)
    
    # Verification should fail due to timestamp being too old
    assert is_valid is False
    assert "expired" in details.get("reason", "")


def test_handle_invalid_input(stamping_service):
    """Test handling of invalid input data."""
    # Test with None
    with pytest.raises(ValueError):
        stamping_service.stamp_invoice(None)
    
    # Test with empty dict
    with pytest.raises(ValueError):
        stamping_service.stamp_invoice({})
    
    # Test with missing required fields
    incomplete_invoice = {"invoice_number": "INV001"}
    with pytest.raises(ValueError):
        stamping_service.stamp_invoice(incomplete_invoice)
