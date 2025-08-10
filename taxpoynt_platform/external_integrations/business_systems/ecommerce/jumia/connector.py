"""
Jumia E-commerce Connector
Main connector implementation for Jumia marketplace integration.
Implements the BaseEcommerceConnector interface for TaxPoynt eInvoice platform.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from ..base_connector import BaseEcommerceConnector
from .auth import JumiaAuthManager
from .rest_client import JumiaRESTClient
from .data_extractor import JumiaDataExtractor
from .order_transformer import JumiaOrderTransformer
from .exceptions import (
    JumiaConnectionError,
    JumiaAuthenticationError,
    JumiaDataExtractionError,
    JumiaTransformationError
)

logger = logging.getLogger(__name__)


class JumiaEcommerceConnector(BaseEcommerceConnector):
    """
    Jumia E-commerce Marketplace Connector
    
    Comprehensive connector for integrating with Jumia marketplace across Africa.
    Supports regional marketplace operations and seller-specific functionality.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Jumia e-commerce connector.
        
        Args:
            config: Configuration dictionary containing:
                - seller_id: Jumia seller ID (required)
                - api_key: Jumia API key (required)
                - api_secret: Jumia API secret (required)
                - country_code: Country code for marketplace (default: 'NG')
                - marketplace: Specific marketplace identifier
                - webhook_secret: Secret for webhook verification
                - sandbox: Use sandbox environment (default: False)
                - rate_limit: API rate limit settings
        """
        super().__init__(config)
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize components
        self.auth_manager = JumiaAuthManager(config)
        self.rest_client = JumiaRESTClient(config, self.auth_manager)
        self.data_extractor = JumiaDataExtractor(self.rest_client)
        self.order_transformer = JumiaOrderTransformer(config.get('transformer', {}))
        
        # Marketplace configuration
        self.seller_id = config.get('seller_id')
        self.marketplace = self.auth_manager.get_marketplace()
        self.country_code = self.auth_manager.get_country_code()
        self.webhook_secret = config.get('webhook_secret', '')
        
        # Connection state
        self._is_connected = False
        self._last_health_check = None
        self._health_check_interval = timedelta(minutes=10)  # Longer interval for Jumia
        self._seller_profile = None
    
    async def connect(self) -> bool:
        """
        Establish connection to Jumia marketplace.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to Jumia marketplace: {self.marketplace}")
            
            # Authenticate with Jumia
            await self.auth_manager.authenticate()
            
            # Test connection with seller profile
            seller_profile = await self.auth_manager.get_seller_profile()
            if not seller_profile:
                raise JumiaConnectionError("Failed to retrieve seller profile")
            
            self._seller_profile = seller_profile
            self._is_connected = True
            self._last_health_check = datetime.now()
            
            seller_name = seller_profile.get('name', 'Unknown Seller')
            self.logger.info(f"Successfully connected to Jumia marketplace as: {seller_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Jumia: {e}")
            self._is_connected = False
            raise JumiaConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Jumia marketplace.
        
        Returns:
            True if disconnection successful
        """
        try:
            self.logger.info("Disconnecting from Jumia marketplace...")
            
            # Clear authentication
            await self.auth_manager.revoke_authentication()
            
            # Close any persistent connections
            await self.rest_client.close()
            
            self._is_connected = False
            self._seller_profile = None
            self.logger.info("Successfully disconnected from Jumia marketplace")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during disconnection: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Jumia marketplace.
        
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
            
            # Test API connectivity with seller profile
            seller_profile = await self.auth_manager.get_seller_profile()
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                'success': True,
                'seller_info': {
                    'seller_id': self.seller_id,
                    'name': seller_profile.get('name', 'Unknown'),
                    'email': seller_profile.get('email', ''),
                    'status': seller_profile.get('status', ''),
                    'marketplace': self.marketplace,
                    'country_code': self.country_code
                },
                'api_version': 'Seller Center API v3',
                'platform': 'Jumia Marketplace',
                'marketplace': self.marketplace,
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
        Retrieve orders from Jumia marketplace.
        
        Args:
            date_from: Start date for order filtering
            date_to: End date for order filtering
            order_id: Specific order ID
            customer_id: Customer ID filter (not typically used in Jumia)
            status: Order status filter
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of order dictionaries
        """
        try:
            await self._ensure_connected()
            
            orders = await self.data_extractor.extract_order_data(
                order_id=order_id,
                date_from=date_from,
                date_to=date_to,
                status=status,
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(orders)} orders from Jumia")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            raise JumiaDataExtractionError(f"Failed to retrieve orders: {e}")
    
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
        Transform Jumia order to FIRS-compliant UBL invoice.
        
        Args:
            order_data: Jumia order data
            
        Returns:
            UBL BIS 3.0 compliant invoice dictionary
        """
        try:
            # Get seller profile for transformation
            seller_profile = self._seller_profile or await self.auth_manager.get_seller_profile()
            
            # Transform order to invoice
            invoice = await self.order_transformer.transform_order_to_invoice(
                order_data, seller_profile
            )
            
            order_id = order_data.get('id', order_data.get('order_id', 'unknown'))
            self.logger.info(f"Successfully transformed order {order_id} to UBL invoice")
            return invoice
            
        except Exception as e:
            self.logger.error(f"Failed to transform order to invoice: {e}")
            raise JumiaTransformationError(f"Order transformation failed: {e}")
    
    async def get_customers(
        self,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve customers from Jumia marketplace.
        
        Note: Jumia doesn't typically provide direct customer access to sellers.
        Customer information is usually embedded within order data.
        
        Args:
            customer_id: Specific customer ID (not typically available)
            email: Customer email filter (not typically available)
            limit: Maximum number of customers to retrieve
            
        Returns:
            List of customer dictionaries (usually empty for Jumia)
        """
        try:
            await self._ensure_connected()
            
            # Jumia doesn't provide direct customer endpoints for sellers
            # Customer data is typically only available through orders
            self.logger.warning("Direct customer access not available in Jumia Seller API")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get customers: {e}")
            raise JumiaDataExtractionError(f"Failed to retrieve customers: {e}")
    
    async def get_products(
        self,
        sku: Optional[str] = None,
        name: Optional[str] = None,
        category_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products from Jumia marketplace.
        
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
                category_id=category_id,
                limit=limit
            )
            
            self.logger.info(f"Retrieved {len(products)} products from Jumia")
            return products
            
        except Exception as e:
            self.logger.error(f"Failed to get products: {e}")
            raise JumiaDataExtractionError(f"Failed to retrieve products: {e}")
    
    async def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Process incoming webhook from Jumia.
        
        Args:
            event_type: Type of webhook event
            payload: Webhook payload data
            headers: HTTP headers from webhook request
            
        Returns:
            Processing result dictionary
        """
        try:
            self.logger.info(f"Processing Jumia webhook: {event_type}")
            
            # Verify webhook signature if secret is configured
            if self.webhook_secret and headers:
                signature = headers.get('X-Jumia-Signature', '')
                timestamp = headers.get('X-Jumia-Timestamp')
                if not await self.auth_manager.verify_webhook_signature(payload, signature, timestamp):
                    return {
                        'success': False,
                        'error': 'Invalid webhook signature',
                        'event_type': event_type
                    }
            
            # Process different event types
            result = None
            
            if event_type.startswith('order.'):
                result = await self._process_order_webhook(event_type, payload)
            elif event_type.startswith('product.'):
                result = await self._process_product_webhook(event_type, payload)
            elif event_type.startswith('shipment.'):
                result = await self._process_shipment_webhook(event_type, payload)
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
            invoice_eligible_statuses = ['shipped', 'delivered']
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
    
    async def _process_shipment_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process shipment-related webhook."""
        try:
            shipment_id = payload.get('shipment_id') or payload.get('id')
            order_id = payload.get('order_id')
            
            if not shipment_id and not order_id:
                return {
                    'success': False,
                    'error': 'No shipment or order identifier found in webhook payload'
                }
            
            return {
                'success': True,
                'action': 'shipment_processed',
                'shipment_id': shipment_id,
                'order_id': order_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Shipment webhook processing failed: {e}'
            }
    
    async def get_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics and statistics from Jumia marketplace.
        
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
                date_to=date_to
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get analytics: {e}")
            raise JumiaDataExtractionError(f"Failed to retrieve analytics: {e}")
    
    async def get_seller_profile(self) -> Dict[str, Any]:
        """
        Get seller profile information.
        
        Returns:
            Seller profile data dictionary
        """
        try:
            await self._ensure_connected()
            
            profile = await self.data_extractor.extract_seller_profile()
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to get seller profile: {e}")
            raise JumiaDataExtractionError(f"Failed to retrieve seller profile: {e}")
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories from Jumia marketplace.
        
        Returns:
            List of category dictionaries
        """
        try:
            await self._ensure_connected()
            
            categories = await self.data_extractor.extract_category_data()
            return categories
            
        except Exception as e:
            self.logger.error(f"Failed to get categories: {e}")
            raise JumiaDataExtractionError(f"Failed to retrieve categories: {e}")
    
    async def get_inventory(
        self,
        sku: Optional[str] = None,
        low_stock_threshold: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get inventory information from Jumia marketplace.
        
        Args:
            sku: Specific product SKU
            low_stock_threshold: Threshold for low stock filtering
            limit: Maximum number of inventory items to retrieve
            
        Returns:
            List of inventory data dictionaries
        """
        try:
            await self._ensure_connected()
            
            inventory = await self.data_extractor.extract_inventory_data(
                sku=sku,
                low_stock_threshold=low_stock_threshold,
                limit=limit
            )
            
            return inventory
            
        except Exception as e:
            self.logger.error(f"Failed to get inventory: {e}")
            raise JumiaDataExtractionError(f"Failed to retrieve inventory: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Jumia connection.
        
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
        """Ensure connection to Jumia is established."""
        if not self._is_connected:
            await self.connect()
        
        # Perform periodic health checks
        if (not self._last_health_check or 
            datetime.now() - self._last_health_check > self._health_check_interval):
            health = await self.health_check()
            if health['status'] != 'healthy':
                await self.connect()
    
    def get_marketplace(self) -> str:
        """Get the current marketplace identifier."""
        return self.marketplace
    
    def get_country_code(self) -> str:
        """Get the current country code."""
        return self.country_code
    
    def get_seller_id(self) -> str:
        """Get the current seller ID."""
        return self.seller_id
    
    def __str__(self) -> str:
        """String representation of the connector."""
        return f"JumiaEcommerceConnector(seller_id={self.seller_id}, marketplace={self.marketplace})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the connector."""
        return (f"JumiaEcommerceConnector("
                f"seller_id='{self.seller_id}', "
                f"marketplace='{self.marketplace}', "
                f"country_code='{self.country_code}', "
                f"connected={self._is_connected})")