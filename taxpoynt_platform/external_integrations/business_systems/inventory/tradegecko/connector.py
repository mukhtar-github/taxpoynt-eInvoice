"""
TradeGecko Inventory Connector
Main connector class for TradeGecko inventory management integration.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from ....connector_framework.inventory.base_inventory_connector import BaseInventoryConnector
from .auth import TradeGeckoAuthManager
from .rest_client import TradeGeckoRestClient
from .data_extractor import TradeGeckoDataExtractor
from .stock_transformer import TradeGeckoStockTransformer
from .exceptions import (
    TradeGeckoException,
    TradeGeckoConfigurationError,
    TradeGeckoConnectionError,
    TradeGeckoAuthenticationError
)


logger = logging.getLogger(__name__)


class TradeGeckoInventoryConnector(BaseInventoryConnector):
    """
    TradeGecko inventory management connector.
    
    Provides comprehensive integration with TradeGecko inventory system including
    product management, variant tracking, stock management, and order processing.
    """
    
    platform_name = "tradegecko"
    display_name = "TradeGecko Inventory Management"
    
    def __init__(
        self,
        access_token: str,
        sandbox: bool = True,
        currency_code: str = "NGN",
        **kwargs
    ):
        """
        Initialize TradeGecko inventory connector.
        
        Args:
            access_token: TradeGecko API access token
            sandbox: Whether to use sandbox environment
            currency_code: Default currency code
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        
        # Validate required configuration
        if not access_token:
            raise TradeGeckoConfigurationError("access_token is required")
        
        self.access_token = access_token
        self.sandbox = sandbox
        self.currency_code = currency_code
        
        # Initialize components
        self.auth_manager: Optional[TradeGeckoAuthManager] = None
        self.rest_client: Optional[TradeGeckoRestClient] = None
        self.data_extractor: Optional[TradeGeckoDataExtractor] = None
        self.stock_transformer: Optional[TradeGeckoStockTransformer] = None
        
        # Connection state
        self._is_connected = False
        self._last_sync: Optional[datetime] = None
    
    async def connect(self) -> Dict[str, Any]:
        """
        Connect to TradeGecko inventory system.
        
        Returns:
            Connection result with account information
        """
        try:
            logger.info(f"Connecting to TradeGecko ({'sandbox' if self.sandbox else 'production'})")
            
            # Initialize auth manager
            self.auth_manager = TradeGeckoAuthManager(
                access_token=self.access_token,
                sandbox=self.sandbox
            )
            
            # Initialize and test connection
            async with self.auth_manager as auth:
                auth_result = await auth.authenticate()
                
                # Initialize other components
                self.rest_client = TradeGeckoRestClient(auth)
                self.data_extractor = TradeGeckoDataExtractor(self.rest_client)
                self.stock_transformer = TradeGeckoStockTransformer(self.currency_code)
                
                self._is_connected = True
                
                logger.info("Successfully connected to TradeGecko")
                
                return {
                    "success": True,
                    "platform": self.platform_name,
                    "environment": "sandbox" if self.sandbox else "production",
                    "account_info": auth_result.get("account_info", {}),
                    "connected_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to connect to TradeGecko: {e}")
            self._is_connected = False
            raise TradeGeckoConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from TradeGecko inventory system.
        
        Returns:
            True if disconnection successful
        """
        try:
            if self.auth_manager:
                self.auth_manager.disconnect()
            
            self.auth_manager = None
            self.rest_client = None
            self.data_extractor = None
            self.stock_transformer = None
            self._is_connected = False
            
            logger.info("Disconnected from TradeGecko")
            return True
            
        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to TradeGecko inventory system.
        
        Returns:
            Connection test results
        """
        if not self.auth_manager:
            return {
                "success": False,
                "status": "not_connected",
                "error": "Not connected to TradeGecko"
            }
        
        try:
            async with self.auth_manager as auth:
                return await auth.test_connection()
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "status": "failed",
                "error": str(e)
            }
    
    def is_connected(self) -> bool:
        """
        Check if connected to TradeGecko.
        
        Returns:
            True if connected, False otherwise
        """
        return self._is_connected and self.auth_manager is not None
    
    # Product Management
    
    async def get_products(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_variants: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from TradeGecko inventory.
        
        Args:
            filters: Optional filters to apply
            include_variants: Whether to include product variants
            limit: Maximum number of products to return
            
        Returns:
            List of standardized product data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw products
            raw_products = await self.data_extractor.extract_products(
                filters=filters,
                include_variants=include_variants,
                limit=limit
            )
            
            # Transform to standard format
            products = self.stock_transformer.transform_products(raw_products)
            
            logger.info(f"Retrieved {len(products)} products from TradeGecko")
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            raise
    
    async def get_product(self, product_id: str, include_variants: bool = True) -> Dict[str, Any]:
        """
        Get a specific product from TradeGecko.
        
        Args:
            product_id: TradeGecko product ID
            include_variants: Whether to include product variants
            
        Returns:
            Standardized product data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw product
            raw_product = await self.data_extractor.extract_product(
                product_id, 
                include_variants=include_variants
            )
            
            # Transform to standard format
            product = self.stock_transformer.transform_product(raw_product)
            
            logger.debug(f"Retrieved product {product_id} from TradeGecko")
            return product
            
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            raise
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product in TradeGecko.
        
        Args:
            product_data: Standardized product data
            
        Returns:
            Created product data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Convert standard format to TradeGecko format
            tradegecko_product_data = self._convert_to_tradegecko_product(product_data)
            
            # Create product via API
            async with self.rest_client as client:
                created_product = await client.create_product(tradegecko_product_data)
            
            # Transform back to standard format
            result = self.stock_transformer.transform_product(created_product.get("product", {}))
            
            logger.info(f"Created product in TradeGecko: {result.get('id')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            raise
    
    # Variant Management
    
    async def get_variants(
        self,
        product_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get product variants from TradeGecko.
        
        Args:
            product_id: Optional product ID to filter variants
            limit: Maximum number of variants to return
            
        Returns:
            List of standardized variant data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw variants
            raw_variants = await self.data_extractor.extract_variants(
                product_id=product_id,
                limit=limit
            )
            
            # Transform to standard format
            variants = [
                self.stock_transformer.transform_variant(variant)
                for variant in raw_variants
            ]
            
            logger.info(f"Retrieved {len(variants)} variants from TradeGecko")
            return variants
            
        except Exception as e:
            logger.error(f"Failed to get variants: {e}")
            raise
    
    # Stock Management
    
    async def get_stock_levels(
        self,
        location_id: Optional[str] = None,
        variant_ids: Optional[List[str]] = None,
        include_zero_stock: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get stock levels from TradeGecko.
        
        Args:
            location_id: Optional location ID to filter
            variant_ids: Optional list of variant IDs to filter
            include_zero_stock: Whether to include zero stock items
            
        Returns:
            List of standardized stock level data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw stock levels
            raw_stock_levels = await self.data_extractor.extract_stock_levels(
                location_id=location_id,
                variant_ids=variant_ids,
                include_zero_stock=include_zero_stock
            )
            
            # Transform to standard format
            stock_levels = self.stock_transformer.transform_stock_levels(raw_stock_levels)
            
            logger.info(f"Retrieved {len(stock_levels)} stock levels from TradeGecko")
            return stock_levels
            
        except Exception as e:
            logger.error(f"Failed to get stock levels: {e}")
            raise
    
    async def get_stock_movements(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        location_id: Optional[str] = None,
        variant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get stock movements from TradeGecko.
        
        Args:
            date_from: Start date for movements
            date_to: End date for movements
            location_id: Optional location ID to filter
            variant_id: Optional variant ID to filter
            
        Returns:
            List of standardized stock movement data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw stock movements
            raw_movements = await self.data_extractor.extract_stock_movements(
                date_from=date_from,
                date_to=date_to,
                location_id=location_id,
                variant_id=variant_id
            )
            
            # Transform to standard format
            movements = [
                self.stock_transformer.transform_stock_movement(movement)
                for movement in raw_movements
            ]
            
            logger.info(f"Retrieved {len(movements)} stock movements from TradeGecko")
            return movements
            
        except Exception as e:
            logger.error(f"Failed to get stock movements: {e}")
            raise
    
    async def create_stock_adjustment(self, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a stock adjustment in TradeGecko.
        
        Args:
            adjustment_data: Stock adjustment data
            
        Returns:
            Created adjustment data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Convert standard format to TradeGecko format
            tradegecko_adjustment = self._convert_to_tradegecko_adjustment(adjustment_data)
            
            # Create adjustment via API
            async with self.rest_client as client:
                created_adjustment = await client.create_stock_adjustment(tradegecko_adjustment)
            
            logger.info(f"Created stock adjustment in TradeGecko")
            return created_adjustment
            
        except Exception as e:
            logger.error(f"Failed to create stock adjustment: {e}")
            raise
    
    # Order Management
    
    async def get_purchase_orders(
        self,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get purchase orders from TradeGecko.
        
        Args:
            status_filter: Optional status filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of standardized purchase order data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw purchase orders
            raw_orders = await self.data_extractor.extract_purchase_orders(
                status_filter=status_filter,
                date_from=date_from,
                date_to=date_to
            )
            
            # Transform to standard format
            orders = [
                self.stock_transformer.transform_purchase_order(order)
                for order in raw_orders
            ]
            
            logger.info(f"Retrieved {len(orders)} purchase orders from TradeGecko")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get purchase orders: {e}")
            raise
    
    async def get_sales_orders(
        self,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sales orders from TradeGecko.
        
        Args:
            status_filter: Optional status filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of standardized sales order data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw sales orders
            raw_orders = await self.data_extractor.extract_sales_orders(
                status_filter=status_filter,
                date_from=date_from,
                date_to=date_to
            )
            
            # Transform to standard format (using purchase order transformer as base)
            orders = [
                self.stock_transformer.transform_purchase_order(order)  # Similar structure
                for order in raw_orders
            ]
            
            logger.info(f"Retrieved {len(orders)} sales orders from TradeGecko")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get sales orders: {e}")
            raise
    
    # Supplier Management
    
    async def get_suppliers(self) -> List[Dict[str, Any]]:
        """
        Get suppliers from TradeGecko.
        
        Returns:
            List of standardized supplier data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw suppliers
            raw_suppliers = await self.data_extractor.extract_suppliers()
            
            # Transform to standard format
            suppliers = [
                self.stock_transformer.transform_supplier(supplier)
                for supplier in raw_suppliers
            ]
            
            logger.info(f"Retrieved {len(suppliers)} suppliers from TradeGecko")
            return suppliers
            
        except Exception as e:
            logger.error(f"Failed to get suppliers: {e}")
            raise
    
    # Location Management
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """
        Get all locations from TradeGecko.
        
        Returns:
            List of standardized location data
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            # Extract raw locations
            raw_locations = await self.data_extractor.extract_locations()
            
            # Transform to standard format
            locations = [
                self.stock_transformer.transform_location(location)
                for location in raw_locations
            ]
            
            logger.info(f"Retrieved {len(locations)} locations from TradeGecko")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to get locations: {e}")
            raise
    
    # Synchronization
    
    async def sync_all_data(self) -> Dict[str, Any]:
        """
        Sync all data from TradeGecko.
        
        Returns:
            Synchronization results
        """
        if not self.is_connected():
            raise TradeGeckoConnectionError("Not connected to TradeGecko")
        
        try:
            logger.info("Starting full data sync from TradeGecko")
            
            sync_results = {
                "started_at": datetime.utcnow().isoformat(),
                "products": 0,
                "variants": 0,
                "stock_levels": 0,
                "locations": 0,
                "suppliers": 0,
                "errors": []
            }
            
            # Sync products
            try:
                products = await self.get_products()
                sync_results["products"] = len(products)
            except Exception as e:
                sync_results["errors"].append(f"Products sync failed: {str(e)}")
            
            # Sync variants
            try:
                variants = await self.get_variants()
                sync_results["variants"] = len(variants)
            except Exception as e:
                sync_results["errors"].append(f"Variants sync failed: {str(e)}")
            
            # Sync stock levels
            try:
                stock_levels = await self.get_stock_levels()
                sync_results["stock_levels"] = len(stock_levels)
            except Exception as e:
                sync_results["errors"].append(f"Stock levels sync failed: {str(e)}")
            
            # Sync locations
            try:
                locations = await self.get_locations()
                sync_results["locations"] = len(locations)
            except Exception as e:
                sync_results["errors"].append(f"Locations sync failed: {str(e)}")
            
            # Sync suppliers
            try:
                suppliers = await self.get_suppliers()
                sync_results["suppliers"] = len(suppliers)
            except Exception as e:
                sync_results["errors"].append(f"Suppliers sync failed: {str(e)}")
            
            self._last_sync = datetime.utcnow()
            sync_results["completed_at"] = self._last_sync.isoformat()
            sync_results["success"] = len(sync_results["errors"]) == 0
            
            logger.info(f"Completed data sync from TradeGecko: {sync_results}")
            return sync_results
            
        except Exception as e:
            logger.error(f"Failed to sync data from TradeGecko: {e}")
            raise
    
    # Helper Methods
    
    def _convert_to_tradegecko_product(self, standard_product: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard product format to TradeGecko format."""
        return {
            "name": standard_product.get("name", ""),
            "description": standard_product.get("description", ""),
            "product_type": "variant",  # Default to variant type
            "brand": standard_product.get("brand", ""),
            "tags": standard_product.get("category", ""),
            "product_status": "active" if standard_product.get("status") == "active" else "inactive"
        }
    
    def _convert_to_tradegecko_adjustment(self, standard_adjustment: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard adjustment format to TradeGecko format."""
        return {
            "variant_id": standard_adjustment.get("product_id"),
            "location_id": standard_adjustment.get("location_id"),
            "quantity": standard_adjustment.get("quantity", 0),
            "notes": standard_adjustment.get("notes", "")
        }
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the TradeGecko platform.
        
        Returns:
            Platform information
        """
        return {
            "platform": self.platform_name,
            "display_name": self.display_name,
            "environment": "sandbox" if self.sandbox else "production",
            "currency": self.currency_code,
            "is_connected": self.is_connected(),
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "capabilities": [
                "product_management",
                "variant_tracking",
                "stock_tracking",
                "order_management",
                "supplier_management",
                "location_management",
                "multi_channel",
                "fulfillment",
                "real_time_sync"
            ]
        }