"""
Base E-commerce Connector
Abstract base class for all e-commerce platform integrations in TaxPoynt eInvoice.

This module provides the foundational interface and common functionality for integrating
with e-commerce platforms including Shopify, WooCommerce, Magento, BigCommerce, and Jumia.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from ..framework.models.base_models import ConnectionConfig
from ..shared.exceptions.integration_exceptions import (
    ConnectionError,
    AuthenticationError,
    DataSyncError,
    ValidationError
)

logger = logging.getLogger(__name__)


class EcommerceOrderStatus(Enum):
    """Standard e-commerce order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    RETURNED = "returned"
    FAILED = "failed"


class EcommercePaymentStatus(Enum):
    """Standard e-commerce payment statuses."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EcommerceOrder:
    """
    Standard e-commerce order data model.
    
    Represents order data extracted from e-commerce platforms in a unified format
    before transformation to UBL invoices.
    """
    
    def __init__(
        self,
        order_id: str,
        order_number: str,
        order_date: datetime,
        order_status: EcommerceOrderStatus,
        payment_status: EcommercePaymentStatus,
        total_amount: float,
        subtotal: float,
        tax_amount: float,
        shipping_amount: float,
        discount_amount: float,
        currency_code: str,
        customer_info: Dict[str, Any],
        billing_address: Dict[str, Any],
        shipping_address: Dict[str, Any],
        line_items: List[Dict[str, Any]],
        payment_info: Dict[str, Any],
        shipping_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.order_id = order_id
        self.order_number = order_number
        self.order_date = order_date
        self.order_status = order_status
        self.payment_status = payment_status
        self.total_amount = total_amount
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.shipping_amount = shipping_amount
        self.discount_amount = discount_amount
        self.currency_code = currency_code
        self.customer_info = customer_info
        self.billing_address = billing_address
        self.shipping_address = shipping_address
        self.line_items = line_items
        self.payment_info = payment_info
        self.shipping_info = shipping_info
        self.metadata = metadata or {}


class EcommerceSyncResult:
    """
    E-commerce synchronization result.
    
    Contains information about the sync operation including success/failure counts,
    processed orders, generated invoices, and any errors encountered.
    """
    
    def __init__(
        self,
        success: bool,
        orders_processed: int,
        orders_successful: int,
        orders_failed: int,
        sync_start_time: datetime,
        sync_end_time: datetime,
        invoices: List[Any] = None,
        errors: List[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.orders_processed = orders_processed
        self.orders_successful = orders_successful
        self.orders_failed = orders_failed
        self.sync_start_time = sync_start_time
        self.sync_end_time = sync_end_time
        self.invoices = invoices or []
        self.errors = errors or []
        self.metadata = metadata or {}


class EcommerceHealthStatus:
    """
    E-commerce connector health status.
    
    Provides information about the connection health, API status,
    and operational capabilities of the e-commerce platform connector.
    """
    
    def __init__(
        self,
        is_healthy: bool,
        status_message: str,
        last_check: datetime,
        details: Optional[Dict[str, Any]] = None
    ):
        self.is_healthy = is_healthy
        self.status_message = status_message
        self.last_check = last_check
        self.details = details or {}


class EcommerceWebhookPayload:
    """
    E-commerce webhook payload.
    
    Standard structure for webhook notifications from e-commerce platforms
    including order updates, payment notifications, and inventory changes.
    """
    
    def __init__(
        self,
        event_type: str,
        event_id: str,
        timestamp: datetime,
        data: Dict[str, Any],
        signature: Optional[str] = None,
        source_platform: Optional[str] = None
    ):
        self.event_type = event_type
        self.event_id = event_id
        self.timestamp = timestamp
        self.data = data
        self.signature = signature
        self.source_platform = source_platform


class BaseEcommerceConnector(ABC):
    """
    Abstract base class for e-commerce platform connectors.
    
    This class defines the standard interface that all e-commerce connectors must implement
    for integration with the TaxPoynt eInvoice platform. It provides common functionality
    and ensures consistency across different e-commerce platform integrations.
    
    Key Features:
    - Order synchronization and data extraction
    - FIRS-compliant invoice transformation
    - Webhook processing for real-time updates
    - Customer and product data management
    - Payment and shipping integration
    - Multi-store and multi-currency support
    - Nigerian tax compliance (7.5% VAT)
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize base e-commerce connector.
        
        Args:
            config: Connection configuration including credentials and settings
        """
        self.config = config
        self.store_id = config.store_id if hasattr(config, 'store_id') else config.merchant_id
        self._is_connected = False
        self._last_sync_time: Optional[datetime] = None
        
        # Default sync configuration
        self.sync_config = {
            'batch_size': 100,
            'max_retries': 3,
            'retry_delay': 5,
            'sync_interval': 300,  # 5 minutes
            'webhook_enabled': True,
            'order_statuses': ['pending', 'processing', 'completed', 'shipped'],
            'include_draft_orders': False,
            'include_cancelled_orders': False
        }
        
        # Update with user-provided sync config
        if hasattr(config, 'sync_config') and config.sync_config:
            self.sync_config.update(config.sync_config)
        
        logger.info(f"Initialized {self.__class__.__name__} for store: {self.store_id}")
    
    # Connection Management
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to e-commerce platform.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from e-commerce platform.
        
        Returns:
            bool: True if disconnection successful
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> EcommerceHealthStatus:
        """
        Test connection health to e-commerce platform.
        
        Returns:
            EcommerceHealthStatus: Connection health information
        """
        pass
    
    # Data Synchronization
    
    @abstractmethod
    async def sync_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_status: Optional[str] = None,
        order_ids: Optional[List[str]] = None
    ) -> EcommerceSyncResult:
        """
        Synchronize orders from e-commerce platform.
        
        Args:
            start_date: Start date for sync
            end_date: End date for sync
            order_status: Filter by order status
            order_ids: Specific order IDs to sync
            
        Returns:
            EcommerceSyncResult: Synchronization results
            
        Raises:
            DataSyncError: If synchronization fails
        """
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[EcommerceOrder]:
        """
        Retrieve specific order from e-commerce platform.
        
        Args:
            order_id: Order ID to retrieve
            
        Returns:
            EcommerceOrder: Order data or None if not found
        """
        pass
    
    # Webhook Processing
    
    @abstractmethod
    async def process_webhook(self, payload: EcommerceWebhookPayload) -> bool:
        """
        Process webhook notification from e-commerce platform.
        
        Args:
            payload: Webhook payload
            
        Returns:
            bool: True if processing successful
        """
        pass
    
    @abstractmethod
    async def validate_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            secret: Webhook secret
            
        Returns:
            bool: True if signature is valid
        """
        pass
    
    # Store and Product Information
    
    @abstractmethod
    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get store/shop information from e-commerce platform.
        
        Returns:
            Dict: Store information including name, address, settings
        """
        pass
    
    async def get_products(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        product_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from e-commerce platform.
        
        Args:
            limit: Maximum number of products to return
            offset: Offset for pagination
            product_ids: Specific product IDs to retrieve
            
        Returns:
            List[Dict]: Product information
        """
        # Default implementation - subclasses can override
        logger.info("get_products not implemented in base class")
        return []
    
    async def get_customers(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        customer_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get customers from e-commerce platform.
        
        Args:
            limit: Maximum number of customers to return
            offset: Offset for pagination
            customer_ids: Specific customer IDs to retrieve
            
        Returns:
            List[Dict]: Customer information
        """
        # Default implementation - subclasses can override
        logger.info("get_customers not implemented in base class")
        return []
    
    # Common Utility Methods
    
    def map_order_status(self, platform_status: str) -> EcommerceOrderStatus:
        """
        Map platform-specific order status to standard status.
        
        Args:
            platform_status: Platform-specific status
            
        Returns:
            EcommerceOrderStatus: Standardized order status
        """
        # Default mapping - subclasses should override for platform-specific mapping
        status_mapping = {
            'pending': EcommerceOrderStatus.PENDING,
            'processing': EcommerceOrderStatus.PROCESSING,
            'shipped': EcommerceOrderStatus.SHIPPED,
            'delivered': EcommerceOrderStatus.DELIVERED,
            'completed': EcommerceOrderStatus.DELIVERED,
            'cancelled': EcommerceOrderStatus.CANCELLED,
            'canceled': EcommerceOrderStatus.CANCELLED,
            'refunded': EcommerceOrderStatus.REFUNDED,
            'returned': EcommerceOrderStatus.RETURNED,
            'failed': EcommerceOrderStatus.FAILED
        }
        
        return status_mapping.get(platform_status.lower(), EcommerceOrderStatus.PENDING)
    
    def map_payment_status(self, platform_status: str) -> EcommercePaymentStatus:
        """
        Map platform-specific payment status to standard status.
        
        Args:
            platform_status: Platform-specific payment status
            
        Returns:
            EcommercePaymentStatus: Standardized payment status
        """
        # Default mapping - subclasses should override for platform-specific mapping
        status_mapping = {
            'pending': EcommercePaymentStatus.PENDING,
            'authorized': EcommercePaymentStatus.AUTHORIZED,
            'paid': EcommercePaymentStatus.PAID,
            'completed': EcommercePaymentStatus.PAID,
            'partially_paid': EcommercePaymentStatus.PARTIALLY_PAID,
            'refunded': EcommercePaymentStatus.REFUNDED,
            'partially_refunded': EcommercePaymentStatus.PARTIALLY_REFUNDED,
            'failed': EcommercePaymentStatus.FAILED,
            'cancelled': EcommercePaymentStatus.CANCELLED,
            'canceled': EcommercePaymentStatus.CANCELLED
        }
        
        return status_mapping.get(platform_status.lower(), EcommercePaymentStatus.PENDING)
    
    def calculate_nigerian_vat(
        self,
        amount: float,
        vat_inclusive: bool = True,
        vat_rate: float = 0.075
    ) -> Dict[str, float]:
        """
        Calculate Nigerian VAT (7.5%) for order amounts.
        
        Args:
            amount: Total amount
            vat_inclusive: Whether VAT is included in amount
            vat_rate: VAT rate (default 7.5%)
            
        Returns:
            Dict: Contains 'subtotal', 'vat_amount', 'total'
        """
        if vat_inclusive:
            # Extract VAT from inclusive amount
            subtotal = amount / (1 + vat_rate)
            vat_amount = amount - subtotal
            total = amount
        else:
            # Add VAT to exclusive amount
            subtotal = amount
            vat_amount = amount * vat_rate
            total = amount + vat_amount
        
        return {
            'subtotal': round(subtotal, 2),
            'vat_amount': round(vat_amount, 2),
            'total': round(total, 2)
        }
    
    def validate_order_data(self, order_data: Dict[str, Any]) -> bool:
        """
        Validate order data for completeness and accuracy.
        
        Args:
            order_data: Order data to validate
            
        Returns:
            bool: True if valid
        """
        required_fields = [
            'order_id', 'order_number', 'total_amount',
            'currency_code', 'customer_info', 'line_items'
        ]
        
        for field in required_fields:
            if field not in order_data or not order_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate amounts
        if order_data['total_amount'] <= 0:
            logger.warning("Invalid total amount")
            return False
        
        # Validate line items
        if not isinstance(order_data['line_items'], list) or len(order_data['line_items']) == 0:
            logger.warning("Invalid or empty line items")
            return False
        
        return True
    
    async def batch_sync_orders(
        self,
        order_ids: List[str],
        batch_size: Optional[int] = None
    ) -> EcommerceSyncResult:
        """
        Synchronize orders in batches for better performance.
        
        Args:
            order_ids: List of order IDs to sync
            batch_size: Size of each batch
            
        Returns:
            EcommerceSyncResult: Batch synchronization results
        """
        if not batch_size:
            batch_size = self.sync_config['batch_size']
        
        total_processed = 0
        total_successful = 0
        total_failed = 0
        all_invoices = []
        all_errors = []
        
        start_time = datetime.utcnow()
        
        # Process orders in batches
        for i in range(0, len(order_ids), batch_size):
            batch_ids = order_ids[i:i + batch_size]
            
            try:
                batch_result = await self.sync_orders(order_ids=batch_ids)
                
                total_processed += batch_result.orders_processed
                total_successful += batch_result.orders_successful
                total_failed += batch_result.orders_failed
                all_invoices.extend(batch_result.invoices)
                all_errors.extend(batch_result.errors)
                
                # Small delay between batches to avoid rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Batch sync failed for orders {batch_ids}: {str(e)}")
                total_failed += len(batch_ids)
                all_errors.append({
                    'batch_ids': batch_ids,
                    'error': str(e)
                })
        
        end_time = datetime.utcnow()
        
        return EcommerceSyncResult(
            success=total_failed == 0,
            orders_processed=total_processed,
            orders_successful=total_successful,
            orders_failed=total_failed,
            sync_start_time=start_time,
            sync_end_time=end_time,
            invoices=all_invoices,
            errors=all_errors,
            metadata={
                'batch_size': batch_size,
                'total_batches': len(range(0, len(order_ids), batch_size)),
                'sync_type': 'batch'
            }
        )
    
    # Properties
    
    @property
    def is_connected(self) -> bool:
        """Check if connector is connected to e-commerce platform."""
        return self._is_connected
    
    @property
    def last_sync_time(self) -> Optional[datetime]:
        """Get last synchronization time."""
        return self._last_sync_time
    
    @property
    @abstractmethod
    def connector_type(self) -> str:
        """Get connector type identifier."""
        pass
    
    # Context Manager Support
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    # Common Event Handlers
    
    async def handle_order_created(self, order_data: Dict[str, Any]) -> bool:
        """
        Handle order created event.
        
        Args:
            order_data: Order creation data
            
        Returns:
            bool: True if handled successfully
        """
        try:
            logger.info(f"Handling order created: {order_data.get('order_id')}")
            
            # Extract and transform order
            order = await self.get_order(order_data.get('order_id'))
            if order:
                # Process order for invoice generation
                # Implementation specific to each platform
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle order created: {str(e)}")
            return False
    
    async def handle_order_updated(self, order_data: Dict[str, Any]) -> bool:
        """
        Handle order updated event.
        
        Args:
            order_data: Order update data
            
        Returns:
            bool: True if handled successfully
        """
        try:
            logger.info(f"Handling order updated: {order_data.get('order_id')}")
            
            # Check if update requires invoice modification
            # Implementation specific to each platform
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle order updated: {str(e)}")
            return False
    
    async def handle_payment_completed(self, payment_data: Dict[str, Any]) -> bool:
        """
        Handle payment completed event.
        
        Args:
            payment_data: Payment completion data
            
        Returns:
            bool: True if handled successfully
        """
        try:
            logger.info(f"Handling payment completed: {payment_data.get('order_id')}")
            
            # Trigger invoice generation if order is complete
            # Implementation specific to each platform
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle payment completed: {str(e)}")
            return False