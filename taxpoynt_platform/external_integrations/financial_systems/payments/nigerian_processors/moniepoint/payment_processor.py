"""
Moniepoint Payment Processor
===========================

Handles raw API communication with Moniepoint's payment and agent banking platform.
Manages authentication, transaction retrieval, settlement processing, and API interactions
with proper error handling and rate limiting.

Features:
- Moniepoint API integration
- Agent banking transaction retrieval
- Settlement information processing
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

from .auth import MoniepointAuthManager
from .models import (
    MoniepointTransaction, MoniepointCustomer, MoniepointSettlement,
    MoniepointTransactionType, MoniepointChannel, 
    create_moniepoint_transaction_from_api_data, AGENT_BANKING_CODES
)

logger = logging.getLogger(__name__)


class MoniepointAPIError(Exception):
    """Moniepoint API specific error."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class MoniepointPaymentProcessor:
    """
    Handles direct API communication with Moniepoint payment platform.
    
    This class focuses purely on API interactions, leaving business logic
    to the MoniepointConnector class for proper separation of concerns.
    """

    def __init__(self, auth_manager: MoniepointAuthManager):
        """
        Initialize Moniepoint payment processor.
        
        Args:
            auth_manager: Authenticated Moniepoint auth manager
        """
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.base_url = auth_manager.base_url
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        # Rate limiting
        self.max_requests_per_minute = 120
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
        agent_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MoniepointTransaction]:
        """
        Retrieve transactions from Moniepoint API.
        
        Args:
            start_date: Filter transactions from this date
            end_date: Filter transactions to this date
            agent_id: Filter by specific agent
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            limit: Maximum number of transactions to retrieve
            offset: Pagination offset
            
        Returns:
            List of MoniepointTransaction objects
        """
        try:
            # Build query parameters
            params = {
                'limit': min(limit, 500),  # API limit
                'offset': offset
            }
            
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            if agent_id:
                params['agent_id'] = agent_id
            if transaction_type:
                params['transaction_type'] = transaction_type
            if status:
                params['status'] = status
            
            # Make API request
            endpoint = "/transactions"
            response_data = await self._make_api_request('GET', endpoint, params=params)
            
            # Parse transactions
            transactions = []
            transaction_list = response_data.get('data', [])
            
            for tx_data in transaction_list:
                try:
                    transaction = create_moniepoint_transaction_from_api_data(tx_data)
                    transactions.append(transaction)
                except Exception as e:
                    self.logger.warning(f"Failed to parse transaction {tx_data.get('id', 'unknown')}: {str(e)}")
            
            self.logger.info(f"Retrieved {len(transactions)} transactions from Moniepoint API")
            return transactions
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve transactions: {str(e)}")
            raise MoniepointAPIError(f"Transaction retrieval failed: {str(e)}")

    async def get_transaction_by_id(self, transaction_id: str) -> Optional[MoniepointTransaction]:
        """
        Get specific transaction by ID.
        
        Args:
            transaction_id: Moniepoint transaction ID
            
        Returns:
            MoniepointTransaction object or None if not found
        """
        try:
            endpoint = f"/transactions/{transaction_id}"
            response_data = await self._make_api_request('GET', endpoint)
            
            if response_data.get('status') == 'success':
                tx_data = response_data.get('data', {})
                return create_moniepoint_transaction_from_api_data(tx_data)
            
            return None
            
        except MoniepointAPIError as e:
            if e.status_code == 404:
                return None
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve transaction {transaction_id}: {str(e)}")
            raise

    async def verify_transaction(self, reference: str) -> Optional[MoniepointTransaction]:
        """
        Verify transaction by reference.
        
        Args:
            reference: Transaction reference
            
        Returns:
            MoniepointTransaction object or None if not found
        """
        try:
            endpoint = f"/transactions/verify/{reference}"
            response_data = await self._make_api_request('GET', endpoint)
            
            if response_data.get('status') == 'success':
                tx_data = response_data.get('data', {})
                return create_moniepoint_transaction_from_api_data(tx_data)
            
            return None
            
        except MoniepointAPIError as e:
            if e.status_code == 404:
                return None
            raise
        except Exception as e:
            self.logger.error(f"Failed to verify transaction {reference}: {str(e)}")
            raise

    async def get_settlements(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        settlement_id: Optional[str] = None,
        limit: int = 100
    ) -> List[MoniepointSettlement]:
        """
        Retrieve settlement information.
        
        Args:
            start_date: Filter settlements from this date
            end_date: Filter settlements to this date  
            settlement_id: Specific settlement ID
            limit: Maximum number of settlements
            
        Returns:
            List of MoniepointSettlement objects
        """
        try:
            params = {'limit': min(limit, 200)}
            
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            if settlement_id:
                params['settlement_id'] = settlement_id
            
            endpoint = "/settlements"
            response_data = await self._make_api_request('GET', endpoint, params=params)
            
            # Parse settlements
            settlements = []
            settlement_list = response_data.get('data', [])
            
            for settlement_data in settlement_list:
                try:
                    settlement = self._parse_settlement_data(settlement_data)
                    settlements.append(settlement)
                except Exception as e:
                    self.logger.warning(f"Failed to parse settlement {settlement_data.get('id', 'unknown')}: {str(e)}")
            
            return settlements
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve settlements: {str(e)}")
            raise MoniepointAPIError(f"Settlement retrieval failed: {str(e)}")

    async def get_agent_transactions(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        limit: int = 100
    ) -> List[MoniepointTransaction]:
        """
        Get transactions for specific agent.
        
        Args:
            agent_id: Agent identifier
            start_date: Filter from date
            end_date: Filter to date
            transaction_type: Agent transaction type
            limit: Maximum transactions
            
        Returns:
            List of agent transactions
        """
        try:
            params = {
                'agent_id': agent_id,
                'limit': min(limit, 500)
            }
            
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            if transaction_type:
                params['transaction_type'] = transaction_type
            
            endpoint = "/agents/transactions"
            response_data = await self._make_api_request('GET', endpoint, params=params)
            
            # Parse agent transactions
            transactions = []
            transaction_list = response_data.get('data', [])
            
            for tx_data in transaction_list:
                try:
                    # Enhance with agent context
                    tx_data['agent_id'] = agent_id
                    transaction = create_moniepoint_transaction_from_api_data(tx_data)
                    transactions.append(transaction)
                except Exception as e:
                    self.logger.warning(f"Failed to parse agent transaction: {str(e)}")
            
            self.logger.info(f"Retrieved {len(transactions)} agent transactions for {agent_id}")
            return transactions
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve agent transactions for {agent_id}: {str(e)}")
            raise MoniepointAPIError(f"Agent transaction retrieval failed: {str(e)}")

    async def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get agent information and verification status.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent information dictionary
        """
        try:
            endpoint = f"/agents/{agent_id}"
            response_data = await self._make_api_request('GET', endpoint)
            
            if response_data.get('status') == 'success':
                return response_data.get('data', {})
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve agent info for {agent_id}: {str(e)}")
            raise

    async def initiate_payment(
        self,
        amount: Decimal,
        recipient_account: str,
        recipient_bank_code: str,
        narration: str,
        reference: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate payment through Moniepoint.
        
        Args:
            amount: Payment amount
            recipient_account: Recipient account number
            recipient_bank_code: Recipient bank code
            narration: Payment description
            reference: Unique payment reference
            agent_id: Agent handling the payment
            
        Returns:
            Payment initiation response
        """
        try:
            payload = {
                'amount': int(amount * 100),  # Convert to kobo
                'recipient_account': recipient_account,
                'recipient_bank_code': recipient_bank_code,
                'narration': narration,
                'reference': reference
            }
            
            if agent_id:
                payload['agent_id'] = agent_id
            
            endpoint = "/payments/initiate"
            response_data = await self._make_api_request('POST', endpoint, json_data=payload)
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Failed to initiate payment {reference}: {str(e)}")
            raise MoniepointAPIError(f"Payment initiation failed: {str(e)}")

    async def get_banks(self) -> List[Dict[str, Any]]:
        """
        Get list of supported banks.
        
        Returns:
            List of bank information
        """
        try:
            endpoint = "/banks"
            response_data = await self._make_api_request('GET', endpoint)
            
            return response_data.get('data', [])
            
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
            params = {
                'account_number': account_number,
                'bank_code': bank_code
            }
            
            endpoint = "/accounts/validate"
            response_data = await self._make_api_request('GET', endpoint, params=params)
            
            return response_data.get('data', {})
            
        except Exception as e:
            self.logger.error(f"Failed to validate account {account_number}: {str(e)}")
            raise

    async def _make_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to Moniepoint.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON request body
            headers: Additional headers
            
        Returns:
            API response data
            
        Raises:
            MoniepointAPIError: If API request fails
        """
        # Check rate limits
        if not self._check_rate_limit():
            self.stats['rate_limit_hits'] += 1
            await asyncio.sleep(1)  # Wait for rate limit reset
        
        # Ensure authentication
        if not await self.auth_manager.validate_token():
            raise MoniepointAPIError("Authentication failed")
        
        # Build request
        url = f"{self.base_url}{endpoint}"
        request_headers = self.auth_manager.get_headers()
        
        if headers:
            request_headers.update(headers)
        
        # Retry logic
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self.stats['api_calls_made'] += 1
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data,
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
                            last_exception = MoniepointAPIError(
                                f"Authentication error: {response.status}",
                                response.status,
                                response_data
                            )
                        elif response.status == 429:
                            # Rate limited
                            self.logger.warning("Rate limited by Moniepoint API")
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            last_exception = MoniepointAPIError(
                                "Rate limited",
                                response.status,
                                response_data
                            )
                        elif response.status >= 500:
                            # Server error - retry
                            self.logger.warning(f"Server error {response.status}, retrying...")
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            last_exception = MoniepointAPIError(
                                f"Server error: {response.status}",
                                response.status,
                                response_data
                            )
                        else:
                            # Client error - don't retry
                            self.stats['api_calls_failed'] += 1
                            raise MoniepointAPIError(
                                f"API error: {response.status} - {response_data.get('message', 'Unknown error')}",
                                response.status,
                                response_data
                            )
                        
                        if attempt < self.max_retries - 1:
                            self.stats['retries_attempted'] += 1
                            
            except aiohttp.ClientError as e:
                last_exception = MoniepointAPIError(f"Network error: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    self.stats['retries_attempted'] += 1
            except Exception as e:
                last_exception = MoniepointAPIError(f"Unexpected error: {str(e)}")
                break
        
        # All retries failed
        self.stats['api_calls_failed'] += 1
        if last_exception:
            raise last_exception
        else:
            raise MoniepointAPIError("Request failed after all retries")

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

    def _parse_settlement_data(self, settlement_data: Dict[str, Any]) -> MoniepointSettlement:
        """Parse settlement data from API response."""
        from .models import MoniepointSettlement
        
        return MoniepointSettlement(
            settlement_id=settlement_data.get('id', ''),
            settlement_reference=settlement_data.get('reference', ''),
            settlement_date=datetime.fromisoformat(settlement_data.get('settlement_date', datetime.now().isoformat())),
            gross_amount=Decimal(str(settlement_data.get('gross_amount', 0))) / 100,
            fees=Decimal(str(settlement_data.get('fees', 0))) / 100,
            net_amount=Decimal(str(settlement_data.get('net_amount', 0))) / 100,
            settlement_bank_code=settlement_data.get('bank_code', ''),
            settlement_account_number=settlement_data.get('account_number', ''),
            settlement_account_name=settlement_data.get('account_name', ''),
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
__all__ = ['MoniepointPaymentProcessor', 'MoniepointAPIError']