"""
Sync Orchestrator Service

Orchestrates data synchronization processes across business systems.
Manages sync schedules, conflict resolution, and data consistency.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass, field
import json
from concurrent.futures import ThreadPoolExecutor
import hashlib

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Data synchronization direction"""
    BIDIRECTIONAL = "bidirectional"
    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"


class SyncStatus(Enum):
    """Synchronization status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    LATEST_TIMESTAMP = "latest_timestamp"
    MANUAL_REVIEW = "manual_review"
    MERGE_FIELDS = "merge_fields"
    SKIP_RECORD = "skip_record"


class SyncPriority(Enum):
    """Synchronization priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SyncMapping:
    """Field mapping configuration between systems"""
    source_field: str
    target_field: str
    transform_function: Optional[str] = None
    validation_rules: List[str] = field(default_factory=list)
    required: bool = False
    default_value: Any = None


@dataclass
class SyncFilter:
    """Data filtering configuration"""
    field: str
    operator: str  # eq, ne, gt, lt, in, contains, etc.
    value: Any
    logical_operator: str = "AND"  # AND, OR


@dataclass
class SyncConfiguration:
    """Synchronization configuration"""
    sync_id: str
    name: str
    source_system: str
    target_system: str
    direction: SyncDirection
    data_type: str  # invoices, customers, products, etc.
    
    # Scheduling
    schedule_type: str = "manual"  # manual, interval, cron
    schedule_interval: Optional[int] = None  # seconds
    schedule_cron: Optional[str] = None
    
    # Data handling
    field_mappings: List[SyncMapping] = field(default_factory=list)
    filters: List[SyncFilter] = field(default_factory=list)
    conflict_resolution: ConflictResolution = ConflictResolution.LATEST_TIMESTAMP
    batch_size: int = 100
    max_retries: int = 3
    priority: SyncPriority = SyncPriority.NORMAL
    
    # Options
    incremental_sync: bool = True
    preserve_timestamps: bool = True
    validate_data: bool = True
    dry_run: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    enabled: bool = True


@dataclass
class SyncRecord:
    """Individual record synchronization info"""
    source_id: str
    target_id: Optional[str] = None
    source_data: Dict[str, Any] = field(default_factory=dict)
    target_data: Dict[str, Any] = field(default_factory=dict)
    mapped_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    error_message: Optional[str] = None
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    sync_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SyncExecution:
    """Synchronization execution details"""
    execution_id: str
    sync_id: str
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None
    next_execution: Optional[datetime] = None


