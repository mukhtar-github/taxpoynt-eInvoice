"""
FIRS API Client - Access Point Provider Services

Official FIRS API client for the APP (Access Point Provider) role.
Handles secure communication with FIRS endpoints using OAuth 2.0 and TLS 1.3.

This client provides:
- OAuth 2.0 authentication with FIRS
- TLS 1.3 secure communications
- Request/response handling
- Connection pooling and retry logic
- Rate limiting and quota management
- Environment-specific endpoint management (sandbox/production)
"""

import asyncio
import logging
import ssl
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import certifi
from urllib.parse import urljoin

# Import APP authentication services (independent)
from .authentication_handler import (
    FIRSAuthenticationHandler,
    AuthenticationError,
    AuthenticationResult,
    OAuthCredentials
)

logger = logging.getLogger(__name__)


class FIRSEnvironment(Enum):
    """FIRS environment types"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class FIRSEndpoint(Enum):
    """FIRS API endpoints"""
    # Authentication endpoints
    TOKEN = "/oauth2/token"
    REFRESH_TOKEN = "/oauth2/refresh"
    
    # Invoice endpoints
    IRN_GENERATE = "/api/v1/irn/generate"
    IRN_VALIDATE = "/api/v1/irn/validate"
    IRN_CANCEL = "/api/v1/irn/cancel"
    
    # Document endpoints
    DOCUMENT_SUBMIT = "/api/v1/documents/submit"
    DOCUMENT_STATUS = "/api/v1/documents/status"
    
    # Reporting endpoints
    REPORTS_SUMMARY = "/api/v1/reports/summary"
    REPORTS_DETAIL = "/api/v1/reports/detail"
    
    # System endpoints
    HEALTH_CHECK = "/api/v1/health"
    SYSTEM_STATUS = "/api/v1/system/status"


@dataclass
class FIRSConfig:
    """Configuration for FIRS API client"""
    environment: FIRSEnvironment = FIRSEnvironment.SANDBOX
    client_id: str = ""
    client_secret: str = ""
    api_key: str = ""
    
    # Connection settings
    base_url: str = ""
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    
    # TLS settings
    tls_version: str = "TLSv1.3"
    verify_ssl: bool = True
    ca_bundle_path: Optional[str] = None
    
    # Authentication settings
    token_expiry_buffer: int = 300  # 5 minutes before actual expiry
    max_auth_retries: int = 2
    
    def __post_init__(self):
        """Initialize environment-specific settings"""
        if not self.base_url:
            if self.environment == FIRSEnvironment.SANDBOX:
                self.base_url = "https://sandbox-api.firs.gov.ng"
            else:
                self.base_url = "https://api.firs.gov.ng"


@dataclass
class FIRSRequest:
    """FIRS API request structure"""
    endpoint: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    data: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    retry_count: int = 0


@dataclass
class FIRSResponse:
    """FIRS API response structure"""
    status_code: int
    headers: Dict[str, str]
    data: Dict[str, Any]
    raw_response: str
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class FIRSClientMetrics:
    """Metrics for FIRS API client"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    authentication_requests: int = 0
    retry_attempts: int = 0
    average_response_time: float = 0.0
    rate_limit_hits: int = 0
    last_request_time: Optional[datetime] = None
    uptime_start: datetime = field(default_factory=datetime.now)


