"""
FreshBooks REST API Client
Handles all HTTP communication with FreshBooks REST API.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .auth import FreshBooksAuthManager
from .exceptions import (
    FreshBooksAPIError,
    FreshBooksConnectionError,
    FreshBooksRateLimitError,
    FreshBooksAuthenticationError,
    FreshBooksMaintenanceError,
    FreshBooksAccountNotFoundError,
    FreshBooksClientNotFoundError,
    FreshBooksInvoiceNotFoundError,
    FreshBooksItemNotFoundError
)


logger = logging.getLogger(__name__)


class FreshBooksRestClient:
    """
    REST client for FreshBooks API.
    
    FreshBooks uses REST API with JSON responses.
    Handles authentication, rate limiting, and error handling.
    """
    
    # FreshBooks API endpoints
    SANDBOX_BASE_URL = "https://api.freshbooks.com"
    PRODUCTION_BASE_URL = "https://api.freshbooks.com"
    
    # API version
    API_VERSION = "accounting"
    
    # Rate limiting settings
    MAX_REQUESTS_PER_MINUTE = 300  # FreshBooks allows 300 requests per minute
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    def __init__(
        self,
        auth_manager: FreshBooksAuthManager,
        session: Optional[ClientSession] = None,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize FreshBooks REST client.
        
        Args:
            auth_manager: FreshBooks authentication manager
            session: Optional aiohttp session
            max_retries: Maximum number of retry attempts
        """
        self.auth_manager = auth_manager
        self.session = session
        self.should_close_session = session is None
        self.max_retries = max_retries
        
        self.base_url = (
            self.SANDBOX_BASE_URL if auth_manager.sandbox 
            else self.PRODUCTION_BASE_URL
        )
        
        # Rate limiting
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.session is None:
            timeout = ClientTimeout(total=60, connect=10)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": "TaxPoynt-FreshBooks-Integration/1.0"}
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.should_close_session and self.session:
            await self.session.close()
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        async with self._rate_limit_lock:
            now = datetime.utcnow()
            # Remove requests older than 1 minute
            cutoff = now - timedelta(minutes=1)
            self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Check if we're at rate limit
            if len(self._request_times) >= self.MAX_REQUESTS_PER_MINUTE:
                sleep_time = 60 - (now - self._request_times[0]).total_seconds()
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                # Clean up old requests again after sleeping
                now = datetime.utcnow()
                cutoff = now - timedelta(minutes=1)
                self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Record this request
            self._request_times.append(now)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        account_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to FreshBooks API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            account_id: FreshBooks account ID (required for most endpoints)
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data
        """
        if not self.session:
            raise FreshBooksConnectionError("No HTTP session available")
        
        await self._rate_limit_check()
        
        # Ensure we have a valid token
        token = await self.auth_manager.ensure_valid_token()
        
        # Use account ID from auth manager if not provided
        if not account_id:
            account_id = self.auth_manager.get_account_id()
        
        if not account_id and endpoint != "users/me":
            raise FreshBooksAccountNotFoundError("Account ID is required for this operation")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Build URL
        if account_id and endpoint != "users/me":
            url = f"{self.base_url}/{self.API_VERSION}/account/{account_id}/{endpoint}"
        else:
            url = f"{self.base_url}/auth/api/v1/{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                kwargs = {
                    "headers": headers,
                    "params": params
                }
                
                if data:
                    kwargs["json"] = data
                
                async with self.session.request(method, url, **kwargs) as response:
                    response_data = await response.json()
                    
                    # Handle HTTP errors
                    if response.status == 401:
                        raise FreshBooksAuthenticationError("Authentication failed")
                    elif response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise FreshBooksRateLimitError(
                            "Rate limit exceeded", 
                            retry_after=retry_after
                        )
                    elif response.status == 503:
                        raise FreshBooksMaintenanceError("FreshBooks API is under maintenance")
                    elif response.status >= 400:
                        # Extract error message from FreshBooks response
                        error_msg = "Unknown error"
                        if "response" in response_data and "errors" in response_data["response"]:
                            errors = response_data["response"]["errors"]
                            if errors:
                                error_msg = errors[0].get("message", "Unknown error")
                        
                        raise FreshBooksAPIError(
                            f"HTTP {response.status}: {error_msg}",
                            status_code=response.status,
                            response_data=response_data
                        )
                    
                    return response_data
                    
            except FreshBooksRateLimitError as e:
                if attempt < self.max_retries:
                    sleep_time = e.retry_after or (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {sleep_time} seconds")
                    await asyncio.sleep(sleep_time)
                    continue
                raise
            except (ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries:
                    sleep_time = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {sleep_time} seconds: {e}")
                    await asyncio.sleep(sleep_time)
                    continue
                raise FreshBooksConnectionError(f"Failed to connect to FreshBooks API: {str(e)}")
        
        raise FreshBooksConnectionError("Max retries exceeded")
    
    async def get_clients(
        self,
        account_id: Optional[str] = None,
        per_page: int = 50,
        page: int = 1,
        updated_since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get clients from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            per_page: Number of clients per page
            page: Page number
            updated_since: Only return clients updated since this date
            
        Returns:
            Clients response with pagination info
        """
        params = {
            "per_page": min(per_page, 100),  # FreshBooks limits to 100 per page
            "page": page
        }
        
        if updated_since:
            params["updated_since"] = updated_since.isoformat()
        
        response = await self._make_request("GET", "users/clients", account_id, params=params)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"]
    
    async def get_client(self, client_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a specific client by ID.
        
        Args:
            client_id: FreshBooks client ID
            account_id: FreshBooks account ID
            
        Returns:
            Client object
        """
        response = await self._make_request("GET", f"users/clients/{client_id}", account_id)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        client = response["response"]
        if not client:
            raise FreshBooksClientNotFoundError(f"Client {client_id} not found")
        
        return client
    
    async def get_items(
        self,
        account_id: Optional[str] = None,
        per_page: int = 50,
        page: int = 1,
        updated_since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get items from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            per_page: Number of items per page
            page: Page number
            updated_since: Only return items updated since this date
            
        Returns:
            Items response with pagination info
        """
        params = {
            "per_page": min(per_page, 100),
            "page": page
        }
        
        if updated_since:
            params["updated_since"] = updated_since.isoformat()
        
        response = await self._make_request("GET", "items/items", account_id, params=params)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"]
    
    async def get_item(self, item_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a specific item by ID.
        
        Args:
            item_id: FreshBooks item ID
            account_id: FreshBooks account ID
            
        Returns:
            Item object
        """
        response = await self._make_request("GET", f"items/items/{item_id}", account_id)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        item = response["response"]
        if not item:
            raise FreshBooksItemNotFoundError(f"Item {item_id} not found")
        
        return item
    
    async def get_invoices(
        self,
        account_id: Optional[str] = None,
        per_page: int = 50,
        page: int = 1,
        updated_since: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get invoices from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            per_page: Number of invoices per page
            page: Page number
            updated_since: Only return invoices updated since this date
            status: Filter by invoice status (draft, sent, paid, etc.)
            
        Returns:
            Invoices response with pagination info
        """
        params = {
            "per_page": min(per_page, 100),
            "page": page
        }
        
        if updated_since:
            params["updated_since"] = updated_since.isoformat()
        
        if status:
            params["search[status]"] = status
        
        response = await self._make_request("GET", "invoices/invoices", account_id, params=params)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"]
    
    async def get_invoice(self, invoice_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a specific invoice by ID.
        
        Args:
            invoice_id: FreshBooks invoice ID
            account_id: FreshBooks account ID
            
        Returns:
            Invoice object
        """
        response = await self._make_request("GET", f"invoices/invoices/{invoice_id}", account_id)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        invoice = response["response"]
        if not invoice:
            raise FreshBooksInvoiceNotFoundError(f"Invoice {invoice_id} not found")
        
        return invoice
    
    async def get_taxes(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tax configurations from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            
        Returns:
            List of tax objects
        """
        response = await self._make_request("GET", "taxes/taxes", account_id)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"].get("taxes", [])
    
    async def get_payments(
        self,
        account_id: Optional[str] = None,
        per_page: int = 50,
        page: int = 1,
        updated_since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get payments from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            per_page: Number of payments per page
            page: Page number
            updated_since: Only return payments updated since this date
            
        Returns:
            Payments response with pagination info
        """
        params = {
            "per_page": min(per_page, 100),
            "page": page
        }
        
        if updated_since:
            params["updated_since"] = updated_since.isoformat()
        
        response = await self._make_request("GET", "payments/payments", account_id, params=params)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"]
    
    async def create_client(
        self,
        client_data: Dict[str, Any],
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new client in FreshBooks.
        
        Args:
            client_data: Client data
            account_id: FreshBooks account ID
            
        Returns:
            Created client object
        """
        data = {"client": client_data}
        
        response = await self._make_request("POST", "users/clients", account_id, data=data)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"]
    
    async def create_invoice(
        self,
        invoice_data: Dict[str, Any],
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new invoice in FreshBooks.
        
        Args:
            invoice_data: Invoice data
            account_id: FreshBooks account ID
            
        Returns:
            Created invoice object
        """
        data = {"invoice": invoice_data}
        
        response = await self._make_request("POST", "invoices/invoices", account_id, data=data)
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"]
    
    async def update_invoice(
        self,
        invoice_id: str,
        invoice_data: Dict[str, Any],
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing invoice in FreshBooks.
        
        Args:
            invoice_id: FreshBooks invoice ID
            invoice_data: Updated invoice data
            account_id: FreshBooks account ID
            
        Returns:
            Updated invoice object
        """
        data = {"invoice": invoice_data}
        
        response = await self._make_request(
            "PUT", 
            f"invoices/invoices/{invoice_id}", 
            account_id, 
            data=data
        )
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"]
    
    async def send_invoice(
        self,
        invoice_id: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an invoice via FreshBooks.
        
        Args:
            invoice_id: FreshBooks invoice ID
            account_id: FreshBooks account ID
            
        Returns:
            Send result
        """
        response = await self._make_request(
            "PUT", 
            f"invoices/invoices/{invoice_id}",
            account_id,
            data={"invoice": {"action_email": True}}
        )
        
        if "response" not in response:
            raise FreshBooksAPIError("Invalid response format")
        
        return response["response"]