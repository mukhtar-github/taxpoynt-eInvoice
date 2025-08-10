"""
PalmPay Payment Processor Connector
==================================

Main connector for PalmPay integration with comprehensive Nigerian inter-bank
transfer and mobile money processing capabilities.

Features:
- NDPR-compliant data collection with configurable privacy levels
- AI-based Nigerian business transaction classification
- Specialized inter-bank transfer processing
- Real-time webhook processing and validation
- Universal Transaction Processor integration
- Comprehensive error handling and retry logic
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .models import PalmPayTransaction, PalmPayCustomer
from .auth import PalmPayAuthManager, PalmPayCredentials
from .payment_processor import PalmPayPaymentProcessor, PalmPayConfig
from .webhook_handler import PalmPayWebhookHandler, PalmPayWebhookConfig
from taxpoynt_platform.external_integrations.connector_framework.base_payment_connector import BasePaymentConnector
from taxpoynt_platform.core_platform.monitoring.logging.service import LoggingService
from taxpoynt_platform.core_platform.data_management.privacy.models import PrivacyLevel


@dataclass
class PalmPayConnectorConfig:
    """
    Complete configuration for PalmPay connector integration
    """
    # Authentication
    api_key: str
    secret_key: str
    merchant_id: str
    environment: str = "sandbox"  # sandbox or production
    
    # Privacy and compliance
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    enable_ai_classification: bool = True
    enable_ndpr_compliance: bool = True
    
    # Processing options
    enable_webhooks: bool = True
    validate_webhook_signatures: bool = True
    enable_auto_retry: bool = True
    max_retry_attempts: int = 3
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    request_timeout: int = 30
    
    # Feature flags
    enable_inter_bank_transfers: bool = True
    enable_mobile_wallet: bool = True
    enable_qr_payments: bool = True
    enable_bill_payments: bool = True


class PalmPayConnector(BasePaymentConnector):
    """
    Main PalmPay integration connector
    
    Specialized for Nigerian inter-bank transfers and mobile money:
    - Inter-bank transfer processing (PalmPay's specialization)
    - Mobile wallet transactions
    - QR code payments
    - Bill payment services
    - AI-powered business classification
    - NDPR compliance with privacy protection
    """
    
    def __init__(self, config: PalmPayConnectorConfig):
        self.config = config
        self.logger = LoggingService().get_logger("palmpay_connector")
        
        # Initialize authentication
        credentials = PalmPayCredentials(
            api_key=config.api_key,
            secret_key=config.secret_key,
            merchant_id=config.merchant_id,
            environment=config.environment
        )
        
        self.auth_manager = PalmPayAuthManager(credentials)
        
        # Initialize payment processor
        processor_config = PalmPayConfig(
            api_key=config.api_key,
            secret_key=config.secret_key,
            merchant_id=config.merchant_id,
            environment=config.environment,
            privacy_level=config.privacy_level,
            enable_ai_classification=config.enable_ai_classification,
            rate_limit_per_minute=config.rate_limit_per_minute,
            request_timeout=config.request_timeout
        )
        
        self.payment_processor = PalmPayPaymentProcessor(processor_config)
        
        # Initialize webhook handler if enabled
        self.webhook_handler = None
        if config.enable_webhooks:
            webhook_config = PalmPayWebhookConfig(
                secret_key=config.secret_key,
                validate_signatures=config.validate_webhook_signatures,
                enable_auto_retry=config.enable_auto_retry,
                max_retry_attempts=config.max_retry_attempts,
                enable_ai_classification=config.enable_ai_classification
            )
            
            self.webhook_handler = PalmPayWebhookHandler(
                webhook_config,
                self.auth_manager,
                self.payment_processor
            )
        
        # Connection state
        self._connection_status = "disconnected"
        self._last_health_check = None
        self._health_check_interval = timedelta(minutes=5)
        
        self.logger.info("PalmPay connector initialized", extra={
            'merchant_id': config.merchant_id,
            'environment': config.environment,
            'privacy_level': config.privacy_level.value,
            'webhooks_enabled': config.enable_webhooks
        })
    
    async def connect(self) -> bool:
        """
        Establish connection to PalmPay API
        """
        try:
            self.logger.info("Connecting to PalmPay API...")
            
            # Test authentication
            token = await self.auth_manager.get_valid_token()
            if not token:
                raise Exception("Failed to obtain authentication token")
            
            # Perform health check
            health_status = await self.health_check()
            if not health_status['healthy']:
                raise Exception(f"Health check failed: {health_status.get('error')}")
            
            self._connection_status = "connected"
            self.logger.info("Successfully connected to PalmPay API", extra={
                'merchant_id': self.config.merchant_id,
                'environment': self.config.environment
            })
            
            return True
            
        except Exception as e:
            self._connection_status = "failed"
            self.logger.error("Failed to connect to PalmPay API", extra={
                'error': str(e),
                'merchant_id': self.config.merchant_id
            })
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from PalmPay API
        """
        try:
            # Clear authentication tokens
            self.auth_manager.clear_credentials()
            
            self._connection_status = "disconnected"
            self.logger.info("Disconnected from PalmPay API")
            
            return True
            
        except Exception as e:
            self.logger.error("Error during disconnect", extra={'error': str(e)})
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of PalmPay integration
        """
        health_start = datetime.utcnow()
        
        try:
            # Check authentication
            auth_healthy = False
            auth_error = None
            try:
                token = await self.auth_manager.get_valid_token()
                auth_healthy = token is not None and not token.is_expired
            except Exception as e:
                auth_error = str(e)
            
            # Check API connectivity (simple endpoint test)
            api_healthy = False
            api_response_time = None
            api_error = None
            
            if auth_healthy:
                try:
                    api_start = datetime.utcnow()
                    # Test with a simple query (this would be a real endpoint in implementation)
                    stats = await self.payment_processor.get_processor_statistics()
                    api_response_time = (datetime.utcnow() - api_start).total_seconds()
                    api_healthy = True
                except Exception as e:
                    api_error = str(e)
            
            # Overall health assessment
            overall_healthy = auth_healthy and api_healthy
            
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
                    }
                },
                'configuration': {
                    'environment': self.config.environment,
                    'merchant_id': self.config.merchant_id,
                    'privacy_level': self.config.privacy_level.value,
                    'webhooks_enabled': self.config.enable_webhooks,
                    'ai_classification_enabled': self.config.enable_ai_classification
                }
            }
            
            if overall_healthy:
                self.logger.debug("PalmPay health check passed", extra=health_result)
            else:
                self.logger.warning("PalmPay health check failed", extra=health_result)
            
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
    
    async def fetch_transactions(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        **kwargs
    ) -> List[PalmPayTransaction]:
        """
        Fetch transactions from PalmPay with comprehensive processing
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        try:
            self.logger.info("Fetching PalmPay transactions", extra={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'limit': limit
            })
            
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            # Fetch transactions with pagination support
            all_transactions = []
            offset = 0
            batch_size = min(limit, 50)  # PalmPay API batch size limit
            
            while len(all_transactions) < limit:
                batch_transactions = await self.payment_processor.fetch_transactions(
                    start_date=start_date,
                    end_date=end_date,
                    limit=batch_size,
                    offset=offset
                )
                
                if not batch_transactions:
                    break  # No more transactions
                
                all_transactions.extend(batch_transactions)
                offset += batch_size
                
                # Break if we have enough transactions
                if len(batch_transactions) < batch_size:
                    break
            
            # Trim to requested limit
            final_transactions = all_transactions[:limit]
            
            self.logger.info("Successfully fetched PalmPay transactions", extra={
                'total_fetched': len(final_transactions),
                'date_range': f"{start_date.date()} to {end_date.date()}"
            })
            
            return final_transactions
            
        except Exception as e:
            self.logger.error("Error fetching PalmPay transactions", extra={
                'error': str(e),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            })
            raise
    
    async def get_customer_info(self, customer_id: str) -> Optional[PalmPayCustomer]:
        """
        Retrieve customer information with privacy protection
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            customer = await self.payment_processor.get_customer_info(customer_id)
            
            if customer:
                self.logger.debug("Customer info retrieved", extra={
                    'customer_id': customer_id,
                    'privacy_level': customer.privacy_level.value
                })
            
            return customer
            
        except Exception as e:
            self.logger.error("Error retrieving customer info", extra={
                'customer_id': customer_id,
                'error': str(e)
            })
            return None
    
    async def query_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Query the status of a specific transaction
        """
        try:
            # Ensure connection
            if self._connection_status != "connected":
                await self.connect()
            
            response = await self.payment_processor.query_transaction_status(transaction_id)
            
            if response.success:
                self.logger.debug("Transaction status queried", extra={
                    'transaction_id': transaction_id,
                    'status': response.data.get('status')
                })
            
            return {
                'success': response.success,
                'data': response.data,
                'error': response.error_message
            }
            
        except Exception as e:
            self.logger.error("Error querying transaction status", extra={
                'transaction_id': transaction_id,
                'error': str(e)
            })
            return {
                'success': False,
                'error': str(e)
            }
    
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
    
    async def process_webhook_retries(self):
        """
        Process failed webhook events that are ready for retry
        """
        if self.webhook_handler:
            await self.webhook_handler.process_retries()
    
    async def get_account_balance(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account balance information (if supported by PalmPay API)
        """
        try:
            # This would be implemented based on PalmPay's actual API
            # For now, return a placeholder response
            return {
                'success': False,
                'message': 'Account balance API not available in current PalmPay integration'
            }
            
        except Exception as e:
            self.logger.error("Error fetching account balance", extra={
                'account_id': account_id,
                'error': str(e)
            })
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_supported_transaction_types(self) -> List[str]:
        """
        Get list of supported transaction types for PalmPay
        """
        return [
            'inter_bank_transfer',    # PalmPay specialization
            'mobile_wallet',
            'qr_payment',
            'bill_payment',
            'airtime_purchase',
            'data_purchase',
            'money_transfer',
            'merchant_payment',
            'cash_in',
            'cash_out'
        ]
    
    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get list of supported features for this connector
        """
        return {
            'fetch_transactions': True,
            'real_time_webhooks': self.config.enable_webhooks,
            'customer_info': True,
            'transaction_status_query': True,
            'account_balance': False,  # Not currently supported
            'ai_classification': self.config.enable_ai_classification,
            'privacy_protection': self.config.enable_ndpr_compliance,
            'inter_bank_transfers': self.config.enable_inter_bank_transfers,
            'mobile_wallet': self.config.enable_mobile_wallet,
            'qr_payments': self.config.enable_qr_payments,
            'bill_payments': self.config.enable_bill_payments
        }
    
    async def get_integration_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive integration statistics and metrics
        """
        try:
            base_stats = {
                'connector': 'palmpay',
                'version': '1.0.0',
                'environment': self.config.environment,
                'connection_status': self._connection_status,
                'last_health_check': self._last_health_check.isoformat() if self._last_health_check else None
            }
            
            # Add processor statistics
            if self._connection_status == "connected":
                processor_stats = await self.payment_processor.get_processor_statistics()
                base_stats.update(processor_stats)
            
            # Add webhook statistics
            if self.webhook_handler:
                webhook_stats = self.webhook_handler.get_webhook_statistics()
                base_stats['webhook_statistics'] = webhook_stats
            
            # Add feature support
            base_stats['supported_features'] = self.get_supported_features()
            base_stats['supported_transaction_types'] = self.get_supported_transaction_types()
            
            return base_stats
            
        except Exception as e:
            self.logger.error("Error getting integration statistics", extra={'error': str(e)})
            return {
                'connector': 'palmpay',
                'error': str(e),
                'connection_status': self._connection_status
            }
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the connector configuration
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        if not self.config.api_key:
            validation_results['errors'].append("API key is required")
            validation_results['valid'] = False
        
        if not self.config.secret_key:
            validation_results['errors'].append("Secret key is required")
            validation_results['valid'] = False
        
        if not self.config.merchant_id:
            validation_results['errors'].append("Merchant ID is required")
            validation_results['valid'] = False
        
        # Check environment
        if self.config.environment not in ['sandbox', 'production']:
            validation_results['errors'].append("Environment must be 'sandbox' or 'production'")
            validation_results['valid'] = False
        
        # Warnings for production
        if self.config.environment == 'production':
            if not self.config.validate_webhook_signatures:
                validation_results['warnings'].append("Webhook signature validation should be enabled in production")
            
            if self.config.privacy_level == PrivacyLevel.STANDARD:
                validation_results['warnings'].append("Consider higher privacy level for production")
        
        return validation_results


# Export for external use
__all__ = [
    'PalmPayConnectorConfig',
    'PalmPayConnector'
]