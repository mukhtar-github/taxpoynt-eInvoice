"""
Submission metrics service for monitoring dashboard.

This module provides functionality for collecting and calculating metrics
related to invoice submissions, including processing times, status breakdowns,
and error statistics.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from sqlalchemy import func, desc, and_, or_, text, cast, Float
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.submission import SubmissionRecord, SubmissionStatus, SubmissionStatusUpdate
from app.models.submission_retry import SubmissionRetry, RetryStatus, FailureSeverity
from app.models.irn import IRNRecord
from app.models.integration import Integration, IntegrationType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SubmissionMetricsService:
    """
    Service for collecting and calculating submission metrics for the monitoring dashboard.
    
    This service provides functions to gather metrics about invoice submissions,
    processing times, status distributions, and error patterns.
    """
    
    @staticmethod
    def get_submission_metrics(
        db: Session, 
        time_range: str = "24h",
        organization_id: Optional[str] = None,
        integration_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics about invoice submissions.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            organization_id: Optional filter by organization ID
            integration_type: Optional filter by integration type (e.g., "odoo")
            status_filter: Optional filter by submission status
            
        Returns:
            Dictionary with submission metrics
        """
        # Calculate time threshold based on time_range
        now = datetime.utcnow()
        if time_range == "24h":
            time_threshold = now - timedelta(hours=24)
        elif time_range == "7d":
            time_threshold = now - timedelta(days=7)
        elif time_range == "30d":
            time_threshold = now - timedelta(days=30)
        else:
            time_threshold = datetime.min  # All time
            
        # Base query
        query = db.query(SubmissionRecord)
        
        # Add time filter
        if time_range != "all":
            query = query.filter(SubmissionRecord.created_at >= time_threshold)
            
        # Add organization filter if provided
        if organization_id:
            # Join with integration to get organization
            query = query.join(
                Integration, 
                SubmissionRecord.integration_id == Integration.id
            ).filter(Integration.organization_id == organization_id)
        
        # Add integration type filter if provided
        if integration_type:
            query = query.join(
                Integration, 
                SubmissionRecord.integration_id == Integration.id
            ).filter(Integration.integration_type == integration_type)
        
        # Add status filter if provided
        if status_filter:
            try:
                submission_status = SubmissionStatus(status_filter)
                query = query.filter(SubmissionRecord.status == submission_status)
            except ValueError:
                # Invalid status, ignore filter
                logger.warning(f"Invalid status filter: {status_filter}")
        
        # Get total count
        total_count = query.count()
        
        if total_count == 0:
            # Return empty metrics if no submissions
            return {
                "timestamp": now.isoformat(),
                "summary": {
                    "total_submissions": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "pending_count": 0,
                    "success_rate": 0.0,
                    "avg_processing_time": 0.0,
                    "common_errors": []
                },
                "status_breakdown": [],
                "hourly_submissions": [],
                "daily_submissions": [],
                "common_errors": [],
                "time_range": time_range
            }
        
        # Get counts by status
        status_counts = {
            status.value: query.filter(SubmissionRecord.status == status).count()
            for status in SubmissionStatus
        }
        
        # Calculate success, failed and pending counts
        success_statuses = [SubmissionStatus.ACCEPTED, SubmissionStatus.SIGNED]
        failed_statuses = [SubmissionStatus.REJECTED, SubmissionStatus.FAILED, SubmissionStatus.ERROR, SubmissionStatus.CANCELLED]
        pending_statuses = [SubmissionStatus.PENDING, SubmissionStatus.PROCESSING, SubmissionStatus.VALIDATED]
        
        success_count = sum(status_counts.get(status.value, 0) for status in success_statuses)
        failed_count = sum(status_counts.get(status.value, 0) for status in failed_statuses)
        pending_count = sum(status_counts.get(status.value, 0) for status in pending_statuses)
        
        # Calculate success rate
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        
        # Calculate status breakdown
        status_breakdown = []
        for status in SubmissionStatus:
            count = status_counts.get(status.value, 0)
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            status_breakdown.append({
                "status": status.value,
                "count": count,
                "percentage": percentage
            })
        
        # Calculate average processing time
        # We'll define processing time as the time between creation and completion (success/failure)
        completed_submissions = query.filter(
            SubmissionRecord.status.in_([s.value for s in success_statuses + failed_statuses])
        ).all()
        
        processing_times = []
        for sub in completed_submissions:
            if sub.last_updated and sub.created_at:
                processing_time = (sub.last_updated - sub.created_at).total_seconds()
                processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Get hourly submission data
        hourly_submissions = []
        for hour_offset in range(24):
            hour_start = now - timedelta(hours=hour_offset + 1)
            hour_end = now - timedelta(hours=hour_offset)
            
            hour_query = query.filter(
                SubmissionRecord.created_at >= hour_start,
                SubmissionRecord.created_at < hour_end
            )
            
            hour_total = hour_query.count()
            hour_success = hour_query.filter(
                SubmissionRecord.status.in_([s.value for s in success_statuses])
            ).count()
            hour_failed = hour_query.filter(
                SubmissionRecord.status.in_([s.value for s in failed_statuses])
            ).count()
            hour_pending = hour_query.filter(
                SubmissionRecord.status.in_([s.value for s in pending_statuses])
            ).count()
            
            hour_success_rate = (hour_success / hour_total) * 100 if hour_total > 0 else 0
            
            hourly_submissions.append({
                "hour": hour_offset,
                "timestamp": hour_end.isoformat(),
                "total": hour_total,
                "success": hour_success,
                "failed": hour_failed,
                "pending": hour_pending,
                "success_rate": hour_success_rate
            })
        
        # Get daily submission data
        daily_submissions = []
        for day_offset in range(min(30, int(time_range.replace("d", "")) if time_range.endswith("d") else 30)):
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=day_offset + 1)
            day_end = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=day_offset)
            
            day_query = query.filter(
                SubmissionRecord.created_at >= day_start,
                SubmissionRecord.created_at < day_end
            )
            
            day_total = day_query.count()
            day_success = day_query.filter(
                SubmissionRecord.status.in_([s.value for s in success_statuses])
            ).count()
            day_failed = day_query.filter(
                SubmissionRecord.status.in_([s.value for s in failed_statuses])
            ).count()
            day_pending = day_query.filter(
                SubmissionRecord.status.in_([s.value for s in pending_statuses])
            ).count()
            
            day_success_rate = (day_success / day_total) * 100 if day_total > 0 else 0
            
            daily_submissions.append({
                "day": day_offset,
                "date": day_end.strftime("%Y-%m-%d"),
                "total": day_total,
                "success": day_success,
                "failed": day_failed,
                "pending": day_pending,
                "success_rate": day_success_rate
            })
        
        # Get common errors from submission retries
        error_query = db.query(
            SubmissionRetry.error_type,
            func.count(SubmissionRetry.id).label("count"),
            SubmissionRetry.severity
        ).join(
            SubmissionRecord,
            SubmissionRetry.submission_id == SubmissionRecord.id
        )
        
        # Apply the same filters as the main query
        if time_range != "all":
            error_query = error_query.filter(SubmissionRecord.created_at >= time_threshold)
            
        if organization_id:
            error_query = error_query.join(
                Integration, 
                SubmissionRecord.integration_id == Integration.id
            ).filter(Integration.organization_id == organization_id)
        
        if integration_type:
            error_query = error_query.join(
                Integration, 
                SubmissionRecord.integration_id == Integration.id,
                isouter=True
            ).filter(Integration.integration_type == integration_type)
        
        common_errors = error_query.group_by(
            SubmissionRetry.error_type, 
            SubmissionRetry.severity
        ).order_by(desc("count")).limit(10).all()
        
        error_list = []
        for error_type, count, severity in common_errors:
            if not error_type:
                continue
                
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            error_list.append({
                "error_type": error_type,
                "count": count,
                "percentage": percentage,
                "severity": severity
            })
        
        # Assemble response
        return {
            "timestamp": now.isoformat(),
            "summary": {
                "total_submissions": total_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "pending_count": pending_count,
                "success_rate": success_rate,
                "avg_processing_time": avg_processing_time,
                "common_errors": error_list[:5]  # Top 5 for summary
            },
            "status_breakdown": status_breakdown,
            "hourly_submissions": hourly_submissions,
            "daily_submissions": daily_submissions,
            "common_errors": error_list,
            "time_range": time_range
        }
    
    @staticmethod
    def get_retry_metrics(
        db: Session, 
        time_range: str = "24h",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics about submission retries.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            organization_id: Optional filter by organization ID
            
        Returns:
            Dictionary with retry metrics
        """
        # Calculate time threshold based on time_range
        now = datetime.utcnow()
        if time_range == "24h":
            time_threshold = now - timedelta(hours=24)
        elif time_range == "7d":
            time_threshold = now - timedelta(days=7)
        elif time_range == "30d":
            time_threshold = now - timedelta(days=30)
        else:
            time_threshold = datetime.min  # All time
        
        # Base query
        query = db.query(SubmissionRetry)
        
        # Add time filter
        if time_range != "all":
            query = query.filter(SubmissionRetry.created_at >= time_threshold)
        
        # Add organization filter if provided
        if organization_id:
            # Join with submission and integration to get organization
            query = query.join(
                SubmissionRecord,
                SubmissionRetry.submission_id == SubmissionRecord.id
            ).join(
                Integration, 
                SubmissionRecord.integration_id == Integration.id
            ).filter(Integration.organization_id == organization_id)
        
        # Get total count
        total_count = query.count()
        
        if total_count == 0:
            # Return empty metrics if no retries
            return {
                "timestamp": now.isoformat(),
                "metrics": {
                    "total_retries": 0,
                    "success_count": 0,
                    "failed_count": 0,
                    "pending_count": 0,
                    "success_rate": 0.0,
                    "avg_attempts": 0.0,
                    "max_attempts_reached_count": 0
                },
                "retry_breakdown_by_status": [],
                "retry_breakdown_by_severity": [],
                "time_range": time_range
            }
        
        # Get counts by status
        status_counts = {
            status.value: query.filter(SubmissionRetry.status == status).count()
            for status in RetryStatus
        }
        
        # Calculate success, failed and pending counts
        success_count = status_counts.get(RetryStatus.SUCCEEDED.value, 0)
        failed_count = status_counts.get(RetryStatus.FAILED.value, 0)
        pending_count = status_counts.get(RetryStatus.PENDING.value, 0) + status_counts.get(RetryStatus.IN_PROGRESS.value, 0)
        max_attempts_count = status_counts.get(RetryStatus.MAX_RETRIES_EXCEEDED.value, 0)
        
        # Calculate success rate
        completed_count = success_count + failed_count + max_attempts_count
        success_rate = (success_count / completed_count) * 100 if completed_count > 0 else 0
        
        # Calculate average attempts
        avg_attempts = db.query(func.avg(SubmissionRetry.attempt_number)).scalar() or 0
        
        # Calculate status breakdown
        status_breakdown = []
        for status in RetryStatus:
            count = status_counts.get(status.value, 0)
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            status_breakdown.append({
                "status": status.value,
                "count": count,
                "percentage": percentage
            })
        
        # Calculate severity breakdown
        severity_counts = {
            severity.value: query.filter(SubmissionRetry.severity == severity).count()
            for severity in FailureSeverity
        }
        
        severity_breakdown = []
        for severity in FailureSeverity:
            count = severity_counts.get(severity.value, 0)
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            severity_breakdown.append({
                "status": severity.value,  # Using 'status' field for consistency
                "count": count,
                "percentage": percentage
            })
        
        # Assemble response
        return {
            "timestamp": now.isoformat(),
            "metrics": {
                "total_retries": total_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "pending_count": pending_count,
                "success_rate": success_rate,
                "avg_attempts": avg_attempts,
                "max_attempts_reached_count": max_attempts_count
            },
            "retry_breakdown_by_status": status_breakdown,
            "retry_breakdown_by_severity": severity_breakdown,
            "time_range": time_range
        }
    
    @staticmethod
    def get_odoo_submission_metrics(db: Session, time_range: str = "24h") -> Dict[str, Any]:
        """
        Get specific metrics about Odoo invoice submissions.
        
        This method specializes in Odoo integration metrics for the dashboard,
        focusing on the ERP-first integration strategy.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            
        Returns:
            Dictionary with Odoo submission metrics
        """
        # Use the main method with integration_type filter
        metrics = SubmissionMetricsService.get_submission_metrics(
            db=db,
            time_range=time_range,
            integration_type="odoo"
        )
        
        # Add Odoo-specific metrics
        
        # Calculate conversion from Odoo invoices to FIRS submissions
        now = datetime.utcnow()
        if time_range == "24h":
            time_threshold = now - timedelta(hours=24)
        elif time_range == "7d":
            time_threshold = now - timedelta(days=7)
        elif time_range == "30d":
            time_threshold = now - timedelta(days=30)
        else:
            time_threshold = datetime.min  # All time
            
        # Query Odoo submissions
        odoo_query = db.query(SubmissionRecord).filter(
            SubmissionRecord.source_type == "odoo"
        )
        
        if time_range != "all":
            odoo_query = odoo_query.filter(SubmissionRecord.created_at >= time_threshold)
        
        odoo_count = odoo_query.count()
        
        # Enrich the metrics with Odoo-specific information
        metrics["odoo_metrics"] = {
            "total_odoo_submissions": odoo_count,
            "percentage_of_all_submissions": (odoo_count / metrics["summary"]["total_submissions"]) * 100 if metrics["summary"]["total_submissions"] > 0 else 0,
        }
        
        return metrics
