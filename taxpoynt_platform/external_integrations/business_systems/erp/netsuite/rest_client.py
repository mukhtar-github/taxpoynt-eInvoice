"""
NetSuite REST Client Module
Handles REST API communication for NetSuite ERP services.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

from .exceptions import NetSuiteAPIError, NetSuiteConnectionError, NetSuiteRateLimitError

logger = logging.getLogger(__name__)


class NetSuiteRESTClient:
    """Handles REST API communication with NetSuite ERP services."""
    
    def __init__(self, authenticator):
        """Initialize with a NetSuite authenticator instance."""
        self.authenticator = authenticator
    
    async def make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        api_type: str = 'rest_api'
    ) -> Dict[str, Any]:
        """
        Make a REST API request to NetSuite.
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            params: Query parameters
            data: Request body data
            api_type: API type (rest_api, suiteql, metadata)
            
        Returns:
            Response data from NetSuite REST API
        """
        try:
            # Ensure valid authentication
            if not await self.authenticator.ensure_valid_token():
                raise NetSuiteConnectionError("Authentication failed")
            
            if not self.authenticator.session:
                self.authenticator.session = await self.authenticator._create_session()
            
            # Build URL
            if api_type == 'suiteql':
                url = self.authenticator.get_suiteql_url()
            else:
                url = self.authenticator.get_api_url(api_type, endpoint)
            
            # Prepare parameters
            if params is None:
                params = {}
            
            # Generate OAuth headers
            headers = self.authenticator._generate_oauth_headers(method, url, params)
            
            # Make request
            async with self.authenticator.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            ) as response:
                return await self._handle_response(response)
                
        except Exception as e:
            logger.error(f"NetSuite REST request failed: {str(e)}")
            raise NetSuiteAPIError(f"NetSuite REST request failed: {str(e)}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle NetSuite REST API response and error cases."""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'data': data.get('items', []) if 'items' in data else data,
                    'count': len(data.get('items', [])) if 'items' in data else 1,
                    'has_more': data.get('hasMore', False),
                    'total_results': data.get('totalResults'),
                    'offset': data.get('offset', 0),
                    'links': data.get('links', [])
                }
            
            elif response.status == 201:  # Created
                data = await response.json()
                return {
                    'success': True,
                    'data': data,
                    'created': True
                }
            
            elif response.status == 204:  # No Content
                return {
                    'success': True,
                    'data': None,
                    'message': 'Operation completed successfully'
                }
            
            elif response.status == 400:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': 'Bad request - invalid parameters',
                    'status_code': 400,
                    'details': error_text
                }
            
            elif response.status == 401:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': 'Authentication failed',
                    'status_code': 401,
                    'details': error_text
                }
            
            elif response.status == 403:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': 'Access forbidden - insufficient permissions',
                    'status_code': 403,
                    'details': error_text
                }
            
            elif response.status == 404:
                return {
                    'success': False,
                    'error': 'Resource not found',
                    'status_code': 404
                }
            
            elif response.status == 429:  # Rate limited
                error_text = await response.text()
                retry_after = response.headers.get('Retry-After', '60')
                raise NetSuiteRateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
            
            else:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': f'Request failed with status {response.status}',
                    'status_code': response.status,
                    'details': error_text
                }
                
        except Exception as e:
            logger.error(f"Error handling NetSuite response: {str(e)}")
            return {
                'success': False,
                'error': f'Response handling error: {str(e)}'
            }
    
    # NetSuite REST API Methods
    async def get_companies(self) -> Dict[str, Any]:
        """Get companies from NetSuite."""
        try:
            return await self.make_request('companies', api_type='metadata')
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite companies: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite companies: {str(e)}")
    
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get invoices from NetSuite."""
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            # Add filters if provided
            if filters:
                if filters.get('start_date'):
                    params['lastModifiedDate'] = f"after:{filters['start_date']}"
                
                if filters.get('customer_id'):
                    params['entity'] = filters['customer_id']
                
                if filters.get('status'):
                    params['status'] = filters['status']
            
            return await self.make_request('invoice', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite invoices: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite invoices: {str(e)}")
    
    async def get_customers(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get customers from NetSuite."""
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            if search_term:
                params['q'] = search_term
            
            return await self.make_request('customer', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite customers: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite customers: {str(e)}")
    
    async def get_vendors(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get vendors from NetSuite."""
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            if search_term:
                params['q'] = search_term
            
            return await self.make_request('vendor', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite vendors: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite vendors: {str(e)}")
    
    async def get_items(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get items from NetSuite."""
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            if search_term:
                params['q'] = search_term
            
            return await self.make_request('item', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite items: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite items: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: str) -> Dict[str, Any]:
        """Get a specific invoice by ID."""
        try:
            endpoint = f"invoice/{invoice_id}"
            return await self.make_request(endpoint)
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite invoice {invoice_id}: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite invoice {invoice_id}: {str(e)}")
    
    async def execute_suiteql(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a SuiteQL query."""
        try:
            query_params = {'q': query}
            if params:
                query_params.update(params)
            
            return await self.make_request('', method='GET', params=query_params, api_type='suiteql')
            
        except Exception as e:
            logger.error(f"Error executing NetSuite SuiteQL query: {str(e)}")
            raise NetSuiteAPIError(f"Error executing NetSuite SuiteQL query: {str(e)}")
    
    async def search_invoices(
        self,
        search_criteria: Dict[str, Any],
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search invoices with specific criteria using SuiteQL."""
        try:
            # Build SuiteQL query
            where_conditions = []
            
            if search_criteria.get('customer_name'):
                where_conditions.append(f"entity.entityid LIKE '%{search_criteria['customer_name']}%'")
            
            if search_criteria.get('invoice_number'):
                where_conditions.append(f"tranid LIKE '%{search_criteria['invoice_number']}%'")
            
            if search_criteria.get('amount_range'):
                min_amount, max_amount = search_criteria['amount_range']
                if min_amount is not None:
                    where_conditions.append(f"total >= {min_amount}")
                if max_amount is not None:
                    where_conditions.append(f"total <= {max_amount}")
            
            if search_criteria.get('date_range'):
                start_date, end_date = search_criteria['date_range']
                if start_date:
                    where_conditions.append(f"trandate >= '{start_date}'")
                if end_date:
                    where_conditions.append(f"trandate <= '{end_date}'")
            
            if search_criteria.get('status'):
                where_conditions.append(f"status = '{search_criteria['status']}'")
            
            # Construct SuiteQL query
            base_query = """
                SELECT 
                    id, tranid, trandate, entity, total, status, currency,
                    entity.entityid as customer_name, entity.email as customer_email
                FROM transaction 
                WHERE recordtype = 'invoice'
            """
            
            if where_conditions:
                base_query += " AND " + " AND ".join(where_conditions)
            
            base_query += f" ORDER BY trandate DESC LIMIT {limit}"
            
            return await self.execute_suiteql(base_query)
            
        except Exception as e:
            logger.error(f"Error searching NetSuite invoices: {str(e)}")
            raise NetSuiteAPIError(f"Error searching NetSuite invoices: {str(e)}")
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice in NetSuite."""
        try:
            return await self.make_request('invoice', method='POST', data=invoice_data)
            
        except Exception as e:
            logger.error(f"Error creating NetSuite invoice: {str(e)}")
            raise NetSuiteAPIError(f"Error creating NetSuite invoice: {str(e)}")
    
    async def update_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing invoice in NetSuite."""
        try:
            endpoint = f"invoice/{invoice_id}"
            return await self.make_request(endpoint, method='PATCH', data=invoice_data)
            
        except Exception as e:
            logger.error(f"Error updating NetSuite invoice {invoice_id}: {str(e)}")
            raise NetSuiteAPIError(f"Error updating NetSuite invoice {invoice_id}: {str(e)}")
    
    async def get_subsidiaries(self) -> Dict[str, Any]:
        """Get subsidiaries from NetSuite."""
        try:
            return await self.make_request('subsidiary')
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite subsidiaries: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite subsidiaries: {str(e)}")
    
    async def get_currencies(self) -> Dict[str, Any]:
        """Get currencies from NetSuite."""
        try:
            return await self.make_request('currency')
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite currencies: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite currencies: {str(e)}")
    
    async def get_tax_codes(self) -> Dict[str, Any]:
        """Get tax codes from NetSuite."""
        try:
            return await self.make_request('salestaxitem')
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite tax codes: {str(e)}")
            raise NetSuiteAPIError(f"Error retrieving NetSuite tax codes: {str(e)}")