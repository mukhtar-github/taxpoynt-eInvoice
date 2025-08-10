"""
Organization Management Endpoints - API v1
==========================================
System Integrator endpoints for managing organizations and their business system connections.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from .....core_platform.authentication.role_manager import PlatformRole
from .....core_platform.messaging.message_router import ServiceRole, MessageRouter
from ....role_routing.models import HTTPRoutingContext
from ....role_routing.role_detector import HTTPRoleDetector
from ....role_routing.permission_guard import APIPermissionGuard
from .version_models import V1ResponseModel, V1ErrorModel, V1PaginationModel

logger = logging.getLogger(__name__)


class OrganizationEndpointsV1:
    """
    Organization Management Endpoints - Version 1
    =============================================
    Handles organization lifecycle management for System Integrators including:
    - Creating and managing organizations
    - Onboarding organizations to e-invoicing
    - Managing organization business system connections
    - Organization compliance status and reporting
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/organizations", tags=["Organizations V1"])
        self._setup_routes()
        
        logger.info("Organization Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup organization management routes"""
        
        # Core Organization CRUD
        self.router.add_api_route(
            "",
            self.list_organizations,
            methods=["GET"],
            summary="List managed organizations",
            description="Get paginated list of organizations managed by this SI",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "",
            self.create_organization,
            methods=["POST"],
            summary="Create new organization",
            description="Create and onboard a new organization for e-invoicing",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            "/{org_id}",
            self.get_organization,
            methods=["GET"],
            summary="Get organization details",
            description="Retrieve detailed information about a specific organization",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}",
            self.update_organization,
            methods=["PUT"],
            summary="Update organization",
            description="Update organization information and settings",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}",
            self.delete_organization,
            methods=["DELETE"],
            summary="Delete organization",
            description="Remove organization from SI management",
            response_model=V1ResponseModel
        )
        
        # Organization Business Systems
        self.router.add_api_route(
            "/{org_id}/business-systems",
            self.get_organization_business_systems,
            methods=["GET"],
            summary="Get organization's business systems",
            description="List all business systems connected to this organization",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}/business-systems/{system_type}",
            self.get_organization_business_system_by_type,
            methods=["GET"],
            summary="Get business systems by type",
            description="Get organization's business systems filtered by type (erp, crm, pos, etc.)",
            response_model=V1ResponseModel
        )
        
        # Organization Onboarding
        self.router.add_api_route(
            "/{org_id}/onboard",
            self.initiate_organization_onboarding,
            methods=["POST"],
            summary="Initiate organization onboarding",
            description="Start the e-invoicing onboarding process for an organization",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}/onboarding-status",
            self.get_onboarding_status,
            methods=["GET"],
            summary="Get onboarding status",
            description="Check the current onboarding progress for an organization",
            response_model=V1ResponseModel
        )
        
        # Organization Compliance
        self.router.add_api_route(
            "/{org_id}/compliance",
            self.get_organization_compliance,
            methods=["GET"],
            summary="Get organization compliance status",
            description="Retrieve compliance status and validation results",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}/validate-compliance",
            self.validate_organization_compliance,
            methods=["POST"],
            summary="Validate organization compliance",
            description="Run compliance validation checks for an organization",
            response_model=V1ResponseModel
        )
        
        # Organization Transactions
        self.router.add_api_route(
            "/{org_id}/transactions",
            self.get_organization_transactions,
            methods=["GET"],
            summary="Get organization transactions",
            description="Retrieve transactions for a specific organization",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}/transaction-summary",
            self.get_organization_transaction_summary,
            methods=["GET"],
            summary="Get transaction summary",
            description="Get aggregated transaction statistics for an organization",
            response_model=V1ResponseModel
        )
    
    async def list_organizations(self, 
                                request: Request,
                                page: int = Query(1, ge=1, description="Page number"),
                                limit: int = Query(50, ge=1, le=1000, description="Items per page"),
                                search: Optional[str] = Query(None, description="Search organizations"),
                                status: Optional[str] = Query(None, description="Filter by status"),
                                business_system: Optional[str] = Query(None, description="Filter by business system type"),
                                context: HTTPRoutingContext = Depends(lambda: None)):
        """List organizations managed by this SI"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_organizations",
                payload={
                    "si_id": context.user_id,
                    "pagination": {"page": page, "limit": limit},
                    "filters": {
                        "search": search,
                        "status": status,
                        "business_system": business_system
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organizations_listed")
        except Exception as e:
            logger.error(f"Error listing organizations in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list organizations")
    
    async def create_organization(self, 
                                 request: Request,
                                 context: HTTPRoutingContext = Depends(lambda: None)):
        """Create new organization"""
        try:
            body = await request.json()
            
            # Validate required fields for v1
            required_fields = ["name", "tax_id", "email", "phone", "address"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
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
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating organization in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to create organization")
    
    async def get_organization(self, 
                              org_id: str,
                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Get organization details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "include_business_systems": True,
                    "include_compliance_status": True,
                    "api_version": "v1"
                }
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Organization not found")
            
            return self._create_v1_response(result, "organization_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization")
    
    async def update_organization(self, 
                                 org_id: str,
                                 request: Request,
                                 context: HTTPRoutingContext = Depends(lambda: None)):
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
    
    async def delete_organization(self, 
                                 org_id: str,
                                 context: HTTPRoutingContext = Depends(lambda: None)):
        """Delete organization"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="delete_organization",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_deleted")
        except Exception as e:
            logger.error(f"Error deleting organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete organization")
    
    async def get_organization_business_systems(self, 
                                               org_id: str,
                                               context: HTTPRoutingContext = Depends(lambda: None)):
        """Get organization's business systems"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization_business_systems",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            # Add available system types for v1
            result["available_system_types"] = {
                "erp": ["sap", "oracle", "dynamics", "netsuite", "odoo"],
                "crm": ["salesforce", "hubspot", "dynamics_crm", "pipedrive", "zoho"],
                "pos": ["square", "clover", "lightspeed", "toast", "shopify_pos", "moniepoint", "opay", "palmpay"],
                "ecommerce": ["shopify", "woocommerce", "magento", "bigcommerce", "jumia"],
                "accounting": ["quickbooks", "xero", "wave", "freshbooks", "sage"],
                "inventory": ["cin7", "fishbowl", "tradegecko", "unleashed"]
            }
            
            return self._create_v1_response(result, "organization_business_systems_retrieved")
        except Exception as e:
            logger.error(f"Error getting organization business systems {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization business systems")
    
    async def get_organization_business_system_by_type(self, 
                                                      org_id: str,
                                                      system_type: str,
                                                      context: HTTPRoutingContext = Depends(lambda: None)):
        """Get organization's business systems by type"""
        try:
            # Validate system type
            valid_types = ["erp", "crm", "pos", "ecommerce", "accounting", "inventory"]
            if system_type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid system type. Must be one of: {', '.join(valid_types)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization_business_systems_by_type",
                payload={
                    "org_id": org_id,
                    "system_type": system_type,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, f"organization_{system_type}_systems_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting organization {system_type} systems {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get organization {system_type} systems")
    
    async def initiate_organization_onboarding(self, 
                                              org_id: str,
                                              request: Request,
                                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Initiate organization onboarding"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="initiate_organization_onboarding",
                payload={
                    "org_id": org_id,
                    "onboarding_config": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_onboarding_initiated")
        except Exception as e:
            logger.error(f"Error initiating onboarding for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to initiate organization onboarding")
    
    async def get_onboarding_status(self, 
                                   org_id: str,
                                   context: HTTPRoutingContext = Depends(lambda: None)):
        """Get onboarding status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization_onboarding_status",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting onboarding status for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get onboarding status")
    
    async def get_organization_compliance(self, 
                                         org_id: str,
                                         context: HTTPRoutingContext = Depends(lambda: None)):
        """Get organization compliance status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization_compliance",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_compliance_retrieved")
        except Exception as e:
            logger.error(f"Error getting compliance for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization compliance")
    
    async def validate_organization_compliance(self, 
                                              org_id: str,
                                              request: Request,
                                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Validate organization compliance"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="validate_organization_compliance",
                payload={
                    "org_id": org_id,
                    "validation_config": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating compliance for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate organization compliance")
    
    async def get_organization_transactions(self, 
                                           org_id: str,
                                           request: Request,
                                           context: HTTPRoutingContext = Depends(lambda: None)):
        """Get organization transactions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization_transactions",
                payload={
                    "org_id": org_id,
                    "filters": dict(request.query_params),
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_transactions_retrieved")
        except Exception as e:
            logger.error(f"Error getting transactions for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization transactions")
    
    async def get_organization_transaction_summary(self, 
                                                   org_id: str,
                                                   context: HTTPRoutingContext = Depends(lambda: None)):
        """Get organization transaction summary"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization_transaction_summary",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_transaction_summary_retrieved")
        except Exception as e:
            logger.error(f"Error getting transaction summary for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization transaction summary")
    
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


def create_organization_router(role_detector: HTTPRoleDetector,
                              permission_guard: APIPermissionGuard,
                              message_router: MessageRouter) -> APIRouter:
    """Factory function to create Organization Router"""
    org_endpoints = OrganizationEndpointsV1(role_detector, permission_guard, message_router)
    return org_endpoints.router