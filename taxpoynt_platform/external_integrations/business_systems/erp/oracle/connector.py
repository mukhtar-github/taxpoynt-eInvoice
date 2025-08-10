"""
Oracle ERP Cloud Connector - Main Module
Integrates all Oracle connector components for TaxPoynt eInvoice System Integrator functions.

This module combines OAuth 2.0 authentication, REST API communication, data extraction, 
and FIRS transformation into a unified connector interface compatible with the BaseERPConnector.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from app.schemas.integration import IntegrationTestResult
from ....connector_framework import BaseERPConnector
from .auth import OracleAuthenticator
from .rest_client import OracleRESTClient
from .data_extractor import OracleDataExtractor
from .firs_transformer import OracleFIRSTransformer
from .exceptions import OracleAPIError, OracleAuthenticationError, OracleConnectionError

logger = logging.getLogger(__name__)


class OracleERPConnector(BaseERPConnector):
    """
    Oracle ERP Cloud Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for Oracle ERP Cloud integration,
    including OAuth 2.0 authentication, REST API connectivity, and data extraction.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - Oracle ERP Cloud REST API connectivity and OAuth 2.0 authentication
    - Data extraction from Oracle FSCM and CRM modules
    - Connection health monitoring and error handling
    - Invoice data transformation for FIRS compliance
    - FIRS UBL format transformation
    
    Supported Oracle Modules:
    - Financial Supply Chain Management (FSCM): Invoices, Receivables, ERP Integrations
    - Customer Relationship Management (CRM): Accounts
    - Future: Human Capital Management (HCM), Project Portfolio Management (PPM)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Oracle ERP Cloud connector with configuration.
        
        Args:
            config: Dictionary with Oracle connection parameters
        """
        super().__init__(config)
        self.config = config
        
        # Initialize components
        self.authenticator = OracleAuthenticator(config)
        self.rest_client = OracleRESTClient(self.authenticator)
        self.data_extractor = OracleDataExtractor(self.rest_client)
        self.firs_transformer = OracleFIRSTransformer(self.data_extractor)
        
        logger.info(f"Initialized OracleERPConnector for {config.get('base_url', 'unknown')}")
    
    @property
    def erp_type(self) -> str:
        """Return the ERP system type"""
        return "oracle"
    
    @property
    def erp_version(self) -> str:
        """Return the ERP system version"""
        # Oracle Cloud version detection would require metadata analysis
        return "Oracle Cloud ERP"  # Default assumption
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features"""
        return [
            "rest_api",
            "oauth2_authentication",
            "ap_invoices",
            "ar_receivables",
            "customer_accounts",
            "erp_integrations",
            "firs_transformation",
            "ubl_format",
            "real_time_sync",
            "connection_testing",
            "data_validation",
            "json_format",
            "metadata_access",
            "search_functionality",
            "pagination_support",
            "fscm_module",
            "crm_module"
        ]
    
    # Connection and Authentication Methods
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to Oracle ERP Cloud - SI Role Function.
        
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
            
            # Test API access for different modules
            test_results = {}
            
            # Test invoices API (FSCM)
            invoices_result = await self.authenticator.test_api_access('invoices')
            test_results['invoices'] = invoices_result.get('success', False)
            
            # Test accounts API (CRM)
            accounts_result = await self.authenticator.test_api_access('accounts')
            test_results['accounts'] = accounts_result.get('success', False)
            
            # Test receivables API (FSCM)
            receivables_result = await self.authenticator.test_api_access('receivables')
            test_results['receivables'] = receivables_result.get('success', False)
            
            # Test ERP integrations API (FSCM)
            integrations_result = await self.authenticator.test_api_access('erpintegrations')
            test_results['erp_integrations'] = integrations_result.get('success', False)
            
            # Overall success if at least one API is accessible
            overall_success = any(test_results.values())
            
            if overall_success:
                return IntegrationTestResult(
                    success=True,
                    message="Successfully connected to Oracle ERP Cloud",
                    details={
                        "erp_type": self.erp_type,
                        "erp_version": self.erp_version,
                        "base_url": self.config.get('base_url'),
                        "auth_method": "OAuth 2.0",
                        "client_id": self.config.get('client_id'),
                        "invoices_api_available": test_results.get('invoices', False),
                        "accounts_api_available": test_results.get('accounts', False),
                        "receivables_api_available": test_results.get('receivables', False),
                        "erp_integrations_api_available": test_results.get('erp_integrations', False),
                        "supported_features": self.supported_features
                    }
                )
            else:
                return IntegrationTestResult(
                    success=False,
                    message="No Oracle API endpoints are accessible",
                    error_code="API_ACCESS_ERROR",
                    details=test_results
                )
            
        except Exception as e:
            logger.error(f"Unexpected error during Oracle connection test: {str(e)}")
            return IntegrationTestResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Oracle ERP Cloud - SI Role Function.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            return await self.authenticator.authenticate()
        except Exception as e:
            logger.error(f"Oracle authentication failed: {str(e)}")
            return False
    
    # Data Extraction Methods
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        supplier_number: Optional[str] = None,
        invoice_status: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'ap_invoices'
    ) -> List[Dict[str, Any]]:
        """Get invoice list from Oracle ERP Cloud"""
        return await self.data_extractor.get_invoices(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            supplier_number=supplier_number,
            invoice_status=invoice_status,
            include_attachments=include_attachments,
            data_source=data_source
        )
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """Get a specific invoice by ID from Oracle ERP Cloud"""
        return await self.data_extractor.get_invoice_by_id(invoice_id)
    
    async def search_invoices(
        self,
        supplier_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search invoices with specific criteria"""
        return await self.data_extractor.search_invoices(
            supplier_name=supplier_name,
            invoice_number=invoice_number,
            amount_range=amount_range,
            date_range=date_range,
            status=status,
            limit=limit
        )
    
    async def get_accounts(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get customer accounts from Oracle CRM"""
        return await self.data_extractor.get_accounts(
            search_term=search_term,
            limit=limit,
            offset=offset
        )
    
    async def get_erp_integrations(
        self,
        integration_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get ERP integrations from Oracle FSCM"""
        return await self.data_extractor.get_erp_integrations(
            integration_name=integration_name,
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
        """Transform Oracle invoice data to FIRS-compliant format"""
        return await self.firs_transformer.transform_to_firs_format(invoice_data, target_format)
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in Oracle system"""
        return await self.firs_transformer.update_invoice_status(invoice_id, status_data)
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from Oracle"""
        return await self.firs_transformer.get_tax_configuration()
    
    # Additional Oracle-specific Methods
    async def get_ap_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get Accounts Payable invoices directly from Oracle FSCM API"""
        return await self.rest_client.get_invoices(limit, offset, filters)
    
    async def get_ar_receivables(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get Accounts Receivable transactions directly from Oracle FSCM API"""
        return await self.rest_client.get_receivables(limit, offset, filters)
    
    async def get_customer_accounts(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get customer accounts directly from Oracle CRM API"""
        return await self.rest_client.get_accounts(limit, offset, search_term)
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice in Oracle"""
        return await self.rest_client.create_invoice(invoice_data)
    
    async def update_oracle_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing invoice in Oracle"""
        return await self.rest_client.update_invoice(invoice_id, invoice_data)
    
    async def get_metadata(self, module: str, entity: str) -> Dict[str, Any]:
        """Get metadata for a specific Oracle entity"""
        return await self.rest_client.get_metadata(module, entity)
    
    # Connection Management
    async def disconnect(self) -> bool:
        """
        Disconnect from Oracle ERP Cloud - SI Role Function.
        
        Properly closes the connection to Oracle ERP Cloud for System Integrator
        resource management and cleanup.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            return await self.authenticator.disconnect()
        except Exception as e:
            logger.error(f"Error during Oracle disconnect: {str(e)}")
            return False
    
    # Utility Methods
    def is_connected(self) -> bool:
        """Check if connected to Oracle"""
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
    async def get_customers(self, limit: int = 100, offset: int = 0, search_term: str = None) -> List[Dict[str, Any]]:
        """Legacy method - maps to get_accounts for Oracle"""
        accounts = await self.get_accounts(search_term=search_term, limit=limit, offset=offset)
        # Convert accounts to customer format
        customers = []
        for account in accounts:
            customer = {
                "id": account.get('customer_account_id', account.get('id', '')),
                "name": account.get('account_name', account.get('name', '')),
                "party_number": account.get('party_number', ''),
                "customer_type": account.get('customer_type', ''),
                "oracle_party_id": account.get('id', ''),
                "oracle_account_number": account.get('account_number', ''),
                "source": "oracle_crm"
            }
            customers.append(customer)
        return customers
    
    async def get_products(self, limit: int = 100, offset: int = 0, search_term: str = None) -> List[Dict[str, Any]]:
        """Legacy method - Oracle product master data would require separate implementation"""
        logger.warning("Product data extraction not yet implemented for Oracle connector")
        return []
    
    async def get_partners(self, search_term: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get business partners from Oracle - maps to accounts"""
        return await self.get_accounts(search_term=search_term, limit=limit)
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user"""
        return {
            "username": self.config.get('username', ''),
            "client_id": self.config.get('client_id', ''),
            "auth_method": "OAuth 2.0",
            "connected": self.is_connected()
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get information about the Oracle system"""
        return {
            "erp_type": self.erp_type,
            "erp_version": self.erp_version,
            "base_url": self.config.get('base_url', ''),
            "system_type": "Oracle Cloud ERP",
            "available_modules": ["FSCM", "CRM", "HCM", "PPM"],
            "supported_apis": ["REST"],
            "authentication": "OAuth 2.0"
        }
    
    # Oracle Cloud specific methods
    def get_oracle_url(self, module: str, endpoint: str) -> str:
        """Get Oracle API URL for a specific module and endpoint"""
        return self.authenticator.get_api_url(module, endpoint)
    
    async def test_oracle_api(self, endpoint: str) -> Dict[str, Any]:
        """Test a specific Oracle API endpoint"""
        return await self.authenticator.test_api_access(endpoint)
    
    def get_supported_modules(self) -> List[str]:
        """Get list of supported Oracle modules"""
        return list(self.authenticator.api_paths.keys())