"""
Crypto endpoints for FIRS e-Invoice system.

This module provides API endpoints for:
- Downloading crypto keys
- Signing IRNs
- Generating QR codes
"""

import os
from typing import Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile # type: ignore
from fastapi.responses import Response, JSONResponse # type: ignore
from pydantic import BaseModel, Field # type: ignore

from app.utils.encryption import encrypt_irn_data, extract_keys_from_file, load_public_key # type: ignore
from app.utils.irn import generate_irn, validate_irn # type: ignore
from app.utils.qr_code import generate_qr_code, generate_qr_code_for_irn, qr_code_as_base64 # type: ignore

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


@router.get("/keys")
async def get_crypto_keys() -> CryptoKeysResponse:
    """
    Download cryptographic keys for IRN signing.
    
    In a production environment, this would retrieve actual keys from FIRS.
    For development, it returns placeholder data.
    """
    # In production, this would retrieve actual FIRS keys
    # For development, return placeholder data
    return CryptoKeysResponse(
        message="Development keys downloaded successfully",
        public_key="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvFfM12y9\n-----END PUBLIC KEY-----"
    )


@router.post("/upload-keys")
async def upload_crypto_keys(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Upload a crypto_keys.txt file and extract the keys.
    
    This is used to process the FIRS-provided key file.
    """
    if file.filename != "crypto_keys.txt":
        raise HTTPException(
            status_code=400,
            detail="Invalid file: must be named crypto_keys.txt"
        )
    
    # Save the uploaded file
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    try:
        # Extract keys
        public_key_pem, certificate = extract_keys_from_file(temp_file_path)
        
        # Clean up temporary file
        os.remove(temp_file_path)
        
        return {
            "message": "Keys extracted successfully",
            "public_key_length": str(len(public_key_pem)),
            "certificate_length": str(len(certificate))
        }
    except Exception as e:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process key file: {str(e)}"
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