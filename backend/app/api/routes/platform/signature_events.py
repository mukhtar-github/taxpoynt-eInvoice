"""
API routes for signature event monitoring in the Platform layer.

These routes expose signature events for monitoring dashboards,
providing comprehensive observability for system administrators.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.security import get_current_active_user
from app.models.user import User
from app.utils.signature_event_tracker import signature_tracker, SignatureEventType

router = APIRouter(prefix="/platform/signatures/events", tags=["platform", "signatures", "events"])
logger = logging.getLogger(__name__)

class EventFilter(BaseModel):
    """Filter parameters for signature events"""
    event_type: Optional[SignatureEventType] = None
    user_id: Optional[str] = None
    invoice_id: Optional[str] = None
    signature_id: Optional[str] = None
    min_duration: Optional[float] = None
    success: Optional[bool] = None
    has_error: Optional[bool] = None
    time_range: Optional[str] = None  # e.g., "1h", "24h", "7d"

@router.get("/recent")
async def get_recent_events(
    limit: int = Query(50, description="Maximum number of events to return", gt=0, le=1000),
    event_type: Optional[SignatureEventType] = Query(None, description="Filter by event type"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get recent signature events
    
    Returns the most recent signature events, optionally filtered by type.
    Primarily intended for system monitoring dashboards.
    """
    # Log access for audit purposes
    logger.info(f"User {current_user.email} accessed recent signature events")
    
    # Get events from tracker
    events = signature_tracker.get_recent_events(limit=limit, event_type=event_type)
    
    # Process events for better readability
    processed_events = []
    for event in events:
        # Format timestamp for display
        if "timestamp" in event:
            event["timestamp_display"] = event["timestamp"]
        
        # Add user-friendly duration if available
        if event.get("duration_ms"):
            if event["duration_ms"] < 1:
                event["duration_display"] = f"{event['duration_ms'] * 1000:.2f} μs"
            elif event["duration_ms"] < 1000:
                event["duration_display"] = f"{event['duration_ms']:.2f} ms"
            else:
                event["duration_display"] = f"{event['duration_ms'] / 1000:.2f} s"
        
        processed_events.append(event)
    
    return {
        "events": processed_events,
        "total": len(processed_events),
        "has_more": len(processed_events) == limit
    }

@router.get("/stats")
async def get_event_stats(
    event_type: Optional[SignatureEventType] = Query(None, description="Filter stats by event type"),
    time_range: str = Query("24h", description="Time range (1h, 24h, 7d, 30d)"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get statistical summaries of signature events
    
    Returns aggregate statistics about signature events, including
    counts, success rates, and performance metrics.
    """
    # Log access for audit purposes
    logger.info(f"User {current_user.email} accessed signature event statistics")
    
    # Get metrics from tracker
    metrics = signature_tracker.get_metrics()
    
    # Format specific statistics based on event type
    if event_type == SignatureEventType.VERIFICATION:
        return {
            "event_type": "verification",
            "total_count": metrics["verification"]["total"],
            "success_count": metrics["verification"]["success"],
            "failure_count": metrics["verification"]["failure"],
            "success_rate": metrics["verification"]["success_rate"],
            "avg_duration_ms": metrics["verification"]["avg_time"],
            "time_range": time_range
        }
    elif event_type == SignatureEventType.GENERATION:
        return {
            "event_type": "generation",
            "total_count": metrics["generation"]["total"],
            "success_count": metrics["generation"]["success"],
            "failure_count": metrics["generation"]["failure"],
            "success_rate": metrics["generation"]["success_rate"],
            "avg_duration_ms": metrics["generation"]["avg_time"],
            "time_range": time_range
        }
    elif event_type == SignatureEventType.CACHE_HIT or event_type == SignatureEventType.CACHE_MISS:
        return {
            "event_type": "cache",
            "hits": metrics["cache"]["hits"],
            "misses": metrics["cache"]["misses"],
            "hit_rate": metrics["cache"]["hit_rate"],
            "clear_count": metrics["cache"]["clear_count"],
            "time_range": time_range
        }
    else:
        # Return all metrics
        return {
            "verification": {
                "total_count": metrics["verification"]["total"],
                "success_rate": metrics["verification"]["success_rate"],
                "avg_duration_ms": metrics["verification"]["avg_time"]
            },
            "generation": {
                "total_count": metrics["generation"]["total"],
                "success_rate": metrics["generation"]["success_rate"],
                "avg_duration_ms": metrics["generation"]["avg_time"]
            },
            "cache": {
                "hits": metrics["cache"]["hits"],
                "misses": metrics["cache"]["misses"],
                "hit_rate": metrics["cache"]["hit_rate"]
            },
            "time_range": time_range
        }

@router.post("/clear")
async def clear_events(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Clear all stored signature events
    
    This is an administrative function to reset the event tracker.
    Does not affect metrics aggregation.
    """
    # Log access for audit purposes
    logger.info(f"User {current_user.email} cleared signature events")
    
    # Clear events
    signature_tracker.clear_events()
    
    return {
        "status": "success",
        "message": "Signature events cleared successfully"
    }
