"""
SI ERP Adapter Service

This module provides a unified adapter interface for SI workflows to interact
with various ERP systems, abstracting ERP-specific implementations and providing
standardized data access patterns for SI processing.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import json
from pathlib import Path

from .erp_session_manager import ERPSessionManager, ERPType, SessionManagerConfig
from .erp_data_processor import ERPDataProcessor, ERPRecord, ProcessingConfig
from .data_sync_coordinator import DataSyncCoordinator, SyncRule, CoordinatorConfig
from .erp_event_handler import ERPEventHandler, ERPEvent, EventHandlerConfig

logger = logging.getLogger(__name__)


class AdapterCapability(Enum):
    """Capabilities supported by ERP adapters"""
    READ_INVOICES = "read_invoices"
    WRITE_INVOICES = "write_invoices"
    READ_CUSTOMERS = "read_customers"
    WRITE_CUSTOMERS = "write_customers"
    READ_PRODUCTS = "read_products"
    WRITE_PRODUCTS = "write_products"
    REAL_TIME_EVENTS = "real_time_events"
    BULK_OPERATIONS = "bulk_operations"
    TRANSACTION_SUPPORT = "transaction_support"
    CUSTOM_FIELDS = "custom_fields"


class OperationType(Enum):
    """Types of operations on ERP data"""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_READ = "batch_read"
    BATCH_WRITE = "batch_write"
    SYNC = "sync"
    SEARCH = "search"


@dataclass
class AdapterConfig:
    """Configuration for ERP adapter"""
    adapter_id: str
    erp_type: ERPType
    connection_params: Dict[str, Any]
    enabled_capabilities: List[AdapterCapability] = field(default_factory=list)
    batch_size: int = 100
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 60
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationContext:
    """Context for ERP operations"""
    operation_type: OperationType
    entity_type: str
    user_context: Dict[str, Any] = field(default_factory=dict)
    timeout_override: Optional[int] = None
    batch_mode: bool = False
    transaction_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult:
    """Result of an ERP operation"""
    success: bool
    operation_type: OperationType
    entity_type: str
    affected_records: int = 0
    data: Optional[Any] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseERPAdapter(ABC):
    """Abstract base class for ERP adapters"""
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self.capabilities = set(config.enabled_capabilities)
        self.is_connected = False
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to ERP system"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from ERP system"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test ERP system connectivity"""
        pass
    
    @abstractmethod
    async def read_records(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Read records from ERP system"""
        pass
    
    @abstractmethod
    async def write_record(
        self,
        entity_type: str,
        data: Dict[str, Any],
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Write a single record to ERP system"""
        pass
    
    @abstractmethod
    async def update_record(
        self,
        entity_type: str,
        record_id: str,
        data: Dict[str, Any],
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Update a record in ERP system"""
        pass
    
    @abstractmethod
    async def delete_record(
        self,
        entity_type: str,
        record_id: str,
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Delete a record from ERP system"""
        pass
    
    def supports_capability(self, capability: AdapterCapability) -> bool:
        """Check if adapter supports a capability"""
        return capability in self.capabilities
    
    async def batch_operation(
        self,
        operations: List[Dict[str, Any]],
        context: Optional[OperationContext] = None
    ) -> List[OperationResult]:
        """Execute batch operations"""
        if not self.supports_capability(AdapterCapability.BULK_OPERATIONS):
            raise NotImplementedError("Bulk operations not supported")
        
        results = []
        for operation in operations:
            # Execute individual operations
            # This is a fallback implementation
            op_type = operation.get("type")
            entity_type = operation.get("entity_type")
            data = operation.get("data", {})
            
            if op_type == "create":
                result = await self.write_record(entity_type, data, context)
            elif op_type == "update":
                record_id = operation.get("record_id")
                result = await self.update_record(entity_type, record_id, data, context)
            elif op_type == "delete":
                record_id = operation.get("record_id")
                result = await self.delete_record(entity_type, record_id, context)
            else:
                result = OperationResult(
                    success=False,
                    operation_type=OperationType.BATCH_WRITE,
                    entity_type=entity_type,
                    error_message=f"Unsupported operation type: {op_type}"
                )
            
            results.append(result)
        
        return results
    
    def _cache_key(self, entity_type: str, filters: Dict[str, Any]) -> str:
        """Generate cache key"""
        import hashlib
        key_data = f"{entity_type}_{json.dumps(filters, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        if not self.config.enable_caching:
            return None
        
        if cache_key in self._cache:
            timestamp = self._cache_timestamps.get(cache_key)
            if timestamp:
                age = (datetime.now() - timestamp).total_seconds()
                if age < self.config.cache_ttl_seconds:
                    return self._cache[cache_key]
                else:
                    # Remove expired entry
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
        
        return None
    
    def _store_in_cache(self, cache_key: str, data: Any) -> None:
        """Store data in cache"""
        if not self.config.enable_caching:
            return
        
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()


class OdooAdapter(BaseERPAdapter):
    """Odoo ERP adapter implementation"""
    
    async def connect(self) -> bool:
        """Connect to Odoo ERP"""
        try:
            # Implementation would use Odoo's XML-RPC or REST API
            logger.info("Connecting to Odoo ERP")
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Odoo ERP"""
        self.is_connected = False
        logger.info("Disconnected from Odoo ERP")
    
    async def test_connection(self) -> bool:
        """Test Odoo connection"""
        try:
            # Implementation would test actual connection
            return self.is_connected
        except Exception as e:
            logger.error(f"Odoo connection test failed: {e}")
            return False
    
    async def read_records(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Read records from Odoo"""
        start_time = datetime.now()
        
        try:
            # Check cache first
            cache_key = self._cache_key(entity_type, filters or {})
            cached_data = self._get_from_cache(cache_key)
            
            if cached_data:
                return OperationResult(
                    success=True,
                    operation_type=OperationType.READ,
                    entity_type=entity_type,
                    affected_records=len(cached_data),
                    data=cached_data,
                    execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
            
            # Simulate Odoo API call
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Mock data based on entity type
            if entity_type == "invoice":
                data = [
                    {
                        "id": i,
                        "name": f"INV/{i:04d}",
                        "partner_id": i % 10,
                        "amount_total": 100.0 + i,
                        "state": "posted",
                        "date": datetime.now().isoformat()
                    }
                    for i in range(1, 6)
                ]
            elif entity_type == "customer":
                data = [
                    {
                        "id": i,
                        "name": f"Customer {i}",
                        "email": f"customer{i}@example.com",
                        "vat": f"VAT{i:08d}",
                        "is_company": True
                    }
                    for i in range(1, 6)
                ]
            else:
                data = []
            
            # Store in cache
            self._store_in_cache(cache_key, data)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return OperationResult(
                success=True,
                operation_type=OperationType.READ,
                entity_type=entity_type,
                affected_records=len(data),
                data=data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return OperationResult(
                success=False,
                operation_type=OperationType.READ,
                entity_type=entity_type,
                error_message=str(e),
                execution_time_ms=execution_time
            )
    
    async def write_record(
        self,
        entity_type: str,
        data: Dict[str, Any],
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Write record to Odoo"""
        start_time = datetime.now()
        
        try:
            # Simulate Odoo create operation
            await asyncio.sleep(0.2)  # Simulate network delay
            
            # Mock record creation
            new_id = hash(json.dumps(data, sort_keys=True)) % 10000
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return OperationResult(
                success=True,
                operation_type=OperationType.CREATE,
                entity_type=entity_type,
                affected_records=1,
                data={"id": new_id, **data},
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return OperationResult(
                success=False,
                operation_type=OperationType.CREATE,
                entity_type=entity_type,
                error_message=str(e),
                execution_time_ms=execution_time
            )
    
    async def update_record(
        self,
        entity_type: str,
        record_id: str,
        data: Dict[str, Any],
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Update record in Odoo"""
        start_time = datetime.now()
        
        try:
            # Simulate Odoo update operation
            await asyncio.sleep(0.15)  # Simulate network delay
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return OperationResult(
                success=True,
                operation_type=OperationType.UPDATE,
                entity_type=entity_type,
                affected_records=1,
                data={"id": record_id, **data},
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return OperationResult(
                success=False,
                operation_type=OperationType.UPDATE,
                entity_type=entity_type,
                error_message=str(e),
                execution_time_ms=execution_time
            )
    
    async def delete_record(
        self,
        entity_type: str,
        record_id: str,
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Delete record from Odoo"""
        start_time = datetime.now()
        
        try:
            # Simulate Odoo delete operation
            await asyncio.sleep(0.1)  # Simulate network delay
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return OperationResult(
                success=True,
                operation_type=OperationType.DELETE,
                entity_type=entity_type,
                affected_records=1,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return OperationResult(
                success=False,
                operation_type=OperationType.DELETE,
                entity_type=entity_type,
                error_message=str(e),
                execution_time_ms=execution_time
            )


class SAPAdapter(BaseERPAdapter):
    """SAP ERP adapter implementation"""
    
    async def connect(self) -> bool:
        """Connect to SAP ERP"""
        try:
            logger.info("Connecting to SAP ERP")
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SAP: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from SAP ERP"""
        self.is_connected = False
        logger.info("Disconnected from SAP ERP")
    
    async def test_connection(self) -> bool:
        """Test SAP connection"""
        return self.is_connected
    
    async def read_records(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Read records from SAP"""
        start_time = datetime.now()
        
        try:
            # Simulate SAP API call
            await asyncio.sleep(0.3)  # SAP tends to be slower
            
            # Mock SAP data
            if entity_type == "invoice":
                data = [
                    {
                        "BUKRS": "1000",  # Company Code
                        "BELNR": f"500000{i}",  # Document Number
                        "GJAHR": "2024",  # Fiscal Year
                        "WRBTR": 100.0 + i,  # Amount
                        "WAERS": "NGN"  # Currency
                    }
                    for i in range(1, 4)
                ]
            else:
                data = []
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return OperationResult(
                success=True,
                operation_type=OperationType.READ,
                entity_type=entity_type,
                affected_records=len(data),
                data=data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return OperationResult(
                success=False,
                operation_type=OperationType.READ,
                entity_type=entity_type,
                error_message=str(e),
                execution_time_ms=execution_time
            )
    
    async def write_record(
        self,
        entity_type: str,
        data: Dict[str, Any],
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Write record to SAP"""
        start_time = datetime.now()
        
        try:
            # SAP write operations are typically complex
            await asyncio.sleep(0.5)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return OperationResult(
                success=True,
                operation_type=OperationType.CREATE,
                entity_type=entity_type,
                affected_records=1,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return OperationResult(
                success=False,
                operation_type=OperationType.CREATE,
                entity_type=entity_type,
                error_message=str(e),
                execution_time_ms=execution_time
            )
    
    async def update_record(
        self,
        entity_type: str,
        record_id: str,
        data: Dict[str, Any],
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Update record in SAP"""
        start_time = datetime.now()
        
        try:
            await asyncio.sleep(0.4)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return OperationResult(
                success=True,
                operation_type=OperationType.UPDATE,
                entity_type=entity_type,
                affected_records=1,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return OperationResult(
                success=False,
                operation_type=OperationType.UPDATE,
                entity_type=entity_type,
                error_message=str(e),
                execution_time_ms=execution_time
            )
    
    async def delete_record(
        self,
        entity_type: str,
        record_id: str,
        context: Optional[OperationContext] = None
    ) -> OperationResult:
        """Delete record from SAP"""
        start_time = datetime.now()
        
        try:
            await asyncio.sleep(0.2)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return OperationResult(
                success=True,
                operation_type=OperationType.DELETE,
                entity_type=entity_type,
                affected_records=1,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return OperationResult(
                success=False,
                operation_type=OperationType.DELETE,
                entity_type=entity_type,
                error_message=str(e),
                execution_time_ms=execution_time
            )


class SIERPAdapter:
    """
    Unified ERP adapter for SI workflows that provides a standardized interface
    to various ERP systems and integrates with SI processing services.
    """
    
    def __init__(
        self,
        session_manager: ERPSessionManager,
        data_processor: ERPDataProcessor,
        sync_coordinator: DataSyncCoordinator,
        event_handler: ERPEventHandler
    ):
        self.session_manager = session_manager
        self.data_processor = data_processor
        self.sync_coordinator = sync_coordinator
        self.event_handler = event_handler
        
        self.adapters: Dict[ERPType, BaseERPAdapter] = {}
        self.adapter_registry: Dict[str, Type[BaseERPAdapter]] = {
            ERPType.ODOO.value: OdooAdapter,
            ERPType.SAP.value: SAPAdapter,
        }
        
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the SI ERP adapter"""
        try:
            if self.is_initialized:
                return True
            
            # Start required services
            await self.session_manager.start_session_manager()
            await self.sync_coordinator.start_coordinator()
            await self.event_handler.start_event_handler()
            
            self.is_initialized = True
            logger.info("SI ERP Adapter initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SI ERP Adapter: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the SI ERP adapter"""
        try:
            if not self.is_initialized:
                return
            
            # Disconnect all adapters
            for adapter in self.adapters.values():
                await adapter.disconnect()
            
            # Stop services
            await self.session_manager.stop_session_manager()
            await self.sync_coordinator.stop_coordinator()
            await self.event_handler.stop_event_handler()
            
            self.is_initialized = False
            logger.info("SI ERP Adapter shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during SI ERP Adapter shutdown: {e}")
    
    async def register_erp_system(
        self,
        erp_type: ERPType,
        config: AdapterConfig
    ) -> bool:
        """Register an ERP system with the adapter"""
        try:
            # Get adapter class
            adapter_class = self.adapter_registry.get(erp_type.value)
            if not adapter_class:
                logger.error(f"No adapter available for {erp_type.value}")
                return False
            
            # Create adapter instance
            adapter = adapter_class(config)
            
            # Test connection
            if await adapter.connect():
                self.adapters[erp_type] = adapter
                
                # Register with session manager
                from .erp_session_manager import ConnectionConfig, AuthenticationType
                session_config = ConnectionConfig(
                    erp_type=erp_type,
                    host=config.connection_params.get("host", "localhost"),
                    port=config.connection_params.get("port", 8080),
                    username=config.connection_params.get("username"),
                    password=config.connection_params.get("password"),
                    authentication_type=AuthenticationType.BASIC
                )
                
                await self.session_manager.register_erp_connection(erp_type, session_config)
                
                logger.info(f"Registered ERP system: {erp_type.value}")
                return True
            else:
                logger.error(f"Failed to connect to {erp_type.value}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to register ERP system {erp_type.value}: {e}")
            return False
    
    async def get_erp_data(
        self,
        erp_type: ERPType,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        process_data: bool = True
    ) -> Optional[List[ERPRecord]]:
        """Get and optionally process data from ERP system"""
        try:
            adapter = self.adapters.get(erp_type)
            if not adapter:
                logger.error(f"No adapter found for {erp_type.value}")
                return None
            
            # Read data from ERP
            result = await adapter.read_records(entity_type, filters)
            
            if not result.success:
                logger.error(f"Failed to read data from {erp_type.value}: {result.error_message}")
                return None
            
            # Convert to ERPRecord objects
            records = []
            for item in result.data:
                record = ERPRecord(
                    record_id=str(item.get("id", "unknown")),
                    record_type=entity_type,
                    source_system=erp_type.value,
                    raw_data=item
                )
                records.append(record)
            
            # Process data if requested
            if process_data and records:
                processing_result = await self.data_processor.process_erp_data(records)
                if processing_result.status.value == "completed":
                    logger.info(f"Processed {processing_result.processed_records} records from {erp_type.value}")
                else:
                    logger.warning(f"Data processing had issues: {processing_result.status.value}")
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to get ERP data from {erp_type.value}: {e}")
            return None
    
    async def write_erp_data(
        self,
        erp_type: ERPType,
        entity_type: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        context: Optional[OperationContext] = None
    ) -> bool:
        """Write data to ERP system"""
        try:
            adapter = self.adapters.get(erp_type)
            if not adapter:
                logger.error(f"No adapter found for {erp_type.value}")
                return False
            
            # Handle batch vs single record
            if isinstance(data, list):
                # Batch operation
                operations = [
                    {"type": "create", "entity_type": entity_type, "data": item}
                    for item in data
                ]
                results = await adapter.batch_operation(operations, context)
                success = all(result.success for result in results)
            else:
                # Single record
                result = await adapter.write_record(entity_type, data, context)
                success = result.success
            
            if success:
                logger.info(f"Successfully wrote data to {erp_type.value}")
            else:
                logger.error(f"Failed to write data to {erp_type.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to write ERP data to {erp_type.value}: {e}")
            return False
    
    async def sync_erp_data(
        self,
        source_erp: ERPType,
        target_erp: ERPType,
        entity_type: str,
        sync_rule_id: Optional[str] = None
    ) -> Optional[str]:
        """Synchronize data between ERP systems"""
        try:
            if not sync_rule_id:
                # Create a default sync rule
                sync_rule_id = f"sync_{source_erp.value}_to_{target_erp.value}_{entity_type}"
            
            # Schedule sync operation
            operation_id = await self.sync_coordinator.schedule_sync(
                rule_id=sync_rule_id,
                metadata={
                    "source_erp": source_erp.value,
                    "target_erp": target_erp.value,
                    "entity_type": entity_type
                }
            )
            
            if operation_id:
                logger.info(f"Scheduled sync operation {operation_id}")
            
            return operation_id
            
        except Exception as e:
            logger.error(f"Failed to sync ERP data: {e}")
            return None
    
    async def handle_erp_event(
        self,
        erp_type: ERPType,
        event_data: Dict[str, Any]
    ) -> bool:
        """Handle an event from ERP system"""
        try:
            # Create ERPEvent
            from .erp_event_handler import ERPEvent, EventType, EventSource, EventPriority
            
            event = ERPEvent(
                event_id=f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                event_type=EventType.UPDATE,  # Default
                source=EventSource.API_CALLBACK,
                erp_system=erp_type.value,
                entity_type=event_data.get("entity_type", "unknown"),
                entity_id=str(event_data.get("entity_id", "unknown")),
                timestamp=datetime.now(),
                payload=event_data,
                priority=EventPriority.NORMAL
            )
            
            # Send event for processing
            success = await self.event_handler.send_event(event)
            
            if success:
                logger.info(f"Handled ERP event from {erp_type.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to handle ERP event: {e}")
            return False
    
    def get_adapter_capabilities(self, erp_type: ERPType) -> List[AdapterCapability]:
        """Get capabilities of an ERP adapter"""
        adapter = self.adapters.get(erp_type)
        if adapter:
            return list(adapter.capabilities)
        return []
    
    def is_erp_connected(self, erp_type: ERPType) -> bool:
        """Check if ERP system is connected"""
        adapter = self.adapters.get(erp_type)
        return adapter.is_connected if adapter else False
    
    async def test_erp_connection(self, erp_type: ERPType) -> bool:
        """Test connection to ERP system"""
        adapter = self.adapters.get(erp_type)
        if adapter:
            return await adapter.test_connection()
        return False
    
    def get_supported_erp_types(self) -> List[ERPType]:
        """Get list of supported ERP types"""
        return [ERPType(erp_type) for erp_type in self.adapter_registry.keys()]
    
    def get_active_erp_types(self) -> List[ERPType]:
        """Get list of currently active ERP types"""
        return list(self.adapters.keys())
    
    async def get_adapter_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all adapters"""
        status = {}
        
        for erp_type, adapter in self.adapters.items():
            status[erp_type.value] = {
                "connected": adapter.is_connected,
                "capabilities": [cap.value for cap in adapter.capabilities],
                "config": {
                    "batch_size": adapter.config.batch_size,
                    "timeout_seconds": adapter.config.timeout_seconds,
                    "caching_enabled": adapter.config.enable_caching,
                    "rate_limiting_enabled": adapter.config.enable_rate_limiting
                }
            }
        
        return status
    
    async def execute_custom_operation(
        self,
        erp_type: ERPType,
        operation_name: str,
        parameters: Dict[str, Any]
    ) -> Optional[OperationResult]:
        """Execute a custom operation on ERP system"""
        try:
            adapter = self.adapters.get(erp_type)
            if not adapter:
                return None
            
            # Check if adapter supports custom operations
            if hasattr(adapter, 'execute_custom_operation'):
                return await adapter.execute_custom_operation(operation_name, parameters)
            else:
                return OperationResult(
                    success=False,
                    operation_type=OperationType.READ,  # Default
                    entity_type="custom",
                    error_message="Custom operations not supported by this adapter"
                )
                
        except Exception as e:
            logger.error(f"Custom operation failed: {e}")
            return OperationResult(
                success=False,
                operation_type=OperationType.READ,
                entity_type="custom",
                error_message=str(e)
            )


# Factory function for creating SI ERP adapter
def create_si_erp_adapter(
    session_config: Optional[SessionManagerConfig] = None,
    processing_config: Optional[ProcessingConfig] = None,
    coordinator_config: Optional[CoordinatorConfig] = None,
    event_config: Optional[EventHandlerConfig] = None
) -> SIERPAdapter:
    """Factory function to create SI ERP adapter with all required services"""
    
    # Create service instances
    session_manager = ERPSessionManager(session_config or SessionManagerConfig())
    data_processor = ERPDataProcessor(processing_config or ProcessingConfig())
    sync_coordinator = DataSyncCoordinator(coordinator_config or CoordinatorConfig())
    event_handler = ERPEventHandler(event_config or EventHandlerConfig())
    
    # Create and return adapter
    return SIERPAdapter(session_manager, data_processor, sync_coordinator, event_handler)