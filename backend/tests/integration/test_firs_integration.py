"""
FIRS API Sandbox Integration Tests.

This module contains tests for validating the integration between
the TaxPoynt eInvoice system and the FIRS API sandbox environment.
"""
import os
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List

# Load environment variables from .env file for testing
load_dotenv()

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import application components
from app.services.firs_service import FIRSService
from app.services.odoo_ubl_transformer import odoo_ubl_transformer
from app.schemas.invoice_validation import InvoiceValidationRequest

# Mock data path
MOCK_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "mock_data")


def load_mock_data(filename: str) -> Dict[str, Any]:
    """Load mock data from JSON file."""
    file_path = os.path.join(MOCK_DATA_DIR, filename)
    with open(file_path, 'r') as f:
        return json.load(f)


@pytest.fixture(scope="module")
def sample_odoo_invoice() -> Dict[str, Any]:
    """Load a sample Odoo invoice for testing."""
    try:
        return load_mock_data("odoo_invoice_sample.json")
    except FileNotFoundError:
        # Create a minimal test invoice if the file doesn't exist
        logger.warning("Sample Odoo invoice file not found. Using minimal test data.")
        return {
            "id": 12345,
            "name": "INV/2025/00001",
            "invoice_date": "2025-05-21",
            "currency_id": {"id": 1, "name": "NGN"},
            "amount_total": 1000.00,
            "amount_untaxed": 900.00,
            "amount_tax": 100.00,
            "partner_id": {
                "id": 1,
                "name": "Test Customer",
                "vat": "12345678901",
                "street": "Test Street",
                "city": "Test City"
            },
            "company_id": {
                "id": 1,
                "name": "Test Company",
                "vat": "98765432109",
            },
            "invoice_line_ids": [
                {
                    "id": 1,
                    "name": "Test Product",
                    "quantity": 1.0,
                    "price_unit": 900.00,
                    "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
                    "price_subtotal": 900.00,
                    "price_total": 1000.00
                }
            ]
        }


@pytest.fixture(scope="module")
def company_info() -> Dict[str, Any]:
    """Provide company info for testing."""
    try:
        return load_mock_data("company_info_sample.json")
    except FileNotFoundError:
        # Create minimal company info if the file doesn't exist
        logger.warning("Sample company info file not found. Using minimal test data.")
        return {
            "id": 1,
            "name": "Test Company Ltd",
            "vat": "98765432109",
            "street": "123 Company Street",
            "city": "Lagos",
            "state_id": {"id": 1, "name": "Lagos"},
            "country_id": {"id": 1, "name": "Nigeria"},
            "phone": "+234 1234567890",
            "email": "info@testcompany.com",
            "website": "https://testcompany.com",
            "company_registry": "RC123456",
            "currency_id": {"id": 1, "name": "NGN"}
        }


@pytest.fixture(scope="module")
def firs_service() -> FIRSService:
    """Create a FIRS service instance for testing."""
    # Always use sandbox mode for integration tests
    from app.core.config import settings
    
    # If running in CI/CD, use environment variables over settings
    api_key = os.getenv("FIRS_SANDBOX_API_KEY", settings.FIRS_SANDBOX_API_KEY)
    api_secret = os.getenv("FIRS_SANDBOX_API_SECRET", settings.FIRS_SANDBOX_API_SECRET)
    api_url = os.getenv("FIRS_SANDBOX_API_URL", settings.FIRS_SANDBOX_API_URL)
    
    service = FIRSService(
        use_sandbox=True,
        base_url=api_url,
        api_key=api_key,
        api_secret=api_secret
    )
    return service


@pytest.mark.asyncio
async def test_auth_sandbox(firs_service):
    """Test authentication with the FIRS sandbox environment."""
    # Use test credentials for sandbox
    email = os.getenv("FIRS_SANDBOX_TEST_EMAIL", "test@example.com")
    password = os.getenv("FIRS_SANDBOX_TEST_PASSWORD", "TestPassword123")
    
    try:
        # Attempt to authenticate
        auth_response = await firs_service.authenticate(email, password)
        
        # Check if authentication was successful
        assert auth_response.success, f"Authentication failed: {auth_response.message}"
        assert auth_response.token, "No token received in successful authentication"
        
        # Verify token is set in the service
        assert firs_service.token, "Token not set in service after successful authentication"
        
        # Check token expiry
        now = datetime.now()
        assert firs_service.token_expiry > now, "Token expiry is in the past"
        
        logger.info("Sandbox authentication successful")
        
    except Exception as e:
        pytest.fail(f"Authentication test failed with exception: {str(e)}")


