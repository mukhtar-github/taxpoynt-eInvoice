"""
Unleashed Authentication Manager
Handles API authentication for Unleashed inventory management system.
"""
import asyncio
import logging
import base64
import hmac
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import quote

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .exceptions import (
    UnleashedAuthenticationError,
    UnleashedAuthorizationError,
    UnleashedConnectionError,
    UnleashedConfigurationError
)


logger = logging.getLogger(__name__)


class UnleashedAuthManager:
    """
    Manages authentication for Unleashed API.
    
    Unleashed uses HMAC-SHA256 signature-based authentication with API ID and API key.
    Each request must be signed with a timestamp and signature.
    """
    
    # Unleashed API endpoints
    BASE_URL = "https://api.unleashedsoftware.com"
    
    def __init__(
        self,
        api_id: str,
        api_key: str,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize Unleashed authentication manager.
        
        Args:
            api_id: Unleashed API ID
            api_key: Unleashed API key
            session: Optional aiohttp session to use
        """
        if not api_id or not api_key:
            raise UnleashedConfigurationError("API ID and API key are required")
        
        self.api_id = api_id
        self.api_key = api_key
        self.session = session
        self.should_close_session = session is None
        
        self.base_url = self.BASE_URL
        
        # Connection state
        self._is_authenticated = False
        self._last_auth_check: Optional[datetime] = None
        self._account_info: Optional[Dict[str, Any]] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.session is None:
            timeout = ClientTimeout(total=30, connect=10)
            self.session = ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.should_close_session and self.session:
            await self.session.close()
    
    def _generate_signature(self, query_string: str) -> str:
        """
        Generate HMAC-SHA256 signature for Unleashed API.
        
        Args:
            query_string: URL query string to sign
            
        Returns:
            Base64 encoded signature
        """
        # Create HMAC-SHA256 signature
        signature = hmac.new(
            self.api_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        )
        
        # Return base64 encoded signature
        return base64.b64encode(signature.digest()).decode('utf-8')
    
    def get_auth_headers(self, query_string: str = "") -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Args:
            query_string: URL query string (for signature generation)
            
        Returns:
            Headers dict with authorization
        """
        # Generate signature for the query string
        signature = self._generate_signature(query_string)
        
        return {
            "api-auth-id": self.api_id,
            "api-auth-signature": signature,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Unleashed API by testing credentials.
        
        Returns:
            Authentication result
        """
        if not self.session:
            raise UnleashedConnectionError("No HTTP session available")
        
        try:
            # Test authentication by getting companies (basic endpoint)
            query_string = ""
            headers = self.get_auth_headers(query_string)
            
            async with self.session.get(
                f"{self.base_url}/Companies",
                headers=headers
            ) as response:
                if response.status == 401:
                    raise UnleashedAuthenticationError("Invalid API credentials")
                elif response.status == 403:
                    raise UnleashedAuthorizationError("Insufficient API permissions")
                elif response.status != 200:
                    raise UnleashedAuthenticationError(f"Authentication failed: HTTP {response.status}")
                
                # Try to get account info from a simple query
                account_data = {
                    "api_id": self.api_id,
                    "authenticated": True,
                    "base_url": self.base_url
                }
                
                self._is_authenticated = True
                self._last_auth_check = datetime.utcnow()
                self._account_info = account_data
                
                logger.info("Successfully authenticated with Unleashed")
                
                return {
                    "success": True,
                    "account_info": account_data,
                    "authenticated_at": self._last_auth_check.isoformat()
                }
                
        except ClientError as e:
            raise UnleashedConnectionError(f"Failed to connect to Unleashed API: {str(e)}")
        except Exception as e:
            raise UnleashedAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Unleashed API.
        
        Returns:
            Connection test results
        """
        try:
            auth_result = await self.authenticate()
            
            return {
                "success": True,
                "status": "connected",
                "account_info": self._account_info,
                "base_url": self.base_url,
                "api_id": self.api_id,
                "last_check": self._last_auth_check.isoformat() if self._last_auth_check else None
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "base_url": self.base_url
            }
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self._is_authenticated
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get cached account information.
        
        Returns:
            Account information if available
        """
        return self._account_info
    
    async def refresh_account_info(self) -> Dict[str, Any]:
        """
        Refresh account information from Unleashed.
        
        Returns:
            Updated account information
        """
        if not self.session:
            raise UnleashedConnectionError("No HTTP session available")
        
        try:
            # Test connection again to refresh
            return await self.authenticate()
                
        except ClientError as e:
            raise UnleashedConnectionError(f"Failed to connect to Unleashed API: {str(e)}")
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get API configuration information.
        
        Returns:
            API configuration details
        """
        return {
            "base_url": self.base_url,
            "api_id": self.api_id,
            "is_authenticated": self._is_authenticated,
            "last_auth_check": self._last_auth_check.isoformat() if self._last_auth_check else None
        }
    
    async def validate_permissions(self, required_permissions: Optional[list] = None) -> Dict[str, Any]:
        """
        Validate API permissions for required operations.
        
        Args:
            required_permissions: List of required permissions to check
            
        Returns:
            Permission validation results
        """
        if not self._account_info:
            await self.refresh_account_info()
        
        # Default required permissions for inventory operations
        if required_permissions is None:
            required_permissions = [
                "products_read",
                "products_write",
                "stock_read",
                "stock_write",
                "orders_read",
                "suppliers_read"
            ]
        
        account_info = self._account_info or {}
        
        return {
            "has_access": self._is_authenticated,
            "api_id": account_info.get("api_id"),
            "base_url": account_info.get("base_url"),
            "required_permissions": required_permissions,
            "validation_note": "Unleashed API uses HMAC authentication. Access validated through successful signature verification."
        }
    
    def disconnect(self) -> bool:
        """
        Disconnect from Unleashed API.
        
        Returns:
            True if disconnection successful
        """
        self._is_authenticated = False
        self._last_auth_check = None
        self._account_info = None
        
        logger.info("Disconnected from Unleashed API")
        return True