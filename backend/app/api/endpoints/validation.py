from typing import List # type: ignore
from uuid import UUID # type: ignore

from fastapi import APIRouter, Depends, HTTPException, status # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.session import get_db # type: ignore
from app.services.validation_service import validation_service
from app.schemas.validation import (
    Invoice,
    InvoiceValidationRequest,
    InvoiceValidationResponse,
    BatchValidationRequest,
    BatchValidationResponse,
    ValidationIssue,
    ValidationRule,
)
from app.crud.crud_validation import validation_rule, validation_record


router = APIRouter()


@router.post("/validate/invoice", response_model=InvoiceValidationResponse, status_code=status.HTTP_200_OK)
def validate_invoice(
    request: InvoiceValidationRequest,
    db: Session = Depends(get_db),
) -> InvoiceValidationResponse:
    """
    Validate a single invoice against FIRS requirements.
    
    This endpoint checks the following:
    - Schema validation (required fields, formats)
    - Business rule validation (calculations, IRN format)
    - FIRS compliance requirements
    
    Returns validation result with any issues found.
    """
    result = validation_service.validate_invoice(request.invoice)

    # Record validation result for tracking
    if request.invoice.irn:
        integration_id = None  # In a real app, this would come from auth/context
        validation_record.create(
            db=db,
            obj_in={
                "integration_id": integration_id or UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
                "irn": request.invoice.irn,
                "invoice_data": request.invoice.dict(),
                "is_valid": result.is_valid,
                "issues": [issue.dict() for issue in result.issues] if result.issues else None,
            },
        )

    return InvoiceValidationResponse(
        is_valid=result.is_valid,
        validation_issues=result.issues,
    )


@router.post("/validate/invoices", response_model=BatchValidationResponse, status_code=status.HTTP_200_OK)
def validate_invoices(
    request: BatchValidationRequest,
    db: Session = Depends(get_db),
) -> BatchValidationResponse:
    """
    Validate multiple invoices in a batch.
    
    This is useful for validating a large number of invoices at once.
    Each invoice is validated independently.
    
    Returns validation results for all invoices and overall validation status.
    """
    results = []
    overall_valid = True
    
    for invoice in request.invoices:
        result = validation_service.validate_invoice(invoice)
        
        # Record validation result
        if invoice.irn:
            integration_id = None  # In a real app, this would come from auth/context
            validation_record.create(
                db=db,
                obj_in={
                    "integration_id": integration_id or UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
                    "irn": invoice.irn,
                    "invoice_data": invoice.dict(),
                    "is_valid": result.is_valid,
                    "issues": [issue.dict() for issue in result.issues] if result.issues else None,
                },
            )
        
        results.append(
            InvoiceValidationResponse(
                is_valid=result.is_valid,
                validation_issues=result.issues,
            )
        )
        
        if not result.is_valid:
            overall_valid = False
    
    return BatchValidationResponse(
        results=results,
        overall_valid=overall_valid,
    )


@router.get("/validation/rules", response_model=List[ValidationRule])
def get_validation_rules(
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = True,
    db: Session = Depends(get_db),
) -> List[ValidationRule]:
    """
    Get list of validation rules currently active in the system.
    
    These are the rules that invoices are validated against.
    Rules can be active or inactive.
    """
    rules = validation_rule.get_multi(db=db, skip=skip, limit=limit, active_only=active_only)
    return rules


@router.post("/validation/test", response_model=InvoiceValidationResponse)
def test_validation(
    invoice: Invoice,
    db: Session = Depends(get_db),
) -> InvoiceValidationResponse:
    """
    Test validation for an invoice without recording the result.
    
    This is useful for testing invoice data before creating a real invoice.
    """
    result = validation_service.validate_invoice(invoice)
    
    return InvoiceValidationResponse(
        is_valid=result.is_valid,
        validation_issues=result.issues,
    ) 