"""
Cin7 Authentication Manager
Handles API authentication for Cin7 inventory management system.
"""
import asyncio
import logging
import base64
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .exceptions import (
    Cin7AuthenticationError,
    Cin7AuthorizationError,
    Cin7ConnectionError,
    Cin7ConfigurationError
)


logger = logging.getLogger(__name__)


class Cin7AuthManager:
    """
    Manages authentication for Cin7 API.
    
    Cin7 uses API token-based authentication with basic auth headers.
    Supports both sandbox and production environments.
    """
    
    # Cin7 API endpoints
    SANDBOX_BASE_URL = "https://sandbox.cin7.com"
    PRODUCTION_BASE_URL = "https://api.cin7.com"
    
    # API version
    API_VERSION = "1.3"
    
    def __init__(
        self,
        api_username: str,
        api_token: str,  
        api_password: str,
        sandbox: bool = True,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize Cin7 authentication manager.
        
        Args:
            api_username: Cin7 API username
            api_token: Cin7 API token
            api_password: Cin7 API password
            sandbox: Whether to use sandbox environment
            session: Optional aiohttp session to use
        """
        if not api_username or not api_token or not api_password:
            raise Cin7ConfigurationError("API username, token, and password are required")
        
        self.api_username = api_username
        self.api_token = api_token
        self.api_password = api_password
        self.sandbox = sandbox
        self.session = session
        self.should_close_session = session is None
        
        self.base_url = self.SANDBOX_BASE_URL if sandbox else self.PRODUCTION_BASE_URL
        
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
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Headers dict with authorization
        """
        # Cin7 uses Basic Auth with username:token format
        auth_string = f"{self.api_username}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_header = base64.b64encode(auth_bytes).decode('ascii')
        
        return {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Cin7 API by testing credentials.
        
        Returns:
            Authentication result with account info
        """
        if not self.session:
            raise Cin7ConnectionError("No HTTP session available")
        
        headers = self.get_auth_headers()
        
        try:
            # Test authentication by getting account info
            async with self.session.get(
                f"{self.base_url}/api/v{self.API_VERSION}/Account",
                headers=headers
            ) as response:
                if response.status == 401:
                    raise Cin7AuthenticationError("Invalid API credentials")
                elif response.status == 403:
                    raise Cin7AuthorizationError("Insufficient API permissions")
                elif response.status != 200:
                    raise Cin7AuthenticationError(f"Authentication failed: HTTP {response.status}")
                
                account_data = await response.json()
                
                self._is_authenticated = True
                self._last_auth_check = datetime.utcnow()
                self._account_info = account_data
                
                logger.info("Successfully authenticated with Cin7")
                
                return {
                    "success": True,
                    "account_info": account_data,
                    "authenticated_at": self._last_auth_check.isoformat()
                }
                
        except ClientError as e:
            raise Cin7ConnectionError(f"Failed to connect to Cin7 API: {str(e)}")
        except Exception as e:
            raise Cin7AuthenticationError(f"Authentication failed: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Cin7 API.
        
        Returns:
            Connection test results
        """
        try:
            auth_result = await self.authenticate()
            
            return {
                "success": True,
                "status": "connected",
                "account_info": self._account_info,
                "api_version": self.API_VERSION,
                "environment": "sandbox" if self.sandbox else "production",
                "last_check": self._last_auth_check.isoformat() if self._last_auth_check else None
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "environment": "sandbox" if self.sandbox else "production"
            }
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        # Cin7 API tokens don't expire, but we check if we've successfully authenticated
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
        Refresh account information from Cin7.
        
        Returns:
            Updated account information
        """
        if not self.session:
            raise Cin7ConnectionError("No HTTP session available")
        
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v{self.API_VERSION}/Account",
                headers=headers
            ) as response:
                if response.status == 401:
                    self._is_authenticated = False
                    raise Cin7AuthenticationError("Authentication expired or invalid")
                elif response.status != 200:
                    raise Cin7AuthenticationError(f"Failed to refresh account info: HTTP {response.status}")
                
                account_data = await response.json()
                self._account_info = account_data
                self._last_auth_check = datetime.utcnow()
                
                logger.info("Successfully refreshed account information")
                return account_data
                
        except ClientError as e:
            raise Cin7ConnectionError(f"Failed to connect to Cin7 API: {str(e)}")
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get API configuration information.
        
        Returns:
            API configuration details
        """
        return {
            "base_url": self.base_url,
            "api_version": self.API_VERSION,
            "environment": "sandbox" if self.sandbox else "production",
            "username": self.api_username,
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
        
        # Cin7 doesn't expose detailed permission info in account endpoint
        # So we assume if authentication succeeds, we have basic permissions
        account_info = self._account_info or {}
        
        return {
            "has_access": self._is_authenticated,
            "account_name": account_info.get("Name"),
            "account_id": account_info.get("Id"),
            "subscription_level": account_info.get("SubscriptionLevel"),
            "required_permissions": required_permissions,
            "validation_note": "Cin7 API doesn't expose detailed permissions. Access validated through successful authentication."
        }
    
    def disconnect(self) -> bool:
        """
        Disconnect from Cin7 API.
        
        Returns:
            True if disconnection successful
        """
        self._is_authenticated = False
        self._last_auth_check = None
        self._account_info = None
        
        logger.info("Disconnected from Cin7 API")
        return True