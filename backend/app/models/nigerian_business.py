"""
Nigerian Business Culture Models

This module contains data models for Nigerian business culture integration,
including relationship managers, hierarchical approvals, and conglomerate structures.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Integer, Numeric, Enum, func, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from enum import Enum as PyEnum

from app.db.base_class import Base


class LanguagePreference(PyEnum):
    """Language preferences for Nigerian business users"""
    ENGLISH = "english"
    HAUSA = "hausa"
    YORUBA = "yoruba"
    IGBO = "igbo"


class GreetingStyle(PyEnum):
    """Greeting style preferences for Nigerian business culture"""
    FORMAL = "formal"
    TRADITIONAL = "traditional"
    MODERN = "modern"


class CommunicationPace(PyEnum):
    """Communication pace preferences for Nigerian business culture"""
    RELATIONSHIP_FIRST = "relationship_first"
    BUSINESS_FIRST = "business_first"


class ApprovalStatus(PyEnum):
    """Status of approval requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class TaxConsolidationType(PyEnum):
    """Tax consolidation types for Nigerian conglomerates"""
    CONSOLIDATED = "consolidated"
    SEPARATE = "separate"


class NigerianRelationshipManager(Base):
    """Model for Nigerian business relationship managers."""
    __tablename__ = "nigerian_relationship_managers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    whatsapp_number = Column(String(20), nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    # Location and language
    office_location = Column(String(255), nullable=True)
    local_language_preference = Column(Enum(LanguagePreference), default=LanguagePreference.ENGLISH)
    
    # Availability
    meeting_availability = Column(JSONB, nullable=True)  # Store availability schedule
    timezone = Column(String(50), default="Africa/Lagos")
    
    # Specialization
    industry_specialization = Column(JSONB, nullable=True)  # Industries they specialize in
    client_capacity = Column(Integer, default=50)  # Max number of clients
    current_client_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    hired_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    client_assignments = relationship("NigerianClientAssignment", back_populates="relationship_manager")


class NigerianClientAssignment(Base):
    """Model for assigning Nigerian clients to relationship managers."""
    __tablename__ = "nigerian_client_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    relationship_manager_id = Column(UUID(as_uuid=True), ForeignKey("nigerian_relationship_managers.id"), nullable=False)
    
    # Assignment details
    assigned_date = Column(DateTime, default=func.now())
    is_primary = Column(Boolean, default=True)
    assignment_reason = Column(Text, nullable=True)
    
    # Client preferences
    cultural_preferences = Column(JSONB, nullable=True)
    communication_preferences = Column(JSONB, nullable=True)
    meeting_preferences = Column(JSONB, nullable=True)
    
    # Relationship metrics
    relationship_score = Column(Float, default=0.0)
    last_interaction_date = Column(DateTime, nullable=True)
    interaction_frequency = Column(String(20), default="weekly")  # daily, weekly, monthly
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    relationship_manager = relationship("NigerianRelationshipManager", back_populates="client_assignments")


class NigerianCulturalPreferences(Base):
    """Model for storing Nigerian cultural preferences per organization."""
    __tablename__ = "nigerian_cultural_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, unique=True)
    
    # Greeting and communication preferences
    greeting_style = Column(Enum(GreetingStyle), default=GreetingStyle.FORMAL)
    communication_pace = Column(Enum(CommunicationPace), default=CommunicationPace.RELATIONSHIP_FIRST)
    
    # Meeting protocols
    relationship_building_time = Column(Integer, default=15)  # minutes
    hierarchy_acknowledgment = Column(Boolean, default=True)
    gift_exchange_customs = Column(Boolean, default=False)
    
    # Preferred support channels
    whatsapp_business_api = Column(Boolean, default=True)
    voice_calls = Column(Boolean, default=True)
    video_calls = Column(Boolean, default=False)
    in_person_meetings = Column(Boolean, default=True)
    traditional_email = Column(Boolean, default=True)
    
    # Language preferences
    primary_language = Column(Enum(LanguagePreference), default=LanguagePreference.ENGLISH)
    secondary_languages = Column(JSONB, nullable=True)  # Array of secondary languages
    
    # Business culture settings
    respect_titles = Column(Boolean, default=True)  # Use titles like "Alhaji", "Chief", etc.
    age_respectful_language = Column(Boolean, default=True)
    gender_appropriate_language = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class NigerianApprovalLevel(Base):
    """Model for Nigerian hierarchical approval levels."""
    __tablename__ = "nigerian_approval_levels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Approval level details
    level_name = Column(String(100), nullable=False)  # e.g., "Junior Staff", "Middle Management"
    level_order = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    
    # Approval limits
    amount_limit_ngn = Column(Numeric(15, 2), nullable=False)
    requires_superior_approval = Column(Boolean, default=True)
    requires_board_approval = Column(Boolean, default=False)
    requires_board_ratification = Column(Boolean, default=False)
    
    # Approval conditions
    conditions = Column(JSONB, nullable=True)  # Additional conditions for approval
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    approval_requests = relationship("NigerianApprovalRequest", back_populates="approval_level")


