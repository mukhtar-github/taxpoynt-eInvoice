"""
Flutterwave Payment Processor
============================

Core payment processing functionality for Flutterwave integration with
Pan-African support and comprehensive Nigerian business classification.

Features:
- Multi-country payment processing across 34+ African countries
- Mobile money integration for all major African providers
- AI-based Nigerian business transaction classification
- NDPR-compliant privacy protection and data handling
- Real-time transaction processing and verification
- Comprehensive fee calculation and currency conversion
- Multi-currency support for cross-border transactions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .models import (
    FlutterwaveTransaction, FlutterwaveCustomer, FlutterwaveRefund,
    FlutterwavePaymentMethod, FlutterwaveCurrency, FlutterwaveCountry,
    FlutterwaveTransactionFee, FlutterwaveCard, FlutterwaveMobileMoney,
    MobileMoneyProvider, AFRICAN_COUNTRY_CURRENCIES, MOBILE_MONEY_COUNTRIES
)
from .auth import FlutterwaveAuthManager, FlutterwaveCredentials
from ....connector_framework.classification_engine.nigerian_classifier import (
    NigerianTransactionClassifier, TransactionClassificationRequest,
    UserContext, NigerianBusinessContext, PrivacyLevel
)
from ....connector_framework.classification_engine.privacy_protection import (
    APIPrivacyProtection, PIIRedactor
)


@dataclass
class FlutterwaveProcessorConfig:
    """Configuration for Flutterwave payment processor"""
    
    # Authentication
    public_key: str
    secret_key: str
    webhook_secret: Optional[str] = None
    environment: str = "sandbox"
    
    # Processing settings
    enable_ai_classification: bool = True
    openai_api_key: Optional[str] = None
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    
    # Multi-country settings
    default_country: FlutterwaveCountry = FlutterwaveCountry.NIGERIA
    supported_countries: List[FlutterwaveCountry] = None
    
    # Fee settings
    merchant_fee_percentage: Decimal = Decimal('0.014')  # 1.4%
    currency_conversion_margin: Decimal = Decimal('0.02')  # 2%
    
    # Limits
    single_transaction_limit: Dict[str, Decimal] = None
    daily_transaction_limit: Dict[str, Decimal] = None
    
    # Processing options
    auto_settlement: bool = True
    settlement_currency: FlutterwaveCurrency = FlutterwaveCurrency.NGN
    enable_split_payments: bool = False
    
    def __post_init__(self):
        if self.supported_countries is None:
            self.supported_countries = [
                FlutterwaveCountry.NIGERIA,
                FlutterwaveCountry.GHANA, 
                FlutterwaveCountry.KENYA,
                FlutterwaveCountry.UGANDA,
                FlutterwaveCountry.SOUTH_AFRICA
            ]
        
        if self.single_transaction_limit is None:
            self.single_transaction_limit = {
                'NGN': Decimal('5000000'),    # ₦5M
                'GHS': Decimal('50000'),      # GH₵50K
                'KES': Decimal('500000'),     # KSh500K
                'UGX': Decimal('10000000'),   # USh10M
                'ZAR': Decimal('100000'),     # R100K
                'USD': Decimal('50000')       # $50K
            }
        
        if self.daily_transaction_limit is None:
            self.daily_transaction_limit = {
                'NGN': Decimal('20000000'),   # ₦20M
                'GHS': Decimal('200000'),     # GH₵200K  
                'KES': Decimal('2000000'),    # KSh2M
                'UGX': Decimal('40000000'),   # USh40M
                'ZAR': Decimal('400000'),     # R400K
                'USD': Decimal('200000')      # $200K
            }


class FlutterwavePaymentProcessor:
    """
    Flutterwave payment processor with Pan-African support
    
    Handles payment processing, verification, transaction management,
    and business classification for all African markets supported by Flutterwave.
    """
    
    def __init__(self, config: FlutterwaveProcessorConfig):
        """
        Initialize Flutterwave payment processor
        
        Args:
            config: FlutterwaveProcessorConfig with processing settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize authentication manager
        credentials = FlutterwaveCredentials(
            public_key=config.public_key,
            secret_key=config.secret_key,
            webhook_secret=config.webhook_secret,
            environment=config.environment
        )
        
        self.auth_manager = FlutterwaveAuthManager(credentials)
        
        # Initialize classification components
        if config.enable_ai_classification:
            self.transaction_classifier = NigerianTransactionClassifier(
                api_key=config.openai_api_key
            )
        else:
            self.transaction_classifier = None
        
        self.privacy_protection = APIPrivacyProtection()
        self.pii_redactor = PIIRedactor()
        
        # Processing state
        self.processed_transactions = {}
        self.processing_stats = {
            'total_processed': 0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'total_volume': Decimal('0'),
            'countries_processed': set(),
            'payment_methods_used': set(),
            'ai_classifications': 0,
            'rule_based_classifications': 0
        }
        
        self.logger.info(f"Flutterwave processor initialized for {len(config.supported_countries)} countries")
    
    async def initiate_payment(
        self,
        amount: Decimal,
        currency: FlutterwaveCurrency,
        customer: FlutterwaveCustomer,
        payment_method: FlutterwavePaymentMethod,
        reference: str,
        callback_url: Optional[str] = None,
        country: Optional[FlutterwaveCountry] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate a payment transaction
        
        Args:
            amount: Payment amount
            currency: Payment currency
            customer: Customer information
            payment_method: Payment method to use
            reference: Unique transaction reference
            callback_url: Optional callback URL
            country: Country for payment
            metadata: Additional metadata
            
        Returns:
            Payment initiation response
        """
        try:
            # Validate transaction limits
            await self._validate_transaction_limits(amount, currency)
            
            # Determine country if not provided
            if not country:
                country = self.config.default_country
            
            # Build payment request
            payment_data = {
                "tx_ref": reference,
                "amount": str(amount),
                "currency": currency.value,
                "payment_options": payment_method.value,
                "customer": {
                    "email": customer.email,
                    "phonenumber": customer.phone_number,
                    "name": customer.name
                },
                "customizations": {
                    "title": "TaxPoynt Payment",
                    "description": metadata.get('description', 'Payment for services'),
                    "logo": metadata.get('logo_url') if metadata else None
                },
                "callback": callback_url
            }
            
            # Add country-specific configuration
            if country:
                payment_data["country"] = country.value
            
            # Add mobile money specific fields
            if payment_method == FlutterwavePaymentMethod.MOBILE_MONEY:
                mobile_money_config = await self._get_mobile_money_config(country)
                if mobile_money_config:
                    payment_data.update(mobile_money_config)
            
            # Add metadata
            if metadata:
                payment_data["meta"] = metadata
            
            # Make API request
            response = await self.auth_manager.make_authenticated_request(
                method='POST',
                endpoint='/payments',
                data=payment_data
            )
            
            # Log payment initiation
            self.logger.info("Payment initiated", extra={
                'reference': reference,
                'amount': str(amount),
                'currency': currency.value,
                'country': country.value if country else None,
                'payment_method': payment_method.value,
                'customer_email': customer.email
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Payment initiation failed: {str(e)}", extra={
                'reference': reference,
                'amount': str(amount),
                'currency': currency.value
            })
            raise
    
    async def verify_transaction(self, transaction_id: str) -> Optional[FlutterwaveTransaction]:
        """
        Verify a transaction and convert to our standard format
        
        Args:
            transaction_id: Flutterwave transaction ID
            
        Returns:
            FlutterwaveTransaction if found, None otherwise
        """
        try:
            # Make verification request
            response = await self.auth_manager.make_authenticated_request(
                method='GET',
                endpoint=f'/transactions/{transaction_id}/verify'
            )
            
            if response.get('status') != 'success':
                self.logger.warning(f"Transaction verification failed: {response.get('message')}")
                return None
            
            transaction_data = response.get('data', {})
            
            # Convert to our transaction format
            transaction = await self._convert_transaction_data(transaction_data)
            
            # Apply business classification if enabled
            if self.transaction_classifier and transaction:
                classification = await self._classify_transaction(transaction)
                transaction.business_income_classified = classification.get('is_business_income', False)
                transaction.classification_confidence = classification.get('confidence', 0.0)
                transaction.requires_human_review = classification.get('requires_human_review', False)
            
            # Apply privacy protection
            if transaction:
                transaction = await self._apply_privacy_protection(transaction)
            
            # Update statistics
            if transaction:
                self.processing_stats['total_processed'] += 1
                if transaction.payment_status.value == 'successful':
                    self.processing_stats['successful_transactions'] += 1
                    self.processing_stats['total_volume'] += transaction.amount
                else:
                    self.processing_stats['failed_transactions'] += 1
                
                if transaction.country:
                    self.processing_stats['countries_processed'].add(transaction.country.value)
                if transaction.payment_method:
                    self.processing_stats['payment_methods_used'].add(transaction.payment_method.value)
            
            self.logger.debug("Transaction verified", extra={
                'transaction_id': transaction_id,
                'status': transaction.payment_status.value if transaction else 'not_found',
                'amount': str(transaction.amount) if transaction else None
            })
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Transaction verification error: {str(e)}", extra={
                'transaction_id': transaction_id
            })
            return None
    
    async def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        currency: Optional[FlutterwaveCurrency] = None,
        country: Optional[FlutterwaveCountry] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FlutterwaveTransaction]:
        """
        Get list of transactions with filtering
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            status: Status filter
            currency: Currency filter
            country: Country filter
            limit: Maximum number of transactions
            offset: Pagination offset
            
        Returns:
            List of FlutterwaveTransaction objects
        """
        try:
            # Build query parameters
            params = {
                'per_page': min(limit, 500),  # Flutterwave max per page
                'page': (offset // limit) + 1
            }
            
            if start_date:
                params['from'] = start_date.strftime('%Y-%m-%d')
            
            if end_date:
                params['to'] = end_date.strftime('%Y-%m-%d')
            
            if status:
                params['status'] = status
            
            if currency:
                params['currency'] = currency.value
            
            # Make API request
            response = await self.auth_manager.make_authenticated_request(
                method='GET',
                endpoint='/transactions',
                params=params,
                country=country
            )
            
            if response.get('status') != 'success':
                self.logger.warning(f"Failed to get transactions: {response.get('message')}")
                return []
            
            transactions_data = response.get('data', [])
            
            # Convert transactions
            transactions = []
            for tx_data in transactions_data:
                transaction = await self._convert_transaction_data(tx_data)
                if transaction:
                    # Apply classification and privacy protection
                    if self.transaction_classifier:
                        classification = await self._classify_transaction(transaction)
                        transaction.business_income_classified = classification.get('is_business_income', False)
                        transaction.classification_confidence = classification.get('confidence', 0.0)
                    
                    transaction = await self._apply_privacy_protection(transaction)
                    transactions.append(transaction)
            
            self.logger.info("Transactions retrieved", extra={
                'count': len(transactions),
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'filters': {
                    'status': status,
                    'currency': currency.value if currency else None,
                    'country': country.value if country else None
                }
            })
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error retrieving transactions: {str(e)}")
            return []
    
    async def get_banks(self, country: FlutterwaveCountry) -> List[Dict[str, Any]]:
        """
        Get list of banks for a specific country
        
        Args:
            country: Country to get banks for
            
        Returns:
            List of bank information
        """
        try:
            response = await self.auth_manager.make_authenticated_request(
                method='GET',
                endpoint='/banks/{country}',
                country=country
            )
            
            return response.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting banks for {country}: {str(e)}")
            return []
    
    async def get_mobile_money_providers(self, country: FlutterwaveCountry) -> List[Dict[str, Any]]:
        """
        Get mobile money providers for a country
        
        Args:
            country: Country to get providers for
            
        Returns:
            List of mobile money provider information
        """
        try:
            response = await self.auth_manager.make_authenticated_request(
                method='GET',
                endpoint='/mobile-money/{country}',
                country=country
            )
            
            return response.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error getting mobile money providers for {country}: {str(e)}")
            return []
    
    async def _convert_transaction_data(self, data: Dict[str, Any]) -> Optional[FlutterwaveTransaction]:
        """Convert Flutterwave API response to FlutterwaveTransaction"""
        try:
            # Extract basic transaction info
            transaction_id = str(data.get('id', ''))
            flw_ref = data.get('flw_ref', '')
            tx_ref = data.get('tx_ref', '')
            
            # Parse amounts
            amount = Decimal(str(data.get('amount', '0')))
            charged_amount = Decimal(str(data.get('charged_amount', '0')))
            
            # Parse currency and country
            currency = FlutterwaveCurrency(data.get('currency', 'NGN'))
            
            # Try to determine country
            country = None
            if 'country' in data:
                try:
                    country = FlutterwaveCountry(data['country'])
                except ValueError:
                    pass
            
            # Parse payment method
            payment_method = None
            if 'payment_type' in data:
                try:
                    payment_method = FlutterwavePaymentMethod(data['payment_type'])
                except ValueError:
                    pass
            
            # Parse customer info
            customer_data = data.get('customer', {})
            customer = FlutterwaveCustomer(
                email=customer_data.get('email'),
                name=customer_data.get('name'),
                phone_number=customer_data.get('phone_number'),
                country=country
            )
            
            # Parse card details if available
            card_details = None
            if 'card' in data:
                card_info = data['card']
                card_details = FlutterwaveCard(
                    first_6digits=card_info.get('first_6digits'),
                    last_4digits=card_info.get('last_4digits'),
                    card_type=card_info.get('type'),
                    country=card_info.get('country'),
                    issuer=card_info.get('issuer')
                )
            
            # Parse fee details
            fee_details = None
            if 'app_fee' in data or 'merchant_fee' in data:
                fee_details = FlutterwaveTransactionFee(
                    total_fee=Decimal(str(data.get('app_fee', '0'))),
                    flutterwave_fee=Decimal(str(data.get('app_fee', '0'))),
                    merchant_fee=Decimal(str(data.get('merchant_fee', '0')))
                )
            
            # Parse timestamps
            created_at = None
            if 'created_at' in data:
                try:
                    created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            
            # Create transaction object
            transaction = FlutterwaveTransaction(
                transaction_id=transaction_id,
                reference=tx_ref,
                amount=amount,
                currency=currency.value,
                payment_status=data.get('status', 'pending'),
                
                # Flutterwave specific
                flw_ref=flw_ref,
                tx_ref=tx_ref,
                flw_id=data.get('id'),
                payment_method=payment_method,
                country=country,
                
                # Customer info
                customer=customer,
                customer_email=customer.email,
                customer_phone=customer.phone_number,
                customer_name=customer.name,
                
                # Payment details
                card_details=card_details,
                fee_details=fee_details,
                processor_response=data.get('processor_response'),
                
                # Metadata
                description=data.get('narration', ''),
                metadata=data.get('meta', {}),
                
                # Timestamps
                created_at=created_at or datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Failed to convert transaction data: {str(e)}")
            return None
    
    async def _classify_transaction(self, transaction: FlutterwaveTransaction) -> Dict[str, Any]:
        """Classify transaction for Nigerian business income"""
        if not self.transaction_classifier:
            return {
                'is_business_income': False,
                'confidence': 0.0,
                'method': 'no_classifier'
            }
        
        try:
            # Build classification request
            user_context = UserContext(
                user_id=transaction.customer.email or 'unknown',
                organization_id='flutterwave_merchant',
                business_name=getattr(transaction.customer, 'business_name', 'Unknown'),
                business_context=NigerianBusinessContext(
                    industry='payment_processing',
                    business_size='sme',
                    location=transaction.country.value.lower() if transaction.country else 'nigeria',
                    state='lagos'
                )
            )
            
            classification_request = TransactionClassificationRequest(
                amount=transaction.amount,
                narration=transaction.description or f"Payment via {transaction.payment_method.value if transaction.payment_method else 'unknown'}",
                sender_name=transaction.customer.name,
                date=transaction.created_at.date() if transaction.created_at else datetime.utcnow().date(),
                time=transaction.created_at.strftime('%H:%M') if transaction.created_at else datetime.utcnow().strftime('%H:%M'),
                reference=transaction.reference,
                user_context=user_context,
                privacy_level=self.config.privacy_level
            )
            
            # Classify transaction
            result = await self.transaction_classifier.classify_transaction(classification_request)
            
            # Update stats
            if result.metadata.classification_method.startswith('api_'):
                self.processing_stats['ai_classifications'] += 1
            else:
                self.processing_stats['rule_based_classifications'] += 1
            
            return {
                'is_business_income': result.is_business_income,
                'confidence': result.confidence,
                'method': result.metadata.classification_method,
                'reasoning': result.reasoning,
                'requires_human_review': result.requires_human_review
            }
            
        except Exception as e:
            self.logger.error(f"Transaction classification failed: {str(e)}")
            return {
                'is_business_income': False,
                'confidence': 0.0,
                'method': 'error',
                'requires_human_review': True
            }
    
    async def _apply_privacy_protection(self, transaction: FlutterwaveTransaction) -> FlutterwaveTransaction:
        """Apply privacy protection to transaction data"""
        try:
            # Redact PII in description
            if transaction.description:
                redacted_description, _ = self.pii_redactor.redact_pii(transaction.description)
                transaction.description = redacted_description
            
            # Apply privacy level protection
            if self.config.privacy_level in [PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
                if transaction.customer_email:
                    local, domain = transaction.customer_email.split('@')
                    transaction.customer_email = f"[EMAIL]@{domain}"
                
                if transaction.customer_phone:
                    transaction.customer_phone = '[PHONE]'
                
                if self.config.privacy_level == PrivacyLevel.MAXIMUM and transaction.customer_name:
                    transaction.customer_name = '[NAME]'
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Privacy protection failed: {str(e)}")
            return transaction
    
    async def _validate_transaction_limits(self, amount: Decimal, currency: FlutterwaveCurrency):
        """Validate transaction against configured limits"""
        currency_str = currency.value
        
        # Check single transaction limit
        if currency_str in self.config.single_transaction_limit:
            limit = self.config.single_transaction_limit[currency_str]
            if amount > limit:
                raise ValueError(f"Transaction amount {amount} {currency_str} exceeds single transaction limit {limit}")
    
    async def _get_mobile_money_config(self, country: FlutterwaveCountry) -> Optional[Dict[str, Any]]:
        """Get mobile money configuration for a country"""
        if country == FlutterwaveCountry.GHANA:
            return {
                "phone_number": "233xxxxxxxxx",
                "network": "MTN"
            }
        elif country == FlutterwaveCountry.KENYA:
            return {
                "phone_number": "254xxxxxxxxx",
                "network": "MPESA"
            }
        elif country == FlutterwaveCountry.UGANDA:
            return {
                "phone_number": "256xxxxxxxxx",
                "network": "MTNMOMO"
            }
        
        return None
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return {
            **self.processing_stats,
            'countries_processed': list(self.processing_stats['countries_processed']),
            'payment_methods_used': list(self.processing_stats['payment_methods_used']),
            'supported_countries': [c.value for c in self.config.supported_countries],
            'ai_classification_enabled': self.config.enable_ai_classification,
            'privacy_level': self.config.privacy_level.value,
            'total_volume_formatted': f"{self.processing_stats['total_volume']:.2f}"
        }


__all__ = [
    'FlutterwaveProcessorConfig',
    'FlutterwavePaymentProcessor'
]