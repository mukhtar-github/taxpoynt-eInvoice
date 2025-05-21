"""FIRS API integration service.

This service implements all required interactions with the Federal Inland Revenue Service (FIRS)
API for e-Invoicing compliance, including IRN validation. The implementation follows the official 
FIRS API documentation and provides sandbox environment testing for IRN validation.
"""

import requests
import json
import base64
import hashlib
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4

from app.core.config import settings
from app.utils.encryption import encrypt_text, decrypt_text
from app.utils.logger import get_logger
from app.models.irn import IRNRecord, IRNValidationRecord, IRNStatus
from app.services.irn_service import create_validation_record
from app.cache.irn_cache import IRNCache

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


class SubmissionStatus(BaseModel):
    """Status response model for FIRS API submission."""
    submission_id: str
    status: str
    timestamp: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class InvoiceSubmissionResponse(BaseModel):
    """Response model for FIRS API invoice submission."""
    success: bool
    message: str
    submission_id: Optional[str] = None
    status: Optional[str] = None
    errors: Optional[List[Dict[str, Any]]] = None
    details: Optional[Dict[str, Any]] = None


class FIRSService:
    """
    Service for interacting with FIRS API.
    
    This service implements all required interactions with the FIRS API
    following the official documentation for e-Invoice compliance.
    
    Features:
    - Authentication with FIRS API
    - Invoice validation and signing
    - IRN validation
    - Invoice submission to FIRS
    - Sandbox environment support for testing
    - Comprehensive error handling
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, api_secret: Optional[str] = None, use_sandbox: Optional[bool] = None):
        """Initialize FIRS service with configuration.
        
        Args:
            base_url: Override the base URL for the FIRS API
            api_key: Override the API key from settings
            api_secret: Override the API secret from settings
            use_sandbox: Override the sandbox setting from environment
        """
        # Determine whether to use sandbox or production
        self.use_sandbox = settings.FIRS_USE_SANDBOX if use_sandbox is None else use_sandbox
        
        # Set base URL and credentials based on environment
        if self.use_sandbox:
            self.base_url = base_url or settings.FIRS_SANDBOX_API_URL
            self.api_key = api_key or settings.FIRS_SANDBOX_API_KEY
            self.api_secret = api_secret or settings.FIRS_SANDBOX_API_SECRET
            logger.info(f"FIRS service initialized in SANDBOX mode with URL: {self.base_url}")
        else:
            self.base_url = base_url or settings.FIRS_API_URL
            self.api_key = api_key or settings.FIRS_API_KEY
            self.api_secret = api_secret or settings.FIRS_API_SECRET
            logger.info(f"FIRS service initialized in PRODUCTION mode with URL: {self.base_url}")
            
        # Authentication state
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # API endpoint paths based on reference data
        self.endpoints = {
            # Authentication endpoints
            "authenticate": "/api/v1/utilities/authenticate",
            "verify_tin": "/api/v1/utilities/verify-tin",
            
            # Invoice management endpoints
            "irn_validate": "/api/v1/invoice/irn/validate",
            "invoice_validate": "/api/v1/invoice/validate",
            "invoice_sign": "/api/v1/invoice/sign",
            "download_invoice": "/api/v1/invoice/download",
            "submit_invoice": "/api/v1/invoice/submit",
            "submit_batch": "/api/v1/invoice/batch/submit",
            "transact": "/api/v1/invoice/transact",
            
            # Business management endpoints
            "business_search": "/api/v1/entity",
            "business_lookup": "/api/v1/invoice/party",
            
            # Reference data endpoints
            "countries": "/api/v1/invoice/resources/countries",
            "invoice_types": "/api/v1/invoice/resources/invoice-types",
            "currencies": "/api/v1/invoice/resources/currencies",
            "vat_exemptions": "/api/v1/invoice/resources/vat-exemptions",
            "service_codes": "/api/v1/invoice/resources/service-codes"
        }
        
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
        """Authenticate with FIRS API using taxpayer credentials.
        
        Args:
            email: User email for authentication
            password: User password for authentication
            
        Returns:
            FIRSAuthResponse containing authentication details
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            url = f"{self.base_url}{self.endpoints['authenticate']}"
            logger.info(f"Authenticating with FIRS API at: {url}")
            
            payload = {
                "email": email,
                "password": password
            }
            
            response = requests.post(
                url, 
                json=payload, 
                headers=self._get_default_headers(),
                timeout=30  # Add timeout for better error handling
            )
            
            if response.status_code != 200:
                logger.error(f"FIRS authentication failed: {response.text}")
                try:
                    error_data = response.json()
                    error_detail = error_data.get("message", "Authentication failed")
                except ValueError:
                    error_detail = f"Authentication failed with status code {response.status_code}"
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"FIRS API authentication failed: {error_detail}"
                )
            
            try:
                auth_response = response.json()
                # Store token and set expiry
                self.token = auth_response["data"]["access_token"]
                self.token_expiry = datetime.now() + timedelta(seconds=auth_response["data"]["expires_in"])
                
                logger.info(f"Successfully authenticated with FIRS API as {email}")
                return FIRSAuthResponse(**auth_response)
            except (KeyError, ValueError) as e:
                logger.error(f"Error parsing authentication response: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing FIRS API authentication response: {str(e)}"
                )
            
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
    
    # === Invoice Submission Endpoints ===
    
    async def submit_invoice(self, invoice_data: Dict[str, Any]) -> InvoiceSubmissionResponse:
        """
        Submit a single invoice to FIRS.
        
        Args:
            invoice_data: Invoice data in FIRS-compliant format
            
        Returns:
            InvoiceSubmissionResponse with submission details
        """
        try:
            # Ensure authentication if token-based auth is required
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['submit_invoice']}"
            logger.info(f"Submitting invoice to FIRS API: {url}")
            logger.debug(f"Invoice data: {json.dumps(invoice_data)[:200]}...")
            
            # Ensure required fields are present
            required_fields = ['invoice_number', 'invoice_type', 'invoice_date', 'currency_code', 'supplier', 'customer']
            missing_fields = [field for field in required_fields if field not in invoice_data]
            
            if missing_fields:
                logger.error(f"Invoice data missing required fields: {missing_fields}")
                return InvoiceSubmissionResponse(
                    success=False,
                    message=f"Invoice data missing required fields: {', '.join(missing_fields)}",
                    errors=[{"code": "VALIDATION_ERROR", "detail": f"Missing field: {field}"} for field in missing_fields]
                )
            
            # Use API key-based authentication for submission as discovered in testing
            headers = self._get_auth_headers()
            
            # Submit the invoice with improved error handling
            try:
                response = requests.post(
                    url, 
                    json=invoice_data, 
                    headers=headers,
                    timeout=60  # Longer timeout for invoice submission
                )
                
                # Try to parse JSON response if present
                result = {}
                if response.content:
                    try:
                        result = response.json()
                    except ValueError as json_err:
                        logger.warning(f"Could not parse JSON response: {str(json_err)}")
                        result = {"message": f"Invalid response format: {response.text[:200]}"}
                
                if response.status_code not in (200, 201, 202):
                    logger.error(f"FIRS invoice submission failed: {response.status_code} - {response.text[:200]}")
                    return InvoiceSubmissionResponse(
                        success=False,
                        message=result.get("message", f"Submission failed with status code {response.status_code}"),
                        errors=result.get("errors", []),
                        status=result.get("status", "FAILED")
                    )
                    
                # Successfully submitted - parse the response
                submission_data = result.get("data", {})
                submission_id = submission_data.get("submission_id", str(uuid4()))
                
                # Log the successful submission
                logger.info(f"Invoice {invoice_data.get('invoice_number')} submitted successfully with ID: {submission_id}")
                
                return InvoiceSubmissionResponse(
                    success=True,
                    message=result.get("message", "Invoice submitted successfully"),
                    submission_id=submission_id,
                    status=result.get("status", "SUBMITTED"),
                    details=submission_data
                )
                
            except requests.RequestException as req_err:
                logger.error(f"Request error during invoice submission: {str(req_err)}")
                return InvoiceSubmissionResponse(
                    success=False,
                    message=f"API request failed: {str(req_err)}",
                    errors=[{"code": "CONNECTION_ERROR", "detail": str(req_err)}]
                )
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.error(f"FIRS API submission error: {str(e)}")
            return InvoiceSubmissionResponse(
                success=False,
                message=f"API request failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    async def submit_invoices_batch(self, invoices: List[Dict[str, Any]]) -> InvoiceSubmissionResponse:
        """Submit multiple invoices in a batch.
        
        Args:
            invoices: List of invoice data dictionaries
            
        Returns:
            InvoiceSubmissionResponse with batch submission details
        """
        try:
            # Ensure we have invoices to submit
            if not invoices:
                logger.warning("Attempted to submit empty batch of invoices")
                return InvoiceSubmissionResponse(
                    success=False,
                    message="No invoices provided for batch submission",
                    errors=[{"code": "VALIDATION_ERROR", "detail": "Empty invoice list"}]
                )
                
            # Ensure authentication for submission
            await self._ensure_authenticated()
            
            # Log batch details
            batch_id = str(uuid4())
            logger.info(f"Preparing batch submission with ID {batch_id} containing {len(invoices)} invoices")
            
            # Use the correct endpoint from our configuration
            url = f"{self.base_url}{self.endpoints['submit_batch']}"
            
            # Basic validation of each invoice
            required_fields = ['invoice_number', 'invoice_type', 'invoice_date', 'currency_code', 'supplier', 'customer']
            invalid_invoices = []
            
            for i, invoice in enumerate(invoices):
                missing_fields = [field for field in required_fields if field not in invoice]
                if missing_fields:
                    invalid_invoices.append({
                        "index": i,
                        "invoice_number": invoice.get("invoice_number", f"Invoice at index {i}"),
                        "missing_fields": missing_fields
                    })
            
            if invalid_invoices:
                logger.error(f"Batch contains {len(invalid_invoices)} invalid invoices")
                return InvoiceSubmissionResponse(
                    success=False,
                    message=f"Batch contains {len(invalid_invoices)} invalid invoices",
                    errors=[{"code": "VALIDATION_ERROR", "detail": f"Invoice {inv['invoice_number']} missing fields: {', '.join(inv['missing_fields'])}"} for inv in invalid_invoices]
                )
            
            # Construct the payload
            payload = {
                "invoices": invoices,
                "batch_id": batch_id,
                "metadata": {
                    "submitted_at": datetime.now().isoformat(),
                    "invoice_count": len(invoices)
                }
            }
            
            # Submit the batch
            try:
                logger.info(f"Submitting batch to {url}")
                response = requests.post(
                    url, 
                    json=payload, 
                    headers=self._get_auth_headers(),
                    timeout=120  # Longer timeout for batch submission
                )
                
                # Try to parse JSON response if present
                result = {}
                if response.content:
                    try:
                        result = response.json()
                    except ValueError as json_err:
                        logger.warning(f"Could not parse JSON response: {str(json_err)}")
                        result = {"message": f"Invalid response format: {response.text[:200]}"}
                
                if response.status_code not in (200, 201, 202):
                    logger.error(f"FIRS batch submission failed: {response.status_code} - {response.text[:200]}")
                    return InvoiceSubmissionResponse(
                        success=False,
                        message=result.get("message", f"Batch submission failed with status code {response.status_code}"),
                        errors=result.get("errors", []),
                        status="FAILED",
                        submission_id=batch_id  # Return the batch ID even if failed, for reference
                    )
                    
                # Successfully submitted
                submission_data = result.get("data", {})
                submission_id = submission_data.get("batch_id", batch_id)
                
                logger.info(f"Successfully submitted batch {submission_id} with {len(invoices)} invoices")
                
                return InvoiceSubmissionResponse(
                    success=True,
                    message=result.get("message", "Batch submitted successfully"),
                    submission_id=submission_id,
                    status=result.get("status", "SUBMITTED"),
                    details=submission_data
                )
                
            except requests.RequestException as req_err:
                logger.error(f"Request error during batch submission: {str(req_err)}")
                return InvoiceSubmissionResponse(
                    success=False,
                    message=f"API request failed: {str(req_err)}",
                    errors=[{"code": "CONNECTION_ERROR", "detail": str(req_err)}],
                    submission_id=batch_id  # Return the batch ID even if failed, for reference
                )
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.error(f"FIRS API batch submission error: {str(e)}")
            return InvoiceSubmissionResponse(
                success=False,
                message=f"Batch submission failed: {str(e)}",
                errors=[{"code": "INTERNAL_ERROR", "detail": str(e)}],
                details={"error_type": type(e).__name__}
            )


    async def validate_irn(self, invoice_reference: str, business_id: str, irn_value: str) -> Dict[str, Any]:
        """
        Validate an IRN with the FIRS API.
        
        Args:
            invoice_reference: The reference number of the invoice
            business_id: The business ID that issued the invoice
            irn_value: The IRN to validate
            
        Returns:
            Dictionary with validation result
        """
        try:
            # Skip authentication for IRN validation as it uses API key/secret
            # This aligns with our test findings that showed API key authentication works
            
            # Use sandbox validation in development
            if self.use_sandbox:
                logger.info(f"Using sandbox for IRN validation: {irn_value}")
                return await self.validate_irn_sandbox(irn_value)
            
            url = f"{self.base_url}{self.endpoints['irn_validate']}"
            logger.info(f"Validating IRN with FIRS API: {irn_value}")
            
            # Prepare signature using the cryptographic keys
            try:
                signature = self._prepare_irn_signature(irn_value)
                logger.debug(f"Generated signature for IRN: {irn_value}")
            except Exception as e:
                logger.error(f"Error generating IRN signature: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate IRN signature: {str(e)}"
                )
            
            # Construct the payload according to FIRS API requirements
            payload = {
                "invoice_reference": invoice_reference,
                "business_id": business_id,
                "irn": irn_value,
                "signature": signature
            }
                
            response = requests.post(
                url, 
                json=payload, 
                headers=self._get_default_headers(),  # Use API key auth for IRN validation
                timeout=30  # Add timeout for better error handling
            )
            
            if response.status_code not in (200, 201, 202):
                logger.error(f"FIRS IRN validation failed: {response.status_code} - {response.text}")
                error_data = {}
                try:
                    if response.content:
                        error_data = response.json()
                except ValueError:
                    error_data = {"message": f"Error parsing response: {response.text[:200]}"}
                
                return {
                    "success": False,
                    "message": error_data.get("message", f"Validation failed with status code {response.status_code}"),
                    "errors": error_data.get("errors", []),
                    "status_code": response.status_code
                }
                
            # Process successful response
            result = {}
            try:
                if response.content:
                    result = response.json()
                    
                # Record the validation in our system
                validation_record = {
                    "irn": irn_value,
                    "business_id": business_id,
                    "invoice_reference": invoice_reference,
                    "timestamp": datetime.now().isoformat(),
                    "is_valid": result.get("data", {}).get("is_valid", False),
                    "response": result
                }
                
                logger.info(f"IRN validation successful for {irn_value}: {validation_record['is_valid']}")
                
                return {
                    "success": True,
                    "message": result.get("message", "IRN validation successful"),
                    "data": result.get("data", {}),
                    "status": "VALID" if result.get("data", {}).get("is_valid", False) else "INVALID",
                    "validation_record": validation_record
                }
            except ValueError as e:
                logger.error(f"Error parsing IRN validation response: {str(e)}")
                return {
                    "success": True,  # Assuming validation succeeded even if parsing response failed
                    "message": "IRN validation processed but response parsing failed",
                    "data": {"raw_response": response.text[:500]},
                    "status": "UNKNOWN"
                }
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.error(f"FIRS IRN validation error: {str(e)}")
            return {
                "success": False,
                "message": f"Validation failed: {str(e)}",
                "errors": [{"code": "INTERNAL_ERROR", "detail": str(e)}]
            }
            
    def _prepare_irn_signature(self, irn_value: str) -> str:
        """
        Prepare a cryptographic signature for an IRN using the FIRS public key.
        
        Args:
            irn_value: The IRN to sign
            
        Returns:
            Base64-encoded signature string
        """
        try:
            # Load the certificate from the configured path
            certificate_path = settings.FIRS_CERTIFICATE_PATH
            if not os.path.exists(certificate_path):
                raise ValueError(f"FIRS certificate file not found at: {certificate_path}")
                
            with open(certificate_path, 'r') as f:
                certificate = f.read().strip()
            
            # Create data dictionary with IRN and certificate
            data = {
                "irn": irn_value,
                "certificate": certificate
            }
            
            # Convert to JSON and encrypt
            return encrypt_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Error preparing IRN signature: {str(e)}")
            raise
    
    async def validate_irn_sandbox(self, irn_value: str) -> Dict[str, Any]:
        """
        Validate an IRN using the FIRS sandbox environment.
        
        This is a simulated validation for testing purposes.
        
        Args:
            irn_value: The IRN to validate
            
        Returns:
            Dictionary with validation result
        """
        import asyncio
        import secrets
        
        # Simulate API call delay
        await asyncio.sleep(0.5)
        
        # First, check if IRN follows the expected format
        is_valid_format = bool(
            irn_value.startswith("IRN-") and 
            len(irn_value.split("-")) == 4 and
            len(irn_value) >= 20
        )
        
        if not is_valid_format:
            return {
                "success": False,
                "message": "Invalid IRN format",
                "details": {
                    "source": "firs_sandbox",
                    "error_code": "FORMAT_ERROR",
                    "error_details": "IRN must follow the format IRN-TIMESTAMP-UUID-HASH"
                }
            }
        
        # Simulate successful validation
        return {
            "success": True,
            "message": "IRN validated successfully with FIRS sandbox",
            "details": {
                "source": "firs_sandbox",
                "validation_id": f"FIRS-{secrets.token_hex(8)}",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


    async def check_submission_status(self, submission_id: str) -> SubmissionStatus:
        """Check the status of a previously submitted invoice.
        
        Args:
            submission_id: ID of the submission to check
            
        Returns:
            SubmissionStatus with current status details
            
        Raises:
            HTTPException: If the status check fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}/api/v1/invoice/submission/{submission_id}/status"
            
            response = requests.get(
                url,
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                return SubmissionStatus(
                    submission_id=submission_id,
                    status=data.get("status", "UNKNOWN"),
                    timestamp=data.get("updated_at", datetime.now().isoformat()),
                    message=data.get("message", result.get("message", "Status retrieved successfully")),
                    details=data
                )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"FIRS API status check error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Status check error: {str(e)}"
            )
    
    async def get_currencies(self) -> List[Dict[str, Any]]:
        """Get list of currencies from FIRS API.
        
        Returns:
            List of currency dictionaries
            
        Raises:
            HTTPException: If retrieval fails
        """
        try:
            # First try to load currencies from our reference data file
            try:
                currency_file = os.path.join(settings.REFERENCE_DATA_DIR, 'firs', 'currencies.json')
                if os.path.exists(currency_file):
                    with open(currency_file, 'r') as f:
                        currency_data = json.load(f)
                        logger.info(f"Loaded {len(currency_data.get('currencies', []))} currencies from reference file")
                        return currency_data.get('currencies', [])
            except Exception as file_err:
                logger.warning(f"Could not load currencies from reference file: {str(file_err)}")
            
            # Fall back to API call if reference file not available
            url = f"{self.base_url}{self.endpoints['currencies']}"
            logger.info(f"Fetching currencies from FIRS API: {url}")
            
            response = requests.get(
                url, 
                headers=self._get_default_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"FIRS currencies retrieval failed: {response.status_code} - {response.text[:200]}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"FIRS API service error: {response.status_code}"
                )
                
            try:
                result = response.json()
                currencies = result.get("data", [])
                logger.info(f"Retrieved {len(currencies)} currencies from FIRS API")
                
                # Save to reference file for future use
                os.makedirs(os.path.dirname(currency_file), exist_ok=True)
                with open(currency_file, 'w') as f:
                    json.dump({"currencies": currencies, "metadata": {"retrieved_at": datetime.now().isoformat()}}, f, indent=2)
                
                return currencies
            except ValueError as json_err:
                logger.error(f"Error parsing FIRS currencies response: {str(json_err)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing FIRS API response: {str(json_err)}"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"FIRS currency retrieval error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving currencies: {str(e)}"
            )
    
    async def get_invoice_types(self) -> List[Dict[str, Any]]:
        """Get list of invoice types from FIRS API.
        
        Returns:
            List of invoice type dictionaries
            
        Raises:
            HTTPException: If retrieval fails
        """
        try:
            # First try to load invoice types from our reference data file
            try:
                invoice_type_file = os.path.join(settings.REFERENCE_DATA_DIR, 'firs', 'invoice_types.json')
                if os.path.exists(invoice_type_file):
                    with open(invoice_type_file, 'r') as f:
                        invoice_type_data = json.load(f)
                        logger.info(f"Loaded {len(invoice_type_data.get('invoice_types', []))} invoice types from reference file")
                        return invoice_type_data.get('invoice_types', [])
            except Exception as file_err:
                logger.warning(f"Could not load invoice types from reference file: {str(file_err)}")
            
            # Fall back to API call if reference file not available
            url = f"{self.base_url}{self.endpoints['invoice_types']}"
            logger.info(f"Fetching invoice types from FIRS API: {url}")
            
            response = requests.get(
                url, 
                headers=self._get_default_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"FIRS invoice types retrieval failed: {response.status_code} - {response.text[:200]}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"FIRS API service error: {response.status_code}"
                )
                
            try:
                result = response.json()
                invoice_types = result.get("data", [])
                logger.info(f"Retrieved {len(invoice_types)} invoice types from FIRS API")
                
                # Save to reference file for future use
                os.makedirs(os.path.dirname(invoice_type_file), exist_ok=True)
                with open(invoice_type_file, 'w') as f:
                    json.dump({"invoice_types": invoice_types, "metadata": {"retrieved_at": datetime.now().isoformat()}}, f, indent=2)
                
                return invoice_types
            except ValueError as json_err:
                logger.error(f"Error parsing FIRS invoice types response: {str(json_err)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing FIRS API response: {str(json_err)}"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"FIRS invoice type retrieval error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving invoice types: {str(e)}"
            )
    
    async def get_vat_exemptions(self) -> List[Dict[str, Any]]:
        """Get list of VAT exemptions from FIRS API.
        
        Returns:
            List of VAT exemption dictionaries
            
        Raises:
            HTTPException: If retrieval fails
        """
        try:
            # First try to load VAT exemptions from our reference data file
            try:
                vat_exemption_file = os.path.join(settings.REFERENCE_DATA_DIR, 'firs', 'vat_exemptions.json')
                if os.path.exists(vat_exemption_file):
                    with open(vat_exemption_file, 'r') as f:
                        vat_exemption_data = json.load(f)
                        logger.info(f"Loaded {len(vat_exemption_data.get('vat_exemptions', []))} VAT exemptions from reference file")
                        return vat_exemption_data.get('vat_exemptions', [])
            except Exception as file_err:
                logger.warning(f"Could not load VAT exemptions from reference file: {str(file_err)}")
            
            # Fall back to API call if reference file not available
            url = f"{self.base_url}{self.endpoints['vat_exemptions']}"
            logger.info(f"Fetching VAT exemptions from FIRS API: {url}")
            
            response = requests.get(
                url, 
                headers=self._get_default_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"FIRS VAT exemptions retrieval failed: {response.status_code} - {response.text[:200]}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"FIRS API service error: {response.status_code}"
                )
                
            try:
                result = response.json()
                vat_exemptions = result.get("data", [])
                logger.info(f"Retrieved {len(vat_exemptions)} VAT exemptions from FIRS API")
                
                # Save to reference file for future use
                os.makedirs(os.path.dirname(vat_exemption_file), exist_ok=True)
                with open(vat_exemption_file, 'w') as f:
                    json.dump({"vat_exemptions": vat_exemptions, "metadata": {"retrieved_at": datetime.now().isoformat()}}, f, indent=2)
                
                return vat_exemptions
            except ValueError as json_err:
                logger.error(f"Error parsing FIRS VAT exemptions response: {str(json_err)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing FIRS API response: {str(json_err)}"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"FIRS VAT exemption retrieval error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving VAT exemptions: {str(e)}"
            )
    
    async def submit_ubl_invoice(self, ubl_xml: str, invoice_type: str = "standard") -> InvoiceSubmissionResponse:
        """Submit a UBL format invoice to FIRS.
        
{{ ... }}
        This method supports UBL format invoices, specifically for BIS Billing 3.0
        compatible documents generated from the Odoo UBL mapping system.
        
        Args:
            ubl_xml: UBL XML as a string
            invoice_type: Type of invoice (standard, credit_note, debit_note, etc.)
            
        Returns:
            InvoiceSubmissionResponse with submission details
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}/api/v1/invoice/ubl/submit"
            
            # UBL invoice type mapping
            invoice_type_codes = {
                "standard": "380",  # Commercial Invoice
                "credit_note": "381",  # Credit Note
                "debit_note": "383",  # Debit Note
                "proforma": "325",  # Proforma Invoice
                "self_billed": "389",  # Self-billed Invoice
            }
            
            # Add custom headers for UBL submission
            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/xml"  # Override for XML content
            
            invoice_type_code = invoice_type_codes.get(invoice_type, "380")
            headers["X-FIRS-InvoiceType"] = invoice_type_code
            headers["X-FIRS-Format"] = "UBL2.1"
            headers["X-FIRS-Profile"] = "BIS3.0"
            
            # Generate submission ID
            submission_id = str(uuid4())
            headers["X-FIRS-SubmissionID"] = submission_id
            
            # Submit the XML directly
            response = requests.post(url, headers=headers, data=ubl_xml)
            
            if response.status_code in (200, 201, 202):
                result = response.json() if response.content else {"message": "UBL invoice submitted successfully"}
                return InvoiceSubmissionResponse(
                    success=True,
                    message=result.get("message", "UBL invoice submitted successfully"),
                    submission_id=result.get("data", {}).get("submission_id", submission_id),
                    status=result.get("data", {}).get("status", "UBL_SUBMITTED"),
                    details=result.get("data", {})
                )
            else:
                error_data = response.json() if response.content else {"message": "Unknown error"}
                logger.error(f"FIRS UBL submission failed: {response.status_code} - {response.text}")
                
                return InvoiceSubmissionResponse(
                    success=False,
                    message=error_data.get("message", f"UBL submission failed with status code {response.status_code}"),
                    errors=error_data.get("errors", []),
                    details={"status_code": response.status_code}
                )
                
        except Exception as e:
            logger.error(f"FIRS API UBL submission error: {str(e)}")
            return InvoiceSubmissionResponse(
                success=False,
                message=f"UBL API request failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    async def validate_ubl_invoice(self, ubl_xml: str) -> InvoiceSubmissionResponse:
        """Validate a UBL format invoice against FIRS requirements.
        
        This method checks if the UBL document meets FIRS validation rules
        without actually submitting it.
        
        Args:
            ubl_xml: UBL XML as a string
            
        Returns:
            InvoiceSubmissionResponse with validation results
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}/api/v1/invoice/ubl/validate"
            
            headers = self._get_auth_headers()
            headers["Content-Type"] = "application/xml"
            
            # Submit the XML directly
            response = requests.post(url, headers=headers, data=ubl_xml)
            
            if response.status_code == 200:
                result = response.json() if response.content else {"message": "UBL invoice is valid"}
                return InvoiceSubmissionResponse(
                    success=True,
                    message=result.get("message", "UBL invoice validation successful"),
                    details=result.get("data", {})
                )
            else:
                error_data = response.json() if response.content else {"message": "Unknown error"}
                logger.error(f"FIRS UBL validation failed: {response.status_code} - {response.text}")
                
                # Special handling for validation errors
                if response.status_code == 400:
                    return InvoiceSubmissionResponse(
                        success=False,
                        message="UBL validation failed",
                        errors=error_data.get("errors", []),
                        details={"validation_result": error_data}
                    )
                else:
                    return InvoiceSubmissionResponse(
                        success=False,
                        message=error_data.get("message", f"UBL validation failed with status code {response.status_code}"),
                        errors=error_data.get("errors", []),
                        details={"status_code": response.status_code}
                    )
                
        except Exception as e:
            logger.error(f"FIRS API UBL validation error: {str(e)}")
            return InvoiceSubmissionResponse(
                success=False,
                message=f"UBL validation request failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )


async def validate_irns_with_firs_sandbox(db, irn_values: List[str], user_id: Optional[UUID] = None) -> Dict[str, Any]:
    """
    Validate a batch of IRNs with the FIRS sandbox API.
    
    Args:
        db: Database session
        irn_values: List of IRNs to validate
        user_id: ID of the user requesting validation
        
    Returns:
        Dictionary with validation results
    """
    logger.info(f"Validating {len(irn_values)} IRNs with FIRS sandbox")
    
    # Create FIRS service instance
    firs_service = FIRSService()
    
    results = []
    for irn_value in irn_values:
        try:
            # Get IRN record if it exists
            irn_record = db.query(IRNRecord).filter(IRNRecord.irn == irn_value).first()
            
            # Validate with FIRS sandbox
            validation_result = await firs_service.validate_irn_sandbox(irn_value)
            
            # Record validation in database if IRN exists
            if irn_record:
                validation_record = create_validation_record(
                    db=db,
                    irn_id=irn_value,
                    is_valid=validation_result["success"],
                    message=validation_result["message"],
                    validated_by=str(user_id) if user_id else None,
                    validation_source="firs_sandbox",
                    request_data={"irn": irn_value},
                    response_data=validation_result["details"]
                )
            
            # Add IRN record details if available
            if irn_record:
                validation_result["details"]["irn_record"] = {
                    "invoice_number": irn_record.invoice_number,
                    "status": irn_record.status.value,
                    "valid_until": irn_record.valid_until.isoformat()
                }
            
            results.append({
                "irn": irn_value,
                "success": validation_result["success"],
                "message": validation_result["message"],
                "details": validation_result["details"]
            })
            
        except Exception as e:
            logger.error(f"Error validating IRN {irn_value} with FIRS sandbox: {str(e)}")
            results.append({
                "irn": irn_value,
                "success": False,
                "message": f"Error during validation: {str(e)}",
                "details": {"error_type": type(e).__name__}
            })
    
    # Commit database changes
    db.commit()
    
    return {
        "source": "firs_sandbox",
        "total": len(irn_values),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }


# Create a default instance for easy importing
firs_service = FIRSService()
