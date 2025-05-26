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
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        on_startup=[start_background_tasks]  # Start background tasks on startup
    )
    logger.info("FastAPI application initialized successfully")
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

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}

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

try:
    # Feature routers - group 1
    app.include_router(validation.router, prefix=f"{settings.API_V1_STR}/validation", tags=["validation"])
    app.include_router(crypto.router, prefix=f"{settings.API_V1_STR}/crypto", tags=["crypto"])
    app.include_router(firs.router, prefix=settings.API_V1_STR, tags=["firs"])
    app.include_router(integrations.router, prefix=f"{settings.API_V1_STR}/integrations", tags=["integrations"])
    app.include_router(api_credentials.router, prefix=f"{settings.API_V1_STR}/api-credentials", tags=["api-credentials"])
    app.include_router(organization.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organizations"])
    logger.info("Successfully included feature routers - group 1")
except Exception as e:
    logger.critical(f"FATAL ERROR including feature routers - group 1: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

try:
    # Feature routers - group 2
    app.include_router(bulk_irn.router, prefix=f"{settings.API_V1_STR}/bulk-irn", tags=["bulk-irn"])
    app.include_router(validation_management.router, prefix=f"{settings.API_V1_STR}/validation-management", tags=["validation-management"])
    app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
    app.include_router(odoo_ubl.router, prefix=f"{settings.API_V1_STR}/odoo-ubl", tags=["odoo-ubl"])
    logger.info("Successfully included feature routers - group 2")
except Exception as e:
    logger.critical(f"FATAL ERROR including feature routers - group 2: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

try:
    # Feature routers - group 3 (FIRS submission related)
    app.include_router(firs_submission.router, prefix=f"{settings.API_V1_STR}/firs-submission", tags=["firs-submission"])
    app.include_router(submission_webhook.router, prefix=f"{settings.API_V1_STR}/webhook", tags=["webhook"])
    app.include_router(retry_management.router, prefix=f"{settings.API_V1_STR}/retry", tags=["retry"])
    app.include_router(submission_dashboard.router, prefix=f"{settings.API_V1_STR}/submission-dashboard", tags=["submission-dashboard"])
    app.include_router(integration_status.router, prefix=f"{settings.API_V1_STR}/integration", tags=["integration-status"])
    logger.info("Successfully included feature routers - group 3")
except Exception as e:
    logger.critical(f"FATAL ERROR including feature routers - group 3: {str(e)}")
    logger.critical(traceback.format_exc())
    raise

# Import and include the new FIRS API router with error handling
try:
    logger.info("Importing FIRS API router...")
    from app.routers.firs import router as firs_api_router
    app.include_router(firs_api_router, prefix=settings.API_V1_STR, tags=["firs-api"])
    logger.info("Successfully included FIRS API router")
except Exception as e:
    logger.critical(f"FATAL ERROR including FIRS API router: {str(e)}")
    logger.critical(traceback.format_exc())
    raise
logger.info("FIRS API router initialized")

logger.info("All routers initialized successfully")
logger.info("Application setup complete and ready to serve requests")

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
