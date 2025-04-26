"""
QR code generation utilities for FIRS e-Invoice system.

This module provides functions for generating QR codes from
encrypted IRN data as required by FIRS.
"""

import base64
import io
from typing import Optional, Union

import qrcode # type: ignore
from fastapi import HTTPException # type: ignore
from PIL import Image # type: ignore


def generate_qr_code(
    encrypted_data: str, 
    size: int = 10, 
    border: int = 4
) -> bytes:
    """
    Generate a QR code containing the encrypted IRN data.
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        size: QR code size (box size in pixels)
        border: Border size (in boxes)
        
    Returns:
        QR code image as bytes
    """
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=border,
        )
        
        # Add data to the QR code
        qr.add_data(encrypted_data)
        qr.make(fit=True)
        
        # Create an image from the QR code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR code generation failed: {str(e)}")


def generate_qr_code_for_irn(
    irn: str, 
    certificate: str, 
    encrypted_data: Optional[str] = None,
    size: int = 10,
    border: int = 4
) -> bytes:
    """
    Generate a QR code specifically for an invoice with IRN.
    
    This function takes either the raw IRN and certificate 
    or pre-encrypted data and generates a QR code.
    
    Args:
        irn: Invoice Reference Number (if encrypted_data not provided)
        certificate: FIRS certificate (if encrypted_data not provided)
        encrypted_data: Pre-encrypted data (optional)
        size: QR code size
        border: Border size
        
    Returns:
        QR code image as bytes
    """
    try:
        # If encrypted data not provided, use the IRN and certificate directly
        if not encrypted_data:
            from .encryption import encrypt_irn_data, load_public_key
            
            # In a real application, this would load the actual FIRS public key
            # For testing purposes, we'd use a generated key
            # TODO: Replace with actual key loading in production
            
            # Placeholder - in production, use actual FIRS public key
            encrypted_data = f"{irn}|{certificate}"
        
        # Generate and return QR code
        return generate_qr_code(encrypted_data, size, border)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IRN QR code generation failed: {str(e)}")


def qr_code_as_base64(qr_code_bytes: bytes) -> str:
    """
    Convert QR code bytes to base64 string for embedding in HTML/JSON.
    
    Args:
        qr_code_bytes: QR code image as bytes
        
    Returns:
        Base64 string representation with data URI prefix
    """
    try:
        base64_encoded = base64.b64encode(qr_code_bytes).decode('utf-8')
        return f"data:image/png;base64,{base64_encoded}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR code conversion failed: {str(e)}") 