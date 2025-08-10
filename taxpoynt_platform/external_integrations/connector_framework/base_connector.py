"""
Base Connector - Universal Connector Framework
Provides universal base class for all external system connectors in the TaxPoynt platform.
Extends and standardizes existing connector patterns with additional protocol support.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)

class ConnectorType(Enum):
    ERP = "erp"
    CRM = "crm"
    ACCOUNTING = "accounting"
    POS = "pos"
    ECOMMERCE = "ecommerce"
    FINANCIAL = "financial"
    GOVERNMENT = "government"
    API_GATEWAY = "api_gateway"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    MESSAGING = "messaging"
    CUSTOM = "custom"

class ProtocolType(Enum):
    REST = "rest"
    SOAP = "soap"
    GRAPHQL = "graphql"
    ODATA = "odata"
    RPC = "rpc"
    WEBSOCKET = "websocket"
    MQTT = "mqtt"
    FILE_TRANSFER = "file_transfer"
    DATABASE_DIRECT = "database_direct"

class AuthenticationType(Enum):
    OAUTH2 = "oauth2"
    JWT = "jwt"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    CERTIFICATE = "certificate"
    SAML = "saml"
    CUSTOM_TOKEN = "custom_token"
    NONE = "none"

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    RATE_LIMITED = "rate_limited"

class DataFormat(Enum):
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    YAML = "yaml"
    BINARY = "binary"
    FORM_DATA = "form_data"
    UBL = "ubl"
    EDI = "edi"
    CUSTOM = "custom"

@dataclass
class ConnectorConfig:
    connector_id: str
    name: str
    connector_type: ConnectorType
    protocol_type: ProtocolType
    authentication_type: AuthenticationType
    base_url: str
    endpoints: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    authentication_config: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    rate_limit_per_minute: int = 100
    batch_size: int = 100
    data_format: DataFormat = DataFormat.JSON
    ssl_verify: bool = True
    proxy_config: Optional[Dict[str, str]] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ConnectorRequest:
    operation: str
    endpoint: str
    method: str = "GET"
    data: Optional[Any] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    retry_on_failure: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ConnectorResponse:
    status_code: int
    data: Any
    headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    response_time_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class HealthStatus:
    connector_id: str
    status: ConnectionStatus
    last_successful_connection: Optional[datetime] = None
    last_error: Optional[str] = None
    response_time_ms: float = 0.0
    success_rate_24h: float = 0.0
    total_requests_24h: int = 0
    failed_requests_24h: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ConnectorMetrics:
    connector_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time_ms: float = 0.0
    peak_response_time_ms: float = 0.0
    requests_per_minute: float = 0.0
    error_rate_percent: float = 0.0
    last_activity: Optional[datetime] = None
    uptime_percent: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class BaseConnector(ABC):
    """Universal base connector class for all external system integrations"""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.session = None
        self.authentication_token = None
        self.token_expires_at = None
        self.request_count = 0
        self.last_request_time = None
        self.metrics = ConnectorMetrics(connector_id=config.connector_id)
        self.health_status = HealthStatus(
            connector_id=config.connector_id,
            status=ConnectionStatus.DISCONNECTED
        )
        
        # Rate limiting
        self.request_times = []
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{config.connector_id}")
    
    async def initialize(self) -> bool:
        """Initialize the connector and establish connection"""
        try:
            self.logger.info(f"Initializing connector: {self.config.connector_id}")
            
            # Initialize session
            await self._initialize_session()
            
            # Authenticate if required
            if self.config.authentication_type != AuthenticationType.NONE:
                success = await self._authenticate()
                if not success:
                    self.status = ConnectionStatus.ERROR
                    self.health_status.status = ConnectionStatus.ERROR
                    self.health_status.last_error = "Authentication failed"
                    return False
            
            # Test connection
            if await self._test_connection():
                self.status = ConnectionStatus.AUTHENTICATED
                self.health_status.status = ConnectionStatus.AUTHENTICATED
                self.health_status.last_successful_connection = datetime.utcnow()
                self.logger.info(f"Connector initialized successfully: {self.config.connector_id}")
                return True
            else:
                self.status = ConnectionStatus.ERROR
                self.health_status.status = ConnectionStatus.ERROR
                self.health_status.last_error = "Connection test failed"
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize connector {self.config.connector_id}: {e}")
            self.status = ConnectionStatus.ERROR
            self.health_status.status = ConnectionStatus.ERROR
            self.health_status.last_error = str(e)
            return False
    
    async def execute_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute a request through the connector"""
        start_time = time.time()
        
        try:
            # Check rate limiting
            if not await self._check_rate_limit():
                raise Exception("Rate limit exceeded")
            
            # Ensure authenticated
            if not await self._ensure_authenticated():
                raise Exception("Authentication required")
            
            # Execute the actual request
            response = await self._execute_protocol_request(request)
            
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            response.response_time_ms = response_time
            await self._update_metrics(True, response_time)
            
            self.logger.debug(f"Request executed successfully: {request.operation}")
            return response
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            await self._update_metrics(False, response_time)
            
            error_response = ConnectorResponse(
                status_code=500,
                data=None,
                success=False,
                error_message=str(e),
                response_time_ms=response_time
            )
            
            self.logger.error(f"Request failed: {request.operation} - {e}")
            return error_response
    
    @abstractmethod
    async def _initialize_session(self):
        """Initialize the connection session - implemented by protocol adapters"""
        pass
    
    @abstractmethod
    async def _authenticate(self) -> bool:
        """Authenticate with the external system - implemented by auth adapters"""
        pass
    
    @abstractmethod
    async def _test_connection(self) -> bool:
        """Test the connection to the external system"""
        pass
    
    @abstractmethod
    async def _execute_protocol_request(self, request: ConnectorRequest) -> ConnectorResponse:
        """Execute request using specific protocol - implemented by protocol adapters"""
        pass
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure the connector is authenticated"""
        try:
            if self.config.authentication_type == AuthenticationType.NONE:
                return True
            
            # Check if token is still valid
            if self.authentication_token and self.token_expires_at:
                if datetime.utcnow() < self.token_expires_at:
                    return True
            
            # Re-authenticate if needed
            return await self._authenticate()
            
        except Exception as e:
            self.logger.error(f"Authentication check failed: {e}")
            return False
    
    async def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        try:
            current_time = datetime.utcnow()
            minute_ago = current_time - timedelta(minutes=1)
            
            # Remove old request times
            self.request_times = [
                req_time for req_time in self.request_times
                if req_time > minute_ago
            ]
            
            # Check rate limit
            if len(self.request_times) >= self.config.rate_limit_per_minute:
                self.status = ConnectionStatus.RATE_LIMITED
                return False
            
            # Add current request time
            self.request_times.append(current_time)
            return True
            
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            return False
    
    async def _update_metrics(self, success: bool, response_time_ms: float):
        """Update connector metrics"""
        try:
            self.metrics.total_requests += 1
            self.metrics.last_activity = datetime.utcnow()
            
            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
            
            # Update response time metrics
            if response_time_ms > self.metrics.peak_response_time_ms:
                self.metrics.peak_response_time_ms = response_time_ms
            
            # Calculate average response time
            total_successful = self.metrics.successful_requests
            if total_successful > 0:
                self.metrics.average_response_time_ms = (
                    (self.metrics.average_response_time_ms * (total_successful - 1) + response_time_ms) / total_successful
                )
            
            # Calculate error rate
            if self.metrics.total_requests > 0:
                self.metrics.error_rate_percent = (
                    self.metrics.failed_requests / self.metrics.total_requests * 100
                )
            
            # Update requests per minute
            self.metrics.requests_per_minute = len(self.request_times)
            
            # Update health status
            self.health_status.response_time_ms = response_time_ms
            self.health_status.total_requests_24h = self.metrics.total_requests  # Simplified
            self.health_status.failed_requests_24h = self.metrics.failed_requests
            
            if self.health_status.total_requests_24h > 0:
                success_count = self.health_status.total_requests_24h - self.health_status.failed_requests_24h
                self.health_status.success_rate_24h = (success_count / self.health_status.total_requests_24h * 100)
            
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
    
    async def get_health_status(self) -> HealthStatus:
        """Get current health status"""
        try:
            # Update status based on recent activity
            if self.status == ConnectionStatus.AUTHENTICATED:
                if self.health_status.success_rate_24h > 95:
                    self.health_status.status = ConnectionStatus.CONNECTED
                elif self.health_status.success_rate_24h > 80:
                    self.health_status.status = ConnectionStatus.AUTHENTICATED
                else:
                    self.health_status.status = ConnectionStatus.ERROR
            
            self.health_status.timestamp = datetime.utcnow()
            return self.health_status
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {e}")
            return HealthStatus(
                connector_id=self.config.connector_id,
                status=ConnectionStatus.ERROR,
                last_error=str(e)
            )
    
    async def get_metrics(self) -> ConnectorMetrics:
        """Get current metrics"""
        try:
            self.metrics.timestamp = datetime.utcnow()
            
            # Calculate uptime (simplified)
            if self.status == ConnectionStatus.AUTHENTICATED:
                self.metrics.uptime_percent = max(0, 100 - self.metrics.error_rate_percent)
            
            return self.metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return ConnectorMetrics(connector_id=self.config.connector_id)
    
    async def disconnect(self):
        """Disconnect from the external system"""
        try:
            self.logger.info(f"Disconnecting connector: {self.config.connector_id}")
            
            # Clean up session
            if self.session:
                await self._cleanup_session()
            
            # Clear authentication
            self.authentication_token = None
            self.token_expires_at = None
            
            # Update status
            self.status = ConnectionStatus.DISCONNECTED
            self.health_status.status = ConnectionStatus.DISCONNECTED
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect: {e}")
    
    async def _cleanup_session(self):
        """Clean up connection session - implemented by protocol adapters"""
        pass
    
    # Standard operations that all connectors should support
    async def create(self, resource_type: str, data: Dict[str, Any]) -> ConnectorResponse:
        """Create a resource in the external system"""
        request = ConnectorRequest(
            operation="create",
            endpoint=self.config.endpoints.get(f"create_{resource_type}", f"/{resource_type}"),
            method="POST",
            data=data
        )
        return await self.execute_request(request)
    
    async def read(self, resource_type: str, resource_id: str) -> ConnectorResponse:
        """Read a resource from the external system"""
        request = ConnectorRequest(
            operation="read",
            endpoint=self.config.endpoints.get(f"read_{resource_type}", f"/{resource_type}/{resource_id}"),
            method="GET"
        )
        return await self.execute_request(request)
    
    async def update(self, resource_type: str, resource_id: str, data: Dict[str, Any]) -> ConnectorResponse:
        """Update a resource in the external system"""
        request = ConnectorRequest(
            operation="update",
            endpoint=self.config.endpoints.get(f"update_{resource_type}", f"/{resource_type}/{resource_id}"),
            method="PUT",
            data=data
        )
        return await self.execute_request(request)
    
    async def delete(self, resource_type: str, resource_id: str) -> ConnectorResponse:
        """Delete a resource from the external system"""
        request = ConnectorRequest(
            operation="delete",
            endpoint=self.config.endpoints.get(f"delete_{resource_type}", f"/{resource_type}/{resource_id}"),
            method="DELETE"
        )
        return await self.execute_request(request)
    
    async def list(self, resource_type: str, filters: Optional[Dict[str, Any]] = None) -> ConnectorResponse:
        """List resources from the external system"""
        request = ConnectorRequest(
            operation="list",
            endpoint=self.config.endpoints.get(f"list_{resource_type}", f"/{resource_type}"),
            method="GET",
            params=filters
        )
        return await self.execute_request(request)
    
    async def batch_operation(self, operations: List[ConnectorRequest]) -> List[ConnectorResponse]:
        """Execute multiple operations in batch"""
        responses = []
        
        for operation in operations:
            response = await self.execute_request(operation)
            responses.append(response)
            
            # Add delay between requests if needed
            if len(responses) % self.config.batch_size == 0:
                await asyncio.sleep(0.1)  # Brief pause between batches
        
        return responses
    
    # Utility methods
    def get_connector_info(self) -> Dict[str, Any]:
        """Get connector information"""
        return {
            'connector_id': self.config.connector_id,
            'name': self.config.name,
            'type': self.config.connector_type.value,
            'protocol': self.config.protocol_type.value,
            'status': self.status.value,
            'base_url': self.config.base_url,
            'created_at': self.config.created_at.isoformat(),
            'metadata': self.config.metadata
        }
    
    def __str__(self) -> str:
        return f"BaseConnector(id={self.config.connector_id}, type={self.config.connector_type.value}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return self.__str__()

# Global connector registry for tracking active connectors
_active_connectors: Dict[str, BaseConnector] = {}

def register_connector(connector: BaseConnector):
    """Register a connector in the global registry"""
    _active_connectors[connector.config.connector_id] = connector

def unregister_connector(connector_id: str):
    """Unregister a connector from the global registry"""
    if connector_id in _active_connectors:
        del _active_connectors[connector_id]

def get_connector(connector_id: str) -> Optional[BaseConnector]:
    """Get a connector from the global registry"""
    return _active_connectors.get(connector_id)

def list_active_connectors() -> List[BaseConnector]:
    """List all active connectors"""
    return list(_active_connectors.values())

async def get_all_health_statuses() -> List[HealthStatus]:
    """Get health status for all active connectors"""
    statuses = []
    for connector in _active_connectors.values():
        status = await connector.get_health_status()
        statuses.append(status)
    return statuses

async def get_all_metrics() -> List[ConnectorMetrics]:
    """Get metrics for all active connectors"""
    metrics = []
    for connector in _active_connectors.values():
        metric = await connector.get_metrics()
        metrics.append(metric)
    return metrics