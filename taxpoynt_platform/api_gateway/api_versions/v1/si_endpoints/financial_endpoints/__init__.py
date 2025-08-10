"""
Financial System Integration Endpoints - API v1
===============================================
Professional organization of financial system endpoints for System Integrators.

**Financial System Categories:**
- **Banking Systems**: Open Banking, Mono, Stitch, BVN validation
- **Payment Processors**: Nigerian (Paystack, Moniepoint, OPay, PalmPay, Interswitch), 
                         African (Flutterwave), Global (Stripe)  
- **Validation Services**: BVN validation, KYC processing, Identity verification

**Architecture Benefits:**
- Clear separation of financial system types
- Independent development and maintenance
- Consistent API patterns across all financial integrations
- Scalable structure for additional financial systems
"""

from .banking_endpoints import create_banking_router
from .payment_processor_endpoints import create_payment_processor_router
from .validation_endpoints import create_validation_router

__all__ = [
    "create_banking_router",
    "create_payment_processor_router", 
    "create_validation_router"
]