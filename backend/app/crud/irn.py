from sqlalchemy.orm import Session # type: ignore
from sqlalchemy import func, and_ # type: ignore
from datetime import datetime, timedelta
import re
from typing import List, Optional, Dict, Any, Tuple # type: ignore
from uuid import UUID
import logging

from app.models.irn import IRNRecord
from app.schemas.irn import IRNGenerateRequest, IRNMetricsResponse
from app.utils.irn_generator import validate_invoice_number, validate_service_id, validate_timestamp, generate_firs_irn as utils_generate_irn
from fastapi import HTTPException # type: ignore

logger = logging.getLogger(__name__)

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
    try:
        return (
            validate_invoice_number(invoice_number) and
            validate_service_id(service_id) and
            validate_timestamp(timestamp)
        )
    except Exception as e:
        logger.error(f"IRN validation error: {str(e)}")
        return False


def generate_irn(invoice_number: str, service_id: str, timestamp: str) -> str:
    """
    Generate an IRN using the FIRS format.
    
    Args:
        invoice_number: Alphanumeric invoice number without special characters
        service_id: 8-character alphanumeric service ID
        timestamp: Date in YYYYMMDD format
        
    Returns:
        str: Generated IRN in the format InvoiceNumber-ServiceID-YYYYMMDD
        
    Raises:
        HTTPException: If any component is invalid
    """
    try:
        return utils_generate_irn(invoice_number, service_id, timestamp)
    except HTTPException as e:
        # Re-raise the HTTPException
        raise e
    except Exception as e:
        logger.error(f"Error generating IRN: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating IRN: {str(e)}"
        )


def create_irn(
    db: Session, 
    request: IRNGenerateRequest, 
    service_id: str, 
    valid_days: int = 7,
    metadata: Optional[Dict[str, Any]] = None
) -> IRNRecord:
    """
    Create a new IRN record in the database.
    
    Args:
        db: Database session
        request: IRN generation request
        service_id: Service ID from FIRS for the organization
        valid_days: Number of days the IRN is valid
        metadata: Optional additional metadata to store with the IRN
        
    Returns:
        IRNRecord: Created IRN record
        
    Raises:
        HTTPException: If IRN generation fails or if a duplicate IRN already exists
    """
    timestamp = request.timestamp or datetime.now().strftime("%Y%m%d")
    
    try:
        # Generate IRN
        irn_value = generate_irn(request.invoice_number, service_id, timestamp)
        
        # Check if IRN already exists
        existing_irn = get_irn_by_value(db, irn_value)
        if existing_irn:
            raise HTTPException(
                status_code=409,
                detail=f"IRN '{irn_value}' already exists"
            )
        
        # Calculate validity
        valid_until = datetime.now() + timedelta(days=valid_days)
        
        # Create IRN record
        irn_record = IRNRecord(
            irn=irn_value,
            integration_id=str(request.integration_id),
            invoice_number=request.invoice_number,
            service_id=service_id,
            timestamp=timestamp,
            valid_until=valid_until,
            status="unused",
            meta_data=metadata or {}
        )
        
        db.add(irn_record)
        db.commit()
        db.refresh(irn_record)
        
        logger.info(f"Created IRN: {irn_value}")
        return irn_record
        
    except HTTPException as e:
        # Re-raise the HTTPException
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating IRN record: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating IRN record: {str(e)}"
        )


