"""
Lifecycle Manager

Manages certificate lifecycle operations including renewal, revocation, and monitoring.
Handles automated certificate management tasks and compliance tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .certificate_store import CertificateStore, CertificateStatus, StoredCertificate
from .certificate_generator import CertificateGenerator
from .key_manager import KeyManager


class LifecycleAction(Enum):
    """Lifecycle action types"""
    RENEWAL = "renewal"
    REVOCATION = "revocation"
    EXPIRATION_WARNING = "expiration_warning"
    COMPLIANCE_CHECK = "compliance_check"
    AUTOMATIC_RENEWAL = "automatic_renewal"


@dataclass
class LifecycleEvent:
    """Certificate lifecycle event"""
    event_id: str
    certificate_id: str
    action: LifecycleAction
    timestamp: str
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class LifecycleManager:
    """Manage certificate lifecycle operations"""
    
    def __init__(
        self,
        certificate_store: Optional[CertificateStore] = None,
        certificate_generator: Optional[CertificateGenerator] = None,
        key_manager: Optional[KeyManager] = None
    ):
        self.certificate_store = certificate_store or CertificateStore()
        self.certificate_generator = certificate_generator or CertificateGenerator()
        self.key_manager = key_manager or KeyManager()
        
        self.lifecycle_events: List[LifecycleEvent] = []
        self.logger = logging.getLogger(__name__)
        
        # Default renewal settings
        self.default_renewal_days = 30  # Renew 30 days before expiration
        self.warning_days = [60, 30, 7]  # Warning intervals
    
    def check_certificate_expiration(
        self,
        organization_id: Optional[str] = None
    ) -> Dict[str, List[StoredCertificate]]:
        """
        Check certificates for expiration and generate warnings
        
        Args:
            organization_id: Filter by organization (None for all)
            
        Returns:
            Dictionary with expiration categories
        """
        try:
            # Get certificates for organization or all
            certificates = self.certificate_store.list_certificates(
                organization_id=organization_id,
                status=CertificateStatus.ACTIVE
            )
            
            now = datetime.now()
            expiration_categories = {
                'expired': [],
                'expiring_soon': [],
                'needs_renewal': [],
                'warning_60_days': [],
                'warning_30_days': [],
                'warning_7_days': []
            }
            
            for cert in certificates:
                not_after = datetime.fromisoformat(cert.not_after)
                days_until_expiry = (not_after - now).days
                
                if days_until_expiry < 0:
                    # Already expired
                    expiration_categories['expired'].append(cert)
                    self._log_lifecycle_event(
                        cert.certificate_id,
                        LifecycleAction.EXPIRATION_WARNING,
                        {'days_overdue': abs(days_until_expiry)},
                        success=True
                    )
                    
                    # Update certificate status
                    self.certificate_store.update_certificate_status(
                        cert.certificate_id,
                        CertificateStatus.EXPIRED,
                        {'expired_at': now.isoformat()}
                    )
                
                elif days_until_expiry <= self.default_renewal_days:
                    # Needs renewal
                    expiration_categories['needs_renewal'].append(cert)
                    expiration_categories['expiring_soon'].append(cert)
                
                elif days_until_expiry <= 60:
                    expiration_categories['expiring_soon'].append(cert)
                    
                    # Check warning intervals
                    for warning_days in self.warning_days:
                        if days_until_expiry <= warning_days:
                            category_key = f'warning_{warning_days}_days'
                            if category_key in expiration_categories:
                                expiration_categories[category_key].append(cert)
                            
                            self._log_lifecycle_event(
                                cert.certificate_id,
                                LifecycleAction.EXPIRATION_WARNING,
                                {'days_until_expiry': days_until_expiry, 'warning_level': warning_days},
                                success=True
                            )
            
            self.logger.info(f"Expiration check completed. Found {len(expiration_categories['expired'])} expired, "
                           f"{len(expiration_categories['needs_renewal'])} needing renewal")
            
            return expiration_categories
            
        except Exception as e:
            self.logger.error(f"Error checking certificate expiration: {str(e)}")
            raise
    
    def renew_certificate(
        self,
        certificate_id: str,
        validity_days: Optional[int] = None,
        reuse_key: bool = True
    ) -> Tuple[str, bool]:
        """
        Renew certificate with new validity period
        
        Args:
            certificate_id: Certificate to renew
            validity_days: New validity period (default: 365 days)
            reuse_key: Whether to reuse existing key pair
            
        Returns:
            Tuple of (new_certificate_id, success)
        """
        try:
            # Get existing certificate info
            cert_info = self.certificate_store.get_certificate_info(certificate_id)
            if not cert_info:
                raise ValueError(f"Certificate not found: {certificate_id}")
            
            # Retrieve existing certificate
            cert_pem = self.certificate_store.retrieve_certificate(certificate_id)
            if not cert_pem:
                raise ValueError("Could not retrieve certificate data")
            
            # Extract subject info from existing certificate
            cert_details = self.certificate_generator.extract_certificate_info(cert_pem)
            subject_info = cert_details['subject']
            
            # Generate new certificate
            validity_days = validity_days or 365
            
            if reuse_key:
                # TODO: Implement key reuse logic
                # For now, generate new key pair
                pass
            
            new_cert_pem, new_key_pem = self.certificate_generator.generate_self_signed_certificate(
                subject_info=subject_info,
                validity_days=validity_days
            )
            
            # Store new certificate
            new_cert_id = self.certificate_store.store_certificate(
                certificate_pem=new_cert_pem,
                organization_id=cert_info.organization_id,
                certificate_type=cert_info.certificate_type,
                metadata={
                    **cert_info.metadata,
                    'renewed_from': certificate_id,
                    'renewal_date': datetime.now().isoformat()
                }
            )
            
            # Store new key
            key_name = f"renewed_{cert_info.subject_cn}_{datetime.now().strftime('%Y%m%d')}"
            self.key_manager.store_key(new_key_pem, key_name, "private")
            
            # Mark old certificate as archived
            self.certificate_store.update_certificate_status(
                certificate_id,
                CertificateStatus.ARCHIVED,
                {
                    'renewed_to': new_cert_id,
                    'renewal_date': datetime.now().isoformat()
                }
            )
            
            # Log renewal event
            self._log_lifecycle_event(
                certificate_id,
                LifecycleAction.RENEWAL,
                {
                    'new_certificate_id': new_cert_id,
                    'validity_days': validity_days,
                    'reused_key': reuse_key
                },
                success=True
            )
            
            self.logger.info(f"Successfully renewed certificate: {certificate_id} -> {new_cert_id}")
            
            return new_cert_id, True
            
        except Exception as e:
            self.logger.error(f"Error renewing certificate {certificate_id}: {str(e)}")
            
            # Log failed renewal
            self._log_lifecycle_event(
                certificate_id,
                LifecycleAction.RENEWAL,
                {'error': str(e)},
                success=False,
                error_message=str(e)
            )
            
            return "", False
    
    def revoke_certificate(
        self,
        certificate_id: str,
        reason: str,
        revocation_date: Optional[datetime] = None
    ) -> bool:
        """
        Revoke certificate
        
        Args:
            certificate_id: Certificate to revoke
            reason: Reason for revocation
            revocation_date: Date of revocation (default: now)
            
        Returns:
            True if revoked successfully
        """
        try:
            revocation_date = revocation_date or datetime.now()
            
            # Update certificate status
            success = self.certificate_store.update_certificate_status(
                certificate_id,
                CertificateStatus.REVOKED,
                {
                    'revocation_reason': reason,
                    'revocation_date': revocation_date.isoformat(),
                    'revoked_by': 'system'  # Could be enhanced to track user
                }
            )
            
            if success:
                # Log revocation event
                self._log_lifecycle_event(
                    certificate_id,
                    LifecycleAction.REVOCATION,
                    {
                        'reason': reason,
                        'revocation_date': revocation_date.isoformat()
                    },
                    success=True
                )
                
                self.logger.info(f"Successfully revoked certificate: {certificate_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error revoking certificate {certificate_id}: {str(e)}")
            
            # Log failed revocation
            self._log_lifecycle_event(
                certificate_id,
                LifecycleAction.REVOCATION,
                {'error': str(e), 'reason': reason},
                success=False,
                error_message=str(e)
            )
            
            return False
    
    def perform_automatic_renewal(
        self,
        organization_id: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Perform automatic renewal for certificates that need it
        
        Args:
            organization_id: Filter by organization
            dry_run: If True, only simulate renewals
            
        Returns:
            Renewal results summary
        """
        try:
            # Check expiration status
            expiration_check = self.check_certificate_expiration(organization_id)
            certificates_to_renew = expiration_check['needs_renewal']
            
            renewal_results = {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'dry_run': dry_run,
                'results': []
            }
            
            for cert in certificates_to_renew:
                renewal_results['processed'] += 1
                
                if dry_run:
                    # Simulate renewal
                    result = {
                        'certificate_id': cert.certificate_id,
                        'subject_cn': cert.subject_cn,
                        'action': 'would_renew',
                        'success': True
                    }
                    renewal_results['successful'] += 1
                else:
                    # Perform actual renewal
                    new_cert_id, success = self.renew_certificate(cert.certificate_id)
                    
                    result = {
                        'certificate_id': cert.certificate_id,
                        'subject_cn': cert.subject_cn,
                        'action': 'renewed' if success else 'failed',
                        'new_certificate_id': new_cert_id if success else None,
                        'success': success
                    }
                    
                    if success:
                        renewal_results['successful'] += 1
                    else:
                        renewal_results['failed'] += 1
                
                renewal_results['results'].append(result)
            
            # Log automatic renewal event
            self._log_lifecycle_event(
                'system',
                LifecycleAction.AUTOMATIC_RENEWAL,
                {
                    'organization_id': organization_id,
                    'processed': renewal_results['processed'],
                    'successful': renewal_results['successful'],
                    'failed': renewal_results['failed'],
                    'dry_run': dry_run
                },
                success=True
            )
            
            self.logger.info(f"Automatic renewal completed: {renewal_results['successful']}/{renewal_results['processed']} successful")
            
            return renewal_results
            
        except Exception as e:
            self.logger.error(f"Error in automatic renewal: {str(e)}")
            raise
    
    def check_compliance_status(
        self,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check FIRS compliance status for certificates
        
        Args:
            organization_id: Filter by organization
            
        Returns:
            Compliance status report
        """
        try:
            certificates = self.certificate_store.list_certificates(
                organization_id=organization_id,
                status=CertificateStatus.ACTIVE
            )
            
            compliance_report = {
                'total_certificates': len(certificates),
                'compliant': 0,
                'non_compliant': 0,
                'issues': [],
                'recommendations': []
            }
            
            for cert in certificates:
                # Check certificate validity period
                not_after = datetime.fromisoformat(cert.not_after)
                validity_period = (not_after - datetime.fromisoformat(cert.not_before)).days
                
                is_compliant = True
                cert_issues = []
                
                # FIRS compliance checks
                if validity_period > 730:  # More than 2 years
                    is_compliant = False
                    cert_issues.append(f"Validity period too long: {validity_period} days (max 730)")
                
                if 'NG' not in cert.subject_cn and cert.organization_id:
                    # Should contain Nigeria-specific information
                    cert_issues.append("Certificate may not contain required Nigerian compliance information")
                
                # Check key strength (if available in metadata)
                key_size = cert.metadata.get('key_size')
                if key_size and key_size < 2048:
                    is_compliant = False
                    cert_issues.append(f"Key size too small: {key_size} bits (min 2048)")
                
                if is_compliant:
                    compliance_report['compliant'] += 1
                else:
                    compliance_report['non_compliant'] += 1
                    compliance_report['issues'].extend([
                        f"Certificate {cert.certificate_id} ({cert.subject_cn}): {issue}"
                        for issue in cert_issues
                    ])
            
            # Generate recommendations
            if compliance_report['non_compliant'] > 0:
                compliance_report['recommendations'].extend([
                    "Review certificate validity periods (max 2 years for FIRS compliance)",
                    "Ensure certificates contain Nigerian-specific information",
                    "Use minimum 2048-bit RSA keys",
                    "Consider renewing non-compliant certificates"
                ])
            
            # Log compliance check
            self._log_lifecycle_event(
                'system',
                LifecycleAction.COMPLIANCE_CHECK,
                {
                    'organization_id': organization_id,
                    'total_certificates': compliance_report['total_certificates'],
                    'compliant': compliance_report['compliant'],
                    'non_compliant': compliance_report['non_compliant']
                },
                success=True
            )
            
            return compliance_report
            
        except Exception as e:
            self.logger.error(f"Error checking compliance status: {str(e)}")
            raise
    
    def get_lifecycle_events(
        self,
        certificate_id: Optional[str] = None,
        action: Optional[LifecycleAction] = None,
        limit: int = 100
    ) -> List[LifecycleEvent]:
        """
        Get lifecycle events with optional filters
        
        Args:
            certificate_id: Filter by certificate
            action: Filter by action type
            limit: Maximum number of events to return
            
        Returns:
            List of lifecycle events
        """
        filtered_events = []
        
        for event in self.lifecycle_events:
            if certificate_id and event.certificate_id != certificate_id:
                continue
            
            if action and event.action != action:
                continue
            
            filtered_events.append(event)
        
        # Sort by timestamp (newest first) and apply limit
        filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_events[:limit]
    
    def _log_lifecycle_event(
        self,
        certificate_id: str,
        action: LifecycleAction,
        details: Dict[str, Any],
        success: bool,
        error_message: Optional[str] = None
    ):
        """Log lifecycle event"""
        event = LifecycleEvent(
            event_id=f"event_{len(self.lifecycle_events) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            certificate_id=certificate_id,
            action=action,
            timestamp=datetime.now().isoformat(),
            details=details,
            success=success,
            error_message=error_message
        )
        
        self.lifecycle_events.append(event)
        
        # Keep only last 1000 events in memory
        if len(self.lifecycle_events) > 1000:
            self.lifecycle_events = self.lifecycle_events[-1000:]