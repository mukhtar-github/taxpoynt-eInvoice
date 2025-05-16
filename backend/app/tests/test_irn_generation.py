import pytest # type: ignore
from datetime import datetime, timedelta
import re
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.utils.irn_generator import (
    validate_invoice_number, 
    validate_service_id,
    validate_timestamp,
    generate_firs_irn as generate_irn, 
    parse_irn, 
    validate_irn
)
from app.crud.irn import (
    validate_irn_format, 
    create_irn, 
    get_irn_by_value,
    get_irns_by_integration,
    update_irn_status
)
from app.models.irn import IRNRecord
from app.schemas.irn import IRNGenerateRequest


class TestIRNValidation:
    """Test suite for IRN validation functions"""
    
    def test_validate_invoice_number(self):
        """Test invoice number validation"""
        # Valid invoice numbers
        assert validate_invoice_number("INV001") is True
        assert validate_invoice_number("ABC123") is True
        assert validate_invoice_number("INVOICE123456789") is True
        
        # Invalid invoice numbers
        assert validate_invoice_number("") is False  # Empty
        assert validate_invoice_number("INV-001") is False  # Special characters
        assert validate_invoice_number("INV/001") is False  # Special characters
        assert validate_invoice_number("INV 001") is False  # Space
        assert validate_invoice_number("INV.001") is False  # Period
        assert validate_invoice_number("INV_001") is False  # Underscore
        
        # Test max length validation
        long_invoice = "A" * 51  # 51 characters
        assert validate_invoice_number(long_invoice) is False
        
        long_invoice = "A" * 50  # 50 characters
        assert validate_invoice_number(long_invoice) is True
    
    def test_validate_service_id(self):
        """Test service ID validation"""
        # Valid service IDs
        assert validate_service_id("94ND90NR") is True
        assert validate_service_id("ABCD1234") is True
        assert validate_service_id("12345678") is True
        
        # Invalid service IDs
        assert validate_service_id("") is False  # Empty
        assert validate_service_id("94ND90") is False  # Too short (6 chars)
        assert validate_service_id("94ND90NR1") is False  # Too long (9 chars)
        assert validate_service_id("94ND-90N") is False  # Special characters
        assert validate_service_id("94ND 90N") is False  # Space
    
    def test_validate_timestamp(self):
        """Test timestamp validation"""
        # Valid timestamps
        assert validate_timestamp("20240611") is True
        assert validate_timestamp("20241231") is True
        
        # Today's date should be valid
        today = datetime.now().strftime("%Y%m%d")
        assert validate_timestamp(today) is True
        
        # Yesterday's date should be valid
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        assert validate_timestamp(yesterday) is True
        
        # Invalid timestamps
        assert validate_timestamp("") is False  # Empty
        assert validate_timestamp("2024-06-11") is False  # Wrong format
        assert validate_timestamp("06112024") is False  # Wrong format
        assert validate_timestamp("24/06/11") is False  # Wrong format
        assert validate_timestamp("ABCD1234") is False  # Not a date
        assert validate_timestamp("99999999") is False  # Invalid date
        assert validate_timestamp("20240631") is False  # Invalid date (June 31)
        
        # Future date should be invalid
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
        assert validate_timestamp(tomorrow) is False


class TestIRNGeneration:
    """Test suite for IRN generation functions"""
    
    def test_generate_irn_success(self):
        """Test successful IRN generation"""
        # Test with valid parameters
        irn = generate_irn("INV001", "94ND90NR", "20240611")
        assert irn == "INV001-94ND90NR-20240611"
        
        # Test with different values
        irn2 = generate_irn("ABC123", "12345678", "20241231")
        assert irn2 == "ABC123-12345678-20241231"
        
        # Test with default timestamp
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 6, 11)
            irn3 = generate_irn("INV002", "94ND90NR")
            assert irn3 == "INV002-94ND90NR-20240611"
    
    def test_generate_irn_invalid_params(self):
        """Test IRN generation with invalid parameters"""
        # Invalid invoice number
        with pytest.raises(HTTPException) as exc_info:
            generate_irn("INV-001", "94ND90NR", "20240611")
        assert "Invalid invoice number" in str(exc_info.value.detail)
        
        # Invalid service ID
        with pytest.raises(HTTPException) as exc_info:
            generate_irn("INV001", "94ND90", "20240611")
        assert "Invalid service ID" in str(exc_info.value.detail)
        
        # Invalid timestamp
        with pytest.raises(HTTPException) as exc_info:
            generate_irn("INV001", "94ND90NR", "2024-06-11")
        assert "Invalid timestamp" in str(exc_info.value.detail)
        
        # Future date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
        with pytest.raises(HTTPException) as exc_info:
            generate_irn("INV001", "94ND90NR", tomorrow)
        assert "Invalid timestamp" in str(exc_info.value.detail)
    
    def test_parse_irn(self):
        """Test IRN parsing"""
        # Valid IRN
        invoice_number, service_id, timestamp = parse_irn("INV001-94ND90NR-20240611")
        assert invoice_number == "INV001"
        assert service_id == "94ND90NR"
        assert timestamp == "20240611"
        
        # Invalid IRN format
        with pytest.raises(HTTPException) as exc_info:
            parse_irn("INV001-94ND90NR")
        assert "Invalid IRN format" in str(exc_info.value.detail)
        
        with pytest.raises(HTTPException) as exc_info:
            parse_irn("INV001-94ND90NR-20240611-extra")
        assert "Invalid IRN format" in str(exc_info.value.detail)
        
        # Invalid components
        with pytest.raises(HTTPException) as exc_info:
            parse_irn("INV-001-94ND90NR-20240611")
        assert "Invalid invoice number in IRN" in str(exc_info.value.detail)
        
        with pytest.raises(HTTPException) as exc_info:
            parse_irn("INV001-94ND90-20240611")
        assert "Invalid service ID in IRN" in str(exc_info.value.detail)
        
        with pytest.raises(HTTPException) as exc_info:
            parse_irn("INV001-94ND90NR-ABCD1234")
        assert "Invalid timestamp in IRN" in str(exc_info.value.detail)
    
    def test_validate_irn(self):
        """Test IRN validation"""
        # Valid IRN
        assert validate_irn("INV001-94ND90NR-20240611") is True
        
        # Invalid IRN
        assert validate_irn("INV-001-94ND90NR-20240611") is False
        assert validate_irn("INV001-94ND90-20240611") is False
        assert validate_irn("INV001-94ND90NR-20240631") is False  # Invalid date
        assert validate_irn("INV001-94ND90NR") is False  # Missing part
        assert validate_irn("") is False  # Empty


