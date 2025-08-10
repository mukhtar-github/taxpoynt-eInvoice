"""
Unleashed Data Extractor
Extracts and processes data from Unleashed inventory management system.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from .rest_client import UnleashedRestClient
from .exceptions import (
    UnleashedDataError,
    UnleashedProductNotFoundError,
    UnleashedWarehouseNotFoundError,
    UnleashedValidationError
)


logger = logging.getLogger(__name__)


class UnleashedDataExtractor:
    """
    Extracts and processes data from Unleashed inventory system.
    
    Handles data retrieval, validation, and preprocessing for various
    Unleashed entities including products, stock, orders, and suppliers.
    """
    
    def __init__(self, rest_client: UnleashedRestClient):
        """
        Initialize Unleashed data extractor.
        
        Args:
            rest_client: Unleashed REST API client
        """
        self.rest_client = rest_client
    
    # Product Data Extraction
    
    async def extract_products(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_stock: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all products from Unleashed.
        
        Args:
            filters: Optional filters to apply
            include_stock: Whether to include stock information
            limit: Maximum number of products to extract
            
        Returns:
            List of product data
        """
        logger.info("Extracting products from Unleashed")
        
        products = []
        page = 1
        page_size = 200
        
        try:
            while True:
                # Build request parameters
                params = {
                    "page": page,
                    "pageSize": page_size
                }
                
                if filters:
                    if "product_code" in filters:
                        params["productCode"] = filters["product_code"]
                    if "product_description" in filters:
                        params["productDescription"] = filters["product_description"]
                    if "modified_since" in filters:
                        params["modifiedSince"] = filters["modified_since"]
                
                # Get page of products
                response = await self.rest_client.get_products(**params)
                
                page_products = response.get("Items", [])
                if not page_products:
                    break
                
                # Include stock information if requested
                if include_stock:
                    for product in page_products:
                        product_code = product.get("ProductCode")
                        if product_code:
                            try:
                                stock_response = await self.rest_client.get_stock_on_hand(
                                    product_code=product_code
                                )
                                product["stock_levels"] = stock_response.get("Items", [])
                            except Exception as e:
                                logger.warning(f"Failed to get stock for product {product_code}: {e}")
                                product["stock_levels"] = []
                
                products.extend(page_products)
                
                # Check if we've reached the limit
                if limit and len(products) >= limit:
                    products = products[:limit]
                    break
                
                # Check if there are more pages
                if len(page_products) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(products)} products from Unleashed")
            return products
            
        except Exception as e:
            logger.error(f"Failed to extract products: {e}")
            raise UnleashedDataError(f"Product extraction failed: {str(e)}")
    
    async def extract_product(self, product_code: str, include_stock: bool = False) -> Dict[str, Any]:
        """
        Extract a specific product from Unleashed.
        
        Args:
            product_code: Unleashed product code
            include_stock: Whether to include stock information
            
        Returns:
            Product data
        """
        try:
            # Get products filtered by code
            response = await self.rest_client.get_products(
                product_code=product_code,
                page_size=1
            )
            
            products = response.get("Items", [])
            if not products:
                raise UnleashedProductNotFoundError(f"Product {product_code} not found")
            
            product = products[0]
            
            # Include stock information if requested
            if include_stock:
                try:
                    stock_response = await self.rest_client.get_stock_on_hand(
                        product_code=product_code
                    )
                    product["stock_levels"] = stock_response.get("Items", [])
                except Exception as e:
                    logger.warning(f"Failed to get stock for product {product_code}: {e}")
                    product["stock_levels"] = []
            
            logger.debug(f"Extracted product {product_code}")
            return product
            
        except Exception as e:
            logger.error(f"Failed to extract product {product_code}: {e}")
            raise
    
    # Stock Data Extraction
    
    async def extract_stock_on_hand(
        self,
        product_code: Optional[str] = None,
        warehouse_code: Optional[str] = None,
        include_zero_stock: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract stock on hand from Unleashed.
        
        Args:
            product_code: Optional product code to filter
            warehouse_code: Optional warehouse code to filter
            include_zero_stock: Whether to include zero stock items
            
        Returns:
            List of stock on hand data
        """
        logger.info("Extracting stock on hand from Unleashed")
        
        stock_items = []
        page = 1
        page_size = 200
        
        try:
            while True:
                # Get page of stock data
                response = await self.rest_client.get_stock_on_hand(
                    page=page,
                    page_size=page_size,
                    product_code=product_code,
                    warehouse_code=warehouse_code
                )
                
                page_stock = response.get("Items", [])
                if not page_stock:
                    break
                
                # Filter zero stock if not included
                if not include_zero_stock:
                    page_stock = [
                        stock for stock in page_stock
                        if float(stock.get("QtyOnHand", 0)) > 0
                    ]
                
                stock_items.extend(page_stock)
                
                # Check if there are more pages
                if len(page_stock) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(stock_items)} stock on hand records from Unleashed")
            return stock_items
            
        except Exception as e:
            logger.error(f"Failed to extract stock on hand: {e}")
            raise UnleashedDataError(f"Stock on hand extraction failed: {str(e)}")
    
    # Stock Movement Data Extraction
    
    async def extract_stock_movements(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        product_code: Optional[str] = None,
        warehouse_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract stock movements from Unleashed.
        
        Args:
            date_from: Start date for movements
            date_to: End date for movements
            product_code: Optional product code to filter
            warehouse_code: Optional warehouse code to filter
            
        Returns:
            List of stock movement data
        """
        logger.info("Extracting stock movements from Unleashed")
        
        movements = []
        page = 1
        page_size = 200
        
        try:
            while True:
                # Build request parameters
                params = {
                    "page": page,
                    "pageSize": page_size
                }
                
                if product_code:
                    params["productCode"] = product_code
                if warehouse_code:
                    params["warehouseCode"] = warehouse_code
                if date_from:
                    params["startDate"] = date_from.strftime("%Y-%m-%d")
                if date_to:
                    params["endDate"] = date_to.strftime("%Y-%m-%d")
                
                # Get page of movements
                response = await self.rest_client.get_stock_movements(**params)
                
                page_movements = response.get("Items", [])
                if not page_movements:
                    break
                
                movements.extend(page_movements)
                
                # Check if there are more pages
                if len(page_movements) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(movements)} stock movements from Unleashed")
            return movements
            
        except Exception as e:
            logger.error(f"Failed to extract stock movements: {e}")
            raise UnleashedDataError(f"Stock movement extraction failed: {str(e)}")
    
    # Purchase Order Data Extraction
    
    async def extract_purchase_orders(
        self,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract purchase orders from Unleashed.
        
        Args:
            status_filter: Optional status filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of purchase order data
        """
        logger.info("Extracting purchase orders from Unleashed")
        
        orders = []
        page = 1
        page_size = 200
        
        try:
            while True:
                # Build request parameters
                params = {
                    "page": page,
                    "pageSize": page_size
                }
                
                if status_filter:
                    params["orderStatus"] = status_filter
                if date_from:
                    params["startDate"] = date_from.strftime("%Y-%m-%d")
                if date_to:
                    params["endDate"] = date_to.strftime("%Y-%m-%d")
                
                # Get page of orders
                response = await self.rest_client.get_purchase_orders(**params)
                
                page_orders = response.get("Items", [])
                if not page_orders:
                    break
                
                orders.extend(page_orders)
                
                # Check if there are more pages
                if len(page_orders) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(orders)} purchase orders from Unleashed")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to extract purchase orders: {e}")
            raise UnleashedDataError(f"Purchase order extraction failed: {str(e)}")
    
    async def extract_purchase_order(self, order_guid: str) -> Dict[str, Any]:
        """
        Extract a specific purchase order from Unleashed.
        
        Args:
            order_guid: Purchase order GUID
            
        Returns:
            Purchase order data
        """
        try:
            order = await self.rest_client.get_purchase_order(order_guid)
            
            if not order:
                raise UnleashedPurchaseOrderNotFoundError(f"Purchase order {order_guid} not found")
            
            logger.debug(f"Extracted purchase order {order_guid}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to extract purchase order {order_guid}: {e}")
            raise
    
    # Sales Order Data Extraction
    
    async def extract_sales_orders(
        self,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract sales orders from Unleashed.
        
        Args:
            status_filter: Optional status filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of sales order data
        """
        logger.info("Extracting sales orders from Unleashed")
        
        orders = []
        page = 1
        page_size = 200
        
        try:
            while True:
                # Build request parameters
                params = {
                    "page": page,
                    "pageSize": page_size
                }
                
                if status_filter:
                    params["orderStatus"] = status_filter
                if date_from:
                    params["startDate"] = date_from.strftime("%Y-%m-%d")
                if date_to:
                    params["endDate"] = date_to.strftime("%Y-%m-%d")
                
                # Get page of orders
                response = await self.rest_client.get_sales_orders(**params)
                
                page_orders = response.get("Items", [])
                if not page_orders:
                    break
                
                orders.extend(page_orders)
                
                # Check if there are more pages
                if len(page_orders) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(orders)} sales orders from Unleashed")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to extract sales orders: {e}")
            raise UnleashedDataError(f"Sales order extraction failed: {str(e)}")
    
    # Supplier Data Extraction
    
    async def extract_suppliers(
        self,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract suppliers from Unleashed.
        
        Args:
            active_only: Only include active suppliers
            limit: Maximum number of suppliers to extract
            
        Returns:
            List of supplier data
        """
        logger.info("Extracting suppliers from Unleashed")
        
        suppliers = []
        page = 1
        page_size = 200
        
        try:
            while True:
                # Get page of suppliers
                response = await self.rest_client.get_suppliers(
                    page=page,
                    page_size=page_size
                )
                
                page_suppliers = response.get("Items", [])
                if not page_suppliers:
                    break
                
                # Filter inactive suppliers if needed
                if active_only:
                    page_suppliers = [
                        supplier for supplier in page_suppliers
                        if supplier.get("IsActive", True)
                    ]
                
                suppliers.extend(page_suppliers)
                
                # Check if we've reached the limit
                if limit and len(suppliers) >= limit:
                    suppliers = suppliers[:limit]
                    break
                
                # Check if there are more pages
                if len(page_suppliers) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(suppliers)} suppliers from Unleashed")
            return suppliers
            
        except Exception as e:
            logger.error(f"Failed to extract suppliers: {e}")
            raise UnleashedDataError(f"Supplier extraction failed: {str(e)}")
    
    # Customer Data Extraction
    
    async def extract_customers(
        self,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract customers from Unleashed.
        
        Args:
            active_only: Only include active customers
            limit: Maximum number of customers to extract
            
        Returns:
            List of customer data
        """
        logger.info("Extracting customers from Unleashed")
        
        customers = []
        page = 1
        page_size = 200
        
        try:
            while True:
                # Get page of customers
                response = await self.rest_client.get_customers(
                    page=page,
                    page_size=page_size
                )
                
                page_customers = response.get("Items", [])
                if not page_customers:
                    break
                
                # Filter inactive customers if needed
                if active_only:
                    page_customers = [
                        customer for customer in page_customers
                        if customer.get("IsActive", True)
                    ]
                
                customers.extend(page_customers)
                
                # Check if we've reached the limit
                if limit and len(customers) >= limit:
                    customers = customers[:limit]
                    break
                
                # Check if there are more pages
                if len(page_customers) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(customers)} customers from Unleashed")
            return customers
            
        except Exception as e:
            logger.error(f"Failed to extract customers: {e}")
            raise UnleashedDataError(f"Customer extraction failed: {str(e)}")
    
    # Warehouse Data Extraction
    
    async def extract_warehouses(self) -> List[Dict[str, Any]]:
        """
        Extract all warehouses from Unleashed.
        
        Returns:
            List of warehouse data
        """
        logger.info("Extracting warehouses from Unleashed")
        
        warehouses = []
        page = 1
        page_size = 200
        
        try:
            while True:
                # Get page of warehouses
                response = await self.rest_client.get_warehouses(
                    page=page,
                    page_size=page_size
                )
                
                page_warehouses = response.get("Items", [])
                if not page_warehouses:
                    break
                
                warehouses.extend(page_warehouses)
                
                # Check if there are more pages
                if len(page_warehouses) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(warehouses)} warehouses from Unleashed")
            return warehouses
            
        except Exception as e:
            logger.error(f"Failed to extract warehouses: {e}")
            raise UnleashedDataError(f"Warehouse extraction failed: {str(e)}")
    
    async def extract_warehouse(self, warehouse_code: str) -> Dict[str, Any]:
        """
        Extract a specific warehouse from Unleashed.
        
        Args:
            warehouse_code: Warehouse code
            
        Returns:
            Warehouse data
        """
        try:
            # Get warehouses filtered by code
            response = await self.rest_client.get_warehouses(
                warehouse_code=warehouse_code
            )
            
            warehouses = response.get("Items", [])
            if not warehouses:
                raise UnleashedWarehouseNotFoundError(f"Warehouse {warehouse_code} not found")
            
            warehouse = warehouses[0]
            
            logger.debug(f"Extracted warehouse {warehouse_code}")
            return warehouse
            
        except Exception as e:
            logger.error(f"Failed to extract warehouse {warehouse_code}: {e}")
            raise
    
    # Validation Methods
    
    def validate_product_data(self, product: Dict[str, Any]) -> bool:
        """
        Validate product data structure.
        
        Args:
            product: Product data to validate
            
        Returns:
            True if valid
            
        Raises:
            UnleashedValidationError: If data is invalid
        """
        required_fields = ["Guid", "ProductCode", "ProductDescription"]
        
        for field in required_fields:
            if field not in product:
                raise UnleashedValidationError(f"Missing required field: {field}")
        
        return True
    
    def validate_stock_data(self, stock: Dict[str, Any]) -> bool:
        """
        Validate stock data structure.
        
        Args:
            stock: Stock data to validate
            
        Returns:
            True if valid
            
        Raises:
            UnleashedValidationError: If data is invalid
        """
        required_fields = ["ProductCode", "WarehouseCode", "QtyOnHand"]
        
        for field in required_fields:
            if field not in stock:
                raise UnleashedValidationError(f"Missing required field: {field}")
        
        return True
    
    # Helper Methods
    
    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float."""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int."""
        try:
            if value is None:
                return 0
            return int(float(value))
        except (ValueError, TypeError):
            return 0