"""
SI Services Router
=================
FastAPI router for System Integrator role endpoints that integrates with si_services/
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


class SIServicesRouter:
    """
    System Integrator Services Router
    ================================
    Handles all HTTP endpoints for System Integrator role operations including:
    - ERP/CRM/POS system integration management
    - Business data collection and processing
    - Customer onboarding and organization setup
    - Transaction processing and compliance
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/si", tags=["System Integrator"])
        self._setup_routes()
        
        logger.info("SI Services Router initialized")
    
    def _setup_routes(self):
        """Configure all SI-specific route handlers"""
        
        # Organization Management Routes
        self.router.add_api_route(
            "/organizations",
            self.list_organizations,
            methods=["GET"],
            summary="List managed organizations",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations/{org_id}",
            self.get_organization,
            methods=["GET"],
            summary="Get organization details",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations",
            self.create_organization,
            methods=["POST"],
            summary="Create new organization",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations/{org_id}",
            self.update_organization,
            methods=["PUT"],
            summary="Update organization",
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Business System Integration Routes
        self.router.add_api_route(
            "/integrations/erp",
            self.list_erp_connections,
            methods=["GET"],
            summary="List ERP system connections",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/integrations/erp",
            self.create_erp_connection,
            methods=["POST"],
            summary="Create ERP system connection",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/integrations/crm",
            self.list_crm_connections,
            methods=["GET"],
            summary="List CRM system connections",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/integrations/pos",
            self.list_pos_connections,
            methods=["GET"],
            summary="List POS system connections",
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Transaction Processing Routes
        self.router.add_api_route(
            "/transactions",
            self.list_transactions,
            methods=["GET"],
            summary="List processed transactions",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/transactions/process",
            self.process_transaction_batch,
            methods=["POST"],
            summary="Process transaction batch",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/transactions/{transaction_id}/status",
            self.get_transaction_status,
            methods=["GET"],
            summary="Get transaction processing status",
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Invoice Generation Routes
        self.router.add_api_route(
            "/invoices/generate",
            self.generate_invoices,
            methods=["POST"],
            summary="Generate FIRS-compliant invoices",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/invoices/{invoice_id}",
            self.get_invoice,
            methods=["GET"],
            summary="Get generated invoice",
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Compliance and Reporting Routes
        self.router.add_api_route(
            "/compliance/validation",
            self.validate_compliance,
            methods=["POST"],
            summary="Validate transaction compliance",
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/reports/onboarding",
            self.get_onboarding_report,
            methods=["GET"],
            summary="Get organization onboarding report",
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Health and Status Routes
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="SI services health check"
        )
    
    async def _require_si_role(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure System Integrator role access"""
        context = await self.role_detector.detect_role_context(request)
        
        if not context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            logger.warning(f"SI endpoint access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System Integrator role required"
            )
        
        # Apply permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"si{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for SI endpoint"
            )
        
        return context
    
    # Organization Management Handlers
    async def list_organizations(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List all organizations managed by this SI"""
        try:
            # Route to si_services through message router
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_organizations",
                payload={"si_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error listing organizations: {e}")
            raise HTTPException(status_code=500, detail="Failed to list organizations")
    
    async def get_organization(self, org_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get specific organization details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization",
                payload={"org_id": org_id, "si_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting organization {org_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization")
    
    async def create_organization(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Create new organization under SI management"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_organization",
                payload={"organization_data": body, "si_id": context.user_id}
            )
            return JSONResponse(content=result, status_code=201)
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise HTTPException(status_code=500, detail="Failed to create organization")
    
    async def update_organization(self, org_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Update organization information"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_organization",
                payload={"org_id": org_id, "updates": body, "si_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error updating organization {org_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update organization")
    
    # Business System Integration Handlers
    async def list_erp_connections(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List ERP system connections"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_erp_connections",
                payload={"si_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error listing ERP connections: {e}")
            raise HTTPException(status_code=500, detail="Failed to list ERP connections")
    
    async def create_erp_connection(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Create new ERP system connection"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_erp_connection",
                payload={"connection_data": body, "si_id": context.user_id}
            )
            return JSONResponse(content=result, status_code=201)
        except Exception as e:
            logger.error(f"Error creating ERP connection: {e}")
            raise HTTPException(status_code=500, detail="Failed to create ERP connection")
    
    async def list_crm_connections(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List CRM system connections"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_crm_connections",
                payload={"si_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error listing CRM connections: {e}")
            raise HTTPException(status_code=500, detail="Failed to list CRM connections")
    
    async def list_pos_connections(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List POS system connections"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_pos_connections",
                payload={"si_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error listing POS connections: {e}")
            raise HTTPException(status_code=500, detail="Failed to list POS connections")
    
    # Transaction Processing Handlers
    async def list_transactions(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List processed transactions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_transactions",
                payload={"si_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error listing transactions: {e}")
            raise HTTPException(status_code=500, detail="Failed to list transactions")
    
    async def process_transaction_batch(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Process batch of transactions"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="process_transaction_batch",
                payload={"transactions": body, "si_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error processing transaction batch: {e}")
            raise HTTPException(status_code=500, detail="Failed to process transactions")
    
    async def get_transaction_status(self, transaction_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get transaction processing status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_transaction_status",
                payload={"transaction_id": transaction_id, "si_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting transaction status {transaction_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get transaction status")
    
    # Invoice Generation Handlers
    async def generate_invoices(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Generate FIRS-compliant invoices"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="generate_invoices",
                payload={"invoice_requests": body, "si_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error generating invoices: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate invoices")
    
    async def get_invoice(self, invoice_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get generated invoice"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_invoice",
                payload={"invoice_id": invoice_id, "si_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting invoice {invoice_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get invoice")
    
    # Compliance and Reporting Handlers
    async def validate_compliance(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Validate transaction compliance"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="validate_compliance",
                payload={"validation_request": body, "si_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error validating compliance: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate compliance")
    
    async def get_onboarding_report(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get organization onboarding report"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_onboarding_report",
                payload={"si_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting onboarding report: {e}")
            raise HTTPException(status_code=500, detail="Failed to get onboarding report")
    
    # Health Check Handler
    async def health_check(self):
        """SI services health check"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="health_check",
                payload={}
            )
            return JSONResponse(content={
                "status": "healthy",
                "service": "si_services",
                "timestamp": result.get("timestamp"),
                "details": result.get("details", {})
            })
        except Exception as e:
            logger.error(f"SI health check failed: {e}")
            return JSONResponse(
                content={"status": "unhealthy", "error": str(e)},
                status_code=503
            )


def create_si_router(role_detector: HTTPRoleDetector,
                    permission_guard: APIPermissionGuard,
                    message_router: MessageRouter) -> APIRouter:
    """Factory function to create SI Services Router"""
    si_router = SIServicesRouter(role_detector, permission_guard, message_router)
    return si_router.router