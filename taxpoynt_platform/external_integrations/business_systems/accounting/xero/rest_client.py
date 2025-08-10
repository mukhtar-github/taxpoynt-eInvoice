"""
Xero Accounting REST Client
Handles HTTP communications with Xero Accounting API.
"""
import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode, quote

from .exceptions import (
    XeroConnectionError,
    XeroRateLimitError,
    XeroValidationError,
    XeroDataError,
    handle_xero_api_error
)
from .auth import XeroAuthManager


class XeroRestClient:
    """
    REST client for Xero Accounting API communication.
    
    Handles:
    - HTTP request/response management
    - Rate limiting and retry logic
    - Multi-tenant organization support
    - Error handling and exception mapping
    - Response data validation
    """
    
    API_BASE_URL = "https://api.xero.com/api.xro/2.0"
    
    def __init__(self, auth_manager: XeroAuthManager):
        """
        Initialize REST client.
        
        Args:
            auth_manager: Xero authentication manager
        """
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting (Xero: 60 calls per minute, 5000 per day per app)
        self.rate_limit_per_minute = 60
        self.rate_limit_per_day = 5000
        self.rate_limit_window = timedelta(minutes=1)
        self.daily_limit_reset = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Request tracking
        self.requests_this_minute = 0
        self.requests_today = 0
        self.minute_window_start = datetime.now()
        
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
                    'User-Agent': 'TaxPoynt-Xero-Integration/1.0'
                }
            )
    
    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _build_url(self, endpoint: str) -> str:
        """Build full API URL."""
        # Remove leading slash if present
        endpoint = endpoint.lstrip('/')
        return f"{self.API_BASE_URL}/{endpoint}"
    
    async def _check_rate_limits(self) -> None:
        """Check and enforce rate limits."""
        now = datetime.now()
        
        # Reset daily counter if new day
        if now >= self.daily_limit_reset:
            self.requests_today = 0
            self.daily_limit_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Reset minute counter if new minute window
        if now - self.minute_window_start >= self.rate_limit_window:
            self.requests_this_minute = 0
            self.minute_window_start = now
        
        # Check daily limit
        if self.requests_today >= self.rate_limit_per_day:
            wait_until = self.daily_limit_reset
            wait_seconds = (wait_until - now).total_seconds()
            self.logger.warning(f"Daily rate limit exceeded. Waiting {wait_seconds:.0f}s until reset.")
            raise XeroRateLimitError(
                "Daily API rate limit exceeded",
                retry_after=int(wait_seconds),
                daily_limit_exceeded=True
            )
        
        # Check minute limit
        if self.requests_this_minute >= self.rate_limit_per_minute:
            wait_until = self.minute_window_start + self.rate_limit_window
            wait_seconds = (wait_until - now).total_seconds()
            if wait_seconds > 0:
                self.logger.warning(f"Minute rate limit reached. Waiting {wait_seconds:.1f}s")
                await asyncio.sleep(wait_seconds)
                # Reset counters after wait
                self.requests_this_minute = 0
                self.minute_window_start = datetime.now()
    
    def _update_rate_limit_counters(self) -> None:
        """Update rate limit counters after successful request."""
        self.requests_this_minute += 1
        self.requests_today += 1
    
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
            XeroConnectionError: Connection issues
            XeroRateLimitError: Rate limit exceeded
            XeroValidationError: Validation errors
            XeroDataError: API errors
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
                if response.status == 200:
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
            raise XeroConnectionError(f"Connection failed after {self.max_retries} retries: {str(e)}")
    
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
            raise XeroDataError(f"Invalid JSON response: {text}")
    
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
            handle_xero_api_error(error_data, endpoint)
        except json.JSONDecodeError:
            raise XeroConnectionError("Authentication failed and unable to parse error response")
    
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
        retry_after = int(response.headers.get('Retry-After', 60))
        
        if retry_count < self.max_retries:
            self.logger.warning(f"Rate limited, waiting {retry_after}s before retry")
            await asyncio.sleep(retry_after)
            return await self._make_request(method, endpoint, params, json_data, retry_count + 1)
        
        raise XeroRateLimitError(
            "Rate limit exceeded and max retries reached",
            retry_after=retry_after
        )
    
    async def _handle_validation_error(self, response: aiohttp.ClientResponse, endpoint: str) -> None:
        """Handle validation errors."""
        try:
            error_data = await response.json()
            handle_xero_api_error(error_data, endpoint)
        except json.JSONDecodeError:
            text = await response.text()
            raise XeroValidationError(f"Validation error at {endpoint}: {text}")
    
    async def _handle_not_found_error(self, response: aiohttp.ClientResponse, endpoint: str) -> None:
        """Handle 404 not found errors."""
        try:
            error_data = await response.json()
            handle_xero_api_error(error_data, endpoint)
        except json.JSONDecodeError:
            raise XeroDataError(f"Resource not found: {endpoint}")
    
    async def _handle_error_response(self, response: aiohttp.ClientResponse, endpoint: str) -> None:
        """Handle other error responses."""
        try:
            error_data = await response.json()
            handle_xero_api_error(error_data, endpoint)
        except json.JSONDecodeError:
            text = await response.text()
            raise XeroDataError(f"API error {response.status} at {endpoint}: {text}")
    
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
    
    # Xero-specific methods
    
    async def get_organisation(self) -> Dict[str, Any]:
        """Get organisation information."""
        return await self.get("Organisation")
    
    async def get_invoices(
        self,
        where: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        include_archived: bool = False
    ) -> Dict[str, Any]:
        """
        Get invoices with optional filtering.
        
        Args:
            where: Xero where clause filter
            order: Order by clause
            page: Page number (1-based)
            include_archived: Include archived invoices
            
        Returns:
            Invoices response
        """
        params = {}
        
        if where:
            params['where'] = where
        if order:
            params['order'] = order
        if page:
            params['page'] = page
        if include_archived:
            params['includeArchived'] = 'true'
        
        return await self.get("Invoices", params=params)
    
    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Get specific invoice by ID."""
        return await self.get(f"Invoices/{invoice_id}")
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new invoice."""
        return await self.post("Invoices", invoice_data)
    
    async def update_invoice(self, invoice_id: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing invoice."""
        return await self.put(f"Invoices/{invoice_id}", invoice_data)
    
    async def get_contacts(
        self,
        where: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        include_archived: bool = False
    ) -> Dict[str, Any]:
        """
        Get contacts with optional filtering.
        
        Args:
            where: Xero where clause filter
            order: Order by clause
            page: Page number (1-based)
            include_archived: Include archived contacts
            
        Returns:
            Contacts response
        """
        params = {}
        
        if where:
            params['where'] = where
        if order:
            params['order'] = order
        if page:
            params['page'] = page
        if include_archived:
            params['includeArchived'] = 'true'
        
        return await self.get("Contacts", params=params)
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get specific contact by ID."""
        return await self.get(f"Contacts/{contact_id}")
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contact."""
        return await self.post("Contacts", contact_data)
    
    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact."""
        return await self.put(f"Contacts/{contact_id}", contact_data)
    
    async def get_accounts(self, where: Optional[str] = None, order: Optional[str] = None) -> Dict[str, Any]:
        """
        Get chart of accounts.
        
        Args:
            where: Xero where clause filter
            order: Order by clause
            
        Returns:
            Accounts response
        """
        params = {}
        
        if where:
            params['where'] = where
        if order:
            params['order'] = order
        
        return await self.get("Accounts", params=params)
    
    async def get_items(
        self,
        where: Optional[str] = None,
        order: Optional[str] = None,
        unit_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get items/products.
        
        Args:
            where: Xero where clause filter
            order: Order by clause
            unit_price: Filter by unit price
            
        Returns:
            Items response
        """
        params = {}
        
        if where:
            params['where'] = where
        if order:
            params['order'] = order
        if unit_price is not None:
            params['unitPrice'] = unit_price
        
        return await self.get("Items", params=params)
    
    async def get_tax_rates(self) -> Dict[str, Any]:
        """Get tax rates."""
        return await self.get("TaxRates")
    
    async def get_currencies(self) -> Dict[str, Any]:
        """Get currencies."""
        return await self.get("Currencies")
    
    async def get_branding_themes(self) -> Dict[str, Any]:
        """Get branding themes."""
        return await self.get("BrandingThemes")
    
    async def get_payments(
        self,
        where: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get payments.
        
        Args:
            where: Xero where clause filter
            order: Order by clause
            page: Page number (1-based)
            
        Returns:
            Payments response
        """
        params = {}
        
        if where:
            params['where'] = where
        if order:
            params['order'] = order
        if page:
            params['page'] = page
        
        return await self.get("Payments", params=params)
    
    async def get_credit_notes(
        self,
        where: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get credit notes.
        
        Args:
            where: Xero where clause filter
            order: Order by clause  
            page: Page number (1-based)
            
        Returns:
            Credit notes response
        """
        params = {}
        
        if where:
            params['where'] = where
        if order:
            params['order'] = order
        if page:
            params['page'] = page
        
        return await self.get("CreditNotes", params=params)
    
    async def get_bank_transactions(
        self,
        where: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get bank transactions.
        
        Args:
            where: Xero where clause filter
            order: Order by clause
            page: Page number (1-based)
            
        Returns:
            Bank transactions response
        """
        params = {}
        
        if where:
            params['where'] = where
        if order:
            params['order'] = order
        if page:
            params['page'] = page
        
        return await self.get("BankTransactions", params=params)
    
    # Batch operations
    
    async def batch_create_invoices(self, invoices_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple invoices in batch.
        
        Args:
            invoices_data: List of invoice data dictionaries
            
        Returns:
            Batch creation response
        """
        batch_data = {"Invoices": invoices_data}
        return await self.post("Invoices", batch_data)
    
    async def batch_create_contacts(self, contacts_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple contacts in batch.
        
        Args:
            contacts_data: List of contact data dictionaries
            
        Returns:
            Batch creation response
        """
        batch_data = {"Contacts": contacts_data}
        return await self.post("Contacts", batch_data)
    
    # Health and status methods
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return status."""
        try:
            org_data = await self.get_organisation()
            return {
                "status": "success",
                "connected": True,
                "organisation": org_data.get("Organisations", [{}])[0] if org_data.get("Organisations") else {},
                "rate_limits": {
                    "requests_this_minute": self.requests_this_minute,
                    "requests_today": self.requests_today,
                    "minute_limit": self.rate_limit_per_minute,
                    "daily_limit": self.rate_limit_per_day
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
            "requests_this_minute": self.requests_this_minute,
            "requests_today": self.requests_today,
            "minute_limit": self.rate_limit_per_minute,
            "daily_limit": self.rate_limit_per_day,
            "minute_window_start": self.minute_window_start.isoformat(),
            "daily_limit_reset": self.daily_limit_reset.isoformat(),
            "minute_remaining": max(0, self.rate_limit_per_minute - self.requests_this_minute),
            "daily_remaining": max(0, self.rate_limit_per_day - self.requests_today)
        }