#!/usr/bin/env python3
"""
Test script for Odoo integration API endpoints.

This script tests the organization Odoo data interaction API endpoints.
"""
import os
import sys
import json
import logging
import argparse
import requests
from uuid import UUID
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("odoo_api_test")

# Parse arguments
parser = argparse.ArgumentParser(description="Test Odoo integration API endpoints")
parser.add_argument("--api-url", help="Base API URL", default="http://localhost:8000/api/v1")
parser.add_argument("--organization-id", help="Organization UUID", required=True)
parser.add_argument("--integration-id", help="Integration UUID", required=True)
parser.add_argument("--token", help="Authentication token", required=True)
parser.add_argument("--output", help="Output file for results", default="odoo_api_test_results.json")
parser.add_argument("--verbose", help="Enable verbose output", action="store_true")
args = parser.parse_args()

# Validate UUIDs
try:
    org_id = UUID(args.organization_id)
    integration_id = UUID(args.integration_id)
except ValueError:
    logger.error("Invalid UUID format for organization_id or integration_id")
    sys.exit(1)


class OdooApiTester:
    """Tester for Odoo API endpoints."""
    
    def __init__(
        self, 
        api_url: str, 
        organization_id: str, 
        integration_id: str, 
        token: str,
        verbose: bool = False
    ):
        """Initialize the tester with configuration."""
        self.api_url = api_url.rstrip("/")
        self.organization_id = organization_id
        self.integration_id = integration_id
        self.auth_header = {"Authorization": f"Bearer {token}"}
        self.verbose = verbose
        self.results = {
            "organization_id": organization_id,
            "integration_id": integration_id,
            "endpoints": {}
        }
    
    def log_request(self, method: str, url: str) -> None:
        """Log request details if verbose mode is enabled."""
        if self.verbose:
            logger.info(f"Sending {method} request to {url}")
    
    def log_response(self, response: requests.Response) -> None:
        """Log response details if verbose mode is enabled."""
        if self.verbose:
            logger.info(f"Response status code: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"Response content: {json.dumps(response.json(), indent=2)}")
    
    def record_result(
        self, 
        endpoint: str, 
        success: bool, 
        status_code: int, 
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Record the test result for an endpoint."""
        self.results["endpoints"][endpoint] = {
            "success": success,
            "status_code": status_code,
            "data_sample": data[:5] if isinstance(data, list) and len(data) > 5 else data,
            "error": error
        }
    
    def test_company_info(self) -> None:
        """Test the company info endpoint."""
        endpoint = "company_info"
        url = f"{self.api_url}/organizations/{self.organization_id}/integrations/{self.integration_id}/odoo/company-info"
        
        self.log_request("GET", url)
        
        try:
            response = requests.get(url, headers=self.auth_header)
            self.log_response(response)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved company info: {data.get('name', 'Unknown')}")
                self.record_result(endpoint, True, response.status_code, data)
            else:
                error = response.json().get("detail", "Unknown error")
                logger.error(f"Failed to retrieve company info: {error}")
                self.record_result(endpoint, False, response.status_code, error=error)
        except Exception as e:
            logger.exception(f"Exception testing company info endpoint: {str(e)}")
            self.record_result(endpoint, False, 0, error=str(e))
    
    def test_invoices(self) -> None:
        """Test the invoices endpoint."""
        endpoint = "invoices"
        url = f"{self.api_url}/organizations/{self.organization_id}/integrations/{self.integration_id}/odoo/invoices"
        
        self.log_request("GET", url)
        
        try:
            response = requests.get(url, headers=self.auth_header)
            self.log_response(response)
            
            if response.status_code == 200:
                data = response.json()
                invoice_count = len(data.get("invoices", []))
                logger.info(f"Successfully retrieved {invoice_count} invoices")
                self.record_result(endpoint, True, response.status_code, data)
            else:
                error = response.json().get("detail", "Unknown error")
                logger.error(f"Failed to retrieve invoices: {error}")
                self.record_result(endpoint, False, response.status_code, error=error)
        except Exception as e:
            logger.exception(f"Exception testing invoices endpoint: {str(e)}")
            self.record_result(endpoint, False, 0, error=str(e))
    
    def test_customers(self) -> None:
        """Test the customers endpoint."""
        endpoint = "customers"
        url = f"{self.api_url}/organizations/{self.organization_id}/integrations/{self.integration_id}/odoo/customers"
        
        self.log_request("GET", url)
        
        try:
            response = requests.get(url, headers=self.auth_header)
            self.log_response(response)
            
            if response.status_code == 200:
                data = response.json()
                customer_count = len(data.get("data", []))
                logger.info(f"Successfully retrieved {customer_count} customers")
                self.record_result(endpoint, True, response.status_code, data)
            else:
                error = response.json().get("detail", "Unknown error")
                logger.error(f"Failed to retrieve customers: {error}")
                self.record_result(endpoint, False, response.status_code, error=error)
        except Exception as e:
            logger.exception(f"Exception testing customers endpoint: {str(e)}")
            self.record_result(endpoint, False, 0, error=str(e))
    
    def test_products(self) -> None:
        """Test the products endpoint."""
        endpoint = "products"
        url = f"{self.api_url}/organizations/{self.organization_id}/integrations/{self.integration_id}/odoo/products"
        
        self.log_request("GET", url)
        
        try:
            response = requests.get(url, headers=self.auth_header)
            self.log_response(response)
            
            if response.status_code == 200:
                data = response.json()
                product_count = len(data.get("data", []))
                logger.info(f"Successfully retrieved {product_count} products")
                self.record_result(endpoint, True, response.status_code, data)
            else:
                error = response.json().get("detail", "Unknown error")
                logger.error(f"Failed to retrieve products: {error}")
                self.record_result(endpoint, False, response.status_code, error=error)
        except Exception as e:
            logger.exception(f"Exception testing products endpoint: {str(e)}")
            self.record_result(endpoint, False, 0, error=str(e))
    
    def test_sync(self) -> None:
        """Test the sync endpoint."""
        endpoint = "sync"
        url = f"{self.api_url}/organizations/{self.organization_id}/integrations/{self.integration_id}/odoo/sync"
        
        self.log_request("POST", url)
        
        try:
            response = requests.post(url, headers=self.auth_header)
            self.log_response(response)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully synced data: {data.get('status', 'Unknown')}")
                self.record_result(endpoint, True, response.status_code, data)
            else:
                error = response.json().get("detail", "Unknown error")
                logger.error(f"Failed to sync data: {error}")
                self.record_result(endpoint, False, response.status_code, error=error)
        except Exception as e:
            logger.exception(f"Exception testing sync endpoint: {str(e)}")
            self.record_result(endpoint, False, 0, error=str(e))
    
    def run_all_tests(self) -> None:
        """Run all API tests."""
        logger.info("Starting Odoo API endpoint tests...")
        
        self.test_company_info()
        self.test_invoices()
        self.test_customers()
        self.test_products()
        self.test_sync()
        
        logger.info("All tests completed")
    
    def save_results(self, output_file: str) -> None:
        """Save test results to a JSON file."""
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Test results saved to {output_file}")


if __name__ == "__main__":
    tester = OdooApiTester(
        api_url=args.api_url,
        organization_id=args.organization_id,
        integration_id=args.integration_id,
        token=args.token,
        verbose=args.verbose
    )
    
    tester.run_all_tests()
    tester.save_results(args.output)
    
    # Report summary
    success_count = sum(1 for result in tester.results["endpoints"].values() if result["success"])
    total_count = len(tester.results["endpoints"])
    
    logger.info(f"Test summary: {success_count}/{total_count} endpoints passed")
    
    # Exit with status code based on test results
    sys.exit(0 if success_count == total_count else 1)