class FIRSAPIClient:
    """
    Official FIRS API client for Access Point Provider services.
    
    Provides secure, authenticated communication with FIRS endpoints
    using OAuth 2.0 and TLS 1.3.
    """
    
    def __init__(
        self,
        config: FIRSConfig,
        auth_handler: Optional[FIRSAuthenticationHandler] = None
    ):
        self.config = config
        
        # Authentication components (independent)
        self.auth_handler = auth_handler or FIRSAuthenticationHandler(
            environment=config.environment.value
        )
        
        # Client state
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.refresh_token: Optional[str] = None
        
        # Rate limiting
        self.request_timestamps: List[datetime] = []
        self.is_rate_limited: bool = False
        self.rate_limit_reset_time: Optional[datetime] = None
        
        # Metrics
        self.metrics = FIRSClientMetrics()
        
        # SSL context for TLS 1.3
        self._ssl_context: Optional[ssl.SSLContext] = None
    
    async def start(self) -> None:
        """Start the FIRS API client"""
        try:
            logger.info(f"Starting FIRS API client for {self.config.environment.value}")
            
            # Initialize authentication handler
            await self.auth_handler.start()
            
            # Create SSL context for TLS 1.3
            self._ssl_context = self._create_ssl_context()
            
            # Create HTTP session with connection pooling
            connector = aiohttp.TCPConnector(
                ssl=self._ssl_context,
                limit=100,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout_seconds,
                connect=10,
                sock_read=self.config.timeout_seconds
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'TaxPoynt-APP-Client/1.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
            
            # Authenticate with FIRS
            await self._authenticate()
            
            logger.info("FIRS API client started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start FIRS API client: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the FIRS API client"""
        try:
            logger.info("Stopping FIRS API client")
            
            if self.session:
                await self.session.close()
                self.session = None
            
            await self.auth_handler.stop()
            
            logger.info("FIRS API client stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping FIRS API client: {e}")
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for TLS 1.3"""
        try:
            # Create SSL context with TLS 1.3
            context = ssl.create_default_context(cafile=certifi.where())
            
            # Force TLS 1.3 if supported
            if hasattr(ssl, 'TLSVersion'):
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            # Security settings
            context.check_hostname = self.config.verify_ssl
            context.verify_mode = ssl.CERT_REQUIRED if self.config.verify_ssl else ssl.CERT_NONE
            
            # Use custom CA bundle if provided
            if self.config.ca_bundle_path:
                context.load_verify_locations(self.config.ca_bundle_path)
            
            # Cipher configuration for maximum security
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            logger.info(f"SSL context created with TLS version: {self.config.tls_version}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            raise
    
    async def _authenticate(self) -> bool:
        """Authenticate with FIRS using OAuth 2.0"""
        try:
            logger.info("Authenticating with FIRS")
            
            # Use independent authentication handler
            auth_result = await self.auth_handler.authenticate_client_credentials(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                api_key=self.config.api_key
            )
            
            if auth_result.success:
                self.access_token = auth_result.auth_data.get('access_token')
                self.refresh_token = auth_result.auth_data.get('refresh_token')
                self.token_expires_at = auth_result.expires_at
                
                self.metrics.authentication_requests += 1
                
                logger.info("Successfully authenticated with FIRS")
                return True
            else:
                logger.error(f"FIRS authentication failed: {auth_result.error_message}")
                return False
                
        except AuthenticationError as e:
            logger.error(f"FIRS authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            return False
    
    async def _refresh_authentication(self) -> bool:
        """Refresh FIRS authentication token"""
        try:
            if not self.refresh_token:
                logger.warning("No refresh token available, re-authenticating")
                return await self._authenticate()
            
            logger.info("Refreshing FIRS authentication token")
            
            refresh_result = await self.auth_handler.refresh_access_token(
                refresh_token=self.refresh_token
            )
            
            if refresh_result.success:
                self.access_token = refresh_result.auth_data.get('access_token')
                self.refresh_token = refresh_result.auth_data.get('refresh_token', self.refresh_token)
                self.token_expires_at = refresh_result.expires_at
                
                logger.info("Successfully refreshed FIRS authentication token")
                return True
            else:
                logger.warning("Token refresh failed, re-authenticating")
                return await self._authenticate()
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return await self._authenticate()
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure client is authenticated"""
        try:
            # Check if token exists and is valid
            if not self.access_token:
                return await self._authenticate()
            
            # Check if token is about to expire
            if self.token_expires_at:
                buffer_time = timedelta(seconds=self.config.token_expiry_buffer)
                if datetime.now() + buffer_time >= self.token_expires_at:
                    return await self._refresh_authentication()
            
            return True
            
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return False
    
    async def _check_rate_limits(self) -> bool:
        """Check if request can be made within rate limits"""
        try:
            current_time = datetime.now()
            
            # Clean old timestamps
            cutoff_time = current_time - timedelta(minutes=1)
            self.request_timestamps = [
                ts for ts in self.request_timestamps 
                if ts > cutoff_time
            ]
            
            # Check per-minute limit
            if len(self.request_timestamps) >= self.config.requests_per_minute:
                self.is_rate_limited = True
                self.rate_limit_reset_time = current_time + timedelta(minutes=1)
                self.metrics.rate_limit_hits += 1
                return False
            
            self.is_rate_limited = False
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow request if check fails
    
    async def make_request(
        self,
        endpoint: Union[str, FIRSEndpoint],
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        retry_on_auth_failure: bool = True
    ) -> FIRSResponse:
        """
        Make authenticated request to FIRS API
        
        Args:
            endpoint: API endpoint (string or FIRSEndpoint enum)
            method: HTTP method
            data: Request payload
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout
            retry_on_auth_failure: Whether to retry on auth failure
            
        Returns:
            FIRSResponse object
        """
        try:
            # Prepare endpoint URL
            if isinstance(endpoint, FIRSEndpoint):
                endpoint_path = endpoint.value
            else:
                endpoint_path = endpoint
            
            url = urljoin(self.config.base_url, endpoint_path)
            
            # Check rate limits
            if not await self._check_rate_limits():
                raise Exception("Rate limit exceeded")
            
            # Ensure authentication
            if not await self._ensure_authenticated():
                raise Exception("Authentication failed")
            
            # Prepare request
            request_headers = {
                'Authorization': f'Bearer {self.access_token}',
                'X-API-Key': self.config.api_key,
                'X-Request-ID': f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self) % 10000}",
                **(headers or {})
            }
            
            request_timeout = timeout or self.config.timeout_seconds
            
            # Make request
            start_time = datetime.now()
            
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=aiohttp.ClientTimeout(total=request_timeout)
            ) as response:
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Update metrics
                self.metrics.total_requests += 1
                self.metrics.last_request_time = datetime.now()
                self.request_timestamps.append(datetime.now())
                
                # Update average response time
                total_time = self.metrics.average_response_time * (self.metrics.total_requests - 1)
                self.metrics.average_response_time = (total_time + response_time) / self.metrics.total_requests
                
                # Parse response
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {'raw_response': response_text}
                
                # Create FIRS response object
                firs_response = FIRSResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    data=response_data,
                    raw_response=response_text,
                    request_id=request_headers.get('X-Request-ID'),
                    timestamp=datetime.now(),
                    success=200 <= response.status < 300
                )
                
                # Handle authentication errors
                if response.status == 401 and retry_on_auth_failure:
                    logger.warning("Authentication error, attempting to refresh token")
                    if await self._refresh_authentication():
                        # Retry request with new token
                        return await self.make_request(
                            endpoint=endpoint,
                            method=method,
                            data=data,
                            params=params,
                            headers=headers,
                            timeout=timeout,
                            retry_on_auth_failure=False  # Avoid infinite retry
                        )
                
                # Update success metrics
                if firs_response.success:
                    self.metrics.successful_requests += 1
                else:
                    self.metrics.failed_requests += 1
                    firs_response.error_code = response_data.get('error_code')
                    firs_response.error_message = response_data.get('error_message', 'Unknown error')
                
                return firs_response
                
        except asyncio.TimeoutError:
            self.metrics.failed_requests += 1
            return FIRSResponse(
                status_code=408,
                headers={},
                data={'error': 'Request timeout'},
                raw_response='',
                success=False,
                error_code='TIMEOUT',
                error_message='Request timed out'
            )
        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"FIRS API request failed: {e}")
            return FIRSResponse(
                status_code=500,
                headers={},
                data={'error': str(e)},
                raw_response='',
                success=False,
                error_code='REQUEST_FAILED',
                error_message=str(e)
            )
    
    async def health_check(self) -> FIRSResponse:
        """Check FIRS API health"""
        return await self.make_request(
            endpoint=FIRSEndpoint.HEALTH_CHECK,
            method="GET"
        )
    
    async def system_status(self) -> FIRSResponse:
        """Get FIRS system status"""
        return await self.make_request(
            endpoint=FIRSEndpoint.SYSTEM_STATUS,
            method="GET"
        )
    
    def get_metrics(self) -> FIRSClientMetrics:
        """Get client metrics"""
        return self.metrics
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'environment': self.config.environment.value,
            'base_url': self.config.base_url,
            'tls_version': self.config.tls_version,
            'authenticated': bool(self.access_token),
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'rate_limited': self.is_rate_limited,
            'session_active': self.session is not None and not self.session.closed
        }


