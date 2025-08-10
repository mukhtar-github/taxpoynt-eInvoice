"""
Salesforce CRM Connector - Main Module
Integrates all Salesforce connector components for TaxPoynt eInvoice System Integrator functions.

This module combines OAuth 2.0/JWT authentication, REST API communication, data extraction, 
and deal-to-invoice transformation into a unified connector interface compatible with the BaseCRMConnector.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from app.schemas.integration import IntegrationTestResult
from ....connector_framework import BaseCRMConnector
from .auth import SalesforceAuthenticator
from .rest_client import SalesforceRESTClient
from .data_extractor import SalesforceDataExtractor
from .deal_transformer import SalesforceDealTransformer
from .exceptions import SalesforceAPIError, SalesforceAuthenticationError, SalesforceConnectionError

logger = logging.getLogger(__name__)


class SalesforceCRMConnector(BaseCRMConnector):
    """
    Salesforce CRM Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for Salesforce integration,
    including OAuth 2.0/JWT authentication, REST API connectivity, and data extraction.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - Salesforce REST API connectivity and OAuth 2.0/JWT authentication
    - Deal/Opportunity data extraction and management
    - Connection health monitoring and error handling
    - Deal data transformation for invoice generation
    - SOQL query execution and data processing
    
    Supported Salesforce APIs:
    - REST API: Standard SObject operations
    - SOQL: Advanced querying and filtering
    - SOSL: Search across multiple objects
    - Bulk API: Large data operations (future)
    - Metadata API: Schema and customization access (future)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Salesforce connector with configuration.
        
        Args:
            config: Dictionary with Salesforce connection parameters
        """
        super().__init__(config)
        self.config = config
        
        # Initialize components
        self.authenticator = SalesforceAuthenticator(config)
        self.rest_client = SalesforceRESTClient(self.authenticator)
        self.data_extractor = SalesforceDataExtractor(self.rest_client)
        self.deal_transformer = SalesforceDealTransformer(self.data_extractor)
        
        logger.info(f"Initialized SalesforceCRMConnector for {config.get('instance_url', 'unknown')}")
    
    @property
    def crm_type(self) -> str:
        """Return the CRM system type"""
        return "salesforce"
    
    @property
    def crm_version(self) -> str:
        """Return the CRM system version"""
        api_version = self.config.get('api_version', 'v58.0')
        environment = self.config.get('environment', 'production')
        return f"Salesforce CRM API {api_version} ({environment})"
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features"""
        return [
            "rest_api",
            "oauth2_authentication",
            "jwt_bearer_authentication",
            "opportunities",
            "accounts",
            "contacts",
            "leads",
            "products",
            "campaigns",
            "deal_to_invoice_transformation",
            "soql_queries",
            "sosl_search",
            "real_time_sync",
            "connection_testing",
            "data_validation",
            "json_format",
            "search_functionality",
            "pagination_support",
            "multi_org_support",
            "sandbox_support",
            "custom_objects",
            "workflow_automation"
        ]
    
    # Connection and Authentication Methods
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to Salesforce CRM - SI Role Function.
        
        Validates connectivity and authentication for System Integrator
        CRM integration health monitoring.
        
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
            
            # Test limits API
            limits_result = await self.authenticator.test_api_access('limits')
            test_results['limits'] = limits_result.get('success', False)
            
            # Test accounts API
            accounts_result = await self.authenticator.test_api_access('accounts')
            test_results['accounts'] = accounts_result.get('success', False)
            
            # Test opportunities API
            opportunities_result = await self.authenticator.test_api_access('opportunities')
            test_results['opportunities'] = opportunities_result.get('success', False)
            
            # Test contacts API
            contacts_result = await self.authenticator.test_api_access('contacts')
            test_results['contacts'] = contacts_result.get('success', False)
            
            # Test SOQL query API
            query_result = await self.authenticator.test_api_access('query')
            test_results['query'] = query_result.get('success', False)
            
            # Overall success if at least one API is accessible
            overall_success = any(test_results.values())
            
            if overall_success:
                return IntegrationTestResult(
                    success=True,
                    message="Successfully connected to Salesforce CRM",
                    details={
                        "crm_type": self.crm_type,
                        "crm_version": self.crm_version,
                        "instance_url": self.config.get('instance_url'),
                        "client_id": self.config.get('client_id'),
                        "environment": self.config.get('environment'),
                        "api_version": self.config.get('api_version'),
                        "auth_method": "JWT Bearer" if self.config.get('private_key') else "Username-Password",
                        "limits_api_available": test_results.get('limits', False),
                        "accounts_api_available": test_results.get('accounts', False),
                        "opportunities_api_available": test_results.get('opportunities', False),
                        "contacts_api_available": test_results.get('contacts', False),
                        "query_api_available": test_results.get('query', False),
                        "supported_features": self.supported_features
                    }
                )
            else:
                return IntegrationTestResult(
                    success=False,
                    message="No Salesforce API endpoints are accessible",
                    error_code="API_ACCESS_ERROR",
                    details=test_results
                )
            
        except Exception as e:
            logger.error(f"Unexpected error during Salesforce connection test: {str(e)}")
            return IntegrationTestResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR"
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Salesforce CRM - SI Role Function.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            return await self.authenticator.authenticate()
        except Exception as e:
            logger.error(f"Salesforce authentication failed: {str(e)}")
            return False
    
    # Deal/Opportunity Management Methods
    async def get_deals(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        stage: Optional[str] = None,
        owner_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get deals/opportunities from Salesforce CRM"""
        return await self.data_extractor.get_deals(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            stage=stage,
            owner_id=owner_id,
            status=status
        )
    
    async def get_deal_by_id(self, deal_id: Union[int, str]) -> Dict[str, Any]:
        """Get a specific deal/opportunity by ID from Salesforce CRM"""
        return await self.data_extractor.get_deal_by_id(deal_id)
    
    async def search_deals(
        self,
        company_name: Optional[str] = None,
        contact_name: Optional[str] = None,
        deal_name: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        stage: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search deals/opportunities with specific criteria"""
        return await self.data_extractor.search_deals(
            company_name=company_name,
            contact_name=contact_name,
            deal_name=deal_name,
            amount_range=amount_range,
            date_range=date_range,
            stage=stage,
            limit=limit
        )
    
    # Customer/Contact Management Methods
    async def get_customers(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get customers/accounts from Salesforce CRM"""
        return await self.data_extractor.get_customers(
            search_term=search_term,
            limit=limit,
            offset=offset
        )
    
    async def get_contacts(
        self,
        search_term: Optional[str] = None,
        company_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get contacts from Salesforce CRM"""
        return await self.data_extractor.get_contacts(
            search_term=search_term,
            company_id=company_id,
            limit=limit,
            offset=offset
        )
    
    async def get_products(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get products from Salesforce CRM"""
        return await self.data_extractor.get_products(
            search_term=search_term,
            limit=limit,
            offset=offset
        )
    
    # Invoice Generation Methods
    async def validate_deal_data(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deal data before invoice generation"""
        return await self.deal_transformer.validate_deal_data(deal_data)
    
    async def transform_deal_to_invoice(
        self,
        deal_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform Salesforce deal data to invoice format"""
        return await self.deal_transformer.transform_deal_to_invoice(deal_data, target_format)
    
    async def update_deal_status(
        self,
        deal_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update deal status in Salesforce system"""
        return await self.deal_transformer.update_deal_status(deal_id, status_data)
    
    # Additional Salesforce-specific Methods
    async def execute_soql(self, query: str) -> Dict[str, Any]:
        """Execute a SOQL query"""
        return await self.rest_client.execute_soql(query)
    
    async def execute_sosl(self, search: str) -> Dict[str, Any]:
        """Execute a SOSL search"""
        return await self.rest_client.execute_sosl(search)
    
    async def get_leads(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get leads from Salesforce"""
        return await self.rest_client.get_leads(
            limit=limit,
            offset=offset,
            status=status,
            search_term=search_term
        )
    
    async def get_opportunity_line_items(self, opportunity_id: str) -> Dict[str, Any]:
        """Get line items for an opportunity"""
        return await self.rest_client.get_opportunity_line_items(opportunity_id)
    
    async def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new opportunity in Salesforce"""
        return await self.rest_client.create_sobject_record('Opportunity', opportunity_data)
    
    async def update_opportunity(self, opportunity_id: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing opportunity in Salesforce"""
        return await self.rest_client.update_sobject_record('Opportunity', opportunity_id, opportunity_data)
    
    async def get_sobject_describe(self, sobject_type: str) -> Dict[str, Any]:
        """Get metadata description for an SObject"""
        return await self.rest_client.get_sobject_describe(sobject_type)
    
    async def get_limits(self) -> Dict[str, Any]:
        """Get organization limits"""
        return await self.rest_client.get_limits()
    
    # Pipeline and Sales Management Methods
    async def get_pipeline_stages(self) -> List[Dict[str, Any]]:
        """Get pipeline stages from Salesforce"""
        try:
            # Query opportunity stages using SOQL
            query = """
                SELECT ApiName, MasterLabel, IsActive, SortOrder, IsWon, IsClosed
                FROM OpportunityStage
                WHERE IsActive = true
                ORDER BY SortOrder
            """
            
            response = await self.execute_soql(query)
            
            if response.get('success'):
                stages = []
                for stage_data in response.get('records', []):
                    stage = {
                        "api_name": stage_data.get('ApiName', ''),
                        "label": stage_data.get('MasterLabel', ''),
                        "is_active": stage_data.get('IsActive', False),
                        "sort_order": stage_data.get('SortOrder', 0),
                        "is_won": stage_data.get('IsWon', False),
                        "is_closed": stage_data.get('IsClosed', False),
                        "source": "salesforce_opportunity_stages"
                    }
                    stages.append(stage)
                return stages
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving Salesforce pipeline stages: {str(e)}")
            return []
    
    async def get_sales_forecast(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get sales forecast data from Salesforce"""
        try:
            # Build date filters
            date_filters = []
            if start_date:
                date_filters.append(f"CloseDate >= {start_date.strftime('%Y-%m-%d')}")
            if end_date:
                date_filters.append(f"CloseDate <= {end_date.strftime('%Y-%m-%d')}")
            
            where_clause = " AND ".join(date_filters) if date_filters else "CloseDate >= TODAY"
            
            # Query opportunities for forecast
            query = f"""
                SELECT COUNT(Id) total_deals, SUM(Amount) total_amount, AVG(Amount) avg_amount, AVG(Probability) avg_probability
                FROM Opportunity
                WHERE {where_clause} AND IsClosed = false
            """
            
            response = await self.execute_soql(query)
            
            if response.get('success') and response.get('records'):
                record = response['records'][0]
                return {
                    'forecast_period': f"{start_date} to {end_date}" if start_date and end_date else "Open pipeline",
                    'total_forecasted_revenue': float(record.get('total_amount', 0) or 0),
                    'deals_in_pipeline': int(record.get('total_deals', 0) or 0),
                    'average_deal_size': float(record.get('avg_amount', 0) or 0),
                    'average_probability': float(record.get('avg_probability', 0) or 0),
                    'conversion_rate': float(record.get('avg_probability', 0) or 0) / 100,
                    'source': 'salesforce_forecast'
                }
            else:
                return super().get_sales_forecast(start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error retrieving Salesforce sales forecast: {str(e)}")
            return super().get_sales_forecast(start_date, end_date)
    
    # Connection Management
    async def disconnect(self) -> bool:
        """
        Disconnect from Salesforce CRM - SI Role Function.
        
        Properly closes the connection to Salesforce for System Integrator
        resource management and cleanup.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            return await self.authenticator.disconnect()
        except Exception as e:
            logger.error(f"Error during Salesforce disconnect: {str(e)}")
            return False
    
    # Utility Methods
    def is_connected(self) -> bool:
        """Check if connected to Salesforce"""
        return self.authenticator.is_authenticated()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        connection_info = self.authenticator.get_connection_info()
        connection_info.update({
            "crm_type": self.crm_type,
            "crm_version": self.crm_version,
            "last_activity": datetime.now().isoformat()
        })
        return connection_info
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user"""
        return {
            "instance_url": self.config.get('instance_url', ''),
            "client_id": self.config.get('client_id', ''),
            "username": self.config.get('username', ''),
            "environment": self.config.get('environment', ''),
            "api_version": self.config.get('api_version', ''),
            "auth_method": "JWT Bearer" if self.config.get('private_key') else "Username-Password",
            "connected": self.is_connected()
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get information about the Salesforce system"""
        return {
            "crm_type": self.crm_type,
            "crm_version": self.crm_version,
            "instance_url": self.config.get('instance_url', ''),
            "environment": self.config.get('environment', ''),
            "api_version": self.config.get('api_version', ''),
            "system_type": "Salesforce CRM",
            "available_apis": ["REST API", "SOQL", "SOSL", "Bulk API", "Metadata API"],
            "supported_objects": ["Opportunity", "Account", "Contact", "Lead", "Product2", "Campaign"],
            "authentication": "OAuth 2.0 / JWT Bearer"
        }
    
    # Salesforce-specific methods
    def get_salesforce_url(self, endpoint: str) -> str:
        """Get Salesforce API URL for a specific endpoint"""
        return self.authenticator.get_api_url(endpoint)
    
    async def test_salesforce_api(self, endpoint: str) -> Dict[str, Any]:
        """Test a specific Salesforce API endpoint"""
        return await self.authenticator.test_api_access(endpoint)
    
    def get_supported_sobjects(self) -> List[str]:
        """Get list of supported Salesforce SObjects"""
        return [
            'Account', 'Contact', 'Opportunity', 'Lead', 'Product2', 
            'Campaign', 'Case', 'Task', 'Event', 'User', 'OpportunityLineItem'
        ]