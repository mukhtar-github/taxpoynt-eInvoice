"""
FIRS API Monitoring Service.

This module provides monitoring capabilities for FIRS API interactions,
tracking performance metrics, error rates, and usage statistics.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import json
import asyncio
from functools import wraps
import statistics
from collections import deque, Counter

logger = logging.getLogger(__name__)

# Configure monitoring settings
DEFAULT_HISTORY_SIZE = 100  # Number of recent requests to keep for stats
DEFAULT_SLOW_THRESHOLD_MS = 1000  # Threshold to mark a request as "slow" (in ms)


class FIRSAPIMonitor:
    """
    Monitor for FIRS API calls with performance tracking and error reporting.
    
    This class provides:
    1. Request timing and performance metrics
    2. Error tracking and categorization
    3. Usage statistics for endpoints
    4. Rate limiting warnings
    """
    
    def __init__(self, history_size: int = DEFAULT_HISTORY_SIZE):
        """Initialize the API monitor."""
        self.request_history = deque(maxlen=history_size)
        self.error_history = deque(maxlen=history_size)
        self.endpoint_usage = Counter()
        self.slow_threshold_ms = DEFAULT_SLOW_THRESHOLD_MS
        self.start_time = datetime.now()
        
        # Stats tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.rate_limited_requests = 0
        
        logger.info(f"FIRS API monitoring initialized (history size: {history_size})")
    
    def record_request(
        self, 
        endpoint: str, 
        method: str, 
        duration_ms: float, 
        status_code: int, 
        environment: str,
        request_id: Optional[str] = None,
        payload_size: Optional[int] = None,
        response_size: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Record a single API request with its performance metrics.
        
        Args:
            endpoint: The API endpoint that was called
            method: HTTP method used (GET, POST, etc.)
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code received
            environment: 'sandbox' or 'production'
            request_id: Optional unique identifier for the request
            payload_size: Optional size of request payload in bytes
            response_size: Optional size of response in bytes
            error: Optional error message if request failed
        """
        timestamp = datetime.now()
        
        # Create request record
        request_record = {
            'timestamp': timestamp,
            'endpoint': endpoint,
            'method': method,
            'duration_ms': duration_ms,
            'status_code': status_code,
            'environment': environment,
            'request_id': request_id,
            'payload_size': payload_size,
            'response_size': response_size,
            'is_slow': duration_ms > self.slow_threshold_ms
        }
        
        # Update stats
        self.total_requests += 1
        self.endpoint_usage[endpoint] += 1
        
        # Categorize based on outcome
        if 200 <= status_code < 300:
            self.successful_requests += 1
        elif status_code == 429:
            self.rate_limited_requests += 1
            self.failed_requests += 1
        else:
            self.failed_requests += 1
        
        # Store in history
        self.request_history.append(request_record)
        
        # Log slow requests
        if request_record['is_slow']:
            logger.warning(
                f"Slow FIRS API call: {method} {endpoint} took {duration_ms:.2f} ms "
                f"(threshold: {self.slow_threshold_ms} ms)"
            )
        
        # Record error if present
        if error:
            self.record_error(endpoint, status_code, error, environment, request_id)
    
    def record_error(
        self, 
        endpoint: str, 
        status_code: int, 
        error_message: str, 
        environment: str,
        request_id: Optional[str] = None
    ) -> None:
        """Record an API error for tracking and analysis."""
        error_record = {
            'timestamp': datetime.now(),
            'endpoint': endpoint,
            'status_code': status_code,
            'error_message': error_message,
            'environment': environment,
            'request_id': request_id
        }
        
        self.error_history.append(error_record)
        logger.error(f"FIRS API error ({status_code}): {error_message} - {endpoint}")
    
    def get_performance_stats(self, timeframe_minutes: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate performance statistics for API calls.
        
        Args:
            timeframe_minutes: Optional timeframe in minutes to limit stats calculation
                               If None, all available history is used
                               
        Returns:
            Dictionary with performance statistics
        """
        # Filter history based on timeframe if specified
        if timeframe_minutes is not None:
            cutoff_time = datetime.now() - timedelta(minutes=timeframe_minutes)
            filtered_history = [
                req for req in self.request_history 
                if req['timestamp'] >= cutoff_time
            ]
        else:
            filtered_history = list(self.request_history)
        
        # Handle empty history
        if not filtered_history:
            return {
                'request_count': 0,
                'avg_duration_ms': 0,
                'min_duration_ms': 0,
                'max_duration_ms': 0,
                'p95_duration_ms': 0,
                'success_rate': 0,
                'error_rate': 0,
                'slow_request_count': 0,
                'timeframe_minutes': timeframe_minutes
            }
        
        # Calculate stats
        durations = [req['duration_ms'] for req in filtered_history]
        durations.sort()
        
        success_count = sum(1 for req in filtered_history if 200 <= req['status_code'] < 300)
        error_count = len(filtered_history) - success_count
        slow_count = sum(1 for req in filtered_history if req['is_slow'])
        
        # Calculate p95 (95th percentile)
        p95_index = int(len(durations) * 0.95)
        if p95_index >= len(durations):
            p95_index = len(durations) - 1
        
        return {
            'request_count': len(filtered_history),
            'avg_duration_ms': statistics.mean(durations) if durations else 0,
            'min_duration_ms': min(durations) if durations else 0,
            'max_duration_ms': max(durations) if durations else 0,
            'p95_duration_ms': durations[p95_index] if durations else 0,
            'success_rate': (success_count / len(filtered_history)) * 100 if filtered_history else 0,
            'error_rate': (error_count / len(filtered_history)) * 100 if filtered_history else 0,
            'slow_request_count': slow_count,
            'timeframe_minutes': timeframe_minutes
        }
    
    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get usage and performance statistics per endpoint."""
        endpoint_stats = {}
        
        # Group requests by endpoint
        for endpoint in self.endpoint_usage:
            endpoint_requests = [req for req in self.request_history if req['endpoint'] == endpoint]
            
            if not endpoint_requests:
                continue
                
            # Calculate stats for this endpoint
            durations = [req['duration_ms'] for req in endpoint_requests]
            success_count = sum(1 for req in endpoint_requests if 200 <= req['status_code'] < 300)
            error_count = len(endpoint_requests) - success_count
            
            endpoint_stats[endpoint] = {
                'request_count': len(endpoint_requests),
                'avg_duration_ms': statistics.mean(durations) if durations else 0,
                'success_rate': (success_count / len(endpoint_requests)) * 100 if endpoint_requests else 0,
                'error_rate': (error_count / len(endpoint_requests)) * 100 if endpoint_requests else 0,
                'usage_percentage': (self.endpoint_usage[endpoint] / self.total_requests) * 100 if self.total_requests else 0
            }
            
        return endpoint_stats
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Summarize recent errors by type and frequency."""
        if not self.error_history:
            return {
                'error_count': 0,
                'error_types': {},
                'most_common_errors': []
            }
        
        # Count errors by status code
        error_types = {}
        for error in self.error_history:
            status = error['status_code']
            if status not in error_types:
                error_types[status] = 0
            error_types[status] += 1
        
        # Find most common error messages
        error_messages = Counter([error['error_message'] for error in self.error_history])
        most_common = error_messages.most_common(5)  # Top 5 errors
        
        return {
            'error_count': len(self.error_history),
            'error_types': error_types,
            'most_common_errors': [
                {'message': msg, 'count': count}
                for msg, count in most_common
            ]
        }
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive monitoring summary report."""
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'summary': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': (self.successful_requests / self.total_requests) * 100 if self.total_requests else 0,
                'rate_limited_requests': self.rate_limited_requests,
                'uptime_hours': uptime_seconds / 3600
            },
            'recent_performance': self.get_performance_stats(timeframe_minutes=60),  # Last hour
            'endpoint_stats': self.get_endpoint_stats(),
            'error_summary': self.get_error_summary(),
            'generated_at': datetime.now().isoformat()
        }
    
    def monitoring_decorator(self, sandbox: bool = True):
        """
        Create a decorator to monitor FIRS API calls.
        
        This decorator wraps API methods to automatically record
        performance metrics and errors.
        
        Args:
            sandbox: Whether the API is in sandbox mode
        
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                environment = "sandbox" if sandbox else "production"
                endpoint = func.__name__
                start_time = time.time()
                request_id = None
                error_message = None
                status_code = 0
                
                try:
                    # Extract request ID if available in kwargs
                    if 'request_id' in kwargs:
                        request_id = kwargs['request_id']
                    
                    # Call the original function
                    result = await func(*args, **kwargs)
                    
                    # Extract status code if result has it
                    if hasattr(result, 'status_code'):
                        status_code = result.status_code
                    else:
                        # Assume success if no status_code attribute
                        status_code = 200
                    
                    return result
                    
                except Exception as e:
                    error_message = str(e)
                    if hasattr(e, 'status_code'):
                        status_code = e.status_code
                    else:
                        status_code = 500
                    
                    # Re-raise the exception
                    raise
                    
                finally:
                    # Calculate duration and record request
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    
                    self.record_request(
                        endpoint=endpoint,
                        method='ASYNC',  # Method is always async in this context
                        duration_ms=duration_ms,
                        status_code=status_code,
                        environment=environment,
                        request_id=request_id,
                        error=error_message
                    )
            
            return wrapper
        
        return decorator


# Create a global instance for use throughout the application
firs_api_monitor = FIRSAPIMonitor()

# Create decorator instances for both environments
monitor_sandbox_api = firs_api_monitor.monitoring_decorator(sandbox=True)
monitor_production_api = firs_api_monitor.monitoring_decorator(sandbox=False)
