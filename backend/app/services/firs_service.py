"""FIRS API integration service."""

import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.utils.encryption import encrypt_text, decrypt_text
from app.utils.logger import get_logger

logger = get_logger(__name__)

class FIRSAuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class FIRSService:
    """Service for interacting with FIRS API."""
    
    def __init__(self, base_url: Optional[str] = None, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """Initialize FIRS service with configuration."""
        self.base_url = base_url or settings.FIRS_API_URL
        self.client_id = client_id or settings.FIRS_CLIENT_ID
        self.client_secret = client_secret or settings.FIRS_CLIENT_SECRET
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
    
    async def authenticate(self, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> FIRSAuthResponse:
        """Authenticate with FIRS API and get access token."""
        try:
            url = f"{self.base_url}/auth/token"
            
            # Use provided credentials or fall back to instance credentials
            client_id = client_id or self.client_id
            client_secret = client_secret or self.client_secret
            
            payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"FIRS authentication failed: {response.text}")
                error_detail = response.json().get("error_description", "Authentication failed")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"FIRS API authentication failed: {error_detail}"
                )
            
            auth_data = response.json()
            # Store token and set expiry
            self.token = auth_data["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=auth_data["expires_in"])
            
            return FIRSAuthResponse(**auth_data)
            
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def _ensure_authenticated(self) -> str:
        """Ensure we have a valid authentication token."""
        if not self.token or not self.token_expiry or datetime.now() >= self.token_expiry:
            auth_response = await self.authenticate()
            return auth_response.access_token
        return self.token
    
    async def generate_irn(self, integration_id: str, invoice_number: str, timestamp: str) -> Dict[str, Any]:
        """Generate an Invoice Reference Number (IRN)."""
        try:
            token = await self._ensure_authenticated()
            
            url = f"{self.base_url}/irn/generate"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "integration_id": integration_id,
                "invoice_number": invoice_number,
                "timestamp": timestamp
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"IRN generation failed: {response.text}")
                error_detail = response.json().get("detail", "IRN generation failed")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"FIRS IRN generation failed: {error_detail}"
                )
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def validate_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an invoice against FIRS rules."""
        try:
            token = await self._ensure_authenticated()
            
            url = f"{self.base_url}/validate/invoice"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=invoice_data, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Invoice validation failed: {response.text}")
                error_detail = response.json().get("detail", "Validation failed")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"FIRS invoice validation failed: {error_detail}"
                )
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )


# Create a default instance for easy importing
firs_service = FIRSService()
