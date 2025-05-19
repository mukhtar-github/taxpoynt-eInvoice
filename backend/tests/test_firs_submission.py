"""Test suite for FIRS submission functionality.

This module contains unit tests for the FIRS submission implementation,
including authentication, invoice submission, batch submission, UBL submission,
and submission status checking.

Note: When running this test directly, ensure your environment has the required
dependencies and the PYTHONPATH includes the backend directory.
"""

import unittest
import asyncio
import json
import os
import sys
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi import HTTPException
from uuid import uuid4

from app.services.firs_service import (
    firs_service,
    InvoiceSubmissionResponse,
    SubmissionStatus,
)


class MockResponse:
    """Mock response object for requests."""
    
    def __init__(self, status_code, json_data, content=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.content = content or json.dumps(json_data).encode()
        self.text = text
        
    def json(self):
        return self._json_data


class TestFIRSSubmission(unittest.TestCase):
    """Tests for FIRS submission functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset firs_service state
        firs_service.token = None
        firs_service.token_expiry = None
        firs_service.base_url = "https://test-api.firs.gov.ng"
        firs_service.api_key = "test_key"
        firs_service.api_secret = "test_secret"
        
        # Sample invoice data
        self.invoice_data = {
            "invoice_number": "INV-2025-0001",
            "issue_date": "2025-05-16",
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
                    "description": "Product A",
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
        
        # Sample UBL XML
        self.ubl_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" 
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:ID>INV-2025-0001</cbc:ID>
    <cbc:IssueDate>2025-05-16</cbc:IssueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <!-- Other UBL elements -->
</Invoice>
"""
    
    @patch('requests.post')
    def test_authenticate(self, mock_post):
        """Test authentication with FIRS API."""
        # Mock successful authentication
        mock_response = MockResponse(200, {
            "status": "success",
            "message": "Authentication successful",
            "data": {
                "access_token": "test_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "issued_at": datetime.now().isoformat(),
                "user": {
                    "id": "user123",
                    "email": "test@example.com",
                    "name": "Test User",
                    "role": "admin"
                }
            }
        })
        mock_post.return_value = mock_response
        
        # Run test
        result = asyncio.run(firs_service.authenticate("test@example.com", "password"))
        
        # Assertions
        self.assertEqual(result.status, "success")
        self.assertEqual(result.message, "Authentication successful")
        self.assertEqual(firs_service.token, "test_token")
        self.assertIsNotNone(firs_service.token_expiry)
        
        # Check request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["url"], "https://test-api.firs.gov.ng/api/v1/utilities/authenticate")
        self.assertEqual(kwargs["json"]["email"], "test@example.com")
        self.assertEqual(kwargs["json"]["password"], "password")
    
    @patch('requests.post')
    def test_authenticate_failure(self, mock_post):
        """Test authentication failure with FIRS API."""
        # Mock failed authentication
        mock_response = MockResponse(401, {
            "status": "error",
            "message": "Invalid credentials"
        }, text="Invalid credentials")
        mock_post.return_value = mock_response
        
        # Run test and check exception
        with self.assertRaises(HTTPException) as context:
            asyncio.run(firs_service.authenticate("wrong@example.com", "wrong_password"))
        
        # Check exception details
        self.assertEqual(context.exception.status_code, 401)
        self.assertTrue("FIRS API authentication failed" in context.exception.detail)
        
    @patch('app.services.firs_service.FIRSService._ensure_authenticated')
    @patch('requests.post')
    def test_submit_invoice(self, mock_post, mock_auth):
        """Test submitting a single invoice."""
        # Setup mocks
        mock_auth.return_value = AsyncMock()
        submission_id = str(uuid4())
        
        mock_response = MockResponse(200, {
            "status": "success",
            "message": "Invoice submitted successfully",
            "data": {
                "submission_id": submission_id,
                "status": "SUBMITTED",
                "received_at": datetime.now().isoformat()
            }
        })
        mock_post.return_value = mock_response
        
        # Run test
        result = asyncio.run(firs_service.submit_invoice(self.invoice_data))
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Invoice submitted successfully")
        self.assertEqual(result.submission_id, submission_id)
        self.assertEqual(result.status, "SUBMITTED")
        
        # Check request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["url"], "https://test-api.firs.gov.ng/api/v1/invoice/submit")
        self.assertEqual(kwargs["json"]["invoice_number"], "INV-2025-0001")
        self.assertTrue("metadata" in kwargs["json"])
    
    @patch('app.services.firs_service.FIRSService._ensure_authenticated')
    @patch('requests.post')
    def test_submit_invoice_failure(self, mock_post, mock_auth):
        """Test invoice submission failure."""
        # Setup mocks
        mock_auth.return_value = AsyncMock()
        
        mock_response = MockResponse(400, {
            "status": "error",
            "message": "Validation failed",
            "errors": [
                {"field": "tax_total", "message": "Tax total does not match sum of line tax amounts"}
            ]
        }, text="Validation failed")
        mock_post.return_value = mock_response
        
        # Run test
        result = asyncio.run(firs_service.submit_invoice(self.invoice_data))
        
        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Validation failed")
        self.assertIsNone(result.submission_id)
        self.assertIsNotNone(result.errors)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0]["field"], "tax_total")
    
    @patch('app.services.firs_service.FIRSService._ensure_authenticated')
    @patch('requests.post')
    def test_submit_invoices_batch(self, mock_post, mock_auth):
        """Test submitting a batch of invoices."""
        # Setup mocks
        mock_auth.return_value = AsyncMock()
        batch_id = str(uuid4())
        
        mock_response = MockResponse(200, {
            "status": "success",
            "message": "Batch submitted successfully",
            "data": {
                "batch_id": batch_id,
                "status": "BATCH_SUBMITTED",
                "invoice_count": 2,
                "received_at": datetime.now().isoformat()
            }
        })
        mock_post.return_value = mock_response
        
        # Create batch of invoices
        invoices = [self.invoice_data.copy(), self.invoice_data.copy()]
        invoices[1]["invoice_number"] = "INV-2025-0002"
        
        # Run test
        result = asyncio.run(firs_service.submit_invoices_batch(invoices))
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Batch submitted successfully")
        self.assertEqual(result.submission_id, batch_id)
        self.assertEqual(result.status, "BATCH_SUBMITTED")
        
        # Check request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["url"], "https://test-api.firs.gov.ng/api/v1/invoice/batch/submit")
        self.assertEqual(len(kwargs["json"]["invoices"]), 2)
        self.assertTrue("metadata" in kwargs["json"])
        
    @patch('app.services.firs_service.FIRSService._ensure_authenticated')
    @patch('requests.post')
    def test_submit_ubl_invoice(self, mock_post, mock_auth):
        """Test submitting a UBL XML invoice."""
        # Setup mocks
        mock_auth.return_value = AsyncMock()
        submission_id = str(uuid4())
        
        mock_response = MockResponse(200, {
            "status": "success",
            "message": "UBL invoice submitted successfully",
            "data": {
                "submission_id": submission_id,
                "status": "UBL_SUBMITTED",
                "received_at": datetime.now().isoformat()
            }
        })
        mock_post.return_value = mock_response
        
        # Run test
        result = asyncio.run(firs_service.submit_ubl_invoice(self.ubl_xml, "standard"))
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "UBL invoice submitted successfully")
        self.assertEqual(result.submission_id, submission_id)
        self.assertEqual(result.status, "UBL_SUBMITTED")
        
        # Check request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["url"], "https://test-api.firs.gov.ng/api/v1/invoice/ubl/submit")
        self.assertEqual(kwargs["data"], self.ubl_xml)
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/xml")
        self.assertEqual(kwargs["headers"]["X-FIRS-InvoiceType"], "380")
        self.assertEqual(kwargs["headers"]["X-FIRS-Format"], "UBL2.1")
        self.assertEqual(kwargs["headers"]["X-FIRS-Profile"], "BIS3.0")
    
    @patch('app.services.firs_service.FIRSService._ensure_authenticated')
    @patch('requests.get')
    def test_check_submission_status(self, mock_get, mock_auth):
        """Test checking submission status."""
        # Setup mocks
        mock_auth.return_value = AsyncMock()
        submission_id = str(uuid4())
        
        mock_response = MockResponse(200, {
            "status": "success",
            "message": "Status retrieved successfully",
            "data": {
                "submission_id": submission_id,
                "status": "PROCESSING",
                "updated_at": datetime.now().isoformat(),
                "progress": 65,
                "message": "Invoice is being processed"
            }
        })
        mock_get.return_value = mock_response
        
        # Run test
        result = asyncio.run(firs_service.check_submission_status(submission_id))
        
        # Assertions
        self.assertEqual(result.submission_id, submission_id)
        self.assertEqual(result.status, "PROCESSING")
        self.assertEqual(result.message, "Invoice is being processed")
        self.assertIsNotNone(result.timestamp)
        self.assertEqual(result.details["progress"], 65)
        
        # Check request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["url"], f"https://test-api.firs.gov.ng/api/v1/invoice/submission/{submission_id}/status")
    
    @patch('app.services.firs_service.FIRSService._ensure_authenticated')
    @patch('requests.get')
    def test_check_submission_status_not_found(self, mock_get, mock_auth):
        """Test checking status for non-existent submission."""
        # Setup mocks
        mock_auth.return_value = AsyncMock()
        submission_id = str(uuid4())
        
        mock_response = MockResponse(404, {
            "status": "error",
            "message": "Submission not found"
        }, text="Submission not found")
        mock_get.return_value = mock_response
        
        # Run test and check exception
        with self.assertRaises(HTTPException) as context:
            asyncio.run(firs_service.check_submission_status(submission_id))
        
        # Check exception details
        self.assertEqual(context.exception.status_code, 404)
        self.assertTrue(f"Submission with ID {submission_id} not found" in context.exception.detail)
    
    @patch('app.services.firs_service.FIRSService._ensure_authenticated')
    @patch('requests.post')
    def test_validate_ubl_invoice(self, mock_post, mock_auth):
        """Test validating a UBL XML invoice."""
        # Setup mocks
        mock_auth.return_value = AsyncMock()
        
        mock_response = MockResponse(200, {
            "status": "success",
            "message": "UBL invoice validation successful",
            "data": {
                "valid": True,
                "format": "UBL2.1",
                "profile": "BIS3.0"
            }
        })
        mock_post.return_value = mock_response
        
        # Run test
        result = asyncio.run(firs_service.validate_ubl_invoice(self.ubl_xml))
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "UBL invoice validation successful")
        self.assertTrue(result.details["valid"])
        
        # Check request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["url"], "https://test-api.firs.gov.ng/api/v1/invoice/ubl/validate")
        self.assertEqual(kwargs["data"], self.ubl_xml)
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/xml")
    
    @patch('app.services.firs_service.FIRSService._ensure_authenticated')
    @patch('requests.post')
    def test_validate_ubl_invoice_invalid(self, mock_post, mock_auth):
        """Test validating an invalid UBL XML invoice."""
        # Setup mocks
        mock_auth.return_value = AsyncMock()
        
        mock_response = MockResponse(400, {
            "status": "error",
            "message": "UBL validation failed",
            "errors": [
                {"field": "cbc:ID", "message": "Invoice ID is required"},
                {"field": "cac:AccountingSupplierParty", "message": "Supplier information is incomplete"}
            ]
        }, text="UBL validation failed")
        mock_post.return_value = mock_response
        
        # Run test
        result = asyncio.run(firs_service.validate_ubl_invoice(self.ubl_xml))
        
        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(result.message, "UBL validation failed")
        self.assertIsNotNone(result.errors)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(result.errors[0]["field"], "cbc:ID")


if __name__ == "__main__":
    # Set up Python path similar to the project's run.sh
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    # Add backend directory to path
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    print("Running FIRS submission tests...")
    unittest.main(verbosity=2)
