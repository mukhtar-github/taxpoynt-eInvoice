"""
Privacy Compliance Manager for Nigerian Regulations
==================================================
Comprehensive privacy compliance management for Nigerian Data Protection
Regulation (NDPR) and other privacy laws. Handles data subject rights,
privacy impact assessments, and regulatory compliance monitoring.

Key Features:
- NDPR compliance management
- Data subject rights fulfillment
- Privacy impact assessments
- Data mapping and inventory
- Breach notification management
- Cross-border transfer compliance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

from ....shared.logging import get_logger
from ....shared.exceptions import IntegrationError


class DataSubjectRights(Enum):
    """Data subject rights under NDPR."""
    ACCESS = "access"                    # Right to access personal data
    RECTIFICATION = "rectification"      # Right to correct inaccurate data
    ERASURE = "erasure"                 # Right to delete personal data
    PORTABILITY = "portability"         # Right to data portability
    RESTRICTION = "restriction"         # Right to restrict processing
    OBJECTION = "objection"             # Right to object to processing
    WITHDRAWAL = "withdrawal"           # Right to withdraw consent
    NOTIFICATION = "notification"       # Right to be notified of breaches


class ProcessingLawfulBasis(Enum):
    """Lawful basis for processing under NDPR."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataCategory(Enum):
    """Categories of personal data."""
    BASIC_IDENTITY = "basic_identity"           # Name, address, phone
    FINANCIAL = "financial"                     # Banking, payment data
    GOVERNMENT_ID = "government_id"             # BVN, NIN, passport
    BIOMETRIC = "biometric"                     # Fingerprints, facial recognition
    COMMUNICATION = "communication"             # Email, phone communications
    LOCATION = "location"                       # GPS, address data
    BEHAVIORAL = "behavioral"                   # Usage patterns, preferences
    SENSITIVE = "sensitive"                     # Health, religion, political views


class CrossBorderTransferMechanism(Enum):
    """Mechanisms for cross-border data transfer."""
    ADEQUACY_DECISION = "adequacy_decision"
    APPROPRIATE_SAFEGUARDS = "appropriate_safeguards"
    BINDING_CORPORATE_RULES = "binding_corporate_rules"
    STANDARD_CONTRACTUAL_CLAUSES = "standard_contractual_clauses"
    CERTIFICATION = "certification"
    DEROGATIONS = "derogations"


