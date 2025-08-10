"""
WooCommerce E-commerce REST API Client
HTTP client for interacting with WooCommerce REST API.
Handles authentication, rate limiting, pagination, and API response processing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urlencode
import aiohttp
import json

from .auth import WooCommerceAuthManager
from .exceptions import (
    WooCommerceConnectionError,
    WooCommerceAPIError,
    WooCommerceRateLimitError,
    create_woocommerce_exception
)

logger = logging.getLogger(__name__)


class WooCommerceRestClient:
    """
    WooCommerce REST API Client
    
    Provides HTTP client functionality for WooCommerce REST API including:
    - Order management and retrieval
    - Product and inventory operations
    - Customer data access
    - Store settings and system status
    - Webhook management
    - Automatic pagination support
    - Rate limiting and error handling
    """
    
    def __init__(self, auth_manager: WooCommerceAuthManager):
        """
        Initialize WooCommerce REST client.
        
        Args:
            auth_manager: WooCommerce authentication manager
        """
        self.auth_manager = auth_manager
        self.base_url = auth_manager.api_base_url
        self.store_url = auth_manager.store_base_url
        
        # Rate limiting configuration
        self.rate_limit_config = {
            'requests_per_minute': 60,  # Conservative limit
            'burst_requests': 10,
            'retry_attempts': 3,
            'retry_delay': 2,  # Base delay in seconds
            'backoff_multiplier': 2
        }
        
        # Request tracking for rate limiting
        self._request_times: List[datetime] = []
        
        logger.info(f"Initialized WooCommerce REST client for store: {self.store_url}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to WooCommerce API with authentication and error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            
        Returns:
            Dict: API response data
            
        Raises:
            WooCommerceAPIError: If API request fails
            WooCommerceRateLimitError: If rate limit exceeded
        """
        if not self.auth_manager.is_authenticated:
            await self.auth_manager.authenticate()
        
        # Handle rate limiting
        await self._handle_rate_limiting()
        
        for attempt in range(self.rate_limit_config['retry_attempts']):
            try:
                # Get headers and URL
                headers = await self.auth_manager.api_headers_method(method, endpoint, params)
                
                if self.auth_manager.uses_oauth:
                    url = f"{self.base_url}{endpoint}"
                    request_params = params
                else:
                    # For basic auth, include credentials in URL
                    url = self.auth_manager.construct_api_url(endpoint, params)
                    request_params = None
                
                async with aiohttp.ClientSession() as session:
                    # Prepare request parameters
                    request_kwargs = {
                        'headers': headers,
                        'ssl': self.auth_manager.ssl_verification,
                        'timeout': aiohttp.ClientTimeout(total=30)
                    }
                    
                    if request_params and method.upper() == 'GET':
                        request_kwargs['params'] = request_params
                    elif data:
                        request_kwargs['json'] = data
                    
                    # Make request
                    async with session.request(method, url, **request_kwargs) as response:
                        # Handle response
                        response_data = await self._handle_response(response, endpoint)
                        
                        # Track successful request
                        self._request_times.append(datetime.utcnow())
                        
                        return response_data
                        
            except WooCommerceRateLimitError:
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
                    raise create_woocommerce_exception(e, {
                        'store_url': self.store_url,
                        'endpoint': endpoint,
                        'method': method
                    })
        
        raise WooCommerceAPIError(f"Request failed after {self.rate_limit_config['retry_attempts']} attempts")
    
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
                error_message = error_data.get('message', 'Bad request')
                error_code = error_data.get('code', 'bad_request')
                
                raise WooCommerceAPIError(
                    f"Bad request: {error_message}",
                    status_code=400,
                    error_code=error_code,
                    response_data=error_data,
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            elif response.status == 401:
                error_data = await response.json()
                error_message = error_data.get('message', 'Unauthorized')
                
                raise WooCommerceAPIError(
                    f"Unauthorized: {error_message}",
                    status_code=401,
                    error_code='unauthorized',
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            elif response.status == 403:
                error_data = await response.json()
                error_message = error_data.get('message', 'Forbidden')
                
                raise WooCommerceAPIError(
                    f"Forbidden: {error_message}",
                    status_code=403,
                    error_code='forbidden',
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            elif response.status == 404:
                error_data = await response.json()
                error_message = error_data.get('message', f'Resource not found: {endpoint}')
                
                raise WooCommerceAPIError(
                    error_message,
                    status_code=404,
                    error_code='not_found',
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            elif response.status == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise WooCommerceRateLimitError(
                    "Rate limit exceeded",
                    retry_after=retry_after,
                    store_url=self.store_url
                )
            
            elif response.status >= 500:
                error_text = await response.text()
                raise WooCommerceAPIError(
                    f"Server error: {response.status} - {error_text}",
                    status_code=response.status,
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            else:
                error_text = await response.text()
                raise WooCommerceAPIError(
                    f"Unexpected response status {response.status}: {error_text}",
                    status_code=response.status,
                    endpoint=endpoint,
                    store_url=self.store_url
                )
                
        except aiohttp.ContentTypeError:
            # Handle non-JSON responses
            error_text = await response.text()
            raise WooCommerceAPIError(
                f"Invalid response format: {error_text}",
                status_code=response.status,
                endpoint=endpoint,
                store_url=self.store_url
            )
    
    async def _handle_rate_limiting(self) -> None:
        """Handle rate limiting by implementing request timing."""
        now = datetime.utcnow()
        
        # Clean old requests (older than 1 minute)
        cutoff_time = now - timedelta(minutes=1)
        self._request_times = [
            req_time for req_time in self._request_times
            if req_time > cutoff_time
        ]
        
        # Check if we need to wait
        if len(self._request_times) >= self.rate_limit_config['requests_per_minute']:
            # Wait until we can make another request
            oldest_request = min(self._request_times)
            wait_until = oldest_request + timedelta(minutes=1)
            wait_time = (wait_until - now).total_seconds()
            
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
    
    # Store/System Operations
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get WooCommerce system status.
        
        Returns:
            Dict: System status information
        """
        return await self._make_request('GET', '/system_status')
    
    async def get_store_settings(self) -> List[Dict[str, Any]]:
        """
        Get store settings.
        
        Returns:
            List[Dict]: Store settings
        """
        return await self._make_request('GET', '/settings')
    
    # Order Operations
    
    async def get_orders(
        self,
        per_page: int = 10,
        page: int = 1,
        after: Optional[str] = None,
        before: Optional[str] = None,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        status: Optional[str] = None,
        customer: Optional[int] = None,
        product: Optional[int] = None,
        order_by: str = 'date',
        order: str = 'desc'
    ) -> List[Dict[str, Any]]:
        """
        Get orders from WooCommerce.
        
        Args:
            per_page: Number of orders per page (max 100)
            page: Page number
            after: Retrieve orders created after this date (ISO8601)
            before: Retrieve orders created before this date (ISO8601)
            modified_after: Retrieve orders modified after this date (ISO8601)
            modified_before: Retrieve orders modified before this date (ISO8601)
            status: Order status filter
            customer: Customer ID filter
            product: Product ID filter
            order_by: Sort orders by field
            order: Sort order (asc/desc)
            
        Returns:
            List[Dict]: List of orders
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page,
            'orderby': order_by,
            'order': order
        }
        
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if modified_after:
            params['modified_after'] = modified_after
        if modified_before:
            params['modified_before'] = modified_before
        if status:
            params['status'] = status
        if customer:
            params['customer'] = customer
        if product:
            params['product'] = product
        
        return await self._make_request('GET', '/orders', params=params)
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Dict: Order data or None if not found
        """
        try:
            return await self._make_request('GET', f'/orders/{order_id}')
        except WooCommerceAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_all_orders_paginated(
        self,
        after: Optional[str] = None,
        before: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 100
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get all orders using pagination.
        
        Args:
            after: Minimum creation date (ISO8601)
            before: Maximum creation date (ISO8601)
            status: Order status filter
            per_page: Number of orders per page
            
        Yields:
            Dict: Individual order data
        """
        page = 1
        
        while True:
            orders = await self.get_orders(
                per_page=per_page,
                page=page,
                after=after,
                before=before,
                status=status
            )
            
            if not orders:
                break
            
            for order in orders:
                yield order
            
            # Check if we got fewer results than requested (last page)
            if len(orders) < per_page:
                break
            
            page += 1
            
            # Small delay between requests
            await asyncio.sleep(0.1)
    
    # Product Operations
    
    async def get_products(
        self,
        per_page: int = 10,
        page: int = 1,
        search: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        sku: Optional[str] = None,
        featured: Optional[bool] = None,
        order_by: str = 'date',
        order: str = 'desc'
    ) -> List[Dict[str, Any]]:
        """
        Get products from WooCommerce.
        
        Args:
            per_page: Number of products per page (max 100)
            page: Page number
            search: Search term
            after: Retrieve products created after this date (ISO8601)
            before: Retrieve products created before this date (ISO8601)
            modified_after: Retrieve products modified after this date (ISO8601)
            modified_before: Retrieve products modified before this date (ISO8601)
            status: Product status filter
            type: Product type filter
            category: Category slug filter
            tag: Tag slug filter
            sku: SKU filter
            featured: Featured products filter
            order_by: Sort products by field
            order: Sort order (asc/desc)
            
        Returns:
            List[Dict]: List of products
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page,
            'orderby': order_by,
            'order': order
        }
        
        if search:
            params['search'] = search
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if modified_after:
            params['modified_after'] = modified_after
        if modified_before:
            params['modified_before'] = modified_before
        if status:
            params['status'] = status
        if type:
            params['type'] = type
        if category:
            params['category'] = category
        if tag:
            params['tag'] = tag
        if sku:
            params['sku'] = sku
        if featured is not None:
            params['featured'] = featured
        
        return await self._make_request('GET', '/products', params=params)
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Dict: Product data or None if not found
        """
        try:
            return await self._make_request('GET', f'/products/{product_id}')
        except WooCommerceAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    # Customer Operations
    
    async def get_customers(
        self,
        per_page: int = 10,
        page: int = 1,
        search: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        order_by: str = 'date_registered',
        order: str = 'desc'
    ) -> List[Dict[str, Any]]:
        """
        Get customers from WooCommerce.
        
        Args:
            per_page: Number of customers per page (max 100)
            page: Page number
            search: Search term
            email: Email filter
            role: Role filter
            order_by: Sort customers by field
            order: Sort order (asc/desc)
            
        Returns:
            List[Dict]: List of customers
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page,
            'orderby': order_by,
            'order': order
        }
        
        if search:
            params['search'] = search
        if email:
            params['email'] = email
        if role:
            params['role'] = role
        
        return await self._make_request('GET', '/customers', params=params)
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific customer by ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dict: Customer data or None if not found
        """
        try:
            return await self._make_request('GET', f'/customers/{customer_id}')
        except WooCommerceAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    # Webhook Operations
    
    async def get_webhooks(self) -> List[Dict[str, Any]]:
        """
        Get all webhooks.
        
        Returns:
            List[Dict]: List of webhooks
        """
        return await self._make_request('GET', '/webhooks')
    
    async def create_webhook(
        self,
        topic: str,
        delivery_url: str,
        secret: Optional[str] = None,
        status: str = 'active'
    ) -> Dict[str, Any]:
        """
        Create a webhook.
        
        Args:
            topic: Webhook topic (e.g., 'order.created')
            delivery_url: Webhook delivery URL
            secret: Webhook secret for signature verification
            status: Webhook status
            
        Returns:
            Dict: Created webhook data
        """
        webhook_data = {
            'topic': topic,
            'delivery_url': delivery_url,
            'status': status
        }
        
        if secret:
            webhook_data['secret'] = secret
        
        return await self._make_request('POST', '/webhooks', data=webhook_data)
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            await self._make_request('DELETE', f'/webhooks/{webhook_id}')
            return True
        except WooCommerceAPIError:
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
            await asyncio.sleep(0.2)
        
        return orders
    
    # Product Categories and Tags
    
    async def get_product_categories(
        self,
        per_page: int = 10,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get product categories.
        
        Args:
            per_page: Number of categories per page
            page: Page number
            
        Returns:
            List[Dict]: List of categories
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page
        }
        
        return await self._make_request('GET', '/products/categories', params=params)
    
    async def get_product_tags(
        self,
        per_page: int = 10,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get product tags.
        
        Args:
            per_page: Number of tags per page
            page: Page number
            
        Returns:
            List[Dict]: List of tags
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page
        }
        
        return await self._make_request('GET', '/products/tags', params=params)
    
    # Tax Operations
    
    async def get_tax_rates(self) -> List[Dict[str, Any]]:
        """
        Get tax rates.
        
        Returns:
            List[Dict]: List of tax rates
        """
        return await self._make_request('GET', '/taxes')
    
    async def get_tax_classes(self) -> List[Dict[str, Any]]:
        """
        Get tax classes.
        
        Returns:
            List[Dict]: List of tax classes
        """
        return await self._make_request('GET', '/taxes/classes')
    
    @property
    def request_history_count(self) -> int:
        """Get number of recent requests for rate limiting."""
        return len(self._request_times)