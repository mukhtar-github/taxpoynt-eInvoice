#!/usr/bin/env python3
"""
Simplified Railway startup script for TaxPoynt Backend.
Designed specifically to resolve Railway health check issues.
"""

import os
import sys
import logging
import time

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("railway_start")

def main():
    """Main startup function."""
    try:
        logger.info("=== TaxPoynt Railway Startup ===")
        
        # Get Railway configuration
        port = int(os.environ.get("PORT", 8000))
        host = "0.0.0.0"
        
        logger.info(f"Starting server on {host}:{port}")
        
        # Import and start the application
        import uvicorn
        from app.main import app
        
        # Railway-optimized Uvicorn configuration
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=1,  # Single worker for Railway
            timeout_keep_alive=300,
            access_log=True,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()