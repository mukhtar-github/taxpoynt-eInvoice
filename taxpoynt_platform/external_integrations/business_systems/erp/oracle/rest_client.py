"""
Oracle REST Client Module
Handles REST API communication for Oracle ERP Cloud services.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlencode

import aiohttp

from .exceptions import OracleAPIError, OracleConnectionError

logger = logging.getLogger(__name__)


class OracleRESTClient:
    """Handles REST API communication with Oracle ERP Cloud services."""
    
    def __init__(self, authenticator):
        """Initialize with an Oracle authenticator instance."""
        self.authenticator = authenticator
    
    async def make_request(
        self,
        module: str,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a REST API request to Oracle ERP Cloud.
        
        Args:
            module: Oracle module (fscm, crm, hcm, ppm)
            endpoint: API endpoint within the module
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            Response data from Oracle REST API
        """
        try:
            # Ensure valid authentication
            if not await self.authenticator.ensure_valid_token():
                raise OracleConnectionError("Authentication failed")
            
            if not self.authenticator.session:
                self.authenticator.session = await self.authenticator._create_session()
            
            # Build URL
            url = self.authenticator.get_api_url(module, endpoint)
            
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
            logger.error(f"Oracle REST request failed: {str(e)}")
            raise OracleAPIError(f"Oracle REST request failed: {str(e)}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle Oracle REST API response and error cases."""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'data': data.get('items', []) if 'items' in data else data,
                    'count': data.get('count', len(data.get('items', []))),
                    'has_more': data.get('hasMore', False),
                    'limit': data.get('limit'),
                    'offset': data.get('offset'),
                    'total_results': data.get('totalResults'),
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
            
            elif response.status == 401:
                error_text = await response.text()
                # Try to refresh token and retry once
                if await self.authenticator.refresh_access_token():
                    raise OracleConnectionError("Token refreshed, retry needed")
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
            logger.error(f"Error handling Oracle response: {str(e)}")
            return {
                'success': False,
                'error': f'Response handling error: {str(e)}'
            }
    
    # Financial Supply Chain Management (FSCM) API Methods
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get invoices from Oracle FSCM API."""
        try:
            params = {
                'limit': limit,
                'offset': offset,
                'fields': 'InvoiceId,InvoiceNumber,InvoiceDate,InvoiceAmount,InvoiceCurrencyCode,SupplierNumber,SupplierName,PaymentStatusLookupCode,InvoiceStatusLookupCode'
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = []
                
                if filters.get('start_date'):
                    filter_conditions.append(f"InvoiceDate >= '{filters['start_date']}'")
                
                if filters.get('end_date'):
                    filter_conditions.append(f"InvoiceDate <= '{filters['end_date']}'")
                
                if filters.get('supplier_number'):
                    filter_conditions.append(f"SupplierNumber = '{filters['supplier_number']}'")
                
                if filters.get('invoice_status'):
                    filter_conditions.append(f"InvoiceStatusLookupCode = '{filters['invoice_status']}'")
                
                if filter_conditions:
                    params['q'] = ' and '.join(filter_conditions)
            
            return await self.make_request('fscm', 'invoices', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle invoices: {str(e)}")
            raise OracleAPIError(f"Error retrieving Oracle invoices: {str(e)}")
    
    async def get_receivables(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get receivables from Oracle FSCM API."""
        try:
            params = {
                'limit': limit,
                'offset': offset,
                'fields': 'CustomerTrxId,TrxNumber,TrxDate,TransactionTypeId,TransactionTypeName,BillToCustomerNumber,BillToCustomerName,InvoiceCurrencyCode,TrxLineAmount'
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = []
                
                if filters.get('start_date'):
                    filter_conditions.append(f"TrxDate >= '{filters['start_date']}'")
                
                if filters.get('end_date'):
                    filter_conditions.append(f"TrxDate <= '{filters['end_date']}'")
                
                if filters.get('customer_number'):
                    filter_conditions.append(f"BillToCustomerNumber = '{filters['customer_number']}'")
                
                if filters.get('transaction_type'):
                    filter_conditions.append(f"TransactionTypeName = '{filters['transaction_type']}'")
                
                if filter_conditions:
                    params['q'] = ' and '.join(filter_conditions)
            
            return await self.make_request('fscm', 'receivables', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle receivables: {str(e)}")
            raise OracleAPIError(f"Error retrieving Oracle receivables: {str(e)}")
    
    async def get_erp_integrations(
        self,
        limit: int = 100,
        offset: int = 0,
        integration_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get ERP integrations from Oracle FSCM API."""
        try:
            params = {
                'limit': limit,
                'offset': offset,
                'fields': 'IntegrationId,IntegrationName,IntegrationStatus,LastRunDate,NextRunDate'
            }
            
            if integration_name:
                params['q'] = f"IntegrationName = '{integration_name}'"
            
            return await self.make_request('fscm', 'erpintegrations', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle ERP integrations: {str(e)}")
            raise OracleAPIError(f"Error retrieving Oracle ERP integrations: {str(e)}")
    
    # Customer Relationship Management (CRM) API Methods
    async def get_accounts(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get customer accounts from Oracle CRM API."""
        try:
            params = {
                'limit': limit,
                'offset': offset,
                'fields': 'PartyId,PartyNumber,PartyName,PartyType,OrganizationType,CustomerAccountId,AccountNumber,AccountName,CustomerType'
            }
            
            if search_term:
                params['q'] = f"PartyName like '%{search_term}%' or AccountName like '%{search_term}%'"
            
            return await self.make_request('crm', 'accounts', params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle accounts: {str(e)}")
            raise OracleAPIError(f"Error retrieving Oracle accounts: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: str) -> Dict[str, Any]:
        """Get a specific invoice by ID."""
        try:
            endpoint = f"invoices/{invoice_id}"
            params = {
                'fields': 'InvoiceId,InvoiceNumber,InvoiceDate,InvoiceAmount,InvoiceCurrencyCode,SupplierNumber,SupplierName,PaymentStatusLookupCode,InvoiceStatusLookupCode,InvoiceLineId,LineNumber,LineAmount,LineDescription'
            }
            
            return await self.make_request('fscm', endpoint, params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle invoice {invoice_id}: {str(e)}")
            raise OracleAPIError(f"Error retrieving Oracle invoice {invoice_id}: {str(e)}")
    
    async def get_account_by_id(self, account_id: str) -> Dict[str, Any]:
        """Get a specific account by ID."""
        try:
            endpoint = f"accounts/{account_id}"
            params = {
                'fields': 'PartyId,PartyNumber,PartyName,PartyType,OrganizationType,CustomerAccountId,AccountNumber,AccountName,CustomerType,PrimaryAddress,PrimaryContactPoint'
            }
            
            return await self.make_request('crm', endpoint, params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle account {account_id}: {str(e)}")
            raise OracleAPIError(f"Error retrieving Oracle account {account_id}: {str(e)}")
    
    async def search_invoices(
        self,
        search_criteria: Dict[str, Any],
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search invoices with specific criteria."""
        try:
            filter_conditions = []
            
            # Build filter conditions based on search criteria
            if search_criteria.get('supplier_name'):
                filter_conditions.append(f"SupplierName like '%{search_criteria['supplier_name']}%'")
            
            if search_criteria.get('invoice_number'):
                filter_conditions.append(f"InvoiceNumber like '%{search_criteria['invoice_number']}%'")
            
            if search_criteria.get('amount_range'):
                min_amount, max_amount = search_criteria['amount_range']
                if min_amount is not None:
                    filter_conditions.append(f"InvoiceAmount >= {min_amount}")
                if max_amount is not None:
                    filter_conditions.append(f"InvoiceAmount <= {max_amount}")
            
            if search_criteria.get('date_range'):
                start_date, end_date = search_criteria['date_range']
                if start_date:
                    filter_conditions.append(f"InvoiceDate >= '{start_date}'")
                if end_date:
                    filter_conditions.append(f"InvoiceDate <= '{end_date}'")
            
            if search_criteria.get('status'):
                filter_conditions.append(f"InvoiceStatusLookupCode = '{search_criteria['status']}'")
            
            params = {
                'limit': limit,
                'fields': 'InvoiceId,InvoiceNumber,InvoiceDate,InvoiceAmount,InvoiceCurrencyCode,SupplierNumber,SupplierName,PaymentStatusLookupCode,InvoiceStatusLookupCode'
            }
            
            if filter_conditions:
                params['q'] = ' and '.join(filter_conditions)
            
            return await self.make_request('fscm', 'invoices', params=params)
            
        except Exception as e:
            logger.error(f"Error searching Oracle invoices: {str(e)}")
            raise OracleAPIError(f"Error searching Oracle invoices: {str(e)}")
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice in Oracle."""
        try:
            return await self.make_request('fscm', 'invoices', method='POST', data=invoice_data)
            
        except Exception as e:
            logger.error(f"Error creating Oracle invoice: {str(e)}")
            raise OracleAPIError(f"Error creating Oracle invoice: {str(e)}")
    
    async def update_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing invoice in Oracle."""
        try:
            endpoint = f"invoices/{invoice_id}"
            return await self.make_request('fscm', endpoint, method='PATCH', data=invoice_data)
            
        except Exception as e:
            logger.error(f"Error updating Oracle invoice {invoice_id}: {str(e)}")
            raise OracleAPIError(f"Error updating Oracle invoice {invoice_id}: {str(e)}")
    
    async def get_metadata(self, module: str, entity: str) -> Dict[str, Any]:
        """Get metadata for a specific entity."""
        try:
            endpoint = f"{entity}/describe"
            return await self.make_request(module, endpoint)
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle metadata for {module}.{entity}: {str(e)}")
            raise OracleAPIError(f"Error retrieving Oracle metadata for {module}.{entity}: {str(e)}")