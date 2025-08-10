"""
API Gateway Role-Based Routing System
====================================
Provides HTTP-level role-aware request routing that integrates with the existing
message router and role management systems.

This module extends the existing message routing capabilities with:
- HTTP request role detection and context analysis
- FastAPI-specific role-based endpoint routing
- Integration with existing core_platform/authentication/role_manager
- Bridging HTTP requests to internal message routing system
- API endpoint protection and permission enforcement

Integration Points:
- Uses core_platform.authentication.role_manager for role validation
- Integrates with core_platform.messaging.message_router for internal routing
- Leverages existing hybrid_services for cross-role operations

Components:
- models.py: HTTP-specific routing models that extend existing role models
- role_detector.py: HTTP request analysis and role context detection
- permission_guard.py: FastAPI middleware for role-based endpoint protection  
- si_router.py: FastAPI router for SI-specific HTTP endpoints
- app_router.py: FastAPI router for APP-specific HTTP endpoints
- hybrid_router.py: FastAPI router for cross-role HTTP endpoints
"""

# Import from NEW architecture core components
from ...core_platform.authentication.role_manager import PlatformRole, RoleScope
from ...core_platform.messaging.message_router import ServiceRole, MessageRouter

from .models import (
    HTTPRoutingContext, APIEndpointRule, RoleBasedRoute,
    RequestAnalysis, RoutePermission
)
from .role_detector import HTTPRoleDetector
from .permission_guard import APIPermissionGuard
from .si_router import SIAPIRouter
from .app_router import APPAPIRouter  
from .hybrid_router import HybridAPIRouter

__all__ = [
    # Existing integrations
    'PlatformRole',
    'RoleScope', 
    'ServiceRole',
    'MessageRouter',
    
    # New HTTP-specific components
    'HTTPRoutingContext',
    'APIEndpointRule',
    'RoleBasedRoute',
    'RequestAnalysis',
    'RoutePermission',
    'HTTPRoleDetector',
    'APIPermissionGuard',
    'SIAPIRouter',
    'APPAPIRouter',
    'HybridAPIRouter'
]