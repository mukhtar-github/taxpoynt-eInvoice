"""
BigCommerce E-commerce REST API Client
HTTP client for interacting with BigCommerce REST API.
Handles authentication, rate limiting, pagination, and multi-channel operations.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urlencode, urlparse, parse_qs

import aiohttp

from .auth import BigCommerceAuthManager
from .exceptions import (
    BigCommerceConnectionError,
    BigCommerceAPIError,
    BigCommerceRateLimitError,
    map_api_error
)

logger = logging.getLogger(__name__)


class BigCommerceRESTClient:
    """
    BigCommerce E-commerce REST API Client
    
    Comprehensive HTTP client for BigCommerce REST API with:
    - Automatic authentication handling
    - Rate limiting and retry logic
    - Pagination support
    - Multi-channel operations
    - Comprehensive error handling
    """
    
    def __init__(self, config: Dict[str, Any], auth_manager: BigCommerceAuthManager):
        """
        Initialize BigCommerce REST client.
        
        Args:
            config: Configuration dictionary containing:
                - rate_limit: Rate limiting configuration
                - timeout: Request timeout settings
                - retry: Retry configuration
            auth_manager: Configured BigCommerce authentication manager
        """
        self.config = config
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Rate limiting configuration
        rate_limit_config = config.get('rate_limit', {})
        self.requests_per_second = rate_limit_config.get('requests_per_second', 5)  # BigCommerce: 5 req/sec
        self.burst_capacity = rate_limit_config.get('burst_capacity', 10)
        self.rate_limit_window = timedelta(seconds=1)
        
        # Request timing tracking
        self._request_times = []
        self._last_rate_limit_reset = datetime.now()
        
        # Timeout configuration
        timeout_config = config.get('timeout', {})
        self.request_timeout = aiohttp.ClientTimeout(
            total=timeout_config.get('total', 30),
            connect=timeout_config.get('connect', 10),
            read=timeout_config.get('read', 20)
        )
        
        # Retry configuration
        retry_config = config.get('retry', {})
        self.max_retries = retry_config.get('max_retries', 3)
        self.retry_backoff = retry_config.get('backoff_factor', 2)
        self.retry_statuses = retry_config.get('retry_statuses', [429, 500, 502, 503, 504])
        
        # HTTP session
        self.session = None
        
        # Base API URL
        self.base_url = auth_manager.get_base_url()
    
    async def _ensure_session(self):
        """Ensure HTTP session is available."""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.request_timeout,
                headers={'User-Agent': 'TaxPoynt-BigCommerce-Connector/1.0'}
            )
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        now = datetime.now()
        
        # Remove old request times outside the window
        cutoff_time = now - self.rate_limit_window
        self._request_times = [t for t in self._request_times if t > cutoff_time]
        
        # Check if we need to wait
        if len(self._request_times) >= self.requests_per_second:
            oldest_request = min(self._request_times)
            wait_time = (oldest_request + self.rate_limit_window - now).total_seconds()
            
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # Record this request time
        self._request_times.append(now)
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to BigCommerce API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Additional headers
            
        Returns:
            API response data
        """
        await self._ensure_session()
        await self._rate_limit_check()
        
        # Build full URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Get authentication headers
        auth_headers = await self.auth_manager.get_auth_headers()
        
        # Merge headers
        request_headers = {**auth_headers}
        if headers:
            request_headers.update(headers)
        
        # Retry logic
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                async with self.session.request(
                    method,
                    url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers
                ) as response:
                    
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        if attempt < self.max_retries:
                            self.logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            raise BigCommerceRateLimitError(
                                "Rate limit exceeded",
                                retry_after=retry_after
                            )
                    
                    # Read response
                    try:
                        response_data = await response.json()
                    except aiohttp.ContentTypeError:
                        response_text = await response.text()
                        if response.status >= 400:
                            raise map_api_error(
                                response.status,
                                f"API request failed: {response_text}",
                                {'raw_response': response_text},
                                endpoint
                            )
                        response_data = {'message': response_text}
                    
                    # Handle successful responses
                    if 200 <= response.status < 300:
                        return response_data
                    
                    # Handle error responses
                    error_message = self._extract_error_message(response_data, response.status)
                    
                    # Retry on specific status codes
                    if response.status in self.retry_statuses and attempt < self.max_retries:
                        wait_time = self.retry_backoff ** attempt
                        self.logger.warning(f"Request failed with {response.status}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # Raise appropriate exception
                    raise map_api_error(
                        response.status,
                        error_message,
                        response_data,
                        endpoint
                    )
                    
            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self.retry_backoff ** attempt
                    self.logger.warning(f"Connection error, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise BigCommerceConnectionError(f"Request failed after {self.max_retries} retries: {e}")
        
        # If we get here, all retries failed
        if last_exception:
            raise BigCommerceConnectionError(f"Request failed: {last_exception}")
    
    def _extract_error_message(self, response_data: Any, status_code: int) -> str:
        """Extract error message from API response."""
        if isinstance(response_data, dict):
            # Check various error message fields
            for field in ['message', 'error', 'detail', 'title']:
                if field in response_data:
                    return str(response_data[field])
            
            # Check for errors array
            if 'errors' in response_data and isinstance(response_data['errors'], list):
                errors = response_data['errors']
                if errors:
                    return '; '.join(str(error) for error in errors)
        
        return f"API request failed with status {status_code}"
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return await self.request('GET', endpoint, params=params)
    
    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        return await self.request('POST', endpoint, json_data=json_data)
    
    async def put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return await self.request('PUT', endpoint, json_data=json_data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self.request('DELETE', endpoint)
    
    async def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get paginated results from BigCommerce API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            limit: Maximum number of items to retrieve
            
        Yields:
            Individual items from paginated results
        """
        params = params or {}
        page = 1
        per_page = min(params.get('limit', 50), 250)  # BigCommerce max: 250
        total_retrieved = 0
        
        while True:
            # Set pagination parameters
            page_params = {
                **params,
                'page': page,
                'limit': per_page
            }
            
            try:
                response = await self.get(endpoint, params=page_params)
                
                # Handle different response formats
                if isinstance(response, dict):
                    if 'data' in response:
                        items = response['data']
                        meta = response.get('meta', {})
                    else:
                        items = response if isinstance(response, list) else [response]
                        meta = {}
                else:
                    items = response if isinstance(response, list) else [response]
                    meta = {}
                
                if not items:
                    break
                
                # Yield items
                for item in items:
                    if limit and total_retrieved >= limit:
                        return
                    
                    yield item
                    total_retrieved += 1
                
                # Check if there are more pages
                pagination = meta.get('pagination', {})
                current_page = pagination.get('current_page', page)
                total_pages = pagination.get('total_pages', 1)
                
                if current_page >= total_pages:
                    break
                
                page += 1
                
            except BigCommerceAPIError as e:
                if e.status_code == 404:
                    # No more results
                    break
                raise
    
    # Store Information
    async def get_store_info(self) -> Dict[str, Any]:
        """Get store information."""
        return await self.get('store')
    
    # Orders
    async def get_orders(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get orders with optional filtering."""
        return await self.get('orders', params=params)
    
    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get specific order by ID."""
        return await self.get(f'orders/{order_id}')
    
    async def get_order_products(self, order_id: int) -> Dict[str, Any]:
        """Get products for a specific order."""
        return await self.get(f'orders/{order_id}/products')
    
    async def get_order_shipping_addresses(self, order_id: int) -> Dict[str, Any]:
        """Get shipping addresses for a specific order."""
        return await self.get(f'orders/{order_id}/shipping_addresses')
    
    # Customers
    async def get_customers(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get customers with optional filtering."""
        return await self.get('customers', params=params)
    
    async def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """Get specific customer by ID."""
        return await self.get(f'customers/{customer_id}')
    
    async def get_customer_addresses(self, customer_id: int) -> Dict[str, Any]:
        """Get addresses for a specific customer."""
        return await self.get(f'customers/{customer_id}/addresses')
    
    # Products
    async def get_products(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get products with optional filtering."""
        return await self.get('catalog/products', params=params)
    
    async def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get specific product by ID."""
        return await self.get(f'catalog/products/{product_id}')
    
    async def get_product_variants(self, product_id: int) -> Dict[str, Any]:
        """Get variants for a specific product."""
        return await self.get(f'catalog/products/{product_id}/variants')
    
    async def get_product_images(self, product_id: int) -> Dict[str, Any]:
        """Get images for a specific product."""
        return await self.get(f'catalog/products/{product_id}/images')
    
    # Categories
    async def get_categories(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get categories with optional filtering."""
        return await self.get('catalog/categories', params=params)
    
    async def get_category(self, category_id: int) -> Dict[str, Any]:
        """Get specific category by ID."""
        return await self.get(f'catalog/categories/{category_id}')
    
    # Brands
    async def get_brands(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get brands with optional filtering."""
        return await self.get('catalog/brands', params=params)
    
    async def get_brand(self, brand_id: int) -> Dict[str, Any]:
        """Get specific brand by ID."""
        return await self.get(f'catalog/brands/{brand_id}')
    
    # Channels (Multi-channel support)
    async def get_channels(self) -> Dict[str, Any]:
        """Get all channels."""
        return await self.get('channels')
    
    async def get_channel(self, channel_id: int) -> Dict[str, Any]:
        """Get specific channel by ID."""
        return await self.get(f'channels/{channel_id}')
    
    async def get_channel_orders(self, channel_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get orders for a specific channel."""
        channel_params = {**(params or {}), 'channel_id': channel_id}
        return await self.get('orders', params=channel_params)
    
    # Webhooks
    async def get_webhooks(self) -> Dict[str, Any]:
        """Get all webhooks."""
        return await self.get('hooks')
    
    async def create_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new webhook."""
        return await self.post('hooks', json_data=webhook_data)
    
    async def update_webhook(self, webhook_id: int, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing webhook."""
        return await self.put(f'hooks/{webhook_id}', json_data=webhook_data)
    
    async def delete_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """Delete a webhook."""
        return await self.delete(f'hooks/{webhook_id}')
    
    # Scripts (for checkout customization)
    async def get_scripts(self) -> Dict[str, Any]:
        """Get all scripts."""
        return await self.get('content/scripts')
    
    async def create_script(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new script."""
        return await self.post('content/scripts', json_data=script_data)
    
    # Tax Classes
    async def get_tax_classes(self) -> Dict[str, Any]:
        """Get tax classes."""
        return await self.get('tax_classes')
    
    # Shipping
    async def get_shipping_zones(self) -> Dict[str, Any]:
        """Get shipping zones."""
        return await self.get('shipping/zones')
    
    async def get_shipping_methods(self, zone_id: int) -> Dict[str, Any]:
        """Get shipping methods for a zone."""
        return await self.get(f'shipping/zones/{zone_id}/methods')
    
    async def close(self):
        """Close the REST client and clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def __str__(self) -> str:
        """String representation of the REST client."""
        return f"BigCommerceRESTClient(base_url={self.base_url})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the REST client."""
        return (f"BigCommerceRESTClient("
                f"base_url='{self.base_url}', "
                f"rate_limit={self.requests_per_second}/sec)")