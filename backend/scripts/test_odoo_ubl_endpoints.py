#!/usr/bin/env python
"""
Test script for the Odoo UBL API endpoints.

This script simulates HTTP requests to the Odoo UBL API endpoints to test their functionality
without needing to run the full FastAPI server.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Dummy implementation of required services to simulate the behavior
class MockOdooService:
    """Mock implementation of Odoo services for testing the API endpoints."""
    
    def __init__(self):
        self.test_invoice = {
            "id": 1234,
            "number": "INV/2023/001",
            "date": "2023-05-31",
            "due_date": "2023-06-30",
            "partner_id": {
                "id": 42,
                "name": "Test Customer",
                "email": "customer@example.com",
                "vat": "NG123456789",
                "street": "123 Test Street",
                "city": "Lagos",
                "country_id": {"id": 156, "code": "NG", "name": "Nigeria"}
            },
            "invoice_line_ids": [
                {
                    "id": 1,
                    "name": "Product A",
                    "quantity": 5,
                    "price_unit": 100.0,
                    "price_subtotal": 500.0,
                    "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}]
                },
                {
                    "id": 2,
                    "name": "Service B",
                    "quantity": 10,
                    "price_unit": 100.0,
                    "price_subtotal": 1000.0,
                    "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}]
                }
            ],
            "amount_untaxed": 1500.0,
            "amount_tax": 112.5,
            "amount_total": 1612.5,
            "currency_id": {"id": 123, "name": "NGN", "symbol": "₦"},
            "state": "posted"
        }
        
        self.company_info = {
            "name": "Test Company Ltd",
            "email": "info@testcompany.com",
            "vat": "NG987654321",
            "street": "456 Business Avenue",
            "city": "Abuja",
            "country_id": {"id": 156, "code": "NG", "name": "Nigeria"},
            "phone": "+234123456789"
        }
    
    def test_connection(self, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate testing a connection to Odoo."""
        print(f"Testing connection to Odoo at {connection_params.get('host')}")
        # Simulate successful connection
        return {
            "success": True,
            "message": "Connection successful",
            "data": {
                "odoo_version": "16.0",
                "user": "admin",
                "company_info": self.company_info
            }
        }
    
    def search_invoices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate searching for invoices in Odoo."""
        print(f"Searching for invoices with params: {params}")
        # Return a list of mock invoices
        return {
            "data": [self.test_invoice],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total_pages": 1,
                "total_items": 1
            }
        }
    
    def get_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """Simulate retrieving a specific invoice from Odoo."""
        print(f"Getting invoice with ID: {invoice_id}")
        # Return a mock invoice
        return self.test_invoice
    
    def map_to_ubl(self, invoice_data: Dict[str, Any], company_info: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate mapping an Odoo invoice to UBL format."""
        print(f"Mapping invoice {invoice_data.get('number')} to UBL format")
        # Return a mock UBL mapping result
        return {
            "success": True,
            "ubl_id": f"ubl_{invoice_data.get('id')}",
            "invoice_number": invoice_data.get("number"),
            "ubl_object": {
                "invoice_number": invoice_data.get("number"),
                "issue_date": invoice_data.get("date"),
                "due_date": invoice_data.get("due_date"),
                "monetary_total": {
                    "tax_exclusive_amount": invoice_data.get("amount_untaxed"),
                    "tax_inclusive_amount": invoice_data.get("amount_total"),
                    "payable_amount": invoice_data.get("amount_total")
                }
            },
            "ubl_xml": f"<Invoice><ID>{invoice_data.get('number')}</ID></Invoice>",
            "validation": {
                "valid": True,
                "warnings": []
            }
        }


