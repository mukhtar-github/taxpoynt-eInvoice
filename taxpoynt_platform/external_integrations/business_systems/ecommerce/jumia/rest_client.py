"""
Jumia E-commerce REST API Client
HTTP client for interacting with Jumia Marketplace Seller API.
Handles authentication, rate limiting, pagination, and regional marketplace operations.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urlencode, urlparse, parse_qs

import aiohttp

from .auth import JumiaAuthManager
from .exceptions import (
    JumiaConnectionError,
    JumiaAPIError,
    JumiaRateLimitError,
    map_api_error
)

logger = logging.getLogger(__name__)


class JumiaRESTClient:
    """
    Jumia E-commerce REST API Client
    
    Comprehensive HTTP client for Jumia Marketplace Seller API with:
    - Automatic authentication handling
    - Rate limiting and retry logic
    - Pagination support
    - Regional marketplace operations
    - Comprehensive error handling
    """
    
    def __init__(self, config: Dict[str, Any], auth_manager: JumiaAuthManager):
        """
        Initialize Jumia REST client.
        
        Args:
            config: Configuration dictionary containing:
                - rate_limit: Rate limiting configuration
                - timeout: Request timeout settings
                - retry: Retry configuration
            auth_manager: Configured Jumia authentication manager
        """
        self.config = config
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Rate limiting configuration (Jumia has strict limits)
        rate_limit_config = config.get('rate_limit', {})
        self.requests_per_minute = rate_limit_config.get('requests_per_minute', 60)  # Conservative estimate
        self.burst_capacity = rate_limit_config.get('burst_capacity', 5)
        self.rate_limit_window = timedelta(minutes=1)
        
        # Request timing tracking
        self._request_times = []
        self._last_rate_limit_reset = datetime.now()
        
        # Timeout configuration
        timeout_config = config.get('timeout', {})
        self.request_timeout = aiohttp.ClientTimeout(
            total=timeout_config.get('total', 60),  # Jumia can be slow
            connect=timeout_config.get('connect', 15),
            read=timeout_config.get('read', 45)
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
                limit=50,
                limit_per_host=10,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.request_timeout,
                headers={'User-Agent': 'TaxPoynt-Jumia-Connector/1.0'}
            )
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        now = datetime.now()
        
        # Remove old request times outside the window
        cutoff_time = now - self.rate_limit_window
        self._request_times = [t for t in self._request_times if t > cutoff_time]
        
        # Check if we need to wait
        if len(self._request_times) >= self.requests_per_minute:
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
        Make authenticated HTTP request to Jumia API.
        
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
                            raise JumiaRateLimitError(
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
                    raise JumiaConnectionError(f"Request failed after {self.max_retries} retries: {e}")
        
        # If we get here, all retries failed
        if last_exception:
            raise JumiaConnectionError(f"Request failed: {last_exception}")
    
    def _extract_error_message(self, response_data: Any, status_code: int) -> str:
        """Extract error message from API response."""
        if isinstance(response_data, dict):
            # Check various error message fields
            for field in ['message', 'error', 'detail', 'description']:
                if field in response_data:
                    return str(response_data[field])
            
            # Check for errors array
            if 'errors' in response_data and isinstance(response_data['errors'], list):
                errors = response_data['errors']
                if errors:
                    return '; '.join(str(error) for error in errors)
            
            # Check for error details in Jumia format
            if 'error_details' in response_data:
                details = response_data['error_details']
                if isinstance(details, dict):
                    return details.get('message', str(details))
                return str(details)
        
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
        Get paginated results from Jumia API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            limit: Maximum number of items to retrieve
            
        Yields:
            Individual items from paginated results
        """
        params = params or {}
        offset = 0
        page_size = min(params.get('limit', 100), 100)  # Jumia typical max: 100
        total_retrieved = 0
        
        while True:
            # Set pagination parameters
            page_params = {
                **params,
                'offset': offset,
                'limit': page_size
            }
            
            try:
                response = await self.get(endpoint, params=page_params)
                
                # Handle different Jumia response formats
                if isinstance(response, dict):
                    if 'data' in response:
                        items = response['data']
                        total_count = response.get('total_count', 0)
                    elif 'body' in response:
                        body = response['body']
                        if isinstance(body, dict):
                            items = body.get('data', body.get('items', []))
                            total_count = body.get('total_count', len(items))
                        else:
                            items = body if isinstance(body, list) else [body]
                            total_count = len(items)
                    else:
                        items = response if isinstance(response, list) else [response]
                        total_count = len(items)
                else:
                    items = response if isinstance(response, list) else [response]
                    total_count = len(items)
                
                if not items:
                    break
                
                # Yield items
                for item in items:
                    if limit and total_retrieved >= limit:
                        return
                    
                    yield item
                    total_retrieved += 1
                
                # Check if there are more pages
                if len(items) < page_size or (total_count > 0 and total_retrieved >= total_count):
                    break
                
                offset += page_size
                
            except JumiaAPIError as e:
                if e.status_code == 404:
                    # No more results
                    break
                raise
    
    # Seller Information
    async def get_seller_profile(self) -> Dict[str, Any]:
        """Get seller profile information."""
        return await self.get('seller/profile')
    
    # Orders
    async def get_orders(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get orders with optional filtering."""
        return await self.get('orders', params=params)
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get specific order by ID."""
        return await self.get(f'orders/{order_id}')
    
    async def get_order_items(self, order_id: str) -> Dict[str, Any]:
        """Get items for a specific order."""
        return await self.get(f'orders/{order_id}/items')
    
    async def update_order_status(self, order_id: str, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update order status."""
        return await self.put(f'orders/{order_id}/status', json_data=status_data)
    
    # Products
    async def get_products(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get products with optional filtering."""
        return await self.get('products', params=params)
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get specific product by ID."""
        return await self.get(f'products/{product_id}')
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        return await self.post('products', json_data=product_data)
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product."""
        return await self.put(f'products/{product_id}', json_data=product_data)
    
    async def delete_product(self, product_id: str) -> Dict[str, Any]:
        """Delete a product."""
        return await self.delete(f'products/{product_id}')
    
    # Categories
    async def get_categories(self) -> Dict[str, Any]:
        """Get all categories."""
        return await self.get('categories')
    
    async def get_category(self, category_id: str) -> Dict[str, Any]:
        """Get specific category by ID."""
        return await self.get(f'categories/{category_id}')
    
    # Inventory
    async def get_inventory(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get inventory information."""
        return await self.get('products/inventory', params=params)
    
    async def update_inventory(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update inventory levels."""
        return await self.put('products/inventory', json_data={'inventory_updates': updates})
    
    # Pricing
    async def get_product_prices(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get product prices."""
        return await self.get('products/prices', params=params)
    
    async def update_product_prices(self, price_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update product prices."""
        return await self.put('products/prices', json_data={'price_updates': price_updates})
    
    # Shipments
    async def get_shipments(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get shipments."""
        return await self.get('shipments', params=params)
    
    async def create_shipment(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shipment."""
        return await self.post('shipments', json_data=shipment_data)
    
    async def get_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """Get specific shipment by ID."""
        return await self.get(f'shipments/{shipment_id}')
    
    # Returns
    async def get_returns(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get returns."""
        return await self.get('returns', params=params)
    
    async def get_return(self, return_id: str) -> Dict[str, Any]:
        """Get specific return by ID."""
        return await self.get(f'returns/{return_id}')
    
    # Reports
    async def get_sales_report(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get sales report."""
        return await self.get('reports/sales', params=params)
    
    async def get_inventory_report(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get inventory report."""
        return await self.get('reports/inventory', params=params)
    
    # Payments
    async def get_payments(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get payment information."""
        return await self.get('payments', params=params)
    
    async def get_payment_settlements(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get payment settlements."""
        return await self.get('payments/settlements', params=params)
    
    # Quality Control
    async def get_qc_status(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get quality control status for products."""
        return await self.get('products/qc-status', params=params)
    
    # Brands
    async def get_brands(self) -> Dict[str, Any]:
        """Get all brands."""
        return await self.get('brands')
    
    # Attributes
    async def get_attributes(self, category_id: Optional[str] = None) -> Dict[str, Any]:
        """Get product attributes, optionally for a specific category."""
        endpoint = 'attributes'
        params = {}
        if category_id:
            params['category_id'] = category_id
        return await self.get(endpoint, params=params if params else None)
    
    async def close(self):
        """Close the REST client and clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def __str__(self) -> str:
        """String representation of the REST client."""
        return f"JumiaRESTClient(base_url={self.base_url})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the REST client."""
        return (f"JumiaRESTClient("
                f"base_url='{self.base_url}', "
                f"marketplace='{self.auth_manager.get_marketplace()}', "
                f"rate_limit={self.requests_per_minute}/min)")