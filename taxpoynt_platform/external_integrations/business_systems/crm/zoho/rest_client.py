"""
Zoho CRM REST Client Module
Handles REST API communication for Zoho CRM services.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, quote
import aiohttp
import json

from .exceptions import (
    ZohoCRMAPIError,
    ZohoCRMConnectionError,
    ZohoCRMQuotaError,
    ZohoCRMPermissionError,
    ZohoCRMValidationError
)


class ZohoCRMRestClient:
    """
    REST client for Zoho CRM API v2.
    Handles CRUD operations, bulk operations, search, and file management.
    """

    def __init__(self, authenticator, config: Dict[str, Any]):
        """
        Initialize the Zoho CRM REST client.
        
        Args:
            authenticator: ZohoCRMAuthenticator instance
            config: Configuration containing API settings
        """
        self.logger = logging.getLogger(__name__)
        self.authenticator = authenticator
        self.api_base_url = authenticator.api_base_url
        
        # API configuration
        self.base_url = f"{self.api_base_url}/crm/v2"
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)
        self.per_page = config.get('per_page', 200)  # Max 200 for Zoho
        
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
                            raise ZohoCRMQuotaError("API rate limit exceeded")
                    
                    # Handle permission errors
                    if response.status == 403:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        error_msg = error_data.get('message', 'Permission denied')
                        raise ZohoCRMPermissionError(f"Permission denied: {error_msg}")
                    
                    # Handle validation errors
                    if response.status == 400:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        error_msg = error_data.get('message', 'Validation error')
                        raise ZohoCRMValidationError(f"Validation error: {error_msg}")
                    
                    # Handle other errors
                    if response.status >= 400:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        error_msg = error_data.get('message', f"HTTP {response.status}")
                        raise ZohoCRMAPIError(f"API request failed: {error_msg}")
                    
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
                    raise ZohoCRMConnectionError(f"Network error: {str(e)}")
        
        raise ZohoCRMConnectionError("Max retries exceeded")

    async def get_records(
        self,
        module: str,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        criteria: Optional[str] = None,
        converted: Optional[bool] = None,
        approved: Optional[bool] = None,
        territory_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get records from a Zoho CRM module.
        
        Args:
            module: Module name (Deals, Accounts, Contacts, etc.)
            fields: List of fields to retrieve
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
            page: Page number (1-based)
            per_page: Records per page (max 200)
            criteria: Search criteria
            converted: Filter by converted status
            approved: Filter by approval status
            territory_id: Territory ID filter
        
        Returns:
            Records data with metadata
        """
        url = f"{self.base_url}/{module}"
        params = {}
        
        if fields:
            params['fields'] = ','.join(fields)
        
        if sort_by:
            params['sort_by'] = sort_by
        
        if sort_order:
            params['sort_order'] = sort_order
        
        if page:
            params['page'] = str(page)
        
        if per_page:
            params['per_page'] = str(min(per_page, 200))
        else:
            params['per_page'] = str(self.per_page)
        
        if criteria:
            params['criteria'] = criteria
        
        if converted is not None:
            params['converted'] = 'true' if converted else 'false'
        
        if approved is not None:
            params['approved'] = 'true' if approved else 'false'
        
        if territory_id:
            params['territory_id'] = territory_id
        
        return await self._make_request('GET', url, params=params)

    async def get_record(
        self,
        module: str,
        record_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a single record by ID.
        
        Args:
            module: Module name
            record_id: Record ID
            fields: List of fields to retrieve
        
        Returns:
            Record data
        """
        url = f"{self.base_url}/{module}/{record_id}"
        params = {}
        
        if fields:
            params['fields'] = ','.join(fields)
        
        return await self._make_request('GET', url, params=params)

    async def create_records(
        self,
        module: str,
        records: List[Dict[str, Any]],
        trigger: Optional[List[str]] = None,
        lar_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create one or more records.
        
        Args:
            module: Module name
            records: List of record data
            trigger: Triggers to execute
            lar_id: Lead Assignment Rule ID
        
        Returns:
            Creation response
        """
        url = f"{self.base_url}/{module}"
        
        data = {'data': records}
        
        params = {}
        if trigger:
            params['trigger'] = ','.join(trigger)
        
        if lar_id:
            params['lar_id'] = lar_id
        
        return await self._make_request('POST', url, data=data, params=params)

    async def update_records(
        self,
        module: str,
        records: List[Dict[str, Any]],
        trigger: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update one or more records.
        
        Args:
            module: Module name
            records: List of record data with IDs
            trigger: Triggers to execute
        
        Returns:
            Update response
        """
        url = f"{self.base_url}/{module}"
        
        data = {'data': records}
        
        params = {}
        if trigger:
            params['trigger'] = ','.join(trigger)
        
        return await self._make_request('PUT', url, data=data, params=params)

    async def delete_records(
        self,
        module: str,
        record_ids: List[str],
        wf_trigger: bool = False
    ) -> Dict[str, Any]:
        """
        Delete one or more records.
        
        Args:
            module: Module name
            record_ids: List of record IDs to delete
            wf_trigger: Whether to trigger workflows
        
        Returns:
            Deletion response
        """
        url = f"{self.base_url}/{module}"
        
        params = {
            'ids': ','.join(record_ids)
        }
        
        if wf_trigger:
            params['wf_trigger'] = 'true'
        
        return await self._make_request('DELETE', url, params=params)

    async def search_records(
        self,
        module: str,
        criteria: str,
        fields: Optional[List[str]] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search records using criteria.
        
        Args:
            module: Module name
            criteria: Search criteria
            fields: List of fields to retrieve
            page: Page number
            per_page: Records per page
        
        Returns:
            Search results
        """
        url = f"{self.base_url}/{module}/search"
        
        params = {
            'criteria': criteria
        }
        
        if fields:
            params['fields'] = ','.join(fields)
        
        if page:
            params['page'] = str(page)
        
        if per_page:
            params['per_page'] = str(min(per_page, 200))
        
        return await self._make_request('GET', url, params=params)

    async def get_related_records(
        self,
        module: str,
        record_id: str,
        related_list: str,
        fields: Optional[List[str]] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get records related to a specific record.
        
        Args:
            module: Module name
            record_id: Parent record ID
            related_list: Related list name
            fields: List of fields to retrieve
            page: Page number
            per_page: Records per page
        
        Returns:
            Related records data
        """
        url = f"{self.base_url}/{module}/{record_id}/{related_list}"
        
        params = {}
        
        if fields:
            params['fields'] = ','.join(fields)
        
        if page:
            params['page'] = str(page)
        
        if per_page:
            params['per_page'] = str(min(per_page, 200))
        
        return await self._make_request('GET', url, params=params)

    async def get_module_metadata(self, module: str) -> Dict[str, Any]:
        """
        Get metadata for a specific module.
        
        Args:
            module: Module name
        
        Returns:
            Module metadata
        """
        url = f"{self.base_url}/settings/modules/{module}"
        return await self._make_request('GET', url)

    async def get_all_modules(self) -> Dict[str, Any]:
        """
        Get all available modules.
        
        Returns:
            List of modules
        """
        url = f"{self.base_url}/settings/modules"
        return await self._make_request('GET', url)

    async def get_fields(self, module: str) -> Dict[str, Any]:
        """
        Get fields for a specific module.
        
        Args:
            module: Module name
        
        Returns:
            Module fields
        """
        url = f"{self.base_url}/settings/fields"
        params = {'module': module}
        return await self._make_request('GET', url, params=params)

    async def get_layouts(self, module: str) -> Dict[str, Any]:
        """
        Get layouts for a specific module.
        
        Args:
            module: Module name
        
        Returns:
            Module layouts
        """
        url = f"{self.base_url}/settings/layouts"
        params = {'module': module}
        return await self._make_request('GET', url, params=params)

    async def bulk_read(
        self,
        module: str,
        job_id: Optional[str] = None,
        fields: Optional[List[str]] = None,
        criteria: Optional[str] = None,
        file_type: str = 'csv'
    ) -> Dict[str, Any]:
        """
        Perform bulk read operation.
        
        Args:
            module: Module name
            job_id: Existing job ID to check status
            fields: List of fields to export
            criteria: Export criteria
            file_type: File type (csv, ics)
        
        Returns:
            Bulk read response
        """
        if job_id:
            # Check job status
            url = f"{self.base_url}/bulk/read/{job_id}"
            return await self._make_request('GET', url)
        else:
            # Create bulk read job
            url = f"{self.base_url}/bulk/read"
            
            query = {
                'module': module,
                'file_type': file_type
            }
            
            if fields:
                query['fields'] = fields
            
            if criteria:
                query['criteria'] = criteria
            
            data = {'query': query}
            return await self._make_request('POST', url, data=data)

    async def bulk_write(
        self,
        operation: str,
        module: str,
        file_id: str,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform bulk write operation.
        
        Args:
            operation: Operation type (insert, update, upsert)
            module: Module name
            file_id: Uploaded file ID
            callback_url: Callback URL for notifications
        
        Returns:
            Bulk write response
        """
        url = f"{self.base_url}/bulk/write"
        
        data = {
            'operation': operation,
            'module': module,
            'file_id': file_id
        }
        
        if callback_url:
            data['callback'] = {'url': callback_url}
        
        return await self._make_request('POST', url, data=data)

    async def convert_lead(
        self,
        lead_id: str,
        conversion_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert a lead to account, contact, and deal.
        
        Args:
            lead_id: Lead ID to convert
            conversion_data: Conversion configuration
        
        Returns:
            Conversion response
        """
        url = f"{self.base_url}/Leads/{lead_id}/actions/convert"
        return await self._make_request('POST', url, data=conversion_data)

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None