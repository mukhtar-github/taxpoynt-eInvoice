"""
Microsoft Dynamics ERP Connector - Main Module
Integrates all Dynamics connector components for TaxPoynt eInvoice System Integrator functions.

This module combines OAuth 2.0 authentication, REST API communication, data extraction, 
and FIRS transformation into a unified connector interface compatible with the BaseERPConnector.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from app.schemas.integration import IntegrationTestResult
from ....connector_framework import BaseERPConnector
from .auth import DynamicsAuthenticator
from .rest_client import DynamicsRESTClient
from .data_extractor import DynamicsDataExtractor
from .firs_transformer import DynamicsFIRSTransformer
from .exceptions import DynamicsAPIError, DynamicsAuthenticationError, DynamicsConnectionError

logger = logging.getLogger(__name__)


class DynamicsERPConnector(BaseERPConnector):
    """
    Microsoft Dynamics 365 ERP Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for Microsoft Dynamics 365 integration,
    including OAuth 2.0 authentication, REST API connectivity, and data extraction.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - Microsoft Dynamics 365 REST API connectivity and OAuth 2.0 authentication
    - Data extraction from Dynamics Business Central and Finance modules
    - Connection health monitoring and error handling
    - Invoice data transformation for FIRS compliance
    - FIRS UBL format transformation
    
    Supported Dynamics Modules:
    - Business Central: Sales/Purchase Invoices, Customers, Vendors, Items
    - Finance & Operations: Advanced financial transactions (future)
    - Common Data Service: Cross-application data (future)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Microsoft Dynamics 365 connector with configuration.
        
        Args:
            config: Dictionary with Dynamics connection parameters
        """
        super().__init__(config)
        self.config = config
        
        # Initialize components
        self.authenticator = DynamicsAuthenticator(config)
        self.rest_client = DynamicsRESTClient(self.authenticator)
        self.data_extractor = DynamicsDataExtractor(self.rest_client)
        self.firs_transformer = DynamicsFIRSTransformer(self.data_extractor)
        
        logger.info(f"Initialized DynamicsERPConnector for {config.get('base_url', 'unknown')}")
    
    @property
    def erp_type(self) -> str:
        """Return the ERP system type"""
        return "dynamics"
    
    @property
    def erp_version(self) -> str:
        """Return the ERP system version"""
        # Dynamics version detection based on environment
        environment = self.config.get('environment', 'production')
        return f"Microsoft Dynamics 365 Business Central ({environment})"
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features"""
        return [
            "rest_api",
            "oauth2_authentication",
            "sales_invoices",
            "purchase_invoices",
            "customers",
            "vendors",
            "items",
            "companies",
            "firs_transformation",
            "ubl_format",
            "real_time_sync",
            "connection_testing",
            "data_validation",
            "json_format",
            "odata_support",
            "search_functionality",
            "pagination_support",
            "business_central",
            "tenant_isolation"
        ]
    
    # Connection and Authentication Methods
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to Microsoft Dynamics 365 - SI Role Function.
        
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
            
            # Test API access for different endpoints
            test_results = {}
            
            # Test companies API
            companies_result = await self.authenticator.test_api_access('companies')
            test_results['companies'] = companies_result.get('success', False)
            
            # Test customers API
            customers_result = await self.authenticator.test_api_access('customers')
            test_results['customers'] = customers_result.get('success', False)
            
            # Test sales invoices API
            sales_invoices_result = await self.authenticator.test_api_access('salesInvoices')
            test_results['sales_invoices'] = sales_invoices_result.get('success', False)
            
            # Test purchase invoices API
            purchase_invoices_result = await self.authenticator.test_api_access('purchaseInvoices')
            test_results['purchase_invoices'] = purchase_invoices_result.get('success', False)
            
            # Test vendors API
            vendors_result = await self.authenticator.test_api_access('vendors')
            test_results['vendors'] = vendors_result.get('success', False)
            
            # Overall success if at least one API is accessible
            overall_success = any(test_results.values())
            
            if overall_success:
                return IntegrationTestResult(
                    success=True,
                    message="Successfully connected to Microsoft Dynamics 365",
                    details={
                        "erp_type": self.erp_type,
                        "erp_version": self.erp_version,
                        "base_url": self.config.get('base_url'),
                        "tenant_id": self.config.get('tenant_id'),
                        "environment": self.config.get('environment'),
                        "company_id": self.config.get('company_id'),
                        "auth_method": "OAuth 2.0",
                        "companies_api_available": test_results.get('companies', False),
                        "customers_api_available": test_results.get('customers', False),
                        "sales_invoices_api_available": test_results.get('sales_invoices', False),
                        "purchase_invoices_api_available": test_results.get('purchase_invoices', False),
                        "vendors_api_available": test_results.get('vendors', False),
                        "supported_features": self.supported_features
                    }
                )
            else:
                return IntegrationTestResult(
                    success=False,
                    message="No Dynamics API endpoints are accessible",
                    error_code="API_ACCESS_ERROR",
                    details=test_results
                )
            
        except Exception as e:
            logger.error(f"Unexpected error during Dynamics connection test: {str(e)}")
            return IntegrationTestResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Dynamics 365 - SI Role Function.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            return await self.authenticator.authenticate()
        except Exception as e:
            logger.error(f"Dynamics authentication failed: {str(e)}")
            return False
    
    # Data Extraction Methods
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_number: Optional[str] = None,
        vendor_number: Optional[str] = None,
        status: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'sales_invoices'
    ) -> List[Dict[str, Any]]:
        """Get invoice list from Microsoft Dynamics 365"""
        return await self.data_extractor.get_invoices(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            customer_number=customer_number,
            vendor_number=vendor_number,
            status=status,
            include_attachments=include_attachments,
            data_source=data_source
        )
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str], invoice_type: str = 'sales') -> Dict[str, Any]:
        """Get a specific invoice by ID from Microsoft Dynamics 365"""
        return await self.data_extractor.get_invoice_by_id(invoice_id, invoice_type)
    
    async def search_invoices(
        self,
        customer_name: Optional[str] = None,
        vendor_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        status: Optional[str] = None,
        invoice_type: str = 'sales',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search invoices with specific criteria"""
        return await self.data_extractor.search_invoices(
            customer_name=customer_name,
            vendor_name=vendor_name,
            invoice_number=invoice_number,
            amount_range=amount_range,
            date_range=date_range,
            status=status,
            invoice_type=invoice_type,
            limit=limit
        )
    
    async def get_customers(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get customers from Dynamics Business Central"""
        return await self.data_extractor.get_customers(
            search_term=search_term,
            limit=limit,
            offset=offset
        )
    
    async def get_vendors(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get vendors from Dynamics Business Central"""
        return await self.data_extractor.get_vendors(
            search_term=search_term,
            limit=limit,
            offset=offset
        )
    
    async def get_products(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get items from Dynamics Business Central"""
        return await self.data_extractor.get_items(
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
        """Transform Dynamics invoice data to FIRS-compliant format"""
        return await self.firs_transformer.transform_to_firs_format(invoice_data, target_format)
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in Dynamics system"""
        return await self.firs_transformer.update_invoice_status(invoice_id, status_data)
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from Dynamics"""
        return await self.firs_transformer.get_tax_configuration()
    
    # Additional Dynamics-specific Methods
    async def get_companies(self) -> Dict[str, Any]:
        """Get companies from Dynamics Business Central"""
        return await self.rest_client.get_companies()
    
    async def get_sales_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get sales invoices directly from Dynamics Business Central API"""
        return await self.rest_client.get_sales_invoices(limit, offset, filters)
    
    async def get_purchase_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get purchase invoices directly from Dynamics Business Central API"""
        return await self.rest_client.get_purchase_invoices(limit, offset, filters)
    
    async def create_sales_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sales invoice in Dynamics"""
        return await self.rest_client.create_sales_invoice(invoice_data)
    
    async def update_sales_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing sales invoice in Dynamics"""
        return await self.rest_client.update_sales_invoice(invoice_id, invoice_data)
    
    async def get_metadata(self, entity: str) -> Dict[str, Any]:
        """Get metadata for a specific Dynamics entity"""
        return await self.rest_client.get_metadata(entity)
    
    # Connection Management
    async def disconnect(self) -> bool:
        """
        Disconnect from Microsoft Dynamics 365 - SI Role Function.
        
        Properly closes the connection to Dynamics 365 for System Integrator
        resource management and cleanup.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            return await self.authenticator.disconnect()
        except Exception as e:
            logger.error(f"Error during Dynamics disconnect: {str(e)}")
            return False
    
    # Utility Methods
    def is_connected(self) -> bool:
        """Check if connected to Dynamics"""
        return self.authenticator.is_authenticated()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        connection_info = self.authenticator.get_connection_info()
        connection_info.update({
            "erp_type": self.erp_type,
            "erp_version": self.erp_version,
            "last_activity": datetime.now().isoformat()
        })
        return connection_info
    
    # Legacy compatibility methods (maintaining original interface)
    async def get_partners(self, search_term: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get business partners from Dynamics - combines customers and vendors"""
        customers = await self.get_customers(search_term=search_term, limit=limit//2)
        vendors = await self.get_vendors(search_term=search_term, limit=limit//2)
        
        # Convert to partner format
        partners = []
        
        for customer in customers:
            partner = {
                "id": customer.get('id', ''),
                "name": customer.get('name', ''),
                "partner_type": "customer",
                "dynamics_number": customer.get('number', ''),
                "email": customer.get('email', ''),
                "phone": customer.get('phone', ''),
                "source": "dynamics_customers"
            }
            partners.append(partner)
        
        for vendor in vendors:
            partner = {
                "id": vendor.get('id', ''),
                "name": vendor.get('name', ''),
                "partner_type": "vendor",
                "dynamics_number": vendor.get('number', ''),
                "email": vendor.get('email', ''),
                "phone": vendor.get('phone', ''),
                "source": "dynamics_vendors"
            }
            partners.append(partner)
        
        return partners
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user"""
        return {
            "tenant_id": self.config.get('tenant_id', ''),
            "client_id": self.config.get('client_id', ''),
            "environment": self.config.get('environment', ''),
            "company_id": self.config.get('company_id', ''),
            "auth_method": "OAuth 2.0",
            "connected": self.is_connected()
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get information about the Dynamics system"""
        return {
            "erp_type": self.erp_type,
            "erp_version": self.erp_version,
            "base_url": self.config.get('base_url', ''),
            "tenant_id": self.config.get('tenant_id', ''),
            "environment": self.config.get('environment', ''),
            "company_id": self.config.get('company_id', ''),
            "system_type": "Microsoft Dynamics 365 Business Central",
            "available_modules": ["Business Central", "Finance & Operations", "Common Data Service"],
            "supported_apis": ["REST", "OData"],
            "authentication": "OAuth 2.0"
        }
    
    # Dynamics-specific methods
    def get_dynamics_url(self, endpoint: str, use_company_context: bool = True) -> str:
        """Get Dynamics API URL for an endpoint"""
        if use_company_context:
            return self.authenticator.get_business_central_url(endpoint)
        else:
            return self.authenticator.get_api_url('business_central', endpoint)
    
    async def test_dynamics_api(self, endpoint: str) -> Dict[str, Any]:
        """Test a specific Dynamics API endpoint"""
        return await self.authenticator.test_api_access(endpoint)
    
    def get_supported_modules(self) -> List[str]:
        """Get list of supported Dynamics modules"""
        return list(self.authenticator.api_paths.keys())