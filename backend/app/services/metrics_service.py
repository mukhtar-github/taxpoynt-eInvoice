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
            "unused": query.filter(IRNRecord.status == IRNStatus.UNUSED).count(),
            "active": query.filter(IRNRecord.status == IRNStatus.ACTIVE).count(),
            "used": query.filter(IRNRecord.status == IRNStatus.USED).count(),
            "expired": query.filter(IRNRecord.status == IRNStatus.EXPIRED).count(),
            "cancelled": query.filter(IRNRecord.status == IRNStatus.CANCELLED).count()
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
            }
        }
