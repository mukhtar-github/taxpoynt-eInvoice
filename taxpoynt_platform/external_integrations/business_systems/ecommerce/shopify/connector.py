"""
Shopify E-commerce Connector
Main connector implementation for Shopify e-commerce platform integration.
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

from .auth import ShopifyAuthManager
from .rest_client import ShopifyRestClient
from .data_extractor import ShopifyDataExtractor
from .order_transformer import ShopifyOrderTransformer
from .exceptions import (
    ShopifyConnectionError,
    ShopifyAuthenticationError,
    ShopifyAPIError,
    create_shopify_exception
)

logger = logging.getLogger(__name__)


class ShopifyEcommerceConnector(BaseEcommerceConnector):
    """
    Shopify E-commerce Connector Implementation
    
    Provides comprehensive integration with Shopify e-commerce platform including:
    - OAuth 2.0 and private app authentication
    - Order synchronization and data extraction
    - FIRS-compliant invoice transformation
    - Webhook processing for real-time updates
    - Customer and product data management
    - Nigerian tax compliance (7.5% VAT)
    - Multi-store support
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Shopify e-commerce connector.
        
        Args:
            config: Connection configuration with Shopify credentials
        """
        super().__init__(config)
        
        # Initialize Shopify components
        self.auth_manager = ShopifyAuthManager(config)
        self.rest_client = ShopifyRestClient(self.auth_manager)
        self.data_extractor = ShopifyDataExtractor(self.rest_client)
        self.transformer = ShopifyOrderTransformer()
        
        # Connection state
        self._is_connected = False
        self._last_sync_time: Optional[datetime] = None
        self._store_info: Optional[Dict[str, Any]] = None
        
        # Configuration
        self.sync_config.update({
            'webhook_topics': [
                'orders/create',
                'orders/updated',
                'orders/paid',
                'orders/cancelled',
                'orders/fulfilled',
                'orders/partially_fulfilled'
            ],
            'include_draft_orders': config.sync_config.get('include_draft_orders', False),
            'include_cancelled_orders': config.sync_config.get('include_cancelled_orders', True),
            'order_statuses': config.sync_config.get('order_statuses', ['any']),
            'financial_statuses': config.sync_config.get('financial_statuses', ['paid', 'partially_paid']),
            'fulfillment_statuses': config.sync_config.get('fulfillment_statuses', ['any'])
        })
        
        logger.info(f"Initialized Shopify e-commerce connector for shop: {self.auth_manager.shop_name}")
    
    async def connect(self) -> bool:
        """
        Establish connection to Shopify store.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            ShopifyConnectionError: If connection fails
            ShopifyAuthenticationError: If authentication fails
        """
        try:
            logger.info("Connecting to Shopify store...")
            
            # Authenticate with Shopify
            auth_success = await self.auth_manager.authenticate()
            if not auth_success:
                raise ShopifyConnectionError("Failed to authenticate with Shopify")
            
            # Test connection by fetching store info
            store_info = await self.rest_client.get_shop_info()
            if not store_info:
                raise ShopifyConnectionError("Failed to retrieve store information")
            
            self._store_info = store_info
            self._is_connected = True
            
            store_name = store_info.get('name', 'Unknown')
            logger.info(f"Successfully connected to Shopify store: {store_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Shopify store: {str(e)}")
            self._is_connected = False
            raise create_shopify_exception(e)
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Shopify store.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            logger.info("Disconnecting from Shopify store...")
            
            # Clean up resources
            await self.auth_manager.cleanup()
            self._is_connected = False
            self._store_info = None
            
            logger.info("Successfully disconnected from Shopify store")
            return True
            
        except Exception as e:
            logger.error(f"Error during Shopify disconnection: {str(e)}")
            return False
    
    async def test_connection(self) -> EcommerceHealthStatus:
        """
        Test connection health to Shopify store.
        
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
            store_info = await self.rest_client.get_shop_info()
            if not store_info:
                return EcommerceHealthStatus(
                    is_healthy=False,
                    status_message="API connectivity failed",
                    last_check=datetime.utcnow(),
                    details={'api_status': 'unreachable'}
                )
            
            # Test order access
            try:
                recent_orders = await self.rest_client.get_orders(limit=1)
                order_access = 'accessible' if recent_orders is not None else 'limited'
            except Exception:
                order_access = 'unavailable'
            
            # Connection is healthy
            return EcommerceHealthStatus(
                is_healthy=True,
                status_message="Connection healthy",
                last_check=datetime.utcnow(),
                details={
                    'shop_name': self.auth_manager.shop_name,
                    'store_name': store_info.get('name'),
                    'api_status': 'connected',
                    'auth_status': 'valid',
                    'order_access': order_access,
                    'store_domain': store_info.get('domain'),
                    'plan_name': store_info.get('plan_name'),
                    'currency': store_info.get('currency'),
                    'country': store_info.get('country'),
                    'rate_limit_info': self.rest_client.rate_limit_info
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
        Synchronize orders from Shopify store.
        
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
            logger.info("Starting Shopify order synchronization...")
            
            # Set default date range
            if not start_date:
                start_date = self._last_sync_time or (datetime.utcnow() - timedelta(days=7))
            if not end_date:
                end_date = datetime.utcnow()
            
            # Extract orders from Shopify
            if order_ids:
                # Sync specific orders
                orders = await self.data_extractor.batch_extract_orders(order_ids)
            else:
                # Sync orders by date range and filters
                financial_status = None
                fulfillment_status = None
                
                # Apply configured filters
                if 'paid' in self.sync_config['financial_statuses']:
                    financial_status = 'paid'
                elif 'partially_paid' in self.sync_config['financial_statuses']:
                    financial_status = 'partially_paid'
                
                orders = await self.data_extractor.extract_orders(
                    start_date=start_date,
                    end_date=end_date,
                    order_status=order_status,
                    financial_status=financial_status,
                    fulfillment_status=fulfillment_status
                )
            
            logger.info(f"Extracted {len(orders)} orders from Shopify")
            
            # Transform orders to UBL invoices
            successful_invoices = []
            failed_orders = []
            
            for order in orders:
                try:
                    # Get Shopify-specific metadata
                    shopify_metadata = await self._get_order_metadata(order)
                    
                    # Transform to UBL invoice
                    invoice = await self.transformer.transform_order(
                        order,
                        self._store_info,
                        shopify_metadata
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
                    'source_system': 'shopify_ecommerce',
                    'shop_name': self.auth_manager.shop_name,
                    'store_name': self._store_info.get('name') if self._store_info else None,
                    'sync_type': 'batch' if order_ids else 'date_range',
                    'filters_applied': {
                        'order_status': order_status,
                        'financial_status': financial_status,
                        'fulfillment_status': fulfillment_status
                    }
                }
            )
            
            logger.info(f"Shopify sync completed: {len(successful_invoices)} successful, {len(failed_orders)} failed")
            return result
            
        except Exception as e:
            logger.error(f"Shopify order synchronization failed: {str(e)}")
            raise DataSyncError(f"Sync failed: {str(e)}")
    
    async def get_order(self, order_id: str) -> Optional[EcommerceOrder]:
        """
        Retrieve specific order from Shopify store.
        
        Args:
            order_id: Shopify order ID
            
        Returns:
            EcommerceOrder: Order data or None if not found
        """
        try:
            order = await self.data_extractor.get_single_order(order_id)
            if order:
                logger.info(f"Retrieved Shopify order: {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to retrieve Shopify order {order_id}: {str(e)}")
            return None
    
    async def process_webhook(self, payload: EcommerceWebhookPayload) -> bool:
        """
        Process Shopify webhook notification.
        
        Args:
            payload: Webhook payload from Shopify
            
        Returns:
            bool: True if processing successful
        """
        try:
            logger.info(f"Processing Shopify webhook: {payload.event_type}")
            
            # Validate webhook signature if configured
            if hasattr(payload, 'signature') and payload.signature:
                is_valid = self.auth_manager.verify_webhook_signature(
                    payload=str(payload.data),
                    signature=payload.signature
                )
                
                if not is_valid:
                    logger.warning("Invalid Shopify webhook signature")
                    return False
            
            # Process based on event type
            if payload.event_type in [
                'orders/create', 'orders/updated', 'orders/paid',
                'orders/fulfilled', 'orders/partially_fulfilled'
            ]:
                # Extract order from webhook data
                order = await self.data_extractor.extract_order_from_webhook(payload.data)
                
                if order:
                    # Transform to UBL invoice
                    shopify_metadata = payload.data
                    invoice = await self.transformer.transform_order(
                        order,
                        self._store_info,
                        shopify_metadata
                    )
                    
                    # Trigger invoice processing (implementation specific)
                    await self._process_webhook_invoice(invoice, payload)
                    
                    logger.info(f"Successfully processed Shopify webhook for order: {order.order_id}")
                    return True
                    
            elif payload.event_type == 'orders/cancelled':
                # Handle order cancellation
                order_id = payload.data.get('id')
                logger.info(f"Processing order cancellation: {order_id}")
                # Implementation for handling cancelled orders
                return True
            
            logger.info(f"Shopify webhook {payload.event_type} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Shopify webhook: {str(e)}")
            return False
    
    async def validate_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate Shopify webhook signature for security.
        
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
        Get store/shop information from Shopify.
        
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
        Get products from Shopify store.
        
        Args:
            limit: Maximum number of products to return
            offset: Offset for pagination (not directly supported by Shopify)
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
                # Get products with limit
                products = await self.data_extractor.extract_products(limit=limit)
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
        Get customers from Shopify store.
        
        Args:
            limit: Maximum number of customers to return
            offset: Offset for pagination (not directly supported by Shopify)
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
                # Get customers with limit
                customers = await self.data_extractor.extract_customers(limit=limit)
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
            logger.info("Setting up Shopify webhooks...")
            
            created_webhooks = []
            
            for topic in self.sync_config['webhook_topics']:
                webhook_endpoint = f"{webhook_url.rstrip('/')}/shopify/{topic.replace('/', '_')}"
                
                try:
                    webhook = await self.rest_client.create_webhook(
                        topic=topic,
                        address=webhook_endpoint,
                        format='json'
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
                'shop_name': self.auth_manager.shop_name,
                'store_name': self._store_info.get('name') if self._store_info else None
            })
            
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to get order statistics: {str(e)}")
            return {}
    
    # Private helper methods
    
    async def _get_order_metadata(self, order: EcommerceOrder) -> Dict[str, Any]:
        """Get Shopify-specific metadata for order."""
        metadata = {
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'shop_name': self.auth_manager.shop_name
        }
        
        # Add any additional Shopify metadata from order
        if order.metadata:
            metadata.update({
                'shopify_order_id': order.metadata.get('shopify_order_id'),
                'shopify_order_number': order.metadata.get('shopify_order_number'),
                'shopify_order_status_url': order.metadata.get('shopify_order_status_url'),
                'shopify_tags': order.metadata.get('shopify_tags'),
                'shopify_source_name': order.metadata.get('shopify_source_name'),
                'ecommerce_platform': 'shopify'
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
        return "shopify_ecommerce"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()