"""
Access Point Provider (APP) Endpoints - API Version 1
=====================================================
Version 1 of APP role endpoints for FIRS e-invoicing compliance and taxpayer management.

**APP Role Context:**
TaxPoynt serves as an Access Point Provider (APP) for FIRS e-invoicing compliance.
APP endpoints handle direct integration with FIRS systems and taxpayer management.

**Professional Structure:**
- FIRS Integration: Direct communication with FIRS e-invoicing systems
- Taxpayer Management: Onboard and manage taxpayers for e-invoicing compliance
- Invoice Submission: Submit compliant invoices to FIRS on behalf of taxpayers
- Compliance Validation: Validate invoices against FIRS requirements
- Certificate Management: Handle FIRS certificates and authentication
- Grant Management: Track FIRS grant milestones and performance metrics
"""

from .firs_integration_endpoints import create_firs_integration_router
from .taxpayer_management_endpoints import create_taxpayer_management_router
from .invoice_submission_endpoints import create_invoice_submission_router
from .compliance_validation_endpoints import create_compliance_validation_router
from .certificate_management_endpoints import create_certificate_management_router
from .grant_management_endpoints import create_grant_management_router
from .main_router import create_app_v1_router

__all__ = [
    "create_firs_integration_router",
    "create_taxpayer_management_router",
    "create_invoice_submission_router",
    "create_compliance_validation_router",
    "create_certificate_management_router",
    "create_grant_management_router",
    "create_app_v1_router"
]