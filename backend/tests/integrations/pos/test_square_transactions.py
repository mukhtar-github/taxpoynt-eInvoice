"""
Test cases for Square transaction processing and FIRS integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime

from app.integrations.pos.square.connector import SquarePOSConnector
from app.integrations.pos.square.firs_transformer import SquareFIRSTransformer


class TestSquareTransactions:
    """Test cases for Square transaction processing."""
    
    @pytest.fixture
    def mock_square_transaction(self):
        """Mock Square transaction data."""
        return {
            "id": "txn_123456789",
            "location_id": "LOC_123",
            "tenders": [{
                "id": "tender_123",
                "amount_money": {
                    "amount": 5000,  # $50.00 in cents
                    "currency": "USD"
                },
                "type": "CARD"
            }],
            "created_at": "2024-01-15T10:30:00Z",
            "order_id": "order_123"
        }
    
    @pytest.mark.asyncio
    async def test_process_transaction_basic(self, mock_square_transaction):
        """Test basic transaction processing."""
        config = {"access_token": "test_token"}
        connector = SquarePOSConnector(config)
        
        with patch.object(connector, '_get_customer_details') as mock_customer:
            mock_customer.return_value = {"name": "Test Customer"}
            
            result = await connector.process_transaction(mock_square_transaction)
            
            assert result["transaction_id"] == "txn_123456789"
            assert result["status"] == "processed"