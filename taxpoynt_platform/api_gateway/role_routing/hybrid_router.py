"""
Hybrid Router
============
FastAPI router for cross-role endpoints that can be accessed by multiple roles
with different permission levels and functionality exposure.
"""
import logging
from typing import Dict, Any, List, Optional, Set, Union
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from ...core_platform.authentication.role_manager import PlatformRole, RoleScope
from ...core_platform.messaging.message_router import ServiceRole, MessageRouter
from .models import HTTPRoutingContext, RoleBasedRoute, RoutingSecurityLevel
from .role_detector import HTTPRoleDetector
from .permission_guard import APIPermissionGuard

logger = logging.getLogger(__name__)


class HybridServicesRouter:
    """
    Hybrid Services Router
    =====================
    Handles HTTP endpoints that can be accessed by multiple roles, providing
    role-appropriate functionality and data filtering:
    - Common health and status endpoints
    - Public API documentation and schemas
    - Cross-role collaboration endpoints
    - Shared resource access with role-based filtering
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/common", tags=["Hybrid Services"])
        self._setup_routes()
        
        logger.info("Hybrid Services Router initialized")
    
    def _setup_routes(self):
        """Configure all hybrid/cross-role route handlers"""
        
        # Public/Open Routes (no authentication required)
        self.router.add_api_route(
            "/health",
            self.public_health_check,
            methods=["GET"],
            summary="Public health check"
        )
        
        self.router.add_api_route(
            "/version",
            self.get_api_version,
            methods=["GET"],
            summary="Get API version information"
        )
        
        self.router.add_api_route(
            "/docs/schema",
            self.get_api_schema,
            methods=["GET"],
            summary="Get API schema documentation"
        )
        
        # Authenticated Cross-Role Routes
        self.router.add_api_route(
            "/profile",
            self.get_user_profile,
            methods=["GET"],
            summary="Get current user profile",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        self.router.add_api_route(
            "/profile",
            self.update_user_profile,
            methods=["PUT"],
            summary="Update user profile",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        self.router.add_api_route(
            "/notifications",
            self.get_notifications,
            methods=["GET"],
            summary="Get user notifications",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        self.router.add_api_route(
            "/notifications/{notification_id}/read",
            self.mark_notification_read,
            methods=["POST"],
            summary="Mark notification as read",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        # Cross-Role Collaboration Routes
        self.router.add_api_route(
            "/organizations/search",
            self.search_organizations,
            methods=["GET"],
            summary="Search organizations (role-filtered)",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        self.router.add_api_route(
            "/organizations/{org_id}/basic",
            self.get_organization_basic_info,
            methods=["GET"],
            summary="Get basic organization info (role-filtered)",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        self.router.add_api_route(
            "/transactions/summary",
            self.get_transaction_summary,
            methods=["GET"],
            summary="Get transaction summary (role-filtered)",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        # System Integration Routes (Multi-role)
        self.router.add_api_route(
            "/integrations/status",
            self.get_integrations_status,
            methods=["GET"],
            summary="Get integration status overview",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        self.router.add_api_route(
            "/integrations/health",
            self.check_integrations_health,
            methods=["GET"],
            summary="Check integration health",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        # Reporting Routes (Role-based data filtering)
        self.router.add_api_route(
            "/reports/dashboard",
            self.get_dashboard_data,
            methods=["GET"],
            summary="Get dashboard data (role-appropriate)",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        self.router.add_api_route(
            "/reports/export",
            self.export_report,
            methods=["POST"],
            summary="Export report (role-filtered)",
            dependencies=[Depends(self._require_authenticated)]
        )
        
        # Platform Administration (Admin-only)
        self.router.add_api_route(
            "/admin/system-status",
            self.get_system_status,
            methods=["GET"],
            summary="Get comprehensive system status",
            dependencies=[Depends(self._require_admin_role)]
        )
        
        self.router.add_api_route(
            "/admin/users",
            self.list_platform_users,
            methods=["GET"],
            summary="List platform users",
            dependencies=[Depends(self._require_admin_role)]
        )
        
        self.router.add_api_route(
            "/admin/audit-logs",
            self.get_audit_logs,
            methods=["GET"],
            summary="Get audit logs",
            dependencies=[Depends(self._require_admin_role)]
        )
    
    async def _require_authenticated(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure any authenticated role access"""
        context = await self.role_detector.detect_role_context(request)
        
        if not context.is_authenticated:
            logger.warning(f"Hybrid endpoint access denied - not authenticated")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Apply permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"common{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for hybrid endpoint"
            )
        
        return context
    
    async def _require_admin_role(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure Administrator role access"""
        context = await self.role_detector.detect_role_context(request)
        
        if not context.has_role(PlatformRole.ADMINISTRATOR):
            logger.warning(f"Admin endpoint access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator role required"
            )
        
        return context
    
    # Public Routes (No Authentication)
    async def public_health_check(self):
        """Public health check endpoint"""
        return JSONResponse(content={
            "status": "healthy",
            "service": "taxpoynt_platform",
            "version": "1.0.0",
            "timestamp": "2024-12-31T00:00:00Z"
        })
    
    async def get_api_version(self):
        """Get API version information"""
        return JSONResponse(content={
            "api_version": "v1",
            "platform_version": "1.0.0",
            "supported_roles": ["system_integrator", "access_point_provider", "administrator"],
            "documentation": "/docs",
            "status": "stable"
        })
    
    async def get_api_schema(self):
        """Get API schema documentation"""
        try:
            # This would typically return OpenAPI schema
            return JSONResponse(content={
                "openapi": "3.0.0",
                "info": {
                    "title": "TaxPoynt E-Invoice Platform API",
                    "version": "1.0.0",
                    "description": "Comprehensive API for TaxPoynt e-invoicing platform"
                },
                "paths": {
                    "/si/*": {"description": "System Integrator endpoints"},
                    "/app/*": {"description": "Access Point Provider endpoints"},
                    "/common/*": {"description": "Hybrid/Cross-role endpoints"}
                }
            })
        except Exception as e:
            logger.error(f"Error getting API schema: {e}")
            raise HTTPException(status_code=500, detail="Failed to get API schema")
    
    # Authenticated Cross-Role Routes
    async def get_user_profile(self, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Get current user profile"""
        try:
            # Route to appropriate service based on user role
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_user_profile",
                payload={"user_id": context.user_id, "role": context.primary_role}
            )
            
            # Filter profile data based on role
            filtered_result = self._filter_profile_data(result, context)
            return JSONResponse(content=filtered_result)
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user profile")
    
    async def update_user_profile(self, request: Request, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Update user profile"""
        try:
            body = await request.json()
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="update_user_profile",
                payload={"user_id": context.user_id, "updates": body, "role": context.primary_role}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            raise HTTPException(status_code=500, detail="Failed to update user profile")
    
    async def get_notifications(self, request: Request, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Get user notifications"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_notifications",
                payload={
                    "user_id": context.user_id, 
                    "role": context.primary_role,
                    "filters": request.query_params
                }
            )
            
            # Filter notifications based on role
            filtered_result = self._filter_notifications(result, context)
            return JSONResponse(content=filtered_result)
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            raise HTTPException(status_code=500, detail="Failed to get notifications")
    
    async def mark_notification_read(self, notification_id: str, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Mark notification as read"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="mark_notification_read",
                payload={
                    "notification_id": notification_id,
                    "user_id": context.user_id,
                    "role": context.primary_role
                }
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error marking notification read {notification_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to mark notification as read")
    
    # Cross-Role Collaboration Routes
    async def search_organizations(self, request: Request, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Search organizations with role-based filtering"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="search_organizations",
                payload={
                    "query": request.query_params.get("q", ""),
                    "filters": request.query_params,
                    "user_id": context.user_id,
                    "role": context.primary_role
                }
            )
            
            # Apply role-based filtering
            filtered_result = self._filter_organization_search(result, context)
            return JSONResponse(content=filtered_result)
        except Exception as e:
            logger.error(f"Error searching organizations: {e}")
            raise HTTPException(status_code=500, detail="Failed to search organizations")
    
    async def get_organization_basic_info(self, org_id: str, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Get basic organization info with role-based filtering"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_organization_basic_info",
                payload={
                    "org_id": org_id,
                    "user_id": context.user_id,
                    "role": context.primary_role
                }
            )
            
            # Filter based on role and permissions
            filtered_result = self._filter_organization_info(result, context)
            return JSONResponse(content=filtered_result)
        except Exception as e:
            logger.error(f"Error getting organization basic info {org_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization info")
    
    async def get_transaction_summary(self, request: Request, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Get transaction summary with role-appropriate filtering"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_transaction_summary",
                payload={
                    "user_id": context.user_id,
                    "role": context.primary_role,
                    "filters": request.query_params
                }
            )
            
            # Apply role-based data filtering
            filtered_result = self._filter_transaction_summary(result, context)
            return JSONResponse(content=filtered_result)
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get transaction summary")
    
    # System Integration Routes
    async def get_integrations_status(self, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Get integration status overview"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_integrations_status",
                payload={"user_id": context.user_id, "role": context.primary_role}
            )
            
            # Filter integration data based on role
            filtered_result = self._filter_integration_status(result, context)
            return JSONResponse(content=filtered_result)
        except Exception as e:
            logger.error(f"Error getting integrations status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get integrations status")
    
    async def check_integrations_health(self, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Check integration health"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="check_integrations_health",
                payload={"user_id": context.user_id, "role": context.primary_role}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error checking integrations health: {e}")
            raise HTTPException(status_code=500, detail="Failed to check integrations health")
    
    # Reporting Routes
    async def get_dashboard_data(self, request: Request, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Get dashboard data appropriate for user role"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_dashboard_data",
                payload={
                    "user_id": context.user_id,
                    "role": context.primary_role,
                    "filters": request.query_params
                }
            )
            
            # Customize dashboard based on role
            customized_result = self._customize_dashboard_data(result, context)
            return JSONResponse(content=customized_result)
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise HTTPException(status_code=500, detail="Failed to get dashboard data")
    
    async def export_report(self, request: Request, context: HTTPRoutingContext = Depends(_require_authenticated)):
        """Export report with role-based filtering"""
        try:
            body = await request.json()
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="export_report",
                payload={
                    "export_request": body,
                    "user_id": context.user_id,
                    "role": context.primary_role
                }
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            raise HTTPException(status_code=500, detail="Failed to export report")
    
    # Administrator Routes
    async def get_system_status(self, context: HTTPRoutingContext = Depends(_require_admin_role)):
        """Get comprehensive system status (admin only)"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ADMINISTRATOR,
                operation="get_system_status",
                payload={"admin_id": context.user_id}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get system status")
    
    async def list_platform_users(self, request: Request, context: HTTPRoutingContext = Depends(_require_admin_role)):
        """List platform users (admin only)"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ADMINISTRATOR,
                operation="list_platform_users",
                payload={"admin_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error listing platform users: {e}")
            raise HTTPException(status_code=500, detail="Failed to list platform users")
    
    async def get_audit_logs(self, request: Request, context: HTTPRoutingContext = Depends(_require_admin_role)):
        """Get audit logs (admin only)"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ADMINISTRATOR,
                operation="get_audit_logs",
                payload={"admin_id": context.user_id, "filters": request.query_params}
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            raise HTTPException(status_code=500, detail="Failed to get audit logs")
    
    # Helper Methods
    def _get_primary_service_role(self, context: HTTPRoutingContext) -> ServiceRole:
        """Map user role to appropriate service role"""
        if context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            return ServiceRole.SYSTEM_INTEGRATOR
        elif context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            return ServiceRole.ACCESS_POINT_PROVIDER
        elif context.has_role(PlatformRole.ADMINISTRATOR):
            return ServiceRole.ADMINISTRATOR
        else:
            return ServiceRole.SYSTEM_INTEGRATOR  # Default
    
    def _filter_profile_data(self, data: Dict[str, Any], context: HTTPRoutingContext) -> Dict[str, Any]:
        """Filter profile data based on user role"""
        if context.has_role(PlatformRole.ADMINISTRATOR):
            return data  # Admins see everything
        
        # Remove sensitive fields for non-admin users
        filtered = {k: v for k, v in data.items() 
                   if k not in ['internal_notes', 'admin_metadata', 'system_config']}
        return filtered
    
    def _filter_notifications(self, data: Dict[str, Any], context: HTTPRoutingContext) -> Dict[str, Any]:
        """Filter notifications based on user role"""
        if not data.get('notifications'):
            return data
        
        # Filter notifications by role relevance
        role_keywords = {
            PlatformRole.SYSTEM_INTEGRATOR: ['integration', 'organization', 'transaction'],
            PlatformRole.ACCESS_POINT_PROVIDER: ['firs', 'taxpayer', 'compliance', 'invoice'],
            PlatformRole.ADMINISTRATOR: ['system', 'user', 'audit', 'security']
        }
        
        relevant_keywords = role_keywords.get(context.primary_role, [])
        if relevant_keywords:
            filtered_notifications = [
                notif for notif in data['notifications']
                if any(keyword in notif.get('message', '').lower() for keyword in relevant_keywords)
            ]
            data['notifications'] = filtered_notifications
        
        return data
    
    def _filter_organization_search(self, data: Dict[str, Any], context: HTTPRoutingContext) -> Dict[str, Any]:
        """Filter organization search results based on user role and permissions"""
        if context.has_role(PlatformRole.ADMINISTRATOR):
            return data  # Admins see all organizations
        
        # Filter based on user's associated organizations
        user_org_access = context.metadata.get('organization_access', [])
        if data.get('organizations'):
            filtered_orgs = [
                org for org in data['organizations']
                if org.get('id') in user_org_access or context.user_id in org.get('accessible_by', [])
            ]
            data['organizations'] = filtered_orgs
        
        return data
    
    def _filter_organization_info(self, data: Dict[str, Any], context: HTTPRoutingContext) -> Dict[str, Any]:
        """Filter organization info based on role"""
        if context.has_role(PlatformRole.ADMINISTRATOR):
            return data
        
        # Remove sensitive organization data for non-admin users
        sensitive_fields = ['tax_details', 'financial_data', 'internal_notes', 'compliance_history']
        filtered = {k: v for k, v in data.items() if k not in sensitive_fields}
        return filtered
    
    def _filter_transaction_summary(self, data: Dict[str, Any], context: HTTPRoutingContext) -> Dict[str, Any]:
        """Filter transaction summary based on role"""
        if context.has_role(PlatformRole.ADMINISTRATOR):
            return data
        
        # SI sees transaction processing data, APP sees compliance data
        if context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            return {k: v for k, v in data.items() 
                   if k in ['processed_count', 'pending_count', 'error_count', 'processing_summary']}
        elif context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            return {k: v for k, v in data.items() 
                   if k in ['submitted_count', 'validated_count', 'compliance_summary', 'firs_status']}
        
        return data
    
    def _filter_integration_status(self, data: Dict[str, Any], context: HTTPRoutingContext) -> Dict[str, Any]:
        """Filter integration status based on role"""
        if context.has_role(PlatformRole.ADMINISTRATOR):
            return data
        
        # Show only relevant integrations for each role
        if context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            relevant_types = ['erp', 'crm', 'pos', 'ecommerce', 'accounting']
        elif context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            relevant_types = ['firs', 'compliance', 'validation', 'certification']
        else:
            relevant_types = []
        
        if data.get('integrations') and relevant_types:
            filtered_integrations = [
                integration for integration in data['integrations']
                if integration.get('type') in relevant_types
            ]
            data['integrations'] = filtered_integrations
        
        return data
    
    def _customize_dashboard_data(self, data: Dict[str, Any], context: HTTPRoutingContext) -> Dict[str, Any]:
        """Customize dashboard data based on user role"""
        if context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            # SI dashboard focuses on organization onboarding and transaction processing
            return {
                'widgets': ['organizations_summary', 'transactions_summary', 'integration_status'],
                'data': data,
                'role_specific': {
                    'recent_organizations': data.get('recent_organizations', []),
                    'processing_metrics': data.get('processing_metrics', {}),
                    'integration_health': data.get('integration_health', {})
                }
            }
        elif context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            # APP dashboard focuses on FIRS compliance and taxpayer management
            return {
                'widgets': ['taxpayers_summary', 'compliance_summary', 'firs_status'],
                'data': data,
                'role_specific': {
                    'recent_taxpayers': data.get('recent_taxpayers', []),
                    'compliance_metrics': data.get('compliance_metrics', {}),
                    'firs_connection': data.get('firs_connection', {})
                }
            }
        elif context.has_role(PlatformRole.ADMINISTRATOR):
            # Admin dashboard shows comprehensive system overview
            return {
                'widgets': ['system_health', 'user_metrics', 'audit_summary'],
                'data': data,
                'role_specific': {
                    'system_status': data.get('system_status', {}),
                    'user_activity': data.get('user_activity', {}),
                    'security_alerts': data.get('security_alerts', [])
                }
            }
        
        return data


def create_hybrid_router(role_detector: HTTPRoleDetector,
                        permission_guard: APIPermissionGuard,
                        message_router: MessageRouter) -> APIRouter:
    """Factory function to create Hybrid Services Router"""
    hybrid_router = HybridServicesRouter(role_detector, permission_guard, message_router)
    return hybrid_router.router