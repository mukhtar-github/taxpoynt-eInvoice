"""
Fishbowl Data Extractor
Extracts and processes data from Fishbowl inventory management system.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio

from .rest_client import FishbowlXMLClient
from .exceptions import (
    FishbowlDataError,
    FishbowlProductNotFoundError,
    FishbowlWarehouseNotFoundError,
    FishbowlValidationError
)


logger = logging.getLogger(__name__)


class FishbowlDataExtractor:
    """
    Extracts and processes data from Fishbowl inventory system.
    
    Handles data retrieval, validation, and preprocessing for various
    Fishbowl entities including parts, inventory, orders, and vendors.
    """
    
    def __init__(self, xml_client: FishbowlXMLClient):
        """
        Initialize Fishbowl data extractor.
        
        Args:
            xml_client: Fishbowl XML API client
        """
        self.xml_client = xml_client
    
    # Part Data Extraction
    
    async def extract_parts(
        self,
        part_type: str = "All",
        location_group: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract all parts (products) from Fishbowl.
        
        Args:
            part_type: Type of parts to extract (All, Inventory, Service, etc.)
            location_group: Location group to filter by
            include_inactive: Whether to include inactive parts
            
        Returns:
            List of part data
        """
        logger.info(f"Extracting parts from Fishbowl (type: {part_type})")
        
        try:
            # Get parts from Fishbowl
            response = await self.xml_client.get_parts(
                part_type=part_type,
                location_group=location_group
            )
            
            parts = response.get("parts", [])
            
            # Filter inactive parts if needed
            if not include_inactive:
                parts = [part for part in parts if part.get("IsActive", True)]
            
            logger.info(f"Extracted {len(parts)} parts from Fishbowl")
            return parts
            
        except Exception as e:
            logger.error(f"Failed to extract parts: {e}")
            raise FishbowlDataError(f"Part extraction failed: {str(e)}")
    
    async def extract_part(self, part_number: str) -> Dict[str, Any]:
        """
        Extract a specific part from Fishbowl.
        
        Args:
            part_number: Fishbowl part number
            
        Returns:
            Part data
        """
        try:
            part = await self.xml_client.get_part(part_number)
            
            if not part:
                raise FishbowlProductNotFoundError(f"Part {part_number} not found")
            
            logger.debug(f"Extracted part {part_number}")
            return part
            
        except Exception as e:
            logger.error(f"Failed to extract part {part_number}: {e}")
            raise
    
    # Inventory Data Extraction
    
    async def extract_inventory_quantities(
        self,
        part_number: Optional[str] = None,
        location_group: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract inventory quantities from Fishbowl.
        
        Args:
            part_number: Optional part number to filter
            location_group: Optional location group to filter
            
        Returns:
            List of inventory quantity data
        """
        logger.info("Extracting inventory quantities from Fishbowl")
        
        try:
            # Get inventory quantities from Fishbowl
            response = await self.xml_client.get_inventory_quantity(
                part_number=part_number,
                location_group=location_group
            )
            
            inventory = response.get("inventory", [])
            
            logger.info(f"Extracted {len(inventory)} inventory records from Fishbowl")
            return inventory
            
        except Exception as e:
            logger.error(f"Failed to extract inventory quantities: {e}")
            raise FishbowlDataError(f"Inventory quantity extraction failed: {str(e)}")
    
    # Purchase Order Data Extraction
    
    async def extract_purchase_orders(
        self,
        status: Optional[str] = None,
        location_group: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract purchase orders from Fishbowl.
        
        Args:
            status: Optional status filter
            location_group: Optional location group filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of purchase order data
        """
        logger.info("Extracting purchase orders from Fishbowl")
        
        try:
            # Get purchase orders from Fishbowl
            response = await self.xml_client.get_purchase_orders(
                status=status,
                location_group=location_group
            )
            
            orders = response.get("purchase_orders", [])
            
            # Apply date filtering if specified
            if date_from or date_to:
                filtered_orders = []
                for order in orders:
                    order_date = self._parse_date(order.get("OrderDate"))
                    if order_date:
                        if date_from and order_date < date_from:
                            continue
                        if date_to and order_date > date_to:
                            continue
                    filtered_orders.append(order)
                orders = filtered_orders
            
            logger.info(f"Extracted {len(orders)} purchase orders from Fishbowl")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to extract purchase orders: {e}")
            raise FishbowlDataError(f"Purchase order extraction failed: {str(e)}")
    
    async def extract_purchase_order(self, po_number: str) -> Dict[str, Any]:
        """
        Extract a specific purchase order from Fishbowl.
        
        Args:
            po_number: Purchase order number
            
        Returns:
            Purchase order data
        """
        try:
            order = await self.xml_client.get_purchase_order(po_number)
            
            if not order:
                raise FishbowlPurchaseOrderNotFoundError(f"Purchase order {po_number} not found")
            
            logger.debug(f"Extracted purchase order {po_number}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to extract purchase order {po_number}: {e}")
            raise
    
    # Sales Order Data Extraction
    
    async def extract_sales_orders(
        self,
        status: Optional[str] = None,
        location_group: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract sales orders from Fishbowl.
        
        Args:
            status: Optional status filter
            location_group: Optional location group filter
            date_from: Start date for orders
            date_to: End date for orders
            
        Returns:
            List of sales order data
        """
        logger.info("Extracting sales orders from Fishbowl")
        
        try:
            # Get sales orders from Fishbowl
            response = await self.xml_client.get_sales_orders(
                status=status,
                location_group=location_group
            )
            
            orders = response.get("sales_orders", [])
            
            # Apply date filtering if specified
            if date_from or date_to:
                filtered_orders = []
                for order in orders:
                    order_date = self._parse_date(order.get("OrderDate"))
                    if order_date:
                        if date_from and order_date < date_from:
                            continue
                        if date_to and order_date > date_to:
                            continue
                    filtered_orders.append(order)
                orders = filtered_orders
            
            logger.info(f"Extracted {len(orders)} sales orders from Fishbowl")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to extract sales orders: {e}")
            raise FishbowlDataError(f"Sales order extraction failed: {str(e)}")
    
    async def extract_sales_order(self, so_number: str) -> Dict[str, Any]:
        """
        Extract a specific sales order from Fishbowl.
        
        Args:
            so_number: Sales order number
            
        Returns:
            Sales order data
        """
        try:
            order = await self.xml_client.get_sales_order(so_number)
            
            if not order:
                raise FishbowlSalesOrderNotFoundError(f"Sales order {so_number} not found")
            
            logger.debug(f"Extracted sales order {so_number}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to extract sales order {so_number}: {e}")
            raise
    
    # Vendor Data Extraction
    
    async def extract_vendors(self) -> List[Dict[str, Any]]:
        """
        Extract all vendors from Fishbowl.
        
        Returns:
            List of vendor data
        """
        logger.info("Extracting vendors from Fishbowl")
        
        try:
            # Get vendors from Fishbowl
            response = await self.xml_client.get_vendors()
            
            vendors = response.get("vendors", [])
            
            logger.info(f"Extracted {len(vendors)} vendors from Fishbowl")
            return vendors
            
        except Exception as e:
            logger.error(f"Failed to extract vendors: {e}")
            raise FishbowlDataError(f"Vendor extraction failed: {str(e)}")
    
    # Location Data Extraction
    
    async def extract_locations(self) -> List[Dict[str, Any]]:
        """
        Extract all locations from Fishbowl.
        
        Returns:
            List of location data
        """
        logger.info("Extracting locations from Fishbowl")
        
        try:
            # Get locations from Fishbowl
            response = await self.xml_client.get_locations()
            
            locations = response.get("locations", [])
            
            logger.info(f"Extracted {len(locations)} locations from Fishbowl")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to extract locations: {e}")
            raise FishbowlDataError(f"Location extraction failed: {str(e)}")
    
    async def extract_location(self, location_name: str) -> Dict[str, Any]:
        """
        Extract a specific location from Fishbowl.
        
        Args:
            location_name: Location name
            
        Returns:
            Location data
        """
        try:
            location = await self.xml_client.get_location(location_name)
            
            if not location:
                raise FishbowlWarehouseNotFoundError(f"Location {location_name} not found")
            
            logger.debug(f"Extracted location {location_name}")
            return location
            
        except Exception as e:
            logger.error(f"Failed to extract location {location_name}: {e}")
            raise
    
    # Validation Methods
    
    def validate_part_data(self, part: Dict[str, Any]) -> bool:
        """
        Validate part data structure.
        
        Args:
            part: Part data to validate
            
        Returns:
            True if valid
            
        Raises:
            FishbowlValidationError: If data is invalid
        """
        required_fields = ["Number", "Description", "Type"]
        
        for field in required_fields:
            if field not in part:
                raise FishbowlValidationError(f"Missing required field: {field}")
        
        return True
    
    def validate_inventory_data(self, inventory: Dict[str, Any]) -> bool:
        """
        Validate inventory data structure.
        
        Args:
            inventory: Inventory data to validate
            
        Returns:
            True if valid
            
        Raises:
            FishbowlValidationError: If data is invalid
        """
        required_fields = ["PartNumber", "LocationName", "Qty"]
        
        for field in required_fields:
            if field not in inventory:
                raise FishbowlValidationError(f"Missing required field: {field}")
        
        return True
    
    # Helper Methods
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Try to parse various date formats
            if 'T' in date_str:
                # ISO format
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Try basic date format
                return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            logger.warning(f"Failed to parse date: {date_str}")
            return None
    
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