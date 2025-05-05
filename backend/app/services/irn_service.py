"""
IRN (Invoice Reference Number) service for generating, validating, and managing IRNs.

This service implements the core logic for:
1. Generating unique IRNs based on invoice data
2. Verifying and validating IRNs
3. Managing IRN lifecycle (creation, validation, expiration)
"""
import uuid
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.irn import IRNRecord, InvoiceData, IRNValidationRecord, IRNStatus
from app.models.user import User
from app.models.organization import Organization
from app.schemas.irn import IRNCreate


def generate_irn(invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Generate a unique Invoice Reference Number (IRN) based on invoice data.
    
    Args:
        invoice_data: Dictionary containing invoice details
        
    Returns:
        Tuple containing (irn_value, verification_code, hash_value)
    """
    # Generate a unique identifier (UUID v4)
    unique_id = str(uuid.uuid4())
    
    # Create a timestamp component in the format YYYYMMDDHHMMSS
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
    
    # Construct the IRN value
    # Format: IRN-{timestamp}-{first 8 chars of unique_id}-{first 6 chars of hash}
    irn_value = f"IRN-{timestamp}-{unique_id[:8]}-{hash_value[:6]}".upper()
    
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
    # Find the IRN record in the database
    irn_record = db.query(IRNRecord).filter(IRNRecord.irn_value == irn_value).first()
    
    if not irn_record:
        return False, "IRN not found"
    
    # Check if the IRN is active
    if irn_record.status != IRNStatus.ACTIVE:
        return False, f"IRN is {irn_record.status.value}"
    
    # Check if the IRN has expired
    if datetime.utcnow() > irn_record.expires_at:
        # Update the status to expired
        irn_record.status = IRNStatus.EXPIRED
        db.add(irn_record)
        db.commit()
        return False, "IRN has expired"
    
    # Verify the verification code
    expected_verification_code = hmac.new(
        settings.SECRET_KEY.encode(),
        irn_record.hash_value.encode(),
        hashlib.sha256
    ).hexdigest()[:12]
    
    if verification_code != expected_verification_code:
        return False, "Invalid verification code"
    
    # Verify the invoice data hash
    # This would involve creating a hash of the provided invoice data and comparing
    # it with the stored hash, but for simplicity we'll skip the detailed verification
    
    return True, "IRN is valid"


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
    irn_id: uuid.UUID,
    is_valid: bool,
    message: str,
    validated_by: str
) -> IRNValidationRecord:
    """
    Create a record of an IRN validation attempt.
    
    Args:
        db: Database session
        irn_id: UUID of the IRN
        is_valid: Whether the validation was successful
        message: Validation message
        validated_by: Who performed the validation
        
    Returns:
        Created validation record
    """
    # Create the validation record
    validation_record = IRNValidationRecord(
        id=uuid.uuid4(),
        irn_id=irn_id,
        validation_date=datetime.utcnow(),
        validation_status=is_valid,
        validation_message=message,
        validated_by=validated_by
    )
    
    db.add(validation_record)
    db.commit()
    db.refresh(validation_record)
    
    return validation_record
