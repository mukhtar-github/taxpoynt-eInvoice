"""
Microsoft Dynamics CRM REST Client Module
Handles REST API communication for Microsoft Dynamics CRM services.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, quote
import aiohttp
import json

from .exceptions import (
    DynamicsCRMAPIError,
    DynamicsCRMConnectionError,
    DynamicsCRMODataError,
    DynamicsCRMQuotaError
)


class DynamicsCRMRestClient:
    """
    REST client for Microsoft Dynamics CRM Web API.
    Handles OData queries, CRUD operations, batch requests, and metadata operations.
    """

    def __init__(self, authenticator, config: Dict[str, Any]):
        """
        Initialize the Dynamics CRM REST client.
        
        Args:
            authenticator: DynamicsCRMAuthenticator instance
            config: Configuration containing API settings
        """
        self.logger = logging.getLogger(__name__)
        self.authenticator = authenticator
        self.environment_url = authenticator.environment_url
        self.api_version = authenticator.api_version
        
        # API configuration
        self.base_url = f"{self.environment_url}/api/data/{self.api_version}"
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)
        
        # Session management
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with authentication and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            url: Request URL
            headers: Additional headers
            data: Request body data
            params: Query parameters
        
        Returns:
            Response data as dictionary
        """
        session = await self._get_session()
        
        # Get authentication headers
        auth_headers = self.authenticator.get_auth_headers()
        if headers:
            auth_headers.update(headers)
        
        # Convert data to JSON if provided
        json_data = json.dumps(data) if data else None
        
        for attempt in range(self.max_retries + 1):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=auth_headers,
                    data=json_data,
                    params=params
                ) as response:
                    
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        if attempt < self.max_retries:
                            self.logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise DynamicsCRMQuotaError("API rate limit exceeded")
                    
                    # Handle other errors
                    if response.status >= 400:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status}")
                        raise DynamicsCRMAPIError(f"API request failed: {error_msg}")
                    
                    # Handle successful responses
                    if response.status == 204:  # No Content
                        return {}
                    
                    if response.content_type == 'application/json':
                        return await response.json()
                    else:
                        return {'raw_response': await response.text()}
                        
            except aiohttp.ClientError as e:
                if attempt < self.max_retries:
                    self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying: {str(e)}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise DynamicsCRMConnectionError(f"Network error: {str(e)}")
        
        raise DynamicsCRMConnectionError("Max retries exceeded")

    async def odata_query(
        self,
        entity_set: str,
        select: Optional[List[str]] = None,
        filter_clause: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        expand: Optional[List[str]] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute OData query against Dynamics CRM.
        
        Args:
            entity_set: Entity set name (e.g., 'opportunities', 'accounts')
            select: List of fields to select
            filter_clause: OData filter expression
            orderby: OData orderby expression
            top: Maximum number of records to return
            expand: List of related entities to expand
            custom_headers: Additional headers
        
        Returns:
            Query results including value array and metadata
        """
        url = f"{self.base_url}/{entity_set}"
        params = {}
        
        # Build OData query parameters
        if select:
            params['$select'] = ','.join(select)
        
        if filter_clause:
            params['$filter'] = filter_clause
        
        if orderby:
            params['$orderby'] = orderby
        
        if top:
            params['$top'] = str(top)
        
        if expand:
            params['$expand'] = ','.join(expand)
        
        return await self._make_request('GET', url, headers=custom_headers, params=params)

    async def get_entity(
        self,
        entity_set: str,
        entity_id: str,
        select: Optional[List[str]] = None,
        expand: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a single entity by ID.
        
        Args:
            entity_set: Entity set name
            entity_id: Entity ID (GUID)
            select: List of fields to select
            expand: List of related entities to expand
        
        Returns:
            Entity data
        """
        url = f"{self.base_url}/{entity_set}({entity_id})"
        params = {}
        
        if select:
            params['$select'] = ','.join(select)
        
        if expand:
            params['$expand'] = ','.join(expand)
        
        return await self._make_request('GET', url, params=params)

    async def create_entity(
        self,
        entity_set: str,
        data: Dict[str, Any],
        return_record: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new entity.
        
        Args:
            entity_set: Entity set name
            data: Entity data
            return_record: Whether to return the created record
        
        Returns:
            Created entity data or creation metadata
        """
        url = f"{self.base_url}/{entity_set}"
        headers = {}
        
        if return_record:
            headers['Prefer'] = 'return=representation'
        
        return await self._make_request('POST', url, headers=headers, data=data)

    async def update_entity(
        self,
        entity_set: str,
        entity_id: str,
        data: Dict[str, Any],
        return_record: bool = False
    ) -> Dict[str, Any]:
        """
        Update an existing entity.
        
        Args:
            entity_set: Entity set name
            entity_id: Entity ID (GUID)
            data: Update data
            return_record: Whether to return the updated record
        
        Returns:
            Updated entity data or update metadata
        """
        url = f"{self.base_url}/{entity_set}({entity_id})"
        headers = {}
        
        if return_record:
            headers['Prefer'] = 'return=representation'
        
        return await self._make_request('PATCH', url, headers=headers, data=data)

    async def delete_entity(
        self,
        entity_set: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """
        Delete an entity.
        
        Args:
            entity_set: Entity set name
            entity_id: Entity ID (GUID)
        
        Returns:
            Deletion metadata
        """
        url = f"{self.base_url}/{entity_set}({entity_id})"
        return await self._make_request('DELETE', url)

    async def execute_batch(
        self,
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute batch request.
        
        Args:
            requests: List of request specifications
        
        Returns:
            Batch response
        """
        batch_url = f"{self.base_url}/$batch"
        
        # Build batch request body
        boundary = "batch_dynamics_crm"
        batch_body = f"--{boundary}\n"
        batch_body += "Content-Type: application/http\n"
        batch_body += "Content-Transfer-Encoding: binary\n\n"
        
        for i, request in enumerate(requests):
            method = request.get('method', 'GET')
            url = request.get('url', '')
            data = request.get('data')
            
            batch_body += f"{method} {url} HTTP/1.1\n"
            batch_body += "Accept: application/json\n"
            
            if data:
                batch_body += "Content-Type: application/json\n"
                batch_body += f"Content-Length: {len(json.dumps(data))}\n\n"
                batch_body += json.dumps(data) + "\n"
            else:
                batch_body += "\n"
            
            if i < len(requests) - 1:
                batch_body += f"--{boundary}\n"
                batch_body += "Content-Type: application/http\n"
                batch_body += "Content-Transfer-Encoding: binary\n\n"
        
        batch_body += f"--{boundary}--"
        
        headers = {
            'Content-Type': f'multipart/mixed;boundary={boundary}'
        }
        
        return await self._make_request('POST', batch_url, headers=headers, data=batch_body)

    async def get_metadata(self) -> Dict[str, Any]:
        """
        Get service metadata.
        
        Returns:
            Metadata document
        """
        metadata_url = f"{self.base_url}/$metadata"
        headers = {'Accept': 'application/xml'}
        
        return await self._make_request('GET', metadata_url, headers=headers)

    async def execute_function(
        self,
        function_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a Dynamics CRM function.
        
        Args:
            function_name: Function name
            parameters: Function parameters
        
        Returns:
            Function result
        """
        url = f"{self.base_url}/{function_name}"
        
        if parameters:
            param_string = ','.join([f"{k}='{v}'" for k, v in parameters.items()])
            url += f"({param_string})"
        
        return await self._make_request('GET', url)

    async def execute_action(
        self,
        action_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        entity_set: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a Dynamics CRM action.
        
        Args:
            action_name: Action name
            parameters: Action parameters
            entity_set: Target entity set (for bound actions)
            entity_id: Target entity ID (for bound actions)
        
        Returns:
            Action result
        """
        if entity_set and entity_id:
            url = f"{self.base_url}/{entity_set}({entity_id})/Microsoft.Dynamics.CRM.{action_name}"
        else:
            url = f"{self.base_url}/{action_name}"
        
        return await self._make_request('POST', url, data=parameters)

    async def search_entities(
        self,
        search_term: str,
        entities: Optional[List[str]] = None,
        top: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search across multiple entity types.
        
        Args:
            search_term: Search term
            entities: List of entity types to search
            top: Maximum number of results per entity
        
        Returns:
            Search results
        """
        search_url = f"{self.base_url}/search"
        
        params = {
            'search': search_term
        }
        
        if entities:
            params['entities'] = ','.join(entities)
        
        if top:
            params['top'] = str(top)
        
        return await self._make_request('GET', search_url, params=params)

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None