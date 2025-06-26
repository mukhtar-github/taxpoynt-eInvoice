"""
Main FastAPI application module for FIRS e-Invoice system.

This module initializes the FastAPI application with:
- TLS configuration
- CORS middleware
- All routers
- Exception handlers
"""

import os
import sys
from pathlib import Path
from typing import List
import logging
import traceback

# Configure logging first - before any imports that might use it
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level to capture more information
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Ensure logs go to stdout for Railway
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Log startup information
logger.info(f"Starting TaxPoynt eInvoice backend application")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")

from fastapi import FastAPI, Request, HTTPException, Depends # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore

# Import routers with error handling
try:
    from app.routers import crypto
    logger.info("Successfully imported crypto router")
except Exception as e:
    logger.critical(f"FATAL ERROR importing crypto router: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

# Import each route module separately with error handling
try:
    from app.routes import auth
    logger.info("Successfully imported auth routes")
except Exception as e:
    logger.critical(f"FATAL ERROR importing auth routes: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

try:
    from app.routes import api_keys
    logger.info("Successfully imported api_keys routes")
except Exception as e:
    logger.critical(f"FATAL ERROR importing api_keys routes: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

try:
    from app.routes import irn
    logger.info("Successfully imported irn routes")
except Exception as e:
    logger.critical(f"FATAL ERROR importing irn routes: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

try:
    from app.routes import validation, firs, integrations, api_credentials, bulk_irn, validation_management, organization
    from app.routes import organization_integrations, organization_odoo, crm_integrations, queue_monitoring, advanced_crm_features
    logger.info("Successfully imported primary feature routes")
except Exception as e:
    logger.critical(f"FATAL ERROR importing primary feature routes: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

try:
    from app.routes import dashboard, odoo_ubl, firs_submission, submission_webhook, retry_management, submission_dashboard, integration_status
    logger.info("Successfully imported secondary feature routes")
except Exception as e:
    logger.critical(f"FATAL ERROR importing secondary feature routes: {str(e)}")
    logger.critical(traceback.format_exc())
    raise
from app.core.config import settings
from app.core.config_retry import retry_settings
from app.services.background_tasks import start_background_tasks
from app.dependencies.auth import get_current_user_from_token # type: ignore
from app.middleware import setup_middleware

# Log critical environment variables (without sensitive values)
try:
    logger.info(f"Environment: DATABASE_URL={'set' if os.environ.get('DATABASE_URL') else 'not set'}")
    logger.info(f"Environment: PORT={'set' if os.environ.get('PORT') else 'not set'}")
    logger.info(f"Environment: DEBUG={'set' if os.environ.get('DEBUG') else 'not set'}")
except Exception as e:
    logger.error(f"Error checking environment variables: {str(e)}")

# Log settings information
try:
    logger.info(f"API_V1_STR: {settings.API_V1_STR}")
    logger.info(f"PROJECT_NAME: {settings.PROJECT_NAME}")
    logger.info(f"ENVIRONMENT: {settings.ENVIRONMENT}")
except Exception as e:
    logger.error(f"Error accessing settings: {str(e)}")
    logger.error(traceback.format_exc())

# Initialize FastAPI application with error handling
try:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="TaxPoynt eInvoice API for ERP integration and electronic invoice management",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        redirect_slashes=False,  # Disable redirects for Railway health checks
        contact={
            "name": "TaxPoynt Support",
            "url": "https://taxpoynt.com/support",
            "email": "support@taxpoynt.com",
        },
        license_info={
            "name": "Proprietary",
            "url": "https://taxpoynt.com/terms",
        },
        terms_of_service="https://taxpoynt.com/terms",
        openapi_tags=[
            {
                "name": "auth",
                "description": "Authentication and authorization operations",
            },
            {
                "name": "integrations",
                "description": "ERP integration management endpoints",
            },
            {
                "name": "crm-integrations",
                "description": "CRM integration management endpoints for deal processing and synchronization",
            },
            {
                "name": "queue-monitoring",
                "description": "Queue system monitoring and management endpoints for Celery task tracking",
            },
            {
                "name": "invoices",
                "description": "Electronic invoice operations", 
            },
            {
                "name": "organizations",
                "description": "Organization management endpoints",
            },
        ],
        on_startup=[start_background_tasks]  # Start background tasks on startup
    )
    logger.info("FastAPI application initialized successfully with enhanced OpenAPI documentation")
except Exception as e:
    logger.critical(f"FATAL ERROR initializing FastAPI application: {str(e)}")
    logger.critical(traceback.format_exc())
    # Re-raise to ensure the error is visible
    raise

# Set up all middleware (CORS, Rate limiting, API Key Auth, Security)
try:
    setup_middleware(app)
    logger.info("Security middleware initialized: CORS, Rate Limiting, API Key Auth, and HTTPS enforcement enabled")
except Exception as e:
    logger.critical(f"FATAL ERROR setting up middleware: {str(e)}")
    logger.critical(traceback.format_exc())
    # Re-raise to ensure the error is visible
    raise

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with custom format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Initialize cryptographic utilities
try:
    from app.utils import encryption, crypto_signing
    logger.info("Encryption and cryptographic signing utilities initialized")
except Exception as e:
    logger.warning(f"Error initializing encryption utilities: {str(e)}")

# Static files - for serving QR codes or other assets
# Static files have been moved to the frontend React application
# Only mount the static directory if it exists (for backward compatibility)
static_path = Path("static")
if static_path.exists() and static_path.is_dir():
    app.mount("/static", StaticFiles(directory=static_path), name="static")
else:
    logger.info("Static files directory not found - static file serving is disabled")
    # Create an empty static directory to prevent the error
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory=Path("static")), name="static")

# Unified health check system for Railway deployment and operational monitoring
try:
    from app.api.routes.health import router as unified_health_router
    app.include_router(unified_health_router, prefix="/api/v1/health", tags=["health"])
    logger.info("Successfully included unified health check system")
except Exception as e:
    logger.warning(f"Could not include unified health router: {str(e)} - using fallback health checks")
    
    # Fallback basic health checks
    @app.get("/health")
    def basic_health_check():
        """Fallback basic health check endpoint."""
        from datetime import datetime
        return {
            "status": "healthy",
            "service": "taxpoynt-backend",
            "timestamp": datetime.now().isoformat(),
            "fallback": True
        }

    @app.get("/ready")
    def basic_ready_check():
        """Fallback readiness check."""
        from datetime import datetime
        return {
            "status": "ready",
            "service": "taxpoynt-backend",
            "timestamp": datetime.now().isoformat(),
            "fallback": True
        }

# Debug endpoint for enum verification
@app.get("/debug/enums")
def debug_enum_values():
    """Debug endpoint to verify enum configuration"""
    from datetime import datetime
    import sys
    from app.models.crm_connection import CRMType
    from app.models.pos_connection import POSType
    
    return {
        "timestamp": datetime.now().isoformat(),
        "enum_debug": {
            "crm_type_names": [e.name for e in CRMType],
            "crm_type_values": [e.value for e in CRMType],
            "pos_type_names": [e.name for e in POSType], 
            "pos_type_values": [e.value for e in POSType],
        },
        "cache_status": {
            "pythondontwritebytecode": os.environ.get('PYTHONDONTWRITEBYTECODE'),
            "nixpacks_no_cache": os.environ.get('NIXPACKS_NO_CACHE'),
            "debug_enums": os.environ.get('DEBUG_ENUMS'),
        },
        "modules_loaded": len(sys.modules),
        "deployment_verification": "SUCCESS"
    }

# Include routers with error handling
try:
    # Authentication and security routers
    app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
    logger.info("Successfully included auth router")
    
    app.include_router(api_keys.router, prefix=settings.API_V1_STR, tags=["api-keys"])
    logger.info("Successfully included api_keys router")
    
    # IRN router - this had issues previously
    app.include_router(irn.router, prefix=f"{settings.API_V1_STR}/irn", tags=["irn"])
    logger.info("Successfully included irn router")
except Exception as e:
    logger.critical(f"FATAL ERROR including core routers: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

# Note: Detailed health checks are now part of the unified health system above

try:    
    # POS real-time processing router
    from app.api.routes.pos_realtime import router as pos_realtime_router
    app.include_router(pos_realtime_router, prefix=f"{settings.API_V1_STR}/pos", tags=["pos-realtime"])
    logger.info("Successfully included POS real-time router")
except Exception as e:
    logger.warning(f"Could not include POS real-time router: {str(e)}")

try:
    # Feature routers - group 1
    app.include_router(validation.router, prefix=f"{settings.API_V1_STR}/validation", tags=["validation"])
    app.include_router(crypto.router, prefix=f"{settings.API_V1_STR}/crypto", tags=["crypto"])
    app.include_router(firs.router, prefix=settings.API_V1_STR, tags=["firs"])
    logger.info("Successfully included core feature routers")
except Exception as e:
    logger.warning(f"Could not include core feature routers: {str(e)}")

try:
    app.include_router(integrations.router, prefix=f"{settings.API_V1_STR}/integrations", tags=["integrations"])
    logger.info("Successfully included integrations router")
except Exception as e:
    logger.warning(f"Could not include integrations router: {str(e)}")

try:
    app.include_router(crm_integrations.router, prefix=f"{settings.API_V1_STR}/integrations", tags=["crm-integrations"])
    logger.info("Successfully included CRM integrations router")
except Exception as e:
    logger.warning(f"Could not include CRM integrations router: {str(e)}")

try:
    app.include_router(advanced_crm_features.router, prefix=settings.API_V1_STR, tags=["advanced-crm-features"])
    logger.info("Successfully included Advanced CRM Features router")
except Exception as e:
    logger.warning(f"Could not include Advanced CRM Features router: {str(e)}")

try:
    app.include_router(queue_monitoring.router, prefix=f"{settings.API_V1_STR}/monitoring", tags=["queue-monitoring"])
    app.include_router(api_credentials.router, prefix=f"{settings.API_V1_STR}/api-credentials", tags=["api-credentials"])
    app.include_router(organization.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organizations"])
    app.include_router(organization_integrations.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organization-integrations"])
    app.include_router(organization_odoo.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organization-odoo"])
    logger.info("Successfully included remaining routers")
except Exception as e:
    logger.warning(f"Could not include some routers: {str(e)}")

try:
    # Feature routers - group 2
    app.include_router(bulk_irn.router, prefix=f"{settings.API_V1_STR}/bulk-irn", tags=["bulk-irn"])
    app.include_router(validation_management.router, prefix=f"{settings.API_V1_STR}/validation-management", tags=["validation-management"])
    app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
    app.include_router(odoo_ubl.router, prefix=f"{settings.API_V1_STR}/odoo-ubl", tags=["odoo-ubl"])
    logger.info("Successfully included feature routers - group 2")
except Exception as e:
    logger.warning(f"Could not include feature routers - group 2: {str(e)}")

try:
    # Feature routers - group 3 (FIRS submission related)
    app.include_router(firs_submission.router, prefix=f"{settings.API_V1_STR}/firs-submission", tags=["firs-submission"])
    app.include_router(submission_webhook.router, prefix=f"{settings.API_V1_STR}/webhook", tags=["webhook"])
    app.include_router(retry_management.router, prefix=f"{settings.API_V1_STR}/retry", tags=["retry"])
    app.include_router(submission_dashboard.router, prefix=f"{settings.API_V1_STR}/submission-dashboard", tags=["submission-dashboard"])
    app.include_router(integration_status.router, prefix=f"{settings.API_V1_STR}/integration", tags=["integration-status"])
    logger.info("Successfully included feature routers - group 3")
except Exception as e:
    logger.warning(f"Could not include feature routers - group 3: {str(e)}")

try:
    # POS webhook routers
    from app.routes import pos_webhooks
    app.include_router(pos_webhooks.router, prefix=settings.API_V1_STR, tags=["pos-webhooks"])
    logger.info("Successfully included POS webhook router")
except Exception as e:
    logger.warning(f"Could not include POS webhook router: {str(e)}")

# Import and include the new FIRS API router with error handling
try:
    logger.info("Importing FIRS API router...")
    from app.routers.firs import router as firs_api_router
    app.include_router(firs_api_router, prefix=settings.API_V1_STR, tags=["firs-api"])
    logger.info("Successfully included FIRS API router")
except Exception as e:
    logger.warning(f"Could not include FIRS API router: {str(e)}")

# Import and include APP functionality routers with error handling
try:
    logger.info("Importing APP functionality routers...")
    from app.routes.certificate_requests import router as certificate_requests_router
    from app.routes.csid import router as csid_router
    from app.routes.transmissions import router as transmissions_router
    from app.routes.certificates import router as certificates_router
    
    # Include APP-related routers
    app.include_router(certificates_router, prefix=settings.API_V1_STR, tags=["certificates"])
    app.include_router(certificate_requests_router, prefix=settings.API_V1_STR, tags=["certificate-requests"])
    app.include_router(csid_router, prefix=settings.API_V1_STR, tags=["csids"])
    app.include_router(transmissions_router, prefix=settings.API_V1_STR, tags=["transmissions"])
    
    logger.info("Successfully included APP functionality routers")
except Exception as e:
    logger.warning(f"Could not include APP functionality routers: {str(e)}")
    logger.warning("APP functionality may not be available")
    # Don't raise exception here to allow the application to start even if APP features are not available
    # This follows the graceful failure approach used in the multi-step database migration strategy

# Include WebSocket routes for real-time dashboard
try:
    from app.routes import websocket_routes
    app.include_router(websocket_routes.router, prefix=settings.API_V1_STR, tags=["websocket"])
    logger.info("Successfully included WebSocket routes for real-time dashboard")
except Exception as e:
    logger.warning(f"Error including WebSocket routes: {str(e)}")
    logger.warning("Real-time WebSocket functionality may not be available")

# Include Nigerian Compliance router
try:
    from app.routes.nigerian_compliance import router as nigerian_compliance_router
    app.include_router(nigerian_compliance_router, prefix=settings.API_V1_STR, tags=["nigerian-compliance"])
    logger.info("Successfully included Nigerian compliance router")
except Exception as e:
    logger.warning(f"Could not include Nigerian compliance router: {str(e)}")

# Include Service Access Management router
try:
    from app.routes.service_access_management import router as service_access_router
    app.include_router(service_access_router, prefix=settings.API_V1_STR, tags=["service-access"])
    logger.info("Successfully included Service Access Management router")
except Exception as e:
    logger.warning(f"Could not include Service Access Management router: {str(e)}")

logger.info("All routers initialized successfully")
logger.info("Application setup complete and ready to serve requests")

# Start the retry scheduler service in background mode
try:
    from app.services.retry_scheduler import RetryScheduler
    
    # Start the retry scheduler with default settings
    retry_scheduler = RetryScheduler()
    scheduler_thread = retry_scheduler.start_background_scheduler()
    logger.info("Transmission retry scheduler started successfully in background mode")
except Exception as e:
    logger.error(f"Failed to start retry scheduler service: {str(e)}")
    logger.error(traceback.format_exc())
    logger.warning("Automatic transmission retries will not be available")
    # Don't raise the exception to allow the application to start
    # even if the retry scheduler is not available

# Final health check to ensure everything is loaded correctly
try:
    # Check that all essential components are available
    logger.info("Performing final application health check...")
    # Add explicit object checks to verify critical components
    assert app is not None, "FastAPI app is not initialized"
    assert auth.router is not None, "Auth router is not available"
    assert irn.router is not None, "IRN router is not available"
    logger.info("Final application health check passed successfully")
except Exception as e:
    logger.critical(f"FATAL ERROR in final application health check: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

if __name__ == "__main__":
    try:
        import uvicorn
        logger.info("Starting uvicorn server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.critical(f"FATAL ERROR starting uvicorn server: {str(e)}")
        logger.critical(traceback.format_exc())
        raise
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "False").lower() in ("true", "1", "t")
    
    # Configure SSL context with TLS 1.2+
    ssl_context = None
    if settings.CLIENT_KEY_PATH and settings.CLIENT_CERT_PATH:
        # Create SSL context with minimum TLS version 1.2
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Set minimum TLS version (TLS 1.2)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Set secure cipher suites
        ssl_context.set_ciphers(settings.TLS_CIPHERS)
        
        # Load certificate and key
        ssl_context.load_cert_chain(
            certfile=settings.CLIENT_CERT_PATH,
            keyfile=settings.CLIENT_KEY_PATH
        )
        
        logger.info(f"TLS {settings.TLS_VERSION}+ enabled with secure cipher suites")
    
    logger.info(f"Starting server on {host}:{port} with secure configuration")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        ssl_keyfile=settings.CLIENT_KEY_PATH if not ssl_context else None,
        ssl_certfile=settings.CLIENT_CERT_PATH if not ssl_context else None,
        ssl=ssl_context,
    )
