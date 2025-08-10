"""
Invoice Submission Endpoints - API v1
=====================================
Access Point Provider endpoints for submitting invoices to FIRS on behalf of taxpayers.
Handles invoice generation, submission, and tracking in FIRS systems.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse

from .....core_platform.authentication.role_manager import PlatformRole
from .....core_platform.messaging.message_router import ServiceRole, MessageRouter
from ....role_routing.models import HTTPRoutingContext
from ....role_routing.role_detector import HTTPRoleDetector
from ....role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class InvoiceSubmissionEndpointsV1:
    """
    Invoice Submission Endpoints - Version 1
    ========================================
    Manages invoice submission to FIRS for taxpayer compliance:
    
    **Invoice Submission Features:**
    - **Invoice Generation**: Generate FIRS-compliant invoices from business data
    - **Individual Submission**: Submit single invoices to FIRS
    - **Batch Submission**: Submit multiple invoices efficiently
    - **Status Tracking**: Track submission and processing status
    - **Error Handling**: Handle submission errors and retries
    - **UBL Compliance**: Ensure Universal Business Language compliance
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/invoices", tags=["Invoice Submission V1"])
        
        self._setup_routes()
        logger.info("Invoice Submission Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup invoice submission routes"""
        
        # Invoice Generation Routes
        self.router.add_api_route(
            "/generate",
            self.generate_firs_compliant_invoice,
            methods=["POST"],
            summary="Generate FIRS-compliant invoice",
            description="Generate invoice compliant with FIRS requirements",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/generate-batch",
            self.generate_invoice_batch,
            methods=["POST"],
            summary="Generate invoice batch",
            description="Generate multiple FIRS-compliant invoices",
            response_model=V1ResponseModel
        )
        
        # Invoice Submission Routes
        self.router.add_api_route(
            "/submit",
            self.submit_invoice,
            methods=["POST"],
            summary="Submit invoice to FIRS",
            description="Submit generated invoice to FIRS systems",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/submit-batch",
            self.submit_invoice_batch,
            methods=["POST"],
            summary="Submit invoice batch to FIRS",
            description="Submit multiple invoices to FIRS in batch",
            response_model=V1ResponseModel
        )
        
        # Submission Status Routes
        self.router.add_api_route(
            "/submissions/{submission_id}/status",
            self.get_submission_status,
            methods=["GET"],
            summary="Get submission status",
            description="Get status of invoice submission to FIRS",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/submissions",
            self.list_submissions,
            methods=["GET"],
            summary="List invoice submissions",
            description="List all invoice submissions to FIRS",
            response_model=V1ResponseModel
        )
        
        # Invoice Management Routes
        self.router.add_api_route(
            "/{invoice_id}",
            self.get_invoice,
            methods=["GET"],
            summary="Get invoice details",
            description="Get details of generated or submitted invoice",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{invoice_id}/cancel",
            self.cancel_invoice_submission,
            methods=["POST"],
            summary="Cancel invoice submission",
            description="Cancel pending invoice submission to FIRS",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{invoice_id}/resubmit",
            self.resubmit_invoice,
            methods=["POST"],
            summary="Resubmit invoice",
            description="Resubmit failed invoice to FIRS",
            response_model=V1ResponseModel
        )
    
    # Invoice Generation Endpoints
    async def generate_firs_compliant_invoice(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Generate FIRS-compliant invoice"""
        try:
            body = await request.json()
            
            # Validate required fields
            required_fields = ["taxpayer_id", "invoice_data"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_firs_compliant_invoice",
                payload={
                    "generation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_compliant_invoice_generated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating FIRS-compliant invoice in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate FIRS-compliant invoice")
    
    async def generate_invoice_batch(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Generate invoice batch"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_invoice_batch",
                payload={
                    "batch_generation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_batch_generation_initiated")
        except Exception as e:
            logger.error(f"Error generating invoice batch in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate invoice batch")
    
    # Invoice Submission Endpoints
    async def submit_invoice(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Submit invoice to FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="submit_invoice",
                payload={
                    "submission_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_submitted")
        except Exception as e:
            logger.error(f"Error submitting invoice in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit invoice")
    
    async def submit_invoice_batch(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Submit invoice batch to FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="submit_invoice_batch",
                payload={
                    "batch_submission_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_batch_submitted")
        except Exception as e:
            logger.error(f"Error submitting invoice batch in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit invoice batch")
    
    # Submission Status Endpoints
    async def get_submission_status(self, submission_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get submission status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_submission_status",
                payload={
                    "submission_id": submission_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "submission_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting submission status {submission_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get submission status")
    
    async def list_submissions(self, 
                             request: Request,
                             status: Optional[str] = Query(None, description="Filter by submission status"),
                             taxpayer_id: Optional[str] = Query(None, description="Filter by taxpayer"),
                             start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                             end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                             context: HTTPRoutingContext = Depends(lambda: None)):
        """List invoice submissions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_submissions",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "status": status,
                        "taxpayer_id": taxpayer_id,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "submissions_listed")
        except Exception as e:
            logger.error(f"Error listing submissions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list submissions")
    
    # Invoice Management Endpoints
    async def get_invoice(self, invoice_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get invoice details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_invoice",
                payload={
                    "invoice_id": invoice_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            return self._create_v1_response(result, "invoice_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting invoice {invoice_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get invoice")
    
    async def cancel_invoice_submission(self, invoice_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Cancel invoice submission"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="cancel_invoice_submission",
                payload={
                    "invoice_id": invoice_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_submission_cancelled")
        except Exception as e:
            logger.error(f"Error cancelling invoice submission {invoice_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to cancel invoice submission")
    
    async def resubmit_invoice(self, invoice_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Resubmit invoice"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="resubmit_invoice",
                payload={
                    "invoice_id": invoice_id,
                    "resubmission_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_resubmitted")
        except Exception as e:
            logger.error(f"Error resubmitting invoice {invoice_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to resubmit invoice")
    
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


def create_invoice_submission_router(role_detector: HTTPRoleDetector,
                                    permission_guard: APIPermissionGuard,
                                    message_router: MessageRouter) -> APIRouter:
    """Factory function to create Invoice Submission Router"""
    invoice_endpoints = InvoiceSubmissionEndpointsV1(role_detector, permission_guard, message_router)
    return invoice_endpoints.router