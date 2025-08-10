"""
Cin7 Data Extractor
Extracts and processes data from Cin7 inventory management system.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from .rest_client import Cin7RestClient
from .exceptions import (
    Cin7DataError,
    Cin7ProductNotFoundError,
    Cin7StockLocationNotFoundError,
    Cin7ValidationError
)


logger = logging.getLogger(__name__)


class Cin7DataExtractor:
    """
    Extracts and processes data from Cin7 inventory system.
    
    Handles data retrieval, validation, and preprocessing for various
    Cin7 entities including products, stock, orders, and suppliers.
    """
    
    def __init__(self, rest_client: Cin7RestClient):
        """
        Initialize Cin7 data extractor.
        
        Args:
            rest_client: Cin7 REST API client
        """
        self.rest_client = rest_client
    
    # Product Data Extraction
    
    async def extract_products(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all products from Cin7.
        
        Args:
            filters: Optional filters to apply
            include_inactive: Whether to include inactive products
            limit: Maximum number of products to extract
            
        Returns:
            List of product data
        """
        logger.info("Extracting products from Cin7")
        
        products = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build where clause
                where_conditions = []
                
                if not include_inactive:
                    where_conditions.append("IsActive = true")
                
                if filters:
                    for key, value in filters.items():
                        if key == "category":
                            where_conditions.append(f"Category = '{value}'")
                        elif key == "min_price":
                            where_conditions.append(f"SellingPrice >= {value}")
                        elif key == "max_price":
                            where_conditions.append(f"SellingPrice <= {value}")
                        elif key == "updated_since":
                            where_conditions.append(f"LastModified >= '{value}'")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else None
                
                # Get page of products
                response = await self.rest_client.get_products(
                    page=page,
                    limit=page_size,
                    where=where_clause,
                    order="LastModified DESC"
                )
                
                page_products = response.get("data", [])
                if not page_products:
                    break
                
                products.extend(page_products)
                
                # Check if we've reached the limit
                if limit and len(products) >= limit:
                    products = products[:limit]
                    break
                
                # Check if there are more pages
                if len(page_products) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(products)} products from Cin7")
            return products
            
        except Exception as e:
            logger.error(f"Failed to extract products: {e}")
            raise Cin7DataError(f"Product extraction failed: {str(e)}")
    
    async def extract_product(self, product_id: str) -> Dict[str, Any]:
        """
        Extract a specific product from Cin7.
        
        Args:
            product_id: Cin7 product ID
            
        Returns:
            Product data
        """
        try:
            product = await self.rest_client.get_product(product_id)
            
            if not product:
                raise Cin7ProductNotFoundError(f"Product {product_id} not found")
            
            logger.debug(f"Extracted product {product_id}")
            return product
            
        except Exception as e:
            logger.error(f"Failed to extract product {product_id}: {e}")
            raise
    
    # Stock Data Extraction
    
    async def extract_stock_levels(
        self,
        location_ids: Optional[List[str]] = None,
        product_ids: Optional[List[str]] = None,
        low_stock_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract stock levels from Cin7.
        
        Args:
            location_ids: Optional list of location IDs to filter
            product_ids: Optional list of product IDs to filter
            low_stock_only: Only include low stock items
            
        Returns:
            List of stock level data
        """
        logger.info("Extracting stock levels from Cin7")
        
        stock_levels = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build where clause
                where_conditions = []
                
                if location_ids:
                    location_filter = " OR ".join([f"LocationId = {loc_id}" for loc_id in location_ids])
                    where_conditions.append(f"({location_filter})")
                
                if product_ids:
                    product_filter = " OR ".join([f"ProductId = {prod_id}" for prod_id in product_ids])
                    where_conditions.append(f"({product_filter})")
                
                if low_stock_only:
                    where_conditions.append("QtyOnHand <= ReorderPoint")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else None
                
                # Get page of stock data
                response = await self.rest_client.get_stock_on_hand(
                    page=page,
                    limit=page_size,
                    where=where_clause
                )
                
                page_stock = response.get("data", [])
                if not page_stock:
                    break
                
                stock_levels.extend(page_stock)
                
                # Check if there are more pages
                if len(page_stock) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(stock_levels)} stock level records from Cin7")
            return stock_levels
            
        except Exception as e:
            logger.error(f"Failed to extract stock levels: {e}")
            raise Cin7DataError(f"Stock level extraction failed: {str(e)}")
    
    async def extract_stock_movements(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        product_ids: Optional[List[str]] = None,
        movement_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract stock movements from Cin7.
        
        Args:
            date_from: Start date for movements
            date_to: End date for movements  
            product_ids: Optional list of product IDs to filter
            movement_types: Optional list of movement types to filter
            
        Returns:
            List of stock movement data
        """
        logger.info("Extracting stock movements from Cin7")
        
        movements = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build where clause
                where_conditions = []
                
                if date_from:
                    where_conditions.append(f"CreatedDate >= '{date_from.isoformat()}'")
                
                if date_to:
                    where_conditions.append(f"CreatedDate <= '{date_to.isoformat()}'")
                
                if product_ids:
                    product_filter = " OR ".join([f"ProductId = {prod_id}" for prod_id in product_ids])
                    where_conditions.append(f"({product_filter})")
                
                if movement_types:
                    type_filter = " OR ".join([f"MovementType = '{mtype}'" for mtype in movement_types])
                    where_conditions.append(f"({type_filter})")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else None
                
                # Get page of movements
                response = await self.rest_client.get_stock_movements(
                    page=page,
                    limit=page_size,
                    where=where_clause,
                    order="CreatedDate DESC"
                )
                
                page_movements = response.get("data", [])
                if not page_movements:
                    break
                
                movements.extend(page_movements)
                
                # Check if there are more pages
                if len(page_movements) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(movements)} stock movements from Cin7")
            return movements
            
        except Exception as e:
            logger.error(f"Failed to extract stock movements: {e}")
            raise Cin7DataError(f"Stock movement extraction failed: {str(e)}")
    
    # Order Data Extraction
    
    async def extract_purchase_orders(
        self,
        status_filter: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        supplier_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract purchase orders from Cin7.
        
        Args:
            status_filter: Optional list of statuses to filter
            date_from: Start date for orders
            date_to: End date for orders
            supplier_ids: Optional list of supplier IDs to filter
            
        Returns:
            List of purchase order data
        """
        logger.info("Extracting purchase orders from Cin7")
        
        orders = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build where clause
                where_conditions = []
                
                if status_filter:
                    status_str = " OR ".join([f"Status = '{status}'" for status in status_filter])
                    where_conditions.append(f"({status_str})")
                
                if date_from:
                    where_conditions.append(f"CreatedDate >= '{date_from.isoformat()}'")
                
                if date_to:
                    where_conditions.append(f"CreatedDate <= '{date_to.isoformat()}'")
                
                if supplier_ids:
                    supplier_filter = " OR ".join([f"SupplierId = {sup_id}" for sup_id in supplier_ids])
                    where_conditions.append(f"({supplier_filter})")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else None
                
                # Get page of orders
                response = await self.rest_client.get_purchase_orders(
                    page=page,
                    limit=page_size,
                    where=where_clause,
                    order="CreatedDate DESC"
                )
                
                page_orders = response.get("data", [])
                if not page_orders:
                    break
                
                orders.extend(page_orders)
                
                # Check if there are more pages
                if len(page_orders) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(orders)} purchase orders from Cin7")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to extract purchase orders: {e}")
            raise Cin7DataError(f"Purchase order extraction failed: {str(e)}")
    
    async def extract_sales_orders(
        self,
        status_filter: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        customer_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract sales orders from Cin7.
        
        Args:
            status_filter: Optional list of statuses to filter
            date_from: Start date for orders
            date_to: End date for orders
            customer_ids: Optional list of customer IDs to filter
            
        Returns:
            List of sales order data
        """
        logger.info("Extracting sales orders from Cin7")
        
        orders = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build where clause
                where_conditions = []
                
                if status_filter:
                    status_str = " OR ".join([f"Status = '{status}'" for status in status_filter])
                    where_conditions.append(f"({status_str})")
                
                if date_from:
                    where_conditions.append(f"CreatedDate >= '{date_from.isoformat()}'")
                
                if date_to:
                    where_conditions.append(f"CreatedDate <= '{date_to.isoformat()}'")
                
                if customer_ids:
                    customer_filter = " OR ".join([f"CustomerId = {cust_id}" for cust_id in customer_ids])
                    where_conditions.append(f"({customer_filter})")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else None
                
                # Get page of orders
                response = await self.rest_client.get_sales_orders(
                    page=page,
                    limit=page_size,
                    where=where_clause,
                    order="CreatedDate DESC"
                )
                
                page_orders = response.get("data", [])
                if not page_orders:
                    break
                
                orders.extend(page_orders)
                
                # Check if there are more pages
                if len(page_orders) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(orders)} sales orders from Cin7")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to extract sales orders: {e}")
            raise Cin7DataError(f"Sales order extraction failed: {str(e)}")
    
    # Location Data Extraction
    
    async def extract_locations(self) -> List[Dict[str, Any]]:
        """
        Extract all stock locations from Cin7.
        
        Returns:
            List of location data
        """
        logger.info("Extracting locations from Cin7")
        
        try:
            response = await self.rest_client.get_stock_locations()
            locations = response.get("data", [])
            
            logger.info(f"Extracted {len(locations)} locations from Cin7")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to extract locations: {e}")
            raise Cin7DataError(f"Location extraction failed: {str(e)}")
    
    # Supplier Data Extraction
    
    async def extract_suppliers(
        self,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract suppliers from Cin7.
        
        Args:
            active_only: Only include active suppliers
            limit: Maximum number of suppliers to extract
            
        Returns:
            List of supplier data
        """
        logger.info("Extracting suppliers from Cin7")
        
        suppliers = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build where clause
                where_clause = "IsActive = true" if active_only else None
                
                # Get page of suppliers
                response = await self.rest_client.get_suppliers(
                    page=page,
                    limit=page_size,
                    where=where_clause
                )
                
                page_suppliers = response.get("data", [])
                if not page_suppliers:
                    break
                
                suppliers.extend(page_suppliers)
                
                # Check if we've reached the limit
                if limit and len(suppliers) >= limit:
                    suppliers = suppliers[:limit]
                    break
                
                # Check if there are more pages
                if len(page_suppliers) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(suppliers)} suppliers from Cin7")
            return suppliers
            
        except Exception as e:
            logger.error(f"Failed to extract suppliers: {e}")
            raise Cin7DataError(f"Supplier extraction failed: {str(e)}")
    
    # Validation Methods
    
    def validate_product_data(self, product: Dict[str, Any]) -> bool:
        """
        Validate product data structure.
        
        Args:
            product: Product data to validate
            
        Returns:
            True if valid
            
        Raises:
            Cin7ValidationError: If data is invalid
        """
        required_fields = ["Id", "Name", "Type"]
        
        for field in required_fields:
            if field not in product:
                raise Cin7ValidationError(f"Missing required field: {field}")
        
        return True
    
    def validate_stock_data(self, stock: Dict[str, Any]) -> bool:
        """
        Validate stock data structure.
        
        Args:
            stock: Stock data to validate
            
        Returns:
            True if valid
            
        Raises:
            Cin7ValidationError: If data is invalid
        """
        required_fields = ["ProductId", "LocationId", "QtyOnHand"]
        
        for field in required_fields:
            if field not in stock:
                raise Cin7ValidationError(f"Missing required field: {field}")
        
        return True
    
    # Reporting Methods
    
    async def extract_stock_valuation(
        self,
        location_id: Optional[str] = None,
        as_at_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract stock valuation report from Cin7.
        
        Args:
            location_id: Optional location to filter
            as_at_date: Optional date for valuation
            
        Returns:
            Stock valuation data
        """
        logger.info("Extracting stock valuation from Cin7")
        
        try:
            valuation = await self.rest_client.get_stock_valuation(
                location_id=location_id,
                as_at_date=as_at_date
            )
            
            logger.info("Successfully extracted stock valuation")
            return valuation
            
        except Exception as e:
            logger.error(f"Failed to extract stock valuation: {e}")
            raise Cin7DataError(f"Stock valuation extraction failed: {str(e)}")
    
    async def extract_low_stock_report(
        self,
        location_id: Optional[str] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Extract low stock report from Cin7.
        
        Args:
            location_id: Optional location to filter
            threshold: Optional threshold for low stock
            
        Returns:
            Low stock report data
        """
        logger.info("Extracting low stock report from Cin7")
        
        try:
            report = await self.rest_client.get_low_stock_report(
                location_id=location_id,
                threshold=threshold
            )
            
            logger.info("Successfully extracted low stock report")
            return report
            
        except Exception as e:
            logger.error(f"Failed to extract low stock report: {e}")
            raise Cin7DataError(f"Low stock report extraction failed: {str(e)}")