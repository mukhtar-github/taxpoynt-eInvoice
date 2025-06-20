"""
Celery configuration for TaxPoynt eInvoice background tasks.

This module provides comprehensive queue management with:
- Multiple priority queues for different task types
- Redis backend for reliable message persistence
- Monitoring and health check capabilities
- Worker specialization and routing
"""

import os
import logging
from typing import Dict, Any, Optional
from celery import Celery
from celery.signals import worker_ready, worker_shutting_down
from kombu import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# ==================== CELERY APP CONFIGURATION ====================

def create_celery_app() -> Celery:
    """
    Create and configure the Celery application.
    
    Returns:
        Configured Celery application instance
    """
    # Initialize Celery app
    celery_app = Celery(
        "taxpoynt_tasks",
        broker=_get_broker_url(),
        backend=_get_result_backend_url(),
        include=[
            "app.tasks.pos_tasks",
            "app.tasks.crm_tasks", 
            "app.tasks.batch_tasks",
            "app.tasks.hubspot_tasks",
            "app.tasks.certificate_tasks",
            "app.tasks.irn_tasks",
            "app.tasks.integration_tasks",
            "app.tasks.firs_tasks",
        ]
    )
    
    # Configure Celery
    celery_app.config_from_object(_get_celery_config())
    
    # Set up queues
    _setup_queues(celery_app)
    
    # Configure task routing
    _setup_task_routing(celery_app)
    
    logger.info("Celery application configured successfully")
    return celery_app


def _get_broker_url() -> str:
    """Get the broker URL for Celery."""
    if settings.REDIS_URL:
        # Use existing Redis URL but ensure it points to the correct database
        if settings.REDIS_URL.endswith("/0"):
            return settings.REDIS_URL.replace("/0", "/0")  # Broker on DB 0
        elif "/" in settings.REDIS_URL.split("//")[1]:
            # URL already has database specified
            return settings.REDIS_URL
        else:
            # Add database 0 for broker
            return f"{settings.REDIS_URL}/0"
    else:
        # Build URL from components
        if settings.REDIS_PASSWORD:
            return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
        else:
            return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"


def _get_result_backend_url() -> str:
    """Get the result backend URL for Celery."""
    if settings.REDIS_URL:
        # Use existing Redis URL but point to database 1 for results
        if settings.REDIS_URL.endswith("/0"):
            return settings.REDIS_URL.replace("/0", "/1")  # Results on DB 1
        elif "/" in settings.REDIS_URL.split("//")[1]:
            # Extract base URL and set database 1
            base_url = settings.REDIS_URL.rsplit("/", 1)[0]
            return f"{base_url}/1"
        else:
            # Add database 1 for results
            return f"{settings.REDIS_URL}/1"
    else:
        # Build URL from components
        if settings.REDIS_PASSWORD:
            return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"
        else:
            return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"


