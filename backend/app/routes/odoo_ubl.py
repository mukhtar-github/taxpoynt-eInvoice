"""
API routes for Odoo UBL mapping and testing.

This module provides endpoints specifically for testing the mapping of Odoo invoices
to BIS Billing 3.0 UBL format, leveraging existing service functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path, Response # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import Any, List, Optional, Dict, Union
from datetime import datetime
from uuid import UUID
import json

from app.db.session import get_db
from app.models.integration import IntegrationType
from app.schemas.integration import (
    Integration, OdooConnectionTestRequest, OdooConfig, OdooInvoiceFetchParams
)
from app.schemas.pagination import PaginatedResponse
from app.services.integration_service import (
    get_integration, test_odoo_connection, test_integration
)
from app.services.firs_si.odoo_service import (
    fetch_odoo_invoices, search_odoo_invoices, fetch_odoo_partners
)
from app.services.firs_si.odoo_invoice_service import odoo_invoice_service
from app.dependencies.auth import get_current_user
from app.services.firs_si.integration_credential_connector import get_credentials_for_integration

# Create a router with prefix and tags
router = APIRouter(prefix="/odoo-ubl", tags=["odoo-ubl"])


@router.get("/test-connection", status_code=status.HTTP_200_OK)
async def test_odoo_ubl_connection(
    host: str = Query(..., description="Odoo host URL"),
    db: str = Query(..., description="Odoo database name"),
    user: str = Query(..., description="Odoo username"),
    password: Optional[str] = Query(None, description="Odoo password (use this or api_key)"),
    api_key: Optional[str] = Query(None, description="Odoo API key (use this or password)"),
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Test connection to an Odoo server and verify UBL mapping capabilities.
    
    This endpoint tests connectivity to an Odoo server using the provided
    credentials and returns basic information about the connection.
    At least one of password or api_key must be provided.
    """
    if not password and not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either password or api_key must be provided"
        )
    
    try:
        # Reuse the existing test_odoo_connection service
        connection_params = OdooConnectionTestRequest(
            host=host,
            db=db,
            user=user,
            password=password,
            api_key=api_key
        )
        
        # Test basic connectivity
        connection_result = test_odoo_connection(connection_params, current_user)
        
        # Add UBL mapping-specific test information
        return {
            **connection_result.dict(),
            "ubl_mapping_status": "available",
            "ubl_mapping_version": "BIS Billing 3.0",
            "ubl_schema_validation": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing Odoo connection: {str(e)}"
        )


