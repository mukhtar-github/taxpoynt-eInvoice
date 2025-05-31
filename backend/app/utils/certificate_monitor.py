"""
Certificate monitoring utilities for FIRS e-Invoice system.

This module provides monitoring capabilities for:
- Certificate expiration alerts
- Certificate validation status
- Certificate usage statistics
- Scheduled certificate checks
"""

import os
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from app.utils.certificate_manager import CertificateManager
from app.utils.crypto_audit_logger import log_certificate_operation
from app.core.config import settings

logger = logging.getLogger(__name__)


class CertificateMonitor:
    """
    Monitor certificates for expiration and validation issues.
    
    This class provides utilities to:
    1. Check certificate expiration dates
    2. Monitor certificate validation status
    3. Track certificate usage
    4. Generate alerts for expiring certificates
    """
    
    def __init__(
        self,
        certificate_manager: Optional[CertificateManager] = None,
        alert_days_before_expiry: int = 30
    ):
        """
        Initialize the certificate monitor.
        
        Args:
            certificate_manager: CertificateManager instance to use
            alert_days_before_expiry: Number of days before expiry to start alerting
        """
        self.certificate_manager = certificate_manager or CertificateManager()
        self.alert_days_before_expiry = alert_days_before_expiry
        
    def check_certificates(self) -> List[Dict[str, Any]]:
        """
        Check all certificates and return their status.
        
        Returns:
            List of certificate status dictionaries
        """
        certificates = self.certificate_manager.list_certificates()
        results = []
        
        for cert_path in certificates:
            try:
                # Get certificate info
                is_valid, cert_info = self.certificate_manager.validate_certificate(cert_path)
                
                # Calculate days until expiry
                days_until_expiry = None
                if cert_info.get('valid_until'):
                    try:
                        expiry_date = datetime.datetime.fromisoformat(cert_info['valid_until'])
                        now = datetime.datetime.now()
                        days_until_expiry = (expiry_date - now).days
                    except (ValueError, TypeError):
                        days_until_expiry = None
                
                # Determine status
                status = "valid"
                if not is_valid:
                    status = "invalid"
                elif days_until_expiry is not None:
                    if days_until_expiry < 0:
                        status = "expired"
                    elif days_until_expiry < self.alert_days_before_expiry:
                        status = "expiring_soon"
                
                # Add to results
                result = {
                    "path": cert_path,
                    "filename": os.path.basename(cert_path),
                    "status": status,
                    "is_valid": is_valid,
                    "days_until_expiry": days_until_expiry,
                    "cert_info": cert_info
                }
                
                results.append(result)
                
                # Log the check operation
                log_certificate_operation(
                    operation="monitor_check",
                    certificate_path=cert_path,
                    success=True,
                    details={
                        "status": status,
                        "days_until_expiry": days_until_expiry
                    }
                )
                
            except Exception as e:
                logger.error(f"Error checking certificate {cert_path}: {e}")
                results.append({
                    "path": cert_path,
                    "filename": os.path.basename(cert_path),
                    "status": "error",
                    "is_valid": False,
                    "error": str(e)
                })
                
                # Log the check operation
                log_certificate_operation(
                    operation="monitor_check",
                    certificate_path=cert_path,
                    success=False,
                    error=str(e)
                )
        
        return results
    
    def get_expiring_certificates(self, days_threshold: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get certificates that are expiring soon.
        
        Args:
            days_threshold: Number of days threshold. Defaults to self.alert_days_before_expiry.
            
        Returns:
            List of expiring certificate status dictionaries
        """
        days = days_threshold if days_threshold is not None else self.alert_days_before_expiry
        all_certificates = self.check_certificates()
        
        # Filter for expiring certificates
        expiring = [
            cert for cert in all_certificates
            if cert.get('days_until_expiry') is not None and 
               cert.get('days_until_expiry') >= 0 and
               cert.get('days_until_expiry') <= days
        ]
        
        return expiring
    
    def get_expired_certificates(self) -> List[Dict[str, Any]]:
        """
        Get certificates that have already expired.
        
        Returns:
            List of expired certificate status dictionaries
        """
        all_certificates = self.check_certificates()
        
        # Filter for expired certificates
        expired = [
            cert for cert in all_certificates
            if cert.get('days_until_expiry') is not None and 
               cert.get('days_until_expiry') < 0
        ]
        
        return expired
    
    def get_invalid_certificates(self) -> List[Dict[str, Any]]:
        """
        Get certificates that are invalid for reasons other than expiration.
        
        Returns:
            List of invalid certificate status dictionaries
        """
        all_certificates = self.check_certificates()
        
        # Filter for invalid certificates that aren't expired
        invalid = [
            cert for cert in all_certificates
            if not cert.get('is_valid') and cert.get('status') != "expired"
        ]
        
        return invalid
    
    def generate_alerts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate alerts for certificate issues.
        
        Returns:
            Dictionary with categories of alerts
        """
        alerts = {
            "expiring_soon": self.get_expiring_certificates(),
            "expired": self.get_expired_certificates(),
            "invalid": self.get_invalid_certificates()
        }
        
        return alerts
    
    def calculate_usage_statistics(self) -> Dict[str, Any]:
        """
        Calculate certificate usage statistics from audit logs.
        
        This function analyzes audit logs to generate usage statistics for certificates.
        
        Returns:
            Dictionary with usage statistics
        """
        # This would typically analyze the audit logs created by crypto_audit_logger
        # For now, return a placeholder
        return {
            "total_certificates": len(self.certificate_manager.list_certificates()),
            "certificates_by_status": {
                "valid": len([c for c in self.check_certificates() if c.get('status') == 'valid']),
                "expiring_soon": len([c for c in self.check_certificates() if c.get('status') == 'expiring_soon']),
                "expired": len([c for c in self.check_certificates() if c.get('status') == 'expired']),
                "invalid": len([c for c in self.check_certificates() if c.get('status') == 'invalid']),
                "error": len([c for c in self.check_certificates() if c.get('status') == 'error'])
            }
        }


def run_certificate_check():
    """
    Run a certificate check and log the results.
    
    This function is designed to be called by a scheduler.
    """
    logger.info("Running scheduled certificate check")
    monitor = CertificateMonitor()
    alerts = monitor.generate_alerts()
    
    # Log alerts
    if alerts["expiring_soon"]:
        logger.warning(f"Found {len(alerts['expiring_soon'])} certificates expiring soon")
        for cert in alerts["expiring_soon"]:
            logger.warning(
                f"Certificate {cert['filename']} expires in {cert['days_until_expiry']} days"
            )
    
    if alerts["expired"]:
        logger.error(f"Found {len(alerts['expired'])} expired certificates")
        for cert in alerts["expired"]:
            logger.error(
                f"Certificate {cert['filename']} expired {abs(cert['days_until_expiry'])} days ago"
            )
    
    if alerts["invalid"]:
        logger.error(f"Found {len(alerts['invalid'])} invalid certificates")
        for cert in alerts["invalid"]:
            logger.error(
                f"Certificate {cert['filename']} is invalid: {cert.get('error', 'Unknown reason')}"
            )
    
    # If no issues, log success
    if not any(alerts.values()):
        logger.info("All certificates are valid and not expiring soon")
    
    return alerts
