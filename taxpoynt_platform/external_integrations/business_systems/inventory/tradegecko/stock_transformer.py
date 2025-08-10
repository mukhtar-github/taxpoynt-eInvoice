"""
TradeGecko Stock Transformer
Transforms TradeGecko data to standardized inventory formats for TaxPoynt platform.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .exceptions import (
    TradeGeckoTransformationError,
    TradeGeckoValidationError,
    TradeGeckoDataError
)


logger = logging.getLogger(__name__)


class TradeGeckoStockTransformer:
    """
    Transforms TradeGecko inventory data to standardized formats.
    
    Handles transformation of products, variants, stock levels, orders,
    and other inventory-related data to TaxPoynt standard schema.
    """
    
    def __init__(self, currency_code: str = "NGN"):
        """
        Initialize TradeGecko stock transformer.
        
        Args:
            currency_code: Default currency code for transformations
        """
        self.currency_code = currency_code
    
    # Product Transformations
    
    def transform_product(self, tradegecko_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform TradeGecko product to standard format.
        
        Args:
            tradegecko_product: Raw TradeGecko product data
            
        Returns:
            Standardized product data
        """
        try:
            # Extract basic product information
            product_id = str(tradegecko_product.get("id", ""))
            name = tradegecko_product.get("name", "")
            description = tradegecko_product.get("description", "")
            brand = tradegecko_product.get("brand", "")
            
            # Product type and category
            product_type = tradegecko_product.get("product_type", "")
            tags = tradegecko_product.get("tags", "")
            
            # Status
            product_status = tradegecko_product.get("product_status", "active")
            is_active = product_status.lower() == "active"
            
            # Timestamps
            created_at = self._parse_datetime(tradegecko_product.get("created_at"))
            updated_at = self._parse_datetime(tradegecko_product.get("updated_at"))
            
            # Variants handling
            variants = tradegecko_product.get("variants", [])
            has_variants = len(variants) > 0
            
            # For products with variants, aggregate pricing from first variant
            pricing_info = {"selling_price": 0.0, "cost_price": 0.0}
            if variants and len(variants) > 0:
                first_variant = variants[0]
                pricing_info = {
                    "selling_price": float(self._safe_decimal(first_variant.get("retail_price", 0))),
                    "cost_price": float(self._safe_decimal(first_variant.get("cost_price", 0)))
                }
            
            # Build standard product format
            standard_product = {
                "id": product_id,
                "external_id": product_id,
                "name": name,
                "description": description,
                "sku": product_id,  # TradeGecko uses ID as primary reference
                "type": self._map_product_type(product_type),
                "category": tags.split(",")[0].strip() if tags else "",
                "brand": brand,
                "status": "active" if is_active else "inactive",
                "is_tracked": True,  # TradeGecko always tracks inventory
                "pricing": {
                    "selling_price": pricing_info["selling_price"],
                    "cost_price": pricing_info["cost_price"],
                    "currency": self.currency_code
                },
                "variants": {
                    "has_variants": has_variants,
                    "variant_count": len(variants),
                    "variants": [self._transform_variant_summary(v) for v in variants[:5]]  # First 5 variants
                },
                "inventory_tracking": {
                    "track_stock": True,
                    "has_multiple_variants": has_variants
                },
                "tradegecko_data": {
                    "supplier_ids": tradegecko_product.get("supplier_ids", []),
                    "image_ids": tradegecko_product.get("image_ids", []),
                    "opt1": tradegecko_product.get("opt1", ""),
                    "opt2": tradegecko_product.get("opt2", ""),
                    "opt3": tradegecko_product.get("opt3", "")
                },
                "timestamps": {
                    "created_at": created_at,
                    "updated_at": updated_at
                },
                "source": "tradegecko",
                "raw_data": tradegecko_product
            }
            
            logger.debug(f"Transformed product {product_id}")
            return standard_product
            
        except Exception as e:
            logger.error(f"Failed to transform product: {e}")
            raise TradeGeckoTransformationError(f"Product transformation failed: {str(e)}")
    
    def transform_products(self, tradegecko_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple TradeGecko products to standard format.
        
        Args:
            tradegecko_products: List of raw TradeGecko product data
            
        Returns:
            List of standardized product data
        """
        transformed_products = []
        
        for product in tradegecko_products:
            try:
                transformed_product = self.transform_product(product)
                transformed_products.append(transformed_product)
            except Exception as e:
                logger.warning(f"Skipping product transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_products)} products")
        return transformed_products
    
    # Variant Transformations
    
    def transform_variant(self, tradegecko_variant: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform TradeGecko variant to standard format.
        
        Args:
            tradegecko_variant: Raw TradeGecko variant data
            
        Returns:
            Standardized variant data
        """
        try:
            # Extract basic variant information
            variant_id = str(tradegecko_variant.get("id", ""))
            product_id = str(tradegecko_variant.get("product_id", ""))
            sku = tradegecko_variant.get("sku", "")
            name = tradegecko_variant.get("name", "")
            
            # Pricing information
            retail_price = self._safe_decimal(tradegecko_variant.get("retail_price", 0))
            cost_price = self._safe_decimal(tradegecko_variant.get("cost_price", 0))
            wholesale_price = self._safe_decimal(tradegecko_variant.get("wholesale_price", 0))
            
            # Physical attributes
            weight = self._safe_decimal(tradegecko_variant.get("weight", 0))
            
            # Inventory settings
            is_sellable = tradegecko_variant.get("is_sellable", True)
            track_inventory = tradegecko_variant.get("track_inventory", True)
            
            # Status
            variant_status = tradegecko_variant.get("variant_status", "active")
            is_active = variant_status.lower() == "active"
            
            # Timestamps
            created_at = self._parse_datetime(tradegecko_variant.get("created_at"))
            updated_at = self._parse_datetime(tradegecko_variant.get("updated_at"))
            
            # Build standard variant format
            standard_variant = {
                "id": variant_id,
                "external_id": variant_id,
                "product_id": product_id,
                "name": name,
                "sku": sku,
                "status": "active" if is_active else "inactive",
                "is_sellable": is_sellable,
                "pricing": {
                    "retail_price": float(retail_price),
                    "cost_price": float(cost_price),
                    "wholesale_price": float(wholesale_price),
                    "currency": self.currency_code
                },
                "physical_attributes": {
                    "weight": float(weight),
                    "weight_unit": "kg"
                },
                "inventory_tracking": {
                    "track_inventory": track_inventory,
                    "is_sellable": is_sellable
                },
                "variant_options": {
                    "option1": tradegecko_variant.get("option1_value", ""),
                    "option2": tradegecko_variant.get("option2_value", ""),
                    "option3": tradegecko_variant.get("option3_value", "")
                },
                "timestamps": {
                    "created_at": created_at,
                    "updated_at": updated_at
                },
                "source": "tradegecko",
                "raw_data": tradegecko_variant
            }
            
            logger.debug(f"Transformed variant {variant_id}")
            return standard_variant
            
        except Exception as e:
            logger.error(f"Failed to transform variant: {e}")
            raise TradeGeckoTransformationError(f"Variant transformation failed: {str(e)}")
    
    # Stock Level Transformations
    
    def transform_stock_level(self, tradegecko_stock: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform TradeGecko stock level to standard format.
        
        Args:
            tradegecko_stock: Raw TradeGecko stock level data
            
        Returns:
            Standardized stock level data
        """
        try:
            # Extract stock information
            variant_id = str(tradegecko_stock.get("variant_id", ""))
            location_id = str(tradegecko_stock.get("location_id", ""))
            
            # Quantity information
            stock_on_hand = self._safe_decimal(tradegecko_stock.get("stock_on_hand", 0))
            allocated_stock = self._safe_decimal(tradegecko_stock.get("allocated_stock", 0))
            available_stock = self._safe_decimal(tradegecko_stock.get("available_stock", 0))
            
            # Inventory settings
            infinite = tradegecko_stock.get("infinite", False)
            
            # Timestamps
            updated_at = self._parse_datetime(tradegecko_stock.get("updated_at"))
            
            # Build standard stock level format
            standard_stock = {
                "product_id": variant_id,  # In TradeGecko, variants are the trackable units
                "variant_id": variant_id,
                "location_id": location_id,
                "quantities": {
                    "on_hand": float(stock_on_hand),
                    "allocated": float(allocated_stock),
                    "available": float(available_stock),
                    "reserved": float(allocated_stock),
                    "infinite": infinite
                },
                "reorder_info": {
                    "reorder_point": 0,  # TradeGecko doesn't expose reorder points in stock levels
                    "max_stock_level": 0,
                    "needs_reorder": float(available_stock) <= 0 and not infinite
                },
                "timestamps": {
                    "last_updated": updated_at or datetime.utcnow().isoformat()
                },
                "source": "tradegecko",
                "raw_data": tradegecko_stock
            }
            
            logger.debug(f"Transformed stock level for variant {variant_id}")
            return standard_stock
            
        except Exception as e:
            logger.error(f"Failed to transform stock level: {e}")
            raise TradeGeckoTransformationError(f"Stock level transformation failed: {str(e)}")
    
    def transform_stock_levels(self, tradegecko_stock_levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform multiple TradeGecko stock levels to standard format.
        
        Args:
            tradegecko_stock_levels: List of raw TradeGecko stock level data
            
        Returns:
            List of standardized stock level data
        """
        transformed_stock = []
        
        for stock in tradegecko_stock_levels:
            try:
                transformed_stock_level = self.transform_stock_level(stock)
                transformed_stock.append(transformed_stock_level)
            except Exception as e:
                logger.warning(f"Skipping stock level transformation due to error: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed_stock)} stock levels")
        return transformed_stock
    
    # Stock Movement Transformations
    
    def transform_stock_movement(self, tradegecko_movement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform TradeGecko stock movement to standard format.
        
        Args:
            tradegecko_movement: Raw TradeGecko stock movement data
            
        Returns:
            Standardized stock movement data
        """
        try:
            # Extract movement information
            movement_id = str(tradegecko_movement.get("id", ""))
            variant_id = str(tradegecko_movement.get("variant_id", ""))
            location_id = str(tradegecko_movement.get("location_id", ""))
            
            # Movement details
            movement_type = tradegecko_movement.get("movement_type", "")
            quantity = self._safe_decimal(tradegecko_movement.get("quantity", 0))
            
            # Reference information
            moveable_id = tradegecko_movement.get("moveable_id", "")
            moveable_type = tradegecko_movement.get("moveable_type", "")
            
            # Timestamps
            created_at = self._parse_datetime(tradegecko_movement.get("created_at"))
            
            # Build standard movement format
            standard_movement = {
                "id": movement_id,
                "external_id": movement_id,
                "product_id": variant_id,
                "variant_id": variant_id,
                "location_id": location_id,
                "movement_type": self._map_movement_type(movement_type),
                "quantity": float(quantity),
                "unit_cost": 0.0,  # TradeGecko doesn't provide unit cost in movements
                "total_cost": 0.0,
                "currency": self.currency_code,
                "reference": {
                    "id": moveable_id,
                    "type": moveable_type,
                    "notes": ""
                },
                "timestamps": {
                    "created_at": created_at or datetime.utcnow().isoformat()
                },
                "source": "tradegecko",
                "raw_data": tradegecko_movement
            }
            
            logger.debug(f"Transformed stock movement {movement_id}")
            return standard_movement
            
        except Exception as e:
            logger.error(f"Failed to transform stock movement: {e}")
            raise TradeGeckoTransformationError(f"Stock movement transformation failed: {str(e)}")
    
    # Order Transformations
    
    def transform_purchase_order(self, tradegecko_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform TradeGecko purchase order to standard format.
        
        Args:
            tradegecko_order: Raw TradeGecko purchase order data
            
        Returns:
            Standardized purchase order data
        """
        try:
            # Extract order information
            order_id = str(tradegecko_order.get("id", ""))
            order_number = tradegecko_order.get("order_number", "")
            company_id = str(tradegecko_order.get("company_id", ""))
            
            # Order details
            status = tradegecko_order.get("status", "")
            total = self._safe_decimal(tradegecko_order.get("total", 0))
            
            # Dates
            order_date = self._parse_datetime(tradegecko_order.get("order_date"))
            due_date = self._parse_datetime(tradegecko_order.get("due_date"))
            
            # Line items
            line_items = []
            items = tradegecko_order.get("purchase_order_line_items", [])
            
            for item in items:
                line_item = {
                    "variant_id": str(item.get("variant_id", "")),
                    "quantity": float(self._safe_decimal(item.get("quantity", 0))),
                    "unit_price": float(self._safe_decimal(item.get("price", 0))),
                    "total_price": float(self._safe_decimal(item.get("line_total", 0)))
                }
                line_items.append(line_item)
            
            # Build standard order format
            standard_order = {
                "id": order_id,
                "external_id": order_id,
                "order_number": order_number,
                "supplier_id": company_id,
                "status": self._map_order_status(status),
                "order_date": order_date,
                "due_date": due_date,
                "totals": {
                    "subtotal": float(total),
                    "tax": 0.0,
                    "total": float(total),
                    "currency": self.currency_code
                },
                "line_items": line_items,
                "source": "tradegecko",
                "raw_data": tradegecko_order
            }
            
            logger.debug(f"Transformed purchase order {order_id}")
            return standard_order
            
        except Exception as e:
            logger.error(f"Failed to transform purchase order: {e}")
            raise TradeGeckoTransformationError(f"Purchase order transformation failed: {str(e)}")
    
    # Company/Supplier Transformations
    
    def transform_supplier(self, tradegecko_company: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform TradeGecko company (supplier) to standard format.
        
        Args:
            tradegecko_company: Raw TradeGecko company data
            
        Returns:
            Standardized supplier data
        """
        try:
            # Extract company information
            company_id = str(tradegecko_company.get("id", ""))
            name = tradegecko_company.get("name", "")
            
            # Contact information
            email = tradegecko_company.get("email", "")
            phone = tradegecko_company.get("phone_number", "")
            
            # Address information - TradeGecko stores addresses in separate objects
            addresses = tradegecko_company.get("addresses", [])
            primary_address = addresses[0] if addresses else {}
            
            # Status
            company_status = tradegecko_company.get("company_status", "active")
            is_active = company_status.lower() == "active"
            
            # Build standard supplier format
            standard_supplier = {
                "id": company_id,
                "external_id": company_id,
                "name": name,
                "code": company_id,
                "status": "active" if is_active else "inactive",
                "contact": {
                    "email": email,
                    "phone": phone
                },
                "address": {
                    "street": primary_address.get("address1", ""),
                    "city": primary_address.get("city", ""),
                    "state": primary_address.get("state", ""),
                    "postal_code": primary_address.get("zip_code", ""),
                    "country": primary_address.get("country", "")
                },
                "tradegecko_data": {
                    "company_type": tradegecko_company.get("company_type", ""),
                    "default_discount_rate": tradegecko_company.get("default_discount_rate", 0),
                    "default_tax_type_id": tradegecko_company.get("default_tax_type_id", "")
                },
                "source": "tradegecko",
                "raw_data": tradegecko_company
            }
            
            logger.debug(f"Transformed supplier {company_id}")
            return standard_supplier
            
        except Exception as e:
            logger.error(f"Failed to transform supplier: {e}")
            raise TradeGeckoTransformationError(f"Supplier transformation failed: {str(e)}")
    
    # Location Transformations
    
    def transform_location(self, tradegecko_location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform TradeGecko location to standard format.
        
        Args:
            tradegecko_location: Raw TradeGecko location data
            
        Returns:
            Standardized location data
        """
        try:
            # Extract location information
            location_id = str(tradegecko_location.get("id", ""))
            name = tradegecko_location.get("name", "")
            
            # Location details
            location_type = tradegecko_location.get("location_type", "")
            
            # Address information
            address = tradegecko_location.get("address", {})
            
            # Status
            location_status = tradegecko_location.get("location_status", "active")
            is_active = location_status.lower() == "active"
            
            # Build standard location format
            standard_location = {
                "id": location_id,
                "external_id": location_id,
                "name": name,
                "code": location_id,
                "type": self._map_location_type(location_type),
                "status": "active" if is_active else "inactive",
                "address": {
                    "street": address.get("address1", "") if isinstance(address, dict) else "",
                    "city": address.get("city", "") if isinstance(address, dict) else "",
                    "state": address.get("state", "") if isinstance(address, dict) else "",
                    "postal_code": address.get("zip_code", "") if isinstance(address, dict) else "",
                    "country": address.get("country", "") if isinstance(address, dict) else ""
                },
                "source": "tradegecko",
                "raw_data": tradegecko_location
            }
            
            logger.debug(f"Transformed location {location_id}")
            return standard_location
            
        except Exception as e:
            logger.error(f"Failed to transform location: {e}")
            raise TradeGeckoTransformationError(f"Location transformation failed: {str(e)}")
    
    # Helper Methods
    
    def _transform_variant_summary(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        """Transform variant to summary format for product overview."""
        return {
            "id": str(variant.get("id", "")),
            "sku": variant.get("sku", ""),
            "name": variant.get("name", ""),
            "retail_price": float(self._safe_decimal(variant.get("retail_price", 0)))
        }
    
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
            # TradeGecko uses ISO format
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.isoformat()
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.isoformat()
        except ValueError:
            logger.warning(f"Failed to parse datetime: {date_str}")
            return date_str
    
    def _map_product_type(self, tradegecko_type: str) -> str:
        """Map TradeGecko product type to standard type."""
        type_mapping = {
            "variant": "product",
            "bundle": "bundle",
            "composite": "bundle",
            "service": "service"
        }
        return type_mapping.get(tradegecko_type.lower(), "product")
    
    def _map_movement_type(self, tradegecko_type: str) -> str:
        """Map TradeGecko movement type to standard type."""
        type_mapping = {
            "positive": "inbound",
            "negative": "outbound",
            "adjustment": "adjustment",
            "transfer": "transfer",
            "sale": "outbound",
            "purchase": "inbound"
        }
        return type_mapping.get(tradegecko_type.lower(), "adjustment")
    
    def _map_order_status(self, tradegecko_status: str) -> str:
        """Map TradeGecko order status to standard status."""
        status_mapping = {
            "draft": "draft",
            "active": "pending",
            "received": "received",
            "complete": "completed",
            "void": "cancelled"
        }
        return status_mapping.get(tradegecko_status.lower(), "pending")
    
    def _map_location_type(self, tradegecko_type: str) -> str:
        """Map TradeGecko location type to standard type."""
        type_mapping = {
            "warehouse": "warehouse",
            "shop": "retail",
            "consignment": "consignment"
        }
        return type_mapping.get(tradegecko_type.lower(), "warehouse")