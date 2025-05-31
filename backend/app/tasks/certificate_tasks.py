"""
Scheduled tasks for certificate management.

This module contains scheduled tasks that automate certificate-related
operations such as:
- Certificate expiration monitoring
- Certificate status validation
- Certificate usage statistics
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.utils.certificate_monitor import CertificateMonitor, run_certificate_check
from app.utils.crypto_audit_logger import log_certificate_operation
from app.core.config import settings

logger = logging.getLogger(__name__)


async def certificate_monitor_task():
    """
    Run the certificate monitoring task.
    
    This task:
    1. Checks all certificates for expiration and validity
    2. Logs issues to both the application log and audit log
    3. Updates certificate status metrics
    """
    logger.info("Running certificate monitoring task")
    
    try:
        # Run the certificate check
        monitor = CertificateMonitor()
        alerts = monitor.generate_alerts()
        
        # Process alerts
        if any(alerts.values()):
            # Get all problematic certificates
            problem_certs = []
            for category, certs in alerts.items():
                problem_certs.extend(certs)
            
            # Log to the application log
            logger.warning(
                f"Certificate issues detected: {len(problem_certs)} certificates have issues. "
                f"{len(alerts['expiring_soon'])} expiring soon, "
                f"{len(alerts['expired'])} expired, "
                f"{len(alerts['invalid'])} invalid."
            )
            
            # Log details of each problematic certificate
            for cert in problem_certs:
                cert_path = cert.get('path', 'unknown')
                status = cert.get('status', 'unknown')
                days_until_expiry = cert.get('days_until_expiry')
                
                # Create a detailed message
                if status == 'expiring_soon':
                    detail_msg = f"Certificate expiring in {days_until_expiry} days"
                elif status == 'expired':
                    detail_msg = f"Certificate expired {abs(days_until_expiry)} days ago"
                else:
                    detail_msg = f"Certificate is invalid: {cert.get('error', 'Unknown reason')}"
                
                logger.warning(f"Certificate issue: {os.path.basename(cert_path)} - {detail_msg}")
                
                # Log to the audit log
                log_certificate_operation(
                    operation="monitor_alert",
                    certificate_path=cert_path,
                    success=False,
                    details={
                        "status": status,
                        "days_until_expiry": days_until_expiry,
                        "message": detail_msg
                    }
                )
        else:
            logger.info("Certificate monitoring: All certificates are valid and not expiring soon")
            
        # Update usage statistics
        usage_stats = monitor.calculate_usage_statistics()
        logger.info(f"Certificate usage statistics: {usage_stats}")
        
        return alerts
    
    except Exception as e:
        logger.error(f"Error in certificate monitoring task: {e}")
        # Log to the audit log
        log_certificate_operation(
            operation="monitor_task",
            certificate_path="all",
            success=False,
            error=str(e)
        )
        return {"error": str(e)}
