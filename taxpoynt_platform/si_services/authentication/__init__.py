"""
SI Services - Authentication Package

This package provides comprehensive authentication services for the System Integrator (SI)
role in the TaxPoynt e-invoicing platform. It handles authentication for ERP systems,
FIRS APIs, certificate-based authentication, and secure credential management.

Key Components:
- AuthenticationManager: Central authentication coordinator
- ERPAuthProvider: ERP-specific authentication (Odoo, SAP, QuickBooks)
- CertificateAuthProvider: Certificate-based authentication for FIRS
- FIRSAuthService: FIRS API authentication service
- TokenManager: OAuth2/JWT token management
- SecureCredentialStore: Encrypted credential storage
- AuthenticationMiddleware: Request authentication middleware
- MultiTenantAuth: Multi-tenant authentication support
- AuthValidators: Authentication validation utilities

Architecture:
The authentication package provides a layered approach to authentication:
1. Central Manager: Coordinates all authentication providers
2. Specialized Providers: Handle specific authentication types
3. Token Management: Manages token lifecycle and validation
4. Secure Storage: Encrypts and stores sensitive credentials
5. Middleware: Integrates authentication into request processing
6. Multi-tenancy: Supports tenant isolation and management
"""

# Core Authentication Components
from .auth_manager import (
    AuthenticationManager,
    BaseAuthProvider,
    AuthenticationContext,
    AuthenticationCredentials,
    AuthenticationResult,
    AuthenticationConfig,
    AuthenticationType,
    AuthenticationStatus,
    AuthenticationScope,
    ServiceType,
    create_auth_manager
)

# ERP Authentication
from .erp_auth_provider import (
    BaseERPAuthProvider,
    OdooAuthProvider,
    SAPAuthProvider,
    QuickBooksAuthProvider,
    ERPAuthProviderFactory,
    ERPSystemType,
    ERPConnectionConfig,
    ERPSessionData,
    create_erp_auth_provider
)

# Certificate Authentication
from .certificate_auth import (
    CertificateAuthProvider,
    CertificateValidator,
    CertificateInfo,
    CertificateBundle,
    CertificateConfig,
    CertificateType,
    CertificateFormat,
    CertificateStatus,
    create_certificate_auth_provider
)

# FIRS Authentication
from .firs_auth_service import (
    FIRSAuthService,
    FIRSSession,
    FIRSAuthConfig,
    FIRSEndpointConfig,
    FIRSEnvironment,
    FIRSAuthMethod,
    FIRSServiceType,
    FIRSAPIVersion,
    create_firs_auth_service
)

# Token Management
from .token_manager import (
    TokenManager,
    TokenInfo,
    TokenConfig,
    TokenRequest,
    TokenResponse,
    TokenType,
    TokenStatus,
    GrantType,
    TokenAlgorithm,
    create_token_manager
)

# Secure Credential Storage
from .credential_store import (
    SecureCredentialStore,
    StoredCredential,
    CredentialMetadata,
    CredentialStoreConfig,
    CredentialType,
    CredentialStatus,
    EncryptionAlgorithm,
    create_credential_store
)

__all__ = [
    # Core Authentication
    'AuthenticationManager',
    'BaseAuthProvider',
    'AuthenticationContext',
    'AuthenticationCredentials',
    'AuthenticationResult',
    'AuthenticationConfig',
    'AuthenticationType',
    'AuthenticationStatus',
    'AuthenticationScope',
    'ServiceType',
    'create_auth_manager',
    
    # ERP Authentication
    'BaseERPAuthProvider',
    'OdooAuthProvider',
    'SAPAuthProvider',
    'QuickBooksAuthProvider',
    'ERPAuthProviderFactory',
    'ERPSystemType',
    'ERPConnectionConfig',
    'ERPSessionData',
    'create_erp_auth_provider',
    
    # Certificate Authentication
    'CertificateAuthProvider',
    'CertificateValidator',
    'CertificateInfo',
    'CertificateBundle',
    'CertificateConfig',
    'CertificateType',
    'CertificateFormat',
    'CertificateStatus',
    'create_certificate_auth_provider',
    
    # FIRS Authentication
    'FIRSAuthService',
    'FIRSSession',
    'FIRSAuthConfig',
    'FIRSEndpointConfig',
    'FIRSEnvironment',
    'FIRSAuthMethod',
    'FIRSServiceType',
    'FIRSAPIVersion',
    'create_firs_auth_service',
    
    # Token Management
    'TokenManager',
    'TokenInfo',
    'TokenConfig',
    'TokenRequest',
    'TokenResponse',
    'TokenType',
    'TokenStatus',
    'GrantType',
    'TokenAlgorithm',
    'create_token_manager',
    
    # Credential Storage
    'SecureCredentialStore',
    'StoredCredential',
    'CredentialMetadata',
    'CredentialStoreConfig',
    'CredentialType',
    'CredentialStatus',
    'EncryptionAlgorithm',
    'create_credential_store',
]

