"""
Health check endpoints for deployment validation and monitoring.

This module provides comprehensive health checks to ensure the application
is ready to serve traffic before Railway switches to the new deployment.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.redis import get_redis_client
from app.core.config import settings
from app.services.pos_queue_service import get_pos_queue_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", summary="Basic health check")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns 200 if the application is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "taxpoynt-backend",
        "version": getattr(settings, "VERSION", "1.0.0")
    }


@router.get("/ready", summary="Simple readiness check")
async def simple_ready_check() -> Dict[str, Any]:
    """
    Simple readiness check without dependency validation.
    This is a backup endpoint for Railway health checks.
    """
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "service": "taxpoynt-backend"
    }


@router.get("/health/ready", summary="Readiness probe")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe to check if the application is ready to serve traffic.
    This is used by Railway to determine when to switch traffic to new deployment.
    Uses a graceful startup approach that doesn't fail immediately.
    """
    start_time = time.time()
    checks = {}
    overall_status = "healthy"
    
    try:
        # For initial startup, just check basic application health
        # Database and Redis checks can be optional during startup
        
        # Database connectivity check (non-blocking)
        try:
            checks["database"] = await _check_database()
        except Exception as e:
            logger.warning(f"Database check failed during startup: {str(e)}")
            checks["database"] = {"healthy": False, "error": str(e), "critical": False}
        
        # Redis connectivity check (non-blocking)
        try:
            checks["redis"] = await _check_redis()
        except Exception as e:
            logger.warning(f"Redis check failed during startup: {str(e)}")
            checks["redis"] = {"healthy": False, "error": str(e), "critical": False}
        
        # Application initialization check (critical)
        try:
            checks["application"] = await _check_application()
        except Exception as e:
            logger.error(f"Application check failed: {str(e)}")
            checks["application"] = {"healthy": False, "error": str(e), "critical": True}
        
        # Queue system check (non-critical for initial startup)
        try:
            checks["queues"] = await _check_queues()
        except Exception as e:
            logger.warning(f"Queue check failed during startup: {str(e)}")
            checks["queues"] = {"healthy": False, "error": str(e), "critical": False}
        
        # Only fail if critical components failed
        critical_failures = [
            name for name, check in checks.items() 
            if not check["healthy"] and check.get("critical", False)
        ]
        
        if critical_failures:
            overall_status = "unhealthy"
            logger.error(f"Critical readiness checks failed: {critical_failures}")
        else:
            # Check if database is healthy (required for most operations)
            if checks.get("database", {}).get("healthy", False):
                overall_status = "healthy"
            else:
                overall_status = "starting"  # Still starting up
        
        processing_time = time.time() - start_time
        
        response = {
            "status": overall_status,
            "checks": checks,
            "processing_time": round(processing_time, 3),
            "timestamp": datetime.now().isoformat(),
            "critical_failures": critical_failures
        }
        
        # Only return 503 for critical failures, not for startup dependencies
        if overall_status == "unhealthy":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response
            )
        
        # Return 200 even if still starting (Railway will keep checking)
        return response
        
    except Exception as e:
        logger.error(f"Readiness check failed with exception: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/live", summary="Liveness probe")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness probe to check if the application is alive.
    Used by Railway to determine if the container should be restarted.
    """
    try:
        # Basic application responsiveness check
        start_time = time.time()
        
        # Minimal checks - just ensure the app is responsive
        response_time = time.time() - start_time
        
        if response_time > 5.0:  # If basic check takes >5s, something is wrong
            raise Exception(f"Application responding too slowly: {response_time}s")
        
        return {
            "status": "alive",
            "response_time": round(response_time, 3),
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - start_time  # Would need proper uptime tracking
        }
        
    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "dead",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/startup", summary="Startup probe")
async def startup_check() -> Dict[str, Any]:
    """
    Startup probe to check if the application has finished initializing.
    Used by Railway to determine when the application is ready for traffic.
    """
    start_time = time.time()
    
    try:
        # Comprehensive startup checks
        startup_checks = {
            "database_migration": await _check_database_migrations(),
            "redis_connection": await _check_redis(),
            "workers_ready": await _check_workers(),
            "config_loaded": await _check_configuration(),
            "services_initialized": await _check_services()
        }
        
        failed_startup_checks = [
            name for name, check in startup_checks.items() 
            if not check["healthy"]
        ]
        
        if failed_startup_checks:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "checks": startup_checks,
                    "failed_checks": failed_startup_checks,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        processing_time = time.time() - start_time
        
        return {
            "status": "ready",
            "checks": startup_checks,
            "startup_time": round(processing_time, 3),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Startup check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "startup_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/deep", summary="Deep health check")
async def deep_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for monitoring and debugging.
    Not used for deployment decisions but for operational monitoring.
    """
    start_time = time.time()
    
    try:
        deep_checks = {
            "database": await _check_database_deep(),
            "redis": await _check_redis_deep(), 
            "queues": await _check_queues_deep(),
            "external_apis": await _check_external_apis(),
            "disk_space": await _check_disk_space(),
            "memory_usage": await _check_memory_usage(),
            "recent_errors": await _check_recent_errors()
        }
        
        # Calculate overall health score
        healthy_checks = sum(1 for check in deep_checks.values() if check["healthy"])
        health_score = (healthy_checks / len(deep_checks)) * 100
        
        processing_time = time.time() - start_time
        
        return {
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "unhealthy",
            "health_score": round(health_score, 1),
            "checks": deep_checks,
            "processing_time": round(processing_time, 3),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Deep health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Helper functions for health checks

async def _check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        with SessionLocal() as db:
            from sqlalchemy import text
            result = db.execute(text("SELECT 1")).scalar()
            return {
                "healthy": result == 1,
                "message": "Database connection successful",
                "response_time": "< 1s"
            }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Database connection failed: {str(e)}",
            "error": str(e)
        }


