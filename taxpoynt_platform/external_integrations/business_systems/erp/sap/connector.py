"""
SAP ERP Connector - Main Module
Integrates all SAP connector components for TaxPoynt eInvoice System Integrator functions.

This module combines authentication, OData communication, data extraction, and FIRS transformation
into a unified connector interface compatible with the BaseERPConnector.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from app.schemas.integration import IntegrationTestResult
from ....connector_framework import BaseERPConnector
from .auth import SAPAuthenticator
from .odata_client import SAPODataClient
from .data_extractor import SAPDataExtractor
from .firs_transformer import SAPFIRSTransformer
from .exceptions import SAPODataError

logger = logging.getLogger(__name__)


class SAPConnector(BaseERPConnector):
    """
    SAP ERP Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for SAP ERP integration,
    including OData API connectivity, authentication, and data extraction.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - SAP OData service connectivity and authentication (OAuth2/Basic)
    - Data extraction from SAP billing and journal services
    - Connection health monitoring and error handling
    - Invoice data transformation for FIRS compliance
    - FIRS UBL format transformation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SAP connector with configuration.
        
        Args:
            config: Dictionary with SAP connection parameters
        """
        super().__init__(config)
        self.config = config
        
        # Initialize components
        self.authenticator = SAPAuthenticator(config)
        self.odata_client = SAPODataClient(self.authenticator)
        self.data_extractor = SAPDataExtractor(self.odata_client)
        self.firs_transformer = SAPFIRSTransformer(self.data_extractor)
        
        logger.info(f"Initialized SAPConnector for {config.get('base_url', 'unknown')}")
    
    @property
    def erp_type(self) -> str:
        """Return the ERP system type"""
        return "sap"
    
    @property
    def erp_version(self) -> str:
        """Return the ERP system version"""
        # SAP version detection would require metadata analysis
        return "S/4HANA Cloud"  # Default assumption
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features"""
        return [
            "odata_api",
            "billing_documents",
            "journal_entries", 
            "business_partners",
            "oauth_authentication",
            "basic_authentication",
            "firs_transformation",
            "ubl_format",
            "real_time_sync",
            "connection_testing",
            "data_validation",
            "metadata_access",
            "document_search"
        ]
    
    # Connection and Authentication Methods
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to SAP ERP - SI Role Function.
        
        Validates connectivity and authentication for System Integrator
        ERP integration health monitoring.
        
        Returns:
            IntegrationTestResult with connection status and details
        """
        try:
            # Test authentication
            auth_result = await self.authenticator.test_authentication()
            if not auth_result.get('success'):
                return IntegrationTestResult(
                    success=False,
                    message=f"Authentication failed: {auth_result.get('error')}",
                    error_code="AUTHENTICATION_ERROR"
                )
            
            # Test metadata access
            metadata_result = await self.authenticator.test_metadata_access()
            if not metadata_result.get('success'):
                return IntegrationTestResult(
                    success=False,
                    message=f"Metadata access failed: {metadata_result.get('error')}",
                    error_code="METADATA_ACCESS_ERROR"
                )
            
            # Test billing service
            billing_result = await self.authenticator.test_billing_service()
            if not billing_result.get('success'):
                return IntegrationTestResult(
                    success=False,
                    message=f"Billing service access failed: {billing_result.get('error')}",
                    error_code="BILLING_SERVICE_ERROR"
                )
            
            # Test partner service
            partner_result = await self.authenticator.test_partner_service()
            partner_available = partner_result.get('success', False)
            
            return IntegrationTestResult(
                success=True,
                message="Successfully connected to SAP ERP",
                details={
                    "erp_type": self.erp_type,
                    "erp_version": self.erp_version,
                    "base_url": self.config.get('base_url'),
                    "auth_method": "OAuth2" if self.config.get('use_oauth') else "Basic",
                    "billing_service_available": billing_result.get('success', False),
                    "partner_service_available": partner_available,
                    "metadata_accessible": metadata_result.get('success', False),
                    "supported_features": self.supported_features
                }
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during SAP connection test: {str(e)}")
            return IntegrationTestResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with SAP ERP - SI Role Function.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            return await self.authenticator.authenticate()
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    # Data Extraction Methods
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        document_type: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'billing'
    ) -> List[Dict[str, Any]]:
        """Get invoice list from SAP ERP"""
        return await self.data_extractor.get_invoices(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            document_type=document_type,
            include_attachments=include_attachments,
            data_source=data_source
        )
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """Get a specific invoice by ID from SAP ERP"""
        return await self.data_extractor.get_invoice_by_id(invoice_id)
    
    async def search_invoices(
        self,
        customer_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search invoices with specific criteria"""
        return await self.data_extractor.search_invoices(
            customer_name=customer_name,
            invoice_number=invoice_number,
            amount_range=amount_range,
            date_range=date_range,
            limit=limit
        )
    
    async def get_partners(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get business partners from SAP ERP"""
        return await self.data_extractor.get_partners(
            search_term=search_term,
            limit=limit,
            offset=offset
        )
    
    # FIRS Transformation Methods
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate invoice data before FIRS submission"""
        return await self.firs_transformer.validate_invoice_data(invoice_data)
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform SAP invoice data to FIRS-compliant format"""
        return await self.firs_transformer.transform_to_firs_format(invoice_data, target_format)
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in SAP system"""
        return await self.firs_transformer.update_invoice_status(invoice_id, status_data)
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from SAP"""
        return await self.firs_transformer.get_tax_configuration()
    
    # Additional SAP-specific Methods
    async def get_billing_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get billing documents directly from SAP OData API"""
        return await self.odata_client.get_billing_documents(limit, offset, filters)
    
    async def get_journal_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get journal entries directly from SAP OData API"""
        return await self.odata_client.get_journal_entries(limit, offset, filters)
    
    async def get_business_partners(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get business partners directly from SAP OData API"""
        return await self.odata_client.get_business_partners(limit, offset, search_term)
    
    async def get_metadata(self, service: str) -> Dict[str, Any]:
        """Get OData metadata for a specific service"""
        return await self.odata_client.get_metadata(service)
    
    # Connection Management
    async def disconnect(self) -> bool:
        """
        Disconnect from SAP ERP - SI Role Function.
        
        Properly closes the connection to SAP ERP for System Integrator
        resource management and cleanup.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            return await self.authenticator.disconnect()
        except Exception as e:
            logger.error(f"Error during SAP disconnect: {str(e)}")
            return False
    
    # Utility Methods
    def is_connected(self) -> bool:
        """Check if connected to SAP"""
        return self.authenticator.is_authenticated()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "connected": self.is_connected(),
            "erp_type": self.erp_type,
            "erp_version": self.erp_version,
            "base_url": self.config.get('base_url'),
            "auth_method": "OAuth2" if self.config.get('use_oauth') else "Basic",
            "username": self.config.get('username') if not self.config.get('use_oauth') else None,
            "oauth_client_id": self.config.get('oauth_client_id') if self.config.get('use_oauth') else None,
            "verify_ssl": self.config.get('verify_ssl', True),
            "last_activity": datetime.now().isoformat()
        }
    
    # Legacy compatibility methods (maintaining original interface)
    async def get_customers(self, limit: int = 100, offset: int = 0, search_term: str = None) -> List[Dict[str, Any]]:
        """Legacy method - maps to get_partners for SAP"""
        partners = await self.get_partners(search_term=search_term, limit=limit, offset=offset)
        # Filter for customers only
        return [p for p in partners if p.get('is_customer', False)]
    
    async def get_products(self, limit: int = 100, offset: int = 0, search_term: str = None) -> List[Dict[str, Any]]:
        """Legacy method - SAP product master data would require separate implementation"""
        logger.warning("Product data extraction not yet implemented for SAP connector")
        return []
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user"""
        return {
            "username": self.config.get('username', ''),
            "auth_method": "OAuth2" if self.config.get('use_oauth') else "Basic",
            "connected": self.is_connected()
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get information about the SAP system"""
        return {
            "erp_type": self.erp_type,
            "erp_version": self.erp_version,
            "base_url": self.config.get('base_url', ''),
            "system_type": "SAP S/4HANA Cloud"
        }