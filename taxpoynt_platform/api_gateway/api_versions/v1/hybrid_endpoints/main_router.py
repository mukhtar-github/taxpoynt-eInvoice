"""
Hybrid Main Router - API Version 1
==================================
Main router for Hybrid endpoints in API v1.
Consolidates all cross-role and shared functionality.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from .....core_platform.authentication.role_manager import PlatformRole, RoleScope
from .....core_platform.messaging.message_router import ServiceRole, MessageRouter
from ....role_routing.models import HTTPRoutingContext
from ....role_routing.role_detector import HTTPRoleDetector
from ....role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel, V1ErrorModel

# Import hybrid system routers
from .cross_role_endpoints import create_cross_role_router
from .shared_resources_endpoints import create_shared_resources_router
from .orchestration_endpoints import create_orchestration_router
from .monitoring_endpoints import create_monitoring_router

logger = logging.getLogger(__name__)


class HybridRouterV1:
    """
    Hybrid Router - Version 1
    =========================
    Handles all Hybrid endpoints for API v1, including:
    - Cross-role operations requiring multiple role capabilities
    - Shared resources accessible by multiple roles
    - Workflow orchestration across role boundaries
    - Cross-system monitoring and observability
    
    **Hybrid Role Context:**
    - Serves functionality spanning multiple roles
    - Enables collaboration between SI and APP operations
    - Provides shared utilities and common resources
    - Facilitates complex multi-role business processes
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/hybrid", tags=["Hybrid Operations V1"])
        
        # Include all hybrid sub-routers
        self._include_sub_routers()
        
        # Setup general hybrid routes
        self._setup_routes()
        
        logger.info("Hybrid Router V1 initialized")
    
    def _include_sub_routers(self):
        """Include all hybrid sub-routers"""
        
        # Cross-Role Operations Routes
        cross_role_router = create_cross_role_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(cross_role_router)
        
        # Shared Resources Routes
        shared_router = create_shared_resources_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(shared_router)
        
        # Orchestration Routes
        orchestration_router = create_orchestration_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(orchestration_router)
        
        # Monitoring Routes
        monitoring_router = create_monitoring_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(monitoring_router)
    
    def _setup_routes(self):
        """Configure general hybrid v1 routes"""
        
        # Hybrid Health and Status Routes
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="Hybrid services health check",
            description="Check health of all hybrid services and cross-role operations",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/status",
            self.get_hybrid_status,
            methods=["GET"],
            summary="Get hybrid status overview",
            description="Get comprehensive status of hybrid operations and integrations",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_role)]
        )
        
        # Hybrid Information Routes
        self.router.add_api_route(
            "/info",
            self.get_hybrid_info,
            methods=["GET"],
            summary="Get hybrid information",
            description="Get hybrid services information and capabilities",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/capabilities",
            self.get_hybrid_capabilities,
            methods=["GET"],
            summary="Get hybrid capabilities",
            description="Get detailed hybrid capabilities and supported cross-role features",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_role)]
        )
        
        # Role Coordination Routes
        self.router.add_api_route(
            "/coordination/check-access",
            self.check_coordination_access,
            methods=["POST"],
            summary="Check coordination access",
            description="Check if user has access to coordinate between specific roles",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_role)]
        )
        
        self.router.add_api_route(
            "/coordination/available-operations",
            self.get_available_operations,
            methods=["GET"],
            summary="Get available coordination operations",
            description="Get coordination operations available to the current user",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_role)]
        )
    
    async def _require_hybrid_role(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure hybrid access for v1"""
        context = await self.role_detector.detect_role_context(request)
        
        # Allow access for SI, APP, or Admin roles
        allowed_roles = {
            PlatformRole.SYSTEM_INTEGRATOR,
            PlatformRole.ACCESS_POINT_PROVIDER,
            PlatformRole.ADMINISTRATOR
        }
        
        if not any(context.has_role(role) for role in allowed_roles):
            logger.warning(f"Hybrid v1 endpoint access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hybrid access requires System Integrator, Access Point Provider, or Administrator role"
            )
        
        # Apply v1-specific permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/hybrid{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for hybrid v1 endpoint"
            )
        
        # Add v1-specific context
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "hybrid"
        
        return context
    
    # Hybrid Health and Status Handlers
    async def health_check(self):
        """Hybrid services health check for v1"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.HYBRID_COORDINATOR,
                operation="health_check",
                payload={"api_version": "v1"}
            )
            
            return JSONResponse(content={
                "status": "healthy",
                "service": "hybrid_services",
                "api_version": "v1",
                "timestamp": result.get("timestamp"),
                "version_specific": {
                    "supported_features": [
                        "cross_role_operations",
                        "shared_resources",
                        "workflow_orchestration",
                        "cross_system_monitoring"
                    ],
                    "v1_compatibility": "full",
                    "coordination_status": "operational"
                }
            })
        except Exception as e:
            logger.error(f"Hybrid v1 health check failed: {e}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "api_version": "v1",
                    "error": str(e)
                },
                status_code=503
            )
    
    async def get_hybrid_status(self, context: HTTPRoutingContext = Depends(_require_hybrid_role)):
        """Get hybrid status overview"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.HYBRID_COORDINATOR,
                operation="get_hybrid_status",
                payload={
                    "user_context": {
                        "user_id": context.user_id,
                        "roles": [role.value for role in context.roles]
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "hybrid_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting hybrid status in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get hybrid status")
    
    # Hybrid Information Handlers
    async def get_hybrid_info(self):
        """Get hybrid information"""
        try:
            hybrid_info = {
                "service_name": "TaxPoynt Hybrid Services",
                "service_version": "v1.0.0",
                "api_version": "v1",
                "description": "Cross-role operations and shared services for TaxPoynt platform",
                "capabilities": [
                    "cross_role_operations",
                    "shared_resources",
                    "workflow_orchestration",
                    "monitoring_and_observability"
                ],
                "supported_workflows": [
                    "end_to_end_invoice_processing",
                    "taxpayer_integration_workflows",
                    "compliance_coordination",
                    "data_synchronization"
                ],
                "role_requirements": {
                    "basic_access": ["system_integrator", "access_point_provider", "administrator"],
                    "cross_role_operations": ["system_integrator", "access_point_provider"],
                    "orchestration": ["administrator", "both_si_and_app"]
                }
            }
            
            return self._create_v1_response(hybrid_info, "hybrid_info_retrieved")
        except Exception as e:
            logger.error(f"Error getting hybrid info in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get hybrid info")
    
    async def get_hybrid_capabilities(self, context: HTTPRoutingContext = Depends(_require_hybrid_role)):
        """Get hybrid capabilities"""
        try:
            user_roles = [role.value for role in context.roles]
            
            # Determine capabilities based on user roles
            base_capabilities = {
                "shared_resources": {
                    "description": "Access to shared configuration, reference data, and templates",
                    "accessible": True
                },
                "monitoring": {
                    "description": "Cross-role monitoring and observability",
                    "accessible": True
                }
            }
            
            # Advanced capabilities require specific role combinations
            advanced_capabilities = {}
            
            if (context.has_role(PlatformRole.SYSTEM_INTEGRATOR) and 
                context.has_role(PlatformRole.ACCESS_POINT_PROVIDER)) or \
               context.has_role(PlatformRole.ADMINISTRATOR):
                advanced_capabilities.update({
                    "cross_role_operations": {
                        "description": "End-to-end processing spanning SI and APP roles",
                        "accessible": True
                    },
                    "orchestration": {
                        "description": "Complex workflow orchestration across roles",
                        "accessible": True
                    }
                })
            
            capabilities = {
                **base_capabilities,
                **advanced_capabilities,
                "user_roles": user_roles,
                "total_accessible": len(base_capabilities) + len(advanced_capabilities)
            }
            
            return self._create_v1_response(capabilities, "hybrid_capabilities_retrieved")
        except Exception as e:
            logger.error(f"Error getting hybrid capabilities in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get hybrid capabilities")
    
    # Role Coordination Handlers
    async def check_coordination_access(self, request: Request, context: HTTPRoutingContext = Depends(_require_hybrid_role)):
        """Check coordination access"""
        try:
            body = await request.json()
            required_roles = body.get("required_roles", [])
            
            # Check if user has access to coordinate the specified roles
            has_coordination_access = (
                context.has_role(PlatformRole.ADMINISTRATOR) or
                all(context.has_role(PlatformRole(role)) for role in required_roles)
            )
            
            result = {
                "has_access": has_coordination_access,
                "required_roles": required_roles,
                "user_roles": [role.value for role in context.roles],
                "coordination_level": "full" if has_coordination_access else "limited"
            }
            
            return self._create_v1_response(result, "coordination_access_checked")
        except Exception as e:
            logger.error(f"Error checking coordination access in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to check coordination access")
    
    async def get_available_operations(self, context: HTTPRoutingContext = Depends(_require_hybrid_role)):
        """Get available coordination operations"""
        try:
            available_operations = []
            
            # Basic operations available to all hybrid users
            available_operations.extend([
                "access_shared_resources",
                "view_monitoring_data",
                "check_system_health"
            ])
            
            # Cross-role operations
            if (context.has_role(PlatformRole.SYSTEM_INTEGRATOR) and 
                context.has_role(PlatformRole.ACCESS_POINT_PROVIDER)) or \
               context.has_role(PlatformRole.ADMINISTRATOR):
                available_operations.extend([
                    "initiate_end_to_end_processing",
                    "coordinate_compliance_validation",
                    "sync_organizations_with_taxpayers",
                    "execute_workflow_orchestration"
                ])
            
            # Admin-only operations
            if context.has_role(PlatformRole.ADMINISTRATOR):
                available_operations.extend([
                    "manage_system_configuration",
                    "access_all_monitoring_data",
                    "coordinate_all_role_operations"
                ])
            
            result = {
                "available_operations": available_operations,
                "total_operations": len(available_operations),
                "user_roles": [role.value for role in context.roles],
                "access_level": "administrator" if context.has_role(PlatformRole.ADMINISTRATOR) else "standard"
            }
            
            return self._create_v1_response(result, "available_operations_retrieved")
        except Exception as e:
            logger.error(f"Error getting available operations in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get available operations")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> JSONResponse:
        """Create standardized v1 response format"""
        response_data = {
            "success": True,
            "action": action,
            "api_version": "v1",
            "timestamp": "2024-12-31T00:00:00Z",
            "data": data
        }
        
        return JSONResponse(content=response_data, status_code=status_code)


def create_hybrid_v1_router(role_detector: HTTPRoleDetector,
                           permission_guard: APIPermissionGuard,
                           message_router: MessageRouter) -> APIRouter:
    """Factory function to create Hybrid V1 Router"""
    hybrid_v1_router = HybridRouterV1(role_detector, permission_guard, message_router)
    return hybrid_v1_router.router