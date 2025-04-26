from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import re
from typing import List, Optional

from app.models.irn import IRNRecord
from app.schemas.irn import IRNGenerateRequest
from app.crud.integration import get_integration_by_id


def validate_irn_format(invoice_number: str, service_id: str, timestamp: str) -> bool:
    """
    Validate that the IRN components follow the FIRS requirements.
    
    Args:
        invoice_number: Alphanumeric invoice number without special characters
        service_id: 8-character alphanumeric service ID
        timestamp: Date in YYYYMMDD format
        
    Returns:
        bool: True if all components are valid, False otherwise
    """
    # Validate invoice number (alphanumeric, no special characters)
    if not re.match(r'^[a-zA-Z0-9]+$', invoice_number):
        return False
    
    # Validate service ID (8-character alphanumeric)
    if not re.match(r'^[a-zA-Z0-9]{8}$', service_id):
        return False
    
    # Validate timestamp (YYYYMMDD format)
    if not re.match(r'^\d{8}$', timestamp):
        return False
    
    return True


def generate_irn(invoice_number: str, service_id: str, timestamp: str) -> str:
    """
    Generate an IRN using the FIRS format.
    
    Args:
        invoice_number: Alphanumeric invoice number without special characters
        service_id: 8-character alphanumeric service ID
        timestamp: Date in YYYYMMDD format
        
    Returns:
        str: Generated IRN in the format InvoiceNumber-ServiceID-YYYYMMDD
    """
    return f"{invoice_number}-{service_id}-{timestamp}"


def create_irn(db: Session, request: IRNGenerateRequest, service_id: str, valid_days: int = 7) -> IRNRecord:
    """
    Create a new IRN record in the database.
    
    Args:
        db: Database session
        request: IRN generation request
        service_id: Service ID from FIRS for the organization
        valid_days: Number of days the IRN is valid
        
    Returns:
        IRNRecord: Created IRN record
    """
    timestamp = request.timestamp or datetime.now().strftime("%Y%m%d")
    
    # Generate IRN
    irn_value = generate_irn(request.invoice_number, service_id, timestamp)
    
    # Calculate validity
    valid_until = datetime.now() + timedelta(days=valid_days)
    
    # Create IRN record
    irn_record = IRNRecord(
        irn=irn_value,
        integration_id=request.integration_id,
        invoice_number=request.invoice_number,
        service_id=service_id,
        timestamp=timestamp,
        valid_until=valid_until,
        status="unused",
    )
    
    db.add(irn_record)
    db.commit()
    db.refresh(irn_record)
    
    return irn_record


def get_irn_by_value(db: Session, irn_value: str) -> Optional[IRNRecord]:
    """
    Retrieve an IRN record by its value.
    
    Args:
        db: Database session
        irn_value: IRN to lookup
        
    Returns:
        Optional[IRNRecord]: Found IRN record or None
    """
    return db.query(IRNRecord).filter(IRNRecord.irn == irn_value).first()


def get_irns_by_integration(db: Session, integration_id: str, skip: int = 0, limit: int = 100) -> List[IRNRecord]:
    """
    Retrieve IRN records for a specific integration.
    
    Args:
        db: Database session
        integration_id: Integration ID
        skip: Records to skip
        limit: Maximum records to return
        
    Returns:
        List[IRNRecord]: List of IRN records
    """
    return db.query(IRNRecord).filter(
        IRNRecord.integration_id == integration_id
    ).offset(skip).limit(limit).all()


def update_irn_status(db: Session, irn_value: str, status: str, invoice_id: Optional[str] = None) -> Optional[IRNRecord]:
    """
    Update the status of an IRN.
    
    Args:
        db: Database session
        irn_value: IRN to update
        status: New status (used, unused, expired)
        invoice_id: Optional external invoice ID
        
    Returns:
        Optional[IRNRecord]: Updated IRN record or None
    """
    irn_record = get_irn_by_value(db, irn_value)
    if not irn_record:
        return None
    
    irn_record.status = status
    
    if status == "used" and not irn_record.used_at:
        irn_record.used_at = datetime.now()
    
    if invoice_id:
        irn_record.invoice_id = invoice_id
    
    db.commit()
    db.refresh(irn_record)
    
    return irn_record 