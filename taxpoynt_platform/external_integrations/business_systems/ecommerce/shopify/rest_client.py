"""
Shopify E-commerce REST API Client
HTTP client for interacting with Shopify Admin REST API.
Handles rate limiting, pagination, and API response processing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urlencode
import aiohttp
import json

from .auth import ShopifyAuthManager
from .exceptions import (
    ShopifyConnectionError,
    ShopifyAPIError,
    ShopifyRateLimitError,
    create_shopify_exception
)

logger = logging.getLogger(__name__)


class ShopifyRestClient:
    """
    Shopify REST API Client
    
    Provides HTTP client functionality for Shopify Admin REST API including:
    - Order management and retrieval
    - Product and inventory operations
    - Customer data access
    - Store information retrieval
    - Automatic rate limit handling
    - Pagination support for large datasets
    - Webhook management
    """
    
    def __init__(self, auth_manager: ShopifyAuthManager):
        """
        Initialize Shopify REST client.
        
        Args:
            auth_manager: Shopify authentication manager
        """
        self.auth_manager = auth_manager
        self.base_url = auth_manager.api_base_url
        self.shop_name = auth_manager.shop_name
        
        # Rate limiting configuration
        self.rate_limit_config = {
            'calls_per_second': 2,  # Shopify allows 2 calls per second
            'burst_bucket_size': 40,  # Burst bucket capacity
            'retry_attempts': 3,
            'retry_delay': 1,  # Base delay in seconds
            'backoff_multiplier': 2
        }
        
        # Request tracking for rate limiting
        self._request_times: List[datetime] = []
        self._rate_limit_info: Dict[str, Any] = {}
        
        logger.info(f"Initialized Shopify REST client for shop: {self.shop_name}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Shopify API with rate limiting and error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            
        Returns:
            Dict: API response data
            
        Raises:
            ShopifyAPIError: If API request fails
            ShopifyRateLimitError: If rate limit exceeded
        """
        if not self.auth_manager.is_authenticated:
            await self.auth_manager.authenticate()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self.auth_manager.api_headers.copy()
        
        if headers:
            request_headers.update(headers)
        
        # Handle rate limiting
        await self._handle_rate_limiting()
        
        for attempt in range(self.rate_limit_config['retry_attempts']):
            try:
                async with aiohttp.ClientSession() as session:
                    # Prepare request parameters
                    request_kwargs = {
                        'headers': request_headers,
                        'timeout': aiohttp.ClientTimeout(total=30)
                    }
                    
                    if params:
                        request_kwargs['params'] = params
                    
                    if data:
                        request_kwargs['json'] = data
                    
                    # Make request
                    async with session.request(method, url, **request_kwargs) as response:
                        # Update rate limit info
                        self._update_rate_limit_info(response.headers)
                        
                        # Handle response
                        response_data = await self._handle_response(response, endpoint)
                        
                        # Track successful request
                        self._request_times.append(datetime.utcnow())
                        
                        return response_data
                        
            except ShopifyRateLimitError:
                if attempt < self.rate_limit_config['retry_attempts'] - 1:
                    delay = self.rate_limit_config['retry_delay'] * (
                        self.rate_limit_config['backoff_multiplier'] ** attempt
                    )
                    logger.info(f"Rate limit hit, retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise
                    
            except Exception as e:
                if attempt < self.rate_limit_config['retry_attempts'] - 1:
                    delay = self.rate_limit_config['retry_delay'] * (
                        self.rate_limit_config['backoff_multiplier'] ** attempt
                    )
                    logger.warning(f"Request failed, retrying in {delay} seconds: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    raise create_shopify_exception(e, {
                        'shop_name': self.shop_name,
                        'endpoint': endpoint,
                        'method': method
                    })
        
        raise ShopifyAPIError(f"Request failed after {self.rate_limit_config['retry_attempts']} attempts")
    
    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        endpoint: str
    ) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            if response.status == 200:
                return await response.json()
            
            elif response.status == 201:
                # Created - return response data
                return await response.json()
            
            elif response.status == 204:
                # No content - return empty dict
                return {}
            
            elif response.status == 400:
                error_data = await response.json()
                raise ShopifyAPIError(
                    f"Bad request: {error_data.get('errors', 'Unknown error')}",
                    status_code=400,
                    response_data=error_data,
                    endpoint=endpoint,
                    shop_name=self.shop_name
                )
            
            elif response.status == 401:
                raise ShopifyAPIError(
                    "Unauthorized - invalid or expired access token",
                    status_code=401,
                    endpoint=endpoint,
                    shop_name=self.shop_name
                )
            
            elif response.status == 403:
                raise ShopifyAPIError(
                    "Forbidden - insufficient permissions",
                    status_code=403,
                    endpoint=endpoint,
                    shop_name=self.shop_name
                )
            
            elif response.status == 404:
                raise ShopifyAPIError(
                    f"Resource not found: {endpoint}",
                    status_code=404,
                    endpoint=endpoint,
                    shop_name=self.shop_name
                )
            
            elif response.status == 422:
                error_data = await response.json()
                raise ShopifyAPIError(
                    f"Unprocessable entity: {error_data.get('errors', 'Validation failed')}",
                    status_code=422,
                    response_data=error_data,
                    endpoint=endpoint,
                    shop_name=self.shop_name
                )
            
            elif response.status == 429:
                retry_after = int(response.headers.get('Retry-After', 4))
                raise ShopifyRateLimitError(
                    "Rate limit exceeded",
                    retry_after=retry_after,
                    shop_name=self.shop_name
                )
            
            elif response.status >= 500:
                raise ShopifyAPIError(
                    f"Server error: {response.status}",
                    status_code=response.status,
                    endpoint=endpoint,
                    shop_name=self.shop_name
                )
            
            else:
                error_text = await response.text()
                raise ShopifyAPIError(
                    f"Unexpected response status {response.status}: {error_text}",
                    status_code=response.status,
                    endpoint=endpoint,
                    shop_name=self.shop_name
                )
                
        except aiohttp.ContentTypeError:
            # Handle non-JSON responses
            error_text = await response.text()
            raise ShopifyAPIError(
                f"Invalid response format: {error_text}",
                status_code=response.status,
                endpoint=endpoint,
                shop_name=self.shop_name
            )
    
    async def _handle_rate_limiting(self) -> None:
        """Handle rate limiting by implementing call bucket pattern."""
        now = datetime.utcnow()
        
        # Clean old requests (older than 1 second)
        cutoff_time = now - timedelta(seconds=1)
        self._request_times = [
            req_time for req_time in self._request_times
            if req_time > cutoff_time
        ]
        
        # Check if we need to wait
        if len(self._request_times) >= self.rate_limit_config['calls_per_second']:
            # Wait until we can make another request
            oldest_request = min(self._request_times)
            wait_until = oldest_request + timedelta(seconds=1)
            wait_time = (wait_until - now).total_seconds()
            
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
    
    def _update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """Update rate limit information from response headers."""
        # Shopify uses X-Shopify-Shop-Api-Call-Limit header
        call_limit_header = headers.get('X-Shopify-Shop-Api-Call-Limit', '')
        
        if call_limit_header:
            try:
                current_calls, max_calls = call_limit_header.split('/')
                self._rate_limit_info = {
                    'current_calls': int(current_calls),
                    'max_calls': int(max_calls),
                    'remaining_calls': int(max_calls) - int(current_calls),
                    'updated_at': datetime.utcnow()
                }
            except (ValueError, IndexError):
                logger.warning(f"Invalid call limit header format: {call_limit_header}")
    
    # Store/Shop Operations
    
    async def get_shop_info(self) -> Dict[str, Any]:
        """
        Get shop information.
        
        Returns:
            Dict: Shop information
        """
        response = await self._make_request('GET', '/shop.json')
        return response.get('shop', {})
    
    # Order Operations
    
    async def get_orders(
        self,
        limit: int = 50,
        since_id: Optional[str] = None,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None,
        updated_at_min: Optional[datetime] = None,
        updated_at_max: Optional[datetime] = None,
        status: Optional[str] = None,
        financial_status: Optional[str] = None,
        fulfillment_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get orders from Shopify.
        
        Args:
            limit: Number of orders to retrieve (max 250)
            since_id: Retrieve orders after this ID
            created_at_min: Minimum creation date
            created_at_max: Maximum creation date
            updated_at_min: Minimum update date
            updated_at_max: Maximum update date
            status: Order status filter
            financial_status: Financial status filter
            fulfillment_status: Fulfillment status filter
            
        Returns:
            List[Dict]: List of orders
        """
        params = {'limit': min(limit, 250)}
        
        if since_id:
            params['since_id'] = since_id
        if created_at_min:
            params['created_at_min'] = created_at_min.isoformat()
        if created_at_max:
            params['created_at_max'] = created_at_max.isoformat()
        if updated_at_min:
            params['updated_at_min'] = updated_at_min.isoformat()
        if updated_at_max:
            params['updated_at_max'] = updated_at_max.isoformat()
        if status:
            params['status'] = status
        if financial_status:
            params['financial_status'] = financial_status
        if fulfillment_status:
            params['fulfillment_status'] = fulfillment_status
        
        response = await self._make_request('GET', '/orders.json', params=params)
        return response.get('orders', [])
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Dict: Order data or None if not found
        """
        try:
            response = await self._make_request('GET', f'/orders/{order_id}.json')
            return response.get('order')
        except ShopifyAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_all_orders_paginated(
        self,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None,
        status: Optional[str] = None,
        batch_size: int = 250
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get all orders using pagination.
        
        Args:
            created_at_min: Minimum creation date
            created_at_max: Maximum creation date
            status: Order status filter
            batch_size: Number of orders per batch
            
        Yields:
            Dict: Individual order data
        """
        since_id = None
        
        while True:
            orders = await self.get_orders(
                limit=batch_size,
                since_id=since_id,
                created_at_min=created_at_min,
                created_at_max=created_at_max,
                status=status
            )
            
            if not orders:
                break
            
            for order in orders:
                yield order
            
            # Set since_id for next batch
            since_id = orders[-1]['id']
            
            # Small delay between batches
            await asyncio.sleep(0.1)
    
    # Product Operations
    
    async def get_products(
        self,
        limit: int = 50,
        since_id: Optional[str] = None,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from Shopify.
        
        Args:
            limit: Number of products to retrieve (max 250)
            since_id: Retrieve products after this ID
            created_at_min: Minimum creation date
            created_at_max: Maximum creation date
            
        Returns:
            List[Dict]: List of products
        """
        params = {'limit': min(limit, 250)}
        
        if since_id:
            params['since_id'] = since_id
        if created_at_min:
            params['created_at_min'] = created_at_min.isoformat()
        if created_at_max:
            params['created_at_max'] = created_at_max.isoformat()
        
        response = await self._make_request('GET', '/products.json', params=params)
        return response.get('products', [])
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Dict: Product data or None if not found
        """
        try:
            response = await self._make_request('GET', f'/products/{product_id}.json')
            return response.get('product')
        except ShopifyAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    # Customer Operations
    
    async def get_customers(
        self,
        limit: int = 50,
        since_id: Optional[str] = None,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get customers from Shopify.
        
        Args:
            limit: Number of customers to retrieve (max 250)
            since_id: Retrieve customers after this ID
            created_at_min: Minimum creation date
            created_at_max: Maximum creation date
            
        Returns:
            List[Dict]: List of customers
        """
        params = {'limit': min(limit, 250)}
        
        if since_id:
            params['since_id'] = since_id
        if created_at_min:
            params['created_at_min'] = created_at_min.isoformat()
        if created_at_max:
            params['created_at_max'] = created_at_max.isoformat()
        
        response = await self._make_request('GET', '/customers.json', params=params)
        return response.get('customers', [])
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific customer by ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dict: Customer data or None if not found
        """
        try:
            response = await self._make_request('GET', f'/customers/{customer_id}.json')
            return response.get('customer')
        except ShopifyAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    # Location and Inventory Operations
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """
        Get all locations.
        
        Returns:
            List[Dict]: List of locations
        """
        response = await self._make_request('GET', '/locations.json')
        return response.get('locations', [])
    
    async def get_inventory_levels(
        self,
        location_ids: Optional[List[str]] = None,
        inventory_item_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get inventory levels.
        
        Args:
            location_ids: Filter by location IDs
            inventory_item_ids: Filter by inventory item IDs
            
        Returns:
            List[Dict]: List of inventory levels
        """
        params = {}
        
        if location_ids:
            params['location_ids'] = ','.join(location_ids)
        if inventory_item_ids:
            params['inventory_item_ids'] = ','.join(inventory_item_ids)
        
        response = await self._make_request('GET', '/inventory_levels.json', params=params)
        return response.get('inventory_levels', [])
    
    # Webhook Operations
    
    async def get_webhooks(self) -> List[Dict[str, Any]]:
        """
        Get all webhooks.
        
        Returns:
            List[Dict]: List of webhooks
        """
        response = await self._make_request('GET', '/webhooks.json')
        return response.get('webhooks', [])
    
    async def create_webhook(
        self,
        topic: str,
        address: str,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Create a webhook.
        
        Args:
            topic: Webhook topic (e.g., 'orders/create')
            address: Webhook URL
            format: Webhook format ('json' or 'xml')
            
        Returns:
            Dict: Created webhook data
        """
        webhook_data = {
            'webhook': {
                'topic': topic,
                'address': address,
                'format': format
            }
        }
        
        response = await self._make_request('POST', '/webhooks.json', data=webhook_data)
        return response.get('webhook', {})
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            await self._make_request('DELETE', f'/webhooks/{webhook_id}.json')
            return True
        except ShopifyAPIError:
            return False
    
    # Batch Operations
    
    async def batch_get_orders(self, order_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple orders by IDs.
        
        Args:
            order_ids: List of order IDs
            
        Returns:
            List[Dict]: List of orders
        """
        orders = []
        
        # Process in small batches to avoid overwhelming the API
        for i in range(0, len(order_ids), 10):
            batch_ids = order_ids[i:i + 10]
            
            for order_id in batch_ids:
                try:
                    order = await self.get_order(order_id)
                    if order:
                        orders.append(order)
                except Exception as e:
                    logger.error(f"Failed to get order {order_id}: {str(e)}")
                    continue
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        return orders
    
    @property
    def rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information."""
        return self._rate_limit_info.copy()