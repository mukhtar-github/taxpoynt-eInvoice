"""
Cross-Role Endpoints - API v1
=============================
Hybrid endpoints for operations requiring multiple role capabilities.
Handles workflows that span System Integrator and Access Point Provider roles.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse

from .....core_platform.authentication.role_manager import PlatformRole
from .....core_platform.messaging.message_router import ServiceRole, MessageRouter
from ....role_routing.models import HTTPRoutingContext
from ....role_routing.role_detector import HTTPRoleDetector
from ....role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class CrossRoleEndpointsV1:
    """
    Cross-Role Endpoints - Version 1
    ================================
    Manages operations requiring multiple role capabilities:
    
    **Cross-Role Operations:**
    - **End-to-End Invoice Processing**: SI data collection → APP FIRS submission
    - **Taxpayer Integration Workflows**: SI organization setup → APP taxpayer onboarding
    - **Compliance Coordination**: SI validation → APP regulatory submission
    - **Data Synchronization**: Real-time sync between SI and APP operations
    - **Performance Analytics**: Cross-role performance metrics and insights
    - **Error Resolution**: Collaborative error handling across role boundaries
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/cross-role", tags=["Cross-Role Operations V1"])
        
        # Define cross-role capabilities
        self.cross_role_capabilities = {
            "end_to_end_processing": {
                "required_roles": [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER],
                "description": "Complete invoice processing from business data to FIRS submission",
                "features": ["data_collection", "validation", "transformation", "submission", "tracking"]
            },
            "taxpayer_workflows": {
                "required_roles": [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER],
                "description": "Integrated taxpayer setup and onboarding workflows",
                "features": ["organization_setup", "taxpayer_registration", "compliance_setup", "monitoring"]
            },
            "compliance_coordination": {
                "required_roles": [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER],
                "description": "Coordinated compliance validation and regulatory submission",
                "features": ["pre_validation", "compliance_checking", "regulatory_submission", "audit_trails"]
            }
        }
        
        self._setup_routes()
        logger.info("Cross-Role Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup cross-role operation routes"""
        
        # Cross-Role Capabilities Information
        self.router.add_api_route(
            "/capabilities",
            self.get_cross_role_capabilities,
            methods=["GET"],
            summary="Get cross-role capabilities",
            description="Get available cross-role operations and requirements",
            response_model=V1ResponseModel
        )
        
        # End-to-End Invoice Processing
        self.router.add_api_route(
            "/invoice-processing/initiate",
            self.initiate_end_to_end_processing,
            methods=["POST"],
            summary="Initiate end-to-end invoice processing",
            description="Start complete invoice processing from business data to FIRS submission",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._create_multi_role_dependency([PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER]))]
        )
        
        self.router.add_api_route(
            "/invoice-processing/{process_id}/status",
            self.get_processing_status,
            methods=["GET"],
            summary="Get processing status",
            description="Get status of end-to-end invoice processing",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        self.router.add_api_route(
            "/invoice-processing/{process_id}/stages",
            self.get_processing_stages,
            methods=["GET"],
            summary="Get processing stages",
            description="Get detailed stages of end-to-end processing",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        # Taxpayer Integration Workflows
        self.router.add_api_route(
            "/taxpayer-workflows/setup",
            self.setup_taxpayer_workflow,
            methods=["POST"],
            summary="Setup taxpayer workflow",
            description="Setup integrated SI organization and APP taxpayer workflow",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._create_multi_role_dependency([PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER]))]
        )
        
        self.router.add_api_route(
            "/taxpayer-workflows/{workflow_id}/status",
            self.get_workflow_status,
            methods=["GET"],
            summary="Get workflow status",
            description="Get status of taxpayer integration workflow",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        self.router.add_api_route(
            "/taxpayer-workflows/{workflow_id}/execute",
            self.execute_workflow_stage,
            methods=["POST"],
            summary="Execute workflow stage",
            description="Execute specific stage of taxpayer workflow",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        # Compliance Coordination
        self.router.add_api_route(
            "/compliance/coordinate",
            self.coordinate_compliance_validation,
            methods=["POST"],
            summary="Coordinate compliance validation",
            description="Coordinate compliance validation across SI and APP roles",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._create_multi_role_dependency([PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER]))]
        )
        
        self.router.add_api_route(
            "/compliance/{validation_id}/progress",
            self.get_compliance_progress,
            methods=["GET"],
            summary="Get compliance validation progress",
            description="Get progress of coordinated compliance validation",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        # Data Synchronization
        self.router.add_api_route(
            "/sync/organizations-taxpayers",
            self.sync_organizations_with_taxpayers,
            methods=["POST"],
            summary="Sync organizations with taxpayers",
            description="Synchronize SI organizations with APP taxpayers",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._create_multi_role_dependency([PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER]))]
        )
        
        self.router.add_api_route(
            "/sync/transactions-invoices",
            self.sync_transactions_with_invoices,
            methods=["POST"],
            summary="Sync transactions with invoices",
            description="Synchronize SI transactions with APP invoice submissions",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._create_multi_role_dependency([PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER]))]
        )
        
        self.router.add_api_route(
            "/sync/status/{sync_id}",
            self.get_sync_status,
            methods=["GET"],
            summary="Get synchronization status",
            description="Get status of data synchronization operation",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        # Performance Analytics
        self.router.add_api_route(
            "/analytics/cross-role-performance",
            self.get_cross_role_performance,
            methods=["GET"],
            summary="Get cross-role performance metrics",
            description="Get performance metrics spanning SI and APP operations",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        self.router.add_api_route(
            "/analytics/bottleneck-analysis",
            self.analyze_bottlenecks,
            methods=["GET"],
            summary="Analyze cross-role bottlenecks",
            description="Analyze performance bottlenecks in cross-role workflows",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        # Error Resolution
        self.router.add_api_route(
            "/errors/cross-role",
            self.list_cross_role_errors,
            methods=["GET"],
            summary="List cross-role errors",
            description="List errors occurring in cross-role operations",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        self.router.add_api_route(
            "/errors/{error_id}/resolve",
            self.resolve_cross_role_error,
            methods=["POST"],
            summary="Resolve cross-role error",
            description="Resolve error in cross-role operation",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
    
    def _create_multi_role_dependency(self, required_roles: List[PlatformRole]):
        """Create dependency function that requires access to multiple roles"""
        async def validate_multi_role_access(request: Request) -> HTTPRoutingContext:
            context = await self.role_detector.detect_role_context(request)
            
            # Check if user has access to all required roles (either directly or through admin)
            has_required_access = (
                context.has_role(PlatformRole.ADMINISTRATOR) or
                all(context.has_role(role) for role in required_roles)
            )
            
            if not has_required_access:
                logger.warning(f"Multi-role access denied for context: {context}, required: {required_roles}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access requires all roles: {[role.value for role in required_roles]}"
                )
            
            # Apply cross-role permission guard
            if not await self.permission_guard.check_endpoint_permission(
                context, f"v1/hybrid/cross-role{request.url.path}", request.method
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for cross-role operation"
                )
            
            # Add cross-role context
            context.metadata["operation_type"] = "cross_role"
            context.metadata["required_roles"] = [role.value for role in required_roles]
            
            return context
        
        return validate_multi_role_access
    
    async def _require_hybrid_access(self, request: Request) -> HTTPRoutingContext:
        """Require hybrid access (any compatible role)"""
        context = await self.role_detector.detect_role_context(request)
        
        # Allow access for SI, APP, or Admin roles
        allowed_roles = {
            PlatformRole.SYSTEM_INTEGRATOR,
            PlatformRole.ACCESS_POINT_PROVIDER,
            PlatformRole.ADMINISTRATOR
        }
        
        if not any(context.has_role(role) for role in allowed_roles):
            logger.warning(f"Hybrid access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access requires System Integrator, Access Point Provider, or Administrator role"
            )
        
        # Apply hybrid permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/hybrid/cross-role{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for hybrid operation"
            )
        
        # Add hybrid context
        context.metadata["operation_type"] = "hybrid"
        
        return context
    
    # Cross-Role Capability Endpoints
    async def get_cross_role_capabilities(self, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get cross-role capabilities"""
        try:
            # Filter capabilities based on user's roles
            accessible_capabilities = {}
            
            for capability_name, capability_info in self.cross_role_capabilities.items():
                required_roles = capability_info["required_roles"]
                
                # Check if user has access to this capability
                has_access = (
                    context.has_role(PlatformRole.ADMINISTRATOR) or
                    all(context.has_role(role) for role in required_roles)
                )
                
                if has_access:
                    accessible_capabilities[capability_name] = capability_info
            
            result = {
                "cross_role_capabilities": accessible_capabilities,
                "user_roles": [role.value for role in context.roles],
                "total_capabilities": len(accessible_capabilities)
            }
            
            return self._create_v1_response(result, "cross_role_capabilities_retrieved")
        except Exception as e:
            logger.error(f"Error getting cross-role capabilities in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get cross-role capabilities")
    
    # End-to-End Invoice Processing Endpoints
    async def initiate_end_to_end_processing(self, request: Request, context: HTTPRoutingContext = Depends(_create_multi_role_dependency)):
        """Initiate end-to-end invoice processing"""
        try:
            body = await request.json()
            
            # Validate required fields
            required_fields = ["organization_id", "business_data", "target_systems"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.HYBRID_COORDINATOR,
                operation="initiate_end_to_end_processing",
                payload={
                    "processing_data": body,
                    "user_context": {
                        "user_id": context.user_id,
                        "roles": [role.value for role in context.roles]
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "end_to_end_processing_initiated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error initiating end-to-end processing in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to initiate end-to-end processing")
    
    async def get_processing_status(self, process_id: str, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get processing status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.HYBRID_COORDINATOR,
                operation="get_processing_status",
                payload={
                    "process_id": process_id,
                    "user_context": {
                        "user_id": context.user_id,
                        "roles": [role.value for role in context.roles]
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "processing_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting processing status {process_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get processing status")
    
    async def get_processing_stages(self, process_id: str, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get processing stages"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.HYBRID_COORDINATOR,
                operation="get_processing_stages",
                payload={
                    "process_id": process_id,
                    "user_context": {
                        "user_id": context.user_id,
                        "roles": [role.value for role in context.roles]
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "processing_stages_retrieved")
        except Exception as e:
            logger.error(f"Error getting processing stages {process_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get processing stages")
    
    # Placeholder implementations for remaining endpoints
    async def setup_taxpayer_workflow(self, request: Request, context: HTTPRoutingContext = Depends(_create_multi_role_dependency)):
        """Setup taxpayer workflow - placeholder"""
        return self._create_v1_response({"workflow_id": "workflow_123"}, "taxpayer_workflow_setup")
    
    async def get_workflow_status(self, workflow_id: str, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get workflow status - placeholder"""
        return self._create_v1_response({"workflow_id": workflow_id, "status": "in_progress"}, "workflow_status_retrieved")
    
    async def execute_workflow_stage(self, workflow_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Execute workflow stage - placeholder"""
        return self._create_v1_response({"workflow_id": workflow_id, "stage": "executed"}, "workflow_stage_executed")
    
    async def coordinate_compliance_validation(self, request: Request, context: HTTPRoutingContext = Depends(_create_multi_role_dependency)):
        """Coordinate compliance validation - placeholder"""
        return self._create_v1_response({"validation_id": "validation_123"}, "compliance_coordination_initiated")
    
    async def get_compliance_progress(self, validation_id: str, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get compliance progress - placeholder"""
        return self._create_v1_response({"validation_id": validation_id, "progress": "75%"}, "compliance_progress_retrieved")
    
    async def sync_organizations_with_taxpayers(self, request: Request, context: HTTPRoutingContext = Depends(_create_multi_role_dependency)):
        """Sync organizations with taxpayers - placeholder"""
        return self._create_v1_response({"sync_id": "sync_123"}, "organization_taxpayer_sync_initiated")
    
    async def sync_transactions_with_invoices(self, request: Request, context: HTTPRoutingContext = Depends(_create_multi_role_dependency)):
        """Sync transactions with invoices - placeholder"""
        return self._create_v1_response({"sync_id": "sync_456"}, "transaction_invoice_sync_initiated")
    
    async def get_sync_status(self, sync_id: str, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get sync status - placeholder"""
        return self._create_v1_response({"sync_id": sync_id, "status": "completed"}, "sync_status_retrieved")
    
    async def get_cross_role_performance(self, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get cross-role performance - placeholder"""
        return self._create_v1_response({"performance_metrics": {}}, "cross_role_performance_retrieved")
    
    async def analyze_bottlenecks(self, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Analyze bottlenecks - placeholder"""
        return self._create_v1_response({"bottlenecks": []}, "bottleneck_analysis_completed")
    
    async def list_cross_role_errors(self, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """List cross-role errors - placeholder"""
        return self._create_v1_response({"errors": []}, "cross_role_errors_listed")
    
    async def resolve_cross_role_error(self, error_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Resolve cross-role error - placeholder"""
        return self._create_v1_response({"error_id": error_id, "resolution": "resolved"}, "cross_role_error_resolved")
    
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


def create_cross_role_router(role_detector: HTTPRoleDetector,
                            permission_guard: APIPermissionGuard,
                            message_router: MessageRouter) -> APIRouter:
    """Factory function to create Cross-Role Router"""
    cross_role_endpoints = CrossRoleEndpointsV1(role_detector, permission_guard, message_router)
    return cross_role_endpoints.router