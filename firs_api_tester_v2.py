#!/usr/bin/env python3
"""
TaxPoynt eInvoice - FIRS API Endpoint Tester (v2)

Tests FIRS API endpoints to determine which ones are accessible
with the current credentials and configuration. This version adds
invoice validation and party endpoints.
"""
import argparse
import datetime
import json
import os
import requests
import sys
import time
import uuid
from typing import Dict, Any, Optional

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

def generate_irn(invoice_number: str) -> str:
    """Generate an IRN using the FIRS format."""
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    return f"{invoice_number}-{BUSINESS_SERVICE_ID}-{date_str}"

def create_invoice_payload(invoice_number: str) -> Dict[str, Any]:
    """Create a sample invoice payload for testing."""
    irn = generate_irn(invoice_number)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    return {
        "business_id": BUSINESS_UUID,
        "invoice_reference": invoice_number,
        "irn": irn,
        "invoice_date": current_date,
        "invoice_type_code": "380",
        "supplier": {
            "id": BUSINESS_UUID,
            "tin": BUSINESS_TIN,
            "name": BUSINESS_NAME,
            "address": "123 Tax Avenue, Lagos",
            "email": "info@taxpoynt.com"
        },
        "customer": {
            "id": "212a597c-f04a-459b-b14c-1875921d8ce1",
            "tin": "98765432-0001",
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
                "vat_amount": 7500.00,
                "vat_rate": 7.5
            }
        ],
        "total_amount": 50000.00,
        "vat_amount": 7500.00,
        "currency_code": "NGN"
    }

def test_resources_endpoint() -> Dict[str, Any]:
    """Test the currencies resource endpoint."""
    url = f"{FIRS_API_URL}/api/v1/invoice/resources/currencies"
    print(f"\nTesting currencies resource endpoint: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('data', []))} currencies")
            return {"success": True, "data": data}
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"success": False, "error": response.text}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_vat_exemptions_endpoint() -> Dict[str, Any]:
    """Test the VAT exemptions resource endpoint."""
    url = f"{FIRS_API_URL}/api/v1/invoice/resources/vat-exemptions"
    print(f"\nTesting VAT exemptions resource endpoint: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('data', []))} VAT exemptions")
            return {"success": True, "data": data}
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"success": False, "error": response.text}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_irn_validation_endpoint(invoice_number: str) -> Dict[str, Any]:
    """Test the IRN validation endpoint."""
    url = f"{FIRS_API_URL}/api/v1/invoice/irn/validate"
    print(f"\nTesting IRN validation endpoint: {url}")
    
    # Create payload
    payload = create_invoice_payload(invoice_number)
    irn = payload["irn"]
    
    try:
        print(f"Using IRN: {irn}")
        print(f"Sending payload: {json.dumps(payload, indent=2)[:200]}...")
        
        response = requests.post(url, json=payload, headers=get_headers())
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! IRN validation successful")
            return {"success": True, "data": data, "irn": irn}
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"success": False, "error": response.text, "irn": irn}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e), "irn": irn}

def test_invoice_validation_endpoint(invoice_number: str) -> Dict[str, Any]:
    """Test the invoice validation endpoint."""
    url = f"{FIRS_API_URL}/api/v1/invoice/validate"
    print(f"\nTesting invoice validation endpoint: {url}")
    
    # Create payload
    payload = create_invoice_payload(invoice_number)
    irn = payload["irn"]
    
    try:
        print(f"Using IRN: {irn}")
        print(f"Sending payload: {json.dumps(payload, indent=2)[:200]}...")
        
        response = requests.post(url, json=payload, headers=get_headers())
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Invoice validation successful")
            return {"success": True, "data": data, "irn": irn}
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"success": False, "error": response.text, "irn": irn}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e), "irn": irn}

