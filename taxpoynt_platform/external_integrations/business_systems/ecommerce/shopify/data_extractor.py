"""
Shopify E-commerce Data Extraction Module
Extracts order and customer data from Shopify REST API.
Handles order processing, customer management, and product synchronization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

from ....connector_framework.base_ecommerce_connector import (
    EcommerceOrder,
    EcommerceOrderStatus,
    EcommercePaymentStatus
)
from ....shared.exceptions.integration_exceptions import DataExtractionError
from .rest_client import ShopifyRestClient
from .exceptions import (
    ShopifyDataExtractionError,
    ShopifyAPIError,
    create_shopify_exception
)

logger = logging.getLogger(__name__)


class ShopifyDataExtractor:
    """
    Shopify E-commerce Data Extraction Service
    
    Handles extraction and parsing of order data from Shopify e-commerce platform
    including order management, customer data, and product information.
    """
    
    def __init__(self, rest_client: ShopifyRestClient):
        """
        Initialize Shopify data extractor.
        
        Args:
            rest_client: Shopify REST API client
        """
        self.rest_client = rest_client
        self.shop_name = rest_client.shop_name
        
        # Nigerian market configuration
        self.nigerian_config = {
            'currency': 'NGN',
            'vat_rate': 0.075,  # 7.5% VAT
            'default_tin': '00000000-0001',
            'vat_inclusive': True
        }
        
        logger.info("Initialized Shopify data extractor")
    
    async def extract_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_status: Optional[str] = None,
        financial_status: Optional[str] = None,
        fulfillment_status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[EcommerceOrder]:
        """
        Extract orders from Shopify store.
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            order_status: Filter by order status
            financial_status: Filter by financial status
            fulfillment_status: Filter by fulfillment status
            limit: Maximum number of orders to extract
            
        Returns:
            List[EcommerceOrder]: Extracted orders
        """
        try:
            logger.info("Starting Shopify order extraction...")
            
            # Set default date range
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            all_orders = []
            
            if limit and limit <= 250:
                # Single request for small limits
                shopify_orders = await self.rest_client.get_orders(
                    limit=limit,
                    created_at_min=start_date,
                    created_at_max=end_date,
                    status=order_status,
                    financial_status=financial_status,
                    fulfillment_status=fulfillment_status
                )
                
                for order_data in shopify_orders:
                    try:
                        order = await self._parse_shopify_order(order_data)
                        if order:
                            all_orders.append(order)
                    except Exception as e:
                        logger.error(f"Failed to parse order {order_data.get('id')}: {str(e)}")
                        continue
            else:
                # Use pagination for large datasets
                extracted_count = 0
                async for order_data in self.rest_client.get_all_orders_paginated(
                    created_at_min=start_date,
                    created_at_max=end_date,
                    status=order_status
                ):
                    try:
                        # Apply additional filters
                        if financial_status and order_data.get('financial_status') != financial_status:
                            continue
                        if fulfillment_status and order_data.get('fulfillment_status') != fulfillment_status:
                            continue
                        
                        order = await self._parse_shopify_order(order_data)
                        if order:
                            all_orders.append(order)
                            extracted_count += 1
                            
                            # Check limit
                            if limit and extracted_count >= limit:
                                break
                                
                    except Exception as e:
                        logger.error(f"Failed to parse order {order_data.get('id')}: {str(e)}")
                        continue
            
            logger.info(f"Extracted {len(all_orders)} orders from Shopify")
            return all_orders
            
        except Exception as e:
            logger.error(f"Shopify order extraction failed: {str(e)}")
            raise ShopifyDataExtractionError(f"Extraction failed: {str(e)}")
    
    async def get_single_order(self, order_id: str) -> Optional[EcommerceOrder]:
        """
        Extract a single order by ID.
        
        Args:
            order_id: Shopify order ID
            
        Returns:
            EcommerceOrder: Order data or None if not found
        """
        try:
            logger.info(f"Extracting single Shopify order: {order_id}")
            
            # Get order details
            order_data = await self.rest_client.get_order(order_id)
            
            if not order_data:
                logger.warning(f"Shopify order not found: {order_id}")
                return None
            
            # Parse order
            order = await self._parse_shopify_order(order_data)
            
            logger.info(f"Successfully extracted Shopify order: {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to extract order {order_id}: {str(e)}")
            return None
    
    async def extract_order_from_webhook(self, webhook_payload: Dict[str, Any]) -> Optional[EcommerceOrder]:
        """
        Extract order from webhook payload.
        
        Args:
            webhook_payload: Shopify webhook data
            
        Returns:
            EcommerceOrder: Extracted order or None
        """
        try:
            logger.info("Extracting order from Shopify webhook")
            
            # Shopify webhook payloads contain the full order object
            order_data = webhook_payload
            
            if not order_data:
                logger.warning("No order data in webhook payload")
                return None
            
            # Parse webhook order
            order = await self._parse_webhook_order(order_data)
            
            if order:
                logger.info(f"Extracted order from webhook: {order.order_id}")
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to extract webhook order: {str(e)}")
            return None
    
    async def _parse_shopify_order(self, data: Dict[str, Any]) -> Optional[EcommerceOrder]:
        """Parse a standard Shopify order."""
        try:
            # Basic order info
            order_id = str(data.get('id'))
            if not order_id:
                logger.warning("Order missing ID")
                return None
            
            order_number = data.get('order_number') or data.get('name', '')
            
            # Parse order date
            created_at_str = data.get('created_at')
            if created_at_str:
                try:
                    order_date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except:
                    order_date = datetime.utcnow()
            else:
                order_date = datetime.utcnow()
            
            # Parse amounts
            total_price = Decimal(str(data.get('total_price', 0)))
            subtotal_price = Decimal(str(data.get('subtotal_price', 0)))
            total_tax = Decimal(str(data.get('total_tax', 0)))
            total_shipping = Decimal(str(data.get('total_shipping_price_set', {}).get('shop_money', {}).get('amount', 0)))
            total_discounts = Decimal(str(data.get('total_discounts', 0)))
            
            currency_code = data.get('currency') or data.get('shop_money', {}).get('currency_code', 'USD')
            
            # Order status mapping
            order_status = self._map_order_status(data.get('financial_status', 'pending'))
            payment_status = self._map_payment_status(data.get('financial_status', 'pending'))
            
            # Customer information
            customer_data = data.get('customer', {})
            customer_info = {
                'id': customer_data.get('id'),
                'email': customer_data.get('email', ''),
                'first_name': customer_data.get('first_name', ''),
                'last_name': customer_data.get('last_name', ''),
                'phone': customer_data.get('phone', ''),
                'total_orders': customer_data.get('orders_count', 0),
                'created_at': customer_data.get('created_at'),
                'tags': customer_data.get('tags', ''),
                'tin': self.nigerian_config['default_tin']  # Default for Nigerian compliance
            }
            
            # Billing address
            billing_address_data = data.get('billing_address', {})
            billing_address = {
                'first_name': billing_address_data.get('first_name', ''),
                'last_name': billing_address_data.get('last_name', ''),
                'address1': billing_address_data.get('address1', ''),
                'address2': billing_address_data.get('address2', ''),
                'city': billing_address_data.get('city', ''),
                'province': billing_address_data.get('province', ''),
                'country': billing_address_data.get('country', ''),
                'zip': billing_address_data.get('zip', ''),
                'phone': billing_address_data.get('phone', '')
            }
            
            # Shipping address
            shipping_address_data = data.get('shipping_address', {})
            shipping_address = {
                'first_name': shipping_address_data.get('first_name', ''),
                'last_name': shipping_address_data.get('last_name', ''),
                'address1': shipping_address_data.get('address1', ''),
                'address2': shipping_address_data.get('address2', ''),
                'city': shipping_address_data.get('city', ''),
                'province': shipping_address_data.get('province', ''),
                'country': shipping_address_data.get('country', ''),
                'zip': shipping_address_data.get('zip', ''),
                'phone': shipping_address_data.get('phone', '')
            }
            
            # Line items
            line_items = []
            for item_data in data.get('line_items', []):
                line_item = {
                    'id': item_data.get('id'),
                    'product_id': item_data.get('product_id'),
                    'variant_id': item_data.get('variant_id'),
                    'title': item_data.get('title', ''),
                    'variant_title': item_data.get('variant_title', ''),
                    'sku': item_data.get('sku', ''),
                    'quantity': int(item_data.get('quantity', 1)),
                    'price': float(item_data.get('price', 0)),
                    'total_discount': float(item_data.get('total_discount', 0)),
                    'tax_lines': item_data.get('tax_lines', []),
                    'vendor': item_data.get('vendor', ''),
                    'product_type': item_data.get('product_type', ''),
                    'gift_card': item_data.get('gift_card', False),
                    'taxable': item_data.get('taxable', True),
                    'fulfillment_service': item_data.get('fulfillment_service', 'manual'),
                    'fulfillment_status': item_data.get('fulfillment_status'),
                    'properties': item_data.get('properties', [])
                }
                line_items.append(line_item)
            
            # Payment information
            payment_gateway_names = data.get('payment_gateway_names', [])
            processing_method = data.get('processing_method', '')
            
            payment_info = {
                'gateway_names': payment_gateway_names,
                'processing_method': processing_method,
                'checkout_token': data.get('checkout_token'),
                'payment_reference': data.get('reference') or order_number,
                'transaction_id': None  # Will be populated from transactions if needed
            }
            
            # Shipping information
            shipping_lines = data.get('shipping_lines', [])
            shipping_info = {
                'shipping_lines': shipping_lines,
                'total_shipping': float(total_shipping),
                'fulfillment_status': data.get('fulfillment_status'),
                'fulfillments': data.get('fulfillments', [])
            }
            
            # Additional metadata
            metadata = {
                'shopify_order_id': order_id,
                'shopify_order_number': order_number,
                'shopify_order_status_url': data.get('order_status_url'),
                'shopify_tags': data.get('tags', ''),
                'shopify_note': data.get('note', ''),
                'shopify_source_name': data.get('source_name', ''),
                'shopify_referring_site': data.get('referring_site', ''),
                'shopify_landing_site': data.get('landing_site', ''),
                'shopify_cancelled_at': data.get('cancelled_at'),
                'shopify_cancel_reason': data.get('cancel_reason'),
                'shopify_closed_at': data.get('closed_at'),
                'shopify_processed_at': data.get('processed_at'),
                'shopify_updated_at': data.get('updated_at'),
                'shopify_app_id': data.get('app_id'),
                'shopify_location_id': data.get('location_id'),
                'shop_name': self.shop_name,
                'extraction_timestamp': datetime.utcnow().isoformat(),
                'original_data': data
            }
            
            return EcommerceOrder(
                order_id=order_id,
                order_number=order_number,
                order_date=order_date,
                order_status=order_status,
                payment_status=payment_status,
                total_amount=float(total_price),
                subtotal=float(subtotal_price),
                tax_amount=float(total_tax),
                shipping_amount=float(total_shipping),
                discount_amount=float(total_discounts),
                currency_code=currency_code,
                customer_info=customer_info,
                billing_address=billing_address,
                shipping_address=shipping_address,
                line_items=line_items,
                payment_info=payment_info,
                shipping_info=shipping_info,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Shopify order: {str(e)}")
            return None
    
    async def _parse_webhook_order(self, data: Dict[str, Any]) -> Optional[EcommerceOrder]:
        """Parse order from webhook payload."""
        # Webhook orders have the same structure as API orders
        order = await self._parse_shopify_order(data)
        
        if order and order.metadata:
            # Add webhook-specific metadata
            order.metadata.update({
                'source': 'webhook',
                'real_time_processing': True,
                'webhook_processed_at': datetime.utcnow().isoformat()
            })
        
        return order
    
    def _map_order_status(self, shopify_status: str) -> EcommerceOrderStatus:
        """Map Shopify order status to standard status."""
        status_mapping = {
            'pending': EcommerceOrderStatus.PENDING,
            'authorized': EcommerceOrderStatus.PROCESSING,
            'partially_paid': EcommerceOrderStatus.PROCESSING,
            'paid': EcommerceOrderStatus.PROCESSING,
            'partially_refunded': EcommerceOrderStatus.PROCESSING,
            'refunded': EcommerceOrderStatus.REFUNDED,
            'voided': EcommerceOrderStatus.CANCELLED,
            'cancelled': EcommerceOrderStatus.CANCELLED,
            'fulfilled': EcommerceOrderStatus.DELIVERED,
            'shipped': EcommerceOrderStatus.SHIPPED,
            'delivered': EcommerceOrderStatus.DELIVERED
        }
        
        return status_mapping.get(shopify_status.lower(), EcommerceOrderStatus.PENDING)
    
    def _map_payment_status(self, shopify_financial_status: str) -> EcommercePaymentStatus:
        """Map Shopify financial status to standard payment status."""
        status_mapping = {
            'pending': EcommercePaymentStatus.PENDING,
            'authorized': EcommercePaymentStatus.AUTHORIZED,
            'partially_paid': EcommercePaymentStatus.PARTIALLY_PAID,
            'paid': EcommercePaymentStatus.PAID,
            'partially_refunded': EcommercePaymentStatus.PARTIALLY_REFUNDED,
            'refunded': EcommercePaymentStatus.REFUNDED,
            'voided': EcommercePaymentStatus.CANCELLED,
            'cancelled': EcommercePaymentStatus.CANCELLED,
            'failed': EcommercePaymentStatus.FAILED
        }
        
        return status_mapping.get(shopify_financial_status.lower(), EcommercePaymentStatus.PENDING)
    
    # Customer extraction methods
    
    async def extract_customers(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract customers from Shopify store.
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            limit: Maximum number of customers to extract
            
        Returns:
            List[Dict]: Extracted customers
        """
        try:
            logger.info("Starting Shopify customer extraction...")
            
            customers = await self.rest_client.get_customers(
                limit=limit or 250,
                created_at_min=start_date,
                created_at_max=end_date
            )
            
            logger.info(f"Extracted {len(customers)} customers from Shopify")
            return customers
            
        except Exception as e:
            logger.error(f"Shopify customer extraction failed: {str(e)}")
            raise ShopifyDataExtractionError(f"Customer extraction failed: {str(e)}")
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract a single customer by ID.
        
        Args:
            customer_id: Shopify customer ID
            
        Returns:
            Dict: Customer data or None if not found
        """
        try:
            customer_data = await self.rest_client.get_customer(customer_id)
            
            if customer_data:
                logger.info(f"Retrieved Shopify customer: {customer_id}")
            
            return customer_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {str(e)}")
            return None
    
    # Product extraction methods
    
    async def extract_products(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract products from Shopify store.
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            limit: Maximum number of products to extract
            
        Returns:
            List[Dict]: Extracted products
        """
        try:
            logger.info("Starting Shopify product extraction...")
            
            products = await self.rest_client.get_products(
                limit=limit or 250,
                created_at_min=start_date,
                created_at_max=end_date
            )
            
            logger.info(f"Extracted {len(products)} products from Shopify")
            return products
            
        except Exception as e:
            logger.error(f"Shopify product extraction failed: {str(e)}")
            raise ShopifyDataExtractionError(f"Product extraction failed: {str(e)}")
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract a single product by ID.
        
        Args:
            product_id: Shopify product ID
            
        Returns:
            Dict: Product data or None if not found
        """
        try:
            product_data = await self.rest_client.get_product(product_id)
            
            if product_data:
                logger.info(f"Retrieved Shopify product: {product_id}")
            
            return product_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve product {product_id}: {str(e)}")
            return None
    
    # Batch operations
    
    async def batch_extract_orders(self, order_ids: List[str]) -> List[EcommerceOrder]:
        """
        Extract multiple orders by IDs.
        
        Args:
            order_ids: List of Shopify order IDs
            
        Returns:
            List[EcommerceOrder]: Extracted orders
        """
        try:
            logger.info(f"Extracting batch of {len(order_ids)} Shopify orders")
            
            # Use REST client batch method
            orders_data = await self.rest_client.batch_get_orders(order_ids)
            
            orders = []
            for data in orders_data:
                try:
                    order = await self._parse_shopify_order(data)
                    if order:
                        orders.append(order)
                except Exception as e:
                    logger.error(f"Failed to parse batch order: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(orders)} orders from batch")
            return orders
            
        except Exception as e:
            logger.error(f"Batch order extraction failed: {str(e)}")
            raise ShopifyDataExtractionError(f"Batch extraction failed: {str(e)}")
    
    # Store information
    
    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get store information from Shopify.
        
        Returns:
            Dict: Store information
        """
        try:
            store_info = await self.rest_client.get_shop_info()
            logger.info("Retrieved Shopify store information")
            return store_info
            
        except Exception as e:
            logger.error(f"Failed to get store info: {str(e)}")
            return {}
    
    # Analytics and statistics
    
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
            # Extract orders for the period
            orders = await self.extract_orders(
                start_date=start_date,
                end_date=end_date
            )
            
            if not orders:
                return {
                    'total_orders': 0,
                    'total_revenue': 0,
                    'average_order_value': 0,
                    'total_tax': 0,
                    'currency': 'USD'
                }
            
            # Calculate statistics
            total_orders = len(orders)
            total_revenue = sum(order.total_amount for order in orders)
            total_tax = sum(order.tax_amount for order in orders)
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0
            currency = orders[0].currency_code if orders else 'USD'
            
            # Status breakdown
            status_counts = {}
            payment_status_counts = {}
            
            for order in orders:
                status = order.order_status.value
                payment_status = order.payment_status.value
                
                status_counts[status] = status_counts.get(status, 0) + 1
                payment_status_counts[payment_status] = payment_status_counts.get(payment_status, 0) + 1
            
            statistics = {
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'average_order_value': round(average_order_value, 2),
                'total_tax': round(total_tax, 2),
                'currency': currency,
                'period': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                },
                'order_status_breakdown': status_counts,
                'payment_status_breakdown': payment_status_counts
            }
            
            logger.info(f"Generated Shopify order statistics: {total_orders} orders, {total_revenue} {currency}")
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to generate order statistics: {str(e)}")
            return {}