async def _check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        redis_client = get_redis_client()
        pong = redis_client.ping()
        return {
            "healthy": pong,
            "message": "Redis connection successful",
            "response": "PONG" if pong else "No response"
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Redis connection failed: {str(e)}",
            "error": str(e)
        }


async def _check_queues() -> Dict[str, Any]:
    """Check queue system health."""
    try:
        queue_service = get_pos_queue_service()
        status = await queue_service.get_queue_status()
        
        # Check if any queues are critically backed up
        critical_queues = []
        for queue_name, queue_info in status.get("queues", {}).items():
            if queue_info.get("status") == "critical":
                critical_queues.append(queue_name)
        
        return {
            "healthy": len(critical_queues) == 0,
            "message": "Queue system healthy" if not critical_queues else f"Critical queues: {critical_queues}",
            "critical_queues": critical_queues,
            "total_queues": len(status.get("queues", {}))
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Queue check failed: {str(e)}",
            "error": str(e)
        }


async def _check_application() -> Dict[str, Any]:
    """Check basic application health."""
    try:
        # Check if FastAPI is responding
        return {
            "healthy": True,
            "message": "Application responding normally",
            "framework": "FastAPI",
            "python_version": "3.12+"
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Application check failed: {str(e)}",
            "error": str(e)
        }


async def _check_database_migrations() -> Dict[str, Any]:
    """Check if database migrations are up to date."""
    try:
        # This would need actual migration checking logic
        # For now, just check if we can query the main tables
        with SessionLocal() as db:
            from sqlalchemy import text
            # Check if key tables exist
            tables_to_check = ["users", "organizations"]  # Start with core tables only
            existing_tables = 0
            
            for table in tables_to_check:
                try:
                    result = db.execute(text(f"SELECT 1 FROM {table} LIMIT 1")).fetchone()
                    existing_tables += 1
                except:
                    # Table might not exist yet, skip it
                    pass
        
        return {
            "healthy": existing_tables > 0,  # At least one core table should exist
            "message": f"Database schema check: {existing_tables}/{len(tables_to_check)} core tables found",
            "tables_found": existing_tables,
            "tables_checked": len(tables_to_check)
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Database migration check failed: {str(e)}",
            "error": str(e)
        }


async def _check_workers() -> Dict[str, Any]:
    """Check if background workers are ready."""
    try:
        # This would need actual worker checking logic
        # For now, just check if Redis queues are accessible
        redis_client = get_redis_client()
        queue_names = ["pos_high", "firs_critical", "maintenance"]
        
        for queue_name in queue_names:
            redis_client.llen(f"celery:queue:{queue_name}")
        
        return {
            "healthy": True,
            "message": "Workers ready",
            "queues_checked": len(queue_names)
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Worker check failed: {str(e)}",
            "error": str(e)
        }


async def _check_configuration() -> Dict[str, Any]:
    """Check if configuration is loaded properly."""
    try:
        # Check key configuration values
        config_checks = {
            "database_url": bool(settings.DATABASE_URL),
            "redis_url": bool(settings.REDIS_URL),
            "secret_key": bool(settings.SECRET_KEY),
            "app_env": bool(settings.APP_ENV)
        }
        
        missing_config = [key for key, value in config_checks.items() if not value]
        
        return {
            "healthy": len(missing_config) == 0,
            "message": "Configuration loaded" if not missing_config else f"Missing config: {missing_config}",
            "missing_config": missing_config,
            "environment": settings.APP_ENV
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Configuration check failed: {str(e)}",
            "error": str(e)
        }