class DataTransformer:
    """Handle data transformation and mapping"""
    
    def __init__(self):
        self.transform_functions = {
            "uppercase": lambda x: str(x).upper() if x else None,
            "lowercase": lambda x: str(x).lower() if x else None,
            "trim": lambda x: str(x).strip() if x else None,
            "format_phone": self._format_phone,
            "format_date": self._format_date,
            "normalize_currency": self._normalize_currency,
            "extract_numbers": self._extract_numbers,
        }
    
    def register_transform_function(self, name: str, func: Callable):
        """Register custom transformation function"""
        self.transform_functions[name] = func
    
    async def transform_record(
        self, 
        source_data: Dict[str, Any], 
        mappings: List[SyncMapping]
    ) -> Dict[str, Any]:
        """Transform source record using field mappings"""
        transformed_data = {}
        
        for mapping in mappings:
            try:
                # Get source value
                source_value = self._get_nested_value(source_data, mapping.source_field)
                
                # Apply transformation if specified
                if mapping.transform_function and mapping.transform_function in self.transform_functions:
                    source_value = self.transform_functions[mapping.transform_function](source_value)
                
                # Use default if value is None and default is specified
                if source_value is None and mapping.default_value is not None:
                    source_value = mapping.default_value
                
                # Validate if required
                if mapping.required and source_value is None:
                    raise ValueError(f"Required field {mapping.source_field} is missing")
                
                # Apply validation rules
                if source_value is not None:
                    for rule in mapping.validation_rules:
                        if not await self._validate_value(source_value, rule):
                            raise ValueError(f"Validation failed for {mapping.source_field}: {rule}")
                
                # Set target value
                self._set_nested_value(transformed_data, mapping.target_field, source_value)
                
            except Exception as e:
                logger.error(f"Transformation error for field {mapping.source_field}: {e}")
                raise
        
        return transformed_data
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    async def _validate_value(self, value: Any, rule: str) -> bool:
        """Validate value against rule"""
        if rule == "not_empty":
            return value is not None and str(value).strip() != ""
        elif rule == "is_email":
            import re
            return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', str(value)))
        elif rule == "is_numeric":
            try:
                float(value)
                return True
            except:
                return False
        elif rule.startswith("min_length:"):
            min_len = int(rule.split(':')[1])
            return len(str(value)) >= min_len
        elif rule.startswith("max_length:"):
            max_len = int(rule.split(':')[1])
            return len(str(value)) <= max_len
        
        return True
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number"""
        if not phone:
            return None
        
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Format Nigerian number
        if len(digits) == 11 and digits.startswith('0'):
            return f"+234{digits[1:]}"
        elif len(digits) == 10:
            return f"+234{digits}"
        
        return phone
    
    def _format_date(self, date_value: Any) -> str:
        """Format date value"""
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        elif isinstance(date_value, str):
            try:
                parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return parsed_date.isoformat()
            except:
                return date_value
        
        return str(date_value) if date_value else None
    
    def _normalize_currency(self, amount: Any) -> float:
        """Normalize currency amount"""
        if isinstance(amount, (int, float)):
            return float(amount)
        elif isinstance(amount, str):
            # Remove currency symbols and commas
            cleaned = ''.join(c for c in amount if c.isdigit() or c in '.-')
            try:
                return float(cleaned)
            except:
                return 0.0
        
        return 0.0
    
    def _extract_numbers(self, text: str) -> str:
        """Extract only numbers from text"""
        if not text:
            return None
        return ''.join(filter(str.isdigit, str(text)))


class ConflictResolver:
    """Handle synchronization conflicts"""
    
    def __init__(self):
        self.resolution_strategies = {
            ConflictResolution.SOURCE_WINS: self._source_wins,
            ConflictResolution.TARGET_WINS: self._target_wins,
            ConflictResolution.LATEST_TIMESTAMP: self._latest_timestamp_wins,
            ConflictResolution.MERGE_FIELDS: self._merge_fields,
            ConflictResolution.SKIP_RECORD: self._skip_record,
        }
    
    async def resolve_conflict(
        self,
        source_record: Dict[str, Any],
        target_record: Dict[str, Any],
        strategy: ConflictResolution,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Resolve conflict between source and target records"""
        
        if strategy in self.resolution_strategies:
            return await self.resolution_strategies[strategy](
                source_record, target_record, metadata or {}
            )
        else:
            raise ValueError(f"Unknown conflict resolution strategy: {strategy}")
    
    async def _source_wins(
        self, 
        source_record: Dict[str, Any], 
        target_record: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Source record wins all conflicts"""
        return source_record
    
    async def _target_wins(
        self, 
        source_record: Dict[str, Any], 
        target_record: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Target record wins all conflicts"""
        return target_record
    
    async def _latest_timestamp_wins(
        self, 
        source_record: Dict[str, Any], 
        target_record: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record with latest timestamp wins"""
        source_timestamp = self._get_timestamp(source_record)
        target_timestamp = self._get_timestamp(target_record)
        
        if source_timestamp >= target_timestamp:
            return source_record
        else:
            return target_record
    
    async def _merge_fields(
        self, 
        source_record: Dict[str, Any], 
        target_record: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge non-conflicting fields"""
        merged = target_record.copy()
        
        for key, value in source_record.items():
            if key not in merged or merged[key] is None:
                merged[key] = value
            elif value is not None and value != merged[key]:
                # Field conflict - use source value by default
                merged[key] = value
        
        return merged
    
    async def _skip_record(
        self, 
        source_record: Dict[str, Any], 
        target_record: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Skip conflicted record"""
        raise ConflictError("Record skipped due to conflict")
    
    def _get_timestamp(self, record: Dict[str, Any]) -> datetime:
        """Extract timestamp from record"""
        timestamp_fields = ['updated_at', 'modified_at', 'last_modified', 'timestamp']
        
        for field in timestamp_fields:
            if field in record:
                timestamp = record[field]
                if isinstance(timestamp, datetime):
                    return timestamp
                elif isinstance(timestamp, str):
                    try:
                        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        pass
        
        # Default to epoch if no timestamp found
        return datetime(1970, 1, 1)


class ConflictError(Exception):
    """Exception raised when conflict cannot be resolved"""
    pass


class SyncOrchestrator:
    """Main synchronization orchestrator"""
    
    def __init__(self, max_workers: int = 4):
        self.configurations: Dict[str, SyncConfiguration] = {}
        self.executions: Dict[str, SyncExecution] = {}
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
        self.transformer = DataTransformer()
        self.conflict_resolver = ConflictResolver()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_syncs: Set[str] = set()
        
    async def register_sync(self, config: SyncConfiguration) -> bool:
        """
        Register synchronization configuration
        
        Args:
            config: Synchronization configuration
            
        Returns:
            Registration success status
        """
        try:
            sync_id = config.sync_id
            
            # Store configuration
            self.configurations[sync_id] = config
            
            # Schedule if configured
            if config.enabled and config.schedule_type != "manual":
                await self._schedule_sync(sync_id)
            
            logger.info(f"Registered sync configuration: {sync_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register sync {config.sync_id}: {e}")
            return False
    
    async def execute_sync(self, sync_id: str, force: bool = False) -> str:
        """
        Execute synchronization
        
        Args:
            sync_id: Synchronization identifier
            force: Force execution even if already running
            
        Returns:
            Execution ID
        """
        if sync_id not in self.configurations:
            raise ValueError(f"Sync configuration not found: {sync_id}")
        
        config = self.configurations[sync_id]
        
        if not config.enabled and not force:
            raise ValueError(f"Sync {sync_id} is disabled")
        
        if sync_id in self.running_syncs and not force:
            raise ValueError(f"Sync {sync_id} is already running")
        
        # Generate execution ID
        execution_id = f"{sync_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create execution record
        execution = SyncExecution(
            execution_id=execution_id,
            sync_id=sync_id,
            status=SyncStatus.PENDING,
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        
        # Start async execution
        asyncio.create_task(self._execute_sync_task(execution_id))
        
        return execution_id
    
    async def _execute_sync_task(self, execution_id: str):
        """Execute sync task asynchronously"""
        execution = self.executions[execution_id]
        config = self.configurations[execution.sync_id]
        
        try:
            self.running_syncs.add(execution.sync_id)
            execution.status = SyncStatus.RUNNING
            
            logger.info(f"Starting sync execution: {execution_id}")
            
            # Fetch source data
            source_data = await self._fetch_source_data(config)
            execution.total_records = len(source_data)
            
            # Process records in batches
            batch_size = config.batch_size
            for i in range(0, len(source_data), batch_size):
                batch = source_data[i:i + batch_size]
                await self._process_batch(execution, config, batch)
            
            # Update execution status
            execution.status = SyncStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.execution_time = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            logger.info(f"Sync execution completed: {execution_id}")
            
        except Exception as e:
            execution.status = SyncStatus.FAILED
            execution.errors.append(str(e))
            execution.completed_at = datetime.now()
            logger.error(f"Sync execution failed: {execution_id}, Error: {e}")
            
        finally:
            self.running_syncs.discard(execution.sync_id)
            
            # Schedule next execution if configured
            if config.schedule_type != "manual":
                execution.next_execution = await self._calculate_next_execution(config)
    
    async def _fetch_source_data(self, config: SyncConfiguration) -> List[Dict[str, Any]]:
        """Fetch data from source system"""
        # TODO: Implement actual data fetching from different systems
        # This would integrate with connection_manager and system-specific adapters
        
        # Mock data for demonstration
        mock_data = [
            {
                "id": f"record_{i}",
                "name": f"Record {i}",
                "email": f"user{i}@example.com",
                "amount": i * 100.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            for i in range(1, 11)
        ]
        
        # Apply filters
        filtered_data = await self._apply_filters(mock_data, config.filters)
        
        return filtered_data
    
    async def _apply_filters(
        self, 
        data: List[Dict[str, Any]], 
        filters: List[SyncFilter]
    ) -> List[Dict[str, Any]]:
        """Apply filters to data"""
        if not filters:
            return data
        
        filtered_data = []
        
        for record in data:
            include_record = True
            
            for filter_item in filters:
                field_value = self.transformer._get_nested_value(record, filter_item.field)
                
                if not self._evaluate_filter(field_value, filter_item):
                    include_record = False
                    if filter_item.logical_operator == "AND":
                        break
                    # For OR, continue checking other filters
            
            if include_record:
                filtered_data.append(record)
        
        return filtered_data
    
    def _evaluate_filter(self, value: Any, filter_item: SyncFilter) -> bool:
        """Evaluate single filter condition"""
        operator = filter_item.operator
        filter_value = filter_item.value
        
        if operator == "eq":
            return value == filter_value
        elif operator == "ne":
            return value != filter_value
        elif operator == "gt":
            return value > filter_value
        elif operator == "lt":
            return value < filter_value
        elif operator == "gte":
            return value >= filter_value
        elif operator == "lte":
            return value <= filter_value
        elif operator == "in":
            return value in filter_value
        elif operator == "contains":
            return filter_value in str(value)
        elif operator == "starts_with":
            return str(value).startswith(str(filter_value))
        elif operator == "ends_with":
            return str(value).endswith(str(filter_value))
        
        return False
    
    async def _process_batch(
        self, 
        execution: SyncExecution, 
        config: SyncConfiguration, 
        batch: List[Dict[str, Any]]
    ):
        """Process batch of records"""
        for record in batch:
            try:
                await self._process_record(execution, config, record)
                execution.processed_records += 1
                
            except Exception as e:
                execution.failed_records += 1
                execution.errors.append(f"Record {record.get('id', 'unknown')}: {str(e)}")
                logger.error(f"Failed to process record: {e}")
    
    async def _process_record(
        self, 
        execution: SyncExecution, 
        config: SyncConfiguration, 
        source_record: Dict[str, Any]
    ):
        """Process individual record"""
        sync_record = SyncRecord(
            source_id=str(source_record.get('id')),
            source_data=source_record
        )
        
        # Transform data
        try:
            mapped_data = await self.transformer.transform_record(
                source_record, 
                config.field_mappings
            )
            sync_record.mapped_data = mapped_data
            
        except Exception as e:
            sync_record.status = "failed"
            sync_record.error_message = f"Transformation failed: {str(e)}"
            raise
        
        # Check for existing record in target
        existing_record = await self._find_existing_record(config, sync_record)
        
        if existing_record:
            # Handle conflict resolution
            try:
                resolved_data = await self.conflict_resolver.resolve_conflict(
                    mapped_data,
                    existing_record,
                    config.conflict_resolution
                )
                sync_record.target_data = resolved_data
                
                # Update existing record
                if not config.dry_run:
                    await self._update_target_record(config, sync_record, resolved_data)
                
                sync_record.status = "updated"
                execution.successful_records += 1
                
            except ConflictError:
                sync_record.status = "skipped"
                execution.skipped_records += 1
                
        else:
            # Create new record
            sync_record.target_data = mapped_data
            
            if not config.dry_run:
                target_id = await self._create_target_record(config, sync_record, mapped_data)
                sync_record.target_id = target_id
            
            sync_record.status = "created"
            execution.successful_records += 1
    
    async def _find_existing_record(
        self, 
        config: SyncConfiguration, 
        sync_record: SyncRecord
    ) -> Optional[Dict[str, Any]]:
        """Find existing record in target system"""
        # TODO: Implement actual record lookup in target system
        # This would use connection_manager to query target system
        
        # Mock implementation - assume no existing records for demo
        return None
    
    async def _create_target_record(
        self, 
        config: SyncConfiguration, 
        sync_record: SyncRecord, 
        data: Dict[str, Any]
    ) -> str:
        """Create new record in target system"""
        # TODO: Implement actual record creation in target system
        # This would use connection_manager to create record
        
        # Mock implementation
        target_id = f"target_{sync_record.source_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Created target record: {target_id}")
        return target_id
    
    async def _update_target_record(
        self, 
        config: SyncConfiguration, 
        sync_record: SyncRecord, 
        data: Dict[str, Any]
    ):
        """Update existing record in target system"""
        # TODO: Implement actual record update in target system
        logger.info(f"Updated target record: {sync_record.target_id}")
    
    async def _schedule_sync(self, sync_id: str):
        """Schedule automatic sync execution"""
        config = self.configurations[sync_id]
        
        if config.schedule_type == "interval" and config.schedule_interval:
            # Schedule interval-based sync
            async def interval_task():
                while config.enabled:
                    await asyncio.sleep(config.schedule_interval)
                    if config.enabled:  # Check again after sleep
                        try:
                            await self.execute_sync(sync_id)
                        except Exception as e:
                            logger.error(f"Scheduled sync failed for {sync_id}: {e}")
            
            self.scheduled_tasks[sync_id] = asyncio.create_task(interval_task())
            
        elif config.schedule_type == "cron" and config.schedule_cron:
            # TODO: Implement cron-based scheduling
            logger.info(f"Cron scheduling not yet implemented for {sync_id}")
    
    async def _calculate_next_execution(self, config: SyncConfiguration) -> Optional[datetime]:
        """Calculate next execution time"""
        if config.schedule_type == "interval" and config.schedule_interval:
            return datetime.now() + timedelta(seconds=config.schedule_interval)
        elif config.schedule_type == "cron":
            # TODO: Calculate next cron execution time
            pass
        
        return None
    
    async def pause_sync(self, sync_id: str) -> bool:
        """Pause synchronization"""
        if sync_id in self.configurations:
            self.configurations[sync_id].enabled = False
            
            # Cancel scheduled task
            if sync_id in self.scheduled_tasks:
                self.scheduled_tasks[sync_id].cancel()
                del self.scheduled_tasks[sync_id]
            
            logger.info(f"Paused sync: {sync_id}")
            return True
        
        return False
    
    async def resume_sync(self, sync_id: str) -> bool:
        """Resume synchronization"""
        if sync_id in self.configurations:
            config = self.configurations[sync_id]
            config.enabled = True
            
            # Reschedule if needed
            if config.schedule_type != "manual":
                await self._schedule_sync(sync_id)
            
            logger.info(f"Resumed sync: {sync_id}")
            return True
        
        return False
    
    async def get_sync_status(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """Get synchronization status"""
        if sync_id not in self.configurations:
            return None
        
        config = self.configurations[sync_id]
        
        # Find latest execution
        latest_execution = None
        for execution in self.executions.values():
            if execution.sync_id == sync_id:
                if not latest_execution or execution.started_at > latest_execution.started_at:
                    latest_execution = execution
        
        return {
            "sync_id": sync_id,
            "name": config.name,
            "enabled": config.enabled,
            "is_running": sync_id in self.running_syncs,
            "latest_execution": latest_execution.__dict__ if latest_execution else None,
            "next_execution": await self._calculate_next_execution(config)
        }
    
    async def get_execution_details(self, execution_id: str) -> Optional[SyncExecution]:
        """Get execution details"""
        return self.executions.get(execution_id)
    
    async def cleanup_old_executions(self, days: int = 30):
        """Clean up old execution records"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for execution_id, execution in self.executions.items():
            if execution.started_at < cutoff_date:
                to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.executions[execution_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old execution records")
    
    async def shutdown(self):
        """Shutdown sync orchestrator"""
        # Cancel all scheduled tasks
        for task in self.scheduled_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.scheduled_tasks:
            await asyncio.gather(*self.scheduled_tasks.values(), return_exceptions=True)
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        # Clear data
        self.configurations.clear()
        self.executions.clear()
        self.scheduled_tasks.clear()
        self.running_syncs.clear()
        
        logger.info("Sync orchestrator shutdown complete")


# Global instance
sync_orchestrator = SyncOrchestrator()


async def register_sync_configuration(config: SyncConfiguration) -> bool:
    """Register sync configuration with global orchestrator"""
    return await sync_orchestrator.register_sync(config)


async def execute_synchronization(sync_id: str) -> str:
    """Execute synchronization with global orchestrator"""
    return await sync_orchestrator.execute_sync(sync_id)