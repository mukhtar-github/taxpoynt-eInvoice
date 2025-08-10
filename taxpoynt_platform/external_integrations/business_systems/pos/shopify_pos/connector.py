"""
Shopify POS Connector - Main Module

Integrates all Shopify POS connector components for TaxPoynt eInvoice System Integrator functions.

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
from .auth import ShopifyAuthenticator
from .rest_client import ShopifyRESTClient
from .data_extractor import ShopifyDataExtractor
from .transaction_transformer import ShopifyTransactionTransformer
from .exceptions import (
    ShopifyAPIError, ShopifyAuthenticationError, ShopifyConnectionError,
    ShopifyWebhookError, ShopifyConfigurationError
)

logger = logging.getLogger(__name__)


class ShopifyPOSConnector(BasePOSConnector):
    """
    Shopify POS Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for Shopify POS integration,
    including OAuth 2.0 authentication, REST API connectivity, and transaction processing.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - Shopify Admin API connectivity and OAuth 2.0 authentication
    - Order/Transaction data extraction and management
    - Real-time webhook processing with signature verification
    - Connection health monitoring and error handling
    - Transaction data transformation for FIRS-compliant invoice generation
    - Location and inventory management
    
    Supported Shopify APIs:
    - Admin REST API: Orders, Customers, Products, Locations
    - GraphQL Admin API: Advanced queries and mutations
    - Webhooks API: Real-time event notifications
    
    Note: Shopify POS transactions are represented as orders in the Shopify Admin API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Shopify POS connector with configuration.
        
        Args:
            config: Configuration dictionary containing Shopify-specific settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Validate required configuration
        self._validate_config(config)
        
        # Initialize components
        self.auth = ShopifyAuthenticator(config)
        self.client = ShopifyRESTClient(self.auth)
        self.extractor = ShopifyDataExtractor(self.client, config)
        self.transformer = ShopifyTransactionTransformer(config)
        
        # Shopify-specific settings
        self.webhook_secret = config.get('webhook_secret')
        self.auto_sync_enabled = config.get('auto_sync_enabled', False)
        self.sync_interval_minutes = config.get('sync_interval_minutes', 15)
        self.pos_location_ids = config.get('pos_location_ids', [])
        self.include_online_orders = config.get('include_online_orders', False)
        
        # Performance settings
        self.batch_size = config.get('batch_size', 100)
        self.max_concurrent_requests = config.get('max_concurrent_requests', 5)
        
        self.logger.info(f"Shopify POS connector initialized for shop: {self.auth.shop_domain}")
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate required configuration parameters."""
        required_fields = ['shop_domain']
        
        # Check for authentication method
        has_private_app = config.get('private_app') and config.get('access_token')
        has_oauth = config.get('api_key') and config.get('api_secret')
        
        if not (has_private_app or has_oauth):
            raise ShopifyConfigurationError(
                "Either private app access token or OAuth credentials (api_key, api_secret) are required",
                config_field='authentication'
            )
        
        for field in required_fields:
            if not config.get(field):
                raise ShopifyConfigurationError(
                    f"Missing required configuration field: {field}",
                    config_field=field
                )
        
        # Validate webhook configuration if provided
        if config.get('webhook_url') and not config.get('webhook_secret'):
            raise ShopifyConfigurationError(
                "webhook_secret is required when webhook_url is configured",
                config_field='webhook_secret'
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Shopify POS system.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            result = await self.auth.authenticate()
            if result:
                self.logger.info("Shopify POS authentication successful")
            else:
                self.logger.error("Shopify POS authentication failed")
            return result
        except Exception as e:
            self.logger.error(f"Shopify authentication error: {str(e)}")
            raise ShopifyAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Shopify POS system.
        
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
            
            # Get shop info
            try:
                shop_info = await self.client.get_shop_info()
            except Exception as e:
                shop_info = {'error': str(e)}
            
            return {
                'success': True,
                'message': 'Shopify POS connection successful',
                'authentication': auth_result,
                'api_access': api_result,
                'health_check': health_result,
                'shop_info': shop_info,
                'connector_info': {
                    'shop_domain': self.auth.shop_domain,
                    'api_version': self.auth.api_version,
                    'private_app': self.auth.private_app,
                    'pos_location_ids': self.pos_location_ids,
                    'include_online_orders': self.include_online_orders,
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
        Retrieve transactions from Shopify POS (orders).
        
        Args:
            filters: Filter criteria including:
                - location_id: Specific location/store
                - start_date: Start date for transaction range
                - end_date: End date for transaction range
                - payment_method: Filter by payment method
                - min_amount: Minimum transaction amount
                - max_amount: Maximum transaction amount
                - financial_status: Order financial status
                - fulfillment_status: Order fulfillment status
            limit: Maximum number of transactions to return
        
        Returns:
            List of POSTransaction objects
        """
        try:
            self.logger.info(f"Retrieving Shopify transactions with filters: {filters}")
            
            # Ensure authentication
            if not await self.auth.ensure_valid_token():
                raise ShopifyAuthenticationError("Failed to authenticate with Shopify")
            
            # Extract transactions using data extractor
            transactions = await self.extractor.extract_transactions(filters, limit)
            
            self.logger.info(f"Retrieved {len(transactions)} transactions from Shopify")
            return transactions
        
        except Exception as e:
            self.logger.error(f"Error retrieving transactions: {str(e)}")
            raise
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve a specific transaction by ID (order ID).
        
        Args:
            transaction_id: Shopify order ID
        
        Returns:
            POSTransaction object or None if not found
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise ShopifyAuthenticationError("Failed to authenticate with Shopify")
            
            transaction = await self.extractor.extract_transaction_by_id(transaction_id)
            
            if transaction:
                self.logger.info(f"Retrieved transaction {transaction_id} from Shopify")
            else:
                self.logger.warning(f"Transaction {transaction_id} not found in Shopify")
            
            return transaction
        
        except Exception as e:
            self.logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            raise
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> POSWebhookEvent:
        """
        Process incoming webhook from Shopify.
        
        Args:
            webhook_data: Raw webhook payload from Shopify
        
        Returns:
            Processed POSWebhookEvent
        """
        try:
            # Extract webhook details
            # Shopify webhook headers should be passed in the webhook_data
            topic = webhook_data.get('topic', webhook_data.get('X-Shopify-Topic', 'unknown'))
            shop_domain = webhook_data.get('shop_domain', webhook_data.get('X-Shopify-Shop-Domain', self.auth.shop_domain))
            
            # Generate unique event ID
            event_id = f"{shop_domain}_{topic}_{int(datetime.now().timestamp())}"
            
            # Extract event data (the actual webhook payload)
            data = webhook_data.get('data', webhook_data)
            
            # Create webhook event
            webhook_event = POSWebhookEvent(
                event_type=topic,
                event_id=event_id,
                timestamp=datetime.now(),
                data=data,
                source='shopify',
                processed=False
            )
            
            # Process specific event types
            await self._process_webhook_event(webhook_event)
            
            self.logger.info(f"Processed Shopify webhook: {topic}")
            return webhook_event
        
        except Exception as e:
            self.logger.error(f"Error processing webhook: {str(e)}")
            raise ShopifyWebhookError(
                message=f"Webhook processing failed: {str(e)}",
                event_type=webhook_data.get('topic', 'unknown')
            )
    
    async def _process_webhook_event(self, webhook_event: POSWebhookEvent):
        """Process specific webhook event types."""
        event_type = webhook_event.event_type
        
        try:
            if event_type == 'orders/create':
                await self._handle_order_created(webhook_event)
            elif event_type == 'orders/updated':
                await self._handle_order_updated(webhook_event)
            elif event_type == 'orders/paid':
                await self._handle_order_paid(webhook_event)
            elif event_type == 'orders/cancelled':
                await self._handle_order_cancelled(webhook_event)
            elif event_type == 'orders/fulfilled':
                await self._handle_order_fulfilled(webhook_event)
            elif event_type == 'orders/partially_fulfilled':
                await self._handle_order_partially_fulfilled(webhook_event)
            elif event_type == 'customers/create':
                await self._handle_customer_created(webhook_event)
            elif event_type == 'customers/update':
                await self._handle_customer_updated(webhook_event)
            elif event_type == 'products/create':
                await self._handle_product_created(webhook_event)
            elif event_type == 'products/update':
                await self._handle_product_updated(webhook_event)
            else:
                self.logger.info(f"Unhandled webhook event type: {event_type}")
            
            webhook_event.processed = True
            
        except Exception as e:
            self.logger.error(f"Error processing webhook event {event_type}: {str(e)}")
            raise
    
    async def _handle_order_created(self, webhook_event: POSWebhookEvent):
        """Handle orders/create webhook event."""
        order_data = webhook_event.data
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"Processing new order: {order_id}")
            # Additional processing logic here (e.g., auto-generate invoice)
    
    async def _handle_order_updated(self, webhook_event: POSWebhookEvent):
        """Handle orders/updated webhook event."""
        order_data = webhook_event.data
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"Order updated: {order_id}")
            # Update processing logic here
    
    async def _handle_order_paid(self, webhook_event: POSWebhookEvent):
        """Handle orders/paid webhook event."""
        order_data = webhook_event.data
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"Order paid: {order_id}")
            # Payment processing logic here
    
    async def _handle_order_cancelled(self, webhook_event: POSWebhookEvent):
        """Handle orders/cancelled webhook event."""
        order_data = webhook_event.data
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"Order cancelled: {order_id}")
    
    async def _handle_order_fulfilled(self, webhook_event: POSWebhookEvent):
        """Handle orders/fulfilled webhook event."""
        order_data = webhook_event.data
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"Order fulfilled: {order_id}")
    
    async def _handle_order_partially_fulfilled(self, webhook_event: POSWebhookEvent):
        """Handle orders/partially_fulfilled webhook event."""
        order_data = webhook_event.data
        order_id = order_data.get('id')
        
        if order_id:
            self.logger.info(f"Order partially fulfilled: {order_id}")
    
    async def _handle_customer_created(self, webhook_event: POSWebhookEvent):
        """Handle customers/create webhook event."""
        customer_data = webhook_event.data
        customer_id = customer_data.get('id')
        
        if customer_id:
            self.logger.info(f"New customer created: {customer_id}")
    
    async def _handle_customer_updated(self, webhook_event: POSWebhookEvent):
        """Handle customers/update webhook event."""
        customer_data = webhook_event.data
        customer_id = customer_data.get('id')
        
        if customer_id:
            self.logger.info(f"Customer updated: {customer_id}")
    
    async def _handle_product_created(self, webhook_event: POSWebhookEvent):
        """Handle products/create webhook event."""
        product_data = webhook_event.data
        product_id = product_data.get('id')
        
        if product_id:
            self.logger.info(f"New product created: {product_id}")
    
    async def _handle_product_updated(self, webhook_event: POSWebhookEvent):
        """Handle products/update webhook event."""
        product_data = webhook_event.data
        product_id = product_data.get('id')
        
        if product_id:
            self.logger.info(f"Product updated: {product_id}")
    
    async def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from Shopify
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not self.webhook_secret:
                self.logger.warning("No webhook secret configured")
                return False
            
            # Shopify webhook signature verification
            # Generate expected signature using HMAC-SHA256
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            # Base64 encode
            expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
            
            # Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(signature, expected_signature_b64)
            
            if not is_valid:
                self.logger.warning("Shopify webhook signature verification failed")
            
            return is_valid
        
        except Exception as e:
            self.logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def get_locations(self) -> List[POSLocation]:
        """
        Retrieve all locations/stores from Shopify.
        
        Returns:
            List of POSLocation objects
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise ShopifyAuthenticationError("Failed to authenticate with Shopify")
            
            locations = await self.extractor.extract_locations()
            
            self.logger.info(f"Retrieved {len(locations)} locations from Shopify")
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
        Transform Shopify transaction to FIRS-compliant invoice.
        
        Args:
            transaction_id: Transaction to transform (order ID)
            transformation_options: Additional settings including:
                - issue_date: Invoice issue date
                - due_date: Invoice due date
                - invoice_number: Custom invoice number
                - customer_tin: Customer TIN number
                - include_tax_breakdown: Detailed tax information
                - shop_info: Shopify shop information
        
        Returns:
            FIRS-compliant invoice data (UBL format)
        """
        try:
            # Get transaction
            transaction = await self.get_transaction_by_id(transaction_id)
            if not transaction:
                raise ShopifyAPIError(f"Transaction {transaction_id} not found")
            
            # Add shop info to transformation options if available
            if not transformation_options:
                transformation_options = {}
            
            if 'shop_info' not in transformation_options:
                try:
                    shop_info = await self.client.get_shop_info()
                    transformation_options['shop_info'] = shop_info
                except Exception as e:
                    self.logger.warning(f"Could not retrieve shop info: {str(e)}")
            
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
        Retrieve inventory items from Shopify products.
        
        Args:
            filters: Filter criteria for inventory items
        
        Returns:
            List of POSInventoryItem objects
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise ShopifyAuthenticationError("Failed to authenticate with Shopify")
            
            items = await self.extractor.extract_inventory_items(filters)
            
            self.logger.info(f"Retrieved {len(items)} inventory items from Shopify")
            return items
        
        except Exception as e:
            self.logger.error(f"Error retrieving inventory: {str(e)}")
            raise
    
    async def sync_transactions(
        self,
        sync_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize transactions from Shopify POS.
        
        Args:
            sync_options: Synchronization options including:
                - full_sync: Whether to perform full synchronization
                - last_sync_date: Last synchronization timestamp
                - batch_size: Number of transactions per batch
                - location_id: Specific location to sync
                - financial_status: Order financial status filter
                - fulfillment_status: Order fulfillment status filter
        
        Returns:
            Synchronization results
        """
        try:
            options = sync_options or {}
            batch_size = options.get('batch_size', self.batch_size)
            
            self.logger.info(f"Starting Shopify transaction sync with options: {options}")
            
            # Build filters for sync
            filters = {}
            
            if options.get('location_id'):
                filters['location_id'] = options['location_id']
            
            if options.get('last_sync_date') and not options.get('full_sync', False):
                filters['start_date'] = options['last_sync_date']
            
            if options.get('financial_status'):
                filters['financial_status'] = options['financial_status']
            
            if options.get('fulfillment_status'):
                filters['fulfillment_status'] = options['fulfillment_status']
            
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
                    await asyncio.sleep(0.5)  # Shopify rate limiting
            
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
        Disconnect from Shopify POS system.
        
        Returns:
            True if disconnection successful
        """
        try:
            result = await self.auth.disconnect()
            if result:
                self.logger.info("Shopify POS disconnection successful")
            else:
                self.logger.warning("Shopify POS disconnection completed with warnings")
            return result
        except Exception as e:
            self.logger.error(f"Error during Shopify disconnect: {str(e)}")
            return False
    
    def get_supported_features(self) -> List[str]:
        """Get list of features supported by Shopify POS connector."""
        features = super().get_supported_features()
        features.extend([
            'oauth_authentication',
            'private_app_authentication',
            'webhook_signature_verification',
            'order_management',
            'customer_management',
            'product_management',
            'inventory_integration',
            'multi_currency_support',
            'gift_card_support',
            'discount_support',
            'graphql_api',
            'batch_processing',
            'real_time_webhooks',
            'location_management',
            'customizations_support',
            'shipping_integration'
        ])
        return features
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information."""
        return {
            'connector_type': 'shopify_pos',
            'version': '1.0',
            'authentication': self.auth.get_connection_info(),
            'features': self.get_supported_features(),
            'configuration': {
                'shop_domain': self.auth.shop_domain,
                'api_version': self.auth.api_version,
                'private_app': self.auth.private_app,
                'webhook_configured': bool(self.webhook_secret),
                'auto_sync_enabled': self.auto_sync_enabled,
                'batch_size': self.batch_size,
                'max_concurrent_requests': self.max_concurrent_requests,
                'pos_location_ids': self.pos_location_ids,
                'include_online_orders': self.include_online_orders
            },
            'nigerian_compliance': {
                'firs_integration': True,
                'vat_rate': float(self.vat_rate),
                'currency_support': ['USD', 'NGN', 'CAD', 'EUR', 'GBP'],
                'tin_validation': True,
                'ubl_bis_3_0': True
            }
        }