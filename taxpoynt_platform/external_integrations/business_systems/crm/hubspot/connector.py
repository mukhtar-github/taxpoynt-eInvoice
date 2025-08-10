"""
HubSpot CRM Connector - Main Module
Integrates all HubSpot connector components for TaxPoynt eInvoice System Integrator functions.

This module combines OAuth 2.0 authentication, REST API communication, data extraction, 
and deal-to-invoice transformation into a unified connector interface compatible with the BaseCRMConnector.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# from app.schemas.integration import IntegrationTestResult  # TODO: Replace with taxpoynt_platform schema
from ....connector_framework import BaseCRMConnector
from .auth import HubSpotAuthenticator
from .rest_client import HubSpotRESTClient
from .data_extractor import HubSpotDataExtractor
from .deal_transformer import HubSpotDealTransformer
from .exceptions import HubSpotAPIError, HubSpotAuthenticationError, HubSpotConnectionError

logger = logging.getLogger(__name__)


class HubSpotCRMConnector(BaseCRMConnector):
    """
    HubSpot CRM Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for HubSpot integration,
    including OAuth 2.0 authentication, REST API connectivity, and data extraction.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - HubSpot REST API connectivity and OAuth 2.0 authentication
    - Deal data extraction and management
    - Connection health monitoring and error handling
    - Deal data transformation for invoice generation
    - Pipeline and stage management
    
    Supported HubSpot APIs:
    - CRM API v3: Objects, Properties, Associations
    - Search API: Advanced filtering and searching
    - Pipelines API: Deal pipeline and stage management
    - Webhooks API: Real-time event notifications (future)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the HubSpot connector with configuration.
        
        Args:
            config: Dictionary with HubSpot connection parameters
        """
        super().__init__(config)
        self.config = config
        
        # Initialize components
        self.authenticator = HubSpotAuthenticator(config)
        self.rest_client = HubSpotRESTClient(self.authenticator)
        self.data_extractor = HubSpotDataExtractor(self.rest_client)
        self.deal_transformer = HubSpotDealTransformer(self.data_extractor)
        
        logger.info(f"Initialized HubSpotCRMConnector for {config.get('client_id', 'unknown')}")
    
    @property
    def crm_type(self) -> str:
        """Return the CRM system type"""
        return "hubspot"
    
    @property
    def crm_version(self) -> str:
        """Return the CRM system version"""
        api_version = self.config.get('api_version', 'v3')
        return f"HubSpot CRM API {api_version}"
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features"""
        return [
            "rest_api",
            "oauth2_authentication",
            "api_key_authentication",
            "private_app_authentication",
            "deals",
            "companies",
            "contacts",
            "products",
            "line_items",
            "pipelines",
            "deal_stages",
            "deal_to_invoice_transformation",
            "search_functionality",
            "associations",
            "real_time_sync",
            "connection_testing",
            "data_validation",
            "json_format",
            "pagination_support",
            "webhook_support",
            "custom_properties",
            "workflow_automation"
        ]
    
    # Connection and Authentication Methods
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to HubSpot CRM - SI Role Function.
        
        Validates connectivity and authentication for System Integrator
        CRM integration health monitoring.
        
        Returns:
            Dict with connection status and details
        """
        try:
            # Test authentication
            auth_result = await self.authenticator.test_authentication()
            if not auth_result.get('success'):
                return {
                    'success': False,
                    'message': f"Authentication failed: {auth_result.get('error')}",
                    'error_code': "AUTHENTICATION_ERROR"
                }
            
            # Test API access for different endpoints
            test_results = {}
            
            # Test contacts API
            contacts_result = await self.authenticator.test_api_access('contacts')
            test_results['contacts'] = contacts_result.get('success', False)
            
            # Test companies API
            companies_result = await self.authenticator.test_api_access('companies')
            test_results['companies'] = companies_result.get('success', False)
            
            # Test deals API
            deals_result = await self.authenticator.test_api_access('deals')
            test_results['deals'] = deals_result.get('success', False)
            
            # Test products API
            products_result = await self.authenticator.test_api_access('products')
            test_results['products'] = products_result.get('success', False)
            
            # Test pipelines API
            pipelines_result = await self.authenticator.test_api_access('pipelines')
            test_results['pipelines'] = pipelines_result.get('success', False)
            
            # Overall success if at least one API is accessible
            overall_success = any(test_results.values())
            
            if overall_success:
                return {
                    'success': True,
                    'message': "Successfully connected to HubSpot CRM",
                    'details': {
                        "crm_type": self.crm_type,
                        "crm_version": self.crm_version,
                        "base_url": self.authenticator.base_url,
                        "client_id": self.config.get('client_id'),
                        "api_version": self.config.get('api_version'),
                        "auth_method": "OAuth 2.0" if self.config.get('access_token') else "API Key",
                        "contacts_api_available": test_results.get('contacts', False),
                        "companies_api_available": test_results.get('companies', False),
                        "deals_api_available": test_results.get('deals', False),
                        "products_api_available": test_results.get('products', False),
                        "pipelines_api_available": test_results.get('pipelines', False),
                        "supported_features": self.supported_features
                    }
                }
            else:
                return {
                    'success': False,
                    'message': "No HubSpot API endpoints are accessible",
                    'error_code': "API_ACCESS_ERROR",
                    'details': test_results
                }
            
        except Exception as e:
            logger.error(f"Unexpected error during HubSpot connection test: {str(e)}")
            return {
                'success': False,
                'message': f"Unexpected error: {str(e)}",
                'error_code': "UNKNOWN_ERROR"
            }
    
    async def authenticate(self) -> bool:
        """
        Authenticate with HubSpot CRM - SI Role Function.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            return await self.authenticator.authenticate()
        except Exception as e:
            logger.error(f"HubSpot authentication failed: {str(e)}")
            return False
    
    # Deal Management Methods
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
        """Get deals from HubSpot CRM"""
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
        """Get a specific deal by ID from HubSpot CRM"""
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
        """Search deals with specific criteria"""
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
        """Get customers/companies from HubSpot CRM"""
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
        """Get contacts from HubSpot CRM"""
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
        """Get products from HubSpot CRM"""
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
        """Transform HubSpot deal data to invoice format"""
        return await self.deal_transformer.transform_deal_to_invoice(deal_data, target_format)
    
    async def update_deal_status(
        self,
        deal_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update deal status in HubSpot system"""
        return await self.deal_transformer.update_deal_status(deal_id, status_data)
    
    # Additional HubSpot-specific Methods
    async def get_line_items(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get line items from HubSpot"""
        after = str(offset) if offset > 0 else None
        return await self.rest_client.get_line_items(limit=limit, after=after)
    
    async def get_deal_line_items(self, deal_id: str) -> Dict[str, Any]:
        """Get line items associated with a specific deal"""
        return await self.rest_client.get_deal_line_items(deal_id)
    
    async def create_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deal in HubSpot"""
        return await self.rest_client.create_crm_object('deals', deal_data)
    
    async def update_deal(self, deal_id: str, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing deal in HubSpot"""
        return await self.rest_client.update_crm_object('deals', deal_id, deal_data)
    
    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company in HubSpot"""
        return await self.rest_client.create_crm_object('companies', company_data)
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact in HubSpot"""
        return await self.rest_client.create_crm_object('contacts', contact_data)
    
    async def search_crm_objects(
        self,
        object_type: str,
        filters: List[Dict[str, Any]],
        properties: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search CRM objects with filters"""
        return await self.rest_client.search_crm_objects(
            object_type=object_type,
            filters=filters,
            properties=properties,
            limit=limit
        )
    
    # Pipeline and Sales Management Methods
    async def get_pipeline_stages(self) -> List[Dict[str, Any]]:
        """Get pipeline stages from HubSpot"""
        try:
            response = await self.rest_client.get_deal_stages()
            
            if response.get('success'):
                stages_data = response.get('data', {})
                stages = stages_data.get('results', [])
                
                formatted_stages = []
                for stage in stages:
                    formatted_stage = {
                        "id": stage.get('id', ''),
                        "label": stage.get('label', ''),
                        "display_order": stage.get('displayOrder', 0),
                        "probability": stage.get('metadata', {}).get('probability', 0),
                        "closed_won": stage.get('metadata', {}).get('isClosed', False) and stage.get('metadata', {}).get('isWon', False),
                        "pipeline_id": stage.get('pipeline_id', ''),
                        "pipeline_label": stage.get('pipeline_label', ''),
                        "source": "hubspot_deal_stages"
                    }
                    formatted_stages.append(formatted_stage)
                
                return formatted_stages
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving HubSpot pipeline stages: {str(e)}")
            return []
    
    async def get_sales_forecast(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get sales forecast data from HubSpot"""
        try:
            # Build search filters for forecast
            filters = []
            
            if start_date:
                filters.append({
                    'propertyName': 'closedate',
                    'operator': 'GTE',
                    'value': int(start_date.timestamp() * 1000)
                })
            
            if end_date:
                filters.append({
                    'propertyName': 'closedate',
                    'operator': 'LTE',
                    'value': int(end_date.timestamp() * 1000)
                })
            
            # Add filter for open deals
            filters.append({
                'propertyName': 'dealstage',
                'operator': 'NEQ',
                'value': 'closedwon'
            })
            filters.append({
                'propertyName': 'dealstage',
                'operator': 'NEQ',
                'value': 'closedlost'
            })
            
            response = await self.rest_client.search_crm_objects(
                'deals',
                filters=filters,
                properties=['amount', 'hs_deal_stage_probability'],
                limit=1000  # Get more deals for forecast calculation
            )
            
            if response.get('success'):
                deals = response.get('results', [])
                
                total_deals = len(deals)
                total_amount = 0
                total_weighted_amount = 0
                
                for deal in deals:
                    properties = deal.get('properties', {})
                    amount = float(properties.get('amount', 0)) if properties.get('amount') else 0
                    probability = float(properties.get('hs_deal_stage_probability', 0)) if properties.get('hs_deal_stage_probability') else 0
                    
                    total_amount += amount
                    total_weighted_amount += amount * (probability / 100)
                
                avg_deal_size = total_amount / total_deals if total_deals > 0 else 0
                avg_probability = sum(float(deal.get('properties', {}).get('hs_deal_stage_probability', 0)) for deal in deals) / total_deals if total_deals > 0 else 0
                
                return {
                    'forecast_period': f"{start_date} to {end_date}" if start_date and end_date else "Open pipeline",
                    'total_forecasted_revenue': total_weighted_amount,
                    'total_pipeline_value': total_amount,
                    'deals_in_pipeline': total_deals,
                    'average_deal_size': avg_deal_size,
                    'average_probability': avg_probability,
                    'conversion_rate': avg_probability / 100,
                    'source': 'hubspot_forecast'
                }
            else:
                return super().get_sales_forecast(start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error retrieving HubSpot sales forecast: {str(e)}")
            return super().get_sales_forecast(start_date, end_date)
    
    async def get_deal_pipelines(self) -> Dict[str, Any]:
        """Get deal pipelines from HubSpot"""
        return await self.rest_client.get_deal_pipelines()
    
    # Connection Management
    async def disconnect(self) -> bool:
        """
        Disconnect from HubSpot CRM - SI Role Function.
        
        Properly closes the connection to HubSpot for System Integrator
        resource management and cleanup.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            return await self.authenticator.disconnect()
        except Exception as e:
            logger.error(f"Error during HubSpot disconnect: {str(e)}")
            return False
    
    # Utility Methods
    def is_connected(self) -> bool:
        """Check if connected to HubSpot"""
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
            "base_url": self.authenticator.base_url,
            "client_id": self.config.get('client_id', ''),
            "api_version": self.config.get('api_version', ''),
            "auth_method": "OAuth 2.0" if self.config.get('access_token') else "API Key",
            "has_refresh_token": bool(self.config.get('refresh_token')),
            "connected": self.is_connected()
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get information about the HubSpot system"""
        return {
            "crm_type": self.crm_type,
            "crm_version": self.crm_version,
            "base_url": self.authenticator.base_url,
            "api_version": self.config.get('api_version', ''),
            "system_type": "HubSpot CRM",
            "available_apis": ["CRM API v3", "Search API", "Pipelines API", "Webhooks API"],
            "supported_objects": ["Deal", "Company", "Contact", "Product", "Line Item", "Ticket"],
            "authentication": "OAuth 2.0 / API Key / Private App"
        }
    
    # HubSpot-specific methods
    def get_hubspot_url(self, endpoint_type: str, object_type: str = '') -> str:
        """Get HubSpot API URL for a specific endpoint type and object"""
        return self.authenticator.get_api_url(endpoint_type, object_type)
    
    async def test_hubspot_api(self, endpoint: str) -> Dict[str, Any]:
        """Test a specific HubSpot API endpoint"""
        return await self.authenticator.test_api_access(endpoint)
    
    def get_supported_objects(self) -> List[str]:
        """Get list of supported HubSpot objects"""
        return [
            'contacts', 'companies', 'deals', 'products', 'line_items',
            'tickets', 'tasks', 'meetings', 'calls', 'emails', 'notes'
        ]