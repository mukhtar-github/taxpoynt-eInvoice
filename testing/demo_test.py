#!/usr/bin/env python3
"""
Demo Test Script for TaxPoynt eInvoice

This script provides a simplified demonstration of the testing framework,
focusing on the key components that were implemented for FIRS integration.
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import from the framework
from framework.test_helpers import FIRSTestHelper
from framework.test_service_codes import ServiceCodeTestHelper, SAMPLE_PRODUCT_CATEGORIES

async def run_demo():
    """Run a demonstration of key test components."""
    print("\n" + "="*80)
    print("TAXPOYNT EINVOICE FIRS INTEGRATION DEMO")
    print("="*80)
    
    # Create report directory
    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Service Code Retrieval Demo
    print("\n" + "="*60)
    print("1. FIRS Service Code Retrieval Demo")
    print("="*60)
    
    service_helper = ServiceCodeTestHelper()
    await service_helper.test_service_code_retrieval()
    
    # 2. Service Code Mapping Demo
    print("\n" + "="*60)
    print("2. Intelligent Service Code Mapping Demo")
    print("="*60)
    
    demo_categories = [
        "Information Technology Services",
        "Software Development",
        "Accounting and Bookkeeping",
        "Legal Consultation",
        "Medical Services"
    ]
    
    await service_helper.test_service_code_mapping(demo_categories)
    
    # 3. FIRS API Reference Data Demo
    print("\n" + "="*60)
    print("3. FIRS API Reference Data Demo")
    print("="*60)
    
    api_helper = FIRSTestHelper()
    api_helper.test_endpoint("Get Countries", "/api/v1/countries", "GET")
    api_helper.test_endpoint("Get Currencies", "/api/v1/currencies", "GET")
    api_helper.test_endpoint("Get Tax Categories", "/api/v1/tax-categories", "GET")
    
    # 4. Generate Reports
    print("\n" + "="*60)
    print("4. Generating Demo Reports")
    print("="*60)
    
    # Save API test results
    api_report = api_helper.generate_report(f"reports/demo_api_tests_{timestamp}.json")
    
    # Save service code test results
    service_report = service_helper.generate_report(f"reports/demo_service_code_tests_{timestamp}.json")
    
    # Create combined HTML report
    generate_html_demo_report(
        api_report, 
        service_report, 
        f"reports/demo_report_{timestamp}.html"
    )
    
    print(f"\nDemo HTML report available at: reports/demo_report_{timestamp}.html")
    
    return {
        "api_report": api_report,
        "service_report": service_report,
        "html_report": f"reports/demo_report_{timestamp}.html"
    }

def generate_html_demo_report(api_report, service_report, output_path):
    """Generate a simple HTML demo report."""
    with open(output_path, 'w') as f:
        f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaxPoynt eInvoice FIRS Integration Demo</title>
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
            text-align: center;
        }
        .summary {
            background-color: #ecf0f1;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 0 0 5px 5px;
        }
        .section {
            margin-bottom: 30px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .section-header {
            background-color: #3498db;
            color: white;
            padding: 10px 20px;
            border-radius: 5px 5px 0 0;
        }
        .section-content {
            padding: 20px;
        }
        .feature {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .success {
            background-color: #e6f7e6;
            border-left: 4px solid #2ecc71;
        }
        .failure {
            background-color: #faebeb;
            border-left: 4px solid #e74c3c;
        }
        .code {
            font-family: monospace;
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            overflow: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TaxPoynt eInvoice FIRS Integration Demo</h1>
            <p>Generated: """ + datetime.now().isoformat() + """</p>
        </div>
        
        <div class="summary">
            <h2>Demo Summary</h2>
            <p>This demonstration showcases the key components of the TaxPoynt eInvoice FIRS integration, focusing on:</p>
            <ul>
                <li>Service Code Retrieval and Mapping</li>
                <li>FIRS API Integration</li>
                <li>Comprehensive Testing Framework</li>
            </ul>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>1. FIRS Service Code Integration</h2>
            </div>
            <div class="section-content">
                <div class="feature">
                    <h3>Service Code Retrieval</h3>
                    <p>The system can retrieve service codes from the FIRS API and cache them for efficient reuse.</p>
                    <div class="code">
                    <pre>
# Sample service code structure
{
  "code": "301020",
  "description": "Accounting and Bookkeeping Services"
}</pre>
                    </div>
                </div>
                
                <div class="feature">
                    <h3>Intelligent Service Code Mapping</h3>
                    <p>Using text similarity algorithms, the system can map Odoo product categories to appropriate FIRS service codes.</p>
                    <div class="code">
                    <pre>
# Example mappings
"Information Technology Services" → "302091" (IT Support and Services)
"Legal Consultation" → "304010" (Legal Services)
"Accounting and Bookkeeping" → "301020" (Accounting and Bookkeeping Services)</pre>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>2. Comprehensive Testing Framework</h2>
            </div>
            <div class="section-content">
                <div class="feature">
                    <h3>API Test Results</h3>
                    <p>Summary of FIRS API integration tests:</p>
                    <ul>
                        <li>Total API Tests: """ + str(len(api_report.get("results", {}))) + """</li>
                        <li>Successful Tests: """ + str(api_report.get("successful_tests", 0)) + """</li>
                        <li>Success Rate: """ + str(round(api_report.get("success_rate", 0) * 100, 1)) + """%</li>
                    </ul>
                </div>
                
                <div class="feature">
                    <h3>Service Code Test Results</h3>
                    <p>Summary of service code mapping tests:</p>
                    <ul>
                        <li>Total Service Code Tests: """ + str(service_report.get("total_tests", 0)) + """</li>
                        <li>Successful Tests: """ + str(service_report.get("successful_tests", 0)) + """</li>
                        <li>Success Rate: """ + str(round(service_report.get("success_rate", 0) * 100, 1)) + """%</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2>3. Future Enhancements</h2>
            </div>
            <div class="section-content">
                <div class="feature">
                    <h3>Planned Improvements</h3>
                    <p>The following enhancements are planned for the next iteration:</p>
                    <ul>
                        <li>Automated CI/CD pipeline integration</li>
                        <li>Performance testing for high-volume invoice processing</li>
                        <li>Enhanced error handling and reporting</li>
                        <li>User interface for test result visualization</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """)
    
    print(f"HTML demo report generated: {output_path}")

if __name__ == "__main__":
    asyncio.run(run_demo())
