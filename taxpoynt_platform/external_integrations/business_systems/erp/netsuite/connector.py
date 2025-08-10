"""
NetSuite ERP Connector - Main Module
Integrates all NetSuite connector components for TaxPoynt eInvoice System Integrator functions.

This module combines OAuth 1.0a authentication, REST API communication, data extraction, 
and FIRS transformation into a unified connector interface compatible with the BaseERPConnector.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from app.schemas.integration import IntegrationTestResult
from ....connector_framework import BaseERPConnector
from .auth import NetSuiteAuthenticator
from .rest_client import NetSuiteRESTClient
from .data_extractor import NetSuiteDataExtractor
from .firs_transformer import NetSuiteFIRSTransformer
from .exceptions import NetSuiteAPIError, NetSuiteAuthenticationError, NetSuiteConnectionError

logger = logging.getLogger(__name__)


class NetSuiteERPConnector(BaseERPConnector):
    """
    NetSuite ERP Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for NetSuite integration,
    including OAuth 1.0a authentication, REST API connectivity, and data extraction.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - NetSuite REST API connectivity and OAuth 1.0a authentication
    - Data extraction from NetSuite records and SuiteQL queries
    - Connection health monitoring and error handling
    - Invoice data transformation for FIRS compliance
    - FIRS UBL format transformation
    
    Supported NetSuite APIs:
    - REST API: Record-level operations (CRUD)
    - SuiteQL: Advanced querying and reporting
    - RESTlets: Custom business logic execution
    - SuiteTalk: Web services integration (future)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the NetSuite connector with configuration.
        
        Args:
            config: Dictionary with NetSuite connection parameters
        """
        super().__init__(config)
        self.config = config
        
        # Initialize components
        self.authenticator = NetSuiteAuthenticator(config)
        self.rest_client = NetSuiteRESTClient(self.authenticator)
        self.data_extractor = NetSuiteDataExtractor(self.rest_client)
        self.firs_transformer = NetSuiteFIRSTransformer(self.data_extractor)
        
        logger.info(f"Initialized NetSuiteERPConnector for {config.get('account_id', 'unknown')}")
    
    @property
    def erp_type(self) -> str:
        """Return the ERP system type"""
        return "netsuite"
    
    @property
    def erp_version(self) -> str:
        """Return the ERP system version"""
        # NetSuite version detection based on API endpoints
        return "NetSuite ERP (REST API 2021.2)"
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features"""
        return [
            "rest_api",
            "oauth1_authentication",
            "invoices",
            "customers",
            "vendors",
            "items",
            "subsidiaries",
            "currencies",
            "tax_codes",
            "firs_transformation",
            "ubl_format",
            "real_time_sync",
            "connection_testing",
            "data_validation",
            "json_format",
            "suiteql_queries",
            "search_functionality",
            "pagination_support",
            "multi_subsidiary",
            "multi_currency",
            "restlets_support",
            "file_cabinet_access"
        ]
    
    # Connection and Authentication Methods
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to NetSuite ERP - SI Role Function.
        
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
            
            # Test invoices API
            invoices_result = await self.authenticator.test_api_access('invoices')
            test_results['invoices'] = invoices_result.get('success', False)
            
            # Test vendors API
            vendors_result = await self.authenticator.test_api_access('vendors')
            test_results['vendors'] = vendors_result.get('success', False)
            
            # Test SuiteQL API
            suiteql_result = await self.authenticator.test_api_access('suiteql')
            test_results['suiteql'] = suiteql_result.get('success', False)
            
            # Overall success if at least one API is accessible
            overall_success = any(test_results.values())
            
            if overall_success:
                return IntegrationTestResult(
                    success=True,
                    message="Successfully connected to NetSuite ERP",
                    details={
                        "erp_type": self.erp_type,
                        "erp_version": self.erp_version,
                        "base_url": self.config.get('base_url'),
                        "account_id": self.config.get('account_id'),
                        "consumer_key": self.config.get('consumer_key'),
                        "auth_method": "OAuth 1.0a",
                        "companies_api_available": test_results.get('companies', False),
                        "customers_api_available": test_results.get('customers', False),
                        "invoices_api_available": test_results.get('invoices', False),
                        "vendors_api_available": test_results.get('vendors', False),
                        "suiteql_api_available": test_results.get('suiteql', False),
                        "supported_features": self.supported_features
                    }
                )
            else:
                return IntegrationTestResult(
                    success=False,
                    message="No NetSuite API endpoints are accessible",
                    error_code="API_ACCESS_ERROR",
                    details=test_results
                )
            
        except Exception as e:
            logger.error(f"Unexpected error during NetSuite connection test: {str(e)}")
            return IntegrationTestResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with NetSuite ERP - SI Role Function.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            return await self.authenticator.authenticate()
        except Exception as e:
            logger.error(f"NetSuite authentication failed: {str(e)}")
            return False
    
    # Data Extraction Methods
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'invoices'
    ) -> List[Dict[str, Any]]:
        """Get invoice list from NetSuite ERP"""
        return await self.data_extractor.get_invoices(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
            status=status,
            include_attachments=include_attachments,
            data_source=data_source
        )
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """Get a specific invoice by ID from NetSuite ERP"""
        return await self.data_extractor.get_invoice_by_id(invoice_id)
    
    async def search_invoices(
        self,
        customer_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search invoices with specific criteria"""
        return await self.data_extractor.search_invoices(
            customer_name=customer_name,
            invoice_number=invoice_number,
            amount_range=amount_range,
            date_range=date_range,
            status=status,
            limit=limit
        )
    
    async def get_customers(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get customers from NetSuite ERP"""
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
        """Get vendors from NetSuite ERP"""
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
        """Get items from NetSuite ERP"""
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
        """Transform NetSuite invoice data to FIRS-compliant format"""
        return await self.firs_transformer.transform_to_firs_format(invoice_data, target_format)
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in NetSuite system"""
        return await self.firs_transformer.update_invoice_status(invoice_id, status_data)
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from NetSuite"""
        return await self.firs_transformer.get_tax_configuration()
    
    # Additional NetSuite-specific Methods
    async def get_subsidiaries(self) -> Dict[str, Any]:
        """Get subsidiaries from NetSuite"""
        return await self.rest_client.get_subsidiaries()
    
    async def get_currencies(self) -> Dict[str, Any]:
        """Get currencies from NetSuite"""
        return await self.rest_client.get_currencies()
    
    async def get_tax_codes(self) -> Dict[str, Any]:
        """Get tax codes from NetSuite"""
        return await self.rest_client.get_tax_codes()
    
    async def execute_suiteql(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a SuiteQL query"""
        return await self.rest_client.execute_suiteql(query, params)
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice in NetSuite"""
        return await self.rest_client.create_invoice(invoice_data)
    
    async def update_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing invoice in NetSuite"""
        return await self.rest_client.update_invoice(invoice_id, invoice_data)
    
    # Connection Management
    async def disconnect(self) -> bool:
        """
        Disconnect from NetSuite ERP - SI Role Function.
        
        Properly closes the connection to NetSuite for System Integrator
        resource management and cleanup.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            return await self.authenticator.disconnect()
        except Exception as e:
            logger.error(f"Error during NetSuite disconnect: {str(e)}")
            return False
    
    # Utility Methods
    def is_connected(self) -> bool:
        """Check if connected to NetSuite"""
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
        """Get business partners from NetSuite - combines customers and vendors"""
        customers = await self.get_customers(search_term=search_term, limit=limit//2)
        vendors = await self.get_vendors(search_term=search_term, limit=limit//2)
        
        # Convert to partner format
        partners = []
        
        for customer in customers:
            partner = {
                "id": customer.get('id', ''),
                "name": customer.get('name', ''),
                "partner_type": "customer",
                "entity_id": customer.get('entity_id', ''),
                "email": customer.get('email', ''),
                "phone": customer.get('phone', ''),
                "source": "netsuite_customers"
            }
            partners.append(partner)
        
        for vendor in vendors:
            partner = {
                "id": vendor.get('id', ''),
                "name": vendor.get('name', ''),
                "partner_type": "vendor",
                "entity_id": vendor.get('entity_id', ''),
                "email": vendor.get('email', ''),
                "phone": vendor.get('phone', ''),
                "source": "netsuite_vendors"
            }
            partners.append(partner)
        
        return partners
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user"""
        return {
            "account_id": self.config.get('account_id', ''),
            "consumer_key": self.config.get('consumer_key', ''),
            "token_id": self.config.get('token_id', ''),
            "auth_method": "OAuth 1.0a",
            "connected": self.is_connected()
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get information about the NetSuite system"""
        return {
            "erp_type": self.erp_type,
            "erp_version": self.erp_version,
            "base_url": self.config.get('base_url', ''),
            "account_id": self.config.get('account_id', ''),
            "system_type": "NetSuite ERP",
            "available_apis": ["REST API", "SuiteQL", "RESTlets", "SuiteTalk"],
            "supported_records": ["Invoice", "Customer", "Vendor", "Item", "Subsidiary", "Currency"],
            "authentication": "OAuth 1.0a"
        }
    
    # NetSuite-specific methods
    def get_netsuite_url(self, api_type: str, endpoint: str) -> str:
        """Get NetSuite API URL for a specific type and endpoint"""
        return self.authenticator.get_api_url(api_type, endpoint)
    
    async def test_netsuite_api(self, endpoint: str) -> Dict[str, Any]:
        """Test a specific NetSuite API endpoint"""
        return await self.authenticator.test_api_access(endpoint)
    
    def get_supported_apis(self) -> List[str]:
        """Get list of supported NetSuite APIs"""
        return list(self.authenticator.api_paths.keys())