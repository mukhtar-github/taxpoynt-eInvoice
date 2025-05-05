from pydantic import BaseModel, Field, validator, root_validator # type: ignore
from typing import Optional, Dict, Any, List # type: ignore
from datetime import datetime
import re
from uuid import UUID


class IRNGenerateRequest(BaseModel):
    """
    Schema for IRN generation request
    
    An IRN (Invoice Reference Number) is a unique identifier for invoices
    following the FIRS format: InvoiceNumber-ServiceID-YYYYMMDD
    """
    integration_id: UUID = Field(..., description="ID of the integration")
    invoice_number: str = Field(
        ..., 
        description="Invoice number from accounting system",
        example="INV001"
    )
    timestamp: Optional[str] = Field(
        None, 
        description="Date in YYYYMMDD format. If not provided, today's date will be used.",
        example="20240611"
    )

    @validator('invoice_number')
    def validate_invoice_number(cls, v):
        if not v:
            raise ValueError('Invoice number must not be empty')
        
        if len(v) > 50:
            raise ValueError('Invoice number must not exceed 50 characters')
            
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('Invoice number must be alphanumeric with no special characters')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is None:
            return v
            
        if not re.match(r'^\d{8}$', v):
            raise ValueError('Timestamp must be in YYYYMMDD format (YYYYMMDD)')
            
        try:
            # Validate date format
            year = int(v[0:4])
            month = int(v[4:6])
            day = int(v[6:8])
            
            # Create date object to validate
            from datetime import date
            date_obj = date(year, month, day)
            
            # Check if it's a future date
            if date_obj > date.today():
                raise ValueError('Timestamp cannot be a future date')
                
            return v
        except ValueError as e:
            raise ValueError(f'Invalid date: {str(e)}')


class IRNBatchGenerateRequest(BaseModel):
    """
    Schema for batch IRN generation request
    
    Allows generating multiple IRNs in a single request, all using the same
    integration and timestamp (optional) but different invoice numbers.
    """
    integration_id: UUID = Field(
        ..., 
        description="ID of the integration"
    )
    invoice_numbers: List[str] = Field(
        ..., 
        description="List of invoice numbers",
        min_items=1,
        max_items=100,  # Limit batch size for performance
    )
    timestamp: Optional[str] = Field(
        None, 
        description="Date in YYYYMMDD format. If not provided, today's date will be used.",
        example="20240611"
    )
    
    @validator('invoice_numbers')
    def validate_invoice_numbers(cls, v):
        if not v:
            raise ValueError('At least one invoice number must be provided')
            
        for invoice_number in v:
            if not invoice_number:
                raise ValueError('Invoice numbers cannot be empty')
                
            if len(invoice_number) > 50:
                raise ValueError(f'Invoice number "{invoice_number}" exceeds 50 characters')
                
            if not re.match(r'^[a-zA-Z0-9]+$', invoice_number):
                raise ValueError(f'Invoice number "{invoice_number}" must be alphanumeric with no special characters')
        
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError('Duplicate invoice numbers are not allowed')
            
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is None:
            return v
            
        if not re.match(r'^\d{8}$', v):
            raise ValueError('Timestamp must be in YYYYMMDD format (YYYYMMDD)')
            
        try:
            # Validate date format
            year = int(v[0:4])
            month = int(v[4:6])
            day = int(v[6:8])
            
            # Create date object to validate
            from datetime import date
            date_obj = date(year, month, day)
            
            # Check if it's a future date
            if date_obj > date.today():
                raise ValueError('Timestamp cannot be a future date')
                
            return v
        except ValueError as e:
            raise ValueError(f'Invalid date: {str(e)}')


