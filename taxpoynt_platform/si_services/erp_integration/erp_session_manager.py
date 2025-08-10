"""
ERP Session Manager Service

This module manages ERP sessions for SI services, handling authentication,
connection pooling, session lifecycle, and secure credential management
for sustained integration operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import base64
from pathlib import Path
import aiohttp
import ssl
from contextlib import asynccontextmanager

# Import authentication services
from taxpoynt_platform.si_services.authentication import (
    AuthenticationManager,
    ERPAuthProvider,
    TokenManager,
    CredentialStore,
    AuthenticationError,
    AuthenticationResult,
    AuthMethod,
    ERPSystem
)

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Status of ERP sessions"""
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    ACTIVE = "active"
    EXPIRED = "expired"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class AuthenticationType(Enum):
    """Types of authentication methods"""
    BASIC = "basic"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    CUSTOM = "custom"


class ERPType(Enum):
    """Supported ERP system types"""
    ODOO = "odoo"
    SAP = "sap"
    QUICKBOOKS = "quickbooks"
    SAGE = "sage"
    DYNAMICS = "dynamics"
    ORACLE = "oracle"
    CUSTOM = "custom"


@dataclass
class ConnectionConfig:
    """Configuration for ERP connection"""
    erp_type: ERPType
    host: str
    port: int
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_redirect_uri: Optional[str] = None
    ssl_enabled: bool = True
    ssl_verify: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    custom_headers: Dict[str, str] = field(default_factory=dict)
    authentication_type: AuthenticationType = AuthenticationType.BASIC
    connection_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionInfo:
    """Information about an ERP session"""
    session_id: str
    erp_type: ERPType
    host: str
    status: SessionStatus
    created_at: datetime
    last_activity: datetime
    expires_at: Optional[datetime] = None
    user_context: Dict[str, Any] = field(default_factory=dict)
    connection_metadata: Dict[str, Any] = field(default_factory=dict)
    usage_stats: Dict[str, int] = field(default_factory=dict)
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class SessionPool:
    """Pool of ERP sessions"""
    pool_id: str
    erp_type: ERPType
    max_sessions: int
    active_sessions: Dict[str, SessionInfo] = field(default_factory=dict)
    available_sessions: Set[str] = field(default_factory=set)
    config: Optional[ConnectionConfig] = None
    created_at: datetime = field(default_factory=datetime.now)
    total_created: int = 0
    total_destroyed: int = 0


@dataclass
class SessionMetrics:
    """Metrics for session management"""
    total_sessions: int = 0
    active_sessions: int = 0
    failed_sessions: int = 0
    expired_sessions: int = 0
    average_session_duration: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    peak_concurrent_sessions: int = 0


@dataclass
class SessionManagerConfig:
    """Configuration for session manager"""
    max_sessions_per_erp: int = 10
    session_timeout_minutes: int = 60
    idle_timeout_minutes: int = 30
    cleanup_interval_minutes: int = 15
    enable_session_pooling: bool = True
    enable_auto_reconnect: bool = True
    max_reconnect_attempts: int = 3
    session_validation_interval: int = 300  # seconds
    enable_session_encryption: bool = True
    credentials_storage_path: Optional[str] = None
    enable_connection_health_check: bool = True
    health_check_interval: int = 60  # seconds


