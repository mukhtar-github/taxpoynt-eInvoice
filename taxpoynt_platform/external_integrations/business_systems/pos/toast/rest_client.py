"""
Toast POS REST API Client
Comprehensive REST API client for Toast POS system.
Handles API communication, rate limiting, error handling, and data retrieval.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode
import aiohttp

from .auth import ToastAuthManager
from .exceptions import (
    ToastAPIError,
    ToastRateLimitError,
    ToastConnectionError,
    create_toast_exception
)

logger = logging.getLogger(__name__)


class ToastRestClient:
    """
    Toast POS REST API Client
    
    Provides comprehensive access to Toast POS REST API endpoints including:
    - Order and check management
    - Menu and item configuration
    - Customer information
    - Payment processing data
    - Restaurant configuration
    """
    
    def __init__(self, auth_manager: ToastAuthManager):
        """
        Initialize Toast REST client.
        
        Args:
            auth_manager: Authentication manager for API access
        """
        self.auth_manager = auth_manager
        self.base_url = auth_manager.base_url
        
        # API configuration
        self.api_config = {
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 2,
            'rate_limit_delay': 1,
            'batch_size': 100,
            'max_concurrent_requests': 10
        }
        
        # Toast API version
        self.api_version = 'v1'
        
        # Rate limiting
        self._rate_limit_remaining = 1000
        self._rate_limit_reset = datetime.utcnow()
        
        logger.info(f"Initialized Toast REST client for {auth_manager.environment}")
    
    async def get_restaurant_info(self, restaurant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get restaurant information.
        
        Args:
            restaurant_id: Specific restaurant ID (optional)
            
        Returns:
            Dict: Restaurant information
        """
        try:
            endpoint = f"/config/{self.api_version}/restaurants"
            if restaurant_id:
                endpoint = f"/config/{self.api_version}/restaurants/{restaurant_id}"
            
            response = await self._make_request('GET', endpoint, restaurant_id=restaurant_id)
            logger.info(f"Retrieved Toast restaurant info: {restaurant_id or 'all'}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get restaurant info: {str(e)}")
            raise create_toast_exception(e)
    
    async def get_checks(
        self,
        restaurant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get checks (receipts) from Toast POS.
        
        Args:
            restaurant_id: Restaurant identifier
            start_date: Start date for check retrieval
            end_date: End date for check retrieval
            limit: Maximum number of checks to retrieve
            offset: Pagination offset
            
        Returns:
            List[Dict]: List of check data
        """
        try:
            endpoint = f"/orders/{self.api_version}/checks"
            params = {}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d')
            if limit:
                params['pageSize'] = limit
            if offset:
                params['page'] = offset // (limit or 100)
            
            response = await self._make_request(
                'GET', 
                endpoint, 
                params=params,
                restaurant_id=restaurant_id
            )
            
            checks = response if isinstance(response, list) else response.get('data', [])
            logger.info(f"Retrieved {len(checks)} Toast checks for restaurant {restaurant_id}")
            return checks
            
        except Exception as e:
            logger.error(f"Failed to get checks: {str(e)}")
            raise create_toast_exception(e)
    
    async def get_check_details(
        self,
        restaurant_id: str,
        check_guid: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific check.
        
        Args:
            restaurant_id: Restaurant identifier
            check_guid: Check GUID
            
        Returns:
            Dict: Detailed check information
        """
        try:
            endpoint = f"/orders/{self.api_version}/checks/{check_guid}"
            
            response = await self._make_request(
                'GET',
                endpoint,
                restaurant_id=restaurant_id
            )
            
            logger.info(f"Retrieved Toast check details: {check_guid}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to get check details {check_guid}: {str(e)}")
            return None
    
    async def get_orders(
        self,
        restaurant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get orders from Toast POS.
        
        Args:
            restaurant_id: Restaurant identifier
            start_date: Start date for order retrieval
            end_date: End date for order retrieval
            limit: Maximum number of orders to retrieve
            
        Returns:
            List[Dict]: List of order data
        """
        try:
            endpoint = f"/orders/{self.api_version}/orders"
            params = {}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d')
            if limit:
                params['pageSize'] = limit
            
            response = await self._make_request(
                'GET',
                endpoint,
                params=params,
                restaurant_id=restaurant_id
            )
            
            orders = response if isinstance(response, list) else response.get('data', [])
            logger.info(f"Retrieved {len(orders)} Toast orders for restaurant {restaurant_id}")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get orders: {str(e)}")
            raise create_toast_exception(e)
    
    async def get_menu_items(
        self,
        restaurant_id: str,
        last_modified: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get menu items from Toast POS.
        
        Args:
            restaurant_id: Restaurant identifier
            last_modified: Only get items modified after this date
            
        Returns:
            List[Dict]: List of menu items
        """
        try:
            endpoint = f"/config/{self.api_version}/menuItems"
            params = {}
            
            if last_modified:
                params['lastModified'] = last_modified.isoformat()
            
            response = await self._make_request(
                'GET',
                endpoint,
                params=params,
                restaurant_id=restaurant_id
            )
            
            items = response if isinstance(response, list) else response.get('data', [])
            logger.info(f"Retrieved {len(items)} Toast menu items for restaurant {restaurant_id}")
            return items
            
        except Exception as e:
            logger.error(f"Failed to get menu items: {str(e)}")
            raise create_toast_exception(e)
    
    async def get_payments(
        self,
        restaurant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get payment information from Toast POS.
        
        Args:
            restaurant_id: Restaurant identifier
            start_date: Start date for payment retrieval
            end_date: End date for payment retrieval
            
        Returns:
            List[Dict]: List of payment data
        """
        try:
            endpoint = f"/orders/{self.api_version}/payments"
            params = {}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d')
            
            response = await self._make_request(
                'GET',
                endpoint,
                params=params,
                restaurant_id=restaurant_id
            )
            
            payments = response if isinstance(response, list) else response.get('data', [])
            logger.info(f"Retrieved {len(payments)} Toast payments for restaurant {restaurant_id}")
            return payments
            
        except Exception as e:
            logger.error(f"Failed to get payments: {str(e)}")
            raise create_toast_exception(e)
    
    async def get_customers(
        self,
        restaurant_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get customer information from Toast POS.
        
        Args:
            restaurant_id: Restaurant identifier
            limit: Maximum number of customers to retrieve
            offset: Pagination offset
            
        Returns:
            List[Dict]: List of customer data
        """
        try:
            endpoint = f"/customers/{self.api_version}/customers"
            params = {}
            
            if limit:
                params['pageSize'] = limit
            if offset:
                params['page'] = offset // (limit or 100)
            
            response = await self._make_request(
                'GET',
                endpoint,
                params=params,
                restaurant_id=restaurant_id
            )
            
            customers = response if isinstance(response, list) else response.get('data', [])
            logger.info(f"Retrieved {len(customers)} Toast customers for restaurant {restaurant_id}")
            return customers
            
        except Exception as e:
            logger.error(f"Failed to get customers: {str(e)}")
            raise create_toast_exception(e)
    
    async def get_cash_entries(
        self,
        restaurant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cash management entries from Toast POS.
        
        Args:
            restaurant_id: Restaurant identifier
            start_date: Start date for cash entries
            end_date: End date for cash entries
            
        Returns:
            List[Dict]: List of cash entries
        """
        try:
            endpoint = f"/orders/{self.api_version}/cashEntries"
            params = {}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d')
            
            response = await self._make_request(
                'GET',
                endpoint,
                params=params,
                restaurant_id=restaurant_id
            )
            
            cash_entries = response if isinstance(response, list) else response.get('data', [])
            logger.info(f"Retrieved {len(cash_entries)} Toast cash entries for restaurant {restaurant_id}")
            return cash_entries
            
        except Exception as e:
            logger.error(f"Failed to get cash entries: {str(e)}")
            raise create_toast_exception(e)
    
    async def batch_get_checks(
        self,
        restaurant_id: str,
        check_guids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get multiple checks in batch.
        
        Args:
            restaurant_id: Restaurant identifier
            check_guids: List of check GUIDs to retrieve
            
        Returns:
            List[Dict]: List of check details
        """
        try:
            checks = []
            semaphore = asyncio.Semaphore(self.api_config['max_concurrent_requests'])
            
            async def get_single_check(check_guid: str):
                async with semaphore:
                    try:
                        check_data = await self.get_check_details(restaurant_id, check_guid)
                        if check_data:
                            return check_data
                    except Exception as e:
                        logger.error(f"Failed to get check {check_guid}: {str(e)}")
                    return None
            
            # Execute requests concurrently
            tasks = [get_single_check(guid) for guid in check_guids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            checks = [result for result in results if result is not None and not isinstance(result, Exception)]
            
            logger.info(f"Retrieved {len(checks)}/{len(check_guids)} Toast checks in batch")
            return checks
            
        except Exception as e:
            logger.error(f"Batch check retrieval failed: {str(e)}")
            return []
    
    # Private helper methods
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        restaurant_id: Optional[str] = None,
        retry_count: int = 0
    ) -> Any:
        """Make authenticated API request to Toast."""
        try:
            # Check rate limits
            await self._check_rate_limits()
            
            # Get authorization headers
            headers = await self.auth_manager._get_auth_headers()
            
            # Override restaurant ID if provided
            if restaurant_id:
                headers['Toast-Restaurant-External-ID'] = restaurant_id
            
            # Build URL
            url = f"{self.base_url}{endpoint}"
            if params:
                url += f"?{urlencode(params)}"
            
            # Make request
            timeout = aiohttp.ClientTimeout(total=self.api_config['timeout'])
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                kwargs = {'headers': headers}
                if data:
                    kwargs['json'] = data
                
                async with session.request(method, url, **kwargs) as response:
                    # Update rate limit info
                    self._update_rate_limit_info(response)
                    
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        if retry_count < self.api_config['max_retries']:
                            retry_after = int(response.headers.get('Retry-After', self.api_config['retry_delay']))
                            await asyncio.sleep(retry_after)
                            return await self._make_request(method, endpoint, params, data, restaurant_id, retry_count + 1)
                        else:
                            raise ToastRateLimitError("Rate limit exceeded, max retries reached")
                    elif response.status == 401:  # Unauthorized
                        # Try to refresh token and retry once
                        if retry_count == 0:
                            await self.auth_manager.authenticate()
                            return await self._make_request(method, endpoint, params, data, restaurant_id, retry_count + 1)
                        else:
                            raise ToastAPIError("Authentication failed", status_code=401)
                    elif response.status >= 500:  # Server error
                        if retry_count < self.api_config['max_retries']:
                            await asyncio.sleep(self.api_config['retry_delay'] ** retry_count)
                            return await self._make_request(method, endpoint, params, data, restaurant_id, retry_count + 1)
                        else:
                            error_text = await response.text()
                            raise ToastAPIError(f"Server error: {error_text}", status_code=response.status)
                    else:
                        error_text = await response.text()
                        raise ToastAPIError(f"API request failed: {error_text}", status_code=response.status)
                        
        except aiohttp.ClientError as e:
            if retry_count < self.api_config['max_retries']:
                await asyncio.sleep(self.api_config['retry_delay'] ** retry_count)
                return await self._make_request(method, endpoint, params, data, restaurant_id, retry_count + 1)
            else:
                raise ToastConnectionError(f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Toast API request failed: {str(e)}")
            raise create_toast_exception(e)
    
    async def _check_rate_limits(self) -> None:
        """Check and enforce rate limits."""
        if self._rate_limit_remaining <= 10:  # Conservative buffer
            sleep_time = (self._rate_limit_reset - datetime.utcnow()).total_seconds()
            if sleep_time > 0:
                logger.warning(f"Rate limit near exhaustion, sleeping for {sleep_time}s")
                await asyncio.sleep(min(sleep_time, 60))  # Max 1 minute sleep
    
    def _update_rate_limit_info(self, response: aiohttp.ClientResponse) -> None:
        """Update rate limit information from response headers."""
        try:
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining:
                self._rate_limit_remaining = int(remaining)
            
            reset_time = response.headers.get('X-RateLimit-Reset')
            if reset_time:
                self._rate_limit_reset = datetime.fromtimestamp(int(reset_time))
                
        except (ValueError, TypeError):
            # Headers may not always be present or valid
            pass
    
    @property
    def rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return {
            'remaining': self._rate_limit_remaining,
            'reset_time': self._rate_limit_reset.isoformat() if self._rate_limit_reset else None,
            'seconds_until_reset': (self._rate_limit_reset - datetime.utcnow()).total_seconds() if self._rate_limit_reset else None
        }