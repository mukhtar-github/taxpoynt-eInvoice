"""
Testing framework helpers for TaxPoynt eInvoice.

This module provides helper classes and functions for testing the TaxPoynt eInvoice
system, particularly focused on FIRS API integration testing.
"""

import os
import requests
import json
import logging
import datetime
import uuid
from typing import Dict, Any, Optional, List, Tuple, Callable

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("firs_test_helper")

class FIRSTestHelper:
    """Helper class for testing FIRS API endpoints."""
    
    def __init__(self, base_url=None, api_key=None, api_secret=None):
        """Initialize test helper with optional custom credentials."""
        # Load from environment or use provided values
        self.base_url = base_url or os.environ.get("FIRS_API_URL", "https://eivc-k6z6d.ondigitalocean.app")
        self.api_key = api_key or os.environ.get("FIRS_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("FIRS_API_SECRET", "")
        
        # Get business info from environment
        self.business_name = os.environ.get("BUSINESS_NAME", "MT GARBA GLOBAL VENTURES")
        self.business_tin = os.environ.get("BUSINESS_TIN", "31569955-0001")
        self.business_service_id = os.environ.get("BUSINESS_SERVICE_ID", "94ND90NR")
        self.business_uuid = os.environ.get("BUSINESS_UUID", "71fcdd6f-3027-487b-ae38-4830b99f1cf5")
        
        # Initialize test results storage
        self.test_results = {}
        self.test_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def get_default_headers(self) -> Dict[str, str]:
        """Generate default headers for API requests."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        request_id = f"test-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "accept": "*/*",
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
            "x-timestamp": timestamp,
            "x-request-id": request_id,
            "Content-Type": "application/json"
        }
    
    def test_endpoint(self, name: str, endpoint: str, method: str = "GET", 
                     data: Dict = None, expected_status: int = 200,
                     validate_func: Optional[Callable] = None) -> Dict[str, Any]:
        """Test a FIRS API endpoint and record the result."""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_default_headers()
        
        print(f"\nTesting: {name} ({method} {url})")
        
        self.test_count += 1
        start_time = datetime.datetime.now()
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                response = requests.request(method, url, headers=headers, json=data, timeout=30)
            
            duration = (datetime.datetime.now() - start_time).total_seconds()
            
            # Check if status code matches expected
            status_ok = response.status_code == expected_status
            
            # Process response content
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_text": response.text[:500]}
            
            # Apply custom validation if provided
            validation_result = True
            validation_message = ""
            if status_ok and validate_func:
                validation_result, validation_message = validate_func(response_data)
            
            # Determine overall success
            success = status_ok and validation_result
            
            # Update counts
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
            
            # Store result
            result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "duration_seconds": duration,
                "response_data": response_data,
                "validation_message": validation_message,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.test_results[name] = result
            
            # Print result
            if success:
                print(f"✅ Success: {name} - {response.status_code} ({duration:.2f}s)")
            else:
                print(f"❌ Failed: {name} - {response.status_code} ({duration:.2f}s)")
                if validation_message:
                    print(f"   Validation error: {validation_message}")
            
            return result
            
        except Exception as e:
            duration = (datetime.datetime.now() - start_time).total_seconds()
            self.failure_count += 1
            
            # Store result
            result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "url": url,
                "success": False,
                "duration_seconds": duration,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            self.test_results[name] = result
            
            print(f"❌ Error: {name} - {str(e)} ({duration:.2f}s)")
            return result
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate a summary report of all test results."""
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_tests": self.test_count,
            "successful_tests": self.success_count,
            "failed_tests": self.failure_count,
            "success_rate": self.success_count / self.test_count if self.test_count > 0 else 0,
            "results": self.test_results
        }
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.success_count}/{self.test_count} passed ({report['success_rate']*100:.1f}%)")
        print(f"{'='*60}")
        
        # Save to file if requested
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Report saved to: {output_file}")
        
        return report


