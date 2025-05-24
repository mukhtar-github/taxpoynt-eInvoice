"""
Integration status service.

This module provides functionality for checking the status of various integrations,
including Odoo connections and FIRS API status.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, desc, and_, text
from sqlalchemy.orm import Session

from app.models.submission import SubmissionRecord, SubmissionStatus
from app.models.integration import Integration, IntegrationType
from app.services.odoo_connector import OdooConnector
from app.services.firs_service import FIRSService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IntegrationStatusService:
    """
    Service for checking status of integrations.
    
    This service provides functions to check the health and status of
    various system integrations, including Odoo and FIRS API.
    """
    
    @staticmethod
    def get_odoo_status(db: Session, integration_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check the status of Odoo integration.
        
        Args:
            db: Database session
            integration_id: Optional specific integration ID to check
            
        Returns:
            Dictionary with Odoo connection status
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
        Check the status of FIRS API.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with FIRS API status
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
        Get status of all integrations.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with status of all integrations
        """
        odoo_status = await IntegrationStatusService.get_odoo_status(db)
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
