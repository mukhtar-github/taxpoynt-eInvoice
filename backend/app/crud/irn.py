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
        ValueError: If any component is invalid
    """
    if not validate_irn_format(invoice_number, service_id, timestamp):
        raise ValueError("Invalid IRN components")
        
    return utils_generate_irn(invoice_number, service_id, timestamp)


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
    # Use current date if timestamp not provided
    timestamp = request.timestamp
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d")
    
    try:
        # Generate the IRN
        irn_value = generate_irn(request.invoice_number, service_id, timestamp)
        
        # Check if IRN already exists
        existing_irn = get_irn_by_value(db, irn_value)
        if existing_irn:
            # If the existing IRN belongs to the same integration and invoice number,
            # we can return it without error (idempotent behavior)
            if (
                existing_irn.integration_id == request.integration_id and 
                existing_irn.invoice_number == request.invoice_number
            ):
                return existing_irn
            else:
                # Otherwise, this is a collision - very unlikely but possible
                raise HTTPException(
                    status_code=409,
                    detail=f"IRN collision detected: {irn_value} already exists for a different invoice"
                )
        
        # Calculate expiration date
        valid_until = datetime.now() + timedelta(days=valid_days)
        
        # Create the IRN record
        irn_record = IRNRecord(
            irn=irn_value,
            integration_id=request.integration_id,
            invoice_number=request.invoice_number,
            service_id=service_id,
            timestamp=timestamp,
            status="unused",
            generated_at=datetime.now(),
            valid_until=valid_until,
            meta_data=metadata or {}
        )
        
        db.add(irn_record)
        db.commit()
        db.refresh(irn_record)
        
        return irn_record
        
    except ValueError as e:
        # Validation error
        raise HTTPException(
            status_code=400,
            detail=f"Failed to generate IRN: {str(e)}"
        )
    except Exception as e:
        # Other errors
        logger.error(f"IRN generation error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate IRN: Internal server error"
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
    # Use current date if timestamp not provided
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d")
    
    successful_records = []
    failed_records = []
    
    # Calculate expiration date (same for all IRNs in batch)
    valid_until = datetime.now() + timedelta(days=valid_days)
    
    for invoice_number in invoice_numbers:
        try:
            # Generate the IRN
            irn_value = generate_irn(invoice_number, service_id, timestamp)
            
            # Check if IRN already exists
            existing_irn = get_irn_by_value(db, irn_value)
            if existing_irn:
                # If the existing IRN belongs to the same integration and invoice number,
                # we can include it in the results without error
                if (
                    existing_irn.integration_id == integration_id and 
                    existing_irn.invoice_number == invoice_number
                ):
                    successful_records.append(existing_irn)
                    continue
                else:
                    # IRN collision
                    failed_records.append({
                        "invoice_number": invoice_number,
                        "error": f"IRN collision: {irn_value} already exists for a different invoice"
                    })
                    continue
            
            # Create the IRN record
            irn_record = IRNRecord(
                irn=irn_value,
                integration_id=integration_id,
                invoice_number=invoice_number,
                service_id=service_id,
                timestamp=timestamp,
                status="unused",
                generated_at=datetime.now(),
                valid_until=valid_until
            )
            
            db.add(irn_record)
            successful_records.append(irn_record)
            
        except Exception as e:
            # Log the failure and continue with other invoice numbers
            logger.error(f"Failed to generate IRN for invoice {invoice_number}: {str(e)}")
            failed_records.append({
                "invoice_number": invoice_number,
                "error": str(e)
            })
    
    # Commit all successful records at once
    if successful_records:
        try:
            db.commit()
            # Refresh all records to get their IDs
            for record in successful_records:
                db.refresh(record)
        except Exception as e:
            # If commit fails, roll back and treat all as failures
            db.rollback()
            logger.error(f"Failed to commit batch IRN generation: {str(e)}")
            failed_records.extend([
                {"invoice_number": record.invoice_number, "error": "Database commit failed"}
                for record in successful_records
            ])
            successful_records = []
    
    return successful_records, failed_records


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
            IRNRecord.integration_id == integration_id,
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
        IRNRecord.integration_id == integration_id
    ).offset(skip).limit(limit).all()


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
    # Validate status
    valid_statuses = ["used", "unused", "expired"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status}. Must be one of {valid_statuses}"
        )
    
    # Retrieve the IRN record
    irn_record = get_irn_by_value(db, irn_value)
    if not irn_record:
        raise HTTPException(
            status_code=404,
            detail=f"IRN not found: {irn_value}"
        )
    
    # Update status
    irn_record.status = status
    
    # Update used_at and invoice_id if status is "used"
    if status == "used":
        irn_record.used_at = datetime.now()
        if invoice_id:
            irn_record.invoice_id = invoice_id
    
    # Reset used_at and invoice_id if status is changing back to "unused"
    elif status == "unused" and irn_record.status != "unused":
        irn_record.used_at = None
        irn_record.invoice_id = None
    
    # Check if IRN has expired and force status if needed
    if irn_record.valid_until and irn_record.valid_until < datetime.now() and status != "expired":
        # Cannot change to "used" or "unused" if expired
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status to {status} for expired IRN. IRN expired on {irn_record.valid_until}"
        )
    
    try:
        db.commit()
        db.refresh(irn_record)
        return irn_record
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update IRN status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update IRN status: Internal server error"
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
    # Base query with optional integration filter
    base_query = db.query(IRNRecord)
    if integration_id:
        base_query = base_query.filter(IRNRecord.integration_id == integration_id)
    
    # Count IRNs by status
    used_count = base_query.filter(IRNRecord.status == "used").count()
    unused_count = base_query.filter(IRNRecord.status == "unused").count()
    expired_count = base_query.filter(IRNRecord.status == "expired").count()
    total_count = used_count + unused_count + expired_count
    
    # Get recent IRNs
    recent_irns = base_query.order_by(IRNRecord.generated_at.desc()).limit(10).all()
    
    return IRNMetricsResponse(
        used_count=used_count,
        unused_count=unused_count,
        expired_count=expired_count,
        total_count=total_count,
        recent_irns=recent_irns
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
        # Find unused IRNs that have expired
        expired_irns = db.query(IRNRecord).filter(
            and_(
                IRNRecord.status == "unused",
                IRNRecord.valid_until < datetime.now()
            )
        ).all()
        
        # Update their status
        count = 0
        for irn in expired_irns:
            irn.status = "expired"
            count += 1
        
        # Commit changes
        if count > 0:
            db.commit()
            
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to expire outdated IRNs: {str(e)}")
        return 0


# Add the missing functions needed by the routes
def get_irn(db: Session, irn_id: UUID) -> Optional[IRNRecord]:
    """
    Retrieve an IRN record by its ID.
    
    Args:
        db: Database session
        irn_id: UUID of the IRN record
        
    Returns:
        Optional[IRNRecord]: Found IRN record or None
    """
    return db.query(IRNRecord).filter(IRNRecord.id == irn_id).first()


def get_irns_by_organization(db: Session, organization_id: UUID, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[IRNRecord]:
    """
    Retrieve IRN records for a specific organization.
    
    Args:
        db: Database session
        organization_id: Organization ID
        skip: Records to skip
        limit: Maximum records to return
        status: Optional status filter
        
    Returns:
        List[IRNRecord]: List of IRN records
    """
    # Base query with organization filter
    # This assumes IRNRecord has a relationship to Organization through Integration
    query = db.query(IRNRecord).join(
        IRNRecord.integration
    ).filter(
        IRNRecord.integration.has(organization_id=organization_id)
    )
    
    # Add status filter if provided
    if status:
        query = query.filter(IRNRecord.status == status)
    
    # Apply pagination
    return query.order_by(IRNRecord.generated_at.desc()).offset(skip).limit(limit).all()


def validate_irn(db: Session, irn_value: str) -> Dict[str, Any]:
    """
    Validate an IRN.
    
    Args:
        db: Database session
        irn_value: IRN to validate
        
    Returns:
        Dict[str, Any]: Validation result with status and details
        
    """
    # Get the IRN record
    irn_record = get_irn_by_value(db, irn_value)
    
    # Check if IRN exists
    if not irn_record:
        return {
            "success": False,
            "message": "IRN not found",
            "details": {}
        }
    
    # Check if IRN has expired
    if irn_record.valid_until and irn_record.valid_until < datetime.now():
        return {
            "success": False,
            "message": "IRN has expired",
            "details": {
                "status": "expired",
                "invoice_number": irn_record.invoice_number,
                "valid_until": irn_record.valid_until.isoformat()
            }
        }
    
    # Check if IRN has been used
    if irn_record.status == "used":
        return {
            "success": True,
            "message": "IRN is valid but has been used",
            "details": {
                "status": "used",
                "invoice_number": irn_record.invoice_number,
                "used_at": irn_record.used_at.isoformat() if irn_record.used_at else None,
                "invoice_id": irn_record.invoice_id
            }
        }
    
    # IRN is valid and unused
    return {
        "success": True,
        "message": "IRN is valid and unused",
        "details": {
            "status": "unused",
            "invoice_number": irn_record.invoice_number,
            "valid_until": irn_record.valid_until.isoformat()
        }
    }
