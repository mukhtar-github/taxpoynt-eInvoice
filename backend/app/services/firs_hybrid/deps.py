"""
FIRS Hybrid Dependency Providers

This module provides dependency injection for services that span across
SI and APP roles, as well as foundation services used by both.

Dependencies managed:
- Database sessions
- Certificate services (used by both SI and APP)
- Document signing services (used by both SI and APP)
- Key management services (foundation for both roles)
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.firs_si.digital_certificate_service import CertificateService
from app.services.document_signing_service import DocumentSigningService
from app.services.key_service import KeyManagementService, get_key_service


def get_certificate_service(
    db: Session = Depends(get_db),
    key_service: KeyManagementService = Depends(get_key_service)
) -> CertificateService:
    """
    Get a configured instance of the certificate service.
    
    Used by both SI (for certificate management) and APP (for secure transmission).
    """
    return CertificateService(db, key_service)


def get_document_signing_service(
    db: Session = Depends(get_db),
    certificate_service: CertificateService = Depends(get_certificate_service)
) -> DocumentSigningService:
    """
    Get a configured instance of the document signing service.
    
    Used by both SI (for invoice signing) and APP (for transmission integrity).
    """
    return DocumentSigningService(db, certificate_service)