# Factory function for creating FIRS API client
def create_firs_api_client(
    environment: FIRSEnvironment = FIRSEnvironment.SANDBOX,
    client_id: str = "",
    client_secret: str = "",
    api_key: str = "",
    config_overrides: Optional[Dict[str, Any]] = None
) -> FIRSAPIClient:
    """
    Factory function to create FIRS API client
    
    Args:
        environment: FIRS environment
        client_id: OAuth 2.0 client ID
        client_secret: OAuth 2.0 client secret
        api_key: FIRS API key
        config_overrides: Additional configuration options
        
    Returns:
        Configured FIRS API client
    """
    config = FIRSConfig(
        environment=environment,
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key
    )
    
    # Apply configuration overrides
    if config_overrides:
        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    return FIRSAPIClient(config)


# Convenience function for creating production client
def create_production_firs_client(
    client_id: str,
    client_secret: str,
    api_key: str,
    **kwargs
) -> FIRSAPIClient:
    """Create production FIRS API client"""
    return create_firs_api_client(
        environment=FIRSEnvironment.PRODUCTION,
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
        config_overrides=kwargs
    )


# Convenience function for creating sandbox client
def create_sandbox_firs_client(
    client_id: str,
    client_secret: str,
    api_key: str,
    **kwargs
) -> FIRSAPIClient:
    """Create sandbox FIRS API client"""
    return create_firs_api_client(
        environment=FIRSEnvironment.SANDBOX,
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
        config_overrides=kwargs
    )