"""
WooCommerce E-commerce Connector
Main connector implementation for WooCommerce e-commerce platform integration.
Implements the BaseEcommerceConnector interface for TaxPoynt eInvoice platform.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ....connector_framework.base_ecommerce_connector import (
    BaseEcommerceConnector,
    EcommerceOrder,
    EcommerceSyncResult,
    EcommerceHealthStatus,
    EcommerceWebhookPayload
)
from ....framework.models.base_models import ConnectionConfig
from ....shared.models.invoice_models import UBLInvoice
from ....shared.exceptions.integration_exceptions import (
    ConnectionError,
    AuthenticationError,
    DataSyncError,
    ValidationError
)

from .auth import WooCommerceAuthManager
from .rest_client import WooCommerceRestClient
from .data_extractor import WooCommerceDataExtractor
from .order_transformer import WooCommerceOrderTransformer
from .exceptions import (
    WooCommerceConnectionError,
    WooCommerceAuthenticationError,
    WooCommerceAPIError,
    create_woocommerce_exception
)

logger = logging.getLogger(__name__)


class WooCommerceEcommerceConnector(BaseEcommerceConnector):
    """
    WooCommerce E-commerce Connector Implementation
    
    Provides comprehensive integration with WooCommerce e-commerce platform including:
    - OAuth 1.0a and Basic authentication
    - Order synchronization and data extraction
    - FIRS-compliant invoice transformation
    - Webhook processing for real-time updates
    - Customer and product data management
    - WordPress integration and plugin compatibility
    - Nigerian tax compliance (7.5% VAT)
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize WooCommerce e-commerce connector.
        
        Args:
            config: Connection configuration with WooCommerce credentials
        """
        super().__init__(config)
        
        # Initialize WooCommerce components
        self.auth_manager = WooCommerceAuthManager(config)
        self.rest_client = WooCommerceRestClient(self.auth_manager)
        self.data_extractor = WooCommerceDataExtractor(self.rest_client)
        self.transformer = WooCommerceOrderTransformer()
        
        # Connection state
        self._is_connected = False
        self._last_sync_time: Optional[datetime] = None
        self._store_info: Optional[Dict[str, Any]] = None
        
        # Configuration
        self.sync_config.update({
            'webhook_topics': [
                'order.created',
                'order.updated',
                'order.completed',
                'order.cancelled',
                'order.refunded',
                'order.restored',
                'customer.created',
                'customer.updated',
                'product.created',
                'product.updated'
            ],
            'order_statuses': config.sync_config.get('order_statuses', ['processing', 'completed']),
            'include_pending_orders': config.sync_config.get('include_pending_orders', False),
            'include_cancelled_orders': config.sync_config.get('include_cancelled_orders', False),
            'include_refunded_orders': config.sync_config.get('include_refunded_orders', True),
            'sync_customers': config.sync_config.get('sync_customers', True),
            'sync_products': config.sync_config.get('sync_products', False)
        })
        
        logger.info(f"Initialized WooCommerce e-commerce connector for store: {self.auth_manager.store_base_url}")
    
    async def connect(self) -> bool:
        """
        Establish connection to WooCommerce store.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            WooCommerceConnectionError: If connection fails
            WooCommerceAuthenticationError: If authentication fails
        """
        try:
            logger.info("Connecting to WooCommerce store...")
            
            # Authenticate with WooCommerce
            auth_success = await self.auth_manager.authenticate()
            if not auth_success:
                raise WooCommerceConnectionError("Failed to authenticate with WooCommerce")
            
            # Test connection by fetching store info
            store_info = await self.data_extractor.get_store_info()
            if not store_info:
                raise WooCommerceConnectionError("Failed to retrieve store information")
            
            self._store_info = store_info
            self._is_connected = True
            
            store_name = store_info.get('store_name', 'Unknown')
            wc_version = store_info.get('woocommerce_version', 'Unknown')
            logger.info(f"Successfully connected to WooCommerce store: {store_name} (WC v{wc_version})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to WooCommerce store: {str(e)}")
            self._is_connected = False
            raise create_woocommerce_exception(e)
    
    async def disconnect(self) -> bool:
        """
        Disconnect from WooCommerce store.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            logger.info("Disconnecting from WooCommerce store...")
            
            # Clean up resources
            await self.auth_manager.cleanup()
            self._is_connected = False
            self._store_info = None
            
            logger.info("Successfully disconnected from WooCommerce store")
            return True
            
        except Exception as e:
            logger.error(f"Error during WooCommerce disconnection: {str(e)}")
            return False
    
    async def test_connection(self) -> EcommerceHealthStatus:
        """
        Test connection health to WooCommerce store.
        
        Returns:
            EcommerceHealthStatus: Connection health information
        """
        try:
            # Test authentication
            auth_valid = await self.auth_manager.validate_credentials()
            if not auth_valid:
                return EcommerceHealthStatus(
                    is_healthy=False,
                    status_message="Authentication failed",
                    last_check=datetime.utcnow(),
                    details={'auth_status': 'invalid'}
                )
            
            # Test API connectivity
            store_info = await self.data_extractor.get_store_info()
            if not store_info:
                return EcommerceHealthStatus(
                    is_healthy=False,
                    status_message="API connectivity failed",
                    last_check=datetime.utcnow(),
                    details={'api_status': 'unreachable'}
                )
            
            # Test order access
            try:
                recent_orders = await self.rest_client.get_orders(per_page=1)
                order_access = 'accessible' if recent_orders is not None else 'limited'
            except Exception:
                order_access = 'unavailable'
            
            # Connection is healthy
            return EcommerceHealthStatus(
                is_healthy=True,
                status_message="Connection healthy",
                last_check=datetime.utcnow(),
                details={
                    'store_url': self.auth_manager.store_base_url,
                    'store_name': store_info.get('store_name'),
                    'woocommerce_version': store_info.get('woocommerce_version'),
                    'wordpress_version': store_info.get('wordpress_version'),
                    'api_status': 'connected',
                    'auth_status': 'valid',
                    'auth_method': 'oauth' if self.auth_manager.uses_oauth else 'basic',
                    'order_access': order_access,
                    'currency': store_info.get('currency'),
                    'country': store_info.get('country'),
                    'api_enabled': store_info.get('api_enabled'),
                    'ssl_enabled': store_info.get('force_ssl'),
                    'taxes_enabled': store_info.get('taxes_enabled'),
                    'active_plugins': len(store_info.get('active_plugins', [])),
                    'request_history': self.rest_client.request_history_count
                }
            )
            
        except Exception as e:
            logger.error(f"Connection health check failed: {str(e)}")
            return EcommerceHealthStatus(
                is_healthy=False,
                status_message=f"Health check failed: {str(e)}",
                last_check=datetime.utcnow(),
                details={'error': str(e)}
            )
    
    async def sync_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_status: Optional[str] = None,
        order_ids: Optional[List[str]] = None
    ) -> EcommerceSyncResult:
        """
        Synchronize orders from WooCommerce store.
        
        Args:
            start_date: Start date for sync (default: last sync time)
            end_date: End date for sync (default: now)
            order_status: Filter by order status
            order_ids: Specific order IDs to sync
            
        Returns:
            EcommerceSyncResult: Synchronization results
            
        Raises:
            DataSyncError: If synchronization fails
        """
        try:
            logger.info("Starting WooCommerce order synchronization...")
            
            # Set default date range
            if not start_date:
                start_date = self._last_sync_time or (datetime.utcnow() - timedelta(days=7))
            if not end_date:
                end_date = datetime.utcnow()
            
            # Extract orders from WooCommerce
            if order_ids:
                # Sync specific orders
                orders = await self.data_extractor.batch_extract_orders(order_ids)
            else:
                # Sync orders by date range and filters
                # Apply configured order status filters if not specified
                if not order_status:
                    if self.sync_config['include_pending_orders']:
                        order_status = None  # Include all statuses
                    else:
                        # Use first configured status as filter
                        order_status = self.sync_config['order_statuses'][0] if self.sync_config['order_statuses'] else None
                
                orders = await self.data_extractor.extract_orders(
                    start_date=start_date,
                    end_date=end_date,
                    order_status=order_status
                )
            
            logger.info(f"Extracted {len(orders)} orders from WooCommerce")
            
            # Transform orders to UBL invoices
            successful_invoices = []
            failed_orders = []
            
            for order in orders:
                try:
                    # Filter orders based on configuration
                    if not self._should_process_order(order):
                        continue
                    
                    # Get WooCommerce-specific metadata
                    woocommerce_metadata = await self._get_order_metadata(order)
                    
                    # Transform to UBL invoice
                    invoice = await self.transformer.transform_order(
                        order,
                        self._store_info,
                        woocommerce_metadata
                    )
                    
                    successful_invoices.append(invoice)
                    
                except Exception as e:
                    logger.error(f"Failed to transform order {order.order_id}: {str(e)}")
                    failed_orders.append({
                        'order_id': order.order_id,
                        'order_number': order.order_number,
                        'error': str(e)
                    })
            
            # Update sync time
            self._last_sync_time = end_date
            
            result = EcommerceSyncResult(
                success=True,
                orders_processed=len(orders),
                orders_successful=len(successful_invoices),
                orders_failed=len(failed_orders),
                sync_start_time=start_date,
                sync_end_time=end_date,
                invoices=successful_invoices,
                errors=failed_orders,
                metadata={
                    'source_system': 'woocommerce_ecommerce',
                    'store_url': self.auth_manager.store_base_url,
                    'store_name': self._store_info.get('store_name') if self._store_info else None,
                    'woocommerce_version': self._store_info.get('woocommerce_version') if self._store_info else None,
                    'sync_type': 'batch' if order_ids else 'date_range',
                    'filters_applied': {
                        'order_status': order_status,
                        'include_pending': self.sync_config['include_pending_orders'],
                        'include_cancelled': self.sync_config['include_cancelled_orders'],
                        'include_refunded': self.sync_config['include_refunded_orders']
                    }
                }
            )
            
            logger.info(f"WooCommerce sync completed: {len(successful_invoices)} successful, {len(failed_orders)} failed")
            return result
            
        except Exception as e:
            logger.error(f"WooCommerce order synchronization failed: {str(e)}")
            raise DataSyncError(f"Sync failed: {str(e)}")
    
    async def get_order(self, order_id: str) -> Optional[EcommerceOrder]:
        """
        Retrieve specific order from WooCommerce store.
        
        Args:
            order_id: WooCommerce order ID
            
        Returns:
            EcommerceOrder: Order data or None if not found
        """
        try:
            order = await self.data_extractor.get_single_order(order_id)
            if order:
                logger.info(f"Retrieved WooCommerce order: {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to retrieve WooCommerce order {order_id}: {str(e)}")
            return None
    
    async def process_webhook(self, payload: EcommerceWebhookPayload) -> bool:
        """
        Process WooCommerce webhook notification.
        
        Args:
            payload: Webhook payload from WooCommerce
            
        Returns:
            bool: True if processing successful
        """
        try:
            logger.info(f"Processing WooCommerce webhook: {payload.event_type}")
            
            # Validate webhook signature if configured
            if hasattr(payload, 'signature') and payload.signature:
                is_valid = self.auth_manager.verify_webhook_signature(
                    payload=str(payload.data),
                    signature=payload.signature
                )
                
                if not is_valid:
                    logger.warning("Invalid WooCommerce webhook signature")
                    return False
            
            # Process based on event type
            if payload.event_type in [
                'order.created', 'order.updated', 'order.completed'
            ]:
                # Extract order from webhook data
                order = await self.data_extractor.extract_order_from_webhook(payload.data)
                
                if order and self._should_process_order(order):
                    # Transform to UBL invoice
                    woocommerce_metadata = payload.data
                    invoice = await self.transformer.transform_order(
                        order,
                        self._store_info,
                        woocommerce_metadata
                    )
                    
                    # Trigger invoice processing (implementation specific)
                    await self._process_webhook_invoice(invoice, payload)
                    
                    logger.info(f"Successfully processed WooCommerce webhook for order: {order.order_id}")
                    return True
                    
            elif payload.event_type in ['order.cancelled', 'order.refunded']:
                # Handle order cancellation or refund
                order_id = payload.data.get('id')
                logger.info(f"Processing order {payload.event_type}: {order_id}")
                # Implementation for handling cancelled/refunded orders
                return True
            
            elif payload.event_type in ['customer.created', 'customer.updated']:
                # Handle customer events
                customer_id = payload.data.get('id')
                logger.info(f"Processing customer {payload.event_type}: {customer_id}")
                # Implementation for handling customer events
                return True
            
            elif payload.event_type in ['product.created', 'product.updated']:
                # Handle product events
                product_id = payload.data.get('id')
                logger.info(f"Processing product {payload.event_type}: {product_id}")
                # Implementation for handling product events
                return True
            
            logger.info(f"WooCommerce webhook {payload.event_type} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process WooCommerce webhook: {str(e)}")
            return False
    
    async def validate_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate WooCommerce webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            secret: Webhook secret
            
        Returns:
            bool: True if signature is valid
        """
        return self.auth_manager.verify_webhook_signature(payload, signature, secret)
    
    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get store/shop information from WooCommerce.
        
        Returns:
            Dict: Store information including name, address, settings
        """
        if not self._store_info:
            self._store_info = await self.data_extractor.get_store_info()
        
        return self._store_info or {}
    
    async def get_products(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        product_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from WooCommerce store.
        
        Args:
            limit: Maximum number of products to return
            offset: Offset for pagination (page number)
            product_ids: Specific product IDs to retrieve
            
        Returns:
            List[Dict]: Product information
        """
        try:
            if product_ids:
                # Get specific products
                products = []
                for product_id in product_ids:
                    product = await self.data_extractor.get_product(product_id)
                    if product:
                        products.append(product)
                return products
            else:
                # Get products with pagination
                page = (offset // (limit or 10)) + 1 if offset else 1
                products = await self.data_extractor.extract_products(
                    limit=limit or 10
                )
                return products
                
        except Exception as e:
            logger.error(f"Failed to get products: {str(e)}")
            return []
    
    async def get_customers(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        customer_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get customers from WooCommerce store.
        
        Args:
            limit: Maximum number of customers to return
            offset: Offset for pagination (page number)
            customer_ids: Specific customer IDs to retrieve
            
        Returns:
            List[Dict]: Customer information
        """
        try:
            if customer_ids:
                # Get specific customers
                customers = []
                for customer_id in customer_ids:
                    customer = await self.data_extractor.get_customer(customer_id)
                    if customer:
                        customers.append(customer)
                return customers
            else:
                # Get customers with pagination
                customers = await self.data_extractor.extract_customers(
                    limit=limit or 10
                )
                return customers
                
        except Exception as e:
            logger.error(f"Failed to get customers: {str(e)}")
            return []
    
    # Webhook Management
    
    async def setup_webhooks(self, webhook_url: str) -> List[Dict[str, Any]]:
        """
        Set up webhooks for real-time order processing.
        
        Args:
            webhook_url: Base URL for webhooks
            
        Returns:
            List[Dict]: Created webhooks
        """
        try:
            logger.info("Setting up WooCommerce webhooks...")
            
            created_webhooks = []
            
            for topic in self.sync_config['webhook_topics']:
                webhook_endpoint = f"{webhook_url.rstrip('/')}/woocommerce/{topic.replace('.', '_')}"
                
                try:
                    webhook = await self.rest_client.create_webhook(
                        topic=topic,
                        delivery_url=webhook_endpoint,
                        secret=self.auth_manager.webhook_secret
                    )
                    
                    created_webhooks.append(webhook)
                    logger.info(f"Created webhook for {topic}: {webhook.get('id')}")
                    
                except Exception as e:
                    logger.error(f"Failed to create webhook for {topic}: {str(e)}")
                    continue
            
            logger.info(f"Successfully created {len(created_webhooks)} webhooks")
            return created_webhooks
            
        except Exception as e:
            logger.error(f"Failed to setup webhooks: {str(e)}")
            return []
    
    async def list_webhooks(self) -> List[Dict[str, Any]]:
        """
        List all configured webhooks.
        
        Returns:
            List[Dict]: List of webhooks
        """
        try:
            webhooks = await self.rest_client.get_webhooks()
            logger.info(f"Retrieved {len(webhooks)} webhooks")
            return webhooks
            
        except Exception as e:
            logger.error(f"Failed to list webhooks: {str(e)}")
            return []
    
    # Analytics and Reporting
    
    async def get_order_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get order statistics for the specified period.
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dict: Order statistics
        """
        try:
            statistics = await self.data_extractor.get_order_statistics(
                start_date=start_date,
                end_date=end_date
            )
            
            # Add store context
            statistics.update({
                'store_url': self.auth_manager.store_base_url,
                'store_name': self._store_info.get('store_name') if self._store_info else None,
                'woocommerce_version': self._store_info.get('woocommerce_version') if self._store_info else None
            })
            
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to get order statistics: {str(e)}")
            return {}
    
    async def get_tax_information(self) -> Dict[str, Any]:
        """
        Get tax configuration from WooCommerce.
        
        Returns:
            Dict: Tax rates and classes information
        """
        try:
            tax_rates = await self.data_extractor.get_tax_rates()
            tax_classes = await self.data_extractor.get_tax_classes()
            
            return {
                'tax_rates': tax_rates,
                'tax_classes': tax_classes,
                'taxes_enabled': self._store_info.get('taxes_enabled') if self._store_info else False
            }
            
        except Exception as e:
            logger.error(f"Failed to get tax information: {str(e)}")
            return {}
    
    # Private helper methods
    
    def _should_process_order(self, order: EcommerceOrder) -> bool:
        """Check if order should be processed based on configuration."""
        order_status = order.order_status.value
        
        # Check configured order statuses
        if self.sync_config['order_statuses'] and order_status not in self.sync_config['order_statuses']:
            # Special handling for configured flags
            if order_status == 'pending' and not self.sync_config['include_pending_orders']:
                return False
            elif order_status == 'cancelled' and not self.sync_config['include_cancelled_orders']:
                return False
            elif order_status == 'refunded' and not self.sync_config['include_refunded_orders']:
                return False
        
        # Additional business logic can be added here
        return True
    
    async def _get_order_metadata(self, order: EcommerceOrder) -> Dict[str, Any]:
        """Get WooCommerce-specific metadata for order."""
        metadata = {
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'store_url': self.auth_manager.store_base_url
        }
        
        # Add any additional WooCommerce metadata from order
        if order.metadata:
            metadata.update({
                'woocommerce_order_id': order.metadata.get('woocommerce_order_id'),
                'woocommerce_order_key': order.metadata.get('woocommerce_order_key'),
                'woocommerce_status': order.metadata.get('woocommerce_status'),
                'woocommerce_version': order.metadata.get('woocommerce_version'),
                'woocommerce_created_via': order.metadata.get('woocommerce_created_via'),
                'wordpress_integration': True,
                'ecommerce_platform': 'woocommerce'
            })
        
        return metadata
    
    async def _process_webhook_invoice(self, invoice: UBLInvoice, payload: EcommerceWebhookPayload) -> None:
        """Process invoice from webhook (implementation specific)."""
        # This would typically send the invoice to the TaxPoynt processing pipeline
        logger.info(f"Processing webhook invoice: {invoice.header.invoice_id}")
        
        # Add webhook processing logic here
        # For example: await self.invoice_processor.process_invoice(invoice)
    
    @property
    def connector_type(self) -> str:
        """Get connector type identifier."""
        return "woocommerce_ecommerce"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()