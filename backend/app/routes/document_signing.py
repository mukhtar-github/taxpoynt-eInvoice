"""
Document Signing Routes for TaxPoynt eInvoice system.

This module provides endpoints for:
- Signing documents using certificates
- Verifying document signatures
- Calculating document hashes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from uuid import UUID

from app.db.session import get_db
from app.schemas.certificate import (
    DocumentSignRequest, DocumentSignResponse,
    SignatureVerificationRequest, SignatureVerificationResponse
)
from app.services.document_signing_service import DocumentSigningService
from app.services.deps import get_document_signing_service
from app.services.user_service import get_current_user

router = APIRouter(prefix="/signing", tags=["document-signing"])


@router.post("/sign", response_model=DocumentSignResponse)
async def sign_document(
    request: DocumentSignRequest,
    document_signing_service: DocumentSigningService = Depends(get_document_signing_service),
    current_user: Any = Depends(get_current_user),
):
    """
    Sign a document using a certificate.
    
    This endpoint signs a document using a certificate stored in the system.
    The document can be any JSON object. The signature is added to the document
    along with metadata about the certificate and signature.
    """
    try:
        return document_signing_service.sign_document(
            document=request.document,
            certificate_id=request.certificate_id,
            include_timestamp=request.include_timestamp,
            include_metadata=request.include_metadata
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error signing document: {str(e)}"
        )


@router.post("/verify", response_model=SignatureVerificationResponse)
async def verify_signature(
    request: SignatureVerificationRequest,
    document_signing_service: DocumentSigningService = Depends(get_document_signing_service),
    current_user: Any = Depends(get_current_user),
):
    """
    Verify a document signature.
    
    This endpoint verifies if a document signature is valid. It checks both
    the cryptographic validity of the signature and the certificate validity.
    """
    return document_signing_service.verify_signature(
        document=request.document,
        certificate_id=request.certificate_id,
        signature=request.signature
    )


@router.post("/hash")
async def calculate_document_hash(
    document: Dict[str, Any] = Body(...),
    document_signing_service: DocumentSigningService = Depends(get_document_signing_service),
    current_user: Any = Depends(get_current_user),
):
    """
    Calculate a hash for a document.
    
    This endpoint calculates a deterministic hash for a document.
    The document is canonicalized to ensure consistent hashing.
    """
    document_hash = document_signing_service.get_document_hash(document)
    return {"hash": document_hash}
