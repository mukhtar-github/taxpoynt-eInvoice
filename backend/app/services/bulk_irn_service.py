"""
Bulk IRN generation service for TaxPoynt eInvoice.

This module provides functions for bulk generation of Invoice Reference Numbers (IRNs),
including job tracking, batch processing, and error handling.
"""
import uuid
import hashlib
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from app.models.irn import IRNRecord, InvoiceData, IRNStatus, IRNValidationRecord
from app.schemas.irn import IRNBatchGenerateRequest
from app.services.irn_service import generate_irn, get_irn_expiration_date, create_validation_record
from app.cache.irn_cache import IRNCache
from app.core.config import settings

logger = logging.getLogger(__name__)


class BulkIRNJob:
    """
    Class to manage bulk IRN generation jobs.
    
    This class maintains the state of a bulk IRN generation job and provides
    methods to update the job status and retrieve results.
    """
    def __init__(self, batch_id: str, total_invoices: int):
        self.batch_id = batch_id
        self.total = total_invoices
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.status = "in_progress"
        self.successful_irns = []
        self.failed_invoices = []
        
        # Cache initial status
        self._cache_status()
        
    def update_status(self, success: bool, irn_data: Optional[Dict[str, Any]] = None, 
                     error_data: Optional[Dict[str, Any]] = None) -> None:
        """Update job status with a new result."""
        self.completed += 1
        
        if success:
            self.successful += 1
            if irn_data:
                self.successful_irns.append(irn_data)
        else:
            self.failed += 1
            if error_data:
                self.failed_invoices.append(error_data)
        
        # Update the cache periodically
        if self.completed % 10 == 0 or self.completed == self.total:
            self._cache_status()
            
        # Check if job is complete
        if self.completed == self.total:
            self.completed_at = datetime.utcnow()
            self.status = "completed"
            self._cache_status()
            
    def _cache_status(self) -> None:
        """Cache the current job status."""
        status_data = {
            "batch_id": self.batch_id,
            "total": self.total,
            "completed": self.completed,
            "successful": self.successful,
            "failed": self.failed,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            # Only include summary counts, not all details, to keep cache size reasonable
            "successful_count": len(self.successful_irns),
            "failed_count": len(self.failed_invoices)
        }
        IRNCache.cache_bulk_irn_status(self.batch_id, status_data)
        
    def get_results(self) -> Dict[str, Any]:
        """Get complete results of the job."""
        return {
            "batch_id": self.batch_id,
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "irns": self.successful_irns,
            "failed_invoices": self.failed_invoices
        }


async def process_bulk_irn_job(
    db: Session,
    batch_request: IRNBatchGenerateRequest,
    user_id: Optional[uuid.UUID] = None,
    organization_id: Optional[uuid.UUID] = None
) -> str:
    """
    Start a background job to process a bulk IRN generation request.
    
    Args:
        db: Database session
        batch_request: Batch generation request with multiple invoice numbers
        user_id: ID of the user generating the IRNs
        organization_id: ID of the organization
        
    Returns:
        Batch ID for tracking the job
    """
    # Generate a batch ID
    batch_id = str(uuid.uuid4())
    
    # Log job start
    logger.info(f"Starting bulk IRN generation for batch {batch_id} with {len(batch_request.invoice_numbers)} invoices")
    
    # Create a job tracker
    job = BulkIRNJob(batch_id, len(batch_request.invoice_numbers))
    
    # Create timestamp if not provided
    timestamp = batch_request.timestamp
    if not timestamp:
        timestamp = datetime.utcnow().strftime("%Y%m%d")
    
    # Process each invoice number asynchronously
    for invoice_number in batch_request.invoice_numbers:
        try:
            # Generate basic invoice data
            invoice_data = {
                "invoice_number": invoice_number,
                "timestamp": timestamp,
                "integration_id": str(batch_request.integration_id)
            }
            
            # Generate IRN
            irn_value, verification_code, hash_value = generate_irn(invoice_data)
            
            # Create expiration date
            valid_until = get_irn_expiration_date()
            
            # Create IRN record
            irn_record = IRNRecord(
                irn=irn_value,
                integration_id=str(batch_request.integration_id),
                invoice_number=invoice_number,
                service_id=getattr(settings, "IRN_SERVICE_ID", "TAXPOINT"),
                timestamp=timestamp,
                generated_at=datetime.utcnow(),
                valid_until=valid_until,
                status=IRNStatus.UNUSED,
                hash_value=hash_value,
                verification_code=verification_code,
                issued_by=user_id
            )
            
            # Add to database
            db.add(irn_record)
            db.flush()
            
            # Cache the IRN
            IRNCache.cache_irn(irn_record)
            
            # Update job status
            job.update_status(
                success=True,
                irn_data={
                    "irn": irn_value,
                    "invoice_number": invoice_number,
                    "service_id": irn_record.service_id,
                    "timestamp": timestamp,
                    "generated_at": irn_record.generated_at.isoformat(),
                    "valid_until": irn_record.valid_until.isoformat(),
                    "status": irn_record.status.value
                }
            )
            
            # Small delay to prevent database overload
            await asyncio.sleep(0.01)
            
        except Exception as e:
            logger.error(f"Error generating IRN for invoice {invoice_number}: {str(e)}")
            
            # Update job status with error
            job.update_status(
                success=False,
                error_data={
                    "invoice_number": invoice_number,
                    "error": str(e)
                }
            )
    
    # Commit all changes
    db.commit()
    
    # Return the batch ID
    return batch_id


