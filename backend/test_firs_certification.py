#!/usr/bin/env python3
"""
FIRS Certification Testing Script

This script demonstrates the complete FIRS invoice lifecycle
for certification testing using the implemented services.
"""

import asyncio
import json
from datetime import date
from app.services.firs_invoice_processor import firs_invoice_processor


async def test_complete_certification_workflow():
    """
    Test the complete FIRS certification workflow.
    
    This function demonstrates all the key functionality needed
    for FIRS certification testing.
    """
    print("🚀 Starting FIRS Certification Testing")
    print("=" * 50)
    
    # Step 1: Test connectivity
    print("\n1️⃣ Testing FIRS connectivity...")
    connectivity = await firs_invoice_processor.test_firs_connectivity()
    print(f"Connectivity Status: {connectivity.get('connectivity_status')}")
    if connectivity.get('health_check', {}).get('healthy'):
        print("✅ FIRS sandbox is accessible")
    else:
        print("❌ FIRS sandbox connectivity issues")
        return
    
    # Step 2: Test resource access
    print("\n2️⃣ Testing resource access...")
    resources = await firs_invoice_processor.get_invoice_resources()
    if 'error' not in resources:
        print("✅ Successfully accessed FIRS resources")
        print(f"   - Countries: {len(resources.get('countries', {}).get('data', []))}")
        print(f"   - Invoice Types: {len(resources.get('invoice_types', {}).get('data', []))}")
        print(f"   - Currencies: {len(resources.get('currencies', {}).get('data', []))}")
    else:
        print(f"❌ Resource access failed: {resources.get('error')}")
    
    # Step 3: Test complete invoice lifecycle
    print("\n3️⃣ Testing complete invoice lifecycle...")
    
    # Sample customer data
    customer_data = {
        "party_name": "Test Customer Ltd",
        "tin": "TIN-CERT001",
        "email": "customer@testcertification.com",
        "telephone": "+2348012345678",
        "business_description": "Test customer for FIRS certification",
        "postal_address": {
            "street_name": "123 Certification Street",
            "city_name": "Lagos",
            "postal_zone": "100001",
            "country": "NG"
        }
    }
    
    # Sample invoice lines
    invoice_lines = [
        {
            "hsn_code": "CC-001",
            "product_category": "Technology Services",
            "invoiced_quantity": 1,
            "line_extension_amount": 50000.00,
            "item": {
                "name": "FIRS Certification Consulting",
                "description": "Professional services for FIRS e-invoicing certification"
            },
            "price": {
                "price_amount": 50000.00,
                "base_quantity": 1,
                "price_unit": "NGN per service"
            }
        }
    ]
    
    # Process complete lifecycle
    results = await firs_invoice_processor.process_complete_invoice_lifecycle(
        invoice_reference="CERT001",
        customer_data=customer_data,
        invoice_lines=invoice_lines,
        issue_date=date.today(),
        note="FIRS certification testing invoice"
    )
    
    print(f"\n📊 Invoice Processing Results:")
    print(f"   - Invoice Reference: {results['invoice_reference']}")
    print(f"   - IRN: {results['irn']}")
    print(f"   - Final Status: {results['status']}")
    print(f"   - Success: {results['success']}")
    
    if results['errors']:
        print(f"   - Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"     • {error}")
    
    # Print step-by-step results
    print(f"\n📋 Step-by-Step Results:")
    for step_name, step_result in results.get('steps', {}).items():
        status_code = step_result.get('code', 'N/A')
        if status_code == 200 or status_code == 201:
            print(f"   ✅ {step_name}: SUCCESS (Code {status_code})")
        else:
            print(f"   ❌ {step_name}: FAILED (Code {status_code})")
            if step_result.get('error'):
                print(f"      Error: {step_result['error'].get('public_message', 'Unknown error')}")
    
    # Step 4: Summary and recommendations
    print(f"\n🎯 Certification Status Summary:")
    if results['success']:
        print("✅ FIRS certification testing PASSED")
        print("   Your implementation is ready for FIRS certification review")
    else:
        print("⚠️  FIRS certification testing had issues")
        print("   Review the errors above and fix before certification submission")
    
    print(f"\n📝 Next Steps:")
    if results['success']:
        print("   1. Configure webhook URLs for production environment")
        print("   2. Test with production FIRS credentials")
        print("   3. Schedule FIRS certification review")
        print("   4. Document the successful test results")
    else:
        print("   1. Fix the identified issues")
        print("   2. Re-run the certification test")
        print("   3. Ensure all steps pass before proceeding")
    
    return results


async def test_individual_components():
    """Test individual components separately."""
    print("\n🔧 Testing Individual Components")
    print("=" * 40)
    
    # Test TIN verification
    print("\n📞 Testing TIN verification...")
    tin_result = await firs_invoice_processor.verify_customer_tin("29445920-4211")
    print(f"TIN verification: {'✅ SUCCESS' if tin_result.get('code') == 200 else '❌ FAILED'}")
    
    # Test party creation
    print("\n👥 Testing party creation...")
    test_party = {
        "party_name": "Certification Test Party",
        "tin": "TIN-TESTPARTY001",
        "email": "testparty@certification.com",
        "telephone": "+2348087654321",
        "business_description": "Test party for certification",
        "postal_address": {
            "street_name": "456 Test Avenue",
            "city_name": "Abuja",
            "postal_zone": "900001",
            "country": "NG"
        }
    }
    
    party_result = await firs_invoice_processor.create_customer_party(test_party)
    print(f"Party creation: {'✅ SUCCESS' if party_result.get('code') == 201 else '❌ FAILED'}")
    
    if party_result.get('code') == 201:
        party_data = party_result.get('data', {}).get('item', {})
        print(f"   Created Party ID: {party_data.get('id')}")
        print(f"   Party Name: {party_data.get('party_name')}")


def print_usage_examples():
    """Print usage examples for the API endpoints."""
    print("\n📚 API Usage Examples")
    print("=" * 30)
    
    examples = {
        "Health Check": "GET /api/v1/firs-certification/health-check",
        "Complete Invoice Test": "POST /api/v1/firs-certification/process-complete-invoice",
        "IRN Validation": "POST /api/v1/firs-certification/validate-irn",
        "TIN Verification": "POST /api/v1/firs-certification/verify-tin",
        "Create Party": "POST /api/v1/firs-certification/create-party",
        "Get Countries": "GET /api/v1/firs-certification/resources/countries",
        "Get Invoice Types": "GET /api/v1/firs-certification/resources/invoice-types",
        "All Resources": "GET /api/v1/firs-certification/resources/all",
        "Configuration": "GET /api/v1/firs-certification/configuration"
    }
    
    for name, endpoint in examples.items():
        print(f"   {name}: {endpoint}")
    
    print(f"\n🔗 Webhook Endpoints:")
    webhook_examples = {
        "Invoice Status": "POST /api/v1/webhooks/firs-certification/invoice-status",
        "Transmission Status": "POST /api/v1/webhooks/firs-certification/transmission-status",
        "Validation Result": "POST /api/v1/webhooks/firs-certification/validation-result"
    }
    
    for name, endpoint in webhook_examples.items():
        print(f"   {name}: {endpoint}")


async def main():
    """Main testing function."""
    print("🇳🇬 TaxPoynt FIRS Certification Testing Suite")
    print("=" * 50)
    print("This script tests the complete FIRS certification implementation")
    print("using the sandbox environment and tested credentials.")
    
    # Test complete workflow
    workflow_results = await test_complete_certification_workflow()
    
    # Test individual components
    await test_individual_components()
    
    # Print usage examples
    print_usage_examples()
    
    print(f"\n🏁 Testing Complete!")
    print("=" * 20)
    
    return workflow_results


if __name__ == "__main__":
    # Run the certification testing
    results = asyncio.run(main())
    
    # Exit with appropriate code
    exit_code = 0 if results.get('success') else 1
    exit(exit_code)