@pytest.mark.asyncio
async def test_odoo_to_ubl_transformation(sample_odoo_invoice, company_info):
    """Test transformation from Odoo invoice to UBL format."""
    try:
        # Transform the invoice
        ubl_invoice, validation_issues = odoo_ubl_transformer.odoo_to_ubl_object(
            sample_odoo_invoice, 
            company_info
        )
        
        # Check transformation result
        assert ubl_invoice is not None, f"Transformation failed with issues: {validation_issues}"
        
        # Validate basic structure
        assert isinstance(ubl_invoice, InvoiceValidationRequest), "Result is not an InvoiceValidationRequest instance"
        
        # Validate required fields
        required_fields = [
            'business_id', 'irn', 'issue_date', 'invoice_type_code', 
            'document_currency_code', 'accounting_supplier_party', 
            'accounting_customer_party', 'legal_monetary_total', 'invoice_line'
        ]
        
        for field in required_fields:
            assert hasattr(ubl_invoice, field), f"Required field {field} is missing from the UBL invoice"
            assert getattr(ubl_invoice, field) is not None, f"Required field {field} is None in the UBL invoice"
        
        # If there are validation issues, log them but don't fail the test
        if validation_issues:
            logger.warning(f"Transformation completed with {len(validation_issues)} validation issues:")
            for issue in validation_issues:
                logger.warning(f"  - {issue['field']}: {issue['message']}")
        
        logger.info("Odoo to UBL transformation successful")
        
        return ubl_invoice
        
    except Exception as e:
        pytest.fail(f"Transformation test failed with exception: {str(e)}")


@pytest.mark.asyncio
async def test_invoice_submission(firs_service, sample_odoo_invoice, company_info):
    """Test submitting an invoice to the FIRS sandbox environment."""
    try:
        # First, authenticate
        await test_auth_sandbox(firs_service)
        
        # Then transform the invoice
        ubl_invoice = await test_odoo_to_ubl_transformation(sample_odoo_invoice, company_info)
        
        # Now submit the transformed invoice
        submission_response = await firs_service.submit_invoice(ubl_invoice.dict())
        
        # Check submission result
        assert submission_response.success, f"Submission failed: {submission_response.message}"
        assert submission_response.submission_id, "No submission ID received in successful submission"
        
        logger.info(f"Invoice submission successful. Submission ID: {submission_response.submission_id}")
        
        # Return submission ID for status check test
        return submission_response.submission_id
        
    except Exception as e:
        pytest.fail(f"Submission test failed with exception: {str(e)}")


@pytest.mark.asyncio
async def test_check_submission_status(firs_service):
    """Test checking the status of a submitted invoice."""
    try:
        # First submit an invoice to get a submission ID
        submission_id = await test_invoice_submission(firs_service, 
                                                     await sample_odoo_invoice(), 
                                                     await company_info())
        
        # Wait a short time for processing
        await asyncio.sleep(2)
        
        # Check status
        status_response = await firs_service.check_submission_status(submission_id)
        
        # Verify response structure
        assert status_response.submission_id == submission_id, "Submission ID mismatch in status response"
        assert status_response.status, "No status received in status response"
        
        logger.info(f"Status check successful. Current status: {status_response.status}")
        
    except Exception as e:
        pytest.fail(f"Status check test failed with exception: {str(e)}")


# Main test execution for manual running
if __name__ == "__main__":
    asyncio.run(test_auth_sandbox(firs_service()))
    print("Authentication test completed")
    
    odoo_invoice = sample_odoo_invoice()
    company = company_info()
    asyncio.run(test_odoo_to_ubl_transformation(odoo_invoice, company))
    print("Transformation test completed")
    
    service = firs_service()
    asyncio.run(test_invoice_submission(service, odoo_invoice, company))
    print("Submission test completed")
    
    asyncio.run(test_check_submission_status(service))
    print("Status check test completed")
