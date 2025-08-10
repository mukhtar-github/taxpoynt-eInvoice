"""
Unleashed Inventory Connector
Main connector class for Unleashed inventory management integration.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from ....connector_framework.inventory.base_inventory_connector import BaseInventoryConnector
from .auth import UnleashedAuthManager
from .rest_client import UnleashedRestClient
from .data_extractor import UnleashedDataExtractor
from .stock_transformer import UnleashedStockTransformer
from .exceptions import (
    UnleashedException,
    UnleashedConfigurationError,
    UnleashedConnectionError,
    UnleashedAuthenticationError
)


logger = logging.getLogger(__name__)


class UnleashedInventoryConnector(BaseInventoryConnector):
    """
    Unleashed inventory management connector.
    
    Provides comprehensive integration with Unleashed inventory system including
    product management, stock tracking, order processing, and warehouse management.
    """
    
    platform_name = "unleashed"
    display_name = "Unleashed Inventory Management"
    
    def __init__(
        self,
        api_id: str,
        api_key: str,
        currency_code: str = "NGN",
        **kwargs
    ):
        """
        Initialize Unleashed inventory connector.
        
        Args:
            api_id: Unleashed API ID
            api_key: Unleashed API key
            currency_code: Default currency code
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        
        # Validate required configuration
        if not all([api_id, api_key]):
            raise UnleashedConfigurationError("api_id and api_key are required")
        
        self.api_id = api_id
        self.api_key = api_key
        self.currency_code = currency_code
        
        # Initialize components
        self.auth_manager: Optional[UnleashedAuthManager] = None
        self.rest_client: Optional[UnleashedRestClient] = None
        self.data_extractor: Optional[UnleashedDataExtractor] = None
        self.stock_transformer: Optional[UnleashedStockTransformer] = None
        
        # Connection state
        self._is_connected = False
        self._last_sync: Optional[datetime] = None
    
    async def connect(self) -> Dict[str, Any]:
        """
        Connect to Unleashed inventory system.
        
        Returns:
            Connection result with account information
        """
        try:
            logger.info("Connecting to Unleashed")
            
            # Initialize auth manager
            self.auth_manager = UnleashedAuthManager(
                api_id=self.api_id,
                api_key=self.api_key
            )
            
            # Initialize and test connection
            async with self.auth_manager as auth:
                auth_result = await auth.authenticate()
                
                # Initialize other components
                self.rest_client = UnleashedRestClient(auth)
                self.data_extractor = UnleashedDataExtractor(self.rest_client)
                self.stock_transformer = UnleashedStockTransformer(self.currency_code)
                
                self._is_connected = True
                
                logger.info("Successfully connected to Unleashed")
                
                return {
                    "success": True,
                    "platform": self.platform_name,
                    "account_info": auth_result.get("account_info", {}),
                    "connected_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to connect to Unleashed: {e}")
            self._is_connected = False
            raise UnleashedConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Unleashed inventory system.
        
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
            
            logger.info("Disconnected from Unleashed")
            return True
            
        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Unleashed inventory system.
        
        Returns:
            Connection test results
        """
        if not self.auth_manager:
            return {
                "success": False,
                "status": "not_connected",
                "error": "Not connected to Unleashed"
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
        Check if connected to Unleashed.
        
        Returns:
            True if connected, False otherwise
        """
        return self._is_connected and self.auth_manager is not None
    
    # Product Management
    
    async def get_products(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_stock: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from Unleashed inventory.
        
        Args:
            filters: Optional filters to apply
            include_stock: Whether to include stock information
            limit: Maximum number of products to return
            
        Returns:
            List of standardized product data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw products
            raw_products = await self.data_extractor.extract_products(
                filters=filters,
                include_stock=include_stock,
                limit=limit
            )
            
            # Transform to standard format
            products = self.stock_transformer.transform_products(raw_products)
            
            logger.info(f"Retrieved {len(products)} products from Unleashed")
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            raise
    
    async def get_product(self, product_code: str, include_stock: bool = False) -> Dict[str, Any]:
        """
        Get a specific product from Unleashed.
        
        Args:
            product_code: Unleashed product code
            include_stock: Whether to include stock information
            
        Returns:
            Standardized product data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw product
            raw_product = await self.data_extractor.extract_product(
                product_code, 
                include_stock=include_stock
            )
            
            # Transform to standard format
            product = self.stock_transformer.transform_product(raw_product)
            
            logger.debug(f"Retrieved product {product_code} from Unleashed")
            return product
            
        except Exception as e:
            logger.error(f"Failed to get product {product_code}: {e}")
            raise
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product in Unleashed.
        
        Args:
            product_data: Standardized product data
            
        Returns:
            Created product data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Convert standard format to Unleashed format
            unleashed_product_data = self._convert_to_unleashed_product(product_data)
            
            # Create product via API
            async with self.rest_client as client:
                created_product = await client.create_product(unleashed_product_data)
            
            # Transform back to standard format
            result = self.stock_transformer.transform_product(created_product)
            
            logger.info(f"Created product in Unleashed: {result.get('id')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            raise
    
    # Stock Management
    
    async def get_stock_levels(
        self,
        product_code: Optional[str] = None,
        warehouse_code: Optional[str] = None,
        include_zero_stock: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get stock levels from Unleashed.
        
        Args:
            product_code: Optional product code to filter
            warehouse_code: Optional warehouse code to filter
            include_zero_stock: Whether to include zero stock items
            
        Returns:
            List of standardized stock level data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw stock levels
            raw_stock_levels = await self.data_extractor.extract_stock_on_hand(
                product_code=product_code,
                warehouse_code=warehouse_code,
                include_zero_stock=include_zero_stock
            )
            
            # Transform to standard format
            stock_levels = self.stock_transformer.transform_stock_levels(raw_stock_levels)
            
            logger.info(f"Retrieved {len(stock_levels)} stock levels from Unleashed")
            return stock_levels
            
        except Exception as e:
            logger.error(f"Failed to get stock levels: {e}")
            raise
    
    async def get_stock_movements(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        product_code: Optional[str] = None,
        warehouse_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get stock movements from Unleashed.
        
        Args:
            date_from: Start date for movements
            date_to: End date for movements
            product_code: Optional product code to filter
            warehouse_code: Optional warehouse code to filter
            
        Returns:
            List of standardized stock movement data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw stock movements
            raw_movements = await self.data_extractor.extract_stock_movements(
                date_from=date_from,
                date_to=date_to,
                product_code=product_code,
                warehouse_code=warehouse_code
            )
            
            # Transform to standard format
            movements = self.stock_transformer.transform_stock_movements(raw_movements)
            
            logger.info(f"Retrieved {len(movements)} stock movements from Unleashed")
            return movements
            
        except Exception as e:
            logger.error(f"Failed to get stock movements: {e}")
            raise
    
    async def create_stock_adjustment(self, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a stock adjustment in Unleashed.
        
        Args:
            adjustment_data: Stock adjustment data
            
        Returns:
            Created adjustment data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Convert standard format to Unleashed format
            unleashed_adjustment = self._convert_to_unleashed_adjustment(adjustment_data)
            
            # Create adjustment via API
            async with self.rest_client as client:
                created_adjustment = await client.create_stock_adjustment(unleashed_adjustment)
            
            logger.info(f"Created stock adjustment in Unleashed")
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
        Get purchase orders from Unleashed.
        
        Args:
            status_filter: Optional status filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of standardized purchase order data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
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
            
            logger.info(f"Retrieved {len(orders)} purchase orders from Unleashed")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get purchase orders: {e}")
            raise
    
    async def get_purchase_order(self, order_guid: str) -> Dict[str, Any]:
        """
        Get a specific purchase order from Unleashed.
        
        Args:
            order_guid: Purchase order GUID
            
        Returns:
            Standardized purchase order data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw purchase order
            raw_order = await self.data_extractor.extract_purchase_order(order_guid)
            
            # Transform to standard format
            order = self.stock_transformer.transform_purchase_order(raw_order)
            
            logger.debug(f"Retrieved purchase order {order_guid} from Unleashed")
            return order
            
        except Exception as e:
            logger.error(f"Failed to get purchase order {order_guid}: {e}")
            raise
    
    async def get_sales_orders(
        self,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sales orders from Unleashed.
        
        Args:
            status_filter: Optional status filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of standardized sales order data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw sales orders
            raw_orders = await self.data_extractor.extract_sales_orders(
                status_filter=status_filter,
                date_from=date_from,
                date_to=date_to
            )
            
            # Transform to standard format
            orders = [
                self.stock_transformer.transform_sales_order(order)
                for order in raw_orders
            ]
            
            logger.info(f"Retrieved {len(orders)} sales orders from Unleashed")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get sales orders: {e}")
            raise
    
    # Supplier Management
    
    async def get_suppliers(
        self,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get suppliers from Unleashed.
        
        Args:
            active_only: Only include active suppliers
            limit: Maximum number of suppliers to return
            
        Returns:
            List of standardized supplier data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw suppliers
            raw_suppliers = await self.data_extractor.extract_suppliers(
                active_only=active_only,
                limit=limit
            )
            
            # Transform to standard format
            suppliers = [
                self.stock_transformer.transform_supplier(supplier)
                for supplier in raw_suppliers
            ]
            
            logger.info(f"Retrieved {len(suppliers)} suppliers from Unleashed")
            return suppliers
            
        except Exception as e:
            logger.error(f"Failed to get suppliers: {e}")
            raise
    
    # Warehouse Management
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """
        Get all warehouses from Unleashed.
        
        Returns:
            List of standardized location data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw warehouses
            raw_warehouses = await self.data_extractor.extract_warehouses()
            
            # Transform to standard format
            locations = [
                self.stock_transformer.transform_warehouse(warehouse)
                for warehouse in raw_warehouses
            ]
            
            logger.info(f"Retrieved {len(locations)} locations from Unleashed")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to get locations: {e}")
            raise
    
    async def get_location(self, warehouse_code: str) -> Dict[str, Any]:
        """
        Get a specific warehouse from Unleashed.
        
        Args:
            warehouse_code: Warehouse code
            
        Returns:
            Standardized location data
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            # Extract raw warehouse
            raw_warehouse = await self.data_extractor.extract_warehouse(warehouse_code)
            
            # Transform to standard format
            location = self.stock_transformer.transform_warehouse(raw_warehouse)
            
            logger.debug(f"Retrieved location {warehouse_code} from Unleashed")
            return location
            
        except Exception as e:
            logger.error(f"Failed to get location {warehouse_code}: {e}")
            raise
    
    # Synchronization
    
    async def sync_all_data(self) -> Dict[str, Any]:
        """
        Sync all data from Unleashed.
        
        Returns:
            Synchronization results
        """
        if not self.is_connected():
            raise UnleashedConnectionError("Not connected to Unleashed")
        
        try:
            logger.info("Starting full data sync from Unleashed")
            
            sync_results = {
                "started_at": datetime.utcnow().isoformat(),
                "products": 0,
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
            
            logger.info(f"Completed data sync from Unleashed: {sync_results}")
            return sync_results
            
        except Exception as e:
            logger.error(f"Failed to sync data from Unleashed: {e}")
            raise
    
    # Helper Methods
    
    def _convert_to_unleashed_product(self, standard_product: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard product format to Unleashed format."""
        return {
            "ProductCode": standard_product.get("sku", ""),
            "ProductDescription": standard_product.get("name", ""),
            "DefaultSellPrice": standard_product.get("pricing", {}).get("selling_price", 0),
            "DefaultPurchasePrice": standard_product.get("pricing", {}).get("cost_price", 0),
            "UnitOfMeasure": standard_product.get("inventory_tracking", {}).get("unit_of_measure", "Each"),
            "IsSellable": standard_product.get("inventory_tracking", {}).get("is_sellable", True),
            "IsPurchasable": standard_product.get("inventory_tracking", {}).get("is_purchasable", True)
        }
    
    def _convert_to_unleashed_adjustment(self, standard_adjustment: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard adjustment format to Unleashed format."""
        return {
            "ProductCode": standard_adjustment.get("product_id"),
            "WarehouseCode": standard_adjustment.get("location_id"),
            "Quantity": standard_adjustment.get("quantity", 0),
            "UnitCost": standard_adjustment.get("unit_cost", 0),
            "Notes": standard_adjustment.get("notes", "")
        }
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the Unleashed platform.
        
        Returns:
            Platform information
        """
        return {
            "platform": self.platform_name,
            "display_name": self.display_name,
            "currency": self.currency_code,
            "is_connected": self.is_connected(),
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "capabilities": [
                "product_management",
                "stock_tracking",
                "multi_warehouse",
                "purchase_orders",
                "sales_orders",
                "supplier_management",
                "customer_management",
                "stock_adjustments",
                "stock_movements",
                "reporting",
                "real_time_sync",
                "assembly_management"
            ]
        }