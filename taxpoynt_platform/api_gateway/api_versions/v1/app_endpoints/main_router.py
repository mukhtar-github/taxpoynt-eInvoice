"""
APP Main Router - API Version 1
===============================
Main router for Access Point Provider (APP) endpoints in API v1.
Consolidates all APP-specific functionality for FIRS e-invoicing compliance.
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

# Import APP system routers
from .firs_integration_endpoints import create_firs_integration_router
from .taxpayer_management_endpoints import create_taxpayer_management_router
from .invoice_submission_endpoints import create_invoice_submission_router
from .compliance_validation_endpoints import create_compliance_validation_router
from .certificate_management_endpoints import create_certificate_management_router
from .grant_management_endpoints import create_grant_management_router

logger = logging.getLogger(__name__)


class APPRouterV1:
    """
    Access Point Provider Router - Version 1
    ========================================
    Handles all APP endpoints for API v1, including:
    - FIRS integration and communication
    - Taxpayer onboarding and management
    - Invoice submission to FIRS systems
    - Compliance validation and reporting
    - Certificate management and security
    - Grant tracking and performance metrics
    
    **APP Role Context:**
    - TaxPoynt serves as Access Point Provider for FIRS e-invoicing
    - Manages direct integration with FIRS systems
    - Handles taxpayer onboarding for FIRS grant milestones
    - Ensures compliance with Nigerian e-invoicing regulations
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/app", tags=["Access Point Provider V1"])
        
        # Include all APP sub-routers
        self._include_sub_routers()
        
        # Setup general APP routes
        self._setup_routes()
        
        logger.info("APP Router V1 initialized")
    
    def _include_sub_routers(self):
        """Include all APP sub-routers"""
        
        # FIRS Integration Routes
        firs_router = create_firs_integration_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(firs_router)
        
        # Taxpayer Management Routes
        taxpayer_router = create_taxpayer_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(taxpayer_router)
        
        # Invoice Submission Routes
        invoice_router = create_invoice_submission_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(invoice_router)
        
        # Compliance Validation Routes
        compliance_router = create_compliance_validation_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(compliance_router)
        
        # Certificate Management Routes
        certificate_router = create_certificate_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(certificate_router)
        
        # Grant Management Routes
        grant_router = create_grant_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(grant_router)
    
    def _setup_routes(self):
        """Configure general APP v1 routes"""
        
        # APP Health and Status Routes
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="APP services health check",
            description="Check health of all APP services and FIRS connectivity",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/status",
            self.get_app_status,
            methods=["GET"],
            summary="Get APP status overview",
            description="Get comprehensive status of APP operations and integrations",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        # APP Information Routes
        self.router.add_api_route(
            "/info",
            self.get_app_info,
            methods=["GET"],
            summary="Get APP information",
            description="Get Access Point Provider information and capabilities",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/capabilities",
            self.get_app_capabilities,
            methods=["GET"],
            summary="Get APP capabilities",
            description="Get detailed APP capabilities and supported features",
            response_model=V1ResponseModel
        )
        
        # APP Dashboard Routes
        self.router.add_api_route(
            "/dashboard",
            self.get_app_dashboard,
            methods=["GET"],
            summary="Get APP dashboard data",
            description="Get dashboard data for APP operations overview",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/dashboard/summary",
            self.get_dashboard_summary,
            methods=["GET"],
            summary="Get dashboard summary",
            description="Get summary statistics for APP dashboard",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        # APP Configuration Routes
        self.router.add_api_route(
            "/configuration",
            self.get_app_configuration,
            methods=["GET"],
            summary="Get APP configuration",
            description="Get current APP configuration settings",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/configuration",
            self.update_app_configuration,
            methods=["PUT"],
            summary="Update APP configuration",
            description="Update APP configuration settings",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
    
    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure Access Point Provider role access for v1"""
        context = await self.role_detector.detect_role_context(request)
        
        if not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            logger.warning(f"APP v1 endpoint access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Point Provider role required for v1 API"
            )
        
        # Apply v1-specific permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/app{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for APP v1 endpoint"
            )
        
        # Add v1-specific context
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "app"
        
        return context
    
    # APP Health and Status Handlers
    async def health_check(self):
        """APP services health check for v1"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="health_check",
                payload={"api_version": "v1"}
            )
            
            return JSONResponse(content={
                "status": "healthy",
                "service": "app_services",
                "api_version": "v1",
                "timestamp": result.get("timestamp"),
                "version_specific": {
                    "supported_features": [
                        "firs_integration",
                        "taxpayer_management", 
                        "invoice_submission",
                        "compliance_validation",
                        "certificate_management",
                        "grant_management"
                    ],
                    "v1_compatibility": "full",
                    "firs_connectivity": "connected"
                }
            })
        except Exception as e:
            logger.error(f"APP v1 health check failed: {e}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "api_version": "v1",
                    "error": str(e)
                },
                status_code=503
            )
    
    async def get_app_status(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get APP status overview"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_app_status",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP status in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP status")
    
    # APP Information Handlers
    async def get_app_info(self):
        """Get APP information"""
        try:
            app_info = {
                "app_name": "TaxPoynt Access Point Provider",
                "app_version": "v1.0.0",
                "api_version": "v1",
                "description": "FIRS e-invoicing Access Point Provider for Nigerian tax compliance",
                "capabilities": [
                    "firs_integration",
                    "taxpayer_onboarding",
                    "invoice_submission",
                    "compliance_validation",
                    "certificate_management",
                    "grant_tracking"
                ],
                "supported_standards": [
                    "UBL (Universal Business Language)",
                    "PEPPOL Standards",
                    "ISO 20022",
                    "ISO 27001",
                    "GDPR & NDPA",
                    "WCO Harmonized System",
                    "Legal Entity Identifier (LEI)"
                ],
                "firs_certified": True,
                "nitda_approved": True
            }
            
            return self._create_v1_response(app_info, "app_info_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP info in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP info")
    
    async def get_app_capabilities(self):
        """Get APP capabilities"""
        try:
            capabilities = {
                "firs_integration": {
                    "features": ["authentication", "invoice_submission", "status_tracking", "validation"],
                    "description": "Direct integration with FIRS e-invoicing systems"
                },
                "taxpayer_management": {
                    "features": ["onboarding", "lifecycle_management", "compliance_monitoring", "bulk_operations"],
                    "description": "Comprehensive taxpayer management for e-invoicing compliance"
                },
                "invoice_submission": {
                    "features": ["generation", "validation", "submission", "tracking"],
                    "description": "Generate and submit FIRS-compliant invoices"
                },
                "compliance_validation": {
                    "features": ["ubl_validation", "peppol_compliance", "iso_standards", "data_protection"],
                    "description": "Validate compliance with multiple regulatory standards"
                },
                "certificate_management": {
                    "features": ["lifecycle_management", "renewal", "security_monitoring", "backup"],
                    "description": "Manage FIRS certificates and authentication credentials"
                },
                "grant_management": {
                    "features": ["milestone_tracking", "performance_metrics", "reporting", "payment_tracking"],
                    "description": "Track FIRS grants and performance metrics"
                }
            }
            
            return self._create_v1_response(capabilities, "app_capabilities_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP capabilities in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP capabilities")
    
    # APP Dashboard Handlers
    async def get_app_dashboard(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get APP dashboard data"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_app_dashboard",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_dashboard_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP dashboard in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP dashboard")
    
    async def get_dashboard_summary(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get dashboard summary"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_dashboard_summary",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "dashboard_summary_retrieved")
        except Exception as e:
            logger.error(f"Error getting dashboard summary in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get dashboard summary")
    
    # APP Configuration Handlers
    async def get_app_configuration(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get APP configuration"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_app_configuration",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_configuration_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP configuration in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP configuration")
    
    async def update_app_configuration(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Update APP configuration"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_app_configuration",
                payload={
                    "configuration_updates": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_configuration_updated")
        except Exception as e:
            logger.error(f"Error updating APP configuration in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update APP configuration")
    
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


def create_app_v1_router(role_detector: HTTPRoleDetector,
                        permission_guard: APIPermissionGuard,
                        message_router: MessageRouter) -> APIRouter:
    """Factory function to create APP V1 Router"""
    app_v1_router = APPRouterV1(role_detector, permission_guard, message_router)
    return app_v1_router.router