"""
Stripe Payment Processor Connector
=================================

Main connector for Stripe integration with comprehensive global
payment processing capabilities.

Features:
- NDPR-compliant data collection with configurable privacy levels
- AI-based Nigerian business transaction classification
- Global payment processing across 40+ countries
- Advanced card payment processing with 3D Secure support
- Real-time webhook processing and validation
- Universal Transaction Processor integration
- Comprehensive error handling and retry logic
- Multi-currency support with automatic conversion
- Advanced fraud detection and dispute management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal

from .models import (
    StripeTransaction, StripeCustomer, StripeWebhookEvent,
    StripePaymentMethod, StripeCurrency, StripeCountry,
    STRIPE_COUNTRY_CURRENCIES, STRIPE_PAYMENT_METHODS_BY_COUNTRY
)
from .auth import StripeAuthManager, StripeCredentials
from .payment_processor import StripePaymentProcessor, StripeProcessorConfig
from .webhook_handler import StripeWebhookHandler, StripeWebhookConfig
from ....connector_framework.base_payment_connector import BasePaymentConnector
from ....connector_framework.classification_engine.nigerian_classifier import (
    NigerianTransactionClassifier, PrivacyLevel
)
from ....connector_framework.classification_engine.privacy_protection import APIPrivacyProtection
from ...banking.open_banking.compliance.consent_manager import ConsentManager


@dataclass
class StripeConfig:
    """
    Complete configuration for Stripe connector integration
    """
    # Authentication
    secret_key: str
    publishable_key: str
    webhook_secret: Optional[str] = None
    environment: str = "test"  # test or live
    
    # Global settings
    default_country: StripeCountry = StripeCountry.UNITED_STATES
    supported_countries: List[StripeCountry] = None
    
    # Privacy and compliance
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    enable_ai_classification: bool = True
    openai_api_key: Optional[str] = None
    enable_ndpr_compliance: bool = True
    
    # Processing options
    enable_webhooks: bool = True
    validate_webhook_signatures: bool = True
    enable_auto_retry: bool = True
    max_retry_attempts: int = 3
    
    # Payment settings
    capture_method: str = "automatic"  # automatic or manual
    confirmation_method: str = "automatic"  # automatic or manual
    
    # Business rules
    auto_invoice_generation: bool = True
    classification_confidence_threshold: float = 0.7
    minimum_amount_for_classification: int = 100  # $1.00 in cents
    
    # Currency and fees
    settlement_currency: StripeCurrency = StripeCurrency.USD
    enable_multi_currency: bool = True
    currency_conversion_enabled: bool = True
    
    # Security features
    enable_3d_secure: bool = True
    enable_fraud_detection: bool = True
    enable_radar_rules: bool = True
    
    # Feature flags
    enable_setup_intents: bool = True
    enable_payment_methods: bool = True
    enable_customers: bool = True
    enable_invoicing: bool = True
    enable_subscriptions: bool = False
    
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
                StripeCountry.JAPAN,
                StripeCountry.SOUTH_AFRICA  # For African customers
            ]


class StripeConnector(BasePaymentConnector):
    """
    Main Stripe integration connector with global support
    
    Specialized for global payment processing:
    - 40+ countries supported worldwide
    - Advanced card processing with 3D Secure
    - Multi-currency processing with automatic conversion
    - AI-powered Nigerian business classification
    - NDPR compliance with privacy protection
    - Real-time webhook processing
    - Universal Transaction Processor integration
    - Advanced fraud detection and dispute management
    """
    
    def __init__(self, config: StripeConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize authentication
        credentials = StripeCredentials(
            secret_key=config.secret_key,
            publishable_key=config.publishable_key,
            webhook_secret=config.webhook_secret,
            environment=config.environment
        )
        
        self.auth_manager = StripeAuthManager(credentials)
        
        # Initialize payment processor
        processor_config = StripeProcessorConfig(
            secret_key=config.secret_key,
            publishable_key=config.publishable_key,
            webhook_secret=config.webhook_secret,
            environment=config.environment,
            enable_ai_classification=config.enable_ai_classification,
            openai_api_key=config.openai_api_key,
            privacy_level=config.privacy_level,
            default_country=config.default_country,
            supported_countries=config.supported_countries,
            capture_method=config.capture_method,
            confirmation_method=config.confirmation_method,
            settlement_currency=config.settlement_currency,
            enable_3d_secure=config.enable_3d_secure
        )
        
        self.payment_processor = StripePaymentProcessor(processor_config)
        
        # Initialize transaction classifier if enabled
        self.transaction_classifier = None
        if config.enable_ai_classification:
            self.transaction_classifier = NigerianTransactionClassifier(
                api_key=config.openai_api_key
            )
        
        # Initialize webhook handler if enabled
        self.webhook_handler = None
        if config.enable_webhooks:
            webhook_config = StripeWebhookConfig(
                webhook_secret=config.webhook_secret,
                validate_signatures=config.validate_webhook_signatures,
                enable_auto_retry=config.enable_auto_retry,
                max_retry_attempts=config.max_retry_attempts,
                enable_ai_classification=config.enable_ai_classification,
                classification_threshold=config.classification_confidence_threshold
            )
            
            self.webhook_handler = StripeWebhookHandler(
                webhook_config,
                self.auth_manager,
                self.payment_processor,
                self.transaction_classifier
            )
        
        # Initialize privacy and compliance components
        self.privacy_protection = APIPrivacyProtection()
        self.consent_manager = ConsentManager()
        
        # Connection state
        self._connection_status = "disconnected"
        self._last_health_check = None
        self._health_check_interval = timedelta(minutes=5)
        
        # Processing state
        self.active_payment_intents = {}
        self.processed_webhooks = set()
        
        # Statistics
        self.integration_stats = {
            'total_payment_intents_created': 0,
            'successful_payments': 0,
            'failed_payments': 0,
            'total_volume_processed': Decimal('0'),
            'countries_active': set(),
            'payment_methods_used': set(),
            'currencies_processed': set(),
            'ai_classifications_performed': 0,
            'webhooks_processed': 0,
            'fraud_events_detected': 0,
            'disputes_received': 0,
            'last_payment_time': None
        }
        
        self.logger.info("Stripe connector initialized", extra={
            'environment': config.environment,
            'supported_countries': len(config.supported_countries),
            'privacy_level': config.privacy_level.value,
            'webhooks_enabled': config.enable_webhooks,
            'ai_classification_enabled': config.enable_ai_classification,
            '3d_secure_enabled': config.enable_3d_secure
        })
    
    async def connect(self) -> bool:
        """
        Establish connection to Stripe API
        """
        try:
            self.logger.info("Connecting to Stripe API...")
            
            # Verify credentials
            credentials_valid = await self.auth_manager.verify_credentials()
            if not credentials_valid:
                raise Exception("Invalid Stripe credentials")
            
            # Perform health check
            health_status = await self.health_check()
            if not health_status['healthy']:
                raise Exception(f"Health check failed: {health_status.get('error')}")
            
            self._connection_status = "connected"
            self.logger.info("Successfully connected to Stripe API", extra={
                'environment': self.config.environment,
                'supported_countries': len(self.config.supported_countries)
            })
            
            return True
            
        except Exception as e:
            self._connection_status = "failed"
            self.logger.error("Failed to connect to Stripe API", extra={
                'error': str(e),
                'environment': self.config.environment
            })
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Stripe API
        """
        try:
            # Close HTTP sessions
            await self.auth_manager.close_session()
            
            self._connection_status = "disconnected"
            self.logger.info("Disconnected from Stripe API")
            
            return True
            
        except Exception as e:
            self.logger.error("Error during disconnect", extra={'error': str(e)})
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of Stripe integration
        """
        health_start = datetime.utcnow()
        
        try:
            # Check authentication
            auth_healthy = False
            auth_error = None
            try:
                auth_healthy = await self.auth_manager.verify_credentials()
            except Exception as e:
                auth_error = str(e)
            
            # Check account access
            account_healthy = False
            account_response_time = None
            account_error = None
            
            if auth_healthy:
                try:
                    account_start = datetime.utcnow()
                    account_info = await self.auth_manager.get_account_info()
                    account_response_time = (datetime.utcnow() - account_start).total_seconds()
                    account_healthy = account_info is not None
                except Exception as e:
                    account_error = str(e)
            
            # Check webhook handler if enabled
            webhook_healthy = True
            webhook_error = None
            if self.config.enable_webhooks and self.webhook_handler:
                try:
                    webhook_stats = self.webhook_handler.get_webhook_statistics()
                    webhook_healthy = True
                except Exception as e:
                    webhook_healthy = False
                    webhook_error = str(e)
            
            # Overall health assessment
            overall_healthy = auth_healthy and account_healthy and webhook_healthy
            
            # Update last health check
            self._last_health_check = datetime.utcnow()
            
            health_result = {
                'healthy': overall_healthy,
                'timestamp': self._last_health_check.isoformat(),
                'response_time': (datetime.utcnow() - health_start).total_seconds(),
                'components': {
                    'authentication': {
                        'healthy': auth_healthy,
                        'error': auth_error
                    },
                    'account_access': {
                        'healthy': account_healthy,
                        'response_time': account_response_time,
                        'error': account_error
                    },
                    'webhook_handler': {
                        'healthy': webhook_healthy,
                        'enabled': self.config.enable_webhooks,
                        'error': webhook_error
                    }
                },
                'configuration': {
                    'environment': self.config.environment,
                    'supported_countries': [c.value for c in self.config.supported_countries],
                    'privacy_level': self.config.privacy_level.value,
                    'multi_currency_enabled': self.config.enable_multi_currency,
                    'ai_classification_enabled': self.config.enable_ai_classification,
                    '3d_secure_enabled': self.config.enable_3d_secure,
                    'fraud_detection_enabled': self.config.enable_fraud_detection
                }
            }
            
            if overall_healthy:
                self.logger.debug("Stripe health check passed", extra=health_result)
            else:
                self.logger.warning("Stripe health check failed", extra=health_result)
            
            return health_result
            
        except Exception as e:
            error_result = {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'response_time': (datetime.utcnow() - health_start).total_seconds()
            }
            
            self.logger.error("Health check error", extra=error_result)
            return error_result
    
    async def create_payment_intent(
        self,
        amount: int,  # Amount in smallest currency unit (e.g., cents)
        currency: StripeCurrency,
        customer_email: Optional[str] = None,
        customer_name: Optional[str] = None,
        payment_method_types: Optional[List[str]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        capture_method: Optional[str] = None,
        confirmation_method: Optional[str] = None,
        setup_future_usage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            # Create customer if email provided
            customer = None
            if customer_email:
                customer = StripeCustomer(
                    email=customer_email,
                    name=customer_name,
                    country=self.config.default_country
                )
            
            # Create payment intent
            payment_intent_response = await self.payment_processor.create_payment_intent(
                amount=amount,
                currency=currency,
                customer=customer,
                payment_method_types=payment_method_types,
                capture_method=capture_method,
                confirmation_method=confirmation_method,
                metadata=metadata,
                description=description,
                receipt_email=customer_email,
                setup_future_usage=setup_future_usage
            )
            
            # Track payment intent
            if payment_intent_response.get('id'):
                payment_intent_id = payment_intent_response['id']
                self.active_payment_intents[payment_intent_id] = {
                    'amount': amount,
                    'currency': currency.value,
                    'customer_email': customer_email,
                    'created_at': datetime.utcnow(),
                    'status': payment_intent_response.get('status')
                }
                
                # Update statistics
                self.integration_stats['total_payment_intents_created'] += 1
                self.integration_stats['countries_active'].add(self.config.default_country.value)
                self.integration_stats['currencies_processed'].add(currency.value)
                self.integration_stats['last_payment_time'] = datetime.utcnow()
            
            return payment_intent_response
            
        except Exception as e:
            self.logger.error(f"Payment intent creation failed: {str(e)}", extra={
                'amount': amount,
                'currency': currency.value,
                'customer_email': customer_email
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
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            # Confirm payment intent
            confirmation_response = await self.payment_processor.confirm_payment_intent(
                payment_intent_id=payment_intent_id,
                payment_method=payment_method,
                return_url=return_url
            )
            
            # Update tracking
            if payment_intent_id in self.active_payment_intents:
                self.active_payment_intents[payment_intent_id]['status'] = confirmation_response.get('status')
                self.active_payment_intents[payment_intent_id]['confirmed_at'] = datetime.utcnow()
            
            return confirmation_response
            
        except Exception as e:
            self.logger.error(f"Payment intent confirmation failed: {str(e)}", extra={
                'payment_intent_id': payment_intent_id
            })
            raise
    
    async def retrieve_payment_intent(self, payment_intent_id: str) -> Optional[StripeTransaction]:
        """
        Retrieve payment intent and convert to transaction format
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            # Retrieve payment intent
            transaction = await self.payment_processor.retrieve_payment_intent(payment_intent_id)
            
            # Update statistics
            if transaction:
                self.integration_stats['last_payment_time'] = datetime.utcnow()
                
                if transaction.payment_status.value == 'succeeded':
                    self.integration_stats['successful_payments'] += 1
                    self.integration_stats['total_volume_processed'] += transaction.amount
                else:
                    self.integration_stats['failed_payments'] += 1
                
                if transaction.country:
                    self.integration_stats['countries_active'].add(transaction.country.value)
                if transaction.payment_method_type:
                    self.integration_stats['payment_methods_used'].add(transaction.payment_method_type.value)
                self.integration_stats['currencies_processed'].add(transaction.currency)
                
                # Track fraud events
                if transaction.outcome and transaction.outcome.risk_level == 'highest':
                    self.integration_stats['fraud_events_detected'] += 1
                
                # Track disputes
                if transaction.disputed:
                    self.integration_stats['disputes_received'] += 1
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Payment intent retrieval failed: {str(e)}", extra={
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
        List payment intents with filtering and classification
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            # Get payment intents from processor
            transactions = await self.payment_processor.list_payment_intents(
                customer=customer,
                created=created,
                limit=limit
            )
            
            # Update statistics
            for transaction in transactions:
                if transaction.country:
                    self.integration_stats['countries_active'].add(transaction.country.value)
                if transaction.payment_method_type:
                    self.integration_stats['payment_methods_used'].add(transaction.payment_method_type.value)
                self.integration_stats['currencies_processed'].add(transaction.currency)
            
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
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            return await self.payment_processor.create_customer(
                email=email,
                name=name,
                phone=phone,
                address=address,
                metadata=metadata
            )
            
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
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            return await self.payment_processor.create_refund(
                payment_intent_id=payment_intent_id,
                amount=amount,
                reason=reason,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Refund creation failed: {str(e)}")
            raise
    
    async def get_supported_countries(self) -> List[Dict[str, Any]]:
        """
        Get list of countries supported by Stripe
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            country_specs = await self.auth_manager.get_country_specs()
            
            # Enhance with our configuration
            enhanced_countries = []
            for country_spec in country_specs:
                country_code = country_spec.get('id', '')
                
                # Check if we support this country
                try:
                    stripe_country = StripeCountry(country_code)
                    supported = stripe_country in self.config.supported_countries
                except ValueError:
                    supported = False
                
                # Get payment methods for this country
                payment_methods = STRIPE_PAYMENT_METHODS_BY_COUNTRY.get(
                    StripeCountry(country_code), []
                ) if country_code in [c.value for c in StripeCountry] else []
                
                enhanced_country = {
                    **country_spec,
                    'supported_by_taxpoynt': supported,
                    'default_currency': STRIPE_COUNTRY_CURRENCIES.get(
                        StripeCountry(country_code)
                    ).value if country_code in [c.value for c in STRIPE_COUNTRY_CURRENCIES.keys()] else None,
                    'available_payment_methods': [pm.value for pm in payment_methods]
                }
                
                enhanced_countries.append(enhanced_country)
            
            return enhanced_countries
            
        except Exception as e:
            self.logger.error(f"Error getting supported countries: {str(e)}")
            return []
    
    async def get_exchange_rates(
        self,
        currency: Optional[StripeCurrency] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get current exchange rates
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            return await self.auth_manager.get_exchange_rates(
                currency.value if currency else None
            )
            
        except Exception as e:
            self.logger.error(f"Error getting exchange rates: {str(e)}")
            return None
    
    async def process_webhook(self, payload: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Process incoming webhook with comprehensive validation and processing
        """
        if not self.webhook_handler:
            return {
                'status': 'error',
                'message': 'Webhooks not enabled'
            }
        
        try:
            result = await self.webhook_handler.process_webhook(payload, headers)
            
            # Update statistics
            self.integration_stats['webhooks_processed'] += 1
            
            self.logger.info("Webhook processed", extra={
                'status': result.get('status'),
                'event_id': result.get('event_id'),
                'processing_time': result.get('processing_time')
            })
            
            return result
            
        except Exception as e:
            self.logger.error("Webhook processing error", extra={
                'error': str(e),
                'payload_preview': payload[:100] if payload else None
            })
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get list of supported features for this connector
        """
        return {
            'global_processing': True,
            'card_payments': True,
            'alternative_payments': True,
            '3d_secure': self.config.enable_3d_secure,
            'fraud_detection': self.config.enable_fraud_detection,
            'dispute_management': True,
            'real_time_webhooks': self.config.enable_webhooks,
            'ai_classification': self.config.enable_ai_classification,
            'privacy_protection': self.config.enable_ndpr_compliance,
            'multi_currency': self.config.enable_multi_currency,
            'currency_conversion': self.config.currency_conversion_enabled,
            'auto_invoice_generation': self.config.auto_invoice_generation,
            'setup_intents': self.config.enable_setup_intents,
            'payment_methods': self.config.enable_payment_methods,
            'customer_management': self.config.enable_customers,
            'invoicing': self.config.enable_invoicing,
            'subscriptions': self.config.enable_subscriptions,
            'marketplace_payments': True,
            'connect_platforms': True,
            'refunds': True,
            'partial_refunds': True
        }
    
    async def get_integration_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive integration statistics and metrics
        """
        try:
            base_stats = {
                'connector': 'stripe',
                'version': '1.0.0',
                'environment': self.config.environment,
                'connection_status': self._connection_status,
                'last_health_check': self._last_health_check.isoformat() if self._last_health_check else None,
                **self.integration_stats
            }
            
            # Convert sets to lists for JSON serialization
            base_stats['countries_active'] = list(self.integration_stats['countries_active'])
            base_stats['payment_methods_used'] = list(self.integration_stats['payment_methods_used'])
            base_stats['currencies_processed'] = list(self.integration_stats['currencies_processed'])
            
            # Add processor statistics
            if self._connection_status == "connected":
                processor_stats = self.payment_processor.get_processing_statistics()
                base_stats['processor_statistics'] = processor_stats
            
            # Add webhook statistics
            if self.webhook_handler:
                webhook_stats = self.webhook_handler.get_webhook_statistics()
                base_stats['webhook_statistics'] = webhook_stats
            
            # Add feature support
            base_stats['supported_features'] = self.get_supported_features()
            
            # Add configuration summary
            base_stats['configuration_summary'] = {
                'supported_countries': [c.value for c in self.config.supported_countries],
                'default_country': self.config.default_country.value,
                'settlement_currency': self.config.settlement_currency.value,
                'privacy_level': self.config.privacy_level.value,
                'classification_threshold': self.config.classification_confidence_threshold,
                'capture_method': self.config.capture_method,
                'confirmation_method': self.config.confirmation_method
            }
            
            return base_stats
            
        except Exception as e:
            self.logger.error("Error getting integration statistics", extra={'error': str(e)})
            return {
                'connector': 'stripe',
                'error': str(e),
                'connection_status': self._connection_status
            }


# Export for external use
__all__ = [
    'StripeConfig',
    'StripeConnector'
]