class TestIRNCRUD:
    """Test suite for IRN CRUD operations"""
    
    @patch('app.crud.irn.db')
    def test_create_irn(self, mock_db):
        """Test IRN creation"""
        # Setup
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing IRN
        
        # Test data
        request = IRNGenerateRequest(
            integration_id="00000000-0000-0000-0000-000000000000",
            invoice_number="INV001"
        )
        service_id = "94ND90NR"
        
        # Mock get_irn_by_value
        with patch('app.crud.irn.get_irn_by_value', return_value=None):
            # Call function
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2024, 6, 11)
                result = create_irn(mock_db, request, service_id)
            
            # Assertions
            assert result.irn == "INV001-94ND90NR-20240611"
            assert result.invoice_number == "INV001"
            assert result.service_id == service_id
            assert result.timestamp == "20240611"
            assert result.status == "unused"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    @patch('app.crud.irn.db')
    def test_create_irn_duplicate(self, mock_db):
        """Test IRN creation with duplicate IRN"""
        # Setup - Simulate existing IRN
        existing_irn = IRNRecord(
            irn="INV001-94ND90NR-20240611",
            integration_id="00000000-0000-0000-0000-000000000000",
            invoice_number="INV001",
            service_id="94ND90NR",
            timestamp="20240611",
            status="unused"
        )
        
        # Test data
        request = IRNGenerateRequest(
            integration_id="00000000-0000-0000-0000-000000000000",
            invoice_number="INV001"
        )
        service_id = "94ND90NR"
        
        # Mock get_irn_by_value to return existing IRN
        with patch('app.crud.irn.get_irn_by_value', return_value=existing_irn):
            # Call function
            with pytest.raises(HTTPException) as exc_info:
                with patch('datetime.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2024, 6, 11)
                    create_irn(mock_db, request, service_id)
            
            # Assertions
            assert exc_info.value.status_code == 409
            assert "IRN 'INV001-94ND90NR-20240611' already exists" in str(exc_info.value.detail)
    
    @patch('app.crud.irn.db')
    def test_update_irn_status(self, mock_db):
        """Test IRN status update"""
        # Setup
        irn_value = "INV001-94ND90NR-20240611"
        mock_irn = MagicMock()
        mock_irn.status = "unused"
        mock_irn.used_at = None
        
        # Mock get_irn_by_value
        with patch('app.crud.irn.get_irn_by_value', return_value=mock_irn):
            # Call function - update to used
            result = update_irn_status(mock_db, irn_value, "used", "EXT123")
            
            # Assertions
            assert result.status == "used"
            assert result.invoice_id == "EXT123"
            assert result.used_at is not None
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_irn)
    
    @patch('app.crud.irn.db')
    def test_update_irn_status_not_found(self, mock_db):
        """Test IRN status update with non-existent IRN"""
        # Mock get_irn_by_value to return None
        with patch('app.crud.irn.get_irn_by_value', return_value=None):
            # Call function
            with pytest.raises(HTTPException) as exc_info:
                update_irn_status(mock_db, "INV001-94ND90NR-20240611", "used")
            
            # Assertions
            assert exc_info.value.status_code == 404
            assert "IRN not found" in str(exc_info.value.detail)
    
    @patch('app.crud.irn.db')
    def test_update_irn_status_invalid_status(self, mock_db):
        """Test IRN status update with invalid status"""
        # Call function with invalid status
        with pytest.raises(HTTPException) as exc_info:
            update_irn_status(mock_db, "INV001-94ND90NR-20240611", "invalid")
        
        # Assertions
        assert exc_info.value.status_code == 400
        assert "Invalid status" in str(exc_info.value.detail)