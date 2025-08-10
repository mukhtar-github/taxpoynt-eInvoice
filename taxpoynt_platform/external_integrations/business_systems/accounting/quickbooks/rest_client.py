"""
QuickBooks Accounting REST Client
Handles HTTP communications with QuickBooks Online API.
"""
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode, quote

from .exceptions import (
    QuickBooksConnectionError,
    QuickBooksRateLimitError,
    QuickBooksValidationError,
    QuickBooksDataError
)
from .auth import QuickBooksAuthManager


class QuickBooksRestClient:
    """
    REST client for QuickBooks Online API communication.
    
    Handles:
    - HTTP request/response management
    - Rate limiting and retry logic
    - Error handling and exception mapping
    - Response data validation
    """
    
    BASE_URL = "https://sandbox-quickbooks.api.intuit.com"  # Use production URL for live
    API_VERSION = "v3"
    
    def __init__(self, auth_manager: QuickBooksAuthManager, company_id: str):
        """
        Initialize REST client.
        
        Args:
            auth_manager: QuickBooks authentication manager
            company_id: QuickBooks company ID
        """
        self.auth_manager = auth_manager
        self.company_id = company_id
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self.rate_limit_remaining = 500  # QuickBooks default
        self.rate_limit_reset = datetime.now() + timedelta(minutes=1)
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Initialize HTTP session."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'Accept': 'application/json'}
            )
    
    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _build_url(self, endpoint: str) -> str:
        """Build full API URL."""
        return f"{self.BASE_URL}/{self.API_VERSION}/company/{self.company_id}/{endpoint}"
    
    async def _check_rate_limit(self) -> None:
        """Check and handle rate limiting."""
        if datetime.now() > self.rate_limit_reset:
            self.rate_limit_remaining = 500  # Reset limit
            self.rate_limit_reset = datetime.now() + timedelta(minutes=1)
        
        if self.rate_limit_remaining <= 1:
            wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
            if wait_time > 0:
                self.logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
    
    def _update_rate_limit(self, headers: Dict[str, str]) -> None:
        """Update rate limit tracking from response headers."""
        if 'intuit_tid' in headers:  # QuickBooks transaction ID
            self.rate_limit_remaining -= 1
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request with error handling and retries.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: Request JSON body
            retry_count: Current retry attempt
            
        Returns:
            Response data
            
        Raises:
            QuickBooksConnectionError: Connection issues
            QuickBooksRateLimitError: Rate limit exceeded
            QuickBooksValidationError: Validation errors
            QuickBooksDataError: API errors
        """
        if not self.session:
            await self.connect()
        
        await self._check_rate_limit()
        
        # Get authentication headers
        auth_headers = await self.auth_manager.get_auth_headers()
        
        # Build request
        url = self._build_url(endpoint)
        headers = {
            **auth_headers,
            'Accept': 'application/json'
        }
        
        if json_data:
            headers['Content-Type'] = 'application/json'
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers
            ) as response:
                
                self._update_rate_limit(dict(response.headers))
                
                # Handle different status codes
                if response.status == 200:
                    return await self._handle_success_response(response)
                elif response.status == 401:
                    return await self._handle_auth_error(response, method, endpoint, params, json_data, retry_count)
                elif response.status == 429:
                    return await self._handle_rate_limit(response, method, endpoint, params, json_data, retry_count)
                elif response.status in [400, 422]:
                    await self._handle_validation_error(response)
                else:
                    await self._handle_error_response(response)
        
        except aiohttp.ClientError as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2 ** retry_count))
                return await self._make_request(method, endpoint, params, json_data, retry_count + 1)
            raise QuickBooksConnectionError(f"Connection failed: {str(e)}")
    
    async def _handle_success_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle successful response."""
        try:
            data = await response.json()
            return data
        except json.JSONDecodeError:
            text = await response.text()
            raise QuickBooksDataError(f"Invalid JSON response: {text}")
    
    async def _handle_auth_error(
        self,
        response: aiohttp.ClientResponse,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        retry_count: int
    ) -> Dict[str, Any]:
        """Handle authentication errors with token refresh."""
        if retry_count < self.max_retries:
            try:
                await self.auth_manager.refresh_token()
                return await self._make_request(method, endpoint, params, json_data, retry_count + 1)
            except Exception as e:
                raise QuickBooksConnectionError(f"Token refresh failed: {str(e)}")
        
        error_data = await response.json() if response.content_type == 'application/json' else {}
        raise QuickBooksConnectionError(f"Authentication failed: {error_data}")
    
    async def _handle_rate_limit(
        self,
        response: aiohttp.ClientResponse,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        retry_count: int
    ) -> Dict[str, Any]:
        """Handle rate limiting with exponential backoff."""
        if retry_count < self.max_retries:
            retry_after = int(response.headers.get('Retry-After', 60))
            await asyncio.sleep(retry_after)
            return await self._make_request(method, endpoint, params, json_data, retry_count + 1)
        
        raise QuickBooksRateLimitError("Rate limit exceeded and max retries reached")
    
    async def _handle_validation_error(self, response: aiohttp.ClientResponse) -> None:
        """Handle validation errors."""
        try:
            error_data = await response.json()
            fault = error_data.get('Fault', {})
            errors = fault.get('Error', [])
            
            if errors:
                error_messages = [err.get('Detail', 'Unknown validation error') for err in errors]
                raise QuickBooksValidationError("; ".join(error_messages))
            else:
                raise QuickBooksValidationError("Validation failed")
        except json.JSONDecodeError:
            text = await response.text()
            raise QuickBooksValidationError(f"Validation error: {text}")
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse) -> None:
        """Handle other error responses."""
        try:
            error_data = await response.json()
            fault = error_data.get('Fault', {})
            errors = fault.get('Error', [])
            
            if errors:
                error_messages = [err.get('Detail', 'Unknown error') for err in errors]
                raise QuickBooksDataError("; ".join(error_messages))
            else:
                raise QuickBooksDataError(f"API error: {response.status}")
        except json.JSONDecodeError:
            text = await response.text()
            raise QuickBooksDataError(f"API error {response.status}: {text}")
    
    # CRUD Operations
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request."""
        return await self._make_request("POST", endpoint, json_data=data)
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request."""
        return await self._make_request("PUT", endpoint, json_data=data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self._make_request("DELETE", endpoint)
    
    # QuickBooks-specific methods
    
    async def query(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute QuickBooks SQL query.
        
        Args:
            sql_query: SQL query string
            
        Returns:
            Query results
        """
        params = {'query': sql_query}
        return await self.get("query", params=params)
    
    async def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """
        Get specific entity by ID.
        
        Args:
            entity_type: Type of entity (customer, item, invoice, etc.)
            entity_id: Entity ID
            
        Returns:
            Entity data
        """
        endpoint = f"{entity_type}/{entity_id}"
        return await self.get(endpoint)
    
    async def create_entity(self, entity_type: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new entity.
        
        Args:
            entity_type: Type of entity
            entity_data: Entity data
            
        Returns:
            Created entity data
        """
        return await self.post(entity_type, entity_data)
    
    async def update_entity(self, entity_type: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing entity.
        
        Args:
            entity_type: Type of entity
            entity_data: Updated entity data (must include Id and SyncToken)
            
        Returns:
            Updated entity data
        """
        return await self.post(entity_type, entity_data)
    
    async def delete_entity(self, entity_type: str, entity_id: str, sync_token: str) -> Dict[str, Any]:
        """
        Delete entity (soft delete).
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            sync_token: Current sync token
            
        Returns:
            Deletion result
        """
        params = {
            'operation': 'delete',
            'include': 'void'
        }
        entity_data = {
            "Id": entity_id,
            "SyncToken": sync_token
        }
        return await self.post(entity_type, entity_data)
    
    async def get_company_info(self) -> Dict[str, Any]:
        """Get company information."""
        return await self.get("companyinfo/1")
    
    async def get_items(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all items."""
        query = "SELECT * FROM Item"
        if active_only:
            query += " WHERE Active = true"
        
        result = await self.query(query)
        return result.get('QueryResponse', {}).get('Item', [])
    
    async def get_customers(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all customers."""
        query = "SELECT * FROM Customer"
        if active_only:
            query += " WHERE Active = true"
        
        result = await self.query(query)
        return result.get('QueryResponse', {}).get('Customer', [])
    
    async def get_invoices(self, start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get invoices, optionally filtered by date."""
        query = "SELECT * FROM Invoice"
        if start_date:
            query += f" WHERE TxnDate >= '{start_date.strftime('%Y-%m-%d')}'"
        query += " ORDER BY TxnDate DESC"
        
        result = await self.query(query)
        return result.get('QueryResponse', {}).get('Invoice', [])
    
    async def batch_request(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute batch operations.
        
        Args:
            operations: List of batch operations
            
        Returns:
            Batch results
        """
        batch_data = {
            "BatchItemRequest": operations
        }
        return await self.post("batch", batch_data)