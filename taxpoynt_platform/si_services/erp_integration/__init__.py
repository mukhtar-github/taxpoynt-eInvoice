"""
ERP Integration Services for SI (System Integrator) Role

This package provides comprehensive ERP integration services specifically designed
for System Integrator workflows in the TaxPoynt e-invoicing platform. These services
handle ERP data processing, session management, synchronization, and event handling
for internal SI operations.

Key Components:
- ERPDataProcessor: Process and validate ERP data for SI workflows
- ERPSessionManager: Manage ERP sessions with connection pooling
- DataSyncCoordinator: Coordinate data synchronization across systems
- ERPEventHandler: Handle real-time events from ERP systems
- SIERPAdapter: Unified adapter interface for SI workflows

Architecture:
This package focuses on backend processing and internal operations,
distinct from the external ERP connectors in external_integrations.
It provides the processing layer that transforms raw ERP data into
standardized formats suitable for e-invoicing compliance.
"""

# Core ERP Integration Services (New Architecture)
from .erp_data_processor import (
    ERPDataProcessor,
    ERPRecord,
    ProcessingResult,
    ProcessingConfig,
    DataIssue,
    ProcessingRule,
    ProcessingStatus,
    DataIssueType,
    ProcessingPriority,
    create_erp_data_processor
)

from .erp_session_manager import (
    ERPSessionManager,
    SessionInfo,
    ConnectionConfig,
    SessionPool,
    SessionMetrics,
    SessionManagerConfig,
    SessionStatus,
    AuthenticationType,
    ERPType,
    create_erp_session_manager,
    create_authenticated_erp_session_manager
)

from .data_sync_coordinator import (
    DataSyncCoordinator,
    SyncRule,
    SyncConflict,
    SyncOperation,
    CoordinatorConfig,
    SyncDirection,
    SyncStrategy,
    SyncStatus,
    ConflictResolution,
    SyncPriority
)

from .erp_event_handler import (
    ERPEventHandler,
    ERPEvent,
    EventHandler,
    WebhookConfig,
    EventMetrics,
    EventHandlerConfig,
    EventType,
    EventSource,
    EventStatus,
    EventPriority,
    EventFilter,
    create_erp_event_handler
)

from .si_erp_adapter import (
    SIERPAdapter,
    BaseERPAdapter,
    OdooAdapter,
    SAPAdapter,
    AdapterConfig,
    OperationContext,
    OperationResult,
    AdapterCapability,
    OperationType,
    create_si_erp_adapter
)

# Legacy ERP Integration Services (Existing)
from .odoo_service import OdooService
from .odoo_invoice_service import OdooInvoiceService
from .odoo_ubl_transformer import OdooUBLTransformer
from .odoo_ubl_mapper import OdooUBLMapper
from .odoo_ubl_validator import OdooUBLValidator
from .odoo_ubl_service_connector import OdooUBLServiceConnector
from .sap_firs_mapping import SAPFIRSMapping
from .sap_firs_transformer import SAPFIRSTransformer
from .sap_oauth import SAPOAuth
from .erp_connector_factory import ERPConnectorFactory
from .erp_integration_service import ERPIntegrationService
from .firs_si_erp_integration_service import FIRSSIERPIntegrationService

__all__ = [
    # Core ERP Integration Services (New Architecture)
    'ERPDataProcessor',
    'ERPRecord',
    'ProcessingResult',
    'ProcessingConfig',
    'DataIssue',
    'ProcessingRule',
    'ProcessingStatus',
    'DataIssueType',
    'ProcessingPriority',
    'create_erp_data_processor',
    
    'ERPSessionManager',
    'SessionInfo',
    'ConnectionConfig',
    'SessionPool',
    'SessionMetrics',
    'SessionManagerConfig',
    'SessionStatus',
    'AuthenticationType',
    'ERPType',
    'create_erp_session_manager',
    'create_authenticated_erp_session_manager',
    
    'DataSyncCoordinator',
    'SyncRule',
    'SyncConflict',
    'SyncOperation',
    'CoordinatorConfig',
    'SyncDirection',
    'SyncStrategy',
    'SyncStatus',
    'ConflictResolution',
    'SyncPriority',
    
    'ERPEventHandler',
    'ERPEvent',
    'EventHandler',
    'WebhookConfig',
    'EventMetrics',
    'EventHandlerConfig',
    'EventType',
    'EventSource',
    'EventStatus',
    'EventPriority',
    'EventFilter',
    'create_erp_event_handler',
    
    'SIERPAdapter',
    'BaseERPAdapter',
    'OdooAdapter',
    'SAPAdapter',
    'AdapterConfig',
    'OperationContext',
    'OperationResult',
    'AdapterCapability',
    'OperationType',
    'create_si_erp_adapter',
    
    # Legacy ERP Integration Services (Existing)
    "OdooService",
    "OdooInvoiceService",
    "OdooUBLTransformer",
    "OdooUBLMapper",
    "OdooUBLValidator",
    "OdooUBLServiceConnector",
    "SAPFIRSMapping",
    "SAPFIRSTransformer", 
    "SAPOAuth",
    "ERPConnectorFactory",
    "ERPIntegrationService",
    "FIRSSIERPIntegrationService"
]

# Version information
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'ERP Integration Services for SI Role'

# Quick access factory functions for common use cases
def create_complete_erp_integration(
    session_config=None,
    processing_config=None,
    coordinator_config=None,
    event_config=None
):
    """
    Factory function to create a complete ERP integration setup
    with all services properly configured and interconnected.
    
    Returns:
        SIERPAdapter: Fully configured SI ERP adapter
    """
    return create_si_erp_adapter(
        session_config=session_config,
        processing_config=processing_config,
        coordinator_config=coordinator_config,
        event_config=event_config
    )

def get_supported_erp_types():
    """
    Get list of supported ERP system types.
    
    Returns:
        List[ERPType]: Supported ERP types
    """
    return list(ERPType)

def get_available_capabilities():
    """
    Get list of available adapter capabilities.
    
    Returns:
        List[AdapterCapability]: Available capabilities
    """
    return list(AdapterCapability)

# Configuration defaults
DEFAULT_CONFIGS = {
    'session_manager': SessionManagerConfig(),
    'data_processor': ProcessingConfig(),
    'event_handler': EventHandlerConfig(),
}

# Service status information
SERVICE_INFO = {
    'package': 'si_services.erp_integration',
    'role': 'System Integrator (SI)',
    'purpose': 'Backend ERP data processing for e-invoicing compliance',
    'services': [
        'Data Processing & Validation',
        'Session Management & Pooling',
        'Data Synchronization',
        'Event Handling & Webhooks',
        'Unified ERP Adapter Interface'
    ],
    'version': __version__
}