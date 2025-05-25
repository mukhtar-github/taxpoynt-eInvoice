#!/usr/bin/env python3
"""
Direct test script for FIRS sandbox API connectivity.
This script tests connection to the FIRS sandbox without complex dependencies.
"""
import os
import requests
import json
import base64
import uuid
from datetime import datetime
from pathlib import Path

# FIRS API credentials and crypto paths
# Updated with the latest sandbox environment information (May 2025)
FIRS_USE_SANDBOX = True
FIRS_API_BASE_URL = "https://eivc-k6z6d.ondigitalocean.app" # Updated sandbox URL
FIRS_API_KEY = "36dc0109-5fab-4433-80c3-84d9cef792a2"
FIRS_API_SECRET = "mHtXX9UBq3qnvgJFkIIEjQLlxjXKS1yECpqmTWa1AuCzRg5sJNOpxDefCYds18WNma3zUUgt1ccIUOgNtBb4wk8s4MshQl8OxhQA"
FIRS_PUBLIC_KEY_PATH = "/home/mukhtar-tanimu/taxpoynt-eInvoice/backend/crypto/firs_public_key.pem"
FIRS_CERTIFICATE_PATH = "/home/mukhtar-tanimu/taxpoynt-eInvoice/backend/crypto/firs_certificate.txt"

# API Endpoints updated from the FIRS-MBS E-Invoicing Documentation (May 2025)
API_ENDPOINT_HEALTH_CHECK = "/api"

# Entity and Party Management Endpoints
API_ENDPOINT_BUSINESS_SEARCH = "/api/v1/entity"
API_ENDPOINT_BUSINESS_BY_ID = "/api/v1/entity/{ENTITY_ID}"
API_ENDPOINT_CREATE_PARTY = "/api/v1/invoice/party"
API_ENDPOINT_GET_PARTY = "/api/v1/invoice/party/{BUSINESS_ID}"

# Invoice Management Endpoints
API_ENDPOINT_IRN_VALIDATE = "/api/v1/invoice/irn/validate"
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
        
def get_business_id():
    """Return a proper UUID4 format business ID for FIRS API.
    
    FIRS API requires valid UUID4 format, not TIN format.
    In production, this would be the UUID4 assigned to your business
    during FIRS registration.
    """
    # Generate a valid UUID4 as required by FIRS API
    # In production, this would be a stored UUID4 associated with your TIN
    return str(uuid.uuid4())

def get_tin():
    """Return the user's TIN for use in appropriate fields."""
    return "31569955-0001"

def prepare_irn_validation_payload():
    """Prepare payload for IRN validation based on the FIRS-MBS E-Invoicing Documentation.
    
    According to the latest documentation, IRN validation requires a standard JSON payload
    with business_id, invoice_reference, and irn.
    """
    try:
        # Create a dictionary with required fields from documentation
        # Using the TIN for business_id as specified by the user
        business_id = get_business_id()
        payload = {
            "business_id": business_id,
            "invoice_reference": "INV001",
            "irn": "INV001-F3A3A0CF-20240619"
        }
        
        print(f"Using business_id UUID4: {business_id} (associated with TIN {get_tin()})")
        return payload
    except Exception as e:
        print(f"Error preparing IRN validation payload: {str(e)}")
        return None

