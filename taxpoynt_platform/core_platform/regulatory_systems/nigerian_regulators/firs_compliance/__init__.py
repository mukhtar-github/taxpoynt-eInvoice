"""
FIRS (Federal Inland Revenue Service) Compliance Framework
========================================================
Comprehensive Nigerian e-invoicing compliance system for FIRS regulatory requirements.

FIRS E-Invoicing Mandate Components:
- Nigerian e-invoicing format validation and standardization
- TIN (Tax Identification Number) validation and verification
- VAT compliance checking and calculation validation
- FIRS-specific business rules and regulatory requirements
- Nigerian tax code compliance and verification
- E-invoice submission format and timing requirements

Core Components:
- firs_validator.py: Main FIRS compliance validation engine
- models.py: FIRS-specific data models and validation schemas
- tax_calculations.py: Nigerian tax calculation and validation engine
- business_rules.py: FIRS business rules and regulatory compliance
- submission_handler.py: FIRS e-invoice submission and acknowledgment processing
"""

from .firs_validator import FIRSValidator
from .models import (
    FIRSValidationResult, NigerianTaxInfo, VATCalculation,
    FIRSComplianceStatus, TINValidationResult, EInvoiceSubmission
)

__all__ = [
    'FIRSValidator',
    'FIRSValidationResult',
    'NigerianTaxInfo',
    'VATCalculation',
    'FIRSComplianceStatus',
    'TINValidationResult',
    'EInvoiceSubmission'
]