"""
Data Sync Coordinator Service

This module coordinates data synchronization across multiple ERP systems
for SI operations, managing sync workflows, conflict resolution,
and ensuring data consistency across all integrated systems.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from collections import defaultdict, deque
import hashlib

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Direction of data synchronization"""
    BIDIRECTIONAL = "bidirectional"
    ERP_TO_PLATFORM = "erp_to_platform"
    PLATFORM_TO_ERP = "platform_to_erp"
    READ_ONLY = "read_only"


class SyncStrategy(Enum):
    """Synchronization strategies"""
    REAL_TIME = "real_time"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    MANUAL = "manual"
    HYBRID = "hybrid"


class SyncStatus(Enum):
    """Status of synchronization operations"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    CONFLICT = "conflict"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    LATEST_TIMESTAMP = "latest_timestamp"
    MANUAL_REVIEW = "manual_review"
    MERGE_FIELDS = "merge_fields"
    CUSTOM_LOGIC = "custom_logic"


class SyncPriority(Enum):
    """Priority levels for sync operations"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class SyncRule:
    """Defines a data synchronization rule"""
    rule_id: str
    rule_name: str
    source_erp: str
    target_erp: str
    entity_type: str
    field_mappings: Dict[str, str]
    sync_direction: SyncDirection
    sync_strategy: SyncStrategy
    conflict_resolution: ConflictResolution
    sync_frequency: Optional[str] = None  # cron expression
    filter_conditions: Dict[str, Any] = field(default_factory=dict)
    transformation_rules: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: SyncPriority = SyncPriority.NORMAL


@dataclass
class SyncConflict:
    """Represents a synchronization conflict"""
    conflict_id: str
    sync_operation_id: str
    entity_type: str
    entity_id: str
    source_erp: str
    target_erp: str
    conflicted_fields: List[str]
    source_values: Dict[str, Any]
    target_values: Dict[str, Any]
    detected_at: datetime
    resolution_strategy: Optional[ConflictResolution] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


