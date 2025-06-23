"""
Salesforce Delta Sync Implementation.

This module provides efficient delta synchronization capabilities for Salesforce,
tracking changes and performing incremental updates to minimize API calls and processing time.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text

from app.integrations.crm.salesforce.connector import SalesforceConnector
from app.integrations.crm.salesforce.models import SalesforceDataValidator
from app.models.crm import CRMConnection, CRMDeal
from app.core.database import get_async_db
from app.core.logging import get_logger
from app.core.redis import get_redis_client

logger = get_logger(__name__)


class ChangeType(str, Enum):
    """Types of changes detected."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    STAGE_CHANGED = "stage_changed"
    AMOUNT_CHANGED = "amount_changed"


@dataclass
class ChangeRecord:
    """Record of a detected change."""
    external_id: str
    change_type: ChangeType
    field_changes: Dict[str, Tuple[Any, Any]]  # field_name: (old_value, new_value)
    timestamp: datetime
    source_data: Dict[str, Any]


@dataclass
class DeltaSyncConfig:
    """Configuration for delta synchronization."""
    lookback_hours: int = 24  # How far back to check for changes
    max_changes_per_sync: int = 1000  # Maximum changes to process per sync
    enable_field_level_tracking: bool = True
    track_deletion: bool = True
    hash_algorithm: str = "md5"
    cache_ttl_hours: int = 48
    batch_size: int = 50


@dataclass
class DeltaSyncResult:
    """Result of a delta synchronization."""
    success: bool
    changes_detected: int
    changes_processed: int
    created_records: int
    updated_records: int
    deleted_records: int
    failed_records: int
    errors: List[str]
    duration_seconds: float
    sync_timestamp: datetime
    next_sync_cursor: Optional[str]


