"""
Microsoft Dynamics REST Client Module
Handles REST API communication for Microsoft Dynamics 365 services.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

from .exceptions import DynamicsAPIError, DynamicsConnectionError

logger = logging.getLogger(__name__)


class DynamicsRESTClient:
    """Handles REST API communication with Microsoft Dynamics 365 services."""
    
    def __init__(self, authenticator):
        """Initialize with a Dynamics authenticator instance."""
        self.authenticator = authenticator
    
    async def make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_company_context: bool = True
    ) -> Dict[str, Any]:
        """
        Make a REST API request to Microsoft Dynamics 365.
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            use_company_context: Whether to include company context in URL
            
        Returns:
            Response data from Dynamics REST API
        """
        try:
            # Ensure valid authentication
            if not await self.authenticator.ensure_valid_token():
                raise DynamicsConnectionError("Authentication failed")
            
            if not self.authenticator.session:
                self.authenticator.session = await self.authenticator._create_session()
            
            # Build URL
            if use_company_context:
                url = self.authenticator.get_business_central_url(endpoint)
            else:
                url = self.authenticator.get_api_url('business_central', endpoint)
            
            # Prepare headers
            request_headers = await self.authenticator._get_auth_headers()
            if headers:
                request_headers.update(headers)
            
            # Prepare parameters
            if params is None:
                params = {}
            
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
            logger.error(f"Dynamics REST request failed: {str(e)}")
            raise DynamicsAPIError(f"Dynamics REST request failed: {str(e)}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle Dynamics REST API response and error cases."""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'data': data.get('value', []) if 'value' in data else data,
                    'count': len(data.get('value', [])) if 'value' in data else 1,
                    'odata_context': data.get('@odata.context'),
                    'odata_nextLink': data.get('@odata.nextLink'),
                    'odata_count': data.get('@odata.count')
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
            
            elif response.status == 401:
                error_text = await response.text()
                # Try to refresh token and retry once
                if await self.authenticator.refresh_access_token():
                    raise DynamicsConnectionError("Token refreshed, retry needed")
                else:
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
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'status_code': 429,
                    'retry_after': retry_after,
                    'details': error_text
                }
            
            else:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': f'Request failed with status {response.status}',
                    'status_code': response.status,
                    'details': error_text
                }
                
        except Exception as e:
            logger.error(f"Error handling Dynamics response: {str(e)}")
            return {
                'success': False,
                'error': f'Response handling error: {str(e)}'
            }
    
    # Business Central API Methods
    async def get_companies(self) -> Dict[str, Any]:
        """Get companies from Dynamics Business Central."""
        try:
            return await self.make_request('companies', use_company_context=False)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics companies: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics companies: {str(e)}")
    
    async def get_sales_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get sales invoices from Dynamics Business Central."""
        try:
            params = {
                '$top': limit,
                '$skip': offset
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = []
                
                if filters.get('start_date'):
                    filter_conditions.append(f"postingDate ge {filters['start_date']}")
                
                if filters.get('end_date'):
                    filter_conditions.append(f"postingDate le {filters['end_date']}")
                
                if filters.get('customer_number'):
                    filter_conditions.append(f"customerNumber eq '{filters['customer_number']}'")
                
                if filters.get('status'):
                    filter_conditions.append(f"status eq '{filters['status']}'")
                
                if filter_conditions:
                    params['$filter'] = ' and '.join(filter_conditions)
            
            return await self.make_request('salesInvoices', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics sales invoices: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics sales invoices: {str(e)}")
    
    async def get_purchase_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get purchase invoices from Dynamics Business Central."""
        try:
            params = {
                '$top': limit,
                '$skip': offset
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = []
                
                if filters.get('start_date'):
                    filter_conditions.append(f"postingDate ge {filters['start_date']}")
                
                if filters.get('end_date'):
                    filter_conditions.append(f"postingDate le {filters['end_date']}")
                
                if filters.get('vendor_number'):
                    filter_conditions.append(f"vendorNumber eq '{filters['vendor_number']}'")
                
                if filters.get('status'):
                    filter_conditions.append(f"status eq '{filters['status']}'")
                
                if filter_conditions:
                    params['$filter'] = ' and '.join(filter_conditions)
            
            return await self.make_request('purchaseInvoices', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics purchase invoices: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics purchase invoices: {str(e)}")
    
    async def get_customers(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get customers from Dynamics Business Central."""
        try:
            params = {
                '$top': limit,
                '$skip': offset
            }
            
            if search_term:
                params['$filter'] = f"contains(displayName, '{search_term}') or contains(number, '{search_term}')"
            
            return await self.make_request('customers', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics customers: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics customers: {str(e)}")
    
    async def get_vendors(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get vendors from Dynamics Business Central."""
        try:
            params = {
                '$top': limit,
                '$skip': offset
            }
            
            if search_term:
                params['$filter'] = f"contains(displayName, '{search_term}') or contains(number, '{search_term}')"
            
            return await self.make_request('vendors', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics vendors: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics vendors: {str(e)}")
    
    async def get_items(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get items from Dynamics Business Central."""
        try:
            params = {
                '$top': limit,
                '$skip': offset
            }
            
            if search_term:
                params['$filter'] = f"contains(displayName, '{search_term}') or contains(number, '{search_term}')"
            
            return await self.make_request('items', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics items: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics items: {str(e)}")
    
    async def get_sales_invoice_by_id(self, invoice_id: str) -> Dict[str, Any]:
        """Get a specific sales invoice by ID."""
        try:
            endpoint = f"salesInvoices({invoice_id})"
            return await self.make_request(endpoint)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics sales invoice {invoice_id}: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics sales invoice {invoice_id}: {str(e)}")
    
    async def get_purchase_invoice_by_id(self, invoice_id: str) -> Dict[str, Any]:
        """Get a specific purchase invoice by ID."""
        try:
            endpoint = f"purchaseInvoices({invoice_id})"
            return await self.make_request(endpoint)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics purchase invoice {invoice_id}: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics purchase invoice {invoice_id}: {str(e)}")
    
    async def search_invoices(
        self,
        search_criteria: Dict[str, Any],
        limit: int = 100,
        invoice_type: str = 'sales'  # 'sales' or 'purchase'
    ) -> Dict[str, Any]:
        """Search invoices with specific criteria."""
        try:
            filter_conditions = []
            
            # Build filter conditions based on search criteria
            if search_criteria.get('customer_name'):
                filter_conditions.append(f"contains(customerName, '{search_criteria['customer_name']}')")
            
            if search_criteria.get('vendor_name'):
                filter_conditions.append(f"contains(vendorName, '{search_criteria['vendor_name']}')")
            
            if search_criteria.get('invoice_number'):
                filter_conditions.append(f"contains(number, '{search_criteria['invoice_number']}')")
            
            if search_criteria.get('amount_range'):
                min_amount, max_amount = search_criteria['amount_range']
                if min_amount is not None:
                    filter_conditions.append(f"totalAmountIncludingTax ge {min_amount}")
                if max_amount is not None:
                    filter_conditions.append(f"totalAmountIncludingTax le {max_amount}")
            
            if search_criteria.get('date_range'):
                start_date, end_date = search_criteria['date_range']
                if start_date:
                    filter_conditions.append(f"postingDate ge {start_date}")
                if end_date:
                    filter_conditions.append(f"postingDate le {end_date}")
            
            if search_criteria.get('status'):
                filter_conditions.append(f"status eq '{search_criteria['status']}'")
            
            params = {
                '$top': limit
            }
            
            if filter_conditions:
                params['$filter'] = ' and '.join(filter_conditions)
            
            endpoint = 'salesInvoices' if invoice_type == 'sales' else 'purchaseInvoices'
            return await self.make_request(endpoint, params=params)
            
        except Exception as e:
            logger.error(f"Error searching Dynamics invoices: {str(e)}")
            raise DynamicsAPIError(f"Error searching Dynamics invoices: {str(e)}")
    
    async def create_sales_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sales invoice in Dynamics."""
        try:
            return await self.make_request('salesInvoices', method='POST', data=invoice_data)
            
        except Exception as e:
            logger.error(f"Error creating Dynamics sales invoice: {str(e)}")
            raise DynamicsAPIError(f"Error creating Dynamics sales invoice: {str(e)}")
    
    async def update_sales_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing sales invoice in Dynamics."""
        try:
            endpoint = f"salesInvoices({invoice_id})"
            return await self.make_request(endpoint, method='PATCH', data=invoice_data)
            
        except Exception as e:
            logger.error(f"Error updating Dynamics sales invoice {invoice_id}: {str(e)}")
            raise DynamicsAPIError(f"Error updating Dynamics sales invoice {invoice_id}: {str(e)}")
    
    async def get_metadata(self, entity: str) -> Dict[str, Any]:
        """Get metadata for a specific entity."""
        try:
            endpoint = f"$metadata#{entity}"
            return await self.make_request(endpoint)
            
        except Exception as e:
            logger.error(f"Error retrieving Dynamics metadata for {entity}: {str(e)}")
            raise DynamicsAPIError(f"Error retrieving Dynamics metadata for {entity}: {str(e)}")