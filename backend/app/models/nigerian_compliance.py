"""
Nigerian Compliance Models

This module contains data models for tracking Nigerian regulatory compliance 
requirements including NITDA accreditation and NDPR compliance.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, Numeric, Enum, func, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from enum import Enum as PyEnum

from app.db.base_class import Base


class AccreditationStatus(PyEnum):
    """Status options for NITDA accreditation"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class ComplianceLevel(PyEnum):
    """Compliance assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    NEEDS_IMPROVEMENT = "needs_improvement"
    NON_COMPLIANT = "non_compliant"


class NITDAAccreditation(Base):
    """Model for tracking NITDA accreditation status."""
    __tablename__ = "nitda_accreditations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    accreditation_number = Column(String(50), unique=True, nullable=True)
    nigerian_ownership_percentage = Column(Numeric(5, 2), nullable=False)
    cac_registration_number = Column(String(20), nullable=True)  # Corporate Affairs Commission
    cbn_license_status = Column(String(20), nullable=True)  # Central Bank of Nigeria
    cpn_registration_status = Column(String(20), nullable=True)  # Computer Professionals
    status = Column(Enum(AccreditationStatus), default=AccreditationStatus.PENDING)
    issued_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    compliance_requirements = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="nitda_accreditations")


class NDPRCompliance(Base):
    """Nigerian Data Protection Regulation compliance tracking."""
    __tablename__ = "ndpr_compliance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    data_processing_activities = Column(JSONB, nullable=True)
    consent_records = Column(JSONB, nullable=True)
    privacy_impact_assessments = Column(JSONB, nullable=True)
    breach_incident_log = Column(JSONB, nullable=True)
    dpo_contact = Column(String, nullable=True)  # Data Protection Officer
    last_audit_date = Column(DateTime, nullable=True)
    compliance_score = Column(Integer, default=0)
    compliance_level = Column(Enum(ComplianceLevel), default=ComplianceLevel.NEEDS_IMPROVEMENT)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="ndpr_compliance")


class NigerianBusinessRegistration(Base):
    """Model for tracking Nigerian business registration details."""
    __tablename__ = "nigerian_business_registrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Corporate Affairs Commission (CAC) Details
    cac_registration_number = Column(String(20), nullable=True)
    business_name = Column(String(255), nullable=False)
    registration_date = Column(DateTime, nullable=True)
    business_type = Column(String(50), nullable=True)  # Limited Company, Partnership, etc.
    
    # Tax Identification
    firs_tin = Column(String(20), nullable=True)  # Federal Inland Revenue Service TIN
    state_tax_id = Column(String(20), nullable=True)
    local_government_tax_id = Column(String(20), nullable=True)
    
    # Location Details
    operating_state = Column(String(50), nullable=True)  # Lagos, Kano, Rivers, etc.
    local_government_area = Column(String(100), nullable=True)
    registered_address = Column(Text, nullable=True)
    
    # Business Activities
    primary_business_activity = Column(String(255), nullable=True)
    business_sector = Column(String(100), nullable=True)  # Manufacturing, Services, etc.
    annual_revenue_ngn = Column(Numeric(15, 2), nullable=True)
    employee_count = Column(Integer, nullable=True)
    
    # Compliance Status
    is_active = Column(Boolean, default=True)
    last_verified = Column(DateTime, nullable=True)
    verification_status = Column(String(20), default="pending")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="nigerian_business_registrations")


class FIRSPenaltyTracking(Base):
    """Model for tracking FIRS compliance penalties."""
    __tablename__ = "firs_penalty_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Penalty Details
    violation_type = Column(String(100), nullable=False)
    violation_date = Column(DateTime, nullable=False)
    days_non_compliant = Column(Integer, default=0)
    
    # Penalty Calculation
    first_day_penalty = Column(Numeric(12, 2), default=1000000.00)  # ₦1,000,000
    subsequent_day_penalty = Column(Numeric(12, 2), default=10000.00)  # ₦10,000 per day
    total_penalty = Column(Numeric(12, 2), nullable=False)
    
    # Payment Status
    payment_status = Column(String(20), default="unpaid")  # unpaid, partial, paid
    amount_paid = Column(Numeric(12, 2), default=0.00)
    payment_plan_id = Column(String(50), nullable=True)
    
    # Dates
    penalty_calculated_date = Column(DateTime, default=func.now())
    payment_due_date = Column(DateTime, nullable=True)
    last_payment_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="firs_penalties")


class ISO27001Compliance(Base):
    """Model for tracking ISO 27001 compliance status."""
    __tablename__ = "iso27001_compliance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Certification Details
    certificate_number = Column(String(50), nullable=True)
    certification_body = Column(String(100), nullable=True)
    issue_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Compliance Controls
    control_status = Column(JSONB, nullable=True)  # Status of ISO 27001 controls
    last_audit_date = Column(DateTime, nullable=True)
    next_audit_date = Column(DateTime, nullable=True)
    audit_findings = Column(JSONB, nullable=True)
    
    # Compliance Score
    overall_compliance_score = Column(Integer, default=0)
    compliance_level = Column(Enum(ComplianceLevel), default=ComplianceLevel.NEEDS_IMPROVEMENT)
    
    # Risk Assessment
    risk_assessment = Column(JSONB, nullable=True)
    mitigation_actions = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="iso27001_compliance")