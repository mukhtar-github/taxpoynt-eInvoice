"""
Cin7 Stock Transformer
Transforms Cin7 data to standardized inventory formats for TaxPoynt platform.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .exceptions import (
    Cin7TransformationError,
    Cin7ValidationError,
    Cin7DataError
)


logger = logging.getLogger(__name__)


class Cin7StockTransformer:
    """
    Transforms Cin7 inventory data to standardized formats.
    
    Handles transformation of products, stock levels, movements,
    orders, and other inventory-related data to TaxPoynt standard schema.
    """
    
    def __init__(self, currency_code: str = "NGN"):
        """
        Initialize Cin7 stock transformer.
        
        Args:
            currency_code: Default currency code for transformations
        """
        self.currency_code = currency_code
    
    # Product Transformations
    
    def transform_product(self, cin7_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Cin7 product to standard format.
        
        Args:
            cin7_product: Raw Cin7 product data
            
        Returns:
            Standardized product data
        """
        try:
            # Extract basic product information
            product_id = str(cin7_product.get("Id", ""))
            name = cin7_product.get("Name", "")
            description = cin7_product.get("Description", "")
            sku = cin7_product.get("SKU", "")
            
            # Product type and category
            product_type = cin7_product.get("Type", "").lower()
            category = cin7_product.get("Category", "")
            
            # Pricing information
            selling_price = self._safe_decimal(cin7_product.get("SellingPrice", 0))
            cost_price = self._safe_decimal(cin7_product.get("CostPrice", 0))
            
            # Physical attributes
            weight = self._safe_decimal(cin7_product.get("Weight", 0))
            length = self._safe_decimal(cin7_product.get("Length", 0))
            width = self._safe_decimal(cin7_product.get("Width", 0))
            height = self._safe_decimal(cin7_product.get("Height", 0))
            
            # Status and tracking
            is_active = cin7_product.get("IsActive", True)
            is_tracked = cin7_product.get("IsTracked", True)
            
            # Timestamps
            created_date = self._parse_datetime(cin7_product.get("CreatedDate"))
            modified_date = self._parse_datetime(cin7_product.get("LastModified"))
            
            # Build standard product format
            standard_product = {
                "id": product_id,
                "external_id": product_id,
                "name": name,
                "description": description,
                "sku": sku,
                "type": self._map_product_type(product_type),
                "category": category,
                "status": "active" if is_active else "inactive",
                "is_tracked": is_tracked,
                "pricing": {
                    "selling_price": float(selling_price),
                    "cost_price": float(cost_price),
                    "currency": self.currency_code
                },
                "physical_attributes": {
                    "weight": float(weight),
                    "dimensions": {
                        "length": float(length),
                        "width": float(width),
                        "height": float(height)
                    },
                    "weight_unit": "kg",
                    "dimension_unit": "cm"
                },
                "inventory_tracking": {
                    "track_stock": is_tracked,
                    "reorder_point": self._safe_decimal(cin7_product.get("ReorderPoint", 0)),
                    "max_stock_level": self._safe_decimal(cin7_product.get("MaxStockLevel", 0))
                },
                "timestamps": {
                    "created_at": created_date,
                    "updated_at": modified_date
                },
                "source": "cin7",
                "raw_data": cin7_product
            }
            
            logger.debug(f"Transformed product {product_id}")
            return standard_product
            
        except Exception as e:
            logger.error(f"Failed to transform product: {e}")
            raise Cin7TransformationError(f"Product transformation failed: {str(e)}")
    
    def transform_products(self, cin7_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple Cin7 products to standard format.
        
        Args:
            cin7_products: List of raw Cin7 product data
            
        Returns:
            List of standardized product data
        """
        transformed_products = []
        
        for product in cin7_products:
            try:
                transformed_product = self.transform_product(product)
                transformed_products.append(transformed_product)
            except Exception as e:
                logger.warning(f"Skipping product transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_products)} products")
        return transformed_products
    
    # Stock Level Transformations
    
    def transform_stock_level(self, cin7_stock: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Cin7 stock level to standard format.
        
        Args:
            cin7_stock: Raw Cin7 stock level data
            
        Returns:
            Standardized stock level data
        """
        try:
            # Extract stock information
            product_id = str(cin7_stock.get("ProductId", ""))
            location_id = str(cin7_stock.get("LocationId", ""))
            
            # Quantity information
            qty_on_hand = self._safe_decimal(cin7_stock.get("QtyOnHand", 0))
            qty_allocated = self._safe_decimal(cin7_stock.get("QtyAllocated", 0))
            qty_available = self._safe_decimal(cin7_stock.get("QtyAvailable", 0))
            qty_on_order = self._safe_decimal(cin7_stock.get("QtyOnOrder", 0))
            
            # Cost information
            avg_cost = self._safe_decimal(cin7_stock.get("AverageCost", 0))
            total_value = self._safe_decimal(cin7_stock.get("TotalValue", 0))
            
            # Timestamps
            last_updated = self._parse_datetime(cin7_stock.get("LastUpdated"))
            
            # Build standard stock level format
            standard_stock = {
                "product_id": product_id,
                "location_id": location_id,
                "quantities": {
                    "on_hand": float(qty_on_hand),
                    "allocated": float(qty_allocated),
                    "available": float(qty_available),
                    "on_order": float(qty_on_order),
                    "reserved": float(qty_allocated)
                },
                "valuation": {
                    "average_cost": float(avg_cost),
                    "total_value": float(total_value),
                    "currency": self.currency_code
                },
                "reorder_info": {
                    "reorder_point": self._safe_decimal(cin7_stock.get("ReorderPoint", 0)),
                    "max_stock_level": self._safe_decimal(cin7_stock.get("MaxStockLevel", 0)),
                    "needs_reorder": float(qty_available) <= float(self._safe_decimal(cin7_stock.get("ReorderPoint", 0)))
                },
                "timestamps": {
                    "last_updated": last_updated
                },
                "source": "cin7",
                "raw_data": cin7_stock
            }
            
            logger.debug(f"Transformed stock level for product {product_id}")
            return standard_stock
            
        except Exception as e:
            logger.error(f"Failed to transform stock level: {e}")
            raise Cin7TransformationError(f"Stock level transformation failed: {str(e)}")
    
    def transform_stock_levels(self, cin7_stock_levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple Cin7 stock levels to standard format.
        
        Args:
            cin7_stock_levels: List of raw Cin7 stock level data
            
        Returns:
            List of standardized stock level data
        """
        transformed_stock = []
        
        for stock in cin7_stock_levels:
            try:
                transformed_stock_level = self.transform_stock_level(stock)
                transformed_stock.append(transformed_stock_level)
            except Exception as e:
                logger.warning(f"Skipping stock level transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_stock)} stock levels")
        return transformed_stock
    
    # Stock Movement Transformations
    
    def transform_stock_movement(self, cin7_movement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Cin7 stock movement to standard format.
        
        Args:
            cin7_movement: Raw Cin7 stock movement data
            
        Returns:
            Standardized stock movement data
        """
        try:
            # Extract movement information
            movement_id = str(cin7_movement.get("Id", ""))
            product_id = str(cin7_movement.get("ProductId", ""))
            location_id = str(cin7_movement.get("LocationId", ""))
            
            # Movement details
            movement_type = cin7_movement.get("MovementType", "")
            quantity = self._safe_decimal(cin7_movement.get("Quantity", 0))
            unit_cost = self._safe_decimal(cin7_movement.get("UnitCost", 0))
            
            # Reference information
            reference_id = cin7_movement.get("ReferenceId", "")
            reference_type = cin7_movement.get("ReferenceType", "")
            notes = cin7_movement.get("Notes", "")
            
            # Timestamps
            created_date = self._parse_datetime(cin7_movement.get("CreatedDate"))
            
            # Build standard movement format
            standard_movement = {
                "id": movement_id,
                "external_id": movement_id,
                "product_id": product_id,
                "location_id": location_id,
                "movement_type": self._map_movement_type(movement_type),
                "quantity": float(quantity),
                "unit_cost": float(unit_cost),
                "total_cost": float(quantity * unit_cost),
                "currency": self.currency_code,
                "reference": {
                    "id": reference_id,
                    "type": reference_type,
                    "notes": notes
                },
                "timestamps": {
                    "created_at": created_date
                },
                "source": "cin7",
                "raw_data": cin7_movement
            }
            
            logger.debug(f"Transformed stock movement {movement_id}")
            return standard_movement
            
        except Exception as e:
            logger.error(f"Failed to transform stock movement: {e}")
            raise Cin7TransformationError(f"Stock movement transformation failed: {str(e)}")
    
    def transform_stock_movements(self, cin7_movements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple Cin7 stock movements to standard format.
        
        Args:
            cin7_movements: List of raw Cin7 stock movement data
            
        Returns:
            List of standardized stock movement data
        """
        transformed_movements = []
        
        for movement in cin7_movements:
            try:
                transformed_movement = self.transform_stock_movement(movement)
                transformed_movements.append(transformed_movement)
            except Exception as e:
                logger.warning(f"Skipping stock movement transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_movements)} stock movements")
        return transformed_movements
    
    # Purchase Order Transformations
    
    def transform_purchase_order(self, cin7_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Cin7 purchase order to standard format.
        
        Args:
            cin7_order: Raw Cin7 purchase order data
            
        Returns:
            Standardized purchase order data
        """
        try:
            # Extract order information
            order_id = str(cin7_order.get("Id", ""))
            order_number = cin7_order.get("OrderNumber", "")
            supplier_id = str(cin7_order.get("SupplierId", ""))
            
            # Order details
            status = cin7_order.get("Status", "")
            total_amount = self._safe_decimal(cin7_order.get("TotalAmount", 0))
            
            # Dates
            order_date = self._parse_datetime(cin7_order.get("OrderDate"))
            expected_date = self._parse_datetime(cin7_order.get("ExpectedDate"))
            
            # Line items
            line_items = []
            for item in cin7_order.get("LineItems", []):
                line_item = {
                    "product_id": str(item.get("ProductId", "")),
                    "quantity": float(self._safe_decimal(item.get("Quantity", 0))),
                    "unit_cost": float(self._safe_decimal(item.get("UnitCost", 0))),
                    "total_cost": float(self._safe_decimal(item.get("TotalCost", 0)))
                }
                line_items.append(line_item)
            
            # Build standard order format
            standard_order = {
                "id": order_id,
                "external_id": order_id,
                "order_number": order_number,
                "supplier_id": supplier_id,
                "status": self._map_order_status(status),
                "order_date": order_date,
                "expected_date": expected_date,
                "totals": {
                    "subtotal": float(total_amount),
                    "tax": 0.0,  # Cin7 doesn't separate tax in basic order data
                    "total": float(total_amount),
                    "currency": self.currency_code
                },
                "line_items": line_items,
                "source": "cin7",
                "raw_data": cin7_order
            }
            
            logger.debug(f"Transformed purchase order {order_id}")
            return standard_order
            
        except Exception as e:
            logger.error(f"Failed to transform purchase order: {e}")
            raise Cin7TransformationError(f"Purchase order transformation failed: {str(e)}")
    
    # Location Transformations
    
    def transform_location(self, cin7_location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Cin7 location to standard format.
        
        Args:
            cin7_location: Raw Cin7 location data
            
        Returns:
            Standardized location data
        """
        try:
            # Extract location information
            location_id = str(cin7_location.get("Id", ""))
            name = cin7_location.get("Name", "")
            code = cin7_location.get("Code", "")
            
            # Address information
            address = cin7_location.get("Address", {})
            
            # Status
            is_active = cin7_location.get("IsActive", True)
            
            # Build standard location format
            standard_location = {
                "id": location_id,
                "external_id": location_id,
                "name": name,
                "code": code,
                "type": "warehouse",  # Cin7 locations are typically warehouses
                "status": "active" if is_active else "inactive",
                "address": {
                    "street": address.get("Street", ""),
                    "city": address.get("City", ""),
                    "state": address.get("State", ""),
                    "postal_code": address.get("PostalCode", ""),
                    "country": address.get("Country", "")
                },
                "source": "cin7",
                "raw_data": cin7_location
            }
            
            logger.debug(f"Transformed location {location_id}")
            return standard_location
            
        except Exception as e:
            logger.error(f"Failed to transform location: {e}")
            raise Cin7TransformationError(f"Location transformation failed: {str(e)}")
    
    # Supplier Transformations
    
    def transform_supplier(self, cin7_supplier: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Cin7 supplier to standard format.
        
        Args:
            cin7_supplier: Raw Cin7 supplier data
            
        Returns:
            Standardized supplier data
        """
        try:
            # Extract supplier information
            supplier_id = str(cin7_supplier.get("Id", ""))
            name = cin7_supplier.get("Name", "")
            code = cin7_supplier.get("Code", "")
            
            # Contact information
            email = cin7_supplier.get("Email", "")
            phone = cin7_supplier.get("Phone", "")
            
            # Address information
            address = cin7_supplier.get("Address", {})
            
            # Status
            is_active = cin7_supplier.get("IsActive", True)
            
            # Build standard supplier format
            standard_supplier = {
                "id": supplier_id,
                "external_id": supplier_id,
                "name": name,
                "code": code,
                "status": "active" if is_active else "inactive",
                "contact": {
                    "email": email,
                    "phone": phone
                },
                "address": {
                    "street": address.get("Street", ""),
                    "city": address.get("City", ""),
                    "state": address.get("State", ""),
                    "postal_code": address.get("PostalCode", ""),
                    "country": address.get("Country", "")
                },
                "source": "cin7",
                "raw_data": cin7_supplier
            }
            
            logger.debug(f"Transformed supplier {supplier_id}")
            return standard_supplier
            
        except Exception as e:
            logger.error(f"Failed to transform supplier: {e}")
            raise Cin7TransformationError(f"Supplier transformation failed: {str(e)}")
    
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
    
    def _map_product_type(self, cin7_type: str) -> str:
        """Map Cin7 product type to standard type."""
        type_mapping = {
            "inventory": "product",
            "noninventory": "service",
            "service": "service",
            "assembly": "bundle",
            "kit": "kit"
        }
        return type_mapping.get(cin7_type.lower(), "product")
    
    def _map_movement_type(self, cin7_type: str) -> str:
        """Map Cin7 movement type to standard type."""
        type_mapping = {
            "sale": "outbound",
            "purchase": "inbound",
            "adjustment": "adjustment",
            "transfer": "transfer",
            "manufacturing": "production",
            "return": "return"
        }
        return type_mapping.get(cin7_type.lower(), "adjustment")
    
    def _map_order_status(self, cin7_status: str) -> str:
        """Map Cin7 order status to standard status."""
        status_mapping = {
            "draft": "draft",
            "pending": "pending",
            "approved": "approved",
            "sent": "sent",
            "received": "received",
            "complete": "completed",
            "cancelled": "cancelled"
        }
        return status_mapping.get(cin7_status.lower(), "pending")