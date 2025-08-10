"""
Interswitch Payment Processor
============================

Core payment processing engine for Interswitch integration with AI-based Nigerian 
business classification and NDPR-compliant privacy protection.

Specializes in interbank transfers and NIBSS infrastructure processing.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import aiohttp
from dataclasses import dataclass

from .models import (
    InterswitchTransaction, InterswitchCustomer, InterswitchTransactionType,
    InterswitchTransactionStatus, InterswitchApiResponse, NIGERIAN_BANKS
)
from .auth import InterswitchAuthManager, InterswitchCredentials
from taxpoynt_platform.core_platform.ai.classification.service import ClassificationService
from taxpoynt_platform.core_platform.data_management.privacy.service import PrivacyService
from taxpoynt_platform.core_platform.monitoring.logging.service import LoggingService
from taxpoynt_platform.core_platform.data_management.privacy.models import PrivacyLevel


@dataclass
class InterswitchConfig:
    """Interswitch processor configuration"""
    client_id: str
    client_secret: str
    merchant_id: str
    environment: str = "sandbox"
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    enable_ai_classification: bool = True
    rate_limit_per_minute: int = 120
    request_timeout: int = 30


class InterswitchPaymentProcessor:
    """
    Interswitch payment processor with Nigerian interbank intelligence
    
    Specializes in:
    - Interbank transfer processing
    - NIBSS NIP transactions
    - RTGS and ACH processing
    - AI-powered business classification
    - NDPR privacy compliance
    """
    
    def __init__(self, config: InterswitchConfig):
        self.config = config
        
        # Initialize services
        credentials = InterswitchCredentials(
            client_id=config.client_id,
            client_secret=config.client_secret,
            merchant_id=config.merchant_id,
            environment=config.environment
        )
        
        self.auth_manager = InterswitchAuthManager(credentials)
        self.ai_classifier = ClassificationService()
        self.privacy_service = PrivacyService()
        self.logger = LoggingService().get_logger("interswitch_processor")
        
        # API endpoints
        self.base_url = self._get_base_url()
        self.endpoints = {
            'transactions': f"{self.base_url}/api/v1/transactions",
            'interbank_transfer': f"{self.base_url}/api/v1/interbank/transfer",
            'nibss_nip': f"{self.base_url}/api/v1/nibss/nip",
            'rtgs': f"{self.base_url}/api/v1/rtgs",
            'query_transaction': f"{self.base_url}/api/v1/transactions/query",
            'bank_lookup': f"{self.base_url}/api/v1/banks",
            'account_inquiry': f"{self.base_url}/api/v1/account/inquiry"
        }
        
        # Rate limiting
        self._request_timestamps = []
        self._max_requests_per_minute = config.rate_limit_per_minute
    
    def _get_base_url(self) -> str:
        """Get base URL based on environment"""
        if self.config.environment == "production":
            return "https://webpay.interswitchng.com"
        else:
            return "https://sandbox.interswitchng.com"
    
    async def fetch_transactions(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[InterswitchTransaction]:
        """
        Fetch transactions from Interswitch with AI classification
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
                        
                        self.logger.info("Successfully fetched Interswitch transactions", extra={
                            'count': len(transactions),
                            'start_date': start_date.isoformat(),
                            'end_date': end_date.isoformat()
                        })
                        
                        return transactions
                    else:
                        error_data = await response.text()
                        raise Exception(f"Failed to fetch transactions: {response.status} - {error_data}")
                        
        except Exception as e:
            self.logger.error("Error fetching Interswitch transactions", extra={
                'error': str(e),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            })
            raise
    
    async def _process_transaction_data(self, raw_transactions: List[Dict]) -> List[InterswitchTransaction]:
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
    
    async def _create_transaction_from_raw(self, raw_tx: Dict) -> InterswitchTransaction:
        """
        Create InterswitchTransaction from raw API response
        """
        # Extract customer data
        customer = None
        if raw_tx.get('customer'):
            customer_data = raw_tx['customer']
            customer = InterswitchCustomer(
                customer_id=customer_data.get('id'),
                account_number=customer_data.get('account_number'),
                bank_code=customer_data.get('bank_code'),
                bvn=customer_data.get('bvn'),
                full_name=customer_data.get('full_name'),
                phone_number=customer_data.get('phone_number'),
                email=customer_data.get('email'),
                customer_reference=customer_data.get('customer_reference'),
                account_type=customer_data.get('account_type'),
                kyc_level=customer_data.get('kyc_level'),
                bank_name=customer_data.get('bank_name'),
                interswitch_metadata=customer_data.get('metadata', {})
            )
        
        # Map transaction type
        tx_type = self._map_transaction_type(raw_tx.get('type', 'interbank_transfer'))
        
        # Map status
        status = self._map_transaction_status(raw_tx.get('status', 'pending'))
        
        # Map channel
        channel = self._map_payment_channel(raw_tx.get('channel', 'nibss_nip'))
        
        transaction = InterswitchTransaction(
            transaction_id=raw_tx['id'],
            reference=raw_tx.get('reference', raw_tx['id']),
            amount=Decimal(str(raw_tx['amount'])),
            currency=raw_tx.get('currency', 'NGN'),
            transaction_type=tx_type,
            status=status,
            channel=channel,
            description=raw_tx.get('description'),
            customer=customer,
            customer_id=raw_tx.get('customer_id'),
            originating_bank_code=raw_tx.get('originating_bank_code'),
            destination_bank_code=raw_tx.get('destination_bank_code'),
            originating_account=raw_tx.get('originating_account'),
            destination_account=raw_tx.get('destination_account'),
            originating_bank_name=raw_tx.get('originating_bank_name'),
            destination_bank_name=raw_tx.get('destination_bank_name'),
            nibss_session_id=raw_tx.get('nibss_session_id'),
            nip_session_id=raw_tx.get('nip_session_id'),
            settlement_id=raw_tx.get('settlement_id'),
            transaction_date=datetime.fromisoformat(raw_tx.get('created_at', datetime.utcnow().isoformat())),
            value_date=datetime.fromisoformat(raw_tx['value_date']) if raw_tx.get('value_date') else None,
            settlement_date=datetime.fromisoformat(raw_tx['settlement_date']) if raw_tx.get('settlement_date') else None,
            fees=Decimal(str(raw_tx['fees'])) if raw_tx.get('fees') else None,
            charges=Decimal(str(raw_tx['charges'])) if raw_tx.get('charges') else None,
            interswitch_metadata=raw_tx.get('metadata', {})
        )
        
        return transaction
    
    def _map_transaction_type(self, raw_type: str) -> InterswitchTransactionType:
        """Map raw transaction type to enum"""
        type_mapping = {
            'interbank_transfer': InterswitchTransactionType.INTERBANK_TRANSFER,
            'nibss_instant_payment': InterswitchTransactionType.NIBSS_INSTANT_PAYMENT,
            'nip': InterswitchTransactionType.NIBSS_INSTANT_PAYMENT,
            'rtgs_transfer': InterswitchTransactionType.RTGS_TRANSFER,
            'rtgs': InterswitchTransactionType.RTGS_TRANSFER,
            'ach_transfer': InterswitchTransactionType.ACH_TRANSFER,
            'ach': InterswitchTransactionType.ACH_TRANSFER,
            'card_payment': InterswitchTransactionType.CARD_PAYMENT,
            'direct_debit': InterswitchTransactionType.DIRECT_DEBIT,
            'standing_order': InterswitchTransactionType.STANDING_ORDER,
            'bulk_payment': InterswitchTransactionType.BULK_PAYMENT,
            'salary_payment': InterswitchTransactionType.SALARY_PAYMENT,
            'pension_payment': InterswitchTransactionType.PENSION_PAYMENT,
            'government_payment': InterswitchTransactionType.GOVERNMENT_PAYMENT,
            'tax_payment': InterswitchTransactionType.TAX_PAYMENT
        }
        
        return type_mapping.get(raw_type, InterswitchTransactionType.INTERBANK_TRANSFER)
    
    def _map_transaction_status(self, raw_status: str) -> InterswitchTransactionStatus:
        """Map raw transaction status to enum"""
        status_mapping = {
            'pending': InterswitchTransactionStatus.PENDING,
            'processing': InterswitchTransactionStatus.PROCESSING,
            'successful': InterswitchTransactionStatus.SUCCESSFUL,
            'completed': InterswitchTransactionStatus.COMPLETED,
            'failed': InterswitchTransactionStatus.FAILED,
            'cancelled': InterswitchTransactionStatus.CANCELLED,
            'expired': InterswitchTransactionStatus.EXPIRED,
            'reversed': InterswitchTransactionStatus.REVERSED,
            'settled': InterswitchTransactionStatus.SETTLED,
            'reconciled': InterswitchTransactionStatus.RECONCILED
        }
        
        return status_mapping.get(raw_status, InterswitchTransactionStatus.PENDING)
    
    def _map_payment_channel(self, raw_channel: str) -> 'InterswitchPaymentChannel':
        """Map raw payment channel to enum"""
        from .models import InterswitchPaymentChannel
        
        channel_mapping = {
            'nibss_nip': InterswitchPaymentChannel.NIBSS_NIP,
            'nip': InterswitchPaymentChannel.NIBSS_NIP,
            'rtgs': InterswitchPaymentChannel.RTGS,
            'ach': InterswitchPaymentChannel.ACH,
            'card_scheme': InterswitchPaymentChannel.CARD_SCHEME,
            'direct_debit': InterswitchPaymentChannel.DIRECT_DEBIT,
            'api': InterswitchPaymentChannel.API,
            'web_portal': InterswitchPaymentChannel.WEB_PORTAL,
            'mobile_app': InterswitchPaymentChannel.MOBILE_APP
        }
        
        return channel_mapping.get(raw_channel, InterswitchPaymentChannel.NIBSS_NIP)
    
    async def _apply_ai_classification(self, transaction: InterswitchTransaction) -> InterswitchTransaction:
        """
        Apply AI-based Nigerian business classification to transaction
        """
        try:
            # Prepare classification context
            classification_context = {
                'transaction_type': transaction.transaction_type.value,
                'amount': float(transaction.amount),
                'description': transaction.description or '',
                'channel': transaction.channel.value,
                'processor': 'interswitch',
                'country': 'nigeria',
                'originating_bank': transaction.originating_bank_name,
                'destination_bank': transaction.destination_bank_name,
                'is_interbank': True
            }
            
            # Add specific context for different transaction types
            if transaction.transaction_type == InterswitchTransactionType.SALARY_PAYMENT:
                classification_context['is_salary'] = True
            elif transaction.transaction_type == InterswitchTransactionType.TAX_PAYMENT:
                classification_context['is_tax_payment'] = True
            elif transaction.transaction_type == InterswitchTransactionType.GOVERNMENT_PAYMENT:
                classification_context['is_government'] = True
            
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
    
    async def _apply_rule_based_classification(self, transaction: InterswitchTransaction) -> InterswitchTransaction:
        """
        Fallback rule-based classification for Nigerian business categories
        """
        # Amount-based classification
        amount = float(transaction.amount)
        
        # Transaction type-based classification
        if transaction.transaction_type == InterswitchTransactionType.SALARY_PAYMENT:
            transaction.business_category = "payroll_management"
            transaction.tax_category = "salary_payment"
            transaction.firs_classification = "employee_salary"
        
        elif transaction.transaction_type == InterswitchTransactionType.TAX_PAYMENT:
            transaction.business_category = "tax_compliance"
            transaction.tax_category = "tax_payment"
            transaction.firs_classification = "tax_remittance"
        
        elif transaction.transaction_type == InterswitchTransactionType.GOVERNMENT_PAYMENT:
            transaction.business_category = "government_services"
            transaction.tax_category = "government_fee"
            transaction.firs_classification = "government_payment"
        
        elif transaction.transaction_type == InterswitchTransactionType.BULK_PAYMENT:
            if amount >= 10_000_000:  # 10M+ bulk payments
                transaction.business_category = "corporate_finance"
                transaction.tax_category = "corporate_bulk_payment"
                transaction.firs_classification = "corporate_bulk_transfer"
            else:
                transaction.business_category = "batch_payment"
                transaction.tax_category = "bulk_transfer"
                transaction.firs_classification = "bulk_payment"
        
        elif transaction.transaction_type == InterswitchTransactionType.RTGS_TRANSFER:
            if amount >= 50_000_000:  # 50M+ RTGS
                transaction.business_category = "high_value_transfer"
                transaction.tax_category = "large_transaction"
                transaction.firs_classification = "high_value_rtgs"
            else:
                transaction.business_category = "rtgs_transfer"
                transaction.tax_category = "interbank_transfer"
                transaction.firs_classification = "rtgs_transaction"
        
        elif transaction.transaction_type == InterswitchTransactionType.NIBSS_INSTANT_PAYMENT:
            if amount >= 1_000_000:  # 1M+ NIP
                transaction.business_category = "business_transfer"
                transaction.tax_category = "business_payment"
                transaction.firs_classification = "business_nip"
            else:
                transaction.business_category = "instant_payment"
                transaction.tax_category = "instant_transfer"
                transaction.firs_classification = "nip_transaction"
        
        else:
            # General interbank transfer
            if amount >= 5_000_000:  # 5M+ general transfers
                transaction.business_category = "corporate_transfer"
                transaction.tax_category = "corporate_payment"
                transaction.firs_classification = "corporate_interbank"
            else:
                transaction.business_category = "interbank_transfer"
                transaction.tax_category = "financial_transfer"
                transaction.firs_classification = "interbank_payment"
        
        transaction.ai_confidence_score = 0.75  # Rule-based confidence
        
        return transaction
    
    async def query_transaction_status(self, transaction_id: str) -> InterswitchApiResponse:
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
                    self.endpoints['query_transaction'],
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return InterswitchApiResponse.success_response(
                            data, 
                            data.get('response_code', '00')
                        )
                    else:
                        error_data = await response.text()
                        return InterswitchApiResponse.error_response(
                            f"HTTP_{response.status}",
                            error_data
                        )
                        
        except Exception as e:
            self.logger.error("Error querying transaction status", extra={
                'transaction_id': transaction_id,
                'error': str(e)
            })
            return InterswitchApiResponse.error_response("QUERY_ERROR", str(e))
    
    async def get_bank_list(self) -> List[Dict[str, Any]]:
        """
        Get list of Nigerian banks supported by Interswitch
        """
        await self._enforce_rate_limit()
        
        try:
            headers = await self.auth_manager.create_authenticated_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.endpoints['bank_lookup'],
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data.get('banks', [])
                    else:
                        # Fallback to static bank list
                        self.logger.warning("Failed to fetch bank list, using static data")
                        return [
                            {
                                'bank_code': bank.bank_code,
                                'bank_name': bank.bank_name,
                                'swift_code': bank.swift_code,
                                'supports_nip': bank.supports_nip,
                                'supports_rtgs': bank.supports_rtgs
                            }
                            for bank in NIGERIAN_BANKS.values()
                        ]
                        
        except Exception as e:
            self.logger.error("Error fetching bank list", extra={'error': str(e)})
            # Return static bank list as fallback
            return [
                {
                    'bank_code': bank.bank_code,
                    'bank_name': bank.bank_name,
                    'swift_code': bank.swift_code,
                    'supports_nip': bank.supports_nip,
                    'supports_rtgs': bank.supports_rtgs
                }
                for bank in NIGERIAN_BANKS.values()
            ]
    
    async def perform_account_inquiry(self, account_number: str, bank_code: str) -> InterswitchApiResponse:
        """
        Perform account name inquiry for verification
        """
        await self._enforce_rate_limit()
        
        try:
            payload = {
                'account_number': account_number,
                'bank_code': bank_code
            }
            
            headers = await self.auth_manager.create_signed_request_headers(payload)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoints['account_inquiry'],
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return InterswitchApiResponse.success_response(
                            data,
                            data.get('response_code', '00')
                        )
                    else:
                        error_data = await response.text()
                        return InterswitchApiResponse.error_response(
                            f"HTTP_{response.status}",
                            error_data
                        )
                        
        except Exception as e:
            self.logger.error("Error performing account inquiry", extra={
                'account_number': account_number[-4:],  # Only log last 4 digits
                'bank_code': bank_code,
                'error': str(e)
            })
            return InterswitchApiResponse.error_response("INQUIRY_ERROR", str(e))
    
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
            'processor': 'interswitch',
            'environment': self.config.environment,
            'privacy_level': self.config.privacy_level.value,
            'ai_classification_enabled': self.config.enable_ai_classification,
            'rate_limit_per_minute': self._max_requests_per_minute,
            'recent_requests': len(self._request_timestamps),
            'specializations': [
                'interbank_transfers',
                'nibss_nip',
                'rtgs_transfers',
                'ach_transfers',
                'bulk_payments',
                'government_payments'
            ]
        }


# Export for use in other modules
__all__ = [
    'InterswitchConfig',
    'InterswitchPaymentProcessor'
]