"""
System Integrator Endpoints - API Version 1
==========================================
Version 1 of System Integrator role endpoints with comprehensive business system
integration support, financial system integration, organization management,
transaction processing, and compliance validation.

**Professional Structure:**
- Organization Management: Create, manage, and onboard organizations
- Business Systems: ERP, CRM, POS, E-commerce, Accounting, Inventory integrations
- Financial Systems: Banking, Payment processors, Validation services
- Transaction Processing: Process and manage transactions from all systems
- Compliance & Reporting: Validate and report on compliance status
"""

from .organization_endpoints import create_organization_router
from .business_endpoints import (
    create_erp_router,
    create_crm_router,
    create_pos_router,
    create_ecommerce_router,
    create_accounting_router,
    create_inventory_router
)
from .financial_endpoints import (
    create_banking_router,
    create_payment_processor_router,
    create_validation_router
)
from .transaction_endpoints import create_transaction_router
from .compliance_endpoints import create_compliance_router
from .main_router import create_si_v1_router

__all__ = [
    "create_organization_router",
    "create_erp_router",
    "create_crm_router",
    "create_pos_router",
    "create_ecommerce_router",
    "create_accounting_router",
    "create_inventory_router",
    "create_banking_router",
    "create_payment_processor_router",
    "create_validation_router",
    "create_transaction_router",
    "create_compliance_router",
    "create_si_v1_router"
]