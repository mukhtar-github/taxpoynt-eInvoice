"""
Metrics service for monitoring dashboard.

This module provides functionality for collecting and calculating metrics
for the monitoring dashboard, including IRN generation, validation,
and Odoo integration metrics.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from sqlalchemy import func, desc, and_, or_, text
from sqlalchemy.orm import Session

from app.models.irn import IRNRecord, IRNValidationRecord, IRNStatus
from app.models.validation import ValidationRecord
from app.models.integration import Integration, IntegrationType
from app.models.organization import Organization
from app.models.api_keys import APIKey, APIKeyUsage
from app.models.transmission import TransmissionRecord, TransmissionStatus
from app.models.transmission_error import TransmissionError, ErrorCategory, ErrorSeverity
from app.models.transmission_metrics import TransmissionDailyMetrics, TransmissionMetricsSnapshot
from app.models.transmission_status_log import TransmissionStatusLog

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for collecting and calculating metrics for the monitoring dashboard.
    
    This service provides functions to gather metrics about IRN generation,
    validation, Odoo integration, and general system health.
    """
    
    @staticmethod
    def get_irn_generation_metrics(
        db: Session, 
        time_range: str = "24h",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics about IRN generation.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            organization_id: Optional filter by organization ID
            
        Returns:
            Dictionary with IRN generation metrics
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
        query = db.query(IRNRecord)
        
        # Add time and organization filters
        if time_range != "all":
            query = query.filter(IRNRecord.generated_at >= time_threshold)
            
        if organization_id:
            # Join with integration to get organization
            query = query.join(
                Integration, 
                IRNRecord.integration_id == Integration.id.cast(str)
            ).filter(Integration.organization_id == organization_id)
        
        # Get total count
        total_count = query.count()
        
        # Get count by status
        status_counts = {
            "unused": query.filter(IRNRecord.status == IRNStatus.UNUSED.value).count(),
            "active": query.filter(IRNRecord.status == IRNStatus.ACTIVE.value).count(),
            "used": query.filter(IRNRecord.status == IRNStatus.USED.value).count(),
            "expired": query.filter(IRNRecord.status == IRNStatus.EXPIRED.value).count(),
            "cancelled": query.filter(IRNRecord.status == IRNStatus.CANCELLED.value).count()
        }
        
        # Get generation rate (per hour) over time
        hourly_generation = []
        for hour_offset in range(24):
            hour_start = now - timedelta(hours=hour_offset + 1)
            hour_end = now - timedelta(hours=hour_offset)
            
            hour_query = query.filter(
                IRNRecord.generated_at >= hour_start,
                IRNRecord.generated_at < hour_end
            )
            
            hourly_generation.append({
                "hour": hour_offset,
                "timestamp": hour_end.isoformat(),
                "count": hour_query.count()
            })
            
        # Get daily generation for the past 30 days
        daily_generation = []
        for day_offset in range(30):
            day_start = (now - timedelta(days=day_offset + 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = (now - timedelta(days=day_offset)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
            day_query = query.filter(
                IRNRecord.generated_at >= day_start,
                IRNRecord.generated_at < day_end
            )
            
            daily_generation.append({
                "day": day_offset,
                "date": day_end.date().isoformat(),
                "count": day_query.count()
            })
        
        return {
            "total_count": total_count,
            "status_counts": status_counts,
            "hourly_generation": sorted(hourly_generation, key=lambda x: x["hour"]),
            "daily_generation": sorted(daily_generation, key=lambda x: x["day"]),
            "time_range": time_range
        }
    
    @staticmethod
    def get_validation_metrics(
        db: Session, 
        time_range: str = "24h",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics about invoice validation.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            organization_id: Optional filter by organization ID
            
        Returns:
            Dictionary with validation metrics
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
        
        # Base query for validation records
        query = db.query(ValidationRecord)
        
        # Add time and organization filters
        if time_range != "all":
            query = query.filter(ValidationRecord.validation_time >= time_threshold)
            
        if organization_id:
            # No need to join with integration since validation_records already has integration_id
            query = query.join(
                Integration,
                ValidationRecord.integration_id == Integration.id
            ).filter(Integration.organization_id == organization_id)
        
        # Get total count
        total_count = query.count()
        
        # Get validation success vs. failure
        success_count = query.filter(ValidationRecord.is_valid == True).count()
        failure_count = query.filter(ValidationRecord.is_valid == False).count()
        
        # Calculate success rate
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        # Get common validation errors
        common_errors = []
        try:
            # This is a complex query that depends on the JSON structure of the issues field
            # For PostgreSQL, we would use jsonb functions
            # For SQLite, we need a simpler approach
            
            # Get failed validations
            failed_validations = query.filter(
                ValidationRecord.is_valid == False
            ).order_by(desc(ValidationRecord.validation_time)).limit(100).all()
            
            # Extract and count error types
            error_counts = {}
            for validation in failed_validations:
                issues = validation.issues or []
                if isinstance(issues, str):
                    # If stored as string, try to parse
                    import json
                    try:
                        issues = json.loads(issues)
                    except:
                        issues = []
                        
                for issue in issues:
                    error_type = issue.get("error_code", "unknown")
                    error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            # Convert to sorted list
            common_errors = [
                {"error_code": code, "count": count, "percentage": (count / len(failed_validations) * 100) if len(failed_validations) > 0 else 0}
                for code, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
            ][:10]  # Top 10 errors
        except Exception as e:
            logger.error(f"Error calculating common validation errors: {str(e)}")
        
        # Get validation rate (per hour) over time
        hourly_validation = []
        for hour_offset in range(24):
            hour_start = now - timedelta(hours=hour_offset + 1)
            hour_end = now - timedelta(hours=hour_offset)
            
            hour_query = query.filter(
                ValidationRecord.validation_time >= hour_start,
                ValidationRecord.validation_time < hour_end
            )
            
            total = hour_query.count()
            success = hour_query.filter(ValidationRecord.is_valid == True).count()
            
            hourly_validation.append({
                "hour": hour_offset,
                "timestamp": hour_end.isoformat(),
                "total": total,
                "success": success,
                "failure": total - success,
                "success_rate": (success / total * 100) if total > 0 else 0
            })
        
        return {
            "total_count": total_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_rate,
            "common_errors": common_errors,
            "hourly_validation": sorted(hourly_validation, key=lambda x: x["hour"]),
            "time_range": time_range
        }
    
    @staticmethod
    def get_b2b_vs_b2c_metrics(
        db: Session, 
        time_range: str = "24h",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics comparing B2B vs B2C invoice processing.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            organization_id: Optional filter by organization ID
            
        Returns:
            Dictionary with B2B vs B2C metrics
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
        
        # For this metric, we need to analyze invoice data
        # We'll consider an invoice as B2B if it has a customer TIN or VAT number
        # This is a simplification - in a real implementation, we would need more complex logic
        
        # Get all validation records with invoice data
        query = db.query(ValidationRecord)
        
        # Add time and organization filters
        if time_range != "all":
            query = query.filter(ValidationRecord.validation_time >= time_threshold)
            
        if organization_id:
            query = query.join(
                Integration,
                ValidationRecord.integration_id == Integration.id
            ).filter(Integration.organization_id == organization_id)
        
        # Count B2B vs B2C invoices
        # This is a simplification - in a real implementation, we would need more complex logic
        b2b_count = 0
        b2c_count = 0
        total_count = 0
        
        for record in query.all():
            total_count += 1
            invoice_data = record.invoice_data or {}
            
            # Simple heuristic for B2B vs B2C
            is_b2b = False
            
            # Check for customer TIN or VAT number in invoice data
            customer = invoice_data.get("customer", {})
            if customer.get("tax_id") or customer.get("vat"):
                is_b2b = True
                
            if is_b2b:
                b2b_count += 1
            else:
                b2c_count += 1
        
        # Calculate validation success rates for B2B vs B2C
        b2b_success_count = 0
        b2c_success_count = 0
        
        for record in query.filter(ValidationRecord.is_valid == True).all():
            invoice_data = record.invoice_data or {}
            
            # Simple heuristic for B2B vs B2C
            is_b2b = False
            
            # Check for customer TIN or VAT number in invoice data
            customer = invoice_data.get("customer", {})
            if customer.get("tax_id") or customer.get("vat"):
                is_b2b = True
                
            if is_b2b:
                b2b_success_count += 1
            else:
                b2c_success_count += 1
        
        b2b_success_rate = (b2b_success_count / b2b_count * 100) if b2b_count > 0 else 0
        b2c_success_rate = (b2c_success_count / b2c_count * 100) if b2c_count > 0 else 0
        
        # Get daily B2B vs B2C counts for the past 30 days
        daily_breakdown = []
        for day_offset in range(30):
            day_start = (now - timedelta(days=day_offset + 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = (now - timedelta(days=day_offset)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
            day_query = query.filter(
                ValidationRecord.validation_time >= day_start,
                ValidationRecord.validation_time < day_end
            ).all()
            
            day_b2b = 0
            day_b2c = 0
            
            for record in day_query:
                invoice_data = record.invoice_data or {}
                
                # Simple heuristic for B2B vs B2C
                is_b2b = False
                
                # Check for customer TIN or VAT number in invoice data
                customer = invoice_data.get("customer", {})
                if customer.get("tax_id") or customer.get("vat"):
                    is_b2b = True
                    
                if is_b2b:
                    day_b2b += 1
                else:
                    day_b2c += 1
            
            daily_breakdown.append({
                "day": day_offset,
                "date": day_end.date().isoformat(),
                "b2b_count": day_b2b,
                "b2c_count": day_b2c,
                "total": day_b2b + day_b2c
            })
        
        return {
            "total_count": total_count,
            "b2b_count": b2b_count,
            "b2c_count": b2c_count,
            "b2b_percentage": (b2b_count / total_count * 100) if total_count > 0 else 0,
            "b2c_percentage": (b2c_count / total_count * 100) if total_count > 0 else 0,
            "b2b_success_rate": b2b_success_rate,
            "b2c_success_rate": b2c_success_rate,
            "daily_breakdown": sorted(daily_breakdown, key=lambda x: x["day"]),
            "time_range": time_range
        }
    
    @staticmethod
    def get_odoo_integration_metrics(
        db: Session, 
        time_range: str = "24h",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics about Odoo integration status and performance.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            organization_id: Optional filter by organization ID
            
        Returns:
            Dictionary with Odoo integration metrics
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
        
        # Get Odoo integrations
        query = db.query(Integration).filter(
            Integration.integration_type == IntegrationType.ODOO
        )
        
        if organization_id:
            query = query.filter(Integration.organization_id == organization_id)
        
        odoo_integrations = query.all()
        
        # Get integration status and counts
        active_count = query.filter(Integration.is_active == True).count()
        inactive_count = query.filter(Integration.is_active == False).count()
        
        # Get total invoice count from validation records
        invoice_query = db.query(ValidationRecord).join(
            Integration,
            ValidationRecord.integration_id == Integration.id
        ).filter(
            Integration.integration_type == IntegrationType.ODOO
        )
        
        if time_range != "all":
            invoice_query = invoice_query.filter(
                ValidationRecord.validation_time >= time_threshold
            )
            
        if organization_id:
            invoice_query = invoice_query.filter(
                Integration.organization_id == organization_id
            )
            
        total_invoices = invoice_query.count()
        
        # Get success rate
        successful_invoices = invoice_query.filter(
            ValidationRecord.is_valid == True
        ).count()
        
        success_rate = (successful_invoices / total_invoices * 100) if total_invoices > 0 else 0
        
        # Get integration statuses
        integration_statuses = []
        for integration in odoo_integrations:
            # Get last validation record for this integration
            last_validation = db.query(ValidationRecord).filter(
                ValidationRecord.integration_id == integration.id
            ).order_by(desc(ValidationRecord.validation_time)).first()
            
            integration_statuses.append({
                "integration_id": str(integration.id),
                "name": integration.name,
                "organization_id": str(integration.organization_id),
                "is_active": integration.is_active,
                "created_at": integration.created_at.isoformat(),
                "last_validated": last_validation.validation_time.isoformat() if last_validation else None,
                "last_validation_success": last_validation.is_valid if last_validation else None
            })
        
        # Get hourly invoice count
        hourly_counts = []
        for hour_offset in range(24):
            hour_start = now - timedelta(hours=hour_offset + 1)
            hour_end = now - timedelta(hours=hour_offset)
            
            hour_query = invoice_query.filter(
                ValidationRecord.validation_time >= hour_start,
                ValidationRecord.validation_time < hour_end
            )
            
            hourly_counts.append({
                "hour": hour_offset,
                "timestamp": hour_end.isoformat(),
                "count": hour_query.count()
            })
        
        return {
            "total_integrations": len(odoo_integrations),
            "active_integrations": active_count,
            "inactive_integrations": inactive_count,
            "total_invoices": total_invoices,
            "successful_invoices": successful_invoices,
            "success_rate": success_rate,
            "integration_statuses": integration_statuses,
            "hourly_counts": sorted(hourly_counts, key=lambda x: x["hour"]),
            "time_range": time_range
        }
    
    @staticmethod
    def get_system_health_metrics(
        db: Session, 
        time_range: str = "24h"
    ) -> Dict[str, Any]:
        """
        Get metrics about overall system health.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            
        Returns:
            Dictionary with system health metrics
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
        
        # Get API key usage statistics
        api_usage_query = db.query(APIKeyUsage)
        
        if time_range != "all":
            api_usage_query = api_usage_query.filter(
                APIKeyUsage.timestamp >= time_threshold
            )
            
        api_usage = api_usage_query.all()
        
        # Calculate total requests and error rate
        total_requests = sum(usage.request_count for usage in api_usage)
        error_requests = sum(usage.error_count for usage in api_usage)
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate average response time
        total_response_time = sum(
            usage.total_response_time for usage in api_usage if usage.total_response_time
        )
        avg_response_time = (
            total_response_time / total_requests if total_requests > 0 else 0
        )
        
        # Get hourly request rates
        hourly_requests = []
        for hour_offset in range(24):
            hour_start = now - timedelta(hours=hour_offset + 1)
            hour_end = now - timedelta(hours=hour_offset)
            
            hour_usage = db.query(APIKeyUsage).filter(
                APIKeyUsage.timestamp >= hour_start,
                APIKeyUsage.timestamp < hour_end
            ).all()
            
            hour_requests = sum(usage.request_count for usage in hour_usage)
            hour_errors = sum(usage.error_count for usage in hour_usage)
            
            hourly_requests.append({
                "hour": hour_offset,
                "timestamp": hour_end.isoformat(),
                "requests": hour_requests,
                "errors": hour_errors,
                "error_rate": (hour_errors / hour_requests * 100) if hour_requests > 0 else 0
            })
        
        # Get endpoint popularity
        endpoint_popularity = {}
        for usage in api_usage:
            path = usage.path or "unknown"
            endpoint_popularity[path] = endpoint_popularity.get(path, 0) + usage.request_count
            
        # Convert to sorted list
        endpoint_popularity_list = [
            {"endpoint": path, "count": count, "percentage": (count / total_requests * 100) if total_requests > 0 else 0}
            for path, count in sorted(endpoint_popularity.items(), key=lambda x: x[1], reverse=True)
        ][:10]  # Top 10 endpoints
        
        return {
            "total_requests": total_requests,
            "error_requests": error_requests,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "hourly_requests": sorted(hourly_requests, key=lambda x: x["hour"]),
            "endpoint_popularity": endpoint_popularity_list,
            "time_range": time_range
        }
    
    @staticmethod
    def get_transmission_metrics(
        db: Session, 
        time_range: str = "24h",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get metrics about secure transmissions.
        
        Args:
            db: Database session
            time_range: Time range to consider ("24h", "7d", "30d", "all")
            organization_id: Optional filter by organization ID
            
        Returns:
            Dictionary with transmission metrics
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
        query = db.query(TransmissionRecord)
        
        # Add time and organization filters
        if time_range != "all":
            query = query.filter(TransmissionRecord.created_at >= time_threshold)
            
        if organization_id:
            query = query.filter(TransmissionRecord.organization_id == organization_id)
        
        # Get total count
        total_count = query.count()
        
        # Get count by status
        status_counts = {}
        for status in TransmissionStatus:
            status_counts[status.value] = query.filter(
                TransmissionRecord.status == status
            ).count()
        
        # Get transmission rate (per hour) over time
        hourly_transmission = []
        for hour_offset in range(24):
            hour_start = now - timedelta(hours=hour_offset + 1)
            hour_end = now - timedelta(hours=hour_offset)
            
            hour_query = query.filter(
                TransmissionRecord.created_at >= hour_start,
                TransmissionRecord.created_at < hour_end
            )
            
            hourly_transmission.append({
                "hour": hour_offset,
                "timestamp": hour_end.isoformat(),
                "count": hour_query.count()
            })
            
        # Get daily transmissions for the past 30 days
        daily_transmission = []
        for day_offset in range(30):
            day_start = (now - timedelta(days=day_offset + 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = (now - timedelta(days=day_offset)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
            day_query = query.filter(
                TransmissionRecord.created_at >= day_start,
                TransmissionRecord.created_at < day_end
            )
            
            daily_transmission.append({
                "day": day_offset,
                "date": day_end.date().isoformat(),
                "count": day_query.count()
            })
        
        # Get success rate
        success_count = query.filter(
            TransmissionRecord.status == TransmissionStatus.COMPLETED
        ).count()
        
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        # Get performance metrics
        perf_data = None
        try:
            # Get average processing times from metrics snapshots
            metrics_query = db.query(
                func.avg(TransmissionMetricsSnapshot.total_processing_time_ms),
                func.avg(TransmissionMetricsSnapshot.encryption_time_ms),
                func.avg(TransmissionMetricsSnapshot.network_time_ms),
                func.avg(TransmissionMetricsSnapshot.payload_size_bytes)
            )
            
            if time_range != "all":
                metrics_query = metrics_query.filter(
                    TransmissionMetricsSnapshot.snapshot_time >= time_threshold
                )
                
            if organization_id:
                metrics_query = metrics_query.filter(
                    TransmissionMetricsSnapshot.organization_id == organization_id
                )
                
            avg_total_time, avg_encryption_time, avg_network_time, avg_payload_size = metrics_query.first()
            
            perf_data = {
                "avg_total_processing_time_ms": avg_total_time or 0,
                "avg_encryption_time_ms": avg_encryption_time or 0,
                "avg_network_time_ms": avg_network_time or 0,
                "avg_payload_size_bytes": avg_payload_size or 0
            }
        except Exception as e:
            logger.warning(f"Failed to get performance metrics: {str(e)}")
            perf_data = {
                "avg_total_processing_time_ms": 0,
                "avg_encryption_time_ms": 0,
                "avg_network_time_ms": 0,
                "avg_payload_size_bytes": 0
            }
        
        # Get error rates
        error_data = None
        try:
            # Count errors by category
            error_query = db.query(
                TransmissionError.error_category,
                func.count(TransmissionError.id).label("count")
            ).group_by(TransmissionError.error_category)
            
            # Add time and organization filters for errors
            if time_range != "all":
                error_query = error_query.filter(TransmissionError.error_time >= time_threshold)
                
            if organization_id:
                error_query = error_query.join(TransmissionRecord).filter(
                    TransmissionRecord.organization_id == organization_id
                )
                
            error_counts = {}
            for category, count in error_query.all():
                error_counts[category] = count
            
            # Count total errors
            total_errors = sum(error_counts.values())
            
            error_data = {
                "total_errors": total_errors,
                "error_rate": (total_errors / total_count * 100) if total_count > 0 else 0,
                "error_counts_by_category": error_counts
            }
        except Exception as e:
            logger.warning(f"Failed to get error metrics: {str(e)}")
            error_data = {
                "total_errors": 0,
                "error_rate": 0,
                "error_counts_by_category": {}
            }
            
        return {
            "total_count": total_count,
            "status_counts": status_counts,
            "success_rate": success_rate,
            "hourly_transmission": sorted(hourly_transmission, key=lambda x: x["hour"]),
            "daily_transmission": sorted(daily_transmission, key=lambda x: x["day"]),
            "performance": perf_data,
            "errors": error_data,
            "time_range": time_range
        }
    
    @staticmethod
    def record_transmission_metrics(
        db: Session,
        transmission_id: str,
        total_processing_time_ms: Optional[float] = None,
        encryption_time_ms: Optional[float] = None,
        network_time_ms: Optional[float] = None,
        payload_size_bytes: Optional[int] = None,
        api_endpoint: Optional[str] = None,
        certificate_type: Optional[str] = None,
        payload_type: Optional[str] = None,
        transmission_mode: Optional[str] = None,
        metric_details: Optional[Dict[str, Any]] = None
    ) -> Optional[TransmissionMetricsSnapshot]:
        """
        Record metrics for a specific transmission.
        
        Args:
            db: Database session
            transmission_id: UUID of the transmission
            total_processing_time_ms: Total processing time in milliseconds
            encryption_time_ms: Encryption time in milliseconds
            network_time_ms: Network request time in milliseconds
            payload_size_bytes: Size of the payload in bytes
            api_endpoint: API endpoint used for transmission
            certificate_type: Type of certificate used
            payload_type: Type of payload
            transmission_mode: Mode of transmission (sync, async)
            metric_details: Additional metric details
            
        Returns:
            Created TransmissionMetricsSnapshot or None if failed
        """
        try:
            # Get transmission to extract organization_id
            transmission = db.query(TransmissionRecord).filter(
                TransmissionRecord.id == transmission_id
            ).first()
            
            if not transmission:
                raise ValueError(f"Transmission with ID {transmission_id} not found")
                
            # Create metrics snapshot
            metrics = TransmissionMetricsSnapshot(
                organization_id=transmission.organization_id,
                transmission_id=transmission_id,
                snapshot_time=datetime.now(),
                encryption_time_ms=encryption_time_ms,
                network_time_ms=network_time_ms,
                total_processing_time_ms=total_processing_time_ms,
                payload_size_bytes=payload_size_bytes,
                retry_count=transmission.retry_count or 0,
                api_endpoint=api_endpoint,
                certificate_type=certificate_type,
                payload_type=payload_type,
                transmission_mode=transmission_mode,
                metric_details=metric_details or {}
            )
            
            db.add(metrics)
            db.commit()
            db.refresh(metrics)
            
            logger.debug(f"Recorded metrics for transmission {transmission_id}")
            
            return metrics
            
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to record transmission metrics: {str(e)}")
            # Don't re-raise, just log the error
            return None
    
    @staticmethod
    def update_daily_metrics(db: Session, date: Optional[datetime] = None):
        """
        Update or create daily metrics for all organizations.
        This should be called by a scheduled task.
        
        Args:
            db: Database session
            date: Optional date to update metrics for (defaults to today)
        """
        try:
            # Default to today's date
            if not date:
                date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
            metric_date = date.date()
            
            # Get all organizations
            organizations = db.query(Organization).all()
            
            for org in organizations:
                # Check if metrics already exist for this date and organization
                existing_metrics = db.query(TransmissionDailyMetrics).filter(
                    TransmissionDailyMetrics.organization_id == org.id,
                    TransmissionDailyMetrics.metric_date == metric_date
                ).first()
                
                # Set date range for the day
                day_start = date
                day_end = date + timedelta(days=1)
                
                # Base query for this organization and date
                base_query = db.query(TransmissionRecord).filter(
                    TransmissionRecord.organization_id == org.id,
                    TransmissionRecord.created_at >= day_start,
                    TransmissionRecord.created_at < day_end
                )
                
                # Count transmissions by status
                total_transmissions = base_query.count()
                successful_transmissions = base_query.filter(
                    TransmissionRecord.status == TransmissionStatus.COMPLETED
                ).count()
                failed_transmissions = base_query.filter(
                    TransmissionRecord.status == TransmissionStatus.FAILED
                ).count()
                pending_transmissions = base_query.filter(
                    TransmissionRecord.status.in_([
                        TransmissionStatus.PENDING,
                        TransmissionStatus.IN_PROGRESS
                    ])
                ).count()
                
                # Calculate performance metrics
                metrics_query = db.query(
                    func.avg(TransmissionMetricsSnapshot.total_processing_time_ms),
                    func.avg(TransmissionMetricsSnapshot.encryption_time_ms),
                    func.avg(TransmissionMetricsSnapshot.network_time_ms),
                    func.avg(TransmissionMetricsSnapshot.payload_size_bytes)
                ).filter(
                    TransmissionMetricsSnapshot.organization_id == org.id,
                    TransmissionMetricsSnapshot.snapshot_time >= day_start,
                    TransmissionMetricsSnapshot.snapshot_time < day_end
                )
                
                avg_processing_time, avg_encryption_time, avg_network_time, avg_payload_size = metrics_query.first()
                
                # Calculate success metrics
                first_attempt_success = db.query(TransmissionRecord).filter(
                    TransmissionRecord.organization_id == org.id,
                    TransmissionRecord.created_at >= day_start,
                    TransmissionRecord.created_at < day_end,
                    TransmissionRecord.status == TransmissionStatus.COMPLETED,
                    TransmissionRecord.retry_count == 0
                ).count()
                
                first_attempt_success_rate = (
                    first_attempt_success / total_transmissions * 100
                ) if total_transmissions > 0 else 0
                
                # Calculate average attempts for successful transmissions
                avg_attempts_query = db.query(
                    func.avg(TransmissionRecord.retry_count + 1)
                ).filter(
                    TransmissionRecord.organization_id == org.id,
                    TransmissionRecord.created_at >= day_start,
                    TransmissionRecord.created_at < day_end,
                    TransmissionRecord.status == TransmissionStatus.COMPLETED
                )
                
                avg_attempts = avg_attempts_query.scalar() or 1.0
                
                # Find peak hour
                peak_hour_data = {
                    "hour": 0,
                    "count": 0
                }
                
                for hour in range(24):
                    hour_start = day_start + timedelta(hours=hour)
                    hour_end = day_start + timedelta(hours=hour + 1)
                    
                    hour_count = db.query(TransmissionRecord).filter(
                        TransmissionRecord.organization_id == org.id,
                        TransmissionRecord.created_at >= hour_start,
                        TransmissionRecord.created_at < hour_end
                    ).count()
                    
                    if hour_count > peak_hour_data["count"]:
                        peak_hour_data = {
                            "hour": hour,
                            "count": hour_count
                        }
                
                # Create or update metrics
                if existing_metrics:
                    # Update existing record
                    existing_metrics.total_transmissions = total_transmissions
                    existing_metrics.successful_transmissions = successful_transmissions
                    existing_metrics.failed_transmissions = failed_transmissions
                    existing_metrics.pending_transmissions = pending_transmissions
                    existing_metrics.avg_processing_time_ms = avg_processing_time or 0.0
                    existing_metrics.avg_encryption_time_ms = avg_encryption_time or 0.0
                    existing_metrics.avg_network_time_ms = avg_network_time or 0.0
                    existing_metrics.avg_payload_size_bytes = avg_payload_size or 0
                    existing_metrics.first_attempt_success_rate = first_attempt_success_rate
                    existing_metrics.avg_attempts_to_success = avg_attempts
                    existing_metrics.peak_hour = peak_hour_data["hour"]
                    existing_metrics.peak_hour_transmissions = peak_hour_data["count"]
                    
                    db.add(existing_metrics)
                else:
                    # Create new record
                    new_metrics = TransmissionDailyMetrics(
                        organization_id=org.id,
                        metric_date=metric_date,
                        total_transmissions=total_transmissions,
                        successful_transmissions=successful_transmissions,
                        failed_transmissions=failed_transmissions,
                        pending_transmissions=pending_transmissions,
                        avg_processing_time_ms=avg_processing_time or 0.0,
                        avg_encryption_time_ms=avg_encryption_time or 0.0,
                        avg_network_time_ms=avg_network_time or 0.0,
                        avg_payload_size_bytes=avg_payload_size or 0,
                        first_attempt_success_rate=first_attempt_success_rate,
                        avg_attempts_to_success=avg_attempts,
                        peak_hour=peak_hour_data["hour"],
                        peak_hour_transmissions=peak_hour_data["count"]
                    )
                    
                    db.add(new_metrics)
            
            db.commit()
            logger.info(f"Updated daily transmission metrics for {len(organizations)} organizations on {metric_date}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update daily transmission metrics: {str(e)}")
            # Don't re-raise, just log the error
    
    @staticmethod
    def get_transmission_metrics_summary(
        db: Session, 
        time_range: str = "24h",
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of transmission metrics for dashboard display.
        
        Args:
            db: Database session
            time_range: Time range to consider
            organization_id: Optional filter by organization ID
            
        Returns:
            Dictionary with transmission summary metrics
        """
        try:
            metrics = MetricsService.get_transmission_metrics(db, time_range, organization_id)
            
            # Extract key metrics for the summary
            return {
                "total_transmissions": metrics["total_count"],
                "success_rate": metrics["success_rate"],
                "completed": metrics["status_counts"].get(TransmissionStatus.COMPLETED.value, 0),
                "failed": metrics["status_counts"].get(TransmissionStatus.FAILED.value, 0),
                "pending": metrics["status_counts"].get(TransmissionStatus.PENDING.value, 0) + 
                           metrics["status_counts"].get(TransmissionStatus.IN_PROGRESS.value, 0),
                "avg_processing_time": metrics["performance"]["avg_total_processing_time_ms"],
                "error_rate": metrics["errors"]["error_rate"]
            }
        except Exception as e:
            logger.warning(f"Failed to get transmission metrics summary: {str(e)}")
            return {
                "total_transmissions": 0,
                "success_rate": 0,
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "avg_processing_time": 0,
                "error_rate": 0
            }
    
    @staticmethod
    def get_dashboard_summary(
        db: Session,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of all metrics for the dashboard.
        
        Args:
            db: Database session
            organization_id: Optional filter by organization ID
            
        Returns:
            Dictionary with dashboard summary metrics
        """
        # Get IRN metrics
        irn_metrics = MetricsService.get_irn_generation_metrics(
            db, "24h", organization_id
        )
        
        # Get validation metrics
        validation_metrics = MetricsService.get_validation_metrics(
            db, "24h", organization_id
        )
        
        # Get B2B vs B2C metrics
        b2b_vs_b2c_metrics = MetricsService.get_b2b_vs_b2c_metrics(
            db, "24h", organization_id
        )
        
        # Get Odoo integration metrics
        odoo_metrics = MetricsService.get_odoo_integration_metrics(
            db, "24h", organization_id
        )
        
        # Get system health metrics
        system_metrics = MetricsService.get_system_health_metrics(db, "24h")
        
        # Combine into summary
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "irn_summary": {
                "total_irns": irn_metrics["total_count"],
                "active_irns": irn_metrics["status_counts"]["active"],
                "unused_irns": irn_metrics["status_counts"]["unused"],
                "expired_irns": irn_metrics["status_counts"]["expired"]
            },
            "validation_summary": {
                "total_validations": validation_metrics["total_count"],
                "success_rate": validation_metrics["success_rate"],
                "common_errors": validation_metrics["common_errors"][:3] if validation_metrics["common_errors"] else []
            },
            "b2b_vs_b2c_summary": {
                "b2b_percentage": b2b_vs_b2c_metrics["b2b_percentage"],
                "b2c_percentage": b2b_vs_b2c_metrics["b2c_percentage"],
                "b2b_success_rate": b2b_vs_b2c_metrics["b2b_success_rate"],
                "b2c_success_rate": b2b_vs_b2c_metrics["b2c_success_rate"]
            },
            "odoo_summary": {
                "active_integrations": odoo_metrics["active_integrations"],
                "total_invoices": odoo_metrics["total_invoices"],
                "success_rate": odoo_metrics["success_rate"]
            },
            "system_summary": {
                "total_requests": system_metrics["total_requests"],
                "error_rate": system_metrics["error_rate"],
                "avg_response_time": system_metrics["avg_response_time"]
            },
            "transmission_summary": MetricsService.get_transmission_metrics_summary(db, "24h", organization_id)
        }
