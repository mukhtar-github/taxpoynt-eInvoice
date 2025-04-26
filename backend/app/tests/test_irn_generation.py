import pytest
from datetime import datetime
import re

from app.crud.irn import validate_irn_format, generate_irn


def test_validate_irn_format():
    """Test validation of IRN components"""
    # Valid inputs
    assert validate_irn_format("INV001", "94ND90NR", "20240611") is True
    assert validate_irn_format("INV123456", "ABCD1234", "20241231") is True
    
    # Invalid invoice number (special characters)
    assert validate_irn_format("INV-001", "94ND90NR", "20240611") is False
    assert validate_irn_format("INV/001", "94ND90NR", "20240611") is False
    
    # Invalid service ID (wrong length)
    assert validate_irn_format("INV001", "94ND90", "20240611") is False
    assert validate_irn_format("INV001", "94ND90NR1", "20240611") is False
    
    # Invalid timestamp (wrong format)
    assert validate_irn_format("INV001", "94ND90NR", "2024-06-11") is False
    assert validate_irn_format("INV001", "94ND90NR", "06/11/2024") is False


def test_generate_irn():
    """Test IRN generation format"""
    # Test with sample data
    invoice_number = "INV001"
    service_id = "94ND90NR"
    timestamp = "20240611"
    
    irn = generate_irn(invoice_number, service_id, timestamp)
    
    # Check format
    assert irn == "INV001-94ND90NR-20240611"
    
    # Test with different data
    irn2 = generate_irn("ABC123", "12345678", "20241231")
    assert irn2 == "ABC123-12345678-20241231"
    
    # Check against FIRS format requirements
    irn_pattern = r'^[a-zA-Z0-9]+-[a-zA-Z0-9]{8}-\d{8}$'
    assert re.match(irn_pattern, irn) is not None
    assert re.match(irn_pattern, irn2) is not None


def test_generate_irn_with_current_date():
    """Test IRN generation with current date"""
    invoice_number = "INV002"
    service_id = "94ND90NR"
    
    # Use current date in YYYYMMDD format
    today = datetime.now().strftime("%Y%m%d")
    
    irn = generate_irn(invoice_number, service_id, today)
    
    # Check that the timestamp part matches today's date
    assert irn.endswith(today)
    
    # Check overall format
    parts = irn.split("-")
    assert len(parts) == 3
    assert parts[0] == invoice_number
    assert parts[1] == service_id
    assert parts[2] == today 