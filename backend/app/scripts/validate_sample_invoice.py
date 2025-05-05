#!/usr/bin/env python
"""
Script to validate a sample invoice against FIRS validation rules.
This script can be used for testing the validation service without running the full API.
"""
import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.schemas.invoice_validation import (
    InvoiceValidationRequest as Invoice,
    InvoiceValidationResponse,
    ValidationError as ValidationIssue,
    PaymentTerms,
    AllowanceCharge,
    LegalMonetaryTotal,
    TaxTotal,
    TaxSubtotal,
    TaxCategory,
    InvoiceLine,
    Address,
    Party,
    PartyIdentification,
    PartyLegalEntity,
    CurrencyCode,
    InvoiceType,
    UnitCode
)
from app.services.invoice_validation_service import validate_invoice


# Sample valid invoice data with complete fields
valid_invoice_data = {
    "business_id": "bb99420d-d6bb-422c-b371-b9f6d6009aae",
    "irn": "INV001-94ND90NR-20240611",
    "issue_date": "2024-06-11",
    "due_date": "2024-07-11",
    "issue_time": "17:59:04",
    "invoice_type_code": "381",
    "payment_status": "PENDING",
    "note": "This is a commercial invoice",
    "tax_point_date": "2024-06-11",
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN",
    "accounting_cost": "2000 NGN",
    "buyer_reference": "buyer-ref-12345",
    "invoice_delivery_period": {
        "start_date": "2024-06-11",
        "end_date": "2024-06-16"
    },
    "order_reference": "ORD-2024-123",
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
    "originator_document_reference": [
        {
            "irn": "ORG001-94ND90NR-20240605",
            "issue_date": "2024-06-05"
        }
    ],
    "contract_document_reference": [
        {
            "irn": "CNT001-94ND90NR-20240501",
            "issue_date": "2024-05-01"
        }
    ],
    "additional_document_reference": [
        {
            "irn": "ADD001-94ND90NR-20240610",
            "issue_date": "2024-06-10"
        }
    ],
    "accounting_supplier_party": {
        "party_name": "ABC Company Ltd",
        "postal_address": {
            "tin": "12345678-0001",
            "email": "business@email.com",
            "telephone": "+23480254099000",
            "business_description": "Sales of IT equipment",
            "street_name": "123 Lagos Street, Abuja",
            "city_name": "Abuja",
            "postal_zone": "900001",
            "country": "NG"
        }
    },
    "accounting_customer_party": {
        "party_name": "XYZ Corporation",
        "postal_address": {
            "tin": "87654321-0001",
            "email": "buyer@email.com",
            "telephone": "+23480254099001",
            "business_description": "IT Consulting",
            "street_name": "456 Abuja Road, Lagos",
            "city_name": "Lagos",
            "postal_zone": "100001",
            "country": "NG"
        }
    },
    "actual_delivery_date": "2024-06-12",
    "payment_means": [
        {
            "payment_means_code": 10,
            "payment_due_date": "2024-07-11"
        }
    ],
    "payment_terms_note": "Payment due within 30 days of invoice issue.",
    "allowance_charge": [
        {
            "charge_indicator": True,
            "amount": 500.00
        },
        {
            "charge_indicator": False,
            "amount": 1000.00
        }
    ],
    "tax_total": [
        {
            "tax_amount": 3000.00,
            "tax_subtotal": [
                {
                    "taxable_amount": 40000.00,
                    "tax_amount": 3000.00,
                    "tax_category": {
                        "id": "VAT",
                        "percent": 7.5
                    }
                }
            ]
        }
    ],
    "legal_monetary_total": {
        "line_extension_amount": 40000.00,
        "tax_exclusive_amount": 40000.00,
        "tax_inclusive_amount": 43000.00,
        "payable_amount": 43000.00
    },
    "invoice_line": [
        {
            "hsn_code": "8471.30",
            "product_category": "Electronics",
            "invoiced_quantity": 10,
            "line_extension_amount": 40000.00,
            "item": {
                "name": "Laptop Computers",
                "description": "15-inch Business Laptops",
                "sellers_item_identification": "LP-2024-001"
            },
            "price": {
                "price_amount": 4000.00,
                "base_quantity": 1,
                "price_unit": "NGN per 1"
            }
        }
    ]
}

