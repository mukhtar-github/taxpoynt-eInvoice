"""
Nigerian Compliance Service

This service handles all Nigerian regulatory compliance requirements including
NITDA accreditation verification, NDPR compliance monitoring, and FIRS penalty calculations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.nigerian_compliance import (
    NITDAAccreditation, 
    NDPRCompliance, 
    NigerianBusinessRegistration,
    FIRSPenaltyTracking,
    ISO27001Compliance,
    AccreditationStatus,
    ComplianceLevel
)
from app.models.organization import Organization
from app.db.session import get_db


class NITDAComplianceService:
    """Service for managing NITDA accreditation compliance."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def verify_nitda_requirements(self, org_id: UUID) -> Dict[str, Any]:
        """Verify NITDA accreditation requirements."""
        accreditation = self.db.query(NITDAAccreditation).filter(
            NITDAAccreditation.organization_id == org_id
        ).first()
        
        if not accreditation:
            return {
                "status": "not_registered",
                "message": "Organization not registered for NITDA accreditation",
                "requirements_met": False
            }
        
        requirements_check = {
            "nigerian_ownership": accreditation.nigerian_ownership_percentage >= 51,
            "cac_registration": bool(accreditation.cac_registration_number),
            "cpn_registration": accreditation.cpn_registration_status == "active",
            "valid_accreditation": accreditation.status == AccreditationStatus.APPROVED,
            "not_expired": (
                accreditation.expiry_date is None or 
                accreditation.expiry_date > datetime.utcnow()
            )
        }
        
        all_requirements_met = all(requirements_check.values())
        
        return {
            "status": "compliant" if all_requirements_met else "non_compliant",
            "requirements": requirements_check,
            "requirements_met": all_requirements_met,
            "accreditation_number": accreditation.accreditation_number,
            "expiry_date": accreditation.expiry_date
        }
    
    async def create_nitda_accreditation(
        self, 
        org_id: UUID, 
        nigerian_ownership_percentage: float,
        cac_registration_number: str,
        cpn_registration_status: str = "pending"
    ) -> NITDAAccreditation:
        """Create a new NITDA accreditation record."""
        accreditation = NITDAAccreditation(
            organization_id=org_id,
            nigerian_ownership_percentage=Decimal(str(nigerian_ownership_percentage)),
            cac_registration_number=cac_registration_number,
            cpn_registration_status=cpn_registration_status,
            status=AccreditationStatus.PENDING
        )
        
        self.db.add(accreditation)
        self.db.commit()
        self.db.refresh(accreditation)
        
        return accreditation
    
    async def update_accreditation_status(
        self, 
        org_id: UUID, 
        status: AccreditationStatus,
        accreditation_number: Optional[str] = None,
        issued_date: Optional[datetime] = None,
        expiry_date: Optional[datetime] = None
    ) -> Optional[NITDAAccreditation]:
        """Update NITDA accreditation status."""
        accreditation = self.db.query(NITDAAccreditation).filter(
            NITDAAccreditation.organization_id == org_id
        ).first()
        
        if not accreditation:
            return None
        
        accreditation.status = status
        if accreditation_number:
            accreditation.accreditation_number = accreditation_number
        if issued_date:
            accreditation.issued_date = issued_date
        if expiry_date:
            accreditation.expiry_date = expiry_date
        
        self.db.commit()
        self.db.refresh(accreditation)
        
        return accreditation


