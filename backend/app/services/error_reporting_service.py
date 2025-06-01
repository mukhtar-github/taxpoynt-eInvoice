"""
Error reporting service for TaxPoynt eInvoice Platform functionality.

This service provides functionality to record, track, and analyze errors 
that occur during transmission operations to improve reliability and support.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List, Union
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException

from app.models.transmission_error import TransmissionError, ErrorCategory, ErrorSeverity
from app.models.transmission import TransmissionRecord, TransmissionStatus

logger = logging.getLogger(__name__)


class ErrorReportingService:
    """Service for managing transmission error reporting."""
    
    def __init__(self, db: Session):
        self.db = db
        
    def record_error(
        self,
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
        Record a transmission error.
        
        Args:
            transmission_id: UUID of the transmission
            error_message: Error message
            error_category: Category of the error
            severity: Severity level of the error
            error_code: Error code if available
            operation_phase: Phase of operation when error occurred
            error_details: Additional error details
            stack_trace: Stack trace if available
            update_transmission_status: Whether to update transmission status to FAILED
            
        Returns:
            The created error record
        """
        try:
            # Verify transmission exists
            transmission = self.db.query(TransmissionRecord).filter(
                TransmissionRecord.id == transmission_id
            ).first()
            
            if not transmission:
                raise ValueError(f"Transmission with ID {transmission_id} not found")
                
            # Create error record
            error = TransmissionError(
                transmission_id=transmission_id,
                error_message=error_message,
                error_code=error_code,
                error_category=error_category,
                severity=severity,
                operation_phase=operation_phase,
                error_details=error_details or {},
                stack_trace=stack_trace,
                error_time=datetime.now()
            )
            
            self.db.add(error)
            
            # Update transmission status if needed
            if update_transmission_status and transmission.status != TransmissionStatus.FAILED:
                transmission.status = TransmissionStatus.FAILED
                
                # Update metadata with error information
                metadata = transmission.transmission_metadata or {}
                error_history = metadata.get("error_history", [])
                error_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "message": error_message,
                    "category": error_category,
                    "severity": severity,
                    "operation_phase": operation_phase
                })
                metadata["error_history"] = error_history
                metadata["last_error"] = {
                    "timestamp": datetime.now().isoformat(),
                    "message": error_message,
                    "category": error_category,
                    "severity": severity
                }
                transmission.transmission_metadata = metadata
            
            # Add status log for the error if we have the status log model
            try:
                from app.models.transmission_status_log import TransmissionStatusLog
                
                # Only create status log if we're changing the status
                if update_transmission_status and transmission.status == TransmissionStatus.FAILED:
                    status_log = TransmissionStatusLog(
                        transmission_id=transmission_id,
                        previous_status=transmission.status,
                        current_status=TransmissionStatus.FAILED,
                        change_reason=f"Error: {error_message}",
                        change_source="error_reporting",
                        change_detail={
                            "error_category": error_category,
                            "severity": severity,
                            "operation_phase": operation_phase
                        }
                    )
                    self.db.add(status_log)
            except ImportError:
                # Status log model not available, just continue
                pass
                
            # Add audit log if available
            try:
                from app.services.audit_service import AuditService
                from app.models.transmission_audit_log import AuditActionType
                
                audit_service = AuditService(self.db)
                audit_service.log_transmission_action(
                    action_type=AuditActionType.OTHER,
                    transmission_id=transmission_id,
                    organization_id=transmission.organization_id,
                    action_status="failure",
                    error_message=error_message,
                    context_data={
                        "error_category": error_category,
                        "severity": severity,
                        "operation_phase": operation_phase
                    }
                )
            except ImportError:
                # Audit service not available, just continue
                pass
                
            self.db.commit()
            self.db.refresh(error)
            
            # Log the error
            log_method = logger.error if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else logger.warning
            log_method(f"Transmission error: {error_message} | Category: {error_category} | "
                      f"Severity: {severity} | Transmission ID: {transmission_id}")
            
            return error
            
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to record error: {str(e)}")
            raise
            
    def record_exception(
        self,
        transmission_id: UUID,
        exception: Exception,
        operation_phase: Optional[str] = None,
        error_category: Union[ErrorCategory, str] = ErrorCategory.OTHER,
        severity: Union[ErrorSeverity, str] = ErrorSeverity.MEDIUM,
        error_details: Optional[Dict[str, Any]] = None,
        update_transmission_status: bool = True
    ) -> TransmissionError:
        """
        Record an exception that occurred during transmission processing.
        
        Args:
            transmission_id: UUID of the transmission
            exception: The exception that occurred
            operation_phase: Phase of operation when error occurred
            error_category: Category of the error
            severity: Severity level of the error
            error_details: Additional error details
            update_transmission_status: Whether to update transmission status to FAILED
            
        Returns:
            The created error record
        """
        error_message = str(exception)
        error_code = exception.__class__.__name__
        stack_trace = traceback.format_exc()
        
        # Auto-detect error category and severity based on exception type
        if isinstance(exception, HTTPException):
            error_category = ErrorCategory.VALIDATION
            if exception.status_code >= 500:
                severity = ErrorSeverity.HIGH
            elif exception.status_code >= 400:
                severity = ErrorSeverity.MEDIUM
            else:
                severity = ErrorSeverity.LOW
                
        elif "Timeout" in error_code:
            error_category = ErrorCategory.TIMEOUT
            severity = ErrorSeverity.HIGH
            
        elif "Auth" in error_code:
            error_category = ErrorCategory.AUTHENTICATION
            severity = ErrorSeverity.HIGH
            
        elif "Permission" in error_code or "Forbidden" in error_code:
            error_category = ErrorCategory.AUTHORIZATION
            severity = ErrorSeverity.HIGH
            
        elif "Encryption" in error_code or "Crypto" in error_code:
            error_category = ErrorCategory.ENCRYPTION
            severity = ErrorSeverity.HIGH
            
        elif "Signature" in error_code or "Sign" in error_code:
            error_category = ErrorCategory.SIGNATURE
            severity = ErrorSeverity.HIGH
            
        elif any(network_error in error_code for network_error in ["Connection", "Network", "Socket", "HTTP"]):
            error_category = ErrorCategory.NETWORK
            severity = ErrorSeverity.MEDIUM
            
        return self.record_error(
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
        
    def resolve_error(
        self,
        error_id: UUID,
        resolution_notes: str,
        user_id: Optional[UUID] = None
    ) -> TransmissionError:
        """
        Mark a transmission error as resolved.
        
        Args:
            error_id: UUID of the error record
            resolution_notes: Notes on how the error was resolved
            user_id: UUID of the user who resolved the error
            
        Returns:
            The updated error record
        """
        error = self.db.query(TransmissionError).filter(
            TransmissionError.id == error_id
        ).first()
        
        if not error:
            raise ValueError(f"Error with ID {error_id} not found")
            
        error.is_resolved = True
        error.resolved_time = datetime.now()
        error.resolution_notes = resolution_notes
        error.resolution_user_id = user_id
        
        self.db.commit()
        self.db.refresh(error)
        
        logger.info(f"Error {error_id} marked as resolved by user {user_id}")
        
        return error
        
    def get_error_stats(
        self,
        organization_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get error statistics for an organization.
        
        Args:
            organization_id: UUID of the organization
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary with error statistics
        """
        query = self.db.query(
            TransmissionError.error_category,
            func.count(TransmissionError.id).label("count"),
            func.avg(TransmissionError.is_resolved.cast(Integer)).label("resolution_rate")
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
        
        # Build results
        results = {
            "total_errors": totals.total if totals else 0,
            "resolved_errors": totals.resolved if totals else 0,
            "affected_transmissions": totals.affected_transmissions if totals else 0,
            "resolution_rate": (totals.resolved / totals.total) if totals and totals.total > 0 else 0,
            "by_category": [
                {
                    "category": category,
                    "count": count,
                    "resolution_rate": resolution_rate
                }
                for category, count, resolution_rate in stats_by_category
            ]
        }
        
        return results
