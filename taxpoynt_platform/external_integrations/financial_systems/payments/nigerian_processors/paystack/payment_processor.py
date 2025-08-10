"""
Paystack Payment Processor
=========================

Core payment processing logic for Paystack integration.
Handles transaction data extraction and FIRS compliance.
"""

import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from .auth import PaystackAuthManager
from .models import (
    PaystackTransaction, PaystackCustomer, PaystackRefund,
    PaystackApiResponse, PaystackSettlement
)
from ....connector_framework.base_payment_connector import (
    PaymentStatus, PaymentMethod, TransactionType
)

logger = logging.getLogger(__name__)


class PaystackPaymentProcessor:
    """
    Paystack payment processor for transaction data collection.
    
    Focus: Data extraction for FIRS compliance, NOT payment processing.
    """

    def __init__(self, auth_manager: PaystackAuthManager):
        """
        Initialize Paystack payment processor.
        
        Args:
            auth_manager: Authenticated Paystack auth manager
        """
        self.auth_manager = auth_manager
        self.base_url = auth_manager.base_url
        self.logger = logging.getLogger(__name__)

    async def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        amount_min: Optional[Decimal] = None,
        amount_max: Optional[Decimal] = None,
        customer: Optional[str] = None,
        limit: int = 50,
        page: int = 1
    ) -> List[PaystackTransaction]:
        """
        Retrieve transactions from Paystack API.
        
        Args:
            start_date: Start date for transaction range
            end_date: End date for transaction range
            status: Filter by transaction status
            amount_min: Minimum transaction amount (kobo)
            amount_max: Maximum transaction amount (kobo)
            customer: Customer identifier
            limit: Number of transactions per page (max 200)
            page: Page number for pagination
        
        Returns:
            List of PaystackTransaction objects
        """
        try:
            self.logger.info(f"Fetching Paystack transactions: page {page}, limit {limit}")
            
            # Build query parameters
            params = {
                'perPage': min(limit, 200),  # Paystack max is 200
                'page': page
            }
            
            if start_date:
                params['from'] = start_date.isoformat()
            if end_date:
                params['to'] = end_date.isoformat()
            if status:
                params['status'] = status
            if amount_min:
                params['amount'] = int(amount_min * 100)  # Convert to kobo
            if customer:
                params['customer'] = customer
            
            # Make API request
            url = f"{self.base_url}/transaction"
            headers = self.auth_manager.get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._process_transaction_response(data)
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Paystack API error {response.status}: {error_text}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching Paystack transactions: {str(e)}")
            return []

    async def get_transaction_by_id(self, transaction_id: str) -> Optional[PaystackTransaction]:
        """
        Get specific transaction by ID or reference.
        
        Args:
            transaction_id: Paystack transaction ID or reference
        
        Returns:
            PaystackTransaction object or None
        """
        try:
            self.logger.debug(f"Fetching Paystack transaction: {transaction_id}")
            
            url = f"{self.base_url}/transaction/{transaction_id}"
            headers = self.auth_manager.get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') and data.get('data'):
                            return await self._convert_to_paystack_transaction(data['data'])
                    else:
                        self.logger.warning(f"Transaction {transaction_id} not found or error {response.status}")
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching transaction {transaction_id}: {str(e)}")
            return None

    async def verify_transaction(self, reference: str) -> Optional[PaystackTransaction]:
        """
        Verify transaction status using reference.
        
        Args:
            reference: Transaction reference
        
        Returns:
            PaystackTransaction object or None
        """
        try:
            self.logger.debug(f"Verifying Paystack transaction: {reference}")
            
            url = f"{self.base_url}/transaction/verify/{reference}"
            headers = self.auth_manager.get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') and data.get('data'):
                            return await self._convert_to_paystack_transaction(data['data'])
                    else:
                        self.logger.warning(f"Transaction verification failed for {reference}: {response.status}")
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error verifying transaction {reference}: {str(e)}")
            return None

    async def get_customers(
        self,
        limit: int = 50,
        page: int = 1
    ) -> List[PaystackCustomer]:
        """
        Get customer list from Paystack.
        
        Args:
            limit: Number of customers per page
            page: Page number for pagination
        
        Returns:
            List of PaystackCustomer objects
        """
        try:
            self.logger.info(f"Fetching Paystack customers: page {page}, limit {limit}")
            
            params = {
                'perPage': min(limit, 200),
                'page': page
            }
            
            url = f"{self.base_url}/customer"
            headers = self.auth_manager.get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._process_customer_response(data)
                    else:
                        self.logger.error(f"Error fetching customers: {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching Paystack customers: {str(e)}")
            return []

    async def get_refunds(
        self,
        reference: Optional[str] = None,
        currency: str = "NGN",
        limit: int = 50,
        page: int = 1
    ) -> List[PaystackRefund]:
        """
        Get refund information from Paystack.
        
        Args:
            reference: Transaction reference to filter refunds
            currency: Currency code
            limit: Number of refunds per page
            page: Page number for pagination
        
        Returns:
            List of PaystackRefund objects
        """
        try:
            self.logger.info(f"Fetching Paystack refunds: page {page}, limit {limit}")
            
            params = {
                'perPage': min(limit, 200),
                'page': page,
                'currency': currency
            }
            
            if reference:
                params['reference'] = reference
            
            url = f"{self.base_url}/refund"
            headers = self.auth_manager.get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._process_refund_response(data)
                    else:
                        self.logger.error(f"Error fetching refunds: {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching Paystack refunds: {str(e)}")
            return []

    async def get_settlements(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        page: int = 1
    ) -> List[PaystackSettlement]:
        """
        Get settlement information from Paystack.
        
        Args:
            start_date: Start date for settlement range
            end_date: End date for settlement range
            limit: Number of settlements per page
            page: Page number for pagination
        
        Returns:
            List of PaystackSettlement objects
        """
        try:
            self.logger.info(f"Fetching Paystack settlements: page {page}, limit {limit}")
            
            params = {
                'perPage': min(limit, 200),
                'page': page
            }
            
            if start_date:
                params['from'] = start_date.isoformat()
            if end_date:
                params['to'] = end_date.isoformat()
            
            url = f"{self.base_url}/settlement"
            headers = self.auth_manager.get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._process_settlement_response(data)
                    else:
                        self.logger.error(f"Error fetching settlements: {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Error fetching Paystack settlements: {str(e)}")
            return []

    async def _process_transaction_response(self, response_data: Dict[str, Any]) -> List[PaystackTransaction]:
        """Process API response and convert to PaystackTransaction objects."""
        transactions = []
        
        if response_data.get('status') and response_data.get('data'):
            for tx_data in response_data['data']:
                try:
                    transaction = await self._convert_to_paystack_transaction(tx_data)
                    transactions.append(transaction)
                except Exception as e:
                    self.logger.warning(f"Error converting transaction: {str(e)}")
                    continue
        
        return transactions

    async def _convert_to_paystack_transaction(self, tx_data: Dict[str, Any]) -> PaystackTransaction:
        """Convert Paystack API transaction data to PaystackTransaction object."""
        
        # Convert status
        status_mapping = {
            'success': PaymentStatus.SUCCESS,
            'failed': PaymentStatus.FAILED,
            'abandoned': PaymentStatus.CANCELLED,
            'pending': PaymentStatus.PENDING,
            'ongoing': PaymentStatus.PROCESSING,
            'reversed': PaymentStatus.REFUNDED
        }
        
        status = status_mapping.get(tx_data.get('status', 'failed'), PaymentStatus.FAILED)
        
        # Convert payment method
        channel_mapping = {
            'card': PaymentMethod.CARD,
            'bank': PaymentMethod.BANK_TRANSFER,
            'ussd': PaymentMethod.USSD,
            'qr': PaymentMethod.QR_CODE,
            'mobile_money': PaymentMethod.MOBILE_WALLET,
            'bank_transfer': PaymentMethod.BANK_TRANSFER
        }
        
        payment_method = channel_mapping.get(tx_data.get('channel', 'card'), PaymentMethod.CARD)
        
        # Convert amounts (Paystack amounts are in kobo)
        amount = Decimal(str(tx_data.get('amount', 0))) / 100
        fees = Decimal(str(tx_data.get('fees', 0))) / 100 if tx_data.get('fees') else None
        
        # Parse dates
        created_at = datetime.fromisoformat(tx_data['created_at'].replace('Z', '+00:00')) if tx_data.get('created_at') else datetime.utcnow()
        
        return PaystackTransaction(
            transaction_id=str(tx_data.get('id', '')),
            reference=tx_data.get('reference', ''),
            amount=amount,
            currency=tx_data.get('currency', 'NGN'),
            payment_method=payment_method,
            payment_status=status,
            transaction_type=TransactionType.PAYMENT,
            created_at=created_at,
            
            # Merchant info
            merchant_id=self.auth_manager.merchant_email or 'unknown',
            
            # Customer info
            customer_email=tx_data.get('customer', {}).get('email'),
            customer_phone=tx_data.get('customer', {}).get('phone'),
            customer_name=f"{tx_data.get('customer', {}).get('first_name', '')} {tx_data.get('customer', {}).get('last_name', '')}".strip(),
            
            # Transaction details
            description=tx_data.get('message'),
            channel=tx_data.get('channel'),
            fees=fees,
            
            # Banking details
            bank_code=tx_data.get('authorization', {}).get('bank'),
            
            # Paystack specific
            paystack_id=tx_data.get('id'),
            access_code=tx_data.get('access_code'),
            authorization=tx_data.get('authorization'),
            paystack_fee=fees,
            paystack_metadata=tx_data.get('metadata'),
            requested_amount=amount,
            
            # Additional metadata
            gateway_response=tx_data.get('gateway_response'),
            ip_address=tx_data.get('ip_address'),
            metadata=tx_data.get('metadata', {})
        )

    async def _process_customer_response(self, response_data: Dict[str, Any]) -> List[PaystackCustomer]:
        """Process customer API response."""
        customers = []
        
        if response_data.get('status') and response_data.get('data'):
            for customer_data in response_data['data']:
                try:
                    customer = PaystackCustomer(
                        customer_id=customer_data.get('customer_code', ''),
                        email=customer_data.get('email', ''),
                        phone=customer_data.get('phone', ''),
                        first_name=customer_data.get('first_name'),
                        last_name=customer_data.get('last_name'),
                        
                        # Paystack specific
                        paystack_customer_code=customer_data.get('customer_code'),
                        integration=customer_data.get('integration'),
                        domain=customer_data.get('domain'),
                        dedicated_account=customer_data.get('dedicated_account'),
                        
                        # Analytics
                        transactions_count=customer_data.get('transactions_count', 0),
                        transactions_value=Decimal(str(customer_data.get('transactions_value', 0))) / 100,
                        
                        # Verification status
                        email_verified=customer_data.get('identified', False),
                        phone_verified=customer_data.get('identified', False),
                        identity_verified=customer_data.get('identified', False),
                        
                        metadata=customer_data.get('metadata', {})
                    )
                    customers.append(customer)
                except Exception as e:
                    self.logger.warning(f"Error converting customer: {str(e)}")
                    continue
        
        return customers

    async def _process_refund_response(self, response_data: Dict[str, Any]) -> List[PaystackRefund]:
        """Process refund API response."""
        refunds = []
        
        if response_data.get('status') and response_data.get('data'):
            for refund_data in response_data['data']:
                try:
                    refund = PaystackRefund(
                        refund_id=str(refund_data.get('id', '')),
                        transaction_id=str(refund_data.get('transaction', {}).get('id', '')),
                        reference=refund_data.get('transaction', {}).get('reference', ''),
                        amount=Decimal(str(refund_data.get('amount', 0))) / 100,
                        currency=refund_data.get('currency', 'NGN'),
                        reason=refund_data.get('merchant_note'),
                        status=PaymentStatus.SUCCESS if refund_data.get('status') == 'processed' else PaymentStatus.PENDING,
                        created_at=datetime.fromisoformat(refund_data['created_at'].replace('Z', '+00:00')),
                        
                        # Paystack specific
                        paystack_refund_id=refund_data.get('id'),
                        merchant_note=refund_data.get('merchant_note'),
                        customer_note=refund_data.get('customer_note'),
                        
                        # Refund details
                        original_amount=Decimal(str(refund_data.get('transaction', {}).get('amount', 0))) / 100,
                        
                        metadata=refund_data
                    )
                    refunds.append(refund)
                except Exception as e:
                    self.logger.warning(f"Error converting refund: {str(e)}")
                    continue
        
        return refunds

    async def _process_settlement_response(self, response_data: Dict[str, Any]) -> List[PaystackSettlement]:
        """Process settlement API response."""
        settlements = []
        
        if response_data.get('status') and response_data.get('data'):
            for settlement_data in response_data['data']:
                try:
                    settlement = PaystackSettlement(
                        settlement_id=settlement_data.get('id'),
                        domain=settlement_data.get('domain', ''),
                        total_amount=Decimal(str(settlement_data.get('total_amount', 0))) / 100,
                        settled_amount=Decimal(str(settlement_data.get('settled_amount', 0))) / 100,
                        settlement_date=datetime.fromisoformat(settlement_data['settlement_date'].replace('Z', '+00:00')),
                        status=settlement_data.get('status', 'pending'),
                        currency=settlement_data.get('currency', 'NGN'),
                        transaction_count=settlement_data.get('transaction_count', 0),
                        transactions=settlement_data.get('transactions', [])
                    )
                    settlements.append(settlement)
                except Exception as e:
                    self.logger.warning(f"Error converting settlement: {str(e)}")
                    continue
        
        return settlements