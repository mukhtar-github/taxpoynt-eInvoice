"""
Integration status service for TaxPoynt eInvoice - System Integrator Functions.

This module provides System Integrator (SI) role functionality for monitoring
and checking the status of various integrations, including ERP/CRM connections
and backend system health monitoring.

SI Role Responsibilities:
- Monitor ERP/CRM integration health and connectivity
- Track integration performance metrics and statistics
- Provide diagnostic information for troubleshooting integrations
- Validate integration configurations and credentials
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, desc, and_, text
from sqlalchemy.orm import Session

from app.models.submission import SubmissionRecord, SubmissionStatus
from app.models.integration import Integration, IntegrationType
from app.services.firs_si.odoo_connector import OdooConnector
from app.services.firs_core.firs_api_client import FIRSService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IntegrationStatusService:
    """
    System Integrator service for monitoring integration status and health.
    
    This service provides SI role functions to check the health and status of
    various system integrations, including ERP systems like Odoo and other
    business system connectors.
    """
    
    @staticmethod
    def get_odoo_status(db: Session, integration_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check the status of Odoo integration - SI Role Function.
        
        Monitors Odoo ERP integration health, connection status, and performance
        metrics as part of System Integrator responsibilities.
        
        Args:
            db: Database session
            integration_id: Optional specific integration ID to check
            
        Returns:
            Dictionary with Odoo connection status and health metrics
        """
        # Query active Odoo integrations
        query = db.query(Integration).filter(
            Integration.integration_type == IntegrationType.ODOO,
            Integration.is_active == True
        )
        
        if integration_id:
            query = query.filter(Integration.id == integration_id)
            
        integrations = query.all()
        
        if not integrations:
            return {
                "status": "not_configured",
                "message": "No active Odoo integrations found",
                "last_checked": datetime.utcnow().isoformat(),
                "integrations": []
            }
        
        # Check status of each integration
        integration_statuses = []
        overall_status = "operational"
        
        for integration in integrations:
            try:
                # Try to connect to Odoo
                try:
                    from app.schemas.integration import OdooConfig
                    
                    # Create OdooConfig object from integration configuration
                    odoo_config = OdooConfig(
                        url=integration.config.get("url"),
                        database=integration.config.get("database"),
                        username=integration.config.get("username"),
                        password=integration.config.get("password")
                    )
                    
                    # Initialize the OdooConnector with the config
                    connector = OdooConnector(config=odoo_config)
                    
                    # Test connection by connecting and authenticating
                    connector.connect()
                    connector.authenticate()
                    
                    # Get version info
                    version_info = connector.version_info or {"server_version": "Unknown"}
                    connection_status = "connected"
                    connection_message = f"Connected to Odoo server v{version_info.get('server_version', 'Unknown')}"
                except Exception as e:
                    logger.error(f"Error connecting to Odoo: {str(e)}")
                    version_info = {"error": str(e)}
                    connection_status = "error"
                    connection_message = f"Failed to connect: {str(e)}"
                    overall_status = "degraded"
                
                # Get recent submission statistics
                now = datetime.utcnow()
                one_day_ago = now - timedelta(days=1)
                
                submissions = db.query(SubmissionRecord).filter(
                    SubmissionRecord.integration_id == str(integration.id),
                    SubmissionRecord.created_at >= one_day_ago
                ).all()
                
                total_submissions = len(submissions)
                successful = sum(1 for s in submissions if s.status in ['accepted', 'signed'])
                failed = sum(1 for s in submissions if s.status in ['failed', 'rejected', 'error'])
                
                success_rate = (successful / total_submissions * 100) if total_submissions > 0 else 0
                
                integration_statuses.append({
                    "id": str(integration.id),
                    "name": integration.name,
                    "status": "operational",
                    "version": version_info.get("server_version", "Unknown"),
                    "last_submission": max([s.created_at for s in submissions], default=None),
                    "submission_stats": {
                        "total_24h": total_submissions,
                        "success_24h": successful,
                        "failed_24h": failed,
                        "success_rate": success_rate
                    }
                })
            except Exception as e:
                logger.error(f"Error checking Odoo integration {integration.id}: {str(e)}")
                integration_statuses.append({
                    "id": str(integration.id),
                    "name": integration.name,
                    "status": "error",
                    "error": str(e),
                    "last_successful_connection": integration.last_successful_connection
                })
                overall_status = "degraded"
        
        return {
            "status": overall_status,
            "message": f"Found {len(integrations)} active Odoo integrations",
            "last_checked": datetime.utcnow().isoformat(),
            "integrations": integration_statuses
        }
    
    @staticmethod
    async def get_firs_api_status(db: Session) -> Dict[str, Any]:
        """
        Check the status of FIRS API - SI Role Function.
        
        Monitors FIRS API connectivity and health from System Integrator perspective,
        focusing on backend integration capabilities.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with FIRS API status and integration metrics
        """
        try:
            # Initialize FIRS service and check status
            firs_service = FIRSService()
            api_status = await firs_service.check_api_status()
            
            # Get recent submission statistics
            now = datetime.utcnow()
            one_day_ago = now - timedelta(days=1)
            
            submissions = db.query(SubmissionRecord).filter(
                SubmissionRecord.created_at >= one_day_ago
            ).all()
            
            total_submissions = len(submissions)
            successful = sum(1 for s in submissions if s.status in ['accepted', 'signed'])
            failed = sum(1 for s in submissions if s.status in ['failed', 'rejected', 'error'])
            
            success_rate = (successful / total_submissions * 100) if total_submissions > 0 else 0
            
            # Check if there are recent submissions with errors
            recent_errors = db.query(SubmissionRecord).filter(
                SubmissionRecord.status.in_(['failed', 'rejected', 'error']),
                SubmissionRecord.created_at >= one_day_ago
            ).order_by(desc(SubmissionRecord.created_at)).limit(5).all()
            
            recent_error_details = []
            for error in recent_errors:
                recent_error_details.append({
                    "id": str(error.id),
                    "timestamp": error.created_at.isoformat(),
                    "status": error.status,
                    "error_message": error.error_message if hasattr(error, 'error_message') else "Unknown error"
                })
            
            return {
                "status": api_status.get("status", "unknown"),
                "sandbox_available": api_status.get("sandbox_available", False),
                "production_available": api_status.get("production_available", False),
                "last_checked": datetime.utcnow().isoformat(),
                "submission_stats": {
                    "total_24h": total_submissions,
                    "success_24h": successful,
                    "failed_24h": failed,
                    "success_rate": success_rate
                },
                "recent_errors": recent_error_details
            }
        except Exception as e:
            logger.error(f"Error checking FIRS API status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    async def get_all_integration_status(db: Session) -> Dict[str, Any]:
        """
        Get comprehensive status of all integrations - SI Role Function.
        
        Provides complete integration health overview for System Integrator
        monitoring, including ERP systems and API connectivity.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with status of all integrations and overall system health
        """
        odoo_status = IntegrationStatusService.get_odoo_status(db)
        firs_status = await IntegrationStatusService.get_firs_api_status(db)
        
        # Calculate overall system status
        system_status = "operational"
        if odoo_status["status"] != "operational" or firs_status["status"] != "operational":
            system_status = "degraded"
        if odoo_status["status"] == "error" and firs_status["status"] == "error":
            system_status = "critical"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": system_status,
            "odoo_integration": odoo_status,
            "firs_api": firs_status
        }
    
    @staticmethod
    def get_integration_performance_metrics(db: Session, integration_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get detailed performance metrics for a specific integration - SI Role Function.
        
        Provides comprehensive performance analysis for System Integrator monitoring
        and optimization of ERP/CRM integrations.
        
        Args:
            db: Database session
            integration_id: ID of the integration to analyze
            days: Number of days to analyze (default: 7)
            
        Returns:
            Dictionary with detailed performance metrics
        """
        # Get time range
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        # Query submissions for the integration
        submissions = db.query(SubmissionRecord).filter(
            SubmissionRecord.integration_id == integration_id,
            SubmissionRecord.created_at >= start_date
        ).all()
        
        if not submissions:
            return {
                "integration_id": integration_id,
                "period_days": days,
                "no_data": True,
                "message": "No submissions found for the specified period"
            }
        
        # Calculate metrics
        total_submissions = len(submissions)
        successful = sum(1 for s in submissions if s.status in ['accepted', 'signed'])
        failed = sum(1 for s in submissions if s.status in ['failed', 'rejected', 'error'])
        pending = sum(1 for s in submissions if s.status in ['pending', 'processing'])
        
        success_rate = (successful / total_submissions * 100) if total_submissions > 0 else 0
        failure_rate = (failed / total_submissions * 100) if total_submissions > 0 else 0
        
        # Daily breakdown
        daily_stats = {}
        for submission in submissions:
            day_key = submission.created_at.strftime("%Y-%m-%d")
            if day_key not in daily_stats:
                daily_stats[day_key] = {"total": 0, "successful": 0, "failed": 0}
            
            daily_stats[day_key]["total"] += 1
            if submission.status in ['accepted', 'signed']:
                daily_stats[day_key]["successful"] += 1
            elif submission.status in ['failed', 'rejected', 'error']:
                daily_stats[day_key]["failed"] += 1
        
        # Average processing time (if available)
        processing_times = []
        for submission in submissions:
            if hasattr(submission, 'processing_time') and submission.processing_time:
                processing_times.append(submission.processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None
        
        return {
            "integration_id": integration_id,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
            "summary": {
                "total_submissions": total_submissions,
                "successful": successful,
                "failed": failed,
                "pending": pending,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2)
            },
            "daily_breakdown": daily_stats,
            "performance": {
                "avg_processing_time_seconds": avg_processing_time,
                "submissions_per_day": round(total_submissions / days, 2)
            }
        }