def start_bulk_irn_generation(
    background_tasks: BackgroundTasks,
    db: Session,
    batch_request: IRNBatchGenerateRequest,
    user_id: Optional[uuid.UUID] = None,
    organization_id: Optional[uuid.UUID] = None
) -> str:
    """
    Start a background task for bulk IRN generation.
    
    Args:
        background_tasks: FastAPI background tasks
        db: Database session
        batch_request: Batch generation request with multiple invoice numbers
        user_id: ID of the user generating the IRNs
        organization_id: ID of the organization
        
    Returns:
        Batch ID for tracking
    """
    # Generate a batch ID
    batch_id = str(uuid.uuid4())
    
    # Add the task to background tasks
    background_tasks.add_task(
        process_bulk_irn_job,
        db,
        batch_request,
        user_id,
        organization_id
    )
    
    # Initialize tracking in cache
    batch_status = {
        "batch_id": batch_id,
        "total": len(batch_request.invoice_numbers),
        "completed": 0,
        "successful": 0,
        "failed": 0,
        "status": "starting",
        "started_at": datetime.utcnow().isoformat()
    }
    IRNCache.cache_bulk_irn_status(batch_id, batch_status)
    
    return batch_id


def get_bulk_generation_status(batch_id: str) -> Dict[str, Any]:
    """
    Get the status of a bulk IRN generation job.
    
    Args:
        batch_id: Batch ID to query
        
    Returns:
        Status information
    """
    status = IRNCache.get_bulk_irn_status(batch_id)
    
    if not status:
        return {
            "batch_id": batch_id,
            "status": "not_found",
            "message": "Batch ID not found or status expired from cache"
        }
    
    return status


async def validate_multiple_irns(
    db: Session,
    irn_values: List[str],
    user_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Validate multiple IRNs in a single batch operation.
    
    Args:
        db: Database session
        irn_values: List of IRNs to validate
        user_id: ID of the user performing validation
        
    Returns:
        Dictionary with validation results
    """
    results = []
    
    for irn_value in irn_values:
        try:
            # First check cache
            cached_irn = IRNCache.get_cached_irn(irn_value)
            
            # If not in cache, get from database
            if not cached_irn:
                irn_record = db.query(IRNRecord).filter(IRNRecord.irn == irn_value).first()
                
                if not irn_record:
                    result = {
                        "irn": irn_value,
                        "is_valid": False,
                        "message": "IRN not found"
                    }
                else:
                    # Check status
                    is_valid = irn_record.status == IRNStatus.ACTIVE
                    message = f"IRN is {irn_record.status.value}"
                    
                    # Check expiration
                    if is_valid and datetime.utcnow() > irn_record.valid_until:
                        is_valid = False
                        message = "IRN has expired"
                        irn_record.status = IRNStatus.EXPIRED
                        db.add(irn_record)
                    
                    result = {
                        "irn": irn_value,
                        "is_valid": is_valid,
                        "message": message,
                        "details": {
                            "invoice_number": irn_record.invoice_number,
                            "status": irn_record.status.value,
                            "valid_until": irn_record.valid_until.isoformat()
                        }
                    }
                    
                    # Add to cache for future lookups
                    IRNCache.cache_irn(irn_record)
            else:
                # Use cached data
                is_valid = cached_irn["status"] == IRNStatus.ACTIVE.value
                message = f"IRN is {cached_irn['status']}"
                
                # Check expiration
                valid_until = datetime.fromisoformat(cached_irn["valid_until"]) if cached_irn.get("valid_until") else None
                if is_valid and valid_until and datetime.utcnow() > valid_until:
                    is_valid = False
                    message = "IRN has expired"
                    
                    # Update database status
                    irn_record = db.query(IRNRecord).filter(IRNRecord.irn == irn_value).first()
                    if irn_record:
                        irn_record.status = IRNStatus.EXPIRED
                        db.add(irn_record)
                        
                        # Update cache
                        cached_irn["status"] = IRNStatus.EXPIRED.value
                        IRNCache.cache_irn(irn_record)
                
                result = {
                    "irn": irn_value,
                    "is_valid": is_valid,
                    "message": message,
                    "details": {
                        "invoice_number": cached_irn.get("invoice_number"),
                        "status": cached_irn.get("status"),
                        "valid_until": cached_irn.get("valid_until")
                    }
                }
            
            # Create validation record
            create_validation_record(
                db,
                irn_value,
                result["is_valid"],
                result["message"],
                str(user_id) if user_id else None,
                "batch_validation"
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error validating IRN {irn_value}: {str(e)}")
            results.append({
                "irn": irn_value,
                "is_valid": False,
                "message": f"Error during validation: {str(e)}"
            })
    
    # Commit database changes
    db.commit()
    
    return {
        "total": len(irn_values),
        "validated": len(results),
        "results": results
    }
