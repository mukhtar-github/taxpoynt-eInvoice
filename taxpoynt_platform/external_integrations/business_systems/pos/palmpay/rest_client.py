"""
PalmPay POS REST API Client
Comprehensive REST API client for PalmPay POS system.
Handles API communication, rate limiting, error handling, and data retrieval
with Nigerian mobile payment and agent network integration.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode
import aiohttp

from .auth import PalmPayAuthManager
from .exceptions import (
    PalmPayAPIError,
    PalmPayRateLimitError,
    PalmPayConnectionError,
    create_palmpay_exception
)

logger = logging.getLogger(__name__)


class PalmPayRestClient:
    """
    PalmPay POS REST API Client
    
    Provides comprehensive access to PalmPay POS REST API endpoints including:
    - Transaction management and retrieval
    - Payment processing and mobile money
    - Wallet operations and agent network
    - Nigerian mobile payment integration
    - POS terminal and agent management
    """
    
    def __init__(self, auth_manager: PalmPayAuthManager):
        """
        Initialize PalmPay REST client.
        
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
        
        # PalmPay API version
        self.api_version = auth_manager.auth_config['api_version']
        
        # Rate limiting
        self._rate_limit_remaining = 1000
        self._rate_limit_reset = datetime.utcnow()
        
        logger.info(f"Initialized PalmPay REST client for {auth_manager.environment}")
    
    async def get_merchant_info(self) -> Optional[Dict[str, Any]]:
        """
        Get merchant information.
        
        Returns:
            Dict: Merchant information
        """
        try:
            endpoint = f"/api/{self.api_version}/merchant/info"
            
            response = await self._make_request('GET', endpoint)
            logger.info("Retrieved PalmPay merchant info")
            return response.get('data')
            
        except Exception as e:
            logger.error(f"Failed to get merchant info: {str(e)}")
            raise create_palmpay_exception(e)
    
    async def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions from PalmPay POS.
        
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
            endpoint = f"/api/{self.api_version}/transaction/query"
            
            request_data = {
                "merchantId": self.auth_manager.merchant_id
            }
            
            if start_date:
                request_data['startDate'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if end_date:
                request_data['endDate'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
            if page is not None:
                request_data['page'] = page
            if size is not None:
                request_data['size'] = size
            if transaction_type:
                request_data['type'] = transaction_type
            
            response = await self._make_request('POST', endpoint, data=request_data)
            
            transactions = response.get('data', {}).get('list', [])
            logger.info(f"Retrieved {len(transactions)} PalmPay transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get transactions: {str(e)}")
            raise create_palmpay_exception(e)
    
    async def get_transaction_details(
        self,
        order_no: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific transaction.
        
        Args:
            order_no: PalmPay order number
            
        Returns:
            Dict: Detailed transaction information
        """
        try:
            endpoint = f"/api/{self.api_version}/transaction/detail"
            data = {
                'merchantId': self.auth_manager.merchant_id,
                'orderNo': order_no
            }
            
            response = await self._make_request('POST', endpoint, data=data)
            
            logger.info(f"Retrieved PalmPay transaction details: {order_no}")
            return response.get('data')
            
        except Exception as e:
            logger.error(f"Failed to get transaction details {order_no}: {str(e)}")
            return None
    
    async def get_agent_transactions(
        self,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: Optional[int] = None,
        size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get agent network transactions.
        
        Args:
            agent_id: Specific agent ID
            start_date: Start date for transaction retrieval
            end_date: End date for transaction retrieval
            page: Page number for pagination
            size: Page size for pagination
            
        Returns:
            List[Dict]: List of agent transactions
        """
        try:
            endpoint = f"/api/{self.api_version}/agent/transactions"
            
            request_data = {
                "merchantId": self.auth_manager.merchant_id
            }
            
            if agent_id:
                request_data['agentId'] = agent_id
            if start_date:
                request_data['startDate'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if end_date:
                request_data['endDate'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
            if page is not None:
                request_data['page'] = page
            if size is not None:
                request_data['size'] = size
            
            response = await self._make_request('POST', endpoint, data=request_data)
            
            transactions = response.get('data', {}).get('list', [])
            logger.info(f"Retrieved {len(transactions)} agent transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get agent transactions: {str(e)}")
            raise create_palmpay_exception(e)
    
    async def get_mobile_money_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: Optional[int] = None,
        size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get mobile money transactions.
        
        Args:
            start_date: Start date for transaction retrieval
            end_date: End date for transaction retrieval
            page: Page number for pagination
            size: Page size for pagination
            
        Returns:
            List[Dict]: List of mobile money transactions
        """
        try:
            endpoint = f"/api/{self.api_version}/mobilemoney/transactions"
            
            request_data = {
                "merchantId": self.auth_manager.merchant_id
            }
            
            if start_date:
                request_data['startDate'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if end_date:
                request_data['endDate'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
            if page is not None:
                request_data['page'] = page
            if size is not None:
                request_data['size'] = size
            
            response = await self._make_request('POST', endpoint, data=request_data)
            
            transactions = response.get('data', {}).get('list', [])
            logger.info(f"Retrieved {len(transactions)} mobile money transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get mobile money transactions: {str(e)}")
            raise create_palmpay_exception(e)
    
    async def initiate_payment(
        self,
        amount: float,
        customer_phone: str,
        reference: str,
        callback_url: Optional[str] = None,
        payment_method: str = 'wallet'
    ) -> Dict[str, Any]:
        """
        Initiate a payment through PalmPay.
        
        Args:
            amount: Payment amount
            customer_phone: Customer phone number
            reference: Payment reference
            callback_url: Optional callback URL
            payment_method: Payment method
            
        Returns:
            Dict: Payment response
        """
        try:
            endpoint = f"/api/{self.api_version}/payment/create"
            
            payment_data = {
                'merchantId': self.auth_manager.merchant_id,
                'orderNo': reference,
                'amount': int(amount * 100),  # Amount in kobo
                'currency': 'NGN',
                'customerPhone': customer_phone,
                'paymentMethod': payment_method,
                'notifyUrl': callback_url or '',
                'returnUrl': callback_url or '',
                'expireTime': int((datetime.utcnow() + timedelta(minutes=30)).timestamp() * 1000)
            }
            
            response = await self._make_request('POST', endpoint, data=payment_data)
            
            logger.info(f"Initiated PalmPay payment: {reference}")
            return response.get('data', {})
            
        except Exception as e:
            logger.error(f"Failed to initiate payment: {str(e)}")
            raise create_palmpay_exception(e)
    
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
                'merchantId': self.auth_manager.merchant_id,
                'orderNo': reference
            }
            
            response = await self._make_request('POST', endpoint, data=data)
            
            logger.info(f"Verified payment: {reference}")
            return response.get('data', {})
            
        except Exception as e:
            logger.error(f"Failed to verify payment {reference}: {str(e)}")
            raise create_palmpay_exception(e)
    
    async def get_wallet_balance(self) -> Dict[str, Any]:
        """
        Get wallet balance.
        
        Returns:
            Dict: Wallet balance information
        """
        try:
            endpoint = f"/api/{self.api_version}/balance/query"
            data = {"merchantId": self.auth_manager.merchant_id}
            
            response = await self._make_request('POST', endpoint, data=data)
            
            balance_info = response.get('data', {})
            logger.info("Retrieved PalmPay wallet balance")
            return balance_info
            
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {str(e)}")
            raise create_palmpay_exception(e)
    
    async def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent information.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict: Agent information
        """
        try:
            endpoint = f"/api/{self.api_version}/agent/info"
            data = {
                'merchantId': self.auth_manager.merchant_id,
                'agentId': agent_id
            }
            
            response = await self._make_request('POST', endpoint, data=data)
            
            agent_info = response.get('data', {})
            logger.info(f"Retrieved agent info: {agent_id}")
            return agent_info
            
        except Exception as e:
            logger.error(f"Failed to get agent info: {str(e)}")
            raise create_palmpay_exception(e)
    
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
            
            logger.info(f"Retrieved {len(transactions)}/{len(order_numbers)} PalmPay transactions in batch")
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
        """Make authenticated API request to PalmPay."""
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
                    kwargs['data'] = request_body
                
                async with session.request(method, url, **kwargs) as response:
                    # Update rate limit info
                    self._update_rate_limit_info(response)
                    
                    if response.status == 200:
                        response_data = await response.json()
                        if response_data.get('code') == '200':  # PalmPay success code
                            return response_data
                        else:
                            raise PalmPayAPIError(
                                f"PalmPay API error: {response_data.get('message', 'Unknown error')}",
                                error_code=response_data.get('code')
                            )
                    elif response.status == 429:  # Rate limited
                        if retry_count < self.api_config['max_retries']:
                            retry_after = int(response.headers.get('Retry-After', self.api_config['retry_delay']))
                            await asyncio.sleep(retry_after)
                            return await self._make_request(method, endpoint, params, data, retry_count + 1)
                        else:
                            raise PalmPayRateLimitError("Rate limit exceeded, max retries reached")
                    elif response.status == 401:  # Unauthorized
                        raise PalmPayAPIError("Authentication failed", status_code=401)
                    elif response.status >= 500:  # Server error
                        if retry_count < self.api_config['max_retries']:
                            await asyncio.sleep(self.api_config['retry_delay'] ** retry_count)
                            return await self._make_request(method, endpoint, params, data, retry_count + 1)
                        else:
                            error_text = await response.text()
                            raise PalmPayAPIError(f"Server error: {error_text}", status_code=response.status)
                    else:
                        error_text = await response.text()
                        raise PalmPayAPIError(f"API request failed: {error_text}", status_code=response.status)
                        
        except aiohttp.ClientError as e:
            if retry_count < self.api_config['max_retries']:
                await asyncio.sleep(self.api_config['retry_delay'] ** retry_count)
                return await self._make_request(method, endpoint, params, data, retry_count + 1)
            else:
                raise PalmPayConnectionError(f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"PalmPay API request failed: {str(e)}")
            raise create_palmpay_exception(e)
    
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