"""
Crypto endpoints for FIRS e-Invoice system.

This module provides API endpoints for:
- Downloading crypto keys
- Signing IRNs
- Generating QR codes
- CSID (Cryptographic Stamp ID) operations
- Cryptographic stamping for FIRS compliance
"""

import os
import datetime
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response, JSONResponse # type: ignore
from pydantic import BaseModel, Field # type: ignore
from sqlalchemy.orm import Session

from app.utils.encryption import encrypt_irn_data, extract_keys_from_file, load_public_key # type: ignore
from app.utils.irn_generator import generate_firs_irn as generate_irn, validate_irn # Using new implementation
from app.utils.qr_code import generate_qr_code, generate_qr_code_for_irn, qr_code_as_base64 # type: ignore
from app.utils.crypto_signing import sign_invoice, verify_csid, csid_generator
from app.utils.certificate_manager import CertificateManager, get_certificate_manager
from app.utils.key_management import KeyManager, get_key_manager
from app.db.session import get_db # type: ignore
from app.services.key_service import KeyManagementService, get_key_service
from app.services.encryption_service import EncryptionService, get_encryption_service
from app.services.cryptographic_stamping_service import CryptographicStampingService, get_cryptographic_stamping_service
from app.api.dependencies import get_current_active_user # type: ignore
from app.models.user import User # type: ignore # type: ignore # type: ignore
from app.schemas.key import KeyMetadata, KeyRotateResponse # type: ignore # type: ignore # type: ignore

router = APIRouter(
    prefix="/crypto",
    tags=["crypto"],
    responses={404: {"description": "Not found"}},
)


class CryptoKeysResponse(BaseModel):
    """Response model for crypto keys."""
    message: str
    public_key: str


class SignIRNRequest(BaseModel):
    """Request model for IRN signing."""
    irn: str = Field(..., description="Invoice Reference Number")
    certificate: Optional[str] = Field(None, description="FIRS certificate")


class SignIRNResponse(BaseModel):
    """Response model for IRN signing."""
    irn: str
    encrypted_data: str
    qr_code_base64: str


class GenerateIRNRequest(BaseModel):
    """Request model for IRN generation."""
    invoice_number: str = Field(..., description="Invoice number from accounting system")
    service_id: str = Field(..., description="FIRS-assigned Service ID")
    timestamp: Optional[str] = Field(None, description="Date in YYYYMMDD format")


class CSIDRequest(BaseModel):
    """Request model for generating a Cryptographic Stamp ID."""
    invoice_data: Dict[str, Any] = Field(..., description="Invoice data to stamp")


class CSIDResponse(BaseModel):
    """Response model for CSID operations."""
    cryptographic_stamp: Dict[str, Any] = Field(..., description="CSID data including timestamp and algorithm")
    is_signed: bool = Field(..., description="Whether the invoice has been successfully signed")


class VerifyCSIDRequest(BaseModel):
    """Request model for verifying a Cryptographic Stamp ID."""
    invoice_data: Dict[str, Any] = Field(..., description="Invoice data to verify")
    csid: str = Field(..., description="CSID to verify")


class VerifyCSIDResponse(BaseModel):
    """Response model for CSID verification."""
    is_valid: bool = Field(..., description="Whether the CSID is valid")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional verification details")


class CryptoStampRequest(BaseModel):
    """Request model for cryptographic stamping."""
    invoice_data: Dict[str, Any] = Field(..., description="Invoice data to stamp")


class CryptoStampResponse(BaseModel):
    """Response model for cryptographic stamping."""
    stamped_invoice: Dict[str, Any] = Field(..., description="Invoice data with cryptographic stamp")
    stamp_info: Dict[str, Any] = Field(..., description="Information about the stamp applied")


class VerifyStampRequest(BaseModel):
    """Request model for verifying a cryptographic stamp."""
    invoice_data: Dict[str, Any] = Field(..., description="Original invoice data")
    stamp_data: Dict[str, Any] = Field(..., description="Stamp data to verify")


