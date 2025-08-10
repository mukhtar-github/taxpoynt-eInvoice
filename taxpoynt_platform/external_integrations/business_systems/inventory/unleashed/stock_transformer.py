"""
Unleashed Stock Transformer
Transforms Unleashed data to standardized inventory formats for TaxPoynt platform.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .exceptions import (
    UnleashedTransformationError,
    UnleashedValidationError,
    UnleashedDataError
)


logger = logging.getLogger(__name__)


class UnleashedStockTransformer:
    """
    Transforms Unleashed inventory data to standardized formats.
    
    Handles transformation of products, stock levels, movements,
    orders, and other inventory-related data to TaxPoynt standard schema.
    """
    
    def __init__(self, currency_code: str = "NGN"):
        """
        Initialize Unleashed stock transformer.
        
        Args:
            currency_code: Default currency code for transformations
        """
        self.currency_code = currency_code
    
    # Product Transformations
    
    def transform_product(self, unleashed_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Unleashed product to standard format.
        
        Args:
            unleashed_product: Raw Unleashed product data
            
        Returns:
            Standardized product data
        """
        try:
            # Extract basic product information
            product_guid = unleashed_product.get("Guid", "")
            product_code = unleashed_product.get("ProductCode", "")
            description = unleashed_product.get("ProductDescription", "")
            
            # Product classification
            product_group = unleashed_product.get("ProductGroup", "")
            unit_of_measure = unleashed_product.get("UnitOfMeasure", "")
            
            # Pricing information
            default_sell_price = self._safe_decimal(unleashed_product.get("DefaultSellPrice", 0))
            default_purchase_price = self._safe_decimal(unleashed_product.get("DefaultPurchasePrice", 0))
            average_cost = self._safe_decimal(unleashed_product.get("AverageCost", 0))
            
            # Physical attributes
            weight = self._safe_decimal(unleashed_product.get("Weight", 0))
            height = self._safe_decimal(unleashed_product.get("Height", 0))
            width = self._safe_decimal(unleashed_product.get("Width", 0))
            depth = self._safe_decimal(unleashed_product.get("Depth", 0))
            
            # Inventory settings
            is_sellable = unleashed_product.get("IsSellable", True)
            is_purchasable = unleashed_product.get("IsPurchasable", True)
            is_assembly = unleashed_product.get("IsAssembly", False)
            is_component = unleashed_product.get("IsComponent", False)
            
            # Stock tracking
            min_stock_alert_level = self._safe_decimal(unleashed_product.get("MinStockAlertLevel", 0))
            max_stock_alert_level = self._safe_decimal(unleashed_product.get("MaxStockAlertLevel", 0))
            
            # Supplier information
            default_supplier = unleashed_product.get("DefaultSupplier", {})
            default_supplier_code = default_supplier.get("SupplierCode", "") if isinstance(default_supplier, dict) else ""
            
            # Timestamps
            created_on = self._parse_datetime(unleashed_product.get("CreatedOn"))
            last_modified_on = self._parse_datetime(unleashed_product.get("LastModifiedOn"))
            
            # Build standard product format
            standard_product = {
                "id": product_code,
                "external_id": product_guid,
                "name": description or product_code,
                "description": description,
                "sku": product_code,
                "type": self._map_product_type(is_assembly, is_component),
                "category": product_group,
                "status": "active",  # Unleashed doesn't have explicit inactive products in basic data
                "is_tracked": True,  # Unleashed always tracks inventory
                "pricing": {
                    "selling_price": float(default_sell_price),
                    "cost_price": float(default_purchase_price or average_cost),
                    "average_cost": float(average_cost),
                    "currency": self.currency_code
                },
                "physical_attributes": {
                    "weight": float(weight),
                    "dimensions": {
                        "length": float(depth),  # Unleashed uses Depth for length
                        "width": float(width),
                        "height": float(height)
                    },
                    "weight_unit": "kg",
                    "dimension_unit": "cm"
                },
                "inventory_tracking": {
                    "track_stock": True,
                    "is_sellable": is_sellable,
                    "is_purchasable": is_purchasable,
                    "unit_of_measure": unit_of_measure
                },
                "reorder_info": {
                    "min_stock_level": float(min_stock_alert_level),
                    "max_stock_level": float(max_stock_alert_level),
                    "reorder_point": float(min_stock_alert_level)
                },
                "unleashed_data": {
                    "guid": product_guid,
                    "is_assembly": is_assembly,
                    "is_component": is_component,
                    "default_supplier_code": default_supplier_code,
                    "barcode": unleashed_product.get("Barcode", ""),
                    "bin_location": unleashed_product.get("BinLocation", ""),
                    "notes": unleashed_product.get("Notes", "")
                },
                "timestamps": {
                    "created_at": created_on,
                    "updated_at": last_modified_on
                },
                "source": "unleashed",
                "raw_data": unleashed_product
            }
            
            logger.debug(f"Transformed product {product_code}")
            return standard_product
            
        except Exception as e:
            logger.error(f"Failed to transform product: {e}")
            raise UnleashedTransformationError(f"Product transformation failed: {str(e)}")
    
    def transform_products(self, unleashed_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple Unleashed products to standard format.
        
        Args:
            unleashed_products: List of raw Unleashed product data
            
        Returns:
            List of standardized product data
        """
        transformed_products = []
        
        for product in unleashed_products:
            try:
                transformed_product = self.transform_product(product)
                transformed_products.append(transformed_product)
            except Exception as e:
                logger.warning(f"Skipping product transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_products)} products")
        return transformed_products
    
    # Stock On Hand Transformations
    
    def transform_stock_level(self, unleashed_stock: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Unleashed stock on hand to standard format.
        
        Args:
            unleashed_stock: Raw Unleashed stock on hand data
            
        Returns:
            Standardized stock level data
        """
        try:
            # Extract stock information
            product_code = unleashed_stock.get("ProductCode", "")
            warehouse_code = unleashed_stock.get("WarehouseCode", "")
            warehouse_guid = unleashed_stock.get("WarehouseGuid", "")
            
            # Quantity information
            qty_on_hand = self._safe_decimal(unleashed_stock.get("QtyOnHand", 0))
            qty_allocated = self._safe_decimal(unleashed_stock.get("QtyAllocated", 0))
            qty_available = self._safe_decimal(unleashed_stock.get("QtyAvailable", 0))
            qty_on_order = self._safe_decimal(unleashed_stock.get("QtyOnOrder", 0))
            
            # Cost information
            average_cost = self._safe_decimal(unleashed_stock.get("AverageCost", 0))
            total_value = qty_on_hand * average_cost
            
            # Timestamps
            last_modified_on = self._parse_datetime(unleashed_stock.get("LastModifiedOn"))
            
            # Build standard stock level format
            standard_stock = {
                "product_id": product_code,
                "location_id": warehouse_code,
                "location_guid": warehouse_guid,
                "quantities": {
                    "on_hand": float(qty_on_hand),
                    "allocated": float(qty_allocated),
                    "available": float(qty_available),
                    "on_order": float(qty_on_order),
                    "reserved": float(qty_allocated)
                },
                "valuation": {
                    "average_cost": float(average_cost),
                    "total_value": float(total_value),
                    "currency": self.currency_code
                },
                "timestamps": {
                    "last_updated": last_modified_on or datetime.utcnow().isoformat()
                },
                "source": "unleashed",
                "raw_data": unleashed_stock
            }
            
            logger.debug(f"Transformed stock level for product {product_code}")
            return standard_stock
            
        except Exception as e:
            logger.error(f"Failed to transform stock level: {e}")
            raise UnleashedTransformationError(f"Stock level transformation failed: {str(e)}")
    
    def transform_stock_levels(self, unleashed_stock_levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple Unleashed stock levels to standard format.
        
        Args:
            unleashed_stock_levels: List of raw Unleashed stock level data
            
        Returns:
            List of standardized stock level data
        """
        transformed_stock = []
        
        for stock in unleashed_stock_levels:
            try:
                transformed_stock_level = self.transform_stock_level(stock)
                transformed_stock.append(transformed_stock_level)
            except Exception as e:
                logger.warning(f"Skipping stock level transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_stock)} stock levels")
        return transformed_stock
    
    # Stock Movement Transformations
    
    def transform_stock_movement(self, unleashed_movement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Unleashed stock movement to standard format.
        
        Args:
            unleashed_movement: Raw Unleashed stock movement data
            
        Returns:
            Standardized stock movement data
        """
        try:
            # Extract movement information
            movement_guid = unleashed_movement.get("Guid", "")
            product_code = unleashed_movement.get("ProductCode", "")
            warehouse_code = unleashed_movement.get("WarehouseCode", "")
            
            # Movement details
            movement_type = unleashed_movement.get("MovementType", "")
            quantity = self._safe_decimal(unleashed_movement.get("Quantity", 0))
            unit_cost = self._safe_decimal(unleashed_movement.get("UnitCost", 0))
            
            # Reference information
            reference_number = unleashed_movement.get("ReferenceNumber", "")
            notes = unleashed_movement.get("Notes", "")
            
            # Timestamps
            created_on = self._parse_datetime(unleashed_movement.get("CreatedOn"))
            
            # Build standard movement format
            standard_movement = {
                "id": movement_guid,
                "external_id": movement_guid,
                "product_id": product_code,
                "location_id": warehouse_code,
                "movement_type": self._map_movement_type(movement_type),
                "quantity": float(quantity),
                "unit_cost": float(unit_cost),
                "total_cost": float(quantity * unit_cost),
                "currency": self.currency_code,
                "reference": {
                    "number": reference_number,
                    "type": movement_type,
                    "notes": notes
                },
                "timestamps": {
                    "created_at": created_on or datetime.utcnow().isoformat()
                },
                "source": "unleashed",
                "raw_data": unleashed_movement
            }
            
            logger.debug(f"Transformed stock movement {movement_guid}")
            return standard_movement
            
        except Exception as e:
            logger.error(f"Failed to transform stock movement: {e}")
            raise UnleashedTransformationError(f"Stock movement transformation failed: {str(e)}")
    
    def transform_stock_movements(self, unleashed_movements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple Unleashed stock movements to standard format.
        
        Args:
            unleashed_movements: List of raw Unleashed stock movement data
            
        Returns:
            List of standardized stock movement data
        """
        transformed_movements = []
        
        for movement in unleashed_movements:
            try:
                transformed_movement = self.transform_stock_movement(movement)
                transformed_movements.append(transformed_movement)
            except Exception as e:
                logger.warning(f"Skipping stock movement transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_movements)} stock movements")
        return transformed_movements
    
    # Purchase Order Transformations
    
    def transform_purchase_order(self, unleashed_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Unleashed purchase order to standard format.
        
        Args:
            unleashed_order: Raw Unleashed purchase order data
            
        Returns:
            Standardized purchase order data
        """
        try:
            # Extract order information
            order_guid = unleashed_order.get("Guid", "")
            order_number = unleashed_order.get("OrderNumber", "")
            supplier_code = unleashed_order.get("SupplierCode", "")
            
            # Order details
            order_status = unleashed_order.get("OrderStatus", "")
            subtotal = self._safe_decimal(unleashed_order.get("SubTotal", 0))
            tax_total = self._safe_decimal(unleashed_order.get("TaxTotal", 0))
            total = self._safe_decimal(unleashed_order.get("Total", 0))
            
            # Dates
            order_date = self._parse_datetime(unleashed_order.get("OrderDate"))
            required_date = self._parse_datetime(unleashed_order.get("RequiredDate"))
            completed_date = self._parse_datetime(unleashed_order.get("CompletedDate"))
            
            # Line items
            line_items = []
            items = unleashed_order.get("PurchaseOrderLines", [])
            
            for item in items:
                line_item = {
                    "product_code": item.get("ProductCode", ""),
                    "description": item.get("ProductDescription", ""),
                    "quantity": float(self._safe_decimal(item.get("OrderQuantity", 0))),
                    "unit_cost": float(self._safe_decimal(item.get("UnitCost", 0))),
                    "total_cost": float(self._safe_decimal(item.get("LineTotal", 0)))
                }
                line_items.append(line_item)
            
            # Build standard order format
            standard_order = {
                "id": order_number,
                "external_id": order_guid,
                "order_number": order_number,
                "supplier_id": supplier_code,
                "status": self._map_order_status(order_status),
                "order_date": order_date,
                "required_date": required_date,
                "completed_date": completed_date,
                "totals": {
                    "subtotal": float(subtotal),
                    "tax": float(tax_total),
                    "total": float(total),
                    "currency": self.currency_code
                },
                "line_items": line_items,
                "unleashed_data": {
                    "guid": order_guid,
                    "warehouse_code": unleashed_order.get("WarehouseCode", ""),
                    "notes": unleashed_order.get("Comments", "")
                },
                "source": "unleashed",
                "raw_data": unleashed_order
            }
            
            logger.debug(f"Transformed purchase order {order_number}")
            return standard_order
            
        except Exception as e:
            logger.error(f"Failed to transform purchase order: {e}")
            raise UnleashedTransformationError(f"Purchase order transformation failed: {str(e)}")
    
    # Sales Order Transformations
    
    def transform_sales_order(self, unleashed_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Unleashed sales order to standard format.
        
        Args:
            unleashed_order: Raw Unleashed sales order data
            
        Returns:
            Standardized sales order data
        """
        try:
            # Extract order information
            order_guid = unleashed_order.get("Guid", "")
            order_number = unleashed_order.get("OrderNumber", "")
            customer_code = unleashed_order.get("CustomerCode", "")
            
            # Order details
            order_status = unleashed_order.get("OrderStatus", "")
            subtotal = self._safe_decimal(unleashed_order.get("SubTotal", 0))
            tax_total = self._safe_decimal(unleashed_order.get("TaxTotal", 0))
            total = self._safe_decimal(unleashed_order.get("Total", 0))
            
            # Dates
            order_date = self._parse_datetime(unleashed_order.get("OrderDate"))
            required_date = self._parse_datetime(unleashed_order.get("RequiredDate"))
            completed_date = self._parse_datetime(unleashed_order.get("CompletedDate"))
            
            # Line items
            line_items = []
            items = unleashed_order.get("SalesOrderLines", [])
            
            for item in items:
                line_item = {
                    "product_code": item.get("ProductCode", ""),
                    "description": item.get("ProductDescription", ""),
                    "quantity": float(self._safe_decimal(item.get("OrderQuantity", 0))),
                    "unit_price": float(self._safe_decimal(item.get("UnitPrice", 0))),
                    "total_price": float(self._safe_decimal(item.get("LineTotal", 0)))
                }
                line_items.append(line_item)
            
            # Build standard order format
            standard_order = {
                "id": order_number,
                "external_id": order_guid,
                "order_number": order_number,
                "customer_id": customer_code,
                "status": self._map_order_status(order_status),
                "order_date": order_date,
                "required_date": required_date,
                "completed_date": completed_date,
                "totals": {
                    "subtotal": float(subtotal),
                    "tax": float(tax_total),
                    "total": float(total),
                    "currency": self.currency_code
                },
                "line_items": line_items,
                "unleashed_data": {
                    "guid": order_guid,
                    "warehouse_code": unleashed_order.get("WarehouseCode", ""),
                    "notes": unleashed_order.get("Comments", "")
                },
                "source": "unleashed",
                "raw_data": unleashed_order
            }
            
            logger.debug(f"Transformed sales order {order_number}")
            return standard_order
            
        except Exception as e:
            logger.error(f"Failed to transform sales order: {e}")
            raise UnleashedTransformationError(f"Sales order transformation failed: {str(e)}")
    
    # Supplier Transformations
    
    def transform_supplier(self, unleashed_supplier: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Unleashed supplier to standard format.
        
        Args:
            unleashed_supplier: Raw Unleashed supplier data
            
        Returns:
            Standardized supplier data
        """
        try:
            # Extract supplier information
            supplier_guid = unleashed_supplier.get("Guid", "")
            supplier_code = unleashed_supplier.get("SupplierCode", "")
            supplier_name = unleashed_supplier.get("SupplierName", "")
            
            # Contact information
            email = unleashed_supplier.get("Email", "")
            phone = unleashed_supplier.get("PhoneNumber", "")
            mobile = unleashed_supplier.get("MobileNumber", "")
            
            # Address information - Unleashed can have multiple addresses
            addresses = unleashed_supplier.get("Addresses", [])
            primary_address = addresses[0] if addresses else {}
            
            # Status
            is_active = unleashed_supplier.get("IsActive", True)
            
            # Build standard supplier format
            standard_supplier = {
                "id": supplier_code,
                "external_id": supplier_guid,
                "name": supplier_name,
                "code": supplier_code,
                "status": "active" if is_active else "inactive",
                "contact": {
                    "email": email,
                    "phone": phone,
                    "mobile": mobile
                },
                "address": {
                    "street": primary_address.get("AddressLine1", "") if isinstance(primary_address, dict) else "",
                    "city": primary_address.get("City", "") if isinstance(primary_address, dict) else "",
                    "state": primary_address.get("Region", "") if isinstance(primary_address, dict) else "",
                    "postal_code": primary_address.get("PostalCode", "") if isinstance(primary_address, dict) else "",
                    "country": primary_address.get("Country", "") if isinstance(primary_address, dict) else ""
                },
                "unleashed_data": {
                    "guid": supplier_guid,
                    "tax_number": unleashed_supplier.get("TaxNumber", ""),
                    "currency_code": unleashed_supplier.get("Currency", {}).get("CurrencyCode", "") if isinstance(unleashed_supplier.get("Currency"), dict) else "",
                    "payment_terms": unleashed_supplier.get("PaymentTerm", ""),
                    "notes": unleashed_supplier.get("Notes", "")
                },
                "source": "unleashed",
                "raw_data": unleashed_supplier
            }
            
            logger.debug(f"Transformed supplier {supplier_code}")
            return standard_supplier
            
        except Exception as e:
            logger.error(f"Failed to transform supplier: {e}")
            raise UnleashedTransformationError(f"Supplier transformation failed: {str(e)}")
    
    # Warehouse Transformations
    
    def transform_warehouse(self, unleashed_warehouse: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Unleashed warehouse to standard format.
        
        Args:
            unleashed_warehouse: Raw Unleashed warehouse data
            
        Returns:
            Standardized location data
        """
        try:
            # Extract warehouse information
            warehouse_guid = unleashed_warehouse.get("Guid", "")
            warehouse_code = unleashed_warehouse.get("WarehouseCode", "")
            warehouse_name = unleashed_warehouse.get("WarehouseName", "")
            
            # Address information
            address_line1 = unleashed_warehouse.get("AddressLine1", "")
            address_line2 = unleashed_warehouse.get("AddressLine2", "")
            city = unleashed_warehouse.get("City", "")
            region = unleashed_warehouse.get("Region", "")
            postal_code = unleashed_warehouse.get("PostalCode", "")
            country = unleashed_warehouse.get("Country", "")
            
            # Contact information
            phone = unleashed_warehouse.get("PhoneNumber", "")
            fax = unleashed_warehouse.get("FaxNumber", "")
            
            # Status
            is_active = unleashed_warehouse.get("IsActive", True)
            
            # Build standard location format
            standard_location = {
                "id": warehouse_code,
                "external_id": warehouse_guid,
                "name": warehouse_name,
                "code": warehouse_code,
                "type": "warehouse",
                "status": "active" if is_active else "inactive",
                "contact": {
                    "phone": phone,
                    "fax": fax
                },
                "address": {
                    "street": f"{address_line1} {address_line2}".strip(),
                    "city": city,
                    "state": region,
                    "postal_code": postal_code,
                    "country": country
                },
                "unleashed_data": {
                    "guid": warehouse_guid,
                    "is_default": unleashed_warehouse.get("IsDefault", False)
                },
                "source": "unleashed",
                "raw_data": unleashed_warehouse
            }
            
            logger.debug(f"Transformed warehouse {warehouse_code}")
            return standard_location
            
        except Exception as e:
            logger.error(f"Failed to transform warehouse: {e}")
            raise UnleashedTransformationError(f"Warehouse transformation failed: {str(e)}")
    
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
            # Unleashed uses ISO format with timezone info
            if 'T' in date_str:
                # Handle timezone info
                if date_str.endswith('Z'):
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                elif '+' in date_str or date_str.count('-') > 2:
                    dt = datetime.fromisoformat(date_str)
                else:
                    dt = datetime.fromisoformat(date_str)
            else:
                # Try basic date format
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            
            return dt.isoformat()
        except ValueError:
            logger.warning(f"Failed to parse datetime: {date_str}")
            return date_str
    
    def _map_product_type(self, is_assembly: bool, is_component: bool) -> str:
        """Map Unleashed product attributes to standard type."""
        if is_assembly:
            return "bundle"
        elif is_component:
            return "component"
        else:
            return "product"
    
    def _map_movement_type(self, unleashed_type: str) -> str:
        """Map Unleashed movement type to standard type."""
        type_mapping = {
            "sale": "outbound",
            "purchase": "inbound",
            "adjustment": "adjustment",
            "transfer": "transfer",
            "manufacturing": "production",
            "return": "return",
            "receipt": "inbound",
            "issue": "outbound"
        }
        return type_mapping.get(unleashed_type.lower(), "adjustment")
    
    def _map_order_status(self, unleashed_status: str) -> str:
        """Map Unleashed order status to standard status."""
        status_mapping = {
            "placed": "pending",
            "confirmed": "confirmed",
            "completed": "completed",
            "cancelled": "cancelled",
            "parked": "draft",
            "backordered": "backordered"
        }
        return status_mapping.get(unleashed_status.lower(), "pending")