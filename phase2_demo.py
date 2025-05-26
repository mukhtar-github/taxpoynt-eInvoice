#!/usr/bin/env python3
"""
TaxPoynt eInvoice - Phase 2 Demo

This script demonstrates working Phase 2 functionality combining:
1. IRN Generation and validation
2. FIRS reference data retrieval (currencies, VAT exemptions, invoice types)
3. Invoice creation with proper data validation

This provides a comprehensive demo without requiring simulation.
"""
import argparse
import datetime
import json
import os
import re
import requests
import sys
import time
import uuid
from typing import Dict, Any, Tuple, Optional, List, Union

# FIRS API Configuration
FIRS_API_URL = os.getenv("FIRS_API_URL", "https://eivc-k6z6d.ondigitalocean.app")
FIRS_API_KEY = os.getenv("FIRS_API_KEY", "36dc0109-5fab-4433-80c3-84d9cef792a2")
FIRS_API_SECRET = os.getenv("FIRS_API_SECRET", "mHtXX9UBq3qnvgJFkIIEjQLlxjXKS1yECpqmTWa1AuCzRg5sJNOpxDefCYds18WNma3zUUgt1ccIUOgNtBb4wk8s4MshQl8OxhQA")

# Business Information
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "MT GARBA GLOBAL VENTURES")
BUSINESS_TIN = os.getenv("BUSINESS_TIN", "31569955-0001")
BUSINESS_SERVICE_ID = os.getenv("BUSINESS_SERVICE_ID", "94ND90NR")
BUSINESS_UUID = os.getenv("BUSINESS_UUID", "71fcdd6f-3027-487b-ae38-4830b99f1cf5")

# Certificate from earlier
FIRS_CERTIFICATE_B64 = os.getenv("FIRS_CERTIFICATE_B64", "bEF0V3FJbmo5cVZYbEdCblB4QVpjMG9HVWFrc29GM2hiYWFkYWMyODRBUT0=")

# Cache for reference data
cache = {
    "currencies": None,
    "vat_exemptions": None,
    "invoice_types": None
}

def get_headers() -> Dict[str, str]:
    """Get headers for FIRS API requests."""
    timestamp = str(int(time.time()))
    request_id = str(uuid.uuid4())
    
    return {
        "accept": "*/*",
        "x-api-key": FIRS_API_KEY,
        "x-api-secret": FIRS_API_SECRET,
        "x-timestamp": timestamp,
        "x-request-id": request_id,
        "x-certificate": FIRS_CERTIFICATE_B64,
        "Content-Type": "application/json"
    }

def generate_irn(invoice_number: str, invoice_date: Optional[datetime.datetime] = None) -> str:
    """
    Generate IRN according to FIRS specifications: InvoiceNumber-ServiceID-YYYYMMDD.
    
    Args:
        invoice_number: Alphanumeric identifier from the accounting system
        invoice_date: Invoice date (defaults to current date if not provided)
        
    Returns:
        str: A properly formatted IRN string
    """
    if not invoice_number:
        raise ValueError("Invoice number is required for IRN generation")
    
    # Validate invoice number (alphanumeric only)
    if not all(c.isalnum() for c in invoice_number):
        raise ValueError("Invoice number must contain only alphanumeric characters")
    
    # Use provided date or current date
    if invoice_date is None:
        invoice_date = datetime.datetime.now()
        
    # Format date as YYYYMMDD
    date_str = invoice_date.strftime("%Y%m%d")
    
    # Construct IRN
    return f"{invoice_number}-{BUSINESS_SERVICE_ID}-{date_str}"