# Sample invalid invoice data with intentional errors
invalid_invoice_data = {
    "business_id": "bb99420d-d6bb-422c-b371-b9f6d6009aae",
    "irn": "INVALID-IRN",  # Invalid IRN format
    "issue_date": "06/11/2024",  # Invalid date format
    "due_date": "2024-07-11",
    "issue_time": "17:59:04",
    "invoice_type_code": "381",
    "payment_status": "PENDING",
    "note": "This is a commercial invoice with errors",
    "tax_point_date": "invalid-date",  # Invalid date format
    "document_currency_code": "NGN",
    "tax_currency_code": "USD",  # Doesn't match document currency
    "accounting_cost": "2000 NGN",
    "buyer_reference": "buyer-ref-12345",
    "invoice_delivery_period": {
        "start_date": "2024-06-20",  # Later than end date
        "end_date": "2024-06-15"
    },
    "order_reference": "ORD-2024-123",
    "billing_reference": [
        {
            "irn": "INVALID-REFERENCE",  # Invalid IRN format
            "issue_date": "2024-06-01"
        }
    ],
    "dispatch_document_reference": [
        {
            "irn": "DSP001-94ND90NR-20240610",
            "issue_date": "invalid-date"  # Invalid date format
        }
    ],
    "accounting_supplier_party": {
        "party_name": "ABC Company Ltd",
        "postal_address": {
            "tin": "123456",  # Invalid TIN format
            "email": "business@email.com",
            "telephone": "+23480254099000",
            "business_description": "Sales of IT equipment",
            "street_name": "123 Lagos Street, Abuja",
            "city_name": "Abuja",
            "postal_zone": "900001",
            "country": "NG"
        }
    },
    "accounting_customer_party": {
        "party_name": "XYZ Corporation",
        "postal_address": {
            "tin": "87654321-0001",
            "email": "buyer@email.com",
            "telephone": "+23480254099001",
            "business_description": "IT Consulting",
            "street_name": "456 Abuja Road, Lagos",
            "city_name": "Lagos",
            "postal_zone": "100001",
            "country": "NG"
        }
    },
    "actual_delivery_date": "2024-13-12",  # Invalid date
    "payment_means": [
        {
            "payment_means_code": 999,  # Invalid payment code
            "payment_due_date": "invalid-date"  # Invalid date format
        }
    ],
    "payment_terms_note": "Payment due within 30 days of invoice issue.",
    "allowance_charge": [
        {
            "charge_indicator": True,
            "amount": 500.00
        }
    ],
    "tax_total": [
        {
            "tax_amount": 5000.00,  # Doesn't match sum of subtotals
            "tax_subtotal": [
                {
                    "taxable_amount": 40000.00,
                    "tax_amount": 3000.00,  # Doesn't match percent calculation
                    "tax_category": {
                        "id": "VAT",
                        "percent": 10.0
                    }
                }
            ]
        }
    ],
    "legal_monetary_total": {
        "line_extension_amount": 30000.00,  # Doesn't match sum of lines
        "tax_exclusive_amount": 40000.00,
        "tax_inclusive_amount": 39000.00,  # Less than tax_exclusive
        "payable_amount": 39000.00
    },
    "invoice_line": [
        {
            "hsn_code": "8471.30",
            "product_category": "Electronics",
            "invoiced_quantity": 10,
            "line_extension_amount": 40000.00,
            "item": {
                "name": "Laptop Computers",
                "description": "15-inch Business Laptops",
                "sellers_item_identification": "LP-2024-001"
            },
            "price": {
                "price_amount": 4000.00,
                "base_quantity": 1,
                "price_unit": "NGN per 1"
            }
        }
    ]
}


def validate_and_print_results(invoice_data, title):
    print(f"\n{title}")
    print("=" * len(title))
    
    try:
        # Parse invoice data
        invoice = Invoice(**invoice_data)
        
        # Validate invoice
        result = validate_invoice(invoice)
        
        # Print results
        print(f"Valid: {result.is_valid}")
        print(f"Issues: {len(result.issues)}")
        
        if result.issues:
            print("\nValidation Issues:")
            for i, issue in enumerate(result.issues, 1):
                print(f"{i}. [{issue.severity.value.upper()}] {issue.field}: {issue.message} (Code: {issue.code})")
    
    except Exception as e:
        print(f"Error parsing invoice: {e}")


def main():
    print("FIRS Invoice Validation Test")
    print("===========================")
    
    validate_and_print_results(valid_invoice_data, "Valid Invoice Test")
    validate_and_print_results(invalid_invoice_data, "Invalid Invoice Test")


if __name__ == "__main__":
    main() 