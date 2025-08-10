"""
Magento E-commerce REST API Client
HTTP client for interacting with Magento REST API.
Handles authentication, rate limiting, pagination, and multi-store operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncGenerator
from urllib.parse import urlencode
import aiohttp
import json

from .auth import MagentoAuthManager
from .exceptions import (
    MagentoConnectionError,
    MagentoAPIError,
    MagentoRateLimitError,
    create_magento_exception
)

logger = logging.getLogger(__name__)


class MagentoRestClient:
    """
    Magento REST API Client
    
    Provides HTTP client functionality for Magento REST API including:
    - Order management and retrieval
    - Product and inventory operations
    - Customer data access
    - Store configuration and multi-store support
    - Category and attribute management
    - Advanced search and filtering
    - Rate limiting and error handling
    """
    
    def __init__(self, auth_manager: MagentoAuthManager):
        """
        Initialize Magento REST client.
        
        Args:
            auth_manager: Magento authentication manager
        """
        self.auth_manager = auth_manager
        self.base_url = auth_manager.api_base_url
        self.store_url = auth_manager.store_base_url
        
        # Rate limiting configuration
        self.rate_limit_config = {
            'requests_per_hour': 300,  # Conservative limit for Magento
            'burst_requests': 20,
            'retry_attempts': 3,
            'retry_delay': 2,  # Base delay in seconds
            'backoff_multiplier': 2
        }
        
        # Request tracking for rate limiting
        self._request_times: List[datetime] = []
        
        logger.info(f"Initialized Magento REST client for store: {self.store_url}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        store_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Magento API with authentication and error handling.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            store_code: Specific store code for multi-store operations
            
        Returns:
            Dict: API response data
            
        Raises:
            MagentoAPIError: If API request fails
            MagentoRateLimitError: If rate limit exceeded
        """
        if not self.auth_manager.is_authenticated:
            await self.auth_manager.authenticate()
        
        # Refresh token if needed
        await self.auth_manager.refresh_token_if_needed()
        
        # Handle rate limiting
        await self._handle_rate_limiting()
        
        for attempt in range(self.rate_limit_config['retry_attempts']):
            try:
                # Get headers and URL
                headers = self.auth_manager.api_headers
                
                if store_code:
                    url = self.auth_manager.get_store_specific_url(endpoint, store_code)
                else:
                    url = f"{self.base_url}{endpoint}"
                
                async with aiohttp.ClientSession() as session:
                    # Prepare request parameters
                    request_kwargs = {
                        'headers': headers,
                        'ssl': self.auth_manager.ssl_verification,
                        'timeout': aiohttp.ClientTimeout(total=60)  # Magento can be slow
                    }
                    
                    if params and method.upper() == 'GET':
                        request_kwargs['params'] = params
                    elif data:
                        request_kwargs['json'] = data
                    
                    # Make request
                    async with session.request(method, url, **request_kwargs) as response:
                        # Handle response
                        response_data = await self._handle_response(response, endpoint)
                        
                        # Track successful request
                        self._request_times.append(datetime.utcnow())
                        
                        return response_data
                        
            except MagentoRateLimitError:
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
                    raise create_magento_exception(e, {
                        'store_url': self.store_url,
                        'endpoint': endpoint,
                        'method': method
                    })
        
        raise MagentoAPIError(f"Request failed after {self.rate_limit_config['retry_attempts']} attempts")
    
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
                
                # Extract parameter errors if available
                if 'parameters' in error_data:
                    param_errors = []
                    for param in error_data['parameters']:
                        param_errors.append(f"{param.get('fieldName', 'field')}: {param.get('message', 'invalid')}")
                    error_message += f" - {', '.join(param_errors)}"
                
                raise MagentoAPIError(
                    f"Bad request: {error_message}",
                    status_code=400,
                    error_code='bad_request',
                    response_data=error_data,
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            elif response.status == 401:
                error_data = await response.json()
                error_message = error_data.get('message', 'Unauthorized')
                
                raise MagentoAPIError(
                    f"Unauthorized: {error_message}",
                    status_code=401,
                    error_code='unauthorized',
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            elif response.status == 403:
                error_data = await response.json()
                error_message = error_data.get('message', 'Forbidden')
                
                raise MagentoAPIError(
                    f"Forbidden: {error_message}",
                    status_code=403,
                    error_code='forbidden',
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            elif response.status == 404:
                error_data = await response.json()
                error_message = error_data.get('message', f'Resource not found: {endpoint}')
                
                raise MagentoAPIError(
                    error_message,
                    status_code=404,
                    error_code='not_found',
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            elif response.status == 429:
                retry_after = int(response.headers.get('Retry-After', 3600))  # Default 1 hour
                raise MagentoRateLimitError(
                    "Rate limit exceeded",
                    retry_after=retry_after,
                    store_url=self.store_url
                )
            
            elif response.status >= 500:
                error_text = await response.text()
                raise MagentoAPIError(
                    f"Server error: {response.status} - {error_text}",
                    status_code=response.status,
                    endpoint=endpoint,
                    store_url=self.store_url
                )
            
            else:
                error_text = await response.text()
                raise MagentoAPIError(
                    f"Unexpected response status {response.status}: {error_text}",
                    status_code=response.status,
                    endpoint=endpoint,
                    store_url=self.store_url
                )
                
        except aiohttp.ContentTypeError:
            # Handle non-JSON responses
            error_text = await response.text()
            raise MagentoAPIError(
                f"Invalid response format: {error_text}",
                status_code=response.status,
                endpoint=endpoint,
                store_url=self.store_url
            )
    
    async def _handle_rate_limiting(self) -> None:
        """Handle rate limiting by implementing request timing."""
        now = datetime.utcnow()
        
        # Clean old requests (older than 1 hour)
        cutoff_time = now - timedelta(hours=1)
        self._request_times = [
            req_time for req_time in self._request_times
            if req_time > cutoff_time
        ]
        
        # Check if we need to wait
        if len(self._request_times) >= self.rate_limit_config['requests_per_hour']:
            # Wait until we can make another request
            oldest_request = min(self._request_times)
            wait_until = oldest_request + timedelta(hours=1)
            wait_time = (wait_until - now).total_seconds()
            
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(min(wait_time, 60))  # Max 1 minute wait
    
    # Store/System Operations
    
    async def get_store_config(self, store_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get store configuration.
        
        Args:
            store_code: Specific store code
            
        Returns:
            List[Dict]: Store configuration
        """
        return await self._make_request('GET', '/store/storeConfigs', store_code=store_code)
    
    async def get_store_views(self) -> List[Dict[str, Any]]:
        """
        Get all store views.
        
        Returns:
            List[Dict]: List of store views
        """
        return await self._make_request('GET', '/store/storeViews')
    
    async def get_websites(self) -> List[Dict[str, Any]]:
        """
        Get all websites.
        
        Returns:
            List[Dict]: List of websites
        """
        return await self._make_request('GET', '/store/websites')
    
    # Order Operations
    
    async def get_orders(
        self,
        page_size: int = 20,
        current_page: int = 1,
        search_criteria: Optional[Dict[str, Any]] = None,
        store_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get orders from Magento.
        
        Args:
            page_size: Number of orders per page (max 100)
            current_page: Page number (1-based)
            search_criteria: Advanced search criteria
            store_code: Specific store code
            
        Returns:
            Dict: Orders response with items and search_criteria
        """
        params = {
            'searchCriteria[pageSize]': min(page_size, 100),
            'searchCriteria[currentPage]': current_page
        }
        
        # Add search criteria
        if search_criteria:
            filter_groups = search_criteria.get('filter_groups', [])
            for group_idx, group in enumerate(filter_groups):
                filters = group.get('filters', [])
                for filter_idx, filter_item in enumerate(filters):
                    field = filter_item.get('field')
                    value = filter_item.get('value')
                    condition_type = filter_item.get('condition_type', 'eq')
                    
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][field]'] = field
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][value]'] = value
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][condition_type]'] = condition_type
            
            # Add sort orders
            sort_orders = search_criteria.get('sort_orders', [])
            for sort_idx, sort_order in enumerate(sort_orders):
                field = sort_order.get('field')
                direction = sort_order.get('direction', 'ASC')
                
                params[f'searchCriteria[sortOrders][{sort_idx}][field]'] = field
                params[f'searchCriteria[sortOrders][{sort_idx}][direction]'] = direction
        
        return await self._make_request('GET', '/orders', params=params, store_code=store_code)
    
    async def get_order(self, order_id: str, store_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get specific order by ID.
        
        Args:
            order_id: Order ID
            store_code: Specific store code
            
        Returns:
            Dict: Order data or None if not found
        """
        try:
            return await self._make_request('GET', f'/orders/{order_id}', store_code=store_code)
        except MagentoAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def search_orders(
        self,
        filters: List[Dict[str, Any]],
        sort_orders: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 20,
        current_page: int = 1,
        store_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search orders with advanced criteria.
        
        Args:
            filters: List of filter dictionaries with field, value, condition_type
            sort_orders: List of sort order dictionaries with field, direction
            page_size: Number of orders per page
            current_page: Page number
            store_code: Specific store code
            
        Returns:
            Dict: Search results
        """
        search_criteria = {
            'filter_groups': [{'filters': filters}],
            'sort_orders': sort_orders or []
        }
        
        return await self.get_orders(
            page_size=page_size,
            current_page=current_page,
            search_criteria=search_criteria,
            store_code=store_code
        )
    
    # Product Operations
    
    async def get_products(
        self,
        page_size: int = 20,
        current_page: int = 1,
        search_criteria: Optional[Dict[str, Any]] = None,
        store_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get products from Magento.
        
        Args:
            page_size: Number of products per page (max 100)
            current_page: Page number (1-based)
            search_criteria: Advanced search criteria
            store_code: Specific store code
            
        Returns:
            Dict: Products response with items and search_criteria
        """
        params = {
            'searchCriteria[pageSize]': min(page_size, 100),
            'searchCriteria[currentPage]': current_page
        }
        
        # Add search criteria (similar to orders)
        if search_criteria:
            filter_groups = search_criteria.get('filter_groups', [])
            for group_idx, group in enumerate(filter_groups):
                filters = group.get('filters', [])
                for filter_idx, filter_item in enumerate(filters):
                    field = filter_item.get('field')
                    value = filter_item.get('value')
                    condition_type = filter_item.get('condition_type', 'eq')
                    
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][field]'] = field
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][value]'] = value
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][condition_type]'] = condition_type
        
        return await self._make_request('GET', '/products', params=params, store_code=store_code)
    
    async def get_product(self, sku: str, store_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get specific product by SKU.
        
        Args:
            sku: Product SKU
            store_code: Specific store code
            
        Returns:
            Dict: Product data or None if not found
        """
        try:
            # URL encode the SKU to handle special characters
            from urllib.parse import quote
            encoded_sku = quote(sku, safe='')
            return await self._make_request('GET', f'/products/{encoded_sku}', store_code=store_code)
        except MagentoAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    # Customer Operations
    
    async def get_customers(
        self,
        page_size: int = 20,
        current_page: int = 1,
        search_criteria: Optional[Dict[str, Any]] = None,
        store_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get customers from Magento.
        
        Args:
            page_size: Number of customers per page (max 100)
            current_page: Page number (1-based)
            search_criteria: Advanced search criteria
            store_code: Specific store code
            
        Returns:
            Dict: Customers response with items and search_criteria
        """
        params = {
            'searchCriteria[pageSize]': min(page_size, 100),
            'searchCriteria[currentPage]': current_page
        }
        
        # Add search criteria (similar to orders)
        if search_criteria:
            filter_groups = search_criteria.get('filter_groups', [])
            for group_idx, group in enumerate(filter_groups):
                filters = group.get('filters', [])
                for filter_idx, filter_item in enumerate(filters):
                    field = filter_item.get('field')
                    value = filter_item.get('value')
                    condition_type = filter_item.get('condition_type', 'eq')
                    
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][field]'] = field
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][value]'] = value
                    params[f'searchCriteria[filter_groups][{group_idx}][filters][{filter_idx}][condition_type]'] = condition_type
        
        return await self._make_request('GET', '/customers/search', params=params, store_code=store_code)
    
    async def get_customer(self, customer_id: str, store_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get specific customer by ID.
        
        Args:
            customer_id: Customer ID
            store_code: Specific store code
            
        Returns:
            Dict: Customer data or None if not found
        """
        try:
            return await self._make_request('GET', f'/customers/{customer_id}', store_code=store_code)
        except MagentoAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    # Category Operations
    
    async def get_categories(
        self,
        root_category_id: Optional[int] = None,
        depth: Optional[int] = None,
        store_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get categories from Magento.
        
        Args:
            root_category_id: Root category ID
            depth: Category tree depth
            store_code: Specific store code
            
        Returns:
            Dict: Categories tree
        """
        params = {}
        if root_category_id:
            params['rootCategoryId'] = root_category_id
        if depth:
            params['depth'] = depth
        
        return await self._make_request('GET', '/categories', params=params, store_code=store_code)
    
    async def get_category(self, category_id: str, store_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get specific category by ID.
        
        Args:
            category_id: Category ID
            store_code: Specific store code
            
        Returns:
            Dict: Category data or None if not found
        """
        try:
            return await self._make_request('GET', f'/categories/{category_id}', store_code=store_code)
        except MagentoAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    # Inventory Operations
    
    async def get_stock_items(
        self,
        page_size: int = 20,
        current_page: int = 1,
        search_criteria: Optional[Dict[str, Any]] = None,
        store_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get stock items from Magento.
        
        Args:
            page_size: Number of items per page
            current_page: Page number
            search_criteria: Advanced search criteria
            store_code: Specific store code
            
        Returns:
            Dict: Stock items response
        """
        params = {
            'searchCriteria[pageSize]': min(page_size, 100),
            'searchCriteria[currentPage]': current_page
        }
        
        return await self._make_request('GET', '/stockItems/search', params=params, store_code=store_code)
    
    # Invoice Operations
    
    async def get_invoices(
        self,
        page_size: int = 20,
        current_page: int = 1,
        search_criteria: Optional[Dict[str, Any]] = None,
        store_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get invoices from Magento.
        
        Args:
            page_size: Number of invoices per page
            current_page: Page number
            search_criteria: Advanced search criteria
            store_code: Specific store code
            
        Returns:
            Dict: Invoices response
        """
        params = {
            'searchCriteria[pageSize]': min(page_size, 100),
            'searchCriteria[currentPage]': current_page
        }
        
        return await self._make_request('GET', '/invoices', params=params, store_code=store_code)
    
    async def get_invoice(self, invoice_id: str, store_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get specific invoice by ID.
        
        Args:
            invoice_id: Invoice ID
            store_code: Specific store code
            
        Returns:
            Dict: Invoice data or None if not found
        """
        try:
            return await self._make_request('GET', f'/invoices/{invoice_id}', store_code=store_code)
        except MagentoAPIError as e:
            if e.status_code == 404:
                return None
            raise
    
    # Batch Operations
    
    async def batch_get_orders(self, order_ids: List[str], store_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get multiple orders by IDs.
        
        Args:
            order_ids: List of order IDs
            store_code: Specific store code
            
        Returns:
            List[Dict]: List of orders
        """
        orders = []
        
        # Process in small batches to avoid overwhelming the API
        for i in range(0, len(order_ids), 10):
            batch_ids = order_ids[i:i + 10]
            
            for order_id in batch_ids:
                try:
                    order = await self.get_order(order_id, store_code)
                    if order:
                        orders.append(order)
                except Exception as e:
                    logger.error(f"Failed to get order {order_id}: {str(e)}")
                    continue
            
            # Small delay between batches
            await asyncio.sleep(0.2)
        
        return orders
    
    # Pagination Helper
    
    async def get_all_orders_paginated(
        self,
        search_criteria: Optional[Dict[str, Any]] = None,
        page_size: int = 20,
        store_code: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get all orders using pagination.
        
        Args:
            search_criteria: Search criteria for filtering
            page_size: Number of orders per page
            store_code: Specific store code
            
        Yields:
            Dict: Individual order data
        """
        current_page = 1
        
        while True:
            orders_response = await self.get_orders(
                page_size=page_size,
                current_page=current_page,
                search_criteria=search_criteria,
                store_code=store_code
            )
            
            orders = orders_response.get('items', [])
            if not orders:
                break
            
            for order in orders:
                yield order
            
            # Check if we've reached the last page
            search_criteria_response = orders_response.get('search_criteria', {})
            total_count = orders_response.get('total_count', 0)
            page_size_actual = search_criteria_response.get('page_size', page_size)
            
            if current_page * page_size_actual >= total_count:
                break
            
            current_page += 1
            
            # Small delay between requests
            await asyncio.sleep(0.1)
    
    @property
    def request_history_count(self) -> int:
        """Get number of recent requests for rate limiting."""
        return len(self._request_times)