class IRNResponse(BaseModel):
    """
    Schema for IRN response
    
    Contains the generated IRN and related metadata.
    """
    irn: str = Field(
        ..., 
        description="Generated IRN in format InvoiceNumber-ServiceID-YYYYMMDD"
    )
    invoice_number: str = Field(
        ..., 
        description="Original invoice number used to generate the IRN"
    )
    service_id: str = Field(
        ..., 
        description="Service ID used in IRN generation"
    )
    timestamp: str = Field(
        ..., 
        description="Timestamp in YYYYMMDD format used in IRN generation"
    )
    status: str = Field(
        ..., 
        description="IRN status (unused, used, expired)"
    )
    generated_at: datetime = Field(
        ..., 
        description="Timestamp when the IRN was generated"
    )
    valid_until: datetime = Field(
        ..., 
        description="Expiration timestamp for the IRN"
    )
    used_at: Optional[datetime] = Field(
        None, 
        description="When the IRN was used (if applicable)"
    )
    invoice_id: Optional[str] = Field(
        None, 
        description="ID of the invoice that used this IRN (if applicable)"
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata",
        alias="metadata"
    )

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class IRNBatchResponse(BaseModel):
    """
    Schema for batch IRN generation response
    
    Contains a list of generated IRNs and a count.
    """
    irns: List[IRNResponse] = Field(
        ..., 
        description="List of generated IRNs"
    )
    count: int = Field(
        ..., 
        description="Number of IRNs generated"
    )
    failed_count: int = Field(
        0, 
        description="Number of invoice numbers that failed IRN generation"
    )
    failed_invoices: Optional[List[Dict[str, str]]] = Field(
        None, 
        description="Details of invoice numbers that failed, with error messages"
    )


class IRNStatusUpdate(BaseModel):
    """
    Schema for updating IRN status
    
    Used to update the status of an existing IRN.
    """
    status: str = Field(
        ..., 
        description="New status (used, unused, expired)"
    )
    invoice_id: Optional[str] = Field(
        None, 
        description="External invoice ID that used this IRN"
    )
    used_at: Optional[datetime] = Field(
        None, 
        description="When the IRN was used"
    )
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["used", "unused", "expired"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class IRNMetricsResponse(BaseModel):
    """
    Schema for IRN usage metrics response
    
    Provides counts of IRNs by status.
    """
    used_count: int = Field(0, description="Count of used IRNs")
    unused_count: int = Field(0, description="Count of unused IRNs")
    expired_count: int = Field(0, description="Count of expired IRNs")
    total_count: int = Field(0, description="Total count of IRNs")
    recent_irns: Optional[List[IRNResponse]] = Field(
        None, 
        description="Recently generated IRNs (limited to 10)"
    )


class OdooIRNGenerateRequest(BaseModel):
    """
    Schema for generating an IRN for an Odoo invoice
    
    Takes an Odoo invoice ID and generates an IRN for it. The invoice data is
    fetched from the Odoo instance via OdooRPC and stored with the IRN.
    """
    integration_id: UUID = Field(
        ..., 
        description="ID of the Odoo integration"
    )
    odoo_invoice_id: int = Field(
        ..., 
        description="ID of the Odoo invoice",
        gt=0,
        example=42
    )

    @validator('odoo_invoice_id')
    def validate_odoo_invoice_id(cls, v):
        if v <= 0:
            raise ValueError('Odoo invoice ID must be a positive integer')
        return v


class IRNValidationResponse(BaseModel):
    """
    Schema for IRN validation response
    
    Contains the validation result and associated invoice data if available.
    """
    success: bool = Field(
        ..., 
        description="Whether the IRN is valid"
    )
    message: str = Field(
        ..., 
        description="Validation message"
    )
    details: Dict[str, Any] = Field(
        {}, 
        description="Additional details about the validation result"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "IRN is valid",
                "details": {
                    "status": "active",
                    "invoice_number": "INV001",
                    "valid_until": "2023-07-31T23:59:59",
                    "invoice_data": {
                        "customer_name": "Acme Corp",
                        "invoice_date": "2023-07-01T00:00:00",
                        "total_amount": 1500.0,
                        "currency_code": "NGN"
                    }
                }
            }
        }