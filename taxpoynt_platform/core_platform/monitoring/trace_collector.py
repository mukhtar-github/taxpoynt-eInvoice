"""
Trace Collector - Core Platform Observability

Distributed tracing system for the TaxPoynt platform.
Collects, processes, and analyzes traces across all services and components.
"""

import asyncio
import logging
import time
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SpanKind(Enum):
    """Types of spans in distributed tracing"""
    SERVER = "server"        # Receiving a request
    CLIENT = "client"        # Making a request
    PRODUCER = "producer"    # Producing a message
    CONSUMER = "consumer"    # Consuming a message
    INTERNAL = "internal"    # Internal function call


class SpanStatus(Enum):
    """Status of a span"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SpanContext:
    """Context information for a span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 0
    trace_state: Dict[str, str] = field(default_factory=dict)


@dataclass
class Span:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    service_role: str
    span_kind: SpanKind
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: SpanStatus = SpanStatus.OK
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    baggage: Dict[str, str] = field(default_factory=dict)
    references: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class Trace:
    """Complete distributed trace"""
    trace_id: str
    root_span_id: str
    spans: List[Span]
    start_time: datetime
    end_time: datetime
    duration_ms: int
    service_count: int
    span_count: int
    error_count: int
    services: Set[str] = field(default_factory=set)
    operations: Set[str] = field(default_factory=set)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SamplingRule:
    """Configuration for trace sampling"""
    rule_id: str
    name: str
    service_patterns: List[str] = field(default_factory=list)
    operation_patterns: List[str] = field(default_factory=list)
    tag_filters: Dict[str, str] = field(default_factory=dict)
    sample_rate: float = 1.0  # 0.0 to 1.0
    enabled: bool = True
    priority: int = 0  # Higher priority rules evaluated first


