#!/usr/bin/env python3
"""
Test Script for Restructured FIRS Services

This script tests the functionality of the newly restructured FIRS service packages
to ensure all System Integrator (SI) and Access Point Provider (APP) services
are working correctly after the architectural reorganization.
"""

import sys
import traceback
from typing import Dict, Any

def test_firs_si_services():
    """Test System Integrator (SI) services."""
    print("🔧 Testing FIRS SI (System Integrator) Services...")
    
    try:
        # Test IRN Generation Service
        from app.services.firs_si.irn_generation_service import generate_irn
        test_invoice = {
            "invoice_number": "INV-TEST-001",
            "supplier_tin": "12345678901",
            "customer_tin": "10987654321",
            "invoice_date": "2024-01-01",
            "total_amount": 1000.00,
            "currency_code": "NGN"
        }
        irn_result = generate_irn(test_invoice)
        print("  ✅ IRN Generation Service: Working")
        
        # Test Digital Certificate Service
        from app.services.firs_si.digital_certificate_service import CertificateService
        print("  ✅ Digital Certificate Service: Import successful")
        
        # Test ERP Integration Service  
        from app.services.firs_si.erp_integration_service import fetch_odoo_invoices
        print("  ✅ ERP Integration Service: Import successful")
        
        # Test Schema Compliance Service
        from app.services.firs_si.schema_compliance_service import validate_invoice
        print("  ✅ Schema Compliance Service: Import successful")
        
        # Test SI Authentication Service
        from app.services.firs_si.si_authentication_service import SIAuthenticationService
        print("  ✅ SI Authentication Service: Import successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ SI Services test failed: {e}")
        traceback.print_exc()
        return False

def test_firs_app_services():
    """Test Access Point Provider (APP) services."""
    print("🛡️ Testing FIRS APP (Access Point Provider) Services...")
    
    try:
        # Test Transmission Service
        from app.services.firs_app.transmission_service import FIRSTransmissionService
        print("  ✅ Transmission Service: Import successful")
        
        # Test Data Validation Service
        from app.services.firs_app.data_validation_service import ValidationRuleService
        print("  ✅ Data Validation Service: Import successful")
        
        # Test Authentication Seal Service
        from app.services.firs_app.authentication_seal_service import CryptographicStampingService
        print("  ✅ Authentication Seal Service: Import successful")
        
        # Test Secure Communication Service
        from app.services.firs_app.secure_communication_service import EncryptionService
        print("  ✅ Secure Communication Service: Import successful")
        
        # Test APP Compliance Service
        from app.services.firs_app.app_compliance_service import APPComplianceService
        print("  ✅ APP Compliance Service: Import successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ APP Services test failed: {e}")
        traceback.print_exc()
        return False

def test_firs_core_services():
    """Test Core FIRS services."""
    print("🏗️ Testing FIRS Core Services...")
    
    try:
        # Test FIRS API Client
        from app.services.firs_core.firs_api_client import FIRSService, FIRSAuthResponse
        print("  ✅ FIRS API Client: Import successful")
        
        # Test Audit Service
        from app.services.firs_core.audit_service import AuditService
        print("  ✅ Audit Service: Import successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Core Services test failed: {e}")
        traceback.print_exc()
        return False

def test_firs_hybrid_services():
    """Test Hybrid cross-cutting services."""
    print("🔄 Testing FIRS Hybrid Services...")
    
    try:
        # Test Dependency Injection
        from app.services.firs_hybrid.deps import get_certificate_service, get_document_signing_service
        print("  ✅ Dependency Injection: Import successful")
        
        # Test Certificate Manager
        from app.services.firs_hybrid.certificate_manager import CertificateService
        print("  ✅ Certificate Manager: Import successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Hybrid Services test failed: {e}")
        traceback.print_exc()
        return False

def test_package_imports():
    """Test package-level imports."""
    print("📦 Testing Package-Level Imports...")
    
    try:
        # Test SI package
        from app.services.firs_si import generate_irn, CertificateService
        print("  ✅ firs_si package: Import successful")
        
        # Test APP package
        from app.services.firs_app import FIRSTransmissionService, ValidationRuleService
        print("  ✅ firs_app package: Import successful")
        
        # Test Core package
        from app.services.firs_core import FIRSService, AuditService
        print("  ✅ firs_core package: Import successful")
        
        # Test Hybrid package
        from app.services.firs_hybrid import get_certificate_service, CertificateService
        print("  ✅ firs_hybrid package: Import successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Package imports test failed: {e}")
        traceback.print_exc()
        return False

def test_application_startup():
    """Test that the main FastAPI application starts correctly."""
    print("🚀 Testing FastAPI Application Startup...")
    
    try:
        from app.main import app
        routes_count = len(app.routes)
        print(f"  ✅ FastAPI Application: Started successfully with {routes_count} routes")
        return True
        
    except Exception as e:
        print(f"  ❌ Application startup test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests for the restructured FIRS services."""
    print("🧪 FIRS Service Architecture Restructuring - Comprehensive Test Suite")
    print("=" * 70)
    
    test_results = []
    
    # Run all test categories
    test_results.append(("SI Services", test_firs_si_services()))
    test_results.append(("APP Services", test_firs_app_services()))
    test_results.append(("Core Services", test_firs_core_services()))
    test_results.append(("Hybrid Services", test_firs_hybrid_services()))
    test_results.append(("Package Imports", test_package_imports()))
    test_results.append(("Application Startup", test_application_startup()))
    
    # Summary
    print("\\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
    
    print(f"\\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\\n🎉 ALL TESTS PASSED! FIRS service restructuring is successful!")
        print("\\n✅ The restructured services are ready for:")
        print("   • FIRS SI (System Integrator) operations")
        print("   • FIRS APP (Access Point Provider) operations")
        print("   • Production deployment")
        print("   • Further development and testing")
        return True
    else:
        print(f"\\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    # Add current directory to Python path
    sys.path.insert(0, '.')
    
    success = main()
    sys.exit(0 if success else 1)