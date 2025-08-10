"""
FIRS Communication Services - APP Services

This package provides comprehensive FIRS API communication services for the
APP (Access Point Provider) role in the TaxPoynt e-invoicing platform.

Key Components:
- FIRSAPIClient: Official FIRS API client with OAuth 2.0 and TLS 1.3
- FIRSAuthenticationHandler: Specialized OAuth 2.0 authentication for FIRS
- FIRSRequestBuilder: Type-safe request building with validation
- FIRSResponseParser: Comprehensive response parsing and interpretation
- FIRSConnectionPool: Advanced connection pooling with load balancing

Architecture:
This package focuses on secure, reliable communication with FIRS endpoints,
providing the transmission layer for Access Point Provider services.
All components are designed to be independent and work with core_platform
foundation services when available.

Security Features:
- OAuth 2.0 client credentials flow
- TLS 1.3 encrypted communication
- Request signing and validation
- Rate limiting and quota management
- Circuit breaker pattern for resilience
"""

# Core FIRS Communication Services
from .firs_api_client import (
    FIRSAPIClient,
    FIRSConfig,
    FIRSRequest,
    FIRSResponse,
    FIRSClientMetrics,
    FIRSEnvironment,
    FIRSEndpoint,
    create_firs_api_client,
    create_production_firs_client,
    create_sandbox_firs_client
)

from .authentication_handler import (
    FIRSAuthenticationHandler,
    OAuthCredentials,
    OAuthTokenResponse,
    AuthenticationState,
    OAuthGrantType,
    OAuthScope,
    AuthenticationError,
    AuthenticationResult,
    create_firs_auth_handler
)

from .request_builder import (
    FIRSRequestBuilder,
    FIRSRequestType,
    FIRSDocumentType,
    FIRSRequestMetadata,
    FIRSRequestValidation,
    FIRSValidationResult,
    create_firs_request_builder
)

from .response_parser import (
    FIRSResponseParser,
    ParsedFIRSResponse,
    FIRSResponseStatus,
    FIRSErrorCode,
    FIRSError,
    FIRSResponseMetadata,
    create_firs_response_parser
)

from .connection_pool import (
    FIRSConnectionPool,
    FIRSEndpoint as PoolEndpoint,
    ConnectionStatus,
    LoadBalancingStrategy,
    ConnectionMetrics,
    PoolConfig,
    create_firs_connection_pool
)

__all__ = [
    # FIRS API Client
    'FIRSAPIClient',
    'FIRSConfig',
    'FIRSRequest',
    'FIRSResponse',
    'FIRSClientMetrics',
    'FIRSEnvironment',
    'FIRSEndpoint',
    'create_firs_api_client',
    'create_production_firs_client',
    'create_sandbox_firs_client',
    
    # Authentication Handler
    'FIRSAuthenticationHandler',
    'OAuthCredentials',
    'OAuthTokenResponse',
    'AuthenticationState',
    'OAuthGrantType',
    'OAuthScope',
    'AuthenticationError',
    'AuthenticationResult',
    'create_firs_auth_handler',
    
    # Request Builder
    'FIRSRequestBuilder',
    'FIRSRequestType',
    'FIRSDocumentType',
    'FIRSRequestMetadata',
    'FIRSRequestValidation',
    'FIRSValidationResult',
    'create_firs_request_builder',
    
    # Response Parser
    'FIRSResponseParser',
    'ParsedFIRSResponse',
    'FIRSResponseStatus',
    'FIRSErrorCode',
    'FIRSError',
    'FIRSResponseMetadata',
    'create_firs_response_parser',
    
    # Connection Pool
    'FIRSConnectionPool',
    'PoolEndpoint',
    'ConnectionStatus',
    'LoadBalancingStrategy',
    'ConnectionMetrics',
    'PoolConfig',
    'create_firs_connection_pool'
]

# Version information
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'FIRS Communication Services for APP Role'

