#!/usr/bin/env python3
"""
Direct test script for FIRS sandbox API connectivity.
This script tests connection to the FIRS sandbox without complex dependencies.
"""
import os
import requests
import json
import base64
from datetime import datetime
from pathlib import Path

# FIRS API credentials and crypto paths
FIRS_API_BASE_URL = "http://206.189.15.119:8080" # From the API documentation URL
FIRS_API_KEY = "36dc0109-5fab-4433-80c3-84d9cef792a2"
FIRS_API_SECRET = "mHtXX9UBq3qnvgJFkIIEjQLlxjXKS1yECpqmTWa1AuCzRg5sJNOpxDefCYds18WNma3zUUgt1ccIUOgNtBb4wk8s4MshQl8OxhQA"
FIRS_PUBLIC_KEY_PATH = "/home/mukhtar-tanimu/taxpoynt-eInvoice/backend/crypto/firs_public_key.pem"
FIRS_CERTIFICATE_PATH = "/home/mukhtar-tanimu/taxpoynt-eInvoice/backend/crypto/firs_certificate.txt"

# API Endpoints from the documentation
API_ENDPOINT_HEALTH_CHECK = "/"

# Invoice Management Endpoints
API_ENDPOINT_IRN_VALIDATE = "/api/v1/invoice/irn/validate"
API_ENDPOINT_INVOICE_VALIDATE = "/api/v1/invoice/validate"
API_ENDPOINT_INVOICE_SIGN = "/api/v1/invoice/sign"
API_ENDPOINT_BUSINESS_SEARCH = "/api/v1/entity"
API_ENDPOINT_DOWNLOAD_INVOICE = "/api/v1/invoice/download"
API_ENDPOINT_TRANSACT = "/api/v1/invoice/transact"

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

def load_firs_public_key():
    """Load the FIRS public key from PEM file."""
    try:
        with open(FIRS_PUBLIC_KEY_PATH, 'rb') as f:
            public_key = f.read()
        return public_key
    except Exception as e:
        print(f"Error loading public key: {str(e)}")
        return None
        
def load_firs_certificate():
    """Load the FIRS certificate from file."""
    try:
        with open(FIRS_CERTIFICATE_PATH, 'r') as f:
            certificate = f.read().strip()
        return certificate
    except Exception as e:
        print(f"Error loading certificate: {str(e)}")
        return None
        
def prepare_encrypted_irn(irn, certificate):
    """Prepare encrypted IRN data for validation.
    
    This is a simplified implementation and may need adjustments based on
    actual FIRS documentation for proper IRN encryption.
    """
    try:
        # Create a dictionary with IRN and certificate
        irn_data = {
            "irn": irn,
            "certificate": certificate
        }
        
        # Convert to JSON and encode as base64
        json_data = json.dumps(irn_data)
        return base64.b64encode(json_data.encode()).decode()
    except Exception as e:
        print(f"Error preparing encrypted IRN: {str(e)}")
        return None