@router.get("/invoices", status_code=status.HTTP_200_OK)
async def get_odoo_invoices(
    host: str = Query(..., description="Odoo host URL"),
    db: str = Query(..., description="Odoo database name"),
    user: str = Query(..., description="Odoo username"),
    password: Optional[str] = Query(None, description="Odoo password (use this or api_key)"),
    api_key: Optional[str] = Query(None, description="Odoo API key (use this or password)"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    include_draft: bool = Query(False, description="Include draft invoices"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Search and retrieve invoices from an Odoo server.
    
    This endpoint searches for invoices in the Odoo server based on date range
    and pagination parameters. Results can be used to test the UBL mapping.
    """
    if not password and not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either password or api_key must be provided"
        )
    
    try:
        # Create fetch parameters using the same schema used by the integration routes
        params = OdooInvoiceFetchParams(
            from_date=datetime.fromisoformat(from_date) if from_date else None,
            to_date=datetime.fromisoformat(to_date) if to_date else None,
            include_draft=include_draft,
            include_attachments=False,  # Not needed for UBL mapping test
            page=page,
            page_size=page_size
        )
        
        # Setup connection parameters
        connection_params = {
            "host": host,
            "db": db,
            "user": user,
            "password": password or "",
            "api_key": api_key or ""
        }
        
        # Use the existing service to fetch invoices
        result = fetch_odoo_invoices(
            **connection_params,
            from_date=from_date,
            to_date=to_date,
            include_draft=include_draft,
            page=page,
            page_size=page_size
        )
        
        # Add UBL mapping capability information to each invoice in the response
        invoices = result.get("data", [])
        for invoice in invoices:
            invoice["ubl_mapping_available"] = True
            invoice["ubl_endpoints"] = {
                "details": f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}",
                "ubl": f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}/ubl",
                "xml": f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}/ubl/xml"
            }
        
        return {
            "status": "success",
            "data": invoices,
            "pagination": result.get("pagination", {}),
            "ubl_mapping": {
                "status": "available",
                "version": "BIS Billing 3.0"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Odoo invoices: {str(e)}"
        )


@router.get("/invoices/{invoice_id}", status_code=status.HTTP_200_OK)
async def get_odoo_invoice_details(
    invoice_id: int = Path(..., description="Odoo invoice ID"),
    host: str = Query(..., description="Odoo host URL"),
    db: str = Query(..., description="Odoo database name"),
    user: str = Query(..., description="Odoo username"),
    password: Optional[str] = Query(None, description="Odoo password (use this or api_key)"),
    api_key: Optional[str] = Query(None, description="Odoo API key (use this or password)"),
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get details of a specific invoice from an Odoo server.
    
    This endpoint retrieves a specific invoice by ID from the Odoo server.
    """
    if not password and not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either password or api_key must be provided"
        )
    
    try:
        # Create connection parameters using the schema from integration service
        connection_params = OdooConnectionTestRequest(
            host=host,
            db=db,
            user=user,
            password=password,
            api_key=api_key
        )
        
        # Connect to Odoo using the existing service infrastructure
        connection_result = test_odoo_connection(connection_params, current_user)
        if not connection_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Odoo: {connection_result.message}"
            )
            
        # Use the search_odoo_invoices function to get a specific invoice
        # This reuses more of the existing logic instead of duplicating it
        search_result = search_odoo_invoices(
            host=host,
            db=db,
            user=user,
            password=password or "",
            api_key=api_key or "",
            invoice_ids=[invoice_id]
        )
        
        if not search_result or not search_result.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found"
            )
            
        invoice_data = search_result.get('data')[0]
        
        # Include UBL mapping availability information
        return {
            "status": "success",
            "data": invoice_data,
            "ubl_mapping": {
                "available": True,
                "endpoints": {
                    "ubl": f"/api/v1/odoo-ubl/invoices/{invoice_id}/ubl",
                    "xml": f"/api/v1/odoo-ubl/invoices/{invoice_id}/ubl/xml"
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving Odoo invoice: {str(e)}"
        )


@router.get("/invoices/{invoice_id}/ubl", status_code=status.HTTP_200_OK)
async def map_odoo_invoice_to_ubl(
    invoice_id: int = Path(..., description="Odoo invoice ID"),
    host: str = Query(..., description="Odoo host URL"),
    db: str = Query(..., description="Odoo database name"),
    user: str = Query(..., description="Odoo username"),
    password: Optional[str] = Query(None, description="Odoo password (use this or api_key)"),
    api_key: Optional[str] = Query(None, description="Odoo API key (use this or password)"),
    validate_schema: bool = Query(True, description="Validate the UBL against schema"),
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Map an Odoo invoice to BIS Billing 3.0 UBL format.
    
    This endpoint retrieves a specific invoice from Odoo and maps it
    to BIS Billing 3.0 UBL format with validation.
    """
    if not password and not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either password or api_key must be provided"
        )
    
    try:
        # First get the invoice data using the same approach as get_odoo_invoice_details
        # to leverage existing services
        connection_params = OdooConnectionTestRequest(
            host=host,
            db=db,
            user=user,
            password=password,
            api_key=api_key
        )
        
        # Test connection using existing service
        connection_result = test_odoo_connection(connection_params, current_user)
        if not connection_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Odoo: {connection_result.message}"
            )
            
        # Get invoice data using search (reusing existing service)
        search_result = search_odoo_invoices(
            host=host,
            db=db,
            user=user,
            password=password or "",
            api_key=api_key or "",
            invoice_ids=[invoice_id]
        )
        
        if not search_result or not search_result.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found"
            )
            
        invoice_data = search_result.get('data')[0]
        
        # Get company info from connection_result
        company_info = connection_result.data.get('company_info', {}) if connection_result.data else {}
        
        # Now use the odoo_invoice_service to map the invoice to UBL
        # We can use the process_invoice_data method which takes already retrieved invoice data
        # This avoids making duplicate calls to Odoo API
        result = odoo_invoice_service.process_invoice_data(
            invoice_data=invoice_data,
            company_info=company_info,
            save_ubl=False,
            validate_ubl=validate_schema
        )
        
        # Check for errors in the mapping process
        if not result.get("success"):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            raise HTTPException(
                status_code=status_code,
                detail={
                    "status": "error",
                    "message": "Failed to map invoice to UBL format",
                    "errors": result.get("errors", []),
                    "warnings": result.get("warnings", [])
                }
            )
        
        return {
            "status": "success",
            "data": result,
            "message": "Invoice successfully mapped to UBL format"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error mapping Odoo invoice to UBL: {str(e)}"
        )


@router.get("/invoices/{invoice_id}/ubl/xml", status_code=status.HTTP_200_OK)
async def get_odoo_invoice_ubl_xml(
    invoice_id: int = Path(..., description="Odoo invoice ID"),
    host: str = Query(..., description="Odoo host URL"),
    db: str = Query(..., description="Odoo database name"),
    user: str = Query(..., description="Odoo username"),
    password: Optional[str] = Query(None, description="Odoo password (use this or api_key)"),
    api_key: Optional[str] = Query(None, description="Odoo API key (use this or password)"),
    validate_schema: bool = Query(True, description="Validate the UBL against schema"),
    current_user: Any = Depends(get_current_user)
) -> Response:
    """
    Get the UBL XML for an Odoo invoice.
    
    This endpoint retrieves a specific invoice from Odoo, maps it
    to BIS Billing 3.0 UBL format, and returns the XML directly.
    """
    if not password and not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either password or api_key must be provided"
        )
    
    try:
        # Use the same approach as the UBL endpoint to get and map the invoice
        # This ensures consistency and reuses existing service logic
        
        # First check connection
        connection_params = OdooConnectionTestRequest(
            host=host,
            db=db,
            user=user,
            password=password,
            api_key=api_key
        )
        
        connection_result = test_odoo_connection(connection_params, current_user)
        if not connection_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Odoo: {connection_result.message}"
            )
        
        # Get invoice data
        search_result = search_odoo_invoices(
            host=host,
            db=db,
            user=user,
            password=password or "",
            api_key=api_key or "",
            invoice_ids=[invoice_id]
        )
        
        if not search_result or not search_result.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found"
            )
        
        invoice_data = search_result.get('data')[0]
        company_info = connection_result.data.get('company_info', {}) if connection_result.data else {}
        
        # Process the invoice data to generate UBL XML
        result = odoo_invoice_service.process_invoice_data(
            invoice_data=invoice_data,
            company_info=company_info,
            save_ubl=False,
            validate_ubl=validate_schema
        )
        
        # Check for errors
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "error",
                    "message": "Failed to generate UBL XML",
                    "errors": result.get("errors", []),
                    "warnings": result.get("warnings", [])
                }
            )
        
        # Extract the XML content
        xml_content = result.get("ubl_xml")
        if not xml_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="UBL XML generation failed: No XML content returned"
            )
        
        # Return the XML with appropriate headers
        filename = f"invoice_{invoice_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xml"
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating UBL XML: {str(e)}"
        )


@router.post("/batch-process", status_code=status.HTTP_200_OK)
async def batch_process_odoo_invoices(
    host: str = Body(..., description="Odoo host URL"),
    db: str = Body(..., description="Odoo database name"),
    user: str = Body(..., description="Odoo username"),
    password: Optional[str] = Body(None, description="Odoo password (use this or api_key)"),
    api_key: Optional[str] = Body(None, description="Odoo API key (use this or password)"),
    from_date: Optional[str] = Body(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Body(None, description="End date (YYYY-MM-DD)"),
    include_draft: bool = Body(False, description="Include draft invoices"),
    page: int = Body(1, ge=1, description="Page number"),
    page_size: int = Body(10, ge=1, le=100, description="Number of items per page"),
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Batch process multiple Odoo invoices.
    
    This endpoint retrieves multiple invoices from Odoo based on date range
    and pagination parameters, maps them to BIS Billing 3.0 UBL format,
    and returns the results.
    """
    if not password and not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either password or api_key must be provided"
        )
    
    try:
        # First test the connection using existing service
        connection_params = OdooConnectionTestRequest(
            host=host,
            db=db,
            user=user,
            password=password,
            api_key=api_key
        )
        
        # Test connection to ensure credentials are valid
        connection_result = test_odoo_connection(connection_params, current_user)
        if not connection_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Odoo: {connection_result.message}"
            )
            
        # Fetch the invoices using the existing service
        # We first fetch the raw invoice data to avoid duplicating code
        invoice_result = fetch_odoo_invoices(
            host=host,
            db=db,
            user=user,
            password=password or "",
            api_key=api_key or "",
            from_date=from_date,
            to_date=to_date,
            include_draft=include_draft,
            page=page,
            page_size=page_size
        )
        
        if not invoice_result or not invoice_result.get('data'):
            return {
                "status": "success",
                "message": "No invoices found matching the criteria",
                "processed_count": 0,
                "success_count": 0,
                "error_count": 0,
                "invoices": []
            }
            
        invoices = invoice_result.get('data', [])
        company_info = connection_result.data.get('company_info', {}) if connection_result.data else {}
        
        # Process each invoice individually
        results = []
        success_count = 0
        error_count = 0
        
        for invoice in invoices:
            try:
                # Process each invoice data using the existing service
                mapping_result = odoo_invoice_service.process_invoice_data(
                    invoice_data=invoice,
                    company_info=company_info,
                    save_ubl=False,  # Don't save to database for this test endpoint
                    validate_ubl=True
                )
                
                # Add to results
                if mapping_result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
                    
                results.append({
                    "invoice_id": invoice.get("id"),
                    "invoice_number": invoice.get("number"),
                    "success": mapping_result.get("success", False),
                    "errors": mapping_result.get("errors", []),
                    "warnings": mapping_result.get("warnings", []),
                    "ubl_id": mapping_result.get("ubl_id") if mapping_result.get("success") else None
                })
                
            except Exception as e:
                error_count += 1
                results.append({
                    "invoice_id": invoice.get("id"),
                    "invoice_number": invoice.get("number"),
                    "success": False,
                    "errors": [{
                        "code": "PROCESSING_ERROR",
                        "message": str(e),
                        "field": None
                    }],
                    "warnings": [],
                    "ubl_id": None
                })
        
        return {
            "status": "success" if error_count == 0 else "partial",
            "processed_count": len(invoices),
            "success_count": success_count,
            "error_count": error_count,
            "message": f"Processed {len(invoices)} invoices: {success_count} successful, {error_count} failed",
            "invoices": results,
            "pagination": invoice_result.get("pagination", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error batch processing Odoo invoices: {str(e)}"
        )


@router.post("/validate", status_code=status.HTTP_200_OK)
async def validate_odoo_invoice_mapping(
    invoice_data: Dict[str, Any] = Body(..., description="Raw Odoo invoice data to validate"),
    company_info: Dict[str, Any] = Body(..., description="Company information for the supplier"),
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate raw Odoo invoice data against BIS Billing 3.0 UBL schema.
    
    This endpoint allows testing the mapping and validation with custom
    Odoo invoice data without connecting to an actual Odoo server.
    """
    try:
        # Import here to avoid circular imports
        from app.services.odoo_ubl_mapper import odoo_ubl_mapper
        from app.services.odoo_ubl_validator import odoo_ubl_validator
        from app.services.odoo_ubl_transformer import odoo_ubl_transformer
        
        # Map the invoice data to UBL object
        ubl_invoice, validation_issues = odoo_ubl_transformer.odoo_to_ubl_object(
            invoice_data, company_info
        )
        
        if validation_issues:
            return {
                "status": "validation_issues",
                "validation_issues": validation_issues,
                "ubl_object": ubl_invoice.dict() if ubl_invoice else None
            }
        
        # Transform to UBL XML if mapping was successful
        if ubl_invoice:
            ubl_xml, conversion_issues = odoo_ubl_transformer.ubl_object_to_xml(ubl_invoice)
            
            return {
                "status": "success" if not conversion_issues else "conversion_issues",
                "validation_issues": validation_issues,
                "conversion_issues": conversion_issues,
                "ubl_object": ubl_invoice.dict(),
                "ubl_xml": ubl_xml if not conversion_issues else None
            }
        
        return {
            "status": "error",
            "message": "Failed to create UBL object",
            "validation_issues": validation_issues
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating Odoo invoice mapping: {str(e)}"
        )
