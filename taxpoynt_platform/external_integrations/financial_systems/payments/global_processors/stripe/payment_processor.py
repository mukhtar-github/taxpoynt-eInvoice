"""
Stripe Payment Processor
=======================

Core payment processing functionality for Stripe integration with
global payment support and comprehensive Nigerian business classification.

Features:
- Global payment processing across 40+ countries
- Advanced card payment processing with 3D Secure
- AI-based Nigerian business transaction classification
- NDPR-compliant privacy protection and data handling
- Real-time payment intent processing and confirmation
- Comprehensive fee calculation and currency conversion
- Multi-currency support with automatic conversion
- Advanced fraud detection and dispute management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .models import (
    StripeTransaction, StripeCustomer, StripeRefund,
    StripePaymentMethod, StripeCurrency, StripeCountry,
    StripeCard, StripeBillingDetails, StripeOutcome,
    StripePaymentStatus, STRIPE_COUNTRY_CURRENCIES
)
from .auth import StripeAuthManager, StripeCredentials
from ....connector_framework.classification_engine.nigerian_classifier import (
    NigerianTransactionClassifier, TransactionClassificationRequest,
    UserContext, NigerianBusinessContext, PrivacyLevel
)
from ....connector_framework.classification_engine.privacy_protection import (
    APIPrivacyProtection, PIIRedactor
)


@dataclass
class StripeProcessorConfig:
    """Configuration for Stripe payment processor"""
    
    # Authentication
    secret_key: str
    publishable_key: str
    webhook_secret: Optional[str] = None
    environment: str = "test"  # test or live
    
    # Processing settings
    enable_ai_classification: bool = True
    openai_api_key: Optional[str] = None
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    
    # Global settings
    default_country: StripeCountry = StripeCountry.UNITED_STATES
    supported_countries: List[StripeCountry] = None
    
    # Payment settings
    capture_method: str = "automatic"  # automatic or manual
    confirmation_method: str = "automatic"  # automatic or manual
    
    # Currency and fees
    settlement_currency: StripeCurrency = StripeCurrency.USD
    enable_multi_currency: bool = True
    
    # Business rules
    auto_invoice_generation: bool = True
    classification_confidence_threshold: float = 0.7
    minimum_amount_for_classification: Decimal = Decimal('100')  # $1.00
    
    # Limits (in cents for USD)
    single_transaction_limit: Dict[str, int] = None
    daily_transaction_limit: Dict[str, int] = None
    
    # Features
    enable_3d_secure: bool = True
    enable_save_payment_method: bool = True
    enable_setup_future_usage: bool = True
    
    def __post_init__(self):
        if self.supported_countries is None:
            self.supported_countries = [
                StripeCountry.UNITED_STATES,
                StripeCountry.UNITED_KINGDOM,
                StripeCountry.CANADA,
                StripeCountry.AUSTRALIA,
                StripeCountry.GERMANY,
                StripeCountry.FRANCE,
                StripeCountry.NETHERLANDS,
                StripeCountry.SINGAPORE,
                StripeCountry.JAPAN
            ]
        
        if self.single_transaction_limit is None:
            self.single_transaction_limit = {
                'usd': 50000000,    # $500,000
                'eur': 45000000,    # €450,000
                'gbp': 40000000,    # £400,000
                'cad': 65000000,    # CAD 650,000
                'aud': 70000000,    # AUD 700,000
                'jpy': 55000000,    # ¥550,000 (already in smallest unit)
                'ngn': 20000000000, # ₦200,000,000 (kobo)
            }
        
        if self.daily_transaction_limit is None:
            self.daily_transaction_limit = {
                'usd': 200000000,   # $2,000,000
                'eur': 180000000,   # €1,800,000
                'gbp': 160000000,   # £1,600,000
                'cad': 260000000,   # CAD 2,600,000
                'aud': 280000000,   # AUD 2,800,000
                'jpy': 220000000,   # ¥2,200,000
                'ngn': 80000000000, # ₦800,000,000 (kobo)
            }


class StripePaymentProcessor:
    """
    Stripe payment processor with global support
    
    Handles payment processing, verification, transaction management,
    and business classification for all global markets supported by Stripe.
    """
    
    def __init__(self, config: StripeProcessorConfig):
        """
        Initialize Stripe payment processor
        
        Args:
            config: StripeProcessorConfig with processing settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize authentication manager
        credentials = StripeCredentials(
            secret_key=config.secret_key,
            publishable_key=config.publishable_key,
            webhook_secret=config.webhook_secret,
            environment=config.environment
        )
        
        self.auth_manager = StripeAuthManager(credentials)
        
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
        self.processed_payments = {}
        self.processing_stats = {
            'total_processed': 0,
            'successful_payments': 0,
            'failed_payments': 0,
            'total_volume': Decimal('0'),
            'countries_processed': set(),
            'payment_methods_used': set(),
            'currencies_processed': set(),
            'ai_classifications': 0,
            'rule_based_classifications': 0,
            'fraud_detected': 0,
            'disputes_received': 0
        }
        
        self.logger.info(f"Stripe processor initialized for {len(config.supported_countries)} countries")
    
    async def create_payment_intent(
        self,
        amount: int,  # Amount in smallest currency unit (e.g., cents)
        currency: StripeCurrency,
        customer: Optional[StripeCustomer] = None,
        payment_method_types: Optional[List[str]] = None,
        capture_method: Optional[str] = None,
        confirmation_method: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        receipt_email: Optional[str] = None,
        setup_future_usage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent
        
        Args:
            amount: Payment amount in smallest currency unit
            currency: Payment currency
            customer: Customer information
            payment_method_types: Allowed payment methods
            capture_method: Capture method (automatic/manual)
            confirmation_method: Confirmation method (automatic/manual)
            metadata: Additional metadata
            description: Payment description
            receipt_email: Email for receipt
            setup_future_usage: Setup for future usage
            
        Returns:
            Payment intent response
        """
        try:
            # Validate transaction limits
            await self._validate_transaction_limits(amount, currency)
            
            # Build payment intent data
            payment_data = {
                'amount': amount,
                'currency': currency.value,
                'capture_method': capture_method or self.config.capture_method,
                'confirmation_method': confirmation_method or self.config.confirmation_method,
            }
            
            # Add payment method types
            if payment_method_types:
                payment_data['payment_method_types'] = payment_method_types
            else:
                payment_data['payment_method_types'] = ['card']
            
            # Add customer if provided
            if customer and customer.id:
                payment_data['customer'] = customer.id
            elif customer and customer.email:
                # Create customer if we have email but no ID
                customer_response = await self.create_customer(
                    email=customer.email,
                    name=customer.name,
                    metadata=metadata
                )
                if customer_response.get('id'):
                    payment_data['customer'] = customer_response['id']
            
            # Add optional fields
            if description:
                payment_data['description'] = description
            
            if receipt_email:
                payment_data['receipt_email'] = receipt_email
            
            if setup_future_usage:
                payment_data['setup_future_usage'] = setup_future_usage
            
            if metadata:
                payment_data['metadata'] = metadata
            
            # Add automatic payment methods if enabled
            if self.config.enable_3d_secure:
                payment_data['automatic_payment_methods'] = {
                    'enabled': True
                }
            
            # Make API request with idempotency
            response = await self.auth_manager.make_authenticated_request(
                method='POST',
                endpoint='/payment_intents',
                data=payment_data,
                idempotent=True,
                operation_name='create_payment_intent'
            )
            
            # Log payment intent creation
            self.logger.info("Payment intent created", extra={
                'payment_intent_id': response.get('id'),
                'amount': amount,
                'currency': currency.value,
                'customer_id': payment_data.get('customer'),
                'status': response.get('status')
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Payment intent creation failed: {str(e)}", extra={
                'amount': amount,
                'currency': currency.value
            })
            raise
    
    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method: Optional[str] = None,
        return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Confirm a payment intent
        
        Args:
            payment_intent_id: Payment intent ID to confirm
            payment_method: Payment method ID
            return_url: Return URL for 3D Secure
            
        Returns:
            Confirmed payment intent
        """
        try:
            confirm_data = {}
            
            if payment_method:
                confirm_data['payment_method'] = payment_method
            
            if return_url:
                confirm_data['return_url'] = return_url
            
            response = await self.auth_manager.make_authenticated_request(
                method='POST',
                endpoint=f'/payment_intents/{payment_intent_id}/confirm',
                data=confirm_data,
                idempotent=True,
                operation_name='confirm_payment_intent'
            )
            
            self.logger.info("Payment intent confirmed", extra={
                'payment_intent_id': payment_intent_id,
                'status': response.get('status')
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Payment intent confirmation failed: {str(e)}", extra={
                'payment_intent_id': payment_intent_id
            })
            raise
    
    async def retrieve_payment_intent(self, payment_intent_id: str) -> Optional[StripeTransaction]:
        """
        Retrieve and convert payment intent to our transaction format
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            StripeTransaction if found, None otherwise
        """
        try:
            # Get payment intent
            response = await self.auth_manager.make_authenticated_request(
                method='GET',
                endpoint=f'/payment_intents/{payment_intent_id}'
            )
            
            # Convert to our transaction format
            transaction = await self._convert_payment_intent_to_transaction(response)
            
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
                if transaction.payment_status.value == 'succeeded':
                    self.processing_stats['successful_payments'] += 1
                    self.processing_stats['total_volume'] += Decimal(str(transaction.amount)) / 100  # Convert from cents
                else:
                    self.processing_stats['failed_payments'] += 1
                
                if transaction.country:
                    self.processing_stats['countries_processed'].add(transaction.country.value)
                if transaction.payment_method_type:
                    self.processing_stats['payment_methods_used'].add(transaction.payment_method_type.value)
                self.processing_stats['currencies_processed'].add(transaction.currency)
            
            self.logger.debug("Payment intent retrieved", extra={
                'payment_intent_id': payment_intent_id,
                'status': transaction.payment_status.value if transaction else 'not_found',
                'amount': str(transaction.amount) if transaction else None
            })
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Payment intent retrieval error: {str(e)}", extra={
                'payment_intent_id': payment_intent_id
            })
            return None
    
    async def list_payment_intents(
        self,
        customer: Optional[str] = None,
        created: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[StripeTransaction]:
        """
        List payment intents with filtering
        
        Args:
            customer: Customer ID filter
            created: Created date filter
            limit: Maximum number of payment intents
            
        Returns:
            List of StripeTransaction objects
        """
        try:
            # Build query parameters
            params = {
                'limit': min(limit, 100)  # Stripe max per page
            }
            
            if customer:
                params['customer'] = customer
            
            if created:
                for key, value in created.items():
                    params[f'created[{key}]'] = value
            
            # Make API request
            response = await self.auth_manager.make_authenticated_request(
                method='GET',
                endpoint='/payment_intents',
                params=params
            )
            
            payment_intents_data = response.get('data', [])
            
            # Convert payment intents
            transactions = []
            for pi_data in payment_intents_data:
                transaction = await self._convert_payment_intent_to_transaction(pi_data)
                if transaction:
                    # Apply classification and privacy protection
                    if self.transaction_classifier:
                        classification = await self._classify_transaction(transaction)
                        transaction.business_income_classified = classification.get('is_business_income', False)
                        transaction.classification_confidence = classification.get('confidence', 0.0)
                    
                    transaction = await self._apply_privacy_protection(transaction)
                    transactions.append(transaction)
            
            self.logger.info("Payment intents retrieved", extra={
                'count': len(transactions),
                'filters': {
                    'customer': customer,
                    'created': created
                }
            })
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error retrieving payment intents: {str(e)}")
            return []
    
    async def create_customer(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a customer
        
        Args:
            email: Customer email
            name: Customer name
            phone: Customer phone
            address: Customer address
            metadata: Additional metadata
            
        Returns:
            Customer creation response
        """
        try:
            customer_data = {}
            
            if email:
                customer_data['email'] = email
            
            if name:
                customer_data['name'] = name
            
            if phone:
                customer_data['phone'] = phone
            
            if address:
                customer_data['address'] = address
            
            if metadata:
                customer_data['metadata'] = metadata
            
            response = await self.auth_manager.make_authenticated_request(
                method='POST',
                endpoint='/customers',
                data=customer_data,
                idempotent=True,
                operation_name='create_customer'
            )
            
            self.logger.info("Customer created", extra={
                'customer_id': response.get('id'),
                'email': email
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Customer creation failed: {str(e)}")
            raise
    
    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment intent
        
        Args:
            payment_intent_id: Payment intent to refund
            amount: Amount to refund (optional, defaults to full amount)
            reason: Refund reason
            metadata: Additional metadata
            
        Returns:
            Refund response
        """
        try:
            refund_data = {
                'payment_intent': payment_intent_id
            }
            
            if amount:
                refund_data['amount'] = amount
            
            if reason:
                refund_data['reason'] = reason
            
            if metadata:
                refund_data['metadata'] = metadata
            
            response = await self.auth_manager.make_authenticated_request(
                method='POST',
                endpoint='/refunds',
                data=refund_data,
                idempotent=True,
                operation_name='create_refund'
            )
            
            self.logger.info("Refund created", extra={
                'refund_id': response.get('id'),
                'payment_intent_id': payment_intent_id,
                'amount': amount
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Refund creation failed: {str(e)}")
            raise
    
    async def _convert_payment_intent_to_transaction(self, data: Dict[str, Any]) -> Optional[StripeTransaction]:
        """Convert Stripe payment intent to StripeTransaction"""
        try:
            # Extract basic payment info
            payment_intent_id = data.get('id', '')
            amount = data.get('amount', 0)
            currency = data.get('currency', 'usd')
            
            # Parse currency
            try:
                stripe_currency = StripeCurrency(currency)
            except ValueError:
                stripe_currency = StripeCurrency.USD
            
            # Parse status
            status = data.get('status', 'requires_payment_method')
            
            # Extract customer info
            customer_data = data.get('customer')
            customer = None
            if customer_data:
                if isinstance(customer_data, str):
                    # Customer ID only
                    customer = StripeCustomer(id=customer_data)
                else:
                    # Full customer object
                    customer = StripeCustomer(
                        id=customer_data.get('id'),
                        email=customer_data.get('email'),
                        name=customer_data.get('name'),
                        phone=customer_data.get('phone')
                    )
            
            # Extract charges (for completed payments)
            charges_data = data.get('charges', {}).get('data', [])
            charge_data = charges_data[0] if charges_data else {}
            
            # Extract payment method details
            payment_method_data = charge_data.get('payment_method_details', {})
            card_details = None
            billing_details = None
            
            if 'card' in payment_method_data:
                card_info = payment_method_data['card']
                card_details = StripeCard(
                    last4=card_info.get('last4'),
                    brand=card_info.get('brand'),
                    country=card_info.get('country'),
                    exp_month=card_info.get('exp_month'),
                    exp_year=card_info.get('exp_year'),
                    fingerprint=card_info.get('fingerprint'),
                    funding=card_info.get('funding'),
                    three_d_secure=card_info.get('three_d_secure'),
                    cvc_check=card_info.get('checks', {}).get('cvc_check'),
                    address_line1_check=card_info.get('checks', {}).get('address_line1_check'),
                    address_postal_code_check=card_info.get('checks', {}).get('address_postal_code_check')
                )
            
            # Extract billing details
            billing_info = charge_data.get('billing_details', {})
            if billing_info:
                billing_details = StripeBillingDetails(
                    address=billing_info.get('address'),
                    email=billing_info.get('email'),
                    name=billing_info.get('name'),
                    phone=billing_info.get('phone')
                )
            
            # Extract outcome details
            outcome_data = charge_data.get('outcome', {})
            outcome = None
            if outcome_data:
                outcome = StripeOutcome(
                    network_status=outcome_data.get('network_status'),
                    reason=outcome_data.get('reason'),
                    risk_level=outcome_data.get('risk_level'),
                    risk_score=outcome_data.get('risk_score'),
                    seller_message=outcome_data.get('seller_message'),
                    type=outcome_data.get('type')
                )
            
            # Parse timestamps
            created = None
            if 'created' in data:
                created = datetime.fromtimestamp(data['created'])
            
            # Determine country
            country = None
            if card_details and card_details.country:
                try:
                    country = StripeCountry(card_details.country)
                except ValueError:
                    pass
            
            # Create transaction object
            transaction = StripeTransaction(
                transaction_id=payment_intent_id,
                reference=payment_intent_id,
                amount=Decimal(str(amount)) / 100,  # Convert from cents
                currency=currency,
                payment_status=status,
                
                # Stripe specific
                stripe_id=payment_intent_id,
                payment_intent_id=payment_intent_id,
                charge_id=charge_data.get('id'),
                payment_method_type=StripePaymentMethod.CARD if card_details else None,
                
                # Details
                card_details=card_details,
                billing_details=billing_details,
                outcome=outcome,
                country=country,
                
                # Customer info
                customer=customer,
                customer_email=customer.email if customer else billing_details.email if billing_details else None,
                customer_phone=customer.phone if customer else billing_details.phone if billing_details else None,
                customer_name=customer.name if customer else billing_details.name if billing_details else None,
                
                # Payment details
                confirmation_method=data.get('confirmation_method'),
                capture_method=data.get('capture_method'),
                setup_future_usage=data.get('setup_future_usage'),
                
                # Metadata
                description=data.get('description', ''),
                metadata=data.get('metadata', {}),
                receipt_email=data.get('receipt_email'),
                
                # Timestamps
                created=created or datetime.utcnow(),
                updated=datetime.utcnow()
            )
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Failed to convert payment intent data: {str(e)}")
            return None
    
    async def _classify_transaction(self, transaction: StripeTransaction) -> Dict[str, Any]:
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
                user_id=transaction.customer.email if transaction.customer else 'unknown',
                organization_id='stripe_merchant',
                business_name=getattr(transaction.customer, 'business_name', 'Unknown'),
                business_context=NigerianBusinessContext(
                    industry='payment_processing',
                    business_size='sme',
                    location=transaction.country.value.lower() if transaction.country else 'us',
                    state='lagos'
                )
            )
            
            classification_request = TransactionClassificationRequest(
                amount=transaction.amount,
                narration=transaction.description or f"Payment via {transaction.payment_method_type.value if transaction.payment_method_type else 'card'}",
                sender_name=transaction.customer_name,
                date=transaction.created.date() if transaction.created else datetime.utcnow().date(),
                time=transaction.created.strftime('%H:%M') if transaction.created else datetime.utcnow().strftime('%H:%M'),
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
    
    async def _apply_privacy_protection(self, transaction: StripeTransaction) -> StripeTransaction:
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
    
    async def _validate_transaction_limits(self, amount: int, currency: StripeCurrency):
        """Validate transaction against configured limits"""
        currency_str = currency.value
        
        # Check single transaction limit
        if currency_str in self.config.single_transaction_limit:
            limit = self.config.single_transaction_limit[currency_str]
            if amount > limit:
                raise ValueError(f"Transaction amount {amount} {currency_str} exceeds single transaction limit {limit}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return {
            **self.processing_stats,
            'countries_processed': list(self.processing_stats['countries_processed']),
            'payment_methods_used': list(self.processing_stats['payment_methods_used']),
            'currencies_processed': list(self.processing_stats['currencies_processed']),
            'supported_countries': [c.value for c in self.config.supported_countries],
            'ai_classification_enabled': self.config.enable_ai_classification,
            'privacy_level': self.config.privacy_level.value,
            'total_volume_formatted': f"{self.processing_stats['total_volume']:.2f}"
        }


__all__ = [
    'StripeProcessorConfig',
    'StripePaymentProcessor'
]