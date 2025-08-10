"""
Invoice Automation Framework
============================

Automated invoice generation pipeline for Open Banking transactions.
Transforms banking transaction data into FIRS-compliant e-invoices.

Key Components:
- auto_invoice_generator.py: Main invoice generation engine
- customer_matcher.py: Match transactions to customers
- tax_calculator.py: Nigerian tax calculations (7.5% VAT)
- firs_submitter.py: Automatic FIRS submission
- invoice_templates.py: Nigerian invoice templates

Features:
- Transaction pattern recognition
- Automated customer identification
- FIRS-compliant invoice generation
- Real-time tax calculations
- Automatic submission to FIRS
- Nigerian business rule compliance

Integration Points:
- Mono transaction webhooks
- TaxPoynt FIRS submission system
- Customer management system
- Business accounting systems

Architecture consistent with existing TaxPoynt patterns.
"""

from enum import Enum
from decimal import Decimal
from typing import Dict, Any


class InvoiceGenerationTrigger(str, Enum):
    """Triggers for automated invoice generation"""
    TRANSACTION_WEBHOOK = "transaction_webhook"
    SCHEDULED_BATCH = "scheduled_batch" 
    MANUAL_REQUEST = "manual_request"
    PATTERN_MATCH = "pattern_match"


class InvoiceStatus(str, Enum):
    """Invoice generation and submission status"""
    PENDING = "pending"
    GENERATED = "generated"
    VALIDATED = "validated"
    SUBMITTED_TO_FIRS = "submitted_to_firs"
    FIRS_ACCEPTED = "firs_accepted"
    FIRS_REJECTED = "firs_rejected"
    FAILED = "failed"


class CustomerMatchingStrategy(str, Enum):
    """Strategies for matching transactions to customers"""
    EXACT_MATCH = "exact_match"        # Exact account/name match
    FUZZY_MATCH = "fuzzy_match"        # Similar name matching
    PATTERN_MATCH = "pattern_match"    # Transaction pattern matching
    BUSINESS_RULES = "business_rules"  # Custom business logic
    MANUAL_REVIEW = "manual_review"    # Requires human intervention


# Nigerian business constants
NIGERIAN_VAT_RATE = Decimal("7.5")  # Current VAT rate in Nigeria
NIGERIAN_WITHHOLDING_TAX_RATES = {
    "professional_services": Decimal("5.0"),
    "technical_services": Decimal("5.0"),
    "management_services": Decimal("5.0"),
    "consultancy": Decimal("5.0"),
    "construction": Decimal("5.0"),
    "manufacturing": Decimal("1.0"),
    "import_services": Decimal("5.0")
}

# Minimum thresholds for invoice generation
INVOICE_GENERATION_THRESHOLDS = {
    "minimum_amount_ngn": Decimal("1000"),      # NGN 1,000 minimum
    "minimum_amount_usd": Decimal("2.50"),      # USD $2.50 minimum
    "vat_threshold_ngn": Decimal("25000000"),   # NGN 25M VAT registration threshold
    "withholding_threshold_ngn": Decimal("10000") # NGN 10K withholding tax threshold
}

# Business transaction indicators
BUSINESS_TRANSACTION_INDICATORS = {
    "keywords": [
        "payment", "invoice", "service", "consultation", "project",
        "contract", "deposit", "installment", "fee", "subscription",
        "salary", "commission", "bonus", "allowance", "expense",
        "reimbursement", "advance", "loan", "interest"
    ],
    "round_amounts": [100, 500, 1000, 5000, 10000, 50000, 100000],
    "recurring_patterns": ["monthly", "weekly", "quarterly", "annual"],
    "business_hours": {
        "start_hour": 8,   # 8 AM
        "end_hour": 18     # 6 PM
    }
}

# Import core components
from .auto_invoice_generator import (
    AutoInvoiceGenerator,
    InvoiceGenerationResult,
    InvoiceGenerationStrategy,
    GenerationRule
)

from .customer_matcher import (
    CustomerMatcher,
    CustomerMatch,
    MatchingStrategy,
    MatchingRule
)

from .vat_calculator import (
    VATCalculator,
    VATCalculationResult,
    VATRule
)

from .firs_formatter import (
    FIRSFormatter,
    FormattingResult,
    FIRSInvoice
)

from .banking_firs_orchestrator import (
    BankingFIRSOrchestrator,
    OrchestrationRequest,
    OrchestrationResult,
    OrchestrationStatus
)

from .invoice_templates import (
    InvoiceTemplates,
    TemplateType,
    TemplateConfig,
    BrandingInfo,
    OutputFormat
)

# Export key components
__all__ = [
    # Enums and constants
    "InvoiceGenerationTrigger",
    "InvoiceStatus", 
    "CustomerMatchingStrategy",
    "NIGERIAN_VAT_RATE",
    "NIGERIAN_WITHHOLDING_TAX_RATES",
    "INVOICE_GENERATION_THRESHOLDS",
    "BUSINESS_TRANSACTION_INDICATORS",
    
    # Core components
    "AutoInvoiceGenerator",
    "InvoiceGenerationResult",
    "InvoiceGenerationStrategy",
    "GenerationRule",
    "CustomerMatcher",
    "CustomerMatch",
    "MatchingStrategy",
    "MatchingRule",
    "VATCalculator",
    "VATCalculationResult",
    "VATRule",
    "FIRSFormatter",
    "FormattingResult",
    "FIRSInvoice",
    "BankingFIRSOrchestrator",
    "OrchestrationRequest",
    "OrchestrationResult",
    "OrchestrationStatus",
    "InvoiceTemplates",
    "TemplateType",
    "TemplateConfig",
    "BrandingInfo",
    "OutputFormat"
]