class NDPRComplianceService:
    """Service for managing NDPR compliance."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def monitor_ndpr_compliance(self, org_id: UUID) -> Dict[str, Any]:
        """Monitor NDPR compliance status."""
        compliance = self.db.query(NDPRCompliance).filter(
            NDPRCompliance.organization_id == org_id
        ).first()
        
        if not compliance:
            # Create initial compliance record
            compliance = NDPRCompliance(
                organization_id=org_id,
                compliance_score=0,
                compliance_level=ComplianceLevel.NON_COMPLIANT
            )
            self.db.add(compliance)
            self.db.commit()
            self.db.refresh(compliance)
        
        # Calculate compliance score based on various factors
        score = await self._calculate_ndpr_score(compliance)
        compliance.compliance_score = score
        compliance.compliance_level = self._get_compliance_level(score)
        
        self.db.commit()
        
        return {
            "compliance_score": score,
            "compliance_level": compliance.compliance_level.value,
            "has_dpo": bool(compliance.dpo_contact),
            "last_audit": compliance.last_audit_date,
            "data_processing_documented": bool(compliance.data_processing_activities),
            "consent_management": bool(compliance.consent_records),
            "privacy_impact_assessments": bool(compliance.privacy_impact_assessments),
            "breach_incidents": len(compliance.breach_incident_log or [])
        }
    
    async def _calculate_ndpr_score(self, compliance: NDPRCompliance) -> int:
        """Calculate NDPR compliance score (0-100)."""
        score = 0
        
        # Data Protection Officer appointed (20 points)
        if compliance.dpo_contact:
            score += 20
        
        # Data processing activities documented (20 points)
        if compliance.data_processing_activities:
            score += 20
        
        # Consent management in place (20 points)
        if compliance.consent_records:
            score += 20
        
        # Privacy impact assessments conducted (20 points)
        if compliance.privacy_impact_assessments:
            score += 20
        
        # Recent audit completed (10 points)
        if compliance.last_audit_date and (
            datetime.utcnow() - compliance.last_audit_date
        ).days <= 365:
            score += 10
        
        # No recent breaches (10 points)
        recent_breaches = []
        if compliance.breach_incident_log:
            recent_breaches = [
                breach for breach in compliance.breach_incident_log
                if (datetime.utcnow() - datetime.fromisoformat(breach.get('date', '2000-01-01'))).days <= 365
            ]
        
        if len(recent_breaches) == 0:
            score += 10
        
        return min(score, 100)
    
    def _get_compliance_level(self, score: int) -> ComplianceLevel:
        """Determine compliance level based on score."""
        if score >= 90:
            return ComplianceLevel.EXCELLENT
        elif score >= 75:
            return ComplianceLevel.GOOD
        elif score >= 60:
            return ComplianceLevel.SATISFACTORY
        elif score >= 40:
            return ComplianceLevel.NEEDS_IMPROVEMENT
        else:
            return ComplianceLevel.NON_COMPLIANT
    
    async def record_data_breach(
        self, 
        org_id: UUID, 
        breach_details: Dict[str, Any]
    ) -> NDPRCompliance:
        """Record a data breach incident."""
        compliance = self.db.query(NDPRCompliance).filter(
            NDPRCompliance.organization_id == org_id
        ).first()
        
        if not compliance:
            compliance = NDPRCompliance(organization_id=org_id)
            self.db.add(compliance)
        
        breach_log = compliance.breach_incident_log or []
        breach_record = {
            "date": datetime.utcnow().isoformat(),
            "type": breach_details.get("type", "unknown"),
            "description": breach_details.get("description", ""),
            "affected_records": breach_details.get("affected_records", 0),
            "reported_to_nitda": breach_details.get("reported_to_nitda", False),
            "mitigation_actions": breach_details.get("mitigation_actions", [])
        }
        breach_log.append(breach_record)
        compliance.breach_incident_log = breach_log
        
        self.db.commit()
        self.db.refresh(compliance)
        
        return compliance


class FIRSPenaltyService:
    """Service for managing FIRS compliance penalties."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_firs_penalties(self, org_id: UUID) -> Dict[str, Any]:
        """Calculate FIRS non-compliance penalties."""
        penalties = self.db.query(FIRSPenaltyTracking).filter(
            FIRSPenaltyTracking.organization_id == org_id,
            FIRSPenaltyTracking.payment_status != "paid"
        ).all()
        
        total_penalties = Decimal('0.00')
        penalty_details = []
        
        for penalty in penalties:
            # Recalculate penalty based on current date
            days_non_compliant = (datetime.utcnow() - penalty.violation_date).days
            if days_non_compliant > 0:
                if days_non_compliant == 1:
                    calculated_penalty = penalty.first_day_penalty
                else:
                    calculated_penalty = (
                        penalty.first_day_penalty + 
                        ((days_non_compliant - 1) * penalty.subsequent_day_penalty)
                    )
                
                # Update penalty record
                penalty.days_non_compliant = days_non_compliant
                penalty.total_penalty = calculated_penalty
                
                total_penalties += calculated_penalty
                
                penalty_details.append({
                    "violation_type": penalty.violation_type,
                    "violation_date": penalty.violation_date,
                    "days_non_compliant": days_non_compliant,
                    "penalty_amount": float(calculated_penalty),
                    "payment_status": penalty.payment_status
                })
        
        self.db.commit()
        
        return {
            "total_penalties": float(total_penalties),
            "penalty_count": len(penalties),
            "penalty_details": penalty_details,
            "requires_immediate_attention": total_penalties > Decimal('5000000.00')  # ₦5M threshold
        }
    
    async def create_penalty_record(
        self, 
        org_id: UUID, 
        violation_type: str,
        violation_date: datetime
    ) -> FIRSPenaltyTracking:
        """Create a new FIRS penalty record."""
        days_non_compliant = max(1, (datetime.utcnow() - violation_date).days)
        
        first_day_penalty = Decimal('1000000.00')  # ₦1,000,000
        subsequent_day_penalty = Decimal('10000.00')  # ₦10,000
        
        if days_non_compliant == 1:
            total_penalty = first_day_penalty
        else:
            total_penalty = first_day_penalty + ((days_non_compliant - 1) * subsequent_day_penalty)
        
        penalty = FIRSPenaltyTracking(
            organization_id=org_id,
            violation_type=violation_type,
            violation_date=violation_date,
            days_non_compliant=days_non_compliant,
            first_day_penalty=first_day_penalty,
            subsequent_day_penalty=subsequent_day_penalty,
            total_penalty=total_penalty,
            payment_due_date=datetime.utcnow() + timedelta(days=30)
        )
        
        self.db.add(penalty)
        self.db.commit()
        self.db.refresh(penalty)
        
        return penalty
    
    async def setup_payment_plan(
        self, 
        org_id: UUID, 
        penalty_id: UUID,
        plan_type: str = "quarterly"
    ) -> Dict[str, Any]:
        """Setup penalty payment plan with FIRS."""
        penalty = self.db.query(FIRSPenaltyTracking).filter(
            FIRSPenaltyTracking.id == penalty_id,
            FIRSPenaltyTracking.organization_id == org_id
        ).first()
        
        if not penalty:
            return {"error": "Penalty record not found"}
        
        payment_options = {
            "immediate": {
                "discount": 0.05,  # 5% discount
                "installments": 1,
                "interest_rate": 0.0,
                "terms": "Full payment within 7 days"
            },
            "quarterly": {
                "discount": 0.0,
                "installments": 4,
                "interest_rate": 0.02,  # 2% quarterly
                "terms": "4 quarterly installments"
            },
            "monthly": {
                "discount": 0.0,
                "installments": 12,
                "interest_rate": 0.015,  # 1.5% monthly
                "terms": "12 monthly installments"
            }
        }
        
        selected_plan = payment_options.get(plan_type, payment_options["quarterly"])
        
        base_amount = penalty.total_penalty
        if selected_plan["discount"] > 0:
            final_amount = base_amount * (1 - selected_plan["discount"])
        else:
            final_amount = base_amount * (1 + selected_plan["interest_rate"])
        
        installment_amount = final_amount / selected_plan["installments"]
        
        # Generate payment plan ID
        plan_id = f"FIRS-PP-{org_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        penalty.payment_plan_id = plan_id
        
        self.db.commit()
        
        return {
            "payment_plan_id": plan_id,
            "base_penalty": float(base_amount),
            "final_amount": float(final_amount),
            "installment_amount": float(installment_amount),
            "installments": selected_plan["installments"],
            "interest_rate": selected_plan["interest_rate"],
            "discount": selected_plan["discount"],
            "terms": selected_plan["terms"]
        }