@dataclass
class SyncOperation:
    """Represents a synchronization operation"""
    operation_id: str
    rule_id: str
    entity_type: str
    entity_ids: List[str]
    source_erp: str
    target_erp: str
    sync_direction: SyncDirection
    status: SyncStatus
    priority: SyncPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    error_details: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncMetrics:
    """Metrics for synchronization operations"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_records_synced: int = 0
    total_conflicts: int = 0
    resolved_conflicts: int = 0
    average_sync_duration: float = 0.0
    sync_throughput: float = 0.0  # records per minute
    error_rate: float = 0.0


@dataclass
class CoordinatorConfig:
    """Configuration for data sync coordinator"""
    max_concurrent_syncs: int = 5
    default_sync_timeout: int = 3600  # seconds
    conflict_resolution_timeout: int = 86400  # 24 hours
    enable_auto_conflict_resolution: bool = True
    enable_sync_monitoring: bool = True
    sync_log_retention_days: int = 30
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 60
    enable_performance_metrics: bool = True
    sync_state_storage_path: Optional[str] = None
    enable_change_tracking: bool = True


class DataSyncCoordinator:
    """
    Service for coordinating data synchronization across multiple ERP systems
    with conflict resolution, monitoring, and performance optimization.
    """
    
    def __init__(self, config: CoordinatorConfig):
        self.config = config
        self.sync_rules: Dict[str, SyncRule] = {}
        self.active_operations: Dict[str, SyncOperation] = {}
        self.sync_conflicts: Dict[str, SyncConflict] = {}
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.metrics = SyncMetrics()
        
        # Sync coordination state
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Sync semaphore for concurrency control
        self.sync_semaphore = asyncio.Semaphore(config.max_concurrent_syncs)
        
        # Change tracking
        self.change_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Setup storage
        if config.sync_state_storage_path:
            self.storage_path = Path(config.sync_state_storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = None
    
    async def start_coordinator(self) -> None:
        """Start the data sync coordinator"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting Data Sync Coordinator")
        
        # Start worker tasks
        for i in range(self.config.max_concurrent_syncs):
            task = asyncio.create_task(self._sync_worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        # Start monitoring task
        if self.config.enable_sync_monitoring:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Load existing sync rules
        await self._load_sync_rules()
    
    async def stop_coordinator(self) -> None:
        """Stop the data sync coordinator"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping Data Sync Coordinator")
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(
            *[t for t in self.worker_tasks + [self.monitoring_task] if t],
            return_exceptions=True
        )
        
        self.worker_tasks.clear()
        
        # Save current state
        await self._save_sync_state()
    
    async def register_sync_rule(self, rule: SyncRule) -> bool:
        """Register a new synchronization rule"""
        try:
            # Validate rule
            if not await self._validate_sync_rule(rule):
                return False
            
            # Store rule
            self.sync_rules[rule.rule_id] = rule
            
            # Save to storage
            await self._save_sync_rule(rule)
            
            logger.info(f"Registered sync rule: {rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register sync rule {rule.rule_id}: {e}")
            return False
    
    async def schedule_sync(
        self,
        rule_id: str,
        entity_ids: Optional[List[str]] = None,
        priority: SyncPriority = SyncPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Schedule a synchronization operation"""
        try:
            rule = self.sync_rules.get(rule_id)
            if not rule:
                logger.error(f"Sync rule {rule_id} not found")
                return None
            
            # Create sync operation
            operation_id = self._generate_operation_id(rule)
            
            operation = SyncOperation(
                operation_id=operation_id,
                rule_id=rule_id,
                entity_type=rule.entity_type,
                entity_ids=entity_ids or [],
                source_erp=rule.source_erp,
                target_erp=rule.target_erp,
                sync_direction=rule.sync_direction,
                status=SyncStatus.PENDING,
                priority=priority,
                created_at=datetime.now(),
                metadata=metadata or {}
            )
            
            # Add to active operations
            self.active_operations[operation_id] = operation
            
            # Queue for processing
            await self.sync_queue.put(operation)
            
            self.metrics.total_operations += 1
            
            logger.info(f"Scheduled sync operation {operation_id} for rule {rule_id}")
            return operation_id
            
        except Exception as e:
            logger.error(f"Failed to schedule sync for rule {rule_id}: {e}")
            return None
    
    async def _sync_worker(self, worker_name: str) -> None:
        """Worker task for processing sync operations"""
        logger.info(f"Starting sync worker: {worker_name}")
        
        while self.is_running:
            try:
                # Get operation from queue
                operation = await asyncio.wait_for(self.sync_queue.get(), timeout=1.0)
                
                # Process operation
                await self._process_sync_operation(operation, worker_name)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Sync worker {worker_name} error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info(f"Sync worker {worker_name} stopped")
    
    async def _process_sync_operation(
        self,
        operation: SyncOperation,
        worker_name: str
    ) -> None:
        """Process a single sync operation"""
        async with self.sync_semaphore:
            try:
                operation.status = SyncStatus.RUNNING
                operation.started_at = datetime.now()
                
                logger.info(f"Worker {worker_name} processing sync {operation.operation_id}")
                
                # Get sync rule
                rule = self.sync_rules.get(operation.rule_id)
                if not rule:
                    raise Exception(f"Sync rule {operation.rule_id} not found")
                
                # Perform synchronization based on direction
                if operation.sync_direction == SyncDirection.ERP_TO_PLATFORM:
                    await self._sync_erp_to_platform(operation, rule)
                elif operation.sync_direction == SyncDirection.PLATFORM_TO_ERP:
                    await self._sync_platform_to_erp(operation, rule)
                elif operation.sync_direction == SyncDirection.BIDIRECTIONAL:
                    await self._sync_bidirectional(operation, rule)
                
                # Update operation status
                if operation.conflicts_detected > 0 and operation.conflicts_resolved < operation.conflicts_detected:
                    operation.status = SyncStatus.CONFLICT
                else:
                    operation.status = SyncStatus.COMPLETED
                    self.metrics.successful_operations += 1
                
                # Update metrics
                self.metrics.total_records_synced += operation.processed_records
                
            except Exception as e:
                logger.error(f"Sync operation {operation.operation_id} failed: {e}")
                operation.status = SyncStatus.FAILED
                operation.error_details.append({
                    "error": str(e),
                    "timestamp": datetime.now(),
                    "worker": worker_name
                })
                self.metrics.failed_operations += 1
            
            finally:
                operation.completed_at = datetime.now()
                
                # Calculate duration and update metrics
                if operation.started_at:
                    duration = (operation.completed_at - operation.started_at).total_seconds()
                    self._update_duration_metrics(duration)
    
    async def _sync_erp_to_platform(self, operation: SyncOperation, rule: SyncRule) -> None:
        """Synchronize data from ERP to platform"""
        try:
            # Extract data from source ERP
            source_data = await self._extract_source_data(operation, rule)
            operation.total_records = len(source_data)
            
            # Process each record
            for record in source_data:
                try:
                    # Transform data according to field mappings
                    transformed_data = await self._transform_record(record, rule)
                    
                    # Validate data
                    if await self._validate_record(transformed_data, rule):
                        # Check for conflicts
                        conflict = await self._detect_conflicts(
                            transformed_data, operation, rule
                        )
                        
                        if conflict:
                            # Handle conflict
                            resolved = await self._resolve_conflict(conflict, rule)
                            if resolved:
                                operation.conflicts_resolved += 1
                            operation.conflicts_detected += 1
                        else:
                            # Apply changes to target
                            await self._apply_changes_to_platform(transformed_data, operation, rule)
                            operation.processed_records += 1
                    else:
                        operation.failed_records += 1
                
                except Exception as e:
                    logger.error(f"Failed to process record in operation {operation.operation_id}: {e}")
                    operation.failed_records += 1
                    operation.error_details.append({
                        "record_error": str(e),
                        "timestamp": datetime.now()
                    })
        
        except Exception as e:
            logger.error(f"ERP to platform sync failed: {e}")
            raise
    
    async def _sync_platform_to_erp(self, operation: SyncOperation, rule: SyncRule) -> None:
        """Synchronize data from platform to ERP"""
        try:
            # Extract data from platform
            platform_data = await self._extract_platform_data(operation, rule)
            operation.total_records = len(platform_data)
            
            # Process each record
            for record in platform_data:
                try:
                    # Transform data for target ERP
                    transformed_data = await self._transform_record_for_erp(record, rule)
                    
                    # Validate data
                    if await self._validate_record_for_erp(transformed_data, rule):
                        # Check for conflicts
                        conflict = await self._detect_erp_conflicts(
                            transformed_data, operation, rule
                        )
                        
                        if conflict:
                            # Handle conflict
                            resolved = await self._resolve_conflict(conflict, rule)
                            if resolved:
                                operation.conflicts_resolved += 1
                            operation.conflicts_detected += 1
                        else:
                            # Apply changes to ERP
                            await self._apply_changes_to_erp(transformed_data, operation, rule)
                            operation.processed_records += 1
                    else:
                        operation.failed_records += 1
                
                except Exception as e:
                    logger.error(f"Failed to process record in operation {operation.operation_id}: {e}")
                    operation.failed_records += 1
        
        except Exception as e:
            logger.error(f"Platform to ERP sync failed: {e}")
            raise
    
    async def _sync_bidirectional(self, operation: SyncOperation, rule: SyncRule) -> None:
        """Perform bidirectional synchronization"""
        try:
            # First sync ERP to platform
            await self._sync_erp_to_platform(operation, rule)
            
            # Then sync platform to ERP for any changes
            await self._sync_platform_to_erp(operation, rule)
        
        except Exception as e:
            logger.error(f"Bidirectional sync failed: {e}")
            raise
    
    async def _extract_source_data(
        self,
        operation: SyncOperation,
        rule: SyncRule
    ) -> List[Dict[str, Any]]:
        """Extract data from source ERP system"""
        try:
            # This would integrate with the ERP data extractor
            # For now, return mock data
            return [
                {
                    "id": f"record_{i}",
                    "name": f"Sample Record {i}",
                    "amount": 100.0 + i,
                    "date": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                for i in range(5)  # Mock 5 records
            ]
        
        except Exception as e:
            logger.error(f"Failed to extract source data: {e}")
            return []
    
    async def _extract_platform_data(
        self,
        operation: SyncOperation,
        rule: SyncRule
    ) -> List[Dict[str, Any]]:
        """Extract data from platform"""
        try:
            # This would query the platform database
            # For now, return mock data
            return [
                {
                    "id": f"platform_record_{i}",
                    "name": f"Platform Record {i}",
                    "total": 150.0 + i,
                    "created_date": datetime.now().isoformat(),
                    "last_modified": datetime.now().isoformat()
                }
                for i in range(3)  # Mock 3 records
            ]
        
        except Exception as e:
            logger.error(f"Failed to extract platform data: {e}")
            return []
    
    async def _transform_record(
        self,
        record: Dict[str, Any],
        rule: SyncRule
    ) -> Dict[str, Any]:
        """Transform record according to field mappings"""
        try:
            transformed = {}
            
            # Apply field mappings
            for source_field, target_field in rule.field_mappings.items():
                if source_field in record:
                    transformed[target_field] = record[source_field]
            
            # Apply transformation rules
            for transform_rule in rule.transformation_rules:
                transformed = await self._apply_transformation_rule(transformed, transform_rule)
            
            return transformed
        
        except Exception as e:
            logger.error(f"Record transformation failed: {e}")
            return record
    
    async def _transform_record_for_erp(
        self,
        record: Dict[str, Any],
        rule: SyncRule
    ) -> Dict[str, Any]:
        """Transform record for ERP system"""
        try:
            # Reverse field mappings for ERP
            transformed = {}
            
            reverse_mappings = {v: k for k, v in rule.field_mappings.items()}
            
            for platform_field, erp_field in reverse_mappings.items():
                if platform_field in record:
                    transformed[erp_field] = record[platform_field]
            
            return transformed
        
        except Exception as e:
            logger.error(f"ERP record transformation failed: {e}")
            return record
    
    async def _apply_transformation_rule(
        self,
        record: Dict[str, Any],
        rule_name: str
    ) -> Dict[str, Any]:
        """Apply a specific transformation rule"""
        try:
            # Example transformation rules
            if rule_name == "uppercase_names":
                if "name" in record:
                    record["name"] = str(record["name"]).upper()
            
            elif rule_name == "round_amounts":
                for field in ["amount", "total", "price"]:
                    if field in record and isinstance(record[field], (int, float)):
                        record[field] = round(float(record[field]), 2)
            
            elif rule_name == "standardize_dates":
                for field in ["date", "created_date", "updated_at"]:
                    if field in record:
                        # Ensure ISO format
                        try:
                            dt = datetime.fromisoformat(str(record[field]))
                            record[field] = dt.isoformat()
                        except:
                            pass
            
            return record
        
        except Exception as e:
            logger.error(f"Transformation rule {rule_name} failed: {e}")
            return record
    
    async def _validate_record(
        self,
        record: Dict[str, Any],
        rule: SyncRule
    ) -> bool:
        """Validate transformed record"""
        try:
            # Apply validation rules
            for validation_rule in rule.validation_rules:
                if not await self._apply_validation_rule(record, validation_rule):
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Record validation failed: {e}")
            return False
    
    async def _validate_record_for_erp(
        self,
        record: Dict[str, Any],
        rule: SyncRule
    ) -> bool:
        """Validate record for ERP system"""
        try:
            # Basic validation for ERP format
            return len(record) > 0
        
        except Exception as e:
            logger.error(f"ERP record validation failed: {e}")
            return False
    
    async def _apply_validation_rule(
        self,
        record: Dict[str, Any],
        rule_name: str
    ) -> bool:
        """Apply a specific validation rule"""
        try:
            if rule_name == "required_fields":
                required = ["id", "name"]
                return all(field in record and record[field] for field in required)
            
            elif rule_name == "positive_amounts":
                for field in ["amount", "total", "price"]:
                    if field in record:
                        try:
                            value = float(record[field])
                            if value < 0:
                                return False
                        except (ValueError, TypeError):
                            return False
            
            elif rule_name == "valid_dates":
                for field in ["date", "created_date", "updated_at"]:
                    if field in record:
                        try:
                            datetime.fromisoformat(str(record[field]))
                        except:
                            return False
            
            return True
        
        except Exception as e:
            logger.error(f"Validation rule {rule_name} failed: {e}")
            return False
    
    async def _detect_conflicts(
        self,
        record: Dict[str, Any],
        operation: SyncOperation,
        rule: SyncRule
    ) -> Optional[SyncConflict]:
        """Detect conflicts when syncing to platform"""
        try:
            # Check if record exists in platform
            existing_record = await self._get_platform_record(record.get("id"), rule.entity_type)
            
            if existing_record:
                # Compare records to detect conflicts
                conflicted_fields = []
                source_values = {}
                target_values = {}
                
                for field, value in record.items():
                    if field in existing_record and existing_record[field] != value:
                        # Check if this is a meaningful conflict
                        if await self._is_meaningful_conflict(field, value, existing_record[field]):
                            conflicted_fields.append(field)
                            source_values[field] = value
                            target_values[field] = existing_record[field]
                
                if conflicted_fields:
                    conflict_id = self._generate_conflict_id(operation.operation_id, record.get("id"))
                    
                    conflict = SyncConflict(
                        conflict_id=conflict_id,
                        sync_operation_id=operation.operation_id,
                        entity_type=rule.entity_type,
                        entity_id=record.get("id"),
                        source_erp=rule.source_erp,
                        target_erp=rule.target_erp,
                        conflicted_fields=conflicted_fields,
                        source_values=source_values,
                        target_values=target_values,
                        detected_at=datetime.now(),
                        resolution_strategy=rule.conflict_resolution
                    )
                    
                    self.sync_conflicts[conflict_id] = conflict
                    return conflict
            
            return None
        
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return None
    
    async def _detect_erp_conflicts(
        self,
        record: Dict[str, Any],
        operation: SyncOperation,
        rule: SyncRule
    ) -> Optional[SyncConflict]:
        """Detect conflicts when syncing to ERP"""
        try:
            # Check if record exists in ERP
            existing_record = await self._get_erp_record(record.get("id"), rule.entity_type, rule.target_erp)
            
            if existing_record:
                # Similar conflict detection logic as for platform
                # Implementation would be similar to _detect_conflicts
                pass
            
            return None
        
        except Exception as e:
            logger.error(f"ERP conflict detection failed: {e}")
            return None
    
    async def _is_meaningful_conflict(
        self,
        field_name: str,
        source_value: Any,
        target_value: Any
    ) -> bool:
        """Determine if a field difference represents a meaningful conflict"""
        try:
            # Skip conflicts for timestamp fields
            if field_name in ["updated_at", "last_modified", "sync_timestamp"]:
                return False
            
            # Skip small numeric differences
            if isinstance(source_value, (int, float)) and isinstance(target_value, (int, float)):
                if abs(float(source_value) - float(target_value)) < 0.01:
                    return False
            
            # Consider empty vs null as same
            if not source_value and not target_value:
                return False
            
            return True
        
        except Exception:
            return True
    
    async def _resolve_conflict(
        self,
        conflict: SyncConflict,
        rule: SyncRule
    ) -> bool:
        """Resolve a synchronization conflict"""
        try:
            resolution_strategy = conflict.resolution_strategy or rule.conflict_resolution
            
            if resolution_strategy == ConflictResolution.SOURCE_WINS:
                # Use source values
                resolved_data = conflict.source_values
                
            elif resolution_strategy == ConflictResolution.TARGET_WINS:
                # Keep target values
                resolved_data = conflict.target_values
                
            elif resolution_strategy == ConflictResolution.LATEST_TIMESTAMP:
                # Use values from record with latest timestamp
                resolved_data = await self._resolve_by_timestamp(conflict)
                
            elif resolution_strategy == ConflictResolution.MERGE_FIELDS:
                # Merge non-conflicting fields
                resolved_data = await self._merge_conflict_fields(conflict)
                
            elif resolution_strategy == ConflictResolution.MANUAL_REVIEW:
                # Mark for manual review
                logger.info(f"Conflict {conflict.conflict_id} marked for manual review")
                return False
                
            else:
                # Default to source wins
                resolved_data = conflict.source_values
            
            # Apply resolution
            await self._apply_conflict_resolution(conflict, resolved_data)
            
            conflict.resolved_at = datetime.now()
            conflict.resolution_notes = f"Auto-resolved using {resolution_strategy.value}"
            
            self.metrics.resolved_conflicts += 1
            
            logger.info(f"Resolved conflict {conflict.conflict_id}")
            return True
        
        except Exception as e:
            logger.error(f"Conflict resolution failed for {conflict.conflict_id}: {e}")
            return False
    
    async def _resolve_by_timestamp(self, conflict: SyncConflict) -> Dict[str, Any]:
        """Resolve conflict by using latest timestamp"""
        try:
            # Get timestamps from both records
            source_timestamp = conflict.source_values.get("updated_at") or conflict.source_values.get("last_modified")
            target_timestamp = conflict.target_values.get("updated_at") or conflict.target_values.get("last_modified")
            
            if source_timestamp and target_timestamp:
                source_dt = datetime.fromisoformat(str(source_timestamp))
                target_dt = datetime.fromisoformat(str(target_timestamp))
                
                if source_dt > target_dt:
                    return conflict.source_values
                else:
                    return conflict.target_values
            
            # Default to source if timestamps not available
            return conflict.source_values
        
        except Exception as e:
            logger.error(f"Timestamp resolution failed: {e}")
            return conflict.source_values
    
    async def _merge_conflict_fields(self, conflict: SyncConflict) -> Dict[str, Any]:
        """Merge conflicted fields intelligently"""
        try:
            merged = {}
            
            for field in conflict.conflicted_fields:
                source_value = conflict.source_values.get(field)
                target_value = conflict.target_values.get(field)
                
                # Field-specific merge logic
                if field in ["name", "description"]:
                    # Use longer text
                    if len(str(source_value)) > len(str(target_value)):
                        merged[field] = source_value
                    else:
                        merged[field] = target_value
                
                elif field in ["amount", "total", "price"]:
                    # Use higher amount (assuming it's more recent)
                    try:
                        if float(source_value) > float(target_value):
                            merged[field] = source_value
                        else:
                            merged[field] = target_value
                    except (ValueError, TypeError):
                        merged[field] = source_value
                
                else:
                    # Default to source value
                    merged[field] = source_value
            
            return merged
        
        except Exception as e:
            logger.error(f"Field merge failed: {e}")
            return conflict.source_values
    
    async def _apply_conflict_resolution(
        self,
        conflict: SyncConflict,
        resolved_data: Dict[str, Any]
    ) -> None:
        """Apply the resolved data to the target system"""
        try:
            # This would update the target system with resolved data
            logger.debug(f"Applied conflict resolution for {conflict.conflict_id}")
        
        except Exception as e:
            logger.error(f"Failed to apply conflict resolution: {e}")
    
    async def _apply_changes_to_platform(
        self,
        data: Dict[str, Any],
        operation: SyncOperation,
        rule: SyncRule
    ) -> None:
        """Apply changes to platform database"""
        try:
            # This would update the platform database
            logger.debug(f"Applied changes to platform for operation {operation.operation_id}")
        
        except Exception as e:
            logger.error(f"Failed to apply changes to platform: {e}")
    
    async def _apply_changes_to_erp(
        self,
        data: Dict[str, Any],
        operation: SyncOperation,
        rule: SyncRule
    ) -> None:
        """Apply changes to ERP system"""
        try:
            # This would update the ERP system
            logger.debug(f"Applied changes to ERP for operation {operation.operation_id}")
        
        except Exception as e:
            logger.error(f"Failed to apply changes to ERP: {e}")
    
    async def _get_platform_record(
        self,
        record_id: str,
        entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing record from platform"""
        try:
            # This would query the platform database
            # For now, return None (no existing record)
            return None
        
        except Exception as e:
            logger.error(f"Failed to get platform record: {e}")
            return None
    
    async def _get_erp_record(
        self,
        record_id: str,
        entity_type: str,
        erp_system: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing record from ERP system"""
        try:
            # This would query the ERP system
            # For now, return None (no existing record)
            return None
        
        except Exception as e:
            logger.error(f"Failed to get ERP record: {e}")
            return None
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while self.is_running:
            try:
                await self._update_metrics()
                await self._cleanup_old_operations()
                await self._check_stuck_operations()
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _update_metrics(self) -> None:
        """Update performance metrics"""
        try:
            # Calculate success rate
            total_ops = self.metrics.total_operations
            if total_ops > 0:
                self.metrics.error_rate = (self.metrics.failed_operations / total_ops) * 100
            
            # Calculate throughput
            total_duration = 0
            operation_count = 0
            
            for operation in self.active_operations.values():
                if operation.completed_at and operation.started_at:
                    duration = (operation.completed_at - operation.started_at).total_seconds()
                    total_duration += duration
                    operation_count += 1
            
            if operation_count > 0:
                self.metrics.average_sync_duration = total_duration / operation_count
                
                # Calculate throughput (records per minute)
                if total_duration > 0:
                    self.metrics.sync_throughput = (self.metrics.total_records_synced / total_duration) * 60
            
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
    
    async def _cleanup_old_operations(self) -> None:
        """Clean up old completed operations"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.config.sync_log_retention_days)
            
            operations_to_remove = []
            for op_id, operation in self.active_operations.items():
                if (operation.status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED] and
                    operation.completed_at and operation.completed_at < cutoff_time):
                    operations_to_remove.append(op_id)
            
            for op_id in operations_to_remove:
                del self.active_operations[op_id]
            
            if operations_to_remove:
                logger.info(f"Cleaned up {len(operations_to_remove)} old operations")
                
        except Exception as e:
            logger.error(f"Operation cleanup failed: {e}")
    
    async def _check_stuck_operations(self) -> None:
        """Check for stuck operations and handle them"""
        try:
            current_time = datetime.now()
            timeout_threshold = timedelta(seconds=self.config.default_sync_timeout)
            
            for operation in self.active_operations.values():
                if (operation.status == SyncStatus.RUNNING and
                    operation.started_at and
                    current_time - operation.started_at > timeout_threshold):
                    
                    logger.warning(f"Operation {operation.operation_id} appears stuck, marking as failed")
                    operation.status = SyncStatus.FAILED
                    operation.completed_at = current_time
                    operation.error_details.append({
                        "error": "Operation timeout",
                        "timestamp": current_time
                    })
                    
        except Exception as e:
            logger.error(f"Stuck operation check failed: {e}")
    
    def _update_duration_metrics(self, duration: float) -> None:
        """Update duration metrics"""
        try:
            # Simple moving average for duration
            if self.metrics.average_sync_duration == 0:
                self.metrics.average_sync_duration = duration
            else:
                # Weighted average (new duration gets 20% weight)
                self.metrics.average_sync_duration = (
                    self.metrics.average_sync_duration * 0.8 + duration * 0.2
                )
        except Exception as e:
            logger.error(f"Duration metrics update failed: {e}")
    
    def _generate_operation_id(self, rule: SyncRule) -> str:
        """Generate unique operation ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rule_hash = hashlib.md5(rule.rule_id.encode()).hexdigest()[:8]
        return f"sync_{rule.entity_type}_{timestamp}_{rule_hash}"
    
    def _generate_conflict_id(self, operation_id: str, entity_id: str) -> str:
        """Generate unique conflict ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"conflict_{operation_id}_{entity_id}_{timestamp}"
    
    async def _validate_sync_rule(self, rule: SyncRule) -> bool:
        """Validate sync rule configuration"""
        try:
            # Check required fields
            if not rule.rule_id or not rule.source_erp or not rule.target_erp:
                return False
            
            # Check field mappings
            if not rule.field_mappings:
                return False
            
            # Check sync direction is valid
            if rule.sync_direction not in SyncDirection:
                return False
            
            return True
        
        except Exception:
            return False
    
    async def _save_sync_rule(self, rule: SyncRule) -> None:
        """Save sync rule to storage"""
        if not self.storage_path:
            return
        
        try:
            rule_file = self.storage_path / f"rule_{rule.rule_id}.json"
            rule_data = {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "source_erp": rule.source_erp,
                "target_erp": rule.target_erp,
                "entity_type": rule.entity_type,
                "field_mappings": rule.field_mappings,
                "sync_direction": rule.sync_direction.value,
                "sync_strategy": rule.sync_strategy.value,
                "conflict_resolution": rule.conflict_resolution.value,
                "enabled": rule.enabled,
                "priority": rule.priority.value
            }
            
            with open(rule_file, 'w') as f:
                json.dump(rule_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save sync rule: {e}")
    
    async def _load_sync_rules(self) -> None:
        """Load sync rules from storage"""
        if not self.storage_path:
            return
        
        try:
            for rule_file in self.storage_path.glob("rule_*.json"):
                with open(rule_file, 'r') as f:
                    rule_data = json.load(f)
                
                # Reconstruct rule object (simplified)
                logger.info(f"Loaded sync rule: {rule_data['rule_id']}")
                
        except Exception as e:
            logger.error(f"Failed to load sync rules: {e}")
    
    async def _save_sync_state(self) -> None:
        """Save current sync state"""
        if not self.storage_path:
            return
        
        try:
            state_data = {
                "metrics": {
                    "total_operations": self.metrics.total_operations,
                    "successful_operations": self.metrics.successful_operations,
                    "failed_operations": self.metrics.failed_operations,
                    "total_records_synced": self.metrics.total_records_synced
                },
                "timestamp": datetime.now().isoformat()
            }
            
            state_file = self.storage_path / "sync_state.json"
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save sync state: {e}")
    
    # Public API methods
    
    def get_sync_operation(self, operation_id: str) -> Optional[SyncOperation]:
        """Get sync operation by ID"""
        return self.active_operations.get(operation_id)
    
    def get_sync_conflicts(self) -> List[SyncConflict]:
        """Get all unresolved conflicts"""
        return [c for c in self.sync_conflicts.values() if not c.resolved_at]
    
    def get_sync_metrics(self) -> SyncMetrics:
        """Get current sync metrics"""
        return self.metrics
    
    def get_active_operations(self) -> List[SyncOperation]:
        """Get all active operations"""
        return list(self.active_operations.values())
    
    async def cancel_sync_operation(self, operation_id: str) -> bool:
        """Cancel a sync operation"""
        operation = self.active_operations.get(operation_id)
        if operation and operation.status in [SyncStatus.PENDING, SyncStatus.RUNNING]:
            operation.status = SyncStatus.CANCELLED
            operation.completed_at = datetime.now()
            return True
        return False


# Factory function for creating data sync coordinator
def create_data_sync_coordinator(config: Optional[CoordinatorConfig] = None) -> DataSyncCoordinator:
    """Factory function to create a data sync coordinator"""
    if config is None:
        config = CoordinatorConfig()
    
    return DataSyncCoordinator(config)