class IRNTestHelper:
    """Helper class for testing IRN generation and validation functionality."""
    
    def __init__(self, service_id=None, business_uuid=None, business_tin=None):
        """Initialize IRN test helper."""
        # Load from environment or use provided values
        self.service_id = service_id or os.environ.get("BUSINESS_SERVICE_ID", "94ND90NR")
        self.business_uuid = business_uuid or os.environ.get("BUSINESS_UUID", "71fcdd6f-3027-487b-ae38-4830b99f1cf5")
        self.business_tin = business_tin or os.environ.get("BUSINESS_TIN", "31569955-0001")
        self.business_name = os.environ.get("BUSINESS_NAME", "MT GARBA GLOBAL VENTURES")
        
        # Initialize test results
        self.test_results = {}
    
    def generate_test_irn(self, invoice_number: str, date_str: Optional[str] = None) -> str:
        """Generate a test IRN for the given invoice number and date."""
        if not date_str:
            date_str = datetime.datetime.now().strftime("%Y%m%d")
        
        return f"{invoice_number}-{self.service_id}-{date_str}"
    
    def validate_irn_format(self, irn: str) -> Tuple[bool, Optional[str]]:
        """Validate the format of an IRN."""
        try:
            # Basic format validation
            parts = irn.split('-')
            if len(parts) != 3:
                return False, "IRN must have three components separated by hyphens"
            
            invoice_number, service_id, date_str = parts
            
            # Validate invoice number
            if not invoice_number or not all(c.isalnum() or c in '-_/' for c in invoice_number):
                return False, "Invoice number must contain only alphanumeric characters and -, _, /"
            
            # Validate service ID
            if len(service_id) != 8 or not all(c.isalnum() for c in service_id):
                return False, "Service ID must be exactly 8 alphanumeric characters"
            
            # Validate date
            if not date_str.isdigit() or len(date_str) != 8:
                return False, "Date must be 8 digits in YYYYMMDD format"
            
            # Parse date
            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            
            # Check if date is valid
            datetime.datetime(year, month, day)
            
            return True, None
        except ValueError as e:
            return False, f"Date validation error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def create_test_invoice_payload(self, invoice_number: str, irn: Optional[str] = None) -> Dict[str, Any]:
        """Create a test invoice payload for IRN validation."""
        if not irn:
            irn = self.generate_test_irn(invoice_number)
        
        return {
            "business_id": self.business_uuid,
            "invoice_reference": invoice_number,
            "irn": irn,
            "invoice_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "invoice_type_code": "380",  # Commercial invoice
            "supplier": {
                "id": self.business_uuid,
                "tin": self.business_tin,
                "name": self.business_name,
                "address": "123 Tax Avenue, Lagos",
                "email": "info@taxpoynt.com"
            },
            "customer": {
                "id": str(uuid.uuid4()),
                "tin": "98765432-0001",
                "name": "Test Customer Ltd",
                "address": "456 Customer Street, Abuja",
                "email": "customer@example.com"
            },
            "invoice_items": [
                {
                    "id": "ITEM001",
                    "name": "Test Product",
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
    
    def test_irn_generation(self, invoice_numbers: List[str]) -> List[Dict[str, Any]]:
        """Test IRN generation for multiple invoice numbers."""
        results = []
        
        for invoice_number in invoice_numbers:
            start_time = datetime.datetime.now()
            
            try:
                # Generate IRN
                irn = self.generate_test_irn(invoice_number)
                
                # Validate format
                is_valid, error = self.validate_irn_format(irn)
                
                duration = (datetime.datetime.now() - start_time).total_seconds()
                
                result = {
                    "invoice_number": invoice_number,
                    "irn": irn,
                    "is_valid": is_valid,
                    "error": error,
                    "duration_seconds": duration,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                if is_valid:
                    print(f"✅ Generated valid IRN for {invoice_number}: {irn} ({duration:.2f}s)")
                else:
                    print(f"❌ Invalid IRN generated for {invoice_number}: {irn} - {error} ({duration:.2f}s)")
                
                results.append(result)
                self.test_results[invoice_number] = result
                
            except Exception as e:
                duration = (datetime.datetime.now() - start_time).total_seconds()
                
                result = {
                    "invoice_number": invoice_number,
                    "is_valid": False,
                    "error": str(e),
                    "duration_seconds": duration,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                print(f"❌ Error generating IRN for {invoice_number}: {str(e)} ({duration:.2f}s)")
                
                results.append(result)
                self.test_results[invoice_number] = result
        
        return results
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate a summary report of all test results."""
        success_count = sum(1 for r in self.test_results.values() if r.get("is_valid", False))
        total_count = len(self.test_results)
        
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_tests": total_count,
            "successful_tests": success_count,
            "failed_tests": total_count - success_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "results": self.test_results
        }
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"IRN TEST SUMMARY: {success_count}/{total_count} passed ({report['success_rate']*100:.1f}%)")
        print(f"{'='*60}")
        
        # Save to file if requested
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Report saved to: {output_file}")
        
        return report
