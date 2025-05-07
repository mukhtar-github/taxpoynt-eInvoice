"""Routes for interacting with FIRS API."""

from fastapi import APIRouter, Depends, HTTPException, status, Body # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import Any, Dict
from uuid import UUID
from pydantic import BaseModel

from app.db.session import get_db
from app.services.firs_service import firs_service
from app.services.user_service import get_current_user # type: ignore

router = APIRouter(prefix="/firs", tags=["firs"])


class FIRSAuthRequest(BaseModel):
    client_id: str
    client_secret: str


@router.post("/auth")
async def authenticate_with_firs(
    auth_data: FIRSAuthRequest
) -> Any:
    """
    Authenticate with FIRS API using client credentials.
    """
    return await firs_service.authenticate(
        client_id=auth_data.client_id,
        client_secret=auth_data.client_secret
    )


class IRNGenerateRequest(BaseModel):
    integration_id: str
    invoice_number: str
    timestamp: str


@router.post("/irn/generate")
async def generate_irn(
    irn_request: IRNGenerateRequest,
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Generate an Invoice Reference Number (IRN) through the FIRS API.
    """
    return await firs_service.generate_irn(
        integration_id=irn_request.integration_id,
        invoice_number=irn_request.invoice_number,
        timestamp=irn_request.timestamp
    )


@router.post("/validate/invoice")
async def validate_invoice(
    invoice_data: Dict[str, Any] = Body(...),
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Validate an invoice against FIRS rules.
    """
    return await firs_service.validate_invoice(invoice_data=invoice_data)
