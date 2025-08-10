"""
OPay POS REST API Client
Comprehensive REST API client for OPay POS system.
Handles API communication, rate limiting, error handling, and data retrieval
with Nigerian mobile money and payment system integration.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode
import aiohttp

from .auth import OPayAuthManager
from .exceptions import (
    OPayAPIError,
    OPayRateLimitError,
    OPayConnectionError,
    create_opay_exception
)

logger = logging.getLogger(__name__)


class OPayRestClient:
    """
    OPay POS REST API Client
    
    Provides comprehensive access to OPay POS REST API endpoints including:
    - Transaction management and retrieval
    - Payment processing and mobile money
    - Wallet operations and balance management
    - Nigerian banking system integration
    - POS terminal management
    """
    
    def __init__(self, auth_manager: OPayAuthManager):
        """
        Initialize OPay REST client.
        
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
        
        # OPay API version
        self.api_version = auth_manager.auth_config['api_version']
        
        # Rate limiting
        self._rate_limit_remaining = 1000
        self._rate_limit_reset = datetime.utcnow()
        
        logger.info(f"Initialized OPay REST client for {auth_manager.environment}")
    
    async def get_merchant_info(self) -> Optional[Dict[str, Any]]:
        """
        Get merchant information.
        
        Returns:
            Dict: Merchant information
        """
        try:
            endpoint = f"/api/{self.api_version}/merchant/info"
            
            response = await self._make_request('GET', endpoint)
            logger.info("Retrieved OPay merchant info")
            return response.get('data')
            
        except Exception as e:
            logger.error(f"Failed to get merchant info: {str(e)}")
            raise create_opay_exception(e)
    
    async def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions from OPay POS.
        
        Args:
            start_date: Start date for transaction retrieval
            end_date: End date for transaction retrieval
            page: Page number for pagination
            size: Page size for pagination
            transaction_type: Type of transactions to retrieve
            
        Returns:
            List[Dict]: List of transaction data
        """
        try:
            endpoint = f"/api/{self.api_version}/merchant/transactions"
            params = {}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
            if page is not None:
                params['page'] = page
            if size is not None:
                params['size'] = size
            if transaction_type:
                params['type'] = transaction_type
            
            response = await self._make_request('GET', endpoint, params=params)
            
            transactions = response.get('data', {}).get('records', [])
            logger.info(f"Retrieved {len(transactions)} OPay transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get transactions: {str(e)}")
            raise create_opay_exception(e)
    
    async def get_transaction_details(
        self,
        order_no: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific transaction.
        
        Args:
            order_no: OPay order number
            
        Returns:
            Dict: Detailed transaction information
        """
        try:
            endpoint = f"/api/{self.api_version}/transaction/status"
            data = {
                'orderNo': order_no,
                'reference': order_no
            }
            
            response = await self._make_request('POST', endpoint, data=data)
            
            logger.info(f"Retrieved OPay transaction details: {order_no}")
            return response.get('data')
            
        except Exception as e:
            logger.error(f"Failed to get transaction details {order_no}: {str(e)}")
            return None
    
    async def get_pos_transactions(
        self,
        terminal_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: Optional[int] = None,
        size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get POS terminal transactions.
        
        Args:
            terminal_id: Specific terminal ID
            start_date: Start date for transaction retrieval
            end_date: End date for transaction retrieval
            page: Page number for pagination
            size: Page size for pagination
            
        Returns:
            List[Dict]: List of POS transactions
        """
        try:
            endpoint = f"/api/{self.api_version}/pos/transactions"
            params = {}
            
            if terminal_id:
                params['terminalId'] = terminal_id
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
            if page is not None:
                params['page'] = page
            if size is not None:
                params['size'] = size
            
            response = await self._make_request('GET', endpoint, params=params)
            
            transactions = response.get('data', {}).get('records', [])
            logger.info(f"Retrieved {len(transactions)} POS transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get POS transactions: {str(e)}")
            raise create_opay_exception(e)
    
    async def get_wallet_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: Optional[int] = None,
        size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get wallet transactions.
        
        Args:
            start_date: Start date for transaction retrieval
            end_date: End date for transaction retrieval
            page: Page number for pagination
            size: Page size for pagination
            
        Returns:
            List[Dict]: List of wallet transactions
        """
        try:
            endpoint = f"/api/{self.api_version}/wallet/transactions"
            params = {}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
            if page is not None:
                params['page'] = page
            if size is not None:
                params['size'] = size
            
            response = await self._make_request('GET', endpoint, params=params)
            
            transactions = response.get('data', {}).get('records', [])
            logger.info(f"Retrieved {len(transactions)} wallet transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get wallet transactions: {str(e)}")
            raise create_opay_exception(e)
    
    async def get_payment_methods(self) -> List[Dict[str, Any]]:
        """
        Get supported payment methods.
        
        Returns:
            List[Dict]: List of payment methods
        """
        try:
            endpoint = f"/api/{self.api_version}/payment/methods"
            
            response = await self._make_request('GET', endpoint)
            
            methods = response.get('data', [])
            logger.info(f"Retrieved {len(methods)} payment methods")
            return methods
            
        except Exception as e:
            logger.error(f"Failed to get payment methods: {str(e)}")
            raise create_opay_exception(e)
    
    async def initiate_payment(
        self,
        amount: float,
        customer_phone: str,
        reference: str,
        callback_url: Optional[str] = None,
        payment_method: str = 'wallet'
    ) -> Dict[str, Any]:
        """
        Initiate a payment through OPay.
        
        Args:
            amount: Payment amount
            customer_phone: Customer phone number
            reference: Payment reference
            callback_url: Optional callback URL
            payment_method: Payment method (wallet, card, etc.)
            
        Returns:
            Dict: Payment response
        """
        try:
            endpoint = f"/api/{self.api_version}/payment/initialize"
            
            payment_data = {
                'reference': reference,
                'amount': int(amount * 100),  # Amount in kobo
                'currency': 'NGN',
                'returnUrl': callback_url or '',
                'callbackUrl': callback_url or '',
                'userPhone': customer_phone,
                'payMethods': [payment_method],
                'expireAt': int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
            }
            
            response = await self._make_request('POST', endpoint, data=payment_data)
            
            logger.info(f"Initiated OPay payment: {reference}")
            return response.get('data', {})
            
        except Exception as e:
            logger.error(f"Failed to initiate payment: {str(e)}")
            raise create_opay_exception(e)
    
    async def verify_payment(
        self,
        reference: str
    ) -> Dict[str, Any]:
        """
        Verify payment status.
        
        Args:
            reference: Payment reference
            
        Returns:
            Dict: Payment verification details
        """
        try:
            endpoint = f"/api/{self.api_version}/payment/status"
            data = {
                'reference': reference,
                'orderNo': reference
            }
            
            response = await self._make_request('POST', endpoint, data=data)
            
            logger.info(f"Verified payment: {reference}")
            return response.get('data', {})
            
        except Exception as e:
            logger.error(f"Failed to verify payment {reference}: {str(e)}")
            raise create_opay_exception(e)
    
    async def get_wallet_balance(self) -> Dict[str, Any]:
        """
        Get wallet balance.
        
        Returns:
            Dict: Wallet balance information
        """
        try:
            endpoint = f"/api/{self.api_version}/merchant/balance"
            
            response = await self._make_request('GET', endpoint)
            
            balance_info = response.get('data', {})
            logger.info("Retrieved OPay wallet balance")
            return balance_info
            
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {str(e)}")
            raise create_opay_exception(e)
    
    async def batch_get_transactions(
        self,
        order_numbers: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get multiple transactions in batch.
        
        Args:
            order_numbers: List of order numbers to retrieve
            
        Returns:
            List[Dict]: List of transaction details
        """
        try:
            transactions = []
            semaphore = asyncio.Semaphore(self.api_config['max_concurrent_requests'])
            
            async def get_single_transaction(order_no: str):
                async with semaphore:
                    try:
                        transaction_data = await self.get_transaction_details(order_no)
                        if transaction_data:
                            return transaction_data
                    except Exception as e:
                        logger.error(f"Failed to get transaction {order_no}: {str(e)}")
                    return None
            
            # Execute requests concurrently
            tasks = [get_single_transaction(order_no) for order_no in order_numbers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            transactions = [result for result in results if result is not None and not isinstance(result, Exception)]
            
            logger.info(f"Retrieved {len(transactions)}/{len(order_numbers)} OPay transactions in batch")
            return transactions
            
        except Exception as e:
            logger.error(f"Batch transaction retrieval failed: {str(e)}")
            return []
    
    # Private helper methods
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Any:
        """Make authenticated API request to OPay."""
        try:
            # Check rate limits
            await self._check_rate_limits()
            
            # Prepare request body
            request_body = json.dumps(data) if data else ""
            
            # Get authorization headers
            headers = await self.auth_manager.get_auth_headers(request_body, endpoint)
            
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
                        response_data = await response.json()
                        if response_data.get('code') == '00000':  # OPay success code
                            return response_data
                        else:
                            raise OPayAPIError(
                                f"OPay API error: {response_data.get('message', 'Unknown error')}",
                                error_code=response_data.get('code')
                            )
                    elif response.status == 429:  # Rate limited
                        if retry_count < self.api_config['max_retries']:
                            retry_after = int(response.headers.get('Retry-After', self.api_config['retry_delay']))
                            await asyncio.sleep(retry_after)
                            return await self._make_request(method, endpoint, params, data, retry_count + 1)
                        else:
                            raise OPayRateLimitError("Rate limit exceeded, max retries reached")
                    elif response.status == 401:  # Unauthorized
                        raise OPayAPIError("Authentication failed", status_code=401)
                    elif response.status >= 500:  # Server error
                        if retry_count < self.api_config['max_retries']:
                            await asyncio.sleep(self.api_config['retry_delay'] ** retry_count)
                            return await self._make_request(method, endpoint, params, data, retry_count + 1)
                        else:
                            error_text = await response.text()
                            raise OPayAPIError(f"Server error: {error_text}", status_code=response.status)
                    else:
                        error_text = await response.text()
                        raise OPayAPIError(f"API request failed: {error_text}", status_code=response.status)
                        
        except aiohttp.ClientError as e:
            if retry_count < self.api_config['max_retries']:
                await asyncio.sleep(self.api_config['retry_delay'] ** retry_count)
                return await self._make_request(method, endpoint, params, data, retry_count + 1)
            else:
                raise OPayConnectionError(f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"OPay API request failed: {str(e)}")
            raise create_opay_exception(e)
    
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