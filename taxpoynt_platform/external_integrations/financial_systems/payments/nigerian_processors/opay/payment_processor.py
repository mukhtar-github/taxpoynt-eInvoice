"""
OPay Payment Processor
=====================

Handles raw API communication with OPay's mobile money and digital wallet platform.
Manages authentication, transaction retrieval, wallet operations, and API interactions
with proper error handling and rate limiting.

Features:
- OPay API integration
- Mobile money transaction retrieval
- Digital wallet operations
- QR payment processing
- Rate limiting and retry logic
- Error handling and logging
- Response parsing and validation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
import aiohttp
from dataclasses import asdict

from .auth import OPayAuthManager
from .models import (
    OPayTransaction, OPayCustomer, OPaySettlement,
    OPayTransactionType, OPayChannel, OPayWalletType,
    create_opay_transaction_from_api_data, MOBILE_MONEY_CODES
)

logger = logging.getLogger(__name__)


class OPayAPIError(Exception):
    """OPay API specific error."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class OPayPaymentProcessor:
    """
    Handles direct API communication with OPay mobile money platform.
    
    This class focuses purely on API interactions, leaving business logic
    to the OPayConnector class for proper separation of concerns.
    """

    def __init__(self, auth_manager: OPayAuthManager):
        """
        Initialize OPay payment processor.
        
        Args:
            auth_manager: Authenticated OPay auth manager
        """
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.base_url = auth_manager.base_url
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        # Rate limiting
        self.max_requests_per_minute = 100
        self.request_count = 0
        self.rate_limit_window_start = datetime.utcnow()
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Statistics
        self.stats = {
            'api_calls_made': 0,
            'api_calls_successful': 0,
            'api_calls_failed': 0,
            'rate_limit_hits': 0,
            'retries_attempted': 0
        }

    async def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        wallet_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        page: int = 1
    ) -> List[OPayTransaction]:
        """
        Retrieve transactions from OPay API.
        
        Args:
            start_date: Filter transactions from this date
            end_date: Filter transactions to this date
            wallet_id: Filter by specific wallet
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            limit: Maximum number of transactions to retrieve
            page: Page number for pagination
            
        Returns:
            List of OPayTransaction objects
        """
        try:
            # Build query parameters
            params = {
                'limit': min(limit, 200),  # OPay API limit
                'page': page
            }
            
            if start_date:
                params['start_date'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if end_date:
                params['end_date'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
            if wallet_id:
                params['wallet_id'] = wallet_id
            if transaction_type:
                params['transaction_type'] = transaction_type
            if status:
                params['status'] = status
            
            # Make API request
            endpoint = "/transaction/query"
            response_data = await self._make_api_request('POST', endpoint, json_data=params)
            
            # Parse transactions
            transactions = []
            if response_data.get('code') == '00000':
                data = response_data.get('data', {})
                transaction_list = data.get('transactions', [])
                
                for tx_data in transaction_list:
                    try:
                        transaction = create_opay_transaction_from_api_data(tx_data)
                        transactions.append(transaction)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse transaction {tx_data.get('reference', 'unknown')}: {str(e)}")
            
            self.logger.info(f"Retrieved {len(transactions)} transactions from OPay API")
            return transactions
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve transactions: {str(e)}")
            raise OPayAPIError(f"Transaction retrieval failed: {str(e)}")

    async def get_transaction_by_reference(self, reference: str) -> Optional[OPayTransaction]:
        """
        Get specific transaction by reference.
        
        Args:
            reference: OPay transaction reference
            
        Returns:
            OPayTransaction object or None if not found
        """
        try:
            payload = {'reference': reference}
            endpoint = "/transaction/status"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            if response_data.get('code') == '00000':
                tx_data = response_data.get('data', {})
                return create_opay_transaction_from_api_data(tx_data)
            
            return None
            
        except OPayAPIError as e:
            if e.response_data and e.response_data.get('code') == '02006':  # Transaction not found
                return None
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve transaction {reference}: {str(e)}")
            raise

    async def get_wallet_balance(self, wallet_id: str) -> Dict[str, Any]:
        """
        Get wallet balance information.
        
        Args:
            wallet_id: Wallet identifier
            
        Returns:
            Wallet balance information
        """
        try:
            payload = {'walletId': wallet_id}
            endpoint = "/wallet/balance"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            if response_data.get('code') == '00000':
                return response_data.get('data', {})
            else:
                raise OPayAPIError(f"Wallet balance query failed: {response_data.get('message')}")
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve wallet balance for {wallet_id}: {str(e)}")
            raise

    async def get_wallet_transactions(
        self,
        wallet_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        limit: int = 100
    ) -> List[OPayTransaction]:
        """
        Get transactions for specific wallet.
        
        Args:
            wallet_id: Wallet identifier
            start_date: Filter from date
            end_date: Filter to date
            transaction_type: Transaction type filter
            limit: Maximum transactions
            
        Returns:
            List of wallet transactions
        """
        try:
            payload = {
                'walletId': wallet_id,
                'limit': min(limit, 200)
            }
            
            if start_date:
                payload['startDate'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
            if end_date:
                payload['endDate'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
            if transaction_type:
                payload['transactionType'] = transaction_type
            
            endpoint = "/wallet/transactions"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            # Parse wallet transactions
            transactions = []
            if response_data.get('code') == '00000':
                data = response_data.get('data', {})
                transaction_list = data.get('transactions', [])
                
                for tx_data in transaction_list:
                    try:
                        # Enhance with wallet context
                        tx_data['wallet_id'] = wallet_id
                        transaction = create_opay_transaction_from_api_data(tx_data)
                        transactions.append(transaction)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse wallet transaction: {str(e)}")
            
            self.logger.info(f"Retrieved {len(transactions)} wallet transactions for {wallet_id}")
            return transactions
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve wallet transactions for {wallet_id}: {str(e)}")
            raise OPayAPIError(f"Wallet transaction retrieval failed: {str(e)}")

    async def initiate_transfer(
        self,
        amount: Decimal,
        recipient_phone: str,
        reference: str,
        narration: str,
        sender_wallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate wallet-to-wallet transfer.
        
        Args:
            amount: Transfer amount
            recipient_phone: Recipient phone number
            reference: Unique transfer reference
            narration: Transfer description
            sender_wallet_id: Sender wallet ID
            
        Returns:
            Transfer initiation response
        """
        try:
            payload = {
                'amount': str(int(amount * 100)),  # Convert to kobo
                'recipient': recipient_phone,
                'reference': reference,
                'narration': narration
            }
            
            if sender_wallet_id:
                payload['senderWalletId'] = sender_wallet_id
            
            endpoint = "/transfer/wallet"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Failed to initiate transfer {reference}: {str(e)}")
            raise OPayAPIError(f"Transfer initiation failed: {str(e)}")

    async def initiate_bank_transfer(
        self,
        amount: Decimal,
        recipient_account: str,
        recipient_bank_code: str,
        reference: str,
        narration: str,
        sender_wallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate wallet-to-bank transfer.
        
        Args:
            amount: Transfer amount
            recipient_account: Recipient account number
            recipient_bank_code: Recipient bank code
            reference: Unique transfer reference
            narration: Transfer description
            sender_wallet_id: Sender wallet ID
            
        Returns:
            Bank transfer initiation response
        """
        try:
            payload = {
                'amount': str(int(amount * 100)),  # Convert to kobo
                'recipient': {
                    'bankCode': recipient_bank_code,
                    'bankAccountNumber': recipient_account
                },
                'reference': reference,
                'narration': narration
            }
            
            if sender_wallet_id:
                payload['senderWalletId'] = sender_wallet_id
            
            endpoint = "/transfer/bank"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Failed to initiate bank transfer {reference}: {str(e)}")
            raise OPayAPIError(f"Bank transfer initiation failed: {str(e)}")

    async def pay_bill(
        self,
        bill_type: str,
        provider_code: str,
        customer_id: str,
        amount: Decimal,
        reference: str,
        wallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pay bill through OPay.
        
        Args:
            bill_type: Type of bill (electricity, water, cable_tv, etc.)
            provider_code: Service provider code
            customer_id: Customer ID/meter number
            amount: Payment amount
            reference: Unique payment reference
            wallet_id: Payer wallet ID
            
        Returns:
            Bill payment response
        """
        try:
            payload = {
                'billType': bill_type,
                'providerCode': provider_code,
                'customerId': customer_id,
                'amount': str(int(amount * 100)),  # Convert to kobo
                'reference': reference
            }
            
            if wallet_id:
                payload['walletId'] = wallet_id
            
            endpoint = "/bill/payment"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Failed to pay bill {reference}: {str(e)}")
            raise OPayAPIError(f"Bill payment failed: {str(e)}")

    async def buy_airtime(
        self,
        phone_number: str,
        amount: Decimal,
        network_code: str,
        reference: str,
        wallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Purchase airtime through OPay.
        
        Args:
            phone_number: Phone number to recharge
            amount: Airtime amount
            network_code: Mobile network code (MTN, AIRTEL, GLO, 9MOBILE)
            reference: Unique purchase reference
            wallet_id: Payer wallet ID
            
        Returns:
            Airtime purchase response
        """
        try:
            payload = {
                'phoneNumber': phone_number,
                'amount': str(int(amount * 100)),  # Convert to kobo
                'networkCode': network_code,
                'reference': reference
            }
            
            if wallet_id:
                payload['walletId'] = wallet_id
            
            endpoint = "/airtime/purchase"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Failed to buy airtime {reference}: {str(e)}")
            raise OPayAPIError(f"Airtime purchase failed: {str(e)}")

    async def generate_qr_code(
        self,
        amount: Decimal,
        merchant_id: str,
        reference: str,
        description: str,
        expiry_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Generate QR code for payment.
        
        Args:
            amount: Payment amount
            merchant_id: Merchant identifier
            reference: Unique payment reference
            description: Payment description
            expiry_minutes: QR code expiry in minutes
            
        Returns:
            QR code generation response
        """
        try:
            payload = {
                'amount': str(int(amount * 100)),  # Convert to kobo
                'merchantId': merchant_id,
                'reference': reference,
                'description': description,
                'expiryMinutes': expiry_minutes
            }
            
            endpoint = "/qr/generate"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate QR code {reference}: {str(e)}")
            raise OPayAPIError(f"QR code generation failed: {str(e)}")

    async def get_banks(self) -> List[Dict[str, Any]]:
        """
        Get list of supported banks.
        
        Returns:
            List of bank information
        """
        try:
            endpoint = "/misc/banks"
            response_data = await self._make_api_request('GET', endpoint)
            
            if response_data.get('code') == '00000':
                return response_data.get('data', [])
            else:
                return []
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve banks: {str(e)}")
            raise

    async def validate_account(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """
        Validate bank account details.
        
        Args:
            account_number: Account number to validate
            bank_code: Bank code
            
        Returns:
            Account validation response
        """
        try:
            payload = {
                'bankCode': bank_code,
                'bankAccountNumber': account_number
            }
            
            endpoint = "/misc/bank/account/verify"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            if response_data.get('code') == '00000':
                return response_data.get('data', {})
            else:
                return {}
            
        except Exception as e:
            self.logger.error(f"Failed to validate account {account_number}: {str(e)}")
            raise

    async def get_merchant_settlements(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        settlement_id: Optional[str] = None,
        limit: int = 100
    ) -> List[OPaySettlement]:
        """
        Retrieve merchant settlement information.
        
        Args:
            start_date: Filter settlements from this date
            end_date: Filter settlements to this date  
            settlement_id: Specific settlement ID
            limit: Maximum number of settlements
            
        Returns:
            List of OPaySettlement objects
        """
        try:
            params = {'limit': min(limit, 100)}
            
            if start_date:
                params['startDate'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['endDate'] = end_date.strftime('%Y-%m-%d')
            if settlement_id:
                params['settlementId'] = settlement_id
            
            endpoint = "/settlement/query"
            response_data = await self._make_api_request('POST', endpoint, json_data=params)
            
            # Parse settlements
            settlements = []
            if response_data.get('code') == '00000':
                data = response_data.get('data', {})
                settlement_list = data.get('settlements', [])
                
                for settlement_data in settlement_list:
                    try:
                        settlement = self._parse_settlement_data(settlement_data)
                        settlements.append(settlement)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse settlement {settlement_data.get('id', 'unknown')}: {str(e)}")
            
            return settlements
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve settlements: {str(e)}")
            raise OPayAPIError(f"Settlement retrieval failed: {str(e)}")

    async def _make_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to OPay.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters (for GET requests)
            json_data: JSON request body
            headers: Additional headers
            
        Returns:
            API response data
            
        Raises:
            OPayAPIError: If API request fails
        """
        # Check rate limits
        if not self._check_rate_limit():
            self.stats['rate_limit_hits'] += 1
            await asyncio.sleep(1)  # Wait for rate limit reset
        
        # Ensure authentication
        if not await self.auth_manager.validate_token():
            raise OPayAPIError("Authentication failed")
        
        # Build request
        url = f"{self.base_url}{endpoint}"
        request_headers = self.auth_manager.get_headers()
        
        if headers:
            request_headers.update(headers)
        
        # Add signature for POST requests with body
        if method == 'POST' and json_data:
            timestamp = str(int(datetime.utcnow().timestamp()))
            payload = json.dumps(json_data, separators=(',', ':'))
            signature = self.auth_manager.create_signature(payload, timestamp)
            
            request_headers['Authorization'] = signature
            request_headers['Timestamp'] = timestamp
        
        # Retry logic
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self.stats['api_calls_made'] += 1
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        params=params if method == 'GET' else None,
                        json=json_data if method == 'POST' else None,
                        headers=request_headers
                    ) as response:
                        
                        response_text = await response.text()
                        
                        # Handle different response types
                        try:
                            response_data = json.loads(response_text)
                        except json.JSONDecodeError:
                            response_data = {'raw_response': response_text}
                        
                        # Check response status
                        if response.status == 200:
                            self.stats['api_calls_successful'] += 1
                            return response_data
                        elif response.status in [401, 403]:
                            # Authentication issue
                            self.logger.warning("Authentication error, attempting re-authentication")
                            await self.auth_manager.authenticate()
                            last_exception = OPayAPIError(
                                f"Authentication error: {response.status}",
                                response.status,
                                response_data
                            )
                        elif response.status == 429:
                            # Rate limited
                            self.logger.warning("Rate limited by OPay API")
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            last_exception = OPayAPIError(
                                "Rate limited",
                                response.status,
                                response_data
                            )
                        elif response.status >= 500:
                            # Server error - retry
                            self.logger.warning(f"Server error {response.status}, retrying...")
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            last_exception = OPayAPIError(
                                f"Server error: {response.status}",
                                response.status,
                                response_data
                            )
                        else:
                            # Client error - don't retry
                            self.stats['api_calls_failed'] += 1
                            error_message = response_data.get('message', 'Unknown error')
                            raise OPayAPIError(
                                f"API error: {response.status} - {error_message}",
                                response.status,
                                response_data
                            )
                        
                        if attempt < self.max_retries - 1:
                            self.stats['retries_attempted'] += 1
                            
            except aiohttp.ClientError as e:
                last_exception = OPayAPIError(f"Network error: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    self.stats['retries_attempted'] += 1
            except Exception as e:
                last_exception = OPayAPIError(f"Unexpected error: {str(e)}")
                break
        
        # All retries failed
        self.stats['api_calls_failed'] += 1
        if last_exception:
            raise last_exception
        else:
            raise OPayAPIError("Request failed after all retries")

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.utcnow()
        
        # Reset counter if window has passed
        if (now - self.rate_limit_window_start).total_seconds() >= 60:
            self.request_count = 0
            self.rate_limit_window_start = now
        
        # Check if we're within limits
        if self.request_count >= self.max_requests_per_minute:
            return False
        
        self.request_count += 1
        return True

    def _parse_settlement_data(self, settlement_data: Dict[str, Any]) -> OPaySettlement:
        """Parse settlement data from API response."""
        from .models import OPaySettlement
        
        return OPaySettlement(
            settlement_id=settlement_data.get('id', ''),
            settlement_reference=settlement_data.get('reference', ''),
            settlement_date=datetime.fromisoformat(settlement_data.get('settlement_date', datetime.now().isoformat())),
            gross_amount=Decimal(str(settlement_data.get('gross_amount', 0))) / 100,
            fees=Decimal(str(settlement_data.get('fees', 0))) / 100,
            charges=Decimal(str(settlement_data.get('charges', 0))) / 100,
            net_amount=Decimal(str(settlement_data.get('net_amount', 0))) / 100,
            settlement_wallet_id=settlement_data.get('wallet_id'),
            settlement_bank_code=settlement_data.get('bank_code'),
            settlement_account_number=settlement_data.get('account_number'),
            settlement_account_name=settlement_data.get('account_name'),
            transaction_count=settlement_data.get('transaction_count', 0),
            transaction_ids=settlement_data.get('transaction_ids', []),
            settlement_status=settlement_data.get('status', 'pending')
        )

    def get_api_stats(self) -> Dict[str, Any]:
        """Get API call statistics."""
        total_calls = self.stats['api_calls_made']
        success_rate = (self.stats['api_calls_successful'] / max(1, total_calls)) * 100
        
        return {
            **self.stats,
            'success_rate_percentage': success_rate,
            'current_rate_limit_window': self.rate_limit_window_start.isoformat(),
            'requests_in_current_window': self.request_count
        }


# Export main class
__all__ = ['OPayPaymentProcessor', 'OPayAPIError']