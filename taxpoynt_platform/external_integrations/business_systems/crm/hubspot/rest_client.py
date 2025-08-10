"""
HubSpot REST Client Module
Handles REST API communication for HubSpot CRM services.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

from .exceptions import HubSpotAPIError, HubSpotConnectionError, HubSpotRateLimitError

logger = logging.getLogger(__name__)


class HubSpotRESTClient:
    """Handles REST API communication with HubSpot CRM services."""
    
    def __init__(self, authenticator):
        """Initialize with a HubSpot authenticator instance."""
        self.authenticator = authenticator
    
    async def make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a REST API request to HubSpot.
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            Response data from HubSpot REST API
        """
        try:
            # Ensure valid authentication
            if not await self.authenticator.ensure_valid_token():
                raise HubSpotConnectionError("Authentication failed")
            
            if not self.authenticator.session:
                self.authenticator.session = await self.authenticator._create_session()
            
            # Build URL
            if endpoint.startswith('http'):
                url = endpoint
            else:
                url = urljoin(self.authenticator.base_url, endpoint)
            
            # Prepare headers
            request_headers = await self.authenticator._get_auth_headers()
            if headers:
                request_headers.update(headers)
            
            # Prepare parameters
            if params is None:
                params = {}
            
            # Add auth params for API key authentication
            auth_params = self.authenticator.get_auth_params()
            params.update(auth_params)
            
            # Make request
            async with self.authenticator.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers
            ) as response:
                return await self._handle_response(response)
                
        except Exception as e:
            logger.error(f"HubSpot REST request failed: {str(e)}")
            raise HubSpotAPIError(f"HubSpot REST request failed: {str(e)}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle HubSpot REST API response and error cases."""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'data': data,
                    'results': data.get('results', []),
                    'total': data.get('total', 0),
                    'paging': data.get('paging', {}),
                    'after': data.get('paging', {}).get('next', {}).get('after'),
                    'has_more': bool(data.get('paging', {}).get('next'))
                }
            
            elif response.status == 201:  # Created
                data = await response.json()
                return {
                    'success': True,
                    'data': data,
                    'created': True,
                    'id': data.get('id')
                }
            
            elif response.status == 204:  # No Content
                return {
                    'success': True,
                    'data': None,
                    'message': 'Operation completed successfully'
                }
            
            elif response.status == 400:
                error_data = await response.json()
                return {
                    'success': False,
                    'error': 'Bad request - invalid parameters',
                    'status_code': 400,
                    'details': error_data
                }
            
            elif response.status == 401:
                error_data = await response.json()
                # Try to refresh token and retry once
                if await self.authenticator.ensure_valid_token():
                    raise HubSpotConnectionError("Token refreshed, retry needed")
                else:
                    return {
                        'success': False,
                        'error': 'Authentication failed',
                        'status_code': 401,
                        'details': error_data
                    }
            
            elif response.status == 403:
                error_data = await response.json()
                return {
                    'success': False,
                    'error': 'Access forbidden - insufficient permissions',
                    'status_code': 403,
                    'details': error_data
                }
            
            elif response.status == 404:
                error_data = await response.json()
                return {
                    'success': False,
                    'error': 'Resource not found',
                    'status_code': 404,
                    'details': error_data
                }
            
            elif response.status == 429:  # Rate limited
                error_data = await response.json()
                retry_after = response.headers.get('Retry-After', '60')
                raise HubSpotRateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
            
            else:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': f'Request failed with status {response.status}',
                    'status_code': response.status,
                    'details': error_text
                }
                
        except Exception as e:
            logger.error(f"Error handling HubSpot response: {str(e)}")
            return {
                'success': False,
                'error': f'Response handling error: {str(e)}'
            }
    
    # CRM Object Methods
    async def get_crm_objects(
        self,
        object_type: str,
        properties: Optional[List[str]] = None,
        limit: int = 100,
        after: Optional[str] = None,
        associations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get CRM objects from HubSpot."""
        try:
            endpoint = self.authenticator.get_crm_object_url(object_type)
            
            params = {
                'limit': limit
            }
            
            if properties:
                params['properties'] = ','.join(properties)
            
            if after:
                params['after'] = after
            
            if associations:
                params['associations'] = ','.join(associations)
            
            response = await self.make_request(endpoint, params=params)
            
            if not response.get('success'):
                raise HubSpotAPIError(f"Failed to retrieve {object_type}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot {object_type}: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot {object_type}: {str(e)}")
    
    async def get_crm_object_by_id(
        self,
        object_type: str,
        object_id: str,
        properties: Optional[List[str]] = None,
        associations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get a specific CRM object by ID."""
        try:
            endpoint = self.authenticator.get_crm_object_url(object_type, object_id)
            
            params = {}
            
            if properties:
                params['properties'] = ','.join(properties)
            
            if associations:
                params['associations'] = ','.join(associations)
            
            response = await self.make_request(endpoint, params=params)
            
            if not response.get('success'):
                raise HubSpotAPIError(f"Failed to retrieve {object_type} {object_id}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot {object_type} {object_id}: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot {object_type} {object_id}: {str(e)}")
    
    async def create_crm_object(self, object_type: str, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new CRM object."""
        try:
            endpoint = self.authenticator.get_crm_object_url(object_type)
            
            response = await self.make_request(endpoint, method='POST', data=object_data)
            
            if not response.get('success'):
                raise HubSpotAPIError(f"Failed to create {object_type}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating HubSpot {object_type}: {str(e)}")
            raise HubSpotAPIError(f"Error creating HubSpot {object_type}: {str(e)}")
    
    async def update_crm_object(self, object_type: str, object_id: str, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing CRM object."""
        try:
            endpoint = self.authenticator.get_crm_object_url(object_type, object_id)
            
            response = await self.make_request(endpoint, method='PATCH', data=object_data)
            
            if not response.get('success'):
                raise HubSpotAPIError(f"Failed to update {object_type} {object_id}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating HubSpot {object_type} {object_id}: {str(e)}")
            raise HubSpotAPIError(f"Error updating HubSpot {object_type} {object_id}: {str(e)}")
    
    async def delete_crm_object(self, object_type: str, object_id: str) -> Dict[str, Any]:
        """Delete a CRM object."""
        try:
            endpoint = self.authenticator.get_crm_object_url(object_type, object_id)
            
            response = await self.make_request(endpoint, method='DELETE')
            
            if not response.get('success'):
                raise HubSpotAPIError(f"Failed to delete {object_type} {object_id}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting HubSpot {object_type} {object_id}: {str(e)}")
            raise HubSpotAPIError(f"Error deleting HubSpot {object_type} {object_id}: {str(e)}")
    
    # Search Methods
    async def search_crm_objects(
        self,
        object_type: str,
        filters: List[Dict[str, Any]],
        properties: Optional[List[str]] = None,
        limit: int = 100,
        after: Optional[str] = None,
        sorts: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Search CRM objects with filters."""
        try:
            endpoint = self.authenticator.get_crm_object_url(object_type, action='search')
            
            search_data = {
                'filterGroups': [{'filters': filters}],
                'limit': limit
            }
            
            if properties:
                search_data['properties'] = properties
            
            if after:
                search_data['after'] = after
            
            if sorts:
                search_data['sorts'] = sorts
            
            response = await self.make_request(endpoint, method='POST', data=search_data)
            
            if not response.get('success'):
                raise HubSpotAPIError(f"Failed to search {object_type}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error searching HubSpot {object_type}: {str(e)}")
            raise HubSpotAPIError(f"Error searching HubSpot {object_type}: {str(e)}")
    
    # Specific CRM Object Methods
    async def get_deals(
        self,
        properties: Optional[List[str]] = None,
        limit: int = 100,
        after: Optional[str] = None,
        associations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get deals from HubSpot."""
        try:
            default_properties = [
                'dealname', 'amount', 'closedate', 'dealstage', 'pipeline',
                'dealtype', 'description', 'createdate', 'hs_lastmodifieddate',
                'hubspot_owner_id', 'hs_deal_stage_probability'
            ]
            
            deal_properties = properties or default_properties
            deal_associations = associations or ['companies', 'contacts']
            
            return await self.get_crm_objects(
                'deals',
                properties=deal_properties,
                limit=limit,
                after=after,
                associations=deal_associations
            )
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot deals: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot deals: {str(e)}")
    
    async def get_companies(
        self,
        properties: Optional[List[str]] = None,
        limit: int = 100,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get companies from HubSpot."""
        try:
            default_properties = [
                'name', 'domain', 'industry', 'phone', 'address', 'city',
                'state', 'zip', 'country', 'website', 'description',
                'createdate', 'hs_lastmodifieddate', 'hubspot_owner_id'
            ]
            
            company_properties = properties or default_properties
            
            return await self.get_crm_objects(
                'companies',
                properties=company_properties,
                limit=limit,
                after=after
            )
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot companies: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot companies: {str(e)}")
    
    async def get_contacts(
        self,
        properties: Optional[List[str]] = None,
        limit: int = 100,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get contacts from HubSpot."""
        try:
            default_properties = [
                'firstname', 'lastname', 'email', 'phone', 'company',
                'jobtitle', 'address', 'city', 'state', 'zip', 'country',
                'createdate', 'lastmodifieddate', 'hubspot_owner_id'
            ]
            
            contact_properties = properties or default_properties
            
            return await self.get_crm_objects(
                'contacts',
                properties=contact_properties,
                limit=limit,
                after=after,
                associations=['companies']
            )
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot contacts: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot contacts: {str(e)}")
    
    async def get_products(
        self,
        properties: Optional[List[str]] = None,
        limit: int = 100,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products from HubSpot."""
        try:
            default_properties = [
                'name', 'description', 'price', 'hs_sku', 'hs_cost_of_goods_sold',
                'hs_product_type', 'createdate', 'hs_lastmodifieddate'
            ]
            
            product_properties = properties or default_properties
            
            return await self.get_crm_objects(
                'products',
                properties=product_properties,
                limit=limit,
                after=after
            )
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot products: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot products: {str(e)}")
    
    async def get_line_items(
        self,
        properties: Optional[List[str]] = None,
        limit: int = 100,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get line items from HubSpot."""
        try:
            default_properties = [
                'name', 'price', 'quantity', 'amount', 'hs_product_id',
                'createdate', 'hs_lastmodifieddate'
            ]
            
            line_item_properties = properties or default_properties
            
            return await self.get_crm_objects(
                'line_items',
                properties=line_item_properties,
                limit=limit,
                after=after,
                associations=['deals', 'products']
            )
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot line items: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot line items: {str(e)}")
    
    async def get_deal_line_items(self, deal_id: str) -> Dict[str, Any]:
        """Get line items associated with a specific deal."""
        try:
            # Get deal with line item associations
            deal_response = await self.get_crm_object_by_id(
                'deals',
                deal_id,
                associations=['line_items']
            )
            
            if not deal_response.get('success'):
                return {'success': False, 'error': 'Failed to retrieve deal'}
            
            # Extract line item IDs from associations
            deal_data = deal_response.get('data', {})
            associations = deal_data.get('associations', {})
            line_item_associations = associations.get('line_items', {})
            line_item_results = line_item_associations.get('results', [])
            
            line_items = []
            for line_item_ref in line_item_results:
                line_item_id = line_item_ref.get('id')
                if line_item_id:
                    line_item_response = await self.get_crm_object_by_id(
                        'line_items',
                        line_item_id,
                        associations=['products']
                    )
                    if line_item_response.get('success'):
                        line_items.append(line_item_response.get('data'))
            
            return {
                'success': True,
                'data': line_items,
                'deal_id': deal_id
            }
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot deal line items: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot deal line items: {str(e)}")
    
    # Pipeline Methods
    async def get_deal_pipelines(self) -> Dict[str, Any]:
        """Get deal pipelines from HubSpot."""
        try:
            endpoint = self.authenticator.get_api_url('crm_pipelines', 'deals')
            
            response = await self.make_request(endpoint)
            
            if not response.get('success'):
                raise HubSpotAPIError(f"Failed to retrieve deal pipelines: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot deal pipelines: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot deal pipelines: {str(e)}")
    
    async def get_deal_stages(self, pipeline_id: Optional[str] = None) -> Dict[str, Any]:
        """Get deal stages from HubSpot."""
        try:
            if pipeline_id:
                endpoint = f"{self.authenticator.get_api_url('crm_pipelines', 'deals')}/{pipeline_id}/stages"
            else:
                # Get all pipelines and their stages
                pipelines_response = await self.get_deal_pipelines()
                if pipelines_response.get('success'):
                    pipelines_data = pipelines_response.get('data', {})
                    results = pipelines_data.get('results', [])
                    
                    all_stages = []
                    for pipeline in results:
                        stages = pipeline.get('stages', [])
                        for stage in stages:
                            stage['pipeline_id'] = pipeline.get('id')
                            stage['pipeline_label'] = pipeline.get('label')
                            all_stages.append(stage)
                    
                    return {
                        'success': True,
                        'data': {'results': all_stages}
                    }
                else:
                    return pipelines_response
            
            response = await self.make_request(endpoint)
            
            if not response.get('success'):
                raise HubSpotAPIError(f"Failed to retrieve deal stages: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot deal stages: {str(e)}")
            raise HubSpotAPIError(f"Error retrieving HubSpot deal stages: {str(e)}")