"""
Clover POS REST API Client

Comprehensive REST API client for Clover POS system.
Handles API communication, rate limiting, error handling, and data retrieval.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode
import aiohttp

from .auth import CloverAuthenticator
from .exceptions import (
    CloverAPIError, CloverRateLimitError, CloverConnectionError,
    CloverNotFoundError, CloverTimeoutError, create_clover_exception
)

logger = logging.getLogger(__name__)


class CloverRESTClient:
    """
    Clover POS REST API client for TaxPoynt eInvoice System Integrator functions.
    
    Provides comprehensive access to Clover REST API for orders, payments, customers,
    items, and merchant information with full error handling and rate limiting.
    
    Key Features:
    - Automatic authentication and token management
    - Rate limiting with automatic retry and backoff
    - Comprehensive error handling and logging
    - Support for all major Clover API endpoints
    - Efficient pagination for large datasets
    - Nigerian market optimizations
    
    API Documentation:
    - REST API: https://docs.clover.com/reference/overview
    - Rate Limits: https://docs.clover.com/docs/rate-limits
    """
    
    def __init__(self, authenticator: CloverAuthenticator):
        """
        Initialize Clover REST client.
        
        Args:
            authenticator: Configured CloverAuthenticator instance
        """
        self.auth = authenticator
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.base_url = authenticator.base_url
        self.api_version = authenticator.api_version
        self.merchant_id = authenticator.merchant_id
        self.environment = authenticator.environment
        
        # Rate limiting configuration (Clover: 1000 requests per hour per merchant)
        self.max_requests_per_hour = 1000
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        self.max_retries = len(self.retry_delays)
        
        # Request timeout settings
        self.default_timeout = 30
        self.long_timeout = 120  # For large data requests
    
    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          params: Optional[Dict] = None,
                          data: Optional[Dict] = None,
                          timeout: Optional[int] = None,
                          retry_count: int = 0) -> Dict[str, Any]:
        """
        Make authenticated API request with error handling and retries.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request payload for POST/PUT requests
            timeout: Request timeout in seconds
            retry_count: Current retry attempt number
            
        Returns:
            API response data
        """
        if retry_count >= self.max_retries:
            raise CloverAPIError("Maximum retry attempts exceeded")
        
        try:
            # Ensure valid authentication
            if not await self.auth.ensure_valid_token():
                raise CloverAPIError("Authentication failed - no valid token")
            
            # Build request URL
            url = self._build_url(endpoint)
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {self.auth.access_token}',
                'Accept': 'application/json',
                'User-Agent': 'TaxPoynt-eInvoice/1.0'
            }
            
            if method in ['POST', 'PUT'] and data:
                headers['Content-Type'] = 'application/json'
            
            # Set timeout
            request_timeout = timeout or self.default_timeout
            
            # Rate limiting delay
            await self._apply_rate_limiting()
            
            # Get session and make request
            session = await self.auth.get_session()
            
            self.logger.debug(f"Making {method} request to {url}")
            
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=data if method in ['POST', 'PUT'] else None,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=request_timeout)
            ) as response:
                
                # Update rate limit information
                self.auth._update_rate_limit_info(response.headers)
                
                # Handle response
                return await self._handle_response(response, method, endpoint, params, data, retry_count)
        
        except asyncio.TimeoutError:
            self.logger.error(f"Request timeout for {method} {endpoint}")
            raise CloverTimeoutError(f"{method} {endpoint}", request_timeout)
        
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error for {method} {endpoint}: {str(e)}")
            if retry_count < self.max_retries - 1:
                delay = self.retry_delays[retry_count]
                self.logger.info(f"Retrying request in {delay} seconds (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
                return await self._make_request(method, endpoint, params, data, timeout, retry_count + 1)
            raise CloverConnectionError(f"Network error: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error for {method} {endpoint}: {str(e)}")
            raise CloverAPIError(f"Request failed: {str(e)}")
    
    def _build_url(self, endpoint: str) -> str:
        """Build full API URL for endpoint."""
        # Clean endpoint
        endpoint = endpoint.lstrip('/')
        
        # Handle merchant-specific endpoints
        if self.merchant_id and not endpoint.startswith('merchants/'):
            return f"{self.base_url}/{self.api_version}/merchants/{self.merchant_id}/{endpoint}"
        else:
            return f"{self.base_url}/{self.api_version}/{endpoint}"
    
    async def _handle_response(self, 
                             response: aiohttp.ClientResponse, 
                             method: str, 
                             endpoint: str,
                             params: Optional[Dict],
                             data: Optional[Dict],
                             retry_count: int) -> Dict[str, Any]:
        """Handle API response and errors."""
        
        if response.status == 200:
            try:
                return await response.json()
            except json.JSONDecodeError:
                text = await response.text()
                raise CloverAPIError(f"Invalid JSON response: {text}")
        
        elif response.status == 401:
            # Authentication error - try to refresh token once
            if retry_count == 0:
                try:
                    # Clover tokens are long-lived, so this might not help
                    # But we can try to validate the token again
                    if await self.auth.validate_token():
                        return await self._make_request(method, endpoint, params, data, None, retry_count + 1)
                except Exception:
                    pass
            raise CloverAPIError("Authentication failed", status_code=401)
        
        elif response.status == 404:
            raise CloverNotFoundError("resource", endpoint)
        
        elif response.status == 429:
            # Rate limit exceeded
            retry_after = response.headers.get('Retry-After', '60')
            try:
                retry_seconds = int(retry_after)
            except ValueError:
                retry_seconds = 60
            
            if retry_count < self.max_retries - 1:
                self.logger.warning(f"Rate limit exceeded, waiting {retry_seconds} seconds")
                await asyncio.sleep(retry_seconds)
                return await self._make_request(method, endpoint, params, data, None, retry_count + 1)
            
            raise CloverRateLimitError("Rate limit exceeded", retry_after=retry_seconds)
        
        elif 500 <= response.status < 600:
            # Server error - retry with backoff
            if retry_count < self.max_retries - 1:
                delay = self.retry_delays[retry_count]
                self.logger.warning(f"Server error {response.status}, retrying in {delay} seconds")
                await asyncio.sleep(delay)
                return await self._make_request(method, endpoint, params, data, None, retry_count + 1)
            
            error_text = await response.text()
            raise CloverAPIError(f"Server error: {error_text}", status_code=response.status)
        
        else:
            # Other errors
            error_text = await response.text()
            raise CloverAPIError(f"API error: {error_text}", status_code=response.status)
    
    async def _apply_rate_limiting(self):
        """Apply rate limiting delay if necessary."""
        # Simple rate limiting - wait if too close to limit
        if self.auth.rate_limit_remaining < 10:
            delay = max(1, (self.auth.rate_limit_reset_time - datetime.now()).total_seconds())
            if delay > 0:
                await asyncio.sleep(min(delay, 300))  # Max 5 minute delay
    
    async def get_orders(self, 
                        filters: Optional[Dict[str, Any]] = None, 
                        limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve orders from Clover POS.
        
        Args:
            filters: Filter criteria including:
                - start_date: Start date for orders range (YYYY-MM-DD or timestamp)
                - end_date: End date for orders range  
                - device_id: Specific device
                - employee_id: Specific employee
                - order_type: Order type filter
                - state: Order state (open, locked, paid, etc.)
                - min_amount: Minimum order amount (in cents)
                - max_amount: Maximum order amount (in cents)
            limit: Maximum number of orders to return
            
        Returns:
            List of order objects
        """
        try:
            params = {}
            
            # Apply filters
            if filters:
                # Date range filtering
                if filters.get('start_date'):
                    start_timestamp = self._convert_to_timestamp(filters['start_date'])
                    params['filter'] = f'createdTime>={start_timestamp}'
                
                if filters.get('end_date'):
                    end_timestamp = self._convert_to_timestamp(filters['end_date'])
                    if 'filter' in params:
                        params['filter'] += f' AND createdTime<={end_timestamp}'
                    else:
                        params['filter'] = f'createdTime<={end_timestamp}'
                
                # Device filtering
                if filters.get('device_id'):
                    device_filter = f'device.id={filters["device_id"]}'
                    if 'filter' in params:
                        params['filter'] += f' AND {device_filter}'
                    else:
                        params['filter'] = device_filter
                
                # Employee filtering
                if filters.get('employee_id'):
                    employee_filter = f'employee.id={filters["employee_id"]}'
                    if 'filter' in params:
                        params['filter'] += f' AND {employee_filter}'
                    else:
                        params['filter'] = employee_filter
                
                # Order state filtering
                if filters.get('state'):
                    state_filter = f'state={filters["state"]}'
                    if 'filter' in params:
                        params['filter'] += f' AND {state_filter}'
                    else:
                        params['filter'] = state_filter
            
            # Limit parameter
            if limit:
                params['limit'] = min(limit, 1000)  # Clover max 1000 per request
            
            # Expand related objects for more complete data
            params['expand'] = 'lineItems,payments,discounts,serviceCharge,device,employee'
            
            # Make API request
            response = await self._make_request('GET', 'orders', params=params)
            orders = response.get('elements', [])
            
            # Apply client-side filters that aren't supported by API
            if filters:
                orders = self._apply_client_side_filters(orders, filters)
            
            self.logger.info(f"Retrieved {len(orders)} orders from Clover")
            return orders
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve orders: {str(e)}")
            raise
    
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific order by ID.
        
        Args:
            order_id: Order ID to retrieve
            
        Returns:
            Order object or None if not found
        """
        try:
            params = {
                'expand': 'lineItems,payments,discounts,serviceCharge,device,employee'
            }
            
            response = await self._make_request('GET', f'orders/{order_id}', params=params)
            return response
        
        except CloverNotFoundError:
            self.logger.warning(f"Order {order_id} not found")
            return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve order {order_id}: {str(e)}")
            raise
    
    async def get_payments(self, 
                         filters: Optional[Dict[str, Any]] = None, 
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve payments from Clover POS.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of payments to return
            
        Returns:
            List of payment objects
        """
        try:
            params = {}
            
            if filters:
                # Date range filtering
                if filters.get('start_date'):
                    start_timestamp = self._convert_to_timestamp(filters['start_date'])
                    params['filter'] = f'createdTime>={start_timestamp}'
                
                if filters.get('end_date'):
                    end_timestamp = self._convert_to_timestamp(filters['end_date'])
                    if 'filter' in params:
                        params['filter'] += f' AND createdTime<={end_timestamp}'
                    else:
                        params['filter'] = f'createdTime<={end_timestamp}'
            
            if limit:
                params['limit'] = min(limit, 1000)
            
            params['expand'] = 'order,tender'
            
            response = await self._make_request('GET', 'payments', params=params)
            payments = response.get('elements', [])
            
            self.logger.info(f"Retrieved {len(payments)} payments from Clover")
            return payments
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve payments: {str(e)}")
            raise
    
    async def get_customers(self, 
                          filters: Optional[Dict[str, Any]] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve customers from Clover POS.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of customers to return
            
        Returns:
            List of customer objects
        """
        try:
            params = {}
            
            if limit:
                params['limit'] = min(limit, 1000)
            
            response = await self._make_request('GET', 'customers', params=params)
            customers = response.get('elements', [])
            
            self.logger.info(f"Retrieved {len(customers)} customers from Clover")
            return customers
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve customers: {str(e)}")
            raise
    
    async def get_items(self, 
                       filters: Optional[Dict[str, Any]] = None, 
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve items/inventory from Clover POS.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of items to return
            
        Returns:
            List of item objects
        """
        try:
            params = {}
            
            if limit:
                params['limit'] = min(limit, 1000)
            
            # Expand to get more complete item data
            params['expand'] = 'categories,taxRates,itemStock'
            
            response = await self._make_request('GET', 'items', params=params)
            items = response.get('elements', [])
            
            self.logger.info(f"Retrieved {len(items)} items from Clover")
            return items
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve items: {str(e)}")
            raise
    
    async def get_employees(self, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve employees from Clover POS.
        
        Args:
            limit: Maximum number of employees to return
            
        Returns:
            List of employee objects
        """
        try:
            params = {}
            
            if limit:
                params['limit'] = min(limit, 1000)
            
            response = await self._make_request('GET', 'employees', params=params)
            employees = response.get('elements', [])
            
            self.logger.info(f"Retrieved {len(employees)} employees from Clover")
            return employees
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve employees: {str(e)}")
            raise
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """
        Retrieve devices/terminals associated with the merchant.
        
        Returns:
            List of device objects
        """
        try:
            response = await self._make_request('GET', 'devices')
            devices = response.get('elements', [])
            
            self.logger.info(f"Retrieved {len(devices)} devices from Clover")
            return devices
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve devices: {str(e)}")
            raise
    
    async def get_merchant_info(self) -> Dict[str, Any]:
        """
        Retrieve merchant information.
        
        Returns:
            Merchant object
        """
        try:
            response = await self._make_request('GET', f'merchants/{self.merchant_id}')
            return response
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve merchant info: {str(e)}")
            raise
    
    async def get_tenders(self) -> List[Dict[str, Any]]:
        """
        Retrieve tender types (payment methods) configured for the merchant.
        
        Returns:
            List of tender objects
        """
        try:
            response = await self._make_request('GET', 'tenders')
            tenders = response.get('elements', [])
            
            self.logger.info(f"Retrieved {len(tenders)} tenders from Clover")
            return tenders
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve tenders: {str(e)}")
            raise
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        Retrieve item categories.
        
        Returns:
            List of category objects
        """
        try:
            response = await self._make_request('GET', 'categories')
            categories = response.get('elements', [])
            
            self.logger.info(f"Retrieved {len(categories)} categories from Clover")
            return categories
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve categories: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of Clover API connectivity.
        
        Returns:
            Health check results
        """
        try:
            start_time = datetime.now()
            
            # Test basic API access with merchant info
            merchant_info = await self.get_merchant_info()
            success = 'id' in merchant_info
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                'success': success,
                'response_time_ms': response_time,
                'merchant_id': self.merchant_id,
                'environment': self.environment,
                'rate_limit_remaining': self.auth.rate_limit_remaining,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'merchant_id': self.merchant_id,
                'environment': self.environment,
                'timestamp': datetime.now().isoformat()
            }
    
    def _convert_to_timestamp(self, date_input: Union[str, datetime, int]) -> int:
        """Convert date input to Clover timestamp (milliseconds since epoch)."""
        if isinstance(date_input, int):
            # Already a timestamp
            return date_input
        elif isinstance(date_input, str):
            # Parse date string
            try:
                dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            except ValueError:
                # Try parsing as date only
                dt = datetime.strptime(date_input, '%Y-%m-%d')
            return int(dt.timestamp() * 1000)
        elif isinstance(date_input, datetime):
            return int(date_input.timestamp() * 1000)
        else:
            raise ValueError(f"Invalid date format: {date_input}")
    
    def _apply_client_side_filters(self, orders: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Apply filters that cannot be done server-side."""
        filtered_orders = orders
        
        # Amount filtering (Clover amounts are in cents)
        if filters.get('min_amount') is not None:
            min_amount = int(filters['min_amount'])  # Convert to cents if needed
            filtered_orders = [
                order for order in filtered_orders 
                if order.get('total', 0) >= min_amount
            ]
        
        if filters.get('max_amount') is not None:
            max_amount = int(filters['max_amount'])  # Convert to cents if needed
            filtered_orders = [
                order for order in filtered_orders 
                if order.get('total', 0) <= max_amount
            ]
        
        return filtered_orders
    
    async def paginate_request(self, 
                             endpoint: str, 
                             params: Optional[Dict] = None, 
                             data_key: str = 'elements',
                             page_size: int = 1000,
                             max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        Handle paginated API requests.
        
        Args:
            endpoint: API endpoint to paginate
            params: Request parameters
            data_key: Key in response containing data array
            page_size: Items per page
            max_pages: Maximum pages to fetch
            
        Returns:
            Combined list of all items
        """
        all_items = []
        current_offset = 0
        params = params or {}
        
        for page in range(max_pages):
            # Set pagination parameters
            page_params = params.copy()
            page_params['limit'] = page_size
            page_params['offset'] = current_offset
            
            try:
                response = await self._make_request('GET', endpoint, params=page_params)
                items = response.get(data_key, [])
                
                if not items:
                    break  # No more data
                
                all_items.extend(items)
                
                # Check if we got fewer items than requested (last page)
                if len(items) < page_size:
                    break
                
                current_offset += page_size
                
                # Small delay between requests for rate limiting
                await asyncio.sleep(0.1)
            
            except Exception as e:
                self.logger.warning(f"Pagination failed on page {page}: {str(e)}")
                break
        
        return all_items