def test_create_party_endpoint() -> Dict[str, Any]:
    """Test the create party endpoint."""
    url = f"{FIRS_API_URL}/api/v1/invoice/party"
    print(f"\nTesting create party endpoint: {url}")
    
    # Create payload
    payload = {
        "business_id": BUSINESS_UUID,
        "tin": BUSINESS_TIN,
        "name": BUSINESS_NAME,
        "address": "123 Tax Avenue, Lagos",
        "email": "info@taxpoynt.com",
        "phone": "08001234567",
        "website": "https://example.com",
        "registration_number": "RC123456",
        "tax_office": "FIRS Lagos Island"
    }
    
    try:
        print(f"Sending payload: {json.dumps(payload, indent=2)[:200]}...")
        
        response = requests.post(url, json=payload, headers=get_headers())
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            print(f"✅ Success! Party created successfully")
            return {"success": True, "data": data}
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"success": False, "error": response.text}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_search_party_endpoint() -> Dict[str, Any]:
    """Test the search party endpoint."""
    url = f"{FIRS_API_URL}/api/v1/invoice/party/{BUSINESS_UUID}"
    print(f"\nTesting search party endpoint: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Party found")
            return {"success": True, "data": data}
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"success": False, "error": response.text}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_invoice_types_endpoint() -> Dict[str, Any]:
    """Test the invoice types resource endpoint."""
    url = f"{FIRS_API_URL}/api/v1/invoice/resources/invoice-types"
    print(f"\nTesting invoice types resource endpoint: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('data', []))} invoice types")
            return {"success": True, "data": data}
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:150]}...")
            return {"success": False, "error": response.text}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """Main function to test FIRS API endpoints."""
    parser = argparse.ArgumentParser(description="FIRS API Endpoint Tester (v2)")
    parser.add_argument("--invoice", help="Invoice number to use for tests", default="INV001")
    parser.add_argument("--endpoint", help="Specific endpoint to test (leave empty to test all)")
    args = parser.parse_args()
    
    # Print welcome banner
    print("="*70)
    print("TaxPoynt eInvoice - FIRS API Endpoint Tester (v2)")
    print("="*70)
    print(f"API URL: {FIRS_API_URL}")
    print(f"Business: {BUSINESS_NAME}")
    print(f"TIN: {BUSINESS_TIN}")
    print(f"Service ID: {BUSINESS_SERVICE_ID}")
    print(f"Business UUID: {BUSINESS_UUID}")
    print("-"*70)
    
    # Define all test functions
    tests = {
        "currencies": lambda: test_resources_endpoint(),
        "vat_exemptions": lambda: test_vat_exemptions_endpoint(),
        "invoice_types": lambda: test_invoice_types_endpoint(),
        "irn_validation": lambda: test_irn_validation_endpoint(args.invoice),
        "invoice_validation": lambda: test_invoice_validation_endpoint(args.invoice),
        "create_party": lambda: test_create_party_endpoint(),
        "search_party": lambda: test_search_party_endpoint()
    }
    
    # Run tests
    results = {}
    
    if args.endpoint and args.endpoint in tests:
        # Run only the specified test
        print(f"Testing only: {args.endpoint}")
        results[args.endpoint] = tests[args.endpoint]()
    else:
        # Run all tests
        for name, test_func in tests.items():
            results[name] = test_func()
    
    # Print summary
    print("\n" + "="*70)
    print("Endpoint Testing Summary")
    print("="*70)
    
    for key, result in results.items():
        status = "✅ SUCCESS" if result.get("success", False) else "❌ FAILED"
        print(f"{key}: {status}")
    
    # Print working endpoints
    working_endpoints = [key for key, result in results.items() if result.get("success", False)]
    if working_endpoints:
        print("\nWorking endpoints:")
        for endpoint in working_endpoints:
            print(f"- {endpoint}")
    
    print("\nTest complete. These endpoints can be included in your Phase 2 demo.")
    print("="*70)

if __name__ == "__main__":
    main()
