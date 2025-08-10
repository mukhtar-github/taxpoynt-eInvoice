"""
Base Inventory Connector
Abstract base class for all inventory management system integrations.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from .base_connector import BaseConnector


class InventoryMovementType(Enum):
    """Types of inventory movements."""
    STOCK_IN = "stock_in"
    STOCK_OUT = "stock_out"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RETURN = "return"
    DAMAGED = "damaged"
    EXPIRED = "expired"


class StockStatus(Enum):
    """Stock status types."""
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LOW_STOCK = "low_stock"
    RESERVED = "reserved"
    ON_ORDER = "on_order"
    DISCONTINUED = "discontinued"


class BaseInventoryConnector(BaseConnector, ABC):
    """
    Abstract base class for inventory management system connectors.
    
    This class defines the standard interface that all inventory connectors
    must implement for TaxPoynt platform integration.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize base inventory connector."""
        super().__init__(*args, **kwargs)
        self.system_type = "inventory"
    
    # Authentication Methods (inherited from BaseConnector)
    
    # Product Management Methods
    
    @abstractmethod
    async def get_products(
        self,
        modified_since: Optional[datetime] = None,
        warehouse_id: Optional[str] = None,
        category_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products from the inventory system.
        
        Args:
            modified_since: Only return products modified since this date
            warehouse_id: Filter by specific warehouse
            category_id: Filter by product category
            limit: Maximum number of products to return
            offset: Number of products to skip
            
        Returns:
            List of normalized product objects
        """
        pass
    
    @abstractmethod
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific product by ID.
        
        Args:
            product_id: Unique product identifier
            
        Returns:
            Normalized product object
        """
        pass
    
    @abstractmethod
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product in the inventory system.
        
        Args:
            product_data: Product information
            
        Returns:
            Created product object with system-generated fields
        """
        pass
    
    @abstractmethod
    async def update_product(
        self,
        product_id: str,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing product.
        
        Args:
            product_id: Unique product identifier
            product_data: Updated product information
            
        Returns:
            Updated product object
        """
        pass
    
    # Stock Level Management
    
    @abstractmethod
    async def get_stock_levels(
        self,
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve current stock levels.
        
        Args:
            product_id: Filter by specific product
            warehouse_id: Filter by specific warehouse
            location_id: Filter by specific location
            
        Returns:
            List of stock level objects
        """
        pass
    
    @abstractmethod
    async def adjust_stock(
        self,
        product_id: str,
        quantity: float,
        warehouse_id: Optional[str] = None,
        location_id: Optional[str] = None,
        reason: Optional[str] = None,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adjust stock levels for a product.
        
        Args:
            product_id: Product to adjust
            quantity: Quantity to adjust (positive or negative)
            warehouse_id: Target warehouse
            location_id: Target location within warehouse
            reason: Reason for adjustment
            reference: Reference number/document
            
        Returns:
            Stock adjustment record
        """
        pass
    
    @abstractmethod
    async def transfer_stock(
        self,
        product_id: str,
        quantity: float,
        from_location: str,
        to_location: str,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transfer stock between locations.
        
        Args:
            product_id: Product to transfer
            quantity: Quantity to transfer
            from_location: Source location ID
            to_location: Destination location ID
            reference: Transfer reference number
            
        Returns:
            Stock transfer record
        """
        pass
    
    # Inventory Movements
    
    @abstractmethod
    async def get_inventory_movements(
        self,
        product_id: Optional[str] = None,
        movement_type: Optional[InventoryMovementType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve inventory movement history.
        
        Args:
            product_id: Filter by specific product
            movement_type: Filter by movement type
            date_from: Start date for movements
            date_to: End date for movements
            limit: Maximum number of movements to return
            
        Returns:
            List of inventory movement records
        """
        pass
    
    @abstractmethod
    async def create_inventory_movement(
        self,
        movement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new inventory movement record.
        
        Args:
            movement_data: Movement information including product, quantity, type, etc.
            
        Returns:
            Created movement record
        """
        pass
    
    # Warehouse Management
    
    @abstractmethod
    async def get_warehouses(self) -> List[Dict[str, Any]]:
        """
        Retrieve all warehouses/locations.
        
        Returns:
            List of warehouse objects
        """
        pass
    
    @abstractmethod
    async def get_warehouse(self, warehouse_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific warehouse by ID.
        
        Args:
            warehouse_id: Unique warehouse identifier
            
        Returns:
            Warehouse object
        """
        pass
    
    # Purchase Order Management
    
    @abstractmethod
    async def get_purchase_orders(
        self,
        status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        modified_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve purchase orders.
        
        Args:
            status: Filter by order status
            supplier_id: Filter by supplier
            modified_since: Only return orders modified since this date
            limit: Maximum number of orders to return
            
        Returns:
            List of purchase order objects
        """
        pass
    
    @abstractmethod
    async def get_purchase_order(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific purchase order by ID.
        
        Args:
            order_id: Unique order identifier
            
        Returns:
            Purchase order object
        """
        pass
    
    @abstractmethod
    async def create_purchase_order(
        self,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new purchase order.
        
        Args:
            order_data: Purchase order information
            
        Returns:
            Created purchase order object
        """
        pass
    
    # Sales Order Management
    
    @abstractmethod
    async def get_sales_orders(
        self,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        modified_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve sales orders.
        
        Args:
            status: Filter by order status
            customer_id: Filter by customer
            modified_since: Only return orders modified since this date
            limit: Maximum number of orders to return
            
        Returns:
            List of sales order objects
        """
        pass
    
    @abstractmethod
    async def get_sales_order(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific sales order by ID.
        
        Args:
            order_id: Unique order identifier
            
        Returns:
            Sales order object
        """
        pass
    
    # Supplier Management
    
    @abstractmethod
    async def get_suppliers(
        self,
        modified_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve suppliers.
        
        Args:
            modified_since: Only return suppliers modified since this date
            limit: Maximum number of suppliers to return
            
        Returns:
            List of supplier objects
        """
        pass
    
    @abstractmethod
    async def get_supplier(self, supplier_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific supplier by ID.
        
        Args:
            supplier_id: Unique supplier identifier
            
        Returns:
            Supplier object
        """
        pass
    
    # Reporting Methods
    
    @abstractmethod
    async def get_stock_valuation(
        self,
        warehouse_id: Optional[str] = None,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get stock valuation report.
        
        Args:
            warehouse_id: Filter by specific warehouse
            as_of_date: Valuation as of specific date
            
        Returns:
            Stock valuation data
        """
        pass
    
    @abstractmethod
    async def get_low_stock_report(
        self,
        threshold: Optional[float] = None,
        warehouse_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products with low stock levels.
        
        Args:
            threshold: Stock level threshold
            warehouse_id: Filter by specific warehouse
            
        Returns:
            List of products with low stock
        """
        pass
    
    @abstractmethod
    async def get_inventory_aging_report(
        self,
        warehouse_id: Optional[str] = None,
        age_in_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get inventory aging report.
        
        Args:
            warehouse_id: Filter by specific warehouse
            age_in_days: Minimum age in days
            
        Returns:
            List of aged inventory items
        """
        pass
    
    # Integration-specific Methods
    
    async def sync_with_accounting(
        self,
        accounting_connector: 'BaseAccountingConnector',
        sync_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize inventory data with accounting system.
        
        Args:
            accounting_connector: Connected accounting system
            sync_options: Synchronization options
            
        Returns:
            Synchronization results
        """
        # Default implementation - can be overridden
        raise NotImplementedError("Accounting sync not implemented for this connector")
    
    async def sync_with_ecommerce(
        self,
        ecommerce_connector: 'BaseECommerceConnector',
        sync_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize inventory data with e-commerce system.
        
        Args:
            ecommerce_connector: Connected e-commerce system
            sync_options: Synchronization options
            
        Returns:
            Synchronization results
        """
        # Default implementation - can be overridden
        raise NotImplementedError("E-commerce sync not implemented for this connector")
    
    # Data Validation Methods
    
    def validate_product_data(self, product_data: Dict[str, Any]) -> List[str]:
        """
        Validate product data structure.
        
        Args:
            product_data: Product data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic validation
        required_fields = ['name', 'sku']
        for field in required_fields:
            if field not in product_data or not product_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate numeric fields
        numeric_fields = ['price', 'cost', 'weight', 'quantity']
        for field in numeric_fields:
            if field in product_data:
                try:
                    float(product_data[field])
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for field: {field}")
        
        return errors
    
    def validate_stock_movement_data(self, movement_data: Dict[str, Any]) -> List[str]:
        """
        Validate stock movement data structure.
        
        Args:
            movement_data: Movement data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        required_fields = ['product_id', 'quantity', 'movement_type']
        for field in required_fields:
            if field not in movement_data or movement_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate movement type
        if 'movement_type' in movement_data:
            try:
                InventoryMovementType(movement_data['movement_type'])
            except ValueError:
                valid_types = [t.value for t in InventoryMovementType]
                errors.append(f"Invalid movement type. Must be one of: {valid_types}")
        
        # Validate quantity
        if 'quantity' in movement_data:
            try:
                quantity = float(movement_data['quantity'])
                if quantity == 0:
                    errors.append("Quantity cannot be zero")
            except (ValueError, TypeError):
                errors.append("Quantity must be a valid number")
        
        return errors
    
    # Utility Methods
    
    def calculate_stock_value(
        self,
        quantity: float,
        unit_cost: float,
        valuation_method: str = "average"
    ) -> float:
        """
        Calculate stock value based on quantity and cost.
        
        Args:
            quantity: Stock quantity
            unit_cost: Cost per unit
            valuation_method: Valuation method (average, fifo, lifo)
            
        Returns:
            Total stock value
        """
        return quantity * unit_cost
    
    def determine_stock_status(
        self,
        current_quantity: float,
        reorder_level: Optional[float] = None,
        min_level: Optional[float] = None
    ) -> StockStatus:
        """
        Determine stock status based on current quantity and thresholds.
        
        Args:
            current_quantity: Current stock quantity
            reorder_level: Reorder point threshold
            min_level: Minimum stock level
            
        Returns:
            Stock status enum
        """
        if current_quantity <= 0:
            return StockStatus.OUT_OF_STOCK
        elif min_level and current_quantity <= min_level:
            return StockStatus.LOW_STOCK
        elif reorder_level and current_quantity <= reorder_level:
            return StockStatus.LOW_STOCK
        else:
            return StockStatus.IN_STOCK
    
    # FIRS E-Invoicing Integration
    
    async def generate_stock_movement_invoice(
        self,
        movement_id: str,
        invoice_type: str = "stock_movement"
    ) -> Dict[str, Any]:
        """
        Generate invoice data for stock movements (for FIRS compliance).
        
        Args:
            movement_id: Stock movement ID
            invoice_type: Type of invoice to generate
            
        Returns:
            Invoice data in standardized format
        """
        # Default implementation - should be overridden by specific connectors
        raise NotImplementedError("Invoice generation not implemented for this connector")
    
    async def get_inventory_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        warehouse_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get inventory movements for a specific period (for tax reporting).
        
        Args:
            start_date: Period start date
            end_date: Period end date
            warehouse_id: Filter by specific warehouse
            
        Returns:
            Period inventory data
        """
        movements = await self.get_inventory_movements(
            date_from=start_date,
            date_to=end_date
        )
        
        # Group by product and calculate totals
        period_data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "warehouse_id": warehouse_id,
            "movements": movements,
            "summary": self._calculate_period_summary(movements)
        }
        
        return period_data
    
    def _calculate_period_summary(self, movements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for a period's movements."""
        total_in = sum(m.get('quantity', 0) for m in movements if m.get('quantity', 0) > 0)
        total_out = sum(abs(m.get('quantity', 0)) for m in movements if m.get('quantity', 0) < 0)
        
        return {
            "total_movements": len(movements),
            "total_stock_in": total_in,
            "total_stock_out": total_out,
            "net_movement": total_in - total_out
        }