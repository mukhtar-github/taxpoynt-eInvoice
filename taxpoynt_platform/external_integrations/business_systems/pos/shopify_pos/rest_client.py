"""
Shopify POS REST Client

Handles REST API and GraphQL communication with Shopify Admin API including orders, 
customers, products, locations, and webhook management.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin

import aiohttp

from .auth import ShopifyAuthenticator
from .exceptions import (
    ShopifyAPIError, ShopifyConnectionError, ShopifyRateLimitError,
    ShopifyNotFoundError, ShopifyTimeoutError, ShopifyPermissionError,
    create_shopify_exception
)

logger = logging.getLogger(__name__)


class ShopifyRESTClient:
    """
    Shopify POS REST API client for TaxPoynt eInvoice - System Integrator Functions.
    
    Provides comprehensive Shopify Admin API functionality including:
    - Orders API: Order management and transaction data
    - Customers API: Customer data management
    - Products API: Product and inventory management
    - Locations API: Store/location management
    - Webhooks API: Event subscription management
    - GraphQL API: Advanced queries and mutations
    """
    
    def __init__(self, authenticator: ShopifyAuthenticator):
        """Initialize Shopify REST client with authenticator."""
        self.auth = authenticator
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting settings (Shopify call limit bucket)
        self.rate_limit_delay = 0.5  # 500ms between requests
        self.max_retries = 3
        self.retry_delay = 2.0  # 2 second initial retry delay
        
        # Request timeout settings
        self.request_timeout = 30.0
        self.connect_timeout = 10.0
        
        # Shopify-specific settings
        self.call_limit_threshold = 35  # Stay under 40 calls per bucket
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to Shopify Admin API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds
        
        Returns:
            API response data
        
        Raises:
            ShopifyAPIError: For API errors
            ShopifyConnectionError: For connection issues
        """
        # Ensure we have valid authentication
        if not await self.auth.ensure_valid_token():
            raise ShopifyConnectionError("Failed to obtain valid authentication token")
        
        url = urljoin(self.auth.base_url, endpoint)
        request_timeout = timeout or self.request_timeout
        
        # Prepare headers
        request_headers = await self.auth._get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        # Apply rate limiting
        await self._rate_limit_delay()
        
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                if not self.auth.session:
                    self.auth.session = await self.auth._create_session()
                
                async with self.auth.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=request_headers,
                    timeout=aiohttp.ClientTimeout(total=request_timeout, connect=self.connect_timeout)
                ) as response:
                    # Check rate limit headers
                    call_limit = response.headers.get('X-Shopify-Shop-Api-Call-Limit')
                    if call_limit:
                        self._handle_rate_limit_headers(call_limit)
                    
                    response_data = await response.json()
                    
                    # Handle successful responses
                    if 200 <= response.status < 300:
                        return response_data
                    
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                        if retry_count < self.max_retries:
                            self.logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                            await asyncio.sleep(retry_after)
                            retry_count += 1
                            continue
                        else:
                            raise ShopifyRateLimitError(
                                message="Shopify API rate limit exceeded",
                                retry_after=retry_after,
                                call_limit=call_limit
                            )
                    
                    # Handle authentication errors
                    if response.status == 401:
                        # Try to re-authenticate once
                        if retry_count == 0:
                            auth_success = await self.auth.authenticate()
                            if auth_success:
                                request_headers = await self.auth._get_auth_headers()
                                if headers:
                                    request_headers.update(headers)
                                retry_count += 1
                                continue
                    
                    # Handle permission errors
                    if response.status == 403:
                        raise ShopifyPermissionError(
                            message="Insufficient permissions for Shopify API request",
                            details={'response_data': response_data}
                        )
                    
                    # Handle not found errors
                    if response.status == 404:
                        raise ShopifyNotFoundError(
                            resource_type="resource",
                            details={'response_data': response_data, 'url': url}
                        )
                    
                    # Handle other API errors
                    raise ShopifyAPIError.from_response(
                        response_data=response_data,
                        status_code=response.status
                    )
            
            except aiohttp.ClientTimeout:
                if retry_count < self.max_retries:
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay * retry_count)
                    continue
                raise ShopifyTimeoutError(
                    message=f"Shopify API request timeout after {request_timeout} seconds",
                    timeout_duration=request_timeout
                )
            
            except aiohttp.ClientError as e:
                if retry_count < self.max_retries:
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay * retry_count)
                    continue
                raise ShopifyConnectionError(f"Shopify API connection error: {str(e)}")
            
            except Exception as e:
                if isinstance(e, (ShopifyAPIError, ShopifyConnectionError, ShopifyRateLimitError)):
                    raise
                
                if retry_count < self.max_retries:
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay * retry_count)
                    continue
                
                raise ShopifyAPIError(f"Unexpected error in Shopify API request: {str(e)}")
        
        raise ShopifyAPIError("Maximum retry attempts exceeded")
    
    def _handle_rate_limit_headers(self, call_limit: str):
        """Handle Shopify rate limit headers."""
        try:
            # Parse call limit: "current/max"
            current, maximum = call_limit.split('/')
            current_calls = int(current)
            max_calls = int(maximum)
            
            # If approaching limit, increase delay
            if current_calls >= self.call_limit_threshold:
                self.rate_limit_delay = min(2.0, self.rate_limit_delay * 1.5)
            else:
                self.rate_limit_delay = max(0.5, self.rate_limit_delay * 0.9)
                
        except (ValueError, AttributeError):
            # Fallback to default delay if header parsing fails
            pass
    
    async def _rate_limit_delay(self):
        """Apply rate limiting delay."""
        await asyncio.sleep(self.rate_limit_delay)
    
    async def _make_graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GraphQL request to Shopify Admin API.
        
        Args:
            query: GraphQL query string
            variables: Query variables
        
        Returns:
            GraphQL response data
        """
        graphql_data = {
            'query': query
        }
        
        if variables:
            graphql_data['variables'] = variables
        
        return await self._make_request(
            method='POST',
            endpoint=self.auth.api_endpoints['graphql'],
            data=graphql_data
        )
    
    # Orders API
    
    async def get_orders(
        self,
        status: Optional[str] = None,
        financial_status: Optional[str] = None,
        fulfillment_status: Optional[str] = None,
        created_at_min: Optional[str] = None,
        created_at_max: Optional[str] = None,
        updated_at_min: Optional[str] = None,
        updated_at_max: Optional[str] = None,
        processed_at_min: Optional[str] = None,
        processed_at_max: Optional[str] = None,
        limit: Optional[int] = None,
        since_id: Optional[str] = None,
        fields: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve orders from Shopify.
        
        Args:
            status: Order status filter
            financial_status: Financial status filter
            fulfillment_status: Fulfillment status filter
            created_at_min: Minimum creation date
            created_at_max: Maximum creation date
            updated_at_min: Minimum update date
            updated_at_max: Maximum update date
            processed_at_min: Minimum processing date
            processed_at_max: Maximum processing date
            limit: Maximum number of results
            since_id: Get orders after this ID
            fields: Comma-separated list of fields to return
        
        Returns:
            Orders response with list of orders
        """
        try:
            params = {}
            
            if status:
                params['status'] = status
            if financial_status:
                params['financial_status'] = financial_status
            if fulfillment_status:
                params['fulfillment_status'] = fulfillment_status
            if created_at_min:
                params['created_at_min'] = created_at_min
            if created_at_max:
                params['created_at_max'] = created_at_max
            if updated_at_min:
                params['updated_at_min'] = updated_at_min
            if updated_at_max:
                params['updated_at_max'] = updated_at_max
            if processed_at_min:
                params['processed_at_min'] = processed_at_min
            if processed_at_max:
                params['processed_at_max'] = processed_at_max
            if limit:
                params['limit'] = min(limit, 250)  # Shopify API limit
            if since_id:
                params['since_id'] = since_id
            if fields:
                params['fields'] = fields
            
            response = await self._make_request('GET', self.auth.api_endpoints['orders'], params=params)
            return response
        except Exception as e:
            self.logger.error(f"Error retrieving orders: {str(e)}")
            raise
    
    async def get_order(self, order_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve specific order by ID.
        
        Args:
            order_id: Shopify order ID
            fields: Comma-separated list of fields to return
        
        Returns:
            Order data
        """
        try:
            params = {}
            if fields:
                params['fields'] = fields
            
            endpoint = f"{self.auth.api_endpoints['orders']}/{order_id}.json"
            response = await self._make_request('GET', endpoint, params=params)
            return response.get('order', {})
        except Exception as e:
            self.logger.error(f"Error retrieving order {order_id}: {str(e)}")
            raise
    
    async def get_order_transactions(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieve transactions for a specific order.
        
        Args:
            order_id: Shopify order ID
        
        Returns:
            Transactions data
        """
        try:
            endpoint = self.auth.api_endpoints['transactions'].format(order_id=order_id)
            response = await self._make_request('GET', endpoint)
            return response
        except Exception as e:
            self.logger.error(f"Error retrieving transactions for order {order_id}: {str(e)}")
            raise
    
    # Customers API
    
    async def get_customers(
        self,
        limit: Optional[int] = None,
        since_id: Optional[str] = None,
        created_at_min: Optional[str] = None,
        created_at_max: Optional[str] = None,
        updated_at_min: Optional[str] = None,
        updated_at_max: Optional[str] = None,
        fields: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve customers from Shopify.
        
        Args:
            limit: Maximum number of results
            since_id: Get customers after this ID
            created_at_min: Minimum creation date
            created_at_max: Maximum creation date
            updated_at_min: Minimum update date
            updated_at_max: Maximum update date
            fields: Comma-separated list of fields to return
        
        Returns:
            Customers response
        """
        try:
            params = {}
            
            if limit:
                params['limit'] = min(limit, 250)
            if since_id:
                params['since_id'] = since_id
            if created_at_min:
                params['created_at_min'] = created_at_min
            if created_at_max:
                params['created_at_max'] = created_at_max
            if updated_at_min:
                params['updated_at_min'] = updated_at_min
            if updated_at_max:
                params['updated_at_max'] = updated_at_max
            if fields:
                params['fields'] = fields
            
            response = await self._make_request('GET', self.auth.api_endpoints['customers'], params=params)
            return response
        except Exception as e:
            self.logger.error(f"Error retrieving customers: {str(e)}")
            raise
    
    async def get_customer(self, customer_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve specific customer by ID.
        
        Args:
            customer_id: Shopify customer ID
            fields: Comma-separated list of fields to return
        
        Returns:
            Customer data
        """
        try:
            params = {}
            if fields:
                params['fields'] = fields
            
            endpoint = f"{self.auth.api_endpoints['customers']}/{customer_id}.json"
            response = await self._make_request('GET', endpoint, params=params)
            return response.get('customer', {})
        except Exception as e:
            self.logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
            raise
    
    # Products API
    
    async def get_products(
        self,
        limit: Optional[int] = None,
        since_id: Optional[str] = None,
        vendor: Optional[str] = None,
        handle: Optional[str] = None,
        product_type: Optional[str] = None,
        collection_id: Optional[str] = None,
        created_at_min: Optional[str] = None,
        created_at_max: Optional[str] = None,
        updated_at_min: Optional[str] = None,
        updated_at_max: Optional[str] = None,
        published_at_min: Optional[str] = None,
        published_at_max: Optional[str] = None,
        published_status: Optional[str] = None,
        fields: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve products from Shopify.
        
        Args:
            limit: Maximum number of results
            since_id: Get products after this ID
            vendor: Filter by vendor
            handle: Filter by handle
            product_type: Filter by product type
            collection_id: Filter by collection ID
            created_at_min: Minimum creation date
            created_at_max: Maximum creation date
            updated_at_min: Minimum update date
            updated_at_max: Maximum update date
            published_at_min: Minimum published date
            published_at_max: Maximum published date
            published_status: Published status filter
            fields: Comma-separated list of fields to return
        
        Returns:
            Products response
        """
        try:
            params = {}
            
            if limit:
                params['limit'] = min(limit, 250)
            if since_id:
                params['since_id'] = since_id
            if vendor:
                params['vendor'] = vendor
            if handle:
                params['handle'] = handle
            if product_type:
                params['product_type'] = product_type
            if collection_id:
                params['collection_id'] = collection_id
            if created_at_min:
                params['created_at_min'] = created_at_min
            if created_at_max:
                params['created_at_max'] = created_at_max
            if updated_at_min:
                params['updated_at_min'] = updated_at_min
            if updated_at_max:
                params['updated_at_max'] = updated_at_max
            if published_at_min:
                params['published_at_min'] = published_at_min
            if published_at_max:
                params['published_at_max'] = published_at_max
            if published_status:
                params['published_status'] = published_status
            if fields:
                params['fields'] = fields
            
            response = await self._make_request('GET', self.auth.api_endpoints['products'], params=params)
            return response
        except Exception as e:
            self.logger.error(f"Error retrieving products: {str(e)}")
            raise
    
    async def get_product(self, product_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve specific product by ID.
        
        Args:
            product_id: Shopify product ID
            fields: Comma-separated list of fields to return
        
        Returns:
            Product data
        """
        try:
            params = {}
            if fields:
                params['fields'] = fields
            
            endpoint = f"{self.auth.api_endpoints['products']}/{product_id}.json"
            response = await self._make_request('GET', endpoint, params=params)
            return response.get('product', {})
        except Exception as e:
            self.logger.error(f"Error retrieving product {product_id}: {str(e)}")
            raise
    
    # Locations API
    
    async def get_locations(self) -> Dict[str, Any]:
        """
        Retrieve all locations from Shopify.
        
        Returns:
            Locations response
        """
        try:
            response = await self._make_request('GET', self.auth.api_endpoints['locations'])
            return response
        except Exception as e:
            self.logger.error(f"Error retrieving locations: {str(e)}")
            raise
    
    async def get_location(self, location_id: str) -> Dict[str, Any]:
        """
        Retrieve specific location by ID.
        
        Args:
            location_id: Shopify location ID
        
        Returns:
            Location data
        """
        try:
            endpoint = f"{self.auth.api_endpoints['locations']}/{location_id}.json"
            response = await self._make_request('GET', endpoint)
            return response.get('location', {})
        except Exception as e:
            self.logger.error(f"Error retrieving location {location_id}: {str(e)}")
            raise
    
    # Webhooks API
    
    async def create_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create webhook subscription.
        
        Args:
            webhook_data: Webhook configuration
        
        Returns:
            Created webhook data
        """
        try:
            data = {'webhook': webhook_data}
            response = await self._make_request('POST', self.auth.api_endpoints['webhooks'], data=data)
            return response.get('webhook', {})
        except Exception as e:
            self.logger.error(f"Error creating webhook: {str(e)}")
            raise
    
    async def get_webhooks(self) -> Dict[str, Any]:
        """
        List webhook subscriptions.
        
        Returns:
            List of webhook subscriptions
        """
        try:
            response = await self._make_request('GET', self.auth.api_endpoints['webhooks'])
            return response
        except Exception as e:
            self.logger.error(f"Error listing webhooks: {str(e)}")
            raise
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete webhook subscription.
        
        Args:
            webhook_id: Webhook ID
        
        Returns:
            True if deletion successful
        """
        try:
            endpoint = f"{self.auth.api_endpoints['webhooks']}/{webhook_id}.json"
            await self._make_request('DELETE', endpoint)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting webhook {webhook_id}: {str(e)}")
            raise
    
    # GraphQL API
    
    async def execute_graphql_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Query variables
        
        Returns:
            GraphQL response
        """
        try:
            response = await self._make_graphql_request(query, variables)
            return response
        except Exception as e:
            self.logger.error(f"Error executing GraphQL query: {str(e)}")
            raise
    
    # Utility methods
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Shopify API connectivity.
        
        Returns:
            Health check results
        """
        try:
            # Test basic API access with locations endpoint
            locations = await self.get_locations()
            
            return {
                'status': 'healthy',
                'authenticated': self.auth.is_authenticated(),
                'api_accessible': True,
                'shop_domain': self.auth.shop_domain,
                'locations_count': len(locations.get('locations', [])),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'authenticated': self.auth.is_authenticated(),
                'api_accessible': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_shop_info(self) -> Dict[str, Any]:
        """
        Get shop information.
        
        Returns:
            Shop information
        """
        try:
            endpoint = f"{self.auth.api_endpoints['admin']}/shop.json"
            response = await self._make_request('GET', endpoint)
            return response.get('shop', {})
        except Exception as e:
            self.logger.error(f"Error retrieving shop info: {str(e)}")
            raise