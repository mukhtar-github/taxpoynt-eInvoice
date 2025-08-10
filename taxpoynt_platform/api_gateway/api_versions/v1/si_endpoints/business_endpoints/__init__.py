"""
Business System Integration Endpoints
====================================
Organized endpoints for different types of business system integrations.

This module provides specialized endpoints for each category of business systems:
- ERP Systems: Enterprise Resource Planning (SAP, Oracle, Dynamics, NetSuite, Odoo)
- CRM Systems: Customer Relationship Management (Salesforce, HubSpot, etc.)
- POS Systems: Point of Sale (Square, Clover, Moniepoint, OPay, etc.)
- E-commerce: Online platforms (Shopify, WooCommerce, Magento, Jumia, etc.)
- Accounting: Financial software (QuickBooks, Xero, Wave, etc.)
- Inventory: Stock management (CIN7, Fishbowl, TradeGecko, etc.)
"""

from .erp_endpoints import create_erp_router
from .crm_endpoints import create_crm_router
from .pos_endpoints import create_pos_router
from .ecommerce_endpoints import create_ecommerce_router
from .accounting_endpoints import create_accounting_router
from .inventory_endpoints import create_inventory_router

__all__ = [
    "create_erp_router",
    "create_crm_router", 
    "create_pos_router",
    "create_ecommerce_router",
    "create_accounting_router",
    "create_inventory_router"
]