#!/usr/bin/env python3
"""
Railway-Optimized Startup Script for TaxPoynt Backend.

This script handles graceful application startup specifically for Railway deployments,
ensuring proper Blue-Green deployment behavior and preventing common startup issues.
"""

import os
import sys
import time
import signal
import logging
import asyncio
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("railway_startup")


class RailwayStartupManager:
    """Manages Railway-specific startup sequence and health checks."""
    
    def __init__(self):
        self.startup_time = time.time()
        self.shutdown_requested = False
        self.app_ready = False
        
        # Railway-specific environment variables
        self.port = int(os.environ.get("PORT", 8000))
        self.railway_env = os.environ.get("RAILWAY_ENVIRONMENT", "production")
        self.railway_service = os.environ.get("RAILWAY_SERVICE_NAME", "taxpoynt-backend")
        
        logger.info(f"Starting {self.railway_service} on Railway environment: {self.railway_env}")
        logger.info(f"Port: {self.port}")
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)
    
    def validate_environment(self) -> bool:
        """Validate critical environment variables."""
        try:
            required_vars = [
                "DATABASE_URL",
                "SECRET_KEY"
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.environ.get(var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.error(f"Missing required environment variables: {missing_vars}")
                return False
            
            logger.info("Environment validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False
    
    def preload_critical_modules(self) -> bool:
        """Preload critical modules to catch import errors early."""
        try:
            logger.info("Preloading critical modules...")
            
            # Import critical modules
            critical_modules = [
                "fastapi",
                "sqlalchemy",
                "pydantic",
                "uvicorn"
            ]
            
            for module in critical_modules:
                try:
                    __import__(module)
                    logger.debug(f"Successfully imported {module}")
                except ImportError as e:
                    logger.error(f"Failed to import critical module {module}: {e}")
                    return False
            
            logger.info("Critical modules preloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Module preloading failed: {e}")
            return False
    
    def test_database_connection(self) -> bool:
        """Test database connection with retry logic."""
        try:
            from app.db.session import SessionLocal
            from sqlalchemy import text
            
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    with SessionLocal() as db:
                        result = db.execute(text("SELECT 1")).scalar()
                        if result == 1:
                            logger.info("Database connection successful")
                            return True
                except Exception as e:
                    logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
            
            logger.error("Database connection failed after all retries")
            return False
            
        except ImportError as e:
            logger.warning(f"Database modules not available: {e}")
            # Don't fail startup for missing database modules during Railway deployment
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def test_redis_connection(self) -> bool:
        """Test Redis connection with retry logic."""
        try:
            from app.db.redis import get_redis_client
            
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    redis_client = get_redis_client()
                    pong = redis_client.ping()
                    if pong:
                        logger.info("Redis connection successful")
                        return True
                except Exception as e:
                    logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
            
            logger.warning("Redis connection failed - continuing without Redis")
            # Don't fail startup for Redis issues
            return True
            
        except ImportError as e:
            logger.warning(f"Redis modules not available: {e}")
            return True
        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}")
            return True
    
    def initialize_application(self) -> bool:
        """Initialize the FastAPI application."""
        try:
            logger.info("Initializing FastAPI application...")
            
            # Import the application
            from app.main import app
            
            # Verify the app was created successfully
            if app is None:
                logger.error("FastAPI application is None")
                return False
            
            logger.info("FastAPI application initialized successfully")
            self.app_ready = True
            return True
            
        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            return False
    
    def start_background_services(self) -> bool:
        """Start background services if available."""
        try:
            logger.info("Starting background services...")
            
            # Try to start background tasks
            try:
                from app.services.background_tasks import start_background_tasks
                start_background_tasks()
                logger.info("Background services started")
            except ImportError:
                logger.info("Background services not available")
            except Exception as e:
                logger.warning(f"Background services failed to start: {e}")
                # Don't fail startup for background service issues
            
            return True
            
        except Exception as e:
            logger.warning(f"Background services startup failed: {e}")
            return True  # Don't fail startup for background service issues
    
    def run_startup_sequence(self) -> bool:
        """Execute the complete startup sequence."""
        logger.info("=== Railway Startup Sequence Started ===")
        
        startup_steps = [
            ("Environment Validation", self.validate_environment),
            ("Critical Modules", self.preload_critical_modules),
            ("Database Connection", self.test_database_connection),
            ("Redis Connection", self.test_redis_connection),
            ("Application Initialization", self.initialize_application),
            ("Background Services", self.start_background_services)
        ]
        
        for step_name, step_func in startup_steps:
            if self.shutdown_requested:
                logger.info("Shutdown requested during startup")
                return False
                
            logger.info(f"Executing: {step_name}")
            step_start_time = time.time()
            
            try:
                success = step_func()
                step_duration = time.time() - step_start_time
                
                if success:
                    logger.info(f"✓ {step_name} completed in {step_duration:.2f}s")
                else:
                    logger.error(f"✗ {step_name} failed after {step_duration:.2f}s")
                    
                    # For Railway deployment, only fail on critical errors
                    if step_name in ["Environment Validation", "Application Initialization"]:
                        return False
                    else:
                        logger.warning(f"Continuing despite {step_name} failure")
                        
            except Exception as e:
                logger.error(f"✗ {step_name} raised exception: {e}")
                
                # For Railway deployment, only fail on critical errors
                if step_name in ["Environment Validation", "Application Initialization"]:
                    return False
                else:
                    logger.warning(f"Continuing despite {step_name} exception")
        
        total_startup_time = time.time() - self.startup_time
        logger.info(f"=== Railway Startup Sequence Completed in {total_startup_time:.2f}s ===")
        
        return True
    
    def start_server(self):
        """Start the Uvicorn server with Railway-optimized settings."""
        try:
            import uvicorn
            from app.main import app
            
            # Railway-optimized Uvicorn configuration
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=self.port,
                workers=1,  # Single worker for Railway
                timeout_keep_alive=300,  # 5 minutes
                timeout_graceful_shutdown=120,  # 2 minutes graceful shutdown
                access_log=True,
                log_level="info"
            )
            
            server = uvicorn.Server(config)
            
            logger.info(f"Starting Uvicorn server on 0.0.0.0:{self.port}")
            logger.info("Application ready to serve traffic")
            
            # Run the server
            server.run()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            sys.exit(1)


def main():
    """Main entry point for Railway startup."""
    startup_manager = RailwayStartupManager()
    
    try:
        # Setup signal handlers for graceful shutdown
        startup_manager.setup_signal_handlers()
        
        # Execute startup sequence
        if not startup_manager.run_startup_sequence():
            logger.error("Startup sequence failed")
            sys.exit(1)
        
        # Start the server
        startup_manager.start_server()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Startup failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()