#!/usr/bin/env python3
"""
Test script for Nigerian Compliance Implementation

This script tests the newly implemented Nigerian compliance features including
NITDA accreditation, NDPR compliance, and FIRS penalty tracking.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Add the app directory to the Python path
sys.path.append('.')

from app.db.session import SessionLocal
from app.services.nigerian_compliance_service import NigerianComplianceService
from app.models.organization import Organization
from app.models.nigerian_compliance import AccreditationStatus, ComplianceLevel


async def test_nigerian_compliance():
    """Test the Nigerian compliance implementation."""
    
    print("🇳🇬 Testing Nigerian Compliance Implementation")
    print("=" * 50)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create test organization
        test_org = Organization(
            id=uuid4(),
            name="Test Nigerian Company Ltd",
            tax_id="123456789",
            address="Lagos, Nigeria",
            email="test@company.ng"
        )
        db.add(test_org)
        db.commit()
        db.refresh(test_org)
        
        print(f"✅ Created test organization: {test_org.name}")
        
        # Initialize compliance service
        compliance_service = NigerianComplianceService(db)
        
        # Test 1: NITDA Accreditation
        print("\n📋 Testing NITDA Accreditation...")
        
        # Create NITDA accreditation
        nitda_accreditation = await compliance_service.nitda_service.create_nitda_accreditation(
            org_id=test_org.id,
            nigerian_ownership_percentage=75.0,  # Above 51% requirement
            cac_registration_number="RC123456",
            cpn_registration_status="active"
        )
        
        print(f"✅ Created NITDA accreditation record")
        print(f"   - Ownership: {nitda_accreditation.nigerian_ownership_percentage}%")
        print(f"   - CAC Number: {nitda_accreditation.cac_registration_number}")
        print(f"   - Status: {nitda_accreditation.status.value}")
        
        # Verify NITDA requirements
        nitda_verification = await compliance_service.nitda_service.verify_nitda_requirements(test_org.id)
        print(f"✅ NITDA verification complete:")
        print(f"   - Requirements met: {nitda_verification['requirements_met']}")
        print(f"   - Status: {nitda_verification['status']}")
        
        # Test 2: NDPR Compliance
        print("\n🔐 Testing NDPR Compliance...")
        
        ndpr_compliance = await compliance_service.ndpr_service.monitor_ndpr_compliance(test_org.id)
        print(f"✅ NDPR compliance monitoring:")
        print(f"   - Compliance score: {ndpr_compliance['compliance_score']}/100")
        print(f"   - Compliance level: {ndpr_compliance['compliance_level']}")
        print(f"   - Has DPO: {ndpr_compliance['has_dpo']}")
        
        # Record a data breach incident
        breach_details = {
            "type": "unauthorized_access",
            "description": "Test breach incident for compliance testing",
            "affected_records": 10,
            "reported_to_nitda": True,
            "mitigation_actions": ["Changed passwords", "Notified users", "Increased monitoring"]
        }
        
        breach_compliance = await compliance_service.ndpr_service.record_data_breach(
            org_id=test_org.id,
            breach_details=breach_details
        )
        print(f"✅ Recorded data breach incident")
        
        # Test 3: FIRS Penalty Calculation
        print("\n💰 Testing FIRS Penalty Calculation...")
        
        # Create a penalty record for non-compliance
        violation_date = datetime.utcnow() - timedelta(days=5)  # 5 days ago
        penalty_record = await compliance_service.firs_penalty_service.create_penalty_record(
            org_id=test_org.id,
            violation_type="late_invoice_submission",
            violation_date=violation_date
        )
        
        print(f"✅ Created FIRS penalty record:")
        print(f"   - Violation type: {penalty_record.violation_type}")
        print(f"   - Days non-compliant: {penalty_record.days_non_compliant}")
        print(f"   - Total penalty: ₦{penalty_record.total_penalty:,.2f}")
        
        # Calculate penalties
        penalties = await compliance_service.firs_penalty_service.calculate_firs_penalties(test_org.id)
        print(f"✅ FIRS penalty calculation:")
        print(f"   - Total penalties: ₦{penalties['total_penalties']:,.2f}")
        print(f"   - Penalty count: {penalties['penalty_count']}")
        print(f"   - Immediate attention required: {penalties['requires_immediate_attention']}")
        
        # Test payment plan setup
        payment_plan = await compliance_service.firs_penalty_service.setup_payment_plan(
            org_id=test_org.id,
            penalty_id=penalty_record.id,
            plan_type="quarterly"
        )
        
        print(f"✅ Payment plan setup:")
        print(f"   - Plan ID: {payment_plan['payment_plan_id']}")
        print(f"   - Installments: {payment_plan['installments']}")
        print(f"   - Installment amount: ₦{payment_plan['installment_amount']:,.2f}")
        
        # Test 4: Business Registration Validation
        print("\n🏢 Testing Business Registration Validation...")
        
        validation_result = await compliance_service.validate_nigerian_business_registration(
            org_id=test_org.id,
            cac_number="RC123456",
            business_name="Test Nigerian Company Ltd",
            tin="12345678"
        )
        
        print(f"✅ Business registration validation:")
        print(f"   - Validation passed: {validation_result['validation_passed']}")
        print(f"   - CAC format valid: {validation_result['validation_details']['cac_format_valid']}")
        print(f"   - TIN format valid: {validation_result['validation_details']['tin_format_valid']}")
        
        # Test 5: Comprehensive Compliance Overview
        print("\n📊 Testing Compliance Overview...")
        
        compliance_overview = await compliance_service.get_compliance_overview(test_org.id)
        print(f"✅ Compliance overview:")
        print(f"   - Overall score: {compliance_overview['overall_compliance_score']:.2f}/100")
        print(f"   - Compliance level: {compliance_overview['compliance_level']}")
        print(f"   - Individual scores:")
        for category, score in compliance_overview['individual_scores'].items():
            print(f"     - {category.upper()}: {score}/100")
        
        print("\n🎉 All Nigerian compliance tests completed successfully!")
        
        return {
            "success": True,
            "nitda_accreditation": nitda_verification,
            "ndpr_compliance": ndpr_compliance,
            "firs_penalties": penalties,
            "business_registration": validation_result,
            "compliance_overview": compliance_overview
        }
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
        
    finally:
        # Clean up test data
        try:
            # Delete test organization and related data
            db.delete(test_org)
            db.commit()
            print(f"\n🧹 Cleaned up test data")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up test data: {str(e)}")
        
        db.close()


async def test_api_schemas():
    """Test the API schemas for validation."""
    print("\n📋 Testing API Schemas...")
    
    try:
        from app.schemas.nigerian_compliance import (
            NITDAAccreditationCreate,
            NigerianBusinessRegistrationCreate,
            PaymentPlanRequest,
            DataBreachReport
        )
        
        # Test NITDA schema
        nitda_data = NITDAAccreditationCreate(
            nigerian_ownership_percentage=75.0,
            cac_registration_number="RC123456",
            cpn_registration_status="active"
        )
        print("✅ NITDA schema validation passed")
        
        # Test business registration schema
        business_data = NigerianBusinessRegistrationCreate(
            cac_registration_number="RC123456",
            business_name="Test Company",
            firs_tin="12345678"
        )
        print("✅ Business registration schema validation passed")
        
        # Test payment plan schema
        payment_data = PaymentPlanRequest(plan_type="quarterly")
        print("✅ Payment plan schema validation passed")
        
        # Test data breach schema
        breach_data = DataBreachReport(
            type="unauthorized_access",
            description="Test breach",
            affected_records=10,
            reported_to_nitda=True,
            mitigation_actions=["Action 1", "Action 2"]
        )
        print("✅ Data breach schema validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation error: {str(e)}")
        return False


def main():
    """Main test function."""
    print("🧪 Starting Nigerian Compliance Tests")
    print("=" * 60)
    
    # Test API schemas first
    schema_result = asyncio.run(test_api_schemas())
    
    if not schema_result:
        print("❌ Schema tests failed. Aborting.")
        return
    
    # Test the main compliance functionality
    result = asyncio.run(test_nigerian_compliance())
    
    print("\n" + "=" * 60)
    if result["success"]:
        print("🎉 ALL TESTS PASSED!")
        print("\n📈 Summary:")
        print(f"   - NITDA Requirements: {'✅ Met' if result['nitda_accreditation']['requirements_met'] else '❌ Not Met'}")
        print(f"   - NDPR Compliance: {result['ndpr_compliance']['compliance_score']}/100")
        print(f"   - FIRS Penalties: ₦{result['firs_penalties']['total_penalties']:,.2f}")
        print(f"   - Overall Compliance: {result['compliance_overview']['overall_compliance_score']:.1f}/100")
    else:
        print("❌ TESTS FAILED!")
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()