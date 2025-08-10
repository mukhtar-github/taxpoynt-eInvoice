"""
Magento E-commerce Connector
Main connector implementation for Magento e-commerce platform integration.
Implements the BaseEcommerceConnector interface for TaxPoynt eInvoice platform.
Supports both Adobe Commerce and Magento Open Source.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from ..base_connector import BaseEcommerceConnector
from .auth import MagentoAuthManager
from .rest_client import MagentoRESTClient
from .data_extractor import MagentoDataExtractor
from .order_transformer import MagentoOrderTransformer
from .exceptions import (
    MagentoConnectionError,
    MagentoAuthenticationError,
    MagentoDataExtractionError,
    MagentoTransformationError
)

logger = logging.getLogger(__name__)


class MagentoEcommerceConnector(BaseEcommerceConnector):
    """
    Magento E-commerce Platform Connector
    
    Comprehensive connector for integrating with Magento/Adobe Commerce stores.
    Supports both Adobe Commerce and Magento Open Source with multi-store operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Magento e-commerce connector.
        
        Args:
            config: Configuration dictionary containing:
                - base_url: Magento store base URL
                - auth_type: Authentication type ('integration', 'bearer', 'customer')
                - integration_token: Integration access token (if using integration auth)
                - username: Admin username (if using bearer auth)
                - password: Admin password (if using bearer auth)
                - store_id: Default store ID for multi-store operations
                - webhook_secret: Secret for webhook verification
                - rate_limit: API rate limit settings
        """
        super().__init__(config)
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize components
        self.auth_manager = MagentoAuthManager(config)
        self.rest_client = MagentoRESTClient(config, self.auth_manager)
        self.data_extractor = MagentoDataExtractor(self.rest_client)
        self.order_transformer = MagentoOrderTransformer(config.get('transformer', {}))
        
        # Store configuration
        self.store_id = config.get('store_id')
        self.webhook_secret = config.get('webhook_secret', '')
        
        # Connection state
        self._is_connected = False
        self._last_health_check = None
        self._health_check_interval = timedelta(minutes=5)
    
    async def connect(self) -> bool:
        """
        Establish connection to Magento store.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info("Connecting to Magento store...")
            
            # Authenticate with Magento
            await self.auth_manager.authenticate()
            
            # Test connection with a simple API call
            store_config = await self.rest_client.get_store_config(self.store_id)
            if not store_config:
                raise MagentoConnectionError("Failed to retrieve store configuration")
            
            self._is_connected = True
            self._last_health_check = datetime.now()
            
            self.logger.info(f"Successfully connected to Magento store: {store_config.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Magento: {e}")
            self._is_connected = False
            raise MagentoConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Magento store.
        
        Returns:
            True if disconnection successful
        """
        try:
            self.logger.info("Disconnecting from Magento store...")
            
            # Clear authentication
            await self.auth_manager.revoke_authentication()
            
            # Close any persistent connections
            await self.rest_client.close()
            
            self._is_connected = False
            self.logger.info("Successfully disconnected from Magento store")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during disconnection: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Magento store.
        
        Returns:
            Connection test results
        """
        try:
            start_time = datetime.now()
            
            # Test authentication
            auth_valid = await self.auth_manager.validate_authentication()
            if not auth_valid:
                return {
                    'success': False,
                    'error': 'Authentication validation failed',
                    'timestamp': start_time.isoformat(),
                    'response_time_ms': 0
                }
            
            # Test API connectivity
            store_config = await self.rest_client.get_store_config(self.store_id)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                'success': True,
                'store_info': {
                    'name': store_config.get('name', 'Unknown'),
                    'website_id': store_config.get('website_id'),
                    'store_id': store_config.get('id'),
                    'locale': store_config.get('locale'),
                    'currency': store_config.get('base_currency_code'),
                    'timezone': store_config.get('timezone')
                },
                'api_version': 'REST API v1',
                'platform': 'Magento/Adobe Commerce',
                'timestamp': start_time.isoformat(),
                'response_time_ms': response_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'response_time_ms': 0
            }
    
    async def get_orders(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        order_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve orders from Magento store.
        
        Args:
            date_from: Start date for order filtering
            date_to: End date for order filtering
            order_id: Specific order ID (increment_id or entity_id)
            customer_id: Customer ID filter
            status: Order status filter
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of order dictionaries
        """
        try:
            await self._ensure_connected()
            
            # Try to parse order_id as increment_id first, then entity_id
            increment_id = None
            entity_id = None
            
            if order_id:
                if order_id.isdigit() and len(order_id) <= 10:
                    entity_id = order_id
                else:
                    increment_id = order_id
            
            orders = await self.data_extractor.extract_order_data(
                order_id=entity_id,
                increment_id=increment_id,
                date_from=date_from,
                date_to=date_to,
                store_id=self.store_id,
                customer_id=int(customer_id) if customer_id and customer_id.isdigit() else None,
                status=status,
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(orders)} orders from Magento")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            raise MagentoDataExtractionError(f"Failed to retrieve orders: {e}")
    
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific order by ID.
        
        Args:
            order_id: Order ID (increment_id or entity_id)
            
        Returns:
            Order dictionary or None if not found
        """
        try:
            orders = await self.get_orders(order_id=order_id, limit=1)
            return orders[0] if orders else None
            
        except Exception as e:
            self.logger.error(f"Failed to get order {order_id}: {e}")
            return None
    
    async def transform_order_to_invoice(
        self,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform Magento order to FIRS-compliant UBL invoice.
        
        Args:
            order_data: Magento order data
            
        Returns:
            UBL BIS 3.0 compliant invoice dictionary
        """
        try:
            # Get store configuration for the order
            store_config = None
            if order_data.get('store_id'):
                store_config = await self.rest_client.get_store_config(order_data['store_id'])
            
            # Transform order to invoice
            invoice = await self.order_transformer.transform_order_to_invoice(
                order_data, store_config
            )
            
            self.logger.info(f"Successfully transformed order {order_data.get('increment_id')} to UBL invoice")
            return invoice
            
        except Exception as e:
            self.logger.error(f"Failed to transform order to invoice: {e}")
            raise MagentoTransformationError(f"Order transformation failed: {e}")
    
    async def get_customers(
        self,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve customers from Magento store.
        
        Args:
            customer_id: Specific customer ID
            email: Customer email filter
            limit: Maximum number of customers to retrieve
            
        Returns:
            List of customer dictionaries
        """
        try:
            await self._ensure_connected()
            
            customers = await self.data_extractor.extract_customer_data(
                customer_id=int(customer_id) if customer_id and customer_id.isdigit() else None,
                email=email,
                website_id=None,  # Could be derived from store configuration
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(customers)} customers from Magento")
            return customers
            
        except Exception as e:
            self.logger.error(f"Failed to get customers: {e}")
            raise MagentoDataExtractionError(f"Failed to retrieve customers: {e}")
    
    async def get_products(
        self,
        sku: Optional[str] = None,
        name: Optional[str] = None,
        category_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products from Magento store.
        
        Args:
            sku: Specific product SKU
            name: Product name filter
            category_id: Category ID filter
            limit: Maximum number of products to retrieve
            
        Returns:
            List of product dictionaries
        """
        try:
            await self._ensure_connected()
            
            products = await self.data_extractor.extract_product_data(
                sku=sku,
                name=name,
                category_id=int(category_id) if category_id and category_id.isdigit() else None,
                store_id=self.store_id,
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(products)} products from Magento")
            return products
            
        except Exception as e:
            self.logger.error(f"Failed to get products: {e}")
            raise MagentoDataExtractionError(f"Failed to retrieve products: {e}")
    
    async def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Process incoming webhook from Magento.
        
        Args:
            event_type: Type of webhook event
            payload: Webhook payload data
            headers: HTTP headers from webhook request
            
        Returns:
            Processing result dictionary
        """
        try:
            self.logger.info(f"Processing Magento webhook: {event_type}")
            
            # Verify webhook signature if secret is configured
            if self.webhook_secret and headers:
                signature = headers.get('X-Magento-Hmac-Sha256', '')
                if not await self._verify_webhook_signature(payload, signature):
                    return {
                        'success': False,
                        'error': 'Invalid webhook signature',
                        'event_type': event_type
                    }
            
            # Process different event types
            result = None
            
            if event_type in ['sales_order_save_after', 'order.created', 'order.updated']:
                result = await self._process_order_webhook(payload)
            elif event_type in ['customer_save_after', 'customer.created', 'customer.updated']:
                result = await self._process_customer_webhook(payload)
            elif event_type in ['catalog_product_save_after', 'product.created', 'product.updated']:
                result = await self._process_product_webhook(payload)
            else:
                self.logger.warning(f"Unsupported webhook event type: {event_type}")
                result = {
                    'success': False,
                    'error': f'Unsupported event type: {event_type}',
                    'event_type': event_type
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process webhook {event_type}: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_type': event_type
            }
    
    async def _process_order_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process order-related webhook."""
        try:
            order_id = payload.get('entity_id') or payload.get('increment_id')
            if not order_id:
                return {
                    'success': False,
                    'error': 'No order ID found in webhook payload'
                }
            
            # Fetch full order data
            order_data = await self.get_order_by_id(str(order_id))
            if not order_data:
                return {
                    'success': False,
                    'error': f'Order {order_id} not found'
                }
            
            # Transform to invoice if order is in appropriate status
            invoice_eligible_statuses = ['processing', 'complete', 'shipped']
            order_status = order_data.get('status', '').lower()
            
            if order_status in invoice_eligible_statuses:
                try:
                    invoice = await self.transform_order_to_invoice(order_data)
                    return {
                        'success': True,
                        'action': 'invoice_generated',
                        'order_id': order_id,
                        'invoice': invoice
                    }
                except Exception as e:
                    self.logger.error(f"Failed to generate invoice for order {order_id}: {e}")
            
            return {
                'success': True,
                'action': 'order_processed',
                'order_id': order_id,
                'status': order_status
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Order webhook processing failed: {e}'
            }
    
    async def _process_customer_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process customer-related webhook."""
        try:
            customer_id = payload.get('entity_id')
            if not customer_id:
                return {
                    'success': False,
                    'error': 'No customer ID found in webhook payload'
                }
            
            return {
                'success': True,
                'action': 'customer_processed',
                'customer_id': customer_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Customer webhook processing failed: {e}'
            }
    
    async def _process_product_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process product-related webhook."""
        try:
            product_id = payload.get('entity_id')
            sku = payload.get('sku')
            
            if not product_id and not sku:
                return {
                    'success': False,
                    'error': 'No product identifier found in webhook payload'
                }
            
            return {
                'success': True,
                'action': 'product_processed',
                'product_id': product_id,
                'sku': sku
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Product webhook processing failed: {e}'
            }
    
    async def _verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> bool:
        """Verify webhook signature."""
        try:
            import hmac
            import hashlib
            import json
            
            # Create expected signature
            payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    async def get_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics and statistics from Magento store.
        
        Args:
            date_from: Start date for analytics
            date_to: End date for analytics
            
        Returns:
            Analytics data dictionary
        """
        try:
            await self._ensure_connected()
            
            analytics = await self.data_extractor.extract_order_analytics(
                date_from=date_from,
                date_to=date_to,
                store_id=self.store_id
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get analytics: {e}")
            raise MagentoDataExtractionError(f"Failed to retrieve analytics: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Magento connection.
        
        Returns:
            Health check results
        """
        try:
            # Check if health check is needed
            if (self._last_health_check and 
                datetime.now() - self._last_health_check < self._health_check_interval):
                return {
                    'status': 'healthy' if self._is_connected else 'unhealthy',
                    'last_check': self._last_health_check.isoformat(),
                    'cached': True
                }
            
            # Perform actual health check
            connection_test = await self.test_connection()
            self._last_health_check = datetime.now()
            self._is_connected = connection_test['success']
            
            return {
                'status': 'healthy' if connection_test['success'] else 'unhealthy',
                'last_check': self._last_health_check.isoformat(),
                'connection_test': connection_test,
                'cached': False
            }
            
        except Exception as e:
            self._is_connected = False
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat(),
                'cached': False
            }
    
    async def _ensure_connected(self):
        """Ensure connection to Magento is established."""
        if not self._is_connected:
            await self.connect()
        
        # Perform periodic health checks
        if (not self._last_health_check or 
            datetime.now() - self._last_health_check > self._health_check_interval):
            health = await self.health_check()
            if health['status'] != 'healthy':
                await self.connect()
    
    def __str__(self) -> str:
        """String representation of the connector."""
        return f"MagentoEcommerceConnector(base_url={self.config.get('base_url')}, store_id={self.store_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the connector."""
        return (f"MagentoEcommerceConnector("
                f"base_url='{self.config.get('base_url')}', "
                f"auth_type='{self.config.get('auth_type')}', "
                f"store_id={self.store_id}, "
                f"connected={self._is_connected})")