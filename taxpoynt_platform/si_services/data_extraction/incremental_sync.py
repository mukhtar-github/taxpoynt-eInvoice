"""
Incremental Sync Service

This module handles incremental data synchronization for efficient updates
and delta sync operations between ERP systems and the platform.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from pathlib import Path

from .erp_data_extractor import (
    InvoiceData, ExtractionFilter, ERPType, ERPDataExtractor, ExtractionResult
)

logger = logging.getLogger(__name__)


class SyncStrategy(Enum):
    """Synchronization strategies"""
    TIMESTAMP_BASED = "timestamp_based"
    SEQUENCE_BASED = "sequence_based"
    HASH_BASED = "hash_based"
    HYBRID = "hybrid"


class SyncStatus(Enum):
    """Status of sync operations"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    STOPPED = "stopped"


class ChangeType(Enum):
    """Types of changes detected"""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class SyncConfig:
    """Configuration for incremental synchronization"""
    sync_strategy: SyncStrategy = SyncStrategy.TIMESTAMP_BASED
    sync_interval_minutes: int = 30
    max_sync_batch_size: int = 500
    overlap_window_minutes: int = 5
    enable_change_detection: bool = True
    enable_conflict_resolution: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 30.0
    sync_state_storage_path: Optional[str] = None
    enable_deduplication: bool = True
    hash_algorithm: str = "sha256"


