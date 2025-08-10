"""
Moniepoint POS REST API Client
Comprehensive REST API client for Moniepoint POS system.
Handles API communication, rate limiting, error handling, and data retrieval
with Nigerian banking system integration.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode
import aiohttp

from .auth import MoniepointAuthManager
from .exceptions import (
    MoniepointAPIError,
    MoniepointRateLimitError,
    MoniepointConnectionError,
    create_moniepoint_exception
)

logger = logging.getLogger(__name__)


class MoniepointRestClient:
    """
    Moniepoint POS REST API Client
    
    Provides comprehensive access to Moniepoint POS REST API endpoints including:
    - Transaction management and retrieval
    - Payment processing and transfers
    - Nigerian banking system integration
    - Merchant and terminal management
    - NIP (Nigeria Instant Payment) support
    """
    
    def __init__(self, auth_manager: MoniepointAuthManager):
        """
        Initialize Moniepoint REST client.
        
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
        
        # Moniepoint API version
        self.api_version = 'v1'
        
        # Rate limiting
        self._rate_limit_remaining = 1000
        self._rate_limit_reset = datetime.utcnow()
        
        logger.info(f"Initialized Moniepoint REST client for {auth_manager.environment}")
    
    async def get_merchant_info(self, merchant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get merchant information.
        
        Args:
            merchant_id: Specific merchant ID (optional)
            
        Returns:
            Dict: Merchant information
        """
        try:
            target_merchant_id = merchant_id or self.auth_manager.merchant_id
            endpoint = f"/api/{self.api_version}/merchant/{target_merchant_id}"
            
            response = await self._make_request('GET', endpoint)
            logger.info(f"Retrieved Moniepoint merchant info: {target_merchant_id}")
            return response.get('responseBody')
            
        except Exception as e:
            logger.error(f"Failed to get merchant info: {str(e)}")
            raise create_moniepoint_exception(e)
    
    async def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        merchant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions from Moniepoint POS.
        
        Args:
            start_date: Start date for transaction retrieval
            end_date: End date for transaction retrieval
            page: Page number for pagination
            size: Page size for pagination
            merchant_id: Specific merchant ID
            
        Returns:
            List[Dict]: List of transaction data
        """
        try:
            endpoint = f"/api/{self.api_version}/merchant/transactions"
            params = {}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d')
            if page is not None:
                params['page'] = page
            if size is not None:
                params['size'] = size
            
            response = await self._make_request('GET', endpoint, params=params)
            
            transactions = response.get('responseBody', {}).get('content', [])
            logger.info(f"Retrieved {len(transactions)} Moniepoint transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get transactions: {str(e)}")
            raise create_moniepoint_exception(e)
    
    async def get_transaction_details(
        self,
        transaction_reference: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific transaction.
        
        Args:
            transaction_reference: Transaction reference
            
        Returns:
            Dict: Detailed transaction information
        """
        try:
            endpoint = f"/api/{self.api_version}/merchant/transactions/{transaction_reference}"
            
            response = await self._make_request('GET', endpoint)
            
            logger.info(f"Retrieved Moniepoint transaction details: {transaction_reference}")
            return response.get('responseBody')
            
        except Exception as e:
            logger.error(f"Failed to get transaction details {transaction_reference}: {str(e)}")
            return None
    
    async def get_account_transactions(
        self,
        account_reference: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: Optional[int] = None,
        size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific account.
        
        Args:
            account_reference: Account reference
            start_date: Start date for transaction retrieval
            end_date: End date for transaction retrieval
            page: Page number for pagination
            size: Page size for pagination
            
        Returns:
            List[Dict]: List of account transactions
        """
        try:
            endpoint = f"/api/{self.api_version}/transactions/{account_reference}"
            params = {}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d')
            if page is not None:
                params['page'] = page
            if size is not None:
                params['size'] = size
            
            response = await self._make_request('GET', endpoint, params=params)
            
            transactions = response.get('responseBody', {}).get('content', [])
            logger.info(f"Retrieved {len(transactions)} account transactions for {account_reference}")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get account transactions: {str(e)}")
            raise create_moniepoint_exception(e)
    
    async def get_virtual_accounts(self, merchant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get virtual accounts for merchant.
        
        Args:
            merchant_id: Specific merchant ID (optional)
            
        Returns:
            List[Dict]: List of virtual accounts
        """
        try:
            endpoint = f"/api/{self.api_version}/bank-transfer/reserved-accounts"
            
            response = await self._make_request('GET', endpoint)
            
            accounts = response.get('responseBody', [])
            logger.info(f"Retrieved {len(accounts)} virtual accounts")
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to get virtual accounts: {str(e)}")
            raise create_moniepoint_exception(e)
    
    async def get_settlement_info(
        self,
        settlement_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get settlement information.
        
        Args:
            settlement_id: Settlement ID
            
        Returns:
            Dict: Settlement information
        """
        try:
            endpoint = f"/api/{self.api_version}/settlements/{settlement_id}"
            
            response = await self._make_request('GET', endpoint)
            
            logger.info(f"Retrieved Moniepoint settlement info: {settlement_id}")
            return response.get('responseBody')
            
        except Exception as e:
            logger.error(f"Failed to get settlement info {settlement_id}: {str(e)}")
            return None
    
    async def initiate_transfer(
        self,
        amount: float,
        destination_bank_code: str,
        destination_account_number: str,
        narration: str,
        reference: Optional[str] = None,
        currency: str = 'NGN'
    ) -> Dict[str, Any]:
        """
        Initiate a transfer through Moniepoint.
        
        Args:
            amount: Transfer amount
            destination_bank_code: Destination bank code
            destination_account_number: Destination account number
            narration: Transfer description
            reference: Optional transaction reference
            currency: Currency code (default: NGN)
            
        Returns:
            Dict: Transfer response
        """
        try:
            endpoint = f"/api/{self.api_version}/disbursements/single"
            
            transfer_data = {
                'amount': amount,
                'reference': reference or f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                'narration': narration,
                'destinationBankCode': destination_bank_code,
                'destinationAccountNumber': destination_account_number,
                'currency': currency,
                'sourceAccountNumber': self.auth_manager.merchant_id
            }
            
            response = await self._make_request('POST', endpoint, data=transfer_data)
            
            logger.info(f"Initiated Moniepoint transfer: {transfer_data['reference']}")
            return response.get('responseBody', {})
            
        except Exception as e:
            logger.error(f"Failed to initiate transfer: {str(e)}")
            raise create_moniepoint_exception(e)
    
    async def verify_account(
        self,
        account_number: str,
        bank_code: str
    ) -> Dict[str, Any]:
        """
        Verify account details.
        
        Args:
            account_number: Account number to verify
            bank_code: Bank code
            
        Returns:
            Dict: Account verification details
        """
        try:
            endpoint = f"/api/{self.api_version}/disbursements/account/validate"
            
            verify_data = {
                'accountNumber': account_number,
                'bankCode': bank_code
            }
            
            response = await self._make_request('POST', endpoint, data=verify_data)
            
            logger.info(f"Verified account: {account_number}")
            return response.get('responseBody', {})
            
        except Exception as e:
            logger.error(f"Failed to verify account {account_number}: {str(e)}")
            raise create_moniepoint_exception(e)
    
    async def get_supported_banks(self) -> List[Dict[str, Any]]:
        """
        Get supported banks for transfers.
        
        Returns:
            List[Dict]: List of supported banks
        """
        try:
            endpoint = f"/api/{self.api_version}/sdk/transactions/banks"
            
            response = await self._make_request('GET', endpoint)
            
            banks = response.get('responseBody', [])
            logger.info(f"Retrieved {len(banks)} supported banks")
            return banks
            
        except Exception as e:
            logger.error(f"Failed to get supported banks: {str(e)}")
            raise create_moniepoint_exception(e)
    
    async def batch_get_transactions(
        self,
        transaction_references: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get multiple transactions in batch.
        
        Args:
            transaction_references: List of transaction references to retrieve
            
        Returns:
            List[Dict]: List of transaction details
        """
        try:
            transactions = []
            semaphore = asyncio.Semaphore(self.api_config['max_concurrent_requests'])
            
            async def get_single_transaction(ref: str):
                async with semaphore:
                    try:
                        transaction_data = await self.get_transaction_details(ref)
                        if transaction_data:
                            return transaction_data
                    except Exception as e:
                        logger.error(f"Failed to get transaction {ref}: {str(e)}")
                    return None
            
            # Execute requests concurrently
            tasks = [get_single_transaction(ref) for ref in transaction_references]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            transactions = [result for result in results if result is not None and not isinstance(result, Exception)]
            
            logger.info(f"Retrieved {len(transactions)}/{len(transaction_references)} Moniepoint transactions in batch")
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
        """Make authenticated API request to Moniepoint."""
        try:
            # Check rate limits
            await self._check_rate_limits()
            
            # Get authorization headers
            headers = await self.auth_manager._get_auth_headers()
            
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
                            return await self._make_request(method, endpoint, params, data, retry_count + 1)
                        else:
                            raise MoniepointRateLimitError("Rate limit exceeded, max retries reached")
                    elif response.status == 401:  # Unauthorized
                        # Try to refresh token and retry once
                        if retry_count == 0:
                            await self.auth_manager.authenticate()
                            return await self._make_request(method, endpoint, params, data, retry_count + 1)
                        else:
                            raise MoniepointAPIError("Authentication failed", status_code=401)
                    elif response.status >= 500:  # Server error
                        if retry_count < self.api_config['max_retries']:
                            await asyncio.sleep(self.api_config['retry_delay'] ** retry_count)
                            return await self._make_request(method, endpoint, params, data, retry_count + 1)
                        else:
                            error_text = await response.text()
                            raise MoniepointAPIError(f"Server error: {error_text}", status_code=response.status)
                    else:
                        error_text = await response.text()
                        raise MoniepointAPIError(f"API request failed: {error_text}", status_code=response.status)
                        
        except aiohttp.ClientError as e:
            if retry_count < self.api_config['max_retries']:
                await asyncio.sleep(self.api_config['retry_delay'] ** retry_count)
                return await self._make_request(method, endpoint, params, data, retry_count + 1)
            else:
                raise MoniepointConnectionError(f"Connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Moniepoint API request failed: {str(e)}")
            raise create_moniepoint_exception(e)
    
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