def create_batch_irn(
    db: Session,
    integration_id: UUID,
    invoice_numbers: List[str],
    service_id: str,
    timestamp: Optional[str] = None,
    valid_days: int = 7
) -> Tuple[List[IRNRecord], List[Dict[str, str]]]:
    """
    Create multiple IRN records in the database.
    
    Args:
        db: Database session
        integration_id: Integration ID
        invoice_numbers: List of invoice numbers
        service_id: Service ID from FIRS for the organization
        timestamp: Optional date in YYYYMMDD format
        valid_days: Number of days the IRNs are valid
        
    Returns:
        Tuple[List[IRNRecord], List[Dict[str, str]]]: Tuple of (successful IRN records, failed invoice details)
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d")
    
    successful_records = []
    failed_invoices = []
    
    for invoice_number in invoice_numbers:
        try:
            if not validate_invoice_number(invoice_number):
                failed_invoices.append({
                    "invoice_number": invoice_number,
                    "error": "Invalid invoice number format"
                })
                continue
                
            # Generate IRN
            irn_value = generate_irn(invoice_number, service_id, timestamp)
            
            # Check if IRN already exists
            existing_irn = get_irn_by_value(db, irn_value)
            if existing_irn:
                failed_invoices.append({
                    "invoice_number": invoice_number,
                    "error": "IRN already exists"
                })
                continue
            
            # Calculate validity
            valid_until = datetime.now() + timedelta(days=valid_days)
            
            # Create IRN record
            irn_record = IRNRecord(
                irn=irn_value,
                integration_id=str(integration_id),
                invoice_number=invoice_number,
                service_id=service_id,
                timestamp=timestamp,
                valid_until=valid_until,
                status="unused"
            )
            
            db.add(irn_record)
            successful_records.append(irn_record)
            
        except Exception as e:
            logger.error(f"Error generating IRN for invoice {invoice_number}: {str(e)}")
            failed_invoices.append({
                "invoice_number": invoice_number,
                "error": str(e)
            })
    
    if successful_records:
        try:
            db.commit()
            # Refresh all records
            for record in successful_records:
                db.refresh(record)
        except Exception as e:
            db.rollback()
            logger.error(f"Error committing batch IRN records: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error committing batch IRN records: {str(e)}"
            )
    
    return successful_records, failed_invoices


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


def get_irn_by_invoice_number(db: Session, integration_id: UUID, invoice_number: str) -> Optional[IRNRecord]:
    """
    Retrieve an IRN record by integration ID and invoice number.
    
    Args:
        db: Database session
        integration_id: Integration ID
        invoice_number: Invoice number
        
    Returns:
        Optional[IRNRecord]: Found IRN record or None
    """
    return db.query(IRNRecord).filter(
        and_(
            IRNRecord.integration_id == str(integration_id),
            IRNRecord.invoice_number == invoice_number
        )
    ).first()


def get_irns_by_integration(db: Session, integration_id: UUID, skip: int = 0, limit: int = 100) -> List[IRNRecord]:
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
        IRNRecord.integration_id == str(integration_id)
    ).order_by(IRNRecord.generated_at.desc()).offset(skip).limit(limit).all()


def update_irn_status(
    db: Session, 
    irn_value: str, 
    status: str, 
    invoice_id: Optional[str] = None
) -> Optional[IRNRecord]:
    """
    Update the status of an IRN.
    
    Args:
        db: Database session
        irn_value: IRN to update
        status: New status (used, unused, expired)
        invoice_id: Optional external invoice ID
        
    Returns:
        Optional[IRNRecord]: Updated IRN record or None
        
    Raises:
        HTTPException: If status is invalid or IRN not found
    """
    valid_statuses = ["used", "unused", "expired"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
        
    irn_record = get_irn_by_value(db, irn_value)
    if not irn_record:
        raise HTTPException(
            status_code=404, 
            detail="IRN not found"
        )
    
    try:
        irn_record.status = status
        
        if status == "used" and not irn_record.used_at:
            irn_record.used_at = datetime.now()
        
        if invoice_id:
            irn_record.invoice_id = invoice_id
        
        db.commit()
        db.refresh(irn_record)
        
        return irn_record
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating IRN status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating IRN status: {str(e)}"
        )


def get_irn_metrics(
    db: Session, 
    integration_id: Optional[UUID] = None
) -> IRNMetricsResponse:
    """
    Get metrics about IRN usage.
    
    Args:
        db: Database session
        integration_id: Optional integration ID to filter metrics
        
    Returns:
        IRNMetricsResponse: Metrics about IRN usage
    """
    try:
        query = db.query(IRNRecord)
        
        if integration_id:
            query = query.filter(IRNRecord.integration_id == str(integration_id))
        
        # Get counts by status
        used_count = query.filter(IRNRecord.status == "used").count()
        unused_count = query.filter(IRNRecord.status == "unused").count()
        expired_count = query.filter(IRNRecord.status == "expired").count()
        total_count = used_count + unused_count + expired_count
        
        # Get recent IRNs
        recent_irns = query.order_by(IRNRecord.generated_at.desc()).limit(10).all()
        
        return IRNMetricsResponse(
            used_count=used_count,
            unused_count=unused_count,
            expired_count=expired_count,
            total_count=total_count,
            recent_irns=recent_irns
        )
    except Exception as e:
        logger.error(f"Error getting IRN metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting IRN metrics: {str(e)}"
        )


def expire_outdated_irns(db: Session) -> int:
    """
    Update the status of all IRNs that have passed their valid_until date to 'expired'.
    
    Args:
        db: Database session
        
    Returns:
        int: Number of IRNs updated
    """
    try:
        # Find IRNs that are past their valid_until date and not already expired
        now = datetime.now()
        result = db.query(IRNRecord).filter(
            and_(
                IRNRecord.valid_until < now,
                IRNRecord.status != "expired"
            )
        ).update(
            {"status": "expired"},
            synchronize_session=False
        )
        
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        logger.error(f"Error expiring outdated IRNs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error expiring outdated IRNs: {str(e)}"
        )