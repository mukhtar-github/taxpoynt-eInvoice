"""
Sage Business Cloud Accounting REST Client
Handles HTTP communications with Sage Business Cloud Accounting API.
"""
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode, quote

from .exceptions import (
    SageConnectionError,
    SageRateLimitError,
    SageValidationError,
    SageDataError,
    handle_sage_api_error
)
from .auth import SageAuthManager


class SageRestClient:
    """
    REST client for Sage Business Cloud Accounting API communication.
    
    Handles:
    - HTTP request/response management
    - Rate limiting and retry logic
    - Business-scoped API requests
    - Error handling and exception mapping
    - Response data validation
    """
    
    def __init__(self, auth_manager: SageAuthManager):
        """
        Initialize REST client.
        
        Args:
            auth_manager: Sage authentication manager
        """
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting (Sage: 5000 calls per hour per business)
        self.rate_limit_per_hour = 5000
        self.rate_limit_window = timedelta(hours=1)
        self.hour_window_start = datetime.now()
        
        # Request tracking
        self.requests_this_hour = 0
        
        # Retry configuration
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
            timeout = aiohttp.ClientTimeout(total=60, connect=15)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'TaxPoynt-Sage-Integration/1.0'
                }
            )
    
    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _build_url(self, endpoint: str) -> str:
        """Build full business-specific API URL."""
        # Remove leading slash if present
        endpoint = endpoint.lstrip('/')
        return self.auth_manager.get_business_url(endpoint)
    
    async def _check_rate_limits(self) -> None:
        """Check and enforce rate limits."""
        now = datetime.now()
        
        # Reset hour counter if new hour window
        if now - self.hour_window_start >= self.rate_limit_window:
            self.requests_this_hour = 0
            self.hour_window_start = now
        
        # Check hourly limit
        if self.requests_this_hour >= self.rate_limit_per_hour:
            wait_until = self.hour_window_start + self.rate_limit_window
            wait_seconds = (wait_until - now).total_seconds()
            self.logger.warning(f"Hourly rate limit exceeded. Waiting {wait_seconds:.0f}s until reset.")
            raise SageRateLimitError(
                "Hourly API rate limit exceeded",
                retry_after=int(wait_seconds),
                quota_exceeded=True
            )
    
    def _update_rate_limit_counters(self) -> None:
        """Update rate limit counters after successful request."""
        self.requests_this_hour += 1
    
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
            SageConnectionError: Connection issues
            SageRateLimitError: Rate limit exceeded
            SageValidationError: Validation errors
            SageDataError: API errors
        """
        if not self.session:
            await self.connect()
        
        # Check rate limits before making request
        await self._check_rate_limits()
        
        # Get authentication headers
        auth_headers = await self.auth_manager.get_auth_headers()
        
        # Build request
        url = self._build_url(endpoint)
        headers = {
            **auth_headers,
            'Accept': 'application/json'
        }
        
        # Add content type for POST/PUT requests
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
                
                # Update rate limit counters for successful request
                self._update_rate_limit_counters()
                
                # Handle different status codes
                if response.status in [200, 201]:
                    return await self._handle_success_response(response)
                elif response.status == 401:
                    return await self._handle_auth_error(response, method, endpoint, params, json_data, retry_count)
                elif response.status == 429:
                    return await self._handle_rate_limit_response(response, method, endpoint, params, json_data, retry_count)
                elif response.status in [400, 422]:
                    await self._handle_validation_error(response, endpoint)
                elif response.status == 404:
                    await self._handle_not_found_error(response, endpoint)
                else:
                    await self._handle_error_response(response, endpoint)
        
        except aiohttp.ClientError as e:
            if retry_count < self.max_retries:
                wait_time = self.retry_delay * (2 ** retry_count)
                self.logger.warning(f"Request failed, retrying in {wait_time}s: {str(e)}")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, params, json_data, retry_count + 1)
            raise SageConnectionError(f"Connection failed after {self.max_retries} retries: {str(e)}")
    
    async def _handle_success_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle successful response."""
        try:
            data = await response.json()
            return data
        except json.JSONDecodeError:
            text = await response.text()
            if not text.strip():
                # Empty response is valid for some operations (like DELETE)
                return {}
            raise SageDataError(f"Invalid JSON response: {text}")
    
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
        if retry_count < 1:  # Only retry once for auth errors
            try:
                self.logger.info("Attempting to refresh access token")
                await self.auth_manager.refresh_access_token()
                return await self._make_request(method, endpoint, params, json_data, retry_count + 1)
            except Exception as e:
                self.logger.error(f"Token refresh failed: {str(e)}")
        
        # If refresh failed or max retries reached
        try:
            error_data = await response.json()
            handle_sage_api_error(error_data, endpoint)
        except json.JSONDecodeError:
            raise SageConnectionError("Authentication failed and unable to parse error response")
    
    async def _handle_rate_limit_response(
        self,
        response: aiohttp.ClientResponse,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        json_data: Optional[Dict[str, Any]],
        retry_count: int
    ) -> Dict[str, Any]:
        """Handle rate limit responses with retry."""
        retry_after = int(response.headers.get('Retry-After', 300))  # Default 5 minutes
        
        if retry_count < self.max_retries:
            self.logger.warning(f"Rate limited, waiting {retry_after}s before retry")
            await asyncio.sleep(retry_after)
            return await self._make_request(method, endpoint, params, json_data, retry_count + 1)
        
        raise SageRateLimitError(
            "Rate limit exceeded and max retries reached",
            retry_after=retry_after
        )
    
    async def _handle_validation_error(self, response: aiohttp.ClientResponse, endpoint: str) -> None:
        """Handle validation errors."""
        try:
            error_data = await response.json()
            handle_sage_api_error(error_data, endpoint)
        except json.JSONDecodeError:
            text = await response.text()
            raise SageValidationError(f"Validation error at {endpoint}: {text}")
    
    async def _handle_not_found_error(self, response: aiohttp.ClientResponse, endpoint: str) -> None:
        """Handle 404 not found errors."""
        try:
            error_data = await response.json()
            handle_sage_api_error(error_data, endpoint)
        except json.JSONDecodeError:
            raise SageDataError(f"Resource not found: {endpoint}")
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse, endpoint: str) -> None:
        """Handle other error responses."""
        try:
            error_data = await response.json()
            handle_sage_api_error(error_data, endpoint)
        except json.JSONDecodeError:
            text = await response.text()
            raise SageDataError(f"API error {response.status} at {endpoint}: {text}")
    
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
    
    # Sage-specific methods
    
    async def get_business_info(self) -> Dict[str, Any]:
        """Get business information."""
        return await self.get("")  # Business root endpoint
    
    async def get_sales_invoices(
        self,
        attributes: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search: Optional[str] = None,
        items_per_page: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get sales invoices with optional filtering.
        
        Args:
            attributes: Comma-separated list of attributes to include
            from_date: Filter invoices from this date
            to_date: Filter invoices to this date
            search: Search term
            items_per_page: Number of items per page (max 200)
            page: Page number (1-based)
            
        Returns:
            Sales invoices response
        """
        params = {
            'items_per_page': min(items_per_page, 200),
            'page': page
        }
        
        if attributes:
            params['attributes'] = attributes
        if from_date:
            params['from_date'] = from_date.strftime('%Y-%m-%d')
        if to_date:
            params['to_date'] = to_date.strftime('%Y-%m-%d')
        if search:
            params['search'] = search
        
        return await self.get("sales_invoices", params=params)
    
    async def get_sales_invoice(self, invoice_id: str, attributes: Optional[str] = None) -> Dict[str, Any]:
        """
        Get specific sales invoice by ID.
        
        Args:
            invoice_id: Sales invoice ID
            attributes: Comma-separated list of attributes to include
            
        Returns:
            Sales invoice data
        """
        params = {}
        if attributes:
            params['attributes'] = attributes
        
        return await self.get(f"sales_invoices/{invoice_id}", params=params)
    
    async def create_sales_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new sales invoice."""
        return await self.post("sales_invoices", invoice_data)
    
    async def update_sales_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing sales invoice."""
        return await self.put(f"sales_invoices/{invoice_id}", invoice_data)
    
    async def get_contacts(
        self,
        attributes: Optional[str] = None,
        contact_type: Optional[str] = None,
        search: Optional[str] = None,
        items_per_page: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get contacts with optional filtering.
        
        Args:
            attributes: Comma-separated list of attributes to include
            contact_type: Filter by contact type (Customer, Vendor, etc.)
            search: Search term
            items_per_page: Number of items per page (max 200)
            page: Page number (1-based)
            
        Returns:
            Contacts response
        """
        params = {
            'items_per_page': min(items_per_page, 200),
            'page': page
        }
        
        if attributes:
            params['attributes'] = attributes
        if contact_type:
            params['contact_type'] = contact_type
        if search:
            params['search'] = search
        
        return await self.get("contacts", params=params)
    
    async def get_contact(self, contact_id: str, attributes: Optional[str] = None) -> Dict[str, Any]:
        """
        Get specific contact by ID.
        
        Args:
            contact_id: Contact ID
            attributes: Comma-separated list of attributes to include
            
        Returns:
            Contact data
        """
        params = {}
        if attributes:
            params['attributes'] = attributes
        
        return await self.get(f"contacts/{contact_id}", params=params)
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contact."""
        return await self.post("contacts", contact_data)
    
    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact."""
        return await self.put(f"contacts/{contact_id}", contact_data)
    
    async def get_ledger_accounts(
        self,
        attributes: Optional[str] = None,
        search: Optional[str] = None,
        items_per_page: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get ledger accounts (chart of accounts).
        
        Args:
            attributes: Comma-separated list of attributes to include
            search: Search term
            items_per_page: Number of items per page (max 200)
            page: Page number (1-based)
            
        Returns:
            Ledger accounts response
        """
        params = {
            'items_per_page': min(items_per_page, 200),
            'page': page
        }
        
        if attributes:
            params['attributes'] = attributes
        if search:
            params['search'] = search
        
        return await self.get("ledger_accounts", params=params)
    
    async def get_tax_rates(
        self,
        attributes: Optional[str] = None,
        items_per_page: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get tax rates.
        
        Args:
            attributes: Comma-separated list of attributes to include
            items_per_page: Number of items per page (max 200)
            page: Page number (1-based)
            
        Returns:
            Tax rates response
        """
        params = {
            'items_per_page': min(items_per_page, 200),
            'page': page
        }
        
        if attributes:
            params['attributes'] = attributes
        
        return await self.get("tax_rates", params=params)
    
    async def get_products(
        self,
        attributes: Optional[str] = None,
        product_type: Optional[str] = None,
        search: Optional[str] = None,
        items_per_page: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get products/services.
        
        Args:
            attributes: Comma-separated list of attributes to include
            product_type: Filter by product type
            search: Search term
            items_per_page: Number of items per page (max 200)
            page: Page number (1-based)
            
        Returns:
            Products response
        """
        params = {
            'items_per_page': min(items_per_page, 200),
            'page': page
        }
        
        if attributes:
            params['attributes'] = attributes
        if product_type:
            params['product_type'] = product_type
        if search:
            params['search'] = search
        
        return await self.get("products", params=params)
    
    async def get_credit_notes(
        self,
        attributes: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search: Optional[str] = None,
        items_per_page: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get sales credit notes.
        
        Args:
            attributes: Comma-separated list of attributes to include
            from_date: Filter credit notes from this date
            to_date: Filter credit notes to this date
            search: Search term
            items_per_page: Number of items per page (max 200)
            page: Page number (1-based)
            
        Returns:
            Credit notes response
        """
        params = {
            'items_per_page': min(items_per_page, 200),
            'page': page
        }
        
        if attributes:
            params['attributes'] = attributes
        if from_date:
            params['from_date'] = from_date.strftime('%Y-%m-%d')
        if to_date:
            params['to_date'] = to_date.strftime('%Y-%m-%d')
        if search:
            params['search'] = search
        
        return await self.get("sales_credit_notes", params=params)
    
    async def get_purchase_invoices(
        self,
        attributes: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        search: Optional[str] = None,
        items_per_page: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get purchase invoices.
        
        Args:
            attributes: Comma-separated list of attributes to include
            from_date: Filter invoices from this date
            to_date: Filter invoices to this date
            search: Search term
            items_per_page: Number of items per page (max 200)
            page: Page number (1-based)
            
        Returns:
            Purchase invoices response
        """
        params = {
            'items_per_page': min(items_per_page, 200),
            'page': page
        }
        
        if attributes:
            params['attributes'] = attributes
        if from_date:
            params['from_date'] = from_date.strftime('%Y-%m-%d')
        if to_date:
            params['to_date'] = to_date.strftime('%Y-%m-%d')
        if search:
            params['search'] = search
        
        return await self.get("purchase_invoices", params=params)
    
    # Pagination helpers
    
    async def get_all_pages(
        self,
        endpoint_method,
        *args,
        max_pages: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get all pages of paginated data.
        
        Args:
            endpoint_method: Method to call for each page
            *args: Method positional arguments
            max_pages: Maximum number of pages to fetch (None for all)
            **kwargs: Method keyword arguments
            
        Returns:
            List of all items from all pages
        """
        all_items = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
            
            # Set page parameter
            kwargs['page'] = page
            
            try:
                result = await endpoint_method(*args, **kwargs)
                items = result.get('$items', [])
                
                if not items:
                    break
                
                all_items.extend(items)
                
                # Check if there are more pages
                total = result.get('$total', 0)
                items_per_page = kwargs.get('items_per_page', 20)
                
                if len(all_items) >= total or len(items) < items_per_page:
                    break
                
                page += 1
                
            except Exception as e:
                self.logger.error(f"Error fetching page {page}: {str(e)}")
                break
        
        return all_items
    
    # Health and status methods
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return status."""
        try:
            business_data = await self.get_business_info()
            return {
                "status": "success",
                "connected": True,
                "business": business_data,
                "rate_limits": {
                    "requests_this_hour": self.requests_this_hour,
                    "hourly_limit": self.rate_limit_per_hour,
                    "window_start": self.hour_window_start.isoformat()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return {
            "requests_this_hour": self.requests_this_hour,
            "hourly_limit": self.rate_limit_per_hour,
            "window_start": self.hour_window_start.isoformat(),
            "remaining": max(0, self.rate_limit_per_hour - self.requests_this_hour),
            "reset_time": (self.hour_window_start + self.rate_limit_window).isoformat()
        }