"""
Authentication Coordinator Service

Coordinates authentication across various business system integrations.
Handles OAuth, API keys, certificates, and other authentication methods.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
import json
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Supported authentication methods"""
    USERNAME_PASSWORD = "username_password"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CERTIFICATE = "certificate"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    CUSTOM = "custom"


class AuthState(Enum):
    """Authentication state"""
    UNAUTHENTICATED = "unauthenticated"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    FAILED = "failed"
    REFRESHING = "refreshing"


@dataclass
class AuthCredentials:
    """Authentication credentials container"""
    system_id: str
    auth_method: AuthMethod
    credentials: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    auto_refresh: bool = True
    encrypted: bool = False


@dataclass
class AuthToken:
    """Authentication token information"""
    token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    issued_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_in:
            return False
        return datetime.now() > self.issued_at + timedelta(seconds=self.expires_in)


@dataclass
class AuthStatus:
    """Authentication status for a system"""
    system_id: str
    auth_method: AuthMethod
    state: AuthState
    authenticated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_refresh: Optional[datetime] = None
    refresh_count: int = 0
    error_message: Optional[str] = None
    token_info: Optional[AuthToken] = None


class CredentialEncryption:
    """Handle encryption/decryption of sensitive credentials"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        if master_key:
            self.fernet = Fernet(master_key)
        else:
            # Generate key from environment or create new one
            self.fernet = Fernet(Fernet.generate_key())
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials dictionary"""
        json_data = json.dumps(credentials).encode()
        encrypted_data = self.fernet.encrypt(json_data)
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt credentials dictionary"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError("Invalid or corrupted credentials")


