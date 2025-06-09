"""
Certificate Management Routes for TaxPoynt eInvoice system.

This module provides endpoints for:
- Creating, updating, and managing digital certificates
- Verifying certificate validity
- Using certificates for document signing
- Certificate revocation management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.db.session import get_db
from app.models.certificate import Certificate, CertificateType, CertificateStatus
from app.schemas.certificate import (
    CertificateCreate, CertificateUpdate, Certificate as CertificateSchema,
    CertificateWithData, CertificateVerification, CertificateRevoke,
    CertificateExport, CertificateImport
)
from app.services.certificate_service import CertificateService
from app.services.key_service import KeyManagementService, get_key_service
from app.dependencies.auth import get_current_user
from app.utils.certificate_signing import (
    sign_invoice, verify_invoice_signature, extract_certificate_info
)

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.post("", response_model=CertificateSchema)
async def create_certificate(
    certificate_in: CertificateCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Create a new certificate with encrypted data.
    
    Certificate data and private key (if provided) will be stored securely using field-level encryption.
    """
    certificate_service = CertificateService(db, key_service)
    
    try:
        certificate = certificate_service.create_certificate(certificate_in, current_user.id)
        return certificate
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[CertificateSchema])
async def list_certificates(
    organization_id: Optional[UUID] = None,
    certificate_type: Optional[CertificateType] = None,
    status: Optional[CertificateStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    List certificates with optional filtering.
    
    Results can be filtered by organization, certificate type, and status.
    """
    certificate_service = CertificateService(db, key_service)
    certificates = certificate_service.get_certificates(
        organization_id=organization_id,
        skip=skip,
        limit=limit
    )
    
    # Apply additional filters if provided
    if certificate_type or status:
        filtered_certs = []
        for cert in certificates:
            if certificate_type and cert.certificate_type != certificate_type:
                continue
            if status and cert.status != status:
                continue
            filtered_certs.append(cert)
        return filtered_certs
    
    return certificates


@router.get("/{certificate_id}", response_model=CertificateSchema)
async def get_certificate(
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Get a certificate by ID (metadata only, without certificate data).
    """
    certificate_service = CertificateService(db, key_service)
    certificate = certificate_service.get_certificate(certificate_id)
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return certificate


@router.get("/{certificate_id}/data", response_model=CertificateWithData)
async def get_certificate_with_data(
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Get a certificate by ID with decrypted certificate data.
    """
    certificate_service = CertificateService(db, key_service)
    certificate_data = certificate_service.get_certificate_with_decrypted_data(certificate_id)
    
    if not certificate_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return certificate_data


@router.put("/{certificate_id}", response_model=CertificateSchema)
async def update_certificate(
    certificate_id: UUID,
    certificate_in: CertificateUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Update a certificate's metadata.
    
    Note: This endpoint only updates metadata, not the certificate data itself.
    """
    certificate_service = CertificateService(db, key_service)
    certificate = certificate_service.update_certificate(
        certificate_id, 
        certificate_in, 
        current_user.id
    )
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return certificate


@router.post("/{certificate_id}/revoke")
async def revoke_certificate(
    certificate_id: UUID,
    revoke_data: CertificateRevoke,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Revoke a certificate.
    
    A revoked certificate can no longer be used for signing.
    """
    certificate_service = CertificateService(db, key_service)
    success = certificate_service.revoke_certificate(
        certificate_id, 
        revoke_data.reason, 
        current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return {"message": "Certificate successfully revoked"}


@router.delete("/{certificate_id}")
async def delete_certificate(
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Delete a certificate.
    
    This permanently removes the certificate and its associated data.
    """
    certificate_service = CertificateService(db, key_service)
    success = certificate_service.delete_certificate(certificate_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return {"message": "Certificate successfully deleted"}


@router.post("/{certificate_id}/verify", response_model=CertificateVerification)
async def verify_certificate(
    certificate_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Verify a certificate's validity.
    
    Checks expiration, revocation status, and other validity constraints.
    """
    certificate_service = CertificateService(db, key_service)
    verification = certificate_service.verify_certificate(certificate_id)
    
    return verification


@router.post("/{certificate_id}/sign-document")
async def sign_document(
    certificate_id: UUID,
    document: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Sign a document using a certificate.
    
    Returns the document with a digital signature block added.
    """
    certificate_service = CertificateService(db, key_service)
    
    # Get certificate with decrypted data
    cert_data = certificate_service.get_certificate_with_decrypted_data(certificate_id)
    if not cert_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    # Check if certificate has a private key
    if not cert_data.get("private_key_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate does not have an associated private key"
        )
    
    # Verify certificate is valid
    verification = certificate_service.verify_certificate(certificate_id)
    if not verification.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate is not valid: {', '.join(verification.errors)}"
        )
    
    # Sign document
    try:
        signed_document = sign_invoice(
            document,
            certificate_id,
            cert_data["certificate_data"],
            cert_data["private_key_data"]
        )
        
        # Update last used timestamp
        certificate = certificate_service.get_certificate(certificate_id)
        certificate.last_used_at = datetime.utcnow()
        db.commit()
        
        return signed_document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error signing document: {str(e)}"
        )


@router.post("/verify-signature")
async def verify_document_signature(
    document: Dict[str, Any] = Body(...),
    certificate_id: UUID = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Verify a document signature.
    
    Checks if the signature is valid for the given document and certificate.
    """
    certificate_service = CertificateService(db, key_service)
    
    # Get certificate with decrypted data
    cert_data = certificate_service.get_certificate_with_decrypted_data(certificate_id)
    if not cert_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    # Verify signature
    try:
        valid = verify_invoice_signature(document, cert_data["certificate_data"])
        return {"valid": valid}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying signature: {str(e)}"
        )


@router.post("/extract-certificate-info")
async def extract_certificate_info_endpoint(
    certificate_data: str = Body(..., embed=True),
    current_user: Any = Depends(get_current_user)
):
    """
    Extract information from a PEM-encoded certificate.
    
    This can be used to preview certificate details before storing.
    """
    try:
        info = extract_certificate_info(certificate_data)
        return info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error extracting certificate info: {str(e)}"
        )
