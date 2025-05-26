"""
Tests for FIRS service code mapping and validation functionality.

This module provides tests for the service code mapping and validation functionality,
ensuring that Odoo product categories are correctly mapped to FIRS service codes.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Tuple, Optional

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.services.firs_service import FIRSService
from app.services.odoo_firs_service_code_mapper import OdooFIRSServiceCodeMapper
from app.services.invoice_service_code_validator import InvoiceServiceCodeValidator
from app.utils.text_similarity import calculate_similarity, preprocess_text
from app.schemas.invoice_validation import InvoiceValidationRequest, InvoiceLine

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("service_code_tests")

class ServiceCodeTestHelper:
    """Helper class for testing FIRS service code functionality."""
    
    def __init__(self):
        """Initialize the service code test helper."""
        self.firs_service = FIRSService()
        self.service_code_mapper = OdooFIRSServiceCodeMapper(self.firs_service)
        self.validator = InvoiceServiceCodeValidator(self.firs_service)
        
        # Initialize test results
        self.test_results = {}
        self.test_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    async def fetch_all_service_codes(self) -> List[Dict[str, Any]]:
        """Fetch all service codes from the FIRS API."""
        print("Fetching service codes from FIRS API...")
        try:
            service_codes = await self.firs_service.get_service_codes()
            print(f"✅ Successfully fetched {len(service_codes)} service codes")
            return service_codes
        except Exception as e:
            print(f"❌ Failed to fetch service codes: {str(e)}")
            return []
    
    async def test_service_code_retrieval(self) -> Dict[str, Any]:
        """Test retrieving service codes from the FIRS API."""
        self.test_count += 1
        name = "service_code_retrieval"
        
        try:
            service_codes = await self.firs_service.get_service_codes()
            
            # Validate response structure
            if not isinstance(service_codes, list):
                raise ValueError(f"Expected list of service codes, got {type(service_codes)}")
            
            if len(service_codes) == 0:
                raise ValueError("No service codes returned")
            
            # Validate some expected fields in service codes
            first_code = service_codes[0]
            required_fields = ["code", "description"]
            for field in required_fields:
                if field not in first_code:
                    raise ValueError(f"Required field '{field}' missing from service code")
            
            result = {
                "name": name,
                "success": True,
                "count": len(service_codes),
                "sample": service_codes[:3]
            }
            
            self.success_count += 1
            print(f"✅ Success: Service code retrieval - {len(service_codes)} codes found")
            
        except Exception as e:
            result = {
                "name": name,
                "success": False,
                "error": str(e)
            }
            
            self.failure_count += 1
            print(f"❌ Failed: Service code retrieval - {str(e)}")
        
        self.test_results[name] = result
        return result
    
    async def test_service_code_mapping(self, product_categories: List[str]) -> Dict[str, Any]:
        """Test mapping Odoo product categories to FIRS service codes."""
        self.test_count += 1
        name = "service_code_mapping"
        
        try:
            results = []
            
            for category in product_categories:
                service_code = await self.service_code_mapper.get_best_service_code_for_category(category)
                
                if service_code:
                    results.append({
                        "category": category,
                        "service_code": service_code.get("code"),
                        "description": service_code.get("description"),
                        "success": True
                    })
                    print(f"✅ Mapped '{category}' to service code '{service_code.get('code')}' ({service_code.get('description')})")
                else:
                    results.append({
                        "category": category,
                        "success": False,
                        "error": "No matching service code found"
                    })
                    print(f"❌ Failed to map '{category}' to a service code")
            
            # Calculate success rate
            success_count = sum(1 for r in results if r.get("success", False))
            success_rate = success_count / len(results) if results else 0
            
            result = {
                "name": name,
                "success": success_rate > 0.7,  # Require at least 70% success rate
                "success_rate": success_rate,
                "results": results
            }
            
            if result["success"]:
                self.success_count += 1
                print(f"✅ Success: Service code mapping - {success_count}/{len(results)} categories mapped ({success_rate*100:.1f}%)")
            else:
                self.failure_count += 1
                print(f"❌ Failed: Service code mapping - Only {success_count}/{len(results)} categories mapped ({success_rate*100:.1f}%)")
            
        except Exception as e:
            result = {
                "name": name,
                "success": False,
                "error": str(e)
            }
            
            self.failure_count += 1
            print(f"❌ Failed: Service code mapping - {str(e)}")
        
        self.test_results[name] = result
        return result
    
    async def test_text_similarity(self, text_pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Test text similarity calculation functionality."""
        self.test_count += 1
        name = "text_similarity"
        
        try:
            results = []
            
            for text1, text2 in text_pairs:
                # Calculate similarity score
                similarity = calculate_similarity(text1, text2)
                
                # Also test preprocessing
                preprocessed1 = preprocess_text(text1)
                preprocessed2 = preprocess_text(text2)
                
                results.append({
                    "text1": text1,
                    "text2": text2,
                    "similarity": similarity,
                    "preprocessed1": preprocessed1,
                    "preprocessed2": preprocessed2
                })
                
                print(f"Similarity between '{text1}' and '{text2}': {similarity:.4f}")
            
            result = {
                "name": name,
                "success": True,
                "results": results
            }
            
            self.success_count += 1
            print(f"✅ Success: Text similarity calculation")
            
        except Exception as e:
            result = {
                "name": name,
                "success": False,
                "error": str(e)
            }
            
            self.failure_count += 1
            print(f"❌ Failed: Text similarity calculation - {str(e)}")
        
        self.test_results[name] = result
        return result
    
    async def test_service_code_validation(self, mock_invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test service code validation functionality."""
        self.test_count += 1
        name = "service_code_validation"
        
        try:
            results = []
            
            for idx, invoice_data in enumerate(mock_invoices):
                # Convert to InvoiceValidationRequest
                invoice = InvoiceValidationRequest(**invoice_data)
                
                # Validate service codes
                errors, warnings = await self.validator.validate_service_codes(invoice)
                
                results.append({
                    "invoice_index": idx,
                    "invoice_id": invoice_data.get("id", f"mock-{idx}"),
                    "errors": [e.dict() for e in errors],
                    "warnings": [w.dict() for w in warnings],
                    "success": len(errors) == 0
                })
                
                if len(errors) == 0:
                    print(f"✅ Invoice {idx}: Service codes valid ({len(warnings)} warnings)")
                else:
                    print(f"❌ Invoice {idx}: {len(errors)} service code errors, {len(warnings)} warnings")
            
            # Calculate success rate
            success_count = sum(1 for r in results if r.get("success", False))
            success_rate = success_count / len(results) if results else 0
            
            result = {
                "name": name,
                "success": success_rate > 0.5,  # Require at least 50% success rate for validation
                "success_rate": success_rate,
                "results": results
            }
            
            if result["success"]:
                self.success_count += 1
                print(f"✅ Success: Service code validation - {success_count}/{len(results)} invoices valid ({success_rate*100:.1f}%)")
            else:
                self.failure_count += 1
                print(f"❌ Failed: Service code validation - Only {success_count}/{len(results)} invoices valid ({success_rate*100:.1f}%)")
            
        except Exception as e:
            result = {
                "name": name,
                "success": False,
                "error": str(e)
            }
            
            self.failure_count += 1
            print(f"❌ Failed: Service code validation - {str(e)}")
        
        self.test_results[name] = result
        return result
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate a summary report of all test results."""
        report = {
            "timestamp": asyncio.get_event_loop().time(),
            "total_tests": self.test_count,
            "successful_tests": self.success_count,
            "failed_tests": self.failure_count,
            "success_rate": self.success_count / self.test_count if self.test_count > 0 else 0,
            "results": self.test_results
        }
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SERVICE CODE TEST SUMMARY: {self.success_count}/{self.test_count} passed ({report['success_rate']*100:.1f}%)")
        print(f"{'='*60}")
        
        # Save to file if requested
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Report saved to: {output_file}")
        
        return report

# Example mock data
def create_mock_invoice(with_service_codes=True) -> Dict[str, Any]:
    """Create a mock invoice for testing."""
    invoice_lines = [
        {
            "id": "line1",
            "name": "Consulting Services",
            "quantity": 1,
            "unit_price": 50000.00,
            "total_amount": 50000.00,
            "vat_amount": 7500.00,
            "vat_rate": 7.5,
            "service_code": "301020" if with_service_codes else ""
        },
        {
            "id": "line2",
            "name": "Software Development",
            "quantity": 5,
            "unit_price": 20000.00,
            "total_amount": 100000.00,
            "vat_amount": 15000.00,
            "vat_rate": 7.5,
            "service_code": "302091" if with_service_codes else ""
        }
    ]
    
    return {
        "id": f"INV-{asyncio.get_event_loop().time()}",
        "issue_date": "2024-05-26",
        "due_date": "2024-06-25",
        "supplier": {
            "name": "Test Supplier Ltd",
            "tin": "12345678-0001",
            "address": "123 Test Street",
            "city": "Lagos",
            "country_code": "NG"
        },
        "customer": {
            "name": "Test Customer Ltd",
            "tin": "87654321-0001",
            "address": "456 Customer Avenue",
            "city": "Abuja",
            "country_code": "NG"
        },
        "invoice_lines": invoice_lines,
        "total_amount": 150000.00,
        "vat_amount": 22500.00,
        "currency_code": "NGN"
    }

# Sample product categories for testing
SAMPLE_PRODUCT_CATEGORIES = [
    "Information Technology Services",
    "Consulting Services",
    "Legal Services",
    "Accounting Services",
    "Medical Services",
    "Engineering Services",
    "Education and Training",
    "Construction Services",
    "Real Estate Services",
    "Transportation and Logistics"
]

# Sample text pairs for similarity testing
SAMPLE_TEXT_PAIRS = [
    ("Information Technology Services", "Computer Programming Services"),
    ("Accounting Services", "Bookkeeping and Auditing"),
    ("Legal Services", "Law Practice and Legal Consultation"),
    ("Construction Services", "Building and Construction"),
    ("Medical Services", "Healthcare and Medical Treatment")
]

async def run_service_code_tests():
    """Run all service code tests."""
    helper = ServiceCodeTestHelper()
    
    # Test service code retrieval
    await helper.test_service_code_retrieval()
    
    # Test service code mapping
    await helper.test_service_code_mapping(SAMPLE_PRODUCT_CATEGORIES)
    
    # Test text similarity
    await helper.test_text_similarity(SAMPLE_TEXT_PAIRS)
    
    # Test service code validation
    mock_invoices = [
        create_mock_invoice(with_service_codes=True),
        create_mock_invoice(with_service_codes=False)
    ]
    await helper.test_service_code_validation(mock_invoices)
    
    # Generate report
    helper.generate_report("testing/reports/service_code_tests.json")

if __name__ == "__main__":
    asyncio.run(run_service_code_tests())
