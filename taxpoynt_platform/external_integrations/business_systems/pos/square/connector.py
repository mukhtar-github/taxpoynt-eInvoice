"""
Square POS Connector - Main Module

Integrates all Square POS connector components for TaxPoynt eInvoice System Integrator functions.

This module combines OAuth 2.0 authentication, REST API communication, data extraction, 
and transaction-to-invoice transformation into a unified connector interface compatible with the BasePOSConnector.
"""

import asyncio
import base64
import hashlib
import hmac
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ....connector_framework.base_pos_connector import (
    BasePOSConnector, POSTransaction, POSWebhookEvent, POSLocation, 
    POSPaymentMethod, POSInventoryItem, POSRefund
)
from .auth import SquareAuthenticator
from .rest_client import SquareRESTClient
from .data_extractor import SquareDataExtractor
from .transaction_transformer import SquareTransactionTransformer
from .exceptions import (
    SquareAPIError, SquareAuthenticationError, SquareConnectionError,
    SquareWebhookError, SquareConfigurationError
)

logger = logging.getLogger(__name__)


class SquarePOSConnector(BasePOSConnector):
    """
    Square POS Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for Square POS integration,
    including OAuth 2.0 authentication, REST API connectivity, and transaction processing.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - Square REST API connectivity and OAuth 2.0 authentication
    - Transaction data extraction and management
    - Real-time webhook processing with signature verification
    - Connection health monitoring and error handling
    - Transaction data transformation for FIRS-compliant invoice generation
    - Location and inventory management
    
    Supported Square APIs:
    - Payments API: Transaction processing and retrieval
    - Orders API: Order management and line items
    - Customers API: Customer data management
    - Catalog API: Inventory and product information
    - Locations API: Store/location management
    - Webhooks API: Real-time event notifications
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Square POS connector with configuration.
        
        Args:
            config: Configuration dictionary containing Square-specific settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Validate required configuration
        self._validate_config(config)
        
        # Initialize components
        self.auth = SquareAuthenticator(config)
        self.client = SquareRESTClient(self.auth)
        self.extractor = SquareDataExtractor(self.client, config)
        self.transformer = SquareTransactionTransformer(config)
        
        # Square-specific settings
        self.webhook_signature_key = config.get('webhook_signature_key')
        self.auto_sync_enabled = config.get('auto_sync_enabled', False)
        self.sync_interval_minutes = config.get('sync_interval_minutes', 15)
        
        # Performance settings
        self.batch_size = config.get('batch_size', 100)
        self.max_concurrent_requests = config.get('max_concurrent_requests', 5)
        
        self.logger.info(f"Square POS connector initialized for {'sandbox' if self.auth.sandbox else 'production'}")
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate required configuration parameters."""
        required_fields = ['application_id', 'application_secret']
        
        for field in required_fields:
            if not config.get(field):
                raise SquareConfigurationError(
                    f"Missing required configuration field: {field}",
                    config_field=field
                )
        
        # Validate webhook configuration if provided
        if config.get('webhook_url') and not config.get('webhook_signature_key'):
            raise SquareConfigurationError(
                "webhook_signature_key is required when webhook_url is configured",
                config_field='webhook_signature_key'
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Square POS system.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            result = await self.auth.authenticate()
            if result:
                self.logger.info("Square POS authentication successful")
            else:
                self.logger.error("Square POS authentication failed")
            return result
        except Exception as e:
            self.logger.error(f"Square authentication error: {str(e)}")
            raise SquareAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Square POS system.
        
        Returns:
            Connection test results
        """
        try:
            # Test authentication
            auth_result = await self.auth.test_authentication()
            if not auth_result.get('success'):
                return {
                    'success': False,
                    'error': f"Authentication failed: {auth_result.get('error')}",
                    'component': 'authentication'
                }
            
            # Test API access
            api_result = await self.auth.test_api_access('locations')
            if not api_result.get('success'):
                return {
                    'success': False,
                    'error': f"API access failed: {api_result.get('error')}",
                    'component': 'api_access'
                }
            
            # Perform health check
            health_result = await self.client.health_check()
            
            return {
                'success': True,
                'message': 'Square POS connection successful',
                'authentication': auth_result,
                'api_access': api_result,
                'health_check': health_result,
                'connector_info': {
                    'sandbox_mode': self.auth.sandbox,
                    'api_version': self.auth.api_version,
                    'available_features': self.get_supported_features()
                }
            }
        
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'component': 'connection_test'
            }
    
    async def get_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[POSTransaction]:
        """
        Retrieve transactions from Square POS.
        
        Args:
            filters: Filter criteria including:
                - location_id: Specific location/store
                - start_date: Start date for transaction range
                - end_date: End date for transaction range
                - payment_method: Filter by payment method
                - min_amount: Minimum transaction amount
                - max_amount: Maximum transaction amount
                - customer_id: Specific customer transactions
            limit: Maximum number of transactions to return
        
        Returns:
            List of POSTransaction objects
        """
        try:
            self.logger.info(f"Retrieving Square transactions with filters: {filters}")
            
            # Ensure authentication
            if not await self.auth.ensure_valid_token():
                raise SquareAuthenticationError("Failed to authenticate with Square")
            
            # Extract transactions using data extractor
            transactions = await self.extractor.extract_transactions(filters, limit)
            
            self.logger.info(f"Retrieved {len(transactions)} transactions from Square")
            return transactions
        
        except Exception as e:
            self.logger.error(f"Error retrieving transactions: {str(e)}")
            raise
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve a specific transaction by ID.
        
        Args:
            transaction_id: Square payment ID
        
        Returns:
            POSTransaction object or None if not found
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise SquareAuthenticationError("Failed to authenticate with Square")
            
            transaction = await self.extractor.extract_transaction_by_id(transaction_id)
            
            if transaction:
                self.logger.info(f"Retrieved transaction {transaction_id} from Square")
            else:
                self.logger.warning(f"Transaction {transaction_id} not found in Square")
            
            return transaction
        
        except Exception as e:
            self.logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            raise
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> POSWebhookEvent:
        """
        Process incoming webhook from Square POS.
        
        Args:
            webhook_data: Raw webhook payload from Square
        
        Returns:
            Processed POSWebhookEvent
        """
        try:
            # Extract webhook details
            event_type = webhook_data.get('type', 'unknown')
            merchant_id = webhook_data.get('merchant_id', '')
            location_id = webhook_data.get('location_id', '')
            
            # Generate unique event ID
            event_id = f"{merchant_id}_{location_id}_{event_type}_{int(datetime.now().timestamp())}"
            
            # Extract event data
            data = webhook_data.get('data', {})
            
            # Create webhook event
            webhook_event = POSWebhookEvent(
                event_type=event_type,
                event_id=event_id,
                timestamp=datetime.now(),
                data=data,
                source='square',
                processed=False
            )
            
            # Process specific event types
            await self._process_webhook_event(webhook_event)
            
            self.logger.info(f"Processed Square webhook: {event_type}")
            return webhook_event
        
        except Exception as e:
            self.logger.error(f"Error processing webhook: {str(e)}")
            raise SquareWebhookError(
                message=f"Webhook processing failed: {str(e)}",
                event_type=webhook_data.get('type')
            )
    
    async def _process_webhook_event(self, webhook_event: POSWebhookEvent):
        """Process specific webhook event types."""
        event_type = webhook_event.event_type
        
        try:
            if event_type == 'payment.created':
                await self._handle_payment_created(webhook_event)
            elif event_type == 'payment.updated':
                await self._handle_payment_updated(webhook_event)
            elif event_type == 'order.created':
                await self._handle_order_created(webhook_event)
            elif event_type == 'order.updated':
                await self._handle_order_updated(webhook_event)
            elif event_type == 'order.fulfilled':
                await self._handle_order_fulfilled(webhook_event)
            elif event_type == 'inventory.count.updated':
                await self._handle_inventory_updated(webhook_event)
            else:
                self.logger.info(f"Unhandled webhook event type: {event_type}")
            
            webhook_event.processed = True
            
        except Exception as e:
            self.logger.error(f"Error processing webhook event {event_type}: {str(e)}")
            raise
    
    async def _handle_payment_created(self, webhook_event: POSWebhookEvent):
        """Handle payment.created webhook event."""
        payment_data = webhook_event.data.get('object', {}).get('payment', {})
        payment_id = payment_data.get('id')
        
        if payment_id:
            self.logger.info(f"Processing new payment: {payment_id}")
            # Additional processing logic here (e.g., auto-generate invoice)
    
    async def _handle_payment_updated(self, webhook_event: POSWebhookEvent):
        """Handle payment.updated webhook event."""
        payment_data = webhook_event.data.get('object', {}).get('payment', {})
        payment_id = payment_data.get('id')
        
        if payment_id:
            self.logger.info(f"Payment updated: {payment_id}")
            # Update processing logic here
    
    async def _handle_order_created(self, webhook_event: POSWebhookEvent):
        """Handle order.created webhook event."""
        order_data = webhook_event.data.get('object', {}).get('order', {})
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"New order created: {order_id}")
    
    async def _handle_order_updated(self, webhook_event: POSWebhookEvent):
        """Handle order.updated webhook event."""
        order_data = webhook_event.data.get('object', {}).get('order', {})
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"Order updated: {order_id}")
    
    async def _handle_order_fulfilled(self, webhook_event: POSWebhookEvent):
        """Handle order.fulfilled webhook event."""
        order_data = webhook_event.data.get('object', {}).get('order', {})
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"Order fulfilled: {order_id}")
    
    async def _handle_inventory_updated(self, webhook_event: POSWebhookEvent):
        """Handle inventory.count.updated webhook event."""
        inventory_data = webhook_event.data.get('object', {})
        catalog_object_id = inventory_data.get('catalog_object_id')
        
        if catalog_object_id:
            self.logger.info(f"Inventory updated for item: {catalog_object_id}")
    
    async def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from Square
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not self.webhook_signature_key:
                self.logger.warning("No webhook signature key configured")
                return False
            
            # Square webhook signature verification
            # Square combines the notification URL with the request body
            notification_url = self.webhook_url or ''
            string_to_sign = notification_url + payload
            
            # Generate expected signature using HMAC-SHA1
            expected_signature = hmac.new(
                self.webhook_signature_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
            
            # Base64 encode
            expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
            
            # Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(signature, expected_signature_b64)
            
            if not is_valid:
                self.logger.warning("Square webhook signature verification failed")
            
            return is_valid
        
        except Exception as e:
            self.logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def get_locations(self) -> List[POSLocation]:
        """
        Retrieve all locations/stores from Square POS.
        
        Returns:
            List of POSLocation objects
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise SquareAuthenticationError("Failed to authenticate with Square")
            
            locations = await self.extractor.extract_locations()
            
            self.logger.info(f"Retrieved {len(locations)} locations from Square")
            return locations
        
        except Exception as e:
            self.logger.error(f"Error retrieving locations: {str(e)}")
            raise
    
    async def get_payment_methods(self) -> List[POSPaymentMethod]:
        """
        Retrieve available payment methods.
        
        Returns:
            List of POSPaymentMethod objects
        """
        try:
            payment_methods = await self.extractor.extract_payment_methods()
            
            self.logger.info(f"Retrieved {len(payment_methods)} payment methods")
            return payment_methods
        
        except Exception as e:
            self.logger.error(f"Error retrieving payment methods: {str(e)}")
            raise
    
    async def transform_transaction_to_invoice(
        self,
        transaction_id: str,
        transformation_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Square transaction to FIRS-compliant invoice.
        
        Args:
            transaction_id: Transaction to transform
            transformation_options: Additional settings including:
                - issue_date: Invoice issue date
                - due_date: Invoice due date
                - invoice_number: Custom invoice number
                - customer_tin: Customer TIN number
                - include_tax_breakdown: Detailed tax information
        
        Returns:
            FIRS-compliant invoice data (UBL format)
        """
        try:
            # Get transaction
            transaction = await self.get_transaction_by_id(transaction_id)
            if not transaction:
                raise SquareAPIError(f"Transaction {transaction_id} not found")
            
            # Transform to invoice
            invoice_data = await self.transformer.transform_transaction_to_invoice(
                transaction, transformation_options
            )
            
            self.logger.info(f"Transformed transaction {transaction_id} to FIRS invoice")
            return invoice_data
        
        except Exception as e:
            self.logger.error(f"Error transforming transaction to invoice: {str(e)}")
            raise
    
    async def get_inventory(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[POSInventoryItem]:
        """
        Retrieve inventory items from Square catalog.
        
        Args:
            filters: Filter criteria for inventory items
        
        Returns:
            List of POSInventoryItem objects
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise SquareAuthenticationError("Failed to authenticate with Square")
            
            items = await self.extractor.extract_inventory_items(filters)
            
            self.logger.info(f"Retrieved {len(items)} inventory items from Square")
            return items
        
        except Exception as e:
            self.logger.error(f"Error retrieving inventory: {str(e)}")
            raise
    
    async def sync_transactions(
        self,
        sync_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize transactions from Square POS.
        
        Args:
            sync_options: Synchronization options including:
                - full_sync: Whether to perform full synchronization
                - last_sync_date: Last synchronization timestamp
                - batch_size: Number of transactions per batch
                - location_id: Specific location to sync
        
        Returns:
            Synchronization results
        """
        try:
            options = sync_options or {}
            batch_size = options.get('batch_size', self.batch_size)
            
            self.logger.info(f"Starting Square transaction sync with options: {options}")
            
            # Build filters for sync
            filters = {}
            
            if options.get('location_id'):
                filters['location_id'] = options['location_id']
            
            if options.get('last_sync_date') and not options.get('full_sync', False):
                filters['start_date'] = options['last_sync_date']
            
            # Get all transactions
            all_transactions = await self.get_transactions(filters=filters)
            
            # Process in batches
            batches = [
                all_transactions[i:i + batch_size] 
                for i in range(0, len(all_transactions), batch_size)
            ]
            
            processed_count = 0
            failed_count = 0
            
            sync_results = {
                'total_records': len(all_transactions),
                'batches_processed': len(batches),
                'batch_size': batch_size,
                'processed_count': 0,
                'failed_count': 0,
                'sync_timestamp': datetime.now().isoformat(),
                'transactions': []
            }
            
            # Process batches with rate limiting
            for batch_index, batch in enumerate(batches):
                self.logger.info(f"Processing batch {batch_index + 1}/{len(batches)} ({len(batch)} records)")
                
                # Process batch transactions
                batch_results = []
                for transaction in batch:
                    try:
                        # Add to results
                        batch_results.append(transaction)
                        processed_count += 1
                    except Exception as e:
                        self.logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}")
                        failed_count += 1
                
                sync_results['transactions'].extend(batch_results)
                
                # Rate limiting between batches
                if batch_index < len(batches) - 1:
                    await asyncio.sleep(0.1)
            
            sync_results['processed_count'] = processed_count
            sync_results['failed_count'] = failed_count
            
            self.logger.info(f"Sync completed: {processed_count} processed, {failed_count} failed")
            return sync_results
        
        except Exception as e:
            self.logger.error(f"Error during sync: {str(e)}")
            return {
                'error': str(e),
                'sync_timestamp': datetime.now().isoformat(),
                'processed_count': 0,
                'failed_count': 0
            }
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Square POS system.
        
        Returns:
            True if disconnection successful
        """
        try:
            result = await self.auth.disconnect()
            if result:
                self.logger.info("Square POS disconnection successful")
            else:
                self.logger.warning("Square POS disconnection completed with warnings")
            return result
        except Exception as e:
            self.logger.error(f"Error during Square disconnect: {str(e)}")
            return False
    
    def get_supported_features(self) -> List[str]:
        """Get list of features supported by Square POS connector."""
        features = super().get_supported_features()
        features.extend([
            'oauth_authentication',
            'webhook_signature_verification',
            'order_management',
            'customer_management',
            'inventory_integration',
            'multi_currency_support',
            'gift_card_support',
            'refund_processing',
            'catalog_management',
            'batch_processing',
            'real_time_webhooks',
            'transaction_search',
            'location_management'
        ])
        return features
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information."""
        return {
            'connector_type': 'square_pos',
            'version': '1.0',
            'authentication': self.auth.get_connection_info(),
            'features': self.get_supported_features(),
            'configuration': {
                'sandbox_mode': self.auth.sandbox,
                'api_version': self.auth.api_version,
                'webhook_configured': bool(self.webhook_signature_key),
                'auto_sync_enabled': self.auto_sync_enabled,
                'batch_size': self.batch_size,
                'max_concurrent_requests': self.max_concurrent_requests
            },
            'nigerian_compliance': {
                'firs_integration': True,
                'vat_rate': float(self.vat_rate),
                'currency_support': ['USD', 'NGN'],
                'tin_validation': True,
                'ubl_bis_3_0': True
            }
        }