@router.get("/keys", response_model=List[KeyMetadata])
async def list_keys(
    current_user: User = Depends(get_current_active_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    List all encryption keys (metadata only, no actual key material).
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view encryption keys"
        )
    
    return key_service.list_keys()


@router.post("/keys/rotate", response_model=KeyRotateResponse)
async def rotate_key(
    current_user: User = Depends(get_current_active_user),
    key_service: KeyManagementService = Depends(get_key_service)
):
    """
    Rotate the encryption key, generating a new active key.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to rotate encryption keys"
        )
    
    new_key_id = key_service.rotate_key()
    return {"key_id": new_key_id, "message": "Key rotation successful"}


@router.post("/upload-keys")
async def upload_crypto_keys(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    certificate_manager: CertificateManager = Depends(get_certificate_manager)
):
    """
    Upload FIRS crypto keys file.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload crypto keys"
        )
    
    try:
        # Save uploaded file to temporary location
        file_location = f"/tmp/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        
        # Extract keys from file
        public_key_bytes, certificate_bytes = extract_keys_from_file(file_location)
        
        # Store the certificate
        cert_name = f"firs_cert_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.crt"
        cert_path = certificate_manager.store_certificate(certificate_bytes, name=cert_name)
        
        # Validate the certificate
        is_valid, cert_info = certificate_manager.validate_certificate(cert_path)
        
        return {
            "filename": file.filename, 
            "message": "FIRS crypto keys uploaded successfully",
            "certificate_info": {
                "path": cert_path,
                "is_valid": is_valid,
                **cert_info
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process crypto keys: {str(e)}"
        )


@router.post("/integration-config/encrypt")
async def encrypt_integration_config(
    config: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Encrypt sensitive fields in an integration configuration.
    """
    try:
        encrypted_config = encryption_service.encrypt_integration_config(config)
        return {
            "encrypted_config": encrypted_config,
            "config_encrypted": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt configuration: {str(e)}"
        )


@router.post("/integration-config/decrypt")
async def decrypt_integration_config(
    encrypted_config: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Decrypt an encrypted integration configuration.
    """
    try:
        decrypted_config = encryption_service.decrypt_integration_config(encrypted_config)
        return {
            "decrypted_config": decrypted_config
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decrypt configuration: {str(e)}"
        )


@router.post("/sign-irn")
async def sign_irn(request: SignIRNRequest) -> SignIRNResponse:
    """
    Sign an IRN with the FIRS public key and generate a QR code.
    """
    # Validate IRN
    if not validate_irn(request.irn):
        raise HTTPException(
            status_code=400,
            detail="Invalid IRN format"
        )
    
    # Use placeholder certificate if not provided
    certificate = request.certificate or "PLACEHOLDER_CERTIFICATE"
    
    # In production, this would use the actual FIRS public key
    # For development, use a placeholder encryption
    encrypted_data = f"{request.irn}|{certificate}"
    
    # Generate QR code
    qr_code_bytes = generate_qr_code_for_irn(
        irn=request.irn,
        certificate=certificate,
        encrypted_data=encrypted_data
    )
    
    # Convert QR code to base64 for response
    qr_code_base64 = qr_code_as_base64(qr_code_bytes)
    
    return SignIRNResponse(
        irn=request.irn,
        encrypted_data=encrypted_data,
        qr_code_base64=qr_code_base64
    )


@router.post("/generate-irn")
async def create_irn(request: GenerateIRNRequest) -> Dict[str, str]:
    """
    Generate an IRN according to FIRS requirements.
    """
    try:
        irn = generate_irn(
            invoice_number=request.invoice_number,
            service_id=request.service_id,
            timestamp=request.timestamp
        )
        
        return {
            "irn": irn,
            "status": "Valid",
            "timestamp": request.timestamp or "",
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"IRN generation failed: {str(e)}"
        )


@router.get("/qr-code/{irn}")
async def get_qr_code(irn: str):
    """
    Generate a QR code for an IRN and return it as an image.
    """
    # Validate IRN
    if not validate_irn(irn):
        raise HTTPException(
            status_code=400,
            detail="Invalid IRN format"
        )
    
    # Use placeholder certificate
    certificate = "PLACEHOLDER_CERTIFICATE"
    
    # Generate QR code
    qr_code_bytes = generate_qr_code_for_irn(
        irn=irn,
        certificate=certificate
    )
    
    # Return as image
    return Response(
        content=qr_code_bytes,
        media_type="image/png"
    ) 


@router.post("/generate-csid")
async def generate_csid(
    request: CSIDRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate a Cryptographic Stamp ID (CSID) for an invoice.
    
    The CSID provides tamper-proof evidence of invoice authenticity
    and is required for compliance with FIRS digital signing requirements.
    """
    try:
        # Generate CSID using the signing utility
        invoice_with_csid = sign_invoice(request.invoice_data)
        
        # Extract CSID information
        csid_info = invoice_with_csid.get("cryptographic_stamp", {})
        
        return CSIDResponse(
            cryptographic_stamp=csid_info,
            is_signed=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CSID: {str(e)}"
        )


@router.post("/verify-csid")
async def verify_csid_endpoint(
    request: VerifyCSIDRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Verify a Cryptographic Stamp ID (CSID) on an invoice.
    
    This checks that the invoice has not been tampered with since it was signed.
    """
    try:
        # Verify the CSID
        is_valid, details = verify_csid(
            invoice_data=request.invoice_data,
            csid=request.csid
        )
        
        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "is_valid": False,
                    "details": {
                        "error": "Invalid CSID",
                        **(details or {})
                    }
                }
            )
        
        return VerifyCSIDResponse(
            is_valid=True,
            details=details
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify CSID: {str(e)}"
        )


@router.post("/generate-stamp", response_model=CryptoStampResponse)
async def generate_cryptographic_stamp(
    request: CryptoStampRequest,
    current_user: User = Depends(get_current_active_user),
    crypto_stamping_service: CryptographicStampingService = Depends(get_cryptographic_stamping_service)
):
    """
    Generate a cryptographic stamp for an invoice according to FIRS requirements.
    
    This enhanced version provides a compliant cryptographic stamp that includes:
    - Digital signature for invoice authenticity verification
    - Timestamp for audit trail
    - QR code containing the signature for easy verification
    - Certificate reference for validation
    """
    try:
        # Apply the cryptographic stamp to the invoice
        stamped_invoice = crypto_stamping_service.stamp_invoice(request.invoice_data)
        
        # Extract stamp information
        stamp_info = stamped_invoice.get("cryptographic_stamp", {})
        
        return CryptoStampResponse(
            stamped_invoice=stamped_invoice,
            stamp_info=stamp_info
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cryptographic stamp: {str(e)}"
        )


@router.post("/verify-stamp")
async def verify_cryptographic_stamp(
    request: VerifyStampRequest,
    current_user: User = Depends(get_current_active_user),
    crypto_stamping_service: CryptographicStampingService = Depends(get_cryptographic_stamping_service)
):
    """
    Verify a cryptographic stamp on an invoice.
    
    This checks that the invoice has not been tampered with since it was stamped
    and validates the authenticity of the stamp according to FIRS requirements.
    """
    try:
        # Verify the cryptographic stamp
        is_valid, details = crypto_stamping_service.verify_stamp(
            request.invoice_data, 
            request.stamp_data
        )
        
        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "is_valid": False,
                    "details": {
                        "error": "Invalid cryptographic stamp",
                        **(details or {})
                    }
                }
            )
        
        return {
            "is_valid": True,
            "details": details
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify cryptographic stamp: {str(e)}"
        )


@router.get("/certificates")
async def list_certificates(
    current_user: User = Depends(get_current_active_user),
    certificate_manager: CertificateManager = Depends(get_certificate_manager)
):
    """
    List all available certificates for cryptographic stamping.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view certificates"
        )
    
    try:
        # Get all certificate files in the certificates directory
        cert_files = [f for f in os.listdir(certificate_manager.certs_dir) 
                     if f.endswith(".crt") or f.endswith(".pem")]
        
        certificates = []
        for cert_file in cert_files:
            cert_path = os.path.join(certificate_manager.certs_dir, cert_file)
            try:
                is_valid, cert_info = certificate_manager.validate_certificate(cert_path)
                certificates.append({
                    "filename": cert_file,
                    "path": cert_path,
                    "is_valid": is_valid,
                    **(cert_info or {})
                })
            except Exception as e:
                certificates.append({
                    "filename": cert_file,
                    "path": cert_path,
                    "is_valid": False,
                    "error": str(e)
                })
        
        return {
            "certificates": certificates,
            "count": len(certificates)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list certificates: {str(e)}"
        )