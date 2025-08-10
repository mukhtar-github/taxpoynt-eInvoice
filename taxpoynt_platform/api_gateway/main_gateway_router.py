"""
Main API Gateway Router
======================
Central router that integrates version management with role-based routing.
Coordinates between API versions, role detection, and endpoint routing.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from ..core_platform.authentication.role_manager import PlatformRole
from ..core_platform.messaging.message_router import ServiceRole, MessageRouter
from .role_routing.models import HTTPRoutingContext
from .role_routing.role_detector import HTTPRoleDetector
from .role_routing.permission_guard import APIPermissionGuard
from .api_versions.version_coordinator import APIVersionCoordinator, APIVersionStatus

# Import version-specific routers
from .api_versions.v1.si_endpoints import create_si_v1_router
from .api_versions.v1.app_endpoints import create_app_v1_router
from .api_versions.v1.hybrid_endpoints import create_hybrid_v1_router

logger = logging.getLogger(__name__)


class MainGatewayRouter:
    """
    Main API Gateway Router
    ======================
    Central coordination between version management and role-based routing.
    
    **Architecture Features:**
    - **Version Management**: Automatic version detection and routing
    - **Role-Based Access**: Integration with existing role routing system
    - **Deprecation Handling**: Automatic deprecation warnings and migration guidance
    - **Rate Limiting**: Version and role-based rate limiting
    - **Health Monitoring**: Comprehensive gateway health checks
    """
    
    def __init__(self,
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter,
                 version_coordinator: APIVersionCoordinator):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.version_coordinator = version_coordinator
        
        # Create main router
        self.router = APIRouter(prefix="/api", tags=["TaxPoynt API Gateway"])
        
        # Setup version-aware routing
        self._setup_version_routing()
        
        # Setup gateway management routes
        self._setup_gateway_routes()
        
        logger.info("Main API Gateway Router initialized")
    
    def _setup_version_routing(self):
        """Setup version-aware routing for all API versions"""
        
        # Get all active versions
        active_versions = self.version_coordinator.list_active_versions()
        
        for version in active_versions:
            version_info = self.version_coordinator.get_version_info(version)
            routing_config = self.version_coordinator.get_routing_config(version)
            
            # Create version-specific router
            version_router = APIRouter(
                prefix=f"/{version}",
                tags=[f"API {version.upper()}"],
                dependencies=[Depends(self._create_version_validator(version))]
            )
            
            # Add role-specific sub-routers for this version
            self._add_role_routers(version_router, version)
            
            # Include version router in main router
            self.router.include_router(version_router)
            
            logger.info(f"Configured routing for API {version} ({version_info.status.value})")
    
    def _add_role_routers(self, version_router: APIRouter, version: str):
        """Add role-specific routers for a version"""
        
        if version == "v1":
            # System Integrator endpoints
            si_router = create_si_v1_router(
                self.role_detector,
                self.permission_guard,
                self.message_router
            )
            version_router.include_router(si_router)
            
            # Access Point Provider endpoints
            app_router = create_app_v1_router(
                self.role_detector,
                self.permission_guard,
                self.message_router
            )
            version_router.include_router(app_router)
            
            # Hybrid endpoints
            hybrid_router = create_hybrid_v1_router(
                self.role_detector,
                self.permission_guard,
                self.message_router
            )
            version_router.include_router(hybrid_router)
        
        # Future versions can be added here
        elif version == "v2":
            # Future v2 routers will be added here
            pass
    
    def _create_version_validator(self, version: str):
        """Create version-specific validation dependency"""
        async def validate_version_access(request: Request) -> HTTPRoutingContext:
            # Detect and validate version
            detected_version = self.version_coordinator.detect_version_from_request(request)
            if detected_version != version:
                logger.warning(f"Version mismatch: requested {version}, detected {detected_version}")
            
            # Get role context
            context = await self.role_detector.detect_role_context(request)
            
            # Validate version access for user role
            if not self.version_coordinator.validate_version_access(version, context.primary_role):
                version_info = self.version_coordinator.get_version_info(version)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API {version} ({version_info.status.value}) not accessible for role {context.primary_role.value}"
                )
            
            # Add version metadata to context
            context.metadata["api_version"] = version
            context.metadata["version_status"] = self.version_coordinator.get_version_info(version).status.value
            
            return context
        
        return validate_version_access
    
    def _setup_gateway_routes(self):
        """Setup gateway management and information routes"""
        
        # Gateway health and status
        self.router.add_api_route(
            "/health",
            self.gateway_health_check,
            methods=["GET"],
            summary="API Gateway health check",
            description="Check health of API Gateway and all versions",
            tags=["Gateway Management"]
        )
        
        self.router.add_api_route(
            "/status",
            self.get_gateway_status,
            methods=["GET"],
            summary="Get gateway status",
            description="Get comprehensive gateway and version status",
            tags=["Gateway Management"]
        )
        
        # Version information
        self.router.add_api_route(
            "/versions",
            self.list_api_versions,
            methods=["GET"],
            summary="List API versions",
            description="List all available API versions and their status",
            tags=["Version Management"]
        )
        
        self.router.add_api_route(
            "/versions/{version}",
            self.get_version_info,
            methods=["GET"],
            summary="Get version information",
            description="Get detailed information about a specific API version",
            tags=["Version Management"]
        )
        
        # Migration guidance
        self.router.add_api_route(
            "/migration/{from_version}/to/{to_version}",
            self.get_migration_guidance,
            methods=["GET"],
            summary="Get migration guidance",
            description="Get guidance for migrating between API versions",
            tags=["Version Management"]
        )
        
        # API documentation and discovery
        self.router.add_api_route(
            "/discovery",
            self.api_discovery,
            methods=["GET"],
            summary="API discovery",
            description="Discover available APIs based on user role",
            tags=["API Discovery"]
        )
    
    # Gateway Health and Status Handlers
    async def gateway_health_check(self):
        """API Gateway health check"""
        try:
            # Check all active versions
            version_health = {}
            overall_healthy = True
            
            for version in self.version_coordinator.list_active_versions():
                try:
                    # This would ideally check version-specific health
                    version_info = self.version_coordinator.get_version_info(version)
                    version_health[version] = {
                        "status": "healthy",
                        "version_status": version_info.status.value,
                        "is_deprecated": version_info.is_deprecated
                    }
                except Exception as e:
                    version_health[version] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    overall_healthy = False
            
            return JSONResponse(
                content={
                    "status": "healthy" if overall_healthy else "degraded",
                    "service": "api_gateway",
                    "timestamp": "2024-12-31T00:00:00Z",
                    "versions": version_health,
                    "gateway_info": {
                        "default_version": self.version_coordinator.default_version,
                        "latest_stable": self.version_coordinator.latest_stable,
                        "active_versions": len(version_health)
                    }
                },
                status_code=200 if overall_healthy else 503
            )
        except Exception as e:
            logger.error(f"Gateway health check failed: {e}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "service": "api_gateway",
                    "error": str(e)
                },
                status_code=503
            )
    
    async def get_gateway_status(self, request: Request):
        """Get comprehensive gateway status"""
        try:
            # Get role context for user-specific information
            context = await self.role_detector.detect_role_context(request)
            
            # Get version summary
            version_summary = self.version_coordinator.get_version_summary()
            
            # Filter versions by user role access
            accessible_versions = {}
            for version, info in version_summary["available_versions"].items():
                if self.version_coordinator.validate_version_access(version, context.primary_role):
                    accessible_versions[version] = info
            
            status_data = {
                "gateway_status": "operational",
                "user_context": {
                    "primary_role": context.primary_role.value,
                    "accessible_versions": list(accessible_versions.keys()),
                    "recommended_version": self.version_coordinator.latest_stable
                },
                "version_summary": {
                    "current_stable": version_summary["current_stable"],
                    "default_version": version_summary["default_version"],
                    "accessible_versions": accessible_versions
                },
                "deprecation_notices": self._get_deprecation_notices(accessible_versions)
            }
            
            return JSONResponse(content=status_data)
        except Exception as e:
            logger.error(f"Error getting gateway status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get gateway status")
    
    # Version Information Handlers
    async def list_api_versions(self, request: Request):
        """List all API versions accessible to user"""
        try:
            context = await self.role_detector.detect_role_context(request)
            version_summary = self.version_coordinator.get_version_summary()
            
            # Filter by user access
            accessible_versions = {}
            for version, info in version_summary["available_versions"].items():
                if self.version_coordinator.validate_version_access(version, context.primary_role):
                    accessible_versions[version] = {
                        **info,
                        "endpoint_prefix": f"/api/{version}",
                        "rate_limit": self.version_coordinator.get_rate_limit(version, context.primary_role.value.lower())
                    }
            
            return JSONResponse(content={
                "versions": accessible_versions,
                "recommended": version_summary["current_stable"],
                "user_role": context.primary_role.value
            })
        except Exception as e:
            logger.error(f"Error listing API versions: {e}")
            raise HTTPException(status_code=500, detail="Failed to list API versions")
    
    async def get_version_info(self, version: str, request: Request):
        """Get detailed information about specific API version"""
        try:
            context = await self.role_detector.detect_role_context(request)
            
            # Validate access
            if not self.version_coordinator.validate_version_access(version, context.primary_role):
                raise HTTPException(status_code=403, detail=f"Access denied to API {version}")
            
            version_info = self.version_coordinator.get_version_info(version)
            routing_config = self.version_coordinator.get_routing_config(version)
            
            detailed_info = {
                "version": version_info.version,
                "full_version": version_info.full_version,
                "status": version_info.status.value,
                "description": version_info.description,
                "release_date": version_info.release_date.isoformat(),
                "is_deprecated": version_info.is_deprecated,
                "endpoint_prefix": routing_config.prefix,
                "rate_limit": routing_config.rate_limits.get(context.primary_role.value.lower(), 1000),
                "supported_roles": [role.value for role in version_info.supported_roles],
                "breaking_changes": version_info.breaking_changes
            }
            
            # Add deprecation info if applicable
            if version_info.is_deprecated:
                detailed_info["deprecation_info"] = {
                    "deprecation_date": version_info.deprecation_date.isoformat() if version_info.deprecation_date else None,
                    "sunset_date": version_info.sunset_date.isoformat() if version_info.sunset_date else None,
                    "days_until_sunset": version_info.days_until_sunset
                }
            
            return JSONResponse(content=detailed_info)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting version info for {version}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get version information")
    
    async def get_migration_guidance(self, from_version: str, to_version: str, request: Request):
        """Get migration guidance between versions"""
        try:
            context = await self.role_detector.detect_role_context(request)
            
            # Validate access to both versions
            if not self.version_coordinator.validate_version_access(from_version, context.primary_role):
                raise HTTPException(status_code=403, detail=f"Access denied to API {from_version}")
            if not self.version_coordinator.validate_version_access(to_version, context.primary_role):
                raise HTTPException(status_code=403, detail=f"Access denied to API {to_version}")
            
            guidance = self.version_coordinator.get_migration_guidance(from_version, to_version)
            
            # Add role-specific guidance
            guidance["role_specific_notes"] = self._get_role_migration_notes(
                from_version, to_version, context.primary_role
            )
            
            return JSONResponse(content=guidance)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting migration guidance {from_version} -> {to_version}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get migration guidance")
    
    async def api_discovery(self, request: Request):
        """API discovery based on user role"""
        try:
            context = await self.role_detector.detect_role_context(request)
            
            # Get accessible versions
            accessible_versions = []
            for version in self.version_coordinator.list_active_versions():
                if self.version_coordinator.validate_version_access(version, context.primary_role):
                    version_info = self.version_coordinator.get_version_info(version)
                    routing_config = self.version_coordinator.get_routing_config(version)
                    
                    accessible_versions.append({
                        "version": version,
                        "status": version_info.status.value,
                        "prefix": routing_config.prefix,
                        "endpoints": self._get_role_endpoints(version, context.primary_role)
                    })
            
            discovery_info = {
                "user_role": context.primary_role.value,
                "accessible_versions": accessible_versions,
                "recommended_version": self.version_coordinator.latest_stable,
                "documentation_base_url": "/docs",  # Swagger UI base
                "role_capabilities": self._get_role_capabilities(context.primary_role)
            }
            
            return JSONResponse(content=discovery_info)
        except Exception as e:
            logger.error(f"Error in API discovery: {e}")
            raise HTTPException(status_code=500, detail="Failed to perform API discovery")
    
    def _get_deprecation_notices(self, versions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get deprecation notices for versions"""
        notices = []
        for version, info in versions.items():
            if info.get("is_deprecated"):
                version_info = self.version_coordinator.get_version_info(version)
                notice = self.version_coordinator.create_deprecation_warning(version)
                if notice:
                    notices.append(notice)
        return notices
    
    def _get_role_migration_notes(self, from_version: str, to_version: str, role: PlatformRole) -> List[str]:
        """Get role-specific migration notes"""
        role_notes = {
            PlatformRole.SYSTEM_INTEGRATOR: [
                "Update business system integration endpoints",
                "Review transaction processing changes",
                "Test financial system connections"
            ],
            PlatformRole.ACCESS_POINT_PROVIDER: [
                "Verify FIRS integration compatibility",
                "Update taxpayer management workflows",
                "Review compliance validation changes"
            ],
            PlatformRole.ADMINISTRATOR: [
                "Review all role-based changes",
                "Update access control configurations",
                "Plan staged migration for users",
                "Test hybrid endpoint functionality"
            ]
        }
        return role_notes.get(role, [])
    
    def _get_role_endpoints(self, version: str, role: PlatformRole) -> List[str]:
        """Get available endpoints for role in version"""
        role_endpoints = {
            PlatformRole.SYSTEM_INTEGRATOR: [
                f"/api/{version}/si/organizations",
                f"/api/{version}/si/erp",
                f"/api/{version}/si/crm",
                f"/api/{version}/si/pos",
                f"/api/{version}/si/financial",
                f"/api/{version}/si/transactions",
                f"/api/{version}/si/compliance"
            ],
            PlatformRole.ACCESS_POINT_PROVIDER: [
                f"/api/{version}/app/firs",
                f"/api/{version}/app/taxpayers",
                f"/api/{version}/app/invoices",
                f"/api/{version}/app/compliance",
                f"/api/{version}/app/certificates",
                f"/api/{version}/app/grants"
            ],
            PlatformRole.ADMINISTRATOR: [
                f"/api/{version}/si/*",
                f"/api/{version}/app/*",
                f"/api/{version}/hybrid/*",
                f"/api/{version}/admin/*"
            ]
        }
        return role_endpoints.get(role, [])
    
    def _get_role_capabilities(self, role: PlatformRole) -> List[str]:
        """Get capabilities description for role"""
        capabilities = {
            PlatformRole.SYSTEM_INTEGRATOR: [
                "Business system integration (ERP, CRM, POS)",
                "Financial system integration (Banking, Payments)",
                "Transaction processing and management",
                "Organization onboarding and management",
                "Compliance validation and reporting"
            ],
            PlatformRole.ACCESS_POINT_PROVIDER: [
                "Direct FIRS system integration",
                "Taxpayer onboarding and lifecycle management",
                "Invoice generation and submission to FIRS",
                "Compliance validation against regulatory standards",
                "Certificate management and security",
                "Grant tracking and performance metrics"
            ],
            PlatformRole.ADMINISTRATOR: [
                "Full platform administration",
                "All role capabilities access",
                "Cross-role hybrid functionality",
                "System configuration and monitoring",
                "User and permission management"
            ]
        }
        return capabilities.get(role, [])


def create_main_gateway_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter,
    version_coordinator: APIVersionCoordinator
) -> APIRouter:
    """Factory function to create main gateway router"""
    gateway = MainGatewayRouter(
        role_detector,
        permission_guard,
        message_router,
        version_coordinator
    )
    return gateway.router