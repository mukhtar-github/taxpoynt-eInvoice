"""
Cin7 Inventory Connector
Main connector class for Cin7 inventory management integration.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from ....connector_framework.inventory.base_inventory_connector import BaseInventoryConnector
from .auth import Cin7AuthManager
from .rest_client import Cin7RestClient
from .data_extractor import Cin7DataExtractor
from .stock_transformer import Cin7StockTransformer
from .exceptions import (
    Cin7Exception,
    Cin7ConfigurationError,
    Cin7ConnectionError,
    Cin7AuthenticationError
)


logger = logging.getLogger(__name__)


class Cin7InventoryConnector(BaseInventoryConnector):
    """
    Cin7 inventory management connector.
    
    Provides comprehensive integration with Cin7 inventory system including
    product management, stock tracking, order processing, and reporting.
    """
    
    platform_name = "cin7"
    display_name = "Cin7 Inventory Management"
    
    def __init__(
        self,
        api_username: str,
        api_token: str,
        api_password: str,
        sandbox: bool = True,
        currency_code: str = "NGN",
        **kwargs
    ):
        """
        Initialize Cin7 inventory connector.
        
        Args:
            api_username: Cin7 API username
            api_token: Cin7 API token
            api_password: Cin7 API password
            sandbox: Whether to use sandbox environment
            currency_code: Default currency code
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        
        # Validate required configuration
        if not all([api_username, api_token, api_password]):
            raise Cin7ConfigurationError(
                "api_username, api_token, and api_password are required"
            )
        
        self.api_username = api_username
        self.api_token = api_token
        self.api_password = api_password
        self.sandbox = sandbox
        self.currency_code = currency_code
        
        # Initialize components
        self.auth_manager: Optional[Cin7AuthManager] = None
        self.rest_client: Optional[Cin7RestClient] = None
        self.data_extractor: Optional[Cin7DataExtractor] = None
        self.stock_transformer: Optional[Cin7StockTransformer] = None
        
        # Connection state
        self._is_connected = False
        self._last_sync: Optional[datetime] = None
    
    async def connect(self) -> Dict[str, Any]:
        """
        Connect to Cin7 inventory system.
        
        Returns:
            Connection result with account information
        """
        try:
            logger.info(f"Connecting to Cin7 ({'sandbox' if self.sandbox else 'production'})")
            
            # Initialize auth manager
            self.auth_manager = Cin7AuthManager(
                api_username=self.api_username,
                api_token=self.api_token,
                api_password=self.api_password,
                sandbox=self.sandbox
            )
            
            # Initialize and test connection
            async with self.auth_manager as auth:
                auth_result = await auth.authenticate()
                
                # Initialize other components
                self.rest_client = Cin7RestClient(auth)
                self.data_extractor = Cin7DataExtractor(self.rest_client)
                self.stock_transformer = Cin7StockTransformer(self.currency_code)
                
                self._is_connected = True
                
                logger.info("Successfully connected to Cin7")
                
                return {
                    "success": True,
                    "platform": self.platform_name,
                    "environment": "sandbox" if self.sandbox else "production",
                    "account_info": auth_result.get("account_info", {}),
                    "connected_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to connect to Cin7: {e}")
            self._is_connected = False
            raise Cin7ConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Cin7 inventory system.
        
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
            
            logger.info("Disconnected from Cin7")
            return True
            
        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Cin7 inventory system.
        
        Returns:
            Connection test results
        """
        if not self.auth_manager:
            return {
                "success": False,
                "status": "not_connected",
                "error": "Not connected to Cin7"
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
        Check if connected to Cin7.
        
        Returns:
            True if connected, False otherwise
        """
        return self._is_connected and self.auth_manager is not None
    
    # Product Management
    
    async def get_products(
        self,
        filters: Optional[Dict[str, Any]] = None,
        include_inactive: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from Cin7 inventory.
        
        Args:
            filters: Optional filters to apply
            include_inactive: Whether to include inactive products
            limit: Maximum number of products to return
            
        Returns:
            List of standardized product data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Extract raw products
            raw_products = await self.data_extractor.extract_products(
                filters=filters,
                include_inactive=include_inactive,
                limit=limit
            )
            
            # Transform to standard format
            products = self.stock_transformer.transform_products(raw_products)
            
            logger.info(f"Retrieved {len(products)} products from Cin7")
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            raise
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Get a specific product from Cin7.
        
        Args:
            product_id: Cin7 product ID
            
        Returns:
            Standardized product data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Extract raw product
            raw_product = await self.data_extractor.extract_product(product_id)
            
            # Transform to standard format
            product = self.stock_transformer.transform_product(raw_product)
            
            logger.debug(f"Retrieved product {product_id} from Cin7")
            return product
            
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            raise
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product in Cin7.
        
        Args:
            product_data: Standardized product data
            
        Returns:
            Created product data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Convert standard format to Cin7 format
            cin7_product_data = self._convert_to_cin7_product(product_data)
            
            # Create product via API
            async with self.rest_client as client:
                created_product = await client.create_product(cin7_product_data)
            
            # Transform back to standard format
            result = self.stock_transformer.transform_product(created_product)
            
            logger.info(f"Created product in Cin7: {result.get('id')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            raise
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing product in Cin7.
        
        Args:
            product_id: Cin7 product ID
            product_data: Updated product data
            
        Returns:
            Updated product data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Convert standard format to Cin7 format
            cin7_product_data = self._convert_to_cin7_product(product_data)
            
            # Update product via API
            async with self.rest_client as client:
                updated_product = await client.update_product(product_id, cin7_product_data)
            
            # Transform back to standard format
            result = self.stock_transformer.transform_product(updated_product)
            
            logger.info(f"Updated product in Cin7: {product_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update product {product_id}: {e}")
            raise
    
    # Stock Management
    
    async def get_stock_levels(
        self,
        location_ids: Optional[List[str]] = None,
        product_ids: Optional[List[str]] = None,
        low_stock_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get stock levels from Cin7.
        
        Args:
            location_ids: Optional list of location IDs to filter
            product_ids: Optional list of product IDs to filter
            low_stock_only: Only include low stock items
            
        Returns:
            List of standardized stock level data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Extract raw stock levels
            raw_stock_levels = await self.data_extractor.extract_stock_levels(
                location_ids=location_ids,
                product_ids=product_ids,
                low_stock_only=low_stock_only
            )
            
            # Transform to standard format
            stock_levels = self.stock_transformer.transform_stock_levels(raw_stock_levels)
            
            logger.info(f"Retrieved {len(stock_levels)} stock levels from Cin7")
            return stock_levels
            
        except Exception as e:
            logger.error(f"Failed to get stock levels: {e}")
            raise
    
    async def get_stock_movements(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        product_ids: Optional[List[str]] = None,
        movement_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get stock movements from Cin7.
        
        Args:
            date_from: Start date for movements
            date_to: End date for movements
            product_ids: Optional list of product IDs to filter
            movement_types: Optional list of movement types to filter
            
        Returns:
            List of standardized stock movement data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Extract raw stock movements
            raw_movements = await self.data_extractor.extract_stock_movements(
                date_from=date_from,
                date_to=date_to,
                product_ids=product_ids,
                movement_types=movement_types
            )
            
            # Transform to standard format
            movements = self.stock_transformer.transform_stock_movements(raw_movements)
            
            logger.info(f"Retrieved {len(movements)} stock movements from Cin7")
            return movements
            
        except Exception as e:
            logger.error(f"Failed to get stock movements: {e}")
            raise
    
    async def create_stock_adjustment(self, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a stock adjustment in Cin7.
        
        Args:
            adjustment_data: Stock adjustment data
            
        Returns:
            Created adjustment data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Convert standard format to Cin7 format
            cin7_adjustment = self._convert_to_cin7_adjustment(adjustment_data)
            
            # Create adjustment via API
            async with self.rest_client as client:
                created_adjustment = await client.create_stock_adjustment(cin7_adjustment)
            
            logger.info(f"Created stock adjustment in Cin7")
            return created_adjustment
            
        except Exception as e:
            logger.error(f"Failed to create stock adjustment: {e}")
            raise
    
    # Order Management
    
    async def get_purchase_orders(
        self,
        status_filter: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        supplier_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get purchase orders from Cin7.
        
        Args:
            status_filter: Optional list of statuses to filter
            date_from: Start date for orders
            date_to: End date for orders
            supplier_ids: Optional list of supplier IDs to filter
            
        Returns:
            List of standardized purchase order data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Extract raw purchase orders
            raw_orders = await self.data_extractor.extract_purchase_orders(
                status_filter=status_filter,
                date_from=date_from,
                date_to=date_to,
                supplier_ids=supplier_ids
            )
            
            # Transform to standard format
            orders = [
                self.stock_transformer.transform_purchase_order(order)
                for order in raw_orders
            ]
            
            logger.info(f"Retrieved {len(orders)} purchase orders from Cin7")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get purchase orders: {e}")
            raise
    
    # Location Management
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """
        Get all locations from Cin7.
        
        Returns:
            List of standardized location data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            # Extract raw locations
            raw_locations = await self.data_extractor.extract_locations()
            
            # Transform to standard format
            locations = [
                self.stock_transformer.transform_location(location)
                for location in raw_locations
            ]
            
            logger.info(f"Retrieved {len(locations)} locations from Cin7")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to get locations: {e}")
            raise
    
    # Supplier Management
    
    async def get_suppliers(
        self,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get suppliers from Cin7.
        
        Args:
            active_only: Only include active suppliers
            limit: Maximum number of suppliers to return
            
        Returns:
            List of standardized supplier data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
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
            
            logger.info(f"Retrieved {len(suppliers)} suppliers from Cin7")
            return suppliers
            
        except Exception as e:
            logger.error(f"Failed to get suppliers: {e}")
            raise
    
    # Reporting
    
    async def get_stock_valuation_report(
        self,
        location_id: Optional[str] = None,
        as_at_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get stock valuation report from Cin7.
        
        Args:
            location_id: Optional location to filter
            as_at_date: Optional date for valuation
            
        Returns:
            Stock valuation report data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            report = await self.data_extractor.extract_stock_valuation(
                location_id=location_id,
                as_at_date=as_at_date
            )
            
            logger.info("Retrieved stock valuation report from Cin7")
            return report
            
        except Exception as e:
            logger.error(f"Failed to get stock valuation report: {e}")
            raise
    
    async def get_low_stock_report(
        self,
        location_id: Optional[str] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get low stock report from Cin7.
        
        Args:
            location_id: Optional location to filter
            threshold: Optional threshold for low stock
            
        Returns:
            Low stock report data
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            report = await self.data_extractor.extract_low_stock_report(
                location_id=location_id,
                threshold=threshold
            )
            
            logger.info("Retrieved low stock report from Cin7")
            return report
            
        except Exception as e:
            logger.error(f"Failed to get low stock report: {e}")
            raise
    
    # Synchronization
    
    async def sync_all_data(self) -> Dict[str, Any]:
        """
        Sync all data from Cin7.
        
        Returns:
            Synchronization results
        """
        if not self.is_connected():
            raise Cin7ConnectionError("Not connected to Cin7")
        
        try:
            logger.info("Starting full data sync from Cin7")
            
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
            
            logger.info(f"Completed data sync from Cin7: {sync_results}")
            return sync_results
            
        except Exception as e:
            logger.error(f"Failed to sync data from Cin7: {e}")
            raise
    
    # Helper Methods
    
    def _convert_to_cin7_product(self, standard_product: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard product format to Cin7 format."""
        return {
            "Name": standard_product.get("name", ""),
            "Description": standard_product.get("description", ""),
            "SKU": standard_product.get("sku", ""),
            "Type": "Inventory",  # Default to inventory type
            "SellingPrice": standard_product.get("pricing", {}).get("selling_price", 0),
            "CostPrice": standard_product.get("pricing", {}).get("cost_price", 0),
            "IsActive": standard_product.get("status") == "active",
            "IsTracked": standard_product.get("is_tracked", True)
        }
    
    def _convert_to_cin7_adjustment(self, standard_adjustment: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard adjustment format to Cin7 format."""
        return {
            "ProductId": standard_adjustment.get("product_id"),
            "LocationId": standard_adjustment.get("location_id"),
            "Quantity": standard_adjustment.get("quantity", 0),
            "UnitCost": standard_adjustment.get("unit_cost", 0),
            "Notes": standard_adjustment.get("notes", "")
        }
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the Cin7 platform.
        
        Returns:
            Platform information
        """
        return {
            "platform": self.platform_name,
            "display_name": self.display_name,
            "version": "1.3",
            "environment": "sandbox" if self.sandbox else "production",
            "currency": self.currency_code,
            "is_connected": self.is_connected(),
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "capabilities": [
                "product_management",
                "stock_tracking",
                "order_management",
                "supplier_management",
                "location_management",
                "stock_adjustments",
                "reporting",
                "real_time_sync"
            ]
        }