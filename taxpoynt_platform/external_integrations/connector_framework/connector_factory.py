"""
Connector Factory - Universal Connector Framework
Dynamic connector creation and management for the TaxPoynt platform.
Creates connectors based on configuration and manages their lifecycle.
"""

import asyncio
import logging
import importlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass, field
from enum import Enum

from .base_connector import (
    BaseConnector, ConnectorConfig, ConnectorType, ProtocolType, 
    AuthenticationType, ConnectionStatus, DataFormat, register_connector, 
    unregister_connector, get_connector, list_active_connectors
)

logger = logging.getLogger(__name__)

class ConnectorTemplate(Enum):
    """Pre-defined connector templates for common systems"""
    GENERIC_REST = "generic_rest"
    GENERIC_SOAP = "generic_soap"
    ODOO_ERP = "odoo_erp"
    SAP_ODATA = "sap_odata"
    SALESFORCE_CRM = "salesforce_crm"
    QUICKBOOKS = "quickbooks"
    FIRS_API = "firs_api"
    SHOPIFY = "shopify"
    STRIPE = "stripe"
    GENERIC_GRAPHQL = "generic_graphql"
    CUSTOM = "custom"

@dataclass
class ConnectorTemplate:
    template_id: str
    name: str
    description: str
    connector_type: ConnectorType
    protocol_type: ProtocolType
    authentication_type: AuthenticationType
    default_endpoints: Dict[str, str] = field(default_factory=dict)
    default_headers: Dict[str, str] = field(default_factory=dict)
    required_config_fields: List[str] = field(default_factory=list)
    optional_config_fields: List[str] = field(default_factory=list)
    default_settings: Dict[str, Any] = field(default_factory=dict)
    connector_class_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConnectorFactory:
    """Factory for creating and managing connectors dynamically"""
    
    def __init__(self):
        self.templates: Dict[str, ConnectorTemplate] = {}
        self.connector_classes: Dict[str, Type[BaseConnector]] = {}
        self.active_connectors: Dict[str, BaseConnector] = {}
        
        # Load built-in templates
        self._load_builtin_templates()
        
        # Load connector classes
        self._load_connector_classes()
    
    def _load_builtin_templates(self):
        """Load built-in connector templates"""
        builtin_templates = [
            ConnectorTemplate(
                template_id="generic_rest",
                name="Generic REST API",
                description="Generic REST API connector with configurable endpoints",
                connector_type=ConnectorType.API_GATEWAY,
                protocol_type=ProtocolType.REST,
                authentication_type=AuthenticationType.API_KEY,
                default_endpoints={
                    "health": "/health",
                    "status": "/status"
                },
                default_headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                required_config_fields=["base_url"],
                optional_config_fields=["api_key", "timeout", "retry_attempts"],
                default_settings={
                    "timeout": 30,
                    "retry_attempts": 3,
                    "data_format": "json"
                },
                connector_class_path="taxpoynt_platform.external_integrations.connector_framework.protocol_adapters.rest_adapter.RestConnector"
            ),
            ConnectorTemplate(
                template_id="generic_soap",
                name="Generic SOAP/XML API",
                description="Generic SOAP connector with WSDL support",
                connector_type=ConnectorType.API_GATEWAY,
                protocol_type=ProtocolType.SOAP,
                authentication_type=AuthenticationType.BASIC_AUTH,
                default_endpoints={
                    "wsdl": "?wsdl"
                },
                default_headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": ""
                },
                required_config_fields=["base_url", "wsdl_url"],
                optional_config_fields=["username", "password", "namespace"],
                default_settings={
                    "timeout": 60,
                    "data_format": "xml"
                },
                connector_class_path="taxpoynt_platform.external_integrations.connector_framework.protocol_adapters.soap_adapter.SoapConnector"
            ),
            ConnectorTemplate(
                template_id="odoo_erp",
                name="Odoo ERP Connector",
                description="Specialized connector for Odoo ERP systems",
                connector_type=ConnectorType.ERP,
                protocol_type=ProtocolType.REST,
                authentication_type=AuthenticationType.CUSTOM_TOKEN,
                default_endpoints={
                    "auth": "/web/session/authenticate",
                    "search_read": "/web/dataset/search_read",
                    "create": "/web/dataset/call_kw",
                    "write": "/web/dataset/call_kw",
                    "unlink": "/web/dataset/call_kw"
                },
                default_headers={
                    "Content-Type": "application/json"
                },
                required_config_fields=["base_url", "database", "username", "password"],
                optional_config_fields=["version", "timeout"],
                default_settings={
                    "timeout": 30,
                    "data_format": "json",
                    "batch_size": 100
                },
                connector_class_path="taxpoynt_platform.external_integrations.business_systems.erp.odoo_connector.OdooConnector"
            ),
            ConnectorTemplate(
                template_id="sap_odata",
                name="SAP OData Connector",
                description="SAP Business Suite connector using OData protocol",
                connector_type=ConnectorType.ERP,
                protocol_type=ProtocolType.ODATA,
                authentication_type=AuthenticationType.BASIC_AUTH,
                default_endpoints={
                    "metadata": "/$metadata",
                    "service": "/"
                },
                default_headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                required_config_fields=["base_url", "username", "password"],
                optional_config_fields=["client", "language", "csrf_token"],
                default_settings={
                    "timeout": 60,
                    "data_format": "json",
                    "odata_version": "v2"
                },
                connector_class_path="taxpoynt_platform.external_integrations.connector_framework.protocol_adapters.odata_adapter.ODataConnector"
            ),
            ConnectorTemplate(
                template_id="firs_api",
                name="FIRS E-Invoice API",
                description="Nigerian FIRS e-invoicing API connector",
                connector_type=ConnectorType.GOVERNMENT,
                protocol_type=ProtocolType.REST,
                authentication_type=AuthenticationType.OAUTH2,
                default_endpoints={
                    "token": "/oauth/token",
                    "submit_invoice": "/api/v1/einvoice/submit",
                    "query_invoice": "/api/v1/einvoice/query",
                    "cancel_invoice": "/api/v1/einvoice/cancel"
                },
                default_headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                required_config_fields=["base_url", "client_id", "client_secret"],
                optional_config_fields=["scope", "environment"],
                default_settings={
                    "timeout": 30,
                    "data_format": "json",
                    "environment": "sandbox"
                },
                connector_class_path="taxpoynt_platform.app_services.firs_communication.firs_connector.FirsConnector"
            ),
            ConnectorTemplate(
                template_id="salesforce_crm",
                name="Salesforce CRM",
                description="Salesforce CRM connector with REST API",
                connector_type=ConnectorType.CRM,
                protocol_type=ProtocolType.REST,
                authentication_type=AuthenticationType.OAUTH2,
                default_endpoints={
                    "auth": "/services/oauth2/token",
                    "sobjects": "/services/data/v{version}/sobjects",
                    "query": "/services/data/v{version}/query"
                },
                default_headers={
                    "Content-Type": "application/json"
                },
                required_config_fields=["instance_url", "client_id", "client_secret"],
                optional_config_fields=["version", "username", "password"],
                default_settings={
                    "version": "58.0",
                    "timeout": 30,
                    "data_format": "json"
                },
                connector_class_path="taxpoynt_platform.external_integrations.connector_framework.protocol_adapters.rest_adapter.RestConnector"
            ),
            ConnectorTemplate(
                template_id="generic_graphql",
                name="Generic GraphQL API",
                description="Generic GraphQL connector with query/mutation support",
                connector_type=ConnectorType.API_GATEWAY,
                protocol_type=ProtocolType.GRAPHQL,
                authentication_type=AuthenticationType.JWT,
                default_endpoints={
                    "graphql": "/graphql",
                    "introspection": "/graphql?introspection"
                },
                default_headers={
                    "Content-Type": "application/json"
                },
                required_config_fields=["base_url"],
                optional_config_fields=["jwt_token", "schema_url"],
                default_settings={
                    "timeout": 30,
                    "data_format": "json"
                },
                connector_class_path="taxpoynt_platform.external_integrations.connector_framework.protocol_adapters.graphql_adapter.GraphQLConnector"
            )
        ]
        
        for template in builtin_templates:
            self.templates[template.template_id] = template
    
    def _load_connector_classes(self):
        """Load and cache connector classes"""
        # This would dynamically load connector classes based on the class paths
        # For now, we'll register known classes
        
        try:
            # Import and register known connector classes
            from .protocol_adapters.rest_adapter import RestConnector
            from .protocol_adapters.soap_adapter import SoapConnector
            from .protocol_adapters.graphql_adapter import GraphQLConnector
            from .protocol_adapters.odata_adapter import ODataConnector
            
            self.connector_classes["rest"] = RestConnector
            self.connector_classes["soap"] = SoapConnector
            self.connector_classes["graphql"] = GraphQLConnector
            self.connector_classes["odata"] = ODataConnector
            
        except ImportError as e:
            logger.warning(f"Some connector classes could not be imported: {e}")
    
    def add_template(self, template: ConnectorTemplate) -> bool:
        """Add a custom connector template"""
        try:
            self.templates[template.template_id] = template
            logger.info(f"Added connector template: {template.template_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add template: {e}")
            return False
    
    def get_template(self, template_id: str) -> Optional[ConnectorTemplate]:
        """Get a connector template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[ConnectorTemplate]:
        """List all available connector templates"""
        return list(self.templates.values())
    
    def create_connector_config(self, template_id: str, config_data: Dict[str, Any]) -> Optional[ConnectorConfig]:
        """Create a connector configuration from a template"""
        try:
            template = self.templates.get(template_id)
            if not template:
                logger.error(f"Template not found: {template_id}")
                return None
            
            # Validate required fields
            for field in template.required_config_fields:
                if field not in config_data:
                    logger.error(f"Required field missing: {field}")
                    return None
            
            # Merge with default settings
            merged_settings = template.default_settings.copy()
            merged_settings.update(config_data.get('custom_settings', {}))
            
            # Create configuration
            config = ConnectorConfig(
                connector_id=config_data.get('connector_id', f"{template_id}_{int(datetime.utcnow().timestamp())}"),
                name=config_data.get('name', template.name),
                connector_type=template.connector_type,
                protocol_type=template.protocol_type,
                authentication_type=template.authentication_type,
                base_url=config_data['base_url'],
                endpoints=template.default_endpoints.copy(),
                headers=template.default_headers.copy(),
                authentication_config=config_data.get('authentication_config', {}),
                timeout=config_data.get('timeout', template.default_settings.get('timeout', 30)),
                retry_attempts=config_data.get('retry_attempts', template.default_settings.get('retry_attempts', 3)),
                retry_delay=config_data.get('retry_delay', 5),
                rate_limit_per_minute=config_data.get('rate_limit_per_minute', 100),
                batch_size=config_data.get('batch_size', template.default_settings.get('batch_size', 100)),
                data_format=DataFormat(config_data.get('data_format', template.default_settings.get('data_format', 'json'))),
                ssl_verify=config_data.get('ssl_verify', True),
                proxy_config=config_data.get('proxy_config'),
                custom_settings=merged_settings,
                metadata={
                    'template_id': template_id,
                    'template_name': template.name,
                    **config_data.get('metadata', {})
                }
            )
            
            # Update endpoints with any custom ones
            if 'endpoints' in config_data:
                config.endpoints.update(config_data['endpoints'])
            
            # Update headers with any custom ones
            if 'headers' in config_data:
                config.headers.update(config_data['headers'])
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to create connector config: {e}")
            return None
    
    async def create_connector(self, config: ConnectorConfig, auto_initialize: bool = True) -> Optional[BaseConnector]:
        """Create a connector instance from configuration"""
        try:
            # Determine connector class
            connector_class = self._get_connector_class(config)
            if not connector_class:
                logger.error(f"No connector class found for protocol: {config.protocol_type.value}")
                return None
            
            # Create connector instance
            connector = connector_class(config)
            
            # Initialize if requested
            if auto_initialize:
                success = await connector.initialize()
                if not success:
                    logger.error(f"Failed to initialize connector: {config.connector_id}")
                    return None
            
            # Register connector
            self.active_connectors[config.connector_id] = connector
            register_connector(connector)
            
            logger.info(f"Created connector: {config.connector_id}")
            return connector
            
        except Exception as e:
            logger.error(f"Failed to create connector: {e}")
            return None
    
    def _get_connector_class(self, config: ConnectorConfig) -> Optional[Type[BaseConnector]]:
        """Get the appropriate connector class for the configuration"""
        try:
            # Check if we have a cached class for this protocol
            protocol_key = config.protocol_type.value
            if protocol_key in self.connector_classes:
                return self.connector_classes[protocol_key]
            
            # Try to load from template metadata
            template_id = config.metadata.get('template_id')
            if template_id and template_id in self.templates:
                template = self.templates[template_id]
                if template.connector_class_path:
                    return self._load_class_from_path(template.connector_class_path)
            
            # Fallback to protocol-based selection
            protocol_map = {
                ProtocolType.REST: "rest",
                ProtocolType.SOAP: "soap",
                ProtocolType.GRAPHQL: "graphql",
                ProtocolType.ODATA: "odata",
                ProtocolType.RPC: "rest"  # Use REST adapter for RPC as fallback
            }
            
            protocol_key = protocol_map.get(config.protocol_type)
            return self.connector_classes.get(protocol_key)
            
        except Exception as e:
            logger.error(f"Failed to get connector class: {e}")
            return None
    
    def _load_class_from_path(self, class_path: str) -> Optional[Type[BaseConnector]]:
        """Dynamically load a class from its path"""
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Failed to load class from path {class_path}: {e}")
            return None
    
    async def create_connector_from_template(self, template_id: str, config_data: Dict[str, Any], 
                                           auto_initialize: bool = True) -> Optional[BaseConnector]:
        """Create a connector directly from template and config data"""
        try:
            # Create configuration from template
            config = self.create_connector_config(template_id, config_data)
            if not config:
                return None
            
            # Create connector
            return await self.create_connector(config, auto_initialize)
            
        except Exception as e:
            logger.error(f"Failed to create connector from template: {e}")
            return None
    
    async def destroy_connector(self, connector_id: str) -> bool:
        """Destroy a connector and clean up resources"""
        try:
            if connector_id in self.active_connectors:
                connector = self.active_connectors[connector_id]
                
                # Disconnect the connector
                await connector.disconnect()
                
                # Remove from registries
                del self.active_connectors[connector_id]
                unregister_connector(connector_id)
                
                logger.info(f"Destroyed connector: {connector_id}")
                return True
            else:
                logger.warning(f"Connector not found: {connector_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to destroy connector: {e}")
            return False
    
    def get_connector(self, connector_id: str) -> Optional[BaseConnector]:
        """Get an active connector by ID"""
        return self.active_connectors.get(connector_id)
    
    def list_active_connectors(self) -> List[BaseConnector]:
        """List all active connectors"""
        return list(self.active_connectors.values())
    
    async def test_connection(self, template_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a connection configuration without creating a persistent connector"""
        try:
            # Create temporary configuration
            config = self.create_connector_config(template_id, config_data)
            if not config:
                return {
                    'success': False,
                    'error': 'Failed to create configuration'
                }
            
            # Create temporary connector
            connector_class = self._get_connector_class(config)
            if not connector_class:
                return {
                    'success': False,
                    'error': f'No connector class for protocol: {config.protocol_type.value}'
                }
            
            connector = connector_class(config)
            
            # Test connection
            start_time = datetime.utcnow()
            success = await connector.initialize()
            end_time = datetime.utcnow()
            
            # Clean up
            await connector.disconnect()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if success:
                return {
                    'success': True,
                    'response_time_ms': response_time,
                    'status': 'connected'
                }
            else:
                health_status = await connector.get_health_status()
                return {
                    'success': False,
                    'error': health_status.last_error or 'Connection test failed',
                    'response_time_ms': response_time,
                    'status': health_status.status.value
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': 'error'
            }
    
    async def bulk_create_connectors(self, connector_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple connectors in bulk"""
        results = {
            'successful': [],
            'failed': [],
            'total': len(connector_configs)
        }
        
        for config_data in connector_configs:
            try:
                template_id = config_data.get('template_id')
                if not template_id:
                    results['failed'].append({
                        'config': config_data,
                        'error': 'Missing template_id'
                    })
                    continue
                
                connector = await self.create_connector_from_template(
                    template_id, 
                    config_data, 
                    auto_initialize=True
                )
                
                if connector:
                    results['successful'].append({
                        'connector_id': connector.config.connector_id,
                        'name': connector.config.name,
                        'status': connector.status.value
                    })
                else:
                    results['failed'].append({
                        'config': config_data,
                        'error': 'Failed to create connector'
                    })
                    
            except Exception as e:
                results['failed'].append({
                    'config': config_data,
                    'error': str(e)
                })
        
        return results
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all active connectors"""
        results = {
            'total_connectors': len(self.active_connectors),
            'healthy': 0,
            'unhealthy': 0,
            'details': []
        }
        
        for connector in self.active_connectors.values():
            try:
                health = await connector.get_health_status()
                
                is_healthy = health.status in [ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED]
                if is_healthy:
                    results['healthy'] += 1
                else:
                    results['unhealthy'] += 1
                
                results['details'].append({
                    'connector_id': connector.config.connector_id,
                    'name': connector.config.name,
                    'status': health.status.value,
                    'response_time_ms': health.response_time_ms,
                    'success_rate_24h': health.success_rate_24h,
                    'last_error': health.last_error
                })
                
            except Exception as e:
                results['unhealthy'] += 1
                results['details'].append({
                    'connector_id': connector.config.connector_id,
                    'name': connector.config.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def get_factory_statistics(self) -> Dict[str, Any]:
        """Get factory statistics"""
        connector_types = {}
        protocol_types = {}
        
        for connector in self.active_connectors.values():
            # Count by connector type
            conn_type = connector.config.connector_type.value
            connector_types[conn_type] = connector_types.get(conn_type, 0) + 1
            
            # Count by protocol type
            protocol_type = connector.config.protocol_type.value
            protocol_types[protocol_type] = protocol_types.get(protocol_type, 0) + 1
        
        return {
            'total_templates': len(self.templates),
            'total_active_connectors': len(self.active_connectors),
            'connector_types': connector_types,
            'protocol_types': protocol_types,
            'available_protocols': list(self.connector_classes.keys())
        }

# Global factory instance
connector_factory = ConnectorFactory()

async def initialize_connector_factory():
    """Initialize the connector factory"""
    try:
        logger.info("Connector factory initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize connector factory: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_connector_factory()
        
        # Example usage
        config_data = {
            'connector_id': 'test_rest_api',
            'name': 'Test REST API',
            'base_url': 'https://api.example.com',
            'authentication_config': {
                'api_key': 'test_key'
            }
        }
        
        # Test connection
        result = await connector_factory.test_connection('generic_rest', config_data)
        print(f"Connection test result: {result}")
        
        if result['success']:
            # Create connector
            connector = await connector_factory.create_connector_from_template(
                'generic_rest', 
                config_data
            )
            
            if connector:
                print(f"Created connector: {connector.config.connector_id}")
                
                # Get factory stats
                stats = connector_factory.get_factory_statistics()
                print(f"Factory statistics: {stats}")
        
    asyncio.run(main())