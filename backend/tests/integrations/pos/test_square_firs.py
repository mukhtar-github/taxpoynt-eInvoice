"""
Test cases for Square FIRS integration and invoice generation.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock

from app.integrations.pos.square.firs_transformer import SquareFIRSTransformer


class TestSquareFIRS:
    """Test cases for Square FIRS integration."""
    
    @pytest.fixture
    def mock_transaction_data(self):
        """Mock transaction data for FIRS transformation."""
        return {
            "id": "txn_123",
            "amount": 5000,  # $50.00 in cents
            "currency": "USD",
            "created_at": "2024-01-15T10:30:00Z",
            "location_id": "LOC_123"
        }
    
    @pytest.fixture
    def firs_config(self):
        """FIRS configuration for testing."""
        return {
            "business_id": "business_123",
            "tin": "12345678-0001",
            "service_id": "SVC_001",
            "exchange_rate": Decimal("1600.00")  # USD to NGN
        }
    
    def test_transform_transaction_to_firs_invoice(self, mock_transaction_data, firs_config):
        """Test transaction to FIRS invoice transformation."""
        transformer = SquareFIRSTransformer(firs_config)
        
        firs_invoice = transformer.transform_transaction_to_firs_invoice(
            mock_transaction_data, 
            location_info={"name": "Test Location"},
            customer_info={"name": "Test Customer"}
        )
        
        assert firs_invoice["business_id"] == "business_123"
        assert "irn" in firs_invoice
        assert firs_invoice["document_currency_code"] == "NGN"