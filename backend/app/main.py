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
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware # type: ignore

from app.routers import crypto
from app.routes import auth, api_keys
from app.core.config import settings
from app.dependencies.auth import get_current_user_from_token # type: ignore
from app.middleware.rate_limit import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for TaxPoynt eInvoice system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Force HTTPS in production environments
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Add rate limiting middleware
async def identify_user(request: Request) -> str:
    """Extract user ID from request for rate limiting."""
    try:
        # Try to get user from token
        user = await get_current_user_from_token(request)
        if user:
            return str(user.id)
    except:
        pass
    return None

app.add_middleware(
    RateLimitMiddleware,
    identify_user_func=identify_user,
)

# Include routers
app.include_router(crypto.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Static files - for serving QR codes or other assets
app.mount("/static", StaticFiles(directory=Path("static")), name="static")

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn # type: ignore
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # In development, don't use HTTPS as it's handled by reverse proxy
    if os.getenv("ENVIRONMENT") == "development":
        uvicorn.run("app.main:app", host=host, port=port, reload=True)
    else:
        # For direct production deployment (not recommended - use a reverse proxy)
        ssl_keyfile = os.getenv("SSL_KEYFILE")
        ssl_certfile = os.getenv("SSL_CERTFILE")
        
        if ssl_keyfile and ssl_certfile:
            uvicorn.run(
                "app.main:app",
                host=host,
                port=port,
                ssl_keyfile=ssl_keyfile,
                ssl_certfile=ssl_certfile,
            )
        else:
            # No SSL files, rely on reverse proxy for TLS
            uvicorn.run("app.main:app", host=host, port=port)
