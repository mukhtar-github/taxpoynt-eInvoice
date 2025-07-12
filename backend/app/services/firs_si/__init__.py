"""
FIRS System Integrator (SI) Services Package

This package contains services specifically designed for System Integrator functionality
as defined by FIRS e-Invoicing requirements:

- ERP system integration and data extraction
- Digital certificate management and lifecycle
- IRN (Invoice Reference Number) generation and QR code creation
- Invoice schema validation and conformity checks
- Authentication services for invoice origin verification

SI Role Responsibilities:
- Integrate with business systems (ERP, CRM, POS)
- Generate unique IRNs for invoices
- Manage digital certificates for invoice signing
- Validate invoice data against FIRS schemas
- Authenticate invoice origins and data integrity
"""

# SI-specific service imports
from .irn_generation_service import generate_irn
from .digital_certificate_service import CertificateService
from .erp_integration_service import fetch_odoo_invoices
from .schema_compliance_service import validate_invoice

__all__ = [
    "generate_irn",
    "CertificateService", 
    "fetch_odoo_invoices",
    "validate_invoice",
]