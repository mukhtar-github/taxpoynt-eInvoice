"""
FIRS Hybrid Error Reporting Service for TaxPoynt eInvoice - Hybrid SI+APP Functions.

This module provides Hybrid FIRS functionality for comprehensive error reporting,
tracking, and analysis that combines System Integrator (SI) and Access Point Provider (APP)
operations for unified error management in FIRS e-invoicing workflows.

Hybrid FIRS Responsibilities:
- Cross-role error tracking for both SI invoice processing and APP transmission failures
- Unified error categorization and severity assessment for SI and APP operations
- Hybrid error resolution workflows covering both SI integration and APP submission errors
- Shared error analytics and reporting for comprehensive FIRS workflow monitoring
- Cross-functional error escalation and alerting for SI and APP operations
"""

import logging
import traceback
from typing import Dict, Any, Optional, List, Union, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, Integer
from fastapi import HTTPException

from app.models.transmission_error import TransmissionError, ErrorCategory, ErrorSeverity
from app.models.transmission import TransmissionRecord, TransmissionStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

# Hybrid FIRS error reporting configuration
HYBRID_ERROR_SERVICE_VERSION = "1.0"
DEFAULT_ERROR_ESCALATION_THRESHOLD = 3
HYBRID_ERROR_CACHE_DURATION_MINUTES = 30
MAX_ERROR_HISTORY_SIZE = 100
FIRS_ERROR_CRITICALITY_THRESHOLD = 5

class HybridErrorCategory(Enum):
    """Enhanced error categories for hybrid SI+APP operations."""
    # SI-specific error categories
    SI_INTEGRATION_ERROR = "si_integration_error"
    SI_VALIDATION_ERROR = "si_validation_error"
    SI_CERTIFICATE_ERROR = "si_certificate_error"
    SI_IRN_GENERATION_ERROR = "si_irn_generation_error"
    SI_ERP_CONNECTION_ERROR = "si_erp_connection_error"
    
    # APP-specific error categories
    APP_TRANSMISSION_ERROR = "app_transmission_error"
    APP_ENCRYPTION_ERROR = "app_encryption_error"
    APP_SIGNATURE_ERROR = "app_signature_error"
    APP_AUTHENTICATION_ERROR = "app_authentication_error"
    APP_FIRS_API_ERROR = "app_firs_api_error"
    
    # Hybrid error categories
    HYBRID_WORKFLOW_ERROR = "hybrid_workflow_error"
    HYBRID_COORDINATION_ERROR = "hybrid_coordination_error"
    HYBRID_COMPLIANCE_ERROR = "hybrid_compliance_error"
    HYBRID_SYSTEM_ERROR = "hybrid_system_error"
    
    # Standard error categories
    NETWORK = "network"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    OTHER = "other"


class HybridErrorSeverity(Enum):
    """Enhanced error severity levels for hybrid operations."""
    CRITICAL_SI = "critical_si"
    CRITICAL_APP = "critical_app"
    CRITICAL_HYBRID = "critical_hybrid"
    HIGH_SI = "high_si"
    HIGH_APP = "high_app"
    HIGH_HYBRID = "high_hybrid"
    MEDIUM_SI = "medium_si"
    MEDIUM_APP = "medium_app"
    MEDIUM_HYBRID = "medium_hybrid"
    LOW_SI = "low_si"
    LOW_APP = "low_app"
    LOW_HYBRID = "low_hybrid"
    INFO = "info"


