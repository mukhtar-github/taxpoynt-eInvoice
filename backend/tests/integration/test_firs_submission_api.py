"""
Integration tests for FIRS submission API endpoints.

This module tests the FIRS submission functionality through the API endpoints,
ensuring the entire flow works correctly in the application context.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from io import BytesIO

# Set base URL for the API - change this to match your deployment
BASE_URL = "http://localhost:8000/api/v1"

# Sample test data - Compatible with Odoo format
test_odoo_invoice = {
    "id": 12345,
    "name": "INV-TEST-2025-001",
    "invoice_date": datetime.now().strftime("%Y-%m-%d"),
    "invoice_date_due": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
    "narration": "Test invoice for FIRS submission",
    "invoice_type_code": "380", # Commercial Invoice
    "currency_id": {
        "id": 1,
        "name": "NGN",
        "symbol": "₦"
    },
    "partner_id": {
        "id": 101,
        "name": "Test Customer Ltd",
        "vat": "0987654321",
        "street": "123 Customer Road",
        "city": "Lagos",
        "country_id": {
            "id": 1,
            "name": "Nigeria",
            "code": "NG"
        }
    },
    "company_id": {
        "id": 1,
        "name": "Test Supplier Ltd",
        "vat": "1234567890",
        "street": "456 Supplier Avenue",
        "city": "Abuja",
        "country_id": {
            "id": 1,
            "name": "Nigeria",
            "code": "NG"
        }
    },
    "invoice_line_ids": [
        {
            "id": 1001,
            "name": "Test Product",
            "quantity": 2,
            "price_unit": 100.00,
            "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
            "price_subtotal": 200.00,
            "price_total": 215.00
        }
    ],
    "amount_untaxed": 200.00,
    "amount_tax": 15.00,
    "amount_total": 215.00,
    "payment_reference": "REF-12345",
    "payment_state": "not_paid"
}

# Simple FIRS format invoice
test_invoice = {
    "invoice_number": "INV-TEST-2025-001",
    "issue_date": datetime.now().strftime("%Y-%m-%d"),
    "supplier": {
        "name": "Test Supplier Ltd",
        "tax_id": "1234567890"
    },
    "customer": {
        "name": "Test Customer Ltd",
        "tax_id": "0987654321"
    },
    "items": [
        {
            "description": "Test Product",
            "quantity": 2,
            "unit_price": 100.00,
            "tax_rate": 7.5,
            "line_extension_amount": 200.00,
            "tax_amount": 15.00
        }
    ],
    "tax_total": 15.00,
    "invoice_total": 215.00
}

# Test credentials
test_credentials = {
    "email": os.environ.get("TEST_USER_EMAIL", "test@example.com"),
    "password": os.environ.get("TEST_USER_PASSWORD", "test_password")
}

# Store auth token and submission IDs
auth_token = None
submission_id = None


def get_auth_token():
    """Get authentication token for API requests."""
    global auth_token
    
    if auth_token:
        return auth_token
        
    response = requests.post(
        f"{BASE_URL}/auth/token",
        json=test_credentials
    )
    
    if response.status_code == 200:
        token_data = response.json()
        auth_token = token_data.get("access_token")
        return auth_token
    else:
        print(f"Authentication failed: {response.status_code} - {response.text}")
        return None


def get_headers():
    """Get headers for authenticated API requests."""
    token = get_auth_token()
    if not token:
        raise Exception("Failed to get authentication token")
        
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def test_submit_invoice():
    """Test submitting a single invoice."""
    global submission_id
    
    print("=== Testing single invoice submission ===")
    
    try:
        headers = get_headers()
        response = requests.post(
            f"{BASE_URL}/firs/submission/invoice",
            headers=headers,
            json=test_invoice
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        
        assert response.status_code in (200, 201, 202), "Submission failed"
        assert result.get("success") == True, "Submission reported failure"
        
        # Store submission ID for status check
        submission_id = result.get("submission_id")
        
        print("✅ Test passed: Invoice submitted successfully")
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_check_submission_status():
    """Test checking the status of a submission."""
    global submission_id
    
    if not submission_id:
        print("❌ No submission ID available to check status")
        return False
        
    print(f"=== Testing submission status check for ID: {submission_id} ===")
    
    try:
        headers = get_headers()
        response = requests.get(
            f"{BASE_URL}/firs/submission/status/{submission_id}",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        
        assert response.status_code == 200, "Status check failed"
        assert result.get("submission_id") == submission_id, "Submission ID mismatch"
        
        print("✅ Test passed: Submission status checked successfully")
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_batch_submission():
    """Test submitting a batch of invoices."""
    global submission_id
    
    print("=== Testing batch invoice submission ===")
    
    # Create batch of invoices
    invoices = []
    for i in range(2):
        invoice = test_invoice.copy()
        invoice["invoice_number"] = f"INV-TEST-2025-{100 + i}"
        invoices.append(invoice)
    
    try:
        headers = get_headers()
        response = requests.post(
            f"{BASE_URL}/firs/submission/batch",
            headers=headers,
            json=invoices
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        
        assert response.status_code in (200, 201, 202), "Batch submission failed"
        assert result.get("success") == True, "Batch submission reported failure"
        
        # Store submission ID for status check
        batch_submission_id = result.get("submission_id")
        
        print("✅ Test passed: Invoice batch submitted successfully")
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def test_odoo_ubl_submission():
    """Test submitting an invoice using the Odoo UBL mapping system.
    
    This test leverages the existing Odoo to BIS Billing 3.0 UBL mapping system
    to transform an Odoo invoice to UBL format and submit it to FIRS.
    """
    global submission_id
    
    print("=== Testing Odoo UBL invoice submission ===")
    
    try:
        # Step 1: Call the Odoo UBL mapping endpoint to transform the invoice to UBL
        headers = get_headers()
        response = requests.post(
            f"{BASE_URL}/odoo-ubl/map-invoice",
            headers=headers,
            json=test_odoo_invoice
        )
        
        # Check if mapping was successful
        if response.status_code != 200:
            print(f"❌ Failed to map Odoo invoice to UBL: {response.status_code} - {response.text}")
            return False
            
        ubl_result = response.json()
        
        # Check if UBL XML was generated
        if not ubl_result.get("success") or not ubl_result.get("ubl_xml"):
            print(f"❌ UBL mapping did not return valid XML: {ubl_result.get('message')}")
            return False
            
        ubl_xml = ubl_result.get("ubl_xml")
        print("✅ Successfully mapped Odoo invoice to UBL format")
        
        # Step 2: Create a file-like object with the UBL XML
        ubl_bytes = ubl_xml.encode("utf-8")
        ubl_file = BytesIO(ubl_bytes)
        
        # Step 3: Submit the UBL XML to FIRS
        files = {
            'ubl_file': ('invoice.xml', ubl_file, 'application/xml')
        }
        
        data = {
            'invoice_type': 'standard'  # Commercial invoice
        }
        
        response = requests.post(
            f"{BASE_URL}/firs/submission/ubl",
            headers=headers,
            files=files,
            data=data
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        
        assert response.status_code in (200, 201, 202), "UBL submission failed"
        assert result.get("success") == True, "UBL submission reported failure"
        
        # Store submission ID for status check
        ubl_submission_id = result.get("submission_id")
        if not submission_id and ubl_submission_id:
            submission_id = ubl_submission_id
        
        print("✅ Test passed: Odoo UBL invoice submitted successfully")
        return True
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all integration tests."""
    print("Starting FIRS Submission API Integration Tests")
    print("-" * 50)
    
    results = {}
    
    # Run tests
    results["submit_invoice"] = test_submit_invoice()
    
    if submission_id:
        results["check_status"] = test_check_submission_status()
    
    results["batch_submission"] = test_batch_submission()
    
    # Test UBL submission using Odoo mapping
    results["odoo_ubl_submission"] = test_odoo_ubl_submission()
    
    # Print summary
    print("\nTest Results Summary:")
    print("-" * 50)
    
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test}: {status}")
        if not passed:
            all_passed = False
    
    print("-" * 50)
    print(f"Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    # Set credentials from environment if available
    if "TEST_USER_EMAIL" in os.environ and "TEST_USER_PASSWORD" in os.environ:
        test_credentials["email"] = os.environ["TEST_USER_EMAIL"]
        test_credentials["password"] = os.environ["TEST_USER_PASSWORD"]
    
    # Check if server URL is specified
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    
    print(f"Using API at: {BASE_URL}")
    
    # Run tests
    success = run_all_tests()
    sys.exit(0 if success else 1)