@dataclass
class SyncState:
    """Tracks the state of synchronization"""
    erp_type: ERPType
    last_sync_timestamp: Optional[datetime] = None
    last_sync_sequence: Optional[int] = None
    last_sync_hash: Optional[str] = None
    total_synced_records: int = 0
    failed_sync_count: int = 0
    last_sync_duration: float = 0.0
    sync_watermarks: Dict[str, Any] = field(default_factory=dict)
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChangeRecord:
    """Represents a detected change in the source system"""
    record_id: str
    change_type: ChangeType
    entity_type: str = "invoice"
    timestamp: Optional[datetime] = None
    sequence_number: Optional[int] = None
    current_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Result of a synchronization operation"""
    sync_id: str
    erp_type: ERPType
    status: SyncStatus
    start_time: datetime
    end_time: Optional[datetime]
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_deleted: int = 0
    records_failed: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    sync_duration: float = 0.0
    error_details: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class ConflictResolver:
    """Handles conflict resolution during synchronization"""
    
    def __init__(self, config: SyncConfig):
        self.config = config
    
    async def resolve_conflict(
        self,
        local_record: InvoiceData,
        remote_record: InvoiceData,
        conflict_type: str
    ) -> Tuple[InvoiceData, str]:
        """
        Resolve conflicts between local and remote records
        Returns: (resolved_record, resolution_strategy)
        """
        try:
            # Default resolution strategies
            if conflict_type == "timestamp_conflict":
                # Use the most recently updated record
                if local_record.updated_at > remote_record.updated_at:
                    return local_record, "local_wins_by_timestamp"
                else:
                    return remote_record, "remote_wins_by_timestamp"
            
            elif conflict_type == "content_conflict":
                # Merge non-conflicting fields
                resolved = await self._merge_records(local_record, remote_record)
                return resolved, "field_level_merge"
            
            elif conflict_type == "deletion_conflict":
                # Restore deleted record if it was modified remotely
                return remote_record, "restore_deleted"
            
            else:
                # Default to remote wins
                return remote_record, "remote_wins_default"
                
        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            # Fallback to remote wins
            return remote_record, "remote_wins_fallback"
    
    async def _merge_records(
        self,
        local_record: InvoiceData,
        remote_record: InvoiceData
    ) -> InvoiceData:
        """Merge two records at field level"""
        # For simplicity, this implementation uses remote values
        # In practice, you would implement field-specific merge logic
        return remote_record


class IncrementalSyncService:
    """
    Service for handling incremental data synchronization with ERP systems
    """
    
    def __init__(
        self,
        config: SyncConfig,
        data_extractor: ERPDataExtractor
    ):
        self.config = config
        self.data_extractor = data_extractor
        self.conflict_resolver = ConflictResolver(config)
        self.sync_states: Dict[ERPType, SyncState] = {}
        self.active_syncs: Dict[str, SyncResult] = {}
        self.record_hashes: Dict[str, str] = {}
        
        # Setup state storage
        if config.sync_state_storage_path:
            self.state_storage = Path(config.sync_state_storage_path)
            self.state_storage.mkdir(parents=True, exist_ok=True)
        else:
            self.state_storage = None
        
        # Load existing sync states
        asyncio.create_task(self._load_sync_states())
    
    async def start_incremental_sync(
        self,
        erp_type: ERPType,
        force_full_sync: bool = False
    ) -> str:
        """Start an incremental synchronization"""
        sync_id = f"sync_{erp_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        sync_result = SyncResult(
            sync_id=sync_id,
            erp_type=erp_type,
            status=SyncStatus.PENDING,
            start_time=datetime.now()
        )
        
        self.active_syncs[sync_id] = sync_result
        
        # Start sync in background
        asyncio.create_task(self._perform_sync(sync_result, force_full_sync))
        
        logger.info(f"Started incremental sync {sync_id} for {erp_type.value}")
        return sync_id
    
    async def _perform_sync(
        self,
        sync_result: SyncResult,
        force_full_sync: bool = False
    ) -> None:
        """Perform the actual synchronization"""
        try:
            sync_result.status = SyncStatus.RUNNING
            
            # Get or create sync state
            sync_state = self._get_sync_state(sync_result.erp_type)
            
            # Determine sync strategy
            if force_full_sync or not sync_state.last_sync_timestamp:
                await self._perform_full_sync(sync_result, sync_state)
            else:
                await self._perform_incremental_sync(sync_result, sync_state)
            
            # Update sync state
            sync_state.last_sync_timestamp = sync_result.start_time
            sync_state.total_synced_records += sync_result.records_processed
            sync_state.last_sync_duration = sync_result.sync_duration
            
            # Save sync state
            await self._save_sync_state(sync_result.erp_type, sync_state)
            
            sync_result.status = SyncStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Sync {sync_result.sync_id} failed: {e}")
            sync_result.status = SyncStatus.FAILED
            sync_result.error_details.append({
                "error": str(e),
                "timestamp": datetime.now(),
                "phase": "main_sync"
            })
        
        finally:
            sync_result.end_time = datetime.now()
            if sync_result.start_time:
                sync_result.sync_duration = (
                    sync_result.end_time - sync_result.start_time
                ).total_seconds()
    
    async def _perform_full_sync(
        self,
        sync_result: SyncResult,
        sync_state: SyncState
    ) -> None:
        """Perform a full synchronization"""
        logger.info(f"Performing full sync for {sync_result.erp_type.value}")
        
        # Create filter for full extraction
        extraction_filter = ExtractionFilter(
            batch_size=self.config.max_sync_batch_size,
            include_draft=False,
            include_cancelled=False
        )
        
        # Extract all data
        extraction_result = await self.data_extractor.extract_data(
            sync_result.erp_type,
            extraction_filter
        )
        
        sync_result.records_processed = extraction_result.extracted_records
        sync_result.records_created = extraction_result.extracted_records
        
        # Update watermarks
        sync_state.sync_watermarks["full_sync_completed"] = True
        sync_state.sync_watermarks["last_full_sync"] = datetime.now()
    
    async def _perform_incremental_sync(
        self,
        sync_result: SyncResult,
        sync_state: SyncState
    ) -> None:
        """Perform an incremental synchronization"""
        logger.info(f"Performing incremental sync for {sync_result.erp_type.value}")
        
        # Calculate sync window
        since_timestamp = sync_state.last_sync_timestamp
        if since_timestamp and self.config.overlap_window_minutes > 0:
            since_timestamp -= timedelta(minutes=self.config.overlap_window_minutes)
        
        # Detect changes
        changes = await self._detect_changes(sync_result.erp_type, since_timestamp)
        
        # Process changes
        for change in changes:
            try:
                await self._process_change(change, sync_result)
            except Exception as e:
                logger.error(f"Failed to process change {change.record_id}: {e}")
                sync_result.records_failed += 1
                sync_result.error_details.append({
                    "change_id": change.record_id,
                    "error": str(e),
                    "timestamp": datetime.now()
                })
        
        sync_result.records_processed = len(changes)
    
    async def _detect_changes(
        self,
        erp_type: ERPType,
        since_timestamp: Optional[datetime]
    ) -> List[ChangeRecord]:
        """Detect changes in the ERP system since the last sync"""
        changes = []
        
        try:
            # Build filter for change detection
            extraction_filter = ExtractionFilter(
                start_date=since_timestamp,
                batch_size=self.config.max_sync_batch_size
            )
            
            async with self.data_extractor.get_connection(erp_type) as adapter:
                # Extract modified records
                invoices = await adapter.extract_invoices(extraction_filter)
                
                for invoice in invoices:
                    change_type = await self._determine_change_type(invoice)
                    
                    change = ChangeRecord(
                        record_id=invoice.invoice_id,
                        change_type=change_type,
                        timestamp=invoice.updated_at,
                        current_hash=self._calculate_record_hash(invoice),
                        data=self._invoice_to_dict(invoice)
                    )
                    
                    changes.append(change)
        
        except Exception as e:
            logger.error(f"Change detection failed for {erp_type.value}: {e}")
            raise
        
        return changes
    
    async def _determine_change_type(self, invoice: InvoiceData) -> ChangeType:
        """Determine the type of change for a record"""
        record_id = invoice.invoice_id
        current_hash = self._calculate_record_hash(invoice)
        
        if record_id not in self.record_hashes:
            # New record
            self.record_hashes[record_id] = current_hash
            return ChangeType.CREATED
        
        previous_hash = self.record_hashes[record_id]
        if previous_hash != current_hash:
            # Updated record
            self.record_hashes[record_id] = current_hash
            return ChangeType.UPDATED
        
        # No change detected
        return ChangeType.UPDATED  # Default to updated for safety
    
    async def _process_change(
        self,
        change: ChangeRecord,
        sync_result: SyncResult
    ) -> None:
        """Process a detected change"""
        try:
            if change.change_type == ChangeType.CREATED:
                await self._handle_create(change, sync_result)
                sync_result.records_created += 1
                
            elif change.change_type == ChangeType.UPDATED:
                await self._handle_update(change, sync_result)
                sync_result.records_updated += 1
                
            elif change.change_type == ChangeType.DELETED:
                await self._handle_delete(change, sync_result)
                sync_result.records_deleted += 1
                
        except Exception as e:
            logger.error(f"Failed to process change {change.record_id}: {e}")
            raise
    
    async def _handle_create(
        self,
        change: ChangeRecord,
        sync_result: SyncResult
    ) -> None:
        """Handle creation of a new record"""
        logger.debug(f"Creating record {change.record_id}")
        # Implementation for handling new records
        pass
    
    async def _handle_update(
        self,
        change: ChangeRecord,
        sync_result: SyncResult
    ) -> None:
        """Handle update of an existing record"""
        logger.debug(f"Updating record {change.record_id}")
        
        # Check for conflicts if enabled
        if self.config.enable_conflict_resolution:
            conflict_detected = await self._detect_conflict(change)
            if conflict_detected:
                sync_result.conflicts_detected += 1
                await self._resolve_conflict(change, sync_result)
                sync_result.conflicts_resolved += 1
        
        # Implementation for handling record updates
        pass
    
    async def _handle_delete(
        self,
        change: ChangeRecord,
        sync_result: SyncResult
    ) -> None:
        """Handle deletion of a record"""
        logger.debug(f"Deleting record {change.record_id}")
        # Implementation for handling record deletions
        pass
    
    async def _detect_conflict(self, change: ChangeRecord) -> bool:
        """Detect if there's a conflict with the change"""
        # Simple conflict detection based on timestamps
        # In practice, this would be more sophisticated
        return False
    
    async def _resolve_conflict(
        self,
        change: ChangeRecord,
        sync_result: SyncResult
    ) -> None:
        """Resolve a detected conflict"""
        # Implementation for conflict resolution
        pass
    
    def _calculate_record_hash(self, invoice: InvoiceData) -> str:
        """Calculate hash for a record to detect changes"""
        # Create a stable representation of the record
        hash_data = {
            "invoice_number": invoice.invoice_number,
            "total_amount": invoice.total_amount,
            "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None,
            "status": invoice.status
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        
        if self.config.hash_algorithm == "sha256":
            return hashlib.sha256(hash_string.encode()).hexdigest()
        elif self.config.hash_algorithm == "md5":
            return hashlib.md5(hash_string.encode()).hexdigest()
        else:
            return hashlib.sha1(hash_string.encode()).hexdigest()
    
    def _invoice_to_dict(self, invoice: InvoiceData) -> Dict[str, Any]:
        """Convert invoice data to dictionary"""
        return {
            "invoice_id": invoice.invoice_id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "customer_id": invoice.customer_id,
            "customer_name": invoice.customer_name,
            "total_amount": invoice.total_amount,
            "status": invoice.status,
            "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None
        }
    
    def _get_sync_state(self, erp_type: ERPType) -> SyncState:
        """Get or create sync state for ERP type"""
        if erp_type not in self.sync_states:
            self.sync_states[erp_type] = SyncState(erp_type=erp_type)
        return self.sync_states[erp_type]
    
    async def _load_sync_states(self) -> None:
        """Load sync states from storage"""
        if not self.state_storage:
            return
        
        try:
            for erp_type in ERPType:
                state_file = self.state_storage / f"{erp_type.value}_sync_state.json"
                if state_file.exists():
                    with open(state_file, 'r') as f:
                        state_data = json.load(f)
                        sync_state = self._dict_to_sync_state(state_data)
                        self.sync_states[erp_type] = sync_state
                        
        except Exception as e:
            logger.error(f"Failed to load sync states: {e}")
    
    async def _save_sync_state(self, erp_type: ERPType, sync_state: SyncState) -> None:
        """Save sync state to storage"""
        if not self.state_storage:
            return
        
        try:
            state_data = self._sync_state_to_dict(sync_state)
            state_file = self.state_storage / f"{erp_type.value}_sync_state.json"
            
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save sync state for {erp_type.value}: {e}")
    
    def _dict_to_sync_state(self, data: Dict[str, Any]) -> SyncState:
        """Convert dictionary to SyncState object"""
        sync_state = SyncState(erp_type=ERPType(data["erp_type"]))
        
        if data.get("last_sync_timestamp"):
            sync_state.last_sync_timestamp = datetime.fromisoformat(data["last_sync_timestamp"])
        
        sync_state.last_sync_sequence = data.get("last_sync_sequence")
        sync_state.last_sync_hash = data.get("last_sync_hash")
        sync_state.total_synced_records = data.get("total_synced_records", 0)
        sync_state.failed_sync_count = data.get("failed_sync_count", 0)
        sync_state.last_sync_duration = data.get("last_sync_duration", 0.0)
        sync_state.sync_watermarks = data.get("sync_watermarks", {})
        sync_state.error_history = data.get("error_history", [])
        sync_state.metadata = data.get("metadata", {})
        
        return sync_state
    
    def _sync_state_to_dict(self, sync_state: SyncState) -> Dict[str, Any]:
        """Convert SyncState object to dictionary"""
        return {
            "erp_type": sync_state.erp_type.value,
            "last_sync_timestamp": sync_state.last_sync_timestamp.isoformat() if sync_state.last_sync_timestamp else None,
            "last_sync_sequence": sync_state.last_sync_sequence,
            "last_sync_hash": sync_state.last_sync_hash,
            "total_synced_records": sync_state.total_synced_records,
            "failed_sync_count": sync_state.failed_sync_count,
            "last_sync_duration": sync_state.last_sync_duration,
            "sync_watermarks": sync_state.sync_watermarks,
            "error_history": sync_state.error_history,
            "metadata": sync_state.metadata
        }
    
    async def get_sync_status(self, sync_id: str) -> Optional[SyncResult]:
        """Get status of a sync operation"""
        return self.active_syncs.get(sync_id)
    
    async def get_sync_state(self, erp_type: ERPType) -> Optional[SyncState]:
        """Get current sync state for ERP type"""
        return self.sync_states.get(erp_type)
    
    async def reset_sync_state(self, erp_type: ERPType) -> bool:
        """Reset sync state for ERP type"""
        try:
            if erp_type in self.sync_states:
                del self.sync_states[erp_type]
            
            # Remove state file
            if self.state_storage:
                state_file = self.state_storage / f"{erp_type.value}_sync_state.json"
                if state_file.exists():
                    state_file.unlink()
            
            logger.info(f"Reset sync state for {erp_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset sync state for {erp_type.value}: {e}")
            return False
    
    async def cleanup_old_syncs(self, max_age_hours: int = 24) -> int:
        """Clean up old sync results"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        syncs_to_remove = []
        for sync_id, sync_result in self.active_syncs.items():
            if (sync_result.status in [SyncStatus.COMPLETED, SyncStatus.FAILED] and
                sync_result.end_time and sync_result.end_time < cutoff_time):
                syncs_to_remove.append(sync_id)
        
        for sync_id in syncs_to_remove:
            del self.active_syncs[sync_id]
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old sync results")
        return cleaned_count


# Factory function for creating incremental sync service
def create_incremental_sync_service(
    config: Optional[SyncConfig] = None,
    data_extractor: Optional[ERPDataExtractor] = None
) -> IncrementalSyncService:
    """Factory function to create an incremental sync service"""
    if config is None:
        config = SyncConfig()
    
    if data_extractor is None:
        from .erp_data_extractor import erp_data_extractor
        data_extractor = erp_data_extractor
    
    return IncrementalSyncService(config, data_extractor)