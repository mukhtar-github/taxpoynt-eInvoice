"""
API Gateway Main Router
======================
Central API Gateway that integrates role-based routing with the existing message router
system to provide unified HTTP access to TaxPoynt platform services.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi

from ...core_platform.authentication.role_manager import RoleManager, PlatformRole
from ...core_platform.messaging.message_router import MessageRouter, ServiceRole
from .models import HTTPRoutingContext, APIGatewayConfig
from .role_detector import HTTPRoleDetector
from .permission_guard import APIPermissionGuard
from .si_router import create_si_router
from .app_router import create_app_router
from .hybrid_router import create_hybrid_router

logger = logging.getLogger(__name__)


class TaxPoyntAPIGateway:
    """
    TaxPoynt API Gateway
    ===================
    Central HTTP gateway that provides:
    - Role-based request routing to appropriate service layers
    - Integration with existing message router system
    - Unified authentication and authorization
    - Cross-role endpoint management
    - Comprehensive API documentation
    """
    
    def __init__(self, 
                 config: APIGatewayConfig,
                 role_manager: RoleManager,
                 message_router: MessageRouter):
        self.config = config
        self.role_manager = role_manager
        self.message_router = message_router
        
        # Initialize core components
        self.role_detector = HTTPRoleDetector(role_manager)
        self.permission_guard = APIPermissionGuard(config.security)
        
        # Create FastAPI app
        self.app = FastAPI(
            title="TaxPoynt E-Invoice Platform API",
            description="Comprehensive API for Nigerian e-invoicing compliance and business system integration",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json"
        )
        
        self._setup_middleware()
        self._setup_routers()
        self._setup_global_handlers()
        
        logger.info("TaxPoynt API Gateway initialized successfully")
    
    def _setup_middleware(self):
        """Configure FastAPI middleware"""
        
        # CORS middleware
        if self.config.cors_enabled:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.cors_origins,
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining"]
            )
        
        # Trusted host middleware
        if self.config.trusted_hosts:
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=self.config.trusted_hosts
            )
        
        # Custom middleware for request logging and monitoring
        @self.app.middleware("http")
        async def request_logging_middleware(request: Request, call_next):
            """Log requests and add request ID"""
            import uuid
            import time
            
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
            
            start_time = time.time()
            
            # Log incoming request
            logger.info(f"Request {request_id}: {request.method} {request.url}")
            
            try:
                response = await call_next(request)
                process_time = time.time() - start_time
                
                # Add headers
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time"] = str(process_time)
                
                # Log response
                logger.info(f"Request {request_id}: {response.status_code} ({process_time:.3f}s)")
                
                return response
            except Exception as e:
                process_time = time.time() - start_time
                logger.error(f"Request {request_id}: Error after {process_time:.3f}s - {e}")
                raise
    
    def _setup_routers(self):
        """Setup role-based routers"""
        
        # Create specialized routers
        si_router = create_si_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        
        app_router = create_app_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        
        hybrid_router = create_hybrid_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        
        # Include routers in main app
        self.app.include_router(
            si_router,
            prefix="/api/v1",
            tags=["System Integrator Services"]
        )
        
        self.app.include_router(
            app_router,
            prefix="/api/v1",
            tags=["Access Point Provider Services"]
        )
        
        self.app.include_router(
            hybrid_router,
            prefix="/api/v1",
            tags=["Hybrid Services"]
        )
        
        # Add root level routes
        self._setup_root_routes()
    
    def _setup_root_routes(self):
        """Setup root level API routes"""
        
        @self.app.get("/", summary="API Root")
        async def api_root():
            """API root endpoint with service information"""
            return JSONResponse(content={
                "service": "TaxPoynt E-Invoice Platform API",
                "version": "1.0.0",
                "status": "operational",
                "endpoints": {
                    "system_integrator": "/api/v1/si",
                    "access_point_provider": "/api/v1/app",
                    "hybrid_services": "/api/v1/common",
                    "documentation": "/docs",
                    "health": "/health"
                },
                "description": "Nigerian e-invoicing compliance and business system integration"
            })
        
        @self.app.get("/health", summary="Health Check")
        async def health_check():
            """Comprehensive health check"""
            try:
                # Check message router health
                router_health = await self._check_message_router_health()
                
                # Check role manager health
                role_manager_health = self._check_role_manager_health()
                
                # Overall health status
                all_healthy = router_health and role_manager_health
                
                return JSONResponse(
                    content={
                        "status": "healthy" if all_healthy else "degraded",
                        "timestamp": "2024-12-31T00:00:00Z",
                        "components": {
                            "api_gateway": "healthy",
                            "message_router": "healthy" if router_health else "unhealthy",
                            "role_manager": "healthy" if role_manager_health else "unhealthy"
                        },
                        "version": "1.0.0"
                    },
                    status_code=200 if all_healthy else 503
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse(
                    content={
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": "2024-12-31T00:00:00Z"
                    },
                    status_code=503
                )
        
        @self.app.get("/metrics", summary="API Metrics")
        async def get_metrics():
            """Get API gateway metrics"""
            try:
                # This would integrate with actual metrics collection
                return JSONResponse(content={
                    "requests_total": 0,
                    "requests_by_role": {
                        "system_integrator": 0,
                        "access_point_provider": 0,
                        "hybrid": 0
                    },
                    "response_times": {
                        "p50": 0.1,
                        "p95": 0.5,
                        "p99": 1.0
                    },
                    "error_rate": 0.01,
                    "active_connections": 0
                })
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail="Failed to get metrics")
    
    def _setup_global_handlers(self):
        """Setup global exception handlers"""
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTP exceptions"""
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.warning(f"HTTP Exception {request_id}: {exc.status_code} - {exc.detail}")
            
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "status_code": exc.status_code,
                    "request_id": request_id,
                    "timestamp": "2024-12-31T00:00:00Z"
                }
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle general exceptions"""
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.error(f"Unhandled Exception {request_id}: {exc}", exc_info=True)
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "timestamp": "2024-12-31T00:00:00Z"
                }
            )
    
    async def _check_message_router_health(self) -> bool:
        """Check message router health"""
        try:
            # Test message routing to each service role
            test_results = []
            
            for service_role in [ServiceRole.SYSTEM_INTEGRATOR, ServiceRole.ACCESS_POINT_PROVIDER]:
                try:
                    result = await self.message_router.route_message(
                        service_role=service_role,
                        operation="health_check",
                        payload={},
                        timeout=5.0
                    )
                    test_results.append(result is not None)
                except Exception as e:
                    logger.warning(f"Health check failed for {service_role}: {e}")
                    test_results.append(False)
            
            return all(test_results)
        except Exception as e:
            logger.error(f"Message router health check failed: {e}")
            return False
    
    def _check_role_manager_health(self) -> bool:
        """Check role manager health"""
        try:
            # Test role manager functionality
            test_roles = [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER]
            
            for role in test_roles:
                permissions = self.role_manager.get_role_permissions(role)
                if not permissions:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Role manager health check failed: {e}")
            return False
    
    def get_custom_openapi(self):
        """Generate custom OpenAPI schema with role-based documentation"""
        if self.app.openapi_schema:
            return self.app.openapi_schema
        
        openapi_schema = get_openapi(
            title="TaxPoynt E-Invoice Platform API",
            version="1.0.0",
            description="""
            ## TaxPoynt E-Invoice Platform API
            
            Comprehensive API for Nigerian e-invoicing compliance and business system integration.
            
            ### Role-Based Access
            
            This API provides role-specific endpoints:
            
            - **System Integrator (`/api/v1/si/`)**: ERP/CRM/POS integration, organization management
            - **Access Point Provider (`/api/v1/app/`)**: FIRS integration, taxpayer onboarding, compliance
            - **Hybrid Services (`/api/v1/common/`)**: Cross-role functionality, shared resources
            
            ### Authentication
            
            API uses role-based authentication with JWT tokens. Include your token in the Authorization header:
            ```
            Authorization: Bearer <your-jwt-token>
            ```
            
            ### Rate Limiting
            
            API requests are rate-limited based on user role and endpoint type.
            """,
            routes=self.app.routes,
        )
        
        # Add custom info
        openapi_schema["info"]["x-logo"] = {
            "url": "https://taxpoynt.com/logo.png",
            "altText": "TaxPoynt Logo"
        }
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for role-based authentication"
            }
        }
        
        # Add role-based tags
        openapi_schema["tags"] = [
            {
                "name": "System Integrator Services",
                "description": "ERP/CRM/POS integration and organization management"
            },
            {
                "name": "Access Point Provider Services", 
                "description": "FIRS integration, taxpayer onboarding, and compliance"
            },
            {
                "name": "Hybrid Services",
                "description": "Cross-role functionality and shared resources"
            }
        ]
        
        self.app.openapi_schema = openapi_schema
        return openapi_schema
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        # Set custom OpenAPI generator
        self.app.openapi = self.get_custom_openapi
        return self.app


def create_api_gateway(config: APIGatewayConfig,
                      role_manager: RoleManager,
                      message_router: MessageRouter) -> TaxPoyntAPIGateway:
    """Factory function to create API Gateway"""
    return TaxPoyntAPIGateway(config, role_manager, message_router)


def create_gateway_app(config: APIGatewayConfig,
                      role_manager: RoleManager, 
                      message_router: MessageRouter) -> FastAPI:
    """Factory function to create FastAPI app with API Gateway"""
    gateway = create_api_gateway(config, role_manager, message_router)
    return gateway.get_app()


# Example usage and configuration
if __name__ == "__main__":
    import uvicorn
    from ...core_platform.authentication.role_manager import create_role_manager
    from ...core_platform.messaging.message_router import create_message_router
    
    # Example configuration
    config = APIGatewayConfig(
        host="0.0.0.0",
        port=8000,
        cors_enabled=True,
        cors_origins=["http://localhost:3000", "https://taxpoynt.com"],
        trusted_hosts=["taxpoynt.com", "*.taxpoynt.com"],
        security=RoutingSecurityLevel.STRICT
    )
    
    # Create dependencies (these would be injected in real application)
    role_manager = create_role_manager()
    message_router = create_message_router()
    
    # Create app
    app = create_gateway_app(config, role_manager, message_router)
    
    # Run server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
        access_log=True
    )