"""
JWT Service

This service manages JWT token creation, validation, and lifecycle management
for the TaxPoynt platform authentication system.
"""

import asyncio
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import uuid

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError
)


class TokenType(Enum):
    """JWT token types"""
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"
    API_KEY = "api_key"
    SESSION_TOKEN = "session_token"


class Algorithm(Enum):
    """JWT signing algorithms"""
    HS256 = "HS256"
    HS384 = "HS384"
    HS512 = "HS512"
    RS256 = "RS256"
    RS384 = "RS384"
    RS512 = "RS512"
    ES256 = "ES256"
    ES384 = "ES384"
    ES512 = "ES512"


class TokenStatus(Enum):
    """Token status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


@dataclass
class JWTConfig:
    """JWT configuration"""
    issuer: str
    algorithm: Algorithm = Algorithm.RS256
    access_token_ttl: timedelta = field(default_factory=lambda: timedelta(hours=1))
    refresh_token_ttl: timedelta = field(default_factory=lambda: timedelta(days=30))
    id_token_ttl: timedelta = field(default_factory=lambda: timedelta(hours=1))
    api_key_ttl: timedelta = field(default_factory=lambda: timedelta(days=365))
    session_token_ttl: timedelta = field(default_factory=lambda: timedelta(hours=8))
    audience: Optional[str] = None
    leeway: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    enable_jti: bool = True
    enable_nbf: bool = True


@dataclass
class JWTClaims:
    """JWT claims"""
    sub: str  # Subject (user ID)
    iss: str  # Issuer
    aud: Optional[str] = None  # Audience
    exp: Optional[datetime] = None  # Expiration
    nbf: Optional[datetime] = None  # Not before
    iat: Optional[datetime] = None  # Issued at
    jti: Optional[str] = None  # JWT ID
    token_type: Optional[TokenType] = None
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    scope: Optional[str] = None
    custom_claims: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenInfo:
    """Token information"""
    token_id: str
    user_id: str
    token_type: TokenType
    status: TokenStatus = TokenStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KeyPair:
    """JWT signing key pair"""
    key_id: str
    algorithm: Algorithm
    private_key: str
    public_key: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    active: bool = True
    usage_count: int = 0


@dataclass
class TokenValidationResult:
    """Token validation result"""
    valid: bool
    claims: Optional[JWTClaims] = None
    token_info: Optional[TokenInfo] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)


class JWTService(BaseService):
    """
    JWT Service
    
    Manages JWT token creation, validation, and lifecycle management
    for the TaxPoynt platform authentication system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # JWT configuration
        self.jwt_config = JWTConfig(
            issuer=self.config.get('issuer', 'taxpoynt-platform'),
            algorithm=Algorithm(self.config.get('algorithm', 'RS256')),
            audience=self.config.get('audience', 'taxpoynt-api')
        )
        
        # Key management
        self.key_pairs: Dict[str, KeyPair] = {}
        self.current_key_id: Optional[str] = None
        self.secret_key: Optional[str] = None
        
        # Token storage and tracking
        self.active_tokens: Dict[str, TokenInfo] = {}
        self.revoked_tokens: Set[str] = set()
        self.user_tokens: Dict[str, List[str]] = {}  # user_id -> token_ids
        
        # Token blacklist for additional security
        self.token_blacklist: Set[str] = set()
        
        # Validation cache
        self.validation_cache: Dict[str, TokenValidationResult] = {}
        self.cache_ttl: timedelta = timedelta(minutes=5)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Background tasks
        self.background_tasks: Dict[str, asyncio.Task] = {}
        
        # Performance metrics
        self.metrics = {
            'tokens_created': 0,
            'tokens_validated': 0,
            'tokens_revoked': 0,
            'validation_cache_hits': 0,
            'validation_cache_misses': 0,
            'key_rotations': 0,
            'validation_errors': 0,
            'expired_tokens_cleaned': 0
        }
    
    async def initialize(self) -> None:
        """Initialize JWT service"""
        try:
            self.logger.info("Initializing JWTService")
            
            # Initialize signing keys
            await self._initialize_signing_keys()
            
            # Start background workers
            await self._start_background_workers()
            
            self.logger.info("JWTService initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize JWTService: {str(e)}")
            raise AuthenticationError(f"Initialization failed: {str(e)}")
    
    async def create_token(
        self,
        user_id: str,
        token_type: TokenType,
        roles: Optional[Set[str]] = None,
        permissions: Optional[Set[str]] = None,
        tenant_id: Optional[str] = None,
        session_id: Optional[str] = None,
        scope: Optional[str] = None,
        custom_claims: Optional[Dict[str, Any]] = None,
        ttl_override: Optional[timedelta] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> str:
        """Create JWT token"""
        try:
            # Generate token ID
            jti = str(uuid.uuid4()) if self.jwt_config.enable_jti else None
            
            # Calculate expiration
            now = datetime.utcnow()
            ttl = ttl_override or self._get_default_ttl(token_type)
            exp = now + ttl
            
            # Create claims
            claims = JWTClaims(
                sub=user_id,
                iss=self.jwt_config.issuer,
                aud=self.jwt_config.audience,
                iat=now,
                exp=exp,
                nbf=now if self.jwt_config.enable_nbf else None,
                jti=jti,
                token_type=token_type,
                roles=roles or set(),
                permissions=permissions or set(),
                tenant_id=tenant_id,
                session_id=session_id,
                scope=scope,
                custom_claims=custom_claims or {}
            )
            
            # Generate token
            token = await self._encode_token(claims)
            
            # Store token info
            if jti:
                token_info = TokenInfo(
                    token_id=jti,
                    user_id=user_id,
                    token_type=token_type,
                    expires_at=exp,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_id=device_id
                )
                
                self.active_tokens[jti] = token_info
                
                # Add to user tokens
                if user_id not in self.user_tokens:
                    self.user_tokens[user_id] = []
                self.user_tokens[user_id].append(jti)
            
            self.metrics['tokens_created'] += 1
            self.logger.info(f"Token created: {token_type.value} for user {user_id}")
            
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to create token: {str(e)}")
            raise AuthenticationError(f"Token creation failed: {str(e)}")
    
    async def validate_token(
        self,
        token: str,
        expected_type: Optional[TokenType] = None,
        required_permissions: Optional[Set[str]] = None,
        required_roles: Optional[Set[str]] = None,
        use_cache: bool = True
    ) -> TokenValidationResult:
        """Validate JWT token"""
        try:
            # Check cache first
            if use_cache:
                cached_result = await self._get_from_validation_cache(token)
                if cached_result:
                    self.metrics['validation_cache_hits'] += 1
                    return cached_result
            
            # Decode and validate token
            try:
                claims = await self._decode_token(token)
            except Exception as e:
                result = TokenValidationResult(
                    valid=False,
                    error=f"Token decode failed: {str(e)}"
                )
                await self._cache_validation_result(token, result)
                self.metrics['validation_errors'] += 1
                return result
            
            # Check if token is revoked
            if claims.jti and (claims.jti in self.revoked_tokens or claims.jti in self.token_blacklist):
                result = TokenValidationResult(
                    valid=False,
                    claims=claims,
                    error="Token has been revoked"
                )
                await self._cache_validation_result(token, result)
                return result
            
            # Get token info
            token_info = None
            if claims.jti and claims.jti in self.active_tokens:
                token_info = self.active_tokens[claims.jti]
                
                # Update usage tracking
                token_info.last_used = datetime.utcnow()
                token_info.usage_count += 1
            
            # Validate token type
            if expected_type and claims.token_type != expected_type:
                result = TokenValidationResult(
                    valid=False,
                    claims=claims,
                    token_info=token_info,
                    error=f"Expected token type {expected_type.value}, got {claims.token_type.value if claims.token_type else 'unknown'}"
                )
                await self._cache_validation_result(token, result)
                return result
            
            # Validate permissions
            if required_permissions and not claims.permissions.issuperset(required_permissions):
                missing_permissions = required_permissions - claims.permissions
                result = TokenValidationResult(
                    valid=False,
                    claims=claims,
                    token_info=token_info,
                    error=f"Missing required permissions: {', '.join(missing_permissions)}"
                )
                await self._cache_validation_result(token, result)
                return result
            
            # Validate roles
            if required_roles and not claims.roles.intersection(required_roles):
                result = TokenValidationResult(
                    valid=False,
                    claims=claims,
                    token_info=token_info,
                    error=f"Missing required roles: {', '.join(required_roles)}"
                )
                await self._cache_validation_result(token, result)
                return result
            
            # Token is valid
            result = TokenValidationResult(
                valid=True,
                claims=claims,
                token_info=token_info
            )
            
            # Cache result
            await self._cache_validation_result(token, result)
            
            self.metrics['tokens_validated'] += 1
            self.metrics['validation_cache_misses'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate token: {str(e)}")
            result = TokenValidationResult(
                valid=False,
                error=f"Validation error: {str(e)}"
            )
            self.metrics['validation_errors'] += 1
            return result
    
    async def revoke_token(
        self,
        token: Optional[str] = None,
        token_id: Optional[str] = None,
        revoked_by: str = "system",
        reason: str = "manual_revocation"
    ) -> bool:
        """Revoke JWT token"""
        try:
            jti = token_id
            
            # Extract token ID from token if needed
            if token and not jti:
                try:
                    claims = await self._decode_token(token, verify_expiration=False)
                    jti = claims.jti
                except Exception:
                    return False
            
            if not jti:
                return False
            
            # Add to revoked tokens
            self.revoked_tokens.add(jti)
            
            # Update token info
            if jti in self.active_tokens:
                token_info = self.active_tokens[jti]
                token_info.status = TokenStatus.REVOKED
                token_info.revoked_at = datetime.utcnow()
                token_info.revoked_by = revoked_by
                token_info.revocation_reason = reason
                
                # Remove from active tokens
                del self.active_tokens[jti]
                
                # Remove from user tokens
                if token_info.user_id in self.user_tokens:
                    self.user_tokens[token_info.user_id] = [
                        tid for tid in self.user_tokens[token_info.user_id] if tid != jti
                    ]
            
            # Clear validation cache
            await self._clear_token_from_cache(token or jti)
            
            self.metrics['tokens_revoked'] += 1
            self.logger.info(f"Token revoked: {jti}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revoke token: {str(e)}")
            return False
    
    async def revoke_user_tokens(
        self,
        user_id: str,
        token_type: Optional[TokenType] = None,
        revoked_by: str = "system",
        reason: str = "user_revocation"
    ) -> int:
        """Revoke all tokens for a user"""
        try:
            if user_id not in self.user_tokens:
                return 0
            
            revoked_count = 0
            token_ids = self.user_tokens[user_id].copy()
            
            for token_id in token_ids:
                if token_id in self.active_tokens:
                    token_info = self.active_tokens[token_id]
                    
                    # Filter by token type if specified
                    if token_type and token_info.token_type != token_type:
                        continue
                    
                    # Revoke token
                    if await self.revoke_token(token_id=token_id, revoked_by=revoked_by, reason=reason):
                        revoked_count += 1
            
            self.logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            return revoked_count
            
        except Exception as e:
            self.logger.error(f"Failed to revoke user tokens for {user_id}: {str(e)}")
            return 0
    
    async def refresh_token(
        self,
        refresh_token: str,
        new_permissions: Optional[Set[str]] = None,
        new_roles: Optional[Set[str]] = None
    ) -> Optional[str]:
        """Refresh access token using refresh token"""
        try:
            # Validate refresh token
            validation_result = await self.validate_token(
                refresh_token,
                expected_type=TokenType.REFRESH_TOKEN
            )
            
            if not validation_result.valid or not validation_result.claims:
                return None
            
            claims = validation_result.claims
            
            # Create new access token
            new_token = await self.create_token(
                user_id=claims.sub,
                token_type=TokenType.ACCESS_TOKEN,
                roles=new_roles or claims.roles,
                permissions=new_permissions or claims.permissions,
                tenant_id=claims.tenant_id,
                session_id=claims.session_id,
                scope=claims.scope,
                custom_claims=claims.custom_claims
            )
            
            self.logger.info(f"Token refreshed for user {claims.sub}")
            return new_token
            
        except Exception as e:
            self.logger.error(f"Failed to refresh token: {str(e)}")
            return None
    
    async def rotate_signing_key(self) -> str:
        """Rotate JWT signing key"""
        try:
            # Generate new key pair
            new_key_id = f"key_{int(datetime.utcnow().timestamp())}"
            
            if self.jwt_config.algorithm.value.startswith('RS'):
                # RSA key pair
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
                
                private_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ).decode()
                
                public_pem = private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()
                
                key_pair = KeyPair(
                    key_id=new_key_id,
                    algorithm=self.jwt_config.algorithm,
                    private_key=private_pem,
                    public_key=public_pem
                )
                
            elif self.jwt_config.algorithm.value.startswith('HS'):
                # HMAC secret
                secret = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode()
                
                key_pair = KeyPair(
                    key_id=new_key_id,
                    algorithm=self.jwt_config.algorithm,
                    private_key=secret,
                    public_key=secret
                )
            
            else:
                raise ValidationError(f"Unsupported algorithm: {self.jwt_config.algorithm}")
            
            # Store new key pair
            self.key_pairs[new_key_id] = key_pair
            
            # Deactivate old key (keep for verification)
            if self.current_key_id and self.current_key_id in self.key_pairs:
                self.key_pairs[self.current_key_id].active = False
            
            # Set as current key
            self.current_key_id = new_key_id
            
            self.metrics['key_rotations'] += 1
            self.logger.info(f"Signing key rotated: {new_key_id}")
            
            return new_key_id
            
        except Exception as e:
            self.logger.error(f"Failed to rotate signing key: {str(e)}")
            raise AuthenticationError(f"Key rotation failed: {str(e)}")
    
    async def get_public_keys(self) -> Dict[str, Any]:
        """Get public keys for token verification (JWKS format)"""
        try:
            keys = []
            
            for key_id, key_pair in self.key_pairs.items():
                if key_pair.algorithm.value.startswith('RS'):
                    # RSA public key
                    public_key = serialization.load_pem_public_key(key_pair.public_key.encode())
                    
                    # Convert to JWK format
                    public_numbers = public_key.public_numbers()
                    n = base64.urlsafe_b64encode(
                        public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')
                    ).decode().rstrip('=')
                    e = base64.urlsafe_b64encode(
                        public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')
                    ).decode().rstrip('=')
                    
                    key_data = {
                        'kty': 'RSA',
                        'kid': key_id,
                        'use': 'sig',
                        'alg': key_pair.algorithm.value,
                        'n': n,
                        'e': e
                    }
                    
                    keys.append(key_data)
            
            return {'keys': keys}
            
        except Exception as e:
            self.logger.error(f"Failed to get public keys: {str(e)}")
            return {'keys': []}
    
    async def get_user_tokens(
        self,
        user_id: str,
        token_type: Optional[TokenType] = None,
        active_only: bool = True
    ) -> List[TokenInfo]:
        """Get tokens for a user"""
        try:
            if user_id not in self.user_tokens:
                return []
            
            user_token_list = []
            
            for token_id in self.user_tokens[user_id]:
                if token_id in self.active_tokens:
                    token_info = self.active_tokens[token_id]
                    
                    # Filter by token type
                    if token_type and token_info.token_type != token_type:
                        continue
                    
                    # Filter by active status
                    if active_only and token_info.status != TokenStatus.ACTIVE:
                        continue
                    
                    # Check expiration
                    if active_only and token_info.expires_at and datetime.utcnow() > token_info.expires_at:
                        continue
                    
                    user_token_list.append(token_info)
            
            return user_token_list
            
        except Exception as e:
            self.logger.error(f"Failed to get user tokens for {user_id}: {str(e)}")
            return []
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get JWT service health status"""
        try:
            # Calculate token statistics
            active_count = len(self.active_tokens)
            expired_count = 0
            
            now = datetime.utcnow()
            for token_info in self.active_tokens.values():
                if token_info.expires_at and token_info.expires_at <= now:
                    expired_count += 1
            
            return {
                'service': 'JWTService',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'configuration': {
                    'issuer': self.jwt_config.issuer,
                    'algorithm': self.jwt_config.algorithm.value,
                    'audience': self.jwt_config.audience,
                    'access_token_ttl_hours': self.jwt_config.access_token_ttl.total_seconds() / 3600,
                    'refresh_token_ttl_days': self.jwt_config.refresh_token_ttl.days
                },
                'keys': {
                    'total': len(self.key_pairs),
                    'active': len([k for k in self.key_pairs.values() if k.active]),
                    'current_key_id': self.current_key_id
                },
                'tokens': {
                    'active': active_count,
                    'expired_pending_cleanup': expired_count,
                    'revoked': len(self.revoked_tokens),
                    'blacklisted': len(self.token_blacklist),
                    'users_with_tokens': len(self.user_tokens),
                    'by_type': {
                        token_type.value: len([t for t in self.active_tokens.values() if t.token_type == token_type])
                        for token_type in TokenType
                    }
                },
                'cache': {
                    'validation_cache_size': len(self.validation_cache),
                    'hit_ratio': (
                        self.metrics['validation_cache_hits'] / 
                        (self.metrics['validation_cache_hits'] + self.metrics['validation_cache_misses'])
                        if (self.metrics['validation_cache_hits'] + self.metrics['validation_cache_misses']) > 0
                        else 0
                    )
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                'service': 'JWTService',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _initialize_signing_keys(self) -> None:
        """Initialize JWT signing keys"""
        if self.jwt_config.algorithm.value.startswith('HS'):
            # HMAC - use secret key
            if not self.secret_key:
                self.secret_key = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode()
        else:
            # Asymmetric - generate key pair
            await self.rotate_signing_key()
    
    async def _start_background_workers(self) -> None:
        """Start background worker tasks"""
        # Token cleanup worker
        async def token_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(3600)  # Check every hour
                    await self._cleanup_expired_tokens()
                except Exception as e:
                    self.logger.error(f"Token cleanup worker error: {str(e)}")
                    await asyncio.sleep(300)
        
        # Cache cleanup worker
        async def cache_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(1800)  # Check every 30 minutes
                    await self._cleanup_validation_cache()
                except Exception as e:
                    self.logger.error(f"Cache cleanup worker error: {str(e)}")
                    await asyncio.sleep(300)
        
        self.background_tasks['token_cleanup'] = asyncio.create_task(token_cleanup_worker())
        self.background_tasks['cache_cleanup'] = asyncio.create_task(cache_cleanup_worker())
    
    def _get_default_ttl(self, token_type: TokenType) -> timedelta:
        """Get default TTL for token type"""
        ttl_map = {
            TokenType.ACCESS_TOKEN: self.jwt_config.access_token_ttl,
            TokenType.REFRESH_TOKEN: self.jwt_config.refresh_token_ttl,
            TokenType.ID_TOKEN: self.jwt_config.id_token_ttl,
            TokenType.API_KEY: self.jwt_config.api_key_ttl,
            TokenType.SESSION_TOKEN: self.jwt_config.session_token_ttl
        }
        return ttl_map.get(token_type, self.jwt_config.access_token_ttl)
    
    async def _encode_token(self, claims: JWTClaims) -> str:
        """Encode JWT token"""
        payload = {
            'sub': claims.sub,
            'iss': claims.iss,
            'iat': int(claims.iat.timestamp()) if claims.iat else None,
            'exp': int(claims.exp.timestamp()) if claims.exp else None,
            'nbf': int(claims.nbf.timestamp()) if claims.nbf else None,
            'jti': claims.jti,
            'token_type': claims.token_type.value if claims.token_type else None,
            'roles': list(claims.roles),
            'permissions': list(claims.permissions),
            'tenant_id': claims.tenant_id,
            'session_id': claims.session_id,
            'scope': claims.scope
        }
        
        # Add audience if configured
        if claims.aud:
            payload['aud'] = claims.aud
        
        # Add custom claims
        payload.update(claims.custom_claims)
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # Get signing key
        if self.jwt_config.algorithm.value.startswith('HS'):
            key = self.secret_key
        else:
            if not self.current_key_id or self.current_key_id not in self.key_pairs:
                raise AuthenticationError("No active signing key available")
            
            key_pair = self.key_pairs[self.current_key_id]
            key = key_pair.private_key
            
            # Add key ID to header
            headers = {'kid': self.current_key_id}
        
        # Encode token
        if self.jwt_config.algorithm.value.startswith('HS'):
            token = jwt.encode(payload, key, algorithm=self.jwt_config.algorithm.value)
        else:
            token = jwt.encode(
                payload, 
                key, 
                algorithm=self.jwt_config.algorithm.value,
                headers=headers
            )
        
        # Update key usage
        if self.current_key_id and self.current_key_id in self.key_pairs:
            self.key_pairs[self.current_key_id].usage_count += 1
        
        return token
    
    async def _decode_token(self, token: str, verify_expiration: bool = True) -> JWTClaims:
        """Decode JWT token"""
        # Get header to determine key
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        
        # Get verification key
        if self.jwt_config.algorithm.value.startswith('HS'):
            key = self.secret_key
        else:
            if kid and kid in self.key_pairs:
                key = self.key_pairs[kid].public_key
            elif self.current_key_id and self.current_key_id in self.key_pairs:
                key = self.key_pairs[self.current_key_id].public_key
            else:
                raise AuthenticationError("No valid verification key found")
        
        # Decode token
        options = {
            'verify_exp': verify_expiration,
            'verify_aud': bool(self.jwt_config.audience),
            'require_exp': True,
            'require_iat': True
        }
        
        try:
            payload = jwt.decode(
                token,
                key,
                algorithms=[self.jwt_config.algorithm.value],
                audience=self.jwt_config.audience,
                issuer=self.jwt_config.issuer,
                leeway=self.jwt_config.leeway,
                options=options
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        
        # Convert to claims object
        claims = JWTClaims(
            sub=payload['sub'],
            iss=payload['iss'],
            aud=payload.get('aud'),
            iat=datetime.fromtimestamp(payload['iat']) if 'iat' in payload else None,
            exp=datetime.fromtimestamp(payload['exp']) if 'exp' in payload else None,
            nbf=datetime.fromtimestamp(payload['nbf']) if 'nbf' in payload else None,
            jti=payload.get('jti'),
            token_type=TokenType(payload['token_type']) if 'token_type' in payload else None,
            roles=set(payload.get('roles', [])),
            permissions=set(payload.get('permissions', [])),
            tenant_id=payload.get('tenant_id'),
            session_id=payload.get('session_id'),
            scope=payload.get('scope'),
            custom_claims={k: v for k, v in payload.items() if k not in [
                'sub', 'iss', 'aud', 'iat', 'exp', 'nbf', 'jti', 'token_type',
                'roles', 'permissions', 'tenant_id', 'session_id', 'scope'
            ]}
        )
        
        return claims
    
    async def _get_from_validation_cache(self, token: str) -> Optional[TokenValidationResult]:
        """Get validation result from cache"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash in self.validation_cache:
            timestamp = self.cache_timestamps.get(token_hash)
            if timestamp and datetime.utcnow() - timestamp < self.cache_ttl:
                return self.validation_cache[token_hash]
            else:
                # Remove expired entry
                del self.validation_cache[token_hash]
                if token_hash in self.cache_timestamps:
                    del self.cache_timestamps[token_hash]
        
        return None
    
    async def _cache_validation_result(self, token: str, result: TokenValidationResult) -> None:
        """Cache validation result"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.validation_cache[token_hash] = result
        self.cache_timestamps[token_hash] = datetime.utcnow()
        
        # Limit cache size
        if len(self.validation_cache) > 10000:
            # Remove oldest entries
            sorted_items = sorted(
                self.cache_timestamps.items(),
                key=lambda x: x[1]
            )
            for old_hash, _ in sorted_items[:5000]:
                if old_hash in self.validation_cache:
                    del self.validation_cache[old_hash]
                del self.cache_timestamps[old_hash]
    
    async def _clear_token_from_cache(self, token: str) -> None:
        """Clear token from validation cache"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in self.validation_cache:
            del self.validation_cache[token_hash]
        if token_hash in self.cache_timestamps:
            del self.cache_timestamps[token_hash]
    
    async def _cleanup_expired_tokens(self) -> None:
        """Clean up expired tokens"""
        now = datetime.utcnow()
        expired_tokens = []
        
        for token_id, token_info in self.active_tokens.items():
            if token_info.expires_at and token_info.expires_at <= now:
                expired_tokens.append(token_id)
        
        for token_id in expired_tokens:
            # Move to revoked set
            self.revoked_tokens.add(token_id)
            
            # Update token info
            token_info = self.active_tokens[token_id]
            token_info.status = TokenStatus.EXPIRED
            
            # Remove from active tokens
            del self.active_tokens[token_id]
            
            # Remove from user tokens
            if token_info.user_id in self.user_tokens:
                self.user_tokens[token_info.user_id] = [
                    tid for tid in self.user_tokens[token_info.user_id] if tid != token_id
                ]
        
        if expired_tokens:
            self.metrics['expired_tokens_cleaned'] += len(expired_tokens)
            self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
    
    async def _cleanup_validation_cache(self) -> None:
        """Clean up expired validation cache entries"""
        now = datetime.utcnow()
        expired_entries = []
        
        for token_hash, timestamp in self.cache_timestamps.items():
            if now - timestamp > self.cache_ttl:
                expired_entries.append(token_hash)
        
        for token_hash in expired_entries:
            if token_hash in self.validation_cache:
                del self.validation_cache[token_hash]
            del self.cache_timestamps[token_hash]
        
        if expired_entries:
            self.logger.debug(f"Cleaned up {len(expired_entries)} expired cache entries")
    
    async def cleanup(self) -> None:
        """Cleanup JWT service resources"""
        try:
            # Cancel background tasks
            for task in self.background_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Clear caches
            self.validation_cache.clear()
            self.cache_timestamps.clear()
            
            self.logger.info("JWTService cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during JWTService cleanup: {str(e)}")