class NigerianComplianceService:
    """Main service for managing all Nigerian regulatory compliance."""
    
    def __init__(self, db: Session):
        self.db = db
        self.nitda_service = NITDAComplianceService(db)
        self.ndpr_service = NDPRComplianceService(db)
        self.firs_penalty_service = FIRSPenaltyService(db)
    
    async def get_compliance_overview(self, org_id: UUID) -> Dict[str, Any]:
        """Get comprehensive compliance overview for an organization."""
        # Get NITDA compliance
        nitda_compliance = await self.nitda_service.verify_nitda_requirements(org_id)
        
        # Get NDPR compliance
        ndpr_compliance = await self.ndpr_service.monitor_ndpr_compliance(org_id)
        
        # Get FIRS penalties
        firs_penalties = await self.firs_penalty_service.calculate_firs_penalties(org_id)
        
        # Calculate overall compliance score
        compliance_scores = {
            "nitda": 100 if nitda_compliance.get("requirements_met") else 0,
            "ndpr": ndpr_compliance.get("compliance_score", 0),
            "firs": 100 if firs_penalties.get("total_penalties", 0) == 0 else max(0, 100 - (firs_penalties.get("penalty_count", 0) * 10))
        }
        
        overall_score = sum(compliance_scores.values()) / len(compliance_scores)
        
        return {
            "overall_compliance_score": round(overall_score, 2),
            "compliance_level": self._get_overall_compliance_level(overall_score),
            "nitda_compliance": nitda_compliance,
            "ndpr_compliance": ndpr_compliance,
            "firs_penalties": firs_penalties,
            "individual_scores": compliance_scores,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _get_overall_compliance_level(self, score: float) -> str:
        """Determine overall compliance level."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "satisfactory"
        elif score >= 40:
            return "needs_improvement"
        else:
            return "non_compliant"
    
    async def validate_nigerian_business_registration(
        self, 
        org_id: UUID,
        cac_number: str,
        business_name: str,
        tin: str
    ) -> Dict[str, Any]:
        """Validate Nigerian business registration details."""
        # Check if registration already exists
        existing_registration = self.db.query(NigerianBusinessRegistration).filter(
            NigerianBusinessRegistration.organization_id == org_id
        ).first()
        
        if existing_registration:
            # Update existing registration
            existing_registration.cac_registration_number = cac_number
            existing_registration.business_name = business_name
            existing_registration.firs_tin = tin
            existing_registration.last_verified = datetime.utcnow()
            existing_registration.verification_status = "verified"
            registration = existing_registration
        else:
            # Create new registration
            registration = NigerianBusinessRegistration(
                organization_id=org_id,
                cac_registration_number=cac_number,
                business_name=business_name,
                firs_tin=tin,
                last_verified=datetime.utcnow(),
                verification_status="verified"
            )
            self.db.add(registration)
        
        self.db.commit()
        self.db.refresh(registration)
        
        # Validate format (basic validation)
        validation_results = {
            "cac_format_valid": len(cac_number) >= 6 and cac_number.startswith(('RC', 'BN', 'IT')),
            "tin_format_valid": len(tin) >= 8 and tin.isdigit(),
            "business_name_valid": len(business_name.strip()) > 0,
            "registration_active": registration.is_active
        }
        
        all_valid = all(validation_results.values())
        
        return {
            "validation_passed": all_valid,
            "validation_details": validation_results,
            "registration_id": str(registration.id),
            "last_verified": registration.last_verified.isoformat() if registration.last_verified else None
        }