"""
TradeGecko Data Extractor
Extracts and processes data from TradeGecko inventory management system.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from .rest_client import TradeGeckoRestClient
from .exceptions import (
    TradeGeckoDataError,
    TradeGeckoProductNotFoundError,
    TradeGeckoLocationNotFoundError,
    TradeGeckoValidationError
)


logger = logging.getLogger(__name__)


class TradeGeckoDataExtractor:
    """
    Extracts and processes data from TradeGecko inventory system.
    
    Handles data retrieval, validation, and preprocessing for various
    TradeGecko entities including products, variants, stock, orders, and suppliers.
    """
    
    def __init__(self, rest_client: TradeGeckoRestClient):
        """
        Initialize TradeGecko data extractor.
        
        Args:
            rest_client: TradeGecko REST API client
        """
        self.rest_client = rest_client
    
    # Product Data Extraction
    
    async def extract_products(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_variants: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all products from TradeGecko.
        
        Args:
            filters: Optional filters to apply
            include_variants: Whether to include product variants
            limit: Maximum number of products to extract
            
        Returns:
            List of product data with variants
        """
        logger.info("Extracting products from TradeGecko")
        
        products = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build request parameters
                params = {
                    "page": page,
                    "limit": page_size
                }
                
                if filters:
                    if "created_at_min" in filters:
                        params["created_at_min"] = filters["created_at_min"]
                    if "updated_at_min" in filters:
                        params["updated_at_min"] = filters["updated_at_min"]
                
                # Get page of products
                response = await self.rest_client.get_products(**params)
                
                page_products = response.get("products", [])
                if not page_products:
                    break
                
                # Include variants if requested
                if include_variants:
                    for product in page_products:
                        product_id = product.get("id")
                        if product_id:
                            try:
                                variants_response = await self.rest_client.get_variants(
                                    product_id=str(product_id)
                                )
                                product["variants"] = variants_response.get("variants", [])
                            except Exception as e:
                                logger.warning(f"Failed to get variants for product {product_id}: {e}")
                                product["variants"] = []
                
                products.extend(page_products)
                
                # Check if we've reached the limit
                if limit and len(products) >= limit:
                    products = products[:limit]
                    break
                
                # Check if there are more pages
                if len(page_products) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(products)} products from TradeGecko")
            return products
            
        except Exception as e:
            logger.error(f"Failed to extract products: {e}")
            raise TradeGeckoDataError(f"Product extraction failed: {str(e)}")
    
    async def extract_product(self, product_id: str, include_variants: bool = True) -> Dict[str, Any]:
        """
        Extract a specific product from TradeGecko.
        
        Args:
            product_id: TradeGecko product ID
            include_variants: Whether to include product variants
            
        Returns:
            Product data with variants
        """
        try:
            response = await self.rest_client.get_product(product_id)
            product = response.get("product", {})
            
            if not product:
                raise TradeGeckoProductNotFoundError(f"Product {product_id} not found")
            
            # Include variants if requested
            if include_variants:
                try:
                    variants_response = await self.rest_client.get_variants(
                        product_id=product_id
                    )
                    product["variants"] = variants_response.get("variants", [])
                except Exception as e:
                    logger.warning(f"Failed to get variants for product {product_id}: {e}")
                    product["variants"] = []
            
            logger.debug(f"Extracted product {product_id}")
            return product
            
        except Exception as e:
            logger.error(f"Failed to extract product {product_id}: {e}")
            raise
    
    # Variant Data Extraction
    
    async def extract_variants(
        self,
        product_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract product variants from TradeGecko.
        
        Args:
            product_id: Optional product ID to filter variants
            limit: Maximum number of variants to extract
            
        Returns:
            List of variant data
        """
        logger.info("Extracting variants from TradeGecko")
        
        variants = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Get page of variants
                response = await self.rest_client.get_variants(
                    page=page,
                    limit=page_size,
                    product_id=product_id
                )
                
                page_variants = response.get("variants", [])
                if not page_variants:
                    break
                
                variants.extend(page_variants)
                
                # Check if we've reached the limit
                if limit and len(variants) >= limit:
                    variants = variants[:limit]
                    break
                
                # Check if there are more pages
                if len(page_variants) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(variants)} variants from TradeGecko")
            return variants
            
        except Exception as e:
            logger.error(f"Failed to extract variants: {e}")
            raise TradeGeckoDataError(f"Variant extraction failed: {str(e)}")
    
    # Stock Level Data Extraction
    
    async def extract_stock_levels(
        self,
        location_id: Optional[str] = None,
        variant_ids: Optional[List[str]] = None,
        include_zero_stock: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract stock levels from TradeGecko.
        
        Args:
            location_id: Optional location ID to filter
            variant_ids: Optional list of variant IDs to filter
            include_zero_stock: Whether to include zero stock items
            
        Returns:
            List of stock level data
        """
        logger.info("Extracting stock levels from TradeGecko")
        
        stock_levels = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Get page of stock levels
                response = await self.rest_client.get_stock_levels(
                    page=page,
                    limit=page_size,
                    location_id=location_id
                )
                
                page_stock = response.get("stock_levels", [])
                if not page_stock:
                    break
                
                # Filter by variant IDs if specified
                if variant_ids:
                    page_stock = [
                        stock for stock in page_stock
                        if str(stock.get("variant_id", "")) in variant_ids
                    ]
                
                # Filter zero stock if not included
                if not include_zero_stock:
                    page_stock = [
                        stock for stock in page_stock
                        if float(stock.get("stock_on_hand", 0)) > 0
                    ]
                
                stock_levels.extend(page_stock)
                
                # Check if there are more pages
                if len(page_stock) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(stock_levels)} stock levels from TradeGecko")
            return stock_levels
            
        except Exception as e:
            logger.error(f"Failed to extract stock levels: {e}")
            raise TradeGeckoDataError(f"Stock level extraction failed: {str(e)}")
    
    # Stock Movement Data Extraction
    
    async def extract_stock_movements(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        location_id: Optional[str] = None,
        variant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract stock movements from TradeGecko.
        
        Args:
            date_from: Start date for movements
            date_to: End date for movements
            location_id: Optional location ID to filter
            variant_id: Optional variant ID to filter
            
        Returns:
            List of stock movement data
        """
        logger.info("Extracting stock movements from TradeGecko")
        
        movements = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build request parameters
                params = {
                    "page": page,
                    "limit": page_size
                }
                
                if location_id:
                    params["location_id"] = location_id
                if variant_id:
                    params["variant_id"] = variant_id
                if date_from:
                    params["created_at_min"] = date_from.isoformat()
                if date_to:
                    params["created_at_max"] = date_to.isoformat()
                
                # Get page of movements
                response = await self.rest_client.get_stock_movements(**params)
                
                page_movements = response.get("stock_movements", [])
                if not page_movements:
                    break
                
                movements.extend(page_movements)
                
                # Check if there are more pages
                if len(page_movements) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(movements)} stock movements from TradeGecko")
            return movements
            
        except Exception as e:
            logger.error(f"Failed to extract stock movements: {e}")
            raise TradeGeckoDataError(f"Stock movement extraction failed: {str(e)}")
    
    # Order Data Extraction
    
    async def extract_purchase_orders(
        self,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract purchase orders from TradeGecko.
        
        Args:
            status_filter: Optional status filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of purchase order data
        """
        logger.info("Extracting purchase orders from TradeGecko")
        
        orders = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build request parameters
                params = {
                    "page": page,
                    "limit": page_size
                }
                
                if status_filter:
                    params["status"] = status_filter
                if date_from:
                    params["created_at_min"] = date_from.isoformat()
                if date_to:
                    params["updated_at_min"] = date_to.isoformat()
                
                # Get page of orders
                response = await self.rest_client.get_purchase_orders(**params)
                
                page_orders = response.get("purchase_orders", [])
                if not page_orders:
                    break
                
                orders.extend(page_orders)
                
                # Check if there are more pages
                if len(page_orders) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(orders)} purchase orders from TradeGecko")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to extract purchase orders: {e}")
            raise TradeGeckoDataError(f"Purchase order extraction failed: {str(e)}")
    
    async def extract_sales_orders(
        self,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract sales orders from TradeGecko.
        
        Args:
            status_filter: Optional status filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of sales order data
        """
        logger.info("Extracting sales orders from TradeGecko")
        
        orders = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Build request parameters
                params = {
                    "page": page,
                    "limit": page_size
                }
                
                if status_filter:
                    params["status"] = status_filter
                if date_from:
                    params["created_at_min"] = date_from.isoformat()
                if date_to:
                    params["updated_at_min"] = date_to.isoformat()
                
                # Get page of orders
                response = await self.rest_client.get_orders(**params)
                
                page_orders = response.get("orders", [])
                if not page_orders:
                    break
                
                orders.extend(page_orders)
                
                # Check if there are more pages
                if len(page_orders) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(orders)} sales orders from TradeGecko")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to extract sales orders: {e}")
            raise TradeGeckoDataError(f"Sales order extraction failed: {str(e)}")
    
    # Company Data Extraction
    
    async def extract_suppliers(self) -> List[Dict[str, Any]]:
        """
        Extract suppliers (companies with supplier type) from TradeGecko.
        
        Returns:
            List of supplier data
        """
        logger.info("Extracting suppliers from TradeGecko")
        
        suppliers = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Get page of companies with supplier type
                response = await self.rest_client.get_companies(
                    page=page,
                    limit=page_size,
                    company_type="supplier"
                )
                
                page_suppliers = response.get("companies", [])
                if not page_suppliers:
                    break
                
                suppliers.extend(page_suppliers)
                
                # Check if there are more pages
                if len(page_suppliers) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(suppliers)} suppliers from TradeGecko")
            return suppliers
            
        except Exception as e:
            logger.error(f"Failed to extract suppliers: {e}")
            raise TradeGeckoDataError(f"Supplier extraction failed: {str(e)}")
    
    # Location Data Extraction
    
    async def extract_locations(self) -> List[Dict[str, Any]]:
        """
        Extract all locations from TradeGecko.
        
        Returns:
            List of location data
        """
        logger.info("Extracting locations from TradeGecko")
        
        locations = []
        page = 1
        page_size = 250
        
        try:
            while True:
                # Get page of locations
                response = await self.rest_client.get_locations(
                    page=page,
                    limit=page_size
                )
                
                page_locations = response.get("locations", [])
                if not page_locations:
                    break
                
                locations.extend(page_locations)
                
                # Check if there are more pages
                if len(page_locations) < page_size:
                    break
                
                page += 1
            
            logger.info(f"Extracted {len(locations)} locations from TradeGecko")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to extract locations: {e}")
            raise TradeGeckoDataError(f"Location extraction failed: {str(e)}")
    
    # Validation Methods
    
    def validate_product_data(self, product: Dict[str, Any]) -> bool:
        """
        Validate product data structure.
        
        Args:
            product: Product data to validate
            
        Returns:
            True if valid
            
        Raises:
            TradeGeckoValidationError: If data is invalid
        """
        required_fields = ["id", "name"]
        
        for field in required_fields:
            if field not in product:
                raise TradeGeckoValidationError(f"Missing required field: {field}")
        
        return True
    
    def validate_stock_data(self, stock: Dict[str, Any]) -> bool:
        """
        Validate stock data structure.
        
        Args:
            stock: Stock data to validate
            
        Returns:
            True if valid
            
        Raises:
            TradeGeckoValidationError: If data is invalid
        """
        required_fields = ["variant_id", "location_id", "stock_on_hand"]
        
        for field in required_fields:
            if field not in stock:
                raise TradeGeckoValidationError(f"Missing required field: {field}")
        
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