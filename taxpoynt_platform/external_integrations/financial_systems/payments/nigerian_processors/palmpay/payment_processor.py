"""
PalmPay Payment Processor
========================

Core payment processing engine for PalmPay integration with AI-based Nigerian 
business classification and NDPR-compliant privacy protection.

Specializes in inter-bank transfers and mobile money transactions.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import aiohttp
from dataclasses import dataclass

from .models import (
    PalmPayTransaction, PalmPayCustomer, PalmPayTransactionType,
    PalmPayTransactionStatus, PalmPayApiResponse
)
from .auth import PalmPayAuthManager, PalmPayCredentials
from taxpoynt_platform.core_platform.ai.classification.service import ClassificationService
from taxpoynt_platform.core_platform.data_management.privacy.service import PrivacyService
from taxpoynt_platform.core_platform.monitoring.logging.service import LoggingService
from taxpoynt_platform.core_platform.data_management.privacy.models import PrivacyLevel


@dataclass
class PalmPayConfig:
    """PalmPay processor configuration"""
    api_key: str
    secret_key: str
    merchant_id: str
    environment: str = "sandbox"
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    enable_ai_classification: bool = True
    rate_limit_per_minute: int = 100
    request_timeout: int = 30


class PalmPayPaymentProcessor:
    """
    PalmPay payment processor with Nigerian business intelligence
    
    Specializes in:
    - Inter-bank transfer processing
    - Mobile money transactions
    - AI-powered business classification
    - NDPR privacy compliance
    """
    
    def __init__(self, config: PalmPayConfig):
        self.config = config
        
        # Initialize services
        credentials = PalmPayCredentials(
            api_key=config.api_key,
            secret_key=config.secret_key,
            merchant_id=config.merchant_id,
            environment=config.environment
        )
        
        self.auth_manager = PalmPayAuthManager(credentials)
        self.ai_classifier = ClassificationService()
        self.privacy_service = PrivacyService()
        self.logger = LoggingService().get_logger("palmpay_processor")
        
        # API endpoints
        self.base_url = self._get_base_url()
        self.endpoints = {
            'transactions': f"{self.base_url}/api/v1/transactions",
            'payment_notification': f"{self.base_url}/api/v1/payment/notification",
            'query_status': f"{self.base_url}/api/v1/query/status",
            'customer_info': f"{self.base_url}/api/v1/customer/info"
        }
        
        # Rate limiting
        self._request_timestamps = []
        self._max_requests_per_minute = config.rate_limit_per_minute
    
    def _get_base_url(self) -> str:
        """Get base URL based on environment"""
        if self.config.environment == "production":
            return "https://api.palmpay.com"
        else:
            return "https://sandbox-api.palmpay.com"
    
    async def fetch_transactions(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[PalmPayTransaction]:
        """
        Fetch transactions from PalmPay with AI classification
        """
        await self._enforce_rate_limit()
        
        try:
            params = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'limit': limit,
                'offset': offset,
                'merchant_id': self.config.merchant_id
            }
            
            headers = await self.auth_manager.create_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.endpoints['transactions'],
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        transactions = await self._process_transaction_data(data.get('transactions', []))
                        
                        self.logger.info("Successfully fetched PalmPay transactions", extra={
                            'count': len(transactions),
                            'start_date': start_date.isoformat(),
                            'end_date': end_date.isoformat()
                        })
                        
                        return transactions
                    else:
                        error_data = await response.text()
                        raise Exception(f"Failed to fetch transactions: {response.status} - {error_data}")
                        
        except Exception as e:
            self.logger.error("Error fetching PalmPay transactions", extra={
                'error': str(e),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            })
            raise
    
    async def _process_transaction_data(self, raw_transactions: List[Dict]) -> List[PalmPayTransaction]:
        """
        Process raw transaction data with AI classification and privacy protection
        """
        processed_transactions = []
        
        for raw_tx in raw_transactions:
            try:
                # Create base transaction
                transaction = await self._create_transaction_from_raw(raw_tx)
                
                # Apply AI classification if enabled
                if self.config.enable_ai_classification:
                    transaction = await self._apply_ai_classification(transaction)
                
                # Apply privacy protection
                transaction = transaction.apply_privacy_protection(self.config.privacy_level)
                
                processed_transactions.append(transaction)
                
            except Exception as e:
                self.logger.error("Error processing transaction", extra={
                    'transaction_id': raw_tx.get('id', 'unknown'),
                    'error': str(e)
                })
                continue
        
        return processed_transactions
    
    async def _create_transaction_from_raw(self, raw_tx: Dict) -> PalmPayTransaction:
        """
        Create PalmPayTransaction from raw API response
        """
        # Extract customer data
        customer = None
        if raw_tx.get('customer'):
            customer_data = raw_tx['customer']
            customer = PalmPayCustomer(
                customer_id=customer_data.get('id'),
                phone_number=customer_data.get('phone_number'),
                email=customer_data.get('email'),
                full_name=customer_data.get('full_name'),
                wallet_id=customer_data.get('wallet_id'),
                account_tier=customer_data.get('account_tier'),
                bank_verification_number=customer_data.get('bvn'),
                palmpay_metadata=customer_data.get('metadata', {})
            )
        
        # Map transaction type
        tx_type = self._map_transaction_type(raw_tx.get('type', 'mobile_wallet'))
        
        # Map status
        status = self._map_transaction_status(raw_tx.get('status', 'pending'))
        
        transaction = PalmPayTransaction(
            transaction_id=raw_tx['id'],
            reference=raw_tx.get('reference', raw_tx['id']),
            amount=Decimal(str(raw_tx['amount'])),
            currency=raw_tx.get('currency', 'NGN'),
            transaction_type=tx_type,
            status=status,
            description=raw_tx.get('description'),
            customer=customer,
            customer_id=raw_tx.get('customer_id'),
            sender_account=raw_tx.get('sender_account'),
            receiver_account=raw_tx.get('receiver_account'),
            sender_bank=raw_tx.get('sender_bank'),
            receiver_bank=raw_tx.get('receiver_bank'),
            session_id=raw_tx.get('session_id'),
            transaction_date=datetime.fromisoformat(raw_tx.get('created_at', datetime.utcnow().isoformat())),
            fees=Decimal(str(raw_tx['fees'])) if raw_tx.get('fees') else None,
            palmpay_metadata=raw_tx.get('metadata', {})
        )
        
        return transaction
    
    def _map_transaction_type(self, raw_type: str) -> PalmPayTransactionType:
        """Map raw transaction type to enum"""
        type_mapping = {
            'inter_bank_transfer': PalmPayTransactionType.INTER_BANK_TRANSFER,
            'mobile_wallet': PalmPayTransactionType.MOBILE_WALLET,
            'qr_payment': PalmPayTransactionType.QR_PAYMENT,
            'bill_payment': PalmPayTransactionType.BILL_PAYMENT,
            'airtime': PalmPayTransactionType.AIRTIME_PURCHASE,
            'data_bundle': PalmPayTransactionType.DATA_PURCHASE,
            'money_transfer': PalmPayTransactionType.MONEY_TRANSFER,
            'merchant_payment': PalmPayTransactionType.MERCHANT_PAYMENT,
            'cash_in': PalmPayTransactionType.CASH_IN,
            'cash_out': PalmPayTransactionType.CASH_OUT
        }
        
        return type_mapping.get(raw_type, PalmPayTransactionType.MOBILE_WALLET)
    
    def _map_transaction_status(self, raw_status: str) -> PalmPayTransactionStatus:
        """Map raw transaction status to enum"""
        status_mapping = {
            'pending': PalmPayTransactionStatus.PENDING,
            'processing': PalmPayTransactionStatus.PROCESSING,
            'successful': PalmPayTransactionStatus.SUCCESSFUL,
            'completed': PalmPayTransactionStatus.SUCCESSFUL,
            'failed': PalmPayTransactionStatus.FAILED,
            'cancelled': PalmPayTransactionStatus.CANCELLED,
            'expired': PalmPayTransactionStatus.EXPIRED,
            'reversed': PalmPayTransactionStatus.REVERSED
        }
        
        return status_mapping.get(raw_status, PalmPayTransactionStatus.PENDING)
    
    async def _apply_ai_classification(self, transaction: PalmPayTransaction) -> PalmPayTransaction:
        """
        Apply AI-based Nigerian business classification to transaction
        """
        try:
            # Prepare classification context
            classification_context = {
                'transaction_type': transaction.transaction_type.value,
                'amount': float(transaction.amount),
                'description': transaction.description or '',
                'channel': 'mobile_money',
                'processor': 'palmpay',
                'country': 'nigeria'
            }
            
            # Add inter-bank transfer context
            if transaction.transaction_type == PalmPayTransactionType.INTER_BANK_TRANSFER:
                classification_context.update({
                    'sender_bank': transaction.sender_bank,
                    'receiver_bank': transaction.receiver_bank,
                    'is_interbank': True
                })
            
            # Get AI classification
            classification_result = await self.ai_classifier.classify_nigerian_business_transaction(
                classification_context
            )
            
            if classification_result.success:
                transaction.business_category = classification_result.business_category
                transaction.tax_category = classification_result.tax_category
                transaction.firs_classification = classification_result.firs_classification
                transaction.ai_confidence_score = classification_result.confidence_score
                
                self.logger.debug("AI classification applied", extra={
                    'transaction_id': transaction.transaction_id,
                    'business_category': transaction.business_category,
                    'confidence': transaction.ai_confidence_score
                })
            else:
                # Fallback to rule-based classification
                transaction = await self._apply_rule_based_classification(transaction)
                
        except Exception as e:
            self.logger.warning("AI classification failed, using fallback", extra={
                'transaction_id': transaction.transaction_id,
                'error': str(e)
            })
            transaction = await self._apply_rule_based_classification(transaction)
        
        return transaction
    
    async def _apply_rule_based_classification(self, transaction: PalmPayTransaction) -> PalmPayTransaction:
        """
        Fallback rule-based classification for Nigerian business categories
        """
        # Amount-based classification
        amount = float(transaction.amount)
        
        if transaction.transaction_type == PalmPayTransactionType.INTER_BANK_TRANSFER:
            if amount >= 1_000_000:  # Large transfers
                transaction.business_category = "corporate_finance"
                transaction.tax_category = "corporate_income"
                transaction.firs_classification = "business_transfer"
            else:
                transaction.business_category = "personal_finance"
                transaction.tax_category = "personal_income"
                transaction.firs_classification = "personal_transfer"
        
        elif transaction.transaction_type == PalmPayTransactionType.BILL_PAYMENT:
            transaction.business_category = "utilities_payment"
            transaction.tax_category = "service_fee"
            transaction.firs_classification = "bill_payment"
        
        elif transaction.transaction_type == PalmPayTransactionType.MERCHANT_PAYMENT:
            if amount >= 50_000:
                transaction.business_category = "retail_sales"
                transaction.tax_category = "vat_applicable"
                transaction.firs_classification = "merchant_sale"
            else:
                transaction.business_category = "small_retail"
                transaction.tax_category = "micro_business"
                transaction.firs_classification = "small_sale"
        
        else:
            transaction.business_category = "mobile_money"
            transaction.tax_category = "financial_service"
            transaction.firs_classification = "mobile_transaction"
        
        transaction.ai_confidence_score = 0.7  # Rule-based confidence
        
        return transaction
    
    async def query_transaction_status(self, transaction_id: str) -> PalmPayApiResponse:
        """
        Query the status of a specific transaction
        """
        await self._enforce_rate_limit()
        
        try:
            headers = await self.auth_manager.create_authenticated_headers()
            params = {
                'transaction_id': transaction_id,
                'merchant_id': self.config.merchant_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.endpoints['query_status'],
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return PalmPayApiResponse.success_response(data)
                    else:
                        error_data = await response.text()
                        return PalmPayApiResponse.error_response(
                            f"HTTP_{response.status}",
                            error_data
                        )
                        
        except Exception as e:
            self.logger.error("Error querying transaction status", extra={
                'transaction_id': transaction_id,
                'error': str(e)
            })
            return PalmPayApiResponse.error_response("QUERY_ERROR", str(e))
    
    async def get_customer_info(self, customer_id: str) -> Optional[PalmPayCustomer]:
        """
        Retrieve customer information with privacy protection
        """
        await self._enforce_rate_limit()
        
        try:
            headers = await self.auth_manager.create_authenticated_headers()
            params = {
                'customer_id': customer_id,
                'merchant_id': self.config.merchant_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.endpoints['customer_info'],
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        customer_data = data.get('customer', {})
                        
                        customer = PalmPayCustomer(
                            customer_id=customer_data.get('id'),
                            phone_number=customer_data.get('phone_number'),
                            email=customer_data.get('email'),
                            full_name=customer_data.get('full_name'),
                            wallet_id=customer_data.get('wallet_id'),
                            account_tier=customer_data.get('account_tier'),
                            bank_verification_number=customer_data.get('bvn'),
                            palmpay_metadata=customer_data.get('metadata', {})
                        )
                        
                        # Apply privacy protection
                        return customer.apply_privacy_protection(self.config.privacy_level)
                    
                    return None
                    
        except Exception as e:
            self.logger.error("Error fetching customer info", extra={
                'customer_id': customer_id,
                'error': str(e)
            })
            return None
    
    async def _enforce_rate_limit(self):
        """
        Enforce rate limiting for API requests
        """
        current_time = datetime.utcnow()
        minute_ago = current_time - timedelta(minutes=1)
        
        # Remove old timestamps
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > minute_ago
        ]
        
        # Check if we're at the limit
        if len(self._request_timestamps) >= self._max_requests_per_minute:
            sleep_time = 60 - (current_time - self._request_timestamps[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Add current timestamp
        self._request_timestamps.append(current_time)
    
    async def get_processor_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics and health metrics
        """
        return {
            'processor': 'palmpay',
            'environment': self.config.environment,
            'privacy_level': self.config.privacy_level.value,
            'ai_classification_enabled': self.config.enable_ai_classification,
            'rate_limit_per_minute': self._max_requests_per_minute,
            'recent_requests': len(self._request_timestamps),
            'specializations': [
                'inter_bank_transfers',
                'mobile_money',
                'qr_payments',
                'bill_payments'
            ]
        }


# Export for use in other modules
__all__ = [
    'PalmPayConfig',
    'PalmPayPaymentProcessor'
]