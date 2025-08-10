"""
Square POS REST Client

Handles REST API communication with Square POS system including payments, orders, 
customers, inventory, and webhook management.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin

import aiohttp

from .auth import SquareAuthenticator
from .exceptions import (
    SquareAPIError, SquareConnectionError, SquareRateLimitError,
    SquareNotFoundError, SquareTimeoutError, create_square_exception
)

logger = logging.getLogger(__name__)


class SquareRESTClient:
    """
    Square POS REST API client for TaxPoynt eInvoice - System Integrator Functions.
    
    Provides comprehensive Square API functionality including:
    - Payments API: Search, retrieve, and manage payments
    - Orders API: Order management and line items
    - Customers API: Customer data management
    - Catalog API: Inventory and product management
    - Locations API: Store/location management
    - Webhooks API: Event subscription management
    """
    
    def __init__(self, authenticator: SquareAuthenticator):
        """Initialize Square REST client with authenticator."""
        self.auth = authenticator
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting settings
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.max_retries = 3
        self.retry_delay = 1.0  # 1 second initial retry delay
        
        # Request timeout settings
        self.request_timeout = 30.0
        self.connect_timeout = 10.0
    
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
        Make authenticated HTTP request to Square API.
        
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
            SquareAPIError: For API errors
            SquareConnectionError: For connection issues
        """
        # Ensure we have valid authentication
        if not await self.auth.ensure_valid_token():
            raise SquareConnectionError("Failed to obtain valid authentication token")
        
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
                            raise SquareRateLimitError(
                                message="Square API rate limit exceeded",
                                retry_after=retry_after
                            )
                    
                    # Handle authentication errors
                    if response.status == 401:
                        # Try to refresh token and retry once
                        if retry_count == 0 and self.auth.refresh_token:
                            refresh_result = await self.auth._refresh_access_token()
                            if refresh_result.get('success'):
                                self.auth.current_access_token = refresh_result.get('access_token')
                                expires_in = refresh_result.get('expires_in', 30 * 24 * 3600)
                                self.auth.expires_at = datetime.now() + timedelta(seconds=expires_in)
                                
                                # Update headers with new token
                                request_headers = await self.auth._get_auth_headers()
                                if headers:
                                    request_headers.update(headers)
                                
                                retry_count += 1
                                continue
                    
                    # Handle other API errors
                    errors = response_data.get('errors', [])
                    if errors:
                        first_error = errors[0]
                        error_code = first_error.get('code', str(response.status))
                        error_message = first_error.get('detail', f"Square API error: {response.status}")
                        
                        # Create specific exception based on error code
                        exception = create_square_exception(
                            error_code=error_code,
                            message=error_message,
                            status_code=response.status,
                            details={'response_data': response_data}
                        )
                        raise exception
                    else:
                        raise SquareAPIError(
                            message=f"Square API error: {response.status}",
                            error_code=str(response.status),
                            status_code=response.status,
                            details={'response_data': response_data}
                        )
            
            except aiohttp.ClientTimeout:
                if retry_count < self.max_retries:
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay * retry_count)
                    continue
                raise SquareTimeoutError(
                    message=f"Square API request timeout after {request_timeout} seconds",
                    timeout_duration=request_timeout
                )
            
            except aiohttp.ClientError as e:
                if retry_count < self.max_retries:
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay * retry_count)
                    continue
                raise SquareConnectionError(f"Square API connection error: {str(e)}")
            
            except Exception as e:
                if isinstance(e, (SquareAPIError, SquareConnectionError, SquareRateLimitError)):
                    raise
                
                if retry_count < self.max_retries:
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay * retry_count)
                    continue
                
                raise SquareAPIError(f"Unexpected error in Square API request: {str(e)}")
        
        raise SquareAPIError("Maximum retry attempts exceeded")
    
    async def _rate_limit_delay(self):
        """Apply rate limiting delay."""
        await asyncio.sleep(self.rate_limit_delay)
    
    # Locations API
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all locations from Square.
        
        Returns:
            List of location data
        """
        try:
            response = await self._make_request('GET', '/v2/locations')
            return response.get('locations', [])
        except Exception as e:
            self.logger.error(f"Error retrieving locations: {str(e)}")
            raise
    
    async def get_location(self, location_id: str) -> Dict[str, Any]:
        """
        Retrieve specific location by ID.
        
        Args:
            location_id: Square location ID
        
        Returns:
            Location data
        """
        try:
            response = await self._make_request('GET', f'/v2/locations/{location_id}')
            return response.get('location', {})
        except Exception as e:
            self.logger.error(f"Error retrieving location {location_id}: {str(e)}")
            raise
    
    # Payments API
    
    async def search_payments(
        self,
        query: Optional[Dict[str, Any]] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search payments using Square Payments API.
        
        Args:
            query: Search query parameters
            cursor: Pagination cursor
            limit: Maximum number of results
        
        Returns:
            Search results with payments and pagination info
        """
        try:
            search_data = {}
            
            if query:
                search_data['query'] = query
            
            if cursor:
                search_data['cursor'] = cursor
            
            if limit:
                search_data['limit'] = min(limit, 500)  # Square API limit
            
            response = await self._make_request('POST', '/v2/payments/search', data=search_data)
            return response
        except Exception as e:
            self.logger.error(f"Error searching payments: {str(e)}")
            raise
    
    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Retrieve specific payment by ID.
        
        Args:
            payment_id: Square payment ID
        
        Returns:
            Payment data
        """
        try:
            response = await self._make_request('GET', f'/v2/payments/{payment_id}')
            return response.get('payment', {})
        except Exception as e:
            self.logger.error(f"Error retrieving payment {payment_id}: {str(e)}")
            raise
    
    async def list_payments(
        self,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
        sort_order: str = 'DESC',
        cursor: Optional[str] = None,
        location_id: Optional[str] = None,
        total: Optional[int] = None,
        last_4: Optional[str] = None,
        card_brand: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List payments with filters.
        
        Args:
            begin_time: Start time filter (ISO 8601)
            end_time: End time filter (ISO 8601)
            sort_order: Sort order (ASC or DESC)
            cursor: Pagination cursor
            location_id: Filter by location
            total: Filter by total amount in cents
            last_4: Filter by last 4 digits of card
            card_brand: Filter by card brand
            limit: Maximum number of results
        
        Returns:
            List results with payments and pagination info
        """
        try:
            params = {
                'sort_order': sort_order
            }
            
            if begin_time:
                params['begin_time'] = begin_time
            if end_time:
                params['end_time'] = end_time
            if cursor:
                params['cursor'] = cursor
            if location_id:
                params['location_id'] = location_id
            if total:
                params['total'] = total
            if last_4:
                params['last_4'] = last_4
            if card_brand:
                params['card_brand'] = card_brand
            if limit:
                params['limit'] = min(limit, 500)
            
            response = await self._make_request('GET', '/v2/payments', params=params)
            return response
        except Exception as e:
            self.logger.error(f"Error listing payments: {str(e)}")
            raise
    
    # Orders API
    
    async def search_orders(
        self,
        query: Optional[Dict[str, Any]] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search orders using Square Orders API.
        
        Args:
            query: Search query parameters
            cursor: Pagination cursor
            limit: Maximum number of results
        
        Returns:
            Search results with orders and pagination info
        """
        try:
            search_data = {}
            
            if query:
                search_data['query'] = query
            
            if cursor:
                search_data['cursor'] = cursor
            
            if limit:
                search_data['limit'] = min(limit, 500)
            
            response = await self._make_request('POST', '/v2/orders/search', data=search_data)
            return response
        except Exception as e:
            self.logger.error(f"Error searching orders: {str(e)}")
            raise
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieve specific order by ID.
        
        Args:
            order_id: Square order ID
        
        Returns:
            Order data
        """
        try:
            response = await self._make_request('GET', f'/v2/orders/{order_id}')
            return response.get('order', {})
        except Exception as e:
            self.logger.error(f"Error retrieving order {order_id}: {str(e)}")
            raise
    
    # Customers API
    
    async def search_customers(
        self,
        query: Optional[Dict[str, Any]] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search customers using Square Customers API.
        
        Args:
            query: Search query parameters
            cursor: Pagination cursor
            limit: Maximum number of results
        
        Returns:
            Search results with customers and pagination info
        """
        try:
            search_data = {}
            
            if query:
                search_data['query'] = query
            
            if cursor:
                search_data['cursor'] = cursor
            
            if limit:
                search_data['limit'] = min(limit, 100)  # Customer API limit
            
            response = await self._make_request('POST', '/v2/customers/search', data=search_data)
            return response
        except Exception as e:
            self.logger.error(f"Error searching customers: {str(e)}")
            raise
    
    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve specific customer by ID.
        
        Args:
            customer_id: Square customer ID
        
        Returns:
            Customer data
        """
        try:
            response = await self._make_request('GET', f'/v2/customers/{customer_id}')
            return response.get('customer', {})
        except Exception as e:
            self.logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
            raise
    
    # Catalog API
    
    async def search_catalog_objects(
        self,
        query: Optional[Dict[str, Any]] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search catalog objects (items, variations, etc.).
        
        Args:
            query: Search query parameters
            cursor: Pagination cursor
            limit: Maximum number of results
        
        Returns:
            Search results with catalog objects and pagination info
        """
        try:
            search_data = {}
            
            if query:
                search_data['query'] = query
            
            if cursor:
                search_data['cursor'] = cursor
            
            if limit:
                search_data['limit'] = min(limit, 1000)
            
            response = await self._make_request('POST', '/v2/catalog/search', data=search_data)
            return response
        except Exception as e:
            self.logger.error(f"Error searching catalog objects: {str(e)}")
            raise
    
    async def get_catalog_object(self, object_id: str, include_related_objects: bool = False) -> Dict[str, Any]:
        """
        Retrieve specific catalog object by ID.
        
        Args:
            object_id: Square catalog object ID
            include_related_objects: Include related objects in response
        
        Returns:
            Catalog object data
        """
        try:
            params = {}
            if include_related_objects:
                params['include_related_objects'] = 'true'
            
            response = await self._make_request('GET', f'/v2/catalog/object/{object_id}', params=params)
            return response.get('object', {})
        except Exception as e:
            self.logger.error(f"Error retrieving catalog object {object_id}: {str(e)}")
            raise
    
    # Inventory API
    
    async def get_inventory_count(
        self,
        catalog_object_id: str,
        location_ids: Optional[List[str]] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get inventory count for a catalog object.
        
        Args:
            catalog_object_id: Square catalog object ID
            location_ids: List of location IDs to filter by
            cursor: Pagination cursor
        
        Returns:
            Inventory count data
        """
        try:
            params = {
                'catalog_object_ids': catalog_object_id
            }
            
            if location_ids:
                params['location_ids'] = ','.join(location_ids)
            
            if cursor:
                params['cursor'] = cursor
            
            response = await self._make_request('GET', '/v2/inventory/counts', params=params)
            return response
        except Exception as e:
            self.logger.error(f"Error retrieving inventory count for {catalog_object_id}: {str(e)}")
            raise
    
    # Webhooks API
    
    async def create_webhook_subscription(
        self,
        subscription_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create webhook subscription.
        
        Args:
            subscription_data: Webhook subscription configuration
        
        Returns:
            Created subscription data
        """
        try:
            response = await self._make_request('POST', '/v2/webhooks/subscriptions', data=subscription_data)
            return response.get('subscription', {})
        except Exception as e:
            self.logger.error(f"Error creating webhook subscription: {str(e)}")
            raise
    
    async def list_webhook_subscriptions(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List webhook subscriptions.
        
        Args:
            cursor: Pagination cursor
        
        Returns:
            List of webhook subscriptions
        """
        try:
            params = {}
            if cursor:
                params['cursor'] = cursor
            
            response = await self._make_request('GET', '/v2/webhooks/subscriptions', params=params)
            return response
        except Exception as e:
            self.logger.error(f"Error listing webhook subscriptions: {str(e)}")
            raise
    
    async def delete_webhook_subscription(self, subscription_id: str) -> bool:
        """
        Delete webhook subscription.
        
        Args:
            subscription_id: Webhook subscription ID
        
        Returns:
            True if deletion successful
        """
        try:
            await self._make_request('DELETE', f'/v2/webhooks/subscriptions/{subscription_id}')
            return True
        except Exception as e:
            self.logger.error(f"Error deleting webhook subscription {subscription_id}: {str(e)}")
            raise
    
    async def test_webhook_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Test webhook subscription.
        
        Args:
            subscription_id: Webhook subscription ID
        
        Returns:
            Test results
        """
        try:
            response = await self._make_request('POST', f'/v2/webhooks/subscriptions/{subscription_id}/test')
            return response
        except Exception as e:
            self.logger.error(f"Error testing webhook subscription {subscription_id}: {str(e)}")
            raise
    
    # Merchant API
    
    async def get_merchant(self, merchant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve merchant information.
        
        Args:
            merchant_id: Specific merchant ID (optional)
        
        Returns:
            Merchant data
        """
        try:
            if merchant_id:
                response = await self._make_request('GET', f'/v2/merchants/{merchant_id}')
                return response.get('merchant', {})
            else:
                response = await self._make_request('GET', '/v2/merchants')
                merchants = response.get('merchants', [])
                return merchants[0] if merchants else {}
        except Exception as e:
            self.logger.error(f"Error retrieving merchant: {str(e)}")
            raise
    
    # Utility methods
    
    async def batch_retrieve_catalog_objects(self, object_ids: List[str]) -> Dict[str, Any]:
        """
        Batch retrieve multiple catalog objects.
        
        Args:
            object_ids: List of catalog object IDs
        
        Returns:
            Batch retrieval results
        """
        try:
            batch_data = {
                'object_ids': object_ids,
                'include_related_objects': False
            }
            
            response = await self._make_request('POST', '/v2/catalog/batch-retrieve', data=batch_data)
            return response
        except Exception as e:
            self.logger.error(f"Error batch retrieving catalog objects: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Square API connectivity.
        
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
                'locations_count': len(locations),
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