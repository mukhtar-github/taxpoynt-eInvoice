"""
Signature Event Tracker

Utility for tracking and logging signature-related events for observability purposes.
Captures key metrics, operation details, and errors for monitoring and debugging.
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from contextlib import contextmanager

logger = logging.getLogger("signature_events")

class SignatureEventType(str, Enum):
    """Types of signature events to track"""
    GENERATION = "generation"
    VERIFICATION = "verification"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CACHE_CLEAR = "cache_clear"
    SETTINGS_CHANGE = "settings_change"
    ERROR = "error"

class SignatureEventTracker:
    """
    Tracks signature-related events and metrics for observability
    
    Features:
    - Detailed event logging with consistent structure
    - Performance timing for operations
    - Error tracking with context
    - Aggregated metrics collection
    """
    
    def __init__(self, max_events: int = 1000):
        """
        Initialize the event tracker
        
        Args:
            max_events: Maximum number of events to store in memory
        """
        self._events: List[Dict[str, Any]] = []
        self._max_events = max_events
        self._metrics: Dict[str, Any] = {
            "verification": {
                "total": 0,
                "success": 0,
                "failure": 0,
                "total_time": 0,
                "avg_time": 0,
            },
            "generation": {
                "total": 0,
                "success": 0,
                "failure": 0,
                "total_time": 0,
                "avg_time": 0,
            },
            "cache": {
                "hits": 0,
                "misses": 0,
                "clear_count": 0,
            }
        }
    
    def track_event(
        self,
        event_type: SignatureEventType,
        user_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        signature_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track a signature-related event
        
        Args:
            event_type: Type of event (generation, verification, etc.)
            user_id: ID of the user performing the operation
            invoice_id: ID of the invoice being processed
            signature_id: ID of the signature
            duration_ms: Duration of the operation in milliseconds
            details: Additional details about the event
            success: Whether the operation was successful
            error_message: Error message if operation failed
            
        Returns:
            The created event record
        """
        timestamp = datetime.utcnow().isoformat()
        
        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "user_id": user_id,
            "invoice_id": invoice_id,
            "signature_id": signature_id,
            "duration_ms": duration_ms,
            "success": success,
            "details": details or {},
        }
        
        if error_message:
            event["error"] = error_message
            
        # Store event and maintain max size
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events.pop(0)
            
        # Update metrics based on event type
        self._update_metrics(event)
        
        # Log the event
        log_data = json.dumps(event)
        if error_message:
            logger.error(f"Signature event: {log_data}")
        else:
            logger.info(f"Signature event: {log_data}")
            
        return event
    
    @contextmanager
    def track_operation(
        self,
        event_type: SignatureEventType,
        user_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        signature_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracking timed operations
        
        Usage:
            with tracker.track_operation(SignatureEventType.VERIFICATION, user_id="123"):
                result = verify_signature(...)
                
        Args:
            event_type: Type of event
            user_id: ID of the user performing the operation
            invoice_id: ID of the invoice being processed
            signature_id: ID of the signature
            details: Additional details about the event
        """
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            self.track_event(
                event_type=event_type,
                user_id=user_id,
                invoice_id=invoice_id,
                signature_id=signature_id,
                duration_ms=duration_ms,
                details=details,
                success=success,
                error_message=error_message
            )
    
    def _update_metrics(self, event: Dict[str, Any]) -> None:
        """
        Update metrics based on the event
        
        Args:
            event: Event data to update metrics with
        """
        event_type = event["event_type"]
        duration = event.get("duration_ms", 0)
        
        if event_type == SignatureEventType.VERIFICATION:
            self._metrics["verification"]["total"] += 1
            self._metrics["verification"]["total_time"] += duration
            
            if event.get("success", False):
                self._metrics["verification"]["success"] += 1
            else:
                self._metrics["verification"]["failure"] += 1
                
            if self._metrics["verification"]["total"] > 0:
                self._metrics["verification"]["avg_time"] = (
                    self._metrics["verification"]["total_time"] / 
                    self._metrics["verification"]["total"]
                )
                
        elif event_type == SignatureEventType.GENERATION:
            self._metrics["generation"]["total"] += 1
            self._metrics["generation"]["total_time"] += duration
            
            if event.get("success", False):
                self._metrics["generation"]["success"] += 1
            else:
                self._metrics["generation"]["failure"] += 1
                
            if self._metrics["generation"]["total"] > 0:
                self._metrics["generation"]["avg_time"] = (
                    self._metrics["generation"]["total_time"] / 
                    self._metrics["generation"]["total"]
                )
                
        elif event_type == SignatureEventType.CACHE_HIT:
            self._metrics["cache"]["hits"] += 1
            
        elif event_type == SignatureEventType.CACHE_MISS:
            self._metrics["cache"]["misses"] += 1
            
        elif event_type == SignatureEventType.CACHE_CLEAR:
            self._metrics["cache"]["clear_count"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics
        
        Returns:
            Dictionary of metrics
        """
        # Calculate additional metrics
        metrics = self._metrics.copy()
        
        # Calculate cache hit rate
        total_cache_ops = metrics["cache"]["hits"] + metrics["cache"]["misses"]
        if total_cache_ops > 0:
            metrics["cache"]["hit_rate"] = metrics["cache"]["hits"] / total_cache_ops
        else:
            metrics["cache"]["hit_rate"] = 0
            
        # Calculate verification success rate
        total_verifications = metrics["verification"]["total"]
        if total_verifications > 0:
            metrics["verification"]["success_rate"] = (
                metrics["verification"]["success"] / total_verifications
            )
        else:
            metrics["verification"]["success_rate"] = 0
            
        # Calculate generation success rate
        total_generations = metrics["generation"]["total"]
        if total_generations > 0:
            metrics["generation"]["success_rate"] = (
                metrics["generation"]["success"] / total_generations
            )
        else:
            metrics["generation"]["success_rate"] = 0
            
        return metrics
    
    def get_recent_events(self, limit: int = 100, event_type: Optional[SignatureEventType] = None) -> List[Dict[str, Any]]:
        """
        Get recent events
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            
        Returns:
            List of recent events
        """
        events = self._events.copy()
        
        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
            
        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda e: e["timestamp"], reverse=True)
        return events[:limit]
    
    def clear_events(self) -> None:
        """Clear all stored events"""
        self._events = []


# Singleton instance for application-wide use
signature_tracker = SignatureEventTracker()
