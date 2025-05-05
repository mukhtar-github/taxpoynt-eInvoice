from typing import List # type: ignore
from uuid import UUID # type: ignore

from fastapi import APIRouter, Depends, HTTPException, status # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.session import get_db # type: ignore
from app.services.invoice_validation_service import validate_invoice
from app.schemas.invoice_validation import (
    InvoiceValidationRequest,
    InvoiceValidationResponse,
    BatchValidationRequest,
    BatchValidationResponse,
    ValidationError as ValidationIssue,
    ValidationRule,
    InvoiceValidationRequest as Invoice,  # Map the Invoice class to our new schema
)
from app.crud.crud_validation import validation_rule, validation_record

router = APIRouter()


@router.post("/invoice", response_model=InvoiceValidationResponse)
async def validate_invoice_endpoint(
    request: InvoiceValidationRequest,
    db: Session = Depends(get_db),
):
    """
    Validate a single invoice against FIRS requirements.
    
    This endpoint checks the following:
    - Schema validation (required fields, formats)
    - Business rule validation (calculations, IRN format)
    - FIRS compliance requirements
    
    Returns validation result with any issues found.
    """
    result = validate_invoice(request.invoice)

    # Record validation result for tracking
    if request.invoice.irn:
        integration_id = None  # In a real app, this would come from auth/context
        validation_record.create(
            db=db,
            obj_in={
                "irn": request.invoice.irn,
                "integration_id": integration_id,
                "is_valid": result.is_valid,
                "issue_count": len(result.issues),
                "error_count": len([i for i in result.issues if i.severity == "ERROR"]),
                "warning_count": len([i for i in result.issues if i.severity == "WARNING"])
            }
        )
    
    return result


@router.post("/invoices/batch", response_model=BatchValidationResponse)
async def validate_invoices(
    request: BatchValidationRequest,
    db: Session = Depends(get_db),
):
    """
    Validate multiple invoices in a batch.
    
    This is useful for validating a large number of invoices at once.
    Each invoice is validated independently.
    
    Returns validation results for all invoices and overall validation status.
    """
    
    results = []
    for i, invoice in enumerate(request.invoices):
        try:
            result = validate_invoice(invoice)
            results.append(result)
            
            # Record validation result if we have IRN
            if invoice.irn:
                integration_id = None  # In a real app, this would come from auth/context
                validation_record.create(
                    db=db,
                    obj_in={
                        "irn": invoice.irn,
                        "integration_id": integration_id,
                        "is_valid": result.is_valid,
                        "issue_count": len(result.issues),
                        "error_count": len([i for i in result.issues if i.severity == "ERROR"]),
                        "warning_count": len([i for i in result.issues if i.severity == "WARNING"])
                    }
                )
        except Exception as e:
            # Handle parsing errors for individual invoices
            results.append(
                InvoiceValidationResponse(
                    is_valid=False,
                    issues=[
                        ValidationIssue(
                            severity="ERROR",
                            field=f"invoices[{i}]",
                            message=f"Failed to validate invoice: {str(e)}",
                            code="VALIDATION_ERROR"
                        )
                    ]
                )
            )
    
    # Calculate overall batch status
    is_valid = all(r.is_valid for r in results)
    total_issues = sum(len(r.issues) for r in results)
    
    return BatchValidationResponse(
        is_valid=is_valid,
        total_issues=total_issues,
        results=results
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


@router.post("/test-validation", response_model=InvoiceValidationResponse)
async def test_validation(
    invoice: Invoice,  # Changed InvoiceValidationRequest to Invoice
    db: Session = Depends(get_db),
):
    """
    Test validation for an invoice without recording the result.
    
    This is useful for testing invoice data before creating a real invoice.
    """
    result = validate_invoice(invoice)
    return result