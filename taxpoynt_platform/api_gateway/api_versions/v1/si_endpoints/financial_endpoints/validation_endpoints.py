"""
Financial Validation Service Endpoints - API v1
===============================================
System Integrator endpoints for financial validation services.
Covers: BVN validation, KYC processing, Identity verification
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse

from ......core_platform.authentication.role_manager import PlatformRole
from ......core_platform.messaging.message_router import ServiceRole, MessageRouter
from .....role_routing.models import HTTPRoutingContext
from .....role_routing.role_detector import HTTPRoleDetector
from .....role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class ValidationEndpointsV1:
    """
    Financial Validation Service Endpoints - Version 1
    ==================================================
    Manages financial validation services for System Integrators:
    
    **Available Validation Services:**
    - **BVN Validation**: Bank Verification Number validation and verification
    - **KYC Processing**: Know Your Customer verification and compliance processing
    - **Identity Verification**: Customer identity validation and document verification
    - **Compliance Checking**: Financial compliance validation for Nigerian regulations
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/validation", tags=["Financial Validation V1"])
        
        # Define available validation services
        self.validation_services = {
            "bvn": {
                "services": ["bvn_validation", "bvn_lookup", "bvn_verification"],
                "description": "Bank Verification Number validation and verification",
                "features": ["individual_validation", "bulk_validation", "real_time_verification"]
            },
            "kyc": {
                "services": ["kyc_processing", "document_verification", "compliance_check"],
                "description": "Know Your Customer verification and compliance processing",
                "features": ["document_processing", "compliance_validation", "risk_assessment"]
            },
            "identity": {
                "services": ["identity_verification", "document_validation", "biometric_verification"],
                "description": "Customer identity validation and document verification",
                "features": ["id_verification", "document_authentication", "biometric_matching"]
            }
        }
        
        self._setup_routes()
        logger.info("Validation Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup validation service routes"""
        
        # Validation Services Overview
        self.router.add_api_route(
            "/available-services",
            self.get_available_validation_services,
            methods=["GET"],
            summary="Get available validation services",
            description="List all validation services available for integration",
            response_model=V1ResponseModel
        )
        
        # BVN Validation Routes
        self._setup_bvn_routes()
        
        # KYC Processing Routes
        self._setup_kyc_routes()
        
        # Identity Verification Routes
        self._setup_identity_routes()
        
        # Validation Health and Testing
        self.router.add_api_route(
            "/services/{service_id}/test",
            self.test_validation_service,
            methods=["POST"],
            summary="Test validation service",
            description="Test connectivity and authentication for a validation service",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/services/{service_id}/health",
            self.get_validation_service_health,
            methods=["GET"],
            summary="Get validation service health",
            description="Get detailed health status of a validation service",
            response_model=V1ResponseModel
        )
    
    def _setup_bvn_routes(self):
        """Setup BVN validation specific routes"""
        
        # Individual BVN Validation
        self.router.add_api_route(
            "/bvn/validate",
            self.validate_bvn,
            methods=["POST"],
            summary="Validate BVN",
            description="Validate Bank Verification Number",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/bvn/lookup",
            self.lookup_bvn,
            methods=["POST"],
            summary="Lookup BVN details",
            description="Lookup Bank Verification Number details",
            response_model=V1ResponseModel
        )
        
        # Bulk BVN Validation
        self.router.add_api_route(
            "/bvn/bulk-validate",
            self.bulk_validate_bvn,
            methods=["POST"],
            summary="Bulk validate BVNs",
            description="Validate multiple Bank Verification Numbers",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/bvn/bulk-lookup",
            self.bulk_lookup_bvn,
            methods=["POST"],
            summary="Bulk lookup BVNs",
            description="Lookup multiple Bank Verification Numbers",
            response_model=V1ResponseModel
        )
        
        # BVN Status and History
        self.router.add_api_route(
            "/bvn/validation-history",
            self.get_bvn_validation_history,
            methods=["GET"],
            summary="Get BVN validation history",
            description="Get history of BVN validations performed",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/bvn/validation/{validation_id}/status",
            self.get_bvn_validation_status,
            methods=["GET"],
            summary="Get BVN validation status",
            description="Get status of a specific BVN validation",
            response_model=V1ResponseModel
        )
    
    def _setup_kyc_routes(self):
        """Setup KYC processing specific routes"""
        
        # KYC Processing
        self.router.add_api_route(
            "/kyc/process",
            self.process_kyc,
            methods=["POST"],
            summary="Process KYC",
            description="Process Know Your Customer verification",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/kyc/process-bulk",
            self.process_bulk_kyc,
            methods=["POST"],
            summary="Process bulk KYC",
            description="Process multiple KYC verifications",
            response_model=V1ResponseModel
        )
        
        # Document Verification
        self.router.add_api_route(
            "/kyc/verify-document",
            self.verify_kyc_document,
            methods=["POST"],
            summary="Verify KYC document",
            description="Verify KYC document authenticity",
            response_model=V1ResponseModel
        )
        
        # KYC Status and Management
        self.router.add_api_route(
            "/kyc/status/{kyc_id}",
            self.get_kyc_status,
            methods=["GET"],
            summary="Get KYC status",
            description="Get KYC processing status",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/kyc/{kyc_id}",
            self.get_kyc_details,
            methods=["GET"],
            summary="Get KYC details",
            description="Get detailed KYC processing information",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/kyc/list",
            self.list_kyc_processes,
            methods=["GET"],
            summary="List KYC processes",
            description="List all KYC processes for the organization",
            response_model=V1ResponseModel
        )
        
        # Compliance Checking
        self.router.add_api_route(
            "/kyc/compliance-check",
            self.check_kyc_compliance,
            methods=["POST"],
            summary="Check KYC compliance",
            description="Check KYC compliance against Nigerian regulations",
            response_model=V1ResponseModel
        )
    
    def _setup_identity_routes(self):
        """Setup identity verification specific routes"""
        
        # Identity Verification
        self.router.add_api_route(
            "/identity/verify",
            self.verify_identity,
            methods=["POST"],
            summary="Verify identity",
            description="Verify customer identity information",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/identity/verify-bulk",
            self.verify_bulk_identity,
            methods=["POST"],
            summary="Verify bulk identities",
            description="Verify multiple customer identities",
            response_model=V1ResponseModel
        )
        
        # Document Validation
        self.router.add_api_route(
            "/identity/validate-document",
            self.validate_identity_document,
            methods=["POST"],
            summary="Validate identity document",
            description="Validate identity document authenticity",
            response_model=V1ResponseModel
        )
        
        # Biometric Verification
        self.router.add_api_route(
            "/identity/biometric-verify",
            self.verify_biometric,
            methods=["POST"],
            summary="Verify biometric",
            description="Verify biometric information",
            response_model=V1ResponseModel
        )
        
        # Identity Status and Management
        self.router.add_api_route(
            "/identity/verification/{verification_id}/status",
            self.get_identity_verification_status,
            methods=["GET"],
            summary="Get identity verification status",
            description="Get status of identity verification",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/identity/verification-history",
            self.get_identity_verification_history,
            methods=["GET"],
            summary="Get identity verification history",
            description="Get history of identity verifications performed",
            response_model=V1ResponseModel
        )
    
    # Validation Services Overview Endpoints
    async def get_available_validation_services(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get all available validation services"""
        try:            
            result = {
                "validation_services": self.validation_services,
                "totals": {
                    "bvn_services": len(self.validation_services["bvn"]["services"]),
                    "kyc_services": len(self.validation_services["kyc"]["services"]),
                    "identity_services": len(self.validation_services["identity"]["services"]),
                    "total_services": (len(self.validation_services["bvn"]["services"]) + 
                                     len(self.validation_services["kyc"]["services"]) +
                                     len(self.validation_services["identity"]["services"]))
                },
                "categories": ["bvn", "kyc", "identity"]
            }
            
            return self._create_v1_response(result, "available_validation_services_retrieved")
        except Exception as e:
            logger.error(f"Error getting available validation services in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get available validation services")
    
    # BVN Validation Endpoints
    async def validate_bvn(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Validate BVN"""
        try:
            body = await request.json()
            
            # Validate required fields
            required_fields = ["bvn"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="validate_bvn",
                payload={
                    "validation_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bvn_validated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating BVN in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate BVN")
    
    async def lookup_bvn(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Lookup BVN details"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="lookup_bvn",
                payload={
                    "lookup_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bvn_looked_up")
        except Exception as e:
            logger.error(f"Error looking up BVN in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to lookup BVN")
    
    async def bulk_validate_bvn(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Bulk validate BVNs"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="bulk_validate_bvn",
                payload={
                    "bulk_validation_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bulk_bvn_validation_initiated")
        except Exception as e:
            logger.error(f"Error bulk validating BVNs in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to bulk validate BVNs")
    
    async def bulk_lookup_bvn(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Bulk lookup BVNs"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="bulk_lookup_bvn",
                payload={
                    "bulk_lookup_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bulk_bvn_lookup_initiated")
        except Exception as e:
            logger.error(f"Error bulk looking up BVNs in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to bulk lookup BVNs")
    
    async def get_bvn_validation_history(self, 
                                       request: Request,
                                       start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                                       end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                                       context: HTTPRoutingContext = Depends(lambda: None)):
        """Get BVN validation history"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_bvn_validation_history",
                payload={
                    "si_id": context.user_id,
                    "filters": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bvn_validation_history_retrieved")
        except Exception as e:
            logger.error(f"Error getting BVN validation history in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get BVN validation history")
    
    async def get_bvn_validation_status(self, validation_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get BVN validation status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_bvn_validation_status",
                payload={
                    "validation_id": validation_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bvn_validation_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting BVN validation status {validation_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get BVN validation status")
    
    # KYC Processing Endpoints
    async def process_kyc(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Process KYC"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="process_kyc",
                payload={
                    "kyc_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "kyc_processing_initiated")
        except Exception as e:
            logger.error(f"Error processing KYC in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to process KYC")
    
    async def process_bulk_kyc(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Process bulk KYC"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="process_bulk_kyc",
                payload={
                    "bulk_kyc_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bulk_kyc_processing_initiated")
        except Exception as e:
            logger.error(f"Error processing bulk KYC in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to process bulk KYC")
    
    async def verify_kyc_document(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Verify KYC document"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="verify_kyc_document",
                payload={
                    "document_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "kyc_document_verified")
        except Exception as e:
            logger.error(f"Error verifying KYC document in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to verify KYC document")
    
    async def get_kyc_status(self, kyc_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get KYC status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_kyc_status",
                payload={
                    "kyc_id": kyc_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "kyc_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting KYC status {kyc_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get KYC status")
    
    async def get_kyc_details(self, kyc_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get KYC details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_kyc_details",
                payload={
                    "kyc_id": kyc_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "kyc_details_retrieved")
        except Exception as e:
            logger.error(f"Error getting KYC details {kyc_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get KYC details")
    
    async def list_kyc_processes(self, 
                               request: Request,
                               status: Optional[str] = Query(None, description="Filter by status"),
                               context: HTTPRoutingContext = Depends(lambda: None)):
        """List KYC processes"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_kyc_processes",
                payload={
                    "si_id": context.user_id,
                    "filters": {
                        "status": status
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "kyc_processes_listed")
        except Exception as e:
            logger.error(f"Error listing KYC processes in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list KYC processes")
    
    async def check_kyc_compliance(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Check KYC compliance"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="check_kyc_compliance",
                payload={
                    "compliance_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "kyc_compliance_checked")
        except Exception as e:
            logger.error(f"Error checking KYC compliance in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to check KYC compliance")
    
    # Identity Verification Endpoints
    async def verify_identity(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Verify identity"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="verify_identity",
                payload={
                    "identity_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "identity_verified")
        except Exception as e:
            logger.error(f"Error verifying identity in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to verify identity")
    
    async def verify_bulk_identity(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Verify bulk identities"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="verify_bulk_identity",
                payload={
                    "bulk_identity_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bulk_identity_verification_initiated")
        except Exception as e:
            logger.error(f"Error verifying bulk identities in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to verify bulk identities")
    
    async def validate_identity_document(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Validate identity document"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="validate_identity_document",
                payload={
                    "document_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "identity_document_validated")
        except Exception as e:
            logger.error(f"Error validating identity document in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate identity document")
    
    async def verify_biometric(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Verify biometric"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="verify_biometric",
                payload={
                    "biometric_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "biometric_verified")
        except Exception as e:
            logger.error(f"Error verifying biometric in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to verify biometric")
    
    async def get_identity_verification_status(self, verification_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get identity verification status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_identity_verification_status",
                payload={
                    "verification_id": verification_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "identity_verification_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting identity verification status {verification_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get identity verification status")
    
    async def get_identity_verification_history(self, 
                                              request: Request,
                                              start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                                              end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Get identity verification history"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_identity_verification_history",
                payload={
                    "si_id": context.user_id,
                    "filters": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "identity_verification_history_retrieved")
        except Exception as e:
            logger.error(f"Error getting identity verification history in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get identity verification history")
    
    # Service Health Endpoints
    async def test_validation_service(self, service_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Test validation service"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="test_validation_service",
                payload={
                    "service_id": service_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "validation_service_tested")
        except Exception as e:
            logger.error(f"Error testing validation service {service_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to test validation service")
    
    async def get_validation_service_health(self, service_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get validation service health"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_validation_service_health",
                payload={
                    "service_id": service_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "validation_service_health_retrieved")
        except Exception as e:
            logger.error(f"Error getting validation service health {service_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get validation service health")
    
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


def create_validation_router(role_detector: HTTPRoleDetector,
                           permission_guard: APIPermissionGuard,
                           message_router: MessageRouter) -> APIRouter:
    """Factory function to create Validation Router"""
    validation_endpoints = ValidationEndpointsV1(role_detector, permission_guard, message_router)
    return validation_endpoints.router