def _get_celery_config() -> Dict[str, Any]:
    """
    Get Celery configuration settings.
    
    Returns:
        Dict containing Celery configuration
    """
    return {
        # Task Settings
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
        "enable_utc": True,
        
        # Result Backend Settings
        "result_expires": 3600,  # Results expire after 1 hour
        "result_persistent": True,  # Persist results in Redis
        "result_backend_transport_options": {
            "global_keyprefix": "taxpoynt_celery_results",
            "retry_policy": {
                "timeout": 5.0
            }
        },
        
        # Worker Settings
        "worker_prefetch_multiplier": 1,  # Prevent worker overload
        "worker_max_tasks_per_child": 1000,  # Restart workers after 1000 tasks
        "worker_disable_rate_limits": False,
        "worker_log_level": "INFO",
        
        # Task Execution Settings
        "task_acks_late": True,  # Acknowledge tasks only after completion
        "task_reject_on_worker_lost": True,  # Reject tasks if worker dies
        "task_track_started": True,  # Track when tasks start
        "task_time_limit": 300,  # 5 minute hard time limit
        "task_soft_time_limit": 240,  # 4 minute soft time limit
        
        # Retry Settings
        "task_annotations": {
            "*": {
                "rate_limit": "100/m",  # Global rate limit
                "time_limit": 300,
                "soft_time_limit": 240,
            },
            "app.tasks.pos_tasks.*": {
                "rate_limit": "200/m",  # Higher limit for POS tasks
                "priority": 9,
            },
            "app.tasks.crm_tasks.*": {
                "rate_limit": "150/m",
                "priority": 6,
            },
            "app.tasks.firs_tasks.*": {
                "rate_limit": "100/m",
                "priority": 8,  # High priority for FIRS submissions
            },
            "app.tasks.batch_tasks.*": {
                "rate_limit": "50/m",  # Lower limit for batch operations
                "priority": 3,
            },
        },
        
        # Beat Schedule (for periodic tasks)
        "beat_schedule": {
            "certificate-monitor": {
                "task": "app.tasks.certificate_tasks.certificate_monitor_task",
                "schedule": 3600.0,  # Every hour
                "options": {"queue": "maintenance"}
            },
            "hubspot-deal-processor": {
                "task": "app.tasks.hubspot_tasks.hubspot_deal_processor_task",
                "schedule": 3600.0,  # Every hour
                "options": {"queue": "crm_standard"}
            },
            "retry-failed-submissions": {
                "task": "app.tasks.firs_tasks.retry_failed_submissions",
                "schedule": 300.0,  # Every 5 minutes
                "options": {"queue": "firs_high"}
            },
            "cleanup-old-results": {
                "task": "app.tasks.maintenance_tasks.cleanup_old_results",
                "schedule": 86400.0,  # Daily
                "options": {"queue": "maintenance"}
            }
        },
        
        # Monitoring Settings
        "worker_send_task_events": True,
        "task_send_sent_event": True,
        
        # Security Settings
        "worker_hijack_root_logger": False,
        "worker_log_color": False,
    }


def _setup_queues(celery_app: Celery) -> None:
    """
    Set up multiple queues with different priorities.
    
    Args:
        celery_app: Celery application instance
    """
    # Define queues with priority levels
    queues = [
        # Critical Priority Queues (Priority 8-10)
        Queue("firs_critical", routing_key="firs.critical", queue_arguments={"x-max-priority": 10}),
        Queue("pos_high", routing_key="pos.high", queue_arguments={"x-max-priority": 9}),
        Queue("firs_high", routing_key="firs.high", queue_arguments={"x-max-priority": 8}),
        
        # Standard Priority Queues (Priority 5-7)
        Queue("crm_high", routing_key="crm.high", queue_arguments={"x-max-priority": 7}),
        Queue("crm_standard", routing_key="crm.standard", queue_arguments={"x-max-priority": 6}),
        Queue("pos_standard", routing_key="pos.standard", queue_arguments={"x-max-priority": 5}),
        
        # Low Priority Queues (Priority 1-4)
        Queue("batch_high", routing_key="batch.high", queue_arguments={"x-max-priority": 4}),
        Queue("batch_standard", routing_key="batch.standard", queue_arguments={"x-max-priority": 3}),
        Queue("maintenance", routing_key="maintenance", queue_arguments={"x-max-priority": 2}),
        Queue("default", routing_key="default", queue_arguments={"x-max-priority": 1}),
    ]
    
    # Configure task queues
    celery_app.conf.task_queues = queues
    celery_app.conf.task_default_queue = "default"
    celery_app.conf.task_default_exchange = "taxpoynt_tasks"
    celery_app.conf.task_default_exchange_type = "direct"
    celery_app.conf.task_default_routing_key = "default"
    
    logger.info(f"Configured {len(queues)} task queues with priority levels")