@dataclass
class DataSubjectRequest:
    """Data subject rights request."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_type: DataSubjectRights = DataSubjectRights.ACCESS
    subject_id: str = ""
    subject_email: Optional[str] = None
    subject_phone: Optional[str] = None
    
    # Request details
    description: str = ""
    specific_data_requested: List[str] = field(default_factory=list)
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    
    # Processing information
    status: str = "pending"  # pending, processing, completed, rejected
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Identity verification
    identity_verified: bool = False
    verification_method: Optional[str] = None
    verification_documents: List[str] = field(default_factory=list)
    
    # Response information
    response_method: str = "email"  # email, postal, secure_portal
    response_data: Optional[Dict[str, Any]] = None
    response_files: List[str] = field(default_factory=list)
    
    # Compliance tracking
    deadline: Optional[datetime] = None
    extension_granted: bool = False
    extension_reason: Optional[str] = None
    
    # Metadata
    source_system: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProcessingActivity:
    """Record of data processing activities."""
    activity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    activity_name: str = ""
    description: str = ""
    
    # Legal basis
    lawful_basis: ProcessingLawfulBasis = ProcessingLawfulBasis.CONSENT
    legal_basis_details: str = ""
    
    # Data information
    data_categories: List[DataCategory] = field(default_factory=list)
    data_subjects: List[str] = field(default_factory=list)  # customer, employee, etc.
    data_sources: List[str] = field(default_factory=list)
    
    # Processing details
    processing_purposes: List[str] = field(default_factory=list)
    processing_operations: List[str] = field(default_factory=list)
    automated_decision_making: bool = False
    profiling: bool = False
    
    # Recipients and transfers
    internal_recipients: List[str] = field(default_factory=list)
    external_recipients: List[str] = field(default_factory=list)
    cross_border_transfers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Retention and security
    retention_period: Optional[str] = None
    security_measures: List[str] = field(default_factory=list)
    
    # Compliance
    privacy_impact_assessment: bool = False
    pia_reference: Optional[str] = None
    data_protection_measures: List[str] = field(default_factory=list)
    
    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_reviewed: Optional[datetime] = None
    next_review_due: Optional[datetime] = None
    status: str = "active"  # active, suspended, terminated


@dataclass
class PrivacyBreach:
    """Privacy breach incident record."""
    breach_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    breach_type: str = ""  # unauthorized_access, data_loss, etc.
    severity: str = "medium"  # low, medium, high, critical
    
    # Incident details
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    occurred_at: Optional[datetime] = None
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Affected data
    data_categories_affected: List[DataCategory] = field(default_factory=list)
    subjects_affected_count: int = 0
    data_volume_affected: Optional[str] = None
    
    # Impact assessment
    likelihood_of_harm: str = "medium"  # low, medium, high
    severity_of_harm: str = "medium"    # low, medium, high
    risk_to_subjects: str = "medium"    # low, medium, high
    
    # Response actions
    containment_actions: List[str] = field(default_factory=list)
    mitigation_actions: List[str] = field(default_factory=list)
    notification_required: bool = False
    subjects_notified: bool = False
    regulator_notified: bool = False
    
    # Notification details
    nitda_notification_deadline: Optional[datetime] = None
    nitda_notified_at: Optional[datetime] = None
    subjects_notification_deadline: Optional[datetime] = None
    subjects_notified_at: Optional[datetime] = None
    
    # Investigation
    cause_analysis: Optional[str] = None
    lessons_learned: List[str] = field(default_factory=list)
    preventive_measures: List[str] = field(default_factory=list)
    
    # Metadata
    assigned_to: Optional[str] = None
    external_support: List[str] = field(default_factory=list)
    costs_incurred: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PrivacyComplianceManager:
    """
    Comprehensive privacy compliance management system.
    
    This manager ensures compliance with Nigerian Data Protection Regulation
    (NDPR) and other privacy laws, handles data subject rights, and manages
    privacy governance for banking operations.
    """
    
    def __init__(self):
        """Initialize privacy compliance manager."""
        self.logger = get_logger(__name__)
        
        # Data storage
        self.data_subject_requests: Dict[str, DataSubjectRequest] = {}
        self.processing_activities: Dict[str, DataProcessingActivity] = {}
        self.privacy_breaches: Dict[str, PrivacyBreach] = {}
        
        # Configuration
        self.ndpr_compliance_enabled = True
        self.auto_acknowledgment = True
        self.request_deadline_days = 30  # NDPR standard
        self.breach_notification_hours = 72  # NITDA notification requirement
        
        # Data protection officer
        self.dpo_contact = {
            "name": "TaxPoynt Data Protection Officer",
            "email": "dpo@taxpoynt.com",
            "phone": "+234-XXX-XXXX-XXX"
        }
        
        # Processing registers
        self.data_inventory: Dict[str, Dict[str, Any]] = {}
        self.consent_records: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("Initialized NDPR privacy compliance manager")
        
        # Set up default processing activities
        self._setup_default_processing_activities()
    
    async def submit_data_subject_request(
        self,
        request_type: DataSubjectRights,
        subject_id: str,
        description: str,
        subject_email: Optional[str] = None,
        specific_data: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        verification_data: Optional[Dict[str, Any]] = None
    ) -> DataSubjectRequest:
        """
        Submit data subject rights request.
        
        Args:
            request_type: Type of rights request
            subject_id: Data subject identifier
            description: Request description
            subject_email: Subject's email address
            specific_data: Specific data categories requested
            date_range: Date range for the request
            verification_data: Identity verification data
            
        Returns:
            Created data subject request
        """
        try:
            # Create request
            request = DataSubjectRequest(
                request_type=request_type,
                subject_id=subject_id,
                subject_email=subject_email,
                description=description,
                specific_data_requested=specific_data or [],
                metadata=verification_data or {}
            )
            
            # Set date range if provided
            if date_range:
                request.date_range_start, request.date_range_end = date_range
            
            # Calculate deadline (30 days under NDPR)
            request.deadline = request.submitted_at + timedelta(days=self.request_deadline_days)
            
            # Auto-acknowledge if enabled
            if self.auto_acknowledgment:
                request.acknowledged_at = datetime.utcnow()
                request.status = "processing"
            
            # Store request
            self.data_subject_requests[request.request_id] = request
            
            # Log compliance event
            await self._log_privacy_event(
                "data_subject_request_submitted",
                {
                    "request_id": request.request_id,
                    "request_type": request_type.value,
                    "subject_id": subject_id,
                    "deadline": request.deadline.isoformat()
                }
            )
            
            self.logger.info(f"Data subject request submitted: {request.request_id}")
            return request
            
        except Exception as e:
            self.logger.error(f"Failed to submit data subject request: {str(e)}")
            raise IntegrationError(f"Data subject request submission failed: {str(e)}")
    
    async def process_access_request(
        self,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Process data access request under NDPR Article 15.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Processed data for the subject
        """
        try:
            request = self.data_subject_requests.get(request_id)
            if not request or request.request_type != DataSubjectRights.ACCESS:
                raise ValueError(f"Invalid access request: {request_id}")
            
            if not request.identity_verified:
                raise ValueError("Identity verification required before processing")
            
            # Collect data from various sources
            collected_data = {}
            
            # Basic profile data
            collected_data["profile"] = await self._collect_profile_data(request.subject_id)
            
            # Banking data
            collected_data["banking"] = await self._collect_banking_data(
                request.subject_id,
                request.date_range_start,
                request.date_range_end
            )
            
            # Consent records
            collected_data["consents"] = await self._collect_consent_data(request.subject_id)
            
            # Processing activities
            collected_data["processing_activities"] = await self._collect_processing_data(request.subject_id)
            
            # Third-party data sharing
            collected_data["data_sharing"] = await self._collect_sharing_data(request.subject_id)
            
            # Filter based on specific data requested
            if request.specific_data_requested:
                filtered_data = {}
                for category in request.specific_data_requested:
                    if category in collected_data:
                        filtered_data[category] = collected_data[category]
                collected_data = filtered_data
            
            # Update request
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            request.response_data = collected_data
            
            # Log compliance event
            await self._log_privacy_event(
                "access_request_completed",
                {
                    "request_id": request_id,
                    "subject_id": request.subject_id,
                    "data_categories": list(collected_data.keys()),
                    "completion_time": request.completed_at.isoformat()
                }
            )
            
            self.logger.info(f"Access request processed: {request_id}")
            return collected_data
            
        except Exception as e:
            self.logger.error(f"Failed to process access request: {str(e)}")
            raise IntegrationError(f"Access request processing failed: {str(e)}")
    
    async def process_erasure_request(
        self,
        request_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Process data erasure request under NDPR Article 17.
        
        Args:
            request_id: Request identifier
            force: Force erasure even if retention obligations exist
            
        Returns:
            Erasure processing results
        """
        try:
            request = self.data_subject_requests.get(request_id)
            if not request or request.request_type != DataSubjectRights.ERASURE:
                raise ValueError(f"Invalid erasure request: {request_id}")
            
            if not request.identity_verified:
                raise ValueError("Identity verification required before processing")
            
            # Check for legal obligations to retain data
            retention_obligations = await self._check_retention_obligations(request.subject_id)
            
            if retention_obligations and not force:
                request.status = "rejected"
                request.rejection_reason = f"Legal retention obligations: {', '.join(retention_obligations)}"
                request.completed_at = datetime.utcnow()
                
                return {
                    "status": "rejected",
                    "reason": request.rejection_reason,
                    "retention_obligations": retention_obligations
                }
            
            # Perform erasure
            erasure_results = {}
            
            # Erase profile data
            erasure_results["profile"] = await self._erase_profile_data(request.subject_id)
            
            # Erase banking data (with retention checks)
            erasure_results["banking"] = await self._erase_banking_data(
                request.subject_id,
                respect_retention=not force
            )
            
            # Erase consent records
            erasure_results["consents"] = await self._erase_consent_data(request.subject_id)
            
            # Anonymize audit logs (where possible)
            erasure_results["audit_logs"] = await self._anonymize_audit_data(request.subject_id)
            
            # Update request
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            request.response_data = erasure_results
            
            # Log compliance event
            await self._log_privacy_event(
                "erasure_request_completed",
                {
                    "request_id": request_id,
                    "subject_id": request.subject_id,
                    "erasure_results": {k: v.get("records_affected", 0) for k, v in erasure_results.items()},
                    "force_erasure": force,
                    "completion_time": request.completed_at.isoformat()
                }
            )
            
            self.logger.info(f"Erasure request processed: {request_id}")
            return {
                "status": "completed",
                "erasure_results": erasure_results,
                "completion_time": request.completed_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process erasure request: {str(e)}")
            raise IntegrationError(f"Erasure request processing failed: {str(e)}")
    
    async def report_privacy_breach(
        self,
        breach_type: str,
        severity: str,
        affected_subjects_count: int,
        data_categories: List[DataCategory],
        description: str,
        occurred_at: Optional[datetime] = None
    ) -> PrivacyBreach:
        """
        Report privacy breach incident.
        
        Args:
            breach_type: Type of breach
            severity: Severity level
            affected_subjects_count: Number of affected data subjects
            data_categories: Categories of affected data
            description: Breach description
            occurred_at: When the breach occurred
            
        Returns:
            Created breach record
        """
        try:
            breach = PrivacyBreach(
                breach_type=breach_type,
                severity=severity,
                subjects_affected_count=affected_subjects_count,
                data_categories_affected=data_categories,
                occurred_at=occurred_at or datetime.utcnow()
            )
            
            # Assess notification requirements
            breach.notification_required = self._assess_notification_requirement(breach)
            
            if breach.notification_required:
                # Set NITDA notification deadline (72 hours)
                breach.nitda_notification_deadline = (
                    breach.discovered_at + timedelta(hours=self.breach_notification_hours)
                )
                
                # Set subject notification deadline (depends on risk assessment)
                if breach.severity in ["high", "critical"]:
                    breach.subjects_notification_deadline = (
                        breach.discovered_at + timedelta(hours=72)
                    )
            
            # Store breach record
            self.privacy_breaches[breach.breach_id] = breach
            
            # Log compliance event
            await self._log_privacy_event(
                "privacy_breach_reported",
                {
                    "breach_id": breach.breach_id,
                    "breach_type": breach_type,
                    "severity": severity,
                    "affected_count": affected_subjects_count,
                    "notification_required": breach.notification_required,
                    "nitda_deadline": breach.nitda_notification_deadline.isoformat() if breach.nitda_notification_deadline else None
                }
            )
            
            self.logger.warning(f"Privacy breach reported: {breach.breach_id}")
            return breach
            
        except Exception as e:
            self.logger.error(f"Failed to report privacy breach: {str(e)}")
            raise IntegrationError(f"Breach reporting failed: {str(e)}")
    
    async def generate_privacy_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive privacy compliance report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            report_type: Type of report
            
        Returns:
            Privacy compliance report
        """
        try:
            # Filter data by date range
            period_requests = [
                req for req in self.data_subject_requests.values()
                if start_date <= req.submitted_at <= end_date
            ]
            
            period_breaches = [
                breach for breach in self.privacy_breaches.values()
                if start_date <= breach.discovered_at <= end_date
            ]
            
            # Calculate metrics
            total_requests = len(period_requests)
            completed_requests = len([r for r in period_requests if r.status == "completed"])
            
            # Request type breakdown
            request_types = {}
            for req in period_requests:
                req_type = req.request_type.value
                request_types[req_type] = request_types.get(req_type, 0) + 1
            
            # Response time metrics
            completed_with_times = [
                r for r in period_requests 
                if r.status == "completed" and r.completed_at and r.submitted_at
            ]
            
            if completed_with_times:
                response_times = [
                    (r.completed_at - r.submitted_at).days 
                    for r in completed_with_times
                ]
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
            else:
                avg_response_time = 0
                max_response_time = 0
            
            # Breach metrics
            total_breaches = len(period_breaches)
            subjects_affected = sum(b.subjects_affected_count for b in period_breaches)
            
            # Compliance score calculation
            on_time_requests = len([
                r for r in completed_with_times
                if r.completed_at <= r.deadline
            ])
            
            compliance_score = (on_time_requests / total_requests * 100) if total_requests > 0 else 100
            
            report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "data_subject_requests": {
                    "total_requests": total_requests,
                    "completed_requests": completed_requests,
                    "completion_rate": (completed_requests / total_requests * 100) if total_requests > 0 else 0,
                    "request_types": request_types,
                    "response_metrics": {
                        "average_response_days": round(avg_response_time, 1),
                        "max_response_days": max_response_time,
                        "on_time_completion_rate": (on_time_requests / total_requests * 100) if total_requests > 0 else 100
                    }
                },
                "privacy_breaches": {
                    "total_breaches": total_breaches,
                    "subjects_affected": subjects_affected,
                    "breach_types": {},
                    "notification_compliance": {}
                },
                "compliance_metrics": {
                    "overall_score": round(compliance_score, 2),
                    "active_processing_activities": len([a for a in self.processing_activities.values() if a.status == "active"]),
                    "consent_records": len(self.consent_records)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Add breach type breakdown
            for breach in period_breaches:
                breach_type = breach.breach_type
                report["privacy_breaches"]["breach_types"][breach_type] = (
                    report["privacy_breaches"]["breach_types"].get(breach_type, 0) + 1
                )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Privacy report generation failed: {str(e)}")
            raise IntegrationError(f"Privacy report generation failed: {str(e)}")
    
    def _setup_default_processing_activities(self) -> None:
        """Set up default data processing activities."""
        # E-invoicing processing activity
        self.processing_activities["einvoicing"] = DataProcessingActivity(
            activity_name="E-Invoice Generation and FIRS Submission",
            description="Processing of banking transaction data for automated invoice generation and tax compliance",
            lawful_basis=ProcessingLawfulBasis.LEGAL_OBLIGATION,
            legal_basis_details="FIRS e-invoicing compliance requirement",
            data_categories=[
                DataCategory.BASIC_IDENTITY,
                DataCategory.FINANCIAL,
                DataCategory.GOVERNMENT_ID
            ],
            data_subjects=["customers", "business_owners"],
            processing_purposes=[
                "e_invoice_generation",
                "tax_compliance",
                "firs_reporting"
            ],
            retention_period="7 years (FIRS requirement)",
            security_measures=[
                "encryption_at_rest",
                "encryption_in_transit",
                "access_controls",
                "audit_logging"
            ]
        )
        
        # Account verification processing
        self.processing_activities["account_verification"] = DataProcessingActivity(
            activity_name="Banking Account Verification",
            description="Verification of banking account ownership and identity",
            lawful_basis=ProcessingLawfulBasis.CONTRACT,
            legal_basis_details="Service provision and fraud prevention",
            data_categories=[
                DataCategory.BASIC_IDENTITY,
                DataCategory.FINANCIAL,
                DataCategory.GOVERNMENT_ID
            ],
            processing_purposes=[
                "identity_verification",
                "fraud_prevention",
                "service_provision"
            ],
            retention_period="7 years (regulatory requirement)"
        )
    
    def _assess_notification_requirement(self, breach: PrivacyBreach) -> bool:
        """Assess if breach requires regulatory notification."""
        # High and critical severity always require notification
        if breach.severity in ["high", "critical"]:
            return True
        
        # Large number of affected subjects
        if breach.subjects_affected_count > 100:
            return True
        
        # Sensitive data categories
        sensitive_categories = [
            DataCategory.BIOMETRIC,
            DataCategory.GOVERNMENT_ID,
            DataCategory.SENSITIVE
        ]
        
        if any(cat in breach.data_categories_affected for cat in sensitive_categories):
            return True
        
        return False
    
    async def _log_privacy_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log privacy compliance event."""
        # This would integrate with the audit logger
        self.logger.info(f"Privacy event: {event_type} - {json.dumps(details)}")
    
    # Mock data collection methods (would integrate with actual data sources)
    async def _collect_profile_data(self, subject_id: str) -> Dict[str, Any]:
        """Collect profile data for subject."""
        return {"message": "Profile data collection would be implemented here"}
    
    async def _collect_banking_data(
        self,
        subject_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Collect banking data for subject."""
        return {"message": "Banking data collection would be implemented here"}
    
    async def _collect_consent_data(self, subject_id: str) -> Dict[str, Any]:
        """Collect consent records for subject."""
        return {"message": "Consent data collection would be implemented here"}
    
    async def _collect_processing_data(self, subject_id: str) -> Dict[str, Any]:
        """Collect processing activity data for subject."""
        return {"message": "Processing data collection would be implemented here"}
    
    async def _collect_sharing_data(self, subject_id: str) -> Dict[str, Any]:
        """Collect data sharing information for subject."""
        return {"message": "Data sharing collection would be implemented here"}
    
    async def _check_retention_obligations(self, subject_id: str) -> List[str]:
        """Check legal retention obligations for subject data."""
        # For banking/financial data, there are usually 7-year retention requirements
        return ["FIRS 7-year retention requirement", "CBN banking regulations"]
    
    async def _erase_profile_data(self, subject_id: str) -> Dict[str, Any]:
        """Erase profile data for subject."""
        return {"records_affected": 0, "message": "Profile data erasure would be implemented here"}
    
    async def _erase_banking_data(self, subject_id: str, respect_retention: bool) -> Dict[str, Any]:
        """Erase banking data for subject."""
        if respect_retention:
            return {"records_affected": 0, "message": "Banking data retained due to legal obligations"}
        return {"records_affected": 0, "message": "Banking data erasure would be implemented here"}
    
    async def _erase_consent_data(self, subject_id: str) -> Dict[str, Any]:
        """Erase consent records for subject."""
        return {"records_affected": 0, "message": "Consent data erasure would be implemented here"}
    
    async def _anonymize_audit_data(self, subject_id: str) -> Dict[str, Any]:
        """Anonymize audit logs for subject."""
        return {"records_affected": 0, "message": "Audit data anonymization would be implemented here"}