# Quick access factory functions for common use cases
def create_complete_firs_client(
    environment: str = "sandbox",
    client_id: str = "",
    client_secret: str = "",
    api_key: str = "",
    enable_connection_pooling: bool = True,
    strict_validation: bool = False
):
    """
    Factory function to create a complete FIRS client setup
    with all services properly configured and interconnected.
    
    Args:
        environment: FIRS environment (sandbox/production)
        client_id: OAuth 2.0 client ID
        client_secret: OAuth 2.0 client secret
        api_key: FIRS API key
        enable_connection_pooling: Enable connection pooling
        strict_validation: Enable strict request/response validation
        
    Returns:
        Tuple of (FIRSAPIClient, FIRSRequestBuilder, FIRSResponseParser, FIRSConnectionPool)
    """
    # Create authentication handler
    auth_handler = create_firs_auth_handler(environment=environment)
    
    # Create connection pool if enabled
    connection_pool = None
    if enable_connection_pooling:
        connection_pool = create_firs_connection_pool(environment=environment)
    
    # Create request builder and response parser
    request_builder = create_firs_request_builder(
        environment=environment,
        strict_validation=strict_validation
    )
    
    response_parser = create_firs_response_parser(
        environment=environment,
        strict_validation=strict_validation
    )
    
    # Create API client configuration
    config = FIRSConfig(
        environment=FIRSEnvironment.PRODUCTION if environment == "production" else FIRSEnvironment.SANDBOX,
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key
    )
    
    # Create API client
    api_client = FIRSAPIClient(config=config, auth_handler=auth_handler)
    
    return api_client, request_builder, response_parser, connection_pool


def create_production_firs_setup(
    client_id: str,
    client_secret: str,
    api_key: str,
    **kwargs
):
    """Create production FIRS client setup with enhanced security settings"""
    return create_complete_firs_client(
        environment="production",
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
        enable_connection_pooling=True,
        strict_validation=True,
        **kwargs
    )


def create_sandbox_firs_setup(
    client_id: str,
    client_secret: str,
    api_key: str,
    **kwargs
):
    """Create sandbox FIRS client setup for development and testing"""
    return create_complete_firs_client(
        environment="sandbox",
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
        enable_connection_pooling=True,
        strict_validation=False,
        **kwargs
    )


# Configuration defaults
DEFAULT_CONFIGS = {
    'sandbox': {
        'base_url': 'https://sandbox-api.firs.gov.ng',
        'auth_url': 'https://sandbox-auth.firs.gov.ng',
        'timeout': 30,
        'max_retries': 3,
        'strict_validation': False
    },
    'production': {
        'base_url': 'https://api.firs.gov.ng',
        'auth_url': 'https://auth.firs.gov.ng',
        'timeout': 60,
        'max_retries': 5,
        'strict_validation': True
    }
}

# Service capabilities
SERVICE_CAPABILITIES = {
    'authentication': [
        'OAuth 2.0 Client Credentials Flow',
        'Token Refresh and Rotation',
        'Secure Credential Storage',
        'Rate Limited Authentication'
    ],
    'communication': [
        'TLS 1.3 Encrypted Communication',
        'Request Signing and Validation',
        'Response Parsing and Interpretation',
        'Comprehensive Error Handling'
    ],
    'reliability': [
        'Connection Pooling and Load Balancing',
        'Circuit Breaker Pattern',
        'Automatic Retry with Backoff',
        'Health Monitoring and Failover'
    ],
    'monitoring': [
        'Performance Metrics Collection',
        'Request/Response Logging',
        'Health Status Monitoring',
        'Rate Limit Tracking'
    ]
}

# Service status information
SERVICE_INFO = {
    'package': 'app_services.firs_communication',
    'role': 'Access Point Provider (APP)',
    'purpose': 'Secure FIRS API communication and transmission',
    'services': [
        'FIRS API Client with OAuth 2.0',
        'Request Building and Validation',
        'Response Parsing and Interpretation',
        'Connection Pooling and Load Balancing',
        'Authentication and Security Management'
    ],
    'security_features': [
        'OAuth 2.0 with TLS 1.3',
        'Request Signing',
        'Rate Limiting',
        'Circuit Breaker Protection'
    ],
    'version': __version__
}