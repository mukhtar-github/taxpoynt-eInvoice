"""
WooCommerce E-commerce Data Extraction Module
Extracts order and customer data from WooCommerce REST API.
Handles WordPress/WooCommerce specific data structures and relationships.
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
from .rest_client import WooCommerceRestClient
from .exceptions import (
    WooCommerceDataExtractionError,
    WooCommerceAPIError,
    create_woocommerce_exception
)

logger = logging.getLogger(__name__)


class WooCommerceDataExtractor:
    """
    WooCommerce E-commerce Data Extraction Service
    
    Handles extraction and parsing of order data from WooCommerce platform
    including WordPress integration, WooCommerce extensions, and plugin compatibility.
    """
    
    def __init__(self, rest_client: WooCommerceRestClient):
        """
        Initialize WooCommerce data extractor.
        
        Args:
            rest_client: WooCommerce REST API client
        """
        self.rest_client = rest_client
        self.store_url = rest_client.store_url
        
        # Nigerian market configuration
        self.nigerian_config = {
            'currency': 'NGN',
            'vat_rate': 0.075,  # 7.5% VAT
            'default_tin': '00000000-0001',
            'vat_inclusive': True
        }
        
        logger.info("Initialized WooCommerce data extractor")
    
    async def extract_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_status: Optional[str] = None,
        customer_id: Optional[int] = None,
        product_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[EcommerceOrder]:
        """
        Extract orders from WooCommerce store.
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            order_status: Filter by order status
            customer_id: Filter by customer ID
            product_id: Filter by product ID
            limit: Maximum number of orders to extract
            
        Returns:
            List[EcommerceOrder]: Extracted orders
        """
        try:
            logger.info("Starting WooCommerce order extraction...")
            
            # Format dates for WooCommerce API (ISO 8601)
            after = start_date.isoformat() if start_date else None
            before = end_date.isoformat() if end_date else None
            
            all_orders = []
            
            if limit and limit <= 100:
                # Single request for small limits
                wc_orders = await self.rest_client.get_orders(
                    per_page=limit,
                    after=after,
                    before=before,
                    status=order_status,
                    customer=customer_id,
                    product=product_id
                )
                
                for order_data in wc_orders:
                    try:
                        order = await self._parse_woocommerce_order(order_data)
                        if order:
                            all_orders.append(order)
                    except Exception as e:
                        logger.error(f"Failed to parse order {order_data.get('id')}: {str(e)}")
                        continue
            else:
                # Use pagination for large datasets
                extracted_count = 0
                async for order_data in self.rest_client.get_all_orders_paginated(
                    after=after,
                    before=before,
                    status=order_status
                ):
                    try:
                        # Apply additional filters
                        if customer_id and order_data.get('customer_id') != customer_id:
                            continue
                        
                        order = await self._parse_woocommerce_order(order_data)
                        if order:
                            all_orders.append(order)
                            extracted_count += 1
                            
                            # Check limit
                            if limit and extracted_count >= limit:
                                break
                                
                    except Exception as e:
                        logger.error(f"Failed to parse order {order_data.get('id')}: {str(e)}")
                        continue
            
            logger.info(f"Extracted {len(all_orders)} orders from WooCommerce")
            return all_orders
            
        except Exception as e:
            logger.error(f"WooCommerce order extraction failed: {str(e)}")
            raise WooCommerceDataExtractionError(f"Extraction failed: {str(e)}")
    
    async def get_single_order(self, order_id: str) -> Optional[EcommerceOrder]:
        """
        Extract a single order by ID.
        
        Args:
            order_id: WooCommerce order ID
            
        Returns:
            EcommerceOrder: Order data or None if not found
        """
        try:
            logger.info(f"Extracting single WooCommerce order: {order_id}")
            
            # Get order details
            order_data = await self.rest_client.get_order(order_id)
            
            if not order_data:
                logger.warning(f"WooCommerce order not found: {order_id}")
                return None
            
            # Parse order
            order = await self._parse_woocommerce_order(order_data)
            
            logger.info(f"Successfully extracted WooCommerce order: {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to extract order {order_id}: {str(e)}")
            return None
    
    async def extract_order_from_webhook(self, webhook_payload: Dict[str, Any]) -> Optional[EcommerceOrder]:
        """
        Extract order from webhook payload.
        
        Args:
            webhook_payload: WooCommerce webhook data
            
        Returns:
            EcommerceOrder: Extracted order or None
        """
        try:
            logger.info("Extracting order from WooCommerce webhook")
            
            # WooCommerce webhook payloads contain the full order object
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
    
    async def _parse_woocommerce_order(self, data: Dict[str, Any]) -> Optional[EcommerceOrder]:
        """Parse a standard WooCommerce order."""
        try:
            # Basic order info
            order_id = str(data.get('id'))
            if not order_id:
                logger.warning("Order missing ID")
                return None
            
            order_number = data.get('number') or order_id
            
            # Parse order date
            date_created_str = data.get('date_created')
            if date_created_str:
                try:
                    # WooCommerce uses ISO 8601 format
                    order_date = datetime.fromisoformat(date_created_str.replace('Z', '+00:00'))
                except:
                    order_date = datetime.utcnow()
            else:
                order_date = datetime.utcnow()
            
            # Parse amounts (WooCommerce stores as strings)
            total = Decimal(str(data.get('total', 0)))
            total_tax = Decimal(str(data.get('total_tax', 0)))
            shipping_total = Decimal(str(data.get('shipping_total', 0)))
            discount_total = Decimal(str(data.get('discount_total', 0)))
            
            # Calculate subtotal (total - tax - shipping)
            subtotal = total - total_tax - shipping_total
            
            currency_code = data.get('currency', 'USD')
            
            # Order status mapping
            wc_status = data.get('status', 'pending')
            order_status = self._map_order_status(wc_status)
            payment_status = self._map_payment_status(wc_status)
            
            # Customer information
            customer_info = {
                'id': data.get('customer_id'),
                'email': data.get('billing', {}).get('email', ''),
                'first_name': data.get('billing', {}).get('first_name', ''),
                'last_name': data.get('billing', {}).get('last_name', ''),
                'phone': data.get('billing', {}).get('phone', ''),
                'company': data.get('billing', {}).get('company', ''),
                'username': data.get('customer_user_agent', ''),
                'note': data.get('customer_note', ''),
                'tin': self.nigerian_config['default_tin']  # Default for Nigerian compliance
            }
            
            # Billing address
            billing_data = data.get('billing', {})
            billing_address = {
                'first_name': billing_data.get('first_name', ''),
                'last_name': billing_data.get('last_name', ''),
                'company': billing_data.get('company', ''),
                'address1': billing_data.get('address_1', ''),
                'address2': billing_data.get('address_2', ''),
                'city': billing_data.get('city', ''),
                'state': billing_data.get('state', ''),
                'postcode': billing_data.get('postcode', ''),
                'country': billing_data.get('country', ''),
                'email': billing_data.get('email', ''),
                'phone': billing_data.get('phone', '')
            }
            
            # Shipping address
            shipping_data = data.get('shipping', {})
            shipping_address = {
                'first_name': shipping_data.get('first_name', ''),
                'last_name': shipping_data.get('last_name', ''),
                'company': shipping_data.get('company', ''),
                'address1': shipping_data.get('address_1', ''),
                'address2': shipping_data.get('address_2', ''),
                'city': shipping_data.get('city', ''),
                'state': shipping_data.get('state', ''),
                'postcode': shipping_data.get('postcode', ''),
                'country': shipping_data.get('country', ''),
                'phone': shipping_data.get('phone', '') if shipping_data.get('phone') else billing_data.get('phone', '')
            }
            
            # Line items
            line_items = []
            for item_data in data.get('line_items', []):
                line_item = {
                    'id': item_data.get('id'),
                    'name': item_data.get('name', ''),
                    'product_id': item_data.get('product_id'),
                    'variation_id': item_data.get('variation_id'),
                    'quantity': int(item_data.get('quantity', 1)),
                    'price': float(item_data.get('price', 0)),
                    'total': float(item_data.get('total', 0)),
                    'subtotal': float(item_data.get('subtotal', 0)),
                    'total_tax': float(item_data.get('total_tax', 0)),
                    'subtotal_tax': float(item_data.get('subtotal_tax', 0)),
                    'sku': item_data.get('sku', ''),
                    'meta_data': item_data.get('meta_data', []),
                    'taxes': item_data.get('taxes', []),
                    'parent_name': item_data.get('parent_name', ''),
                    'bundled_by': item_data.get('bundled_by', ''),
                    'bundled_items': item_data.get('bundled_items', [])
                }
                line_items.append(line_item)
            
            # Payment information
            payment_method = data.get('payment_method', '')
            payment_method_title = data.get('payment_method_title', '')
            transaction_id = data.get('transaction_id', '')
            
            payment_info = {
                'payment_method': payment_method,
                'payment_method_title': payment_method_title,
                'transaction_id': transaction_id,
                'payment_reference': transaction_id or order_number,
                'date_paid': data.get('date_paid'),
                'date_paid_gmt': data.get('date_paid_gmt')
            }
            
            # Shipping information
            shipping_lines = data.get('shipping_lines', [])
            shipping_info = {
                'shipping_lines': shipping_lines,
                'total_shipping': float(shipping_total),
                'shipping_method': shipping_lines[0].get('method_title', '') if shipping_lines else '',
                'shipping_method_id': shipping_lines[0].get('method_id', '') if shipping_lines else '',
                'date_completed': data.get('date_completed'),
                'date_completed_gmt': data.get('date_completed_gmt')
            }
            
            # Additional metadata
            metadata = {
                'woocommerce_order_id': order_id,
                'woocommerce_order_key': data.get('order_key', ''),
                'woocommerce_status': wc_status,
                'woocommerce_version': data.get('version', ''),
                'woocommerce_created_via': data.get('created_via', ''),
                'woocommerce_parent_id': data.get('parent_id'),
                'woocommerce_customer_ip': data.get('customer_ip_address', ''),
                'woocommerce_customer_user_agent': data.get('customer_user_agent', ''),
                'woocommerce_refunds': data.get('refunds', []),
                'woocommerce_fee_lines': data.get('fee_lines', []),
                'woocommerce_coupon_lines': data.get('coupon_lines', []),
                'woocommerce_tax_lines': data.get('tax_lines', []),
                'woocommerce_meta_data': data.get('meta_data', []),
                'store_url': self.store_url,
                'extraction_timestamp': datetime.utcnow().isoformat(),
                'original_data': data
            }
            
            return EcommerceOrder(
                order_id=order_id,
                order_number=order_number,
                order_date=order_date,
                order_status=order_status,
                payment_status=payment_status,
                total_amount=float(total),
                subtotal=float(subtotal),
                tax_amount=float(total_tax),
                shipping_amount=float(shipping_total),
                discount_amount=float(discount_total),
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
            logger.error(f"Failed to parse WooCommerce order: {str(e)}")
            return None
    
    async def _parse_webhook_order(self, data: Dict[str, Any]) -> Optional[EcommerceOrder]:
        """Parse order from webhook payload."""
        # Webhook orders have the same structure as API orders
        order = await self._parse_woocommerce_order(data)
        
        if order and order.metadata:
            # Add webhook-specific metadata
            order.metadata.update({
                'source': 'webhook',
                'real_time_processing': True,
                'webhook_processed_at': datetime.utcnow().isoformat()
            })
        
        return order
    
    def _map_order_status(self, wc_status: str) -> EcommerceOrderStatus:
        """Map WooCommerce order status to standard status."""
        status_mapping = {
            'pending': EcommerceOrderStatus.PENDING,
            'processing': EcommerceOrderStatus.PROCESSING,
            'on-hold': EcommerceOrderStatus.PENDING,
            'completed': EcommerceOrderStatus.DELIVERED,
            'cancelled': EcommerceOrderStatus.CANCELLED,
            'refunded': EcommerceOrderStatus.REFUNDED,
            'failed': EcommerceOrderStatus.FAILED,
            'trash': EcommerceOrderStatus.CANCELLED
        }
        
        return status_mapping.get(wc_status.lower(), EcommerceOrderStatus.PENDING)
    
    def _map_payment_status(self, wc_status: str) -> EcommercePaymentStatus:
        """Map WooCommerce order status to payment status."""
        # WooCommerce doesn't have separate payment status, derive from order status
        status_mapping = {
            'pending': EcommercePaymentStatus.PENDING,
            'processing': EcommercePaymentStatus.PAID,
            'on-hold': EcommercePaymentStatus.AUTHORIZED,
            'completed': EcommercePaymentStatus.PAID,
            'cancelled': EcommercePaymentStatus.CANCELLED,
            'refunded': EcommercePaymentStatus.REFUNDED,
            'failed': EcommercePaymentStatus.FAILED,
            'trash': EcommercePaymentStatus.CANCELLED
        }
        
        return status_mapping.get(wc_status.lower(), EcommercePaymentStatus.PENDING)
    
    # Customer extraction methods
    
    async def extract_customers(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract customers from WooCommerce store.
        
        Args:
            start_date: Start date for extraction (not directly supported by WooCommerce API)
            end_date: End date for extraction (not directly supported by WooCommerce API)
            limit: Maximum number of customers to extract
            
        Returns:
            List[Dict]: Extracted customers
        """
        try:
            logger.info("Starting WooCommerce customer extraction...")
            
            customers = await self.rest_client.get_customers(
                per_page=limit or 100
            )
            
            logger.info(f"Extracted {len(customers)} customers from WooCommerce")
            return customers
            
        except Exception as e:
            logger.error(f"WooCommerce customer extraction failed: {str(e)}")
            raise WooCommerceDataExtractionError(f"Customer extraction failed: {str(e)}")
    
    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract a single customer by ID.
        
        Args:
            customer_id: WooCommerce customer ID
            
        Returns:
            Dict: Customer data or None if not found
        """
        try:
            customer_data = await self.rest_client.get_customer(customer_id)
            
            if customer_data:
                logger.info(f"Retrieved WooCommerce customer: {customer_id}")
            
            return customer_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {str(e)}")
            return None
    
    # Product extraction methods
    
    async def extract_products(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        status: Optional[str] = 'publish'
    ) -> List[Dict[str, Any]]:
        """
        Extract products from WooCommerce store.
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            limit: Maximum number of products to extract
            status: Product status filter
            
        Returns:
            List[Dict]: Extracted products
        """
        try:
            logger.info("Starting WooCommerce product extraction...")
            
            # Format dates for WooCommerce API (ISO 8601)
            after = start_date.isoformat() if start_date else None
            before = end_date.isoformat() if end_date else None
            
            products = await self.rest_client.get_products(
                per_page=limit or 100,
                after=after,
                before=before,
                status=status
            )
            
            logger.info(f"Extracted {len(products)} products from WooCommerce")
            return products
            
        except Exception as e:
            logger.error(f"WooCommerce product extraction failed: {str(e)}")
            raise WooCommerceDataExtractionError(f"Product extraction failed: {str(e)}")
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract a single product by ID.
        
        Args:
            product_id: WooCommerce product ID
            
        Returns:
            Dict: Product data or None if not found
        """
        try:
            product_data = await self.rest_client.get_product(product_id)
            
            if product_data:
                logger.info(f"Retrieved WooCommerce product: {product_id}")
            
            return product_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve product {product_id}: {str(e)}")
            return None
    
    # Batch operations
    
    async def batch_extract_orders(self, order_ids: List[str]) -> List[EcommerceOrder]:
        """
        Extract multiple orders by IDs.
        
        Args:
            order_ids: List of WooCommerce order IDs
            
        Returns:
            List[EcommerceOrder]: Extracted orders
        """
        try:
            logger.info(f"Extracting batch of {len(order_ids)} WooCommerce orders")
            
            # Use REST client batch method
            orders_data = await self.rest_client.batch_get_orders(order_ids)
            
            orders = []
            for data in orders_data:
                try:
                    order = await self._parse_woocommerce_order(data)
                    if order:
                        orders.append(order)
                except Exception as e:
                    logger.error(f"Failed to parse batch order: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(orders)} orders from batch")
            return orders
            
        except Exception as e:
            logger.error(f"Batch order extraction failed: {str(e)}")
            raise WooCommerceDataExtractionError(f"Batch extraction failed: {str(e)}")
    
    # Store information
    
    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get store information from WooCommerce.
        
        Returns:
            Dict: Store information
        """
        try:
            system_status = await self.rest_client.get_system_status()
            store_info = await self.rest_client.get_store_settings()
            
            # Extract relevant store information
            environment = system_status.get('environment', {})
            settings = environment.get('settings', {})
            
            combined_info = {
                'store_name': settings.get('title', ''),
                'store_url': environment.get('home_url', ''),
                'admin_email': settings.get('admin_email', ''),
                'currency': settings.get('currency', 'USD'),
                'currency_symbol': settings.get('currency_symbol', '$'),
                'country': settings.get('base_country', ''),
                'state': settings.get('base_state', ''),
                'city': settings.get('base_city', ''),
                'postcode': settings.get('base_postcode', ''),
                'address': settings.get('base_address', ''),
                'woocommerce_version': environment.get('wc_version', ''),
                'wordpress_version': environment.get('wp_version', ''),
                'theme': environment.get('theme', {}).get('name', ''),
                'active_plugins': environment.get('active_plugins', []),
                'api_enabled': settings.get('api_enabled', False),
                'force_ssl': settings.get('force_ssl', False),
                'taxes_enabled': settings.get('enable_taxes', False),
                'calc_taxes': settings.get('calc_taxes', 'no')
            }
            
            logger.info("Retrieved WooCommerce store information")
            return combined_info
            
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
            
            logger.info(f"Generated WooCommerce order statistics: {total_orders} orders, {total_revenue} {currency}")
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to generate order statistics: {str(e)}")
            return {}
    
    # Tax and shipping information
    
    async def get_tax_rates(self) -> List[Dict[str, Any]]:
        """
        Get tax rates from WooCommerce.
        
        Returns:
            List[Dict]: Tax rates configuration
        """
        try:
            tax_rates = await self.rest_client.get_tax_rates()
            logger.info(f"Retrieved {len(tax_rates)} tax rates")
            return tax_rates
            
        except Exception as e:
            logger.error(f"Failed to get tax rates: {str(e)}")
            return []
    
    async def get_tax_classes(self) -> List[Dict[str, Any]]:
        """
        Get tax classes from WooCommerce.
        
        Returns:
            List[Dict]: Tax classes configuration
        """
        try:
            tax_classes = await self.rest_client.get_tax_classes()
            logger.info(f"Retrieved {len(tax_classes)} tax classes")
            return tax_classes
            
        except Exception as e:
            logger.error(f"Failed to get tax classes: {str(e)}")
            return []