def main():
    print("=" * 60)
    print("FIRS API Direct Integration Test")
    print("=" * 60)
    print("Using TaxPoynt eInvoice Odoo Integration Framework")
    print("=" * 60)
    
    # Test 1: Health Check (API Availability)
    print("\n[1/5] Testing API Health Check...")
    try:
        # Use the health check endpoint from documentation
        health_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_HEALTH_CHECK}"
        print(f"Connecting to: {health_url}")
        
        response = requests.get(
            health_url,
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Connection successful! Status code: {response.status_code}")
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
            "limit": 10,
            "page": 1,
            "sort_by": "created_at"
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
        # Extract BUSINESS_ID from documentation Image 4 (/api/v1/invoice/party/{BUSINESS_ID})
        business_id = "BUSINESS_ID"
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
        
        # Try with MT GARBA GLOBAL VENTURES from your dashboard
        try:
            print("\nTrying with 'MT GARBA GLOBAL VENTURES' business ID...")
            business_id = "MT_GARBA_GLOBAL_VENTURES"
            business_url = f"{FIRS_API_BASE_URL}/api/v1/invoice/party/{business_id}"
            print(f"Connecting to: {business_url}")
            
            alt_response = requests.get(
                business_url,
                headers=get_headers(),
                timeout=10
            )
            print(f"Alternative business lookup response: Status {alt_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Alternative business lookup failed: {str(e)}")
    
    
    # Test 4: Get Reference Data (for Odoo UBL Mapping)
    print("\n[4/5] Testing Reference Data for Odoo Integration...")
    try:
        # Testing retrieval of invoice types - important for Odoo UBL mapping
        invoice_types_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_GET_INVOICE_TYPES}"
        print(f"Getting invoice types from: {invoice_types_url}")
        
        invoice_types_response = requests.get(
            invoice_types_url,
            headers=get_headers(),
            timeout=10
        )
        
        print(f"Invoice types response: Status {invoice_types_response.status_code}")
        if invoice_types_response.status_code == 200:
            print("✅ Retrieved invoice types successfully")
            # Save the response for reference with Odoo integration
            with open("firs_invoice_types.json", "w") as f:
                try:
                    json.dump(invoice_types_response.json(), f, indent=2)
                    print("   Invoice types saved to firs_invoice_types.json")
                except:
                    f.write(invoice_types_response.text)
                    print("   Raw invoice types response saved")
        else:
            print(f"⚠️ Failed to retrieve invoice types: {invoice_types_response.status_code}")
        
        # Get currencies for invoice creation
        currencies_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_GET_CURRENCIES}"
        print(f"\nGetting currencies from: {currencies_url}")
        
        currencies_response = requests.get(
            currencies_url,
            headers=get_headers(),
            timeout=10
        )
        
        print(f"Currencies response: Status {currencies_response.status_code}")
        if currencies_response.status_code == 200:
            print("✅ Retrieved currencies successfully")
            # Save for Odoo mapping reference
            with open("firs_currencies.json", "w") as f:
                try:
                    json.dump(currencies_response.json(), f, indent=2)
                    print("   Currencies saved to firs_currencies.json")
                except:
                    f.write(currencies_response.text)
                    print("   Raw currencies response saved")
        else:
            print(f"⚠️ Failed to retrieve currencies: {currencies_response.status_code}")
            
        # Get VAT exemptions for tax handling
        vat_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_GET_VAT_EXEMPTIONS}"
        print(f"\nGetting VAT exemptions from: {vat_url}")
        
        vat_response = requests.get(
            vat_url,
            headers=get_headers(),
            timeout=10
        )
        
        print(f"VAT exemptions response: Status {vat_response.status_code}")
        if vat_response.status_code == 200:
            print("✅ Retrieved VAT exemptions successfully")
            with open("firs_vat_exemptions.json", "w") as f:
                try:
                    json.dump(vat_response.json(), f, indent=2)
                    print("   VAT exemptions saved to firs_vat_exemptions.json")
                except:
                    f.write(vat_response.text)
                    print("   Raw VAT exemptions response saved")
        else:
            print(f"⚠️ Failed to retrieve VAT exemptions: {vat_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Reference data test failed: {str(e)}")
    
    # Test 5: IRN Validation with Cryptographic Keys
    print("\n[5/5] Testing IRN Validation with Cryptographic Keys...")
    try:
        # Load cryptographic materials
        public_key = load_firs_public_key()
        certificate = load_firs_certificate()
        
        if not public_key or not certificate:
            print("❌ Failed to load cryptographic keys")
            return
        
        print("✅ Successfully loaded cryptographic keys")
        print(f"   Public key length: {len(public_key)} bytes")
        print(f"   Certificate: {certificate[:20]}...")
        
        # Test IRN - this would be a real IRN in production
        test_irn = "TEST-IRN-2025-001"
        business_id = "MT GARBA GLOBAL VENTURES"  # From your Image 3
        
        # Prepare encrypted IRN data
        encrypted_irn = prepare_encrypted_irn(test_irn, certificate)
        
        if not encrypted_irn:
            print("❌ Failed to prepare encrypted IRN data")
            return
            
        print("✅ Successfully prepared encrypted IRN data")
        
        # The correct endpoint from the documentation Image 4
        irn_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_IRN_VALIDATE}"
        print(f"Connecting to: {irn_url}")
        
        # Based on the documentation, construct the proper payload
        irn_payload = {
            "invoice_reference": "INV-2025-001",
            "business_id": business_id,
            "irn": test_irn,
            "signature": encrypted_irn
        }
        
        print("Sending IRN validation request...")
        irn_response = requests.post(
            irn_url,
            headers=get_headers(),
            json=irn_payload,
            timeout=15
        )
        
        print(f"IRN Validation response: Status {irn_response.status_code}")
        if irn_response.status_code in (200, 201, 202):
            print("✅ IRN Validation successful")
            print(f"Response: {irn_response.text[:100]}...")
            # Save the response for reference
            with open("irn_validation_response.json", "w") as f:
                json.dump(irn_response.json(), f, indent=2)
            print("   Response saved to irn_validation_response.json")
        else:
            print(f"⚠️ IRN Validation returned status: {irn_response.status_code}")
            print(f"Response: {irn_response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"❌ IRN Validation request failed: {str(e)}")
    except Exception as e:
        print(f"❌ Error during IRN validation: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("FIRS Sandbox API Tests Completed")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Review any errors from the tests above")
    print("2. Adjust API endpoints based on actual documentation if needed")
    print("3. Verify the credentials are correct if authentications failed")
    print("4. For production integration, update the FIRSService to match working endpoints")

if __name__ == "__main__":
    main()
