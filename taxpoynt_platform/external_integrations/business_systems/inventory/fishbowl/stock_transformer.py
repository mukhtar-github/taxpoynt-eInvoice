"""
Fishbowl Stock Transformer
Transforms Fishbowl data to standardized inventory formats for TaxPoynt platform.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .exceptions import (
    FishbowlTransformationError,
    FishbowlValidationError,
    FishbowlDataError
)


logger = logging.getLogger(__name__)


class FishbowlStockTransformer:
    """
    Transforms Fishbowl inventory data to standardized formats.
    
    Handles transformation of parts, inventory quantities, orders,
    and other inventory-related data to TaxPoynt standard schema.
    """
    
    def __init__(self, currency_code: str = "NGN"):
        """
        Initialize Fishbowl stock transformer.
        
        Args:
            currency_code: Default currency code for transformations
        """
        self.currency_code = currency_code
    
    # Part Transformations
    
    def transform_part(self, fishbowl_part: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Fishbowl part to standard format.
        
        Args:
            fishbowl_part: Raw Fishbowl part data
            
        Returns:
            Standardized product data
        """
        try:
            # Extract basic part information
            part_number = fishbowl_part.get("Number", "")
            description = fishbowl_part.get("Description", "")
            part_type = fishbowl_part.get("Type", "")
            
            # Pricing information
            unit_cost = self._safe_decimal(fishbowl_part.get("UnitCost", 0))
            std_cost = self._safe_decimal(fishbowl_part.get("StdCost", 0))
            
            # Physical attributes
            weight = self._safe_decimal(fishbowl_part.get("Weight", 0))
            length = self._safe_decimal(fishbowl_part.get("Length", 0))
            width = self._safe_decimal(fishbowl_part.get("Width", 0))
            height = self._safe_decimal(fishbowl_part.get("Height", 0))
            
            # Status and tracking
            is_active = fishbowl_part.get("IsActive", True)
            is_tracked = fishbowl_part.get("IsTracked", True)
            
            # UOM (Unit of Measure)
            uom = fishbowl_part.get("UOM", {})
            unit_name = uom.get("Name", "Each") if isinstance(uom, dict) else str(uom)
            
            # Build standard product format
            standard_product = {
                "id": part_number,
                "external_id": part_number,
                "name": description or part_number,
                "description": description,
                "sku": part_number,
                "type": self._map_part_type(part_type),
                "category": fishbowl_part.get("Category", ""),
                "status": "active" if is_active else "inactive",
                "is_tracked": is_tracked,
                "pricing": {
                    "cost_price": float(unit_cost or std_cost),
                    "standard_cost": float(std_cost),
                    "currency": self.currency_code
                },
                "physical_attributes": {
                    "weight": float(weight),
                    "dimensions": {
                        "length": float(length),
                        "width": float(width),
                        "height": float(height)
                    },
                    "weight_unit": "lb",  # Fishbowl typically uses pounds
                    "dimension_unit": "in"  # Fishbowl typically uses inches
                },
                "inventory_tracking": {
                    "track_stock": is_tracked,
                    "unit_of_measure": unit_name
                },
                "fishbowl_data": {
                    "part_id": fishbowl_part.get("ID", ""),
                    "abc_code": fishbowl_part.get("ABCCode", ""),
                    "configurable": fishbowl_part.get("IsConfigurable", False),
                    "serialized": fishbowl_part.get("IsSerialized", False)
                },
                "source": "fishbowl",
                "raw_data": fishbowl_part
            }
            
            logger.debug(f"Transformed part {part_number}")
            return standard_product
            
        except Exception as e:
            logger.error(f"Failed to transform part: {e}")
            raise FishbowlTransformationError(f"Part transformation failed: {str(e)}")
    
    def transform_parts(self, fishbowl_parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple Fishbowl parts to standard format.
        
        Args:
            fishbowl_parts: List of raw Fishbowl part data
            
        Returns:
            List of standardized product data
        """
        transformed_parts = []
        
        for part in fishbowl_parts:
            try:
                transformed_part = self.transform_part(part)
                transformed_parts.append(transformed_part)
            except Exception as e:
                logger.warning(f"Skipping part transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_parts)} parts")
        return transformed_parts
    
    # Inventory Quantity Transformations
    
    def transform_inventory_quantity(self, fishbowl_inventory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Fishbowl inventory quantity to standard format.
        
        Args:
            fishbowl_inventory: Raw Fishbowl inventory data
            
        Returns:
            Standardized stock level data
        """
        try:
            # Extract inventory information
            part_number = fishbowl_inventory.get("PartNumber", "")
            location_name = fishbowl_inventory.get("LocationName", "")
            
            # Quantity information
            qty_on_hand = self._safe_decimal(fishbowl_inventory.get("Qty", 0))
            qty_allocated = self._safe_decimal(fishbowl_inventory.get("QtyAllocated", 0))
            qty_available = self._safe_decimal(fishbowl_inventory.get("QtyAvailable", 0))
            qty_on_order = self._safe_decimal(fishbowl_inventory.get("QtyOnOrder", 0))
            
            # Cost information
            unit_cost = self._safe_decimal(fishbowl_inventory.get("UnitCost", 0))
            total_value = qty_on_hand * unit_cost
            
            # Build standard stock level format
            standard_stock = {
                "product_id": part_number,
                "location_id": location_name,
                "quantities": {
                    "on_hand": float(qty_on_hand),
                    "allocated": float(qty_allocated),
                    "available": float(qty_available),
                    "on_order": float(qty_on_order),
                    "reserved": float(qty_allocated)
                },
                "valuation": {
                    "unit_cost": float(unit_cost),
                    "total_value": float(total_value),
                    "currency": self.currency_code
                },
                "timestamps": {
                    "last_updated": datetime.utcnow().isoformat()
                },
                "source": "fishbowl",
                "raw_data": fishbowl_inventory
            }
            
            logger.debug(f"Transformed inventory for part {part_number}")
            return standard_stock
            
        except Exception as e:
            logger.error(f"Failed to transform inventory quantity: {e}")
            raise FishbowlTransformationError(f"Inventory quantity transformation failed: {str(e)}")
    
    def transform_inventory_quantities(self, fishbowl_inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple Fishbowl inventory quantities to standard format.
        
        Args:
            fishbowl_inventory: List of raw Fishbowl inventory data
            
        Returns:
            List of standardized stock level data
        """
        transformed_inventory = []
        
        for inventory in fishbowl_inventory:
            try:
                transformed_stock = self.transform_inventory_quantity(inventory)
                transformed_inventory.append(transformed_stock)
            except Exception as e:
                logger.warning(f"Skipping inventory transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_inventory)} inventory records")
        return transformed_inventory
    
    # Purchase Order Transformations
    
    def transform_purchase_order(self, fishbowl_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Fishbowl purchase order to standard format.
        
        Args:
            fishbowl_order: Raw Fishbowl purchase order data
            
        Returns:
            Standardized purchase order data
        """
        try:
            # Extract order information
            po_number = fishbowl_order.get("Number", "")
            vendor_name = fishbowl_order.get("VendorName", "")
            status = fishbowl_order.get("Status", "")
            
            # Order details
            total_cost = self._safe_decimal(fishbowl_order.get("TotalCost", 0))
            
            # Dates
            order_date = self._parse_datetime(fishbowl_order.get("OrderDate"))
            date_issued = self._parse_datetime(fishbowl_order.get("DateIssued"))
            date_expected = self._parse_datetime(fishbowl_order.get("DateExpected"))
            
            # Line items
            line_items = []
            items = fishbowl_order.get("Items", [])
            if isinstance(items, dict):
                items = [items]
            
            for item in items:
                line_item = {
                    "product_id": item.get("PartNumber", ""),
                    "description": item.get("Description", ""),
                    "quantity": float(self._safe_decimal(item.get("Quantity", 0))),
                    "unit_cost": float(self._safe_decimal(item.get("UnitCost", 0))),
                    "total_cost": float(self._safe_decimal(item.get("TotalCost", 0)))
                }
                line_items.append(line_item)
            
            # Build standard order format
            standard_order = {
                "id": po_number,
                "external_id": po_number,
                "order_number": po_number,
                "supplier_id": vendor_name,
                "supplier_name": vendor_name,
                "status": self._map_order_status(status),
                "order_date": order_date,
                "issued_date": date_issued,
                "expected_date": date_expected,
                "totals": {
                    "subtotal": float(total_cost),
                    "tax": 0.0,  # Fishbowl doesn't separate tax in basic order data
                    "total": float(total_cost),
                    "currency": self.currency_code
                },
                "line_items": line_items,
                "fishbowl_data": {
                    "location_group": fishbowl_order.get("LocationGroup", ""),
                    "carrier": fishbowl_order.get("Carrier", ""),
                    "ship_terms": fishbowl_order.get("ShipTerms", "")
                },
                "source": "fishbowl",
                "raw_data": fishbowl_order
            }
            
            logger.debug(f"Transformed purchase order {po_number}")
            return standard_order
            
        except Exception as e:
            logger.error(f"Failed to transform purchase order: {e}")
            raise FishbowlTransformationError(f"Purchase order transformation failed: {str(e)}")
    
    # Sales Order Transformations
    
    def transform_sales_order(self, fishbowl_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Fishbowl sales order to standard format.
        
        Args:
            fishbowl_order: Raw Fishbowl sales order data
            
        Returns:
            Standardized sales order data
        """
        try:
            # Extract order information
            so_number = fishbowl_order.get("Number", "")
            customer_name = fishbowl_order.get("CustomerName", "")
            status = fishbowl_order.get("Status", "")
            
            # Order details
            total_price = self._safe_decimal(fishbowl_order.get("TotalPrice", 0))
            
            # Dates
            order_date = self._parse_datetime(fishbowl_order.get("OrderDate"))
            date_issued = self._parse_datetime(fishbowl_order.get("DateIssued"))
            date_scheduled = self._parse_datetime(fishbowl_order.get("DateScheduled"))
            
            # Line items
            line_items = []
            items = fishbowl_order.get("Items", [])
            if isinstance(items, dict):
                items = [items]
            
            for item in items:
                line_item = {
                    "product_id": item.get("PartNumber", ""),
                    "description": item.get("Description", ""),
                    "quantity": float(self._safe_decimal(item.get("Quantity", 0))),
                    "unit_price": float(self._safe_decimal(item.get("UnitPrice", 0))),
                    "total_price": float(self._safe_decimal(item.get("TotalPrice", 0)))
                }
                line_items.append(line_item)
            
            # Build standard order format
            standard_order = {
                "id": so_number,
                "external_id": so_number,
                "order_number": so_number,
                "customer_id": customer_name,
                "customer_name": customer_name,
                "status": self._map_order_status(status),
                "order_date": order_date,
                "issued_date": date_issued,
                "scheduled_date": date_scheduled,
                "totals": {
                    "subtotal": float(total_price),
                    "tax": 0.0,
                    "total": float(total_price),
                    "currency": self.currency_code
                },
                "line_items": line_items,
                "fishbowl_data": {
                    "location_group": fishbowl_order.get("LocationGroup", ""),
                    "carrier": fishbowl_order.get("Carrier", ""),
                    "ship_terms": fishbowl_order.get("ShipTerms", "")
                },
                "source": "fishbowl",
                "raw_data": fishbowl_order
            }
            
            logger.debug(f"Transformed sales order {so_number}")
            return standard_order
            
        except Exception as e:
            logger.error(f"Failed to transform sales order: {e}")
            raise FishbowlTransformationError(f"Sales order transformation failed: {str(e)}")
    
    # Vendor Transformations
    
    def transform_vendor(self, fishbowl_vendor: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Fishbowl vendor to standard format.
        
        Args:
            fishbowl_vendor: Raw Fishbowl vendor data
            
        Returns:
            Standardized supplier data
        """
        try:
            # Extract vendor information
            vendor_name = fishbowl_vendor.get("Name", "")
            account_number = fishbowl_vendor.get("AccountNumber", "")
            
            # Contact information
            contact = fishbowl_vendor.get("Contact", {})
            email = contact.get("Email", "") if isinstance(contact, dict) else ""
            phone = contact.get("Phone", "") if isinstance(contact, dict) else ""
            
            # Address information
            address = fishbowl_vendor.get("Address", {})
            if isinstance(address, dict):
                street = address.get("Street", "")
                city = address.get("City", "")
                state = address.get("State", "")
                zip_code = address.get("Zip", "")
                country = address.get("Country", "")
            else:
                street = city = state = zip_code = country = ""
            
            # Status
            is_active = fishbowl_vendor.get("IsActive", True)
            
            # Build standard supplier format
            standard_supplier = {
                "id": account_number or vendor_name,
                "external_id": account_number,
                "name": vendor_name,
                "code": account_number,
                "status": "active" if is_active else "inactive",
                "contact": {
                    "email": email,
                    "phone": phone
                },
                "address": {
                    "street": street,
                    "city": city,
                    "state": state,
                    "postal_code": zip_code,
                    "country": country
                },
                "fishbowl_data": {
                    "vendor_id": fishbowl_vendor.get("ID", ""),
                    "tax_id": fishbowl_vendor.get("TaxID", ""),
                    "payment_terms": fishbowl_vendor.get("PaymentTerms", "")
                },
                "source": "fishbowl",
                "raw_data": fishbowl_vendor
            }
            
            logger.debug(f"Transformed vendor {vendor_name}")
            return standard_supplier
            
        except Exception as e:
            logger.error(f"Failed to transform vendor: {e}")
            raise FishbowlTransformationError(f"Vendor transformation failed: {str(e)}")
    
    # Location Transformations
    
    def transform_location(self, fishbowl_location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Fishbowl location to standard format.
        
        Args:
            fishbowl_location: Raw Fishbowl location data
            
        Returns:
            Standardized location data
        """
        try:
            # Extract location information
            location_name = fishbowl_location.get("Name", "")
            location_id = fishbowl_location.get("ID", "")
            
            # Address information
            address = fishbowl_location.get("Address", {})
            
            # Status
            is_active = fishbowl_location.get("IsActive", True)
            
            # Build standard location format
            standard_location = {
                "id": location_id or location_name,
                "external_id": location_id,
                "name": location_name,
                "code": location_name,
                "type": "warehouse",
                "status": "active" if is_active else "inactive",
                "address": {
                    "street": address.get("Street", "") if isinstance(address, dict) else "",
                    "city": address.get("City", "") if isinstance(address, dict) else "",
                    "state": address.get("State", "") if isinstance(address, dict) else "",
                    "postal_code": address.get("Zip", "") if isinstance(address, dict) else "",
                    "country": address.get("Country", "") if isinstance(address, dict) else ""
                },
                "source": "fishbowl",
                "raw_data": fishbowl_location
            }
            
            logger.debug(f"Transformed location {location_name}")
            return standard_location
            
        except Exception as e:
            logger.error(f"Failed to transform location: {e}")
            raise FishbowlTransformationError(f"Location transformation failed: {str(e)}")
    
    # Helper Methods
    
    def _safe_decimal(self, value: Any) -> Decimal:
        """Safely convert value to Decimal."""
        try:
            if value is None:
                return Decimal('0')
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal('0')
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[str]:
        """Parse datetime string to ISO format."""
        if not date_str:
            return None
        
        try:
            # Try to parse various datetime formats
            if 'T' in date_str:
                # ISO format
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Try basic date format
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            
            return dt.isoformat()
        except ValueError:
            logger.warning(f"Failed to parse datetime: {date_str}")
            return date_str
    
    def _map_part_type(self, fishbowl_type: str) -> str:
        """Map Fishbowl part type to standard type."""
        type_mapping = {
            "inventory": "product",
            "non-inventory": "service",
            "service": "service",
            "assembly": "bundle",
            "kit": "kit",
            "labor": "service",
            "overhead": "service"
        }
        return type_mapping.get(fishbowl_type.lower(), "product")
    
    def _map_order_status(self, fishbowl_status: str) -> str:
        """Map Fishbowl order status to standard status."""
        status_mapping = {
            "entered": "draft",
            "bid": "pending",
            "confirm": "confirmed",
            "issued": "issued",
            "in progress": "in_progress",
            "fulfilled": "fulfilled",
            "closed": "completed",
            "void": "cancelled"
        }
        return status_mapping.get(fishbowl_status.lower(), "pending")