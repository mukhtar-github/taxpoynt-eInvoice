"""
BigCommerce E-commerce Connector
Main connector implementation for BigCommerce e-commerce platform integration.
Implements the BaseEcommerceConnector interface for TaxPoynt eInvoice platform.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from ..base_connector import BaseEcommerceConnector
from .auth import BigCommerceAuthManager
from .rest_client import BigCommerceRESTClient
from .data_extractor import BigCommerceDataExtractor
from .order_transformer import BigCommerceOrderTransformer
from .exceptions import (
    BigCommerceConnectionError,
    BigCommerceAuthenticationError,
    BigCommerceDataExtractionError,
    BigCommerceTransformationError
)

logger = logging.getLogger(__name__)


class BigCommerceEcommerceConnector(BaseEcommerceConnector):
    """
    BigCommerce E-commerce Platform Connector
    
    Comprehensive connector for integrating with BigCommerce stores.
    Supports multi-channel operations and BigCommerce-specific features.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize BigCommerce e-commerce connector.
        
        Args:
            config: Configuration dictionary containing:
                - store_hash: BigCommerce store hash (required)
                - auth_type: Authentication type ('api_token', 'oauth2', 'store_token')
                - api_token: API access token (if using api_token auth)
                - client_id: OAuth2 client ID (if using oauth2 auth)
                - client_secret: OAuth2 client secret (if using oauth2 auth)
                - access_token: OAuth2 access token (if using oauth2 auth)
                - store_token: Store-specific API token (if using store_token auth)
                - webhook_secret: Secret for webhook verification
                - rate_limit: API rate limit settings
                - channel_id: Default channel ID for multi-channel operations
        """
        super().__init__(config)
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize components
        self.auth_manager = BigCommerceAuthManager(config)
        self.rest_client = BigCommerceRESTClient(config, self.auth_manager)
        self.data_extractor = BigCommerceDataExtractor(self.rest_client)
        self.order_transformer = BigCommerceOrderTransformer(config.get('transformer', {}))
        
        # Store configuration
        self.store_hash = config.get('store_hash')
        self.channel_id = config.get('channel_id')
        self.webhook_secret = config.get('webhook_secret', '')
        
        # Connection state
        self._is_connected = False
        self._last_health_check = None
        self._health_check_interval = timedelta(minutes=5)
        self._store_info = None
    
    async def connect(self) -> bool:
        """
        Establish connection to BigCommerce store.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info("Connecting to BigCommerce store...")
            
            # Authenticate with BigCommerce
            await self.auth_manager.authenticate()
            
            # Test connection with store information
            store_info = await self.rest_client.get_store_info()
            if not store_info:
                raise BigCommerceConnectionError("Failed to retrieve store information")
            
            self._store_info = store_info
            self._is_connected = True
            self._last_health_check = datetime.now()
            
            self.logger.info(f"Successfully connected to BigCommerce store: {store_info.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to BigCommerce: {e}")
            self._is_connected = False
            raise BigCommerceConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from BigCommerce store.
        
        Returns:
            True if disconnection successful
        """
        try:
            self.logger.info("Disconnecting from BigCommerce store...")
            
            # Clear authentication
            await self.auth_manager.revoke_authentication()
            
            # Close any persistent connections
            await self.rest_client.close()
            
            self._is_connected = False
            self._store_info = None
            self.logger.info("Successfully disconnected from BigCommerce store")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during disconnection: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to BigCommerce store.
        
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
            store_info = await self.rest_client.get_store_info()
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                'success': True,
                'store_info': {
                    'name': store_info.get('name', 'Unknown'),
                    'domain': store_info.get('domain', ''),
                    'currency': store_info.get('currency', ''),
                    'language': store_info.get('language', ''),
                    'timezone': store_info.get('timezone', {}).get('name', ''),
                    'plan_name': store_info.get('plan_name', ''),
                    'status': store_info.get('status', '')
                },
                'api_version': 'REST API v3',
                'platform': 'BigCommerce',
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
        Retrieve orders from BigCommerce store.
        
        Args:
            date_from: Start date for order filtering
            date_to: End date for order filtering
            order_id: Specific order ID
            customer_id: Customer ID filter
            status: Order status filter
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of order dictionaries
        """
        try:
            await self._ensure_connected()
            
            # Convert order_id to int if provided
            order_id_int = None
            if order_id:
                try:
                    order_id_int = int(order_id)
                except ValueError:
                    raise BigCommerceDataExtractionError(f"Invalid order ID format: {order_id}")
            
            # Convert customer_id to int if provided
            customer_id_int = None
            if customer_id:
                try:
                    customer_id_int = int(customer_id)
                except ValueError:
                    raise BigCommerceDataExtractionError(f"Invalid customer ID format: {customer_id}")
            
            # Map status to status_id if needed
            status_id = None
            if status:
                # BigCommerce uses numeric status IDs
                status_mapping = {
                    'pending': 1,
                    'shipped': 2,
                    'partially_shipped': 3,
                    'refunded': 4,
                    'cancelled': 5,
                    'declined': 6,
                    'awaiting_payment': 7,
                    'awaiting_pickup': 8,
                    'awaiting_shipment': 9,
                    'completed': 10,
                    'awaiting_fulfillment': 11,
                    'manual_verification_required': 12,
                    'disputed': 13,
                    'partially_refunded': 14
                }
                status_id = status_mapping.get(status.lower())
            
            orders = await self.data_extractor.extract_order_data(
                order_id=order_id_int,
                date_from=date_from,
                date_to=date_to,
                customer_id=customer_id_int,
                status_id=status_id,
                channel_id=self.channel_id,
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(orders)} orders from BigCommerce")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            raise BigCommerceDataExtractionError(f"Failed to retrieve orders: {e}")
    
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific order by ID.
        
        Args:
            order_id: Order ID
            
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
        Transform BigCommerce order to FIRS-compliant UBL invoice.
        
        Args:
            order_data: BigCommerce order data
            
        Returns:
            UBL BIS 3.0 compliant invoice dictionary
        """
        try:
            # Get store configuration
            store_config = self._store_info or {}
            
            # Get channel configuration if channel_id is available
            channel_config = None
            if order_data.get('channel_id'):
                try:
                    channel_config = await self.rest_client.get_channel(order_data['channel_id'])
                except Exception as e:
                    self.logger.warning(f"Failed to get channel config: {e}")
            
            # Transform order to invoice
            invoice = await self.order_transformer.transform_order_to_invoice(
                order_data, store_config, channel_config
            )
            
            self.logger.info(f"Successfully transformed order {order_data.get('id')} to UBL invoice")
            return invoice
            
        except Exception as e:
            self.logger.error(f"Failed to transform order to invoice: {e}")
            raise BigCommerceTransformationError(f"Order transformation failed: {e}")
    
    async def get_customers(
        self,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve customers from BigCommerce store.
        
        Args:
            customer_id: Specific customer ID
            email: Customer email filter
            limit: Maximum number of customers to retrieve
            
        Returns:
            List of customer dictionaries
        """
        try:
            await self._ensure_connected()
            
            # Convert customer_id to int if provided
            customer_id_int = None
            if customer_id:
                try:
                    customer_id_int = int(customer_id)
                except ValueError:
                    raise BigCommerceDataExtractionError(f"Invalid customer ID format: {customer_id}")
            
            customers = await self.data_extractor.extract_customer_data(
                customer_id=customer_id_int,
                email=email,
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(customers)} customers from BigCommerce")
            return customers
            
        except Exception as e:
            self.logger.error(f"Failed to get customers: {e}")
            raise BigCommerceDataExtractionError(f"Failed to retrieve customers: {e}")
    
    async def get_products(
        self,
        sku: Optional[str] = None,
        name: Optional[str] = None,
        category_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products from BigCommerce store.
        
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
            
            # Convert category_id to int if provided
            category_id_int = None
            if category_id:
                try:
                    category_id_int = int(category_id)
                except ValueError:
                    raise BigCommerceDataExtractionError(f"Invalid category ID format: {category_id}")
            
            products = await self.data_extractor.extract_product_data(
                sku=sku,
                name=name,
                category_id=category_id_int,
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(products)} products from BigCommerce")
            return products
            
        except Exception as e:
            self.logger.error(f"Failed to get products: {e}")
            raise BigCommerceDataExtractionError(f"Failed to retrieve products: {e}")
    
    async def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Process incoming webhook from BigCommerce.
        
        Args:
            event_type: Type of webhook event
            payload: Webhook payload data
            headers: HTTP headers from webhook request
            
        Returns:
            Processing result dictionary
        """
        try:
            self.logger.info(f"Processing BigCommerce webhook: {event_type}")
            
            # Verify webhook signature if secret is configured
            if self.webhook_secret and headers:
                signature = headers.get('X-BC-Webhook-Signature', '')
                if not await self.auth_manager.verify_webhook_signature(payload, signature):
                    return {
                        'success': False,
                        'error': 'Invalid webhook signature',
                        'event_type': event_type
                    }
            
            # Process different event types
            result = None
            
            if event_type.startswith('store/order/'):
                result = await self._process_order_webhook(event_type, payload)
            elif event_type.startswith('store/customer/'):
                result = await self._process_customer_webhook(event_type, payload)
            elif event_type.startswith('store/product/'):
                result = await self._process_product_webhook(event_type, payload)
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
    
    async def _process_order_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process order-related webhook."""
        try:
            order_id = payload.get('order_id') or payload.get('id')
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
            invoice_eligible_statuses = [
                'shipped', 'partially_shipped', 'completed', 'awaiting_fulfillment'
            ]
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
    
    async def _process_customer_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process customer-related webhook."""
        try:
            customer_id = payload.get('customer_id') or payload.get('id')
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
    
    async def _process_product_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process product-related webhook."""
        try:
            product_id = payload.get('product_id') or payload.get('id')
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
    
    async def get_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics and statistics from BigCommerce store.
        
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
                channel_id=self.channel_id
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get analytics: {e}")
            raise BigCommerceDataExtractionError(f"Failed to retrieve analytics: {e}")
    
    async def get_channels(self) -> List[Dict[str, Any]]:
        """
        Get all channels from BigCommerce store.
        
        Returns:
            List of channel dictionaries
        """
        try:
            await self._ensure_connected()
            
            channels = await self.data_extractor.extract_channel_data()
            return channels
            
        except Exception as e:
            self.logger.error(f"Failed to get channels: {e}")
            raise BigCommerceDataExtractionError(f"Failed to retrieve channels: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on BigCommerce connection.
        
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
        """Ensure connection to BigCommerce is established."""
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
        return f"BigCommerceEcommerceConnector(store_hash={self.store_hash}, channel_id={self.channel_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the connector."""
        return (f"BigCommerceEcommerceConnector("
                f"store_hash='{self.store_hash}', "
                f"auth_type='{self.config.get('auth_type')}', "
                f"channel_id={self.channel_id}, "
                f"connected={self._is_connected})")