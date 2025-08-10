"""
Fishbowl Inventory Connector
Main connector class for Fishbowl inventory management integration.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from ....connector_framework.inventory.base_inventory_connector import BaseInventoryConnector
from .auth import FishbowlAuthManager
from .rest_client import FishbowlXMLClient
from .data_extractor import FishbowlDataExtractor
from .stock_transformer import FishbowlStockTransformer
from .exceptions import (
    FishbowlException,
    FishbowlConfigurationError,
    FishbowlConnectionError,
    FishbowlAuthenticationError
)


logger = logging.getLogger(__name__)


class FishbowlInventoryConnector(BaseInventoryConnector):
    """
    Fishbowl inventory management connector.
    
    Provides comprehensive integration with Fishbowl inventory system including
    part management, inventory tracking, order processing, and manufacturing.
    """
    
    platform_name = "fishbowl"
    display_name = "Fishbowl Inventory Management"
    
    def __init__(
        self,
        server_host: str,
        server_port: int,
        username: str,
        password: str,
        app_name: str = "TaxPoynt",
        app_description: str = "TaxPoynt E-Invoice Integration",
        currency_code: str = "NGN",
        **kwargs
    ):
        """
        Initialize Fishbowl inventory connector.
        
        Args:
            server_host: Fishbowl server hostname/IP
            server_port: Fishbowl server port (usually 28192)
            username: Fishbowl username
            password: Fishbowl password
            app_name: Application name for identification
            app_description: Application description
            currency_code: Default currency code
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        
        # Validate required configuration
        if not all([server_host, server_port, username, password]):
            raise FishbowlConfigurationError(
                "server_host, server_port, username, and password are required"
            )
        
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.password = password
        self.app_name = app_name
        self.app_description = app_description
        self.currency_code = currency_code
        
        # Initialize components
        self.auth_manager: Optional[FishbowlAuthManager] = None
        self.xml_client: Optional[FishbowlXMLClient] = None
        self.data_extractor: Optional[FishbowlDataExtractor] = None
        self.stock_transformer: Optional[FishbowlStockTransformer] = None
        
        # Connection state
        self._is_connected = False
        self._last_sync: Optional[datetime] = None
    
    async def connect(self) -> Dict[str, Any]:
        """
        Connect to Fishbowl inventory system.
        
        Returns:
            Connection result with session information
        """
        try:
            logger.info(f"Connecting to Fishbowl server at {self.server_host}:{self.server_port}")
            
            # Initialize auth manager
            self.auth_manager = FishbowlAuthManager(
                server_host=self.server_host,
                server_port=self.server_port,
                username=self.username,
                password=self.password,
                app_name=self.app_name,
                app_description=self.app_description
            )
            
            # Initialize and test connection
            async with self.auth_manager as auth:
                auth_result = await auth.authenticate()
                
                # Initialize other components
                self.xml_client = FishbowlXMLClient(auth)
                self.data_extractor = FishbowlDataExtractor(self.xml_client)
                self.stock_transformer = FishbowlStockTransformer(self.currency_code)
                
                self._is_connected = True
                
                logger.info("Successfully connected to Fishbowl")
                
                return {
                    "success": True,
                    "platform": self.platform_name,
                    "server_host": self.server_host,
                    "server_port": self.server_port,
                    "session_info": auth_result.get("user_info", {}),
                    "connected_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to connect to Fishbowl: {e}")
            self._is_connected = False
            raise FishbowlConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Fishbowl inventory system.
        
        Returns:
            True if disconnection successful
        """
        try:
            if self.auth_manager:
                self.auth_manager.disconnect()
            
            self.auth_manager = None
            self.xml_client = None
            self.data_extractor = None
            self.stock_transformer = None
            self._is_connected = False
            
            logger.info("Disconnected from Fishbowl")
            return True
            
        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Fishbowl inventory system.
        
        Returns:
            Connection test results
        """
        if not self.auth_manager:
            return {
                "success": False,
                "status": "not_connected",
                "error": "Not connected to Fishbowl"
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
        Check if connected to Fishbowl.
        
        Returns:
            True if connected, False otherwise
        """
        return self._is_connected and self.auth_manager is not None
    
    # Part Management
    
    async def get_products(
        self,
        part_type: str = "All",
        location_group: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get parts (products) from Fishbowl inventory.
        
        Args:
            part_type: Type of parts to retrieve
            location_group: Optional location group filter
            include_inactive: Whether to include inactive parts
            
        Returns:
            List of standardized product data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw parts
            raw_parts = await self.data_extractor.extract_parts(
                part_type=part_type,
                location_group=location_group,
                include_inactive=include_inactive
            )
            
            # Transform to standard format
            products = self.stock_transformer.transform_parts(raw_parts)
            
            logger.info(f"Retrieved {len(products)} products from Fishbowl")
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            raise
    
    async def get_product(self, part_number: str) -> Dict[str, Any]:
        """
        Get a specific part from Fishbowl.
        
        Args:
            part_number: Fishbowl part number
            
        Returns:
            Standardized product data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw part
            raw_part = await self.data_extractor.extract_part(part_number)
            
            # Transform to standard format
            product = self.stock_transformer.transform_part(raw_part)
            
            logger.debug(f"Retrieved product {part_number} from Fishbowl")
            return product
            
        except Exception as e:
            logger.error(f"Failed to get product {part_number}: {e}")
            raise
    
    # Inventory Management
    
    async def get_stock_levels(
        self,
        part_number: Optional[str] = None,
        location_group: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get inventory quantities from Fishbowl.
        
        Args:
            part_number: Optional part number filter
            location_group: Optional location group filter
            
        Returns:
            List of standardized stock level data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw inventory quantities
            raw_inventory = await self.data_extractor.extract_inventory_quantities(
                part_number=part_number,
                location_group=location_group
            )
            
            # Transform to standard format
            stock_levels = self.stock_transformer.transform_inventory_quantities(raw_inventory)
            
            logger.info(f"Retrieved {len(stock_levels)} stock levels from Fishbowl")
            return stock_levels
            
        except Exception as e:
            logger.error(f"Failed to get stock levels: {e}")
            raise
    
    async def set_inventory_quantity(
        self,
        part_number: str,
        location_name: str,
        quantity: float,
        unit_cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Set inventory quantity for a part in Fishbowl.
        
        Args:
            part_number: Part number
            location_name: Location name
            quantity: New quantity
            unit_cost: Optional unit cost
            
        Returns:
            Operation result
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Set inventory quantity via XML client
            async with self.xml_client as client:
                result = await client.set_inventory_quantity(
                    part_number=part_number,
                    location_name=location_name,
                    quantity=quantity,
                    unit_cost=unit_cost
                )
            
            logger.info(f"Set inventory quantity for {part_number} at {location_name}: {quantity}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to set inventory quantity: {e}")
            raise
    
    # Order Management
    
    async def get_purchase_orders(
        self,
        status: Optional[str] = None,
        location_group: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get purchase orders from Fishbowl.
        
        Args:
            status: Optional status filter
            location_group: Optional location group filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of standardized purchase order data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw purchase orders
            raw_orders = await self.data_extractor.extract_purchase_orders(
                status=status,
                location_group=location_group,
                date_from=date_from,
                date_to=date_to
            )
            
            # Transform to standard format
            orders = [
                self.stock_transformer.transform_purchase_order(order)
                for order in raw_orders
            ]
            
            logger.info(f"Retrieved {len(orders)} purchase orders from Fishbowl")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get purchase orders: {e}")
            raise
    
    async def get_purchase_order(self, po_number: str) -> Dict[str, Any]:
        """
        Get a specific purchase order from Fishbowl.
        
        Args:
            po_number: Purchase order number
            
        Returns:
            Standardized purchase order data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw purchase order
            raw_order = await self.data_extractor.extract_purchase_order(po_number)
            
            # Transform to standard format
            order = self.stock_transformer.transform_purchase_order(raw_order)
            
            logger.debug(f"Retrieved purchase order {po_number} from Fishbowl")
            return order
            
        except Exception as e:
            logger.error(f"Failed to get purchase order {po_number}: {e}")
            raise
    
    async def get_sales_orders(
        self,
        status: Optional[str] = None,
        location_group: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sales orders from Fishbowl.
        
        Args:
            status: Optional status filter
            location_group: Optional location group filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of standardized sales order data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw sales orders
            raw_orders = await self.data_extractor.extract_sales_orders(
                status=status,
                location_group=location_group,
                date_from=date_from,
                date_to=date_to
            )
            
            # Transform to standard format
            orders = [
                self.stock_transformer.transform_sales_order(order)
                for order in raw_orders
            ]
            
            logger.info(f"Retrieved {len(orders)} sales orders from Fishbowl")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get sales orders: {e}")
            raise
    
    # Vendor Management
    
    async def get_suppliers(self) -> List[Dict[str, Any]]:
        """
        Get vendors (suppliers) from Fishbowl.
        
        Returns:
            List of standardized supplier data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw vendors
            raw_vendors = await self.data_extractor.extract_vendors()
            
            # Transform to standard format
            suppliers = [
                self.stock_transformer.transform_vendor(vendor)
                for vendor in raw_vendors
            ]
            
            logger.info(f"Retrieved {len(suppliers)} suppliers from Fishbowl")
            return suppliers
            
        except Exception as e:
            logger.error(f"Failed to get suppliers: {e}")
            raise
    
    # Location Management
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """
        Get all locations from Fishbowl.
        
        Returns:
            List of standardized location data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw locations
            raw_locations = await self.data_extractor.extract_locations()
            
            # Transform to standard format
            locations = [
                self.stock_transformer.transform_location(location)
                for location in raw_locations
            ]
            
            logger.info(f"Retrieved {len(locations)} locations from Fishbowl")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to get locations: {e}")
            raise
    
    async def get_location(self, location_name: str) -> Dict[str, Any]:
        """
        Get a specific location from Fishbowl.
        
        Args:
            location_name: Location name
            
        Returns:
            Standardized location data
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            # Extract raw location
            raw_location = await self.data_extractor.extract_location(location_name)
            
            # Transform to standard format
            location = self.stock_transformer.transform_location(raw_location)
            
            logger.debug(f"Retrieved location {location_name} from Fishbowl")
            return location
            
        except Exception as e:
            logger.error(f"Failed to get location {location_name}: {e}")
            raise
    
    # Synchronization
    
    async def sync_all_data(self) -> Dict[str, Any]:
        """
        Sync all data from Fishbowl.
        
        Returns:
            Synchronization results
        """
        if not self.is_connected():
            raise FishbowlConnectionError("Not connected to Fishbowl")
        
        try:
            logger.info("Starting full data sync from Fishbowl")
            
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
            
            logger.info(f"Completed data sync from Fishbowl: {sync_results}")
            return sync_results
            
        except Exception as e:
            logger.error(f"Failed to sync data from Fishbowl: {e}")
            raise
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        Get information about the Fishbowl platform.
        
        Returns:
            Platform information
        """
        return {
            "platform": self.platform_name,
            "display_name": self.display_name,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "currency": self.currency_code,
            "is_connected": self.is_connected(),
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "capabilities": [
                "part_management",
                "inventory_tracking",
                "purchase_orders",
                "sales_orders",
                "vendor_management",
                "location_management",
                "manufacturing",
                "work_orders",
                "real_time_sync"
            ]
        }