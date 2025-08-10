"""
FIRS Invoice Submission API Routes.

This module provides API endpoints for submitting invoices to FIRS:
- Single invoice submission
- Batch invoice submission
- UBL XML invoice submission
- Submission status checking
- Validation endpoints
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Body, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.services.firs_core.firs_api_client import firs_service, InvoiceSubmissionResponse, SubmissionStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/firs/submission",
    tags=["firs-submission"],
    responses={404: {"description": "Not found"}},
)


@router.post("/invoice", response_model=InvoiceSubmissionResponse)
async def submit_invoice(
    invoice_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Submit a single invoice to FIRS.
    
    This endpoint submits an invoice in FIRS-compliant JSON format.
    The invoice must follow the FIRS API specification.
    """
    logger.info(f"User {current_user.email} submitting invoice to FIRS")
    
    # Add user metadata
    invoice_data.setdefault("metadata", {}).update({
        "submitted_by": current_user.email,
        "organization_id": str(current_user.organization_id)
    })
    
    result = await firs_service.submit_invoice(invoice_data)
    
    # Log the submission attempt
    logger.info(
        f"Invoice submission result: success={result.success}, "
        f"submission_id={result.submission_id or 'N/A'}, "
        f"message={result.message}"
    )
    
    return result


@router.post("/batch", response_model=InvoiceSubmissionResponse)
async def submit_invoices_batch(
    invoices: List[Dict[str, Any]] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Submit multiple invoices in a batch to FIRS.
    
    This endpoint allows for efficient submission of multiple invoices
    in a single API call. Each invoice must follow the FIRS API specification.
    """
    logger.info(f"User {current_user.email} submitting batch of {len(invoices)} invoices to FIRS")
    
    # Add user metadata to each invoice
    for invoice in invoices:
        invoice.setdefault("metadata", {}).update({
            "submitted_by": current_user.email,
            "organization_id": str(current_user.organization_id)
        })
    
    result = await firs_service.submit_invoices_batch(invoices)
    
    # Log the batch submission attempt
    logger.info(
        f"Batch submission result: success={result.success}, "
        f"submission_id={result.submission_id or 'N/A'}, "
        f"message={result.message}, "
        f"invoice_count={len(invoices)}"
    )
    
    return result


@router.post("/ubl", response_model=InvoiceSubmissionResponse)
async def submit_ubl_invoice(
    ubl_file: UploadFile = File(...),
    invoice_type: str = Query("standard", description="Invoice type (standard, credit_note, debit_note, proforma, self_billed)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Submit a UBL format XML invoice to FIRS.
    
    This endpoint accepts UBL 2.1 XML files following the BIS Billing 3.0 standard.
    The endpoint is compatible with the Odoo UBL mapping system.
    """
    logger.info(f"User {current_user.email} submitting UBL invoice to FIRS")
    
    # Read the UBL file
    ubl_content = await ubl_file.read()
    
    # Decode bytes to string if needed
    if isinstance(ubl_content, bytes):
        ubl_content = ubl_content.decode("utf-8")
    
    # Validate invoice type
    valid_types = ["standard", "credit_note", "debit_note", "proforma", "self_billed"]
    if invoice_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid invoice type. Must be one of: {', '.join(valid_types)}"
        )
    
    result = await firs_service.submit_ubl_invoice(ubl_content, invoice_type)
    
    # Log the UBL submission attempt
    logger.info(
        f"UBL invoice submission result: success={result.success}, "
        f"submission_id={result.submission_id or 'N/A'}, "
        f"message={result.message}, "
        f"invoice_type={invoice_type}"
    )
    
    return result


@router.post("/ubl/validate", response_model=InvoiceSubmissionResponse)
async def validate_ubl_invoice(
    ubl_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Validate a UBL format XML invoice against FIRS requirements.
    
    This endpoint checks if the UBL document meets FIRS validation rules
    without actually submitting it to FIRS.
    """
    logger.info(f"User {current_user.email} validating UBL invoice against FIRS requirements")
    
    # Read the UBL file
    ubl_content = await ubl_file.read()
    
    # Decode bytes to string if needed
    if isinstance(ubl_content, bytes):
        ubl_content = ubl_content.decode("utf-8")
    
    result = await firs_service.validate_ubl_invoice(ubl_content)
    
    # Log the validation attempt
    logger.info(
        f"UBL validation result: success={result.success}, "
        f"message={result.message}"
    )
    
    return result


@router.get("/status/{submission_id}", response_model=SubmissionStatus)
async def check_submission_status(
    submission_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Check the status of a previously submitted invoice.
    
    This endpoint retrieves the current status of an invoice submission
    from the FIRS API using the submission ID.
    """
    logger.info(f"User {current_user.email} checking submission status for {submission_id}")
    
    try:
        result = await firs_service.check_submission_status(submission_id)
        
        # Log the status check
        logger.info(
            f"Submission status check: submission_id={submission_id}, "
            f"status={result.status}, "
            f"message={result.message or 'No message'}"
        )
        
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error checking submission status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check submission status: {str(e)}"
        )
