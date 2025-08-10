"""
TradeGecko REST API Client
Handles all HTTP communication with TradeGecko inventory management API.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .auth import TradeGeckoAuthManager
from .exceptions import (
    TradeGeckoAPIError,
    TradeGeckoConnectionError,
    TradeGeckoRateLimitError,
    TradeGeckoAuthenticationError,
    TradeGeckoMaintenanceError,
    TradeGeckoProductNotFoundError,
    TradeGeckoVariantNotFoundError,
    TradeGeckoLocationNotFoundError
)


logger = logging.getLogger(__name__)


class TradeGeckoRestClient:
    """
    REST client for TradeGecko inventory management API.
    
    Handles HTTP communication, rate limiting, and error handling
    for all TradeGecko API operations.
    """
    
    # API version
    API_VERSION = "v1"
    
    # Rate limiting settings (TradeGecko allows 300 requests per minute)
    MAX_REQUESTS_PER_MINUTE = 300
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    def __init__(
        self,
        auth_manager: TradeGeckoAuthManager,
        session: Optional[ClientSession] = None,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize TradeGecko REST client.
        
        Args:
            auth_manager: TradeGecko authentication manager
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
                headers={"User-Agent": "TaxPoynt-TradeGecko-Integration/1.0"}
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
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to TradeGecko API.
        
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
            raise TradeGeckoConnectionError("No HTTP session available")
        
        await self._rate_limit_check()
        
        # Get authentication headers
        headers = self.auth_manager.get_auth_headers()
        
        # Build URL
        url = f"{self.auth_manager.base_url}/{self.API_VERSION}/{endpoint.lstrip('/')}"
        
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
                        raise TradeGeckoAuthenticationError("Authentication failed")
                    elif response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise TradeGeckoRateLimitError(
                            "Rate limit exceeded", 
                            retry_after=retry_after
                        )
                    elif response.status == 503:
                        raise TradeGeckoMaintenanceError("TradeGecko API is under maintenance")
                    elif response.status >= 400:
                        # Try to parse error response
                        try:
                            error_data = json.loads(response_text)
                            error_msg = error_data.get("message", response_text)
                        except json.JSONDecodeError:
                            error_msg = response_text
                        
                        raise TradeGeckoAPIError(
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
                    
            except TradeGeckoRateLimitError as e:
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
                raise TradeGeckoConnectionError(f"Failed to connect to TradeGecko API: {str(e)}")
        
        raise TradeGeckoConnectionError("Max retries exceeded")
    
    # Product Operations
    
    async def get_products(
        self,
        page: int = 1,
        limit: int = 250,
        ids: Optional[List[str]] = None,
        created_at_min: Optional[str] = None,
        updated_at_min: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250),  # TradeGecko max is 250
        }
        
        if ids:
            params["ids"] = ",".join(ids)
        if created_at_min:
            params["created_at_min"] = created_at_min
        if updated_at_min:
            params["updated_at_min"] = updated_at_min
        
        return await self._make_request("GET", "products", params=params)
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get a specific product by ID."""
        response = await self._make_request("GET", f"products/{product_id}")
        
        if not response or "product" not in response:
            raise TradeGeckoProductNotFoundError(f"Product {product_id} not found")
        
        return response
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        return await self._make_request("POST", "products", json_data={"product": product_data})
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product."""
        return await self._make_request("PUT", f"products/{product_id}", json_data={"product": product_data})
    
    # Variant Operations
    
    async def get_variants(
        self,
        page: int = 1,
        limit: int = 250,
        product_id: Optional[str] = None,
        ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get product variants from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if product_id:
            params["product_id"] = product_id
        if ids:
            params["ids"] = ",".join(ids)
        
        return await self._make_request("GET", "variants", params=params)
    
    async def get_variant(self, variant_id: str) -> Dict[str, Any]:
        """Get a specific variant by ID."""
        response = await self._make_request("GET", f"variants/{variant_id}")
        
        if not response or "variant" not in response:
            raise TradeGeckoVariantNotFoundError(f"Variant {variant_id} not found")
        
        return response
    
    async def create_variant(self, variant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new variant."""
        return await self._make_request("POST", "variants", json_data={"variant": variant_data})
    
    async def update_variant(self, variant_id: str, variant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing variant."""
        return await self._make_request("PUT", f"variants/{variant_id}", json_data={"variant": variant_data})
    
    # Stock Level Operations
    
    async def get_stock_levels(
        self,
        page: int = 1,
        limit: int = 250,
        location_id: Optional[str] = None,
        variant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock levels from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if location_id:
            params["location_id"] = location_id
        if variant_id:
            params["variant_id"] = variant_id
        
        return await self._make_request("GET", "stock_levels", params=params)
    
    async def get_stock_level(self, stock_level_id: str) -> Dict[str, Any]:
        """Get a specific stock level by ID."""
        return await self._make_request("GET", f"stock_levels/{stock_level_id}")
    
    async def update_stock_level(self, stock_level_id: str, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update stock level."""
        return await self._make_request("PUT", f"stock_levels/{stock_level_id}", json_data={"stock_level": stock_data})
    
    # Stock Movement Operations
    
    async def get_stock_movements(
        self,
        page: int = 1,
        limit: int = 250,
        location_id: Optional[str] = None,
        variant_id: Optional[str] = None,
        created_at_min: Optional[str] = None,
        created_at_max: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock movements from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if location_id:
            params["location_id"] = location_id
        if variant_id:
            params["variant_id"] = variant_id
        if created_at_min:
            params["created_at_min"] = created_at_min
        if created_at_max:
            params["created_at_max"] = created_at_max
        
        return await self._make_request("GET", "stock_movements", params=params)
    
    async def create_stock_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a stock movement."""
        return await self._make_request("POST", "stock_movements", json_data={"stock_movement": movement_data})
    
    # Stock Adjustment Operations
    
    async def get_stock_adjustments(
        self,
        page: int = 1,
        limit: int = 250,
        location_id: Optional[str] = None,
        created_at_min: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock adjustments from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if location_id:
            params["location_id"] = location_id
        if created_at_min:
            params["created_at_min"] = created_at_min
        
        return await self._make_request("GET", "stock_adjustments", params=params)
    
    async def create_stock_adjustment(self, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a stock adjustment."""
        return await self._make_request("POST", "stock_adjustments", json_data={"stock_adjustment": adjustment_data})
    
    # Purchase Order Operations
    
    async def get_purchase_orders(
        self,
        page: int = 1,
        limit: int = 250,
        status: Optional[str] = None,
        created_at_min: Optional[str] = None,
        updated_at_min: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get purchase orders from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if status:
            params["status"] = status
        if created_at_min:
            params["created_at_min"] = created_at_min
        if updated_at_min:
            params["updated_at_min"] = updated_at_min
        
        return await self._make_request("GET", "purchase_orders", params=params)
    
    async def get_purchase_order(self, order_id: str) -> Dict[str, Any]:
        """Get a specific purchase order by ID."""
        return await self._make_request("GET", f"purchase_orders/{order_id}")
    
    async def create_purchase_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new purchase order."""
        return await self._make_request("POST", "purchase_orders", json_data={"purchase_order": order_data})
    
    # Sales Order Operations
    
    async def get_orders(
        self,
        page: int = 1,
        limit: int = 250,
        status: Optional[str] = None,
        created_at_min: Optional[str] = None,
        updated_at_min: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sales orders from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if status:
            params["status"] = status
        if created_at_min:
            params["created_at_min"] = created_at_min
        if updated_at_min:
            params["updated_at_min"] = updated_at_min
        
        return await self._make_request("GET", "orders", params=params)
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get a specific sales order by ID."""
        return await self._make_request("GET", f"orders/{order_id}")
    
    # Supplier Operations
    
    async def get_companies(
        self,
        page: int = 1,
        limit: int = 250,
        company_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get companies (suppliers/customers) from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if company_type:
            params["company_type"] = company_type
        
        return await self._make_request("GET", "companies", params=params)
    
    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """Get a specific company by ID."""
        return await self._make_request("GET", f"companies/{company_id}")
    
    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company."""
        return await self._make_request("POST", "companies", json_data={"company": company_data})
    
    # Location Operations
    
    async def get_locations(
        self,
        page: int = 1,
        limit: int = 250
    ) -> Dict[str, Any]:
        """Get all locations from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        return await self._make_request("GET", "locations", params=params)
    
    async def get_location(self, location_id: str) -> Dict[str, Any]:
        """Get a specific location by ID."""
        response = await self._make_request("GET", f"locations/{location_id}")
        
        if not response or "location" not in response:
            raise TradeGeckoLocationNotFoundError(f"Location {location_id} not found")
        
        return response
    
    async def create_location(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new location."""
        return await self._make_request("POST", "locations", json_data={"location": location_data})
    
    # Fulfillment Operations
    
    async def get_fulfillments(
        self,
        page: int = 1,
        limit: int = 250,
        order_id: Optional[str] = None,
        created_at_min: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get fulfillments from TradeGecko."""
        params = {
            "page": page,
            "limit": min(limit, 250)
        }
        
        if order_id:
            params["order_id"] = order_id
        if created_at_min:
            params["created_at_min"] = created_at_min
        
        return await self._make_request("GET", "fulfillments", params=params)
    
    async def create_fulfillment(self, fulfillment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fulfillment."""
        return await self._make_request("POST", "fulfillments", json_data={"fulfillment": fulfillment_data})
    
    # Reporting Operations
    
    async def get_stock_report(
        self,
        location_id: Optional[str] = None,
        as_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock report from TradeGecko."""
        params = {}
        
        if location_id:
            params["location_id"] = location_id
        if as_at:
            params["as_at"] = as_at
        
        return await self._make_request("GET", "stock_report", params=params)
    
    async def get_low_stock_report(
        self,
        location_id: Optional[str] = None,
        threshold: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get low stock report from TradeGecko."""
        params = {}
        
        if location_id:
            params["location_id"] = location_id
        if threshold:
            params["threshold"] = threshold
        
        return await self._make_request("GET", "low_stock_report", params=params)