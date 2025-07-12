"""
Cryptographic stamping service for FIRS e-Invoice system.

This service provides comprehensive functionality for:
- Generating cryptographic stamps for invoices
- Verifying cryptographic stamps
- Managing certificates for the stamping process
- Generating QR codes with embedded cryptographic stamps
"""

import os
import base64
import json
import hashlib
import logging
import datetime
from typing import Dict, Tuple, Union, Optional, Any, List

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
from fastapi import HTTPException, Depends

from app.core.config import settings
from app.utils.certificate_manager import CertificateManager, get_certificate_manager
from app.utils.key_management import KeyManager, get_key_manager
from app.utils.crypto_signing import CSIDGenerator, SigningAlgorithm
from app.utils.qr_code import generate_qr_code, qr_code_as_base64

logger = logging.getLogger(__name__)


class CryptographicStampingService:
    """
    Service for cryptographic stamping operations required by FIRS.
    
    This service integrates with the certificate management system to:
    - Generate compliant cryptographic stamps for e-invoices
    - Verify the authenticity of cryptographic stamps
    - Manage certificate lifecycles
    - Ensure compliance with FIRS specifications
    """
    
    def __init__(
        self,
        certificate_manager: Optional[CertificateManager] = None,
        key_manager: Optional[KeyManager] = None
    ):
        """
        Initialize the Cryptographic Stamping Service.
        
        Args:
            certificate_manager: CertificateManager instance
            key_manager: KeyManager instance
        """
        self.certificate_manager = certificate_manager or get_certificate_manager()
        self.key_manager = key_manager or get_key_manager()
        self.csid_generator = CSIDGenerator()
    
    def generate_stamp(
        self, 
        invoice_data: Dict[str, Any],
        algorithm: str = SigningAlgorithm.RSA_PSS_SHA256.value
    ) -> Dict[str, Any]:
        """
        Generate a cryptographic stamp for an invoice according to FIRS requirements.
        
        Args:
            invoice_data: Invoice data to stamp
            algorithm: Signing algorithm to use
            
        Returns:
            Dictionary containing the stamp data and metadata
        """
        try:
            # Get a certificate for stamping
            cert_path = self.certificate_manager.get_or_create_firs_stamp_certificate()
            
            # Generate a CSID for the invoice data
            csid = self.csid_generator.generate_csid(invoice_data, algorithm)
            
            # Create a timestamp for the stamping operation
            timestamp = datetime.datetime.now().isoformat()
            
            # Generate a QR code containing the CSID
            qr_data = {
                "csid": csid,
                "timestamp": timestamp,
                "algorithm": algorithm,
                "irn": invoice_data.get("irn", ""),
                "invoice_number": invoice_data.get("invoice_number", "")
            }
            
            qr_code_base64 = qr_code_as_base64(json.dumps(qr_data))
            
            # Create the stamp data
            stamp_data = {
                "cryptographic_stamp_id": csid,
                "timestamp": timestamp,
                "algorithm": algorithm,
                "certificate_used": os.path.basename(cert_path),
                "qr_code": qr_code_base64,
                "is_valid": True
            }
            
            return stamp_data
        except Exception as e:
            logger.error(f"Failed to generate cryptographic stamp: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate cryptographic stamp: {str(e)}"
            )
    
    def verify_stamp(
        self, 
        invoice_data: Dict[str, Any],
        stamp_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify a cryptographic stamp on an invoice.
        
        Args:
            invoice_data: Original invoice data
            stamp_data: Stamp data to verify
            
        Returns:
            Tuple of (is_valid, verification_details)
        """
        try:
            # Extract the CSID from the stamp data
            csid = stamp_data.get("cryptographic_stamp_id")
            if not csid:
                return False, {"error": "No cryptographic stamp ID found"}
            
            # Get the certificate that was used for stamping
            cert_name = stamp_data.get("certificate_used")
            if not cert_name:
                return False, {"error": "No certificate information found in stamp"}
            
            cert_path = os.path.join(self.certificate_manager.certs_dir, cert_name)
            if not os.path.exists(cert_path):
                return False, {"error": f"Certificate {cert_name} not found"}
            
            # Verify the CSID
            is_valid, details = self.csid_generator.verify_csid(
                invoice_data,
                csid,
                cert_path
            )
            
            # Add timestamp validation
            stamp_timestamp = stamp_data.get("timestamp")
            if stamp_timestamp:
                try:
                    stamp_datetime = datetime.datetime.fromisoformat(stamp_timestamp)
                    details["timestamp_validation"] = {
                        "stamp_time": stamp_timestamp,
                        "current_time": datetime.datetime.now().isoformat(),
                        "is_future_dated": stamp_datetime > datetime.datetime.now()
                    }
                except Exception as e:
                    details["timestamp_validation"] = {
                        "error": f"Invalid timestamp format: {str(e)}"
                    }
            
            return is_valid, details
        except Exception as e:
            logger.error(f"Failed to verify cryptographic stamp: {str(e)}")
            return False, {"error": f"Verification failed: {str(e)}"}
    
    def stamp_invoice(
        self, 
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply a cryptographic stamp to an invoice and return the updated invoice data.
        
        Args:
            invoice_data: Original invoice data
            
        Returns:
            Invoice data with cryptographic stamp added
        """
        # Generate the cryptographic stamp
        stamp_data = self.generate_stamp(invoice_data)
        
        # Create a copy of the invoice data to avoid modifying the original
        stamped_invoice = invoice_data.copy()
        
        # Add the stamp data to the invoice
        stamped_invoice["cryptographic_stamp"] = stamp_data
        
        # Generate QR code URL if not already present
        if "qr_code_url" not in stamped_invoice:
            qr_content = {
                "irn": stamped_invoice.get("irn", ""),
                "invoice_number": stamped_invoice.get("invoice_number", ""),
                "cryptographic_stamp_id": stamp_data["cryptographic_stamp_id"],
                "timestamp": stamp_data["timestamp"]
            }
            stamped_invoice["qr_code_url"] = qr_code_as_base64(json.dumps(qr_content))
        
        return stamped_invoice


# Create a singleton instance for easy import
cryptographic_stamping_service = CryptographicStampingService()


def get_cryptographic_stamping_service(
    certificate_manager: CertificateManager = Depends(get_certificate_manager),
    key_manager: KeyManager = Depends(get_key_manager)
) -> CryptographicStampingService:
    """
    Get or create the cryptographic stamping service instance.
    
    Args:
        certificate_manager: CertificateManager instance
        key_manager: KeyManager instance
    
    Returns:
        CryptographicStampingService instance
    """
    global cryptographic_stamping_service
    
    # Ensure the service is using the correct dependencies
    if cryptographic_stamping_service.certificate_manager != certificate_manager or \
       cryptographic_stamping_service.key_manager != key_manager:
        cryptographic_stamping_service = CryptographicStampingService(
            certificate_manager=certificate_manager,
            key_manager=key_manager
        )
    
    return cryptographic_stamping_service
