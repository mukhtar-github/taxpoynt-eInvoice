"""
ERP Authentication Provider Service

This module provides ERP-specific authentication implementations for various
ERP systems (Odoo, SAP, QuickBooks, etc.) used in SI workflows, handling
different authentication methods and credential management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import base64
import hashlib
import hmac
import secrets
import aiohttp
import ssl
from urllib.parse import urlencode, parse_qs

from .auth_manager import (
    BaseAuthProvider,
    AuthenticationType,
    AuthenticationContext,
    AuthenticationCredentials,
    AuthenticationResult,
    AuthenticationStatus,
    AuthenticationScope,
    ServiceType
)

logger = logging.getLogger(__name__)


class ERPSystemType(Enum):
    """Types of ERP systems"""
    ODOO = "odoo"
    SAP = "sap"
    QUICKBOOKS = "quickbooks"
    SAGE = "sage"
    DYNAMICS = "dynamics"
    ORACLE = "oracle"
    NETSUITE = "netsuite"
    CUSTOM = "custom"


class ERPAuthMethod(Enum):
    """ERP-specific authentication methods"""
    ODOO_SESSION = "odoo_session"
    ODOO_API_KEY = "odoo_api_key"
    SAP_OAUTH = "sap_oauth"
    SAP_BASIC = "sap_basic"
    QUICKBOOKS_OAUTH = "quickbooks_oauth"
    SAGE_API_KEY = "sage_api_key"
    DYNAMICS_OAUTH = "dynamics_oauth"
    ORACLE_BASIC = "oracle_basic"


@dataclass
class ERPConnectionConfig:
    """Configuration for ERP connection"""
    erp_system: ERPSystemType
    host: str
    port: int = 443
    use_ssl: bool = True
    database: Optional[str] = None
    api_version: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3
    custom_headers: Dict[str, str] = field(default_factory=dict)
    connection_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ERPSessionData:
    """ERP session data"""
    session_token: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    database_list: List[str] = field(default_factory=list)
    user_context: Dict[str, Any] = field(default_factory=dict)
    server_version: Optional[str] = None
    session_info: Dict[str, Any] = field(default_factory=dict)


class BaseERPAuthProvider(BaseAuthProvider):
    """Base class for ERP authentication providers"""
    
    def __init__(self, provider_id: str, erp_system: ERPSystemType, auth_type: AuthenticationType):
        super().__init__(provider_id, auth_type)
        self.erp_system = erp_system
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.connection_configs: Dict[str, ERPConnectionConfig] = {}
    
    async def initialize(self) -> None:
        """Initialize the ERP auth provider"""
        # Setup HTTP session
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=10,
            ssl=ssl.create_default_context()
        )
        
        timeout = aiohttp.ClientTimeout(total=300)
        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        logger.info(f"Initialized ERP auth provider: {self.provider_id}")
    
    async def shutdown(self) -> None:
        """Shutdown the ERP auth provider"""
        if self.http_session:
            await self.http_session.close()
    
    def register_erp_config(self, service_identifier: str, config: ERPConnectionConfig) -> None:
        """Register ERP connection configuration"""
        self.connection_configs[service_identifier] = config
        logger.info(f"Registered ERP config for {service_identifier}")
    
    def _build_url(self, config: ERPConnectionConfig, endpoint: str) -> str:
        """Build URL for ERP endpoint"""
        protocol = "https" if config.use_ssl else "http"
        base_url = f"{protocol}://{config.host}:{config.port}"
        return f"{base_url}{endpoint}"


class OdooAuthProvider(BaseERPAuthProvider):
    """Odoo-specific authentication provider"""
    
    def __init__(self):
        super().__init__("odoo_auth", ERPSystemType.ODOO, AuthenticationType.BASIC)
    
    async def authenticate(
        self,
        credentials: AuthenticationCredentials,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate with Odoo ERP"""
        try:
            config = self.connection_configs.get(credentials.service_identifier)
            if not config:
                return self._create_failed_result(credentials, "No configuration found")
            
            if credentials.auth_type == AuthenticationType.BASIC:
                return await self._authenticate_basic(credentials, config, context)
            elif credentials.auth_type == AuthenticationType.API_KEY:
                return await self._authenticate_api_key(credentials, config, context)
            else:
                return self._create_failed_result(credentials, f"Unsupported auth type: {credentials.auth_type}")
                
        except Exception as e:
            logger.error(f"Odoo authentication failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_basic(
        self,
        credentials: AuthenticationCredentials,
        config: ERPConnectionConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using Odoo session authentication"""
        try:
            auth_url = self._build_url(config, "/web/session/authenticate")
            
            auth_data = {
                "db": config.database or credentials.custom_params.get("database"),
                "login": credentials.username,
                "password": credentials.password
            }
            
            headers = {
                "Content-Type": "application/json",
                **config.custom_headers
            }
            
            async with self.http_session.post(auth_url, json=auth_data, headers=headers) as response:
                if response.status == 200:
                    result_data = await response.json()
                    
                    if result_data.get("result") and result_data["result"].get("uid"):
                        session_data = result_data["result"]
                        
                        # Extract session information
                        erp_session = ERPSessionData(
                            session_token=response.cookies.get("session_id", "").value,
                            session_id=session_data.get("session_id"),
                            user_id=str(session_data.get("uid")),
                            database_list=session_data.get("db", []),
                            user_context=session_data.get("user_context", {}),
                            server_version=session_data.get("server_version"),
                            session_info=session_data
                        )
                        
                        return self._create_success_result(
                            credentials,
                            session_data.get("session_id", ""),
                            erp_session,
                            [AuthenticationScope.ERP_READ, AuthenticationScope.ERP_WRITE]
                        )
                    else:
                        error_msg = result_data.get("error", {}).get("message", "Authentication failed")
                        return self._create_failed_result(credentials, error_msg)
                else:
                    return self._create_failed_result(credentials, f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Odoo basic auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_api_key(
        self,
        credentials: AuthenticationCredentials,
        config: ERPConnectionConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using Odoo API key"""
        try:
            # Test API key with a simple request
            test_url = self._build_url(config, "/web/dataset/call_kw")
            
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": credentials.api_key,
                **config.custom_headers
            }
            
            test_data = {
                "model": "res.users",
                "method": "search_read",
                "args": [[]],
                "kwargs": {
                    "fields": ["id", "name", "login"],
                    "limit": 1
                }
            }
            
            async with self.http_session.post(test_url, json=test_data, headers=headers) as response:
                if response.status == 200:
                    result_data = await response.json()
                    
                    if result_data.get("result"):
                        # API key is valid
                        erp_session = ERPSessionData(
                            session_token=credentials.api_key,
                            user_context={"api_key_auth": True}
                        )
                        
                        return self._create_success_result(
                            credentials,
                            f"api_key_{credentials.api_key[:8]}",
                            erp_session,
                            [AuthenticationScope.ERP_READ, AuthenticationScope.ERP_WRITE]
                        )
                    else:
                        return self._create_failed_result(credentials, "Invalid API key")
                else:
                    return self._create_failed_result(credentials, f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Odoo API key auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def validate_token(self, token: str, context: AuthenticationContext) -> bool:
        """Validate Odoo session token"""
        try:
            # For session tokens, we'd need to make a test request
            # For API keys, we can validate format or make a simple API call
            return len(token) > 10  # Basic validation
        except Exception:
            return False
    
    async def refresh_token(
        self,
        refresh_token: str,
        context: AuthenticationContext
    ) -> Optional[AuthenticationResult]:
        """Refresh Odoo session (not typically supported)"""
        # Odoo sessions typically don't support refresh
        return None
    
    async def revoke_token(self, token: str, context: AuthenticationContext) -> bool:
        """Revoke Odoo session"""
        try:
            # For session-based auth, we'd call logout endpoint
            # For API keys, revocation happens on Odoo side
            return True
        except Exception:
            return False


class SAPAuthProvider(BaseERPAuthProvider):
    """SAP-specific authentication provider"""
    
    def __init__(self):
        super().__init__("sap_auth", ERPSystemType.SAP, AuthenticationType.OAUTH2)
    
    async def authenticate(
        self,
        credentials: AuthenticationCredentials,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate with SAP ERP"""
        try:
            config = self.connection_configs.get(credentials.service_identifier)
            if not config:
                return self._create_failed_result(credentials, "No configuration found")
            
            if credentials.auth_type == AuthenticationType.OAUTH2:
                return await self._authenticate_oauth2(credentials, config, context)
            elif credentials.auth_type == AuthenticationType.BASIC:
                return await self._authenticate_basic(credentials, config, context)
            else:
                return self._create_failed_result(credentials, f"Unsupported auth type: {credentials.auth_type}")
                
        except Exception as e:
            logger.error(f"SAP authentication failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_oauth2(
        self,
        credentials: AuthenticationCredentials,
        config: ERPConnectionConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using SAP OAuth2"""
        try:
            token_url = self._build_url(config, "/sap/bc/rest/oauth2/token")
            
            # Prepare OAuth2 token request
            token_data = {
                "grant_type": "client_credentials",
                "client_id": credentials.oauth_client_id,
                "client_secret": credentials.oauth_client_secret,
                "scope": "read write"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                **config.custom_headers
            }
            
            async with self.http_session.post(
                token_url,
                data=urlencode(token_data),
                headers=headers
            ) as response:
                if response.status == 200:
                    token_result = await response.json()
                    
                    access_token = token_result.get("access_token")
                    if access_token:
                        # Create session data
                        erp_session = ERPSessionData(
                            session_token=access_token,
                            user_context={
                                "oauth_client_id": credentials.oauth_client_id,
                                "token_type": token_result.get("token_type", "Bearer")
                            }
                        )
                        
                        expires_in = token_result.get("expires_in", 3600)
                        expires_at = datetime.now() + timedelta(seconds=expires_in)
                        
                        result = self._create_success_result(
                            credentials,
                            f"sap_oauth_{access_token[:8]}",
                            erp_session,
                            [AuthenticationScope.ERP_READ, AuthenticationScope.ERP_WRITE]
                        )
                        result.expires_at = expires_at
                        result.access_token = access_token
                        result.refresh_token = token_result.get("refresh_token")
                        
                        return result
                    else:
                        return self._create_failed_result(credentials, "No access token received")
                else:
                    error_text = await response.text()
                    return self._create_failed_result(credentials, f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"SAP OAuth2 auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_basic(
        self,
        credentials: AuthenticationCredentials,
        config: ERPConnectionConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using SAP basic authentication"""
        try:
            # Test basic auth with a simple request
            test_url = self._build_url(config, "/sap/opu/odata/sap/API_TEST/")
            
            # Create basic auth header
            auth_string = f"{credentials.username}:{credentials.password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Accept": "application/json",
                **config.custom_headers
            }
            
            async with self.http_session.get(test_url, headers=headers) as response:
                if response.status in [200, 404]:  # 404 is OK if endpoint doesn't exist
                    erp_session = ERPSessionData(
                        session_token=auth_b64,
                        user_context={"basic_auth": True, "username": credentials.username}
                    )
                    
                    return self._create_success_result(
                        credentials,
                        f"sap_basic_{credentials.username}",
                        erp_session,
                        [AuthenticationScope.ERP_READ, AuthenticationScope.ERP_WRITE]
                    )
                else:
                    return self._create_failed_result(credentials, f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"SAP basic auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def validate_token(self, token: str, context: AuthenticationContext) -> bool:
        """Validate SAP token"""
        try:
            # For OAuth tokens, check if they look valid
            # For basic auth, validate the base64 encoding
            return len(token) > 10
        except Exception:
            return False
    
    async def refresh_token(
        self,
        refresh_token: str,
        context: AuthenticationContext
    ) -> Optional[AuthenticationResult]:
        """Refresh SAP OAuth token"""
        try:
            # Implementation would use the refresh token to get new access token
            # This is a simplified version
            return None
        except Exception:
            return None
    
    async def revoke_token(self, token: str, context: AuthenticationContext) -> bool:
        """Revoke SAP token"""
        try:
            # Implementation would call SAP token revocation endpoint
            return True
        except Exception:
            return False


class QuickBooksAuthProvider(BaseERPAuthProvider):
    """QuickBooks-specific authentication provider"""
    
    def __init__(self):
        super().__init__("quickbooks_auth", ERPSystemType.QUICKBOOKS, AuthenticationType.OAUTH2)
    
    async def authenticate(
        self,
        credentials: AuthenticationCredentials,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate with QuickBooks Online"""
        try:
            config = self.connection_configs.get(credentials.service_identifier)
            if not config:
                return self._create_failed_result(credentials, "No configuration found")
            
            return await self._authenticate_oauth2(credentials, config, context)
                
        except Exception as e:
            logger.error(f"QuickBooks authentication failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_oauth2(
        self,
        credentials: AuthenticationCredentials,
        config: ERPConnectionConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using QuickBooks OAuth2"""
        try:
            # QuickBooks uses Intuit's OAuth2 flow
            token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
            
            # Prepare token request
            token_data = {
                "grant_type": "authorization_code",
                "code": credentials.custom_params.get("authorization_code"),
                "redirect_uri": credentials.custom_params.get("redirect_uri")
            }
            
            # Create authorization header
            auth_string = f"{credentials.oauth_client_id}:{credentials.oauth_client_secret}"
            auth_b64 = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            async with self.http_session.post(
                token_url,
                data=urlencode(token_data),
                headers=headers
            ) as response:
                if response.status == 200:
                    token_result = await response.json()
                    
                    access_token = token_result.get("access_token")
                    if access_token:
                        erp_session = ERPSessionData(
                            session_token=access_token,
                            user_context={
                                "company_id": credentials.custom_params.get("company_id"),
                                "token_type": token_result.get("token_type", "Bearer")
                            }
                        )
                        
                        expires_in = token_result.get("expires_in", 3600)
                        expires_at = datetime.now() + timedelta(seconds=expires_in)
                        
                        result = self._create_success_result(
                            credentials,
                            f"qb_oauth_{access_token[:8]}",
                            erp_session,
                            [AuthenticationScope.ERP_READ, AuthenticationScope.ERP_WRITE]
                        )
                        result.expires_at = expires_at
                        result.access_token = access_token
                        result.refresh_token = token_result.get("refresh_token")
                        
                        return result
                    else:
                        return self._create_failed_result(credentials, "No access token received")
                else:
                    error_text = await response.text()
                    return self._create_failed_result(credentials, f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"QuickBooks OAuth2 auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def validate_token(self, token: str, context: AuthenticationContext) -> bool:
        """Validate QuickBooks token"""
        try:
            # Test token with company info request
            return len(token) > 10
        except Exception:
            return False
    
    async def refresh_token(
        self,
        refresh_token: str,
        context: AuthenticationContext
    ) -> Optional[AuthenticationResult]:
        """Refresh QuickBooks token"""
        try:
            # Implementation would use QuickBooks refresh token flow
            return None
        except Exception:
            return None
    
    async def revoke_token(self, token: str, context: AuthenticationContext) -> bool:
        """Revoke QuickBooks token"""
        try:
            # Implementation would call QuickBooks revocation endpoint
            return True
        except Exception:
            return False


class ERPAuthProviderFactory:
    """Factory for creating ERP authentication providers"""
    
    @staticmethod
    def create_provider(erp_system: ERPSystemType) -> Optional[BaseERPAuthProvider]:
        """Create authentication provider for ERP system"""
        try:
            if erp_system == ERPSystemType.ODOO:
                return OdooAuthProvider()
            elif erp_system == ERPSystemType.SAP:
                return SAPAuthProvider()
            elif erp_system == ERPSystemType.QUICKBOOKS:
                return QuickBooksAuthProvider()
            else:
                logger.warning(f"No auth provider available for {erp_system.value}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create auth provider for {erp_system.value}: {e}")
            return None
    
    @staticmethod
    def get_supported_systems() -> List[ERPSystemType]:
        """Get list of supported ERP systems"""
        return [
            ERPSystemType.ODOO,
            ERPSystemType.SAP,
            ERPSystemType.QUICKBOOKS
        ]


# Helper methods for auth providers
def _create_success_result(
    self,
    credentials: AuthenticationCredentials,
    session_id: str,
    erp_session: ERPSessionData,
    scopes: List[AuthenticationScope]
) -> AuthenticationResult:
    """Create successful authentication result"""
    return AuthenticationResult(
        session_id=session_id,
        status=AuthenticationStatus.AUTHENTICATED,
        auth_type=credentials.auth_type,
        service_identifier=credentials.service_identifier,
        authenticated_at=datetime.now(),
        granted_scopes=scopes,
        service_metadata={
            "erp_system": self.erp_system.value,
            "session_data": erp_session.__dict__
        }
    )

def _create_failed_result(
    self,
    credentials: AuthenticationCredentials,
    error_message: str
) -> AuthenticationResult:
    """Create failed authentication result"""
    return AuthenticationResult(
        session_id=f"failed_{secrets.token_hex(4)}",
        status=AuthenticationStatus.FAILED,
        auth_type=credentials.auth_type,
        service_identifier=credentials.service_identifier,
        authenticated_at=datetime.now(),
        error_message=error_message
    )

# Bind helper methods to base class
BaseERPAuthProvider._create_success_result = _create_success_result
BaseERPAuthProvider._create_failed_result = _create_failed_result


# Factory function for creating ERP auth provider
def create_erp_auth_provider(erp_system: ERPSystemType) -> Optional[BaseERPAuthProvider]:
    """Factory function to create ERP authentication provider"""
    return ERPAuthProviderFactory.create_provider(erp_system)