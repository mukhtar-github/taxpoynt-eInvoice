"""
SI Main Router - API Version 1
==============================
Main router for System Integrator endpoints in API v1.
Consolidates all SI-specific functionality into a single versioned router.
Professional business system integration architecture.
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

# Import business system routers  
from .organization_endpoints import create_organization_router
from .business_endpoints import (
    create_erp_router,
    create_crm_router, 
    create_pos_router,
    create_ecommerce_router,
    create_accounting_router,
    create_inventory_router
)
from .financial_endpoints import (
    create_banking_router,
    create_payment_processor_router,
    create_validation_router
)
from .transaction_endpoints import create_transaction_router
from .compliance_endpoints import create_compliance_router

logger = logging.getLogger(__name__)


class SIRouterV1:
    """
    System Integrator Router - Version 1
    ====================================
    Handles all System Integrator endpoints for API v1, including:
    - Organization management and onboarding
    - ERP/CRM/POS system integrations
    - Transaction processing and validation
    - Compliance checking and reporting
    - Health monitoring and status
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/si", tags=["System Integrator V1"])
        self._setup_routes()
        
        logger.info("SI Router V1 initialized")
    
    def _setup_routes(self):
        """Configure all SI v1 routes"""
        
        # Organization Management Routes
        self.router.add_api_route(
            "/organizations",
            self.list_organizations,
            methods=["GET"],
            summary="List managed organizations",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations/{org_id}",
            self.get_organization,
            methods=["GET"],
            summary="Get organization details",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations",
            self.create_organization,
            methods=["POST"],
            summary="Create new organization",
            response_model=V1ResponseModel,
            status_code=201,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations/{org_id}",
            self.update_organization,
            methods=["PUT"],
            summary="Update organization",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Business System Integration Routes
        self.router.add_api_route(
            "/integrations/erp",
            self.list_erp_connections,
            methods=["GET"],
            summary="List ERP system connections",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/integrations/erp",
            self.create_erp_connection,
            methods=["POST"],
            summary="Create ERP connection",
            response_model=V1ResponseModel,
            status_code=201,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/integrations/erp/{connection_id}",
            self.update_erp_connection,
            methods=["PUT"],
            summary="Update ERP connection",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/integrations/erp/{connection_id}/test",
            self.test_erp_connection,
            methods=["POST"],
            summary="Test ERP connection",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/integrations/crm",
            self.list_crm_connections,
            methods=["GET"],
            summary="List CRM system connections",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/integrations/pos",
            self.list_pos_connections,
            methods=["GET"],
            summary="List POS system connections",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Transaction Processing Routes
        self.router.add_api_route(
            "/transactions",
            self.list_transactions,
            methods=["GET"],
            summary="List processed transactions",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/transactions/process",
            self.process_transaction_batch,
            methods=["POST"],
            summary="Process transaction batch",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/transactions/{transaction_id}",
            self.get_transaction,
            methods=["GET"],
            summary="Get transaction details",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/transactions/{transaction_id}/status",
            self.get_transaction_status,
            methods=["GET"],
            summary="Get transaction processing status",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/transactions/bulk-import",
            self.bulk_import_transactions,
            methods=["POST"],
            summary="Bulk import transactions from business systems",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Invoice Generation Routes
        self.router.add_api_route(
            "/invoices/generate",
            self.generate_invoices,
            methods=["POST"],
            summary="Generate FIRS-compliant invoices",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/invoices/{invoice_id}",
            self.get_invoice,
            methods=["GET"],
            summary="Get generated invoice",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/invoices/batch/{batch_id}",
            self.get_invoice_batch_status,
            methods=["GET"],
            summary="Get invoice batch generation status",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Compliance and Validation Routes
        self.router.add_api_route(
            "/compliance/validate",
            self.validate_compliance,
            methods=["POST"],
            summary="Validate transaction compliance",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/compliance/reports/onboarding",
            self.get_onboarding_report,
            methods=["GET"],
            summary="Get organization onboarding report",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/compliance/reports/transactions",
            self.get_transaction_compliance_report,
            methods=["GET"],
            summary="Get transaction compliance report",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Data Management Routes
        self.router.add_api_route(
            "/data/export",
            self.export_data,
            methods=["POST"],
            summary="Export organization and transaction data",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/data/sync",
            self.sync_business_system_data,
            methods=["POST"],
            summary="Sync data from connected business systems",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Health and Monitoring Routes
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="SI services health check",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/status/integrations",
            self.get_integration_status,
            methods=["GET"],
            summary="Get integration status overview",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
    
    async def _require_si_role(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure System Integrator role access for v1"""
        context = await self.role_detector.detect_role_context(request)
        
        if not context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            logger.warning(f"SI v1 endpoint access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System Integrator role required for v1 API"
            )
        
        # Apply v1-specific permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/si{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for SI v1 endpoint"
            )
        
        # Add v1-specific context
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "si"
        
        return context
    
    # Organization Management Handlers
    async def list_organizations(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List all organizations managed by this SI"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_organizations",
                payload={
                    "si_id": context.user_id,
                    "filters": dict(request.query_params),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organizations_listed")
        except Exception as e:
            logger.error(f"Error listing organizations in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list organizations")
    
    async def get_organization(self, org_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get specific organization details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_retrieved")
        except Exception as e:
            logger.error(f"Error getting organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization")
    
    async def create_organization(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Create new organization under SI management"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_organization",
                payload={
                    "organization_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_created", status_code=201)
        except Exception as e:
            logger.error(f"Error creating organization in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to create organization")
    
    async def update_organization(self, org_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Update organization information"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_organization",
                payload={
                    "org_id": org_id,
                    "updates": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_updated")
        except Exception as e:
            logger.error(f"Error updating organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update organization")
    
    # Integration Management Handlers (abbreviated for brevity - similar pattern)
    async def list_erp_connections(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List ERP system connections"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_erp_connections",
                payload={
                    "si_id": context.user_id,
                    "filters": dict(request.query_params),
                    "api_version": "v1"
                }
            )
            return self._create_v1_response(result, "erp_connections_listed")
        except Exception as e:
            logger.error(f"Error listing ERP connections in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list ERP connections")
    
    async def create_erp_connection(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Create new ERP system connection"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_erp_connection",
                payload={
                    "connection_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            return self._create_v1_response(result, "erp_connection_created", status_code=201)
        except Exception as e:
            logger.error(f"Error creating ERP connection in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to create ERP connection")
    
    # Additional handlers following same pattern...
    async def update_erp_connection(self, connection_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Update ERP connection"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_erp_connection",
                payload={
                    "connection_id": connection_id,
                    "updates": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            return self._create_v1_response(result, "erp_connection_updated")
        except Exception as e:
            logger.error(f"Error updating ERP connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update ERP connection")
    
    async def test_erp_connection(self, connection_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Test ERP connection"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="test_erp_connection",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            return self._create_v1_response(result, "erp_connection_tested")
        except Exception as e:
            logger.error(f"Error testing ERP connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to test ERP connection")
    
    # Health and utility handlers
    async def health_check(self):
        """SI services health check for v1"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="health_check",
                payload={"api_version": "v1"}
            )
            
            return JSONResponse(content={
                "status": "healthy",
                "service": "si_services",
                "api_version": "v1",
                "timestamp": result.get("timestamp"),
                "version_specific": {
                    "supported_features": [
                        "organization_management",
                        "erp_integration", 
                        "transaction_processing",
                        "compliance_validation"
                    ],
                    "v1_compatibility": "full"
                }
            })
        except Exception as e:
            logger.error(f"SI v1 health check failed: {e}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "api_version": "v1",
                    "error": str(e)
                },
                status_code=503
            )
    
    # Additional placeholder handlers (implement as needed)
    async def list_crm_connections(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List CRM connections - placeholder"""
        return self._create_v1_response({"connections": []}, "crm_connections_listed")
    
    async def list_pos_connections(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List POS connections - placeholder"""
        return self._create_v1_response({"connections": []}, "pos_connections_listed")
    
    async def list_transactions(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """List transactions - placeholder"""
        return self._create_v1_response({"transactions": []}, "transactions_listed")
    
    async def process_transaction_batch(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Process transaction batch - placeholder"""
        return self._create_v1_response({"batch_id": "batch_123"}, "transaction_batch_processed")
    
    async def get_transaction(self, transaction_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get transaction - placeholder"""
        return self._create_v1_response({"transaction_id": transaction_id}, "transaction_retrieved")
    
    async def get_transaction_status(self, transaction_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get transaction status - placeholder"""
        return self._create_v1_response({"status": "processed"}, "transaction_status_retrieved")
    
    async def bulk_import_transactions(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Bulk import transactions - placeholder"""
        return self._create_v1_response({"import_id": "import_123"}, "bulk_import_started")
    
    async def generate_invoices(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Generate invoices - placeholder"""
        return self._create_v1_response({"generation_id": "gen_123"}, "invoice_generation_started")
    
    async def get_invoice(self, invoice_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get invoice - placeholder"""
        return self._create_v1_response({"invoice_id": invoice_id}, "invoice_retrieved")
    
    async def get_invoice_batch_status(self, batch_id: str, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get invoice batch status - placeholder"""
        return self._create_v1_response({"batch_id": batch_id, "status": "completed"}, "invoice_batch_status_retrieved")
    
    async def validate_compliance(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Validate compliance - placeholder"""
        return self._create_v1_response({"validation_result": "passed"}, "compliance_validated")
    
    async def get_onboarding_report(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get onboarding report - placeholder"""
        return self._create_v1_response({"report_id": "report_123"}, "onboarding_report_generated")
    
    async def get_transaction_compliance_report(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get transaction compliance report - placeholder"""
        return self._create_v1_response({"report_id": "compliance_report_123"}, "compliance_report_generated")
    
    async def export_data(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Export data - placeholder"""
        return self._create_v1_response({"export_id": "export_123"}, "data_export_started")
    
    async def sync_business_system_data(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Sync business system data - placeholder"""
        return self._create_v1_response({"sync_id": "sync_123"}, "data_sync_started")
    
    async def get_integration_status(self, request: Request, context: HTTPRoutingContext = Depends(_require_si_role)):
        """Get integration status - placeholder"""
        return self._create_v1_response({"integrations": []}, "integration_status_retrieved")
    
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


def create_si_v1_router(role_detector: HTTPRoleDetector,
                       permission_guard: APIPermissionGuard,
                       message_router: MessageRouter) -> APIRouter:
    """Factory function to create SI V1 Router"""
    si_v1_router = SIRouterV1(role_detector, permission_guard, message_router)
    return si_v1_router.router