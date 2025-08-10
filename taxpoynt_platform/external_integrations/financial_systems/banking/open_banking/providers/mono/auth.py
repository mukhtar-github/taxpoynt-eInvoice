"""
Mono Authentication Handler
===========================

Handles authentication and authorization for Mono Open Banking API.
Based on official Mono API documentation and TaxPoynt auth patterns.

Authentication Flow:
1. Account Linking Initiation (POST /v2/accounts/initiate)
2. Customer Authentication via Mono Widget
3. Account Connection Callback
4. Access Token Management for API calls

Key Features:
- Secure API key management
- Account linking orchestration
- Token validation and refresh
- Nigerian banking compliance
- Error handling and retry logic

Architecture consistent with backend/app/integrations/ auth patterns.
"""

import asyncio
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlencode

import httpx
from pydantic import ValidationError

from .models import (
    MonoAccountLinkingRequest, 
    MonoAccountLinkingResponse,
    MonoError,
    MonoAccountConnectionStatus
)
from .exceptions import (
    MonoAuthenticationError,
    MonoConnectionError,
    MonoValidationError,
    MonoRateLimitError
)


logger = logging.getLogger(__name__)


class MonoAuthHandler:
    """
    Handles Mono API authentication and account linking.
    
    Based on Mono API v2 specifications with Nigerian banking compliance.
    """
    
    def __init__(
        self,
        secret_key: str,
        app_id: str,
        environment: str = "sandbox",
        webhook_secret: Optional[str] = None
    ):
        """
        Initialize Mono authentication handler.
        
        Args:
            secret_key: Mono secret key (mono-sec-key)
            app_id: Mono application ID
            environment: "sandbox" or "production"
            webhook_secret: Optional webhook signature verification secret
        """
        self.secret_key = secret_key
        self.app_id = app_id
        self.environment = environment
        self.webhook_secret = webhook_secret
        
        # API configuration based on Mono docs
        self.base_urls = {
            "sandbox": "https://api.withmono.com",
            "production": "https://api.withmono.com"
        }
        
        self.widget_urls = {
            "sandbox": "https://connect.mono.co",
            "production": "https://connect.mono.co"
        }
        
        self.base_url = self.base_urls[environment]
        self.widget_url = self.widget_urls[environment]
        
        # HTTP client with default headers
        self.client = httpx.AsyncClient(
            headers={
                "mono-sec-key": self.secret_key,
                "Content-Type": "application/json",
                "User-Agent": f"TaxPoynt-Platform/1.0 (Mono-Integration)"
            },
            timeout=30.0
        )
        
        # Rate limiting (60 requests per minute per Mono docs)
        self.rate_limit = 60
        self.rate_window = 60  # seconds
        self.request_timestamps: List[datetime] = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()
    
    def _check_rate_limit(self) -> None:
        """Check if we're within rate limits"""
        now = datetime.utcnow()
        # Remove old timestamps outside the window
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if (now - ts).total_seconds() < self.rate_window
        ]
        
        if len(self.request_timestamps) >= self.rate_limit:
            raise MonoRateLimitError(
                f"Rate limit exceeded: {self.rate_limit} requests per {self.rate_window} seconds"
            )
        
        self.request_timestamps.append(now)
    
    async def initiate_account_linking(
        self,
        customer_name: str,
        customer_email: str,
        redirect_url: str,
        customer_id: Optional[str] = None,
        reference: Optional[str] = None,
        scope: str = "auth",
        meta_data: Optional[Dict[str, Any]] = None
    ) -> MonoAccountLinkingResponse:
        """
        Initiate account linking process with Mono.
        
        Based on: POST /v2/accounts/initiate
        Documentation: https://docs.mono.co/api/bank-data/authorisation/initiate-account-linking
        
        Args:
            customer_name: Customer's full name
            customer_email: Customer's email address
            redirect_url: HTTPS URL for post-authentication redirect
            customer_id: Optional customer identifier
            reference: Unique reference (min 10 chars, auto-generated if None)
            scope: Access scope (default: "auth")
            meta_data: Additional metadata
            
        Returns:
            MonoAccountLinkingResponse with mono_url for customer linking
            
        Raises:
            MonoAuthenticationError: Authentication failed
            MonoValidationError: Invalid request parameters
            MonoConnectionError: Network/API connection issues
        """
        try:
            # Check rate limiting
            self._check_rate_limit()
            
            # Generate unique reference if not provided
            if not reference:
                reference = self._generate_reference()
            
            # Validate reference length (min 10 chars per Mono docs)
            if len(reference) < 10:
                raise MonoValidationError("Reference must be at least 10 characters long")
            
            # Prepare customer data
            customer_data = {
                "name": customer_name,
                "email": customer_email
            }
            if customer_id:
                customer_data["id"] = customer_id
            
            # Prepare metadata
            meta = {"ref": reference}
            if meta_data:
                meta.update(meta_data)
            
            # Create request payload
            request_data = MonoAccountLinkingRequest(
                customer=customer_data,
                scope=scope,
                redirect_url=redirect_url,
                meta=meta
            )
            
            logger.info(f"Initiating Mono account linking for customer: {customer_email}")
            
            # Make API request
            response = await self.client.post(
                f"{self.base_url}/v2/accounts/initiate",
                json=request_data.dict()
            )
            
            # Handle response
            if response.status_code == 200:
                response_data = response.json()
                linking_response = MonoAccountLinkingResponse(**response_data)
                
                logger.info(f"Account linking initiated successfully. Customer ID: {linking_response.customer}")
                return linking_response
                
            elif response.status_code == 400:
                error_data = response.json()
                raise MonoValidationError(f"Invalid request: {error_data.get('message', 'Unknown error')}")
                
            elif response.status_code == 401:
                raise MonoAuthenticationError("Invalid API credentials")
                
            elif response.status_code == 429:
                raise MonoRateLimitError("Rate limit exceeded")
                
            else:
                error_data = response.json() if response.content else {}
                raise MonoConnectionError(
                    f"API request failed with status {response.status_code}: "
                    f"{error_data.get('message', 'Unknown error')}"
                )
                
        except ValidationError as e:
            raise MonoValidationError(f"Request validation failed: {str(e)}")
        except httpx.RequestError as e:
            raise MonoConnectionError(f"Network request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in account linking: {str(e)}", exc_info=True)
            raise MonoConnectionError(f"Unexpected error: {str(e)}")
    
    def _generate_reference(self) -> str:
        """Generate a unique reference for account linking"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(6)
        return f"TXP_{timestamp}_{random_suffix}"
    
    async def get_account_status(self, account_id: str) -> MonoAccountConnectionStatus:
        """
        Get account connection status.
        
        Args:
            account_id: Mono account identifier
            
        Returns:
            MonoAccountConnectionStatus with current status
        """
        try:
            self._check_rate_limit()
            
            response = await self.client.get(
                f"{self.base_url}/v2/accounts/{account_id}"
            )
            
            if response.status_code == 200:
                account_data = response.json()
                
                # Map Mono response to our status model
                status_data = {
                    "account_id": account_id,
                    "status": account_data.get("status", "connected"),
                    "institution": account_data.get("institution", {}),
                    "last_updated": datetime.utcnow(),
                    "reauth_required": account_data.get("status") == "reauthorization_required"
                }
                
                return MonoAccountConnectionStatus(**status_data)
                
            elif response.status_code == 404:
                raise MonoValidationError(f"Account not found: {account_id}")
            elif response.status_code == 401:
                raise MonoAuthenticationError("Invalid API credentials")
            else:
                error_data = response.json() if response.content else {}
                raise MonoConnectionError(
                    f"Failed to get account status: {error_data.get('message', 'Unknown error')}"
                )
                
        except httpx.RequestError as e:
            raise MonoConnectionError(f"Network request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting account status: {str(e)}", exc_info=True)
            raise MonoConnectionError(f"Unexpected error: {str(e)}")
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        timestamp: str
    ) -> bool:
        """
        Verify Mono webhook signature for security.
        
        Args:
            payload: Raw webhook payload string
            signature: Webhook signature header
            timestamp: Timestamp header
            
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        
        try:
            # Mono webhook signature format (may vary - adjust based on actual implementation)
            # This is a placeholder implementation - update based on Mono's actual webhook signature format
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                f"{timestamp}.{payload}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    def generate_connect_url(
        self,
        mono_url: str,
        additional_params: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate the final connect URL for customer account linking.
        
        Args:
            mono_url: URL from Mono account linking response
            additional_params: Optional additional URL parameters
            
        Returns:
            str: Complete URL for customer to link their account
        """
        if additional_params:
            separator = "&" if "?" in mono_url else "?"
            params = urlencode(additional_params)
            return f"{mono_url}{separator}{params}"
        
        return mono_url
    
    async def reauthorize_account(self, account_id: str) -> str:
        """
        Initiate account reauthorization when required.
        
        Args:
            account_id: Account requiring reauthorization
            
        Returns:
            str: Reauthorization URL for customer
        """
        try:
            self._check_rate_limit()
            
            response = await self.client.post(
                f"{self.base_url}/v2/accounts/{account_id}/reauthorise"
            )
            
            if response.status_code == 200:
                reauth_data = response.json()
                return reauth_data.get("mono_url", "")
            else:
                error_data = response.json() if response.content else {}
                raise MonoConnectionError(
                    f"Reauthorization failed: {error_data.get('message', 'Unknown error')}"
                )
                
        except httpx.RequestError as e:
            raise MonoConnectionError(f"Network request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error during reauthorization: {str(e)}", exc_info=True)
            raise MonoConnectionError(f"Unexpected error: {str(e)}")
    
    async def unlink_account(self, account_id: str) -> bool:
        """
        Unlink/disconnect an account from Mono.
        
        Args:
            account_id: Account to unlink
            
        Returns:
            bool: True if successfully unlinked
        """
        try:
            self._check_rate_limit()
            
            response = await self.client.delete(
                f"{self.base_url}/v2/accounts/{account_id}/unlink"
            )
            
            return response.status_code == 200
            
        except httpx.RequestError as e:
            logger.error(f"Network error during account unlinking: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error unlinking account: {str(e)}", exc_info=True)
            return False
    
    def get_widget_config(
        self,
        customer_name: str,
        customer_email: str,
        reference: str
    ) -> Dict[str, Any]:
        """
        Generate configuration for Mono Connect widget (frontend integration).
        
        Args:
            customer_name: Customer name
            customer_email: Customer email
            reference: Unique reference
            
        Returns:
            Dict with widget configuration
        """
        return {
            "key": self.app_id,
            "scope": "auth",
            "customer": {
                "name": customer_name,
                "email": customer_email
            },
            "meta": {
                "ref": reference
            },
            "env": self.environment,
            "onSuccess": "handleMonoSuccess",
            "onEvent": "handleMonoEvent",
            "onClose": "handleMonoClose"
        }


# Export auth handler
__all__ = ["MonoAuthHandler"]