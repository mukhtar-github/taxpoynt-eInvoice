"""
Pipedrive REST Client Module
Handles REST API communication for Pipedrive CRM services.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import aiohttp
import json

from .exceptions import (
    PipedriveAPIError,
    PipedriveConnectionError,
    PipedriveQuotaError,
    PipedrivePermissionError,
    PipedriveValidationError
)


class PipedriveRestClient:
    """
    REST client for Pipedrive API v1.
    Handles CRUD operations, search, filtering, and bulk operations.
    """

    def __init__(self, authenticator, config: Dict[str, Any]):
        """
        Initialize the Pipedrive REST client.
        
        Args:
            authenticator: PipedriveAuthenticator instance
            config: Configuration containing API settings
        """
        self.logger = logging.getLogger(__name__)
        self.authenticator = authenticator
        self.base_url = authenticator.base_url
        
        # API configuration
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)
        self.per_page = config.get('per_page', 500)  # Max 500 for Pipedrive
        
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
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with authentication and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            headers: Additional headers
        
        Returns:
            Response data as dictionary
        """
        session = await self._get_session()
        
        # Build URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Get authentication parameters and headers
        auth_params = self.authenticator.get_auth_params()
        auth_headers = self.authenticator.get_auth_headers()
        
        # Merge parameters
        if params:
            auth_params.update(params)
        
        # Merge headers
        if headers:
            auth_headers.update(headers)
        
        # Convert data to JSON if provided
        json_data = None
        if data:
            json_data = json.dumps(data)
            auth_headers['Content-Type'] = 'application/json'
        
        for attempt in range(self.max_retries + 1):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    params=auth_params,
                    data=json_data,
                    headers=auth_headers
                ) as response:
                    
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        if attempt < self.max_retries:
                            self.logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise PipedriveQuotaError("API rate limit exceeded")
                    
                    # Handle permission errors
                    if response.status == 403:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        error_msg = error_data.get('error', 'Permission denied')
                        raise PipedrivePermissionError(f"Permission denied: {error_msg}")
                    
                    # Handle validation errors
                    if response.status == 400:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        error_msg = error_data.get('error', 'Validation error')
                        raise PipedriveValidationError(f"Validation error: {error_msg}")
                    
                    # Handle other errors
                    if response.status >= 400:
                        error_data = await response.json() if response.content_type == 'application/json' else {}
                        error_msg = error_data.get('error', f"HTTP {response.status}")
                        raise PipedriveAPIError(f"API request failed: {error_msg}")
                    
                    # Handle successful responses
                    if response.status == 204:  # No Content
                        return {'success': True}
                    
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
                    raise PipedriveConnectionError(f"Network error: {str(e)}")
        
        raise PipedriveConnectionError("Max retries exceeded")

    async def get_deals(
        self,
        user_id: Optional[int] = None,
        filter_id: Optional[int] = None,
        stage_id: Optional[int] = None,
        status: Optional[str] = None,
        start: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
        owned_by_you: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get deals from Pipedrive.
        
        Args:
            user_id: User ID to filter by
            filter_id: Filter ID to apply
            stage_id: Stage ID to filter by
            status: Deal status (open, closed, all_not_deleted)
            start: Start index for pagination
            limit: Number of items to return
            sort: Sort order
            owned_by_you: Filter by ownership
        
        Returns:
            Deals data with metadata
        """
        params = {}
        
        if user_id:
            params['user_id'] = user_id
        
        if filter_id:
            params['filter_id'] = filter_id
        
        if stage_id:
            params['stage_id'] = stage_id
        
        if status:
            params['status'] = status
        
        if start:
            params['start'] = start
        
        if limit:
            params['limit'] = min(limit, self.per_page)
        else:
            params['limit'] = self.per_page
        
        if sort:
            params['sort'] = sort
        
        if owned_by_you is not None:
            params['owned_by_you'] = 1 if owned_by_you else 0
        
        return await self._make_request('GET', 'deals', params=params)

    async def get_deal(self, deal_id: int) -> Dict[str, Any]:
        """
        Get a single deal by ID.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            Deal data
        """
        return await self._make_request('GET', f'deals/{deal_id}')

    async def get_deal_products(self, deal_id: int) -> Dict[str, Any]:
        """
        Get products attached to a deal.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            Deal products data
        """
        return await self._make_request('GET', f'deals/{deal_id}/products')

    async def get_deal_activities(self, deal_id: int) -> Dict[str, Any]:
        """
        Get activities for a deal.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            Deal activities data
        """
        return await self._make_request('GET', f'deals/{deal_id}/activities')

    async def create_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new deal.
        
        Args:
            deal_data: Deal information
        
        Returns:
            Created deal data
        """
        return await self._make_request('POST', 'deals', data=deal_data)

    async def update_deal(self, deal_id: int, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a deal.
        
        Args:
            deal_id: Deal ID
            deal_data: Updated deal information
        
        Returns:
            Updated deal data
        """
        return await self._make_request('PUT', f'deals/{deal_id}', data=deal_data)

    async def delete_deal(self, deal_id: int) -> Dict[str, Any]:
        """
        Delete a deal.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            Deletion response
        """
        return await self._make_request('DELETE', f'deals/{deal_id}')

    async def search_deals(
        self,
        term: str,
        fields: Optional[str] = None,
        exact_match: Optional[bool] = None,
        person_id: Optional[int] = None,
        org_id: Optional[int] = None,
        status: Optional[str] = None,
        include_fields: Optional[str] = None,
        start: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search deals.
        
        Args:
            term: Search term
            fields: Fields to search in
            exact_match: Whether to use exact matching
            person_id: Person ID to filter by
            org_id: Organization ID to filter by
            status: Deal status
            include_fields: Additional fields to include
            start: Start index
            limit: Number of results
        
        Returns:
            Search results
        """
        params = {'term': term}
        
        if fields:
            params['fields'] = fields
        
        if exact_match is not None:
            params['exact_match'] = exact_match
        
        if person_id:
            params['person_id'] = person_id
        
        if org_id:
            params['org_id'] = org_id
        
        if status:
            params['status'] = status
        
        if include_fields:
            params['include_fields'] = include_fields
        
        if start:
            params['start'] = start
        
        if limit:
            params['limit'] = min(limit, self.per_page)
        
        return await self._make_request('GET', 'deals/search', params=params)

    async def get_persons(
        self,
        user_id: Optional[int] = None,
        filter_id: Optional[int] = None,
        first_char: Optional[str] = None,
        start: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get persons (contacts) from Pipedrive.
        
        Args:
            user_id: User ID to filter by
            filter_id: Filter ID to apply
            first_char: Filter by first character of name
            start: Start index for pagination
            limit: Number of items to return
            sort: Sort order
        
        Returns:
            Persons data
        """
        params = {}
        
        if user_id:
            params['user_id'] = user_id
        
        if filter_id:
            params['filter_id'] = filter_id
        
        if first_char:
            params['first_char'] = first_char
        
        if start:
            params['start'] = start
        
        if limit:
            params['limit'] = min(limit, self.per_page)
        else:
            params['limit'] = self.per_page
        
        if sort:
            params['sort'] = sort
        
        return await self._make_request('GET', 'persons', params=params)

    async def get_person(self, person_id: int) -> Dict[str, Any]:
        """
        Get a single person by ID.
        
        Args:
            person_id: Person ID
        
        Returns:
            Person data
        """
        return await self._make_request('GET', f'persons/{person_id}')

    async def get_organizations(
        self,
        user_id: Optional[int] = None,
        filter_id: Optional[int] = None,
        first_char: Optional[str] = None,
        start: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get organizations from Pipedrive.
        
        Args:
            user_id: User ID to filter by
            filter_id: Filter ID to apply
            first_char: Filter by first character of name
            start: Start index for pagination
            limit: Number of items to return
            sort: Sort order
        
        Returns:
            Organizations data
        """
        params = {}
        
        if user_id:
            params['user_id'] = user_id
        
        if filter_id:
            params['filter_id'] = filter_id
        
        if first_char:
            params['first_char'] = first_char
        
        if start:
            params['start'] = start
        
        if limit:
            params['limit'] = min(limit, self.per_page)
        else:
            params['limit'] = self.per_page
        
        if sort:
            params['sort'] = sort
        
        return await self._make_request('GET', 'organizations', params=params)

    async def get_organization(self, org_id: int) -> Dict[str, Any]:
        """
        Get a single organization by ID.
        
        Args:
            org_id: Organization ID
        
        Returns:
            Organization data
        """
        return await self._make_request('GET', f'organizations/{org_id}')

    async def get_products(
        self,
        user_id: Optional[int] = None,
        filter_id: Optional[int] = None,
        first_char: Optional[str] = None,
        start: Optional[int] = None,
        limit: Optional[int] = None,
        include_fields: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get products from Pipedrive.
        
        Args:
            user_id: User ID to filter by
            filter_id: Filter ID to apply
            first_char: Filter by first character of name
            start: Start index for pagination
            limit: Number of items to return
            include_fields: Additional fields to include
        
        Returns:
            Products data
        """
        params = {}
        
        if user_id:
            params['user_id'] = user_id
        
        if filter_id:
            params['filter_id'] = filter_id
        
        if first_char:
            params['first_char'] = first_char
        
        if start:
            params['start'] = start
        
        if limit:
            params['limit'] = min(limit, self.per_page)
        else:
            params['limit'] = self.per_page
        
        if include_fields:
            params['include_fields'] = include_fields
        
        return await self._make_request('GET', 'products', params=params)

    async def get_activities(
        self,
        user_id: Optional[int] = None,
        filter_id: Optional[int] = None,
        type_: Optional[str] = None,
        start: Optional[int] = None,
        limit: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        done: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get activities from Pipedrive.
        
        Args:
            user_id: User ID to filter by
            filter_id: Filter ID to apply
            type_: Activity type
            start: Start index for pagination
            limit: Number of items to return
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            done: Filter by completion status
        
        Returns:
            Activities data
        """
        params = {}
        
        if user_id:
            params['user_id'] = user_id
        
        if filter_id:
            params['filter_id'] = filter_id
        
        if type_:
            params['type'] = type_
        
        if start:
            params['start'] = start
        
        if limit:
            params['limit'] = min(limit, self.per_page)
        else:
            params['limit'] = self.per_page
        
        if start_date:
            params['start_date'] = start_date
        
        if end_date:
            params['end_date'] = end_date
        
        if done is not None:
            params['done'] = 1 if done else 0
        
        return await self._make_request('GET', 'activities', params=params)

    async def get_notes(
        self,
        user_id: Optional[int] = None,
        deal_id: Optional[int] = None,
        person_id: Optional[int] = None,
        org_id: Optional[int] = None,
        start: Optional[int] = None,
        limit: Optional[int] = None,
        sort: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        pinned_to_deal_flag: Optional[bool] = None,
        pinned_to_organization_flag: Optional[bool] = None,
        pinned_to_person_flag: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get notes from Pipedrive.
        
        Args:
            user_id: User ID to filter by
            deal_id: Deal ID to filter by
            person_id: Person ID to filter by
            org_id: Organization ID to filter by
            start: Start index for pagination
            limit: Number of items to return
            sort: Sort order
            start_date: Start date filter
            end_date: End date filter
            pinned_to_deal_flag: Filter by deal pinning
            pinned_to_organization_flag: Filter by org pinning
            pinned_to_person_flag: Filter by person pinning
        
        Returns:
            Notes data
        """
        params = {}
        
        if user_id:
            params['user_id'] = user_id
        
        if deal_id:
            params['deal_id'] = deal_id
        
        if person_id:
            params['person_id'] = person_id
        
        if org_id:
            params['org_id'] = org_id
        
        if start:
            params['start'] = start
        
        if limit:
            params['limit'] = min(limit, self.per_page)
        else:
            params['limit'] = self.per_page
        
        if sort:
            params['sort'] = sort
        
        if start_date:
            params['start_date'] = start_date
        
        if end_date:
            params['end_date'] = end_date
        
        if pinned_to_deal_flag is not None:
            params['pinned_to_deal_flag'] = 1 if pinned_to_deal_flag else 0
        
        if pinned_to_organization_flag is not None:
            params['pinned_to_organization_flag'] = 1 if pinned_to_organization_flag else 0
        
        if pinned_to_person_flag is not None:
            params['pinned_to_person_flag'] = 1 if pinned_to_person_flag else 0
        
        return await self._make_request('GET', 'notes', params=params)

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None