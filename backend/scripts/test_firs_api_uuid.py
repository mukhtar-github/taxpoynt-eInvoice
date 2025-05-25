#!/usr/bin/env python3
"""
Direct test script for FIRS sandbox API connectivity using UUID4 business IDs.
This script tests connection to the FIRS sandbox without complex dependencies.
"""
import os
import requests
import json
import base64
import uuid
import datetime
from pathlib import Path

# FIRS API credentials and crypto paths
# Updated with the latest sandbox environment information (May 2025)
FIRS_USE_SANDBOX = True
FIRS_API_BASE_URL = "https://eivc-k6z6d.ondigitalocean.app" # Updated sandbox URL
FIRS_API_KEY = "36dc0109-5fab-4433-80c3-84d9cef792a2"
FIRS_API_SECRET = "mHtXX9UBq3qnvgJFkIIEjQLlxjXKS1yECpqmTWa1AuCzRg5sJNOpxDefCYds18WNma3zUUgt1ccIUOgNtBb4wk8s4MshQl8OxhQA"
FIRS_PUBLIC_KEY_PATH = "/home/mukhtar-tanimu/taxpoynt-eInvoice/backend/crypto/firs_public_key.pem"
FIRS_CERTIFICATE_PATH = "/home/mukhtar-tanimu/taxpoynt-eInvoice/backend/crypto/firs_certificate.txt"

# TIN information and FIRS credentials
USER_TIN = "31569955-0001"
# FIRS-assigned 8-character Service ID for IRN generation
SERVICE_ID = "94ND90NR"

# API Endpoints updated from the FIRS-MBS E-Invoicing Documentation (May 2025)
API_ENDPOINT_HEALTH_CHECK = "/api"

# Entity and Party Management Endpoints
API_ENDPOINT_BUSINESS_SEARCH = "/api/v1/entity"
API_ENDPOINT_BUSINESS_BY_ID = "/api/v1/entity/{ENTITY_ID}"
API_ENDPOINT_CREATE_PARTY = "/api/v1/invoice/party"
API_ENDPOINT_GET_PARTY = "/api/v1/invoice/party/{BUSINESS_ID}"

# Invoice Management Endpoints
API_ENDPOINT_IRN_VALIDATION = "/api/v1/invoice/irn/validate"
API_ENDPOINT_INVOICE_VALIDATE = "/api/v1/invoice/validate"
API_ENDPOINT_INVOICE_SIGN = "/api/v1/invoice/sign"
API_ENDPOINT_INVOICE_CONFIRM = "/api/v1/invoice/confirm/{IRN}"
API_ENDPOINT_DOWNLOAD_INVOICE = "/api/v1/invoice/download/{IRN}"
API_ENDPOINT_SEARCH_INVOICE = "/api/v1/invoice/{BUSINESS_ID}"

# Utility Endpoints
API_ENDPOINT_VERIFY_TIN = "/api/v1/utilities/verify-tin"
API_ENDPOINT_AUTHENTICATE = "/api/v1/utilities/authenticate"

# Resource Endpoints
API_ENDPOINT_GET_COUNTRIES = "/api/v1/invoice/resources/countries"
API_ENDPOINT_GET_INVOICE_TYPES = "/api/v1/invoice/resources/invoice-types"
API_ENDPOINT_GET_CURRENCIES = "/api/v1/invoice/resources/currencies"
API_ENDPOINT_GET_VAT_EXEMPTIONS = "/api/v1/invoice/resources/vat-exemptions"
API_ENDPOINT_GET_SERVICE_CODES = "/api/v1/invoice/resources/service-codes"

# Utility functions for API requests and crypto
def get_headers():
    """Get headers for API requests with API key authentication."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": FIRS_API_KEY,
        "x-api-secret": FIRS_API_SECRET
    }

def get_business_id():
    """Return a UUID4 format business ID for FIRS API.
    
    FIRS API requires valid UUID4 format business IDs.
    In production, this would be a stored UUID4 associated with your TIN.
    """
    # Generate a valid UUID4 as required by FIRS API
    # In production, this would be a stored UUID4 associated with your TIN
    business_id = str(uuid.uuid4())
    print(f"Using business_id UUID4: {business_id} (associated with TIN {USER_TIN})")
    return business_id

def get_tin():
    """Return the TIN for use in invoice payloads.
    
    This function returns the USER's TIN for use in fields where TIN is required,
    such as supplier/customer party fields in invoice payloads.
    """
    # In a production system, this would be fetched from a secure storage or config
    return USER_TIN

def generate_irn(invoice_number, invoice_date=None):
    """Generate IRN according to FIRS specifications: InvoiceNumber-ServiceID-YYYYMMDD.
    
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
    return f"{invoice_number}-{SERVICE_ID}-{date_str}"

