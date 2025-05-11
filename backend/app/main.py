"""
Main FastAPI application module for FIRS e-Invoice system.

This module initializes the FastAPI application with:
- TLS configuration
- CORS middleware
- All routers
- Exception handlers
"""

import os
from pathlib import Path
from typing import List
import logging

from fastapi import FastAPI, Request, HTTPException, Depends # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore

from app.routers import crypto
from app.routes import auth, api_keys, irn, validation, firs, integrations, api_credentials
from app.core.config import settings
from app.dependencies.auth import get_current_user_from_token # type: ignore
from app.middleware import setup_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up all middleware (CORS, Rate limiting, API Key Auth, Security)
setup_middleware(app)
logger.info("Security middleware initialized: CORS, Rate Limiting, API Key Auth, and HTTPS enforcement enabled")

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
app.mount("/static", StaticFiles(directory=Path("static")), name="static")

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(api_keys.router, prefix=settings.API_V1_STR, tags=["api-keys"])
app.include_router(irn.router, prefix=f"{settings.API_V1_STR}/irn", tags=["irn"])
app.include_router(validation.router, prefix=f"{settings.API_V1_STR}/validation", tags=["validation"])
app.include_router(crypto.router, prefix=f"{settings.API_V1_STR}/crypto", tags=["crypto"])
app.include_router(firs.router, prefix=settings.API_V1_STR, tags=["firs"])
app.include_router(integrations.router, prefix=settings.API_V1_STR, tags=["integrations"])
app.include_router(api_credentials.router, prefix=settings.API_V1_STR, tags=["api-credentials"])

if __name__ == "__main__":
    import uvicorn # type: ignore
    import ssl
    
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
