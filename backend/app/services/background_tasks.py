"""
Background task management for TaxPoynt eInvoice.

This module provides background task management for:
1. Processing scheduled submission retries
2. Monitoring failed submissions
3. Cleanup of old records
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.retry_service import process_pending_retries
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

# Global task registry to prevent duplicate tasks
_tasks = {}


async def start_background_tasks():
    """Start all background tasks."""
    logger.info("Starting background tasks")
    
    # Start the submission retry processor
    start_task(
        "submission_retry_processor",
        submission_retry_processor,
        interval_seconds=settings.RETRY_PROCESSOR_INTERVAL or 60
    )
    
    # Add more background tasks here as needed


def start_task(
    name: str,
    coro_func: Callable[[], Awaitable[None]],
    interval_seconds: int = 60,
    jitter_percent: float = 0.1
):
    """
    Start a background task that runs periodically.
    
    Args:
        name: Unique name for the task
        coro_func: Coroutine function to run
        interval_seconds: Interval between runs in seconds
        jitter_percent: Random jitter percentage to add to interval
    """
    if name in _tasks:
        logger.warning(f"Task {name} is already running")
        return

    async def task_wrapper():
        import random
        
        logger.info(f"Background task {name} started with interval {interval_seconds}s")
        
        while True:
            try:
                # Add jitter to prevent all tasks running at once
                jitter = random.uniform(-jitter_percent, jitter_percent)
                actual_interval = interval_seconds * (1 + jitter)
                
                # Run the task
                start_time = datetime.utcnow()
                await coro_func()
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                logger.debug(f"Task {name} completed in {duration:.2f}s")
                
                # Sleep until next run
                await asyncio.sleep(actual_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Task {name} cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in background task {name}: {str(e)}")
                # Sleep a bit to prevent tight loop on persistent errors
                await asyncio.sleep(min(interval_seconds, 10))

    # Start the task
    task = asyncio.create_task(task_wrapper())
    _tasks[name] = task
    
    return task


def stop_task(name: str):
    """
    Stop a running background task.
    
    Args:
        name: Name of the task to stop
    """
    if name not in _tasks:
        logger.warning(f"Task {name} is not running")
        return

    task = _tasks.pop(name)
    task.cancel()
    logger.info(f"Task {name} stopped")


async def submission_retry_processor():
    """
    Process pending submission retries.
    
    This task runs periodically to check for pending retries that are due
    and triggers their processing.
    """
    # Create a new database session for this task
    db = SessionLocal()
    try:
        # Process pending retries
        processed_count = await process_pending_retries(db)
        
        if processed_count > 0:
            logger.info(f"Processed {processed_count} pending submission retries")
            
    except Exception as e:
        logger.exception(f"Error processing submission retries: {str(e)}")
    finally:
        db.close()
