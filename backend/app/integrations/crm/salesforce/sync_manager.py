"""
Salesforce Data Synchronization Manager.

This module provides bidirectional synchronization between Salesforce and TaxPoynt,
including batch processing for historical data import and delta sync for efficient updates.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.integrations.crm.salesforce.connector import SalesforceConnector
from app.integrations.crm.salesforce.models import (
    OpportunityToInvoiceTransformer,
    SalesforceDataValidator
)
from app.models.crm import CRMConnection, CRMDeal
from app.core.database import get_async_db
from app.core.logging import get_logger
from app.services.invoice_service import InvoiceService

logger = get_logger(__name__)


class SyncMode(str, Enum):
    """Synchronization modes."""
    FULL = "full"
    DELTA = "delta"
    BIDIRECTIONAL = "bidirectional"


class SyncDirection(str, Enum):
    """Synchronization directions."""
    FROM_SALESFORCE = "from_salesforce"
    TO_SALESFORCE = "to_salesforce"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    success: bool
    records_processed: int
    records_created: int
    records_updated: int
    records_failed: int
    errors: List[str]
    duration_seconds: float
    sync_timestamp: datetime


@dataclass
class SyncConfig:
    """Configuration for synchronization operations."""
    batch_size: int = 100
    max_retries: int = 3
    retry_delay_seconds: int = 5
    parallel_workers: int = 5
    enable_validation: bool = True
    auto_generate_invoices: bool = False
    stage_mappings: Dict[str, str] = None
    field_mappings: Dict[str, str] = None


class SalesforceSyncManager:
    """Manages bidirectional synchronization between Salesforce and TaxPoynt."""
    
    def __init__(self, connection: CRMConnection, db_session: AsyncSession):
        """
        Initialize the sync manager.
        
        Args:
            connection: CRM connection configuration
            db_session: Database session
        """
        self.connection = connection
        self.db_session = db_session
        self.connector = SalesforceConnector(connection.credentials)
        self.validator = SalesforceDataValidator()
        self.transformer = OpportunityToInvoiceTransformer()
        self.invoice_service = InvoiceService(db_session)
        
        # Default sync configuration
        self.config = SyncConfig()
        if connection.connection_settings:
            self._update_config_from_settings(connection.connection_settings)
    
    def _update_config_from_settings(self, settings: Dict[str, Any]):
        """Update sync configuration from connection settings."""
        sync_settings = settings.get("sync_settings", {})
        
        self.config.batch_size = sync_settings.get("batch_size", self.config.batch_size)
        self.config.max_retries = sync_settings.get("max_retries", self.config.max_retries)
        self.config.parallel_workers = sync_settings.get("parallel_workers", self.config.parallel_workers)
        self.config.enable_validation = sync_settings.get("enable_validation", self.config.enable_validation)
        self.config.auto_generate_invoices = sync_settings.get("auto_generate_invoices", self.config.auto_generate_invoices)
        self.config.stage_mappings = sync_settings.get("stage_mappings", {})
        self.config.field_mappings = sync_settings.get("field_mappings", {})
    
    async def sync_opportunities_from_salesforce(
        self,
        mode: SyncMode = SyncMode.DELTA,
        limit: Optional[int] = None,
        stage_filter: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> SyncResult:
        """
        Sync opportunities from Salesforce to TaxPoynt.
        
        Args:
            mode: Synchronization mode (full, delta, bidirectional)
            limit: Maximum number of records to process
            stage_filter: Filter by specific opportunity stages
            date_range: Date range for filtering (start_date, end_date)
            
        Returns:
            SyncResult with operation details
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting Salesforce sync in {mode} mode for connection {self.connection.id}")
            
            # Determine the date filter based on mode
            modified_since = None
            if mode == SyncMode.DELTA:
                modified_since = self.connection.last_successful_sync or (datetime.now() - timedelta(days=7))
            elif date_range:
                modified_since = date_range[0]
            
            # Get opportunities from Salesforce
            opportunities_result = await self.connector.get_opportunities(
                limit=limit or self.config.batch_size * 10,
                modified_since=modified_since,
                stage_names=stage_filter
            )
            
            opportunities = opportunities_result.get("opportunities", [])
            
            if not opportunities:
                logger.info("No opportunities found to sync")
                return SyncResult(
                    success=True,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    records_failed=0,
                    errors=[],
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    sync_timestamp=datetime.now()
                )
            
            # Process opportunities in batches
            total_processed = 0
            total_created = 0
            total_updated = 0
            total_failed = 0
            all_errors = []
            
            for i in range(0, len(opportunities), self.config.batch_size):
                batch = opportunities[i:i + self.config.batch_size]
                
                batch_result = await self._process_opportunity_batch(batch)
                
                total_processed += batch_result.records_processed
                total_created += batch_result.records_created
                total_updated += batch_result.records_updated
                total_failed += batch_result.records_failed
                all_errors.extend(batch_result.errors)
                
                # Small delay between batches to avoid overwhelming the system
                if i + self.config.batch_size < len(opportunities):
                    await asyncio.sleep(1)
            
            # Update connection statistics
            await self._update_connection_stats(
                deals_synced=total_processed,
                invoices_generated=0,  # Will be updated separately if auto-generation is enabled
                last_sync=datetime.now(),
                sync_successful=total_failed == 0
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = SyncResult(
                success=total_failed == 0,
                records_processed=total_processed,
                records_created=total_created,
                records_updated=total_updated,
                records_failed=total_failed,
                errors=all_errors,
                duration_seconds=duration,
                sync_timestamp=datetime.now()
            )
            
            logger.info(f"Salesforce sync completed: {total_processed} processed, "
                       f"{total_created} created, {total_updated} updated, "
                       f"{total_failed} failed in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Salesforce sync failed: {str(e)}", exc_info=True)
            return SyncResult(
                success=False,
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_failed=0,
                errors=[str(e)],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                sync_timestamp=datetime.now()
            )
    
    async def _process_opportunity_batch(self, opportunities: List[Dict[str, Any]]) -> SyncResult:
        """Process a batch of opportunities."""
        start_time = datetime.now()
        
        processed = 0
        created = 0
        updated = 0
        failed = 0
        errors = []
        
        # Process opportunities in parallel
        semaphore = asyncio.Semaphore(self.config.parallel_workers)
        
        async def process_single_opportunity(opportunity: Dict[str, Any]):
            nonlocal processed, created, updated, failed, errors
            
            async with semaphore:
                try:
                    result = await self._process_single_opportunity(opportunity)
                    processed += 1
                    
                    if result["action"] == "created":
                        created += 1
                    elif result["action"] == "updated":
                        updated += 1
                        
                except Exception as e:
                    failed += 1
                    error_msg = f"Failed to process opportunity {opportunity.get('Id', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
        
        # Execute all tasks
        tasks = [process_single_opportunity(opp) for opp in opportunities]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return SyncResult(
            success=failed == 0,
            records_processed=processed,
            records_created=created,
            records_updated=updated,
            records_failed=failed,
            errors=errors,
            duration_seconds=(datetime.now() - start_time).total_seconds(),
            sync_timestamp=datetime.now()
        )
    
    async def _process_single_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single opportunity."""
        opportunity_id = opportunity.get("Id")
        
        # Validate opportunity data if enabled
        if self.config.enable_validation:
            validation_result = self.validator.validate_opportunity(opportunity)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid opportunity data: {validation_result['issues']}")
        
        # Transform opportunity to deal format
        deal_data = self.connector.transform_opportunity_to_deal(opportunity)
        
        # Check if deal already exists
        existing_deal = await self._get_existing_deal(opportunity_id)
        
        if existing_deal:
            # Update existing deal
            await self._update_deal(existing_deal, deal_data)
            action = "updated"
            deal = existing_deal
        else:
            # Create new deal
            deal = await self._create_deal(deal_data)
            action = "created"
        
        # Auto-generate invoice if enabled and conditions are met
        if self.config.auto_generate_invoices and self._should_generate_invoice(deal_data):
            try:
                await self._generate_invoice_for_deal(deal)
            except Exception as e:
                logger.warning(f"Failed to auto-generate invoice for deal {deal.id}: {str(e)}")
        
        return {"action": action, "deal_id": deal.id}
    
    async def _get_existing_deal(self, external_deal_id: str) -> Optional[CRMDeal]:
        """Get existing deal by external ID."""
        result = await self.db_session.execute(
            select(CRMDeal).where(
                and_(
                    CRMDeal.connection_id == self.connection.id,
                    CRMDeal.external_deal_id == external_deal_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def _create_deal(self, deal_data: Dict[str, Any]) -> CRMDeal:
        """Create a new deal."""
        deal = CRMDeal(
            connection_id=self.connection.id,
            external_deal_id=deal_data["external_deal_id"],
            deal_title=deal_data["deal_title"],
            deal_amount=deal_data["deal_amount"],
            deal_currency=deal_data["deal_currency"],
            deal_stage=deal_data["deal_stage"],
            deal_probability=deal_data.get("deal_probability"),
            customer_data=deal_data["customer_data"],
            deal_data=deal_data["deal_data"],
            created_at_source=deal_data.get("created_at_source"),
            updated_at_source=deal_data.get("updated_at_source"),
            closed_at_source=deal_data.get("closed_at_source"),
            sync_status="success"
        )
        
        self.db_session.add(deal)
        await self.db_session.flush()
        return deal
    
    async def _update_deal(self, existing_deal: CRMDeal, deal_data: Dict[str, Any]):
        """Update an existing deal."""
        existing_deal.deal_title = deal_data["deal_title"]
        existing_deal.deal_amount = deal_data["deal_amount"]
        existing_deal.deal_currency = deal_data["deal_currency"]
        existing_deal.deal_stage = deal_data["deal_stage"]
        existing_deal.deal_probability = deal_data.get("deal_probability")
        existing_deal.customer_data = deal_data["customer_data"]
        existing_deal.deal_data = deal_data["deal_data"]
        existing_deal.updated_at_source = deal_data.get("updated_at_source")
        existing_deal.closed_at_source = deal_data.get("closed_at_source")
        existing_deal.last_sync = datetime.now()
        existing_deal.sync_status = "success"
        
        await self.db_session.flush()
    
    def _should_generate_invoice(self, deal_data: Dict[str, Any]) -> bool:
        """Determine if an invoice should be generated for a deal."""
        stage = deal_data.get("deal_stage", "").lower()
        
        # Check stage mappings from configuration
        if self.config.stage_mappings:
            action = self.config.stage_mappings.get(stage, "no_action")
            return action == "generate_invoice"
        
        # Default logic: generate invoice for closed-won opportunities
        closed_won_stages = ["closed won", "closedwon", "won", "completed", "delivered"]
        return stage in closed_won_stages
    
    async def _generate_invoice_for_deal(self, deal: CRMDeal):
        """Generate an invoice for a deal."""
        if deal.invoice_generated:
            return  # Invoice already generated
        
        try:
            # Transform deal to invoice format
            invoice_data = self.transformer.transform_opportunity_to_invoice(
                deal.deal_data,
                self.connection.connection_settings
            )
            
            # Create invoice through invoice service
            invoice = await self.invoice_service.create_invoice(
                organization_id=self.connection.organization_id,
                invoice_data=invoice_data
            )
            
            # Update deal with invoice information
            deal.invoice_generated = True
            deal.invoice_data = {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "generated_at": datetime.now().isoformat()
            }
            
            await self.db_session.flush()
            
            logger.info(f"Generated invoice {invoice.invoice_number} for deal {deal.id}")
            
        except Exception as e:
            logger.error(f"Failed to generate invoice for deal {deal.id}: {str(e)}")
            raise
    
    async def sync_invoices_to_salesforce(
        self,
        limit: Optional[int] = None,
        modified_since: Optional[datetime] = None
    ) -> SyncResult:
        """
        Sync invoices from TaxPoynt back to Salesforce as custom objects or notes.
        
        Args:
            limit: Maximum number of invoices to process
            modified_since: Only sync invoices modified since this date
            
        Returns:
            SyncResult with operation details
        """
        start_time = datetime.now()
        
        try:
            logger.info("Starting invoice sync to Salesforce")
            
            # Get invoices that need to be synced to Salesforce
            invoices = await self._get_invoices_for_salesforce_sync(limit, modified_since)
            
            if not invoices:
                logger.info("No invoices found to sync to Salesforce")
                return SyncResult(
                    success=True,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    records_failed=0,
                    errors=[],
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    sync_timestamp=datetime.now()
                )
            
            # Process invoices
            processed = 0
            created = 0
            failed = 0
            errors = []
            
            for invoice in invoices:
                try:
                    await self._sync_invoice_to_salesforce(invoice)
                    processed += 1
                    created += 1
                except Exception as e:
                    failed += 1
                    error_msg = f"Failed to sync invoice {invoice.id} to Salesforce: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = SyncResult(
                success=failed == 0,
                records_processed=processed,
                records_created=created,
                records_updated=0,
                records_failed=failed,
                errors=errors,
                duration_seconds=duration,
                sync_timestamp=datetime.now()
            )
            
            logger.info(f"Invoice sync to Salesforce completed: {processed} processed, "
                       f"{failed} failed in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Invoice sync to Salesforce failed: {str(e)}", exc_info=True)
            return SyncResult(
                success=False,
                records_processed=0,
                records_created=0,
                records_updated=0,
                records_failed=0,
                errors=[str(e)],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                sync_timestamp=datetime.now()
            )
    
    async def _get_invoices_for_salesforce_sync(
        self,
        limit: Optional[int],
        modified_since: Optional[datetime]
    ) -> List[Any]:
        """Get invoices that need to be synced to Salesforce."""
        # This would query the invoice table for invoices related to Salesforce deals
        # that haven't been synced back to Salesforce yet
        # Implementation depends on the invoice model structure
        
        # Placeholder - would need actual invoice model and query logic
        return []
    
    async def _sync_invoice_to_salesforce(self, invoice):
        """Sync a single invoice to Salesforce."""
        # This would create a custom object, note, or attachment in Salesforce
        # with the invoice details and link it to the original opportunity
        
        # Placeholder - implementation would depend on Salesforce configuration
        pass
    
    async def perform_bidirectional_sync(
        self,
        sync_opportunities: bool = True,
        sync_invoices: bool = True,
        mode: SyncMode = SyncMode.DELTA
    ) -> Dict[str, SyncResult]:
        """
        Perform bidirectional synchronization.
        
        Args:
            sync_opportunities: Whether to sync opportunities from Salesforce
            sync_invoices: Whether to sync invoices to Salesforce
            mode: Synchronization mode
            
        Returns:
            Dict with sync results for each direction
        """
        results = {}
        
        if sync_opportunities:
            results["opportunities"] = await self.sync_opportunities_from_salesforce(mode=mode)
        
        if sync_invoices:
            results["invoices"] = await self.sync_invoices_to_salesforce()
        
        return results
    
    async def _update_connection_stats(
        self,
        deals_synced: int,
        invoices_generated: int,
        last_sync: datetime,
        sync_successful: bool
    ):
        """Update connection statistics."""
        self.connection.total_deals += deals_synced
        self.connection.total_invoices += invoices_generated
        self.connection.last_sync = last_sync
        
        if sync_successful:
            self.connection.last_successful_sync = last_sync
            self.connection.sync_error_count = 0
        else:
            self.connection.sync_error_count += 1
        
        await self.db_session.flush()
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status."""
        # Get recent deals
        recent_deals_result = await self.db_session.execute(
            select(CRMDeal)
            .where(CRMDeal.connection_id == self.connection.id)
            .order_by(desc(CRMDeal.last_sync))
            .limit(10)
        )
        recent_deals = recent_deals_result.scalars().all()
        
        # Calculate statistics
        total_deals = self.connection.total_deals
        total_invoices = self.connection.total_invoices
        last_sync = self.connection.last_sync
        last_successful_sync = self.connection.last_successful_sync
        
        # Get failed deals count
        failed_deals_result = await self.db_session.execute(
            select(CRMDeal)
            .where(
                and_(
                    CRMDeal.connection_id == self.connection.id,
                    CRMDeal.sync_status == "failed"
                )
            )
        )
        failed_deals_count = len(failed_deals_result.scalars().all())
        
        return {
            "connection_id": self.connection.id,
            "connection_name": self.connection.connection_name,
            "status": self.connection.status,
            "total_deals": total_deals,
            "total_invoices": total_invoices,
            "failed_deals": failed_deals_count,
            "last_sync": last_sync.isoformat() if last_sync else None,
            "last_successful_sync": last_successful_sync.isoformat() if last_successful_sync else None,
            "sync_error_count": self.connection.sync_error_count,
            "recent_deals": [
                {
                    "id": deal.id,
                    "external_id": deal.external_deal_id,
                    "title": deal.deal_title,
                    "amount": deal.deal_amount,
                    "stage": deal.deal_stage,
                    "last_sync": deal.last_sync.isoformat() if deal.last_sync else None,
                    "sync_status": deal.sync_status,
                    "invoice_generated": deal.invoice_generated
                }
                for deal in recent_deals
            ]
        }


async def create_sync_manager(connection_id: str) -> SalesforceSyncManager:
    """
    Create a sync manager for a specific connection.
    
    Args:
        connection_id: ID of the CRM connection
        
    Returns:
        SalesforceSyncManager instance
    """
    async with get_async_db() as db_session:
        # Get the connection
        result = await db_session.execute(
            select(CRMConnection).where(CRMConnection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        if connection.crm_type != "salesforce":
            raise ValueError(f"Connection {connection_id} is not a Salesforce connection")
        
        return SalesforceSyncManager(connection, db_session)