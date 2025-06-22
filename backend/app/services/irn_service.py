"""
IRN (Invoice Reference Number) service for generating, validating, and managing IRNs.

This service implements the core logic for:
1. Generating unique IRNs based on invoice data
2. Verifying and validating IRNs
3. Managing IRN lifecycle (creation, validation, expiration)
4. Bulk IRN generation for batch processing
5. IRN caching for performance optimization
6. Audit logging for compliance and traceability
7. FIRS sandbox API integration for validation
"""
import uuid
import hashlib
import hmac
import base64
import json
import logging
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List, Union, Set
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.irn import IRNRecord, InvoiceData, IRNValidationRecord, IRNStatus
from app.models.user import User
from app.models.organization import Organization
from app.schemas.irn import IRNCreate, IRNBatchGenerateRequest
from app.cache.irn_cache import IRNCache
from app.services.odoo_service import fetch_odoo_invoices

logger = logging.getLogger(__name__)


def generate_irn(invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Generate a unique Invoice Reference Number (IRN) based on invoice data.
    
    Args:
        invoice_data: Dictionary containing invoice details
        
    Returns:
        Tuple containing (irn_value, verification_code, hash_value)
    """
    # Import the IRN generator
    from app.utils.irn_generator import generate_firs_irn
    
    try:
        # Generate IRN using the enhanced FIRS-compliant generator
        irn_result = generate_firs_irn(invoice_data)
        
        # Extract components from the result
        irn_value = irn_result['irn']
        verification_code = irn_result['verification_code']
        hash_value = irn_result['hash_value']
        
        # Log successful generation
        logger.info(f"Generated IRN: {irn_value} for invoice: {invoice_data.get('invoice_number', '')}")  
        
        return irn_value, verification_code, hash_value
    
    except Exception as e:
        # Log error
        logger.error(f"Error generating IRN: {str(e)}")
        
        # Fallback to legacy method if new implementation fails
        # This ensures backward compatibility
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        # Extract key invoice fields for the hash
        invoice_number = invoice_data.get('invoice_number', '')
        invoice_date = invoice_data.get('invoice_date', '')
        customer_tax_id = invoice_data.get('customer_tax_id', '')
        total_amount = str(invoice_data.get('total_amount', 0))
        
        # Create a string to hash
        data_to_hash = f"{invoice_number}|{invoice_date}|{customer_tax_id}|{total_amount}|{timestamp}|{unique_id}"
        
        # Create a hash of the invoice data for verification
        hash_value = hashlib.sha256(data_to_hash.encode()).hexdigest()
        
        # Generate a verification code using HMAC and a secret key
        verification_code = hmac.new(
            settings.SECRET_KEY.encode(),
            hash_value.encode(),
            hashlib.sha256
        ).hexdigest()[:12]  # Take first 12 characters for brevity
        
        # Construct the IRN value with legacy format
        # Format: IRN-{timestamp}-{first 8 chars of unique_id}-{first 6 chars of hash}
        irn_value = f"IRN-{timestamp}-{unique_id[:8]}-{hash_value[:6]}".upper()
        
        # Log fallback to legacy method
        logger.warning(f"Used legacy IRN generation for invoice: {invoice_data.get('invoice_number', '')}")  
        
        return irn_value, verification_code, hash_value


def verify_irn(
    db: Session,
    irn_value: str,
    verification_code: str,
    invoice_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Verify if an IRN is valid.
    
    Args:
        db: Database session
        irn_value: The IRN value to verify
        verification_code: The verification code provided with the IRN
        invoice_data: The invoice data to verify against
        
    Returns:
        Tuple containing (is_valid, message)
    """
    try:
        # First, check if this IRN exists in the database for quick validation
        irn_record = db.query(IRNRecord).filter(IRNRecord.irn_value == irn_value).first()
        
        if irn_record:
            # Check if the IRN has expired
            if irn_record.expiration_date and irn_record.expiration_date < datetime.utcnow():
                return False, "IRN has expired"
            
            # Check if the IRN is revoked
            if irn_record.status == IRNStatus.REVOKED:
                return False, "IRN has been revoked"
            
            # Check if verification code matches
            if verification_code != irn_record.verification_code:
                return False, "Invalid verification code"
            
            # If stored invoice data exists, verify it against the provided data
            if irn_record.invoice_data:
                stored_data = decode_invoice_data(irn_record.invoice_data)
                
                # Verify key invoice details
                if stored_data.get('invoice_number') != invoice_data.get('invoice_number'):
                    return False, "Invoice number mismatch"
                
                if stored_data.get('total_amount') != invoice_data.get('total_amount'):
                    return False, "Invoice amount mismatch"
                
                # More detailed validations could be added here
            
            return True, "IRN verification successful"
        
        # If not in database, determine if it's a FIRS-formatted IRN or a legacy IRN
        if irn_value.startswith("IRN-"):
            # Legacy format: IRN-{timestamp}-{unique_id}-{hash}
            parts = irn_value.split('-')
            if len(parts) != 4 or parts[0] != 'IRN':
                return False, "Invalid IRN format"
            
            # Currently, we can't fully verify an unknown legacy IRN without the original unique_id
            return False, "Legacy IRN not found in database"
        else:
            # Attempt to verify FIRS-formatted IRN using the new generator
            from app.utils.irn_generator import verify_irn as verify_firs_irn
            
            # Use the new verification function
            is_valid, message = verify_firs_irn(irn_value, invoice_data)
            
            if is_valid:
                logger.info(f"Verified external FIRS IRN: {irn_value}")
                # Consider adding this verified IRN to the database
                return True, "External FIRS IRN verification successful"
            else:
                logger.warning(f"Failed to verify external FIRS IRN: {irn_value} - {message}")
                return False, message
        
    except Exception as e:
        logger.error(f"Error verifying IRN: {e}")
        return False, f"Verification error: {str(e)}"


def get_irn_expiration_date() -> datetime:
    """
    Calculate the expiration date for a new IRN.
    By default, IRNs expire after 30 days.
    
    Returns:
        Datetime object for the expiration date
    """
    # IRNs expire after 30 days by default, or as configured
    expiration_days = getattr(settings, "IRN_EXPIRATION_DAYS", 30)
    return datetime.utcnow() + timedelta(days=expiration_days)


def expire_outdated_irns(db: Session) -> int:
    """
    Find and expire all IRNs that have passed their expiration date.
    
    Args:
        db: Database session
        
    Returns:
        Number of IRNs expired
    """
    now = datetime.utcnow()
    
    # Find all active IRNs that have expired
    expired_irns = (
        db.query(IRNRecord)
        .filter(
            IRNRecord.status == IRNStatus.ACTIVE,
            IRNRecord.expires_at < now
        )
        .all()
    )
    
    # Update their status to expired
    for irn in expired_irns:
        irn.status = IRNStatus.EXPIRED
        db.add(irn)
    
    if expired_irns:
        db.commit()
    
    return len(expired_irns)


def encode_invoice_data(invoice_data: Dict[str, Any]) -> str:
    """
    Encode invoice data for storage.
    This could involve encryption in a production environment.
    
    Args:
        invoice_data: Dictionary of invoice data
        
    Returns:
        Encoded string representation
    """
    # For simplicity, we'll just create a string representation
    # In a production environment, this would use encryption
    import json
    return json.dumps(invoice_data)


def decode_invoice_data(encoded_data: str) -> Dict[str, Any]:
    """
    Decode stored invoice data.
    
    Args:
        encoded_data: Encoded invoice data string
        
    Returns:
        Dictionary of invoice data
    """
    # For simplicity, we'll just parse the JSON
    # In a production environment, this would use decryption
    import json
    return json.loads(encoded_data)


def create_validation_record(
    db: Session,
    irn_id: str,
    is_valid: bool,
    message: str,
    validated_by: Optional[str] = None,
    validation_source: str = "system",
    request_data: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None
) -> IRNValidationRecord:
    """
    Create a record of an IRN validation attempt with enhanced audit logging.
    
    Args:
        db: Database session
        irn_id: ID of the IRN
        is_valid: Whether the validation was successful
        message: Validation message
        validated_by: User ID that performed the validation (if applicable)
        validation_source: Source of validation (system, api, user, firs)
        request_data: Data used in the validation request (for audit)
        response_data: Response data from validation (for audit)
        
    Returns:
        Created validation record
    """
    # Log the validation attempt
    logger.info(
        f"IRN validation attempt: {irn_id}, valid={is_valid}, source={validation_source}, message={message}"
    )
    
    # Create the validation record with enhanced audit data
    validation_record = IRNValidationRecord(
        id=uuid.uuid4(),
        irn=irn_id,
        validation_date=datetime.utcnow(),
        validation_status=is_valid,
        validation_message=message,
        validated_by=validated_by,
        validation_source=validation_source,
        request_data=request_data,
        response_data=response_data
    )
    
    db.add(validation_record)
    db.commit()
    db.refresh(validation_record)
    
    return validation_record


class IRNService:
    """
    IRN (Invoice Reference Number) service class for generating, validating, and managing IRNs.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = IRNCache()
        
    def generate_irn(self, invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Generate IRN using the module function."""
        return generate_irn(invoice_data)
    
    def verify_irn(self, irn_value: str, verification_code: str, invoice_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Verify IRN using the module function."""
        return verify_irn(self.db, irn_value, verification_code, invoice_data)
    
    def expire_outdated_irns(self) -> int:
        """Expire outdated IRNs using the module function."""
        return expire_outdated_irns(self.db)
    
    def create_validation_record(self, irn_id: str, is_valid: bool, message: str, **kwargs) -> IRNValidationRecord:
        """Create validation record using the module function."""
        return create_validation_record(self.db, irn_id, is_valid, message, **kwargs)
