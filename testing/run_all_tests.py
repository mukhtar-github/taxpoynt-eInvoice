#!/usr/bin/env python3
"""
TaxPoynt eInvoice Comprehensive Test Suite

This script runs a comprehensive set of tests for the TaxPoynt eInvoice system,
covering FIRS API integration, IRN generation and validation, service code mapping,
and more.
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import testing framework
from framework.test_helpers import FIRSTestHelper, IRNTestHelper
from framework.test_service_codes import ServiceCodeTestHelper, run_service_code_tests

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_runner")

def create_report_dir():
    """Create the reports directory if it doesn't exist."""
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def get_timestamp_str():
    """Get a timestamp string for report filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def run_firs_api_tests(output_file: Optional[str] = None):
    """Run tests for FIRS API interactions."""
    print("\n" + "="*80)
    print("RUNNING FIRS API TESTS")
    print("="*80)
    
    helper = FIRSTestHelper()
    
    # Test endpoints
    helper.test_endpoint("Get Countries", "/api/v1/countries", "GET")
    helper.test_endpoint("Get Currencies", "/api/v1/currencies", "GET")
    helper.test_endpoint("Get Tax Categories", "/api/v1/tax-categories", "GET")
    helper.test_endpoint("Get Payment Means", "/api/v1/payment-means", "GET")
    helper.test_endpoint("Get Invoice Types", "/api/v1/invoice-types", "GET")
    helper.test_endpoint("Get Service Codes", "/api/v1/service-codes", "GET")
    
    # Test IRN validation endpoint
    sample_irn = "INV12345-94ND90NR-20240526"
    helper.test_endpoint(
        "Validate IRN", 
        "/api/v1/irn/validate", 
        "POST",
        data={"irn": sample_irn},
        expected_status=200  # Assuming the endpoint returns 200 even for invalid IRNs
    )
    
    # Generate report
    if not output_file:
        timestamp = get_timestamp_str()
        output_file = f"testing/reports/firs_api_tests_{timestamp}.json"
    
    helper.generate_report(output_file)
    return helper.test_results

def run_irn_tests(output_file: Optional[str] = None):
    """Run tests for IRN generation and validation."""
    print("\n" + "="*80)
    print("RUNNING IRN GENERATION AND VALIDATION TESTS")
    print("="*80)
    
    helper = IRNTestHelper()
    
    # Test IRN generation with various invoice numbers
    invoice_numbers = [
        "INV12345",
        "INVOICE/2024/001",
        "CRD-20240526-001",
        "SLS_2024_05_26_1",
        "TAXPOYNT-INV-001"
    ]
    
    helper.test_irn_generation(invoice_numbers)
    
    # Generate report
    if not output_file:
        timestamp = get_timestamp_str()
        output_file = f"testing/reports/irn_tests_{timestamp}.json"
    
    helper.generate_report(output_file)
    return helper.test_results

async def run_all_tests():
    """Run all test suites and generate a comprehensive report."""
    timestamp = get_timestamp_str()
    reports_dir = create_report_dir()
    
    print("\n" + "="*80)
    print(f"STARTING COMPREHENSIVE TEST SUITE - {datetime.now().isoformat()}")
    print("="*80)
    
    # Run all test suites
    firs_api_results = await run_firs_api_tests(f"{reports_dir}/firs_api_tests_{timestamp}.json")
    irn_results = run_irn_tests(f"{reports_dir}/irn_tests_{timestamp}.json")
    
    # Run service code tests
    service_code_helper = ServiceCodeTestHelper()
    await service_code_helper.test_service_code_retrieval()
    await service_code_helper.test_service_code_mapping([
        "Information Technology Services",
        "Consulting Services",
        "Legal Services",
        "Accounting Services",
        "Medical Services"
    ])
    service_code_results = service_code_helper.generate_report(f"{reports_dir}/service_code_tests_{timestamp}.json")
    
    # Create combined report
    combined_report = {
        "timestamp": datetime.now().isoformat(),
        "firs_api_tests": {
            "success_count": sum(1 for r in firs_api_results.values() if r.get("success", False)),
            "total_count": len(firs_api_results),
            "results": firs_api_results
        },
        "irn_tests": {
            "success_count": sum(1 for r in irn_results.values() if r.get("is_valid", False)),
            "total_count": len(irn_results),
            "results": irn_results
        },
        "service_code_tests": service_code_results
    }
    
    # Calculate overall success metrics
    total_tests = (
        combined_report["firs_api_tests"]["total_count"] + 
        combined_report["irn_tests"]["total_count"] + 
        service_code_results["total_tests"]
    )
    
    successful_tests = (
        combined_report["firs_api_tests"]["success_count"] + 
        combined_report["irn_tests"]["success_count"] + 
        service_code_results["successful_tests"]
    )
    
    combined_report["total_tests"] = total_tests
    combined_report["successful_tests"] = successful_tests
    combined_report["failed_tests"] = total_tests - successful_tests
    combined_report["success_rate"] = successful_tests / total_tests if total_tests > 0 else 0
    
    # Save combined report
    combined_report_path = f"{reports_dir}/combined_report_{timestamp}.json"
    with open(combined_report_path, 'w') as f:
        json.dump(combined_report, f, indent=2, default=str)
    
    # Print final summary
    print("\n" + "="*80)
    print(f"COMPREHENSIVE TEST SUMMARY - {datetime.now().isoformat()}")
    print(f"Total Tests: {total_tests}")
    print(f"Successful Tests: {successful_tests}")
    print(f"Failed Tests: {total_tests - successful_tests}")
    print(f"Success Rate: {(combined_report['success_rate']*100):.1f}%")
    print(f"Combined Report: {combined_report_path}")
    print("="*80)
    
    return combined_report

def generate_html_report(json_report_path):
    """Generate an HTML report from a JSON report file."""
    with open(json_report_path, 'r') as f:
        data = json.load(f)
    
    html_path = json_report_path.replace('.json', '.html')
    
    with open(html_path, 'w') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaxPoynt eInvoice Test Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px 5px 0 0;
        }
        .summary {
            background-color: #ecf0f1;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 0 0 5px 5px;
        }
        .test-group {
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .test-group-header {
            background-color: #3498db;
            color: white;
            padding: 10px 20px;
            border-radius: 5px 5px 0 0;
        }
        .test-list {
            padding: 20px;
        }
        .test-item {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 5px;
        }
        .success {
            background-color: #e6f7e6;
            border-left: 4px solid #2ecc71;
        }
        .failure {
            background-color: #faebeb;
            border-left: 4px solid #e74c3c;
        }
        .detail-section {
            margin-top: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 3px;
        }
        .progress-bar {
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .progress {
            height: 100%;
            background-color: #2ecc71;
            border-radius: 10px;
            text-align: center;
            line-height: 20px;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TaxPoynt eInvoice Test Report</h1>
            <p>Generated: """ + data.get("timestamp", datetime.now().isoformat()) + """</p>
        </div>
        
        <div class="summary">
            <h2>Test Summary</h2>
            <div class="progress-bar">
                <div class="progress" style="width: """ + str(round(data.get("success_rate", 0) * 100)) + """%;">
                    """ + str(round(data.get("success_rate", 0) * 100)) + """%
                </div>
            </div>
            <p>Total Tests: """ + str(data.get("total_tests", 0)) + """</p>
            <p>Successful Tests: """ + str(data.get("successful_tests", 0)) + """</p>
            <p>Failed Tests: """ + str(data.get("failed_tests", 0)) + """</p>
        </div>
        """)
        
        # Add FIRS API Test Results
        if "firs_api_tests" in data:
            firs_api = data["firs_api_tests"]
            f.write("""
        <div class="test-group">
            <div class="test-group-header">
                <h2>FIRS API Tests</h2>
                <p>Success Rate: """ + str(round((firs_api.get("success_count", 0) / max(firs_api.get("total_count", 1), 1)) * 100)) + """%</p>
            </div>
            <div class="test-list">
            """)
            
            for name, result in firs_api.get("results", {}).items():
                success = result.get("success", False)
                status_class = "success" if success else "failure"
                status_text = "Success" if success else "Failure"
                
                f.write(f"""
                <div class="test-item {status_class}">
                    <h3>{name} - {status_text}</h3>
                    <p>Endpoint: {result.get("endpoint", "N/A")}</p>
                    <p>Status Code: {result.get("status_code", "N/A")}</p>
                    <p>Duration: {result.get("duration_seconds", "N/A")} seconds</p>
                </div>
                """)
            
            f.write("""
            </div>
        </div>
            """)
        
        # Add IRN Test Results
        if "irn_tests" in data:
            irn_tests = data["irn_tests"]
            f.write("""
        <div class="test-group">
            <div class="test-group-header">
                <h2>IRN Generation and Validation Tests</h2>
                <p>Success Rate: """ + str(round((irn_tests.get("success_count", 0) / max(irn_tests.get("total_count", 1), 1)) * 100)) + """%</p>
            </div>
            <div class="test-list">
            """)
            
            for invoice_number, result in irn_tests.get("results", {}).items():
                is_valid = result.get("is_valid", False)
                status_class = "success" if is_valid else "failure"
                status_text = "Valid" if is_valid else "Invalid"
                
                f.write(f"""
                <div class="test-item {status_class}">
                    <h3>Invoice Number: {invoice_number} - {status_text}</h3>
                    <p>IRN: {result.get("irn", "N/A")}</p>
                    <p>Duration: {result.get("duration_seconds", "N/A")} seconds</p>
                    {f"<p>Error: {result.get('error', 'N/A')}</p>" if result.get("error") else ""}
                </div>
                """)
            
            f.write("""
            </div>
        </div>
            """)
        
        # Add Service Code Test Results
        if "service_code_tests" in data:
            service_tests = data["service_code_tests"]
            f.write("""
        <div class="test-group">
            <div class="test-group-header">
                <h2>Service Code Tests</h2>
                <p>Success Rate: """ + str(round((service_tests.get("successful_tests", 0) / max(service_tests.get("total_tests", 1), 1)) * 100)) + """%</p>
            </div>
            <div class="test-list">
            """)
            
            for name, result in service_tests.get("results", {}).items():
                success = result.get("success", False)
                status_class = "success" if success else "failure"
                status_text = "Success" if success else "Failure"
                
                f.write(f"""
                <div class="test-item {status_class}">
                    <h3>{name} - {status_text}</h3>
                """)
                
                if "count" in result:
                    f.write(f"<p>Service Codes Found: {result.get('count', 'N/A')}</p>")
                
                if "success_rate" in result:
                    f.write(f"<p>Success Rate: {result.get('success_rate', 0) * 100:.1f}%</p>")
                
                if "error" in result:
                    f.write(f"<p>Error: {result.get('error', 'N/A')}</p>")
                
                f.write("""
                </div>
                """)
            
            f.write("""
            </div>
        </div>
            """)
        
        f.write("""
    </div>
</body>
</html>
        """)
    
    print(f"HTML report generated: {html_path}")
    return html_path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run TaxPoynt eInvoice tests")
    parser.add_argument(
        "--html", 
        action="store_true", 
        help="Generate HTML report in addition to JSON"
    )
    parser.add_argument(
        "--api-only", 
        action="store_true", 
        help="Run only FIRS API tests"
    )
    parser.add_argument(
        "--irn-only", 
        action="store_true", 
        help="Run only IRN generation and validation tests"
    )
    parser.add_argument(
        "--service-codes-only", 
        action="store_true", 
        help="Run only service code tests"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.api_only:
        asyncio.run(run_firs_api_tests())
    elif args.irn_only:
        run_irn_tests()
    elif args.service_codes_only:
        asyncio.run(run_service_code_tests())
    else:
        # Run all tests
        report = asyncio.run(run_all_tests())
        
        # Generate HTML report if requested
        if args.html:
            timestamp = get_timestamp_str()
            reports_dir = create_report_dir()
            combined_report_path = f"{reports_dir}/combined_report_{timestamp}.json"
            generate_html_report(combined_report_path)
