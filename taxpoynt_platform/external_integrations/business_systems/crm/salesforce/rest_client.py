"""
Salesforce REST Client Module
Handles REST API communication and SOQL queries for Salesforce CRM services.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, quote

import aiohttp

from .exceptions import SalesforceAPIError, SalesforceConnectionError, SalesforceRateLimitError, SalesforceSOQLError

logger = logging.getLogger(__name__)


class SalesforceRESTClient:
    """Handles REST API communication with Salesforce CRM services."""
    
    def __init__(self, authenticator):
        """Initialize with a Salesforce authenticator instance."""
        self.authenticator = authenticator
    
    async def make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_instance_url: bool = True
    ) -> Dict[str, Any]:
        """
        Make a REST API request to Salesforce.
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            use_instance_url: Whether to use instance URL as base
            
        Returns:
            Response data from Salesforce REST API
        """
        try:
            # Ensure valid authentication
            if not await self.authenticator.ensure_valid_token():
                raise SalesforceConnectionError("Authentication failed")
            
            if not self.authenticator.session:
                self.authenticator.session = await self.authenticator._create_session()
            
            # Build URL
            if use_instance_url:
                if endpoint.startswith('/'):
                    url = urljoin(self.authenticator.instance_url, endpoint)
                else:
                    url = urljoin(self.authenticator.instance_url, f"/{endpoint}")
            else:
                url = endpoint
            
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
            logger.error(f"Salesforce REST request failed: {str(e)}")
            raise SalesforceAPIError(f"Salesforce REST request failed: {str(e)}")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle Salesforce REST API response and error cases."""
        try:
            if response.status == 200:
                data = await response.json()
                return {
                    'success': True,
                    'data': data,
                    'total_size': data.get('totalSize', 0),
                    'done': data.get('done', True),
                    'next_records_url': data.get('nextRecordsUrl'),
                    'records': data.get('records', [])
                }
            
            elif response.status == 201:  # Created
                data = await response.json()
                return {
                    'success': True,
                    'data': data,
                    'created': True,
                    'id': data.get('id'),
                    'success_flag': data.get('success')
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
                if await self.authenticator.refresh_access_token():
                    raise SalesforceConnectionError("Token refreshed, retry needed")
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
                raise SalesforceRateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
            
            else:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': f'Request failed with status {response.status}',
                    'status_code': response.status,
                    'details': error_text
                }
                
        except Exception as e:
            logger.error(f"Error handling Salesforce response: {str(e)}")
            return {
                'success': False,
                'error': f'Response handling error: {str(e)}'
            }
    
    # SOQL Query Methods
    async def execute_soql(self, query: str) -> Dict[str, Any]:
        """Execute a SOQL query."""
        try:
            endpoint = self.authenticator.get_api_url('query')
            params = {'q': query}
            
            response = await self.make_request(endpoint, params=params)
            
            if not response.get('success'):
                raise SalesforceSOQLError(f"SOQL query failed: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing SOQL query: {str(e)}")
            raise SalesforceSOQLError(f"Error executing SOQL query: {str(e)}")
    
    async def execute_sosl(self, search: str) -> Dict[str, Any]:
        """Execute a SOSL search."""
        try:
            endpoint = self.authenticator.get_api_url('search')
            params = {'q': search}
            
            response = await self.make_request(endpoint, params=params)
            
            if not response.get('success'):
                raise SalesforceAPIError(f"SOSL search failed: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing SOSL search: {str(e)}")
            raise SalesforceAPIError(f"Error executing SOSL search: {str(e)}")
    
    # SObject Methods
    async def get_sobject_records(
        self,
        sobject_type: str,
        fields: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get records from a Salesforce SObject."""
        try:
            # Build SOQL query
            if fields:
                field_list = ', '.join(fields)
            else:
                field_list = 'Id, Name'
            
            query = f"SELECT {field_list} FROM {sobject_type}"
            
            if where_clause:
                query += f" WHERE {where_clause}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            query += f" LIMIT {limit}"
            
            if offset > 0:
                query += f" OFFSET {offset}"
            
            return await self.execute_soql(query)
            
        except Exception as e:
            logger.error(f"Error retrieving {sobject_type} records: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving {sobject_type} records: {str(e)}")
    
    async def get_sobject_by_id(self, sobject_type: str, record_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a specific SObject record by ID."""
        try:
            endpoint = self.authenticator.get_sobject_url(sobject_type, record_id)
            
            params = {}
            if fields:
                params['fields'] = ','.join(fields)
            
            response = await self.make_request(endpoint, params=params)
            
            if not response.get('success'):
                raise SalesforceAPIError(f"Failed to retrieve {sobject_type} {record_id}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving {sobject_type} {record_id}: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving {sobject_type} {record_id}: {str(e)}")
    
    async def create_sobject_record(self, sobject_type: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new SObject record."""
        try:
            endpoint = self.authenticator.get_sobject_url(sobject_type)
            
            response = await self.make_request(endpoint, method='POST', data=record_data)
            
            if not response.get('success'):
                raise SalesforceAPIError(f"Failed to create {sobject_type}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating {sobject_type}: {str(e)}")
            raise SalesforceAPIError(f"Error creating {sobject_type}: {str(e)}")
    
    async def update_sobject_record(self, sobject_type: str, record_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing SObject record."""
        try:
            endpoint = self.authenticator.get_sobject_url(sobject_type, record_id)
            
            response = await self.make_request(endpoint, method='PATCH', data=record_data)
            
            if not response.get('success'):
                raise SalesforceAPIError(f"Failed to update {sobject_type} {record_id}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating {sobject_type} {record_id}: {str(e)}")
            raise SalesforceAPIError(f"Error updating {sobject_type} {record_id}: {str(e)}")
    
    async def delete_sobject_record(self, sobject_type: str, record_id: str) -> Dict[str, Any]:
        """Delete an SObject record."""
        try:
            endpoint = self.authenticator.get_sobject_url(sobject_type, record_id)
            
            response = await self.make_request(endpoint, method='DELETE')
            
            if not response.get('success'):
                raise SalesforceAPIError(f"Failed to delete {sobject_type} {record_id}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting {sobject_type} {record_id}: {str(e)}")
            raise SalesforceAPIError(f"Error deleting {sobject_type} {record_id}: {str(e)}")
    
    # Specific CRM Object Methods
    async def get_opportunities(
        self,
        limit: int = 100,
        offset: int = 0,
        stage: Optional[str] = None,
        owner_id: Optional[str] = None,
        close_date_from: Optional[str] = None,
        close_date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get opportunities from Salesforce."""
        try:
            fields = [
                'Id', 'Name', 'AccountId', 'Account.Name', 'Amount', 'CloseDate',
                'StageName', 'Probability', 'OwnerId', 'Owner.Name', 'Description',
                'CreatedDate', 'LastModifiedDate', 'Type', 'LeadSource'
            ]
            
            where_conditions = []
            
            if stage:
                where_conditions.append(f"StageName = '{stage}'")
            
            if owner_id:
                where_conditions.append(f"OwnerId = '{owner_id}'")
            
            if close_date_from:
                where_conditions.append(f"CloseDate >= {close_date_from}")
            
            if close_date_to:
                where_conditions.append(f"CloseDate <= {close_date_to}")
            
            where_clause = ' AND '.join(where_conditions) if where_conditions else None
            
            return await self.get_sobject_records(
                'Opportunity',
                fields=fields,
                limit=limit,
                offset=offset,
                where_clause=where_clause,
                order_by='LastModifiedDate DESC'
            )
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce opportunities: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving Salesforce opportunities: {str(e)}")
    
    async def get_accounts(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get accounts/companies from Salesforce."""
        try:
            fields = [
                'Id', 'Name', 'Type', 'Industry', 'Phone', 'Website',
                'BillingAddress', 'ShippingAddress', 'Description',
                'AnnualRevenue', 'NumberOfEmployees', 'OwnerId', 'Owner.Name'
            ]
            
            where_clause = None
            if search_term:
                where_clause = f"Name LIKE '%{search_term}%'"
            
            return await self.get_sobject_records(
                'Account',
                fields=fields,
                limit=limit,
                offset=offset,
                where_clause=where_clause,
                order_by='Name ASC'
            )
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce accounts: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving Salesforce accounts: {str(e)}")
    
    async def get_contacts(
        self,
        limit: int = 100,
        offset: int = 0,
        account_id: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get contacts from Salesforce."""
        try:
            fields = [
                'Id', 'FirstName', 'LastName', 'Name', 'Email', 'Phone',
                'AccountId', 'Account.Name', 'Title', 'Department',
                'MailingAddress', 'Description', 'OwnerId', 'Owner.Name'
            ]
            
            where_conditions = []
            
            if account_id:
                where_conditions.append(f"AccountId = '{account_id}'")
            
            if search_term:
                where_conditions.append(f"(Name LIKE '%{search_term}%' OR Email LIKE '%{search_term}%')")
            
            where_clause = ' AND '.join(where_conditions) if where_conditions else None
            
            return await self.get_sobject_records(
                'Contact',
                fields=fields,
                limit=limit,
                offset=offset,
                where_clause=where_clause,
                order_by='LastName ASC'
            )
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce contacts: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving Salesforce contacts: {str(e)}")
    
    async def get_leads(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get leads from Salesforce."""
        try:
            fields = [
                'Id', 'FirstName', 'LastName', 'Name', 'Company', 'Email',
                'Phone', 'Status', 'LeadSource', 'Industry', 'Title',
                'Address', 'Description', 'OwnerId', 'Owner.Name'
            ]
            
            where_conditions = []
            
            if status:
                where_conditions.append(f"Status = '{status}'")
            
            if search_term:
                where_conditions.append(f"(Name LIKE '%{search_term}%' OR Company LIKE '%{search_term}%' OR Email LIKE '%{search_term}%')")
            
            where_clause = ' AND '.join(where_conditions) if where_conditions else None
            
            return await self.get_sobject_records(
                'Lead',
                fields=fields,
                limit=limit,
                offset=offset,
                where_clause=where_clause,
                order_by='LastModifiedDate DESC'
            )
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce leads: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving Salesforce leads: {str(e)}")
    
    async def get_products(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products from Salesforce."""
        try:
            fields = [
                'Id', 'Name', 'ProductCode', 'Description', 'IsActive',
                'Family', 'CreatedDate', 'LastModifiedDate'
            ]
            
            where_conditions = ['IsActive = true']  # Only active products
            
            if search_term:
                where_conditions.append(f"(Name LIKE '%{search_term}%' OR ProductCode LIKE '%{search_term}%')")
            
            where_clause = ' AND '.join(where_conditions)
            
            return await self.get_sobject_records(
                'Product2',
                fields=fields,
                limit=limit,
                offset=offset,
                where_clause=where_clause,
                order_by='Name ASC'
            )
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce products: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving Salesforce products: {str(e)}")
    
    async def get_opportunity_line_items(self, opportunity_id: str) -> Dict[str, Any]:
        """Get line items for an opportunity."""
        try:
            fields = [
                'Id', 'OpportunityId', 'Product2Id', 'Product2.Name',
                'Product2.ProductCode', 'Quantity', 'UnitPrice', 'TotalPrice',
                'Description', 'ServiceDate'
            ]
            
            where_clause = f"OpportunityId = '{opportunity_id}'"
            
            return await self.get_sobject_records(
                'OpportunityLineItem',
                fields=fields,
                where_clause=where_clause,
                order_by='Product2.Name ASC'
            )
            
        except Exception as e:
            logger.error(f"Error retrieving opportunity line items: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving opportunity line items: {str(e)}")
    
    # Metadata and Utility Methods
    async def get_sobject_describe(self, sobject_type: str) -> Dict[str, Any]:
        """Get metadata description for an SObject."""
        try:
            endpoint = f"{self.authenticator.get_sobject_url(sobject_type)}/describe"
            
            response = await self.make_request(endpoint)
            
            if not response.get('success'):
                raise SalesforceAPIError(f"Failed to describe {sobject_type}: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error describing {sobject_type}: {str(e)}")
            raise SalesforceAPIError(f"Error describing {sobject_type}: {str(e)}")
    
    async def get_limits(self) -> Dict[str, Any]:
        """Get organization limits."""
        try:
            endpoint = self.authenticator.get_api_url('limits')
            
            response = await self.make_request(endpoint)
            
            if not response.get('success'):
                raise SalesforceAPIError(f"Failed to retrieve limits: {response.get('error')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce limits: {str(e)}")
            raise SalesforceAPIError(f"Error retrieving Salesforce limits: {str(e)}")