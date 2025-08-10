"""
Authentication & Authorization Core Platform Package

This package provides comprehensive authentication and authorization services for the TaxPoynt platform,
including role management, permission engine, OAuth coordination, JWT services, and session management.

Components:
- RoleManager: Manages SI/APP role assignments and role hierarchies
- PermissionEngine: Implements role-based permission system with fine-grained access control
- OAuthCoordinator: Coordinates OAuth authentication with external systems
- JWTService: Manages JWT token creation, validation, and lifecycle
- SessionManager: Manages user session lifecycle with security features
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError
)

from .role_manager import RoleManager, PlatformRole, RoleScope, RoleAssignment
from .permission_engine import PermissionEngine, PermissionContext, PermissionEvaluation, AccessLevel
from .oauth_coordinator import OAuthCoordinator, OAuthProvider, OAuthFlow, TokenType as OAuthTokenType
from .jwt_service import JWTService, TokenType as JWTTokenType, Algorithm, JWTClaims
from .session_manager import SessionManager, SessionType, SessionStatus, DeviceType, SecurityLevel


__all__ = [
    'RoleManager',
    'PermissionEngine', 
    'OAuthCoordinator',
    'JWTService',
    'SessionManager',
    'AuthenticationService',
    'PlatformRole',
    'RoleScope',
    'AccessLevel',
    'OAuthProvider',
    'OAuthFlow',
    'JWTTokenType',
    'SessionType',
    'SecurityLevel'
]


class AuthenticationService(BaseService):
    """
    Unified Authentication Service
    
    Orchestrates all authentication and authorization components to provide a unified
    interface for authentication across the TaxPoynt platform.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Component services
        self.role_manager: Optional[RoleManager] = None
        self.permission_engine: Optional[PermissionEngine] = None
        self.oauth_coordinator: Optional[OAuthCoordinator] = None
        self.jwt_service: Optional[JWTService] = None
        self.session_manager: Optional[SessionManager] = None
        
        # Service registry
        self.services: Dict[str, BaseService] = {}
        
        # Authentication state
        self.is_initialized = False
        
        # Metrics aggregation
        self.metrics = {
            'total_authentications': 0,
            'total_authorizations': 0,
            'failed_authentications': 0,
            'active_sessions': 0,
            'active_tokens': 0,
            'role_assignments': 0,
            'permission_evaluations': 0,
            'oauth_flows': 0,
            'initialization_time': None,
            'last_health_check': None
        }
    
    async def initialize(self) -> None:
        """Initialize all authentication services"""
        try:
            start_time = datetime.utcnow()
            self.logger.info("Initializing AuthenticationService")
            
            # Initialize role manager
            self.role_manager = RoleManager(self.config)
            await self.role_manager.initialize()
            self.services['role_manager'] = self.role_manager
            
            # Initialize permission engine
            self.permission_engine = PermissionEngine(self.config)
            await self.permission_engine.initialize()
            self.services['permission_engine'] = self.permission_engine
            
            # Initialize OAuth coordinator
            self.oauth_coordinator = OAuthCoordinator(self.config)
            await self.oauth_coordinator.initialize()
            self.services['oauth_coordinator'] = self.oauth_coordinator
            
            # Initialize JWT service
            self.jwt_service = JWTService(self.config)
            await self.jwt_service.initialize()
            self.services['jwt_service'] = self.jwt_service
            
            # Initialize session manager
            self.session_manager = SessionManager(self.config)
            await self.session_manager.initialize()
            self.services['session_manager'] = self.session_manager
            
            # Set up inter-service integration
            await self._setup_service_integration()
            
            # Mark as initialized
            self.is_initialized = True
            end_time = datetime.utcnow()
            self.metrics['initialization_time'] = (end_time - start_time).total_seconds()
            
            self.logger.info("AuthenticationService initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AuthenticationService: {str(e)}")
            raise AuthenticationError(f"Initialization failed: {str(e)}")
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        session_type: SessionType = SessionType.WEB,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        mfa_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user and create session
        
        This is the main entry point for user authentication across the platform.
        """
        try:
            if not self.is_initialized:
                raise AuthenticationError("Authentication service not initialized")
            
            # Step 1: Validate credentials (placeholder - integrate with user service)
            user_info = await self._validate_credentials(username, password)
            if not user_info:
                self.metrics['failed_authentications'] += 1
                raise AuthenticationError("Invalid credentials")
            
            user_id = user_info['user_id']
            tenant_id = user_info.get('tenant_id')
            
            # Step 2: Get user roles
            user_context = await self.role_manager.get_user_context(user_id)
            roles = {assignment.role_id for assignment in user_context.active_roles}
            
            # Step 3: Get user permissions
            permissions = await self.permission_engine.get_user_permissions(
                user_id, roles, tenant_id
            )
            
            # Step 4: Create session
            session = await self.session_manager.create_session(
                user_id=user_id,
                session_type=session_type,
                ip_address=ip_address,
                user_agent=user_agent,
                tenant_id=tenant_id,
                roles=roles,
                permissions=permissions
            )
            
            # Step 5: Handle MFA if required
            mfa_required = 'mfa_required' in session.flags
            if mfa_required and mfa_token:
                mfa_verified = await self.session_manager.verify_mfa(session.session_id, mfa_token)
                if not mfa_verified:
                    await self.session_manager.terminate_session(session.session_id, "mfa_failed")
                    raise AuthenticationError("MFA verification failed")
            
            # Step 6: Create JWT tokens
            access_token = await self.jwt_service.create_token(
                user_id=user_id,
                token_type=JWTTokenType.ACCESS_TOKEN,
                roles=roles,
                permissions=permissions,
                tenant_id=tenant_id,
                session_id=session.session_id
            )
            
            refresh_token = await self.jwt_service.create_token(
                user_id=user_id,
                token_type=JWTTokenType.REFRESH_TOKEN,
                tenant_id=tenant_id,
                session_id=session.session_id
            )
            
            self.metrics['total_authentications'] += 1
            
            return {
                'success': True,
                'user_id': user_id,
                'session_id': session.session_id,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': session.expires_at.isoformat(),
                'roles': list(roles),
                'permissions': list(permissions),
                'mfa_required': mfa_required and not session.mfa_verified,
                'session_info': {
                    'session_type': session.session_type.value,
                    'security_level': session.security_level.value,
                    'risk_score': session.risk_score
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate user {username}: {str(e)}")
            self.metrics['failed_authentications'] += 1
            return {
                'success': False,
                'error': str(e)
            }
    
    async def authorize_action(
        self,
        token: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        required_roles: Optional[Set[str]] = None,
        required_permissions: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Authorize user action based on token
        
        This is the main entry point for authorization checks across the platform.
        """
        try:
            if not self.is_initialized:
                raise AuthorizationError("Authentication service not initialized")
            
            # Step 1: Validate JWT token
            validation_result = await self.jwt_service.validate_token(
                token, 
                expected_type=JWTTokenType.ACCESS_TOKEN,
                required_permissions=required_permissions,
                required_roles=required_roles
            )
            
            if not validation_result.valid or not validation_result.claims:
                self.metrics['failed_authentications'] += 1
                return {
                    'authorized': False,
                    'error': validation_result.error or "Invalid token"
                }
            
            claims = validation_result.claims
            
            # Step 2: Validate session
            if claims.session_id:
                session = await self.session_manager.get_session(claims.session_id)
                if not session:
                    return {
                        'authorized': False,
                        'error': "Session not found or expired"
                    }
                
                # Update session activity
                await self.session_manager.update_session_activity(
                    claims.session_id, f"action_{action}"
                )
            
            # Step 3: Check specific action permission
            if action and resource_type:
                from .permission_engine import ResourceType
                resource_enum = None
                try:
                    resource_enum = ResourceType(resource_type)
                except ValueError:
                    pass
                
                has_permission = await self.permission_engine.check_action_permission(
                    user_id=claims.sub,
                    action=action,
                    resource_type=resource_enum,
                    resource_id=resource_id,
                    roles=claims.roles,
                    tenant_id=claims.tenant_id
                )
                
                if not has_permission:
                    return {
                        'authorized': False,
                        'error': f"Insufficient permissions for action: {action}"
                    }
            
            self.metrics['total_authorizations'] += 1
            
            return {
                'authorized': True,
                'user_id': claims.sub,
                'tenant_id': claims.tenant_id,
                'roles': list(claims.roles),
                'permissions': list(claims.permissions),
                'session_id': claims.session_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to authorize action {action}: {str(e)}")
            return {
                'authorized': False,
                'error': str(e)
            }
    
    async def logout_user(
        self,
        token: Optional[str] = None,
        session_id: Optional[str] = None,
        logout_all_sessions: bool = False
    ) -> Dict[str, Any]:
        """Logout user and cleanup tokens/sessions"""
        try:
            user_id = None
            target_session_id = session_id
            
            # Extract user and session info from token if needed
            if token and not target_session_id:
                validation_result = await self.jwt_service.validate_token(token)
                if validation_result.valid and validation_result.claims:
                    user_id = validation_result.claims.sub
                    target_session_id = validation_result.claims.session_id
            
            # Revoke JWT token
            if token:
                await self.jwt_service.revoke_token(token=token)
            
            # Terminate session(s)
            if target_session_id:
                if logout_all_sessions and user_id:
                    terminated_count = await self.session_manager.terminate_user_sessions(
                        user_id, reason="user_logout_all"
                    )
                    return {
                        'success': True,
                        'message': f"Logged out from {terminated_count} sessions"
                    }
                else:
                    success = await self.session_manager.terminate_session(
                        target_session_id, reason="user_logout"
                    )
                    return {
                        'success': success,
                        'message': "Logged out successfully" if success else "Session not found"
                    }
            
            return {
                'success': True,
                'message': "Token revoked successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to logout user: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def refresh_user_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh user access token"""
        try:
            new_access_token = await self.jwt_service.refresh_token(refresh_token)
            
            if new_access_token:
                return {
                    'success': True,
                    'access_token': new_access_token
                }
            else:
                return {
                    'success': False,
                    'error': "Failed to refresh token"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to refresh token: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def assign_user_role(
        self,
        user_id: str,
        role_id: str,
        scope: RoleScope,
        assigned_by: str,
        tenant_id: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Assign role to user"""
        try:
            assignment = await self.role_manager.assign_role(
                user_id=user_id,
                role_id=role_id,
                scope=scope,
                assigned_by=assigned_by,
                tenant_id=tenant_id,
                expires_at=expires_at
            )
            
            self.metrics['role_assignments'] += 1
            
            return {
                'success': True,
                'assignment_id': assignment.assignment_id,
                'message': f"Role {role_id} assigned to user {user_id}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to assign role {role_id} to user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_unified_health_status(self) -> Dict[str, Any]:
        """Get unified health status of all authentication services"""
        try:
            health_status = {
                'service': 'AuthenticationService',
                'status': 'healthy' if self.is_initialized else 'initializing',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'components': {}
            }
            
            # Get health status from each component
            for service_name, service in self.services.items():
                try:
                    component_health = await service.get_health_status()
                    health_status['components'][service_name] = component_health
                except Exception as e:
                    health_status['components'][service_name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Determine overall health
            component_statuses = [
                comp.get('status', 'unknown') 
                for comp in health_status['components'].values()
            ]
            
            if any(status == 'unhealthy' for status in component_statuses):
                health_status['status'] = 'degraded'
            elif any(status != 'healthy' for status in component_statuses):
                health_status['status'] = 'warning'
            
            self.metrics['last_health_check'] = datetime.utcnow().isoformat()
            return health_status
            
        except Exception as e:
            self.logger.error(f"Failed to get unified health status: {str(e)}")
            return {
                'service': 'AuthenticationService',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _setup_service_integration(self) -> None:
        """Setup integration between authentication services"""
        try:
            # Set up role-permission integration
            if self.role_manager and self.permission_engine:
                # When roles change, update permissions
                pass  # Implementation would depend on specific requirements
            
            # Set up session-JWT integration
            if self.session_manager and self.jwt_service:
                # When sessions are terminated, revoke associated tokens
                pass  # Implementation would depend on specific requirements
            
            self.logger.info("Service integration setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup service integration: {str(e)}")
    
    async def _validate_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate user credentials (placeholder implementation)"""
        # This would integrate with your actual user service/database
        # For demo purposes, we'll simulate credential validation
        
        # Simulate database lookup
        mock_users = {
            'admin@taxpoynt.com': {
                'user_id': 'user_admin',
                'password_hash': 'hashed_password',  # In reality, this would be properly hashed
                'tenant_id': 'tenant_platform',
                'active': True
            },
            'si_user@company.com': {
                'user_id': 'user_si_001',
                'password_hash': 'hashed_password',
                'tenant_id': 'tenant_company_001',
                'active': True
            }
        }
        
        user_data = mock_users.get(username)
        if user_data and user_data['active']:
            # In reality, you'd hash the password and compare
            if password == 'password':  # Simplified for demo
                return {
                    'user_id': user_data['user_id'],
                    'tenant_id': user_data['tenant_id'],
                    'username': username
                }
        
        return None
    
    async def _update_metrics(self) -> None:
        """Update aggregated metrics"""
        try:
            # Update active sessions count
            if self.session_manager:
                session_metrics = await self.session_manager.get_session_metrics()
                self.metrics['active_sessions'] = session_metrics.active_sessions
            
            # Update role assignments count
            if self.role_manager:
                self.metrics['role_assignments'] = len(self.role_manager.assignments)
            
            # Update permission evaluations count
            if self.permission_engine:
                self.metrics['permission_evaluations'] = self.permission_engine.metrics['evaluations_performed']
                
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {str(e)}")
    
    async def cleanup(self) -> None:
        """Cleanup all authentication services"""
        try:
            self.logger.info("Starting AuthenticationService cleanup")
            
            # Cleanup all services
            cleanup_tasks = []
            for service_name, service in self.services.items():
                if hasattr(service, 'cleanup'):
                    cleanup_tasks.append(service.cleanup())
            
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            # Clear service registry
            self.services.clear()
            
            # Reset state
            self.is_initialized = False
            
            self.logger.info("AuthenticationService cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during AuthenticationService cleanup: {str(e)}")


# Convenience functions for direct service access
async def get_authentication_service(config: Optional[Dict[str, Any]] = None) -> AuthenticationService:
    """Get initialized authentication service"""
    service = AuthenticationService(config)
    await service.initialize()
    return service


async def authenticate_user(
    username: str, 
    password: str, 
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Authenticate user with automatic service management"""
    service = await get_authentication_service(config)
    try:
        return await service.authenticate_user(username, password, **kwargs)
    finally:
        await service.cleanup()


async def authorize_action(
    token: str,
    action: str,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Authorize action with automatic service management"""
    service = await get_authentication_service(config)
    try:
        return await service.authorize_action(token, action, **kwargs)
    finally:
        await service.cleanup()


# Service factory functions
def create_role_manager(config: Optional[Dict[str, Any]] = None) -> RoleManager:
    """Create and return a RoleManager instance"""
    return RoleManager(config)


def create_permission_engine(config: Optional[Dict[str, Any]] = None) -> PermissionEngine:
    """Create and return a PermissionEngine instance"""
    return PermissionEngine(config)


def create_oauth_coordinator(config: Optional[Dict[str, Any]] = None) -> OAuthCoordinator:
    """Create and return an OAuthCoordinator instance"""
    return OAuthCoordinator(config)


def create_jwt_service(config: Optional[Dict[str, Any]] = None) -> JWTService:
    """Create and return a JWTService instance"""
    return JWTService(config)


def create_session_manager(config: Optional[Dict[str, Any]] = None) -> SessionManager:
    """Create and return a SessionManager instance"""
    return SessionManager(config)


# Package-level configuration
DEFAULT_CONFIG = {
    'role_manager': {
        'cache_ttl_minutes': 15,
        'max_delegation_depth': 3,
        'enable_hierarchies': True
    },
    'permission_engine': {
        'cache_ttl_minutes': 5,
        'enable_policy_engine': True,
        'enable_resource_permissions': True
    },
    'oauth_coordinator': {
        'cache_ttl_hours': 1,
        'enable_pkce': True,
        'token_cleanup_interval_hours': 1
    },
    'jwt_service': {
        'issuer': 'taxpoynt-platform',
        'algorithm': 'RS256',
        'access_token_ttl_hours': 1,
        'refresh_token_ttl_days': 30
    },
    'session_manager': {
        'default_idle_timeout_minutes': 30,
        'default_session_timeout_hours': 8,
        'max_concurrent_sessions': 5,
        'enable_risk_assessment': True
    }
}


def get_default_config() -> Dict[str, Any]:
    """Get default configuration for authentication services"""
    return DEFAULT_CONFIG.copy()


# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Authentication and authorization services for the TaxPoynt platform"