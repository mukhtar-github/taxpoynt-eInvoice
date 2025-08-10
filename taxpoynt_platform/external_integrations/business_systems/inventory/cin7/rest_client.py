"""
Cin7 REST API Client
Handles all HTTP communication with Cin7 inventory management API.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .auth import Cin7AuthManager
from .exceptions import (
    Cin7APIError,
    Cin7ConnectionError,
    Cin7RateLimitError,
    Cin7AuthenticationError,
    Cin7MaintenanceError,
    Cin7ProductNotFoundError,
    Cin7StockLocationNotFoundError
)


logger = logging.getLogger(__name__)


class Cin7RestClient:
    """
    REST client for Cin7 inventory management API.
    
    Handles HTTP communication, rate limiting, and error handling
    for all Cin7 API operations.
    """
    
    # API version
    API_VERSION = "1.3"
    
    # Rate limiting settings (Cin7 allows 1000 requests per hour)
    MAX_REQUESTS_PER_HOUR = 1000
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    def __init__(
        self,
        auth_manager: Cin7AuthManager,
        session: Optional[ClientSession] = None,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize Cin7 REST client.
        
        Args:
            auth_manager: Cin7 authentication manager
            session: Optional aiohttp session
            max_retries: Maximum number of retry attempts
        """
        self.auth_manager = auth_manager
        self.session = session
        self.should_close_session = session is None
        self.max_retries = max_retries
        
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
                headers={"User-Agent": "TaxPoynt-Cin7-Integration/1.0"}
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
            # Remove requests older than 1 hour
            cutoff = now - timedelta(hours=1)
            self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Check if we're at rate limit
            if len(self._request_times) >= self.MAX_REQUESTS_PER_HOUR:
                sleep_time = 3600 - (now - self._request_times[0]).total_seconds()
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                # Clean up old requests again after sleeping
                now = datetime.utcnow()
                cutoff = now - timedelta(hours=1)
                self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Record this request
            self._request_times.append(now)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to Cin7 API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Form data
            json_data: JSON data
            
        Returns:
            Response data
        """
        if not self.session:
            raise Cin7ConnectionError("No HTTP session available")
        
        await self._rate_limit_check()
        
        # Get authentication headers
        headers = self.auth_manager.get_auth_headers()
        
        # Build URL
        url = f"{self.auth_manager.base_url}/api/v{self.API_VERSION}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries + 1):
            try:
                kwargs = {
                    "headers": headers,
                    "params": params
                }
                
                if json_data:
                    kwargs["json"] = json_data
                elif data:
                    kwargs["data"] = data
                
                async with self.session.request(method, url, **kwargs) as response:
                    response_text = await response.text()
                    
                    # Handle HTTP errors
                    if response.status == 401:
                        raise Cin7AuthenticationError("Authentication failed")
                    elif response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 3600))
                        raise Cin7RateLimitError(
                            "Rate limit exceeded", 
                            retry_after=retry_after
                        )
                    elif response.status == 503:
                        raise Cin7MaintenanceError("Cin7 API is under maintenance")
                    elif response.status >= 400:
                        # Try to parse error response
                        try:
                            error_data = json.loads(response_text)
                            error_msg = error_data.get("Message", response_text)
                        except json.JSONDecodeError:
                            error_msg = response_text
                        
                        raise Cin7APIError(
                            f"HTTP {response.status}: {error_msg}",
                            status_code=response.status,
                            response_data={"raw_response": response_text}
                        )
                    
                    # Parse JSON response
                    try:
                        if response_text:
                            return json.loads(response_text)
                        else:
                            return {}
                    except json.JSONDecodeError:
                        return {"raw_response": response_text}
                    
            except Cin7RateLimitError as e:
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
                raise Cin7ConnectionError(f"Failed to connect to Cin7 API: {str(e)}")
        
        raise Cin7ConnectionError("Max retries exceeded")
    
    # Product Operations
    
    async def get_products(
        self,
        page: int = 1,
        limit: int = 250,
        where: Optional[str] = None,
        order: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products from Cin7."""
        params = {
            "page": page,
            "limit": min(limit, 250),  # Cin7 max is 250
        }
        
        if where:
            params["where"] = where
        if order:
            params["order"] = order
        
        return await self._make_request("GET", "Products", params=params)
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get a specific product by ID."""
        response = await self._make_request("GET", f"Products/{product_id}")
        
        if not response:
            raise Cin7ProductNotFoundError(f"Product {product_id} not found")
        
        return response
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        return await self._make_request("POST", "Products", json_data=product_data)
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product."""
        return await self._make_request("PUT", f"Products/{product_id}", json_data=product_data)
    
    # Stock Operations
    
    async def get_stock_on_hand(
        self,
        page: int = 1,
        limit: int = 250,
        where: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock on hand data."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if where:
            params["where"] = where
        
        return await self._make_request("GET", "StockOnHand", params=params)
    
    async def get_stock_movements(
        self,
        page: int = 1,
        limit: int = 250,
        where: Optional[str] = None,
        order: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock movement history."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if where:
            params["where"] = where
        if order:
            params["order"] = order
        
        return await self._make_request("GET", "StockMovements", params=params)
    
    async def create_stock_adjustment(self, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a stock adjustment."""
        return await self._make_request("POST", "StockAdjustments", json_data=adjustment_data)
    
    async def create_stock_transfer(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a stock transfer."""
        return await self._make_request("POST", "StockTransfers", json_data=transfer_data)
    
    # Purchase Order Operations
    
    async def get_purchase_orders(
        self,
        page: int = 1,
        limit: int = 250,
        where: Optional[str] = None,
        order: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get purchase orders."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if where:
            params["where"] = where
        if order:
            params["order"] = order
        
        return await self._make_request("GET", "PurchaseOrders", params=params)
    
    async def get_purchase_order(self, order_id: str) -> Dict[str, Any]:
        """Get a specific purchase order by ID."""
        return await self._make_request("GET", f"PurchaseOrders/{order_id}")
    
    async def create_purchase_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new purchase order."""
        return await self._make_request("POST", "PurchaseOrders", json_data=order_data)
    
    # Sales Order Operations
    
    async def get_sales_orders(
        self,
        page: int = 1,
        limit: int = 250,
        where: Optional[str] = None,
        order: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sales orders."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if where:
            params["where"] = where
        if order:
            params["order"] = order
        
        return await self._make_request("GET", "SalesOrders", params=params)
    
    async def get_sales_order(self, order_id: str) -> Dict[str, Any]:
        """Get a specific sales order by ID."""
        return await self._make_request("GET", f"SalesOrders/{order_id}")
    
    # Supplier Operations
    
    async def get_suppliers(
        self,
        page: int = 1,
        limit: int = 250,
        where: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get suppliers."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if where:
            params["where"] = where
        
        return await self._make_request("GET", "Suppliers", params=params)
    
    async def get_supplier(self, supplier_id: str) -> Dict[str, Any]:
        """Get a specific supplier by ID."""
        return await self._make_request("GET", f"Suppliers/{supplier_id}")
    
    # Location Operations
    
    async def get_stock_locations(self) -> Dict[str, Any]:
        """Get all stock locations."""
        return await self._make_request("GET", "StockLocations")
    
    async def get_stock_location(self, location_id: str) -> Dict[str, Any]:
        """Get a specific stock location by ID."""
        response = await self._make_request("GET", f"StockLocations/{location_id}")
        
        if not response:
            raise Cin7StockLocationNotFoundError(f"Stock location {location_id} not found")
        
        return response
    
    # Reporting Operations
    
    async def get_stock_valuation(
        self,
        location_id: Optional[str] = None,
        as_at_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock valuation report."""
        params = {}
        
        if location_id:
            params["locationId"] = location_id
        if as_at_date:
            params["asAtDate"] = as_at_date
        
        return await self._make_request("GET", "StockValuation", params=params)
    
    async def get_low_stock_report(
        self,
        location_id: Optional[str] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get low stock report."""
        params = {}
        
        if location_id:
            params["locationId"] = location_id
        if threshold:
            params["threshold"] = threshold
        
        return await self._make_request("GET", "LowStockReport", params=params)