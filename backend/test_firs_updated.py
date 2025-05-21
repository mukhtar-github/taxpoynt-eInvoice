#!/usr/bin/env python3
"""
Test script for the updated FIRS service implementation.

This script tests the key functionality of the updated FIRS service,
including authentication, IRN validation, reference data retrieval,
and invoice submission.
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4

# Add the backend directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.firs_service import FIRSService
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"test_firs_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("firs_test")

# Test configuration
TEST_CONFIG = {
    "use_sandbox": True,
    "test_tin": "12345678-1234",  # Replace with a valid test TIN
    "test_irn": "NG12345678901234567890123456789012345",  # Replace with a valid test IRN
    "test_invoice_reference": "INV-2025-001",  # Replace with a test invoice reference
    "test_business_id": "TAXPAYER-12345"  # Replace with a test business ID
}

# Sample invoice data for testing
SAMPLE_INVOICE = {
    "invoice_number": "INV-2025-001",
    "invoice_type": "standard",
    "invoice_date": datetime.now().strftime("%Y-%m-%d"),
    "currency_code": "NGN",
    "supplier": {
        "name": "Test Supplier Ltd",
        "tin": "12345678-1234",
        "address": {
            "street": "123 Supplier Street",
            "city": "Lagos",
            "state": "Lagos",
            "country": "NG"
        }
    },
    "customer": {
        "name": "Test Customer Ltd",
        "tin": "87654321-4321",
        "address": {
            "street": "456 Customer Road",
            "city": "Abuja",
            "state": "FCT",
            "country": "NG"
        }
    },
    "items": [
        {
            "description": "Test Product",
            "quantity": 1,
            "unit_price": 1000.00,
            "tax_rate": 7.5,
            "tax_amount": 75.00,
            "subtotal": 1000.00,
            "total": 1075.00
        }
    ],
    "totals": {
        "subtotal": 1000.00,
        "tax_total": 75.00,
        "discount_total": 0.00,
        "grand_total": 1075.00
    }
}

async def test_authentication(firs_service: FIRSService) -> bool:
    """Test FIRS authentication"""
    logger.info("=== Testing FIRS Authentication ===")
    
    if not settings.FIRS_TEST_EMAIL or not settings.FIRS_TEST_PASSWORD:
        logger.warning("Test credentials not configured. Skipping authentication test.")
        return False
    
    try:
        auth_response = await firs_service.authenticate(
            settings.FIRS_TEST_EMAIL, 
            settings.FIRS_TEST_PASSWORD
        )
        
        if auth_response and auth_response.status == "success":
            logger.info(f"Authentication successful for user: {auth_response.data.user.name}")
            return True
        else:
            logger.error("Authentication failed")
            return False
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return False

async def test_irn_validation(firs_service: FIRSService) -> bool:
    """Test IRN validation"""
    logger.info("=== Testing IRN Validation ===")
    
    try:
        # Test with a known IRN
        validation_result = await firs_service.validate_irn(
            invoice_reference=TEST_CONFIG["test_invoice_reference"],
            business_id=TEST_CONFIG["test_business_id"],
            irn_value=TEST_CONFIG["test_irn"]
        )
        
        logger.info(f"IRN Validation result: {json.dumps(validation_result, indent=2)}")
        return validation_result.get("success", False)
    except Exception as e:
        logger.error(f"IRN validation error: {str(e)}")
        return False

async def test_reference_data(firs_service: FIRSService) -> bool:
    """Test reference data retrieval"""
    logger.info("=== Testing Reference Data Retrieval ===")
    
    try:
        # Test currency retrieval
        currencies = await firs_service.get_currencies()
        logger.info(f"Retrieved {len(currencies)} currencies")
        
        # Test invoice types retrieval
        invoice_types = await firs_service.get_invoice_types()
        logger.info(f"Retrieved {len(invoice_types)} invoice types")
        
        # Test VAT exemptions retrieval
        vat_exemptions = await firs_service.get_vat_exemptions()
        logger.info(f"Retrieved {len(vat_exemptions)} VAT exemptions")
        
        # If we retrieved data from all endpoints, consider the test successful
        return len(currencies) > 0 and len(invoice_types) > 0 and len(vat_exemptions) > 0
    except Exception as e:
        logger.error(f"Reference data retrieval error: {str(e)}")
        return False

async def test_invoice_submission(firs_service: FIRSService) -> bool:
    """Test invoice submission"""
    logger.info("=== Testing Invoice Submission ===")
    
    try:
        # Create a test invoice with a unique number
        test_invoice = SAMPLE_INVOICE.copy()
        test_invoice["invoice_number"] = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Submit the invoice
        logger.info(f"Submitting test invoice: {test_invoice['invoice_number']}")
        submission_result = await firs_service.submit_invoice(test_invoice)
        
        logger.info(f"Submission result: {submission_result.dict()}")
        return submission_result.success
    except Exception as e:
        logger.error(f"Invoice submission error: {str(e)}")
        return False

async def test_batch_submission(firs_service: FIRSService) -> bool:
    """Test batch invoice submission"""
    logger.info("=== Testing Batch Invoice Submission ===")
    
    try:
        # Create multiple test invoices
        test_invoices = []
        for i in range(3):
            invoice = SAMPLE_INVOICE.copy()
            invoice["invoice_number"] = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i+1}"
            test_invoices.append(invoice)
        
        # Submit the batch
        logger.info(f"Submitting batch of {len(test_invoices)} invoices")
        batch_result = await firs_service.submit_invoices_batch(test_invoices)
        
        logger.info(f"Batch submission result: {batch_result.dict()}")
        return batch_result.success
    except Exception as e:
        logger.error(f"Batch submission error: {str(e)}")
        return False

async def main():
    """Main test function"""
    logger.info("Starting FIRS service tests")
    
    # Initialize the FIRS service
    firs_service = FIRSService(use_sandbox=TEST_CONFIG["use_sandbox"])
    logger.info(f"Initialized FIRS service in {'SANDBOX' if TEST_CONFIG['use_sandbox'] else 'PRODUCTION'} mode")
    
    # Run the tests
    test_results = {
        "authentication": await test_authentication(firs_service),
        "irn_validation": await test_irn_validation(firs_service),
        "reference_data": await test_reference_data(firs_service),
        "invoice_submission": await test_invoice_submission(firs_service),
        "batch_submission": await test_batch_submission(firs_service)
    }
    
    # Print test summary
    logger.info("=== FIRS Service Test Summary ===")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name.ljust(20)}: {status}")
    
    overall_success = all(test_results.values())
    logger.info(f"Overall Test Result: {'SUCCESS' if overall_success else 'FAILURE'}")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())
