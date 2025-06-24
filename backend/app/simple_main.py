"""
Minimal FastAPI application for Railway deployment debugging.
This version strips away complex dependencies to isolate deployment issues.
"""

import os
import sys
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TaxPoynt eInvoice API (Minimal)",
    description="Minimal version for Railway deployment debugging",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "TaxPoynt eInvoice API is running", "status": "ok"}

@app.get("/health")
async def health():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "taxpoynt-backend",
        "environment": os.environ.get("RAILWAY_ENVIRONMENT", "unknown"),
        "port": os.environ.get("PORT", "8000")
    }

@app.get("/api/v1/health/ready")
async def ready():
    """Railway readiness probe"""
    return {
        "status": "ready",
        "service": "taxpoynt-backend-minimal",
        "deployment_id": os.environ.get("RAILWAY_DEPLOYMENT_ID", "unknown")
    }

@app.get("/debug")
async def debug():
    """Debug information"""
    return {
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "environment_vars": {
            "PORT": os.environ.get("PORT"),
            "RAILWAY_ENVIRONMENT": os.environ.get("RAILWAY_ENVIRONMENT"),
            "DATABASE_URL_exists": bool(os.environ.get("DATABASE_URL")),
            "SECRET_KEY_exists": bool(os.environ.get("SECRET_KEY"))
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")