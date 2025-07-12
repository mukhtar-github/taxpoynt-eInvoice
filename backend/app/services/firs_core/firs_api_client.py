"""FIRS Core API Client Service.

This service implements the core FIRS API client functionality used by both
System Integrator (SI) and Access Point Provider (APP) components.

Core responsibilities:
- FIRS API authentication and session management
- Base API communication methods
- Common FIRS API utilities
- Shared API response handling

This service is part of the firs_core package and provides foundation
API capabilities for both SI and APP specific services.
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
from app.services.firs_si.irn_generation_service import create_validation_record
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
        
        # Verify configuration
        missing_config = []
        if not self.base_url:
            missing_config.append("API URL")
        if not self.api_key:
            missing_config.append("API Key")
        if not self.api_secret:
            missing_config.append("API Secret")
            
        if missing_config:
            logger.warning(f"FIRS service initialized with missing configuration: {', '.join(missing_config)}")
            
        # Authentication state
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
        # Session configuration for consistent connection handling
        self.session = requests.Session()
        self.session.headers.update(self._get_default_headers())
        
        # Connection settings
        self.default_timeout = 30  # Default timeout in seconds
        self.submission_timeout = 60  # Longer timeout for submissions
        
        # API endpoint paths based on reference data
        self.endpoints = {
            # Health check endpoint
            "health_check": "/api",
            
            # Authentication endpoints
            "authenticate": "/api/v1/utilities/authenticate",
            "verify_tin": "/api/v1/utilities/verify-tin",
            
            # Invoice management endpoints
            "irn_validate": "/api/v1/invoice/irn/validate",
            "invoice_validate": "/api/v1/invoice/validate",
            "invoice_sign": "/api/v1/invoice/sign",
            "download_invoice": "/api/v1/invoice/download/{IRN}",  # IRN as path parameter
            "confirm_invoice": "/api/v1/invoice/confirm/{IRN}",  # IRN as path parameter
            "submit_invoice": "/api/v1/invoice/submit",
            "submit_batch": "/api/v1/invoice/batch/submit",
            "update_invoice": "/api/v1/invoice/update/{IRN}",  # IRN as path parameter
            "search_invoice": "/api/v1/invoice/{BUSINESS_ID}",  # BUSINESS_ID as path parameter
            "transact": "/api/v1/invoice/transact",
            
            # Entity/Party management endpoints
            "entity_search": "/api/v1/entity",
            "entity_get": "/api/v1/entity/{ENTITY_ID}",  # ENTITY_ID as path parameter
            "create_party": "/api/v1/invoice/party",
            "get_party": "/api/v1/invoice/party/{PARTY_ID}",  # PARTY_ID as path parameter
            
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
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "TaxPoynt-eInvoice/1.0"
        }
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with auth token for API requests."""
        headers = self._get_default_headers()
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
        
    def _handle_api_response(self, response: requests.Response, operation_name: str, success_codes: List[int] = None) -> Dict[str, Any]:
        """
        Handle API responses consistently with proper error management.
        
        Args:
            response: The HTTP response from the FIRS API
            operation_name: Name of the operation for logging
            success_codes: List of status codes considered successful (defaults to [200, 201, 202])
            
        Returns:
            Parsed JSON response data
            
        Raises:
            HTTPException: If the response indicates an error
        """
        if success_codes is None:
            success_codes = [200, 201, 202]
        
        # Log detailed response info in sandbox mode
        if self.use_sandbox:
            logger.debug(f"FIRS {operation_name} response status: {response.status_code}")
            logger.debug(f"FIRS {operation_name} response headers: {dict(response.headers)}")
            if response.content and len(response.content) < 1000:
                logger.debug(f"FIRS {operation_name} response body: {response.text}")
            else:
                logger.debug(f"FIRS {operation_name} response body preview: {response.text[:500]}...")
        
        # Try to parse JSON response if present
        result = {}
        content_type = response.headers.get('content-type', '')
        
        if response.content:
            try:
                if 'application/json' in content_type:
                    result = response.json()
                elif response.content.strip().startswith(b'{') and response.content.strip().endswith(b'}'): 
                    # Some APIs return JSON without proper content type
                    try:
                        result = json.loads(response.content)
                    except json.JSONDecodeError:
                        logger.warning(f"Content looks like JSON but failed to parse: {response.text[:200]}")
                        result = {"message": response.text[:200]}
                else:
                    # Handle non-JSON responses
                    logger.warning(f"Non-JSON response: {content_type} - {response.text[:200]}")
                    result = {"message": response.text[:200], "content_type": content_type}
            except ValueError as e:
                logger.warning(f"Failed to parse response: {str(e)}")
                result = {"message": f"Invalid response format: {response.text[:200]}"}
        
        # Check if the response is successful
        if response.status_code in success_codes:
            return result
        
        # Handle various error conditions
        error_detail = result.get("message", f"Operation failed with status {response.status_code}")
        errors = result.get("errors", [])
        
        if response.status_code == 400:
            # Bad request - likely validation errors
            error_msg = f"FIRS {operation_name} validation failed: {error_detail}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": error_msg,
                    "errors": errors,
                    "environment": "sandbox" if self.use_sandbox else "production"
                }
            )
        elif response.status_code == 401 or response.status_code == 403:
            # Authentication or authorization failure
            error_msg = f"FIRS {operation_name} authorization failed: {error_detail}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": error_msg,
                    "environment": "sandbox" if self.use_sandbox else "production"
                }
            )
        elif response.status_code == 404:
            # Resource not found
            error_msg = f"FIRS {operation_name} resource not found: {error_detail}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": error_msg,
                    "environment": "sandbox" if self.use_sandbox else "production"
                }
            )
        elif response.status_code == 429:
            # Rate limiting
            retry_after = response.headers.get('Retry-After', '60')
            error_msg = f"FIRS {operation_name} rate limited. Retry after {retry_after} seconds."
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": error_msg,
                    "retry_after": retry_after,
                    "environment": "sandbox" if self.use_sandbox else "production"
                }
            )
        else:
            # Other unexpected errors
            error_msg = f"FIRS {operation_name} failed: {error_detail}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": error_msg,
                    "status_code": response.status_code,
                    "errors": errors,
                    "environment": "sandbox" if self.use_sandbox else "production"
                }
            )
    
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
            
            # Use session for consistency
            response = self.session.post(
                url, 
                json=payload,
                timeout=self.default_timeout
            )
            
            # Log additional details in sandbox mode
            if self.use_sandbox:
                logger.debug(f"FIRS sandbox auth response status: {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    logger.debug(f"FIRS sandbox auth response preview: {response.text[:200]}")
            
            if response.status_code != 200:
                logger.error(f"FIRS authentication failed: {response.text}")
                try:
                    error_data = response.json()
                    error_detail = error_data.get("message", "Authentication failed")
                    error_code = error_data.get("code", response.status_code)
                except ValueError:
                    error_detail = f"Authentication failed with status code {response.status_code}"
                    error_code = response.status_code
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "message": f"FIRS API authentication failed: {error_detail}",
                        "code": error_code,
                        "environment": "sandbox" if self.use_sandbox else "production"
                    }
                )
            
            try:
                auth_response = response.json()
                
                # Store token and set expiry
                self.token = auth_response["data"]["access_token"]
                self.token_expiry = datetime.now() + timedelta(seconds=auth_response["data"]["expires_in"])
                
                # Update session headers with the new token
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                logger.info(f"Successfully authenticated with FIRS API as {email}")
                logger.info(f"Token will expire at {self.token_expiry.isoformat()}")
                
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
                detail={
                    "message": f"FIRS API service unavailable: {str(e)}",
                    "environment": "sandbox" if self.use_sandbox else "production"
                }
            )
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token.
        
        This is a helper method and should be used internally before making
        API calls that require authentication. If no credentials are provided,
        it will raise an exception.
        """
        if not self.token or not self.token_expiry or datetime.now() >= self.token_expiry:
            # In a production environment, this would attempt to refresh the token
            # rather than immediately failing
            logger.warning("Authentication token missing or expired")
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
            
            url = f"{self.base_url}{self.endpoints['irn_validate']}"
            
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
            irn: Invoice Reference Number (IRN) as path parameter
            
        Returns:
            Dictionary with invoice PDF data containing base64-encoded PDF
            
        Raises:
            HTTPException: If the download fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['download_invoice'].replace('{IRN}', irn)}"
            
            response = requests.get(
                url, 
                headers=self._get_auth_headers(),
                timeout=60  # Longer timeout for potentially large PDF downloads
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Invoice with IRN {irn} not found"
                )
            else:
                logger.error(f"Invoice download failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API invoice download failed"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def check_health(self) -> Dict[str, Any]:
        """Check the health status of the FIRS API.
        
        Returns:
            Dictionary with health status information
        
        Raises:
            HTTPException: If the health check fails
        """
        try:
            url = f"{self.base_url}{self.endpoints['health_check']}"
            
            response = requests.get(
                url,
                headers=self._get_default_headers(),
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Health check failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="FIRS API health check failed"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API health check failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API health check failed: {str(e)}"
            )
    
    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Get entity details by ID from FIRS API.
        
        Args:
            entity_id: The entity ID to look up
            
        Returns:
            Dictionary with entity details
            
        Raises:
            HTTPException: If the entity lookup fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['entity_get'].replace('{ENTITY_ID}', entity_id)}"
            
            response = requests.get(
                url, 
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Entity with ID {entity_id} not found"
                )
            else:
                logger.error(f"Entity lookup failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API entity lookup failed"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def search_entities(self, search_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for entities using provided parameters.
        
        Args:
            search_params: Dictionary of search parameters such as:
                - size: Number of items per page
                - page: Page number
                - sort_by: Field to sort by
                - sort_direction_desc: Whether to sort descending
                - reference: Search by reference
                
        Returns:
            Dictionary with search results
            
        Raises:
            HTTPException: If the search fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['entity_search']}"
            
            # Add search parameters to URL
            if search_params:
                query_params = "&".join([f"{key}={value}" for key, value in search_params.items()])
                url = f"{url}?{query_params}"
            
            response = requests.get(
                url, 
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Entity search failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API entity search failed"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def create_party(self, party_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new party in the FIRS system.
        
        Args:
            party_data: Complete party data following FIRS specification
            
        Returns:
            Dictionary with the created party details
            
        Raises:
            HTTPException: If the party creation fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['create_party']}"
            
            response = requests.post(
                url, 
                json=party_data, 
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("message", "Party creation failed")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": error_detail,
                        "errors": error_data.get("errors", [])
                    }
                )
            else:
                logger.error(f"Party creation failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API party creation failed"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def get_party(self, party_id: str) -> Dict[str, Any]:
        """Get party details by ID from FIRS API.
        
        Args:
            party_id: The party ID to look up
            
        Returns:
            Dictionary with party details
            
        Raises:
            HTTPException: If the party lookup fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['get_party'].replace('{PARTY_ID}', party_id)}"
            
            response = requests.get(
                url, 
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Party with ID {party_id} not found"
                )
            else:
                logger.error(f"Party lookup failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API party lookup failed"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def confirm_invoice(self, irn: str) -> Dict[str, Any]:
        """Confirm an invoice in the FIRS system.
        
        Args:
            irn: The Invoice Reference Number (IRN) to confirm
            
        Returns:
            Dictionary with confirmation result
            
        Raises:
            HTTPException: If the confirmation fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['confirm_invoice'].replace('{IRN}', irn)}"
            
            response = requests.get(
                url, 
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Invoice with IRN {irn} not found"
                )
            else:
                logger.error(f"Invoice confirmation failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API invoice confirmation failed"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def search_invoices(self, business_id: str, search_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for invoices for a specific business.
        
        Args:
            business_id: The business ID to search invoices for
            search_params: Dictionary of search parameters such as:
                - size: Number of items per page
                - page: Page number
                - sort_by: Field to sort by
                - sort_direction_desc: Whether to sort descending
                - irn: Search by IRN
                - payment_status: Filter by payment status
                - invoice_type_code: Filter by invoice type
                
        Returns:
            Dictionary with search results
            
        Raises:
            HTTPException: If the search fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['search_invoice'].replace('{BUSINESS_ID}', business_id)}"
            
            # Add search parameters to URL
            if search_params:
                query_params = "&".join([f"{key}={value}" for key, value in search_params.items()])
                url = f"{url}?{query_params}"
            
            response = requests.get(
                url, 
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Invoice search failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API invoice search failed"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
    
    async def update_invoice(self, irn: str, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing invoice in the FIRS system.
        
        Args:
            irn: The Invoice Reference Number (IRN) to update
            invoice_data: Updated invoice data following FIRS specification
            
        Returns:
            Dictionary with the updated invoice details
            
        Raises:
            HTTPException: If the update fails
        """
        try:
            await self._ensure_authenticated()
            
            url = f"{self.base_url}{self.endpoints['update_invoice'].replace('{IRN}', irn)}"
            
            response = requests.patch(
                url, 
                json=invoice_data, 
                headers=self._get_auth_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("message", "Invoice update failed")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": error_detail,
                        "errors": error_data.get("errors", [])
                    }
                )
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Invoice with IRN {irn} not found"
                )
            else:
                logger.error(f"Invoice update failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="FIRS API invoice update failed"
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
        Submit a single invoice to FIRS API.
        
        Args:
            invoice_data: Invoice data in FIRS-compliant format (BIS Billing 3.0 / UBL)
            
        Returns:
            InvoiceSubmissionResponse with submission details
        """
        invoice_reference = invoice_data.get('irn', '') or invoice_data.get('invoice_number', 'Unknown')
        
        try:
            # Ensure authentication token is available and valid
            try:
                await self._ensure_authenticated()
            except HTTPException as auth_err:
                logger.warning(f"Authentication error during invoice submission for {invoice_reference}: {str(auth_err)}")
                # For sandbox, we might still try to submit with just API key authentication
                if not self.use_sandbox:
                    raise
                logger.info("Proceeding with API key authentication for sandbox environment")
            
            url = f"{self.base_url}{self.endpoints['submit_invoice']}"
            logger.info(f"Submitting invoice {invoice_reference} to FIRS API: {url}")
            
            # Log more details in sandbox mode
            if self.use_sandbox:
                logger.debug(f"Sandbox submission for invoice: {invoice_reference}")
                # Truncate large payloads to avoid excessive logging
                logger.debug(f"Invoice data sample: {json.dumps(invoice_data)[:500]}...")
            
            # Validate invoice against required fields for FIRS API
            # Updated required fields based on BIS Billing 3.0 / UBL standard
            required_fields = [
                'business_id', 'irn', 'issue_date', 'invoice_type_code', 
                'document_currency_code', 'accounting_supplier_party', 
                'accounting_customer_party', 'legal_monetary_total', 'invoice_line'
            ]
            missing_fields = [field for field in required_fields if field not in invoice_data]
            
            if missing_fields:
                logger.error(f"Invoice {invoice_reference} missing required fields: {missing_fields}")
                return InvoiceSubmissionResponse(
                    success=False,
                    message=f"Invoice data missing required fields: {', '.join(missing_fields)}",
                    errors=[{"code": "VALIDATION_ERROR", "detail": f"Missing field: {field}"} for field in missing_fields]
                )
            
            # Prepare request with proper headers
            headers = self._get_auth_headers()
            
            # Track submission start time for performance monitoring
            start_time = datetime.now()
            
            # Submit the invoice with comprehensive error handling
            try:
                # Use session for consistent connection handling
                response = self.session.post(
                    url, 
                    json=invoice_data, 
                    headers=headers,
                    timeout=self.submission_timeout
                )
                
                # Calculate response time for monitoring
                response_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"FIRS API response time: {response_time:.2f} seconds")
                
                # Enhanced logging for sandbox environment
                if self.use_sandbox:
                    logger.debug(f"Sandbox response status: {response.status_code}")
                    logger.debug(f"Sandbox response headers: {dict(response.headers)}")
                
                # Try to parse JSON response with fallback handling
                result = {}
                if response.content:
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        try:
                            result = response.json()
                        except ValueError as json_err:
                            logger.warning(f"Could not parse JSON response: {str(json_err)}")
                            result = {"message": f"Invalid JSON response: {response.text[:200]}"}
                    else:
                        logger.warning(f"Unexpected content type: {content_type}")
                        result = {"message": f"Unexpected response format: {response.text[:200]}"}
                
                # Handle various response status codes
                if response.status_code in (200, 201, 202):
                    # Successfully submitted - parse the response
                    submission_data = result.get("data", {})
                    submission_id = submission_data.get("submission_id", None)
                    
                    # Generate a submission ID if none provided (especially in sandbox)
                    if submission_id is None:
                        submission_id = str(uuid4())
                        logger.info(f"Generated submission ID for tracking: {submission_id}")
                    
                    # Log the successful submission
                    logger.info(f"Invoice {invoice_reference} submitted successfully with ID: {submission_id}")
                    
                    return InvoiceSubmissionResponse(
                        success=True,
                        message=result.get("message", "Invoice submitted successfully"),
                        submission_id=submission_id,
                        status=result.get("status", "SUBMITTED"),
                        details=submission_data
                    )
                elif response.status_code == 400:
                    # Handle validation errors
                    logger.error(f"FIRS invoice validation failed: {response.text[:500]}")
                    return InvoiceSubmissionResponse(
                        success=False,
                        message=result.get("message", "Validation failed"),
                        errors=result.get("errors", [{"code": "VALIDATION_ERROR", "detail": response.text[:200]}]),
                        status="VALIDATION_FAILED"
                    )
                elif response.status_code == 401:
                    # Authentication issue
                    logger.error("FIRS API authentication failed during submission")
                    return InvoiceSubmissionResponse(
                        success=False,
                        message="Authentication failed. Please re-authenticate.",
                        errors=[{"code": "AUTH_ERROR", "detail": result.get("message", "Unauthorized")}],
                        status="AUTH_FAILED"
                    )
                elif response.status_code == 429:
                    # Rate limiting
                    retry_after = response.headers.get('Retry-After', '60')
                    logger.warning(f"FIRS API rate limit exceeded. Retry after {retry_after} seconds")
                    return InvoiceSubmissionResponse(
                        success=False,
                        message=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                        errors=[{"code": "RATE_LIMIT", "detail": "Too many requests"}],
                        status="RATE_LIMITED"
                    )
                else:
                    # Other error conditions
                    logger.error(f"FIRS invoice submission failed with status {response.status_code}: {response.text[:500]}")
                    return InvoiceSubmissionResponse(
                        success=False,
                        message=result.get("message", f"Submission failed with status code {response.status_code}"),
                        errors=result.get("errors", [{"code": f"HTTP_{response.status_code}", "detail": "Unexpected error"}]),
                        status="FAILED"
                    )
                    
            except requests.RequestException as req_err:
                logger.error(f"Request error during invoice submission for {invoice_reference}: {str(req_err)}")
                return InvoiceSubmissionResponse(
                    success=False,
                    message=f"API connection failed: {str(req_err)}",
                    errors=[{"code": "CONNECTION_ERROR", "detail": str(req_err)}],
                    status="CONNECTION_FAILED"
                )
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.error(f"FIRS API submission error for {invoice_reference}: {str(e)}", exc_info=True)
            return InvoiceSubmissionResponse(
                success=False,
                message=f"API request failed: {str(e)}",
                errors=[{"code": "INTERNAL_ERROR", "detail": str(e)}],
                status="ERROR",
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
        """
        Check the status of a submitted invoice.
        
        Args:
            submission_id: The ID of the submission to check
            
        Returns:
            SubmissionStatus object with current status details
        """
        try:
            # Ensure we have authentication
            try:
                await self._ensure_authenticated()
            except HTTPException as auth_err:
                logger.warning(f"Authentication error during status check for {submission_id}: {str(auth_err)}")
                # For sandbox, continue with API key authentication
                if not self.use_sandbox:
                    raise
                logger.info("Proceeding with API key authentication for sandbox status check")
            
            # Construct the status check URL
            url = f"{self.base_url}/api/v1/invoice/submission/{submission_id}"
            logger.info(f"Checking submission status for ID: {submission_id} at {url}")
            
            # Make the request with session for consistency
            response = self.session.get(
                url,
                headers=self._get_auth_headers(),
                timeout=self.default_timeout
            )
            
            # Log detailed response in sandbox mode
            if self.use_sandbox:
                logger.debug(f"Sandbox status check response code: {response.status_code}")
                if response.content:
                    logger.debug(f"Sandbox status response preview: {response.text[:200]}")
            
            # Process the response based on status code
            if response.status_code == 200:
                # Successfully retrieved status
                try:
                    result = response.json()
                    status_data = result.get("data", {})
                    
                    # Extract status information
                    status_code = status_data.get("status", "UNKNOWN")
                    status_message = status_data.get("message", "Status check completed")
                    timestamp = status_data.get("timestamp", datetime.now().isoformat())
                    details = status_data.get("details", {})
                    
                    logger.info(f"Submission {submission_id} status: {status_code}")
                    
                    return SubmissionStatus(
                        submission_id=submission_id,
                        status=status_code,
                        timestamp=timestamp,
                        message=status_message,
                        details=details
                    )
                except (ValueError, KeyError) as parse_err:
                    logger.error(f"Error parsing status response: {str(parse_err)}")
                    # For sandbox environment, create a simulated response if parsing fails
                    if self.use_sandbox:
                        logger.info(f"Creating simulated status response for sandbox submission {submission_id}")
                        return SubmissionStatus(
                            submission_id=submission_id,
                            status="PROCESSING",
                            timestamp=datetime.now().isoformat(),
                            message="Sandbox simulated status",
                            details={"environment": "sandbox", "simulated": True}
                        )
                    
                    # For production, raise the error
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error parsing FIRS API status response: {str(parse_err)}"
                    )
            elif response.status_code == 404:
                # Submission not found
                logger.warning(f"Submission {submission_id} not found")
                
                # In sandbox, we might want to simulate a status even if not found
                if self.use_sandbox:
                    return SubmissionStatus(
                        submission_id=submission_id,
                        status="NOT_FOUND",
                        timestamp=datetime.now().isoformat(),
                        message="Submission ID not found in sandbox environment",
                        details={"environment": "sandbox", "simulated": True}
                    )
                
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Submission ID {submission_id} not found"
                )
            elif response.status_code == 401:
                # Authentication failed
                logger.error("Authentication failed during status check")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed. Please re-authenticate."
                )
            else:
                # Other error conditions
                logger.error(f"Status check failed with code {response.status_code}: {response.text[:200]}")
                
                # For sandbox, provide a fallback response
                if self.use_sandbox:
                    return SubmissionStatus(
                        submission_id=submission_id,
                        status="ERROR",
                        timestamp=datetime.now().isoformat(),
                        message=f"Sandbox status check failed with code {response.status_code}",
                        details={"error": response.text[:200], "environment": "sandbox"}
                    )
                
                # For production, raise an error
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"FIRS API status check failed with status code {response.status_code}"
                )
                
        except requests.RequestException as e:
            logger.error(f"FIRS API request failed during status check: {str(e)}")
            
            # For sandbox, provide a fallback response
            if self.use_sandbox:
                return SubmissionStatus(
                    submission_id=submission_id,
                    status="CONNECTION_ERROR",
                    timestamp=datetime.now().isoformat(),
                    message=f"Error connecting to sandbox API: {str(e)}",
                    details={"error_type": "connection", "environment": "sandbox"}
                )
            
            # For production, raise the error
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"FIRS API service unavailable: {str(e)}"
            )
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.error(f"Unexpected error during status check: {str(e)}", exc_info=True)
            
            # For sandbox, provide a fallback response
            if self.use_sandbox:
                return SubmissionStatus(
                    submission_id=submission_id,
                    status="ERROR",
                    timestamp=datetime.now().isoformat(),
                    message=f"Unexpected error in sandbox environment: {str(e)}",
                    details={"error_type": type(e).__name__, "environment": "sandbox"}
                )
            
            # For production, raise the error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Status check failed: {str(e)}"
            )
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
    
    async def get_service_codes(self) -> List[Dict[str, Any]]:
        """Get list of service codes from FIRS API.
        
        Returns:
            List of service code dictionaries
            
        Raises:
            HTTPException: If retrieval fails
        """
        try:
            # First try to load service codes from our reference data file
            try:
                service_codes_file = os.path.join(settings.REFERENCE_DATA_DIR, 'firs', 'service_codes.json')
                if os.path.exists(service_codes_file):
                    with open(service_codes_file, 'r') as f:
                        service_codes_data = json.load(f)
                        logger.info(f"Loaded {len(service_codes_data.get('service_codes', []))} service codes from reference file")
                        return service_codes_data.get('service_codes', [])
            except Exception as file_err:
                logger.warning(f"Could not load service codes from reference file: {str(file_err)}")
            
            # Fall back to API call if reference file not available
            url = f"{self.base_url}{self.endpoints['service_codes']}"
            logger.info(f"Fetching service codes from FIRS API: {url}")
            
            response = requests.get(
                url, 
                headers=self._get_default_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"FIRS service codes retrieval failed: {response.status_code} - {response.text[:200]}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"FIRS API service error: {response.status_code}"
                )
                
            try:
                result = response.json()
                service_codes = result.get("data", [])
                logger.info(f"Retrieved {len(service_codes)} service codes from FIRS API")
                
                # Save to reference file for future use
                os.makedirs(os.path.dirname(service_codes_file), exist_ok=True)
                with open(service_codes_file, 'w') as f:
                    json.dump({"service_codes": service_codes, "metadata": {"retrieved_at": datetime.now().isoformat()}}, f, indent=2)
                
                return service_codes
            except ValueError as json_err:
                logger.error(f"Error parsing FIRS service codes response: {str(json_err)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing FIRS API response: {str(json_err)}"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"FIRS service codes retrieval error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving service codes: {str(e)}"
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


# Enhanced FIRS API Client with OAuth 2.0 and TLS 1.3 Security
import aiohttp
import ssl
import asyncio
import os
from typing import Dict, Any, Optional


class FIRSAuthenticationError(Exception):
    """Exception raised for FIRS authentication failures"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code or "AUTH_ERROR"
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()


class FIRSAPIClient:
    """
    Official FIRS API client implementation with modern security features
    
    This client implements OAuth 2.0 authentication and TLS 1.3 security
    for secure communication with FIRS systems, complementing the existing
    FIRSService class with enhanced security capabilities.
    
    Features:
    - OAuth 2.0 client credentials flow
    - TLS 1.3 with certificate verification
    - Async aiohttp-based communication
    - FIRS-compliant payload preparation
    - Comprehensive error handling
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FIRS API client with enhanced security configuration
        
        Args:
            config: Configuration dictionary containing:
                - firs_api_base_url: Base URL for FIRS API
                - firs_client_id: OAuth 2.0 client ID
                - firs_client_secret: OAuth 2.0 client secret
                - sandbox_mode: Boolean for sandbox/production mode
                - ssl_cert_path: Path to SSL certificate file (optional)
        """
        self.base_url = config.get('firs_api_base_url')
        self.client_id = config.get('firs_client_id')
        self.client_secret = config.get('firs_client_secret')
        self.sandbox_mode = config.get('sandbox_mode', True)
        self.ssl_cert_path = config.get('ssl_cert_path')

        # FIRS-required TLS configuration
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3

        # Load custom certificate if provided
        if self.ssl_cert_path and os.path.exists(self.ssl_cert_path):
            self.ssl_context.load_verify_locations(self.ssl_cert_path)
            logger.info(f"Loaded FIRS SSL certificate from: {self.ssl_cert_path}")

        # Authentication state
        self._access_token = None
        self._token_expires_at = None
        self._refresh_token = None
        
        # Session management
        self._session = None
        
        logger.info(f"FIRS API client initialized for {'sandbox' if self.sandbox_mode else 'production'} mode")

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()

    async def _ensure_session(self):
        """Ensure aiohttp session is available"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                ssl=self.ssl_context,
                limit=100,
                limit_per_host=30,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'TaxPoynt-eInvoice/2.0 (FIRS-API-Client)',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )

    async def _close_session(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def authenticate_with_firs(self) -> Dict[str, Any]:
        """
        Authenticate with FIRS using OAuth 2.0 Client Credentials Flow
        
        FIRS Requirement: OAuth 2.0 authentication for secure API access
        
        Returns:
            Dictionary containing authentication details and session info
        """
        await self._ensure_session()
        
        # Prepare OAuth 2.0 client credentials payload
        auth_payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'invoice:submit invoice:validate invoice:status invoice:query'
        }

        # OAuth 2.0 requires form-encoded data
        auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

        try:
            auth_url = f"{self.base_url}/oauth/token"
            logger.info(f"Authenticating with FIRS OAuth 2.0 at: {auth_url}")
            
            async with self._session.post(
                auth_url,
                data=auth_payload,
                headers=auth_headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"FIRS OAuth authentication failed: {response.status} - {error_text}")
                    
                    raise FIRSAuthenticationError(
                        f"FIRS authentication failed: HTTP {response.status}",
                        error_code="OAUTH_FAILED",
                        details={
                            "status_code": response.status,
                            "response": error_text[:500],
                            "url": auth_url
                        }
                    )

                auth_result = await response.json()
                
                # Store authentication details
                self._access_token = auth_result['access_token']
                expires_in = auth_result.get('expires_in', 3600)
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                self._refresh_token = auth_result.get('refresh_token')

                logger.info(f"FIRS OAuth authentication successful. Token expires at: {self._token_expires_at}")
                
                return {
                    'authenticated': True,
                    'token_type': auth_result.get('token_type', 'Bearer'),
                    'expires_at': self._token_expires_at.isoformat(),
                    'expires_in': expires_in,
                    'scope': auth_result.get('scope', ''),
                    'firs_session_id': auth_result.get('session_id'),
                    'sandbox_mode': self.sandbox_mode
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"FIRS OAuth authentication network error: {str(e)}")
            raise FIRSAuthenticationError(
                f"Network error during FIRS authentication: {str(e)}",
                error_code="NETWORK_ERROR",
                details={"error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error(f"Unexpected error during FIRS authentication: {str(e)}")
            raise FIRSAuthenticationError(
                f"Unexpected authentication error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                details={"error_type": type(e).__name__}
            )

    async def _is_authenticated(self) -> bool:
        """Check if client is authenticated with valid token"""
        if not self._access_token or not self._token_expires_at:
            return False
        
        # Check if token will expire in the next 5 minutes
        expiry_buffer = timedelta(minutes=5)
        return datetime.utcnow() < (self._token_expires_at - expiry_buffer)

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        if not await self._is_authenticated():
            await self.authenticate_with_firs()
        
        return {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
            'X-FIRS-Version': '2025.1',
            'X-Client-Mode': 'sandbox' if self.sandbox_mode else 'production'
        }

    async def submit_invoice_to_firs(
        self,
        invoice_data: Dict[str, Any],
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Submit invoice to FIRS for processing with enhanced security
        
        FIRS Requirement: Secure submission with TLS 1.3 encryption
        
        Args:
            invoice_data: Invoice data in FIRS-compliant format
            organization_id: UUID of the organization submitting the invoice
            
        Returns:
            Dictionary containing submission results
        """
        await self._ensure_session()
        
        # Ensure we have valid authentication
        if not await self._is_authenticated():
            await self.authenticate_with_firs()

        # Prepare FIRS-compliant payload
        firs_payload = await self._prepare_firs_invoice_payload(
            invoice_data=invoice_data,
            organization_id=organization_id
        )

        # Create secure headers with organization context
        headers = await self._get_auth_headers()
        headers.update({
            'X-Organization-ID': str(organization_id),
            'X-Submission-Timestamp': datetime.utcnow().isoformat(),
            'X-Request-ID': str(uuid4())
        })

        try:
            submission_url = f"{self.base_url}/api/v1/invoice/submit"
            logger.info(f"Submitting invoice to FIRS: {submission_url}")
            
            async with self._session.post(
                submission_url,
                json=firs_payload,
                headers=headers
            ) as response:
                
                firs_response = await response.json()
                
                if response.status == 200:
                    logger.info(f"Invoice submitted successfully to FIRS: {firs_response.get('submission_id')}")
                    return {
                        'status': 'SUCCESS',
                        'firs_irn': firs_response.get('irn'),
                        'submission_id': firs_response.get('submission_id'),
                        'firs_timestamp': firs_response.get('timestamp'),
                        'processing_status': firs_response.get('processing_status', 'PENDING'),
                        'firs_reference': firs_response.get('reference'),
                        'validation_status': firs_response.get('validation_status', 'VALID')
                    }
                else:
                    logger.error(f"Invoice submission failed: {response.status} - {firs_response}")
                    return {
                        'status': 'FAILED',
                        'error_code': firs_response.get('error_code'),
                        'error_message': firs_response.get('message'),
                        'firs_reference': firs_response.get('reference'),
                        'validation_errors': firs_response.get('validation_errors', [])
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error during invoice submission: {str(e)}")
            return {
                'status': 'FAILED',
                'error_code': 'NETWORK_ERROR',
                'error_message': f"Network error: {str(e)}",
                'error_type': type(e).__name__
            }
        except Exception as e:
            logger.error(f"Unexpected error during invoice submission: {str(e)}")
            return {
                'status': 'FAILED',
                'error_code': 'UNEXPECTED_ERROR',
                'error_message': f"Unexpected error: {str(e)}",
                'error_type': type(e).__name__
            }

    async def validate_invoice_with_firs(
        self,
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate invoice against FIRS rules without submission
        
        FIRS Requirement: Pre-submission validation capability
        
        Args:
            invoice_data: Invoice data to validate
            
        Returns:
            Dictionary containing validation results
        """
        await self._ensure_session()
        
        if not await self._is_authenticated():
            await self.authenticate_with_firs()

        validation_payload = await self._prepare_firs_validation_payload(invoice_data)

        headers = await self._get_auth_headers()
        headers.update({
            'X-Validation-Mode': 'pre-submission',
            'X-Request-ID': str(uuid4())
        })

        try:
            validation_url = f"{self.base_url}/api/v1/invoice/validate"
            logger.info(f"Validating invoice with FIRS: {validation_url}")
            
            async with self._session.post(
                validation_url,
                json=validation_payload,
                headers=headers
            ) as response:
                
                validation_result = await response.json()
                
                return {
                    'validation_status': 'VALID' if response.status == 200 else 'INVALID',
                    'firs_validation_id': validation_result.get('validation_id'),
                    'schema_compliance': validation_result.get('schema_valid', False),
                    'business_rules_compliance': validation_result.get('business_rules_valid', False),
                    'tax_compliance': validation_result.get('tax_valid', False),
                    'validation_errors': validation_result.get('errors', []),
                    'validation_warnings': validation_result.get('warnings', []),
                    'validation_timestamp': validation_result.get('timestamp'),
                    'firs_version': validation_result.get('api_version', '2025.1')
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during invoice validation: {str(e)}")
            return {
                'validation_status': 'ERROR',
                'error_code': 'NETWORK_ERROR',
                'error_message': f"Network error: {str(e)}",
                'error_type': type(e).__name__
            }
        except Exception as e:
            logger.error(f"Unexpected error during invoice validation: {str(e)}")
            return {
                'validation_status': 'ERROR',
                'error_code': 'UNEXPECTED_ERROR',
                'error_message': f"Unexpected error: {str(e)}",
                'error_type': type(e).__name__
            }

    async def _prepare_firs_invoice_payload(
        self,
        invoice_data: Dict[str, Any],
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Prepare invoice data for FIRS submission
        
        Args:
            invoice_data: Raw invoice data
            organization_id: Organization UUID
            
        Returns:
            FIRS-compliant payload
        """
        # Ensure required FIRS fields are present
        required_fields = [
            'business_id', 'irn', 'issue_date', 'invoice_type_code',
            'document_currency_code', 'accounting_supplier_party',
            'accounting_customer_party', 'legal_monetary_total', 'invoice_line'
        ]
        
        for field in required_fields:
            if field not in invoice_data:
                raise ValueError(f"Required FIRS field '{field}' is missing from invoice data")
        
        # Prepare FIRS-compliant payload
        firs_payload = {
            'invoice': invoice_data,
            'metadata': {
                'organization_id': str(organization_id),
                'submission_timestamp': datetime.utcnow().isoformat(),
                'api_version': '2025.1',
                'client_version': '2.0.0',
                'sandbox_mode': self.sandbox_mode
            },
            'security': {
                'request_id': str(uuid4()),
                'client_signature': self._generate_client_signature(invoice_data)
            }
        }
        
        return firs_payload

    async def _prepare_firs_validation_payload(
        self,
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare invoice data for FIRS validation
        
        Args:
            invoice_data: Raw invoice data
            
        Returns:
            FIRS-compliant validation payload
        """
        return {
            'invoice': invoice_data,
            'validation_mode': 'comprehensive',
            'metadata': {
                'validation_timestamp': datetime.utcnow().isoformat(),
                'api_version': '2025.1',
                'client_version': '2.0.0',
                'sandbox_mode': self.sandbox_mode
            },
            'security': {
                'request_id': str(uuid4()),
                'client_signature': self._generate_client_signature(invoice_data)
            }
        }

    def _generate_client_signature(self, data: Dict[str, Any]) -> str:
        """
        Generate client signature for data integrity
        
        Args:
            data: Data to sign
            
        Returns:
            Base64-encoded signature
        """
        try:
            # Create a stable string representation
            data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            
            # Generate SHA-256 hash
            hash_digest = hashlib.sha256(data_str.encode()).digest()
            
            # Return base64-encoded signature
            return base64.b64encode(hash_digest).decode()
            
        except Exception as e:
            logger.warning(f"Error generating client signature: {str(e)}")
            return "SIGNATURE_ERROR"

    async def check_connection(self) -> Dict[str, Any]:
        """
        Check connection to FIRS API
        
        Returns:
            Dictionary with connection status
        """
        await self._ensure_session()
        
        try:
            health_url = f"{self.base_url}/api/health"
            
            async with self._session.get(health_url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return {
                        'status': 'CONNECTED',
                        'firs_status': health_data.get('status', 'UNKNOWN'),
                        'api_version': health_data.get('version', '2025.1'),
                        'environment': 'sandbox' if self.sandbox_mode else 'production'
                    }
                else:
                    return {
                        'status': 'DISCONNECTED',
                        'error': f'HTTP {response.status}',
                        'environment': 'sandbox' if self.sandbox_mode else 'production'
                    }
                    
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'environment': 'sandbox' if self.sandbox_mode else 'production'
            }


# Create a default instance for easy importing
firs_service = FIRSService()

# Factory function for creating enhanced API client
def create_firs_api_client(config: Dict[str, Any] = None) -> FIRSAPIClient:
    """
    Factory function to create FIRS API client with default configuration
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured FIRSAPIClient instance
    """
    if config is None:
        config = {
            'firs_api_base_url': settings.FIRS_API_URL,
            'firs_client_id': settings.FIRS_CLIENT_ID,
            'firs_client_secret': settings.FIRS_CLIENT_SECRET,
            'sandbox_mode': settings.FIRS_USE_SANDBOX,
            'ssl_cert_path': getattr(settings, 'FIRS_SSL_CERT_PATH', None)
        }
    
    return FIRSAPIClient(config)
