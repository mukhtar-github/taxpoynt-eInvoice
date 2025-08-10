"""
APP Services Router
==================
FastAPI router for Access Point Provider role endpoints that integrates with app_services/
architecture and existing role management system.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from ...core_platform.authentication.role_manager import PlatformRole, RoleScope
from ...core_platform.messaging.message_router import ServiceRole, MessageRouter
from .models import HTTPRoutingContext, RoleBasedRoute, RoutingSecurityLevel
from .role_detector import HTTPRoleDetector
from .permission_guard import APIPermissionGuard

logger = logging.getLogger(__name__)


class APPServicesRouter:
    """
    Access Point Provider Services Router
    ====================================
    Handles all HTTP endpoints for Access Point Provider role operations including:
    - FIRS integration management and certification
    - Taxpayer onboarding and compliance monitoring
    - Invoice validation and submission to FIRS
    - Regulatory compliance and reporting
    - Grant milestone tracking and reporting
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/app", tags=["Access Point Provider"])
        self._setup_routes()
        
        logger.info("APP Services Router initialized")
    
    def _setup_routes(self):
        """Configure all APP-specific route handlers"""
        
        # FIRS Integration Routes
        self.router.add_api_route(
            "/firs/connection",
            self.get_firs_connection_status,
            methods=["GET"],
            summary="Get FIRS connection status",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/firs/certification",
            self.get_app_certification,
            methods=["GET"],
            summary="Get APP certification status",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/firs/invoices/submit",
            self.submit_invoices_to_firs,
            methods=["POST"],
            summary="Submit invoices to FIRS",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/firs/invoices/{invoice_id}/status",
            self.get_firs_invoice_status,
            methods=["GET"],
            summary="Get FIRS invoice status",
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Taxpayer Management Routes
        self.router.add_api_route(
            "/taxpayers",
            self.list_taxpayers,
            methods=["GET"],
            summary="List onboarded taxpayers",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/taxpayers/{taxpayer_id}",
            self.get_taxpayer,
            methods=["GET"],
            summary="Get taxpayer details",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/taxpayers",
            self.onboard_taxpayer,
            methods=["POST"],
            summary="Onboard new taxpayer",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/taxpayers/{taxpayer_id}/compliance",
            self.get_taxpayer_compliance,
            methods=["GET"],
            summary="Get taxpayer compliance status",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/taxpayers/{taxpayer_id}/activate",
            self.activate_taxpayer,
            methods=["POST"],
            summary="Activate taxpayer e-invoicing",
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Invoice Validation and Processing Routes
        self.router.add_api_route(
            "/invoices/validate",
            self.validate_invoices,
            methods=["POST"],
            summary="Validate invoices for FIRS compliance",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/invoices/batch",
            self.process_invoice_batch,
            methods=["POST"],
            summary="Process invoice batch for submission",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/invoices/{invoice_id}/validate",
            self.validate_single_invoice,
            methods=["POST"],
            summary="Validate single invoice",
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Compliance and Regulatory Routes
        self.router.add_api_route(
            "/compliance/standards",
            self.get_compliance_standards,
            methods=["GET"],
            summary="Get current compliance standards",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/compliance/check",
            self.run_compliance_check,
            methods=["POST"],
            summary="Run comprehensive compliance check",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/compliance/report",
            self.generate_compliance_report,
            methods=["POST"],
            summary="Generate compliance report",
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Grant and Milestone Routes
        self.router.add_api_route(
            "/grants/milestones",
            self.get_grant_milestones,
            methods=["GET"],
            summary="Get grant milestone status",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/grants/milestones/{milestone_id}",
            self.update_milestone_progress,
            methods=["PUT"],
            summary="Update milestone progress",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/grants/onboarding-report",
            self.generate_onboarding_report,
            methods=["POST"],
            summary="Generate onboarding report for FIRS",
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Certificate Management Routes
        self.router.add_api_route(
            "/certificates",
            self.list_certificates,
            methods=["GET"],
            summary="List APP certificates",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/certificates/{cert_id}",
            self.get_certificate,
            methods=["GET"],
            summary="Get certificate details",
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/certificates/renew",
            self.renew_certificates,
            methods=["POST"],
            summary="Renew APP certificates",
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Health and Status Routes
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="APP services health check"
        )
        
        self.router.add_api_route(
            "/status/firs",
            self.get_firs_system_status,
            methods=["GET"],
            summary="Get FIRS system status",
            dependencies=[Depends(self._require_app_role)]
        )
    
    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure Access Point Provider role access"""
        context = await self.role_detector.detect_role_context(request)
        
        if not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            logger.warning(f"APP endpoint access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Point Provider role required"
            )
        
        # Apply permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"app{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for APP endpoint"
            )
        
        return context
    
    # FIRS Integration Handlers
    async def get_firs_connection_status(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get FIRS connection status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_connection_status",
                payload={"app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting FIRS connection status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS connection status")
    
    async def get_app_certification(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get APP certification status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_app_certification",
                payload={"app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting APP certification: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP certification")
    
    async def submit_invoices_to_firs(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Submit invoices to FIRS"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="submit_invoices_to_firs",
                payload={"invoices": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error submitting invoices to FIRS: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit invoices to FIRS")
    
    async def get_firs_invoice_status(self, invoice_id: str, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get FIRS invoice status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_invoice_status",
                payload={"invoice_id": invoice_id, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting FIRS invoice status {invoice_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS invoice status")
    
    # Taxpayer Management Handlers
    async def list_taxpayers(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """List onboarded taxpayers"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_taxpayers",
                payload={"app_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error listing taxpayers: {e}")
            raise HTTPException(status_code=500, detail="Failed to list taxpayers")
    
    async def get_taxpayer(self, taxpayer_id: str, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get taxpayer details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_taxpayer",
                payload={"taxpayer_id": taxpayer_id, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting taxpayer {taxpayer_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get taxpayer")
    
    async def onboard_taxpayer(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Onboard new taxpayer"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="onboard_taxpayer",
                payload={"taxpayer_data": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result, status_code=201)
        except Exception as e:
            logger.error(f"Error onboarding taxpayer: {e}")
            raise HTTPException(status_code=500, detail="Failed to onboard taxpayer")
    
    async def get_taxpayer_compliance(self, taxpayer_id: str, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get taxpayer compliance status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_taxpayer_compliance",
                payload={"taxpayer_id": taxpayer_id, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting taxpayer compliance {taxpayer_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get taxpayer compliance")
    
    async def activate_taxpayer(self, taxpayer_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Activate taxpayer e-invoicing"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="activate_taxpayer",
                payload={"taxpayer_id": taxpayer_id, "activation_data": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error activating taxpayer {taxpayer_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to activate taxpayer")
    
    # Invoice Validation and Processing Handlers
    async def validate_invoices(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Validate invoices for FIRS compliance"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_invoices",
                payload={"invoices": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error validating invoices: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate invoices")
    
    async def process_invoice_batch(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Process invoice batch for submission"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="process_invoice_batch",
                payload={"invoice_batch": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error processing invoice batch: {e}")
            raise HTTPException(status_code=500, detail="Failed to process invoice batch")
    
    async def validate_single_invoice(self, invoice_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Validate single invoice"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_single_invoice",
                payload={"invoice_id": invoice_id, "validation_data": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error validating single invoice {invoice_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate single invoice")
    
    # Compliance and Regulatory Handlers
    async def get_compliance_standards(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get current compliance standards"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_compliance_standards",
                payload={"app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting compliance standards: {e}")
            raise HTTPException(status_code=500, detail="Failed to get compliance standards")
    
    async def run_compliance_check(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Run comprehensive compliance check"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="run_compliance_check",
                payload={"check_request": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error running compliance check: {e}")
            raise HTTPException(status_code=500, detail="Failed to run compliance check")
    
    async def generate_compliance_report(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Generate compliance report"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_compliance_report",
                payload={"report_request": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate compliance report")
    
    # Grant and Milestone Handlers
    async def get_grant_milestones(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get grant milestone status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_grant_milestones",
                payload={"app_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting grant milestones: {e}")
            raise HTTPException(status_code=500, detail="Failed to get grant milestones")
    
    async def update_milestone_progress(self, milestone_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Update milestone progress"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_milestone_progress",
                payload={"milestone_id": milestone_id, "progress_data": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error updating milestone progress {milestone_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update milestone progress")
    
    async def generate_onboarding_report(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Generate onboarding report for FIRS"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_onboarding_report",
                payload={"report_request": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error generating onboarding report: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate onboarding report")
    
    # Certificate Management Handlers
    async def list_certificates(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """List APP certificates"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_certificates",
                payload={"app_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error listing certificates: {e}")
            raise HTTPException(status_code=500, detail="Failed to list certificates")
    
    async def get_certificate(self, cert_id: str, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get certificate details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_certificate",
                payload={"cert_id": cert_id, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting certificate {cert_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get certificate")
    
    async def renew_certificates(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Renew APP certificates"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="renew_certificates",
                payload={"renewal_request": body, "app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error renewing certificates: {e}")
            raise HTTPException(status_code=500, detail="Failed to renew certificates")
    
    # Health and Status Handlers
    async def health_check(self):
        """APP services health check"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="health_check",
                payload={}
            )
            return JSONResponse(content={
                "status": "healthy",
                "service": "app_services",
                "timestamp": result.get("timestamp"),
                "details": result.get("details", {})
            })
        except Exception as e:
            logger.error(f"APP health check failed: {e}")
            return JSONResponse(
                content={"status": "unhealthy", "error": str(e)},
                status_code=503
            )
    
    async def get_firs_system_status(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get FIRS system status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_system_status",
                payload={"app_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting FIRS system status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS system status")


def create_app_router(role_detector: HTTPRoleDetector,
                     permission_guard: APIPermissionGuard,
                     message_router: MessageRouter) -> APIRouter:
    """Factory function to create APP Services Router"""
    app_router = APPServicesRouter(role_detector, permission_guard, message_router)
    return app_router.router