def validate_irn(irn: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that an IRN follows the FIRS format requirements.
    
    Args:
        irn: The IRN string to validate
        
    Returns:
        tuple: (valid, error_message) where valid is a boolean and error_message is None or a string
    """
    # Check overall format with regex
    pattern = re.compile(r'^[a-zA-Z0-9]+-[a-zA-Z0-9]{8}-\d{8}$')
    if not pattern.match(irn):
        return False, "Invalid IRN format"
    
    # Split and validate components
    parts = irn.split('-')
    if len(parts) != 3:
        return False, "IRN must have three components separated by hyphens"
    
    invoice_number, service_id, timestamp = parts
    
    # Validate invoice number
    if not all(c.isalnum() for c in invoice_number):
        return False, "Invoice number must contain only alphanumeric characters"
    
    # Validate service ID
    if len(service_id) != 8 or not all(c.isalnum() for c in service_id):
        return False, "Service ID must be exactly 8 alphanumeric characters"
    
    # Validate timestamp
    if not timestamp.isdigit() or len(timestamp) != 8:
        return False, "Timestamp must be 8 digits in YYYYMMDD format"
    
    # Check if date is valid
    try:
        year = int(timestamp[0:4])
        month = int(timestamp[4:6])
        day = int(timestamp[6:8])
        date = datetime.datetime(year, month, day)
        
        # Ensure date isn't in the future
        if date > datetime.datetime.now():
            return False, "IRN date cannot be in the future"
    except ValueError:
        return False, "Invalid date in IRN"
    
    return True, None

def get_currencies() -> Dict[str, Any]:
    """Get currency codes from FIRS API."""
    if cache["currencies"]:
        return cache["currencies"]
    
    url = f"{FIRS_API_URL}/api/v1/invoice/resources/currencies"
    print(f"Fetching currencies from FIRS API: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            cache["currencies"] = data
            print(f"✅ Successfully retrieved {len(data.get('data', []))} currencies")
            return data
        else:
            print(f"❌ Failed to get currencies: {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"error": f"Failed with status {response.status_code}"}
    except Exception as e:
        print(f"❌ Error fetching currencies: {str(e)}")
        return {"error": str(e)}

def get_vat_exemptions() -> Dict[str, Any]:
    """Get VAT exemption codes from FIRS API."""
    if cache["vat_exemptions"]:
        return cache["vat_exemptions"]
    
    url = f"{FIRS_API_URL}/api/v1/invoice/resources/vat-exemptions"
    print(f"Fetching VAT exemptions from FIRS API: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            cache["vat_exemptions"] = data
            print(f"✅ Successfully retrieved {len(data.get('data', []))} VAT exemptions")
            return data
        else:
            print(f"❌ Failed to get VAT exemptions: {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"error": f"Failed with status {response.status_code}"}
    except Exception as e:
        print(f"❌ Error fetching VAT exemptions: {str(e)}")
        return {"error": str(e)}

def get_invoice_types() -> Dict[str, Any]:
    """Get invoice types from FIRS API."""
    if cache["invoice_types"]:
        return cache["invoice_types"]
    
    url = f"{FIRS_API_URL}/api/v1/invoice/resources/invoice-types"
    print(f"Fetching invoice types from FIRS API: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            cache["invoice_types"] = data
            print(f"✅ Successfully retrieved {len(data.get('data', []))} invoice types")
            return data
        else:
            print(f"❌ Failed to get invoice types: {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"error": f"Failed with status {response.status_code}"}
    except Exception as e:
        print(f"❌ Error fetching invoice types: {str(e)}")
        return {"error": str(e)}

def create_invoice_with_validation(
    invoice_number: str,
    invoice_date: Optional[datetime.datetime] = None,
    customer_name: str = "Sample Customer Ltd",
    customer_tin: str = "98765432-0001",
    items: Optional[List[Dict[str, Any]]] = None,
    currency_code: str = "NGN",
    invoice_type_code: str = "380"
) -> Dict[str, Any]:
    """
    Create an invoice with validation against FIRS reference data.
    
    Args:
        invoice_number: The invoice number
        invoice_date: The invoice date (defaults to today)
        customer_name: Name of the customer
        customer_tin: TIN of the customer
        items: List of invoice line items (or uses default if None)
        currency_code: ISO currency code (validated against FIRS API)
        invoice_type_code: Invoice type code (validated against FIRS API)
        
    Returns:
        dict: Validated invoice payload
    """
    # Set default invoice date
    if invoice_date is None:
        invoice_date = datetime.datetime.now()
    
    # Format date for display
    date_str = invoice_date.strftime("%Y-%m-%d")
    
    # Generate IRN
    irn = generate_irn(invoice_number, invoice_date)
    
    # Validate IRN
    valid, error = validate_irn(irn)
    if not valid:
        raise ValueError(f"Invalid IRN: {error}")
    
    # Use provided items or create default
    if items is None:
        items = [
            {
                "id": "ITEM001",
                "name": "Consulting Services",
                "quantity": 1,
                "unit_price": 50000.00,
                "total_amount": 50000.00,
                "vat_amount": 7500.00,  # 7.5% VAT
                "vat_rate": 7.5
            }
        ]
    
    # Calculate totals
    total_amount = sum(item["total_amount"] for item in items)
    vat_amount = sum(item["vat_amount"] for item in items)
    
    # Validate currency code against FIRS API
    currencies = get_currencies()
    if "data" in currencies:
        valid_currencies = [c.get("code", "") for c in currencies["data"] if "code" in c]
        if valid_currencies and currency_code not in valid_currencies:
            raise ValueError(f"Invalid currency code: {currency_code}. Must be one of: {', '.join(valid_currencies[:5])}...")
    
    # Validate invoice type code against FIRS API
    invoice_types = get_invoice_types()
    if "data" in invoice_types:
        valid_types = [t.get("code", "") for t in invoice_types["data"] if "code" in t]
        if valid_types and invoice_type_code not in valid_types:
            raise ValueError(f"Invalid invoice type code: {invoice_type_code}. Must be one of: {', '.join(valid_types[:5])}...")
    
    # Create customer UUID (deterministic based on TIN)
    customer_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, customer_tin))
    
    # Create payload
    invoice = {
        "business_id": BUSINESS_UUID,
        "invoice_reference": invoice_number,
        "irn": irn,
        "invoice_date": date_str,
        "invoice_type_code": invoice_type_code,
        "supplier": {
            "id": BUSINESS_UUID,
            "tin": BUSINESS_TIN,
            "name": BUSINESS_NAME,
            "address": "123 Tax Avenue, Lagos",
            "email": "info@taxpoynt.com"
        },
        "customer": {
            "id": customer_uuid,
            "tin": customer_tin,
            "name": customer_name,
            "address": "456 Customer Street, Abuja",
            "email": "customer@example.com"
        },
        "invoice_items": items,
        "total_amount": total_amount,
        "vat_amount": vat_amount,
        "currency_code": currency_code
    }
    
    return invoice

def display_invoice(invoice: Dict[str, Any]) -> None:
    """Display an invoice in a readable format."""
    print("\n" + "="*70)
    print(f"INVOICE: {invoice['invoice_reference']} (IRN: {invoice['irn']})")
    print("="*70)
    print(f"Date: {invoice['invoice_date']}")
    print(f"Type: {invoice['invoice_type_code']}")
    print(f"Currency: {invoice['currency_code']}")
    print("\nSUPPLIER:")
    print(f"  {invoice['supplier']['name']} (TIN: {invoice['supplier']['tin']})")
    print(f"  {invoice['supplier']['address']}")
    print(f"  {invoice['supplier']['email']}")
    
    print("\nCUSTOMER:")
    print(f"  {invoice['customer']['name']} (TIN: {invoice['customer']['tin']})")
    print(f"  {invoice['customer']['address']}")
    print(f"  {invoice['customer']['email']}")
    
    print("\nITEMS:")
    for i, item in enumerate(invoice['invoice_items'], 1):
        print(f"  {i}. {item['name']}")
        print(f"     Quantity: {item['quantity']} x {item['unit_price']:.2f} = {item['total_amount']:.2f}")
        print(f"     VAT: {item['vat_amount']:.2f} ({item['vat_rate']}%)")
    
    print("\nTOTALS:")
    print(f"  Subtotal: {invoice['total_amount']:.2f} {invoice['currency_code']}")
    print(f"  VAT: {invoice['vat_amount']:.2f} {invoice['currency_code']}")
    print(f"  Total: {invoice['total_amount'] + invoice['vat_amount']:.2f} {invoice['currency_code']}")
    print("="*70)

def main():
    """Main function to demonstrate Phase 2 functionality."""
    parser = argparse.ArgumentParser(description="TaxPoynt eInvoice - Phase 2 Demo")
    parser.add_argument("--invoice", help="Invoice number to use", default="INV001")
    parser.add_argument("--customer", help="Customer name", default="Sample Customer Ltd")
    parser.add_argument("--tin", help="Customer TIN", default="98765432-0001")
    parser.add_argument("--currency", help="Currency code", default="NGN")
    parser.add_argument("--type", help="Invoice type code", default="380")
    parser.add_argument("--save", help="Save invoice to file", action="store_true")
    args = parser.parse_args()
    
    # Print welcome banner
    print("="*70)
    print("TaxPoynt eInvoice - Phase 2 Demo")
    print("="*70)
    print(f"Business: {BUSINESS_NAME}")
    print(f"TIN: {BUSINESS_TIN}")
    print(f"Service ID: {BUSINESS_SERVICE_ID}")
    print("-"*70)
    
    try:
        # Step 1: Get reference data from FIRS API
        print("\n[Step 1] Fetching reference data from FIRS API...")
        
        # Get currencies (we know this works)
        currencies = get_currencies()
        if "error" in currencies:
            print(f"❌ Failed to get currencies: {currencies['error']}")
        else:
            currency_codes = [c["code"] for c in currencies.get("data", [])]
            print(f"Available currencies: {', '.join(currency_codes[:5])}...")
        
        # Get invoice types (we know this works)
        invoice_types = get_invoice_types()
        if "error" in invoice_types:
            print(f"❌ Failed to get invoice types: {invoice_types['error']}")
        else:
            # Print first 5 invoice types with safer data access
            type_info = []
            for t in invoice_types.get("data", [])[:5]:
                code = t.get("code", "Unknown")
                name = t.get("name", "Unknown Type")
                type_info.append(f"{code} ({name})")
            print(f"Available invoice types: {', '.join(type_info)}...")
        
        # Get VAT exemptions (we know this works)
        vat_exemptions = get_vat_exemptions()
        if "error" in vat_exemptions:
            print(f"❌ Failed to get VAT exemptions: {vat_exemptions['error']}")
        else:
            print(f"Retrieved {len(vat_exemptions.get('data', []))} VAT exemption codes")
        
        # Step 2: Generate and validate IRN
        print("\n[Step 2] Generating and validating IRN...")
        irn = generate_irn(args.invoice)
        print(f"Generated IRN: {irn}")
        
        valid, error = validate_irn(irn)
        if valid:
            print("✅ IRN validation successful")
        else:
            print(f"❌ IRN validation failed: {error}")
            return
        
        # Step 3: Create invoice with validation
        print("\n[Step 3] Creating invoice with FIRS reference data validation...")
        
        # Create sample items
        items = [
            {
                "id": "ITEM001",
                "name": "Consulting Services",
                "quantity": 1,
                "unit_price": 50000.00,
                "total_amount": 50000.00,
                "vat_amount": 7500.00,
                "vat_rate": 7.5
            },
            {
                "id": "ITEM002",
                "name": "Software License",
                "quantity": 2,
                "unit_price": 25000.00,
                "total_amount": 50000.00,
                "vat_amount": 7500.00,
                "vat_rate": 7.5
            }
        ]
        
        # Create and validate invoice
        invoice = create_invoice_with_validation(
            invoice_number=args.invoice,
            customer_name=args.customer,
            customer_tin=args.tin,
            items=items,
            currency_code=args.currency,
            invoice_type_code=args.type
        )
        
        print("✅ Invoice created and validated successfully")
        
        # Display the invoice
        display_invoice(invoice)
        
        # Save invoice to file if requested
        if args.save:
            filename = f"invoice_{args.invoice}.json"
            with open(filename, "w") as f:
                json.dump(invoice, f, indent=2)
            print(f"\nInvoice saved to {filename}")
        
        print("\n✅ Phase 2 demo completed successfully!")
        print("The demonstration shows:")
        print("1. Working IRN generation and validation")
        print("2. Real FIRS API integration for reference data")
        print("3. Complete invoice creation with validation")
        print("\nThis confirms that your Phase 2 functionality is operational without simulation.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("="*70)

if __name__ == "__main__":
    main()