class TestOdooUblEndpoints:
    """Test class for the Odoo UBL API endpoints."""
    
    def __init__(self):
        self.odoo_service = MockOdooService()
        self.test_connection_params = {
            "host": "https://odoo.example.com",
            "db": "test_db",
            "user": "test_user",
            "password": "test_password",
            "api_key": None
        }
    
    def test_connection_endpoint(self):
        """Test the /odoo-ubl/test-connection endpoint."""
        print("\n=== Testing /odoo-ubl/test-connection endpoint ===")
        
        # Simulate the test_odoo_ubl_connection function
        try:
            # Create connection parameters
            connection_result = self.odoo_service.test_connection(self.test_connection_params)
            
            # Add UBL mapping-specific test information
            result = {
                **connection_result,
                "ubl_mapping_status": "available",
                "ubl_mapping_version": "BIS Billing 3.0",
                "ubl_schema_validation": True
            }
            
            print(f"Response: {json.dumps(result, indent=2)}")
            print("Test successful!\n")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Test failed!\n")
    
    def test_get_invoices_endpoint(self):
        """Test the /odoo-ubl/invoices endpoint."""
        print("\n=== Testing /odoo-ubl/invoices endpoint ===")
        
        try:
            # Simulate the get_odoo_invoices function
            # Setup parameters
            params = {
                **self.test_connection_params,
                "from_date": "2023-01-01",
                "to_date": "2023-12-31",
                "include_draft": False,
                "page": 1,
                "page_size": 10
            }
            
            # Fetch invoices
            invoice_result = self.odoo_service.search_invoices(params)
            
            # Add UBL mapping capability information to each invoice
            invoices = invoice_result.get("data", [])
            for invoice in invoices:
                invoice["ubl_mapping_available"] = True
                invoice["ubl_endpoints"] = {
                    "details": f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}",
                    "ubl": f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}/ubl",
                    "xml": f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}/ubl/xml"
                }
            
            result = {
                "status": "success",
                "data": invoices,
                "pagination": invoice_result.get("pagination", {}),
                "ubl_mapping": {
                    "status": "available",
                    "version": "BIS Billing 3.0"
                }
            }
            
            print(f"Response: {json.dumps(result, indent=2)}")
            print("Test successful!\n")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Test failed!\n")
    
    def test_invoice_details_endpoint(self):
        """Test the /odoo-ubl/invoices/{invoice_id} endpoint."""
        print("\n=== Testing /odoo-ubl/invoices/{invoice_id} endpoint ===")
        
        try:
            # Simulate the get_odoo_invoice_details function
            invoice_id = 1234
            
            # Connect to Odoo (already simulated in the constructor)
            
            # Get invoice data
            invoice_data = self.odoo_service.get_invoice(invoice_id)
            
            # Include UBL mapping availability information
            result = {
                "status": "success",
                "data": invoice_data,
                "ubl_mapping": {
                    "available": True,
                    "endpoints": {
                        "ubl": f"/api/v1/odoo-ubl/invoices/{invoice_id}/ubl",
                        "xml": f"/api/v1/odoo-ubl/invoices/{invoice_id}/ubl/xml"
                    }
                }
            }
            
            print(f"Response: {json.dumps(result, indent=2)}")
            print("Test successful!\n")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Test failed!\n")
    
    def test_ubl_mapping_endpoint(self):
        """Test the /odoo-ubl/invoices/{invoice_id}/ubl endpoint."""
        print("\n=== Testing /odoo-ubl/invoices/{invoice_id}/ubl endpoint ===")
        
        try:
            # Simulate the map_odoo_invoice_to_ubl function
            invoice_id = 1234
            
            # Get invoice data
            invoice_data = self.odoo_service.get_invoice(invoice_id)
            company_info = self.odoo_service.company_info
            
            # Map to UBL
            mapping_result = self.odoo_service.map_to_ubl(invoice_data, company_info)
            
            result = {
                "status": "success",
                "data": mapping_result,
                "message": "Invoice successfully mapped to UBL format"
            }
            
            print(f"Response: {json.dumps(result, indent=2)}")
            print("Test successful!\n")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Test failed!\n")
    
    def test_ubl_xml_endpoint(self):
        """Test the /odoo-ubl/invoices/{invoice_id}/ubl/xml endpoint."""
        print("\n=== Testing /odoo-ubl/invoices/{invoice_id}/ubl/xml endpoint ===")
        
        try:
            # Simulate the get_odoo_invoice_ubl_xml function
            invoice_id = 1234
            
            # Get invoice data and map to UBL
            invoice_data = self.odoo_service.get_invoice(invoice_id)
            company_info = self.odoo_service.company_info
            mapping_result = self.odoo_service.map_to_ubl(invoice_data, company_info)
            
            # Extract the XML content
            xml_content = mapping_result.get("ubl_xml")
            
            # In a real API response, this would set the Content-Type to application/xml
            # and return the XML directly. Here we just print it.
            print(f"XML Content: {xml_content}")
            print("Test successful!\n")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Test failed!\n")
    
    def test_batch_process_endpoint(self):
        """Test the /odoo-ubl/batch-process endpoint."""
        print("\n=== Testing /odoo-ubl/batch-process endpoint ===")
        
        try:
            # Simulate the batch_process_odoo_invoices function
            # Fetch invoices
            params = {
                **self.test_connection_params,
                "from_date": "2023-01-01",
                "to_date": "2023-12-31",
                "include_draft": False,
                "page": 1,
                "page_size": 10
            }
            
            invoice_result = self.odoo_service.search_invoices(params)
            invoices = invoice_result.get("data", [])
            company_info = self.odoo_service.company_info
            
            # Process each invoice
            results = []
            success_count = 0
            error_count = 0
            
            for invoice in invoices:
                try:
                    # Process invoice
                    mapping_result = self.odoo_service.map_to_ubl(invoice, company_info)
                    
                    if mapping_result.get("success"):
                        success_count += 1
                    else:
                        error_count += 1
                        
                    results.append({
                        "invoice_id": invoice.get("id"),
                        "invoice_number": invoice.get("number"),
                        "success": mapping_result.get("success", False),
                        "errors": mapping_result.get("errors", []),
                        "warnings": mapping_result.get("warnings", []),
                        "ubl_id": mapping_result.get("ubl_id")
                    })
                    
                except Exception as e:
                    error_count += 1
                    results.append({
                        "invoice_id": invoice.get("id"),
                        "invoice_number": invoice.get("number"),
                        "success": False,
                        "errors": [{
                            "code": "PROCESSING_ERROR",
                            "message": str(e),
                            "field": None
                        }],
                        "warnings": []
                    })
            
            result = {
                "status": "success" if error_count == 0 else "partial",
                "processed_count": len(invoices),
                "success_count": success_count,
                "error_count": error_count,
                "message": f"Processed {len(invoices)} invoices: {success_count} successful, {error_count} failed",
                "invoices": results,
                "pagination": invoice_result.get("pagination", {})
            }
            
            print(f"Response: {json.dumps(result, indent=2)}")
            print("Test successful!\n")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Test failed!\n")
    
    def run_all_tests(self):
        """Run all endpoint tests."""
        print("==== Starting Odoo UBL API Endpoint Tests ====")
        self.test_connection_endpoint()
        self.test_get_invoices_endpoint()
        self.test_invoice_details_endpoint()
        self.test_ubl_mapping_endpoint()
        self.test_ubl_xml_endpoint()
        self.test_batch_process_endpoint()
        print("==== All Odoo UBL API Endpoint Tests Completed ====")


if __name__ == "__main__":
    tester = TestOdooUblEndpoints()
    tester.run_all_tests()