class TraceCollector:
    """
    Distributed tracing collector for the TaxPoynt platform.
    
    Collects traces from all platform components:
    - SI Services (ERP integration flows, certificate generation, etc.)
    - APP Services (FIRS communication, taxpayer onboarding, etc.)
    - Hybrid Services (billing workflows, analytics pipelines, etc.)
    - Core Platform (authentication flows, data operations, etc.)
    - External Integrations (third-party API calls, etc.)
    """
    
    def __init__(self, max_spans: int = 100000, trace_retention_hours: int = 168):
        # Span storage
        self.active_spans: Dict[str, Span] = {}  # span_id -> Span
        self.completed_spans: deque = deque(maxlen=max_spans)
        self.traces: Dict[str, Trace] = {}  # trace_id -> Trace
        
        # Configuration
        self.trace_retention_hours = trace_retention_hours
        self.sampling_rules: List[SamplingRule] = []
        self.default_sample_rate = 0.1  # 10% sampling by default
        
        # Thread-local storage for current span context
        self._local = threading.local()
        
        # Background tasks
        self._running = False
        self._processor_task = None
        self._cleanup_task = None
        
        # Processing queues
        self.span_queue: asyncio.Queue = asyncio.Queue()
        self.trace_complete_queue: asyncio.Queue = asyncio.Queue()
        
        # Statistics
        self.stats = {
            "total_spans": 0,
            "total_traces": 0,
            "spans_dropped": 0,
            "traces_completed": 0,
            "avg_trace_duration_ms": 0,
            "avg_spans_per_trace": 0,
            "error_rate": 0.0
        }
        
        # Event handlers
        self.span_finished_handlers: List[Callable] = []
        self.trace_finished_handlers: List[Callable] = []
        
        # Dependencies
        self.metrics_aggregator = None
    
    # === Dependency Injection ===
    
    def set_metrics_aggregator(self, metrics_aggregator):
        """Inject metrics aggregator dependency"""
        self.metrics_aggregator = metrics_aggregator
    
    # === Span Context Management ===
    
    def _get_current_context(self) -> Optional[SpanContext]:
        """Get current span context from thread-local storage"""
        return getattr(self._local, 'current_context', None)
    
    def _set_current_context(self, context: Optional[SpanContext]):
        """Set current span context in thread-local storage"""
        self._local.current_context = context
    
    def get_current_span_id(self) -> Optional[str]:
        """Get the current active span ID"""
        context = self._get_current_context()
        return context.span_id if context else None
    
    def get_current_trace_id(self) -> Optional[str]:
        """Get the current active trace ID"""
        context = self._get_current_context()
        return context.trace_id if context else None
    
    # === Span Management ===
    
    def start_span(
        self,
        operation_name: str,
        service_name: str,
        service_role: str,
        span_kind: SpanKind = SpanKind.INTERNAL,
        parent_span_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        baggage: Optional[Dict[str, str]] = None
    ) -> str:
        """Start a new span"""
        
        # Generate IDs
        span_id = str(uuid.uuid4())
        
        if not trace_id:
            # Check if we have a current context
            current_context = self._get_current_context()
            if current_context:
                trace_id = current_context.trace_id
                if not parent_span_id:
                    parent_span_id = current_context.span_id
            else:
                # Start new trace
                trace_id = str(uuid.uuid4())
        
        # Apply sampling
        if not self._should_sample(trace_id, service_name, operation_name, tags or {}):
            # Return a no-op span ID
            return f"noop_{span_id}"
        
        # Create span
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=service_name,
            service_role=service_role,
            span_kind=span_kind,
            start_time=datetime.utcnow(),
            tags=tags or {},
            baggage=baggage or {}
        )
        
        # Store active span
        self.active_spans[span_id] = span
        
        # Update current context
        new_context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id
        )
        self._set_current_context(new_context)
        
        logger.debug(f"Started span: {operation_name} [{span_id}] in trace [{trace_id}]")
        return span_id
    
    def finish_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        error: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """Finish a span"""
        
        # Handle no-op spans
        if span_id.startswith("noop_"):
            return True
        
        if span_id not in self.active_spans:
            logger.warning(f"Attempted to finish unknown span: {span_id}")
            return False
        
        span = self.active_spans[span_id]
        
        # Complete the span
        span.end_time = datetime.utcnow()
        span.duration_ms = int((span.end_time - span.start_time).total_seconds() * 1000)
        span.status = status
        
        if error:
            span.error = error
            span.status = SpanStatus.ERROR
        
        if tags:
            span.tags.update(tags)
        
        # Move to completed spans
        del self.active_spans[span_id]
        self.completed_spans.append(span)
        
        # Update statistics
        self.stats["total_spans"] += 1
        
        # Queue for processing
        asyncio.create_task(self.span_queue.put(span))
        
        # Reset context if this was the current span
        current_context = self._get_current_context()
        if current_context and current_context.span_id == span_id:
            # Set context to parent span if available
            if span.parent_span_id and span.parent_span_id in self.active_spans:
                parent_span = self.active_spans[span.parent_span_id]
                parent_context = SpanContext(
                    trace_id=parent_span.trace_id,
                    span_id=parent_span.span_id,
                    parent_span_id=parent_span.parent_span_id
                )
                self._set_current_context(parent_context)
            else:
                self._set_current_context(None)
        
        # Notify handlers
        asyncio.create_task(self._notify_span_finished_handlers(span))
        
        logger.debug(f"Finished span: {span.operation_name} [{span_id}] - {span.duration_ms}ms")
        return True
    
    def add_span_tag(self, span_id: str, key: str, value: str) -> bool:
        """Add a tag to an active span"""
        if span_id.startswith("noop_"):
            return True
            
        if span_id in self.active_spans:
            self.active_spans[span_id].tags[key] = value
            return True
        return False
    
    def add_span_log(self, span_id: str, message: str, level: str = "info", fields: Optional[Dict[str, Any]] = None) -> bool:
        """Add a log entry to an active span"""
        if span_id.startswith("noop_"):
            return True
            
        if span_id in self.active_spans:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "message": message,
                "level": level,
                "fields": fields or {}
            }
            self.active_spans[span_id].logs.append(log_entry)
            return True
        return False
    
    def set_span_error(self, span_id: str, error: str) -> bool:
        """Mark a span as having an error"""
        if span_id.startswith("noop_"):
            return True
            
        if span_id in self.active_spans:
            self.active_spans[span_id].error = error
            self.active_spans[span_id].status = SpanStatus.ERROR
            return True
        return False
    
    # === Context Managers ===
    
    @contextmanager
    def trace_span(
        self,
        operation_name: str,
        service_name: str,
        service_role: str,
        span_kind: SpanKind = SpanKind.INTERNAL,
        tags: Optional[Dict[str, str]] = None
    ):
        """Context manager for tracing a span"""
        span_id = self.start_span(
            operation_name=operation_name,
            service_name=service_name,
            service_role=service_role,
            span_kind=span_kind,
            tags=tags
        )
        
        try:
            yield span_id
        except Exception as e:
            self.set_span_error(span_id, str(e))
            raise
        finally:
            self.finish_span(span_id)
    
    # === Trace Assembly ===
    
    async def _process_completed_span(self, span: Span):
        """Process a completed span and potentially complete traces"""
        trace_id = span.trace_id
        
        # Check if trace is complete
        if await self._is_trace_complete(trace_id):
            trace = await self._assemble_trace(trace_id)
            if trace:
                self.traces[trace_id] = trace
                await self.trace_complete_queue.put(trace)
                await self._notify_trace_finished_handlers(trace)
                
                # Update statistics
                self.stats["total_traces"] += 1
                self.stats["traces_completed"] += 1
                self._update_trace_stats(trace)
    
    async def _is_trace_complete(self, trace_id: str) -> bool:
        """Check if a trace has all spans completed"""
        # For now, use a simple heuristic: no active spans in this trace for 5 seconds
        trace_spans = [s for s in self.active_spans.values() if s.trace_id == trace_id]
        
        if not trace_spans:
            # No active spans, check if we have completed spans for this trace
            completed_trace_spans = [s for s in self.completed_spans if s.trace_id == trace_id]
            return len(completed_trace_spans) > 0
        
        return False
    
    async def _assemble_trace(self, trace_id: str) -> Optional[Trace]:
        """Assemble a complete trace from spans"""
        # Get all spans for this trace
        trace_spans = [s for s in self.completed_spans if s.trace_id == trace_id]
        
        if not trace_spans:
            return None
        
        # Sort spans by start time
        trace_spans.sort(key=lambda s: s.start_time)
        
        # Find root span (span without parent)
        root_spans = [s for s in trace_spans if s.parent_span_id is None]
        root_span_id = root_spans[0].span_id if root_spans else trace_spans[0].span_id
        
        # Calculate trace metrics
        start_time = min(s.start_time for s in trace_spans)
        end_time = max(s.end_time for s in trace_spans if s.end_time)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        services = set(s.service_name for s in trace_spans)
        operations = set(s.operation_name for s in trace_spans)
        error_count = len([s for s in trace_spans if s.status == SpanStatus.ERROR])
        
        # Aggregate tags from all spans
        all_tags = {}
        for span in trace_spans:
            all_tags.update(span.tags)
        
        trace = Trace(
            trace_id=trace_id,
            root_span_id=root_span_id,
            spans=trace_spans,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            service_count=len(services),
            span_count=len(trace_spans),
            error_count=error_count,
            services=services,
            operations=operations,
            tags=all_tags
        )
        
        return trace
    
    # === Sampling ===
    
    def add_sampling_rule(
        self,
        rule_id: str,
        name: str,
        sample_rate: float,
        service_patterns: Optional[List[str]] = None,
        operation_patterns: Optional[List[str]] = None,
        tag_filters: Optional[Dict[str, str]] = None,
        priority: int = 0
    ) -> bool:
        """Add a sampling rule"""
        try:
            rule = SamplingRule(
                rule_id=rule_id,
                name=name,
                service_patterns=service_patterns or [],
                operation_patterns=operation_patterns or [],
                tag_filters=tag_filters or {},
                sample_rate=sample_rate,
                priority=priority
            )
            
            self.sampling_rules.append(rule)
            
            # Sort by priority (higher first)
            self.sampling_rules.sort(key=lambda r: r.priority, reverse=True)
            
            logger.info(f"Added sampling rule: {rule_id} (rate: {sample_rate})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add sampling rule {rule_id}: {e}")
            return False
    
    def _should_sample(self, trace_id: str, service_name: str, operation_name: str, tags: Dict[str, str]) -> bool:
        """Determine if a trace should be sampled"""
        
        # Check sampling rules in priority order
        for rule in self.sampling_rules:
            if not rule.enabled:
                continue
            
            if self._rule_matches(rule, service_name, operation_name, tags):
                return self._sample_decision(trace_id, rule.sample_rate)
        
        # Use default sampling rate
        return self._sample_decision(trace_id, self.default_sample_rate)
    
    def _rule_matches(self, rule: SamplingRule, service_name: str, operation_name: str, tags: Dict[str, str]) -> bool:
        """Check if a sampling rule matches the span"""
        import re
        
        # Check service patterns
        if rule.service_patterns:
            if not any(re.search(pattern, service_name) for pattern in rule.service_patterns):
                return False
        
        # Check operation patterns
        if rule.operation_patterns:
            if not any(re.search(pattern, operation_name) for pattern in rule.operation_patterns):
                return False
        
        # Check tag filters
        for tag_key, tag_value in rule.tag_filters.items():
            if tags.get(tag_key) != tag_value:
                return False
        
        return True
    
    def _sample_decision(self, trace_id: str, sample_rate: float) -> bool:
        """Make sampling decision based on trace ID and rate"""
        if sample_rate >= 1.0:
            return True
        if sample_rate <= 0.0:
            return False
        
        # Use trace ID hash for consistent sampling decisions
        trace_hash = hash(trace_id) % 1000000
        threshold = int(sample_rate * 1000000)
        
        return trace_hash < threshold
    
    # === Querying and Analysis ===
    
    def get_trace_by_id(self, trace_id: str) -> Optional[Trace]:
        """Get a specific trace by ID"""
        return self.traces.get(trace_id)
    
    def get_traces(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        min_duration_ms: Optional[int] = None,
        max_duration_ms: Optional[int] = None,
        has_errors: Optional[bool] = None,
        hours: Optional[int] = None,
        limit: int = 100
    ) -> List[Trace]:
        """Get traces with optional filtering"""
        traces = list(self.traces.values())
        
        # Apply filters
        if service_name:
            traces = [t for t in traces if service_name in t.services]
        
        if operation_name:
            traces = [t for t in traces if operation_name in t.operations]
        
        if min_duration_ms is not None:
            traces = [t for t in traces if t.duration_ms >= min_duration_ms]
        
        if max_duration_ms is not None:
            traces = [t for t in traces if t.duration_ms <= max_duration_ms]
        
        if has_errors is not None:
            if has_errors:
                traces = [t for t in traces if t.error_count > 0]
            else:
                traces = [t for t in traces if t.error_count == 0]
        
        if hours is not None:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            traces = [t for t in traces if t.start_time >= cutoff_time]
        
        # Sort by start time descending
        traces.sort(key=lambda t: t.start_time, reverse=True)
        
        # Apply limit
        return traces[:limit]
    
    def get_service_dependencies(self, hours: int = 24) -> Dict[str, List[str]]:
        """Analyze service dependencies from traces"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_traces = [t for t in self.traces.values() if t.start_time >= cutoff_time]
        
        dependencies = defaultdict(set)
        
        for trace in recent_traces:
            # Build dependency graph from span relationships
            spans_by_id = {s.span_id: s for s in trace.spans}
            
            for span in trace.spans:
                if span.parent_span_id and span.parent_span_id in spans_by_id:
                    parent_span = spans_by_id[span.parent_span_id]
                    
                    # Parent service depends on child service
                    if parent_span.service_name != span.service_name:
                        dependencies[parent_span.service_name].add(span.service_name)
        
        # Convert sets to lists
        return {service: list(deps) for service, deps in dependencies.items()}
    
    def get_operation_performance(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Analyze operation performance metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_spans = [
            s for s in self.completed_spans
            if s.start_time >= cutoff_time and s.duration_ms is not None
        ]
        
        # Group by operation
        by_operation = defaultdict(list)
        for span in recent_spans:
            operation_key = f"{span.service_name}.{span.operation_name}"
            by_operation[operation_key].append(span)
        
        # Calculate metrics for each operation
        performance = {}
        for operation, spans in by_operation.items():
            durations = [s.duration_ms for s in spans]
            errors = [s for s in spans if s.status == SpanStatus.ERROR]
            
            performance[operation] = {
                "call_count": len(spans),
                "error_count": len(errors),
                "error_rate": len(errors) / len(spans) * 100,
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p95_duration_ms": self._calculate_percentile(durations, 95),
                "p99_duration_ms": self._calculate_percentile(durations, 99)
            }
        
        return performance
    
    def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze errors across traces and spans"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Analyze traces with errors
        recent_traces = [t for t in self.traces.values() if t.start_time >= cutoff_time]
        error_traces = [t for t in recent_traces if t.error_count > 0]
        
        # Analyze error spans
        recent_spans = [s for s in self.completed_spans if s.start_time >= cutoff_time]
        error_spans = [s for s in recent_spans if s.status == SpanStatus.ERROR]
        
        # Group errors by service
        errors_by_service = defaultdict(int)
        for span in error_spans:
            errors_by_service[span.service_name] += 1
        
        # Group errors by operation
        errors_by_operation = defaultdict(int)
        for span in error_spans:
            operation = f"{span.service_name}.{span.operation_name}"
            errors_by_operation[operation] += 1
        
        return {
            "total_traces": len(recent_traces),
            "error_traces": len(error_traces),
            "trace_error_rate": len(error_traces) / len(recent_traces) * 100 if recent_traces else 0,
            "total_spans": len(recent_spans),
            "error_spans": len(error_spans),
            "span_error_rate": len(error_spans) / len(recent_spans) * 100 if recent_spans else 0,
            "errors_by_service": dict(errors_by_service),
            "errors_by_operation": dict(sorted(errors_by_operation.items(), key=lambda x: x[1], reverse=True)[:10]),
            "common_errors": self._get_common_error_messages(error_spans)
        }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_values):
            return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
        else:
            return sorted_values[f]
    
    def _get_common_error_messages(self, error_spans: List[Span]) -> List[Dict[str, Any]]:
        """Get most common error messages"""
        error_counts = defaultdict(int)
        
        for span in error_spans:
            if span.error:
                # Normalize error message (first line only)
                error_msg = span.error.split('\n')[0][:100]
                error_counts[error_msg] += 1
        
        # Return top 5 errors
        return [
            {"message": msg, "count": count}
            for msg, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    # === Background Tasks ===
    
    async def start_trace_processing(self):
        """Start background trace processing"""
        if self._running:
            return
        
        self._running = True
        
        # Start processor tasks
        self._processor_task = asyncio.create_task(self._process_spans())
        self._cleanup_task = asyncio.create_task(self._cleanup_old_traces())
        
        logger.info("Trace processing started")
    
    async def stop_trace_processing(self):
        """Stop background trace processing"""
        self._running = False
        
        # Cancel tasks
        for task in [self._processor_task, self._cleanup_task]:
            if task:
                task.cancel()
        
        logger.info("Trace processing stopped")
    
    async def _process_spans(self):
        """Main span processing loop"""
        while self._running:
            try:
                # Get span from queue with timeout
                span = await asyncio.wait_for(self.span_queue.get(), timeout=1.0)
                
                # Process the span
                await self._process_completed_span(span)
                
                # Send metrics if available
                if self.metrics_aggregator:
                    await self._send_span_metrics(span)
                
                # Mark task as done
                self.span_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing span: {e}")
                await asyncio.sleep(1)
    
    async def _cleanup_old_traces(self):
        """Clean up old traces and spans"""
        while self._running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=self.trace_retention_hours)
                
                # Clean up traces
                old_trace_ids = [
                    trace_id for trace_id, trace in self.traces.items()
                    if trace.start_time < cutoff_time
                ]
                
                for trace_id in old_trace_ids:
                    del self.traces[trace_id]
                
                if old_trace_ids:
                    logger.info(f"Cleaned up {len(old_trace_ids)} old traces")
                
                await asyncio.sleep(3600)  # Run every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)
    
    # === Event Handling ===
    
    async def _notify_span_finished_handlers(self, span: Span):
        """Notify span finished handlers"""
        for handler in self.span_finished_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(span)
                else:
                    handler(span)
            except Exception as e:
                logger.error(f"Error in span finished handler: {e}")
    
    async def _notify_trace_finished_handlers(self, trace: Trace):
        """Notify trace finished handlers"""
        for handler in self.trace_finished_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(trace)
                else:
                    handler(trace)
            except Exception as e:
                logger.error(f"Error in trace finished handler: {e}")
    
    async def _send_span_metrics(self, span: Span):
        """Send span metrics to metrics aggregator"""
        try:
            # Send span duration metric
            if span.duration_ms is not None:
                await self.metrics_aggregator.collect_metric_point(
                    name="trace_span_duration_ms",
                    value=span.duration_ms,
                    service_role=span.service_role,
                    service_name=span.service_name,
                    tags={
                        "operation": span.operation_name,
                        "span_kind": span.span_kind.value,
                        "status": span.status.value
                    }
                )
            
            # Send span count metric
            await self.metrics_aggregator.collect_metric_point(
                name="trace_spans_completed",
                value=1,
                service_role=span.service_role,
                service_name=span.service_name,
                tags={"operation": span.operation_name}
            )
            
        except Exception as e:
            logger.error(f"Error sending span metrics: {e}")
    
    def _update_trace_stats(self, trace: Trace):
        """Update trace statistics"""
        # Update average trace duration
        current_avg = self.stats["avg_trace_duration_ms"]
        trace_count = self.stats["total_traces"]
        
        if trace_count == 1:
            self.stats["avg_trace_duration_ms"] = trace.duration_ms
        else:
            self.stats["avg_trace_duration_ms"] = (
                (current_avg * (trace_count - 1) + trace.duration_ms) / trace_count
            )
        
        # Update average spans per trace
        current_avg_spans = self.stats["avg_spans_per_trace"]
        if trace_count == 1:
            self.stats["avg_spans_per_trace"] = trace.span_count
        else:
            self.stats["avg_spans_per_trace"] = (
                (current_avg_spans * (trace_count - 1) + trace.span_count) / trace_count
            )
        
        # Update error rate
        total_spans = self.stats["total_spans"]
        if total_spans > 0:
            error_spans = sum(1 for s in self.completed_spans if s.status == SpanStatus.ERROR)
            self.stats["error_rate"] = error_spans / total_spans * 100
    
    # === Handler Management ===
    
    def add_span_finished_handler(self, handler: Callable):
        """Add handler for span finished events"""
        self.span_finished_handlers.append(handler)
    
    def add_trace_finished_handler(self, handler: Callable):
        """Add handler for trace finished events"""
        self.trace_finished_handlers.append(handler)
    
    def remove_span_finished_handler(self, handler: Callable):
        """Remove span finished handler"""
        if handler in self.span_finished_handlers:
            self.span_finished_handlers.remove(handler)
    
    def remove_trace_finished_handler(self, handler: Callable):
        """Remove trace finished handler"""
        if handler in self.trace_finished_handlers:
            self.trace_finished_handlers.remove(handler)
    
    # === Health and Status ===
    
    def get_trace_collector_health(self) -> Dict[str, Any]:
        """Get health status of the trace collector"""
        return {
            "status": "running" if self._running else "stopped",
            "active_spans": len(self.active_spans),
            "completed_spans": len(self.completed_spans),
            "stored_traces": len(self.traces),
            "sampling_rules": len(self.sampling_rules),
            "queue_sizes": {
                "span_queue": self.span_queue.qsize(),
                "trace_complete_queue": self.trace_complete_queue.qsize()
            },
            "statistics": self.stats.copy()
        }


# Global instance for platform-wide access
trace_collector = TraceCollector()


# Convenience decorators and functions
def trace_function(operation_name: str, service_name: str, service_role: str, tags: Optional[Dict[str, str]] = None):
    """Decorator to trace a function"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with trace_collector.trace_span(operation_name, service_name, service_role, tags=tags):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with trace_collector.trace_span(operation_name, service_name, service_role, tags=tags):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


async def setup_default_sampling_rules():
    """Setup default sampling rules"""
    
    # High sampling for critical operations
    trace_collector.add_sampling_rule(
        rule_id="critical_operations",
        name="Critical Operations",
        service_patterns=["authentication.*", "firs_communication.*"],
        sample_rate=1.0,  # 100% sampling
        priority=100
    )
    
    # Medium sampling for important services
    trace_collector.add_sampling_rule(
        rule_id="important_services",
        name="Important Services",
        service_patterns=[".*integration.*", ".*validation.*"],
        sample_rate=0.5,  # 50% sampling
        priority=50
    )
    
    # Low sampling for verbose operations
    trace_collector.add_sampling_rule(
        rule_id="verbose_operations",
        name="Verbose Operations",
        operation_patterns=[".*health.*", ".*metrics.*"],
        sample_rate=0.1,  # 10% sampling
        priority=10
    )
    
    logger.info("Default sampling rules setup completed")


async def shutdown_trace_collection():
    """Shutdown trace collection"""
    await trace_collector.stop_trace_processing()
    logger.info("Trace collection shutdown completed")