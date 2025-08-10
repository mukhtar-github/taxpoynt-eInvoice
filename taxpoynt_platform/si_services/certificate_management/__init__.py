"""
SI Services - Certificate Management Module

Handles digital certificate lifecycle management for System Integrator role.
Manages certificate requests, digital certificates, and certificate operations.
"""

# New granular components
from .certificate_generator import CertificateGenerator
from .key_manager import KeyManager
from .certificate_store import CertificateStore, CertificateStatus
from .lifecycle_manager import LifecycleManager
from .ca_integration import CAIntegration

# Refactored services (using granular components)
from .certificate_service import CertificateService
from .certificate_request_service import CertificateRequestService  
from .digital_certificate_service import DigitalCertificateService

# Legacy services (original monolithic versions)
from .certificate_service_legacy import CertificateService as CertificateServiceLegacy
from .certificate_request_service_legacy import CertificateRequestService as CertificateRequestServiceLegacy
from .digital_certificate_service_legacy import DigitalCertificateService as DigitalCertificateServiceLegacy

__all__ = [
    # New granular components
    "CertificateGenerator",
    "KeyManager",
    "CertificateStore",
    "CertificateStatus",
    "LifecycleManager",
    "CAIntegration",
    
    # Refactored services
    "CertificateService",
    "CertificateRequestService",
    "DigitalCertificateService",
    
    # Legacy services
    "CertificateServiceLegacy",
    "CertificateRequestServiceLegacy",
    "DigitalCertificateServiceLegacy"
]