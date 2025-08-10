"""
Universal Connector Framework
Comprehensive framework for integrating with external systems across different protocols.
Provides unified interfaces, authentication, data transformation, and health monitoring.
"""

from .base_connector import BaseConnector, ConnectorConfig, ConnectionStatus
from .base_erp_connector import BaseERPConnector, ERPConnectionError, ERPAuthenticationError, ERPDataError, ERPValidationError
from .base_crm_connector import BaseCRMConnector, CRMConnectionError, CRMAuthenticationError, CRMDataError, CRMValidationError
from .base_pos_connector import (
    BasePOSConnector, 
    POSTransaction, 
    POSWebhookEvent, 
    POSLocation, 
    POSPaymentMethod, 
    POSInventoryItem, 
    POSRefund
)
from .base_ecommerce_connector import (
    BaseEcommerceConnector,
    EcommerceOrder,
    EcommerceSyncResult,
    EcommerceHealthStatus,
    EcommerceWebhookPayload,
    EcommerceOrderStatus,
    EcommercePaymentStatus
)
from .base_accounting_connector import (
    BaseAccountingConnector,
    AccountingTransaction,
    AccountingContact,
    AccountingAccount,
    AccountingWebhookEvent,
    AccountingTransactionType,
    AccountingDocumentStatus,
    AccountingConnectionError,
    AccountingAuthenticationError,
    AccountingDataError,
    AccountingValidationError,
    AccountingTransformationError
)
from .base_inventory_connector import (
    BaseInventoryConnector,
    InventoryMovementType,
    StockStatus
)
from .generic_erp_connector import GenericERPConnector, ERPIntegrationPattern, ERPDiscoveryTemplate
from .connector_factory import ConnectorFactory, ConnectorRegistry
from .authentication_manager import AuthenticationManager, AuthConfig, AuthType
from .data_transformer import DataTransformer, TransformationConfig, DataFormat
from .health_monitor import HealthMonitor, HealthStatus, HealthCheck, Alert, Metric

# Protocol adapters
from .protocol_adapters import (
    RestConnector,
    SoapConnector,
    GraphQLConnector,
    ODataConnector,
    RpcConnector
)

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"

__all__ = [
    # Core framework classes
    "BaseConnector",
    "ConnectorConfig", 
    "ConnectionStatus",
    "ConnectorFactory",
    "ConnectorRegistry",
    
    # ERP base classes and framework
    "BaseERPConnector",
    "ERPConnectionError",
    "ERPAuthenticationError", 
    "ERPDataError",
    "ERPValidationError",
    "GenericERPConnector",
    "ERPIntegrationPattern",
    "ERPDiscoveryTemplate",
    
    # CRM base classes and framework
    "BaseCRMConnector",
    "CRMConnectionError",
    "CRMAuthenticationError",
    "CRMDataError", 
    "CRMValidationError",
    
    # POS base classes and models
    "BasePOSConnector",
    "POSTransaction",
    "POSWebhookEvent",
    "POSLocation",
    "POSPaymentMethod",
    "POSInventoryItem",
    "POSRefund",
    
    # E-commerce base classes and models
    "BaseEcommerceConnector",
    "EcommerceOrder",
    "EcommerceSyncResult",
    "EcommerceHealthStatus", 
    "EcommerceWebhookPayload",
    "EcommerceOrderStatus",
    "EcommercePaymentStatus",
    
    # Accounting base classes and models
    "BaseAccountingConnector",
    "AccountingTransaction",
    "AccountingContact",
    "AccountingAccount",
    "AccountingWebhookEvent",
    "AccountingTransactionType",
    "AccountingDocumentStatus",
    "AccountingConnectionError",
    "AccountingAuthenticationError",
    "AccountingDataError",
    "AccountingValidationError",
    "AccountingTransformationError",
    
    # Inventory base classes and models
    "BaseInventoryConnector",
    "InventoryMovementType",
    "StockStatus",
    
    # Authentication
    "AuthenticationManager",
    "AuthConfig",
    "AuthType",
    
    # Data transformation
    "DataTransformer",
    "TransformationConfig",
    "DataFormat",
    
    # Health monitoring
    "HealthMonitor",
    "HealthStatus",
    "HealthCheck",
    "Alert",
    "Metric",
    
    # Protocol adapters
    "RestConnector",
    "SoapConnector", 
    "GraphQLConnector",
    "ODataConnector",
    "RpcConnector"
]