"""
Jumia E-commerce Data Extraction Module
Extracts order and product data from Jumia Marketplace Seller API.
Handles African marketplace operations and Jumia-specific data structures.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .rest_client import JumiaRESTClient
from .exceptions import (
    JumiaDataExtractionError,
    JumiaOrderNotFoundError,
    JumiaProductNotFoundError
)

logger = logging.getLogger(__name__)


class JumiaDataExtractor:
    """
    Jumia E-commerce Data Extraction Service
    
    Extracts and processes order, product, and marketplace data from Jumia Seller API.
    Supports African marketplace operations and Jumia-specific features.
    """
    
    def __init__(self, rest_client: JumiaRESTClient):
        """
        Initialize Jumia data extractor.
        
        Args:
            rest_client: Configured Jumia REST API client
        """
        self.rest_client = rest_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def extract_order_data(
        self,
        order_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract order data from Jumia.
        
        Args:
            order_id: Specific order ID
            date_from: Start date for order filtering
            date_to: End date for order filtering
            status: Order status filter ('pending', 'shipped', 'delivered', etc.)
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of extracted order data dictionaries
        """
        try:
            if order_id:
                # Get specific order
                order = await self.rest_client.get_order(order_id)
                if not order:
                    raise JumiaOrderNotFoundError(order_id)
                
                # Enrich with additional data
                enriched_order = await self._enrich_order_data(order)
                return [enriched_order]
            
            # Build query parameters for multiple orders
            params = {'limit': min(limit, 100)}  # Jumia max: 100
            
            if date_from:
                params['created_after'] = date_from.strftime('%Y-%m-%d')
            
            if date_to:
                params['created_before'] = date_to.strftime('%Y-%m-%d')
            
            if status:
                # Map common status names to Jumia status values
                status_mapping = {
                    'pending': 'pending',
                    'shipped': 'shipped',
                    'delivered': 'delivered',
                    'canceled': 'canceled',
                    'returned': 'returned',
                    'failed_delivery': 'failed_delivery'
                }
                jumia_status = status_mapping.get(status.lower(), status)
                params['status'] = jumia_status
            
            # Get orders
            response = await self.rest_client.get_orders(params)
            
            # Handle response format
            orders = self._extract_data_from_response(response)
            
            if not orders:
                self.logger.warning("No orders found matching criteria")
                return []
            
            # Enrich orders with additional details
            enriched_orders = []
            for order in orders:
                try:
                    enriched_order = await self._enrich_order_data(order)
                    enriched_orders.append(enriched_order)
                except Exception as e:
                    self.logger.error(f"Failed to enrich order {order.get('order_id', 'unknown')}: {e}")
                    # Include basic order data even if enrichment fails
                    enriched_orders.append(order)
            
            self.logger.info(f"Successfully extracted {len(enriched_orders)} orders from Jumia")
            return enriched_orders
            
        except Exception as e:
            self.logger.error(f"Failed to extract order data: {e}")
            raise JumiaDataExtractionError(f"Order data extraction failed: {e}")
    
    async def _enrich_order_data(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich order data with additional details.
        
        Args:
            order: Basic order data from API
            
        Returns:
            Enriched order data dictionary
        """
        try:
            order_id = order.get('order_id')
            if not order_id:
                return order
            
            # Get order items
            try:
                items_response = await self.rest_client.get_order_items(order_id)
                items = self._extract_data_from_response(items_response)
                order['items'] = items or []
            except Exception as e:
                self.logger.warning(f"Failed to get items for order {order_id}: {e}")
                order['items'] = []
            
            # Add marketplace-specific information
            order['marketplace'] = self.rest_client.auth_manager.get_marketplace()
            order['country_code'] = self.rest_client.auth_manager.get_country_code()
            
            # Parse and standardize order data
            order = self._standardize_order_data(order)
            
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to enrich order data: {e}")
            return order
    
    def _standardize_order_data(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize Jumia order data to common format.
        
        Args:
            order: Raw order data from Jumia API
            
        Returns:
            Standardized order data dictionary
        """
        try:
            # Map Jumia fields to standard fields
            standardized = {
                'id': order.get('order_id'),
                'order_number': order.get('order_number'),
                'status': order.get('status'),
                'created_at': order.get('created_at'),
                'updated_at': order.get('updated_at'),
                'total_amount': order.get('total_amount'),
                'currency': order.get('currency_code', 'NGN'),  # Default to NGN for Nigeria
                'payment_method': order.get('payment_method'),
                'shipping_fee': order.get('shipping_fee'),
                'voucher_amount': order.get('voucher_amount', 0),
                'tax_amount': order.get('tax_amount', 0),
                'items': order.get('items', []),
                'customer': {
                    'name': order.get('customer_first_name', '') + ' ' + order.get('customer_last_name', ''),
                    'email': order.get('customer_email'),
                    'phone': order.get('customer_phone')
                },
                'shipping_address': {
                    'name': order.get('shipping_name'),
                    'address': order.get('shipping_address'),
                    'city': order.get('shipping_city'),
                    'region': order.get('shipping_region'),
                    'country': order.get('shipping_country'),
                    'phone': order.get('shipping_phone')
                },
                'billing_address': {
                    'name': order.get('billing_name'),
                    'address': order.get('billing_address'),
                    'city': order.get('billing_city'),
                    'region': order.get('billing_region'),
                    'country': order.get('billing_country'),
                    'phone': order.get('billing_phone')
                }
            }
            
            # Merge with original data to preserve Jumia-specific fields
            return {**order, **standardized}
            
        except Exception as e:
            self.logger.warning(f"Failed to standardize order data: {e}")
            return order
    
    def _extract_data_from_response(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract data from Jumia API response.
        
        Args:
            response: API response data
            
        Returns:
            List of data items
        """
        if isinstance(response, dict):
            # Check for different response formats
            if 'data' in response:
                data = response['data']
            elif 'body' in response:
                body = response['body']
                if isinstance(body, dict):
                    data = body.get('data', body.get('items', body))
                else:
                    data = body
            else:
                data = response
            
            # Ensure data is a list
            if not isinstance(data, list):
                data = [data] if data else []
            
            return data
        elif isinstance(response, list):
            return response
        else:
            return [response] if response else []
    
    async def extract_product_data(
        self,
        product_id: Optional[str] = None,
        sku: Optional[str] = None,
        name: Optional[str] = None,
        category_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract product data from Jumia.
        
        Args:
            product_id: Specific product ID
            sku: Product SKU filter
            name: Product name filter
            category_id: Category ID filter
            status: Product status filter ('active', 'inactive', etc.)
            limit: Maximum number of products to retrieve
            
        Returns:
            List of extracted product data dictionaries
        """
        try:
            if product_id:
                # Get specific product
                product = await self.rest_client.get_product(product_id)
                if not product:
                    raise JumiaProductNotFoundError(product_id)
                
                # Enrich with additional data
                enriched_product = await self._enrich_product_data(product)
                return [enriched_product]
            
            # Build query parameters for multiple products
            params = {'limit': min(limit, 100)}  # Jumia max: 100
            
            if sku:
                params['sku'] = sku
            
            if name:
                params['search'] = name
            
            if category_id:
                params['category_id'] = category_id
            
            if status:
                params['status'] = status
            
            # Get products
            response = await self.rest_client.get_products(params)
            
            # Handle response format
            products = self._extract_data_from_response(response)
            
            if not products:
                self.logger.warning("No products found matching criteria")
                return []
            
            # Enrich products with additional data
            enriched_products = []
            for product in products[:limit]:  # Respect limit for enrichment
                try:
                    enriched_product = await self._enrich_product_data(product)
                    enriched_products.append(enriched_product)
                except Exception as e:
                    self.logger.error(f"Failed to enrich product {product.get('product_id', 'unknown')}: {e}")
                    enriched_products.append(product)
            
            self.logger.info(f"Successfully extracted {len(enriched_products)} products from Jumia")
            return enriched_products
            
        except Exception as e:
            self.logger.error(f"Failed to extract product data: {e}")
            raise JumiaDataExtractionError(f"Product data extraction failed: {e}")
    
    async def _enrich_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich product data with additional details.
        
        Args:
            product: Basic product data from API
            
        Returns:
            Enriched product data dictionary
        """
        try:
            # Add marketplace-specific information
            product['marketplace'] = self.rest_client.auth_manager.get_marketplace()
            product['country_code'] = self.rest_client.auth_manager.get_country_code()
            
            # Standardize product data
            product = self._standardize_product_data(product)
            
            return product
            
        except Exception as e:
            self.logger.error(f"Failed to enrich product data: {e}")
            return product
    
    def _standardize_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize Jumia product data to common format.
        
        Args:
            product: Raw product data from Jumia API
            
        Returns:
            Standardized product data dictionary
        """
        try:
            # Map Jumia fields to standard fields
            standardized = {
                'id': product.get('product_id'),
                'sku': product.get('sku'),
                'name': product.get('name'),
                'description': product.get('description'),
                'brand': product.get('brand'),
                'category_id': product.get('category_id'),
                'status': product.get('status'),
                'price': product.get('price'),
                'special_price': product.get('special_price'),
                'quantity': product.get('quantity'),
                'images': product.get('images', []),
                'attributes': product.get('attributes', {}),
                'created_at': product.get('created_at'),
                'updated_at': product.get('updated_at')
            }
            
            # Merge with original data to preserve Jumia-specific fields
            return {**product, **standardized}
            
        except Exception as e:
            self.logger.warning(f"Failed to standardize product data: {e}")
            return product
    
    async def extract_category_data(self) -> List[Dict[str, Any]]:
        """
        Extract category data from Jumia.
        
        Returns:
            List of extracted category data dictionaries
        """
        try:
            response = await self.rest_client.get_categories()
            categories = self._extract_data_from_response(response)
            
            self.logger.info(f"Successfully extracted {len(categories)} categories from Jumia")
            return categories
            
        except Exception as e:
            self.logger.error(f"Failed to extract category data: {e}")
            raise JumiaDataExtractionError(f"Category data extraction failed: {e}")
    
    async def extract_inventory_data(
        self,
        sku: Optional[str] = None,
        low_stock_threshold: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract inventory data from Jumia.
        
        Args:
            sku: Specific product SKU
            low_stock_threshold: Threshold for low stock filtering
            limit: Maximum number of inventory items to retrieve
            
        Returns:
            List of inventory data dictionaries
        """
        try:
            params = {'limit': min(limit, 100)}
            
            if sku:
                params['sku'] = sku
            
            response = await self.rest_client.get_inventory(params)
            inventory_items = self._extract_data_from_response(response)
            
            # Filter by low stock threshold if specified
            if low_stock_threshold is not None:
                inventory_items = [
                    item for item in inventory_items 
                    if item.get('quantity', 0) < low_stock_threshold
                ]
            
            self.logger.info(f"Successfully extracted inventory data for {len(inventory_items)} items")
            return inventory_items
            
        except Exception as e:
            self.logger.error(f"Failed to extract inventory data: {e}")
            raise JumiaDataExtractionError(f"Inventory data extraction failed: {e}")
    
    async def extract_order_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Extract order analytics and statistics.
        
        Args:
            date_from: Start date for analytics
            date_to: End date for analytics
            
        Returns:
            Dictionary containing order analytics
        """
        try:
            # Default to last 30 days if no dates provided
            if not date_to:
                date_to = datetime.now()
            if not date_from:
                date_from = date_to - timedelta(days=30)
            
            # Get orders for the period
            orders = await self.extract_order_data(
                date_from=date_from,
                date_to=date_to,
                limit=1000  # Increased limit for analytics
            )
            
            # Calculate analytics
            total_orders = len(orders)
            total_revenue = sum(float(order.get('total_amount', 0)) for order in orders)
            total_tax = sum(float(order.get('tax_amount', 0)) for order in orders)
            total_shipping = sum(float(order.get('shipping_fee', 0)) for order in orders)
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Status breakdown
            status_breakdown = {}
            for order in orders:
                status = order.get('status', 'unknown')
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            # Payment method breakdown
            payment_methods = {}
            for order in orders:
                method = order.get('payment_method', 'unknown')
                payment_methods[method] = payment_methods.get(method, 0) + 1
            
            # Top products
            product_sales = {}
            for order in orders:
                for item in order.get('items', []):
                    sku = item.get('sku', 'unknown')
                    qty = int(item.get('quantity', 0))
                    product_sales[sku] = product_sales.get(sku, 0) + qty
            
            top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Regional breakdown
            regional_breakdown = {}
            for order in orders:
                region = order.get('shipping_address', {}).get('region', 'Unknown')
                regional_breakdown[region] = regional_breakdown.get(region, 0) + 1
            
            analytics = {
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                },
                'marketplace': self.rest_client.auth_manager.get_marketplace(),
                'country_code': self.rest_client.auth_manager.get_country_code(),
                'summary': {
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'total_tax': total_tax,
                    'total_shipping': total_shipping,
                    'average_order_value': average_order_value
                },
                'breakdowns': {
                    'by_status': status_breakdown,
                    'by_payment_method': payment_methods,
                    'by_region': regional_breakdown
                },
                'top_products': [{'sku': sku, 'quantity_sold': qty} for sku, qty in top_products]
            }
            
            self.logger.info(f"Successfully generated analytics for {total_orders} orders")
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to extract order analytics: {e}")
            raise JumiaDataExtractionError(f"Order analytics extraction failed: {e}")
    
    async def extract_payment_data(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract payment data from Jumia.
        
        Args:
            date_from: Start date for payment filtering
            date_to: End date for payment filtering
            limit: Maximum number of payments to retrieve
            
        Returns:
            List of payment data dictionaries
        """
        try:
            params = {'limit': min(limit, 100)}
            
            if date_from:
                params['date_from'] = date_from.strftime('%Y-%m-%d')
            
            if date_to:
                params['date_to'] = date_to.strftime('%Y-%m-%d')
            
            response = await self.rest_client.get_payments(params)
            payments = self._extract_data_from_response(response)
            
            self.logger.info(f"Successfully extracted {len(payments)} payments from Jumia")
            return payments
            
        except Exception as e:
            self.logger.error(f"Failed to extract payment data: {e}")
            raise JumiaDataExtractionError(f"Payment data extraction failed: {e}")
    
    async def extract_shipment_data(
        self,
        shipment_id: Optional[str] = None,
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract shipment data from Jumia.
        
        Args:
            shipment_id: Specific shipment ID
            order_id: Order ID filter
            status: Shipment status filter
            limit: Maximum number of shipments to retrieve
            
        Returns:
            List of shipment data dictionaries
        """
        try:
            if shipment_id:
                # Get specific shipment
                shipment = await self.rest_client.get_shipment(shipment_id)
                return [shipment] if shipment else []
            
            params = {'limit': min(limit, 100)}
            
            if order_id:
                params['order_id'] = order_id
            
            if status:
                params['status'] = status
            
            response = await self.rest_client.get_shipments(params)
            shipments = self._extract_data_from_response(response)
            
            self.logger.info(f"Successfully extracted {len(shipments)} shipments from Jumia")
            return shipments
            
        except Exception as e:
            self.logger.error(f"Failed to extract shipment data: {e}")
            raise JumiaDataExtractionError(f"Shipment data extraction failed: {e}")
    
    async def extract_seller_profile(self) -> Dict[str, Any]:
        """
        Extract seller profile information from Jumia.
        
        Returns:
            Seller profile data dictionary
        """
        try:
            profile = await self.rest_client.get_seller_profile()
            
            self.logger.info("Successfully extracted seller profile from Jumia")
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to extract seller profile: {e}")
            raise JumiaDataExtractionError(f"Seller profile extraction failed: {e}")
    
    async def extract_brand_data(self) -> List[Dict[str, Any]]:
        """
        Extract brand data from Jumia.
        
        Returns:
            List of brand data dictionaries
        """
        try:
            response = await self.rest_client.get_brands()
            brands = self._extract_data_from_response(response)
            
            self.logger.info(f"Successfully extracted {len(brands)} brands from Jumia")
            return brands
            
        except Exception as e:
            self.logger.error(f"Failed to extract brand data: {e}")
            raise JumiaDataExtractionError(f"Brand data extraction failed: {e}")
    
    async def extract_sales_report(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Extract sales report from Jumia.
        
        Args:
            date_from: Start date for report
            date_to: End date for report
            
        Returns:
            Sales report data dictionary
        """
        try:
            params = {}
            
            if date_from:
                params['date_from'] = date_from.strftime('%Y-%m-%d')
            
            if date_to:
                params['date_to'] = date_to.strftime('%Y-%m-%d')
            
            report = await self.rest_client.get_sales_report(params)
            
            self.logger.info("Successfully extracted sales report from Jumia")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to extract sales report: {e}")
            raise JumiaDataExtractionError(f"Sales report extraction failed: {e}")