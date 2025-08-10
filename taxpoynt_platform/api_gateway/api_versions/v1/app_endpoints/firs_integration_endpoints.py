"""
FIRS Integration Endpoints - API v1
===================================
Access Point Provider endpoints for direct FIRS system integration.
Handles communication with FIRS e-invoicing infrastructure.
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


class FIRSIntegrationEndpointsV1:
    """
    FIRS Integration Endpoints - Version 1
    ======================================
    Manages direct integration with FIRS e-invoicing systems:
    
    **FIRS Integration Features:**
    - **Authentication**: FIRS API authentication and token management
    - **Invoice Submission**: Submit invoices directly to FIRS systems
    - **Status Tracking**: Track invoice processing status in FIRS
    - **Compliance Validation**: Validate invoices against FIRS rules
    - **Certificate Management**: Handle FIRS certificates and credentials
    - **System Health**: Monitor FIRS system availability and performance
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/firs", tags=["FIRS Integration V1"])
        
        # Define FIRS integration capabilities
        self.firs_capabilities = {
            "authentication": {
                "features": ["oauth2_flow", "token_management", "certificate_auth"],
                "description": "FIRS API authentication and credential management"
            },
            "invoice_submission": {
                "features": ["individual_submission", "batch_submission", "real_time_processing"],
                "description": "Submit invoices to FIRS e-invoicing systems"
            },
            "validation": {
                "features": ["schema_validation", "business_rules", "compliance_check"],
                "description": "Validate invoices against FIRS requirements"
            },
            "tracking": {
                "features": ["submission_status", "processing_status", "error_tracking"],
                "description": "Track invoice processing in FIRS systems"
            }
        }
        
        self._setup_routes()
        logger.info("FIRS Integration Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup FIRS integration routes"""
        
        # FIRS System Information
        self.router.add_api_route(
            "/system/info",
            self.get_firs_system_info,
            methods=["GET"],
            summary="Get FIRS system information",
            description="Get FIRS e-invoicing system information and capabilities",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/system/health",
            self.check_firs_system_health,
            methods=["GET"],
            summary="Check FIRS system health",
            description="Check FIRS system availability and performance",
            response_model=V1ResponseModel
        )
        
        # FIRS Authentication Routes
        self.router.add_api_route(
            "/auth/authenticate",
            self.authenticate_with_firs,
            methods=["POST"],
            summary="Authenticate with FIRS",
            description="Authenticate TaxPoynt APP with FIRS systems",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/auth/refresh-token",
            self.refresh_firs_token,
            methods=["POST"],
            summary="Refresh FIRS authentication token",
            description="Refresh authentication token for FIRS integration",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/auth/status",
            self.get_firs_auth_status,
            methods=["GET"],
            summary="Get FIRS authentication status",
            description="Get current FIRS authentication status and token validity",
            response_model=V1ResponseModel
        )
        
        # Invoice Submission Routes
        self.router.add_api_route(
            "/invoices/submit",
            self.submit_invoice_to_firs,
            methods=["POST"],
            summary="Submit invoice to FIRS",
            description="Submit individual invoice to FIRS e-invoicing system",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/invoices/submit-batch",
            self.submit_invoice_batch_to_firs,
            methods=["POST"],
            summary="Submit invoice batch to FIRS",
            description="Submit multiple invoices to FIRS in a single batch",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/invoices/{submission_id}/status",
            self.get_firs_submission_status,
            methods=["GET"],
            summary="Get FIRS submission status",
            description="Get processing status of invoice submission in FIRS",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/invoices/submissions",
            self.list_firs_submissions,
            methods=["GET"],
            summary="List FIRS submissions",
            description="List all invoice submissions to FIRS",
            response_model=V1ResponseModel
        )
        
        # Invoice Validation Routes
        self.router.add_api_route(
            "/validation/validate-invoice",
            self.validate_invoice_for_firs,
            methods=["POST"],
            summary="Validate invoice for FIRS",
            description="Validate invoice against FIRS compliance rules",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/validation/validate-batch",
            self.validate_invoice_batch_for_firs,
            methods=["POST"],
            summary="Validate invoice batch for FIRS",
            description="Validate multiple invoices against FIRS compliance rules",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/validation/rules",
            self.get_firs_validation_rules,
            methods=["GET"],
            summary="Get FIRS validation rules",
            description="Get current FIRS validation rules and compliance requirements",
            response_model=V1ResponseModel
        )
        
        # Certificate Management Routes
        self.router.add_api_route(
            "/certificates/list",
            self.list_firs_certificates,
            methods=["GET"],
            summary="List FIRS certificates",
            description="List all FIRS certificates and their status",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/certificates/{certificate_id}",
            self.get_firs_certificate,
            methods=["GET"],
            summary="Get FIRS certificate",
            description="Get specific FIRS certificate details",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/certificates/renew/{certificate_id}",
            self.renew_firs_certificate,
            methods=["POST"],
            summary="Renew FIRS certificate",
            description="Renew expiring FIRS certificate",
            response_model=V1ResponseModel
        )
        
        # Error and Log Management Routes
        self.router.add_api_route(
            "/errors/list",
            self.get_firs_errors,
            methods=["GET"],
            summary="Get FIRS integration errors",
            description="Get errors from FIRS integration attempts",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/logs/integration",
            self.get_firs_integration_logs,
            methods=["GET"],
            summary="Get FIRS integration logs",
            description="Get logs from FIRS integration activities",
            response_model=V1ResponseModel
        )
    
    # FIRS System Information Endpoints
    async def get_firs_system_info(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS system information"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_system_info",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            # Add capabilities information
            result["capabilities"] = self.firs_capabilities
            
            return self._create_v1_response(result, "firs_system_info_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS system info in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS system info")
    
    async def check_firs_system_health(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Check FIRS system health"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="check_firs_system_health",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_system_health_checked")
        except Exception as e:
            logger.error(f"Error checking FIRS system health in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to check FIRS system health")
    
    # FIRS Authentication Endpoints
    async def authenticate_with_firs(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Authenticate with FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="authenticate_with_firs",
                payload={
                    "auth_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_authentication_completed")
        except Exception as e:
            logger.error(f"Error authenticating with FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to authenticate with FIRS")
    
    async def refresh_firs_token(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Refresh FIRS authentication token"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="refresh_firs_token",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_token_refreshed")
        except Exception as e:
            logger.error(f"Error refreshing FIRS token in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh FIRS token")
    
    async def get_firs_auth_status(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS authentication status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_auth_status",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_auth_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS auth status in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS auth status")
    
    # Invoice Submission Endpoints
    async def submit_invoice_to_firs(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Submit invoice to FIRS"""
        try:
            body = await request.json()
            
            # Validate required fields
            required_fields = ["invoice_data", "taxpayer_id"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="submit_invoice_to_firs",
                payload={
                    "submission_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_submitted_to_firs")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error submitting invoice to FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit invoice to FIRS")
    
    async def submit_invoice_batch_to_firs(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Submit invoice batch to FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="submit_invoice_batch_to_firs",
                payload={
                    "batch_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_batch_submitted_to_firs")
        except Exception as e:
            logger.error(f"Error submitting invoice batch to FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit invoice batch to FIRS")
    
    async def get_firs_submission_status(self, submission_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS submission status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_submission_status",
                payload={
                    "submission_id": submission_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_submission_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS submission status {submission_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS submission status")
    
    async def list_firs_submissions(self, 
                                  request: Request,
                                  status: Optional[str] = Query(None, description="Filter by submission status"),
                                  start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                                  end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                                  context: HTTPRoutingContext = Depends(lambda: None)):
        """List FIRS submissions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_firs_submissions",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "status": status,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_submissions_listed")
        except Exception as e:
            logger.error(f"Error listing FIRS submissions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list FIRS submissions")
    
    # Invoice Validation Endpoints
    async def validate_invoice_for_firs(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Validate invoice for FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_invoice_for_firs",
                payload={
                    "validation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_validated_for_firs")
        except Exception as e:
            logger.error(f"Error validating invoice for FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate invoice for FIRS")
    
    async def validate_invoice_batch_for_firs(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Validate invoice batch for FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_invoice_batch_for_firs",
                payload={
                    "batch_validation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_batch_validated_for_firs")
        except Exception as e:
            logger.error(f"Error validating invoice batch for FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate invoice batch for FIRS")
    
    async def get_firs_validation_rules(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS validation rules"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_validation_rules",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_validation_rules_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS validation rules in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS validation rules")
    
    # Certificate Management Endpoints
    async def list_firs_certificates(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """List FIRS certificates"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_firs_certificates",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_certificates_listed")
        except Exception as e:
            logger.error(f"Error listing FIRS certificates in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list FIRS certificates")
    
    async def get_firs_certificate(self, certificate_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS certificate"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_certificate",
                payload={
                    "certificate_id": certificate_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_certificate_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS certificate {certificate_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS certificate")
    
    async def renew_firs_certificate(self, certificate_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Renew FIRS certificate"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="renew_firs_certificate",
                payload={
                    "certificate_id": certificate_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_certificate_renewed")
        except Exception as e:
            logger.error(f"Error renewing FIRS certificate {certificate_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to renew FIRS certificate")
    
    # Error and Log Management Endpoints
    async def get_firs_errors(self, 
                            request: Request,
                            error_type: Optional[str] = Query(None, description="Filter by error type"),
                            start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                            end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                            context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS integration errors"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_errors",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "error_type": error_type,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_errors_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS errors in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS errors")
    
    async def get_firs_integration_logs(self, 
                                      request: Request,
                                      log_level: Optional[str] = Query(None, description="Filter by log level"),
                                      start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                                      end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                                      context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS integration logs"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_integration_logs",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "log_level": log_level,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_integration_logs_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS integration logs in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS integration logs")
    
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


def create_firs_integration_router(role_detector: HTTPRoleDetector,
                                  permission_guard: APIPermissionGuard,
                                  message_router: MessageRouter) -> APIRouter:
    """Factory function to create FIRS Integration Router"""
    firs_endpoints = FIRSIntegrationEndpointsV1(role_detector, permission_guard, message_router)
    return firs_endpoints.router