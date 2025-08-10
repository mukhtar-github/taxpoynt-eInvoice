"""
HTTP Role Detector
=================
Detects and validates role context from HTTP requests by analyzing request patterns,
headers, authentication tokens, and endpoint paths.
"""
import logging
import re
import json
import base64
from typing import Dict, Any, List, Optional, Tuple, Set
from urllib.parse import urlparse, parse_qs
from fastapi import Request
from datetime import datetime, timezone

# Import from NEW architecture core components
from ...core_platform.authentication.role_manager import PlatformRole, RoleScope
from ...core_platform.messaging.message_router import ServiceRole

from .models import (
    HTTPRoutingContext, RequestAnalysis, RouteType, HTTPMethod,
    PermissionLevel
)

logger = logging.getLogger(__name__)


class HTTPRoleDetector:
    """
    Detects role context from HTTP requests using multiple analysis techniques:
    - Path pattern analysis
    - Authentication token inspection
    - Request header analysis  
    - Query parameter examination
    - Request body content analysis
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize role detection patterns (learned from existing architecture)
        self.si_patterns = self._initialize_si_patterns()
        self.app_patterns = self._initialize_app_patterns()
        self.hybrid_patterns = self._initialize_hybrid_patterns()
        self.admin_patterns = self._initialize_admin_patterns()
        
        # Authentication patterns
        self.auth_patterns = self._initialize_auth_patterns()
        
        # Permission mappings
        self.path_permissions = self._initialize_path_permissions()

    def _initialize_si_patterns(self) -> Dict[str, List[str]]:
        """Initialize SI (System Integrator) detection patterns."""
        return {
            "path_patterns": [
                r"/api/v\d+/si/.*",
                r"/api/v\d+/integration/.*",
                r"/api/v\d+/erp/.*",
                r"/api/v\d+/certificates/.*",
                r"/api/v\d+/schemas/.*",
                r"/api/v\d+/validation/.*",
                r"/api/v\d+/transformation/.*",
                r"/api/v\d+/sync/.*",
                r"/api/v\d+/mapping/.*",
                r"/api/v\d+/irn/generate.*",
                r"/api/v\d+/document/.*",
                r"/api/v\d+/compliance/check.*"
            ],
            "service_indicators": [
                "erp_integration", "certificate_management", "schema_compliance",
                "data_extraction", "document_processing", "transformation",
                "irn_generation", "qr_generation", "validation_service"
            ],
            "header_patterns": [
                "X-SI-Integration-Type",
                "X-ERP-System", 
                "X-Certificate-ID",
                "X-Schema-Version",
                "X-IRN-Request",
                "X-SI-Service"
            ],
            "query_params": [
                "integration_type", "erp_system", "schema_version",
                "certificate_id", "irn_mode", "validation_type"
            ]
        }

    def _initialize_app_patterns(self) -> Dict[str, List[str]]:
        """Initialize APP (Access Point Provider) detection patterns."""
        return {
            "path_patterns": [
                r"/api/v\d+/app/.*",
                r"/api/v\d+/transmission/.*",
                r"/api/v\d+/firs/.*",
                r"/api/v\d+/submit/.*",
                r"/api/v\d+/status/.*",
                r"/api/v\d+/acknowledgment/.*",
                r"/api/v\d+/webhooks/.*",
                r"/api/v\d+/notifications/.*",
                r"/api/v\d+/reports/.*",
                r"/api/v\d+/taxpayer/.*",
                r"/api/v\d+/onboarding/.*",
                r"/api/v\d+/security/.*"
            ],
            "service_indicators": [
                "transmission", "firs_communication", "status_management",
                "webhook_services", "reporting", "taxpayer_management",
                "authentication_seals", "security_compliance"
            ],
            "header_patterns": [
                "X-APP-Service",
                "X-FIRS-Token",
                "X-Transmission-ID",
                "X-Taxpayer-ID",
                "X-Submission-ID",
                "X-Webhook-ID",
                "X-APP-Authentication"
            ],
            "query_params": [
                "taxpayer_id", "submission_id", "transmission_id",
                "webhook_id", "status_type", "report_type"
            ]
        }

    def _initialize_hybrid_patterns(self) -> Dict[str, List[str]]:
        """Initialize Hybrid service detection patterns."""
        return {
            "path_patterns": [
                r"/api/v\d+/hybrid/.*",
                r"/api/v\d+/analytics/.*",
                r"/api/v\d+/billing/.*",
                r"/api/v\d+/compliance/cross.*",
                r"/api/v\d+/configuration/.*",
                r"/api/v\d+/workflow/.*",
                r"/api/v\d+/orchestration/.*",
                r"/api/v\d+/monitoring/.*",
                r"/api/v\d+/health/.*"
            ],
            "service_indicators": [
                "analytics_aggregation", "billing_orchestration",
                "compliance_coordination", "configuration_management",
                "workflow_orchestration", "data_synchronization",
                "error_management", "service_access_control"
            ],
            "header_patterns": [
                "X-Hybrid-Service",
                "X-Cross-Role",
                "X-Analytics-Query",
                "X-Billing-Context",
                "X-Workflow-ID",
                "X-Configuration-Scope"
            ],
            "query_params": [
                "cross_role", "analytics_type", "billing_context",
                "workflow_id", "config_scope", "orchestration_type"
            ]
        }

    def _initialize_admin_patterns(self) -> Dict[str, List[str]]:
        """Initialize administrative endpoint patterns."""
        return {
            "path_patterns": [
                r"/api/v\d+/admin/.*",
                r"/api/v\d+/platform/.*",
                r"/api/v\d+/tenants/.*",
                r"/api/v\d+/users/.*",
                r"/api/v\d+/roles/.*",
                r"/api/v\d+/permissions/.*",
                r"/api/v\d+/system/.*"
            ],
            "service_indicators": [
                "user_management", "tenant_management", "role_management",
                "permission_management", "system_administration"
            ],
            "header_patterns": [
                "X-Admin-Token",
                "X-Platform-Admin",
                "X-System-Role",
                "X-Tenant-Admin"
            ]
        }

    def _initialize_auth_patterns(self) -> Dict[str, Any]:
        """Initialize authentication detection patterns."""
        return {
            "jwt_prefixes": ["Bearer ", "JWT ", "Token "],
            "api_key_headers": [
                "X-API-Key", "X-Api-Key", "API-Key", "Authorization",
                "X-SI-API-Key", "X-APP-API-Key", "X-Platform-Key"
            ],
            "session_indicators": [
                "session_id", "sessionid", "X-Session-ID", "X-Session-Token"
            ],
            "certificate_headers": [
                "X-Client-Certificate", "X-SSL-Client-Cert", "X-Certificate-ID"
            ]
        }

    def _initialize_path_permissions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize path-based permission mappings."""
        return {
            # SI-specific permissions
            "/api/v*/integration/**": {
                "required_roles": [PlatformRole.SYSTEM_INTEGRATOR],
                "permissions": ["integration:read", "integration:write"],
                "route_type": RouteType.SI_ONLY
            },
            "/api/v*/certificates/**": {
                "required_roles": [PlatformRole.SYSTEM_INTEGRATOR],
                "permissions": ["certificates:manage"],
                "route_type": RouteType.SI_ONLY
            },
            
            # APP-specific permissions
            "/api/v*/transmission/**": {
                "required_roles": [PlatformRole.ACCESS_POINT_PROVIDER],
                "permissions": ["transmission:execute"],
                "route_type": RouteType.APP_ONLY
            },
            "/api/v*/firs/**": {
                "required_roles": [PlatformRole.ACCESS_POINT_PROVIDER],
                "permissions": ["firs:communicate"],
                "route_type": RouteType.APP_ONLY
            },
            
            # Hybrid permissions
            "/api/v*/analytics/**": {
                "required_roles": [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER],
                "permissions": ["analytics:read"],
                "route_type": RouteType.HYBRID
            },
            
            # Admin permissions
            "/api/v*/admin/**": {
                "required_roles": [PlatformRole.PLATFORM_ADMIN],
                "permissions": ["admin:full"],
                "route_type": RouteType.ADMIN
            }
        }

    async def analyze_request(self, request: Request) -> RequestAnalysis:
        """
        Analyze HTTP request to detect role context and requirements.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            RequestAnalysis with detected roles and requirements
        """
        try:
            self.logger.debug(f"Analyzing request: {request.method} {request.url.path}")
            
            analysis = RequestAnalysis(
                request_path=str(request.url.path),
                http_method=HTTPMethod(request.method)
            )
            
            # Analyze different aspects of the request
            await self._analyze_path_patterns(request, analysis)
            await self._analyze_headers(request, analysis)
            await self._analyze_query_parameters(request, analysis)
            await self._analyze_authentication(request, analysis)
            await self._analyze_request_body(request, analysis)
            
            # Determine final role detection
            await self._finalize_role_detection(analysis)
            
            # Calculate confidence score
            analysis.confidence_score = self._calculate_confidence_score(analysis)
            
            self.logger.debug(f"Request analysis complete: roles={[r.value for r in analysis.detected_roles]}, confidence={analysis.confidence_score}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing request: {str(e)}")
            # Return default analysis with low confidence
            return RequestAnalysis(
                request_path=str(request.url.path),
                http_method=HTTPMethod(request.method),
                confidence_score=0.0,
                security_flags=["analysis_error"]
            )

    async def detect_role_context(self, request: Request) -> HTTPRoutingContext:
        """
        Detect and create HTTP routing context from request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            HTTPRoutingContext with detected role information
        """
        try:
            # Perform request analysis
            analysis = await self.analyze_request(request)
            
            # Extract authentication information
            auth_info = await self._extract_authentication_info(request)
            
            # Create routing context
            context = HTTPRoutingContext(
                user_id=auth_info.get("user_id"),
                organization_id=auth_info.get("organization_id"),
                tenant_id=auth_info.get("tenant_id"),
                session_id=auth_info.get("session_id"),
                api_key=auth_info.get("api_key"),
                client_ip=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                correlation_id=request.headers.get("x-correlation-id") or request.headers.get("x-request-id")
            )
            
            # Set detected roles
            if analysis.detected_roles:
                context.platform_role = analysis.detected_roles[0]  # Primary role
                
                # Map platform role to service role
                context.service_role = self._map_platform_to_service_role(context.platform_role)
            
            # Set permissions based on analysis
            context.permissions = analysis.required_permissions.copy()
            
            # Add metadata from analysis
            context.metadata.update({
                "analysis_id": analysis.analysis_id,
                "confidence_score": analysis.confidence_score,
                "route_type": analysis.route_type.value if analysis.route_type else None,
                "si_indicators": analysis.si_indicators,
                "app_indicators": analysis.app_indicators,
                "hybrid_indicators": analysis.hybrid_indicators,
                "security_flags": analysis.security_flags,
                "risk_score": analysis.risk_score
            })
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error detecting role context: {str(e)}")
            raise

    async def _analyze_path_patterns(self, request: Request, analysis: RequestAnalysis):
        """Analyze URL path patterns for role indicators."""
        path = str(request.url.path)
        
        # Check SI patterns
        for pattern in self.si_patterns["path_patterns"]:
            if re.match(pattern, path, re.IGNORECASE):
                analysis.si_indicators.append(f"path_match:{pattern}")
                if PlatformRole.SYSTEM_INTEGRATOR not in analysis.detected_roles:
                    analysis.detected_roles.append(PlatformRole.SYSTEM_INTEGRATOR)
        
        # Check APP patterns
        for pattern in self.app_patterns["path_patterns"]:
            if re.match(pattern, path, re.IGNORECASE):
                analysis.app_indicators.append(f"path_match:{pattern}")
                if PlatformRole.ACCESS_POINT_PROVIDER not in analysis.detected_roles:
                    analysis.detected_roles.append(PlatformRole.ACCESS_POINT_PROVIDER)
        
        # Check Hybrid patterns
        for pattern in self.hybrid_patterns["path_patterns"]:
            if re.match(pattern, path, re.IGNORECASE):
                analysis.hybrid_indicators.append(f"path_match:{pattern}")
                if PlatformRole.HYBRID not in analysis.detected_roles:
                    analysis.detected_roles.append(PlatformRole.HYBRID)
        
        # Check Admin patterns
        for pattern in self.admin_patterns["path_patterns"]:
            if re.match(pattern, path, re.IGNORECASE):
                analysis.hybrid_indicators.append(f"admin_path_match:{pattern}")
                if PlatformRole.PLATFORM_ADMIN not in analysis.detected_roles:
                    analysis.detected_roles.append(PlatformRole.PLATFORM_ADMIN)
        
        # Determine permissions based on path
        for path_pattern, config in self.path_permissions.items():
            # Convert glob pattern to regex
            regex_pattern = path_pattern.replace("*", ".*").replace("**", ".*")
            if re.match(regex_pattern, path, re.IGNORECASE):
                analysis.required_permissions.extend(config.get("permissions", []))
                analysis.route_type = config.get("route_type")

    async def _analyze_headers(self, request: Request, analysis: RequestAnalysis):
        """Analyze request headers for role indicators."""
        headers = dict(request.headers)
        
        # Check SI headers
        for header in self.si_patterns["header_patterns"]:
            if header.lower() in [h.lower() for h in headers.keys()]:
                analysis.si_indicators.append(f"header:{header}")
        
        # Check APP headers
        for header in self.app_patterns["header_patterns"]:
            if header.lower() in [h.lower() for h in headers.keys()]:
                analysis.app_indicators.append(f"header:{header}")
        
        # Check Hybrid headers
        for header in self.hybrid_patterns["header_patterns"]:
            if header.lower() in [h.lower() for h in headers.keys()]:
                analysis.hybrid_indicators.append(f"header:{header}")
        
        # Analyze specific role headers
        if "x-user-role" in headers:
            role_value = headers["x-user-role"].lower()
            if "si" in role_value or "system_integrator" in role_value:
                analysis.si_indicators.append("explicit_role_header:si")
            elif "app" in role_value or "access_point" in role_value:
                analysis.app_indicators.append("explicit_role_header:app")
            elif "hybrid" in role_value:
                analysis.hybrid_indicators.append("explicit_role_header:hybrid")

    async def _analyze_query_parameters(self, request: Request, analysis: RequestAnalysis):
        """Analyze query parameters for role indicators."""
        query_params = dict(request.query_params)
        
        # Check SI parameters
        for param in self.si_patterns["query_params"]:
            if param in query_params:
                analysis.si_indicators.append(f"query_param:{param}")
        
        # Check APP parameters
        for param in self.app_patterns["query_params"]:
            if param in query_params:
                analysis.app_indicators.append(f"query_param:{param}")
        
        # Check Hybrid parameters
        for param in self.hybrid_patterns["query_params"]:
            if param in query_params:
                analysis.hybrid_indicators.append(f"query_param:{param}")

    async def _analyze_authentication(self, request: Request, analysis: RequestAnalysis):
        """Analyze authentication information for role indicators."""
        auth_header = request.headers.get("authorization", "")
        
        if auth_header:
            analysis.has_authentication = True
            
            # Check for JWT tokens
            for prefix in self.auth_patterns["jwt_prefixes"]:
                if auth_header.startswith(prefix):
                    analysis.authentication_method = "jwt"
                    token = auth_header[len(prefix):]
                    await self._analyze_jwt_token(token, analysis)
                    break
            else:
                # Check for API keys
                analysis.authentication_method = "api_key"
        
        # Check for API key headers
        for header in self.auth_patterns["api_key_headers"]:
            if header.lower() in request.headers:
                analysis.has_authentication = True
                if not analysis.authentication_method:
                    analysis.authentication_method = "api_key"
                
                # Analyze API key for role indicators
                api_key = request.headers[header]
                await self._analyze_api_key(api_key, analysis)

    async def _analyze_jwt_token(self, token: str, analysis: RequestAnalysis):
        """Analyze JWT token for role information."""
        try:
            # Decode JWT payload (without verification for role detection)
            parts = token.split('.')
            if len(parts) >= 2:
                # Add padding if needed
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)
                
                decoded = base64.b64decode(payload)
                claims = json.loads(decoded)
                
                # Extract role information from claims
                if "role" in claims:
                    role = claims["role"].lower()
                    if "si" in role or "system_integrator" in role:
                        analysis.si_indicators.append("jwt_role:si")
                    elif "app" in role or "access_point" in role:
                        analysis.app_indicators.append("jwt_role:app")
                    elif "hybrid" in role:
                        analysis.hybrid_indicators.append("jwt_role:hybrid")
                
                # Extract permissions
                if "permissions" in claims:
                    analysis.required_permissions.extend(claims["permissions"])
                
                # Extract organization context
                if "org_id" in claims:
                    analysis.analysis_metadata["organization_id"] = claims["org_id"]
                
        except Exception as e:
            self.logger.warning(f"Error analyzing JWT token: {str(e)}")
            analysis.security_flags.append("jwt_decode_error")

    async def _analyze_api_key(self, api_key: str, analysis: RequestAnalysis):
        """Analyze API key for role indicators."""
        # Check API key prefixes/patterns that might indicate roles
        if api_key.startswith("si_"):
            analysis.si_indicators.append("api_key_prefix:si")
        elif api_key.startswith("app_"):
            analysis.app_indicators.append("api_key_prefix:app")
        elif api_key.startswith("hybrid_"):
            analysis.hybrid_indicators.append("api_key_prefix:hybrid")

    async def _analyze_request_body(self, request: Request, analysis: RequestAnalysis):
        """Analyze request body for role indicators."""
        try:
            content_type = request.headers.get("content-type", "")
            analysis.content_type = content_type
            
            # Only analyze if JSON content
            if "application/json" in content_type:
                # Note: In practice, you'd need to carefully handle body reading
                # as it can only be read once in FastAPI
                pass
                
        except Exception as e:
            self.logger.warning(f"Error analyzing request body: {str(e)}")

    async def _finalize_role_detection(self, analysis: RequestAnalysis):
        """Finalize role detection based on all indicators."""
        # Count indicators for each role type
        si_score = len(analysis.si_indicators)
        app_score = len(analysis.app_indicators)
        hybrid_score = len(analysis.hybrid_indicators)
        
        # Clear detected roles and re-determine based on scores
        analysis.detected_roles.clear()
        
        # Determine primary roles based on indicator scores
        if hybrid_score > 0:
            analysis.detected_roles.append(PlatformRole.HYBRID)
            analysis.route_type = RouteType.HYBRID
        
        if si_score > app_score and si_score > 0:
            if PlatformRole.SYSTEM_INTEGRATOR not in analysis.detected_roles:
                analysis.detected_roles.append(PlatformRole.SYSTEM_INTEGRATOR)
            if not analysis.route_type:
                analysis.route_type = RouteType.SI_ONLY
        elif app_score > 0:
            if PlatformRole.ACCESS_POINT_PROVIDER not in analysis.detected_roles:
                analysis.detected_roles.append(PlatformRole.ACCESS_POINT_PROVIDER)
            if not analysis.route_type:
                analysis.route_type = RouteType.APP_ONLY
        
        # Default to USER role if no specific role detected
        if not analysis.detected_roles:
            analysis.detected_roles.append(PlatformRole.USER)
            analysis.route_type = RouteType.PUBLIC

    def _calculate_confidence_score(self, analysis: RequestAnalysis) -> float:
        """Calculate confidence score for role detection."""
        total_indicators = len(analysis.si_indicators) + len(analysis.app_indicators) + len(analysis.hybrid_indicators)
        
        if total_indicators == 0:
            return 0.1  # Very low confidence
        
        # Base confidence on number and quality of indicators
        base_score = min(total_indicators * 0.2, 0.8)  # Max 0.8 from indicators
        
        # Boost for explicit role headers/tokens
        if analysis.has_authentication:
            base_score += 0.1
        
        # Boost for path pattern matches
        path_indicators = [i for i in (analysis.si_indicators + analysis.app_indicators + analysis.hybrid_indicators) 
                          if i.startswith("path_match")]
        if path_indicators:
            base_score += 0.1
        
        return min(base_score, 1.0)

    async def _extract_authentication_info(self, request: Request) -> Dict[str, Any]:
        """Extract authentication information from request."""
        auth_info = {}
        
        # Extract from headers
        auth_info["api_key"] = request.headers.get("x-api-key")
        auth_info["session_id"] = request.headers.get("x-session-id")
        auth_info["organization_id"] = request.headers.get("x-organization-id")
        auth_info["tenant_id"] = request.headers.get("x-tenant-id")
        auth_info["user_id"] = request.headers.get("x-user-id")
        
        return {k: v for k, v in auth_info.items() if v is not None}

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None

    def _map_platform_to_service_role(self, platform_role: PlatformRole) -> ServiceRole:
        """Map platform role to service role for message routing."""
        mapping = {
            PlatformRole.SYSTEM_INTEGRATOR: ServiceRole.SYSTEM_INTEGRATOR,
            PlatformRole.ACCESS_POINT_PROVIDER: ServiceRole.ACCESS_POINT_PROVIDER,
            PlatformRole.HYBRID: ServiceRole.HYBRID,
            PlatformRole.PLATFORM_ADMIN: ServiceRole.CORE,
            PlatformRole.TENANT_ADMIN: ServiceRole.CORE,
            PlatformRole.USER: ServiceRole.CORE
        }
        return mapping.get(platform_role, ServiceRole.CORE)