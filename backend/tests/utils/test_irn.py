"""
Tests for IRN generation utilities.
"""

import datetime
import pytest # type: ignore
from fastapi import HTTPException # type: ignore

from app.utils.irn import (
    generate_irn,
    parse_irn,
    validate_invoice_number,
    validate_irn,
    validate_service_id,
    validate_timestamp,
)


def test_validate_invoice_number():
    """Test validation of invoice numbers."""
    # Valid invoice numbers
    assert validate_invoice_number("INV001") is True
    assert validate_invoice_number("INVOICE123") is True
    assert validate_invoice_number("1234") is True
    assert validate_invoice_number("ABC123") is True
    
    # Invalid invoice numbers
    assert validate_invoice_number("INV-001") is False  # Contains hyphen
    assert validate_invoice_number("INV_001") is False  # Contains underscore
    assert validate_invoice_number("INV 001") is False  # Contains space
    assert validate_invoice_number("INV#001") is False  # Contains special character
    assert validate_invoice_number("") is False  # Empty string


def test_validate_service_id():
    """Test validation of service IDs."""
    # Valid service IDs
    assert validate_service_id("94ND90NR") is True
    assert validate_service_id("12345678") is True
    assert validate_service_id("ABCD1234") is True
    
    # Invalid service IDs
    assert validate_service_id("ABC123") is False  # Too short
    assert validate_service_id("123456789") is False  # Too long
    assert validate_service_id("ABCD-123") is False  # Contains hyphen
    assert validate_service_id("") is False  # Empty string


def test_validate_timestamp():
    """Test validation of timestamps."""
    # Valid timestamps
    assert validate_timestamp("20240611") is True
    assert validate_timestamp("20241231") is True
    assert validate_timestamp("20250101") is True
    
    # Invalid timestamps
    assert validate_timestamp("2024-06-11") is False  # Contains hyphens
    assert validate_timestamp("06/11/2024") is False  # Wrong format
    assert validate_timestamp("2024011") is False  # Too short
    assert validate_timestamp("202406111") is False  # Too long
    assert validate_timestamp("20241232") is False  # Invalid date (December 32)
    assert validate_timestamp("20240631") is False  # Invalid date (June 31)
    assert validate_timestamp("") is False  # Empty string


def test_generate_irn():
    """Test generation of IRNs."""
    # Test with valid inputs
    invoice_number = "INV001"
    service_id = "94ND90NR"
    timestamp = "20240611"
    
    irn = generate_irn(invoice_number, service_id, timestamp)
    assert irn == "INV001-94ND90NR-20240611"
    
    # Test with default timestamp
    today = datetime.datetime.now().strftime("%Y%m%d")
    irn = generate_irn(invoice_number, service_id)
    assert irn == f"INV001-94ND90NR-{today}"
    
    # Test with invalid inputs
    with pytest.raises(HTTPException) as excinfo:
        generate_irn("INV-001", service_id, timestamp)
    assert excinfo.value.status_code == 400
    assert "Invalid invoice number" in excinfo.value.detail
    
    with pytest.raises(HTTPException) as excinfo:
        generate_irn(invoice_number, "123", timestamp)
    assert excinfo.value.status_code == 400
    assert "Invalid service ID" in excinfo.value.detail
    
    with pytest.raises(HTTPException) as excinfo:
        generate_irn(invoice_number, service_id, "2024-06-11")
    assert excinfo.value.status_code == 400
    assert "Invalid timestamp" in excinfo.value.detail


def test_parse_irn():
    """Test parsing of IRNs."""
    # Test with valid IRN
    irn = "INV001-94ND90NR-20240611"
    invoice_number, service_id, timestamp = parse_irn(irn)
    
    assert invoice_number == "INV001"
    assert service_id == "94ND90NR"
    assert timestamp == "20240611"
    
    # Test with invalid IRN format
    with pytest.raises(HTTPException) as excinfo:
        parse_irn("INV001_94ND90NR_20240611")  # Wrong separator
    assert excinfo.value.status_code == 400
    assert "Invalid IRN format" in excinfo.value.detail
    
    with pytest.raises(HTTPException) as excinfo:
        parse_irn("INV001-94ND90NR")  # Missing timestamp
    assert excinfo.value.status_code == 400
    assert "Invalid IRN format" in excinfo.value.detail
    
    # Test with invalid components
    with pytest.raises(HTTPException) as excinfo:
        parse_irn("INV-001-94ND90NR-20240611")  # Invalid invoice number
    assert excinfo.value.status_code == 400
    assert "Invalid invoice number in IRN" in excinfo.value.detail
    
    with pytest.raises(HTTPException) as excinfo:
        parse_irn("INV001-123-20240611")  # Invalid service ID
    assert excinfo.value.status_code == 400
    assert "Invalid service ID in IRN" in excinfo.value.detail
    
    with pytest.raises(HTTPException) as excinfo:
        parse_irn("INV001-94ND90NR-20241301")  # Invalid date (13th month)
    assert excinfo.value.status_code == 400
    assert "Invalid timestamp in IRN" in excinfo.value.detail


def test_validate_irn():
    """Test validation of complete IRNs."""
    # Valid IRNs
    assert validate_irn("INV001-94ND90NR-20240611") is True
    assert validate_irn("INVOICE123-ABCD1234-20241231") is True
    
    # Invalid IRNs
    assert validate_irn("INV001_94ND90NR_20240611") is False  # Wrong separator
    assert validate_irn("INV-001-94ND90NR-20240611") is False  # Invalid invoice number
    assert validate_irn("INV001-123-20240611") is False  # Invalid service ID
    assert validate_irn("INV001-94ND90NR-2024-06-11") is False  # Invalid timestamp format
    assert validate_irn("INV001-94ND90NR-20241301") is False  # Invalid date 