def validate_irn(irn):
    """Validate that an IRN follows the FIRS format requirements.
    
    Args:
        irn: The IRN string to validate
        
    Returns:
        tuple: (valid, error_message) where valid is a boolean and error_message is None or a string
    """
    import re
    
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

def prepare_irn_validation_payload():
    """Prepare payload for IRN validation based on the FIRS-MBS E-Invoicing Documentation.
    
    This function creates a sample invoice payload that uses:
    - UUID4 format for business_id fields (required by FIRS API)
    - TIN for tax identification fields (supplier_tin, customer_tin)
    """
    try:
        # Get UUID4 business ID and TIN
        business_id = get_business_id()
        tin = get_tin()
        
        # Current date in ISO format for invoice date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Create a dictionary with required fields from documentation
        payload = {
            "business_id": business_id,  # UUID4 format as required by API
            "invoice_reference": "INV001",
            "irn": generate_irn("INV001"),  # Proper FIRS IRN format: InvoiceNumber-ServiceID-YYYYMMDD
            "invoice_date": current_date,
            "invoice_type_code": "380",  # Commercial Invoice
            "supplier": {
                "id": business_id,  # UUID4 format
                "tin": tin,  # TIN for tax identification
                "name": "TaxPoynt Ltd",
                "address": "123 Tax Avenue, Lagos",
                "email": "info@taxpoynt.com"
            },
            "customer": {
                "id": str(uuid.uuid4()),  # UUID4 format for customer ID
                "tin": "98765432-0001",  # Sample customer TIN
                "name": "Sample Customer Ltd",
                "address": "456 Customer Street, Abuja",
                "email": "customer@example.com"
            },
            "invoice_items": [
                {
                    "id": "ITEM001",
                    "name": "Consulting Services",
                    "quantity": 1,
                    "unit_price": 50000.00,
                    "total_amount": 50000.00,
                    "vat_amount": 7500.00,  # 7.5% VAT
                    "vat_rate": 7.5
                }
            ],
            "total_amount": 50000.00,
            "vat_amount": 7500.00,
            "currency_code": "NGN"
        }
        
        return payload
    except Exception as e:
        print(f"Error preparing IRN validation payload: {str(e)}")
        return None