class NigerianApprovalRequest(Base):
    """Model for tracking approval requests in Nigerian hierarchical system."""
    __tablename__ = "nigerian_approval_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    approval_level_id = Column(UUID(as_uuid=True), ForeignKey("nigerian_approval_levels.id"), nullable=False)
    
    # Request details
    request_type = Column(String(50), nullable=False)  # invoice, payment, contract, etc.
    request_reference = Column(String(100), nullable=False)
    amount_ngn = Column(Numeric(15, 2), nullable=True)
    description = Column(Text, nullable=False)
    
    # Requester and approver
    requester_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approver_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Status and timing
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    submitted_at = Column(DateTime, default=func.now())
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Escalation
    escalation_level = Column(Integer, default=0)
    escalated_at = Column(DateTime, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    
    # Metadata
    request_data = Column(JSONB, nullable=True)  # Store additional request data
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    approval_level = relationship("NigerianApprovalLevel", back_populates="approval_requests")
    requester = relationship("User", foreign_keys=[requester_user_id])
    approver = relationship("User", foreign_keys=[approver_user_id])


class NigerianConglomerate(Base):
    """Model for Nigerian business conglomerates."""
    __tablename__ = "nigerian_conglomerates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Conglomerate details
    conglomerate_name = Column(String(255), nullable=False)  # e.g., "Dangote Group"
    cac_group_registration = Column(String(50), nullable=True)
    
    # Business structure
    tax_consolidation_type = Column(Enum(TaxConsolidationType), default=TaxConsolidationType.SEPARATE)
    primary_business_sector = Column(String(100), nullable=True)  # "manufacturing", "oil_gas", "telecoms"
    
    # Financial information
    total_subsidiaries = Column(Integer, default=0)
    total_employees = Column(Integer, nullable=True)
    consolidated_revenue_ngn = Column(Numeric(20, 2), nullable=True)
    
    # Governance
    board_structure = Column(JSONB, nullable=True)
    governance_model = Column(String(50), default="traditional")  # traditional, modern, hybrid
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    parent_organization = relationship("Organization")
    subsidiaries = relationship("NigerianSubsidiary", back_populates="conglomerate")


class NigerianSubsidiary(Base):
    """Nigerian subsidiary company model."""
    __tablename__ = "nigerian_subsidiaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conglomerate_id = Column(UUID(as_uuid=True), ForeignKey("nigerian_conglomerates.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Subsidiary details
    subsidiary_name = Column(String(255), nullable=False)
    cac_registration_number = Column(String(50), nullable=True)
    
    # Nigerian jurisdiction
    operating_state = Column(String(50), nullable=True)  # Lagos, Kano, Rivers, etc.
    local_government_area = Column(String(100), nullable=True)
    
    # Tax and compliance
    firs_tin = Column(String(20), nullable=True)
    state_tax_id = Column(String(20), nullable=True)
    local_government_tax_id = Column(String(20), nullable=True)
    
    # Business operations
    primary_location = Column(JSONB, nullable=True)
    business_activities = Column(JSONB, nullable=True)
    employee_count = Column(Integer, nullable=True)
    annual_revenue_ngn = Column(Numeric(15, 2), nullable=True)
    
    # Ownership
    ownership_percentage = Column(Numeric(5, 2), nullable=True)
    shareholding_structure = Column(JSONB, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    incorporation_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    conglomerate = relationship("NigerianConglomerate", back_populates="subsidiaries")
    organization = relationship("Organization")


class NigerianBusinessInteraction(Base):
    """Model for tracking business interactions in Nigerian context."""
    __tablename__ = "nigerian_business_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    relationship_manager_id = Column(UUID(as_uuid=True), ForeignKey("nigerian_relationship_managers.id"), nullable=True)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # call, meeting, whatsapp, email
    interaction_subject = Column(String(255), nullable=True)
    interaction_notes = Column(Text, nullable=True)
    
    # Participants
    participants = Column(JSONB, nullable=True)  # List of participants
    
    # Cultural context
    relationship_building_time = Column(Integer, nullable=True)  # minutes spent on relationship building
    business_discussion_time = Column(Integer, nullable=True)  # minutes spent on business
    cultural_elements_observed = Column(JSONB, nullable=True)  # Greetings, respect shown, etc.
    
    # Outcome
    interaction_outcome = Column(String(50), nullable=True)  # positive, neutral, negative
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    
    # Timing
    interaction_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    relationship_manager = relationship("NigerianRelationshipManager")