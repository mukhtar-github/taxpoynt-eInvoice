"""
Nigerian Compliance Pydantic Schemas

This module contains Pydantic schemas for Nigerian compliance API endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class NITDAAccreditationCreate(BaseModel):
    """Schema for creating NITDA accreditation."""
    nigerian_ownership_percentage: float = Field(..., ge=0, le=100, description="Nigerian ownership percentage")
    cac_registration_number: str = Field(..., description="Corporate Affairs Commission registration number")
    cpn_registration_status: str = Field(default="pending", description="Computer Professionals registration status")
    
    @validator('nigerian_ownership_percentage')
    def validate_ownership(cls, v):
        if v < 51:
            raise ValueError('Nigerian ownership must be at least 51% for NITDA accreditation')
        return v


class NITDAAccreditationResponse(BaseModel):
    """Schema for NITDA accreditation response."""
    id: UUID
    organization_id: UUID
    accreditation_number: Optional[str]
    nigerian_ownership_percentage: float
    cac_registration_number: str
    cpn_registration_status: str
    status: str
    issued_date: Optional[datetime]
    expiry_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class NDPRComplianceResponse(BaseModel):
    """Schema for NDPR compliance response."""
    compliance_score: int = Field(..., ge=0, le=100)
    compliance_level: str
    has_dpo: bool
    last_audit: Optional[datetime]
    data_processing_documented: bool
    consent_management: bool
    privacy_impact_assessments: bool
    breach_incidents: int
    
    class Config:
        from_attributes = True


class DataBreachReport(BaseModel):
    """Schema for reporting data breaches."""
    type: str = Field(..., description="Type of data breach")
    description: str = Field(..., description="Description of the breach")
    affected_records: int = Field(default=0, description="Number of affected records")
    reported_to_nitda: bool = Field(default=False, description="Whether breach was reported to NITDA")
    mitigation_actions: List[str] = Field(default=[], description="Actions taken to mitigate the breach")


class NigerianBusinessRegistrationCreate(BaseModel):
    """Schema for creating Nigerian business registration."""
    cac_registration_number: str = Field(..., description="CAC registration number")
    business_name: str = Field(..., description="Business name")
    firs_tin: str = Field(..., description="FIRS Tax Identification Number")
    business_type: Optional[str] = Field(None, description="Type of business")
    operating_state: Optional[str] = Field(None, description="Operating state in Nigeria")
    local_government_area: Optional[str] = Field(None, description="Local Government Area")
    
    @validator('cac_registration_number')
    def validate_cac_number(cls, v):
        if not v or len(v) < 6:
            raise ValueError('CAC registration number must be at least 6 characters')
        if not v.startswith(('RC', 'BN', 'IT')):
            raise ValueError('CAC registration number must start with RC, BN, or IT')
        return v
    
    @validator('firs_tin')
    def validate_tin(cls, v):
        if not v or len(v) < 8:
            raise ValueError('TIN must be at least 8 characters')
        return v


class NigerianBusinessRegistrationResponse(BaseModel):
    """Schema for Nigerian business registration response."""
    validation_passed: bool
    validation_details: Dict[str, bool]
    registration_id: UUID
    last_verified: Optional[str]
    
    class Config:
        from_attributes = True


class PenaltyDetail(BaseModel):
    """Schema for penalty details."""
    violation_type: str
    violation_date: datetime
    days_non_compliant: int
    penalty_amount: float
    payment_status: str


class FIRSPenaltyResponse(BaseModel):
    """Schema for FIRS penalty response."""
    total_penalties: float
    penalty_count: int
    penalty_details: List[PenaltyDetail]
    requires_immediate_attention: bool
    
    class Config:
        from_attributes = True


class PaymentPlanRequest(BaseModel):
    """Schema for payment plan request."""
    plan_type: str = Field(..., description="Type of payment plan: immediate, quarterly, monthly")
    
    @validator('plan_type')
    def validate_plan_type(cls, v):
        if v not in ['immediate', 'quarterly', 'monthly']:
            raise ValueError('Plan type must be immediate, quarterly, or monthly')
        return v


class PaymentPlanResponse(BaseModel):
    """Schema for payment plan response."""
    payment_plan_id: str
    base_penalty: float
    final_amount: float
    installment_amount: float
    installments: int
    interest_rate: float
    discount: float
    terms: str
    
    class Config:
        from_attributes = True


class ComplianceScore(BaseModel):
    """Schema for individual compliance scores."""
    nitda: int = Field(..., ge=0, le=100)
    ndpr: int = Field(..., ge=0, le=100)
    firs: int = Field(..., ge=0, le=100)


class ComplianceOverviewResponse(BaseModel):
    """Schema for comprehensive compliance overview."""
    overall_compliance_score: float = Field(..., ge=0, le=100)
    compliance_level: str
    nitda_compliance: Dict[str, Any]
    ndpr_compliance: Dict[str, Any]
    firs_penalties: Dict[str, Any]
    individual_scores: Dict[str, int]
    last_updated: str
    
    class Config:
        from_attributes = True


class ComplianceRecommendation(BaseModel):
    """Schema for compliance recommendations."""
    priority: str = Field(..., description="Priority level: low, medium, high, critical")
    title: str
    description: str
    estimated_effort: Optional[str] = None
    deadline: Optional[datetime] = None


class ComplianceActionItem(BaseModel):
    """Schema for compliance action items."""
    priority: str = Field(..., description="Priority level: low, medium, high, critical")
    title: str
    description: str
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    status: str = Field(default="pending", description="Status: pending, in_progress, completed")


class ComplianceDashboardResponse(BaseModel):
    """Schema for compliance dashboard response."""
    compliance_overview: ComplianceOverviewResponse
    penalty_summary: FIRSPenaltyResponse
    ndpr_details: NDPRComplianceResponse
    nitda_status: Dict[str, Any]
    recommendations: List[ComplianceRecommendation]
    action_items: List[ComplianceActionItem]
    
    class Config:
        from_attributes = True


class ISO27001ComplianceResponse(BaseModel):
    """Schema for ISO 27001 compliance response."""
    certificate_number: Optional[str]
    certification_body: Optional[str]
    issue_date: Optional[datetime]
    expiry_date: Optional[datetime]
    overall_compliance_score: int = Field(..., ge=0, le=100)
    compliance_level: str
    last_audit_date: Optional[datetime]
    next_audit_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class NigerianStateInfo(BaseModel):
    """Schema for Nigerian state information."""
    code: str
    name: str
    capital: str
    region: str
    internal_revenue_service: str
    tax_rates: Dict[str, float]
    major_lgas: List[str]


class TaxJurisdictionResponse(BaseModel):
    """Schema for Nigerian tax jurisdiction response."""
    federal_taxes: List[Dict[str, Any]]
    state_taxes: List[Dict[str, Any]]
    local_taxes: List[Dict[str, Any]]
    total_tax_amount: float
    effective_tax_rate: float
    
    class Config:
        from_attributes = True