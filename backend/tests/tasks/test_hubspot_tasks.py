"""
Test cases for HubSpot deal processing tasks.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.tasks.hubspot_tasks import (
    process_hubspot_deal,
    sync_hubspot_deals,
    batch_process_hubspot_deals,
    hubspot_deal_processor_task,
    _parse_date
)
from app.models.crm_connection import CRMConnection, CRMDeal


class TestProcessHubSpotDeal:
    """Test cases for process_hubspot_deal function."""

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.SessionLocal')
    @patch('app.tasks.hubspot_tasks.get_hubspot_connector')
    async def test_process_deal_success_new_deal(self, mock_get_connector, mock_session):
        """Test successful processing of a new deal."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock connection from database
        mock_connection = Mock()
        mock_connection.id = "conn-123"
        mock_connection.is_active = True
        mock_connection.connection_settings = {
            "deal_stage_mapping": {
                "closedwon": "generate_invoice"
            }
        }
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock existing deal lookup (no existing deal)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_connection,  # First call for connection
            None  # Second call for existing deal
        ]
        
        # Mock HubSpot connector
        mock_connector = Mock()
        mock_connector.get_deal_by_id = AsyncMock(return_value={
            "id": "deal-123",
            "properties": {
                "dealname": "Test Deal",
                "amount": "50000",
                "dealstage": "closedwon",
                "closedate": "1703030400000",  # Timestamp
                "createdate": "1703020400000"
            }
        })
        mock_connector.transform_deal_to_invoice = AsyncMock(return_value={
            "invoice_number": "HUB-123",
            "customer": {"name": "Test Customer"}
        })
        mock_get_connector.return_value = mock_connector
        
        # Execute test
        result = await process_hubspot_deal("deal-123", "conn-123")
        
        # Verify results
        assert result["success"] is True
        assert result["details"]["deal_id"] == "deal-123"
        assert result["details"]["connection_id"] == "conn-123"
        assert result["details"]["invoice_generated"] is True
        assert result["details"]["deal_stage"] == "closedwon"
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.SessionLocal')
    @patch('app.tasks.hubspot_tasks.get_hubspot_connector')
    async def test_process_deal_success_existing_deal(self, mock_get_connector, mock_session):
        """Test successful processing of an existing deal."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock connection from database
        mock_connection = Mock()
        mock_connection.id = "conn-123"
        mock_connection.is_active = True
        mock_connection.connection_settings = {}
        
        # Mock existing deal
        mock_existing_deal = Mock()
        mock_existing_deal.invoice_generated = False
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_connection,  # First call for connection
            mock_existing_deal  # Second call for existing deal
        ]
        
        # Mock HubSpot connector
        mock_connector = Mock()
        mock_connector.get_deal_by_id = AsyncMock(return_value={
            "id": "deal-123",
            "properties": {
                "dealname": "Updated Deal",
                "amount": "75000",
                "dealstage": "negotiation",
                "closedate": None,
                "createdate": "1703020400000"
            }
        })
        mock_connector.transform_deal_to_invoice = AsyncMock(return_value={
            "invoice_number": "HUB-123",
            "customer": {"name": "Test Customer"}
        })
        mock_get_connector.return_value = mock_connector
        
        # Execute test
        result = await process_hubspot_deal("deal-123", "conn-123")
        
        # Verify results
        assert result["success"] is True
        assert result["details"]["invoice_generated"] is False  # No stage mapping
        assert mock_existing_deal.deal_title == "Updated Deal"
        assert mock_existing_deal.deal_amount == "75000"
        
        # Verify database operations
        mock_db.add.assert_not_called()  # Existing deal, not added
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.SessionLocal')
    async def test_process_deal_connection_not_found(self, mock_session):
        """Test processing when connection is not found."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute test
        result = await process_hubspot_deal("deal-123", "conn-123")
        
        # Verify results
        assert result["success"] is False
        assert "not found" in result["message"]
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.SessionLocal')
    @patch('app.tasks.hubspot_tasks.get_hubspot_connector')
    async def test_process_deal_integration_error(self, mock_get_connector, mock_session):
        """Test processing when integration error occurs."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock connector that raises an error
        from app.integrations.base.errors import IntegrationError
        mock_connector = Mock()
        mock_connector.get_deal_by_id = AsyncMock(side_effect=IntegrationError("API Error"))
        mock_get_connector.return_value = mock_connector
        
        # Execute test
        result = await process_hubspot_deal("deal-123", "conn-123")
        
        # Verify results
        assert result["success"] is False
        assert result["details"]["error_type"] == "IntegrationError"
        mock_db.rollback.assert_called_once()


class TestSyncHubSpotDeals:
    """Test cases for sync_hubspot_deals function."""

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.SessionLocal')
    @patch('app.tasks.hubspot_tasks.get_hubspot_connector')
    @patch('app.tasks.hubspot_tasks.process_hubspot_deal')
    async def test_sync_deals_success(self, mock_process_deal, mock_get_connector, mock_session):
        """Test successful deal synchronization."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.id = "conn-123"
        mock_connection.is_active = True
        mock_connection.connection_settings = {}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock HubSpot connector
        mock_connector = Mock()
        mock_connector.get_deals = AsyncMock(return_value={
            "results": [
                {
                    "id": "deal-1",
                    "properties": {
                        "createdate": str(int((datetime.utcnow() - timedelta(days=1)).timestamp() * 1000)),
                        "hs_lastmodifieddate": str(int(datetime.utcnow().timestamp() * 1000))
                    }
                },
                {
                    "id": "deal-2",
                    "properties": {
                        "createdate": str(int((datetime.utcnow() - timedelta(days=2)).timestamp() * 1000)),
                        "hs_lastmodifieddate": str(int(datetime.utcnow().timestamp() * 1000))
                    }
                }
            ]
        })
        mock_get_connector.return_value = mock_connector
        
        # Mock deal processing
        mock_process_deal.return_value = {"success": True}
        
        # Execute test
        result = await sync_hubspot_deals("conn-123", days_back=30)
        
        # Verify results
        assert result["success"] is True
        assert result["details"]["processed_count"] == 2
        assert result["details"]["error_count"] == 0
        
        # Verify process_deal was called for each deal
        assert mock_process_deal.call_count == 2

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.SessionLocal')
    @patch('app.tasks.hubspot_tasks.get_hubspot_connector')
    async def test_sync_deals_pagination(self, mock_get_connector, mock_session):
        """Test deal synchronization with pagination."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.is_active = True
        mock_connection.connection_settings = {}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock HubSpot connector with pagination
        mock_connector = Mock()
        # First call returns 100 deals, second call returns 50 deals (end of data)
        mock_connector.get_deals = AsyncMock(side_effect=[
            {"results": [{"id": f"deal-{i}", "properties": {}} for i in range(100)]},
            {"results": [{"id": f"deal-{i}", "properties": {}} for i in range(100, 150)]},
            {"results": []}  # Empty response indicates end
        ])
        mock_get_connector.return_value = mock_connector
        
        # Mock process_deal to track calls
        with patch('app.tasks.hubspot_tasks.process_hubspot_deal') as mock_process_deal:
            mock_process_deal.return_value = {"success": True}
            
            # Execute test
            result = await sync_hubspot_deals("conn-123", days_back=30)
            
            # Verify pagination worked
            assert mock_connector.get_deals.call_count == 3  # 3 API calls
            # No deals should be processed as they don't match date filter
            assert result["details"]["total_deals_fetched"] == 0  # Filtered out by date


class TestBatchProcessHubSpotDeals:
    """Test cases for batch_process_hubspot_deals function."""

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.sync_hubspot_deals')
    async def test_batch_process_success(self, mock_sync_deals):
        """Test successful batch processing."""
        # Mock sync_deals to return success for all connections
        mock_sync_deals.return_value = {
            "success": True,
            "details": {"processed_count": 5}
        }
        
        connection_ids = ["conn-1", "conn-2", "conn-3"]
        
        # Execute test
        result = await batch_process_hubspot_deals(connection_ids, days_back=30)
        
        # Verify results
        assert result["success"] is True
        assert result["details"]["total_connections"] == 3
        assert result["details"]["successful_connections"] == 3
        assert result["details"]["failed_connections"] == 0
        assert len(result["details"]["connection_results"]) == 3
        
        # Verify sync_deals was called for each connection
        assert mock_sync_deals.call_count == 3

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.sync_hubspot_deals')
    async def test_batch_process_with_failures(self, mock_sync_deals):
        """Test batch processing with some failures."""
        # Mock sync_deals to return mixed results
        mock_sync_deals.side_effect = [
            {"success": True, "details": {"processed_count": 5}},
            {"success": False, "message": "Connection failed"},
            {"success": True, "details": {"processed_count": 3}}
        ]
        
        connection_ids = ["conn-1", "conn-2", "conn-3"]
        
        # Execute test
        result = await batch_process_hubspot_deals(connection_ids)
        
        # Verify results
        assert result["success"] is False  # At least one failure
        assert result["details"]["successful_connections"] == 2
        assert result["details"]["failed_connections"] == 1


class TestHubSpotDealProcessorTask:
    """Test cases for hubspot_deal_processor_task function."""

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.SessionLocal')
    @patch('app.tasks.hubspot_tasks.batch_process_hubspot_deals')
    async def test_processor_task_success(self, mock_batch_process, mock_session):
        """Test successful processor task execution."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock active connections
        mock_conn1 = Mock()
        mock_conn1.id = "conn-1"
        mock_conn2 = Mock()
        mock_conn2.id = "conn-2"
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_conn1, mock_conn2]
        
        # Mock batch processing
        mock_batch_process.return_value = {"success": True}
        
        # Execute test
        await hubspot_deal_processor_task()
        
        # Verify batch processing was called with correct connection IDs
        mock_batch_process.assert_called_once_with(["conn-1", "conn-2"], days_back=1)

    @pytest.mark.asyncio
    @patch('app.tasks.hubspot_tasks.SessionLocal')
    async def test_processor_task_no_connections(self, mock_session):
        """Test processor task when no active connections exist."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Mock no active connections
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Execute test (should not raise any errors)
        await hubspot_deal_processor_task()
        
        # Verify database was queried but no further processing occurred
        mock_db.query.assert_called_once()


class TestParseDateFunction:
    """Test cases for _parse_date utility function."""

    def test_parse_timestamp_milliseconds(self):
        """Test parsing timestamp in milliseconds."""
        # Test with millisecond timestamp (December 20, 2023)
        timestamp_ms = "1703030400000"
        result = _parse_date(timestamp_ms)
        
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 20

    def test_parse_iso_format(self):
        """Test parsing ISO format date."""
        iso_date = "2023-12-20T10:30:00Z"
        result = _parse_date(iso_date)
        
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 20

    def test_parse_none(self):
        """Test parsing None value."""
        result = _parse_date(None)
        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = _parse_date("")
        assert result is None

    def test_parse_invalid_format(self):
        """Test parsing invalid date format."""
        result = _parse_date("invalid-date")
        assert result is None  # Should not raise exception