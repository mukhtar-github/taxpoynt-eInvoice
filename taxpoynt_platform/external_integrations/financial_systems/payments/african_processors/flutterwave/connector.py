"""
Flutterwave Payment Processor Connector
======================================

Main connector for Flutterwave integration with comprehensive Pan-African
payment processing capabilities.

Features:
- NDPR-compliant data collection with configurable privacy levels
- AI-based Nigerian business transaction classification
- Multi-country African payment processing (34+ countries)
- Mobile money, card, and bank transfer support
- Real-time webhook processing and validation
- Universal Transaction Processor integration
- Comprehensive error handling and retry logic
- Multi-currency support with automatic conversion
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decimal import Decimal

from .models import (
    FlutterwaveTransaction, FlutterwaveCustomer, FlutterwaveWebhookEvent,
    FlutterwavePaymentMethod, FlutterwaveCurrency, FlutterwaveCountry,
    AFRICAN_COUNTRY_CURRENCIES
)
from .auth import FlutterwaveAuthManager, FlutterwaveCredentials
from .payment_processor import FlutterwavePaymentProcessor, FlutterwaveProcessorConfig
from .webhook_handler import FlutterwaveWebhookHandler, FlutterwaveWebhookConfig
from ....connector_framework.base_payment_connector import BasePaymentConnector
from ....connector_framework.classification_engine.nigerian_classifier import (
    NigerianTransactionClassifier, PrivacyLevel
)
from ....connector_framework.classification_engine.privacy_protection import APIPrivacyProtection
from ...banking.open_banking.compliance.consent_manager import ConsentManager


@dataclass
class FlutterwaveConfig:
    """
    Complete configuration for Flutterwave connector integration
    """
    # Authentication
    public_key: str
    secret_key: str
    webhook_secret: Optional[str] = None
    environment: str = "sandbox"  # sandbox or production
    
    # Multi-country settings
    default_country: FlutterwaveCountry = FlutterwaveCountry.NIGERIA
    supported_countries: List[FlutterwaveCountry] = None
    
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
    
    # Business rules
    auto_invoice_generation: bool = True
    classification_confidence_threshold: float = 0.7
    minimum_amount_for_classification: Decimal = Decimal('1000')  # ₦1,000
    
    # Currency and fees
    settlement_currency: FlutterwaveCurrency = FlutterwaveCurrency.NGN
    enable_multi_currency: bool = True
    currency_conversion_enabled: bool = True
    
    # Rate limiting
    rate_limit_per_minute: int = 120
    request_timeout: int = 30
    
    # Feature flags
    enable_mobile_money: bool = True
    enable_card_payments: bool = True
    enable_bank_transfers: bool = True
    enable_crypto_payments: bool = False
    
    def __post_init__(self):
        if self.supported_countries is None:
            self.supported_countries = [
                FlutterwaveCountry.NIGERIA,
                FlutterwaveCountry.GHANA,
                FlutterwaveCountry.KENYA,
                FlutterwaveCountry.UGANDA,
                FlutterwaveCountry.TANZANIA,
                FlutterwaveCountry.RWANDA,
                FlutterwaveCountry.ZAMBIA,
                FlutterwaveCountry.SOUTH_AFRICA
            ]


class FlutterwaveConnector(BasePaymentConnector):
    """
    Main Flutterwave integration connector with Pan-African support
    
    Specialized for African payment processing:
    - 34+ African countries supported
    - Mobile money integration for all major providers
    - Multi-currency processing with automatic conversion
    - AI-powered Nigerian business classification
    - NDPR compliance with privacy protection
    - Real-time webhook processing
    - Universal Transaction Processor integration
    """
    
    def __init__(self, config: FlutterwaveConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize authentication
        credentials = FlutterwaveCredentials(
            public_key=config.public_key,
            secret_key=config.secret_key,
            webhook_secret=config.webhook_secret,
            environment=config.environment
        )
        
        self.auth_manager = FlutterwaveAuthManager(credentials)
        
        # Initialize payment processor
        processor_config = FlutterwaveProcessorConfig(
            public_key=config.public_key,
            secret_key=config.secret_key,
            webhook_secret=config.webhook_secret,
            environment=config.environment,
            enable_ai_classification=config.enable_ai_classification,
            openai_api_key=config.openai_api_key,
            privacy_level=config.privacy_level,
            default_country=config.default_country,
            supported_countries=config.supported_countries,
            settlement_currency=config.settlement_currency
        )
        
        self.payment_processor = FlutterwavePaymentProcessor(processor_config)
        
        # Initialize transaction classifier if enabled
        self.transaction_classifier = None
        if config.enable_ai_classification:
            self.transaction_classifier = NigerianTransactionClassifier(
                api_key=config.openai_api_key
            )
        
        # Initialize webhook handler if enabled
        self.webhook_handler = None
        if config.enable_webhooks:
            webhook_config = FlutterwaveWebhookConfig(
                webhook_secret=config.webhook_secret,
                validate_signatures=config.validate_webhook_signatures,
                enable_auto_retry=config.enable_auto_retry,
                max_retry_attempts=config.max_retry_attempts,
                enable_ai_classification=config.enable_ai_classification,
                classification_threshold=config.classification_confidence_threshold
            )
            
            self.webhook_handler = FlutterwaveWebhookHandler(
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
        self.active_transactions = {}
        self.processed_webhooks = set()
        
        # Statistics
        self.integration_stats = {
            'total_transactions_processed': 0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'total_volume_processed': Decimal('0'),
            'countries_active': set(),
            'payment_methods_used': set(),
            'currencies_processed': set(),
            'ai_classifications_performed': 0,
            'webhooks_processed': 0,
            'last_transaction_time': None
        }
        
        self.logger.info("Flutterwave connector initialized", extra={
            'environment': config.environment,
            'supported_countries': len(config.supported_countries),
            'privacy_level': config.privacy_level.value,
            'webhooks_enabled': config.enable_webhooks,
            'ai_classification_enabled': config.enable_ai_classification
        })
    
    async def connect(self) -> bool:
        """
        Establish connection to Flutterwave API
        """
        try:
            self.logger.info("Connecting to Flutterwave API...")
            
            # Verify credentials
            credentials_valid = await self.auth_manager.verify_credentials()
            if not credentials_valid:
                raise Exception("Invalid Flutterwave credentials")
            
            # Perform health check
            health_status = await self.health_check()
            if not health_status['healthy']:
                raise Exception(f"Health check failed: {health_status.get('error')}")
            
            self._connection_status = "connected"
            self.logger.info("Successfully connected to Flutterwave API", extra={
                'environment': self.config.environment,
                'supported_countries': len(self.config.supported_countries)
            })
            
            return True
            
        except Exception as e:
            self._connection_status = "failed"
            self.logger.error("Failed to connect to Flutterwave API", extra={
                'error': str(e),
                'environment': self.config.environment
            })
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Flutterwave API
        """
        try:
            # Close HTTP sessions
            await self.auth_manager.close_session()
            
            self._connection_status = "disconnected"
            self.logger.info("Disconnected from Flutterwave API")
            
            return True
            
        except Exception as e:
            self.logger.error("Error during disconnect", extra={'error': str(e)})
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of Flutterwave integration
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
            
            # Check API connectivity
            api_healthy = False
            api_response_time = None
            api_error = None
            
            if auth_healthy:
                try:
                    api_start = datetime.utcnow()
                    countries = await self.auth_manager.get_supported_countries()
                    api_response_time = (datetime.utcnow() - api_start).total_seconds()
                    api_healthy = len(countries) > 0
                except Exception as e:
                    api_error = str(e)
            
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
            overall_healthy = auth_healthy and api_healthy and webhook_healthy
            
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
                    'api_connectivity': {
                        'healthy': api_healthy,
                        'response_time': api_response_time,
                        'error': api_error
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
                    'ai_classification_enabled': self.config.enable_ai_classification
                }
            }
            
            if overall_healthy:
                self.logger.debug("Flutterwave health check passed", extra=health_result)
            else:
                self.logger.warning("Flutterwave health check failed", extra=health_result)
            
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
    
    async def initiate_payment(
        self,
        amount: Decimal,
        currency: FlutterwaveCurrency,
        customer_email: str,
        reference: str,
        payment_method: FlutterwavePaymentMethod = FlutterwavePaymentMethod.CARD,
        country: Optional[FlutterwaveCountry] = None,
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate a payment transaction
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            # Create customer object
            customer = FlutterwaveCustomer(
                email=customer_email,
                country=country or self.config.default_country
            )
            
            # Initiate payment
            payment_response = await self.payment_processor.initiate_payment(
                amount=amount,
                currency=currency,
                customer=customer,
                payment_method=payment_method,
                reference=reference,
                callback_url=callback_url,
                country=country,
                metadata=metadata
            )
            
            # Track transaction
            if payment_response.get('status') == 'success':
                self.active_transactions[reference] = {
                    'amount': amount,
                    'currency': currency.value,
                    'country': (country or self.config.default_country).value,
                    'payment_method': payment_method.value,
                    'initiated_at': datetime.utcnow()
                }
                
                # Update statistics
                self.integration_stats['countries_active'].add(
                    (country or self.config.default_country).value
                )
                self.integration_stats['payment_methods_used'].add(payment_method.value)
                self.integration_stats['currencies_processed'].add(currency.value)
            
            return payment_response
            
        except Exception as e:
            self.logger.error(f"Payment initiation failed: {str(e)}", extra={
                'reference': reference,
                'amount': str(amount),
                'currency': currency.value
            })
            raise
    
    async def verify_payment(self, payment_reference: str) -> Optional[FlutterwaveTransaction]:
        """
        Verify payment status and get transaction details
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            # Find transaction by reference
            transactions = await self.payment_processor.get_transactions(
                limit=1
            )
            
            # Look for transaction with matching reference
            for transaction in transactions:
                if transaction.tx_ref == payment_reference or transaction.flw_ref == payment_reference:
                    # Update statistics
                    self.integration_stats['total_transactions_processed'] += 1
                    self.integration_stats['last_transaction_time'] = datetime.utcnow()
                    
                    if transaction.payment_status.value == 'successful':
                        self.integration_stats['successful_transactions'] += 1
                        self.integration_stats['total_volume_processed'] += transaction.amount
                    else:
                        self.integration_stats['failed_transactions'] += 1
                    
                    return transaction
            
            # If not found in recent transactions, try direct verification
            # This would require transaction ID which we don't have from reference
            self.logger.warning(f"Transaction not found for reference: {payment_reference}")
            return None
            
        except Exception as e:
            self.logger.error(f"Payment verification failed: {str(e)}", extra={
                'reference': payment_reference
            })
            return None
    
    async def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        country: Optional[FlutterwaveCountry] = None,
        currency: Optional[FlutterwaveCurrency] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[FlutterwaveTransaction]:
        """
        Get transactions with filtering and classification
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            # Get transactions from processor
            transactions = await self.payment_processor.get_transactions(
                start_date=start_date,
                end_date=end_date,
                status=status,
                currency=currency,
                country=country,
                limit=limit
            )
            
            # Update statistics
            for transaction in transactions:
                if transaction.country:
                    self.integration_stats['countries_active'].add(transaction.country.value)
                if transaction.payment_method:
                    self.integration_stats['payment_methods_used'].add(transaction.payment_method.value)
                self.integration_stats['currencies_processed'].add(transaction.currency)
            
            self.logger.info("Transactions retrieved", extra={
                'count': len(transactions),
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'filters': {
                    'country': country.value if country else None,
                    'currency': currency.value if currency else None,
                    'status': status
                }
            })
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error retrieving transactions: {str(e)}")
            return []
    
    async def get_supported_countries(self) -> List[Dict[str, Any]]:
        """
        Get list of countries supported by Flutterwave
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            countries = await self.auth_manager.get_supported_countries()
            
            # Enhance with our configuration
            enhanced_countries = []
            for country in countries:
                country_code = country.get('iso_code', '')
                
                # Check if we support this country
                try:
                    flw_country = FlutterwaveCountry(country_code)
                    supported = flw_country in self.config.supported_countries
                except ValueError:
                    supported = False
                
                enhanced_country = {
                    **country,
                    'supported_by_taxpoynt': supported,
                    'default_currency': AFRICAN_COUNTRY_CURRENCIES.get(
                        FlutterwaveCountry(country_code)
                    ).value if country_code in [c.value for c in AFRICAN_COUNTRY_CURRENCIES.keys()] else None
                }
                
                enhanced_countries.append(enhanced_country)
            
            return enhanced_countries
            
        except Exception as e:
            self.logger.error(f"Error getting supported countries: {str(e)}")
            return []
    
    async def get_banks(self, country: FlutterwaveCountry) -> List[Dict[str, Any]]:
        """
        Get banks for a specific country
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            return await self.payment_processor.get_banks(country)
            
        except Exception as e:
            self.logger.error(f"Error getting banks for {country}: {str(e)}")
            return []
    
    async def get_mobile_money_providers(self, country: FlutterwaveCountry) -> List[Dict[str, Any]]:
        """
        Get mobile money providers for a country
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            return await self.payment_processor.get_mobile_money_providers(country)
            
        except Exception as e:
            self.logger.error(f"Error getting mobile money providers for {country}: {str(e)}")
            return []
    
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
    
    async def get_exchange_rates(
        self,
        from_currency: FlutterwaveCurrency,
        to_currency: FlutterwaveCurrency,
        amount: Optional[Decimal] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get exchange rates between currencies
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            return await self.auth_manager.get_exchange_rates(
                from_currency.value,
                to_currency.value,
                float(amount) if amount else None
            )
            
        except Exception as e:
            self.logger.error(f"Error getting exchange rates: {str(e)}")
            return None
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get list of supported features for this connector
        """
        return {
            'multi_country_processing': True,
            'mobile_money_payments': self.config.enable_mobile_money,
            'card_payments': self.config.enable_card_payments,
            'bank_transfers': self.config.enable_bank_transfers,
            'crypto_payments': self.config.enable_crypto_payments,
            'real_time_webhooks': self.config.enable_webhooks,
            'ai_classification': self.config.enable_ai_classification,
            'privacy_protection': self.config.enable_ndpr_compliance,
            'multi_currency': self.config.enable_multi_currency,
            'currency_conversion': self.config.currency_conversion_enabled,
            'auto_invoice_generation': self.config.auto_invoice_generation,
            'batch_processing': True,
            'transaction_history': True,
            'settlement_tracking': True
        }
    
    async def get_integration_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive integration statistics and metrics
        """
        try:
            base_stats = {
                'connector': 'flutterwave',
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
                'classification_threshold': float(self.config.classification_confidence_threshold)
            }
            
            return base_stats
            
        except Exception as e:
            self.logger.error("Error getting integration statistics", extra={'error': str(e)})
            return {
                'connector': 'flutterwave',
                'error': str(e),
                'connection_status': self._connection_status
            }


# Export for external use
__all__ = [
    'FlutterwaveConfig',
    'FlutterwaveConnector'
]