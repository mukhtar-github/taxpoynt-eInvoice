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

from fastapi import FastAPI, Request, HTTPException # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import JSONResponse # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware # type: ignore

from app.routers import crypto

# Initialize FastAPI app
app = FastAPI(
    title="TaxPoynt eInvoice",
    description="API for FIRS e-Invoice System Integration",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  # NextJS dev server
    "https://localhost",
    "https://localhost:3000",
]

# Add production origins in non-dev environments
if os.getenv("ENVIRONMENT") != "development":
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Force HTTPS in production environments
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Include routers
app.include_router(crypto.router)

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
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

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