class SalesforceDeltaSync:
    """Handles efficient delta synchronization with Salesforce."""
    
    def __init__(self, connection: CRMConnection, db_session: AsyncSession):
        """
        Initialize the delta sync manager.
        
        Args:
            connection: CRM connection configuration
            db_session: Database session
        """
        self.connection = connection
        self.db_session = db_session
        self.connector = SalesforceConnector(connection.credentials)
        self.validator = SalesforceDataValidator()
        
        # Configuration
        self.config = DeltaSyncConfig()
        if connection.connection_settings:
            self._update_config_from_settings(connection.connection_settings)
        
        # Redis client for caching
        self.redis_client = get_redis_client()
        
        # Cache keys
        self.cache_prefix = f"sf_delta_{connection.id}"
        self.hash_cache_key = f"{self.cache_prefix}:hashes"
        self.cursor_cache_key = f"{self.cache_prefix}:cursor"
        self.metadata_cache_key = f"{self.cache_prefix}:metadata"
    
    def _update_config_from_settings(self, settings: Dict[str, Any]):
        """Update configuration from connection settings."""
        delta_settings = settings.get("delta_sync", {})
        
        self.config.lookback_hours = delta_settings.get("lookback_hours", self.config.lookback_hours)
        self.config.max_changes_per_sync = delta_settings.get("max_changes_per_sync", self.config.max_changes_per_sync)
        self.config.enable_field_level_tracking = delta_settings.get("enable_field_level_tracking", self.config.enable_field_level_tracking)
        self.config.track_deletion = delta_settings.get("track_deletion", self.config.track_deletion)
        self.config.batch_size = delta_settings.get("batch_size", self.config.batch_size)
    
    async def perform_delta_sync(
        self,
        force_full_comparison: bool = False,
        stage_filter: Optional[List[str]] = None
    ) -> DeltaSyncResult:
        """
        Perform delta synchronization.
        
        Args:
            force_full_comparison: Force comparison of all records instead of using timestamp
            stage_filter: Filter by specific opportunity stages
            
        Returns:
            DeltaSyncResult with sync details
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting delta sync for connection {self.connection.id}")
            
            # Get the last sync cursor/timestamp
            last_sync_time = await self._get_last_sync_cursor()
            
            if not last_sync_time and not force_full_comparison:
                # First sync or no previous cursor - fall back to recent data
                last_sync_time = datetime.now() - timedelta(hours=self.config.lookback_hours)
            
            # Detect changes
            changes = await self._detect_changes(
                since=last_sync_time if not force_full_comparison else None,
                stage_filter=stage_filter
            )
            
            if not changes:
                logger.info("No changes detected")
                return DeltaSyncResult(
                    success=True,
                    changes_detected=0,
                    changes_processed=0,
                    created_records=0,
                    updated_records=0,
                    deleted_records=0,
                    failed_records=0,
                    errors=[],
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    sync_timestamp=datetime.now(),
                    next_sync_cursor=datetime.now().isoformat()
                )
            
            # Process changes
            result = await self._process_changes(changes)
            
            # Update sync cursor
            current_time = datetime.now()
            await self._update_sync_cursor(current_time.isoformat())
            
            # Update result with final details
            result.duration_seconds = (current_time - start_time).total_seconds()
            result.sync_timestamp = current_time
            result.next_sync_cursor = current_time.isoformat()
            
            logger.info(f"Delta sync completed: {result.changes_detected} changes detected, "
                       f"{result.changes_processed} processed, {result.failed_records} failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Delta sync failed: {str(e)}", exc_info=True)
            return DeltaSyncResult(
                success=False,
                changes_detected=0,
                changes_processed=0,
                created_records=0,
                updated_records=0,
                deleted_records=0,
                failed_records=0,
                errors=[str(e)],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                sync_timestamp=datetime.now(),
                next_sync_cursor=None
            )
    
    async def _detect_changes(
        self,
        since: Optional[datetime] = None,
        stage_filter: Optional[List[str]] = None
    ) -> List[ChangeRecord]:
        """Detect changes in Salesforce opportunities."""
        changes = []
        
        try:
            # Get current opportunities from Salesforce
            sf_opportunities = await self._get_salesforce_opportunities(since, stage_filter)
            
            # Get existing deals from local database
            local_deals = await self._get_local_deals()
            
            # Create lookup maps
            sf_lookup = {opp.get("Id"): opp for opp in sf_opportunities}
            local_lookup = {deal.external_deal_id: deal for deal in local_deals}
            
            # Get cached hashes for comparison
            cached_hashes = await self._get_cached_hashes()
            
            # Detect new and updated records
            for sf_id, sf_opp in sf_lookup.items():
                local_deal = local_lookup.get(sf_id)
                
                # Calculate current hash
                current_hash = self._calculate_record_hash(sf_opp)
                cached_hash = cached_hashes.get(sf_id)
                
                if not local_deal:
                    # New record
                    changes.append(ChangeRecord(
                        external_id=sf_id,
                        change_type=ChangeType.CREATED,
                        field_changes={},
                        timestamp=datetime.now(),
                        source_data=sf_opp
                    ))
                elif cached_hash != current_hash or self._force_update_needed(local_deal, sf_opp):
                    # Updated record
                    field_changes = self._detect_field_changes(local_deal, sf_opp)
                    change_type = self._determine_change_type(field_changes)
                    
                    changes.append(ChangeRecord(
                        external_id=sf_id,
                        change_type=change_type,
                        field_changes=field_changes,
                        timestamp=datetime.now(),
                        source_data=sf_opp
                    ))
                
                # Update hash cache
                cached_hashes[sf_id] = current_hash
            
            # Detect deleted records (if enabled)
            if self.config.track_deletion:
                for local_id, local_deal in local_lookup.items():
                    if local_id not in sf_lookup:
                        # Record was deleted in Salesforce
                        changes.append(ChangeRecord(
                            external_id=local_id,
                            change_type=ChangeType.DELETED,
                            field_changes={},
                            timestamp=datetime.now(),
                            source_data={}
                        ))
            
            # Update hash cache
            await self._update_cached_hashes(cached_hashes)
            
            # Limit changes if necessary
            if len(changes) > self.config.max_changes_per_sync:
                logger.warning(f"Too many changes detected ({len(changes)}), limiting to {self.config.max_changes_per_sync}")
                changes = changes[:self.config.max_changes_per_sync]
            
            logger.info(f"Detected {len(changes)} changes")
            return changes
            
        except Exception as e:
            logger.error(f"Failed to detect changes: {str(e)}")
            raise
    
    async def _get_salesforce_opportunities(
        self,
        since: Optional[datetime] = None,
        stage_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get opportunities from Salesforce."""
        try:
            # Build parameters for the query
            params = {
                "limit": self.config.max_changes_per_sync * 2,  # Get more than we need for safety
                "modified_since": since,
                "stage_names": stage_filter
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            result = await self.connector.get_opportunities(**params)
            return result.get("opportunities", [])
            
        except Exception as e:
            logger.error(f"Failed to get Salesforce opportunities: {str(e)}")
            raise
    
    async def _get_local_deals(self) -> List[CRMDeal]:
        """Get existing deals from local database."""
        try:
            result = await self.db_session.execute(
                select(CRMDeal).where(CRMDeal.connection_id == self.connection.id)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get local deals: {str(e)}")
            raise
    
    def _calculate_record_hash(self, record: Dict[str, Any]) -> str:
        """Calculate a hash for a record to detect changes."""
        try:
            # Extract key fields for hashing
            key_fields = [
                "Name", "Amount", "StageName", "CloseDate", "Probability",
                "LastModifiedDate", "Description"
            ]
            
            hash_data = {}
            for field in key_fields:
                value = record.get(field)
                if value is not None:
                    hash_data[field] = str(value)
            
            # Include account data if available
            if "Account" in record and record["Account"]:
                account = record["Account"]
                account_fields = ["Name", "BillingStreet", "BillingCity", "Phone"]
                for field in account_fields:
                    if field in account:
                        hash_data[f"Account.{field}"] = str(account[field])
            
            # Sort for consistent hashing
            sorted_data = json.dumps(hash_data, sort_keys=True)
            
            if self.config.hash_algorithm == "md5":
                return hashlib.md5(sorted_data.encode()).hexdigest()
            else:
                return hashlib.sha256(sorted_data.encode()).hexdigest()
                
        except Exception as e:
            logger.warning(f"Failed to calculate hash for record: {str(e)}")
            return ""
    
    def _force_update_needed(self, local_deal: CRMDeal, sf_opp: Dict[str, Any]) -> bool:
        """Check if an update is needed regardless of hash."""
        # Force update if local sync status is failed
        if local_deal.sync_status == "failed":
            return True
        
        # Force update if last sync is too old
        if local_deal.last_sync:
            age = datetime.now() - local_deal.last_sync
            if age.total_seconds() > (self.config.lookback_hours * 3600):
                return True
        
        return False
    
    def _detect_field_changes(
        self, 
        local_deal: CRMDeal, 
        sf_opp: Dict[str, Any]
    ) -> Dict[str, Tuple[Any, Any]]:
        """Detect specific field changes."""
        if not self.config.enable_field_level_tracking:
            return {}
        
        changes = {}
        
        # Map Salesforce fields to local fields
        field_mappings = {
            "Name": "deal_title",
            "Amount": "deal_amount",
            "StageName": "deal_stage",
            "Probability": "deal_probability"
        }
        
        for sf_field, local_field in field_mappings.items():
            sf_value = sf_opp.get(sf_field)
            local_value = getattr(local_deal, local_field, None)
            
            # Convert for comparison
            if sf_field == "Amount":
                sf_value = str(sf_value) if sf_value is not None else "0"
                local_value = local_value or "0"
            
            if str(sf_value) != str(local_value):
                changes[local_field] = (local_value, sf_value)
        
        return changes
    
    def _determine_change_type(self, field_changes: Dict[str, Tuple[Any, Any]]) -> ChangeType:
        """Determine the type of change based on field changes."""
        if "deal_stage" in field_changes:
            return ChangeType.STAGE_CHANGED
        elif "deal_amount" in field_changes:
            return ChangeType.AMOUNT_CHANGED
        else:
            return ChangeType.UPDATED
    
    async def _process_changes(self, changes: List[ChangeRecord]) -> DeltaSyncResult:
        """Process detected changes."""
        processed = 0
        created = 0
        updated = 0
        deleted = 0
        failed = 0
        errors = []
        
        # Process changes in batches
        for i in range(0, len(changes), self.config.batch_size):
            batch = changes[i:i + self.config.batch_size]
            
            batch_results = await self._process_change_batch(batch)
            
            processed += len(batch)
            created += batch_results["created"]
            updated += batch_results["updated"]
            deleted += batch_results["deleted"]
            failed += batch_results["failed"]
            errors.extend(batch_results["errors"])
            
            # Small delay between batches
            if i + self.config.batch_size < len(changes):
                await asyncio.sleep(0.5)
        
        return DeltaSyncResult(
            success=failed == 0,
            changes_detected=len(changes),
            changes_processed=processed,
            created_records=created,
            updated_records=updated,
            deleted_records=deleted,
            failed_records=failed,
            errors=errors,
            duration_seconds=0.0,  # Will be set by caller
            sync_timestamp=datetime.now(),
            next_sync_cursor=None  # Will be set by caller
        )
    
    async def _process_change_batch(self, changes: List[ChangeRecord]) -> Dict[str, Any]:
        """Process a batch of changes."""
        created = 0
        updated = 0
        deleted = 0
        failed = 0
        errors = []
        
        for change in changes:
            try:
                if change.change_type == ChangeType.CREATED:
                    await self._create_deal_from_change(change)
                    created += 1
                elif change.change_type in [ChangeType.UPDATED, ChangeType.STAGE_CHANGED, ChangeType.AMOUNT_CHANGED]:
                    await self._update_deal_from_change(change)
                    updated += 1
                elif change.change_type == ChangeType.DELETED:
                    await self._delete_deal_from_change(change)
                    deleted += 1
                    
            except Exception as e:
                failed += 1
                error_msg = f"Failed to process change for {change.external_id}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        return {
            "created": created,
            "updated": updated,
            "deleted": deleted,
            "failed": failed,
            "errors": errors
        }
    
    async def _create_deal_from_change(self, change: ChangeRecord):
        """Create a new deal from a change record."""
        # Validate the data
        if self.config.enable_field_level_tracking:
            validation_result = self.validator.validate_opportunity(change.source_data)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid opportunity data: {validation_result['issues']}")
        
        # Transform to deal format
        deal_data = self.connector.transform_opportunity_to_deal(change.source_data)
        
        # Create the deal
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
        
        logger.debug(f"Created deal {deal.id} from Salesforce opportunity {change.external_id}")
    
    async def _update_deal_from_change(self, change: ChangeRecord):
        """Update an existing deal from a change record."""
        # Get the existing deal
        result = await self.db_session.execute(
            select(CRMDeal).where(
                and_(
                    CRMDeal.connection_id == self.connection.id,
                    CRMDeal.external_deal_id == change.external_id
                )
            )
        )
        deal = result.scalar_one_or_none()
        
        if not deal:
            # Deal doesn't exist locally, create it
            await self._create_deal_from_change(change)
            return
        
        # Transform updated data
        deal_data = self.connector.transform_opportunity_to_deal(change.source_data)
        
        # Update the deal
        deal.deal_title = deal_data["deal_title"]
        deal.deal_amount = deal_data["deal_amount"]
        deal.deal_currency = deal_data["deal_currency"]
        deal.deal_stage = deal_data["deal_stage"]
        deal.deal_probability = deal_data.get("deal_probability")
        deal.customer_data = deal_data["customer_data"]
        deal.deal_data = deal_data["deal_data"]
        deal.updated_at_source = deal_data.get("updated_at_source")
        deal.closed_at_source = deal_data.get("closed_at_source")
        deal.last_sync = datetime.now()
        deal.sync_status = "success"
        
        await self.db_session.flush()
        
        logger.debug(f"Updated deal {deal.id} from Salesforce opportunity {change.external_id}")
    
    async def _delete_deal_from_change(self, change: ChangeRecord):
        """Handle deletion of a deal."""
        # Get the existing deal
        result = await self.db_session.execute(
            select(CRMDeal).where(
                and_(
                    CRMDeal.connection_id == self.connection.id,
                    CRMDeal.external_deal_id == change.external_id
                )
            )
        )
        deal = result.scalar_one_or_none()
        
        if deal:
            # Mark as deleted or actually delete based on configuration
            # For now, we'll just mark the sync status
            deal.sync_status = "deleted"
            deal.last_sync = datetime.now()
            await self.db_session.flush()
            
            logger.debug(f"Marked deal {deal.id} as deleted (Salesforce opportunity {change.external_id})")
    
    async def _get_last_sync_cursor(self) -> Optional[datetime]:
        """Get the last sync cursor/timestamp."""
        try:
            cursor_str = await self.redis_client.get(self.cursor_cache_key)
            if cursor_str:
                return datetime.fromisoformat(cursor_str.decode())
            
            # Fallback to connection's last sync time
            return self.connection.last_successful_sync
            
        except Exception as e:
            logger.warning(f"Failed to get sync cursor: {str(e)}")
            return self.connection.last_successful_sync
    
    async def _update_sync_cursor(self, cursor: str):
        """Update the sync cursor."""
        try:
            await self.redis_client.setex(
                self.cursor_cache_key,
                self.config.cache_ttl_hours * 3600,
                cursor
            )
        except Exception as e:
            logger.warning(f"Failed to update sync cursor: {str(e)}")
    
    async def _get_cached_hashes(self) -> Dict[str, str]:
        """Get cached record hashes."""
        try:
            cached_data = await self.redis_client.get(self.hash_cache_key)
            if cached_data:
                return json.loads(cached_data.decode())
            return {}
        except Exception as e:
            logger.warning(f"Failed to get cached hashes: {str(e)}")
            return {}
    
    async def _update_cached_hashes(self, hashes: Dict[str, str]):
        """Update cached record hashes."""
        try:
            await self.redis_client.setex(
                self.hash_cache_key,
                self.config.cache_ttl_hours * 3600,
                json.dumps(hashes)
            )
        except Exception as e:
            logger.warning(f"Failed to update cached hashes: {str(e)}")
    
    async def clear_cache(self):
        """Clear all cached data for this connection."""
        try:
            keys = [
                self.hash_cache_key,
                self.cursor_cache_key,
                self.metadata_cache_key
            ]
            
            for key in keys:
                await self.redis_client.delete(key)
            
            logger.info(f"Cleared delta sync cache for connection {self.connection.id}")
            
        except Exception as e:
            logger.warning(f"Failed to clear cache: {str(e)}")
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Get delta sync statistics."""
        try:
            # Get recent sync activity
            recent_deals_result = await self.db_session.execute(
                select(CRMDeal)
                .where(CRMDeal.connection_id == self.connection.id)
                .where(CRMDeal.last_sync >= datetime.now() - timedelta(hours=24))
                .order_by(desc(CRMDeal.last_sync))
            )
            recent_deals = recent_deals_result.scalars().all()
            
            # Calculate statistics
            total_deals = len(recent_deals)
            successful_syncs = len([d for d in recent_deals if d.sync_status == "success"])
            failed_syncs = len([d for d in recent_deals if d.sync_status == "failed"])
            
            # Get cache info
            cached_hashes = await self._get_cached_hashes()
            last_cursor = await self._get_last_sync_cursor()
            
            return {
                "connection_id": self.connection.id,
                "last_24_hours": {
                    "total_deals_synced": total_deals,
                    "successful_syncs": successful_syncs,
                    "failed_syncs": failed_syncs,
                    "success_rate": (successful_syncs / total_deals * 100) if total_deals > 0 else 0
                },
                "cache_info": {
                    "cached_records": len(cached_hashes),
                    "last_cursor": last_cursor.isoformat() if last_cursor else None
                },
                "configuration": {
                    "lookback_hours": self.config.lookback_hours,
                    "max_changes_per_sync": self.config.max_changes_per_sync,
                    "field_level_tracking": self.config.enable_field_level_tracking,
                    "track_deletion": self.config.track_deletion
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get sync statistics: {str(e)}")
            return {
                "connection_id": self.connection.id,
                "error": str(e)
            }


async def create_delta_sync(connection_id: str) -> SalesforceDeltaSync:
    """
    Create a delta sync manager for a specific connection.
    
    Args:
        connection_id: ID of the CRM connection
        
    Returns:
        SalesforceDeltaSync instance
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
        
        return SalesforceDeltaSync(connection, db_session)