# Version information
__version__ = '1.0.0'
__author__ = 'TaxPoynt Development Team'
__description__ = 'Authentication Services for SI Role'

# Quick access factory functions for complete authentication setup
async def create_complete_auth_system(
    auth_config=None,
    token_config=None,
    credential_config=None,
    erp_systems=None
):
    """
    Factory function to create a complete authentication system
    with all services properly configured and interconnected.
    
    Args:
        auth_config: AuthenticationConfig for main auth manager
        token_config: TokenConfig for token management
        credential_config: CredentialStoreConfig for credential storage
        erp_systems: List of ERPSystemType to support
    
    Returns:
        Tuple of (AuthenticationManager, TokenManager, SecureCredentialStore)
    """
    from .auth_manager import AuthenticationConfig
    from .token_manager import TokenConfig
    from .credential_store import CredentialStoreConfig
    
    # Create services with default configs if not provided
    auth_manager = create_auth_manager(auth_config or AuthenticationConfig())
    token_manager = create_token_manager(token_config or TokenConfig())
    credential_store = create_credential_store(
        credential_config or CredentialStoreConfig(storage_path="./credentials")
    )
    
    # Initialize services
    await auth_manager.start_auth_manager()
    await token_manager.initialize()
    await credential_store.initialize()
    
    # Register ERP providers if specified
    if erp_systems:
        for erp_system in erp_systems:
            provider = create_erp_auth_provider(erp_system)
            if provider:
                await provider.initialize()
                await auth_manager.register_auth_provider(
                    provider,
                    [ServiceType.ERP_SYSTEM]
                )
    
    # Register FIRS auth service
    firs_service = create_firs_auth_service()
    await firs_service.initialize()
    await auth_manager.register_auth_provider(
        firs_service,
        [ServiceType.FIRS_API]
    )
    
    return auth_manager, token_manager, credential_store

def get_supported_auth_types():
    """Get list of supported authentication types"""
    return list(AuthenticationType)

def get_supported_erp_systems():
    """Get list of supported ERP systems"""
    return list(ERPSystemType)

def get_supported_firs_environments():
    """Get list of supported FIRS environments"""
    return list(FIRSEnvironment)

# Configuration defaults
DEFAULT_CONFIGS = {
    'auth_manager': AuthenticationConfig(),
    'token_manager': TokenConfig(),
    'credential_store': CredentialStoreConfig(storage_path="./credentials"),
}

# Service capability matrix
SERVICE_CAPABILITIES = {
    'erp_authentication': {
        'odoo': ['basic', 'api_key', 'session'],
        'sap': ['oauth2', 'basic'],
        'quickbooks': ['oauth2'],
        'sage': ['api_key'],
        'dynamics': ['oauth2'],
        'oracle': ['basic']
    },
    'firs_authentication': {
        'sandbox': ['api_key', 'oauth2', 'certificate'],
        'production': ['api_key', 'oauth2', 'certificate']
    },
    'token_management': {
        'supported_types': ['jwt', 'oauth2', 'api_key', 'bearer'],
        'algorithms': ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
    },
    'credential_storage': {
        'encryption': ['fernet', 'aes_256_gcm'],
        'features': ['backup', 'rotation', 'audit_log', 'secure_delete']
    }
}

# Integration patterns
INTEGRATION_PATTERNS = {
    'erp_to_firs': {
        'description': 'Authenticate to ERP system, extract data, authenticate to FIRS, submit data',
        'flow': ['erp_auth', 'data_extraction', 'firs_auth', 'data_submission'],
        'required_services': ['erp_auth_provider', 'firs_auth_service', 'token_manager']
    },
    'certificate_based': {
        'description': 'Use client certificates for secure FIRS communication',
        'flow': ['cert_validation', 'cert_auth', 'secure_communication'],
        'required_services': ['certificate_auth', 'credential_store']
    },
    'multi_tenant': {
        'description': 'Support multiple tenants with isolated authentication',
        'flow': ['tenant_identification', 'tenant_auth', 'tenant_isolation'],
        'required_services': ['auth_manager', 'credential_store', 'token_manager']
    }
}

# Service status information
SERVICE_INFO = {
    'package': 'si_services.authentication',
    'role': 'System Integrator (SI)',
    'purpose': 'Comprehensive authentication for SI workflows',
    'services': [
        'Central Authentication Management',
        'ERP System Authentication', 
        'FIRS API Authentication',
        'Certificate-based Authentication',
        'Token Management (OAuth2/JWT)',
        'Secure Credential Storage',
        'Authentication Middleware',
        'Multi-tenant Support'
    ],
    'version': __version__,
    'capabilities': SERVICE_CAPABILITIES,
    'integration_patterns': INTEGRATION_PATTERNS
}