class HybridFIRSErrorReportingService:
    """
    Hybrid FIRS error reporting service for comprehensive error management.
    
    This service provides Hybrid FIRS functions for error reporting, tracking,
    and analysis that combine System Integrator (SI) and Access Point Provider (APP)
    operations for unified error management in Nigerian e-invoicing compliance.
    
    Hybrid Error Reporting Functions:
    1. Cross-role error tracking for both SI invoice processing and APP transmission failures
    2. Unified error categorization and severity assessment for SI and APP operations
    3. Hybrid error resolution workflows covering both SI integration and APP submission errors
    4. Shared error analytics and reporting for comprehensive FIRS workflow monitoring
    5. Cross-functional error escalation and alerting for SI and APP operations
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Hybrid FIRS error reporting service with enhanced capabilities.
        
        Args:
            db: Database session
        """
        self.db = db
        self.error_cache = {}
        self.error_analytics = {}
        self.escalation_tracking = {}
        self.firs_metrics = {
            "total_errors": 0,
            "si_errors": 0,
            "app_errors": 0,
            "hybrid_errors": 0,
            "resolved_errors": 0,
            "critical_errors": 0,
            "escalated_errors": 0,
            "last_updated": datetime.now()
        }
        
        logger.info(f"Hybrid FIRS Error Reporting Service initialized (Version: {HYBRID_ERROR_SERVICE_VERSION})")
    
    def get_error_classification(self, error_message: str, error_code: str, context: Dict[str, Any]) -> Tuple[HybridErrorCategory, HybridErrorSeverity]:
        """
        Classify error with hybrid SI+APP context - Hybrid FIRS Function.
        
        Provides enhanced error classification that considers both SI and APP
        operations for comprehensive error categorization.
        
        Args:
            error_message: The error message
            error_code: The error code
            context: Additional context about the error
            
        Returns:
            Tuple of (category, severity) for the error
        """
        error_message_lower = error_message.lower()
        error_code_lower = error_code.lower()
        
        # Determine operation context
        is_si_operation = context.get("si_operation", False)
        is_app_operation = context.get("app_operation", False)
        is_hybrid_operation = context.get("hybrid_operation", False)
        
        # SI-specific error classification
        if is_si_operation or any(keyword in error_message_lower for keyword in ["erp", "integration", "odoo", "irn"]):
            if "certificate" in error_message_lower:
                return HybridErrorCategory.SI_CERTIFICATE_ERROR, HybridErrorSeverity.HIGH_SI
            elif "irn" in error_message_lower or "qr" in error_message_lower:
                return HybridErrorCategory.SI_IRN_GENERATION_ERROR, HybridErrorSeverity.HIGH_SI
            elif "validation" in error_message_lower:
                return HybridErrorCategory.SI_VALIDATION_ERROR, HybridErrorSeverity.MEDIUM_SI
            elif "connection" in error_message_lower or "timeout" in error_message_lower:
                return HybridErrorCategory.SI_ERP_CONNECTION_ERROR, HybridErrorSeverity.HIGH_SI
            else:
                return HybridErrorCategory.SI_INTEGRATION_ERROR, HybridErrorSeverity.MEDIUM_SI
        
        # APP-specific error classification
        elif is_app_operation or any(keyword in error_message_lower for keyword in ["transmission", "firs", "api", "encrypt"]):
            if "transmission" in error_message_lower:
                return HybridErrorCategory.APP_TRANSMISSION_ERROR, HybridErrorSeverity.HIGH_APP
            elif "encrypt" in error_message_lower or "decrypt" in error_message_lower:
                return HybridErrorCategory.APP_ENCRYPTION_ERROR, HybridErrorSeverity.CRITICAL_APP
            elif "signature" in error_message_lower or "sign" in error_message_lower:
                return HybridErrorCategory.APP_SIGNATURE_ERROR, HybridErrorSeverity.CRITICAL_APP
            elif "auth" in error_message_lower or "unauthorized" in error_message_lower:
                return HybridErrorCategory.APP_AUTHENTICATION_ERROR, HybridErrorSeverity.CRITICAL_APP
            elif "firs" in error_message_lower or "api" in error_message_lower:
                return HybridErrorCategory.APP_FIRS_API_ERROR, HybridErrorSeverity.HIGH_APP
            else:
                return HybridErrorCategory.APP_TRANSMISSION_ERROR, HybridErrorSeverity.MEDIUM_APP
        
        # Hybrid operation error classification
        elif is_hybrid_operation or any(keyword in error_message_lower for keyword in ["workflow", "coordination", "compliance"]):
            if "workflow" in error_message_lower:
                return HybridErrorCategory.HYBRID_WORKFLOW_ERROR, HybridErrorSeverity.HIGH_HYBRID
            elif "coordination" in error_message_lower:
                return HybridErrorCategory.HYBRID_COORDINATION_ERROR, HybridErrorSeverity.MEDIUM_HYBRID
            elif "compliance" in error_message_lower:
                return HybridErrorCategory.HYBRID_COMPLIANCE_ERROR, HybridErrorSeverity.CRITICAL_HYBRID
            else:
                return HybridErrorCategory.HYBRID_SYSTEM_ERROR, HybridErrorSeverity.MEDIUM_HYBRID
        
        # Default classification based on error content
        else:
            if "network" in error_message_lower or "connection" in error_message_lower:
                return HybridErrorCategory.NETWORK, HybridErrorSeverity.MEDIUM_HYBRID
            elif "validation" in error_message_lower:
                return HybridErrorCategory.VALIDATION, HybridErrorSeverity.MEDIUM_HYBRID
            elif "timeout" in error_message_lower:
                return HybridErrorCategory.TIMEOUT, HybridErrorSeverity.HIGH_HYBRID
            else:
                return HybridErrorCategory.OTHER, HybridErrorSeverity.MEDIUM_HYBRID

    def record_hybrid_error(
        self,
        transmission_id: UUID,
        error_message: str,
        error_category: Optional[Union[HybridErrorCategory, ErrorCategory, str]] = None,
        severity: Optional[Union[HybridErrorSeverity, ErrorSeverity, str]] = None,
        error_code: Optional[str] = None,
        operation_phase: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        update_transmission_status: bool = True
    ) -> TransmissionError:
        """
        Record a hybrid error with enhanced SI+APP context - Hybrid FIRS Function.
        
        Provides comprehensive error recording that considers both SI and APP
        operations for unified error management and tracking.
        
        Args:
            transmission_id: UUID of the transmission
            error_message: Error message
            error_category: Category of the error
            severity: Severity level of the error
            error_code: Error code if available
            operation_phase: Phase of operation when error occurred
            error_details: Additional error details
            stack_trace: Stack trace if available
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            update_transmission_status: Whether to update transmission status
            
        Returns:
            The created enhanced error record
        """
        error_id = str(uuid4())
        
        try:
            # Verify transmission exists
            transmission = self.db.query(TransmissionRecord).filter(
                TransmissionRecord.id == transmission_id
            ).first()
            
            if not transmission:
                raise ValueError(f"Transmission with ID {transmission_id} not found")
            
            # Enhanced error classification
            context = {
                "si_operation": bool(si_context),
                "app_operation": bool(app_context),
                "hybrid_operation": bool(hybrid_context),
                **((si_context or {})),
                **((app_context or {})),
                **((hybrid_context or {}))
            }
            
            if not error_category or not severity:
                classified_category, classified_severity = self.get_error_classification(
                    error_message, error_code or "", context
                )
                error_category = error_category or classified_category
                severity = severity or classified_severity
            
            # Enhanced error details with hybrid context
            enhanced_error_details = {
                **(error_details or {}),
                "error_id": error_id,
                "si_context": si_context or {},
                "app_context": app_context or {},
                "hybrid_context": hybrid_context or {},
                "hybrid_error": True,
                "classification_context": context,
                "firs_compliance_impact": self._assess_firs_compliance_impact(error_category, severity),
                "hybrid_version": HYBRID_ERROR_SERVICE_VERSION,
                "timestamp": datetime.now().isoformat()
            }
            
            # Create enhanced error record
            error = TransmissionError(
                transmission_id=transmission_id,
                error_message=error_message,
                error_code=error_code,
                error_category=str(error_category.value) if hasattr(error_category, 'value') else str(error_category),
                severity=str(severity.value) if hasattr(severity, 'value') else str(severity),
                operation_phase=operation_phase,
                error_details=enhanced_error_details,
                stack_trace=stack_trace,
                error_time=datetime.now()
            )
            
            self.db.add(error)
            
            # Update transmission status with hybrid context
            if update_transmission_status and transmission.status != TransmissionStatus.FAILED:
                transmission.status = TransmissionStatus.FAILED
                
                # Enhanced metadata with hybrid error information
                metadata = transmission.transmission_metadata or {}
                error_history = metadata.get("error_history", [])
                
                hybrid_error_entry = {
                    "error_id": error_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": error_message,
                    "category": str(error_category.value) if hasattr(error_category, 'value') else str(error_category),
                    "severity": str(severity.value) if hasattr(severity, 'value') else str(severity),
                    "operation_phase": operation_phase,
                    "si_context": si_context or {},
                    "app_context": app_context or {},
                    "hybrid_context": hybrid_context or {},
                    "firs_compliance_impact": enhanced_error_details["firs_compliance_impact"],
                    "hybrid_version": HYBRID_ERROR_SERVICE_VERSION
                }
                
                error_history.append(hybrid_error_entry)
                
                # Keep only recent errors
                if len(error_history) > MAX_ERROR_HISTORY_SIZE:
                    error_history = error_history[-MAX_ERROR_HISTORY_SIZE:]
                
                metadata["error_history"] = error_history
                metadata["last_error"] = hybrid_error_entry
                metadata["hybrid_error_tracking"] = True
                transmission.transmission_metadata = metadata
            
            # Enhanced status logging
            self._create_hybrid_status_log(transmission_id, error_message, error_category, severity, context)
            
            # Enhanced audit logging
            self._create_hybrid_audit_log(transmission_id, transmission.organization_id, error_message, enhanced_error_details)
            
            # Track error for analytics
            self._track_error_analytics(error_category, severity, si_context, app_context, hybrid_context)
            
            # Check for escalation
            self._check_error_escalation(transmission_id, error_category, severity, enhanced_error_details)
            
            self.db.commit()
            self.db.refresh(error)
            
            # Enhanced logging
            self._log_hybrid_error(error_message, error_category, severity, transmission_id, error_id, context)
            
            return error
            
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Hybrid FIRS: Failed to record error (Error ID: {error_id}): {str(e)}")
            raise

    def _assess_firs_compliance_impact(self, error_category: Union[HybridErrorCategory, ErrorCategory, str], severity: Union[HybridErrorSeverity, ErrorSeverity, str]) -> Dict[str, Any]:
        """
        Assess FIRS compliance impact of error - Hybrid FIRS Function.
        
        Evaluates how the error affects FIRS compliance and e-invoicing operations.
        
        Args:
            error_category: Category of the error
            severity: Severity of the error
            
        Returns:
            Dict containing compliance impact assessment
        """
        impact = {
            "compliance_risk": "low",
            "blocks_submission": False,
            "requires_immediate_action": False,
            "affects_taxpayer_operations": False,
            "firs_notification_required": False,
            "recommended_actions": []
        }
        
        # Assess based on error category
        if isinstance(error_category, HybridErrorCategory):
            if error_category in [HybridErrorCategory.SI_CERTIFICATE_ERROR, HybridErrorCategory.APP_SIGNATURE_ERROR]:
                impact.update({
                    "compliance_risk": "critical",
                    "blocks_submission": True,
                    "requires_immediate_action": True,
                    "affects_taxpayer_operations": True,
                    "firs_notification_required": True,
                    "recommended_actions": ["Verify digital certificates", "Contact FIRS support", "Regenerate certificates"]
                })
            elif error_category in [HybridErrorCategory.SI_IRN_GENERATION_ERROR, HybridErrorCategory.APP_TRANSMISSION_ERROR]:
                impact.update({
                    "compliance_risk": "high",
                    "blocks_submission": True,
                    "requires_immediate_action": True,
                    "affects_taxpayer_operations": True,
                    "recommended_actions": ["Retry operation", "Check system status", "Contact support"]
                })
            elif error_category in [HybridErrorCategory.HYBRID_COMPLIANCE_ERROR]:
                impact.update({
                    "compliance_risk": "critical",
                    "blocks_submission": True,
                    "requires_immediate_action": True,
                    "affects_taxpayer_operations": True,
                    "firs_notification_required": True,
                    "recommended_actions": ["Review compliance requirements", "Update system configuration", "Contact compliance team"]
                })
        
        # Assess based on severity
        if isinstance(severity, HybridErrorSeverity):
            if "critical" in str(severity.value).lower():
                impact["compliance_risk"] = "critical"
                impact["requires_immediate_action"] = True
                impact["firs_notification_required"] = True
            elif "high" in str(severity.value).lower():
                impact["compliance_risk"] = "high"
                impact["requires_immediate_action"] = True
        
        return impact

    def _create_hybrid_status_log(self, transmission_id: UUID, error_message: str, error_category: Any, severity: Any, context: Dict[str, Any]) -> None:
        """Create enhanced status log with hybrid context."""
        try:
            from app.models.transmission_status_log import TransmissionStatusLog
            
            status_log = TransmissionStatusLog(
                transmission_id=transmission_id,
                previous_status=TransmissionStatus.PENDING,
                current_status=TransmissionStatus.FAILED,
                change_reason=f"Hybrid Error: {error_message}",
                change_source="hybrid_error_reporting",
                change_detail={
                    "error_category": str(error_category.value) if hasattr(error_category, 'value') else str(error_category),
                    "severity": str(severity.value) if hasattr(severity, 'value') else str(severity),
                    "si_context": context.get("si_context", {}),
                    "app_context": context.get("app_context", {}),
                    "hybrid_context": context.get("hybrid_context", {}),
                    "hybrid_status_log": True,
                    "hybrid_version": HYBRID_ERROR_SERVICE_VERSION
                }
            )
            self.db.add(status_log)
        except ImportError:
            pass

    def _create_hybrid_audit_log(self, transmission_id: UUID, organization_id: UUID, error_message: str, error_details: Dict[str, Any]) -> None:
        """Create enhanced audit log with hybrid context."""
        try:
            from app.services.firs_core.audit_service import AuditService
            from app.models.transmission_audit_log import AuditActionType
            
            audit_service = AuditService(self.db)
            audit_service.log_transmission_action(
                action_type=AuditActionType.OTHER,
                transmission_id=transmission_id,
                organization_id=organization_id,
                action_status="hybrid_error",
                error_message=error_message,
                context_data={
                    **error_details,
                    "audit_type": "hybrid_error",
                    "hybrid_version": HYBRID_ERROR_SERVICE_VERSION
                }
            )
        except ImportError:
            pass

    def _track_error_analytics(self, error_category: Any, severity: Any, si_context: Optional[Dict], app_context: Optional[Dict], hybrid_context: Optional[Dict]) -> None:
        """Track error analytics for hybrid operations."""
        category_str = str(error_category.value) if hasattr(error_category, 'value') else str(error_category)
        severity_str = str(severity.value) if hasattr(severity, 'value') else str(severity)
        
        # Update analytics
        if category_str not in self.error_analytics:
            self.error_analytics[category_str] = {
                "count": 0,
                "si_errors": 0,
                "app_errors": 0,
                "hybrid_errors": 0,
                "severity_breakdown": {},
                "last_occurrence": None
            }
        
        analytics = self.error_analytics[category_str]
        analytics["count"] += 1
        analytics["last_occurrence"] = datetime.now().isoformat()
        
        # Track by operation type
        if si_context:
            analytics["si_errors"] += 1
        if app_context:
            analytics["app_errors"] += 1
        if hybrid_context:
            analytics["hybrid_errors"] += 1
        
        # Track severity breakdown
        if severity_str not in analytics["severity_breakdown"]:
            analytics["severity_breakdown"][severity_str] = 0
        analytics["severity_breakdown"][severity_str] += 1
        
        # Update overall metrics
        self.firs_metrics["total_errors"] += 1
        if si_context:
            self.firs_metrics["si_errors"] += 1
        if app_context:
            self.firs_metrics["app_errors"] += 1
        if hybrid_context:
            self.firs_metrics["hybrid_errors"] += 1
        if "critical" in severity_str.lower():
            self.firs_metrics["critical_errors"] += 1
        
        self.firs_metrics["last_updated"] = datetime.now()

    def _check_error_escalation(self, transmission_id: UUID, error_category: Any, severity: Any, error_details: Dict[str, Any]) -> None:
        """Check if error should be escalated based on hybrid criteria."""
        category_str = str(error_category.value) if hasattr(error_category, 'value') else str(error_category)
        severity_str = str(severity.value) if hasattr(severity, 'value') else str(severity)
        
        # Track escalation criteria
        if transmission_id not in self.escalation_tracking:
            self.escalation_tracking[transmission_id] = {
                "error_count": 0,
                "critical_errors": 0,
                "last_error": None,
                "escalated": False
            }
        
        tracking = self.escalation_tracking[transmission_id]
        tracking["error_count"] += 1
        tracking["last_error"] = datetime.now().isoformat()
        
        if "critical" in severity_str.lower():
            tracking["critical_errors"] += 1
        
        # Check escalation conditions
        should_escalate = (
            not tracking["escalated"] and (
                tracking["error_count"] >= DEFAULT_ERROR_ESCALATION_THRESHOLD or
                tracking["critical_errors"] >= 1 or
                "critical" in severity_str.lower()
            )
        )
        
        if should_escalate:
            tracking["escalated"] = True
            self.firs_metrics["escalated_errors"] += 1
            self._escalate_error(transmission_id, error_category, severity, error_details)

    def _escalate_error(self, transmission_id: UUID, error_category: Any, severity: Any, error_details: Dict[str, Any]) -> None:
        """Escalate error to appropriate channels."""
        escalation_id = str(uuid4())
        
        logger.critical(f"Hybrid FIRS: Error escalated for transmission {transmission_id} - Category: {error_category}, Severity: {severity} (Escalation ID: {escalation_id})")
        
        # Additional escalation logic would go here
        # (e.g., send alerts, create tickets, notify administrators)

    def _log_hybrid_error(self, error_message: str, error_category: Any, severity: Any, transmission_id: UUID, error_id: str, context: Dict[str, Any]) -> None:
        """Enhanced logging for hybrid errors."""
        category_str = str(error_category.value) if hasattr(error_category, 'value') else str(error_category)
        severity_str = str(severity.value) if hasattr(severity, 'value') else str(severity)
        
        log_level = logging.ERROR if "critical" in severity_str.lower() or "high" in severity_str.lower() else logging.WARNING
        
        context_info = []
        if context.get("si_operation"):
            context_info.append("SI")
        if context.get("app_operation"):
            context_info.append("APP")
        if context.get("hybrid_operation"):
            context_info.append("HYBRID")
        
        context_str = f"[{'/'.join(context_info)}]" if context_info else "[UNKNOWN]"
        
        logger.log(
            log_level,
            f"Hybrid FIRS Error {context_str}: {error_message} | Category: {category_str} | "
            f"Severity: {severity_str} | Transmission: {transmission_id} | Error ID: {error_id}"
        )

    def record_hybrid_exception(
        self,
        transmission_id: UUID,
        exception: Exception,
        operation_phase: Optional[str] = None,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        error_details: Optional[Dict[str, Any]] = None,
        update_transmission_status: bool = True
    ) -> TransmissionError:
        """
        Record a hybrid exception with enhanced context - Hybrid FIRS Function.
        
        Provides comprehensive exception recording that considers both SI and APP
        operations for unified exception management and tracking.
        
        Args:
            transmission_id: UUID of the transmission
            exception: The exception that occurred
            operation_phase: Phase of operation when error occurred
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            error_details: Additional error details
            update_transmission_status: Whether to update transmission status
            
        Returns:
            The created enhanced error record
        """
        error_message = str(exception)
        error_code = exception.__class__.__name__
        stack_trace = traceback.format_exc()
        
        # Enhanced exception classification
        context = {
            "si_operation": bool(si_context),
            "app_operation": bool(app_context),
            "hybrid_operation": bool(hybrid_context),
            "exception_type": error_code,
            **((si_context or {})),
            **((app_context or {})),
            **((hybrid_context or {}))
        }
        
        error_category, severity = self.get_error_classification(error_message, error_code, context)
        
        # Auto-detect enhanced error category and severity
        if isinstance(exception, HTTPException):
            if exception.status_code >= 500:
                severity = HybridErrorSeverity.CRITICAL_HYBRID
            elif exception.status_code >= 400:
                severity = HybridErrorSeverity.MEDIUM_HYBRID
            else:
                severity = HybridErrorSeverity.LOW_HYBRID
        
        enhanced_error_details = {
            **(error_details or {}),
            "exception_type": error_code,
            "exception_args": str(exception.args) if exception.args else None,
            "http_status_code": getattr(exception, 'status_code', None),
            "hybrid_exception": True
        }
        
        return self.record_hybrid_error(
            transmission_id=transmission_id,
            error_message=error_message,
            error_category=error_category,
            severity=severity,
            error_code=error_code,
            operation_phase=operation_phase,
            error_details=enhanced_error_details,
            stack_trace=stack_trace,
            si_context=si_context,
            app_context=app_context,
            hybrid_context=hybrid_context,
            update_transmission_status=update_transmission_status
        )

    def resolve_hybrid_error(
        self,
        error_id: UUID,
        resolution_notes: str,
        user_id: Optional[UUID] = None,
        resolution_type: str = "manual",
        si_actions: Optional[List[str]] = None,
        app_actions: Optional[List[str]] = None,
        hybrid_actions: Optional[List[str]] = None
    ) -> TransmissionError:
        """
        Resolve a hybrid error with enhanced tracking - Hybrid FIRS Function.
        
        Provides comprehensive error resolution with enhanced tracking of
        resolution actions across SI and APP operations.
        
        Args:
            error_id: UUID of the error record
            resolution_notes: Notes on how the error was resolved
            user_id: UUID of the user who resolved the error
            resolution_type: Type of resolution (manual, automatic, hybrid)
            si_actions: SI-specific resolution actions
            app_actions: APP-specific resolution actions
            hybrid_actions: Hybrid resolution actions
            
        Returns:
            The updated error record with enhanced resolution metadata
        """
        resolution_id = str(uuid4())
        
        try:
            error = self.db.query(TransmissionError).filter(
                TransmissionError.id == error_id
            ).first()
            
            if not error:
                raise ValueError(f"Error with ID {error_id} not found")
            
            # Enhanced resolution tracking
            resolution_metadata = {
                "resolution_id": resolution_id,
                "resolution_type": resolution_type,
                "si_actions": si_actions or [],
                "app_actions": app_actions or [],
                "hybrid_actions": hybrid_actions or [],
                "resolution_timestamp": datetime.now().isoformat(),
                "resolved_by": str(user_id) if user_id else None,
                "hybrid_resolution": True,
                "hybrid_version": HYBRID_ERROR_SERVICE_VERSION
            }
            
            error.is_resolved = True
            error.resolved_time = datetime.now()
            error.resolution_notes = resolution_notes
            error.resolution_user_id = user_id
            
            # Update error details with resolution metadata
            error_details = error.error_details or {}
            error_details["resolution_metadata"] = resolution_metadata
            error.error_details = error_details
            
            self.db.commit()
            self.db.refresh(error)
            
            # Update metrics
            self.firs_metrics["resolved_errors"] += 1
            
            logger.info(f"Hybrid FIRS: Error {error_id} resolved by user {user_id} (Resolution ID: {resolution_id})")
            
            return error
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Hybrid FIRS: Error resolving error {error_id} (Resolution ID: {resolution_id}): {str(e)}")
            raise

    def get_hybrid_error_statistics(
        self,
        organization_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_hybrid_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive hybrid error statistics - Hybrid FIRS Function.
        
        Provides detailed error statistics that include both SI and APP
        operations for comprehensive error analysis and reporting.
        
        Args:
            organization_id: UUID of the organization
            start_date: Start date for statistics
            end_date: End date for statistics
            include_hybrid_metrics: Whether to include hybrid-specific metrics
            
        Returns:
            Dictionary with comprehensive error statistics
        """
        try:
            # Base query
            query = self.db.query(
                TransmissionError.error_category,
                func.count(TransmissionError.id).label("count"),
                func.sum(TransmissionError.is_resolved.cast(Integer)).label("resolved_count")
            )
            
            if organization_id:
                query = query.join(TransmissionRecord).filter(
                    TransmissionRecord.organization_id == organization_id
                )
            
            if start_date:
                query = query.filter(TransmissionError.error_time >= start_date)
            
            if end_date:
                query = query.filter(TransmissionError.error_time <= end_date)
            
            stats_by_category = query.group_by(TransmissionError.error_category).all()
            
            # Get overall stats
            total_query = self.db.query(
                func.count(TransmissionError.id).label("total"),
                func.sum(TransmissionError.is_resolved.cast(Integer)).label("resolved"),
                func.count(func.distinct(TransmissionError.transmission_id)).label("affected_transmissions")
            )
            
            if organization_id:
                total_query = total_query.join(TransmissionRecord).filter(
                    TransmissionRecord.organization_id == organization_id
                )
            
            if start_date:
                total_query = total_query.filter(TransmissionError.error_time >= start_date)
            
            if end_date:
                total_query = total_query.filter(TransmissionError.error_time <= end_date)
            
            totals = total_query.first()
            
            # Build basic results
            results = {
                "total_errors": totals.total if totals else 0,
                "resolved_errors": totals.resolved if totals else 0,
                "affected_transmissions": totals.affected_transmissions if totals else 0,
                "resolution_rate": (totals.resolved / totals.total) if totals and totals.total > 0 else 0,
                "by_category": [
                    {
                        "category": category,
                        "count": count,
                        "resolved_count": resolved_count,
                        "resolution_rate": (resolved_count / count) if count > 0 else 0
                    }
                    for category, count, resolved_count in stats_by_category
                ]
            }
            
            # Add hybrid metrics if requested
            if include_hybrid_metrics:
                results["hybrid_metrics"] = {
                    **self.firs_metrics,
                    "error_analytics": dict(self.error_analytics),
                    "escalation_summary": {
                        "total_escalations": sum(1 for track in self.escalation_tracking.values() if track["escalated"]),
                        "pending_escalations": sum(1 for track in self.escalation_tracking.values() if not track["escalated"] and track["error_count"] >= DEFAULT_ERROR_ESCALATION_THRESHOLD)
                    },
                    "firs_compliance_impact": {
                        "high_risk_errors": sum(1 for cat_data in self.error_analytics.values() if any("critical" in sev.lower() for sev in cat_data["severity_breakdown"].keys())),
                        "submission_blocking_errors": len([cat for cat in self.error_analytics.keys() if "transmission" in cat.lower() or "certificate" in cat.lower()])
                    },
                    "hybrid_version": HYBRID_ERROR_SERVICE_VERSION,
                    "statistics_generated_at": datetime.now().isoformat()
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid FIRS: Error generating statistics: {str(e)}")
            return {
                "error": str(e),
                "hybrid_statistics": False,
                "timestamp": datetime.now().isoformat()
            }

    def get_error_trends(
        self,
        organization_id: Optional[UUID] = None,
        days: int = 30,
        include_predictions: bool = False
    ) -> Dict[str, Any]:
        """
        Get error trends for hybrid operations - Hybrid FIRS Function.
        
        Provides trend analysis for errors across SI and APP operations
        with optional predictive analytics.
        
        Args:
            organization_id: UUID of the organization
            days: Number of days to analyze
            include_predictions: Whether to include trend predictions
            
        Returns:
            Dictionary with error trend analysis
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get daily error counts
            daily_query = self.db.query(
                func.date(TransmissionError.error_time).label("date"),
                func.count(TransmissionError.id).label("count")
            ).filter(
                TransmissionError.error_time >= start_date,
                TransmissionError.error_time <= end_date
            )
            
            if organization_id:
                daily_query = daily_query.join(TransmissionRecord).filter(
                    TransmissionRecord.organization_id == organization_id
                )
            
            daily_counts = daily_query.group_by(func.date(TransmissionError.error_time)).all()
            
            # Build trend data
            trend_data = {
                "period": f"{days} days",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "daily_counts": [
                    {
                        "date": str(date),
                        "count": count
                    }
                    for date, count in daily_counts
                ],
                "total_errors": sum(count for _, count in daily_counts),
                "average_daily_errors": sum(count for _, count in daily_counts) / days if days > 0 else 0,
                "peak_day": max(daily_counts, key=lambda x: x[1]) if daily_counts else None,
                "hybrid_trend_analysis": True,
                "generated_at": datetime.now().isoformat()
            }
            
            # Add predictions if requested
            if include_predictions and daily_counts:
                # Simple linear trend prediction
                counts = [count for _, count in daily_counts]
                if len(counts) >= 2:
                    # Calculate trend
                    x = list(range(len(counts)))
                    y = counts
                    n = len(counts)
                    
                    # Linear regression
                    sum_x = sum(x)
                    sum_y = sum(y)
                    sum_xy = sum(x[i] * y[i] for i in range(n))
                    sum_x2 = sum(x[i] ** 2 for i in range(n))
                    
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
                    intercept = (sum_y - slope * sum_x) / n
                    
                    # Predict next 7 days
                    predictions = []
                    for i in range(7):
                        predicted_count = max(0, slope * (len(counts) + i) + intercept)
                        predictions.append({
                            "day": i + 1,
                            "predicted_count": round(predicted_count, 2)
                        })
                    
                    trend_data["predictions"] = {
                        "next_7_days": predictions,
                        "trend_direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable",
                        "trend_strength": abs(slope),
                        "prediction_accuracy": "basic_linear_regression"
                    }
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Hybrid FIRS: Error generating trends: {str(e)}")
            return {
                "error": str(e),
                "hybrid_trends": False,
                "timestamp": datetime.now().isoformat()
            }


# Legacy compatibility functions
def record_error(
    db: Session,
    transmission_id: UUID,
    error_message: str,
    error_category: Union[ErrorCategory, str] = ErrorCategory.OTHER,
    severity: Union[ErrorSeverity, str] = ErrorSeverity.MEDIUM,
    error_code: Optional[str] = None,
    operation_phase: Optional[str] = None,
    error_details: Optional[Dict[str, Any]] = None,
    stack_trace: Optional[str] = None,
    update_transmission_status: bool = True
) -> TransmissionError:
    """
    Legacy compatibility function for recording errors.
    
    This function maintains backward compatibility while delegating to the
    enhanced hybrid error reporting service.
    """
    service = HybridFIRSErrorReportingService(db)
    return service.record_hybrid_error(
        transmission_id=transmission_id,
        error_message=error_message,
        error_category=error_category,
        severity=severity,
        error_code=error_code,
        operation_phase=operation_phase,
        error_details=error_details,
        stack_trace=stack_trace,
        update_transmission_status=update_transmission_status
    )


def record_exception(
    db: Session,
    transmission_id: UUID,
    exception: Exception,
    operation_phase: Optional[str] = None,
    error_category: Union[ErrorCategory, str] = ErrorCategory.OTHER,
    severity: Union[ErrorSeverity, str] = ErrorSeverity.MEDIUM,
    error_details: Optional[Dict[str, Any]] = None,
    update_transmission_status: bool = True
) -> TransmissionError:
    """
    Legacy compatibility function for recording exceptions.
    
    This function maintains backward compatibility while delegating to the
    enhanced hybrid error reporting service.
    """
    service = HybridFIRSErrorReportingService(db)
    return service.record_hybrid_exception(
        transmission_id=transmission_id,
        exception=exception,
        operation_phase=operation_phase,
        error_details=error_details,
        update_transmission_status=update_transmission_status
    )


# Initialize the original ErrorReportingService class for backward compatibility
class ErrorReportingService:
    """Legacy ErrorReportingService class for backward compatibility."""
    
    def __init__(self, db: Session):
        self.db = db
        self._hybrid_service = HybridFIRSErrorReportingService(db)
    
    def record_error(self, *args, **kwargs):
        """Delegate to hybrid service."""
        return self._hybrid_service.record_hybrid_error(*args, **kwargs)
    
    def record_exception(self, *args, **kwargs):
        """Delegate to hybrid service."""
        return self._hybrid_service.record_hybrid_exception(*args, **kwargs)
    
    def resolve_error(self, *args, **kwargs):
        """Delegate to hybrid service."""
        return self._hybrid_service.resolve_hybrid_error(*args, **kwargs)
    
    def get_error_stats(self, *args, **kwargs):
        """Delegate to hybrid service."""
        return self._hybrid_service.get_hybrid_error_statistics(*args, **kwargs)