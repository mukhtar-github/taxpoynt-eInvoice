"""
Odoo ERP Connector - Main Module
Integrates all Odoo connector components for TaxPoynt eInvoice System Integrator functions.

This module combines authentication, data extraction, and FIRS transformation
into a unified connector interface compatible with the BaseERPConnector.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from app.schemas.integration import OdooConfig, IntegrationTestResult
from ....connector_framework import BaseERPConnector
from .auth import OdooAuthenticator
from .data_extractor import OdooDataExtractor  
from .firs_transformer import OdooFIRSTransformer
from .exceptions import OdooConnectorError, OdooConnectionError, OdooAuthenticationError, OdooDataError

logger = logging.getLogger(__name__)


class OdooConnector(BaseERPConnector):
    """
    OdooConnector class for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for Odoo ERP integration,
    including connection management, data extraction, and ERP system communication.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - ERP system connectivity and authentication
    - Data extraction from Odoo instances (invoices, customers, products)
    - Connection health monitoring and error handling
    - Invoice data transformation for FIRS compliance
    - FIRS UBL format transformation
    """
    
    def __init__(self, config: Union[OdooConfig, Dict[str, Any]]):
        """
        Initialize the Odoo connector with configuration.
        
        Args:
            config: OdooConfig instance or dictionary with connection parameters
        """
        super().__init__(config)
        
        # Convert dict to OdooConfig if needed
        if isinstance(config, dict):
            self.config = OdooConfig(**config)
        else:
            self.config = config
        
        # Initialize components
        self.authenticator = OdooAuthenticator(self.config)
        self.data_extractor = OdooDataExtractor(self.authenticator)
        self.firs_transformer = OdooFIRSTransformer(self.data_extractor)
        
        logger.info(f"Initialized OdooConnector for {self.config.url}")
    
    @property
    def erp_type(self) -> str:
        """Return the ERP system type"""
        return "odoo"
    
    @property 
    def erp_version(self) -> str:
        """Return the ERP system version"""
        if hasattr(self.authenticator, 'version_info') and self.authenticator.version_info:
            return self.authenticator.version_info.get('server_version', 'unknown')
        return "unknown"
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features"""
        features = [
            "invoice_extraction",
            "customer_management", 
            "product_catalog",
            "partner_management",
            "attachment_handling",
            "firs_transformation",
            "ubl_format",
            "real_time_sync",
            "batch_processing",
            "connection_testing",
            "data_validation"
        ]
        
        # Add version-specific features
        if hasattr(self.authenticator, 'major_version'):
            if self.authenticator.major_version >= 13:
                features.extend(["advanced_partner_ranking", "improved_accounting"])
            if self.authenticator.major_version >= 15:
                features.extend(["modern_ui_support", "enhanced_api"])
        
        return features
    
    # Connection and Authentication Methods
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to Odoo ERP - SI Role Function.
        
        Validates connectivity and authentication for System Integrator
        ERP integration health monitoring.
        
        Returns:
            IntegrationTestResult with connection status and details
        """
        try:
            # Test basic connection
            self.authenticator.connect()
            
            # Test authentication
            self.authenticator.authenticate()
            
            # Test data access
            user_info = self.authenticator.get_user_info()
            company_info = self.authenticator.get_company_info()
            
            # Test basic data extraction
            customers = self.data_extractor.get_customers(limit=1)
            products = self.data_extractor.get_products(limit=1)
            
            return IntegrationTestResult(
                success=True,
                message="Successfully connected to Odoo ERP",
                details={
                    "erp_type": self.erp_type,
                    "erp_version": self.erp_version,
                    "user": user_info.get('name'),
                    "company": company_info.get('name'),
                    "database": self.config.database,
                    "customers_available": len(customers) > 0,
                    "products_available": len(products) > 0,
                    "supported_features": self.supported_features
                }
            )
            
        except OdooConnectionError as e:
            return IntegrationTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                error_code="CONNECTION_ERROR"
            )
        except OdooAuthenticationError as e:
            return IntegrationTestResult(
                success=False,
                message=f"Authentication failed: {str(e)}",
                error_code="AUTHENTICATION_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {str(e)}")
            return IntegrationTestResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Odoo ERP - SI Role Function.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            self.authenticator.authenticate()
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    # Data Extraction Methods
    def get_customers(self, limit: int = 100, offset: int = 0, search_term: str = None) -> List[Dict[str, Any]]:
        """Get customer list from Odoo ERP"""
        return self.data_extractor.get_customers(limit=limit, offset=offset, search_term=search_term)
    
    def get_products(self, limit: int = 100, offset: int = 0, search_term: str = None) -> List[Dict[str, Any]]:
        """Get product list from Odoo ERP"""
        return self.data_extractor.get_products(limit=limit, offset=offset, search_term=search_term)
    
    def get_invoices(self, 
                    limit: int = 100, 
                    offset: int = 0, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    state: Optional[str] = None,
                    include_attachments: bool = False) -> List[Dict[str, Any]]:
        """Get invoice list from Odoo ERP"""
        return self.data_extractor.get_invoices(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            state=state,
            include_attachments=include_attachments
        )
    
    def get_invoice_by_id(self, invoice_id: int, include_attachments: bool = False) -> Dict[str, Any]:
        """Get a specific invoice by ID from Odoo ERP"""
        return self.data_extractor.get_invoice_by_id(invoice_id, include_attachments)
    
    def search_invoices(self,
                       customer_name: Optional[str] = None,
                       invoice_number: Optional[str] = None,
                       amount_range: Optional[tuple] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Search invoices with specific criteria"""
        return self.data_extractor.search_invoices(
            customer_name=customer_name,
            invoice_number=invoice_number,
            amount_range=amount_range,
            limit=limit
        )
    
    def get_partners(self, search_term: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get business partners from Odoo ERP"""
        return self.data_extractor.get_partners(search_term=search_term, limit=limit)
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user"""
        return self.authenticator.get_user_info()
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get information about the company"""
        return self.authenticator.get_company_info()
    
    # FIRS Transformation Methods
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate invoice data before FIRS submission"""
        return await self.firs_transformer.validate_invoice_data(invoice_data)
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform ERP invoice data to FIRS-compliant format"""
        return await self.firs_transformer.transform_to_firs_format(invoice_data, target_format)
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in the ERP system"""
        return await self.firs_transformer.update_invoice_status(invoice_id, status_data)
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from Odoo"""
        return await self.firs_transformer.get_tax_configuration()
    
    # Connection Management
    async def disconnect(self) -> bool:
        """
        Disconnect from Odoo ERP - SI Role Function.
        
        Properly closes the connection to Odoo ERP for System Integrator
        resource management and cleanup.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if hasattr(self.authenticator, 'odoo') and self.authenticator.odoo:
                # OdooRPC doesn't have explicit disconnect, just clear the session
                self.authenticator.odoo = None
                
            logger.info("Disconnected from Odoo ERP")
            return True
            
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
            return False
    
    # Utility Methods
    def is_connected(self) -> bool:
        """Check if connected to Odoo"""
        return self.authenticator.is_connected()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "connected": self.is_connected(),
            "erp_type": self.erp_type,
            "erp_version": self.erp_version,
            "database": self.config.database,
            "host": getattr(self.authenticator, 'host', None),
            "port": getattr(self.authenticator, 'port', None),
            "protocol": getattr(self.authenticator, 'protocol', None),
            "last_activity": datetime.now().isoformat()
        }