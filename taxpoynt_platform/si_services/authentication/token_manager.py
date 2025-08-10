"""
Token Manager Service

This module provides comprehensive token management for OAuth2, JWT, and other
token-based authentication systems used in SI services, including token generation,
validation, refresh, revocation, and secure storage.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import secrets
import hashlib
import hmac
import base64
import jwt
from pathlib import Path
import aiofiles
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Types of tokens"""
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"
    API_KEY = "api_key"
    SESSION_TOKEN = "session_token"
    BEARER_TOKEN = "bearer_token"
    JWT = "jwt"
    CUSTOM = "custom"


class TokenStatus(Enum):
    """Token status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"
    PENDING = "pending"
    SUSPENDED = "suspended"


class GrantType(Enum):
    """OAuth2 grant types"""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    PASSWORD = "password"
    IMPLICIT = "implicit"
    DEVICE_CODE = "device_code"


class TokenAlgorithm(Enum):
    """Token signing algorithms"""
    HS256 = "HS256"
    HS384 = "HS384"
    HS512 = "HS512"
    RS256 = "RS256"
    RS384 = "RS384"
    RS512 = "RS512"
    ES256 = "ES256"
    ES384 = "ES384"
    ES512 = "ES512"


@dataclass
class TokenInfo:
    """Information about a token"""
    token_id: str
    token_type: TokenType
    token_value: str
    token_hash: str
    issued_at: datetime
    expires_at: Optional[datetime] = None
    not_before: Optional[datetime] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None
    subject: Optional[str] = None
    scope: List[str] = field(default_factory=list)
    claims: Dict[str, Any] = field(default_factory=dict)
    status: TokenStatus = TokenStatus.ACTIVE
    refresh_token_id: Optional[str] = None
    parent_token_id: Optional[str] = None
    client_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenConfig:
    """Configuration for token management"""
    default_access_token_ttl: int = 3600  # 1 hour
    default_refresh_token_ttl: int = 604800  # 1 week
    default_id_token_ttl: int = 3600  # 1 hour
    jwt_issuer: str = "taxpoynt-si"
    jwt_audience: str = "taxpoynt-platform"
    jwt_algorithm: TokenAlgorithm = TokenAlgorithm.HS256
    jwt_secret_key: Optional[str] = None
    jwt_private_key_path: Optional[str] = None
    jwt_public_key_path: Optional[str] = None
    enable_token_rotation: bool = True
    enable_token_binding: bool = False
    max_tokens_per_client: int = 100
    token_storage_path: Optional[str] = None
    enable_token_encryption: bool = True
    cleanup_interval_minutes: int = 60


@dataclass
class TokenRequest:
    """Token generation request"""
    token_type: TokenType
    client_id: str
    user_id: Optional[str] = None
    scope: List[str] = field(default_factory=list)
    claims: Dict[str, Any] = field(default_factory=dict)
    expires_in: Optional[int] = None
    audience: Optional[str] = None
    subject: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenResponse:
    """Token generation response"""
    access_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None
    token_info: Optional[TokenInfo] = None
    error: Optional[str] = None


class TokenManager:
    """
    Comprehensive token management service for SI authentication,
    supporting OAuth2, JWT, and custom token formats.
    """
    
    def __init__(self, config: TokenConfig):
        self.config = config
        self.active_tokens: Dict[str, TokenInfo] = {}
        self.token_by_value: Dict[str, str] = {}  # token_value -> token_id
        self.client_tokens: Dict[str, List[str]] = {}  # client_id -> [token_ids]
        self.user_tokens: Dict[str, List[str]] = {}  # user_id -> [token_ids]
        
        # Cryptographic keys
        self.jwt_secret_key: Optional[str] = None
        self.jwt_private_key: Optional[Any] = None
        self.jwt_public_key: Optional[Any] = None
        
        # Background tasks
        self.is_running = False
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Setup storage
        if config.token_storage_path:
            self.storage_path = Path(config.token_storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = None
    
    async def initialize(self) -> None:
        """Initialize token manager"""
        try:
            self.is_running = True
            
            # Load cryptographic keys
            await self._load_crypto_keys()
            
            # Load stored tokens
            if self.storage_path:
                await self._load_stored_tokens()
            
            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info("Token manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize token manager: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown token manager"""
        try:
            self.is_running = False
            
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Save current state
            await self._save_token_state()
            
            logger.info("Token manager shutdown")
            
        except Exception as e:
            logger.error(f"Token manager shutdown error: {e}")
    
    async def generate_token(self, request: TokenRequest) -> TokenResponse:
        """Generate a new token"""
        try:
            # Check client token limits
            if not await self._check_token_limits(request.client_id):
                return TokenResponse(error="Token limit exceeded for client")
            
            # Generate token based on type
            if request.token_type == TokenType.JWT:
                return await self._generate_jwt_token(request)
            elif request.token_type in [TokenType.ACCESS_TOKEN, TokenType.REFRESH_TOKEN]:
                return await self._generate_oauth_tokens(request)
            elif request.token_type == TokenType.API_KEY:
                return await self._generate_api_key(request)
            else:
                return await self._generate_generic_token(request)
                
        except Exception as e:
            logger.error(f"Token generation failed: {e}")
            return TokenResponse(error=str(e))
    
    async def _generate_jwt_token(self, request: TokenRequest) -> TokenResponse:
        """Generate JWT token"""
        try:
            now = datetime.now()
            expires_in = request.expires_in or self.config.default_access_token_ttl
            expires_at = now + timedelta(seconds=expires_in)
            
            # Prepare JWT payload
            payload = {
                "iss": self.config.jwt_issuer,
                "aud": request.audience or self.config.jwt_audience,
                "sub": request.subject or request.user_id,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
                "client_id": request.client_id,
                "scope": " ".join(request.scope),
                "jti": secrets.token_hex(16),  # JWT ID
                **request.claims
            }
            
            if request.session_id:
                payload["session_id"] = request.session_id
            
            # Sign JWT
            if self.config.jwt_algorithm.value.startswith("HS"):
                # HMAC signing
                if not self.jwt_secret_key:
                    raise ValueError("JWT secret key not configured")
                
                token_value = jwt.encode(
                    payload,
                    self.jwt_secret_key,
                    algorithm=self.config.jwt_algorithm.value
                )
            else:
                # RSA/EC signing
                if not self.jwt_private_key:
                    raise ValueError("JWT private key not configured")
                
                token_value = jwt.encode(
                    payload,
                    self.jwt_private_key,
                    algorithm=self.config.jwt_algorithm.value
                )
            
            # Create token info
            token_info = TokenInfo(
                token_id=payload["jti"],
                token_type=TokenType.JWT,
                token_value=token_value,
                token_hash=hashlib.sha256(token_value.encode()).hexdigest(),
                issued_at=now,
                expires_at=expires_at,
                issuer=payload["iss"],
                audience=payload["aud"],
                subject=payload["sub"],
                scope=request.scope,
                claims=request.claims,
                client_id=request.client_id,
                user_id=request.user_id,
                session_id=request.session_id,
                metadata=request.metadata
            )
            
            # Store token
            await self._store_token(token_info)
            
            return TokenResponse(
                access_token=token_value,
                token_type="Bearer",
                expires_in=expires_in,
                scope=" ".join(request.scope),
                token_info=token_info
            )
            
        except Exception as e:
            logger.error(f"JWT generation failed: {e}")
            return TokenResponse(error=str(e))
    
    async def _generate_oauth_tokens(self, request: TokenRequest) -> TokenResponse:
        """Generate OAuth2 access and refresh tokens"""
        try:
            now = datetime.now()
            
            # Generate access token
            access_token_value = self._generate_secure_token()
            access_expires_in = request.expires_in or self.config.default_access_token_ttl
            access_expires_at = now + timedelta(seconds=access_expires_in)
            
            access_token_id = secrets.token_hex(16)
            access_token_info = TokenInfo(
                token_id=access_token_id,
                token_type=TokenType.ACCESS_TOKEN,
                token_value=access_token_value,
                token_hash=hashlib.sha256(access_token_value.encode()).hexdigest(),
                issued_at=now,
                expires_at=access_expires_at,
                issuer=self.config.jwt_issuer,
                audience=request.audience or self.config.jwt_audience,
                subject=request.subject or request.user_id,
                scope=request.scope,
                claims=request.claims,
                client_id=request.client_id,
                user_id=request.user_id,
                session_id=request.session_id,
                metadata=request.metadata
            )
            
            # Generate refresh token if requested
            refresh_token_value = None
            refresh_token_info = None
            
            if request.token_type == TokenType.ACCESS_TOKEN or "offline_access" in request.scope:
                refresh_token_value = self._generate_secure_token()
                refresh_expires_at = now + timedelta(seconds=self.config.default_refresh_token_ttl)
                
                refresh_token_id = secrets.token_hex(16)
                refresh_token_info = TokenInfo(
                    token_id=refresh_token_id,
                    token_type=TokenType.REFRESH_TOKEN,
                    token_value=refresh_token_value,
                    token_hash=hashlib.sha256(refresh_token_value.encode()).hexdigest(),
                    issued_at=now,
                    expires_at=refresh_expires_at,
                    issuer=self.config.jwt_issuer,
                    audience=request.audience or self.config.jwt_audience,
                    subject=request.subject or request.user_id,
                    scope=["offline_access"],
                    client_id=request.client_id,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    metadata=request.metadata
                )
                
                # Link tokens
                access_token_info.refresh_token_id = refresh_token_id
                refresh_token_info.parent_token_id = access_token_id
            
            # Store tokens
            await self._store_token(access_token_info)
            if refresh_token_info:
                await self._store_token(refresh_token_info)
            
            return TokenResponse(
                access_token=access_token_value,
                token_type="Bearer",
                expires_in=access_expires_in,
                refresh_token=refresh_token_value,
                scope=" ".join(request.scope),
                token_info=access_token_info
            )
            
        except Exception as e:
            logger.error(f"OAuth token generation failed: {e}")
            return TokenResponse(error=str(e))
    
    async def _generate_api_key(self, request: TokenRequest) -> TokenResponse:
        """Generate API key"""
        try:
            now = datetime.now()
            
            # Generate API key
            api_key_value = f"tpsi_{secrets.token_urlsafe(32)}"
            
            # API keys typically don't expire unless specified
            expires_at = None
            if request.expires_in:
                expires_at = now + timedelta(seconds=request.expires_in)
            
            api_key_id = secrets.token_hex(16)
            api_key_info = TokenInfo(
                token_id=api_key_id,
                token_type=TokenType.API_KEY,
                token_value=api_key_value,
                token_hash=hashlib.sha256(api_key_value.encode()).hexdigest(),
                issued_at=now,
                expires_at=expires_at,
                issuer=self.config.jwt_issuer,
                audience=request.audience or self.config.jwt_audience,
                subject=request.subject or request.user_id,
                scope=request.scope,
                claims=request.claims,
                client_id=request.client_id,
                user_id=request.user_id,
                session_id=request.session_id,
                metadata=request.metadata
            )
            
            await self._store_token(api_key_info)
            
            return TokenResponse(
                access_token=api_key_value,
                token_type="API-Key",
                expires_in=request.expires_in,
                scope=" ".join(request.scope),
                token_info=api_key_info
            )
            
        except Exception as e:
            logger.error(f"API key generation failed: {e}")
            return TokenResponse(error=str(e))
    
    async def _generate_generic_token(self, request: TokenRequest) -> TokenResponse:
        """Generate generic token"""
        try:
            now = datetime.now()
            expires_in = request.expires_in or self.config.default_access_token_ttl
            expires_at = now + timedelta(seconds=expires_in)
            
            token_value = self._generate_secure_token()
            token_id = secrets.token_hex(16)
            
            token_info = TokenInfo(
                token_id=token_id,
                token_type=request.token_type,
                token_value=token_value,
                token_hash=hashlib.sha256(token_value.encode()).hexdigest(),
                issued_at=now,
                expires_at=expires_at,
                issuer=self.config.jwt_issuer,
                audience=request.audience or self.config.jwt_audience,
                subject=request.subject or request.user_id,
                scope=request.scope,
                claims=request.claims,
                client_id=request.client_id,
                user_id=request.user_id,
                session_id=request.session_id,
                metadata=request.metadata
            )
            
            await self._store_token(token_info)
            
            return TokenResponse(
                access_token=token_value,
                token_type="Bearer",
                expires_in=expires_in,
                scope=" ".join(request.scope),
                token_info=token_info
            )
            
        except Exception as e:
            logger.error(f"Generic token generation failed: {e}")
            return TokenResponse(error=str(e))
    
    def _generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    async def validate_token(self, token_value: str) -> Tuple[bool, Optional[TokenInfo]]:
        """Validate a token"""
        try:
            # Find token by value
            token_id = self.token_by_value.get(token_value)
            if not token_id:
                return False, None
            
            token_info = self.active_tokens.get(token_id)
            if not token_info:
                return False, None
            
            # Check token status
            if token_info.status != TokenStatus.ACTIVE:
                return False, token_info
            
            # Check expiration
            if token_info.expires_at and datetime.now() > token_info.expires_at:
                token_info.status = TokenStatus.EXPIRED
                return False, token_info
            
            # Check not before
            if token_info.not_before and datetime.now() < token_info.not_before:
                return False, token_info
            
            # Additional validation for JWT tokens
            if token_info.token_type == TokenType.JWT:
                jwt_valid = await self._validate_jwt_token(token_value)
                if not jwt_valid:
                    return False, token_info
            
            return True, token_info
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False, None
    
    async def _validate_jwt_token(self, token_value: str) -> bool:
        """Validate JWT token signature and claims"""
        try:
            if self.config.jwt_algorithm.value.startswith("HS"):
                # HMAC verification
                if not self.jwt_secret_key:
                    return False
                
                payload = jwt.decode(
                    token_value,
                    self.jwt_secret_key,
                    algorithms=[self.config.jwt_algorithm.value]
                )
            else:
                # RSA/EC verification
                if not self.jwt_public_key:
                    return False
                
                payload = jwt.decode(
                    token_value,
                    self.jwt_public_key,
                    algorithms=[self.config.jwt_algorithm.value]
                )
            
            # Validate issuer and audience
            if payload.get("iss") != self.config.jwt_issuer:
                return False
            
            if payload.get("aud") != self.config.jwt_audience:
                return False
            
            return True
            
        except jwt.ExpiredSignatureError:
            logger.debug("JWT token expired")
            return False
        except jwt.InvalidTokenError as e:
            logger.debug(f"JWT token invalid: {e}")
            return False
        except Exception as e:
            logger.error(f"JWT validation error: {e}")
            return False
    
    async def refresh_token(self, refresh_token_value: str) -> TokenResponse:
        """Refresh an access token using refresh token"""
        try:
            # Validate refresh token
            is_valid, refresh_token_info = await self.validate_token(refresh_token_value)
            
            if not is_valid or not refresh_token_info:
                return TokenResponse(error="Invalid refresh token")
            
            if refresh_token_info.token_type != TokenType.REFRESH_TOKEN:
                return TokenResponse(error="Token is not a refresh token")
            
            # Find original access token
            original_token_id = refresh_token_info.parent_token_id
            if not original_token_id:
                return TokenResponse(error="No associated access token")
            
            original_token = self.active_tokens.get(original_token_id)
            if not original_token:
                return TokenResponse(error="Original access token not found")
            
            # Revoke old access token if rotation is enabled
            if self.config.enable_token_rotation:
                await self.revoke_token(original_token.token_value)
            
            # Generate new access token
            new_request = TokenRequest(
                token_type=TokenType.ACCESS_TOKEN,
                client_id=refresh_token_info.client_id,
                user_id=refresh_token_info.user_id,
                scope=original_token.scope,
                claims=original_token.claims,
                audience=original_token.audience,
                subject=original_token.subject,
                session_id=refresh_token_info.session_id,
                metadata=original_token.metadata
            )
            
            new_token_response = await self._generate_oauth_tokens(new_request)
            
            # Update refresh token's parent reference
            if new_token_response.token_info:
                refresh_token_info.parent_token_id = new_token_response.token_info.token_id
            
            return new_token_response
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return TokenResponse(error=str(e))
    
    async def revoke_token(self, token_value: str) -> bool:
        """Revoke a token"""
        try:
            token_id = self.token_by_value.get(token_value)
            if not token_id:
                return False
            
            token_info = self.active_tokens.get(token_id)
            if not token_info:
                return False
            
            # Mark as revoked
            token_info.status = TokenStatus.REVOKED
            
            # Remove from lookup
            if token_value in self.token_by_value:
                del self.token_by_value[token_value]
            
            # Remove from client and user token lists
            if token_info.client_id and token_info.client_id in self.client_tokens:
                if token_id in self.client_tokens[token_info.client_id]:
                    self.client_tokens[token_info.client_id].remove(token_id)
            
            if token_info.user_id and token_info.user_id in self.user_tokens:
                if token_id in self.user_tokens[token_info.user_id]:
                    self.user_tokens[token_info.user_id].remove(token_id)
            
            # Revoke associated refresh token
            if token_info.refresh_token_id:
                refresh_token = self.active_tokens.get(token_info.refresh_token_id)
                if refresh_token:
                    refresh_token.status = TokenStatus.REVOKED
                    if refresh_token.token_value in self.token_by_value:
                        del self.token_by_value[refresh_token.token_value]
            
            logger.info(f"Revoked token: {token_id}")
            return True
            
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False
    
    async def get_token_info(self, token_value: str) -> Optional[TokenInfo]:
        """Get token information"""
        try:
            token_id = self.token_by_value.get(token_value)
            if token_id:
                return self.active_tokens.get(token_id)
            return None
        except Exception:
            return None
    
    async def list_tokens(
        self,
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
        token_type: Optional[TokenType] = None,
        status: Optional[TokenStatus] = None
    ) -> List[TokenInfo]:
        """List tokens with optional filters"""
        try:
            tokens = []
            
            # Start with all tokens or filter by client/user
            if client_id:
                token_ids = self.client_tokens.get(client_id, [])
                token_list = [self.active_tokens[tid] for tid in token_ids if tid in self.active_tokens]
            elif user_id:
                token_ids = self.user_tokens.get(user_id, [])
                token_list = [self.active_tokens[tid] for tid in token_ids if tid in self.active_tokens]
            else:
                token_list = list(self.active_tokens.values())
            
            # Apply additional filters
            for token in token_list:
                if token_type and token.token_type != token_type:
                    continue
                if status and token.status != status:
                    continue
                tokens.append(token)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Token listing failed: {e}")
            return []
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        try:
            now = datetime.now()
            expired_count = 0
            tokens_to_remove = []
            
            for token_id, token_info in self.active_tokens.items():
                if (token_info.expires_at and now > token_info.expires_at and
                    token_info.status == TokenStatus.ACTIVE):
                    token_info.status = TokenStatus.EXPIRED
                    tokens_to_remove.append(token_id)
                    expired_count += 1
            
            # Remove expired tokens from lookup tables
            for token_id in tokens_to_remove:
                token_info = self.active_tokens[token_id]
                if token_info.token_value in self.token_by_value:
                    del self.token_by_value[token_info.token_value]
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired tokens")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Token cleanup failed: {e}")
            return 0
    
    async def _store_token(self, token_info: TokenInfo) -> None:
        """Store token in memory and optionally persist"""
        try:
            # Store in memory
            self.active_tokens[token_info.token_id] = token_info
            self.token_by_value[token_info.token_value] = token_info.token_id
            
            # Update client tokens
            if token_info.client_id:
                if token_info.client_id not in self.client_tokens:
                    self.client_tokens[token_info.client_id] = []
                self.client_tokens[token_info.client_id].append(token_info.token_id)
            
            # Update user tokens
            if token_info.user_id:
                if token_info.user_id not in self.user_tokens:
                    self.user_tokens[token_info.user_id] = []
                self.user_tokens[token_info.user_id].append(token_info.token_id)
            
            # Persist to storage if enabled
            if self.storage_path:
                await self._persist_token(token_info)
                
        except Exception as e:
            logger.error(f"Token storage failed: {e}")
    
    async def _persist_token(self, token_info: TokenInfo) -> None:
        """Persist token to storage"""
        try:
            token_file = self.storage_path / f"token_{token_info.token_id}.json"
            
            # Prepare token data (exclude sensitive info)
            token_data = {
                "token_id": token_info.token_id,
                "token_type": token_info.token_type.value,
                "token_hash": token_info.token_hash,
                "issued_at": token_info.issued_at.isoformat(),
                "expires_at": token_info.expires_at.isoformat() if token_info.expires_at else None,
                "issuer": token_info.issuer,
                "audience": token_info.audience,
                "subject": token_info.subject,
                "scope": token_info.scope,
                "status": token_info.status.value,
                "client_id": token_info.client_id,
                "user_id": token_info.user_id,
                "session_id": token_info.session_id,
                "metadata": token_info.metadata
            }
            
            async with aiofiles.open(token_file, 'w') as f:
                await f.write(json.dumps(token_data, indent=2))
                
        except Exception as e:
            logger.error(f"Token persistence failed: {e}")
    
    async def _load_stored_tokens(self) -> None:
        """Load tokens from storage"""
        try:
            if not self.storage_path:
                return
            
            token_files = list(self.storage_path.glob("token_*.json"))
            loaded_count = 0
            
            for token_file in token_files:
                try:
                    async with aiofiles.open(token_file, 'r') as f:
                        token_data = json.loads(await f.read())
                    
                    # Reconstruct token info (without sensitive token value)
                    token_info = TokenInfo(
                        token_id=token_data["token_id"],
                        token_type=TokenType(token_data["token_type"]),
                        token_value="",  # Not stored
                        token_hash=token_data["token_hash"],
                        issued_at=datetime.fromisoformat(token_data["issued_at"]),
                        expires_at=datetime.fromisoformat(token_data["expires_at"]) if token_data.get("expires_at") else None,
                        issuer=token_data.get("issuer"),
                        audience=token_data.get("audience"),
                        subject=token_data.get("subject"),
                        scope=token_data.get("scope", []),
                        status=TokenStatus(token_data.get("status", "active")),
                        client_id=token_data.get("client_id"),
                        user_id=token_data.get("user_id"),
                        session_id=token_data.get("session_id"),
                        metadata=token_data.get("metadata", {})
                    )
                    
                    # Only load if not expired
                    if (not token_info.expires_at or 
                        datetime.now() < token_info.expires_at):
                        self.active_tokens[token_info.token_id] = token_info
                        loaded_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to load token from {token_file}: {e}")
            
            logger.info(f"Loaded {loaded_count} tokens from storage")
            
        except Exception as e:
            logger.error(f"Failed to load stored tokens: {e}")
    
    async def _load_crypto_keys(self) -> None:
        """Load cryptographic keys"""
        try:
            # Load JWT secret key
            if self.config.jwt_secret_key:
                self.jwt_secret_key = self.config.jwt_secret_key
            else:
                # Generate random secret if none provided
                self.jwt_secret_key = secrets.token_urlsafe(32)
                logger.warning("Using generated JWT secret key - configure for production")
            
            # Load RSA keys if paths provided
            if self.config.jwt_private_key_path:
                private_key_path = Path(self.config.jwt_private_key_path)
                if private_key_path.exists():
                    async with aiofiles.open(private_key_path, 'rb') as f:
                        private_key_data = await f.read()
                    self.jwt_private_key = load_pem_private_key(private_key_data, password=None)
            
            if self.config.jwt_public_key_path:
                public_key_path = Path(self.config.jwt_public_key_path)
                if public_key_path.exists():
                    async with aiofiles.open(public_key_path, 'rb') as f:
                        public_key_data = await f.read()
                    self.jwt_public_key = load_pem_public_key(public_key_data)
            
            logger.info("Cryptographic keys loaded")
            
        except Exception as e:
            logger.error(f"Failed to load crypto keys: {e}")
            raise
    
    async def _check_token_limits(self, client_id: str) -> bool:
        """Check if client has exceeded token limits"""
        try:
            client_token_count = len(self.client_tokens.get(client_id, []))
            return client_token_count < self.config.max_tokens_per_client
        except Exception:
            return True
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop"""
        while self.is_running:
            try:
                await self.cleanup_expired_tokens()
                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _save_token_state(self) -> None:
        """Save current token state"""
        try:
            if not self.storage_path:
                return
            
            state_data = {
                "active_tokens_count": len(self.active_tokens),
                "total_clients": len(self.client_tokens),
                "total_users": len(self.user_tokens),
                "timestamp": datetime.now().isoformat()
            }
            
            state_file = self.storage_path / "token_state.json"
            async with aiofiles.open(state_file, 'w') as f:
                await f.write(json.dumps(state_data, indent=2))
                
        except Exception as e:
            logger.error(f"Failed to save token state: {e}")
    
    def get_token_stats(self) -> Dict[str, Any]:
        """Get token manager statistics"""
        try:
            stats = {
                "total_tokens": len(self.active_tokens),
                "active_tokens": len([t for t in self.active_tokens.values() if t.status == TokenStatus.ACTIVE]),
                "expired_tokens": len([t for t in self.active_tokens.values() if t.status == TokenStatus.EXPIRED]),
                "revoked_tokens": len([t for t in self.active_tokens.values() if t.status == TokenStatus.REVOKED]),
                "total_clients": len(self.client_tokens),
                "total_users": len(self.user_tokens),
                "token_types": {},
                "config": {
                    "jwt_algorithm": self.config.jwt_algorithm.value,
                    "default_access_token_ttl": self.config.default_access_token_ttl,
                    "default_refresh_token_ttl": self.config.default_refresh_token_ttl,
                    "enable_token_rotation": self.config.enable_token_rotation
                }
            }
            
            # Count tokens by type
            for token in self.active_tokens.values():
                token_type = token.token_type.value
                stats["token_types"][token_type] = stats["token_types"].get(token_type, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get token stats: {e}")
            return {}


# Factory function for creating token manager
def create_token_manager(config: Optional[TokenConfig] = None) -> TokenManager:
    """Factory function to create token manager"""
    if config is None:
        config = TokenConfig()
    
    return TokenManager(config)