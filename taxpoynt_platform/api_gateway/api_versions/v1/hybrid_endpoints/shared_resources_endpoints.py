"""
Shared Resources Endpoints - API v1
===================================
Hybrid endpoints for shared resources accessible by multiple roles.
Handles common data, configurations, and utilities used across roles.
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
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class SharedResourcesEndpointsV1:
    """
    Shared Resources Endpoints - Version 1
    ======================================
    Manages shared resources accessible by multiple roles:
    
    **Shared Resource Categories:**
    - **Configuration Data**: Common configuration settings and parameters
    - **Reference Data**: Lookup tables, taxonomies, and reference information
    - **Template Resources**: Document templates and format definitions
    - **Cache Management**: Shared cache operations and invalidation
    - **File Storage**: Shared file upload, download, and management
    - **Notification Services**: Cross-role notification and messaging
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/shared", tags=["Shared Resources V1"])
        
        self._setup_routes()
        logger.info("Shared Resources Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup shared resource routes"""
        
        # Configuration Data Routes
        self.router.add_api_route(
            "/configuration/common",
            self.get_common_configuration,
            methods=["GET"],
            summary="Get common configuration",
            description="Get configuration settings shared across roles",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_shared_access)]
        )
        
        # Reference Data Routes
        self.router.add_api_route(
            "/reference/countries",
            self.get_country_reference,
            methods=["GET"],
            summary="Get country reference data",
            description="Get country codes and related reference information",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reference/currencies",
            self.get_currency_reference,
            methods=["GET"],
            summary="Get currency reference data",
            description="Get currency codes and exchange rate information",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reference/tax-codes",
            self.get_tax_code_reference,
            methods=["GET"],
            summary="Get tax code reference data",
            description="Get Nigerian tax codes and classifications",
            response_model=V1ResponseModel
        )
        
        # Template Resources Routes
        self.router.add_api_route(
            "/templates/invoice",
            self.get_invoice_templates,
            methods=["GET"],
            summary="Get invoice templates",
            description="Get available invoice templates and formats",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_shared_access)]
        )
        
        # Cache Management Routes
        self.router.add_api_route(
            "/cache/invalidate",
            self.invalidate_cache,
            methods=["POST"],
            summary="Invalidate shared cache",
            description="Invalidate shared cache entries",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_shared_access)]
        )
        
        # File Storage Routes
        self.router.add_api_route(
            "/files/upload",
            self.upload_shared_file,
            methods=["POST"],
            summary="Upload shared file",
            description="Upload file to shared storage",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_shared_access)]
        )
        
        self.router.add_api_route(
            "/files/{file_id}",
            self.get_shared_file,
            methods=["GET"],
            summary="Get shared file",
            description="Download file from shared storage",
            dependencies=[Depends(self._require_shared_access)]
        )
        
        # Notification Services Routes
        self.router.add_api_route(
            "/notifications/send",
            self.send_notification,
            methods=["POST"],
            summary="Send notification",
            description="Send notification to users across roles",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_shared_access)]
        )
    
    async def _require_shared_access(self, request: Request) -> HTTPRoutingContext:
        """Require shared resource access"""
        context = await self.role_detector.detect_role_context(request)
        
        # Allow access for SI, APP, or Admin roles
        allowed_roles = {
            PlatformRole.SYSTEM_INTEGRATOR,
            PlatformRole.ACCESS_POINT_PROVIDER,
            PlatformRole.ADMINISTRATOR
        }
        
        if not any(context.has_role(role) for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access requires System Integrator, Access Point Provider, or Administrator role"
            )
        
        return context
    
    # Configuration Data Endpoints
    async def get_common_configuration(self, context: HTTPRoutingContext = Depends(_require_shared_access)):
        """Get common configuration"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SHARED_RESOURCES,
                operation="get_common_configuration",
                payload={
                    "user_context": {
                        "user_id": context.user_id,
                        "roles": [role.value for role in context.roles]
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "common_configuration_retrieved")
        except Exception as e:
            logger.error(f"Error getting common configuration in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get common configuration")
    
    # Reference Data Endpoints
    async def get_country_reference(self):
        """Get country reference data"""
        try:
            # This could be cached reference data
            result = {
                "countries": [
                    {"code": "NG", "name": "Nigeria", "currency": "NGN"},
                    {"code": "US", "name": "United States", "currency": "USD"},
                    {"code": "GB", "name": "United Kingdom", "currency": "GBP"}
                    # ... more countries
                ],
                "total_countries": 195
            }
            
            return self._create_v1_response(result, "country_reference_retrieved")
        except Exception as e:
            logger.error(f"Error getting country reference in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get country reference")
    
    async def get_currency_reference(self):
        """Get currency reference data"""
        try:
            result = {
                "currencies": [
                    {"code": "NGN", "name": "Nigerian Naira", "symbol": "₦"},
                    {"code": "USD", "name": "US Dollar", "symbol": "$"},
                    {"code": "EUR", "name": "Euro", "symbol": "€"}
                    # ... more currencies
                ],
                "exchange_rates_last_updated": "2024-12-31T00:00:00Z"
            }
            
            return self._create_v1_response(result, "currency_reference_retrieved")
        except Exception as e:
            logger.error(f"Error getting currency reference in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get currency reference")
    
    async def get_tax_code_reference(self):
        """Get tax code reference data"""
        try:
            result = {
                "tax_codes": [
                    {"code": "VAT_7.5", "description": "Value Added Tax 7.5%", "rate": 0.075},
                    {"code": "WHT_5", "description": "Withholding Tax 5%", "rate": 0.05},
                    {"code": "ZERO_RATED", "description": "Zero Rated VAT", "rate": 0.0}
                    # ... more tax codes
                ],
                "last_updated": "2024-12-31T00:00:00Z"
            }
            
            return self._create_v1_response(result, "tax_code_reference_retrieved")
        except Exception as e:
            logger.error(f"Error getting tax code reference in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get tax code reference")
    
    # Placeholder implementations for remaining endpoints
    async def get_invoice_templates(self, context: HTTPRoutingContext = Depends(_require_shared_access)):
        """Get invoice templates - placeholder"""
        return self._create_v1_response({"templates": []}, "invoice_templates_retrieved")
    
    async def invalidate_cache(self, request: Request, context: HTTPRoutingContext = Depends(_require_shared_access)):
        """Invalidate cache - placeholder"""
        return self._create_v1_response({"cache_invalidated": True}, "cache_invalidated")
    
    async def upload_shared_file(self, request: Request, context: HTTPRoutingContext = Depends(_require_shared_access)):
        """Upload shared file - placeholder"""
        return self._create_v1_response({"file_id": "file_123"}, "shared_file_uploaded")
    
    async def get_shared_file(self, file_id: str, context: HTTPRoutingContext = Depends(_require_shared_access)):
        """Get shared file - placeholder"""
        return self._create_v1_response({"file_id": file_id}, "shared_file_retrieved")
    
    async def send_notification(self, request: Request, context: HTTPRoutingContext = Depends(_require_shared_access)):
        """Send notification - placeholder"""
        return self._create_v1_response({"notification_sent": True}, "notification_sent")
    
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


def create_shared_resources_router(role_detector: HTTPRoleDetector,
                                  permission_guard: APIPermissionGuard,
                                  message_router: MessageRouter) -> APIRouter:
    """Factory function to create Shared Resources Router"""
    shared_endpoints = SharedResourcesEndpointsV1(role_detector, permission_guard, message_router)
    return shared_endpoints.router