def _setup_task_routing(celery_app: Celery) -> None:
    """
    Configure task routing to appropriate queues.
    
    Args:
        celery_app: Celery application instance
    """
    # Task routing configuration
    task_routes = {
        # POS Tasks (High Priority - Real-time transactions)
        "app.tasks.pos_tasks.process_sale": {"queue": "pos_high", "priority": 9},
        "app.tasks.pos_tasks.process_refund": {"queue": "pos_high", "priority": 9},
        "app.tasks.pos_tasks.sync_inventory": {"queue": "pos_standard", "priority": 5},
        "app.tasks.pos_tasks.*": {"queue": "pos_standard", "priority": 5},
        
        # CRM Tasks (Standard Priority - Business processes)
        "app.tasks.crm_tasks.process_deal": {"queue": "crm_high", "priority": 7},
        "app.tasks.crm_tasks.sync_deals": {"queue": "crm_standard", "priority": 6},
        "app.tasks.crm_tasks.*": {"queue": "crm_standard", "priority": 6},
        "app.tasks.hubspot_tasks.*": {"queue": "crm_standard", "priority": 6},
        
        # FIRS Tasks (Critical/High Priority - Compliance)
        "app.tasks.firs_tasks.submit_invoice": {"queue": "firs_critical", "priority": 10},
        "app.tasks.firs_tasks.retry_submission": {"queue": "firs_high", "priority": 8},
        "app.tasks.firs_tasks.validate_invoice": {"queue": "firs_high", "priority": 8},
        "app.tasks.firs_tasks.*": {"queue": "firs_high", "priority": 8},
        
        # Batch Tasks (Low Priority - Background processing)
        "app.tasks.batch_tasks.bulk_import": {"queue": "batch_high", "priority": 4},
        "app.tasks.batch_tasks.bulk_export": {"queue": "batch_standard", "priority": 3},
        "app.tasks.batch_tasks.*": {"queue": "batch_standard", "priority": 3},
        
        # Integration Tasks
        "app.tasks.integration_tasks.*": {"queue": "crm_standard", "priority": 6},
        
        # Certificate & IRN Tasks
        "app.tasks.certificate_tasks.*": {"queue": "maintenance", "priority": 2},
        "app.tasks.irn_tasks.*": {"queue": "firs_high", "priority": 8},
        
        # Maintenance Tasks (Lowest Priority)
        "app.tasks.maintenance_tasks.*": {"queue": "maintenance", "priority": 1},
    }
    
    celery_app.conf.task_routes = task_routes
    logger.info(f"Configured task routing for {len(task_routes)} task patterns")


# ==================== MONITORING & HEALTH CHECKS ====================

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal."""
    worker_name = sender.hostname if sender else "unknown"
    logger.info(f"Celery worker '{worker_name}' is ready and waiting for tasks")


@worker_shutting_down.connect
def worker_shutting_down_handler(sender=None, **kwargs):
    """Handle worker shutdown signal."""
    worker_name = sender.hostname if sender else "unknown"
    logger.info(f"Celery worker '{worker_name}' is shutting down")


def get_queue_health() -> Dict[str, Any]:
    """
    Get health information for all queues.
    
    Returns:
        Dict containing queue health metrics
    """
    try:
        from app.db.redis import get_redis_client
        
        redis_client = get_redis_client()
        queue_info = {}
        
        # List of queue names to check
        queue_names = [
            "firs_critical", "pos_high", "firs_high",
            "crm_high", "crm_standard", "pos_standard", 
            "batch_high", "batch_standard", "maintenance", "default"
        ]
        
        for queue_name in queue_names:
            # Get queue length from Redis
            queue_key = f"celery:queue:{queue_name}"
            length = redis_client.llen(queue_key)
            
            queue_info[queue_name] = {
                "length": length,
                "status": "healthy" if length < 1000 else "warning" if length < 5000 else "critical"
            }
        
        return {
            "status": "healthy",
            "queues": queue_info,
            "total_pending": sum(q["length"] for q in queue_info.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting queue health: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "queues": {},
            "total_pending": 0
        }


def get_worker_health() -> Dict[str, Any]:
    """
    Get health information for active workers.
    
    Returns:
        Dict containing worker health metrics
    """
    try:
        # This would require Celery inspect functionality
        # For now, return basic info
        return {
            "status": "healthy",
            "active_workers": 0,  # Would be populated by celery.control.inspect()
            "available_queues": [
                "firs_critical", "pos_high", "firs_high",
                "crm_high", "crm_standard", "pos_standard",
                "batch_high", "batch_standard", "maintenance", "default"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting worker health: {str(e)}")
        return {
            "status": "error", 
            "error": str(e),
            "active_workers": 0,
            "available_queues": []
        }


# ==================== CELERY APP INSTANCE ====================

# Create the Celery app instance
celery_app = create_celery_app()

# Export for imports
__all__ = ["celery_app", "get_queue_health", "get_worker_health"]