def main():
    print("=" * 60)
    print("FIRS API Direct Integration Test (UUID4 Format)")
    print("=" * 60)
    print("Using TaxPoynt eInvoice Odoo Integration Framework")
    print(f"FIRS Sandbox Mode: {FIRS_USE_SANDBOX}")
    print(f"User TIN: {USER_TIN}")
    print(f"FIRS Service ID: {SERVICE_ID}")
    print("=" * 60)
    
    # Test IRN generation and validation
    print("\n[0/5] Testing IRN Generation...")
    try:
        # Generate a test IRN
        test_invoice_number = "TEST001"
        test_irn = generate_irn(test_invoice_number)
        print(f"✅ Generated IRN: {test_irn}")
        
        # Validate the IRN
        is_valid, error_message = validate_irn(test_irn)
        if is_valid:
            print("✅ IRN validation successful")
        else:
            print(f"❌ IRN validation failed: {error_message}")
            
        # Test with an invalid IRN
        invalid_irn = "INVALID-FORMAT"
        is_valid, error_message = validate_irn(invalid_irn)
        if not is_valid:
            print(f"✅ Invalid IRN correctly detected: {error_message}")
        
        # Test with a malformed IRN (wrong service ID length)
        malformed_irn = f"TEST001-ABCD-{datetime.datetime.now().strftime('%Y%m%d')}"
        is_valid, error_message = validate_irn(malformed_irn)
        if not is_valid:
            print(f"✅ Malformed IRN correctly detected: {error_message}")
            
        print("✅ IRN generation and validation tests completed successfully")
    except Exception as e:
        print(f"❌ IRN generation test failed: {str(e)}")
    print("-" * 60)
    
    # Test 1: Health Check (API Availability)
    print("\n[1/5] Testing API Health Check...")
    try:
        # Use the updated health check endpoint from FIRS API Integration Guide
        health_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_HEALTH_CHECK}"
        print(f"Connecting to: {health_url}")
        
        response = requests.get(
            health_url,
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Connection successful! Status code: {response.status_code}")
            try:
                health_data = response.json()
                print(f"Response: {json.dumps(health_data, indent=2)}")
                if health_data.get('healthy') == True:
                    print("✅ API health check confirmed operational status")
            except:
                # Handle case where response might not be JSON
                print(f"Response: {response.text[:100]}...")
        else:
            print(f"⚠️ Connection received a non-200 response: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {str(e)}")
    
    # Test 2: Business Entity Search
    print("\n[2/5] Testing Business Entity Search...")
    try:
        # Use the business search endpoint from documentation
        business_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_BUSINESS_SEARCH}"
        print(f"Connecting to: {business_url}")
        
        # Parameters based on documentation screenshot
        business_params = {
            "size": 20,
            "page": 1,
            "sort_by": "created_at",
            "sort_direction_desc": "true"
        }
        
        business_response = requests.get(
            business_url,
            headers=get_headers(),
            params=business_params,
            timeout=10
        )
        
        print(f"Business search response: Status {business_response.status_code}")
        if business_response.status_code == 200:
            print("✅ Business search endpoint accessible")
            print(f"Response: {business_response.text[:100]}...")
            # Save the response for reference
            with open("business_search_response.json", "w") as f:
                try:
                    json.dump(business_response.json(), f, indent=2)
                    print("   Response saved to business_search_response.json")
                except:
                    f.write(business_response.text)
                    print("   Raw response saved to business_search_response.json")
        else:
            print(f"⚠️ Business search endpoint returned status: {business_response.status_code}")
            print(f"Response: {business_response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Business search test failed: {str(e)}")
        
    # Test 3: Specific Business ID lookup
    print("\n[3/5] Testing Business ID Lookup...")
    try:
        # Use UUID4 format business_id
        business_id = get_business_id()
        business_url = f"{FIRS_API_BASE_URL}/api/v1/invoice/party/{business_id}"
        print(f"Connecting to: {business_url}")
        
        business_lookup_response = requests.get(
            business_url,
            headers=get_headers(),
            timeout=10
        )
        
        print(f"Business lookup response: Status {business_lookup_response.status_code}")
        if business_lookup_response.status_code == 200:
            print("✅ Business lookup endpoint accessible")
            print(f"Response: {business_lookup_response.text[:100]}...")
        else:
            print(f"⚠️ Business lookup endpoint returned status: {business_lookup_response.status_code}")
            print(f"Response: {business_lookup_response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Business lookup test failed: {str(e)}")
        
    # Test 4: IRN Validation Test
    print("\n[4/5] Testing IRN Validation...")
    try:
        irn_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_IRN_VALIDATION}"
        print(f"Connecting to: {irn_url}")
        
        # Prepare IRN validation payload with UUID4 business_id
        irn_payload = prepare_irn_validation_payload()
        print(f"Sending payload: {json.dumps(irn_payload, indent=2)}")
        
        irn_response = requests.post(
            irn_url,
            headers=get_headers(),
            json=irn_payload,
            timeout=10
        )
        
        print(f"IRN validation response: Status {irn_response.status_code}")
        if irn_response.status_code == 200:
            print("✅ IRN validation endpoint accessible")
            print(f"Response: {irn_response.text[:100]}...")
        else:
            print(f"⚠️ IRN validation endpoint returned status: {irn_response.status_code}")
            print(f"Response: {irn_response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ IRN validation test failed: {str(e)}")
    
    # Test 5: Resources Endpoints
    print("\n[5/5] Testing Resources Endpoints...")
    try:
        # Test currencies endpoint
        currencies_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_GET_CURRENCIES}"
        print(f"Connecting to currencies endpoint: {currencies_url}")
        
        currencies_response = requests.get(
            currencies_url,
            headers=get_headers(),
            timeout=10
        )
        
        print(f"Currencies endpoint response: Status {currencies_response.status_code}")
        if currencies_response.status_code == 200:
            print("✅ Currencies endpoint accessible")
            print(f"Response: {currencies_response.text[:100]}...")
        else:
            print(f"⚠️ Currencies endpoint returned status: {currencies_response.status_code}")
            print(f"Response: {currencies_response.text[:200]}")
            
        # Test VAT exemptions endpoint
        vat_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_GET_VAT_EXEMPTIONS}"
        print(f"\nConnecting to VAT exemptions endpoint: {vat_url}")
        
        vat_response = requests.get(
            vat_url,
            headers=get_headers(),
            timeout=10
        )
        
        print(f"VAT exemptions endpoint response: Status {vat_response.status_code}")
        if vat_response.status_code == 200:
            print("✅ VAT exemptions endpoint accessible")
            print(f"Response: {vat_response.text[:100]}...")
        else:
            print(f"⚠️ VAT exemptions endpoint returned status: {vat_response.status_code}")
            print(f"Response: {vat_response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Resources endpoints test failed: {str(e)}")
        
    print("\n" + "=" * 60)
    print("FIRS API Direct Integration Test Complete")
    print("=" * 60)
    print("Next steps:")
    print("1. Register your business with FIRS to obtain a valid UUID4 business ID")
    print("2. Update the API calls with your registered business ID")
    print("3. Test with actual Odoo invoice data using the OdooUBLTransformer")
    print("=" * 60)

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
