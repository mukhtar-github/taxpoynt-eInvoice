"""
Lightspeed POS REST API Client

Comprehensive REST API client for Lightspeed Retail and Restaurant POS systems.
Handles API communication, rate limiting, error handling, and data retrieval.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode
import aiohttp

from .auth import LightspeedAuthenticator
from .exceptions import (
    LightspeedAPIError, LightspeedRateLimitError, LightspeedConnectionError,
    LightspeedNotFoundError, LightspeedTimeoutError, create_lightspeed_exception
)

logger = logging.getLogger(__name__)


class LightspeedRESTClient:
    """
    Lightspeed POS REST API client for TaxPoynt eInvoice System Integrator functions.
    
    Supports both Lightspeed Retail (R-Series) and Restaurant (K-Series) APIs.
    Provides comprehensive access to sales, customers, products, and inventory data.
    
    Key Features:
    - Automatic authentication and token refresh
    - Rate limiting with automatic retry and backoff
    - Comprehensive error handling and logging
    - Support for both retail and restaurant API endpoints
    - Efficient pagination for large datasets
    - Nigerian market optimizations
    
    API Documentation:
    - Retail: https://developers.lightspeedhq.com/retail/
    - Restaurant: https://developers.lightspeedhq.com/restaurant/
    """
    
    def __init__(self, authenticator: LightspeedAuthenticator):
        """
        Initialize Lightspeed REST client.
        
        Args:
            authenticator: Configured LightspeedAuthenticator instance
        """
        self.auth = authenticator
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.base_url = authenticator.base_url
        self.api_type = authenticator.api_type
        self.api_version = authenticator.api_version
        self.account_id = authenticator.account_id
        
        # Rate limiting configuration
        self.max_requests_per_second = 2  # Conservative rate limit
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
            raise LightspeedAPIError("Maximum retry attempts exceeded")
        
        try:
            # Ensure valid authentication
            if not await self.auth.ensure_valid_token():
                raise LightspeedAPIError("Authentication failed - no valid token")
            
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
            raise LightspeedTimeoutError(f"{method} {endpoint}", request_timeout)
        
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error for {method} {endpoint}: {str(e)}")
            if retry_count < self.max_retries - 1:
                delay = self.retry_delays[retry_count]
                self.logger.info(f"Retrying request in {delay} seconds (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
                return await self._make_request(method, endpoint, params, data, timeout, retry_count + 1)
            raise LightspeedConnectionError(f"Network error: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error for {method} {endpoint}: {str(e)}")
            raise LightspeedAPIError(f"Request failed: {str(e)}")
    
    def _build_url(self, endpoint: str) -> str:
        """Build full API URL for endpoint."""
        if self.api_type == 'retail':
            if self.account_id:
                return f"{self.base_url}/{self.api_version}/Account/{self.account_id}/{endpoint}.json"
            else:
                return f"{self.base_url}/{self.api_version}/{endpoint}.json"
        else:  # restaurant
            return f"{self.base_url}/v1/{endpoint}"
    
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
                raise LightspeedAPIError(f"Invalid JSON response: {text}")
        
        elif response.status == 401:
            # Authentication error - try to refresh token once
            if retry_count == 0:
                try:
                    await self.auth.refresh_access_token()
                    return await self._make_request(method, endpoint, params, data, None, retry_count + 1)
                except Exception:
                    pass
            raise LightspeedAPIError("Authentication failed", status_code=401)
        
        elif response.status == 404:
            raise LightspeedNotFoundError("resource", endpoint)
        
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
            
            raise LightspeedRateLimitError("Rate limit exceeded", retry_after=retry_seconds)
        
        elif 500 <= response.status < 600:
            # Server error - retry with backoff
            if retry_count < self.max_retries - 1:
                delay = self.retry_delays[retry_count]
                self.logger.warning(f"Server error {response.status}, retrying in {delay} seconds")
                await asyncio.sleep(delay)
                return await self._make_request(method, endpoint, params, data, None, retry_count + 1)
            
            error_text = await response.text()
            raise LightspeedAPIError(f"Server error: {error_text}", status_code=response.status)
        
        else:
            # Other errors
            error_text = await response.text()
            raise LightspeedAPIError(f"API error: {error_text}", status_code=response.status)
    
    async def _apply_rate_limiting(self):
        """Apply rate limiting delay if necessary."""
        # Simple rate limiting - wait if too many requests
        if self.auth.rate_limit_remaining < 10:
            delay = max(1, (self.auth.rate_limit_reset_time - datetime.now()).total_seconds())
            if delay > 0:
                await asyncio.sleep(min(delay, 60))  # Max 60 second delay
    
    async def get_sales(self, 
                       filters: Optional[Dict[str, Any]] = None, 
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve sales transactions from Lightspeed POS.
        
        Args:
            filters: Filter criteria including:
                - start_date: Start date for sales range (YYYY-MM-DD or datetime)
                - end_date: End date for sales range
                - location_id: Specific location/shop
                - register_id: Specific register/terminal
                - customer_id: Specific customer
                - completed: Only completed sales (default: true)
                - min_amount: Minimum sale amount
                - max_amount: Maximum sale amount
            limit: Maximum number of sales to return
            
        Returns:
            List of sale objects
        """
        try:
            params = {}
            
            # Apply filters
            if filters:
                # Date range filtering
                if filters.get('start_date'):
                    start_date = self._format_date(filters['start_date'])
                    params['timeStamp'] = f'><,{start_date}T00:00:00+00:00'
                
                if filters.get('end_date'):
                    end_date = self._format_date(filters['end_date'])
                    if 'timeStamp' in params:
                        # Combine with start date
                        params['timeStamp'] = f'><,{start_date}T00:00:00+00:00,{end_date}T23:59:59+00:00'
                    else:
                        params['timeStamp'] = f'<,{end_date}T23:59:59+00:00'
                
                # Location/Shop filtering
                if filters.get('location_id'):
                    params['shopID'] = filters['location_id']
                
                # Register filtering
                if filters.get('register_id'):
                    params['registerID'] = filters['register_id']
                
                # Customer filtering
                if filters.get('customer_id'):
                    params['customerID'] = filters['customer_id']
                
                # Completed sales only (default)
                if filters.get('completed', True):
                    params['completed'] = 'true'
            
            # Limit parameter
            if limit:
                params['limit'] = min(limit, 100)  # Lightspeed max 100 per request
            
            # Make API request
            if self.api_type == 'retail':
                response = await self._make_request('GET', 'Sale', params=params)
                sales = response.get('Sale', [])
            else:  # restaurant
                response = await self._make_request('GET', 'orders', params=params)
                sales = response.get('orders', [])
            
            # Ensure we have a list
            if isinstance(sales, dict):
                sales = [sales]
            
            # Apply additional filters that aren't supported by API
            if filters:
                sales = self._apply_client_side_filters(sales, filters)
            
            self.logger.info(f"Retrieved {len(sales)} sales from Lightspeed")
            return sales
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve sales: {str(e)}")
            raise
    
    async def get_sale_by_id(self, sale_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific sale by ID.
        
        Args:
            sale_id: Sale ID to retrieve
            
        Returns:
            Sale object or None if not found
        """
        try:
            if self.api_type == 'retail':
                response = await self._make_request('GET', f'Sale/{sale_id}')
                return response.get('Sale')
            else:  # restaurant
                response = await self._make_request('GET', f'orders/{sale_id}')
                return response.get('order')
        
        except LightspeedNotFoundError:
            self.logger.warning(f"Sale {sale_id} not found")
            return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve sale {sale_id}: {str(e)}")
            raise
    
    async def get_customers(self, 
                          filters: Optional[Dict[str, Any]] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve customers from Lightspeed POS.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of customers to return
            
        Returns:
            List of customer objects
        """
        try:
            params = {}
            
            if limit:
                params['limit'] = min(limit, 100)
            
            if self.api_type == 'retail':
                response = await self._make_request('GET', 'Customer', params=params)
                customers = response.get('Customer', [])
            else:  # restaurant
                response = await self._make_request('GET', 'customers', params=params)
                customers = response.get('customers', [])
            
            if isinstance(customers, dict):
                customers = [customers]
            
            self.logger.info(f"Retrieved {len(customers)} customers from Lightspeed")
            return customers
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve customers: {str(e)}")
            raise
    
    async def get_products(self, 
                         filters: Optional[Dict[str, Any]] = None, 
                         limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve products/items from Lightspeed POS.
        
        Args:
            filters: Filter criteria
            limit: Maximum number of products to return
            
        Returns:
            List of product objects
        """
        try:
            params = {}
            
            if limit:
                params['limit'] = min(limit, 100)
            
            if self.api_type == 'retail':
                response = await self._make_request('GET', 'Item', params=params)
                products = response.get('Item', [])
            else:  # restaurant
                response = await self._make_request('GET', 'products', params=params)
                products = response.get('products', [])
            
            if isinstance(products, dict):
                products = [products]
            
            self.logger.info(f"Retrieved {len(products)} products from Lightspeed")
            return products
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve products: {str(e)}")
            raise
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all locations/shops.
        
        Returns:
            List of location objects
        """
        try:
            if self.api_type == 'retail':
                response = await self._make_request('GET', 'Shop')
                locations = response.get('Shop', [])
            else:  # restaurant
                response = await self._make_request('GET', 'locations')
                locations = response.get('locations', [])
            
            if isinstance(locations, dict):
                locations = [locations]
            
            self.logger.info(f"Retrieved {len(locations)} locations from Lightspeed")
            return locations
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve locations: {str(e)}")
            raise
    
    async def get_payment_types(self) -> List[Dict[str, Any]]:
        """
        Retrieve available payment types.
        
        Returns:
            List of payment type objects
        """
        try:
            if self.api_type == 'retail':
                response = await self._make_request('GET', 'PaymentType')
                payment_types = response.get('PaymentType', [])
            else:  # restaurant
                response = await self._make_request('GET', 'payment-types')
                payment_types = response.get('payment_types', [])
            
            if isinstance(payment_types, dict):
                payment_types = [payment_types]
            
            self.logger.info(f"Retrieved {len(payment_types)} payment types from Lightspeed")
            return payment_types
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve payment types: {str(e)}")
            raise
    
    async def get_sale_lines(self, sale_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve line items for a specific sale.
        
        Args:
            sale_id: Sale ID to get line items for
            
        Returns:
            List of sale line objects
        """
        try:
            if self.api_type == 'retail':
                params = {'saleID': sale_id}
                response = await self._make_request('GET', 'SaleLine', params=params)
                lines = response.get('SaleLine', [])
            else:  # restaurant
                response = await self._make_request('GET', f'orders/{sale_id}/items')
                lines = response.get('items', [])
            
            if isinstance(lines, dict):
                lines = [lines]
            
            return lines
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve sale lines for sale {sale_id}: {str(e)}")
            raise
    
    async def get_sale_payments(self, sale_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve payments for a specific sale.
        
        Args:
            sale_id: Sale ID to get payments for
            
        Returns:
            List of payment objects
        """
        try:
            if self.api_type == 'retail':
                params = {'saleID': sale_id}
                response = await self._make_request('GET', 'SalePayment', params=params)
                payments = response.get('SalePayment', [])
            else:  # restaurant
                response = await self._make_request('GET', f'orders/{sale_id}/payments')
                payments = response.get('payments', [])
            
            if isinstance(payments, dict):
                payments = [payments]
            
            return payments
        
        except Exception as e:
            self.logger.error(f"Failed to retrieve sale payments for sale {sale_id}: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of Lightspeed API connectivity.
        
        Returns:
            Health check results
        """
        try:
            start_time = datetime.now()
            
            # Test basic API access
            if self.api_type == 'retail':
                response = await self._make_request('GET', 'Account')
                success = 'Account' in response
            else:  # restaurant
                response = await self._make_request('GET', 'account')
                success = 'account' in response or 'id' in response
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                'success': success,
                'response_time_ms': response_time,
                'api_type': self.api_type,
                'account_id': self.account_id,
                'rate_limit_remaining': self.auth.rate_limit_remaining,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'api_type': self.api_type,
                'timestamp': datetime.now().isoformat()
            }
    
    def _format_date(self, date_input: Union[str, datetime]) -> str:
        """Format date for API queries."""
        if isinstance(date_input, str):
            return date_input
        elif isinstance(date_input, datetime):
            return date_input.strftime('%Y-%m-%d')
        else:
            raise ValueError(f"Invalid date format: {date_input}")
    
    def _apply_client_side_filters(self, sales: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Apply filters that cannot be done server-side."""
        filtered_sales = sales
        
        # Amount filtering
        if filters.get('min_amount') is not None:
            min_amount = float(filters['min_amount'])
            filtered_sales = [
                sale for sale in filtered_sales 
                if float(sale.get('total', 0)) >= min_amount
            ]
        
        if filters.get('max_amount') is not None:
            max_amount = float(filters['max_amount'])
            filtered_sales = [
                sale for sale in filtered_sales 
                if float(sale.get('total', 0)) <= max_amount
            ]
        
        return filtered_sales
    
    async def paginate_request(self, 
                             endpoint: str, 
                             params: Optional[Dict] = None, 
                             data_key: str = None,
                             page_size: int = 100,
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
        current_page = 0
        params = params or {}
        
        while current_page < max_pages:
            # Set pagination parameters
            page_params = params.copy()
            page_params['limit'] = page_size
            page_params['offset'] = current_page * page_size
            
            try:
                response = await self._make_request('GET', endpoint, params=page_params)
                
                # Extract items from response
                if data_key:
                    items = response.get(data_key, [])
                else:
                    # Try to guess data key
                    for key in response:
                        if isinstance(response[key], list):
                            items = response[key]
                            break
                    else:
                        items = []
                
                if isinstance(items, dict):
                    items = [items]
                
                if not items:
                    break  # No more data
                
                all_items.extend(items)
                
                # Check if we got fewer items than requested (last page)
                if len(items) < page_size:
                    break
                
                current_page += 1
                
                # Small delay between requests for rate limiting
                await asyncio.sleep(0.5)
            
            except Exception as e:
                self.logger.warning(f"Pagination failed on page {current_page}: {str(e)}")
                break
        
        return all_items