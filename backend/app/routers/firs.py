"""
FIRS API Submission Router.

This module provides endpoints for submitting invoices to the FIRS API
using the BIS Billing 3.0 UBL format.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging
import json

from app.services.firs_service import firs_service, InvoiceSubmissionResponse, SubmissionStatus
from app.services.odoo_ubl_transformer import odoo_ubl_transformer
from app.schemas.invoice_validation import InvoiceValidationRequest
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/firs",
    tags=["FIRS e-Invoice"],
    responses={404: {"description": "Not found"}},
)


class OdooInvoiceSubmitRequest(BaseModel):
    """Request model for submitting an Odoo invoice to FIRS."""
    odoo_invoice: Dict[str, Any] = Field(..., description="Odoo invoice data")
    company_info: Dict[str, Any] = Field(..., description="Company information for the supplier")
    sandbox_mode: Optional[bool] = Field(None, description="Override sandbox mode setting")


class SubmissionResponse(BaseModel):
    """Response model for invoice submission."""
    success: bool = Field(..., description="Whether the submission was successful")
    message: str = Field(..., description="Status message")
    submission_id: Optional[str] = Field(None, description="Submission ID for tracking")
    validation_issues: List[Dict[str, str]] = Field([], description="Validation issues if any")
    firs_response: Optional[Dict[str, Any]] = Field(None, description="Raw FIRS API response details")


@router.post("/submit-invoice", response_model=SubmissionResponse)
async def submit_odoo_invoice(
    request: OdooInvoiceSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> SubmissionResponse:
    """
    Submit an Odoo invoice to FIRS API.
    
    This endpoint:
    1. Transforms Odoo invoice data to BIS Billing 3.0 UBL format
    2. Validates the transformation
    3. Submits to FIRS API
    4. Returns the submission status
    
    If configured, a background task will track the submission status.
    """
    logger.info(f"Processing Odoo invoice submission request from user {current_user.email}")
    
    try:
        # Transform Odoo invoice to UBL format
        ubl_invoice_obj, validation_issues = odoo_ubl_transformer.odoo_to_ubl_object(
            request.odoo_invoice, 
            request.company_info
        )
        
        # If there are validation issues, return them without submitting
        if validation_issues and not ubl_invoice_obj:
            logger.warning(f"Validation issues prevented FIRS submission: {json.dumps(validation_issues)}")
            return SubmissionResponse(
                success=False,
                message="Invoice validation failed. Please fix the issues and try again.",
                validation_issues=validation_issues
            )
        
        # Convert UBL object to FIRS-compatible format
        firs_invoice_data = ubl_invoice_obj.dict() if ubl_invoice_obj else {}
        
        # If sandbox_mode is specified in the request, use it to override the service setting
        use_sandbox = request.sandbox_mode if request.sandbox_mode is not None else None
        
        # Create a service instance with the appropriate sandbox setting if needed
        service = firs_service
        if use_sandbox is not None and use_sandbox != firs_service.use_sandbox:
            logger.info(f"Using override sandbox mode: {use_sandbox}")
            # Create a new service instance with the specified sandbox mode
            from app.core.config import settings
            service = type(firs_service)(
                use_sandbox=use_sandbox,
                base_url=settings.FIRS_SANDBOX_API_URL if use_sandbox else settings.FIRS_API_URL
            )
        
        # Submit to FIRS API
        submission_result = await service.submit_invoice(firs_invoice_data)
        
        # If submission was successful, add background task to check status
        if submission_result.success and submission_result.submission_id:
            background_tasks.add_task(
                track_submission_status,
                submission_result.submission_id,
                current_user.id,
                use_sandbox
            )
        
        return SubmissionResponse(
            success=submission_result.success,
            message=submission_result.message,
            submission_id=submission_result.submission_id,
            validation_issues=validation_issues,
            firs_response=submission_result.details
        )
        
    except Exception as e:
        logger.error(f"Error during FIRS submission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FIRS submission failed: {str(e)}"
        )


@router.get("/submission-status/{submission_id}", response_model=Dict[str, Any])
async def check_submission_status(
    submission_id: str,
    use_sandbox: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check the status of a FIRS invoice submission.
    
    Args:
        submission_id: The submission ID to check
        use_sandbox: Override sandbox setting
        current_user: Authenticated user
    
    Returns:
        Status details of the submission
    """
    try:
        # Create a service instance with the appropriate sandbox setting if needed
        service = firs_service
        if use_sandbox is not None and use_sandbox != firs_service.use_sandbox:
            logger.info(f"Using override sandbox mode for status check: {use_sandbox}")
            # Create a new service instance with the specified sandbox mode
            from app.core.config import settings
            service = type(firs_service)(
                use_sandbox=use_sandbox,
                base_url=settings.FIRS_SANDBOX_API_URL if use_sandbox else settings.FIRS_API_URL
            )
        
        # Get status from the service
        status_result = await service.check_submission_status(submission_id)
        
        return {
            "submission_id": status_result.submission_id,
            "status": status_result.status,
            "timestamp": status_result.timestamp,
            "message": status_result.message,
            "details": status_result.details
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error checking submission status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )


