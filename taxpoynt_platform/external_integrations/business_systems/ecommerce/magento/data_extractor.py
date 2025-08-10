"""
Magento E-commerce Data Extraction Module
Extracts order and customer data from Magento REST API.
Handles Adobe Commerce and Magento Open Source with multi-store support.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .rest_client import MagentoRESTClient
from .exceptions import (
    MagentoDataExtractionError,
    MagentoOrderNotFoundError,
    MagentoCustomerNotFoundError,
    MagentoProductNotFoundError,
    MagentoStoreNotFoundError
)

logger = logging.getLogger(__name__)


class MagentoDataExtractor:
    """
    Magento E-commerce Data Extraction Service
    
    Extracts and processes order, customer, and product data from Magento REST API.
    Supports both Adobe Commerce and Magento Open Source with multi-store operations.
    """
    
    def __init__(self, rest_client: MagentoRESTClient):
        """
        Initialize Magento data extractor.
        
        Args:
            rest_client: Configured Magento REST API client
        """
        self.rest_client = rest_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def extract_order_data(
        self,
        order_id: Optional[str] = None,
        increment_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        store_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract order data from Magento.
        
        Args:
            order_id: Specific order entity ID
            increment_id: Human-readable order number
            date_from: Start date for order filtering
            date_to: End date for order filtering
            store_id: Store ID for multi-store filtering
            customer_id: Customer ID for customer-specific orders
            status: Order status filter
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of extracted order data dictionaries
        """
        try:
            # Build search criteria
            search_criteria = []
            
            if order_id:
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][field]=entity_id")
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][value]={order_id}")
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][condition_type]=eq")
            
            if increment_id:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=increment_id")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={increment_id}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=eq")
            
            if date_from:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=created_at")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={date_from.isoformat()}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=gteq")
            
            if date_to:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=created_at")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={date_to.isoformat()}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=lteq")
            
            if store_id:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=store_id")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={store_id}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=eq")
            
            if customer_id:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=customer_id")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={customer_id}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=eq")
            
            if status:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=status")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={status}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=eq")
            
            # Add pagination
            search_criteria.append(f"searchCriteria[pageSize]={limit}")
            search_criteria.append("searchCriteria[currentPage]=1")
            
            # Add sorting by creation date (newest first)
            search_criteria.append("searchCriteria[sortOrders][0][field]=created_at")
            search_criteria.append("searchCriteria[sortOrders][0][direction]=DESC")
            
            query_string = "&".join(search_criteria)
            orders_response = await self.rest_client.get_orders(query_params=query_string)
            
            if not orders_response or 'items' not in orders_response:
                self.logger.warning("No orders found matching criteria")
                return []
            
            orders = []
            for order in orders_response['items']:
                try:
                    # Enrich order data with additional details
                    enriched_order = await self._enrich_order_data(order, store_id)
                    orders.append(enriched_order)
                except Exception as e:
                    self.logger.error(f"Failed to enrich order {order.get('entity_id', 'unknown')}: {e}")
                    # Include basic order data even if enrichment fails
                    orders.append(order)
            
            self.logger.info(f"Successfully extracted {len(orders)} orders from Magento")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to extract order data: {e}")
            raise MagentoDataExtractionError(f"Order data extraction failed: {e}")
    
    async def _enrich_order_data(self, order: Dict[str, Any], store_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Enrich order data with additional details.
        
        Args:
            order: Basic order data from API
            store_id: Store ID for context
            
        Returns:
            Enriched order data dictionary
        """
        try:
            # Get customer details if customer_id exists
            if order.get('customer_id'):
                try:
                    customer = await self.rest_client.get_customer(order['customer_id'])
                    order['customer_details'] = customer
                except Exception as e:
                    self.logger.warning(f"Failed to get customer details for order {order.get('entity_id')}: {e}")
            
            # Enrich order items with product details
            if 'items' in order:
                enriched_items = []
                for item in order['items']:
                    try:
                        # Get product details
                        product = await self.rest_client.get_product(item['sku'])
                        item['product_details'] = product
                    except Exception as e:
                        self.logger.warning(f"Failed to get product details for SKU {item.get('sku')}: {e}")
                    
                    enriched_items.append(item)
                order['items'] = enriched_items
            
            # Add store information
            if store_id or order.get('store_id'):
                try:
                    store_info = await self.rest_client.get_store_config(store_id or order['store_id'])
                    order['store_info'] = store_info
                except Exception as e:
                    self.logger.warning(f"Failed to get store info: {e}")
            
            # Add payment and shipping details
            if order.get('payment'):
                order['payment_details'] = order['payment']
            
            if order.get('extension_attributes', {}).get('shipping_assignments'):
                order['shipping_details'] = order['extension_attributes']['shipping_assignments']
            
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to enrich order data: {e}")
            return order
    
    async def extract_customer_data(
        self,
        customer_id: Optional[int] = None,
        email: Optional[str] = None,
        website_id: Optional[int] = None,
        group_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract customer data from Magento.
        
        Args:
            customer_id: Specific customer ID
            email: Customer email filter
            website_id: Website ID for multi-site filtering
            group_id: Customer group ID filter
            limit: Maximum number of customers to retrieve
            
        Returns:
            List of extracted customer data dictionaries
        """
        try:
            if customer_id:
                # Get specific customer
                customer = await self.rest_client.get_customer(customer_id)
                return [customer] if customer else []
            
            # Build search criteria for multiple customers
            search_criteria = []
            
            if email:
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][field]=email")
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][value]={email}")
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][condition_type]=eq")
            
            if website_id:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=website_id")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={website_id}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=eq")
            
            if group_id:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=group_id")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={group_id}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=eq")
            
            # Add pagination
            search_criteria.append(f"searchCriteria[pageSize]={limit}")
            search_criteria.append("searchCriteria[currentPage]=1")
            
            query_string = "&".join(search_criteria)
            customers_response = await self.rest_client.get_customers(query_params=query_string)
            
            if not customers_response or 'items' not in customers_response:
                self.logger.warning("No customers found matching criteria")
                return []
            
            customers = customers_response['items']
            self.logger.info(f"Successfully extracted {len(customers)} customers from Magento")
            return customers
            
        except Exception as e:
            self.logger.error(f"Failed to extract customer data: {e}")
            raise MagentoDataExtractionError(f"Customer data extraction failed: {e}")
    
    async def extract_product_data(
        self,
        sku: Optional[str] = None,
        name: Optional[str] = None,
        category_id: Optional[int] = None,
        status: Optional[int] = None,
        store_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract product data from Magento.
        
        Args:
            sku: Specific product SKU
            name: Product name filter
            category_id: Category ID filter
            status: Product status (1=enabled, 2=disabled)
            store_id: Store ID for multi-store filtering
            limit: Maximum number of products to retrieve
            
        Returns:
            List of extracted product data dictionaries
        """
        try:
            if sku:
                # Get specific product
                product = await self.rest_client.get_product(sku)
                return [product] if product else []
            
            # Build search criteria for multiple products
            search_criteria = []
            
            if name:
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][field]=name")
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][value]={name}")
                search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][condition_type]=like")
            
            if category_id:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=category_id")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={category_id}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=eq")
            
            if status is not None:
                group_index = len([c for c in search_criteria if 'filter_groups' in c and 'filters' in c]) // 3
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][field]=status")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][value]={status}")
                search_criteria.append(f"searchCriteria[filter_groups][{group_index}][filters][0][condition_type]=eq")
            
            # Add pagination
            search_criteria.append(f"searchCriteria[pageSize]={limit}")
            search_criteria.append("searchCriteria[currentPage]=1")
            
            query_string = "&".join(search_criteria)
            products_response = await self.rest_client.get_products(query_params=query_string)
            
            if not products_response or 'items' not in products_response:
                self.logger.warning("No products found matching criteria")
                return []
            
            products = products_response['items']
            
            # Enrich products with additional data if store_id provided
            if store_id:
                enriched_products = []
                for product in products:
                    try:
                        # Get store-specific product data
                        store_product = await self.rest_client.get_product(product['sku'], store_id=store_id)
                        enriched_products.append(store_product or product)
                    except Exception as e:
                        self.logger.warning(f"Failed to get store-specific data for product {product.get('sku')}: {e}")
                        enriched_products.append(product)
                products = enriched_products
            
            self.logger.info(f"Successfully extracted {len(products)} products from Magento")
            return products
            
        except Exception as e:
            self.logger.error(f"Failed to extract product data: {e}")
            raise MagentoDataExtractionError(f"Product data extraction failed: {e}")
    
    async def extract_order_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        store_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract order analytics and statistics.
        
        Args:
            date_from: Start date for analytics
            date_to: End date for analytics
            store_id: Store ID for multi-store analytics
            
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
                store_id=store_id,
                limit=1000  # Increased limit for analytics
            )
            
            # Calculate analytics
            total_orders = len(orders)
            total_revenue = sum(float(order.get('grand_total', 0)) for order in orders)
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Status breakdown
            status_breakdown = {}
            for order in orders:
                status = order.get('status', 'unknown')
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            # Payment method breakdown
            payment_methods = {}
            for order in orders:
                method = order.get('payment', {}).get('method', 'unknown')
                payment_methods[method] = payment_methods.get(method, 0) + 1
            
            # Top products
            product_sales = {}
            for order in orders:
                for item in order.get('items', []):
                    sku = item.get('sku', 'unknown')
                    qty = float(item.get('qty_ordered', 0))
                    product_sales[sku] = product_sales.get(sku, 0) + qty
            
            top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:10]
            
            analytics = {
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                },
                'store_id': store_id,
                'summary': {
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'average_order_value': average_order_value
                },
                'breakdowns': {
                    'by_status': status_breakdown,
                    'by_payment_method': payment_methods
                },
                'top_products': [{'sku': sku, 'quantity_sold': qty} for sku, qty in top_products]
            }
            
            self.logger.info(f"Successfully generated analytics for {total_orders} orders")
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to extract order analytics: {e}")
            raise MagentoDataExtractionError(f"Order analytics extraction failed: {e}")
    
    async def extract_inventory_data(
        self,
        sku: Optional[str] = None,
        low_stock_threshold: Optional[float] = None,
        store_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract inventory/stock data from Magento.
        
        Args:
            sku: Specific product SKU
            low_stock_threshold: Threshold for low stock filtering
            store_id: Store ID for multi-store inventory
            
        Returns:
            List of inventory data dictionaries
        """
        try:
            inventory_data = []
            
            if sku:
                # Get specific product inventory
                try:
                    stock_item = await self.rest_client.get(f"stockItems/{sku}")
                    inventory_data.append(stock_item)
                except Exception as e:
                    self.logger.warning(f"Failed to get inventory for SKU {sku}: {e}")
            else:
                # Get all inventory items (this might be limited by Magento API)
                try:
                    search_criteria = []
                    
                    if low_stock_threshold is not None:
                        search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][field]=qty")
                        search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][value]={low_stock_threshold}")
                        search_criteria.append(f"searchCriteria[filter_groups][0][filters][0][condition_type]=lt")
                    
                    search_criteria.append("searchCriteria[pageSize]=100")
                    query_string = "&".join(search_criteria)
                    
                    response = await self.rest_client.get("stockItems", query_params=query_string)
                    if response and 'items' in response:
                        inventory_data = response['items']
                except Exception as e:
                    self.logger.warning(f"Failed to get bulk inventory data: {e}")
            
            self.logger.info(f"Successfully extracted inventory data for {len(inventory_data)} items")
            return inventory_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract inventory data: {e}")
            raise MagentoDataExtractionError(f"Inventory data extraction failed: {e}")
    
    async def extract_category_data(
        self,
        category_id: Optional[int] = None,
        parent_id: Optional[int] = None,
        store_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract category data from Magento.
        
        Args:
            category_id: Specific category ID
            parent_id: Parent category ID for hierarchy filtering
            store_id: Store ID for multi-store categories
            
        Returns:
            List of category data dictionaries
        """
        try:
            if category_id:
                # Get specific category
                category = await self.rest_client.get(f"categories/{category_id}")
                return [category] if category else []
            
            # Get category tree or filtered categories
            categories_response = await self.rest_client.get("categories")
            
            categories = []
            if categories_response:
                # Extract categories from tree structure
                def extract_categories_recursive(cat_data):
                    if isinstance(cat_data, dict):
                        categories.append(cat_data)
                        for child in cat_data.get('children_data', []):
                            extract_categories_recursive(child)
                
                extract_categories_recursive(categories_response)
            
            # Filter by parent_id if specified
            if parent_id is not None:
                categories = [cat for cat in categories if cat.get('parent_id') == parent_id]
            
            self.logger.info(f"Successfully extracted {len(categories)} categories from Magento")
            return categories
            
        except Exception as e:
            self.logger.error(f"Failed to extract category data: {e}")
            raise MagentoDataExtractionError(f"Category data extraction failed: {e}")