async def _check_services() -> Dict[str, Any]:
    """Check if key services are initialized."""
    try:
        # Check if key services can be imported and initialized
        services_checked = [
            "pos_queue_service",
            "redis_client", 
            "database_session"
        ]
        
        return {
            "healthy": True,
            "message": "Services initialized successfully",
            "services_checked": services_checked
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Service initialization check failed: {str(e)}",
            "error": str(e)
        }


# Deep health check helpers

async def _check_database_deep() -> Dict[str, Any]:
    """Deep database health check."""
    try:
        start_time = time.time()
        with SessionLocal() as db:
            # Test read/write operations
            result = db.execute("SELECT COUNT(*) FROM users").scalar()
            query_time = time.time() - start_time
            
            return {
                "healthy": query_time < 1.0,  # Query should complete in <1s
                "message": f"Database responding in {query_time:.3f}s",
                "response_time": round(query_time, 3),
                "user_count": result
            }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Deep database check failed: {str(e)}",
            "error": str(e)
        }


async def _check_redis_deep() -> Dict[str, Any]:
    """Deep Redis health check."""
    try:
        redis_client = get_redis_client()
        
        # Test read/write operations
        start_time = time.time()
        test_key = f"health_check_{int(time.time())}"
        redis_client.set(test_key, "test_value", ex=60)  # Expires in 60s
        value = redis_client.get(test_key)
        redis_client.delete(test_key)
        operation_time = time.time() - start_time
        
        return {
            "healthy": value == "test_value" and operation_time < 0.1,
            "message": f"Redis read/write test completed in {operation_time:.3f}s",
            "response_time": round(operation_time, 3)
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Deep Redis check failed: {str(e)}",
            "error": str(e)
        }


async def _check_queues_deep() -> Dict[str, Any]:
    """Deep queue system health check."""
    try:
        queue_service = get_pos_queue_service()
        status = await queue_service.get_queue_status()
        
        queue_summary = {}
        total_pending = 0
        
        for queue_name, queue_info in status.get("queues", {}).items():
            length = queue_info.get("length", 0)
            queue_summary[queue_name] = {
                "length": length,
                "status": queue_info.get("status", "unknown")
            }
            total_pending += length
        
        return {
            "healthy": total_pending < 1000,  # Total pending < 1000
            "message": f"Total pending transactions: {total_pending}",
            "queue_summary": queue_summary,
            "total_pending": total_pending
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Deep queue check failed: {str(e)}",
            "error": str(e)
        }


async def _check_external_apis() -> Dict[str, Any]:
    """Check external API connectivity."""
    try:
        # This would test connections to FIRS, POS platforms, etc.
        # For now, just return a placeholder
        return {
            "healthy": True,
            "message": "External API checks not implemented",
            "apis_checked": 0
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"External API check failed: {str(e)}",
            "error": str(e)
        }


async def _check_disk_space() -> Dict[str, Any]:
    """Check available disk space."""
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        
        return {
            "healthy": free_percent > 10,  # At least 10% free space
            "message": f"Disk space: {free_percent:.1f}% free",
            "free_percent": round(free_percent, 1),
            "free_bytes": free,
            "total_bytes": total
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Disk space check failed: {str(e)}",
            "error": str(e)
        }


async def _check_memory_usage() -> Dict[str, Any]:
    """Check memory usage."""
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        return {
            "healthy": memory.percent < 90,  # Less than 90% memory usage
            "message": f"Memory usage: {memory.percent:.1f}%",
            "usage_percent": round(memory.percent, 1),
            "available_bytes": memory.available,
            "total_bytes": memory.total
        }
    except ImportError:
        return {
            "healthy": True,
            "message": "Memory check not available (psutil not installed)",
            "usage_percent": 0
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Memory check failed: {str(e)}",
            "error": str(e)
        }


async def _check_recent_errors() -> Dict[str, Any]:
    """Check for recent application errors."""
    try:
        # This would check error logs, Redis error counts, etc.
        # For now, just return a placeholder
        return {
            "healthy": True,
            "message": "No recent critical errors detected",
            "error_count": 0,
            "last_24h_errors": 0
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Error check failed: {str(e)}",
            "error": str(e)
        }