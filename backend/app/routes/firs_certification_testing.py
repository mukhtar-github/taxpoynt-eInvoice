"""
FIRS Certification Testing API Routes

This module provides comprehensive testing endpoints for FIRS certification,
allowing complete testing of the invoice lifecycle and all FIRS integration points.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import date

from app.db.session import get_db
from app.services.firs_invoice_processor import firs_invoice_processor, firs_error_handler
from app.services.firs_certification_service import firs_certification_service
from app.dependencies.auth import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/firs-certification",
    tags=["firs-certification-testing"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models for request/response validation
class CustomerData(BaseModel):
    party_name: str = Field(..., description="Customer/buyer company name")
    tin: str = Field(..., description="Customer TIN number")
    email: str = Field(..., description="Customer email address")
    telephone: Optional[str] = Field(None, description="Customer phone number (with +234)")
    business_description: Optional[str] = Field(None, description="Customer business description")
    postal_address: Optional[Dict[str, str]] = Field(None, description="Customer postal address")


class InvoiceLineItem(BaseModel):
    hsn_code: Optional[str] = Field("CC-001", description="HSN/service code")
    product_category: Optional[str] = Field("Technology Services", description="Product category")
    invoiced_quantity: int = Field(..., description="Quantity of items")
    line_extension_amount: float = Field(..., description="Line total amount")
    item: Dict[str, str] = Field(..., description="Item details (name, description)")
    price: Dict[str, Any] = Field(..., description="Price details")


class CompleteInvoiceTestRequest(BaseModel):
    invoice_reference: str = Field(..., description="Unique invoice reference")
    customer_data: CustomerData = Field(..., description="Customer information")
    invoice_lines: List[InvoiceLineItem] = Field(..., description="Invoice line items")
    issue_date: Optional[date] = Field(None, description="Invoice issue date")
    due_date: Optional[date] = Field(None, description="Invoice due date")
    note: Optional[str] = Field(None, description="Invoice notes")
    payment_status: Optional[str] = Field("PENDING", description="Payment status")


class TINVerificationRequest(BaseModel):
    tin: str = Field(..., description="TIN number to verify")


class PartyCreationRequest(BaseModel):
    party_name: str = Field(..., description="Party name")
    tin: str = Field(..., description="Party TIN")
    email: str = Field(..., description="Party email")
    telephone: Optional[str] = Field(None, description="Party phone number")
    business_description: Optional[str] = Field(None, description="Business description")
    postal_address: Optional[Dict[str, str]] = Field(None, description="Postal address")


@router.get("/health-check")
async def test_firs_health_check():
    """
    Test FIRS API connectivity and health.
    
    This endpoint verifies that the FIRS sandbox environment is accessible
    and properly configured for certification testing.
    """
    try:
        result = await firs_invoice_processor.test_firs_connectivity()
        return firs_error_handler.handle_firs_response({"code": 200, "data": result})
    except Exception as e:
        logger.error(f"FIRS health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.post("/process-complete-invoice")
async def test_complete_invoice_processing(
    request: CompleteInvoiceTestRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Test complete invoice processing lifecycle for FIRS certification.
    
    This endpoint processes a complete invoice through all FIRS stages:
    1. Build invoice structure
    2. Validate IRN
    3. Validate complete invoice
    4. Sign invoice
    5. Transmit invoice
    6. Confirm invoice
    7. Download invoice
    """
    try:
        logger.info(f"Processing complete invoice test for: {request.invoice_reference}")
        
        # Convert Pydantic models to dictionaries
        customer_data = request.customer_data.dict()
        invoice_lines = [line.dict() for line in request.invoice_lines]
        
        # Process complete lifecycle
        results = await firs_invoice_processor.process_complete_invoice_lifecycle(
            invoice_reference=request.invoice_reference,
            customer_data=customer_data,
            invoice_lines=invoice_lines,
            issue_date=request.issue_date,
            due_date=request.due_date,
            note=request.note,
            payment_status=request.payment_status
        )
        
        return firs_error_handler.handle_firs_response({"code": 200, "data": results})
        
    except Exception as e:
        logger.error(f"Complete invoice processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invoice processing failed: {str(e)}"
        )


@router.post("/validate-irn")
async def test_irn_validation(
    invoice_reference: str,
    current_user: Any = Depends(get_current_user)
):
    """
    Test IRN validation with FIRS.
    
    This endpoint tests the IRN format validation process
    using the FIRS template requirements.
    """
    try:
        # Generate IRN using the service
        irn = firs_certification_service.generate_irn(invoice_reference)
        
        # Validate IRN
        result = await firs_certification_service.validate_irn(
            business_id=firs_certification_service.business_id,
            invoice_reference=invoice_reference,
            irn=irn
        )
        
        return firs_error_handler.handle_firs_response(result)
        
    except Exception as e:
        logger.error(f"IRN validation test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IRN validation failed: {str(e)}"
        )


