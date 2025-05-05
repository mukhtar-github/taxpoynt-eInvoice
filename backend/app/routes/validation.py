"""
API endpoints for invoice validation against BIS Billing 3.0 UBL schema and FIRS requirements.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.invoice_validation import (
    InvoiceValidationRequest,
    InvoiceValidationResponse,
    BatchValidationRequest,
    BatchValidationResponse,
    ValidationRule,
    ValidationRulesList
)
from app.services.invoice_validation_service import (
    validate_invoice,
    validate_invoice_batch,
    get_validation_rules
)

router = APIRouter(prefix="/validate", tags=["validation"])


@router.post("/invoice", response_model=InvoiceValidationResponse)
async def validate_single_invoice(
    invoice: InvoiceValidationRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate a single invoice against BIS Billing 3.0 UBL schema and FIRS requirements.
    
    This endpoint checks invoice data for compliance with:
    - BIS Billing 3.0 structural requirements
    - FIRS Nigeria tax rules and requirements
    - Standard invoice calculation validations
    
    Returns a detailed validation report with any errors or warnings.
    """
    try:
        validation_result = validate_invoice(invoice)
        return validation_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation service error: {str(e)}"
        )


@router.post("/invoices", response_model=BatchValidationResponse)
async def validate_invoice_batch_endpoint(
    batch_request: BatchValidationRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validate a batch of invoices in a single request.
    
    This endpoint allows validating multiple invoices at once,
    which is more efficient for bulk operations.
    
    Returns a detailed validation report for each invoice in the batch.
    """
    try:
        if len(batch_request.invoices) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size exceeded. Maximum 100 invoices per request."
            )
            
        validation_result = validate_invoice_batch(batch_request)
        return validation_result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch validation error: {str(e)}"
        )


@router.get("/rules", response_model=ValidationRulesList)
async def get_validation_rules_endpoint(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all available validation rules.
    
    This endpoint returns the complete list of validation rules used in the system,
    including their severity (error/warning) and source (BIS3/FIRS/custom).
    """
    try:
        rules = get_validation_rules()
        return ValidationRulesList(
            rules=rules,
            count=len(rules)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving validation rules: {str(e)}"
        )


@router.post("/test", response_model=InvoiceValidationResponse)
async def test_invoice_validation(
    invoice: InvoiceValidationRequest,
    rule_ids: List[str] = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Test an invoice against specific validation rules.
    
    This endpoint allows testing invoice data against a subset of validation rules
    specified by their rule IDs. If no rule IDs are provided, all rules are applied.
    
    This is useful for testing during development or for troubleshooting specific issues.
    """
    try:
        # For now, we'll just use the standard validation since we haven't
        # implemented rule filtering yet.
        # In a full implementation, this would filter rules by the provided rule_ids
        validation_result = validate_invoice(invoice)
        return validation_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test validation error: {str(e)}"
        )
