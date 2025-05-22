#!/usr/bin/env python3
"""
Comprehensive test script for FIRS API integration.

This script tests all implemented FIRS API endpoints against the sandbox environment.
It validates the correct functioning of authentication, entity management, invoice operations,
and reference data retrieval.

Usage:
    python test_firs_api_integration.py

Requirements:
    - Python 3.8+
    - Environment variables for FIRS_SANDBOX_API_URL, FIRS_SANDBOX_API_KEY, FIRS_SANDBOX_API_SECRET
    - Test user credentials in environment variables (FIRS_TEST_EMAIL, FIRS_TEST_PASSWORD)
    - Valid test TIN (31569955-0001)
"""

import os
import sys
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variables needed to bypass database requirements
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
os.environ["ODOO_API_URL"] = "http://example.com"
os.environ["ODOO_DB"] = "test_db"
os.environ["ODOO_USERNAME"] = "test_user"
os.environ["ODOO_API_KEY"] = "test_key"

# Import the FIRS service
from app.services.firs_service import FIRSService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("firs_api_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("firs_api_test")

# Load environment variables
load_dotenv()

# Test constants
TEST_TIN = "31569955-0001"
TEST_EMAIL = os.getenv("FIRS_TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("FIRS_TEST_PASSWORD", "password")
SANDBOX_API_URL = os.getenv("FIRS_SANDBOX_API_URL", "https://eivc-k6z6d.ondigitalocean.app")
SANDBOX_API_KEY = os.getenv("FIRS_SANDBOX_API_KEY", "")
SANDBOX_API_SECRET = os.getenv("FIRS_SANDBOX_API_SECRET", "")

# Initialize the FIRS service with sandbox configuration
firs_service = FIRSService(
    base_url=SANDBOX_API_URL,
    api_key=SANDBOX_API_KEY,
    api_secret=SANDBOX_API_SECRET,
    use_sandbox=True
)

# Test status tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "total": 0
}

def log_test_result(test_name: str, passed: bool, error: Optional[Exception] = None, skipped: bool = False):
    """Log the result of a test and update test statistics."""
    test_results["total"] += 1
    
    if skipped:
        test_results["skipped"] += 1
        logger.warning(f"TEST SKIPPED: {test_name}")
        return
        
    if passed:
        test_results["passed"] += 1
        logger.info(f"TEST PASSED: {test_name}")
    else:
        test_results["failed"] += 1
        error_message = str(error) if error else "Unknown error"
        logger.error(f"TEST FAILED: {test_name} - {error_message}")


async def test_health_check():
    """Test the health check endpoint."""
    test_name = "Health Check"
    try:
        result = await firs_service.check_health()
        passed = result.get("healthy") is True
        log_test_result(test_name, passed)
        return passed
    except Exception as e:
        log_test_result(test_name, False, e)
        return False


async def test_authentication():
    """Test authentication with the FIRS API."""
    test_name = "Authentication"
    try:
        result = await firs_service.authenticate(TEST_EMAIL, TEST_PASSWORD)
        passed = result.data.access_token is not None and result.data.user is not None
        log_test_result(test_name, passed)
        return passed
    except Exception as e:
        log_test_result(test_name, False, e)
        return False


async def test_reference_data():
    """Test fetching reference data (countries, currencies, etc.)."""
    # Test countries
    try:
        countries = await firs_service.get_countries()
        passed_countries = len(countries) > 0
        log_test_result("Get Countries", passed_countries)
    except Exception as e:
        log_test_result("Get Countries", False, e)
        passed_countries = False
        
    # Test currencies
    try:
        currencies = await firs_service.get_currencies()
        passed_currencies = len(currencies) > 0
        log_test_result("Get Currencies", passed_currencies)
    except Exception as e:
        log_test_result("Get Currencies", False, e)
        passed_currencies = False
        
    # Test invoice types
    try:
        invoice_types = await firs_service.get_invoice_types()
        passed_invoice_types = len(invoice_types) > 0
        log_test_result("Get Invoice Types", passed_invoice_types)
    except Exception as e:
        log_test_result("Get Invoice Types", False, e)
        passed_invoice_types = False
        
    # Test VAT exemptions
    try:
        vat_exemptions = await firs_service.get_vat_exemptions()
        passed_vat_exemptions = len(vat_exemptions) > 0
        log_test_result("Get VAT Exemptions", passed_vat_exemptions)
    except Exception as e:
        log_test_result("Get VAT Exemptions", False, e)
        passed_vat_exemptions = False
        
    return passed_countries and passed_currencies and passed_invoice_types and passed_vat_exemptions


async def test_entity_operations():
    """Test entity search and retrieval operations."""
    # Test entity search
    try:
        search_params = {
            "size": 5,
            "page": 1,
            "sort_by": "created_at",
            "sort_direction_desc": "true"
        }
        search_results = await firs_service.search_entities(search_params)
        passed_search = isinstance(search_results, dict) and "data" in search_results
        log_test_result("Entity Search", passed_search)
        
        # If we found any entities, test getting one by ID
        if passed_search and search_results.get("data", {}).get("items", []):
            entity_id = search_results["data"]["items"][0]["id"]
            entity = await firs_service.get_entity(entity_id)
            passed_get = entity is not None and "id" in entity
            log_test_result("Get Entity by ID", passed_get)
        else:
            log_test_result("Get Entity by ID", False, skipped=True)
            passed_get = True  # Skip this test if no entities found
        
        return passed_search and passed_get
    except Exception as e:
        log_test_result("Entity Operations", False, e)
        return False


async def test_party_operations():
    """Test party creation and retrieval."""
    # Test party creation
    try:
        party_data = {
            "business_id": os.getenv("FIRS_TEST_BUSINESS_ID", "test-business-id"),
            "party_name": f"Test Party {datetime.now().strftime('%Y%m%d%H%M%S')}",
            "tin": TEST_TIN,
            "email": "test.party@example.com",
            "telephone": "+2348012345678",
            "business_description": "Test party for API validation",
            "postal_address": {
                "street_name": "123 Test Street",
                "city_name": "Lagos",
                "postal_zone": "100001",
                "country": "NG"
            }
        }
        
        create_result = await firs_service.create_party(party_data)
        passed_create = isinstance(create_result, dict) and "id" in create_result
        log_test_result("Create Party", passed_create)
        
        # Test party retrieval if creation succeeded
        if passed_create:
            party_id = create_result["id"]
            party = await firs_service.get_party(party_id)
            passed_get = party is not None and party.get("id") == party_id
            log_test_result("Get Party by ID", passed_get)
        else:
            log_test_result("Get Party by ID", False, skipped=True)
            passed_get = True  # Skip this test if creation failed
            
        return passed_create and passed_get
    except Exception as e:
        log_test_result("Party Operations", False, e)
        return False


async def test_irn_validation():
    """Test IRN validation."""
    test_name = "IRN Validation"
    try:
        # Generate a test IRN
        invoice_reference = f"TST{datetime.now().strftime('%y%m%d%H%M')}"
        irn = f"{invoice_reference}-ABCDEF12-{datetime.now().strftime('%Y%m%d')}"
        business_id = os.getenv("FIRS_TEST_BUSINESS_ID", "test-business-id")
        
        result = await firs_service.validate_irn(business_id, irn, invoice_reference)
        passed = isinstance(result, dict)
        log_test_result(test_name, passed)
        return passed
    except Exception as e:
        log_test_result(test_name, False, e)
        return False


async def test_invoice_operations():
    """Test invoice validation, signing, and other operations."""
    # Create a test invoice - must match BIS Billing 3.0 UBL format
    now = datetime.now()
    invoice_reference = f"TST{now.strftime('%y%m%d%H%M')}"
    irn = f"{invoice_reference}-ABCDEF12-{now.strftime('%Y%m%d')}"
    business_id = os.getenv("FIRS_TEST_BUSINESS_ID", "test-business-id")
    
    invoice_data = {
        "business_id": business_id,
        "irn": irn,
        "issue_date": now.strftime("%Y-%m-%d"),
        "due_date": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
        "issue_time": now.strftime("%H:%M:%S"),
        "invoice_type_code": "380",  # Commercial Invoice
        "profile_id": "urn:firs.gov.ng:einvoicing:01:01",
        "payment_status": "PENDING",
        "document_currency_code": "NGN",
        "tax_currency_code": "NGN",
        "accounting_supplier_party": {
            "party_name": "Test Supplier",
            "tin": TEST_TIN,
            "email": "supplier@example.com",
            "telephone": "+2348012345678",
            "business_description": "Test supplier for API validation",
            "postal_address": {
                "street_name": "123 Supplier Street",
                "additional_street_name": "Building A",
                "city_name": "Lagos",
                "postal_zone": "100001",
                "country": "NG"
            }
        },
        "accounting_customer_party": {
            "party_name": "Test Customer",
            "tin": TEST_TIN,
            "email": "customer@example.com",
            "telephone": "+2348087654321",
            "business_description": "Test customer for API validation",
            "postal_address": {
                "street_name": "456 Customer Avenue",
                "city_name": "Abuja",
                "postal_zone": "900001",
                "country": "NG"
            }
        },
        "delivery": {
            "actual_delivery_date": now.strftime("%Y-%m-%d"),
            "delivery_location": {
                "address": {
                    "street_name": "456 Customer Avenue",
                    "city_name": "Abuja",
                    "postal_zone": "900001",
                    "country": "NG"
                }
            }
        },
        "payment_means": [
            {
                "payment_means_code": "30",  # Credit transfer
                "payment_due_date": (now + timedelta(days=30)).strftime("%Y-%m-%d")
            }
        ],
        "tax_total": [
            {
                "tax_amount": 150.00,
                "tax_subtotal": [
                    {
                        "taxable_amount": 1000.00,
                        "tax_amount": 150.00,
                        "tax_category": {
                            "id": "VAT",
                            "percent": 15.0,
                            "tax_scheme": {
                                "id": "FIRS"
                            }
                        }
                    }
                ]
            }
        ],
        "legal_monetary_total": {
            "line_extension_amount": 1000.00,
            "tax_exclusive_amount": 1000.00,
            "tax_inclusive_amount": 1150.00,
            "payable_amount": 1150.00
        },
        "invoice_line": [
            {
                "id": "LINE-1",
                "invoiced_quantity": 1,
                "invoiced_quantity_unit_code": "EA",
                "line_extension_amount": 1000.00,
                "item": {
                    "name": "Test Product",
                    "description": "Product for testing",
                    "sellers_item_identification": {
                        "id": "TP001"
                    },
                    "commodity_classification": [
                        {
                            "item_classification_code": {
                                "value": "TEST-001",
                                "list_id": "UNSPSC"
                            }
                        }
                    ]
                },
                "price": {
                    "price_amount": 1000.00,
                    "base_quantity": 1,
                    "base_quantity_unit_code": "EA"
                },
                "tax_total": {
                    "tax_amount": 150.00,
                    "tax_subtotal": {
                        "taxable_amount": 1000.00,
                        "tax_amount": 150.00,
                        "tax_category": {
                            "id": "VAT",
                            "percent": 15.0,
                            "tax_scheme": {
                                "id": "FIRS"
                            }
                        }
                    }
                }
            }
        ]
    }
    
    # Test invoice validation
    try:
        validation_result = await firs_service.validate_invoice(invoice_data)
        passed_validation = isinstance(validation_result, dict) and validation_result.get("data", {}).get("valid") is True
        log_test_result("Invoice Validation", passed_validation)
    except Exception as e:
        log_test_result("Invoice Validation", False, e)
        passed_validation = False
    
    # Test invoice signing if validation passed
    if passed_validation:
        try:
            signing_result = await firs_service.sign_invoice(invoice_data)
            passed_signing = isinstance(signing_result, dict) and "csid" in signing_result.get("data", {})
            log_test_result("Invoice Signing", passed_signing)
            
            # Store the IRN for subsequent tests
            if passed_signing:
                signed_irn = signing_result["data"]["irn"]
            else:
                signed_irn = None
        except Exception as e:
            log_test_result("Invoice Signing", False, e)
            passed_signing = False
            signed_irn = None
    else:
        log_test_result("Invoice Signing", False, skipped=True)
        passed_signing = True  # Skip this test if validation failed
        signed_irn = None
    
    # Test invoice download if signing succeeded
    if signed_irn:
        try:
            download_result = await firs_service.download_invoice(signed_irn)
            passed_download = isinstance(download_result, dict) and "pdf_content" in download_result.get("data", {})
            log_test_result("Invoice Download", passed_download)
        except Exception as e:
            log_test_result("Invoice Download", False, e)
            passed_download = False
    else:
        log_test_result("Invoice Download", False, skipped=True)
        passed_download = True  # Skip this test if signing failed
    
    # Test invoice confirmation if signing succeeded
    if signed_irn:
        try:
            confirm_result = await firs_service.confirm_invoice(signed_irn)
            passed_confirm = isinstance(confirm_result, dict) and confirm_result.get("data", {}).get("status") == "CONFIRMED"
            log_test_result("Invoice Confirmation", passed_confirm)
        except Exception as e:
            log_test_result("Invoice Confirmation", False, e)
            passed_confirm = False
    else:
        log_test_result("Invoice Confirmation", False, skipped=True)
        passed_confirm = True  # Skip this test if signing failed
    
    # Test invoice search
    try:
        search_params = {
            "size": 5,
            "page": 1,
            "sort_by": "created_at",
            "sort_direction_desc": "true"
        }
        search_results = await firs_service.search_invoices(business_id, search_params)
        passed_search = isinstance(search_results, dict) and "data" in search_results
        log_test_result("Invoice Search", passed_search)
    except Exception as e:
        log_test_result("Invoice Search", False, e)
        passed_search = False
    
    # Combine all results
    return all([passed_validation, passed_signing, passed_download, passed_confirm, passed_search])


async def run_tests():
    """Run all tests in the correct order."""
    logger.info("Starting FIRS API integration tests...")
    
    # Start with health check
    health_check_passed = await test_health_check()
    if not health_check_passed:
        logger.error("Health check failed. Aborting further tests.")
        return False
    
    # Test authentication
    auth_passed = await test_authentication()
    if not auth_passed:
        logger.error("Authentication failed. Aborting further tests.")
        return False
    
    # Run independent tests
    reference_data_passed = await test_reference_data()
    entity_operations_passed = await test_entity_operations()
    party_operations_passed = await test_party_operations()
    irn_validation_passed = await test_irn_validation()
    invoice_operations_passed = await test_invoice_operations()
    
    # Print summary
    logger.info("\n----- TEST SUMMARY -----")
    logger.info(f"Total tests: {test_results['total']}")
    logger.info(f"Passed: {test_results['passed']}")
    logger.info(f"Failed: {test_results['failed']}")
    logger.info(f"Skipped: {test_results['skipped']}")
    logger.info("-----------------------")
    
    return test_results["failed"] == 0


if __name__ == "__main__":
    # Run all tests
    if asyncio.run(run_tests()):
        logger.info("All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("Some tests failed. Check the logs for details.")
        sys.exit(1)
