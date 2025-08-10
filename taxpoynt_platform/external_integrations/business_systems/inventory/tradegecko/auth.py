"""
TradeGecko Authentication Manager
Handles API authentication for TradeGecko inventory management system.
"""
import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .exceptions import (
    TradeGeckoAuthenticationError,
    TradeGeckoAuthorizationError,
    TradeGeckoConnectionError,
    TradeGeckoConfigurationError
)


logger = logging.getLogger(__name__)


class TradeGeckoAuthManager:
    """
    Manages authentication for TradeGecko API.
    
    TradeGecko uses OAuth 2.0 with access tokens for authentication.
    Supports both sandbox and production environments.
    """
    
    # TradeGecko API endpoints
    SANDBOX_BASE_URL = "https://api.tradegecko.com"
    PRODUCTION_BASE_URL = "https://api.tradegecko.com"
    
    # API version
    API_VERSION = "v1"
    
    def __init__(
        self,
        access_token: str,
        sandbox: bool = True,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize TradeGecko authentication manager.
        
        Args:
            access_token: TradeGecko API access token
            sandbox: Whether to use sandbox environment
            session: Optional aiohttp session to use
        """
        if not access_token:
            raise TradeGeckoConfigurationError("Access token is required")
        
        self.access_token = access_token
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
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with TradeGecko API by testing credentials.
        
        Returns:
            Authentication result with account info
        """
        if not self.session:
            raise TradeGeckoConnectionError("No HTTP session available")
        
        headers = self.get_auth_headers()
        
        try:
            # Test authentication by getting account info
            async with self.session.get(
                f"{self.base_url}/{self.API_VERSION}/account",
                headers=headers
            ) as response:
                if response.status == 401:
                    raise TradeGeckoAuthenticationError("Invalid access token")
                elif response.status == 403:
                    raise TradeGeckoAuthorizationError("Insufficient API permissions")
                elif response.status == 404:
                    # TradeGecko might not have account endpoint, try current_user
                    async with self.session.get(
                        f"{self.base_url}/{self.API_VERSION}/current_user",
                        headers=headers
                    ) as user_response:
                        if user_response.status == 401:
                            raise TradeGeckoAuthenticationError("Invalid access token")
                        elif user_response.status == 403:
                            raise TradeGeckoAuthorizationError("Insufficient API permissions")
                        elif user_response.status != 200:
                            raise TradeGeckoAuthenticationError(f"Authentication failed: HTTP {user_response.status}")
                        
                        account_data = await user_response.json()
                elif response.status != 200:
                    raise TradeGeckoAuthenticationError(f"Authentication failed: HTTP {response.status}")
                else:
                    account_data = await response.json()
                
                self._is_authenticated = True
                self._last_auth_check = datetime.utcnow()
                self._account_info = account_data
                
                logger.info("Successfully authenticated with TradeGecko")
                
                return {
                    "success": True,
                    "account_info": account_data,
                    "authenticated_at": self._last_auth_check.isoformat()
                }
                
        except ClientError as e:
            raise TradeGeckoConnectionError(f"Failed to connect to TradeGecko API: {str(e)}")
        except Exception as e:
            raise TradeGeckoAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to TradeGecko API.
        
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
        Refresh account information from TradeGecko.
        
        Returns:
            Updated account information
        """
        if not self.session:
            raise TradeGeckoConnectionError("No HTTP session available")
        
        headers = self.get_auth_headers()
        
        try:
            # Try current_user endpoint first
            async with self.session.get(
                f"{self.base_url}/{self.API_VERSION}/current_user",
                headers=headers
            ) as response:
                if response.status == 401:
                    self._is_authenticated = False
                    raise TradeGeckoAuthenticationError("Authentication expired or invalid")
                elif response.status != 200:
                    raise TradeGeckoAuthenticationError(f"Failed to refresh account info: HTTP {response.status}")
                
                account_data = await response.json()
                self._account_info = account_data
                self._last_auth_check = datetime.utcnow()
                
                logger.info("Successfully refreshed account information")
                return account_data
                
        except ClientError as e:
            raise TradeGeckoConnectionError(f"Failed to connect to TradeGecko API: {str(e)}")
    
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
            "user_id": account_info.get("id"),
            "email": account_info.get("email"),
            "company_id": account_info.get("company_id"),
            "required_permissions": required_permissions,
            "validation_note": "TradeGecko API doesn't expose detailed permissions. Access validated through successful authentication."
        }
    
    def disconnect(self) -> bool:
        """
        Disconnect from TradeGecko API.
        
        Returns:
            True if disconnection successful
        """
        self._is_authenticated = False
        self._last_auth_check = None
        self._account_info = None
        
        logger.info("Disconnected from TradeGecko API")
        return True