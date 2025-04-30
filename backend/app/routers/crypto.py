"""
Crypto endpoints for FIRS e-Invoice system.

This module provides API endpoints for:
- Downloading crypto keys
- Signing IRNs
- Generating QR codes
"""

import os
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response, JSONResponse # type: ignore
from pydantic import BaseModel, Field # type: ignore
from sqlalchemy.orm import Session

from app.utils.encryption import encrypt_irn_data, extract_keys_from_file, load_public_key # type: ignore
from app.utils.irn import generate_irn, validate_irn # type: ignore
from app.utils.qr_code import generate_qr_code, generate_qr_code_for_irn, qr_code_as_base64 # type: ignore
from app.db.deps import get_db # type: ignore
from app.services.key_service import KeyManagementService, get_key_service
from app.services.encryption_service import EncryptionService, get_encryption_service
from app.core.security import get_current_active_user # type: ignore # type: ignore # type: ignore
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
    db: Session = Depends(get_db)
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
        
        # TODO: Store these keys in database for the organization
        
        return {"filename": file.filename, "message": "FIRS crypto keys uploaded successfully"}
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