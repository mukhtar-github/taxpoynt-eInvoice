"""
Integration Status Monitoring Service for Odoo and other integrations.

This module provides functions to monitor the status of integrations,
with enhanced capabilities for Odoo 18+ integrations.
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.integration import Integration, IntegrationType
from app.schemas.integration import IntegrationTestResult
from app.services.odoo_service import test_odoo_connection

logger = logging.getLogger(__name__)

# Global dictionary to track integration monitoring threads
_monitoring_threads = {}
# Cache for status info to reduce database load
_status_cache = {}


class MonitoringStatus(BaseModel):
    """Status information for integration monitoring."""
    integration_id: str
    name: str
    status: str
    last_checked: Optional[datetime] = None
    next_check: Optional[datetime] = None
    uptime_percentage: Optional[float] = None
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    is_being_monitored: bool = False


def get_integration_monitoring_status(db: Session, integration_id: UUID) -> MonitoringStatus:
    """
    Get the current monitoring status of an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration
        
    Returns:
        Monitoring status object
    """
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        raise ValueError(f"Integration not found: {integration_id}")
    
    # Check if we have a cached status
    status_key = str(integration_id)
    if status_key in _status_cache:
        return _status_cache[status_key]
    
    # Create a new status object if not in cache
    status = MonitoringStatus(
        integration_id=str(integration_id),
        name=integration.name,
        status=integration.status or "unknown",
        last_checked=integration.last_tested,
        is_being_monitored=status_key in _monitoring_threads,
        consecutive_failures=0
    )
    
    # Calculate next check time if monitoring is active
    if status.is_being_monitored:
        thread_info = _monitoring_threads.get(status_key)
        if thread_info and thread_info.get("interval_minutes"):
            if status.last_checked:
                status.next_check = status.last_checked + timedelta(
                    minutes=thread_info["interval_minutes"]
                )
    
    # Cache the status
    _status_cache[status_key] = status
    return status


def get_all_monitored_integrations(db: Session) -> List[MonitoringStatus]:
    """
    Get a list of all integrations with their monitoring status.
    
    Args:
        db: Database session
        
    Returns:
        List of integration monitoring status objects
    """
    integrations = db.query(Integration).all()
    result = []
    
    for integration in integrations:
        try:
            status = get_integration_monitoring_status(db, integration.id)
            result.append(status)
        except Exception as e:
            logger.error(f"Error getting status for integration {integration.id}: {str(e)}")
    
    return result


def _monitor_integration(db_session_factory, integration_id: UUID, interval_minutes: int):
    """
    Background thread function to periodically check integration status.
    
    Args:
        db_session_factory: Function to create a new database session
        integration_id: ID of the integration to monitor
        interval_minutes: Interval between checks in minutes
    """
    status_key = str(integration_id)
    consecutive_failures = 0
    
    logger.info(f"Starting monitoring for integration {integration_id} every {interval_minutes} minutes")
    
    while status_key in _monitoring_threads and _monitoring_threads[status_key]["active"]:
        try:
            # Create a new database session for this check
            db = db_session_factory()
            
            # Get the integration
            integration = db.query(Integration).filter(Integration.id == integration_id).first()
            if not integration:
                logger.error(f"Integration not found: {integration_id}, stopping monitoring")
                break
            
            # Test the integration
            logger.debug(f"Testing integration {integration.name} ({integration_id})")
            
            # Initialize result
            result = None
            
            # Test based on integration type
            if integration.integration_type == IntegrationType.ODOO:
                from app.schemas.integration import OdooConfig
                from app.services.integration_service import decrypt_integration_config
                
                # Decrypt config for testing
                decrypted_integration = decrypt_integration_config(integration)
                config = OdooConfig(**decrypted_integration.config)
                result = test_odoo_connection(config)
            else:
                # For other integration types
                from app.services.integration_service import test_integration_connection
                result = test_integration_connection(db, integration_id)
            
            # Update integration status
            if result and isinstance(result, dict):
                new_status = "active" if result.get("success", False) else "error"
                integration.status = new_status
                integration.last_tested = func.now()
                
                if not result.get("success", False):
                    consecutive_failures += 1
                    integration.status_message = result.get("message", "Unknown error")
                else:
                    consecutive_failures = 0
                    integration.status_message = "Connection successful"
                
                # Update cache
                if status_key in _status_cache:
                    _status_cache[status_key].status = new_status
                    _status_cache[status_key].last_checked = datetime.now()
                    _status_cache[status_key].next_check = datetime.now() + timedelta(minutes=interval_minutes)
                    _status_cache[status_key].consecutive_failures = consecutive_failures
                    if not result.get("success", False):
                        _status_cache[status_key].last_error = result.get("message", "Unknown error")
            
                # Commit changes
                db.commit()
                
                # Log the result
                log_level = logging.INFO if result.get("success", False) else logging.ERROR
                logger.log(log_level, f"Integration check result for {integration.name}: {result.get('message', 'No message')}")
            
            # Close the database session
            db.close()
            
        except Exception as e:
            logger.exception(f"Error monitoring integration {integration_id}: {str(e)}")
            consecutive_failures += 1
            
            # Update cache if available
            if status_key in _status_cache:
                _status_cache[status_key].consecutive_failures = consecutive_failures
                _status_cache[status_key].last_error = str(e)
                _status_cache[status_key].status = "error"
            
            try:
                # Try to update the database
                db = db_session_factory()
                integration = db.query(Integration).filter(Integration.id == integration_id).first()
                if integration:
                    integration.status = "error"
                    integration.last_tested = func.now()
                    integration.status_message = str(e)
                    db.commit()
                db.close()
            except Exception:
                logger.exception(f"Error updating integration status in database for {integration_id}")
        
        # Sleep until next check
        time.sleep(interval_minutes * 60)


def start_integration_monitoring(
    db: Session,
    integration_id: UUID,
    interval_minutes: int = 30
) -> bool:
    """
    Start background monitoring for an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration to monitor
        interval_minutes: Interval between checks in minutes
        
    Returns:
        True if monitoring started, False otherwise
    """
    # Check if integration exists
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        logger.error(f"Integration not found: {integration_id}")
        return False
    
    # Check if already being monitored
    status_key = str(integration_id)
    if status_key in _monitoring_threads and _monitoring_threads[status_key]["active"]:
        logger.info(f"Integration {integration.name} ({integration_id}) is already being monitored")
        return True
    
    # Start a new monitoring thread
    from app.db.session import SessionLocal
    
    # Create a new thread
    thread = threading.Thread(
        target=_monitor_integration,
        args=(SessionLocal, integration_id, interval_minutes),
        daemon=True
    )
    
    # Store thread info
    _monitoring_threads[status_key] = {
        "thread": thread,
        "active": True,
        "interval_minutes": interval_minutes,
        "started_at": datetime.now()
    }
    
    # Start the thread
    thread.start()
    
    logger.info(f"Started monitoring for integration {integration.name} ({integration_id}) every {interval_minutes} minutes")
    
    # Update integration status in database
    integration.status = "pending"
    integration.status_message = "Monitoring started"
    db.commit()
    
    return True


def stop_integration_monitoring(db: Session, integration_id: UUID) -> bool:
    """
    Stop background monitoring for an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration to stop monitoring
        
    Returns:
        True if monitoring stopped, False otherwise
    """
    # Check if integration exists
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        logger.error(f"Integration not found: {integration_id}")
        return False
    
    # Check if being monitored
    status_key = str(integration_id)
    if status_key not in _monitoring_threads or not _monitoring_threads[status_key]["active"]:
        logger.info(f"Integration {integration.name} ({integration_id}) is not being monitored")
        return False
    
    # Stop the monitoring thread
    _monitoring_threads[status_key]["active"] = False
    
    # Update integration status in database
    integration.status = "unknown"
    integration.status_message = "Monitoring stopped"
    db.commit()
    
    logger.info(f"Stopped monitoring for integration {integration.name} ({integration_id})")
    
    return True


def run_integration_health_check(db: Session, integration_id: UUID) -> IntegrationTestResult:
    """
    Run a manual health check for an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration to check
        
    Returns:
        Test result object
    """
    # Check if integration exists
    integration = db.query(Integration).filter(Integration.id == integration_id).first()
    if not integration:
        return IntegrationTestResult(
            success=False,
            message=f"Integration not found: {integration_id}",
            details={"error": "Integration not found"}
        )
    
    try:
        # Run the test based on integration type
        if integration.integration_type == IntegrationType.ODOO:
            from app.schemas.integration import OdooConfig
            from app.services.integration_service import decrypt_integration_config
            
            # Decrypt config for testing
            decrypted_integration = decrypt_integration_config(integration)
            config = OdooConfig(**decrypted_integration.config)
            result = test_odoo_connection(config)
            
            # Cast to IntegrationTestResult
            test_result = IntegrationTestResult(
                success=result.get("success", False),
                message=result.get("message", "Unknown error"),
                details=result.get("details", {})
            )
        else:
            # For other integration types
            from app.services.integration_service import test_integration_connection
            test_result = test_integration_connection(db, integration_id)
        
        # Update integration status
        integration.status = "active" if test_result.success else "error"
        integration.last_tested = func.now()
        integration.status_message = test_result.message
        db.commit()
        
        # Update cache if it exists
        status_key = str(integration_id)
        if status_key in _status_cache:
            _status_cache[status_key].status = integration.status
            _status_cache[status_key].last_checked = datetime.now()
            if not test_result.success:
                _status_cache[status_key].last_error = test_result.message
        
        return test_result
    
    except Exception as e:
        logger.exception(f"Error running health check for integration {integration_id}: {str(e)}")
        
        # Update integration status
        integration.status = "error"
        integration.last_tested = func.now()
        integration.status_message = str(e)
        db.commit()
        
        # Update cache if it exists
        status_key = str(integration_id)
        if status_key in _status_cache:
            _status_cache[status_key].status = "error"
            _status_cache[status_key].last_checked = datetime.now()
            _status_cache[status_key].last_error = str(e)
        
        return IntegrationTestResult(
            success=False,
            message=f"Error running health check: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__}
        )
