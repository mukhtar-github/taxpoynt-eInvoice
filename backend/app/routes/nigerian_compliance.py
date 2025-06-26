"""
Nigerian Compliance API Routes

This module contains FastAPI routes for managing Nigerian regulatory compliance
including NITDA accreditation, NDPR compliance, and FIRS penalty tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.models.nigerian_compliance import AccreditationStatus, ComplianceLevel
from app.services.nigerian_compliance_service import NigerianComplianceService
from app.schemas.nigerian_compliance import (
    NITDAAccreditationCreate,
    NITDAAccreditationResponse,
    NDPRComplianceResponse,
    NigerianBusinessRegistrationCreate,
    NigerianBusinessRegistrationResponse,
    FIRSPenaltyResponse,
    ComplianceOverviewResponse,
    PaymentPlanRequest,
    PaymentPlanResponse,
    DataBreachReport
)

router = APIRouter(prefix="/nigerian-compliance", tags=["Nigerian Compliance"])


@router.get("/overview/{organization_id}", response_model=ComplianceOverviewResponse)
async def get_compliance_overview(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive compliance overview for an organization."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        overview = await compliance_service.get_compliance_overview(organization_id)
        return ComplianceOverviewResponse(**overview)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance overview: {str(e)}"
        )


@router.post("/nitda-accreditation/{organization_id}", response_model=NITDAAccreditationResponse)
async def create_nitda_accreditation(
    organization_id: UUID,
    accreditation_data: NITDAAccreditationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new NITDA accreditation record."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        accreditation = await compliance_service.nitda_service.create_nitda_accreditation(
            org_id=organization_id,
            nigerian_ownership_percentage=accreditation_data.nigerian_ownership_percentage,
            cac_registration_number=accreditation_data.cac_registration_number,
            cpn_registration_status=accreditation_data.cpn_registration_status
        )
        
        return NITDAAccreditationResponse(
            id=accreditation.id,
            organization_id=accreditation.organization_id,
            accreditation_number=accreditation.accreditation_number,
            nigerian_ownership_percentage=float(accreditation.nigerian_ownership_percentage),
            cac_registration_number=accreditation.cac_registration_number,
            cpn_registration_status=accreditation.cpn_registration_status,
            status=accreditation.status.value,
            issued_date=accreditation.issued_date,
            expiry_date=accreditation.expiry_date,
            created_at=accreditation.created_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create NITDA accreditation: {str(e)}"
        )


@router.get("/nitda-accreditation/{organization_id}", response_model=Dict[str, Any])
async def verify_nitda_requirements(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify NITDA accreditation requirements for an organization."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        verification = await compliance_service.nitda_service.verify_nitda_requirements(organization_id)
        return verification
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify NITDA requirements: {str(e)}"
        )


@router.put("/nitda-accreditation/{organization_id}/status")
async def update_accreditation_status(
    organization_id: UUID,
    status: AccreditationStatus,
    accreditation_number: Optional[str] = None,
    issued_date: Optional[datetime] = None,
    expiry_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update NITDA accreditation status."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        accreditation = await compliance_service.nitda_service.update_accreditation_status(
            org_id=organization_id,
            status=status,
            accreditation_number=accreditation_number,
            issued_date=issued_date,
            expiry_date=expiry_date
        )
        
        if not accreditation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NITDA accreditation record not found"
            )
        
        return {"message": "Accreditation status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update accreditation status: {str(e)}"
        )


@router.get("/ndpr-compliance/{organization_id}", response_model=NDPRComplianceResponse)
async def get_ndpr_compliance(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get NDPR compliance status for an organization."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        compliance = await compliance_service.ndpr_service.monitor_ndpr_compliance(organization_id)
        return NDPRComplianceResponse(**compliance)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get NDPR compliance: {str(e)}"
        )


@router.post("/ndpr-compliance/{organization_id}/breach")
async def report_data_breach(
    organization_id: UUID,
    breach_report: DataBreachReport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report a data breach incident."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        compliance = await compliance_service.ndpr_service.record_data_breach(
            org_id=organization_id,
            breach_details=breach_report.dict()
        )
        
        return {
            "message": "Data breach recorded successfully",
            "compliance_id": str(compliance.id)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record data breach: {str(e)}"
        )


@router.post("/business-registration/{organization_id}", response_model=NigerianBusinessRegistrationResponse)
async def create_business_registration(
    organization_id: UUID,
    registration_data: NigerianBusinessRegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update Nigerian business registration."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        validation = await compliance_service.validate_nigerian_business_registration(
            org_id=organization_id,
            cac_number=registration_data.cac_registration_number,
            business_name=registration_data.business_name,
            tin=registration_data.firs_tin
        )
        
        return NigerianBusinessRegistrationResponse(
            validation_passed=validation["validation_passed"],
            validation_details=validation["validation_details"],
            registration_id=UUID(validation["registration_id"]),
            last_verified=validation.get("last_verified")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate business registration: {str(e)}"
        )


@router.get("/firs-penalties/{organization_id}", response_model=FIRSPenaltyResponse)
async def get_firs_penalties(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get FIRS penalty calculation for an organization."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        penalties = await compliance_service.firs_penalty_service.calculate_firs_penalties(organization_id)
        return FIRSPenaltyResponse(**penalties)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate FIRS penalties: {str(e)}"
        )


@router.post("/firs-penalties/{organization_id}")
async def create_penalty_record(
    organization_id: UUID,
    violation_type: str,
    violation_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new FIRS penalty record."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        penalty = await compliance_service.firs_penalty_service.create_penalty_record(
            org_id=organization_id,
            violation_type=violation_type,
            violation_date=violation_date
        )
        
        return {
            "message": "Penalty record created successfully",
            "penalty_id": str(penalty.id),
            "total_penalty": float(penalty.total_penalty)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create penalty record: {str(e)}"
        )


@router.post("/firs-penalties/{organization_id}/{penalty_id}/payment-plan", response_model=PaymentPlanResponse)
async def setup_payment_plan(
    organization_id: UUID,
    penalty_id: UUID,
    payment_plan: PaymentPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Setup a payment plan for FIRS penalties."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        plan = await compliance_service.firs_penalty_service.setup_payment_plan(
            org_id=organization_id,
            penalty_id=penalty_id,
            plan_type=payment_plan.plan_type
        )
        
        if "error" in plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=plan["error"]
            )
        
        return PaymentPlanResponse(**plan)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup payment plan: {str(e)}"
        )


@router.get("/compliance-dashboard/{organization_id}")
async def get_compliance_dashboard(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get compliance dashboard data for Nigerian regulations."""
    compliance_service = NigerianComplianceService(db)
    
    try:
        # Get comprehensive overview
        overview = await compliance_service.get_compliance_overview(organization_id)
        
        # Get FIRS penalties
        penalties = await compliance_service.firs_penalty_service.calculate_firs_penalties(organization_id)
        
        # Get NDPR compliance details
        ndpr = await compliance_service.ndpr_service.monitor_ndpr_compliance(organization_id)
        
        # Get NITDA verification
        nitda = await compliance_service.nitda_service.verify_nitda_requirements(organization_id)
        
        dashboard_data = {
            "compliance_overview": overview,
            "penalty_summary": penalties,
            "ndpr_details": ndpr,
            "nitda_status": nitda,
            "recommendations": [],
            "action_items": []
        }
        
        # Generate recommendations based on compliance status
        if overview["overall_compliance_score"] < 75:
            dashboard_data["recommendations"].append({
                "priority": "high",
                "title": "Improve Overall Compliance",
                "description": "Your compliance score is below the recommended threshold of 75%"
            })
        
        if not nitda.get("requirements_met", False):
            dashboard_data["action_items"].append({
                "priority": "critical",
                "title": "Complete NITDA Accreditation",
                "description": "NITDA accreditation is required for legal operation in Nigeria",
                "due_date": None
            })
        
        if penalties.get("total_penalties", 0) > 0:
            dashboard_data["action_items"].append({
                "priority": "high",
                "title": "Address FIRS Penalties",
                "description": f"Outstanding penalties: ₦{penalties['total_penalties']:,.2f}",
                "due_date": None
            })
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance dashboard: {str(e)}"
        )