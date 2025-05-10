"""
Dependency providers for various services.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.certificate_service import CertificateService
from app.services.document_signing_service import DocumentSigningService
from app.services.key_service import KeyManagementService, get_key_service


def get_certificate_service(
    db: Session = Depends(get_db),
    key_service: KeyManagementService = Depends(get_key_service)
) -> CertificateService:
    """
    Get a configured instance of the certificate service.
    """
    return CertificateService(db, key_service)


def get_document_signing_service(
    db: Session = Depends(get_db),
    certificate_service: CertificateService = Depends(get_certificate_service)
) -> DocumentSigningService:
    """
    Get a configured instance of the document signing service.
    """
    return DocumentSigningService(db, certificate_service)