class ERPSessionManager:
    """
    Service for managing ERP sessions with connection pooling,
    authentication, and lifecycle management for SI operations.
    
    Enhanced with integrated authentication services for secure
    ERP connections and credential management.
    """
    
    def __init__(self, config: SessionManagerConfig, auth_manager: Optional[AuthenticationManager] = None):
        self.config = config
        self.session_pools: Dict[ERPType, SessionPool] = {}
        self.session_registry: Dict[str, SessionInfo] = {}
        self.connection_configs: Dict[ERPType, ConnectionConfig] = {}
        self.metrics = SessionMetrics()
        
        # Session management state
        self.is_running = False
        self.cleanup_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
        # HTTP session for API connections
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Authentication services integration
        self.auth_manager = auth_manager or AuthenticationManager()
        self.erp_auth_provider = ERPAuthProvider()
        self.token_manager = TokenManager()
        self.credential_store = CredentialStore()
        
        # Setup credentials storage
        if config.credentials_storage_path:
            self.credentials_path = Path(config.credentials_storage_path)
            self.credentials_path.mkdir(parents=True, exist_ok=True)
        else:
            self.credentials_path = None
    
    async def start_session_manager(self) -> None:
        """Start the session manager with authentication services"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting ERP Session Manager with Authentication Services")
        
        # Initialize authentication services
        await self.auth_manager.start()
        await self.credential_store.initialize()
        await self.token_manager.start()
        
        # Initialize HTTP session
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=20,
            ssl=ssl.create_default_context() if self.config.enable_session_encryption else False
        )
        
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Start background tasks
        self.cleanup_task = asyncio.create_task(self._session_cleanup_loop())
        
        if self.config.enable_connection_health_check:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Load saved configurations
        await self._load_connection_configs()
    
    async def stop_session_manager(self) -> None:
        """Stop the session manager and authentication services"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping ERP Session Manager and Authentication Services")
        
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Close all sessions
        await self._close_all_sessions()
        
        # Close HTTP session
        if self.http_session:
            await self.http_session.close()
        
        # Stop authentication services
        await self.auth_manager.stop()
        await self.token_manager.stop()
        await self.credential_store.cleanup()
        
        # Wait for tasks to complete
        await asyncio.gather(
            *[t for t in [self.cleanup_task, self.health_check_task] if t],
            return_exceptions=True
        )
    
    async def register_erp_connection(
        self,
        erp_type: ERPType,
        config: ConnectionConfig
    ) -> bool:
        """Register an ERP connection configuration"""
        try:
            # Validate connection config
            if not await self._validate_connection_config(config):
                return False
            
            # Store configuration
            self.connection_configs[erp_type] = config
            
            # Create session pool if pooling is enabled
            if self.config.enable_session_pooling:
                pool = SessionPool(
                    pool_id=f"pool_{erp_type.value}",
                    erp_type=erp_type,
                    max_sessions=self.config.max_sessions_per_erp,
                    config=config
                )
                self.session_pools[erp_type] = pool
            
            # Save configuration
            await self._save_connection_config(erp_type, config)
            
            logger.info(f"Registered ERP connection for {erp_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register ERP connection for {erp_type.value}: {e}")
            return False
    
    async def create_session(
        self,
        erp_type: ERPType,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a new ERP session"""
        try:
            # Check if ERP is registered
            if erp_type not in self.connection_configs:
                logger.error(f"ERP type {erp_type.value} not registered")
                return None
            
            config = self.connection_configs[erp_type]
            
            # Try to get session from pool first
            if self.config.enable_session_pooling and erp_type in self.session_pools:
                session_id = await self._get_pooled_session(erp_type, user_context)
                if session_id:
                    return session_id
            
            # Create new session
            session_id = await self._create_new_session(erp_type, config, user_context)
            
            if session_id:
                self.metrics.total_sessions += 1
                self.metrics.active_sessions += 1
                
                # Update peak concurrent sessions
                if self.metrics.active_sessions > self.metrics.peak_concurrent_sessions:
                    self.metrics.peak_concurrent_sessions = self.metrics.active_sessions
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session for {erp_type.value}: {e}")
            self.metrics.failed_sessions += 1
            return None
    
    async def _get_pooled_session(
        self,
        erp_type: ERPType,
        user_context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Get an available session from the pool"""
        try:
            pool = self.session_pools[erp_type]
            
            if pool.available_sessions:
                session_id = pool.available_sessions.pop()
                session = pool.active_sessions[session_id]
                
                # Update session context
                session.user_context = user_context or {}
                session.last_activity = datetime.now()
                session.status = SessionStatus.ACTIVE
                
                logger.debug(f"Reused pooled session {session_id} for {erp_type.value}")
                return session_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get pooled session for {erp_type.value}: {e}")
            return None
    
    async def _create_new_session(
        self,
        erp_type: ERPType,
        config: ConnectionConfig,
        user_context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Create a new ERP session"""
        try:
            session_id = self._generate_session_id(erp_type)
            
            # Create session info
            session = SessionInfo(
                session_id=session_id,
                erp_type=erp_type,
                host=config.host,
                status=SessionStatus.CONNECTING,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                user_context=user_context or {},
                usage_stats={"requests": 0, "bytes_transferred": 0}
            )
            
            # Authenticate with ERP system
            auth_success = await self._authenticate_session(session, config)
            
            if auth_success:
                session.status = SessionStatus.ACTIVE
                session.expires_at = datetime.now() + timedelta(
                    minutes=self.config.session_timeout_minutes
                )
                
                # Register session
                self.session_registry[session_id] = session
                
                # Add to pool if pooling is enabled
                if self.config.enable_session_pooling and erp_type in self.session_pools:
                    pool = self.session_pools[erp_type]
                    pool.active_sessions[session_id] = session
                    pool.total_created += 1
                
                logger.info(f"Created new session {session_id} for {erp_type.value}")
                return session_id
            else:
                session.status = SessionStatus.FAILED
                logger.error(f"Authentication failed for {erp_type.value}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create new session for {erp_type.value}: {e}")
            return None
    
    async def _authenticate_session(
        self,
        session: SessionInfo,
        config: ConnectionConfig
    ) -> bool:
        """Authenticate session with ERP system using authentication services"""
        try:
            # Map ERPType to ERPSystem for authentication
            erp_system_map = {
                ERPType.ODOO: ERPSystem.ODOO,
                ERPType.SAP: ERPSystem.SAP,
                ERPType.QUICKBOOKS: ERPSystem.QUICKBOOKS,
                ERPType.SAGE: ERPSystem.SAGE,
                ERPType.DYNAMICS: ERPSystem.DYNAMICS,
                ERPType.ORACLE: ERPSystem.ORACLE,
            }
            
            erp_system = erp_system_map.get(session.erp_type, ERPSystem.CUSTOM)
            
            # Map AuthenticationType to AuthMethod
            auth_method_map = {
                AuthenticationType.BASIC: AuthMethod.BASIC,
                AuthenticationType.OAUTH2: AuthMethod.OAUTH2,
                AuthenticationType.API_KEY: AuthMethod.API_KEY,
                AuthenticationType.TOKEN: AuthMethod.TOKEN,
                AuthenticationType.CERTIFICATE: AuthMethod.CERTIFICATE,
            }
            
            auth_method = auth_method_map.get(config.authentication_type, AuthMethod.BASIC)
            
            # Prepare credentials
            credentials = {
                "host": config.host,
                "port": config.port,
                "database": config.database,
            }
            
            if config.authentication_type == AuthenticationType.BASIC:
                credentials.update({
                    "username": config.username,
                    "password": config.password
                })
            elif config.authentication_type == AuthenticationType.OAUTH2:
                credentials.update({
                    "client_id": config.oauth_client_id,
                    "client_secret": config.oauth_client_secret,
                    "redirect_uri": config.oauth_redirect_uri
                })
            elif config.authentication_type == AuthenticationType.API_KEY:
                credentials["api_key"] = config.api_key
            
            # Authenticate using ERP authentication provider
            auth_result = await self.erp_auth_provider.authenticate(
                erp_system=erp_system,
                auth_method=auth_method,
                credentials=credentials,
                context={"session_id": session.session_id}
            )
            
            if auth_result.success:
                # Store authentication data in session
                session.connection_metadata.update(auth_result.auth_data)
                
                # Set session expiration based on token expiry if available
                if auth_result.expires_at:
                    session.expires_at = auth_result.expires_at
                
                logger.info(f"Successfully authenticated session {session.session_id} for {erp_system.value}")
                return True
            else:
                session.last_error = auth_result.error_message or "Authentication failed"
                logger.error(f"Authentication failed for session {session.session_id}: {session.last_error}")
                return False
                
        except AuthenticationError as e:
            logger.error(f"Authentication error for session {session.session_id}: {e}")
            session.last_error = str(e)
            return False
        except Exception as e:
            logger.error(f"Unexpected authentication error for session {session.session_id}: {e}")
            session.last_error = str(e)
            return False
    
    async def refresh_session_authentication(self, session_id: str) -> bool:
        """Refresh authentication for a session using token manager"""
        try:
            session = self.session_registry.get(session_id)
            if not session:
                return False
            
            # Get current auth data
            auth_data = session.connection_metadata
            
            # Try to refresh using token manager
            if "access_token" in auth_data:
                refresh_result = await self.token_manager.refresh_token(
                    token=auth_data.get("access_token"),
                    refresh_token=auth_data.get("refresh_token"),
                    context={"session_id": session_id}
                )
                
                if refresh_result.success:
                    # Update session with new tokens
                    session.connection_metadata.update(refresh_result.token_data)
                    if refresh_result.expires_at:
                        session.expires_at = refresh_result.expires_at
                    
                    logger.info(f"Successfully refreshed authentication for session {session_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to refresh session authentication: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information"""
        session = self.session_registry.get(session_id)
        
        if session:
            # Check if session is still valid
            if await self._is_session_valid(session):
                session.last_activity = datetime.now()
                return session
            else:
                # Invalid session, remove it
                await self._destroy_session(session_id)
                return None
        
        return None
    
    async def _is_session_valid(self, session: SessionInfo) -> bool:
        """Check if session is still valid"""
        try:
            # Check status
            if session.status != SessionStatus.ACTIVE:
                return False
            
            # Check expiration
            if session.expires_at and datetime.now() > session.expires_at:
                session.status = SessionStatus.EXPIRED
                return False
            
            # Check idle timeout
            idle_time = datetime.now() - session.last_activity
            if idle_time.total_seconds() > (self.config.idle_timeout_minutes * 60):
                session.status = SessionStatus.EXPIRED
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed for {session.session_id}: {e}")
            return False
    
    @asynccontextmanager
    async def get_session_context(self, erp_type: ERPType, user_context: Optional[Dict[str, Any]] = None):
        """Context manager for ERP sessions"""
        session_id = None
        try:
            session_id = await self.create_session(erp_type, user_context)
            if not session_id:
                raise Exception(f"Failed to create session for {erp_type.value}")
            
            session = await self.get_session(session_id)
            yield session
            
        finally:
            if session_id and not self.config.enable_session_pooling:
                await self._destroy_session(session_id)
            elif session_id and self.config.enable_session_pooling:
                await self._return_session_to_pool(session_id)
    
    async def _return_session_to_pool(self, session_id: str) -> None:
        """Return session to pool for reuse"""
        try:
            session = self.session_registry.get(session_id)
            if not session:
                return
            
            pool = self.session_pools.get(session.erp_type)
            if not pool:
                await self._destroy_session(session_id)
                return
            
            # Clean up session context
            session.user_context = {}
            session.last_activity = datetime.now()
            session.status = SessionStatus.ACTIVE
            
            # Add to available sessions
            pool.available_sessions.add(session_id)
            
            logger.debug(f"Returned session {session_id} to pool")
            
        except Exception as e:
            logger.error(f"Failed to return session to pool: {e}")
            await self._destroy_session(session_id)
    
    async def _destroy_session(self, session_id: str) -> None:
        """Destroy a session"""
        try:
            session = self.session_registry.get(session_id)
            if not session:
                return
            
            # Remove from registry
            del self.session_registry[session_id]
            
            # Remove from pool
            if session.erp_type in self.session_pools:
                pool = self.session_pools[session.erp_type]
                if session_id in pool.active_sessions:
                    del pool.active_sessions[session_id]
                pool.available_sessions.discard(session_id)
                pool.total_destroyed += 1
            
            # Update metrics
            self.metrics.active_sessions = max(0, self.metrics.active_sessions - 1)
            
            logger.debug(f"Destroyed session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to destroy session {session_id}: {e}")
    
    async def _close_all_sessions(self) -> None:
        """Close all active sessions"""
        try:
            session_ids = list(self.session_registry.keys())
            
            for session_id in session_ids:
                await self._destroy_session(session_id)
            
            self.session_pools.clear()
            self.session_registry.clear()
            
            logger.info("Closed all sessions")
            
        except Exception as e:
            logger.error(f"Failed to close all sessions: {e}")
    
    async def _session_cleanup_loop(self) -> None:
        """Background task for session cleanup"""
        while self.is_running:
            try:
                await self._cleanup_expired_sessions()
                await asyncio.sleep(self.config.cleanup_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.session_registry.items():
                # Check expiration
                if session.expires_at and current_time > session.expires_at:
                    expired_sessions.append(session_id)
                    continue
                
                # Check idle timeout
                idle_time = current_time - session.last_activity
                if idle_time.total_seconds() > (self.config.idle_timeout_minutes * 60):
                    expired_sessions.append(session_id)
            
            # Clean up expired sessions
            for session_id in expired_sessions:
                await self._destroy_session(session_id)
                self.metrics.expired_sessions += 1
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background task for connection health checks"""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on active sessions"""
        try:
            for session_id, session in list(self.session_registry.items()):
                if session.status == SessionStatus.ACTIVE:
                    is_healthy = await self._check_session_health(session)
                    
                    if not is_healthy:
                        session.error_count += 1
                        
                        if session.error_count >= 3:
                            session.status = SessionStatus.FAILED
                            await self._destroy_session(session_id)
                    else:
                        session.error_count = 0
                        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _check_session_health(self, session: SessionInfo) -> bool:
        """Check health of a specific session"""
        try:
            config = self.connection_configs.get(session.erp_type)
            if not config:
                return False
            
            # Simple connectivity test
            url = f"{'https' if config.ssl_enabled else 'http'}://{config.host}:{config.port}"
            
            headers = self._get_session_headers(session)
            
            async with self.http_session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return response.status < 500
                
        except Exception as e:
            logger.debug(f"Health check failed for session {session.session_id}: {e}")
            return False
    
    def _get_session_headers(self, session: SessionInfo) -> Dict[str, str]:
        """Get headers for session requests"""
        headers = {}
        
        metadata = session.connection_metadata
        
        if "access_token" in metadata:
            token_type = metadata.get("token_type", "Bearer")
            headers["Authorization"] = f"{token_type} {metadata['access_token']}"
        
        elif "api_key" in metadata:
            headers["X-API-Key"] = metadata["api_key"]
        
        elif "token" in metadata:
            headers["Authorization"] = f"Token {metadata['token']}"
        
        return headers
    
    def _generate_session_id(self, erp_type: ERPType) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_part = hashlib.md5(f"{erp_type.value}_{timestamp}".encode()).hexdigest()[:8]
        return f"session_{erp_type.value}_{timestamp}_{random_part}"
    
    async def _validate_connection_config(self, config: ConnectionConfig) -> bool:
        """Validate connection configuration"""
        try:
            if not config.host:
                return False
            
            if config.port <= 0 or config.port > 65535:
                return False
            
            if config.authentication_type == AuthenticationType.BASIC:
                return bool(config.username and config.password)
            
            elif config.authentication_type == AuthenticationType.OAUTH2:
                return bool(config.oauth_client_id and config.oauth_client_secret)
            
            elif config.authentication_type == AuthenticationType.API_KEY:
                return bool(config.api_key)
            
            return True
            
        except Exception:
            return False
    
    async def _save_connection_config(self, erp_type: ERPType, config: ConnectionConfig) -> None:
        """Save connection configuration using secure credential store"""
        try:
            # Prepare safe configuration (non-sensitive data)
            safe_config = {
                "erp_type": erp_type.value,
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "authentication_type": config.authentication_type.value,
                "ssl_enabled": config.ssl_enabled,
                "timeout_seconds": config.timeout_seconds,
                "custom_headers": config.custom_headers,
                "connection_params": {k: v for k, v in config.connection_params.items() if "password" not in k.lower()}
            }
            
            # Prepare sensitive credentials for secure storage
            sensitive_credentials = {}
            if config.username and config.password:
                sensitive_credentials.update({
                    "username": config.username,
                    "password": config.password
                })
            if config.api_key:
                sensitive_credentials["api_key"] = config.api_key
            if config.oauth_client_id and config.oauth_client_secret:
                sensitive_credentials.update({
                    "oauth_client_id": config.oauth_client_id,
                    "oauth_client_secret": config.oauth_client_secret,
                    "oauth_redirect_uri": config.oauth_redirect_uri
                })
            
            # Store sensitive credentials securely
            if sensitive_credentials:
                credential_id = f"erp_{erp_type.value}_credentials"
                await self.credential_store.store_credentials(
                    credential_id=credential_id,
                    credentials=sensitive_credentials,
                    metadata={"erp_type": erp_type.value, "host": config.host}
                )
            
            # Save safe configuration to file
            if self.credentials_path:
                config_file = self.credentials_path / f"{erp_type.value}_config.json"
                with open(config_file, 'w') as f:
                    json.dump(safe_config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save connection config: {e}")
    
    async def _load_connection_configs(self) -> None:
        """Load saved connection configurations"""
        if not self.credentials_path:
            return
        
        try:
            for config_file in self.credentials_path.glob("*_config.json"):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                erp_type = ERPType(config_data["erp_type"])
                
                # Note: Sensitive data would need to be loaded from secure storage
                # This is a simplified implementation
                logger.info(f"Loaded configuration for {erp_type.value}")
                
        except Exception as e:
            logger.error(f"Failed to load connection configs: {e}")
    
    def get_session_metrics(self) -> SessionMetrics:
        """Get current session metrics"""
        return self.metrics
    
    def get_active_sessions(self) -> List[SessionInfo]:
        """Get list of active sessions"""
        return list(self.session_registry.values())
    
    def get_session_pools_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of session pools"""
        status = {}
        
        for erp_type, pool in self.session_pools.items():
            status[erp_type.value] = {
                "max_sessions": pool.max_sessions,
                "active_sessions": len(pool.active_sessions),
                "available_sessions": len(pool.available_sessions),
                "total_created": pool.total_created,
                "total_destroyed": pool.total_destroyed,
                "created_at": pool.created_at.isoformat()
            }
        
        return status


# Factory function for creating ERP session manager
def create_erp_session_manager(
    config: Optional[SessionManagerConfig] = None,
    auth_manager: Optional[AuthenticationManager] = None
) -> ERPSessionManager:
    """Factory function to create an ERP session manager with authentication services"""
    if config is None:
        config = SessionManagerConfig()
    
    return ERPSessionManager(config, auth_manager)


# Convenience function for creating session manager with default authentication
def create_authenticated_erp_session_manager(
    config: Optional[SessionManagerConfig] = None
) -> ERPSessionManager:
    """Create ERP session manager with pre-configured authentication services"""
    if config is None:
        config = SessionManagerConfig()
    
    # Create default authentication manager
    auth_manager = AuthenticationManager()
    
    return ERPSessionManager(config, auth_manager)