"""
Tests for Salesforce synchronization functionality.

This module contains comprehensive tests for the Salesforce integration,
including sync manager, batch processor, and delta sync components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from app.integrations.crm.salesforce.sync_manager import (
    SalesforceSyncManager,
    SyncMode,
    SyncResult,
    SyncConfig
)
from app.integrations.crm.salesforce.batch_processor import (
    SalesforceBatchProcessor,
    BatchJob,
    BatchStatus,
    BatchProgress
)
from app.integrations.crm.salesforce.delta_sync import (
    SalesforceDeltaSync,
    ChangeType,
    ChangeRecord,
    DeltaSyncResult
)
from app.models.crm import CRMConnection, CRMDeal


@pytest.fixture
def mock_connection():
    """Mock CRM connection."""
    connection = Mock(spec=CRMConnection)
    connection.id = "test_connection_id"
    connection.organization_id = "test_org_id"
    connection.crm_type = "salesforce"
    connection.connection_name = "Test Salesforce"
    connection.credentials = {
        "client_id": "test_client_id",
        "private_key": "test_private_key",
        "username": "test@example.com",
        "sandbox": True
    }
    connection.connection_settings = {
        "auto_sync": True,
        "sync_frequency": "daily",
        "stage_mappings": {
            "closedwon": "generate_invoice"
        }
    }
    connection.last_sync = None
    connection.last_successful_sync = None
    connection.total_deals = 0
    connection.total_invoices = 0
    connection.sync_error_count = 0
    return connection


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def sample_sf_opportunity():
    """Sample Salesforce opportunity data."""
    return {
        "Id": "0061234567890ABC",
        "Name": "Test Opportunity",
        "Amount": 50000.0,
        "CloseDate": "2023-12-31",
        "StageName": "Closed Won",
        "Probability": 100,
        "Type": "New Customer",
        "LeadSource": "Website",
        "Description": "Test opportunity description",
        "CreatedDate": "2023-01-01T00:00:00.000Z",
        "LastModifiedDate": "2023-12-01T10:30:00.000Z",
        "AccountId": "0011234567890ABC",
        "Account": {
            "Id": "0011234567890ABC",
            "Name": "Test Company",
            "BillingStreet": "123 Test St",
            "BillingCity": "Lagos",
            "BillingState": "Lagos",
            "BillingCountry": "Nigeria",
            "BillingPostalCode": "100001",
            "Phone": "+2341234567890"
        },
        "Owner": {
            "Id": "0051234567890ABC",
            "Name": "Test Owner",
            "Email": "owner@example.com"
        }
    }


class TestSalesforceSyncManager:
    """Tests for SalesforceSyncManager."""
    
    @pytest.fixture
    def sync_manager(self, mock_connection, mock_db_session):
        """Create sync manager instance."""
        with patch('app.integrations.crm.salesforce.sync_manager.SalesforceConnector'):
            manager = SalesforceSyncManager(mock_connection, mock_db_session)
            manager.connector = AsyncMock()
            manager.invoice_service = AsyncMock()
            return manager
    
    @pytest.mark.asyncio
    async def test_sync_opportunities_from_salesforce_success(self, sync_manager, sample_sf_opportunity):
        """Test successful opportunity synchronization."""
        # Mock connector response
        sync_manager.connector.get_opportunities.return_value = {
            "opportunities": [sample_sf_opportunity],
            "total_size": 1,
            "done": True
        }
        
        # Mock existing deal lookup
        sync_manager._get_existing_deal = AsyncMock(return_value=None)
        sync_manager._create_deal = AsyncMock()
        
        # Execute sync
        result = await sync_manager.sync_opportunities_from_salesforce(
            mode=SyncMode.DELTA,
            limit=100
        )
        
        # Assertions
        assert result.success is True
        assert result.records_processed == 1
        assert result.records_created == 1
        assert result.records_failed == 0
        
        # Verify connector was called
        sync_manager.connector.get_opportunities.assert_called_once()
        sync_manager._create_deal.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_opportunities_update_existing(self, sync_manager, sample_sf_opportunity):
        """Test updating existing opportunities."""
        # Mock existing deal
        existing_deal = Mock(spec=CRMDeal)
        existing_deal.id = "test_deal_id"
        existing_deal.external_deal_id = sample_sf_opportunity["Id"]
        
        # Mock connector response
        sync_manager.connector.get_opportunities.return_value = {
            "opportunities": [sample_sf_opportunity],
            "total_size": 1,
            "done": True
        }
        
        # Mock existing deal lookup
        sync_manager._get_existing_deal = AsyncMock(return_value=existing_deal)
        sync_manager._update_deal = AsyncMock()
        
        # Execute sync
        result = await sync_manager.sync_opportunities_from_salesforce()
        
        # Assertions
        assert result.success is True
        assert result.records_processed == 1
        assert result.records_updated == 1
        assert result.records_created == 0
        
        # Verify update was called
        sync_manager._update_deal.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_with_auto_invoice_generation(self, sync_manager, sample_sf_opportunity):
        """Test synchronization with automatic invoice generation."""
        # Enable auto invoice generation
        sync_manager.config.auto_generate_invoices = True
        
        # Mock connector response
        sync_manager.connector.get_opportunities.return_value = {
            "opportunities": [sample_sf_opportunity],
            "total_size": 1,
            "done": True
        }
        
        # Mock deal creation
        mock_deal = Mock(spec=CRMDeal)
        mock_deal.id = "test_deal_id"
        sync_manager._get_existing_deal = AsyncMock(return_value=None)
        sync_manager._create_deal = AsyncMock(return_value=mock_deal)
        sync_manager._should_generate_invoice = Mock(return_value=True)
        sync_manager._generate_invoice_for_deal = AsyncMock()
        
        # Execute sync
        result = await sync_manager.sync_opportunities_from_salesforce()
        
        # Assertions
        assert result.success is True
        sync_manager._generate_invoice_for_deal.assert_called_once_with(mock_deal)
    
    @pytest.mark.asyncio
    async def test_sync_handles_connector_error(self, sync_manager):
        """Test sync handles connector errors gracefully."""
        # Mock connector to raise exception
        sync_manager.connector.get_opportunities.side_effect = Exception("API Error")
        
        # Execute sync
        result = await sync_manager.sync_opportunities_from_salesforce()
        
        # Assertions
        assert result.success is False
        assert len(result.errors) == 1
        assert "API Error" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_should_generate_invoice_logic(self, sync_manager):
        """Test invoice generation decision logic."""
        # Test with stage mapping
        sync_manager.config.stage_mappings = {"closedwon": "generate_invoice"}
        
        deal_data = {"deal_stage": "closedwon"}
        assert sync_manager._should_generate_invoice(deal_data) is True
        
        deal_data = {"deal_stage": "open"}
        assert sync_manager._should_generate_invoice(deal_data) is False
        
        # Test default logic
        sync_manager.config.stage_mappings = {}
        
        deal_data = {"deal_stage": "closed won"}
        assert sync_manager._should_generate_invoice(deal_data) is True
        
        deal_data = {"deal_stage": "prospecting"}
        assert sync_manager._should_generate_invoice(deal_data) is False


class TestSalesforceBatchProcessor:
    """Tests for SalesforceBatchProcessor."""
    
    @pytest.fixture
    def batch_processor(self, mock_connection, mock_db_session):
        """Create batch processor instance."""
        with patch('app.integrations.crm.salesforce.batch_processor.SalesforceConnector'):
            processor = SalesforceBatchProcessor(mock_connection, mock_db_session)
            processor.connector = AsyncMock()
            processor.sync_manager = AsyncMock()
            return processor
    
    @pytest.mark.asyncio
    async def test_start_historical_import_success(self, batch_processor):
        """Test starting a historical import job."""
        # Mock total record count
        batch_processor._get_total_record_count = AsyncMock(return_value=1000)
        
        # Start import
        job_id = await batch_processor.start_historical_import(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            batch_size=50
        )
        
        # Assertions
        assert job_id is not None
        assert job_id in batch_processor.active_jobs
        
        job = batch_processor.active_jobs[job_id]
        assert job.total_records == 1000
        assert job.batch_size == 50
        assert job.status == BatchStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_total_record_count(self, batch_processor):
        """Test getting total record count."""
        # Mock connector response
        batch_processor.connector._make_api_request = AsyncMock(
            return_value={"totalSize": 500}
        )
        
        # Get count
        count = await batch_processor._get_total_record_count(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            stage_filter=["Closed Won"]
        )
        
        # Assertions
        assert count == 500
        batch_processor.connector._make_api_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_estimate_import_time(self, batch_processor):
        """Test import time estimation."""
        # Mock total record count
        batch_processor._get_total_record_count = AsyncMock(return_value=1000)
        
        # Get estimation
        estimation = await batch_processor.estimate_import_time(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            batch_size=50
        )
        
        # Assertions
        assert estimation["total_records"] == 1000
        assert estimation["total_batches"] == 20  # 1000 / 50
        assert "estimated_duration_hours" in estimation
        assert "estimated_completion" in estimation
    
    @pytest.mark.asyncio
    async def test_cancel_job(self, batch_processor):
        """Test job cancellation."""
        # Create a running job
        job = BatchJob(
            job_id="test_job",
            connection_id="test_conn",
            total_records=100,
            batch_size=10,
            status=BatchStatus.RUNNING
        )
        batch_processor.active_jobs["test_job"] = job
        
        # Cancel job
        success = await batch_processor.cancel_job("test_job")
        
        # Assertions
        assert success is True
        assert job.status == BatchStatus.CANCELLED
        assert job.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_retry_failed_job(self, batch_processor):
        """Test retrying a failed job."""
        # Create a failed job
        job = BatchJob(
            job_id="test_job",
            connection_id="test_conn",
            total_records=100,
            batch_size=10,
            status=BatchStatus.FAILED,
            error_message="Test error"
        )
        batch_processor.active_jobs["test_job"] = job
        
        # Mock execution
        with patch.object(batch_processor, '_execute_import_job') as mock_execute:
            # Retry job
            success = await batch_processor.retry_failed_job("test_job")
            
            # Assertions
            assert success is True
            assert job.status == BatchStatus.PENDING
            assert job.error_message is None
            mock_execute.assert_called_once()


class TestSalesforceDeltaSync:
    """Tests for SalesforceDeltaSync."""
    
    @pytest.fixture
    def delta_sync(self, mock_connection, mock_db_session):
        """Create delta sync instance."""
        with patch('app.integrations.crm.salesforce.delta_sync.SalesforceConnector'):
            delta = SalesforceDeltaSync(mock_connection, mock_db_session)
            delta.connector = AsyncMock()
            delta.redis_client = AsyncMock()
            return delta
    
    @pytest.mark.asyncio
    async def test_perform_delta_sync_success(self, delta_sync, sample_sf_opportunity):
        """Test successful delta synchronization."""
        # Mock dependencies
        delta_sync._get_last_sync_cursor = AsyncMock(
            return_value=datetime.now() - timedelta(hours=1)
        )
        delta_sync._detect_changes = AsyncMock(return_value=[
            ChangeRecord(
                external_id=sample_sf_opportunity["Id"],
                change_type=ChangeType.CREATED,
                field_changes={},
                timestamp=datetime.now(),
                source_data=sample_sf_opportunity
            )
        ])
        delta_sync._process_changes = AsyncMock(return_value=DeltaSyncResult(
            success=True,
            changes_detected=1,
            changes_processed=1,
            created_records=1,
            updated_records=0,
            deleted_records=0,
            failed_records=0,
            errors=[],
            duration_seconds=0.0,
            sync_timestamp=datetime.now(),
            next_sync_cursor=None
        ))
        delta_sync._update_sync_cursor = AsyncMock()
        
        # Execute delta sync
        result = await delta_sync.perform_delta_sync()
        
        # Assertions
        assert result.success is True
        assert result.changes_detected == 1
        assert result.changes_processed == 1
        assert result.created_records == 1
        
        # Verify methods were called
        delta_sync._detect_changes.assert_called_once()
        delta_sync._process_changes.assert_called_once()
        delta_sync._update_sync_cursor.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_changes_new_record(self, delta_sync, sample_sf_opportunity):
        """Test detecting new records."""
        # Mock Salesforce opportunities
        delta_sync._get_salesforce_opportunities = AsyncMock(
            return_value=[sample_sf_opportunity]
        )
        
        # Mock empty local deals
        delta_sync._get_local_deals = AsyncMock(return_value=[])
        
        # Mock cache operations
        delta_sync._get_cached_hashes = AsyncMock(return_value={})
        delta_sync._update_cached_hashes = AsyncMock()
        delta_sync._calculate_record_hash = Mock(return_value="test_hash")
        
        # Detect changes
        changes = await delta_sync._detect_changes()
        
        # Assertions
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.CREATED
        assert changes[0].external_id == sample_sf_opportunity["Id"]
    
    @pytest.mark.asyncio
    async def test_detect_changes_updated_record(self, delta_sync, sample_sf_opportunity):
        """Test detecting updated records."""
        # Mock existing local deal
        existing_deal = Mock(spec=CRMDeal)
        existing_deal.external_deal_id = sample_sf_opportunity["Id"]
        existing_deal.deal_title = "Old Title"
        existing_deal.deal_amount = "40000"
        existing_deal.deal_stage = "Open"
        
        # Mock dependencies
        delta_sync._get_salesforce_opportunities = AsyncMock(
            return_value=[sample_sf_opportunity]
        )
        delta_sync._get_local_deals = AsyncMock(return_value=[existing_deal])
        delta_sync._get_cached_hashes = AsyncMock(return_value={
            sample_sf_opportunity["Id"]: "old_hash"
        })
        delta_sync._update_cached_hashes = AsyncMock()
        delta_sync._calculate_record_hash = Mock(return_value="new_hash")
        delta_sync._force_update_needed = Mock(return_value=False)
        delta_sync._detect_field_changes = Mock(return_value={
            "deal_title": ("Old Title", "Test Opportunity"),
            "deal_amount": ("40000", "50000")
        })
        delta_sync._determine_change_type = Mock(return_value=ChangeType.UPDATED)
        
        # Detect changes
        changes = await delta_sync._detect_changes()
        
        # Assertions
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.UPDATED
        assert changes[0].external_id == sample_sf_opportunity["Id"]
        assert len(changes[0].field_changes) == 2
    
    @pytest.mark.asyncio
    async def test_detect_changes_deleted_record(self, delta_sync):
        """Test detecting deleted records."""
        # Configure to track deletions
        delta_sync.config.track_deletion = True
        
        # Mock existing local deal with no corresponding SF opportunity
        existing_deal = Mock(spec=CRMDeal)
        existing_deal.external_deal_id = "deleted_opportunity_id"
        
        # Mock dependencies
        delta_sync._get_salesforce_opportunities = AsyncMock(return_value=[])
        delta_sync._get_local_deals = AsyncMock(return_value=[existing_deal])
        delta_sync._get_cached_hashes = AsyncMock(return_value={})
        delta_sync._update_cached_hashes = AsyncMock()
        
        # Detect changes
        changes = await delta_sync._detect_changes()
        
        # Assertions
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.DELETED
        assert changes[0].external_id == "deleted_opportunity_id"
    
    @pytest.mark.asyncio
    async def test_calculate_record_hash(self, delta_sync, sample_sf_opportunity):
        """Test record hash calculation."""
        # Calculate hash
        hash1 = delta_sync._calculate_record_hash(sample_sf_opportunity)
        
        # Should be consistent
        hash2 = delta_sync._calculate_record_hash(sample_sf_opportunity)
        assert hash1 == hash2
        
        # Should change when data changes
        modified_opportunity = sample_sf_opportunity.copy()
        modified_opportunity["Amount"] = 60000.0
        hash3 = delta_sync._calculate_record_hash(modified_opportunity)
        assert hash1 != hash3
    
    @pytest.mark.asyncio
    async def test_process_change_batch_success(self, delta_sync, sample_sf_opportunity):
        """Test processing a batch of changes."""
        # Create test changes
        changes = [
            ChangeRecord(
                external_id=sample_sf_opportunity["Id"],
                change_type=ChangeType.CREATED,
                field_changes={},
                timestamp=datetime.now(),
                source_data=sample_sf_opportunity
            )
        ]
        
        # Mock processing methods
        delta_sync._create_deal_from_change = AsyncMock()
        
        # Process changes
        result = await delta_sync._process_change_batch(changes)
        
        # Assertions
        assert result["created"] == 1
        assert result["updated"] == 0
        assert result["failed"] == 0
        assert len(result["errors"]) == 0
        
        delta_sync._create_deal_from_change.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, delta_sync):
        """Test cache operations."""
        # Test updating cached hashes
        test_hashes = {"id1": "hash1", "id2": "hash2"}
        await delta_sync._update_cached_hashes(test_hashes)
        
        # Test getting cached hashes
        delta_sync.redis_client.get.return_value = '{"id1": "hash1", "id2": "hash2"}'.encode()
        cached_hashes = await delta_sync._get_cached_hashes()
        
        assert cached_hashes == test_hashes
    
    @pytest.mark.asyncio
    async def test_sync_cursor_operations(self, delta_sync):
        """Test sync cursor operations."""
        test_cursor = datetime.now().isoformat()
        
        # Test updating cursor
        await delta_sync._update_sync_cursor(test_cursor)
        
        # Test getting cursor
        delta_sync.redis_client.get.return_value = test_cursor.encode()
        cursor = await delta_sync._get_last_sync_cursor()
        
        assert cursor.isoformat() == test_cursor
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, delta_sync):
        """Test cache clearing."""
        await delta_sync.clear_cache()
        
        # Should delete all cache keys
        assert delta_sync.redis_client.delete.call_count == 3


class TestIntegrationScenarios:
    """Integration tests for complete synchronization scenarios."""
    
    @pytest.fixture
    def full_sync_setup(self, mock_connection, mock_db_session):
        """Set up complete sync environment."""
        with patch('app.integrations.crm.salesforce.sync_manager.SalesforceConnector'), \
             patch('app.integrations.crm.salesforce.batch_processor.SalesforceConnector'), \
             patch('app.integrations.crm.salesforce.delta_sync.SalesforceConnector'):
            
            sync_manager = SalesforceSyncManager(mock_connection, mock_db_session)
            batch_processor = SalesforceBatchProcessor(mock_connection, mock_db_session)
            delta_sync = SalesforceDeltaSync(mock_connection, mock_db_session)
            
            # Mock all connectors
            for component in [sync_manager, batch_processor, delta_sync]:
                component.connector = AsyncMock()
            
            return sync_manager, batch_processor, delta_sync
    
    @pytest.mark.asyncio
    async def test_full_sync_workflow(self, full_sync_setup, sample_sf_opportunity):
        """Test complete synchronization workflow."""
        sync_manager, batch_processor, delta_sync = full_sync_setup
        
        # 1. Initial batch import
        batch_processor._get_total_record_count = AsyncMock(return_value=1)
        batch_processor.sync_manager._process_opportunity_batch = AsyncMock(
            return_value=SyncResult(
                success=True,
                records_processed=1,
                records_created=1,
                records_updated=0,
                records_failed=0,
                errors=[],
                duration_seconds=1.0,
                sync_timestamp=datetime.now()
            )
        )
        
        job_id = await batch_processor.start_historical_import(batch_size=1)
        
        # Wait a bit for the async job to start
        await asyncio.sleep(0.1)
        
        # Check job status
        job_status = await batch_processor.get_job_status(job_id)
        assert job_status is not None
        
        # 2. Delta sync for new changes
        delta_sync._get_last_sync_cursor = AsyncMock(return_value=datetime.now() - timedelta(minutes=5))
        delta_sync._detect_changes = AsyncMock(return_value=[])
        
        delta_result = await delta_sync.perform_delta_sync()
        assert delta_result.success is True
        assert delta_result.changes_detected == 0
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, full_sync_setup):
        """Test error handling and recovery scenarios."""
        sync_manager, batch_processor, delta_sync = full_sync_setup
        
        # Test sync manager error recovery
        sync_manager.connector.get_opportunities.side_effect = [
            Exception("Network error"),  # First call fails
            {"opportunities": [], "total_size": 0, "done": True}  # Second call succeeds
        ]
        
        # First sync should fail
        result1 = await sync_manager.sync_opportunities_from_salesforce()
        assert result1.success is False
        
        # Second sync should succeed
        result2 = await sync_manager.sync_opportunities_from_salesforce()
        assert result2.success is True
    
    @pytest.mark.asyncio
    async def test_concurrent_sync_operations(self, full_sync_setup, sample_sf_opportunity):
        """Test concurrent synchronization operations."""
        sync_manager, batch_processor, delta_sync = full_sync_setup
        
        # Mock successful operations
        sync_manager.connector.get_opportunities.return_value = {
            "opportunities": [sample_sf_opportunity],
            "total_size": 1,
            "done": True
        }
        sync_manager._get_existing_deal = AsyncMock(return_value=None)
        sync_manager._create_deal = AsyncMock()
        
        delta_sync._get_last_sync_cursor = AsyncMock(return_value=datetime.now() - timedelta(hours=1))
        delta_sync._detect_changes = AsyncMock(return_value=[])
        delta_sync._process_changes = AsyncMock(return_value=DeltaSyncResult(
            success=True, changes_detected=0, changes_processed=0,
            created_records=0, updated_records=0, deleted_records=0,
            failed_records=0, errors=[], duration_seconds=0.0,
            sync_timestamp=datetime.now(), next_sync_cursor=None
        ))
        delta_sync._update_sync_cursor = AsyncMock()
        
        # Run both operations concurrently
        sync_task = sync_manager.sync_opportunities_from_salesforce()
        delta_task = delta_sync.perform_delta_sync()
        
        sync_result, delta_result = await asyncio.gather(sync_task, delta_task)
        
        # Both should succeed
        assert sync_result.success is True
        assert delta_result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])