def main():
    print("=" * 60)
    print("FIRS API Direct Integration Test")
    print("=" * 60)
    print("Using TaxPoynt eInvoice Odoo Integration Framework")
    print(f"FIRS Sandbox Mode: {FIRS_USE_SANDBOX}")
    print("=" * 60)
    
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
        # Use the TIN for business_id as specified by the user
        business_id = get_business_id()
        business_url = f"{FIRS_API_BASE_URL}/api/v1/invoice/party/{business_id}"
        print(f"Connecting to: {business_url}")
        print(f"Using business_id: {business_id} (TIN)")
        
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
        
        # Try with user's TIN as business ID
        try:
            print("\nTrying with user's TIN as business ID...")
            business_id = get_business_id()
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
    
    # Test 5: IRN Validation with Updated Request Format
    print("\n[5/5] Testing IRN Validation with Updated Request Format...")
    try:
        # Prepare IRN validation payload based on latest API docs
        irn_payload = prepare_irn_validation_payload()
        
        if irn_payload:
            print("✅ Successfully prepared IRN validation payload")
            print(f"   Sample payload: {json.dumps(irn_payload, indent=2)}")
            
            # Use the IRN validation endpoint
            irn_validate_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_IRN_VALIDATE}"
            print(f"Connecting to: {irn_validate_url}")
            print("Sending IRN validation request...")
            
            irn_response = requests.post(
                irn_validate_url,
                headers=get_headers(),
                json=irn_payload,
                timeout=10
            )
            
            print(f"IRN Validation response: Status {irn_response.status_code}")
            if irn_response.status_code in [200, 201]:
                print("✅ IRN Validation successful")
                print(f"Response: {irn_response.text[:200]}")
                
                # Save the response for reference
                with open("irn_validation_response.json", "w") as f:
                    try:
                        json.dump(irn_response.json(), f, indent=2)
                        print("   Response saved to irn_validation_response.json")
                    except:
                        f.write(irn_response.text)
                        print("   Raw response saved to irn_validation_response.json")
            else:
                print(f"⚠️ IRN Validation returned status: {irn_response.status_code}")
                print(f"Response: {irn_response.text[:200]}")
        else:
            print("❌ Failed to prepare IRN validation payload")
    except Exception as e:
        print(f"❌ IRN Validation test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    # Test 6: Test Invoice Validation Endpoint
    print("\n[+] BONUS: Testing Invoice Validation Endpoint...")
    try:
        # Use the TIN for business_id as specified by the user
        business_id = get_business_id()
        
        # Prepare a properly formatted invoice validation payload based on FIRS-MBS documentation
        current_date = datetime.now().strftime("%Y-%m-%d")
        validation_payload = {
            "business_id": business_id,
            "irn": "ITW006-F3A3A0CF-20240703",
            "issue_date": current_date,
            "invoice_type_code": "396",
            "document_currency_code": "NGN",
            "accounting_supplier_party": {
                "party_name": "Test Supplier",
                "tin": get_tin(),  # Use actual TIN here,
                "email": "supplier@example.com",
                "postal_address": {
                    "street_name": "123 Test Street",
                    "city_name": "Lagos",
                    "postal_zone": "100001",
                    "country": "NG"
                }
            },
            "accounting_customer_party": {
                "party_name": "Test Customer",
                "tin": get_tin(),  # Use actual TIN here,
                "email": "customer@example.com",
                "postal_address": {
                    "street_name": "456 Test Avenue",
                    "city_name": "Abuja",
                    "postal_zone": "900001",
                    "country": "NG"
                }
            },
            "invoice_line": [
                {
                    "id": "1",
                    "invoiced_quantity": 2,
                    "line_extension_amount": 100.00,
                    "item": {
                        "name": "Test Product",
                        "description": "Test product description"
                    },
                    "price": {
                        "price_amount": 50.00
                    },
                    "tax_total": {
                        "tax_amount": 7.50
                    }
                }
            ],
            "tax_total": {
                "tax_amount": 7.50
            },
            "monetary_total": {
                "line_extension_amount": 100.00,
                "tax_exclusive_amount": 100.00,
                "tax_inclusive_amount": 107.50,
                "payable_amount": 107.50
            }
        }
        
        validation_url = f"{FIRS_API_BASE_URL}{API_ENDPOINT_INVOICE_VALIDATE}"
        print(f"Connecting to: {validation_url}")
        print(f"Using business_id: {business_id} (TIN)")
        print("Sending test invoice validation request...")
        
        validation_response = requests.post(
            validation_url,
            headers=get_headers(),
            json=validation_payload,
            timeout=15
        )
        
        print(f"Invoice Validation response: Status {validation_response.status_code}")
        if validation_response.status_code in [200, 201, 202]:
            print("✅ Invoice Validation API accessible")
            print(f"Response: {validation_response.text[:200]}")
            # Save the response for reference
            with open("invoice_validation_response.json", "w") as f:
                try:
                    json.dump(validation_response.json(), f, indent=2)
                    print("   Response saved to invoice_validation_response.json")
                except:
                    f.write(validation_response.text)
                    print("   Raw response saved to invoice_validation_response.json")
        else:
            print(f"⚠️ Invoice Validation returned status: {validation_response.status_code}")
            print(f"Response: {validation_response.text[:200]}")
    except Exception as e:
        print(f"❌ Invoice Validation test failed: {str(e)}")
    
    print("\n==== FIRS Sandbox API Tests Completed")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    print("\nNext Steps:")
    print("1. Review any errors from the tests above")
    print("2. Ensure all business IDs are valid UUIDs as required by the FIRS API")
    print("3. Validate invoice payloads against the complete FIRS-MBS E-Invoicing specifications")
    print("4. For production integration, update the sandbox flag to false and use production credentials")
    print("5. Integrate Odoo invoice data with proper field mapping for FIRS validation and signing")
    print("6. Implement proper error handling for different API response codes")
    print("7. Consider adding retry mechanisms for transient errors")

if __name__ == "__main__":
    main()
