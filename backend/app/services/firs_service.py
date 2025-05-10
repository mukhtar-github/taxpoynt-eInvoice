"""FIRS API integration service.

This service implements all required interactions with the Federal Inland Revenue Service (FIRS)
API for e-Invoicing compliance. The implementation follows the official FIRS API documentation.
"""

import requests
import json
import base64
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID

from app.core.config import settings
from app.utils.encryption import encrypt_text, decrypt_text
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Response models for FIRS API
class FIRSUserData(BaseModel):
    id: str
    email: str
    name: str
    role: str


class FIRSAuthData(BaseModel):
    user_id: str
    access_token: str
    token_type: str
    expires_in: int
    issued_at: str
    user: FIRSUserData


class FIRSAuthResponse(BaseModel):
    status: str
    message: str
    data: FIRSAuthData


class FIRSResourceItem(BaseModel):
    id: str
    name: str


class FIRSCodeResourceItem(BaseModel):
    code: str
    name: str


class FIRSTaxCategory(BaseModel):
    id: str
    name: str
    default_percent: float


class FIRSService:
    """Service for interacting with FIRS API.
    
    This service implements all required interactions with the FIRS API
    following the official documentation for e-Invoice compliance.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize FIRS service with configuration."""
        self.base_url = base_url or settings.FIRS_API_URL
        self.api_key = api_key or settings.FIRS_API_KEY
        self.api_secret = api_secret or settings.FIRS_API_SECRET
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        return {
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
            "Content-Type": "application/json"
        }
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with auth token for API requests."""
        headers = self._get_default_headers()
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def authenticate(self, email: str, password: str) -> FIRSAuthResponse:
        """Authenticate with FIRS API using taxpayer credentials."""
        try:
            url = f"{self.base_url}/api/v1/utilities/authenticate"
            
            payload = {
                "email": email,
                "password": password
            }
            
            response = requests.post(
                url, 
                json=payload, 
                headers=self._get_default_headers()
            )
            
            if response.status_code != 200:
                logger.error(f"FIRS authentication failed: {response.text}")
                error_data = response.json()
                error_detail = error_data.get("message", "Authentication failed")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"FIRS API authentication failed: {error_detail}"
                )
            
            auth_response = response.json()
            # Store token and set expiry
            self.token = auth_response["data"]["access_token"]
            self.token_expiry = datetime.now() + timedelta(seconds=auth_response["data"]["expires_in"])
            
            return FIRSAuthResponse(**auth_response)
            
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token.
        
        This is a helper method and should be used internally before making
        API calls that require authentication. If no credentials are provided,
        it will raise an exception.
        """
        if not self.token or not self.token_expiry or datetime.now() >= self.token_expiry:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid authentication token. Please authenticate first."
            )
    
    async def validate_irn(self, business_id: str, irn: str, invoice_reference: str) -> Dict[str, Any]:
        """Validate an Invoice Reference Number (IRN).
        
        Args:
            business_id: The business ID of the invoice
            irn: The IRN to validate
            invoice_reference: The invoice reference number
            
        Returns:
            Dictionary with validation results
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}/api/v1/invoice/irn/validate"
            
            payload = {
                "invoice_reference": invoice_reference,
                "business_id": business_id,
                "irn": irn
            }
            
            response = requests.post(
                url, 
                json=payload, 
                headers=self._get_auth_headers()
            )
            
            # Handle response based on status code
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("message", "IRN validation failed")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"FIRS API IRN validation failed: {error_detail}"
                )
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="IRN not found"
                )
            else:
                logger.error(f"IRN validation failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API IRN validation failed with unexpected status code"
                )
            
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def validate_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an invoice against FIRS rules.
        
        Args:
            invoice_data: Complete invoice data following FIRS specification
            
        Returns:
            Dictionary with validation results
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}/api/v1/invoice/validate"
            
            response = requests.post(
                url, 
                json=invoice_data, 
                headers=self._get_auth_headers()
            )
            
            # Handle response based on status code
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("message", "Invoice validation failed")
                # Return the validation errors to provide details to the client
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": error_detail,
                        "errors": error_data.get("errors", [])
                    }
                )
            else:
                logger.error(f"Invoice validation failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API invoice validation failed with unexpected status code"
                )
            
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def sign_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sign an invoice using FIRS API.
        
        This endpoint submits a properly formed invoice to the FIRS API
        for signing, which generates a Cryptographic Stamp ID (CSID).
        
        Args:
            invoice_data: Complete invoice data following FIRS specification
            
        Returns:
            Dictionary with the signed invoice details including CSID
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}/api/v1/invoice/sign"
            
            response = requests.post(
                url, 
                json=invoice_data, 
                headers=self._get_auth_headers()
            )
            
            # Handle response based on status code
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("message", "Invoice signing failed")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": error_detail,
                        "errors": error_data.get("errors", [])
                    }
                )
            else:
                logger.error(f"Invoice signing failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API invoice signing failed with unexpected status code"
                )
            
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def download_invoice(self, irn: str) -> Dict[str, Any]:
        """Download a signed invoice PDF from FIRS API.
        
        Args:
            irn: Invoice Reference Number
            
        Returns:
            Dictionary with invoice PDF data
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}/api/v1/invoice/download/{irn}"
            
            response = requests.get(
                url,
                headers=self._get_auth_headers()
            )
            
            # Handle response based on status code
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invoice not found"
                )
            else:
                logger.error(f"Invoice download failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API invoice download failed with unexpected status code"
                )
            
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    # Resource endpoints - these do not require authentication
    
    async def get_countries(self) -> List[FIRSResourceItem]:
        """Get list of countries from FIRS API."""
        try:
            url = f"{self.base_url}/api/v1/invoice/resources/countries"
            response = requests.get(url)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("data", [])
            else:
                logger.error(f"Countries fetch failed: {response.text}")
                return []
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            return []
    
    async def get_currencies(self) -> List[FIRSResourceItem]:
        """Get list of currencies from FIRS API."""
        try:
            url = f"{self.base_url}/api/v1/invoice/resources/currencies"
            response = requests.get(url)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("data", [])
            else:
                logger.error(f"Currencies fetch failed: {response.text}")
                return []
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            return []
    
    async def get_tax_categories(self) -> List[FIRSTaxCategory]:
        """Get list of tax categories from FIRS API."""
        try:
            url = f"{self.base_url}/api/v1/invoice/resources/tax-categories"
            response = requests.get(url)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("data", [])
            else:
                logger.error(f"Tax categories fetch failed: {response.text}")
                return []
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            return []
    
    async def get_payment_means(self) -> List[FIRSCodeResourceItem]:
        """Get list of payment means from FIRS API."""
        try:
            url = f"{self.base_url}/api/v1/invoice/resources/payment-means"
            response = requests.get(url)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("data", [])
            else:
                logger.error(f"Payment means fetch failed: {response.text}")
                return []
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            return []
    
    async def get_invoice_types(self) -> List[FIRSCodeResourceItem]:
        """Get list of invoice types from FIRS API."""
        try:
            url = f"{self.base_url}/api/v1/invoice/resources/invoice-types"
            response = requests.get(url)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("data", [])
            else:
                logger.error(f"Invoice types fetch failed: {response.text}")
                return []
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            return []


# Create a default instance for easy importing
firs_service = FIRSService()
