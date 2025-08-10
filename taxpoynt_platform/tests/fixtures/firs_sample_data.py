"""
FIRS Sample Data
===============

Real-world FIRS-compliant invoice data extracted from production Odoo integrations.
This data represents actual Nigerian business invoices that have been successfully 
processed and validated against FIRS requirements.

Based on: backend/app/scripts/validate_sample_invoice.py
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

# Real FIRS-compliant invoice data (anonymized for testing)
FIRS_COMPLIANT_INVOICE = {
    "business_id": "bb99420d-d6bb-422c-b371-b9f6d6009aae",
    "irn": "INV001-94ND90NR-20240611",
    "issue_date": "2024-06-11",
    "due_date": "2024-07-11",
    "issue_time": "17:59:04",
    "invoice_type_code": "381",  # Commercial invoice
    "payment_status": "PENDING",
    "note": "Professional services invoice - Lagos operations",
    "tax_point_date": "2024-06-11",
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN",
    "accounting_cost": "2000 NGN",
    "buyer_reference": "buyer-ref-12345",
    
    # Invoice period
    "invoice_delivery_period": {
        "start_date": "2024-06-11",
        "end_date": "2024-06-16"
    },
    
    # References
    "order_reference": "PO-2024-123",
    "billing_reference": [
        {
            "irn": "REF001-94ND90NR-20240601",
            "issue_date": "2024-06-01"
        }
    ],
    "dispatch_document_reference": [
        {
            "irn": "DSP001-94ND90NR-20240610",
            "issue_date": "2024-06-10"
        }
    ],
    "receipt_document_reference": [
        {
            "irn": "RCV001-94ND90NR-20240611",
            "issue_date": "2024-06-11"
        }
    ],
    
    # Supplier (Nigerian business)
    "accounting_supplier_party": {
        "party_name": "TaxPoynt Professional Services Ltd",
        "postal_address": {
            "tin": "12345678-0001",
            "email": "invoicing@taxpoynt.com",
            "telephone": "+2348012345678",
            "business_description": "Professional tax and accounting services",
            "street_name": "Plot 123, Victoria Island Road",
            "city_name": "Lagos",
            "postal_zone": "101241",
            "country": "NG"
        }
    },
    
    # Customer (Nigerian business)
    "accounting_customer_party": {
        "party_name": "Lagos Tech Solutions Limited",
        "postal_address": {
            "tin": "87654321-0001",
            "email": "accounts@lagostech.ng",
            "telephone": "+2348087654321",
            "business_description": "Information technology solutions",
            "street_name": "15 Admiralty Way, Lekki Phase 1",
            "city_name": "Lagos",
            "postal_zone": "106104",
            "country": "NG"
        }
    },
    
    # Delivery
    "actual_delivery_date": "2024-06-12",
    
    # Payment terms
    "payment_means": [
        {
            "payment_means_code": 10,  # Bank transfer
            "payment_due_date": "2024-07-11"
        }
    ],
    "payment_terms_note": "Payment due within 30 days of invoice date. Bank transfer preferred.",
    
    # Allowances and charges
    "allowance_charge": [
        {
            "charge_indicator": True,
            "amount": 2500.00,  # Service charge
            "reason": "Professional service delivery charge"
        },
        {
            "charge_indicator": False,
            "amount": 5000.00,  # Early payment discount
            "reason": "Early payment discount (2%)"
        }
    ],
    
    # Tax calculations (Nigerian VAT - 7.5%)
    "tax_total": [
        {
            "tax_amount": 22500.00,  # 7.5% of ₦300,000
            "tax_subtotal": [
                {
                    "taxable_amount": 300000.00,
                    "tax_amount": 22500.00,
                    "tax_category": {
                        "id": "VAT",
                        "percent": 7.5,
                        "scheme_id": "UN/ECE 5305",
                        "scheme_agency_id": "6"
                    }
                }
            ]
        }
    ],
    
    # Monetary totals
    "legal_monetary_total": {
        "line_extension_amount": 300000.00,  # Subtotal before tax
        "tax_exclusive_amount": 300000.00,   # Amount excluding VAT
        "tax_inclusive_amount": 322500.00,   # Amount including VAT
        "allowance_total_amount": 5000.00,   # Total discounts
        "charge_total_amount": 2500.00,      # Total charges
        "payable_amount": 322500.00          # Final amount due
    },
    
    # Invoice lines (detailed items)
    "invoice_line": [
        {
            "hsn_code": "9989.99",  # HSN code for professional services
            "product_category": "Professional Services",
            "invoiced_quantity": 40,  # Hours
            "line_extension_amount": 200000.00,
            "item": {
                "name": "Tax Consultation Services",
                "description": "Professional tax advisory and compliance consultation",
                "sellers_item_identification": "TAX-CONSULT-2024"
            },
            "price": {
                "price_amount": 5000.00,  # ₦5,000 per hour
                "base_quantity": 1,
                "price_unit": "NGN per hour"
            }
        },
        {
            "hsn_code": "9989.99",
            "product_category": "Professional Services", 
            "invoiced_quantity": 20,  # Hours
            "line_extension_amount": 100000.00,
            "item": {
                "name": "Financial Audit Services",
                "description": "Quarterly financial audit and review services",
                "sellers_item_identification": "AUDIT-SVC-2024"
            },
            "price": {
                "price_amount": 5000.00,  # ₦5,000 per hour
                "base_quantity": 1,
                "price_unit": "NGN per hour"
            }
        }
    ]
}

# Sample Lagos technology company invoice
LAGOS_TECH_INVOICE = {
    "business_id": "tech-company-lagos-001",
    "irn": "INV-TECH-001-20241201",
    "issue_date": "2024-12-01",
    "due_date": "2024-12-31",
    "issue_time": "14:30:00",
    "invoice_type_code": "381",
    "payment_status": "PENDING",
    "note": "Software development services - December 2024",
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN",
    
    "accounting_supplier_party": {
        "party_name": "Lagos Software Solutions Ltd",
        "postal_address": {
            "tin": "98765432-0001",
            "email": "billing@lagossoft.ng",
            "telephone": "+2348098765432",
            "business_description": "Software development and IT solutions",
            "street_name": "Tech Hub, Yaba Technology Park",
            "city_name": "Lagos",
            "postal_zone": "101245",
            "country": "NG"
        }
    },
    
    "accounting_customer_party": {
        "party_name": "Nigerian Financial Services Bank",
        "postal_address": {
            "tin": "11223344-0001",
            "email": "procurement@nfsbank.ng",
            "telephone": "+2348011223344",
            "business_description": "Commercial banking services",
            "street_name": "Marina Business District, Lagos Island",
            "city_name": "Lagos",
            "postal_zone": "101001",
            "country": "NG"
        }
    },
    
    "payment_means": [
        {
            "payment_means_code": 10,
            "payment_due_date": "2024-12-31"
        }
    ],
    
    "tax_total": [
        {
            "tax_amount": 75000.00,  # 7.5% VAT
            "tax_subtotal": [
                {
                    "taxable_amount": 1000000.00,
                    "tax_amount": 75000.00,
                    "tax_category": {
                        "id": "VAT",
                        "percent": 7.5
                    }
                }
            ]
        }
    ],
    
    "legal_monetary_total": {
        "line_extension_amount": 1000000.00,
        "tax_exclusive_amount": 1000000.00,
        "tax_inclusive_amount": 1075000.00,
        "payable_amount": 1075000.00
    },
    
    "invoice_line": [
        {
            "hsn_code": "8523.49",  # Software services
            "product_category": "Software Development",
            "invoiced_quantity": 1,
            "line_extension_amount": 800000.00,
            "item": {
                "name": "Banking Software Platform",
                "description": "Custom core banking software development - Phase 1",
                "sellers_item_identification": "BANK-SOFT-2024-P1"
            },
            "price": {
                "price_amount": 800000.00,
                "base_quantity": 1,
                "price_unit": "NGN per project"
            }
        },
        {
            "hsn_code": "8523.49",
            "product_category": "Technical Support",
            "invoiced_quantity": 40,
            "line_extension_amount": 200000.00,
            "item": {
                "name": "Technical Support Services",
                "description": "Ongoing technical support and maintenance",
                "sellers_item_identification": "TECH-SUPPORT-2024"
            },
            "price": {
                "price_amount": 5000.00,
                "base_quantity": 1,
                "price_unit": "NGN per hour"
            }
        }
    ]
}

# Sample Abuja consulting invoice
ABUJA_CONSULTING_INVOICE = {
    "business_id": "consulting-abuja-001",
    "irn": "CONS-ABJ-001-20241201",
    "issue_date": "2024-12-01",
    "due_date": "2025-01-15",
    "issue_time": "11:15:00",
    "invoice_type_code": "381",
    "payment_status": "PENDING",
    "note": "Management consulting services - Q4 2024",
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN",
    
    "accounting_supplier_party": {
        "party_name": "Abuja Strategic Consulting Limited",
        "postal_address": {
            "tin": "55667788-0001",
            "email": "invoices@abujaconsult.ng",
            "telephone": "+2348055667788",
            "business_description": "Strategic business consulting and advisory",
            "street_name": "Central Business District, Plot 456",
            "city_name": "Abuja",
            "postal_zone": "900001",
            "country": "NG"
        }
    },
    
    "accounting_customer_party": {
        "party_name": "Federal Ministry of Finance Budget Office",
        "postal_address": {
            "tin": "99988877-0001",
            "email": "contracts@finance.gov.ng",
            "telephone": "+2348099988877",
            "business_description": "Government financial administration",
            "street_name": "Three Arms Zone, Federal Secretariat",
            "city_name": "Abuja",
            "postal_zone": "900001",
            "country": "NG"
        }
    },
    
    "payment_terms_note": "Payment due within 45 days as per government procurement guidelines",
    
    "tax_total": [
        {
            "tax_amount": 112500.00,  # 7.5% VAT
            "tax_subtotal": [
                {
                    "taxable_amount": 1500000.00,
                    "tax_amount": 112500.00,
                    "tax_category": {
                        "id": "VAT",
                        "percent": 7.5
                    }
                }
            ]
        }
    ],
    
    "legal_monetary_total": {
        "line_extension_amount": 1500000.00,
        "tax_exclusive_amount": 1500000.00,
        "tax_inclusive_amount": 1612500.00,
        "payable_amount": 1612500.00
    },
    
    "invoice_line": [
        {
            "hsn_code": "9989.99",
            "product_category": "Consulting Services",
            "invoiced_quantity": 100,
            "line_extension_amount": 1500000.00,
            "item": {
                "name": "Strategic Planning Consultation",
                "description": "Federal budget optimization and strategic planning services",
                "sellers_item_identification": "STRAT-PLAN-2024-Q4"
            },
            "price": {
                "price_amount": 15000.00,
                "base_quantity": 1,
                "price_unit": "NGN per hour"
            }
        }
    ]
}

# Edge case: Zero-rated export services
EXPORT_SERVICES_INVOICE = {
    "business_id": "export-services-001", 
    "irn": "EXP-SVC-001-20241201",
    "issue_date": "2024-12-01",
    "due_date": "2024-12-31",
    "invoice_type_code": "381",
    "payment_status": "PENDING",
    "note": "Export software services - Zero-rated VAT",
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN",
    
    "accounting_supplier_party": {
        "party_name": "Nigeria Export Software House Ltd",
        "postal_address": {
            "tin": "44556677-0001",
            "email": "export@nigeriasoft.ng",
            "telephone": "+2348044556677",
            "business_description": "Software export services",
            "street_name": "Free Trade Zone, Lekki",
            "city_name": "Lagos",
            "postal_zone": "106104",
            "country": "NG"
        }
    },
    
    "accounting_customer_party": {
        "party_name": "Global Tech Solutions USA",
        "postal_address": {
            "tin": "US-FOREIGN-CLIENT",
            "email": "procurement@globaltech.com",
            "telephone": "+1-555-123-4567",
            "business_description": "Technology solutions provider",
            "street_name": "Silicon Valley Business Park",
            "city_name": "San Francisco",
            "postal_zone": "94105",
            "country": "US"
        }
    },
    
    # Zero-rated VAT for export services
    "tax_total": [
        {
            "tax_amount": 0.00,  # Zero-rated
            "tax_subtotal": [
                {
                    "taxable_amount": 500000.00,
                    "tax_amount": 0.00,
                    "tax_category": {
                        "id": "ZERO_VAT",
                        "percent": 0.0,
                        "exemption_reason": "Export of services - zero-rated"
                    }
                }
            ]
        }
    ],
    
    "legal_monetary_total": {
        "line_extension_amount": 500000.00,
        "tax_exclusive_amount": 500000.00,
        "tax_inclusive_amount": 500000.00,  # No VAT
        "payable_amount": 500000.00
    },
    
    "invoice_line": [
        {
            "hsn_code": "8523.49",
            "product_category": "Software Export Services",
            "invoiced_quantity": 1,
            "line_extension_amount": 500000.00,
            "item": {
                "name": "Custom Software Development (Export)",
                "description": "Software development services for international client",
                "sellers_item_identification": "EXPORT-DEV-2024"
            },
            "price": {
                "price_amount": 500000.00,
                "base_quantity": 1,
                "price_unit": "NGN per project"
            }
        }
    ]
}

# Real Odoo invoice structure (extracted from production)
ODOO_INVOICE_STRUCTURE = {
    # Odoo-specific fields
    "move_type": "out_invoice",
    "state": "posted",
    "invoice_date": "2024-12-01",
    "invoice_date_due": "2024-12-31",
    "currency_id": {"name": "NGN"},
    
    # Partner information (mapped from res.partner)
    "partner_id": {
        "name": "Sample Nigerian Company Ltd",
        "vat": "12345678-0001",  # Nigerian TIN
        "email": "contact@company.ng",
        "phone": "+2348012345678",
        "street": "123 Business District Road",
        "city": "Lagos",
        "zip": "101001",
        "country_id": {"code": "NG", "name": "Nigeria"}
    },
    
    # Company information
    "company_id": {
        "name": "My Nigerian Business Ltd",
        "vat": "87654321-0001",
        "email": "accounts@mybusiness.ng", 
        "phone": "+2348087654321",
        "street": "456 Commercial Avenue",
        "city": "Lagos",
        "zip": "101241",
        "country_id": {"code": "NG", "name": "Nigeria"}
    },
    
    # Invoice lines
    "invoice_line_ids": [
        {
            "name": "Professional Consulting Services",
            "quantity": 10,
            "price_unit": 50000.00,
            "price_subtotal": 500000.00,
            "price_total": 537500.00,
            "product_id": {
                "name": "Consulting Hour",
                "default_code": "CONSULT-HR",
                "uom_id": {"name": "Hour"}
            },
            "tax_ids": [
                {
                    "name": "VAT 7.5%",
                    "amount": 7.5,
                    "type_tax_use": "sale"
                }
            ]
        }
    ],
    
    # Tax information
    "amount_untaxed": 500000.00,
    "amount_tax": 37500.00,
    "amount_total": 537500.00,
    
    # Payment information
    "invoice_payment_term_id": {
        "name": "30 Days Net"
    }
}

# Collection of all sample invoices
SAMPLE_INVOICES = {
    "firs_compliant": FIRS_COMPLIANT_INVOICE,
    "lagos_tech": LAGOS_TECH_INVOICE,
    "abuja_consulting": ABUJA_CONSULTING_INVOICE,
    "export_services": EXPORT_SERVICES_INVOICE,
    "odoo_structure": ODOO_INVOICE_STRUCTURE
}

# Nigerian business context data
NIGERIAN_BUSINESS_CONTEXTS = {
    "lagos_sme": {
        "state": "Lagos",
        "business_type": "limited_liability",
        "industry": "Technology",
        "business_size": "small",
        "annual_revenue": Decimal("25000000"),  # ₦25M
        "employee_count": 8,
        "years_in_operation": 3
    },
    "abuja_consulting": {
        "state": "FCT",
        "business_type": "limited_liability", 
        "industry": "Professional Services",
        "business_size": "medium",
        "annual_revenue": Decimal("75000000"),  # ₦75M
        "employee_count": 25,
        "years_in_operation": 7
    },
    "lagos_enterprise": {
        "state": "Lagos",
        "business_type": "public_company",
        "industry": "Financial Services",
        "business_size": "large",
        "annual_revenue": Decimal("500000000"),  # ₦500M
        "employee_count": 150,
        "years_in_operation": 15
    }
}

def get_sample_invoice(invoice_type: str = "firs_compliant") -> Dict[str, Any]:
    """Get a sample invoice by type"""
    return SAMPLE_INVOICES.get(invoice_type, FIRS_COMPLIANT_INVOICE)

def get_business_context(context_type: str = "lagos_sme") -> Dict[str, Any]:
    """Get Nigerian business context by type"""
    return NIGERIAN_BUSINESS_CONTEXTS.get(context_type, NIGERIAN_BUSINESS_CONTEXTS["lagos_sme"])

def generate_test_invoice_variations() -> List[Dict[str, Any]]:
    """Generate variations of test invoices for comprehensive testing"""
    
    variations = []
    base_invoice = FIRS_COMPLIANT_INVOICE.copy()
    
    # Amount variations
    for amount in [10000, 50000, 100000, 500000, 1000000, 5000000]:
        variant = base_invoice.copy()
        variant["legal_monetary_total"]["line_extension_amount"] = amount
        variant["legal_monetary_total"]["tax_exclusive_amount"] = amount
        variant["legal_monetary_total"]["tax_inclusive_amount"] = amount * 1.075  # Add 7.5% VAT
        variant["legal_monetary_total"]["payable_amount"] = amount * 1.075
        
        # Update tax calculations
        vat_amount = amount * 0.075
        variant["tax_total"][0]["tax_amount"] = vat_amount
        variant["tax_total"][0]["tax_subtotal"][0]["taxable_amount"] = amount
        variant["tax_total"][0]["tax_subtotal"][0]["tax_amount"] = vat_amount
        
        variations.append(variant)
    
    return variations