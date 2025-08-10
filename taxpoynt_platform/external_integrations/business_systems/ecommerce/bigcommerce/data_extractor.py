"""
BigCommerce E-commerce Data Extraction Module
Extracts order and customer data from BigCommerce REST API.
Handles multi-channel operations and BigCommerce-specific data structures.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .rest_client import BigCommerceRESTClient
from .exceptions import (
    BigCommerceDataExtractionError,
    BigCommerceOrderNotFoundError,
    BigCommerceCustomerNotFoundError,
    BigCommerceProductNotFoundError
)

logger = logging.getLogger(__name__)


class BigCommerceDataExtractor:
    """
    BigCommerce E-commerce Data Extraction Service
    
    Extracts and processes order, customer, and product data from BigCommerce REST API.
    Supports multi-channel operations and BigCommerce-specific features.
    """
    
    def __init__(self, rest_client: BigCommerceRESTClient):
        """
        Initialize BigCommerce data extractor.
        
        Args:
            rest_client: Configured BigCommerce REST API client
        """
        self.rest_client = rest_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def extract_order_data(
        self,
        order_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        customer_id: Optional[int] = None,
        status_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract order data from BigCommerce.
        
        Args:
            order_id: Specific order ID
            date_from: Start date for order filtering
            date_to: End date for order filtering
            customer_id: Customer ID for customer-specific orders
            status_id: Order status ID filter
            channel_id: Channel ID for multi-channel filtering
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of extracted order data dictionaries
        """
        try:
            if order_id:
                # Get specific order
                order = await self.rest_client.get_order(order_id)
                if not order:
                    raise BigCommerceOrderNotFoundError(str(order_id))
                
                # Enrich with additional data
                enriched_order = await self._enrich_order_data(order)
                return [enriched_order]
            
            # Build query parameters for multiple orders
            params = {'limit': min(limit, 250)}  # BigCommerce max: 250
            
            if date_from:
                params['min_date_created'] = date_from.strftime('%Y-%m-%dT%H:%M:%S')
            
            if date_to:
                params['max_date_created'] = date_to.strftime('%Y-%m-%dT%H:%M:%S')
            
            if customer_id:
                params['customer_id'] = customer_id
            
            if status_id:
                params['status_id'] = status_id
            
            if channel_id:
                params['channel_id'] = channel_id
            
            # Add sorting by creation date (newest first)
            params['sort'] = 'date_created:desc'
            
            # Get orders
            response = await self.rest_client.get_orders(params)
            
            # Handle response format
            if isinstance(response, dict) and 'data' in response:
                orders = response['data']
            elif isinstance(response, list):
                orders = response
            else:
                orders = [response] if response else []
            
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
                    self.logger.error(f"Failed to enrich order {order.get('id', 'unknown')}: {e}")
                    # Include basic order data even if enrichment fails
                    enriched_orders.append(order)
            
            self.logger.info(f"Successfully extracted {len(enriched_orders)} orders from BigCommerce")
            return enriched_orders
            
        except Exception as e:
            self.logger.error(f"Failed to extract order data: {e}")
            raise BigCommerceDataExtractionError(f"Order data extraction failed: {e}")
    
    async def _enrich_order_data(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich order data with additional details.
        
        Args:
            order: Basic order data from API
            
        Returns:
            Enriched order data dictionary
        """
        try:
            order_id = order.get('id')
            if not order_id:
                return order
            
            # Get order products
            try:
                products_response = await self.rest_client.get_order_products(order_id)
                if isinstance(products_response, dict) and 'data' in products_response:
                    products = products_response['data']
                elif isinstance(products_response, list):
                    products = products_response
                else:
                    products = []
                
                order['products'] = products
            except Exception as e:
                self.logger.warning(f"Failed to get products for order {order_id}: {e}")
                order['products'] = []
            
            # Get shipping addresses
            try:
                shipping_response = await self.rest_client.get_order_shipping_addresses(order_id)
                if isinstance(shipping_response, dict) and 'data' in shipping_response:
                    shipping_addresses = shipping_response['data']
                elif isinstance(shipping_response, list):
                    shipping_addresses = shipping_response
                else:
                    shipping_addresses = []
                
                order['shipping_addresses'] = shipping_addresses
            except Exception as e:
                self.logger.warning(f"Failed to get shipping addresses for order {order_id}: {e}")
                order['shipping_addresses'] = []
            
            # Get customer details if customer_id exists
            customer_id = order.get('customer_id')
            if customer_id and customer_id > 0:
                try:
                    customer = await self.rest_client.get_customer(customer_id)
                    order['customer_details'] = customer
                except Exception as e:
                    self.logger.warning(f"Failed to get customer details for order {order_id}: {e}")
            
            # Add channel information if available
            channel_id = order.get('channel_id')
            if channel_id:
                try:
                    channel = await self.rest_client.get_channel(channel_id)
                    order['channel_details'] = channel
                except Exception as e:
                    self.logger.warning(f"Failed to get channel details for order {order_id}: {e}")
            
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to enrich order data: {e}")
            return order
    
    async def extract_customer_data(
        self,
        customer_id: Optional[int] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract customer data from BigCommerce.
        
        Args:
            customer_id: Specific customer ID
            email: Customer email filter
            company: Customer company filter
            date_from: Start date for customer filtering
            date_to: End date for customer filtering
            limit: Maximum number of customers to retrieve
            
        Returns:
            List of extracted customer data dictionaries
        """
        try:
            if customer_id:
                # Get specific customer
                customer = await self.rest_client.get_customer(customer_id)
                if not customer:
                    raise BigCommerceCustomerNotFoundError(str(customer_id))
                
                # Enrich with addresses
                enriched_customer = await self._enrich_customer_data(customer)
                return [enriched_customer]
            
            # Build query parameters for multiple customers
            params = {'limit': min(limit, 250)}  # BigCommerce max: 250
            
            if email:
                params['email:in'] = email
            
            if company:
                params['company:like'] = company
            
            if date_from:
                params['min_date_created'] = date_from.strftime('%Y-%m-%dT%H:%M:%S')
            
            if date_to:
                params['max_date_created'] = date_to.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Add sorting by creation date (newest first)
            params['sort'] = 'date_created:desc'
            
            # Get customers
            response = await self.rest_client.get_customers(params)
            
            # Handle response format
            if isinstance(response, dict) and 'data' in response:
                customers = response['data']
            elif isinstance(response, list):
                customers = response
            else:
                customers = [response] if response else []
            
            if not customers:
                self.logger.warning("No customers found matching criteria")
                return []
            
            # Enrich customers with addresses
            enriched_customers = []
            for customer in customers:
                try:
                    enriched_customer = await self._enrich_customer_data(customer)
                    enriched_customers.append(enriched_customer)
                except Exception as e:
                    self.logger.error(f"Failed to enrich customer {customer.get('id', 'unknown')}: {e}")
                    enriched_customers.append(customer)
            
            self.logger.info(f"Successfully extracted {len(enriched_customers)} customers from BigCommerce")
            return enriched_customers
            
        except Exception as e:
            self.logger.error(f"Failed to extract customer data: {e}")
            raise BigCommerceDataExtractionError(f"Customer data extraction failed: {e}")
    
    async def _enrich_customer_data(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich customer data with addresses.
        
        Args:
            customer: Basic customer data from API
            
        Returns:
            Enriched customer data dictionary
        """
        try:
            customer_id = customer.get('id')
            if not customer_id:
                return customer
            
            # Get customer addresses
            try:
                addresses_response = await self.rest_client.get_customer_addresses(customer_id)
                if isinstance(addresses_response, dict) and 'data' in addresses_response:
                    addresses = addresses_response['data']
                elif isinstance(addresses_response, list):
                    addresses = addresses_response
                else:
                    addresses = []
                
                customer['addresses'] = addresses
            except Exception as e:
                self.logger.warning(f"Failed to get addresses for customer {customer_id}: {e}")
                customer['addresses'] = []
            
            return customer
            
        except Exception as e:
            self.logger.error(f"Failed to enrich customer data: {e}")
            return customer
    
    async def extract_product_data(
        self,
        product_id: Optional[int] = None,
        sku: Optional[str] = None,
        name: Optional[str] = None,
        category_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        is_visible: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract product data from BigCommerce.
        
        Args:
            product_id: Specific product ID
            sku: Product SKU filter
            name: Product name filter
            category_id: Category ID filter
            brand_id: Brand ID filter
            is_visible: Visibility filter
            limit: Maximum number of products to retrieve
            
        Returns:
            List of extracted product data dictionaries
        """
        try:
            if product_id:
                # Get specific product
                product = await self.rest_client.get_product(product_id)
                if not product:
                    raise BigCommerceProductNotFoundError(str(product_id))
                
                # Enrich with variants and images
                enriched_product = await self._enrich_product_data(product)
                return [enriched_product]
            
            # Build query parameters for multiple products
            params = {'limit': min(limit, 250)}  # BigCommerce max: 250
            
            if sku:
                params['sku'] = sku
            
            if name:
                params['name:like'] = name
            
            if category_id:
                params['categories:in'] = category_id
            
            if brand_id:
                params['brand_id'] = brand_id
            
            if is_visible is not None:
                params['is_visible'] = is_visible
            
            # Add sorting by creation date (newest first)
            params['sort'] = 'date_created:desc'
            
            # Get products
            response = await self.rest_client.get_products(params)
            
            # Handle response format
            if isinstance(response, dict) and 'data' in response:
                products = response['data']
            elif isinstance(response, list):
                products = response
            else:
                products = [response] if response else []
            
            if not products:
                self.logger.warning("No products found matching criteria")
                return []
            
            # Enrich products with variants and images
            enriched_products = []
            for product in products[:limit]:  # Respect limit for enrichment
                try:
                    enriched_product = await self._enrich_product_data(product)
                    enriched_products.append(enriched_product)
                except Exception as e:
                    self.logger.error(f"Failed to enrich product {product.get('id', 'unknown')}: {e}")
                    enriched_products.append(product)
            
            self.logger.info(f"Successfully extracted {len(enriched_products)} products from BigCommerce")
            return enriched_products
            
        except Exception as e:
            self.logger.error(f"Failed to extract product data: {e}")
            raise BigCommerceDataExtractionError(f"Product data extraction failed: {e}")
    
    async def _enrich_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich product data with variants and images.
        
        Args:
            product: Basic product data from API
            
        Returns:
            Enriched product data dictionary
        """
        try:
            product_id = product.get('id')
            if not product_id:
                return product
            
            # Get product variants
            try:
                variants_response = await self.rest_client.get_product_variants(product_id)
                if isinstance(variants_response, dict) and 'data' in variants_response:
                    variants = variants_response['data']
                elif isinstance(variants_response, list):
                    variants = variants_response
                else:
                    variants = []
                
                product['variants'] = variants
            except Exception as e:
                self.logger.warning(f"Failed to get variants for product {product_id}: {e}")
                product['variants'] = []
            
            # Get product images
            try:
                images_response = await self.rest_client.get_product_images(product_id)
                if isinstance(images_response, dict) and 'data' in images_response:
                    images = images_response['data']
                elif isinstance(images_response, list):
                    images = images_response
                else:
                    images = []
                
                product['images'] = images
            except Exception as e:
                self.logger.warning(f"Failed to get images for product {product_id}: {e}")
                product['images'] = []
            
            return product
            
        except Exception as e:
            self.logger.error(f"Failed to enrich product data: {e}")
            return product
    
    async def extract_category_data(
        self,
        category_id: Optional[int] = None,
        parent_id: Optional[int] = None,
        name: Optional[str] = None,
        is_visible: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract category data from BigCommerce.
        
        Args:
            category_id: Specific category ID
            parent_id: Parent category ID for hierarchy filtering
            name: Category name filter
            is_visible: Visibility filter
            limit: Maximum number of categories to retrieve
            
        Returns:
            List of extracted category data dictionaries
        """
        try:
            if category_id:
                # Get specific category
                category = await self.rest_client.get_category(category_id)
                return [category] if category else []
            
            # Build query parameters for multiple categories
            params = {'limit': min(limit, 250)}  # BigCommerce max: 250
            
            if parent_id is not None:
                params['parent_id'] = parent_id
            
            if name:
                params['name:like'] = name
            
            if is_visible is not None:
                params['is_visible'] = is_visible
            
            # Get categories
            response = await self.rest_client.get_categories(params)
            
            # Handle response format
            if isinstance(response, dict) and 'data' in response:
                categories = response['data']
            elif isinstance(response, list):
                categories = response
            else:
                categories = [response] if response else []
            
            self.logger.info(f"Successfully extracted {len(categories)} categories from BigCommerce")
            return categories
            
        except Exception as e:
            self.logger.error(f"Failed to extract category data: {e}")
            raise BigCommerceDataExtractionError(f"Category data extraction failed: {e}")
    
    async def extract_brand_data(
        self,
        brand_id: Optional[int] = None,
        name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract brand data from BigCommerce.
        
        Args:
            brand_id: Specific brand ID
            name: Brand name filter
            limit: Maximum number of brands to retrieve
            
        Returns:
            List of extracted brand data dictionaries
        """
        try:
            if brand_id:
                # Get specific brand
                brand = await self.rest_client.get_brand(brand_id)
                return [brand] if brand else []
            
            # Build query parameters for multiple brands
            params = {'limit': min(limit, 250)}  # BigCommerce max: 250
            
            if name:
                params['name:like'] = name
            
            # Get brands
            response = await self.rest_client.get_brands(params)
            
            # Handle response format
            if isinstance(response, dict) and 'data' in response:
                brands = response['data']
            elif isinstance(response, list):
                brands = response
            else:
                brands = [response] if response else []
            
            self.logger.info(f"Successfully extracted {len(brands)} brands from BigCommerce")
            return brands
            
        except Exception as e:
            self.logger.error(f"Failed to extract brand data: {e}")
            raise BigCommerceDataExtractionError(f"Brand data extraction failed: {e}")
    
    async def extract_order_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        channel_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract order analytics and statistics.
        
        Args:
            date_from: Start date for analytics
            date_to: End date for analytics
            channel_id: Channel ID for multi-channel analytics
            
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
                channel_id=channel_id,
                limit=1000  # Increased limit for analytics
            )
            
            # Calculate analytics
            total_orders = len(orders)
            total_revenue = sum(float(order.get('total_inc_tax', 0)) for order in orders)
            total_tax = sum(float(order.get('total_tax', 0)) for order in orders)
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
            
            # Channel breakdown
            channel_breakdown = {}
            if not channel_id:  # Only show channel breakdown if not filtering by channel
                for order in orders:
                    channel = order.get('channel_id', 'unknown')
                    channel_breakdown[str(channel)] = channel_breakdown.get(str(channel), 0) + 1
            
            # Top products
            product_sales = {}
            for order in orders:
                for product in order.get('products', []):
                    sku = product.get('sku', 'unknown')
                    qty = int(product.get('quantity', 0))
                    product_sales[sku] = product_sales.get(sku, 0) + qty
            
            top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:10]
            
            analytics = {
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                },
                'channel_id': channel_id,
                'summary': {
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'total_tax': total_tax,
                    'average_order_value': average_order_value
                },
                'breakdowns': {
                    'by_status': status_breakdown,
                    'by_payment_method': payment_methods,
                    'by_channel': channel_breakdown
                },
                'top_products': [{'sku': sku, 'quantity_sold': qty} for sku, qty in top_products]
            }
            
            self.logger.info(f"Successfully generated analytics for {total_orders} orders")
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to extract order analytics: {e}")
            raise BigCommerceDataExtractionError(f"Order analytics extraction failed: {e}")
    
    async def extract_channel_data(self) -> List[Dict[str, Any]]:
        """
        Extract channel data from BigCommerce.
        
        Returns:
            List of channel data dictionaries
        """
        try:
            response = await self.rest_client.get_channels()
            
            # Handle response format
            if isinstance(response, dict) and 'data' in response:
                channels = response['data']
            elif isinstance(response, list):
                channels = response
            else:
                channels = [response] if response else []
            
            self.logger.info(f"Successfully extracted {len(channels)} channels from BigCommerce")
            return channels
            
        except Exception as e:
            self.logger.error(f"Failed to extract channel data: {e}")
            raise BigCommerceDataExtractionError(f"Channel data extraction failed: {e}")
    
    async def extract_store_info(self) -> Dict[str, Any]:
        """
        Extract store information from BigCommerce.
        
        Returns:
            Store information dictionary
        """
        try:
            store_info = await self.rest_client.get_store_info()
            
            self.logger.info("Successfully extracted store information from BigCommerce")
            return store_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract store information: {e}")
            raise BigCommerceDataExtractionError(f"Store information extraction failed: {e}")