class OAuthHandler:
    """Handle OAuth 2.0 authentication flows"""
    
    def __init__(self):
        self.client_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_oauth_client(self, system_id: str, config: Dict[str, Any]):
        """Register OAuth client configuration"""
        required_fields = ["client_id", "client_secret", "authorization_url", "token_url"]
        if not all(field in config for field in required_fields):
            raise ValueError(f"Missing required OAuth config fields for {system_id}")
        
        self.client_configs[system_id] = config
        logger.info(f"Registered OAuth client for {system_id}")
    
    def get_authorization_url(self, system_id: str, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL"""
        if system_id not in self.client_configs:
            raise ValueError(f"OAuth client not configured for {system_id}")
        
        config = self.client_configs[system_id]
        params = {
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": config.get("scope", "")
        }
        
        # Build URL with parameters
        auth_url = config["authorization_url"]
        query_string = "&".join(f"{k}={v}" for k, v in params.items() if v)
        return f"{auth_url}?{query_string}"
    
    async def exchange_code_for_token(self, system_id: str, code: str, redirect_uri: str) -> AuthToken:
        """Exchange authorization code for access token"""
        if system_id not in self.client_configs:
            raise ValueError(f"OAuth client not configured for {system_id}")
        
        config = self.client_configs[system_id]
        
        # Prepare token request
        token_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        # TODO: Make actual HTTP request to token endpoint
        # For now, return mock token
        return AuthToken(
            token=f"access_token_{secrets.token_hex(16)}",
            token_type="Bearer",
            expires_in=3600,
            refresh_token=f"refresh_token_{secrets.token_hex(16)}",
            scope=config.get("scope", "")
        )
    
    async def refresh_token(self, system_id: str, refresh_token: str) -> AuthToken:
        """Refresh access token using refresh token"""
        if system_id not in self.client_configs:
            raise ValueError(f"OAuth client not configured for {system_id}")
        
        config = self.client_configs[system_id]
        
        # Prepare refresh request
        refresh_data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        # TODO: Make actual HTTP request to token endpoint
        # For now, return mock token
        return AuthToken(
            token=f"refreshed_token_{secrets.token_hex(16)}",
            token_type="Bearer",
            expires_in=3600,
            refresh_token=refresh_token,
            scope=config.get("scope", "")
        )


class AuthCoordinator:
    """Main authentication coordinator for all integrations"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        self.credential_store: Dict[str, AuthCredentials] = {}
        self.auth_status: Dict[str, AuthStatus] = {}
        # Keep encryption for backward compatibility, but prefer Config Manager when available  
        self.encryption = CredentialEncryption(encryption_key)
        self.config_manager = None  # Will be injected for enhanced encryption
        self.oauth_handler = OAuthHandler()
        self.auth_cache: Dict[str, AuthToken] = {}
        self.refresh_tasks: Dict[str, asyncio.Task] = {}
    
    def set_config_manager(self, config_manager):
        """Inject config manager dependency for enhanced encryption"""
        self.config_manager = config_manager
        
    async def register_credentials(self, credentials: AuthCredentials) -> bool:
        """
        Register authentication credentials for a system
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            Success status
        """
        try:
            system_id = credentials.system_id
            
            # Encrypt sensitive credentials if requested
            if credentials.encrypted:
                credentials.credentials = {
                    "encrypted_data": self.encryption.encrypt_credentials(credentials.credentials)
                }
            
            # Store credentials
            self.credential_store[system_id] = credentials
            
            # Initialize auth status
            self.auth_status[system_id] = AuthStatus(
                system_id=system_id,
                auth_method=credentials.auth_method,
                state=AuthState.UNAUTHENTICATED
            )
            
            # Setup OAuth if needed
            if credentials.auth_method == AuthMethod.OAUTH2:
                oauth_config = credentials.credentials.get("oauth_config", {})
                if oauth_config:
                    self.oauth_handler.register_oauth_client(system_id, oauth_config)
            
            logger.info(f"Registered credentials for {system_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register credentials for {credentials.system_id}: {e}")
            return False
    
    async def authenticate(self, system_id: str) -> bool:
        """
        Perform authentication for specific system
        
        Args:
            system_id: System identifier
            
        Returns:
            Authentication success status
        """
        if system_id not in self.credential_store:
            logger.error(f"No credentials found for {system_id}")
            return False
        
        credentials = self.credential_store[system_id]
        status = self.auth_status[system_id]
        
        try:
            status.state = AuthState.AUTHENTICATING
            
            # Get actual credentials (decrypt if needed)
            actual_credentials = await self._get_decrypted_credentials(credentials)
            
            # Perform authentication based on method
            auth_result = await self._perform_authentication(
                system_id, 
                credentials.auth_method, 
                actual_credentials
            )
            
            if auth_result["success"]:
                status.state = AuthState.AUTHENTICATED
                status.authenticated_at = datetime.now()
                status.error_message = None
                
                # Handle token-based auth
                if "token" in auth_result:
                    token = auth_result["token"]
                    status.token_info = token
                    self.auth_cache[system_id] = token
                    
                    # Setup auto-refresh if needed
                    if credentials.auto_refresh and token.refresh_token:
                        await self._schedule_token_refresh(system_id)
                
                # Set expiration
                if credentials.expires_at:
                    status.expires_at = credentials.expires_at
                elif status.token_info and status.token_info.expires_in:
                    status.expires_at = datetime.now() + timedelta(
                        seconds=status.token_info.expires_in
                    )
                
                logger.info(f"Authentication successful for {system_id}")
                return True
            else:
                status.state = AuthState.FAILED
                status.error_message = auth_result.get("error", "Authentication failed")
                logger.error(f"Authentication failed for {system_id}: {status.error_message}")
                return False
                
        except Exception as e:
            status.state = AuthState.FAILED
            status.error_message = str(e)
            logger.error(f"Authentication error for {system_id}: {e}")
            return False
    
    async def _get_decrypted_credentials(self, credentials: AuthCredentials) -> Dict[str, Any]:
        """Get decrypted credentials"""
        if credentials.encrypted:
            encrypted_data = credentials.credentials.get("encrypted_data")
            if encrypted_data:
                return self.encryption.decrypt_credentials(encrypted_data)
        return credentials.credentials
    
    async def _perform_authentication(
        self, 
        system_id: str, 
        auth_method: AuthMethod, 
        credentials: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform authentication based on method"""
        
        if auth_method == AuthMethod.USERNAME_PASSWORD:
            return await self._authenticate_username_password(system_id, credentials)
        elif auth_method == AuthMethod.API_KEY:
            return await self._authenticate_api_key(system_id, credentials)
        elif auth_method == AuthMethod.OAUTH2:
            return await self._authenticate_oauth2(system_id, credentials)
        elif auth_method == AuthMethod.JWT:
            return await self._authenticate_jwt(system_id, credentials)
        elif auth_method == AuthMethod.BEARER_TOKEN:
            return await self._authenticate_bearer_token(system_id, credentials)
        else:
            return {"success": False, "error": f"Unsupported auth method: {auth_method}"}
    
    async def _authenticate_username_password(self, system_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using username/password"""
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            return {"success": False, "error": "Missing username or password"}
        
        # TODO: Implement actual authentication logic for different systems
        # For now, return success
        return {
            "success": True,
            "method": "username_password",
            "authenticated_user": username
        }
    
    async def _authenticate_api_key(self, system_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using API key"""
        api_key = credentials.get("api_key")
        
        if not api_key:
            return {"success": False, "error": "Missing API key"}
        
        # TODO: Validate API key with target system
        return {
            "success": True,
            "method": "api_key",
            "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest()[:8]
        }
    
    async def _authenticate_oauth2(self, system_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using OAuth 2.0"""
        # Check if we have existing token
        if system_id in self.auth_cache:
            token = self.auth_cache[system_id]
            if not token.is_expired:
                return {"success": True, "method": "oauth2", "token": token}
        
        # Check for refresh token
        refresh_token = credentials.get("refresh_token")
        if refresh_token:
            try:
                new_token = await self.oauth_handler.refresh_token(system_id, refresh_token)
                return {"success": True, "method": "oauth2", "token": new_token}
            except Exception as e:
                logger.error(f"Token refresh failed for {system_id}: {e}")
        
        # Need to initiate OAuth flow
        return {
            "success": False, 
            "error": "OAuth flow required",
            "auth_url_required": True
        }
    
    async def _authenticate_jwt(self, system_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using JWT token"""
        jwt_token = credentials.get("jwt_token")
        
        if not jwt_token:
            return {"success": False, "error": "Missing JWT token"}
        
        # TODO: Validate JWT token
        return {
            "success": True,
            "method": "jwt",
            "token": AuthToken(token=jwt_token, token_type="JWT")
        }
    
    async def _authenticate_bearer_token(self, system_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate using Bearer token"""
        bearer_token = credentials.get("bearer_token")
        
        if not bearer_token:
            return {"success": False, "error": "Missing Bearer token"}
        
        return {
            "success": True,
            "method": "bearer_token",
            "token": AuthToken(token=bearer_token, token_type="Bearer")
        }
    
    async def get_auth_token(self, system_id: str) -> Optional[str]:
        """
        Get current authentication token for system
        
        Args:
            system_id: System identifier
            
        Returns:
            Authentication token or None
        """
        status = self.auth_status.get(system_id)
        if not status or status.state != AuthState.AUTHENTICATED:
            return None
        
        # Check if we have cached token
        if system_id in self.auth_cache:
            token = self.auth_cache[system_id]
            if not token.is_expired:
                return token.token
            else:
                # Try to refresh if possible
                await self.refresh_authentication(system_id)
                if system_id in self.auth_cache:
                    return self.auth_cache[system_id].token
        
        return None
    
    async def refresh_authentication(self, system_id: str) -> bool:
        """
        Refresh authentication for system
        
        Args:
            system_id: System identifier
            
        Returns:
            Refresh success status
        """
        if system_id not in self.auth_status:
            return False
        
        status = self.auth_status[system_id]
        credentials = self.credential_store.get(system_id)
        
        if not credentials:
            return False
        
        try:
            status.state = AuthState.REFRESHING
            
            # Handle different refresh methods
            if credentials.auth_method == AuthMethod.OAUTH2:
                # Use refresh token
                cached_token = self.auth_cache.get(system_id)
                if cached_token and cached_token.refresh_token:
                    new_token = await self.oauth_handler.refresh_token(
                        system_id, 
                        cached_token.refresh_token
                    )
                    
                    # Update cache and status
                    self.auth_cache[system_id] = new_token
                    status.token_info = new_token
                    status.state = AuthState.AUTHENTICATED
                    status.last_refresh = datetime.now()
                    status.refresh_count += 1
                    
                    logger.info(f"Token refreshed for {system_id}")
                    return True
            else:
                # Re-authenticate
                return await self.authenticate(system_id)
                
        except Exception as e:
            status.state = AuthState.FAILED
            status.error_message = f"Refresh failed: {str(e)}"
            logger.error(f"Authentication refresh failed for {system_id}: {e}")
        
        return False
    
    async def _schedule_token_refresh(self, system_id: str):
        """Schedule automatic token refresh"""
        # Cancel existing refresh task
        if system_id in self.refresh_tasks:
            self.refresh_tasks[system_id].cancel()
        
        # Calculate refresh time (refresh at 80% of token lifetime)
        token = self.auth_cache.get(system_id)
        if token and token.expires_in:
            refresh_delay = int(token.expires_in * 0.8)
            
            async def refresh_job():
                await asyncio.sleep(refresh_delay)
                await self.refresh_authentication(system_id)
            
            self.refresh_tasks[system_id] = asyncio.create_task(refresh_job())
    
    async def is_authenticated(self, system_id: str) -> bool:
        """Check if system is currently authenticated"""
        status = self.auth_status.get(system_id)
        if not status:
            return False
        
        # Check state
        if status.state != AuthState.AUTHENTICATED:
            return False
        
        # Check expiration
        if status.expires_at and datetime.now() > status.expires_at:
            status.state = AuthState.EXPIRED
            return False
        
        return True
    
    async def logout(self, system_id: str) -> bool:
        """
        Logout from specific system
        
        Args:
            system_id: System identifier
            
        Returns:
            Logout success status
        """
        try:
            # Cancel refresh task
            if system_id in self.refresh_tasks:
                self.refresh_tasks[system_id].cancel()
                del self.refresh_tasks[system_id]
            
            # Clear auth cache
            self.auth_cache.pop(system_id, None)
            
            # Update status
            if system_id in self.auth_status:
                self.auth_status[system_id].state = AuthState.UNAUTHENTICATED
                self.auth_status[system_id].authenticated_at = None
                self.auth_status[system_id].token_info = None
            
            logger.info(f"Logged out from {system_id}")
            return True
            
        except Exception as e:
            logger.error(f"Logout failed for {system_id}: {e}")
            return False
    
    async def get_auth_status(self, system_id: str) -> Optional[AuthStatus]:
        """Get authentication status for system"""
        return self.auth_status.get(system_id)
    
    async def get_all_auth_statuses(self) -> Dict[str, AuthStatus]:
        """Get authentication status for all systems"""
        return self.auth_status.copy()
    
    async def cleanup_expired_tokens(self):
        """Clean up expired tokens and refresh where possible"""
        for system_id, token in list(self.auth_cache.items()):
            if token.is_expired:
                if token.refresh_token:
                    # Try to refresh
                    await self.refresh_authentication(system_id)
                else:
                    # Remove expired token
                    del self.auth_cache[system_id]
                    if system_id in self.auth_status:
                        self.auth_status[system_id].state = AuthState.EXPIRED
    
    async def shutdown(self):
        """Shutdown auth coordinator and cleanup resources"""
        # Cancel all refresh tasks
        for task in self.refresh_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.refresh_tasks:
            await asyncio.gather(*self.refresh_tasks.values(), return_exceptions=True)
        
        # Clear all data
        self.credential_store.clear()
        self.auth_status.clear()
        self.auth_cache.clear()
        self.refresh_tasks.clear()
        
        logger.info("Auth coordinator shutdown complete")


# Global instance
auth_coordinator = AuthCoordinator()


async def register_system_credentials(credentials: AuthCredentials) -> bool:
    """Register credentials with global auth coordinator"""
    return await auth_coordinator.register_credentials(credentials)


async def authenticate_system(system_id: str) -> bool:
    """Authenticate system using global auth coordinator"""
    return await auth_coordinator.authenticate(system_id)


async def get_system_auth_token(system_id: str) -> Optional[str]:
    """Get auth token for system"""
    return await auth_coordinator.get_auth_token(system_id)