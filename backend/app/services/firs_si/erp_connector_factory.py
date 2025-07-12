"""
ERP Connector Factory

This module provides a factory class for creating ERP connectors with seamless
switching capability between different ERP systems (Odoo, SAP, Oracle).

The factory pattern ensures consistent connector creation and supports both
production and mock connectors for development and testing.
"""

from typing import Dict, Any, Optional, Type
import logging
from enum import Enum

from app.services.firs_si.base_erp_connector import BaseERPConnector
from app.services.firs_si.odoo_connector import OdooConnector
from app.schemas.integration import OdooConfig


class ERPType(str, Enum):
    """Supported ERP system types"""
    ODOO = "odoo"
    SAP = "sap"
    ORACLE = "oracle"


class UnsupportedERPError(Exception):
    """Exception raised for unsupported ERP systems"""
    pass


class ERPConnectorFactory:
    """
    Factory class for creating ERP connectors with seamless switching capability
    
    This factory supports multiple ERP systems and can create both production
    and mock connectors for development and testing purposes.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._registered_connectors: Dict[str, Type[BaseERPConnector]] = {}
        self._mock_connectors: Dict[str, Type[BaseERPConnector]] = {}
        
        # Register default connectors
        self._register_default_connectors()
    
    def _register_default_connectors(self) -> None:
        """Register default ERP connectors"""
        try:
            # Register Odoo connector
            self._registered_connectors[ERPType.ODOO] = OdooConnector
            
            # Register SAP connector when available
            try:
                from app.services.firs_si.sap_connector import SAPConnector
                self._registered_connectors[ERPType.SAP] = SAPConnector
            except ImportError:
                self.logger.debug("SAP connector not available")
                
            # Register Oracle connector when available
            try:
                from app.services.firs_si.oracle_connector import OracleConnector
                self._registered_connectors[ERPType.ORACLE] = OracleConnector
            except ImportError:
                self.logger.debug("Oracle connector not available")
                
            # Register mock connectors for development
            self._register_mock_connectors()
                
        except Exception as e:
            self.logger.error(f"Error registering default connectors: {str(e)}")
    
    def _register_mock_connectors(self) -> None:
        """Register mock connectors for development and testing"""
        try:
            # Register mock SAP connector
            try:
                from app.services.firs_si.mock_sap_connector import MockSAPConnector
                self._mock_connectors[ERPType.SAP] = MockSAPConnector
            except ImportError:
                self.logger.debug("Mock SAP connector not available")
                
            # Register mock Oracle connector
            try:
                from app.services.firs_si.mock_oracle_connector import MockOracleConnector
                self._mock_connectors[ERPType.ORACLE] = MockOracleConnector
            except ImportError:
                self.logger.debug("Mock Oracle connector not available")
                
        except Exception as e:
            self.logger.error(f"Error registering mock connectors: {str(e)}")
    
    def register_connector(
        self,
        erp_type: str,
        connector_class: Type[BaseERPConnector],
        is_mock: bool = False
    ) -> None:
        """
        Register a new ERP connector
        
        Args:
            erp_type: ERP system type identifier
            connector_class: Connector class that implements BaseERPConnector
            is_mock: Whether this is a mock connector for testing
        """
        try:
            if not issubclass(connector_class, BaseERPConnector):
                raise ValueError(f"Connector class must inherit from BaseERPConnector")
                
            if is_mock:
                self._mock_connectors[erp_type] = connector_class
                self.logger.info(f"Registered mock connector for {erp_type}")
            else:
                self._registered_connectors[erp_type] = connector_class
                self.logger.info(f"Registered connector for {erp_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to register connector for {erp_type}: {str(e)}")
            raise
    
    def create_connector(
        self,
        erp_type: str,
        config: Dict[str, Any],
        use_mock: bool = False
    ) -> BaseERPConnector:
        """
        Create an ERP connector instance
        
        Args:
            erp_type: ERP system type ('odoo', 'sap', 'oracle')
            config: Configuration dictionary for the connector
            use_mock: Whether to create a mock connector for development/testing
            
        Returns:
            BaseERPConnector instance
            
        Raises:
            UnsupportedERPError: If ERP type is not supported
            ValueError: If configuration is invalid
        """
        try:
            self.logger.debug(f"Creating connector for ERP type: {erp_type}, use_mock: {use_mock}")
            
            # Validate ERP type
            if erp_type not in self.get_supported_erp_types():
                raise UnsupportedERPError(f"ERP type '{erp_type}' is not supported")
            
            # Validate configuration
            self._validate_config(erp_type, config)
            
            # Determine which connector to use
            connector_class = None
            
            if use_mock or config.get('use_mock', False):
                # Use mock connector if requested or configured
                connector_class = self._mock_connectors.get(erp_type)
                if not connector_class:
                    self.logger.warning(f"Mock connector not available for {erp_type}, using production connector")
                    connector_class = self._registered_connectors.get(erp_type)
            else:
                # Use production connector
                connector_class = self._registered_connectors.get(erp_type)
            
            if not connector_class:
                raise UnsupportedERPError(f"No connector available for ERP type '{erp_type}'")
            
            # Create connector instance
            connector = connector_class(config)
            
            self.logger.info(f"Created {erp_type} connector: {connector.__class__.__name__}")
            
            return connector
            
        except Exception as e:
            self.logger.error(f"Failed to create connector for {erp_type}: {str(e)}")
            raise
    
    def _validate_config(self, erp_type: str, config: Dict[str, Any]) -> None:
        """
        Validate configuration for the specific ERP type
        
        Args:
            erp_type: ERP system type
            config: Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not config:
            raise ValueError("Configuration cannot be empty")
        
        # ERP-specific validation
        if erp_type == ERPType.ODOO:
            required_fields = ['host', 'port', 'database', 'username', 'password']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field '{field}' for Odoo configuration")
        
        elif erp_type == ERPType.SAP:
            # SAP can use either basic auth or OAuth2
            if config.get('use_oauth', True):
                required_fields = ['host', 'client_id', 'client_secret']
            else:
                required_fields = ['host', 'username', 'password']
            
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field '{field}' for SAP configuration")
        
        elif erp_type == ERPType.ORACLE:
            required_fields = ['instance_url', 'username', 'password']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field '{field}' for Oracle configuration")
    
    def get_supported_erp_types(self) -> list[str]:
        """
        Get list of supported ERP types
        
        Returns:
            List of supported ERP type strings
        """
        return list(set(list(self._registered_connectors.keys()) + list(self._mock_connectors.keys())))
    
    def get_available_connectors(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about available connectors
        
        Returns:
            Dictionary with connector information
        """
        connectors_info = {}
        
        for erp_type in self.get_supported_erp_types():
            production_connector = self._registered_connectors.get(erp_type)
            mock_connector = self._mock_connectors.get(erp_type)
            
            connectors_info[erp_type] = {
                'production_available': production_connector is not None,
                'mock_available': mock_connector is not None,
                'production_class': production_connector.__name__ if production_connector else None,
                'mock_class': mock_connector.__name__ if mock_connector else None
            }
        
        return connectors_info
    
    def create_odoo_connector(self, config: OdooConfig) -> BaseERPConnector:
        """
        Convenience method to create Odoo connector
        
        Args:
            config: Odoo configuration
            
        Returns:
            Odoo connector instance
        """
        return self.create_connector(ERPType.ODOO, config.dict())
    
    def create_sap_connector(
        self,
        config: Dict[str, Any],
        use_mock: bool = False
    ) -> BaseERPConnector:
        """
        Convenience method to create SAP connector
        
        Args:
            config: SAP configuration
            use_mock: Whether to use mock connector
            
        Returns:
            SAP connector instance
        """
        return self.create_connector(ERPType.SAP, config, use_mock=use_mock)
    
    def create_oracle_connector(
        self,
        config: Dict[str, Any],
        use_mock: bool = False
    ) -> BaseERPConnector:
        """
        Convenience method to create Oracle connector
        
        Args:
            config: Oracle configuration
            use_mock: Whether to use mock connector
            
        Returns:
            Oracle connector instance
        """
        return self.create_connector(ERPType.ORACLE, config, use_mock=use_mock)
    
    async def test_all_connectors(self) -> Dict[str, Any]:
        """
        Test all available connectors (for diagnostics)
        
        Returns:
            Dictionary with test results for all connectors
        """
        test_results = {}
        
        for erp_type in self.get_supported_erp_types():
            try:
                # Create a basic test configuration
                test_config = self._create_test_config(erp_type)
                
                # Test production connector
                if erp_type in self._registered_connectors:
                    try:
                        connector = self.create_connector(erp_type, test_config)
                        test_results[f"{erp_type}_production"] = {
                            'available': True,
                            'connector_class': connector.__class__.__name__,
                            'erp_type': connector.erp_type,
                            'supported_features': connector.supported_features
                        }
                    except Exception as e:
                        test_results[f"{erp_type}_production"] = {
                            'available': False,
                            'error': str(e)
                        }
                
                # Test mock connector
                if erp_type in self._mock_connectors:
                    try:
                        connector = self.create_connector(erp_type, test_config, use_mock=True)
                        test_results[f"{erp_type}_mock"] = {
                            'available': True,
                            'connector_class': connector.__class__.__name__,
                            'erp_type': connector.erp_type,
                            'supported_features': connector.supported_features
                        }
                    except Exception as e:
                        test_results[f"{erp_type}_mock"] = {
                            'available': False,
                            'error': str(e)
                        }
                        
            except Exception as e:
                test_results[erp_type] = {
                    'error': f"Failed to test {erp_type}: {str(e)}"
                }
        
        return test_results
    
    def _create_test_config(self, erp_type: str) -> Dict[str, Any]:
        """Create minimal test configuration for the given ERP type"""
        test_configs = {
            ERPType.ODOO: {
                'host': 'test.odoo.com',
                'port': 8069,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_password',
                'use_ssl': True
            },
            ERPType.SAP: {
                'host': 'test.sap.com',
                'client': '100',
                'client_id': 'test_client',
                'client_secret': 'test_secret',
                'use_oauth': True,
                'use_mock': True
            },
            ERPType.ORACLE: {
                'instance_url': 'https://test.oracle.com',
                'username': 'test_user',
                'password': 'test_password',
                'use_mock': True
            }
        }
        
        return test_configs.get(erp_type, {})


# Global factory instance
erp_factory = ERPConnectorFactory()