@router.post("/verify-tin")
async def test_tin_verification(
    request: TINVerificationRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Test TIN verification with FIRS.
    
    This endpoint tests the TIN verification functionality
    against the FIRS database.
    """
    try:
        result = await firs_certification_service.verify_tin(request.tin)
        return firs_error_handler.handle_firs_response(result)
        
    except Exception as e:
        logger.error(f"TIN verification test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TIN verification failed: {str(e)}"
        )


@router.post("/create-party")
async def test_party_creation(
    request: PartyCreationRequest,
    current_user: Any = Depends(get_current_user)
):
    """
    Test party creation in FIRS.
    
    This endpoint tests creating a new party (customer/supplier)
    in the FIRS system for invoice processing.
    """
    try:
        party_data = request.dict(exclude_none=True)
        result = await firs_certification_service.create_party(party_data)
        return firs_error_handler.handle_firs_response(result)
        
    except Exception as e:
        logger.error(f"Party creation test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Party creation failed: {str(e)}"
        )


@router.get("/search-parties")
async def test_party_search(
    page: int = 1,
    size: int = 10,
    current_user: Any = Depends(get_current_user)
):
    """
    Test party search functionality.
    
    This endpoint tests searching for existing parties
    in the FIRS system.
    """
    try:
        result = await firs_certification_service.search_parties(page=page, size=size)
        return firs_error_handler.handle_firs_response(result)
        
    except Exception as e:
        logger.error(f"Party search test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Party search failed: {str(e)}"
        )


@router.get("/resources/countries")
async def get_countries_resource():
    """Get available countries from FIRS."""
    try:
        result = await firs_certification_service.get_countries()
        return firs_error_handler.handle_firs_response(result)
    except Exception as e:
        logger.error(f"Countries fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch countries: {str(e)}"
        )


@router.get("/resources/invoice-types")
async def get_invoice_types_resource():
    """Get available invoice types from FIRS."""
    try:
        result = await firs_certification_service.get_invoice_types()
        return firs_error_handler.handle_firs_response(result)
    except Exception as e:
        logger.error(f"Invoice types fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch invoice types: {str(e)}"
        )


@router.get("/resources/currencies")
async def get_currencies_resource():
    """Get available currencies from FIRS."""
    try:
        result = await firs_certification_service.get_currencies()
        return firs_error_handler.handle_firs_response(result)
    except Exception as e:
        logger.error(f"Currencies fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch currencies: {str(e)}"
        )


@router.get("/resources/vat-exemptions")
async def get_vat_exemptions_resource():
    """Get VAT exemption codes from FIRS."""
    try:
        result = await firs_certification_service.get_vat_exemptions()
        return firs_error_handler.handle_firs_response(result)
    except Exception as e:
        logger.error(f"VAT exemptions fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch VAT exemptions: {str(e)}"
        )


@router.get("/resources/service-codes")
async def get_service_codes_resource():
    """Get service codes from FIRS."""
    try:
        result = await firs_certification_service.get_service_codes()
        return firs_error_handler.handle_firs_response(result)
    except Exception as e:
        logger.error(f"Service codes fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch service codes: {str(e)}"
        )


@router.get("/resources/all")
async def get_all_resources():
    """
    Get all invoice resources from FIRS.
    
    This endpoint fetches all required resources for invoice creation
    including countries, currencies, invoice types, VAT exemptions, and service codes.
    """
    try:
        result = await firs_invoice_processor.get_invoice_resources()
        return firs_error_handler.handle_firs_response({"code": 200, "data": result})
    except Exception as e:
        logger.error(f"All resources fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch resources: {str(e)}"
        )


@router.get("/configuration")
async def get_certification_configuration():
    """
    Get FIRS certification configuration details.
    
    This endpoint returns the current configuration used for
    certification testing including sandbox credentials and endpoints.
    """
    try:
        config = {
            "sandbox_environment": {
                "base_url": firs_certification_service.sandbox_base_url,
                "business_id": firs_certification_service.business_id,
                "supplier_party_id": firs_certification_service.test_supplier_party_id,
                "supplier_address_id": firs_certification_service.test_supplier_address_id,
            },
            "irn_template": "{{invoice_id}}-59854B81-{{YYYYMMDD}}",
            "supported_features": [
                "IRN Validation",
                "Invoice Validation", 
                "Invoice Signing",
                "Invoice Transmission",
                "Invoice Confirmation",
                "Invoice Download",
                "Party Management",
                "TIN Verification",
                "Resource Data Access"
            ],
            "certification_status": "ready"
        }
        
        return firs_error_handler.handle_firs_response({"code": 200, "data": config})
        
    except Exception as e:
        logger.error(f"Configuration fetch failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch configuration: {str(e)}"
        )


@router.post("/test-individual-step")
async def test_individual_processing_step(
    step: str,
    irn: Optional[str] = None,
    invoice_data: Optional[Dict[str, Any]] = None,
    current_user: Any = Depends(get_current_user)
):
    """
    Test individual invoice processing steps.
    
    This endpoint allows testing specific steps of the invoice lifecycle
    independently for debugging and certification verification.
    
    Supported steps:
    - validate_irn: Test IRN validation
    - validate_invoice: Test complete invoice validation
    - sign_invoice: Test invoice signing
    - transmit_invoice: Test invoice transmission
    - confirm_invoice: Test invoice confirmation
    - download_invoice: Test invoice download
    """
    try:
        if step == "validate_irn" and irn:
            result = await firs_certification_service.validate_irn(
                business_id=firs_certification_service.business_id,
                invoice_reference=irn.split('-')[0],
                irn=irn
            )
        elif step == "validate_invoice" and invoice_data:
            result = await firs_certification_service.validate_complete_invoice(invoice_data)
        elif step == "sign_invoice" and invoice_data:
            result = await firs_certification_service.sign_invoice(invoice_data)
        elif step == "transmit_invoice" and irn:
            result = await firs_certification_service.transmit_invoice(irn)
        elif step == "confirm_invoice" and irn:
            result = await firs_certification_service.confirm_invoice(irn)
        elif step == "download_invoice" and irn:
            result = await firs_certification_service.download_invoice(irn)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid step '{step}' or missing required parameters"
            )
        
        return firs_error_handler.handle_firs_response(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Individual step test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Step test failed: {str(e)}"
        )