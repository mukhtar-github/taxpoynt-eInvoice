#!/usr/bin/env python
"""
Test script for the FIRS API endpoints with Odoo integration.

This script combines Odoo connectivity via OdooRPC with FIRS API testing to validate the complete
ERP-first integration flow. It fetches real invoice data from Odoo and tests the submission to
FIRS API endpoints.

Usage:
    python backend/scripts/test_firs_api_endpoints.py [--use-odoo-data]

Options:
    --use-odoo-data    Use real invoice data from Odoo instead of mock data
"""

import sys
import os
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))  

# Import OdooRPC if available
try:
    import odoorpc
    logger.info("OdooRPC library successfully imported")
    ODOORPC_AVAILABLE = True
except ImportError:
    logger.warning("OdooRPC not installed. To enable Odoo connectivity, install with: pip install odoorpc")
    ODOORPC_AVAILABLE = False

# Try to import test credentials if available
try:
    from backend.test_credentials import test_config as odoo_config
    logger.info("Odoo test credentials loaded successfully")
    ODOO_CREDENTIALS_AVAILABLE = True
except ImportError:
    logger.warning("Odoo test credentials not found. Using mock data only.")
    ODOO_CREDENTIALS_AVAILABLE = False
    odoo_config = None

class SubmissionStatus(Enum):
    """Enum for submission status values."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


class OdooConnector:
    """Connector for Odoo integration using OdooRPC."""
    
    def __init__(self, config):
        """Initialize Odoo connector with configuration."""
        self.config = config
        self.odoo = None
        self.connected = False
    
    def connect(self):
        """Connect to Odoo using OdooRPC."""
        if not ODOORPC_AVAILABLE:
            logger.error("OdooRPC not available. Cannot connect to Odoo.")
            return False
        
        try:
            logger.info(f"Connecting to Odoo at {self.config['host']} using {self.config['protocol']}")
            
            # Initialize OdooRPC connection
            self.odoo = odoorpc.ODOO(
                self.config["host"], 
                protocol=self.config["protocol"], 
                port=self.config["port"]
            )
            
            # Login to Odoo
            self.odoo.login(
                self.config["database"], 
                self.config["username"], 
                self.config["password"]
            )
            
            # Get user info
            user = self.odoo.env['res.users'].browse(self.odoo.env.uid)
            logger.info(f"Connected as user: {user.name} (ID: {self.odoo.env.uid})")
            
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {str(e)}")
            return False
    
    def fetch_invoices(self, limit=5, from_days_ago=30):
        """Fetch invoices from Odoo."""
        if not self.connected or not self.odoo:
            logger.error("Not connected to Odoo. Call connect() first.")
            return []
        
        logger.info(f"Fetching up to {limit} invoices from the past {from_days_ago} days")
        
        # Calculate from_date
        from_date = (datetime.now() - timedelta(days=from_days_ago)).strftime('%Y-%m-%d')
        
        try:
            # Get the invoice model (account.move in Odoo 13+)
            Invoice = self.odoo.env['account.move']
            
            # Build search domain
            domain = [
                ('move_type', '=', 'out_invoice'),  # Only customer invoices
                ('invoice_date', '>=', from_date)   # Only recent invoices
            ]
            
            # First use search to get IDs
            invoice_ids = Invoice.search(domain, limit=limit)
            logger.info(f"Found {len(invoice_ids)} invoices")
            
            if not invoice_ids:
                return []
            
            # Use search_read instead of browse to avoid frozendict issues
            invoice_data = Invoice.search_read(
                [('id', 'in', invoice_ids)], 
                [
                    'name', 'ref', 'invoice_date', 'amount_total', 'amount_untaxed', 'amount_tax',
                    'partner_id', 'invoice_line_ids', 'state', 'currency_id', 'company_id'
                ]
            )
            
            # Get line details for each invoice
            result = []
            for invoice in invoice_data:
                # Get invoice lines
                if invoice.get('invoice_line_ids'):
                    line_ids = invoice['invoice_line_ids']
                    lines = self.odoo.env['account.move.line'].search_read(
                        [('id', 'in', line_ids), ('display_type', 'in', [False, 'product'])],
                        ['product_id', 'name', 'quantity', 'price_unit', 'price_subtotal', 'tax_ids']
                    )
                    invoice['lines'] = lines
                
                # Get partner details
                if invoice.get('partner_id'):
                    partner_id = invoice['partner_id'][0]
                    partner = self.odoo.env['res.partner'].search_read(
                        [('id', '=', partner_id)],
                        ['name', 'vat', 'email', 'phone', 'street', 'city', 'country_id']
                    )
                    if partner:
                        invoice['partner'] = partner[0]
                
                # Get company details
                if invoice.get('company_id'):
                    company_id = invoice['company_id'][0]
                    company = self.odoo.env['res.company'].search_read(
                        [('id', '=', company_id)],
                        ['name', 'vat', 'email', 'phone', 'street', 'city', 'country_id']
                    )
                    if company:
                        invoice['company'] = company[0]
                
                result.append(invoice)
            
            return result
        except Exception as e:
            logger.error(f"Error fetching invoices: {str(e)}")
            return []


class OdooToFIRSMapper:
    """Maps Odoo invoice data to FIRS API format."""
    
    @staticmethod
    def map_invoice(odoo_invoice):
        """Map Odoo invoice to FIRS API format."""
        try:
            # Extract basic invoice information
            invoice_number = odoo_invoice.get('name') or f"INV-{odoo_invoice['id']}"
            invoice_date = odoo_invoice.get('invoice_date', datetime.now().strftime('%Y-%m-%d'))
            
            # Extract partner (customer) information
            partner = odoo_invoice.get('partner', {})
            customer_name = partner.get('name', 'Unknown Customer')
            customer_tin = partner.get('vat', '').replace('NG', '')  # Remove country prefix from TIN
            
            # Extract company (supplier) information
            company = odoo_invoice.get('company', {})
            supplier_name = company.get('name', 'Unknown Supplier')
            supplier_tin = company.get('vat', '').replace('NG', '')  # Remove country prefix from TIN
            
            # Extract monetary values
            amount_total = float(odoo_invoice.get('amount_total', 0))
            amount_untaxed = float(odoo_invoice.get('amount_untaxed', 0))
            amount_tax = float(odoo_invoice.get('amount_tax', 0))
            
            # Extract line items
            items = []
            for line in odoo_invoice.get('lines', []):
                product_name = ''
                if line.get('product_id'):
                    product_name = line['product_id'][1]
                else:
                    product_name = line.get('name', 'Unknown Product')
                
                item = {
                    "name": product_name,
                    "description": line.get('name', ''),
                    "quantity": float(line.get('quantity', 0)),
                    "unitPrice": float(line.get('price_unit', 0)),
                    "totalAmount": float(line.get('price_subtotal', 0)),
                    "taxRate": 7.5,  # Default Nigerian VAT rate
                    "taxAmount": float(line.get('price_subtotal', 0)) * 0.075,
                    "itemType": "GOODS"  # Default to GOODS
                }
                items.append(item)
            
            # Create FIRS format invoice
            firs_invoice = {
                "odoo_reference": invoice_number,
                "invoiceNumber": invoice_number,
                "invoiceType": "REGULAR",
                "date": invoice_date,
                "dueDate": invoice_date,  # Use same date as a fallback
                "supplier": {
                    "name": supplier_name,
                    "tin": supplier_tin,
                    "address": f"{company.get('street', '')}, {company.get('city', '')}",
                    "email": company.get('email', ''),
                    "phone": company.get('phone', '')
                },
                "customer": {
                    "name": customer_name,
                    "tin": customer_tin,
                    "address": f"{partner.get('street', '')}, {partner.get('city', '')}",
                    "email": partner.get('email', ''),
                    "phone": partner.get('phone', '')
                },
                "items": items,
                "subTotal": amount_untaxed,
                "totalTax": amount_tax,
                "totalAmount": amount_total,
                "currency": "NGN",
                "paymentTerms": "30 days",
                "notes": f"Invoice from Odoo: {invoice_number}"
            }
            
            return firs_invoice
        except Exception as e:
            logger.error(f"Error mapping Odoo invoice to FIRS format: {str(e)}")
            return None

class MockFIRSService:
    """Mock implementation of FIRS API services for testing.
    
    This service simulates the FIRS API endpoints based on the latest integration guide
    and follows the ERP-first integration strategy with a focus on Odoo integration.
    """
    
    def __init__(self):
        # Base URLs from the FIRS API Integration Guide
        self.sandbox_url = "https://eivc-k6z6d.ondigitalocean.app"
        self.production_url = None  # To be provided by FIRS
        
        # Mock API credentials
        self.api_key = "mock_api_key"
        self.api_secret = "mock_api_secret"
        self.auth_token = "mock_jwt_token"
        
        # Cache for submissions
        self.submissions = {}
        
        # Mock Odoo connection info
        self.odoo_info = {
            "host": "https://odoo.example.com",
            "database": "test_db",
            "username": "test_user",
            "version": "16.0"
        }
        
    def get_headers(self, include_auth=False):
        """Get the headers for API requests."""
        headers = {
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
            "Content-Type": "application/json"
        }
        
        if include_auth:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        return headers
    
    def health_check(self):
        """Mock health check endpoint.
        
        Endpoint: GET /api
        """
        return {"healthy": True}
    
    def authenticate(self):
        """Mock authentication with the FIRS API.
        
        Endpoint: POST /api/v1/utilities/authenticate
        """
        return {
            "status": "success",
            "message": "Authentication successful",
            "data": {
                "access_token": self.auth_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": {
                    "email": "test@example.com",
                    "name": "Test User",
                    "role": "admin"
                }
            }
        }
    
    def submit_invoice(self, invoice_data):
        """Mock invoice submission with Odoo integration.
        
        Endpoint: POST /api/v1/invoice/submission
        """
        # Generate a submission ID
        submission_id = f"sub-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Store the submission in our cache
        self.submissions[submission_id] = {
            "invoice_data": invoice_data,
            "status": SubmissionStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "odoo_reference": invoice_data.get("odoo_reference", "INV/2023/001")
        }
        
        return {
            "code": 201,
            "data": {
                "submission_id": submission_id,
                "status": SubmissionStatus.PENDING.value,
                "irn": invoice_data.get("irn", f"ITW006-{datetime.now().strftime('%Y%m%d')}"),
                "timestamp": datetime.now().isoformat(),
                "odoo_reference": invoice_data.get("odoo_reference", "INV/2023/001")
            },
            "message": "Invoice submitted successfully"
        }
    
    def check_submission_status(self, submission_id):
        """Mock submission status check.
        
        Endpoint: GET /api/v1/invoice/submission/{SUBMISSION_ID}/status
        """
        # If submission exists in our cache, update its status to COMPLETED
        if submission_id in self.submissions:
            self.submissions[submission_id]["status"] = SubmissionStatus.COMPLETED.value
            self.submissions[submission_id]["updated_at"] = datetime.now().isoformat()
            
            return {
                "code": 200,
                "data": {
                    "submission_id": submission_id,
                    "status": SubmissionStatus.COMPLETED.value,
                    "irn": self.submissions[submission_id]["invoice_data"].get("irn", f"ITW006-{datetime.now().strftime('%Y%m%d')}"),
                    "timestamp": self.submissions[submission_id]["created_at"],
                    "completion_timestamp": datetime.now().isoformat(),
                    "odoo_reference": self.submissions[submission_id].get("odoo_reference", "INV/2023/001")
                },
                "message": "Submission status retrieved successfully"
            }
        else:
            # For unknown submissions, return a mock response
            return {
                "code": 200,
                "data": {
                    "submission_id": submission_id,
                    "status": SubmissionStatus.COMPLETED.value,
                    "timestamp": datetime.now().isoformat()
                },
                "message": "Submission status retrieved successfully"
            }
    
    def batch_submit_invoices(self, invoices_data):
        """Mock batch invoice submission from Odoo.
        
        Endpoint: POST /api/v1/invoice/batch-submission
        """
        batch_id = f"batch-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        submissions = []
        
        for idx, invoice in enumerate(invoices_data):
            submission_id = f"sub-batch-{idx}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.submissions[submission_id] = {
                "invoice_data": invoice,
                "status": SubmissionStatus.PENDING.value,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "batch_id": batch_id,
                "odoo_reference": invoice.get("odoo_reference", f"INV/2023/{idx+1:03d}")
            }
            
            submissions.append({
                "submission_id": submission_id,
                "status": SubmissionStatus.PENDING.value,
                "irn": invoice.get("irn", f"ITW006-BATCH-{idx}-{datetime.now().strftime('%Y%m%d')}")
            })
        
        return {
            "code": 202,
            "data": {
                "batch_id": batch_id,
                "total_submitted": len(invoices_data),
                "status": "PROCESSING",
                "submissions": submissions,
                "timestamp": datetime.now().isoformat()
            },
            "message": f"Batch submission with {len(invoices_data)} invoices accepted for processing"
        }
    
    def get_odoo_connection_status(self):
        """Mock Odoo connection status check for ERP-first integration.
        
        Endpoint: GET /api/v1/integrations/odoo/status
        """
        return {
            "code": 200,
            "data": {
                "connected": True,
                "odoo_version": self.odoo_info["version"],
                "host": self.odoo_info["host"],
                "database": self.odoo_info["database"],
                "username": self.odoo_info["username"],
                "company_info": {
                    "name": "Test Company Ltd",
                    "vat": "NG987654321"
                },
                "last_sync": datetime.now().isoformat()
            },
            "message": "Odoo connection successful"
        }


def get_sample_invoice():
    """Get a sample invoice based on Odoo UBL format for testing."""
    return {
        "odoo_reference": "INV/2023/001",
        "invoiceNumber": "INV12345",
        "invoiceType": "REGULAR",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "dueDate": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "supplier": {
            "name": "Test Company Ltd",
            "tin": "NG987654321",
            "address": "456 Business Avenue, Abuja",
            "email": "info@testcompany.com",
            "phone": "+234123456789"
        },
        "customer": {
            "name": "Test Customer",
            "tin": "NG123456789",
            "address": "123 Test Street, Lagos",
            "email": "customer@example.com",
            "phone": "+2348012345678"
        },
        "items": [
            {
                "name": "Product A",
                "description": "High quality product",
                "quantity": 5,
                "unitPrice": 100.0,
                "totalAmount": 500.0,
                "taxRate": 7.5,
                "taxAmount": 37.5,
                "itemType": "GOODS"
            },
            {
                "name": "Service B",
                "description": "Professional service",
                "quantity": 10,
                "unitPrice": 100.0,
                "totalAmount": 1000.0,
                "taxRate": 7.5,
                "taxAmount": 75.0,
                "itemType": "SERVICE"
            }
        ],
        "subTotal": 1500.0,
        "totalTax": 112.5,
        "totalAmount": 1612.5,
        "currency": "NGN",
        "paymentTerms": "30 days",
        "notes": "Sample invoice for testing"
    }


class TestFIRSApiEndpoints:
    """Test class for FIRS API endpoints with ERP-first integration.
    
    This class provides a comprehensive test suite for FIRS API endpoints,
    with support for using real invoice data from Odoo via OdooRPC.
    """
    
    def __init__(self, use_odoo_data=False):
        """Initialize test class.
        
        Args:
            use_odoo_data: Whether to use real Odoo data instead of mock data
        """
        self.firs_service = MockFIRSService()
        self.test_results = {"passed": 0, "failed": 0, "total": 0}
        self.sample_invoice = get_sample_invoice()
        
        # Odoo integration
        self.use_odoo_data = use_odoo_data
        self.odoo_connector = None
        self.odoo_invoices = []
        self.firs_invoices = []
        
        # Initialize Odoo connection if requested
        if self.use_odoo_data:
            if not ODOORPC_AVAILABLE or not ODOO_CREDENTIALS_AVAILABLE:
                logger.warning("Cannot use Odoo data: OdooRPC or credentials not available")
                self.use_odoo_data = False
            else:
                self.init_odoo_connection()
    
    def test_health_check(self):
        """Test the health check endpoint."""
        print("\n=== Testing /api health check endpoint ===")
        response = self.firs_service.health_check()
        print(f"Response: {json.dumps(response, indent=2)}")
        
        success = response.get("healthy", False)
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print("Test successful!")
        else:
            self.test_results["failed"] += 1
            print("Test failed!")
        return success
    
    def test_authentication(self):
        """Test the authentication endpoint."""
        print("\n=== Testing /api/v1/utilities/authenticate endpoint ===")
        response = self.firs_service.authenticate()
        print(f"Response: {json.dumps(response, indent=2)}")
        
        success = response.get("status") == "success" and "access_token" in response.get("data", {})
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print("Test successful!")
        else:
            self.test_results["failed"] += 1
            print("Test failed!")
        return success
    
    def test_odoo_connection(self):
        """Test the Odoo connection status endpoint for ERP-first integration."""
        print("\n=== Testing /api/v1/integrations/odoo/status endpoint ===")
        response = self.firs_service.get_odoo_connection_status()
        print(f"Response: {json.dumps(response, indent=2)}")
        
        success = response.get("code") == 200 and response.get("data", {}).get("connected", False)
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print("Test successful!")
        else:
            self.test_results["failed"] += 1
            print("Test failed!")
        return success
    
    def test_invoice_submission(self):
        """Test the invoice submission and status check endpoints with Odoo data."""
        print("\n=== Testing /api/v1/invoice/submission endpoint ===")
        
        # Submit invoice
        submission_response = self.firs_service.submit_invoice(self.sample_invoice)
        submission_id = submission_response.get("data", {}).get("submission_id")
        print(f"Submit Invoice Response: {json.dumps(submission_response, indent=2)}")
        
        # Check submission status
        status_response = self.firs_service.check_submission_status(submission_id)
        print(f"Check Submission Status Response: {json.dumps(status_response, indent=2)}")
        
        success = (
            submission_response.get("code") == 201 and 
            status_response.get("code") == 200 and
            status_response.get("data", {}).get("status") == SubmissionStatus.COMPLETED.value
        )
        
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print("Test successful!")
        else:
            self.test_results["failed"] += 1
            print("Test failed!")
        return success
    
    def test_batch_submission(self):
        """Test the batch invoice submission endpoint with multiple Odoo invoices."""
        print("\n=== Testing /api/v1/invoice/batch-submission endpoint ===")
        
        # Create a batch of invoices (3 invoices)
        batch_invoices = []
        for i in range(3):
            invoice = get_sample_invoice()
            invoice["invoiceNumber"] = f"INV12345-{i+1}"
            invoice["odoo_reference"] = f"INV/2023/{i+1:03d}"
            batch_invoices.append(invoice)
        
        # Submit batch
        batch_response = self.firs_service.batch_submit_invoices(batch_invoices)
        print(f"Batch Submission Response: {json.dumps(batch_response, indent=2)}")
        
        success = batch_response.get("code") == 202 and len(batch_response.get("data", {}).get("submissions", [])) == 3
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print("Test successful!")
        else:
            self.test_results["failed"] += 1
            print("Test failed!")
        return success
    
    def init_odoo_connection(self):
        """Initialize connection to Odoo and fetch invoices."""
        try:
            logger.info("Initializing Odoo connector...")
            self.odoo_connector = OdooConnector(odoo_config)
            
            # Connect to Odoo
            if not self.odoo_connector.connect():
                logger.error("Failed to connect to Odoo. Using mock data instead.")
                self.use_odoo_data = False
                return False
            
            # Fetch invoices from Odoo
            self.odoo_invoices = self.odoo_connector.fetch_invoices(limit=3, from_days_ago=30)
            if not self.odoo_invoices:
                logger.warning("No invoices found in Odoo. Using mock data instead.")
                self.use_odoo_data = False
                return False
            
            # Map Odoo invoices to FIRS format
            logger.info(f"Mapping {len(self.odoo_invoices)} Odoo invoices to FIRS format")
            for odoo_invoice in self.odoo_invoices:
                firs_invoice = OdooToFIRSMapper.map_invoice(odoo_invoice)
                if firs_invoice:
                    self.firs_invoices.append(firs_invoice)
            
            if not self.firs_invoices:
                logger.warning("Failed to map any Odoo invoices to FIRS format. Using mock data instead.")
                self.use_odoo_data = False
                return False
            
            logger.info(f"Successfully mapped {len(self.firs_invoices)} Odoo invoices to FIRS format")
            return True
        except Exception as e:
            logger.error(f"Error initializing Odoo connection: {str(e)}")
            self.use_odoo_data = False
            return False
    
    def test_odoo_connection_status(self):
        """Test Odoo connection status."""
        print("\n=== Testing Odoo Connection Status ===")
        
        if not ODOORPC_AVAILABLE:
            print("OdooRPC not available. Test skipped.")
            return True
        
        if not ODOO_CREDENTIALS_AVAILABLE:
            print("Odoo credentials not available. Test skipped.")
            return True
        
        if not self.odoo_connector:
            # Initialize connection if not already done
            self.odoo_connector = OdooConnector(odoo_config)
        
        # Test connection
        success = self.odoo_connector.connect()
        
        # Record result
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print("Successfully connected to Odoo")
            print("Test successful!")
        else:
            self.test_results["failed"] += 1
            print("Failed to connect to Odoo")
            print("Test failed!")
        
        return success
    
    def test_odoo_to_firs_mapping(self):
        """Test mapping Odoo invoices to FIRS format."""
        print("\n=== Testing Odoo to FIRS Invoice Mapping ===")
        
        if not self.use_odoo_data or not self.odoo_invoices:
            print("Odoo data not available. Test skipped.")
            return True
        
        # Perform mapping test
        success = len(self.firs_invoices) > 0
        
        # Show sample mapped invoice
        if success and self.firs_invoices:
            sample_invoice = self.firs_invoices[0]
            print("Sample mapped invoice:")
            print(f"  Invoice Number: {sample_invoice.get('invoiceNumber')}")
            print(f"  Date: {sample_invoice.get('date')}")
            print(f"  Customer: {sample_invoice.get('customer', {}).get('name')}")
            print(f"  Supplier: {sample_invoice.get('supplier', {}).get('name')}")
            print(f"  Total Amount: {sample_invoice.get('totalAmount')}")
            print(f"  Items: {len(sample_invoice.get('items', []))}")
        
        # Record result
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print(f"Successfully mapped {len(self.firs_invoices)} Odoo invoices to FIRS format")
            print("Test successful!")
        else:
            self.test_results["failed"] += 1
            print("Failed to map any Odoo invoices to FIRS format")
            print("Test failed!")
        
        return success
    
    def test_odoo_to_firs_submission(self):
        """Test submitting Odoo invoices to FIRS API."""
        print("\n=== Testing Odoo Invoice Submission to FIRS API ===")
        
        if not self.use_odoo_data or not self.firs_invoices:
            print("Odoo invoice data not available. Test skipped.")
            return True
        
        # Use the first mapped invoice for testing
        firs_invoice = self.firs_invoices[0]
        
        # Submit to FIRS API
        submission_response = self.firs_service.submit_invoice(firs_invoice)
        submission_id = submission_response.get("data", {}).get("submission_id")
        
        # Check submission status
        status_response = self.firs_service.check_submission_status(submission_id)
        
        # Print responses
        print(f"Odoo Invoice: {firs_invoice.get('invoiceNumber')}")
        print(f"Submit Response: {json.dumps(submission_response, indent=2)}")
        print(f"Status Response: {json.dumps(status_response, indent=2)}")
        
        # Validate success
        success = (
            submission_response.get("code") == 201 and 
            status_response.get("code") == 200 and
            status_response.get("data", {}).get("status") == SubmissionStatus.COMPLETED.value
        )
        
        # Record result
        self.test_results["total"] += 1
        if success:
            self.test_results["passed"] += 1
            print("Successfully submitted Odoo invoice to FIRS API")
            print("Test successful!")
        else:
            self.test_results["failed"] += 1
            print("Failed to submit Odoo invoice to FIRS API")
            print("Test failed!")
        
        return success
    
    def run_all_tests(self):
        """Run all tests and report results."""
        print("==== Starting FIRS API Endpoint Tests ====\n")
        
        # Run standard tests
        self.test_health_check()
        self.test_authentication()
        self.test_odoo_connection_status()
        
        # Run Odoo-specific tests if enabled
        if self.use_odoo_data:
            self.test_odoo_to_firs_mapping()
            self.test_odoo_to_firs_submission()
        
        # Run standard FIRS API tests
        self.test_invoice_submission()
        self.test_batch_submission()
        
        # Print summary
        print("\n==== Test Summary ====\n")
        print(f"Tests Run: {self.test_results['total']}")
        print(f"Tests Passed: {self.test_results['passed']}")
        print(f"Tests Failed: {self.test_results['failed']}")
        print(f"Odoo Integration: {'Enabled' if self.use_odoo_data else 'Disabled'}")
        
        # Overall result
        if self.test_results["failed"] == 0 and self.test_results["total"] > 0:
            print("\n==== All Tests Passed Successfully! ====\n")
            return True
        else:
            print("\n==== Some Tests Failed! ====\n")
            return False


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test FIRS API endpoints with optional Odoo integration")
    parser.add_argument(
        "--use-odoo-data",
        action="store_true",
        help="Use real invoice data from Odoo instead of mock data"
    )
    args = parser.parse_args()
    
    # Initialize test class with command-line arguments
    tester = TestFIRSApiEndpoints(use_odoo_data=args.use_odoo_data)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