@router.post("/batch-submit", response_model=SubmissionResponse)
async def submit_invoice_batch(
    invoices: List[OdooInvoiceSubmitRequest],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> SubmissionResponse:
    """
    Submit a batch of Odoo invoices to FIRS API.
    
    This endpoint transforms multiple Odoo invoices to UBL format and submits them
    as a batch to the FIRS API.
    """
    logger.info(f"Processing batch submission request for {len(invoices)} invoices")
    
    try:
        # Process each invoice in the batch
        firs_invoices = []
        all_validation_issues = []
        
        for idx, invoice_req in enumerate(invoices):
            # Transform Odoo invoice to UBL format
            ubl_invoice_obj, validation_issues = odoo_ubl_transformer.odoo_to_ubl_object(
                invoice_req.odoo_invoice, 
                invoice_req.company_info
            )
            
            # Track validation issues with invoice index
            if validation_issues:
                for issue in validation_issues:
                    issue["invoice_index"] = idx
                all_validation_issues.extend(validation_issues)
            
            # Add valid invoices to the batch
            if ubl_invoice_obj:
                firs_invoices.append(ubl_invoice_obj.dict())
        
        # If no valid invoices were found, return with validation issues
        if not firs_invoices:
            return SubmissionResponse(
                success=False,
                message="No valid invoices to submit. Please fix the validation issues.",
                validation_issues=all_validation_issues
            )
        
        # Determine sandbox mode (use the mode from the first invoice)
        use_sandbox = invoices[0].sandbox_mode if invoices[0].sandbox_mode is not None else None
        
        # Create a service instance with the appropriate sandbox setting if needed
        service = firs_service
        if use_sandbox is not None and use_sandbox != firs_service.use_sandbox:
            logger.info(f"Using override sandbox mode for batch: {use_sandbox}")
            # Create a new service instance with the specified sandbox mode
            from app.core.config import settings
            service = type(firs_service)(
                use_sandbox=use_sandbox,
                base_url=settings.FIRS_SANDBOX_API_URL if use_sandbox else settings.FIRS_API_URL
            )
        
        # Submit the batch to FIRS API
        submission_result = await service.submit_invoices_batch(firs_invoices)
        
        # If submission was successful, add background task to check status
        if submission_result.success and submission_result.submission_id:
            background_tasks.add_task(
                track_submission_status,
                submission_result.submission_id,
                current_user.id,
                use_sandbox
            )
        
        return SubmissionResponse(
            success=submission_result.success,
            message=submission_result.message,
            submission_id=submission_result.submission_id,
            validation_issues=all_validation_issues,
            firs_response=submission_result.details
        )
        
    except Exception as e:
        logger.error(f"Error during FIRS batch submission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FIRS batch submission failed: {str(e)}"
        )


async def track_submission_status(submission_id: str, user_id: str, use_sandbox: Optional[bool] = None):
    """
    Background task to track submission status.
    
    This function will periodically check the submission status and update
    the database with the latest status.
    """
    try:
        logger.info(f"Starting background status tracking for submission {submission_id}")
        
        # Create a service instance with the appropriate sandbox setting if needed
        service = firs_service
        if use_sandbox is not None and use_sandbox != firs_service.use_sandbox:
            # Create a new service instance with the specified sandbox mode
            from app.core.config import settings
            service = type(firs_service)(
                use_sandbox=use_sandbox,
                base_url=settings.FIRS_SANDBOX_API_URL if use_sandbox else settings.FIRS_API_URL
            )
        
        # Check initial status
        status = await service.check_submission_status(submission_id)
        
        # TODO: Store status in database for record-keeping
        logger.info(f"Submission {submission_id} status: {status.status}")
        
        # Additional status tracking could be implemented here
        # with periodic checks and notifications
        
    except Exception as e:
        logger.error(f"Error tracking submission status: {str(e)}", exc_info=True)
