"""
Log Aggregator - Core Platform Observability

Centralized log aggregation and analysis system for the TaxPoynt platform.
Collects, processes, and analyzes logs from all platform services and components.
"""

import asyncio
import logging
import time
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, TextIO
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels"""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogFormat(Enum):
    """Log formats"""
    JSON = "json"
    PLAIN = "plain"
    STRUCTURED = "structured"


@dataclass
class LogEntry:
    """Individual log entry"""
    log_id: str
    timestamp: datetime
    level: LogLevel
    message: str
    service_name: str
    service_role: str
    logger_name: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    thread_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    fields: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    exception_type: Optional[str] = None
    raw_log: Optional[str] = None


@dataclass
class LogPattern:
    """Pattern for log parsing and matching"""
    pattern_id: str
    name: str
    description: str
    regex_pattern: str
    field_mappings: Dict[str, str]  # regex group -> field mapping
    service_filters: List[str] = field(default_factory=list)
    level_filters: List[LogLevel] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0


@dataclass
class LogMetric:
    """Metric derived from log analysis"""
    metric_name: str
    value: Union[int, float]
    timestamp: datetime
    service_name: str
    service_role: str
    tags: Dict[str, str] = field(default_factory=dict)
    source_logs: List[str] = field(default_factory=list)  # log IDs


@dataclass
class LogAlert:
    """Alert triggered from log analysis"""
    alert_id: str
    pattern_id: str
    trigger_condition: str
    matched_logs: List[LogEntry]
    triggered_at: datetime
    severity: str
    message: str
    count: int
    time_window: timedelta


class LogAggregator:
    """
    Centralized log aggregation system for the TaxPoynt platform.
    
    Aggregates logs from all platform components:
    - SI Services (ERP integration logs, certificate management logs, etc.)
    - APP Services (FIRS communication logs, taxpayer management logs, etc.)
    - Hybrid Services (billing logs, analytics logs, workflow logs, etc.)
    - Core Platform (authentication logs, database logs, messaging logs, etc.)
    - External Integrations (third-party API logs, connector logs, etc.)
    """
    
    def __init__(self, max_logs: int = 1000000, retention_hours: int = 168):
        # Log storage
        self.logs: deque = deque(maxlen=max_logs)
        self.log_index: Dict[str, LogEntry] = {}  # log_id -> LogEntry
        self.retention_hours = retention_hours
        
        # Log sources and handlers
        self.log_handlers: Dict[str, logging.Handler] = {}
        self.log_sources: Set[str] = set()
        
        # Processing and parsing
        self.log_patterns: List[LogPattern] = []
        self.parsing_rules: Dict[str, Callable] = {}
        
        # Analysis and metrics
        self.log_metrics: deque = deque(maxlen=50000)
        self.log_alerts: List[LogAlert] = []
        
        # Processing queues
        self.log_queue: asyncio.Queue = asyncio.Queue()
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        
        # Background tasks
        self._running = False
        self._processor_task = None
        self._analysis_task = None
        self._cleanup_task = None
        self._metrics_task = None
        
        # Statistics
        self.stats = {
            "total_logs": 0,
            "logs_by_level": {level.value: 0 for level in LogLevel},
            "logs_by_service": defaultdict(int),
            "logs_by_service_role": defaultdict(int),
            "parsing_errors": 0,
            "patterns_matched": 0,
            "alerts_triggered": 0,
            "metrics_generated": 0
        }
        
        # Event handlers
        self.log_received_handlers: List[Callable] = []
        self.alert_handlers: List[Callable] = []
        self.metric_handlers: List[Callable] = []
        
        # Dependencies
        self.metrics_aggregator = None
        self.alert_manager = None
        self.trace_collector = None
        
        # Configuration
        self.enable_real_time_analysis = True
        self.enable_metrics_generation = True
        self.enable_pattern_matching = True
    
    # === Dependency Injection ===
    
    def set_metrics_aggregator(self, metrics_aggregator):
        """Inject metrics aggregator dependency"""
        self.metrics_aggregator = metrics_aggregator
    
    def set_alert_manager(self, alert_manager):
        """Inject alert manager dependency"""
        self.alert_manager = alert_manager
    
    def set_trace_collector(self, trace_collector):
        """Inject trace collector dependency"""
        self.trace_collector = trace_collector
    
    # === Log Ingestion ===
    
    async def ingest_log_entry(
        self,
        message: str,
        level: LogLevel,
        service_name: str,
        service_role: str,
        logger_name: str = "root",
        timestamp: Optional[datetime] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        fields: Optional[Dict[str, Any]] = None,
        exception_info: Optional[Dict[str, Any]] = None,
        raw_log: Optional[str] = None
    ) -> str:
        """Ingest a single log entry"""
        
        log_id = str(uuid.uuid4())
        
        # Create log entry
        log_entry = LogEntry(
            log_id=log_id,
            timestamp=timestamp or datetime.utcnow(),
            level=level,
            message=message,
            service_name=service_name,
            service_role=service_role,
            logger_name=logger_name,
            trace_id=trace_id,
            span_id=span_id,
            user_id=user_id,
            request_id=request_id,
            tags=tags or {},
            fields=fields or {},
            raw_log=raw_log
        )
        
        # Add exception information if provided
        if exception_info:
            log_entry.exception_type = exception_info.get("type")
            log_entry.stack_trace = exception_info.get("stack_trace")
        
        # Store log
        self.logs.append(log_entry)
        self.log_index[log_id] = log_entry
        
        # Update statistics
        self.stats["total_logs"] += 1
        self.stats["logs_by_level"][level.value] += 1
        self.stats["logs_by_service"][service_name] += 1
        self.stats["logs_by_service_role"][service_role] += 1
        
        # Queue for processing
        await self.log_queue.put(log_entry)
        
        # Notify handlers
        await self._notify_log_received_handlers(log_entry)
        
        return log_id
    
    async def ingest_log_batch(self, log_entries: List[Dict[str, Any]]) -> List[str]:
        """Ingest multiple log entries in batch"""
        log_ids = []
        
        for log_data in log_entries:
            try:
                log_id = await self.ingest_log_entry(
                    message=log_data["message"],
                    level=LogLevel(log_data["level"]),
                    service_name=log_data["service_name"],
                    service_role=log_data["service_role"],
                    logger_name=log_data.get("logger_name", "root"),
                    timestamp=log_data.get("timestamp"),
                    trace_id=log_data.get("trace_id"),
                    span_id=log_data.get("span_id"),
                    user_id=log_data.get("user_id"),
                    request_id=log_data.get("request_id"),
                    tags=log_data.get("tags"),
                    fields=log_data.get("fields"),
                    exception_info=log_data.get("exception_info"),
                    raw_log=log_data.get("raw_log")
                )
                log_ids.append(log_id)
                
            except Exception as e:
                logger.error(f"Failed to ingest log entry: {e}")
                self.stats["parsing_errors"] += 1
        
        return log_ids
    
    async def ingest_raw_log(
        self,
        raw_log: str,
        service_name: str,
        service_role: str,
        log_format: LogFormat = LogFormat.PLAIN
    ) -> Optional[str]:
        """Parse and ingest a raw log line"""
        
        try:
            # Parse the raw log based on format
            if log_format == LogFormat.JSON:
                parsed_log = self._parse_json_log(raw_log, service_name, service_role)
            elif log_format == LogFormat.STRUCTURED:
                parsed_log = self._parse_structured_log(raw_log, service_name, service_role)
            else:
                parsed_log = self._parse_plain_log(raw_log, service_name, service_role)
            
            if parsed_log:
                return await self.ingest_log_entry(
                    message=parsed_log["message"],
                    level=parsed_log["level"],
                    service_name=service_name,
                    service_role=service_role,
                    logger_name=parsed_log.get("logger_name", "root"),
                    timestamp=parsed_log.get("timestamp"),
                    trace_id=parsed_log.get("trace_id"),
                    span_id=parsed_log.get("span_id"),
                    user_id=parsed_log.get("user_id"),
                    request_id=parsed_log.get("request_id"),
                    tags=parsed_log.get("tags"),
                    fields=parsed_log.get("fields"),
                    exception_info=parsed_log.get("exception_info"),
                    raw_log=raw_log
                )
        
        except Exception as e:
            logger.error(f"Failed to parse raw log: {e}")
            self.stats["parsing_errors"] += 1
        
        return None
    
    # === Log Parsing ===
    
    def _parse_json_log(self, raw_log: str, service_name: str, service_role: str) -> Optional[Dict[str, Any]]:
        """Parse JSON formatted log"""
        try:
            log_data = json.loads(raw_log)
            
            # Extract standard fields
            parsed = {
                "message": log_data.get("message", ""),
                "level": LogLevel(log_data.get("level", "info").lower()),
                "logger_name": log_data.get("logger", "root"),
                "trace_id": log_data.get("trace_id"),
                "span_id": log_data.get("span_id"),
                "user_id": log_data.get("user_id"),
                "request_id": log_data.get("request_id"),
                "tags": log_data.get("tags", {}),
                "fields": {k: v for k, v in log_data.items() if k not in [
                    "message", "level", "logger", "timestamp", "trace_id", "span_id", "user_id", "request_id", "tags"
                ]}
            }
            
            # Parse timestamp
            if "timestamp" in log_data:
                if isinstance(log_data["timestamp"], str):
                    parsed["timestamp"] = datetime.fromisoformat(log_data["timestamp"].replace('Z', '+00:00'))
                else:
                    parsed["timestamp"] = datetime.fromtimestamp(log_data["timestamp"])
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse JSON log: {e}")
            return None
    
    def _parse_structured_log(self, raw_log: str, service_name: str, service_role: str) -> Optional[Dict[str, Any]]:
        """Parse structured log format (key=value pairs)"""
        try:
            fields = {}
            
            # Simple key=value parsing
            for part in raw_log.split():
                if '=' in part:
                    key, value = part.split('=', 1)
                    fields[key.strip()] = value.strip().strip('"')
            
            parsed = {
                "message": fields.get("msg", fields.get("message", raw_log)),
                "level": LogLevel(fields.get("level", "info").lower()),
                "logger_name": fields.get("logger", "root"),
                "trace_id": fields.get("trace_id"),
                "span_id": fields.get("span_id"),
                "user_id": fields.get("user_id"),
                "request_id": fields.get("request_id"),
                "tags": {},
                "fields": {k: v for k, v in fields.items() if k not in [
                    "msg", "message", "level", "logger", "timestamp", "trace_id", "span_id", "user_id", "request_id"
                ]}
            }
            
            # Parse timestamp
            if "timestamp" in fields:
                try:
                    parsed["timestamp"] = datetime.fromisoformat(fields["timestamp"])
                except:
                    pass
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse structured log: {e}")
            return None
    
    def _parse_plain_log(self, raw_log: str, service_name: str, service_role: str) -> Optional[Dict[str, Any]]:
        """Parse plain text log format"""
        try:
            # Try to extract level from common patterns
            level = LogLevel.INFO
            message = raw_log.strip()
            
            level_patterns = {
                LogLevel.ERROR: r'\b(ERROR|error|Error)\b',
                LogLevel.WARNING: r'\b(WARN|WARNING|warn|warning|Warning)\b',
                LogLevel.INFO: r'\b(INFO|info|Info)\b',
                LogLevel.DEBUG: r'\b(DEBUG|debug|Debug)\b',
                LogLevel.CRITICAL: r'\b(CRITICAL|FATAL|critical|fatal|Critical|Fatal)\b'
            }
            
            for log_level, pattern in level_patterns.items():
                if re.search(pattern, raw_log):
                    level = log_level
                    break
            
            # Try to extract timestamp from beginning of log
            timestamp = None
            timestamp_patterns = [
                r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})',
                r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})',
                r'(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})'
            ]
            
            for pattern in timestamp_patterns:
                match = re.search(pattern, raw_log)
                if match:
                    try:
                        timestamp_str = match.group(1)
                        # Try different formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y %H:%M:%S', '%d-%m-%Y %H:%M:%S']:
                            try:
                                timestamp = datetime.strptime(timestamp_str, fmt)
                                break
                            except:
                                continue
                        break
                    except:
                        continue
            
            return {
                "message": message,
                "level": level,
                "logger_name": "root",
                "timestamp": timestamp,
                "tags": {},
                "fields": {}
            }
            
        except Exception as e:
            logger.error(f"Failed to parse plain log: {e}")
            return None
    
    # === Pattern Matching ===
    
    def add_log_pattern(
        self,
        pattern_id: str,
        name: str,
        description: str,
        regex_pattern: str,
        field_mappings: Dict[str, str],
        service_filters: Optional[List[str]] = None,
        level_filters: Optional[List[LogLevel]] = None,
        priority: int = 0
    ) -> bool:
        """Add a log pattern for matching and extraction"""
        try:
            pattern = LogPattern(
                pattern_id=pattern_id,
                name=name,
                description=description,
                regex_pattern=regex_pattern,
                field_mappings=field_mappings,
                service_filters=service_filters or [],
                level_filters=level_filters or [],
                priority=priority
            )
            
            self.log_patterns.append(pattern)
            
            # Sort by priority (higher first)
            self.log_patterns.sort(key=lambda p: p.priority, reverse=True)
            
            logger.info(f"Added log pattern: {pattern_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add log pattern {pattern_id}: {e}")
            return False
    
    def _match_log_patterns(self, log_entry: LogEntry) -> List[Dict[str, Any]]:
        """Match log entry against patterns"""
        matches = []
        
        for pattern in self.log_patterns:
            if not pattern.enabled:
                continue
            
            # Check filters
            if pattern.service_filters and log_entry.service_name not in pattern.service_filters:
                continue
            
            if pattern.level_filters and log_entry.level not in pattern.level_filters:
                continue
            
            # Try to match regex
            try:
                match = re.search(pattern.regex_pattern, log_entry.message)
                if match:
                    # Extract fields based on mappings
                    extracted_fields = {}
                    for group_name, field_name in pattern.field_mappings.items():
                        try:
                            if group_name.isdigit():
                                extracted_fields[field_name] = match.group(int(group_name))
                            else:
                                extracted_fields[field_name] = match.group(group_name)
                        except (IndexError, KeyError):
                            pass
                    
                    matches.append({
                        "pattern_id": pattern.pattern_id,
                        "pattern_name": pattern.name,
                        "extracted_fields": extracted_fields,
                        "full_match": match.group(0)
                    })
                    
                    self.stats["patterns_matched"] += 1
            
            except Exception as e:
                logger.error(f"Error matching pattern {pattern.pattern_id}: {e}")
        
        return matches
    
    # === Log Querying ===
    
    def get_logs(
        self,
        service_name: Optional[str] = None,
        service_role: Optional[str] = None,
        level: Optional[LogLevel] = None,
        logger_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        message_contains: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[LogEntry]:
        """Query logs with filtering"""
        
        filtered_logs = []
        
        # Apply filters
        for log_entry in reversed(list(self.logs)):  # Most recent first
            if service_name and log_entry.service_name != service_name:
                continue
            
            if service_role and log_entry.service_role != service_role:
                continue
            
            if level and log_entry.level != level:
                continue
            
            if logger_name and log_entry.logger_name != logger_name:
                continue
            
            if trace_id and log_entry.trace_id != trace_id:
                continue
            
            if user_id and log_entry.user_id != user_id:
                continue
            
            if request_id and log_entry.request_id != request_id:
                continue
            
            if message_contains and message_contains.lower() not in log_entry.message.lower():
                continue
            
            if start_time and log_entry.timestamp < start_time:
                continue
            
            if end_time and log_entry.timestamp > end_time:
                continue
            
            filtered_logs.append(log_entry)
        
        # Apply offset and limit
        return filtered_logs[offset:offset + limit]
    
    def get_log_by_id(self, log_id: str) -> Optional[LogEntry]:
        """Get a specific log entry by ID"""
        return self.log_index.get(log_id)
    
    def search_logs(self, query: str, limit: int = 100) -> List[LogEntry]:
        """Search logs using simple text search"""
        matching_logs = []
        query_lower = query.lower()
        
        for log_entry in reversed(list(self.logs)):
            if (query_lower in log_entry.message.lower() or
                query_lower in log_entry.service_name.lower() or
                query_lower in log_entry.logger_name.lower() or
                any(query_lower in str(v).lower() for v in log_entry.fields.values())):
                
                matching_logs.append(log_entry)
                
                if len(matching_logs) >= limit:
                    break
        
        return matching_logs
    
    # === Log Analysis ===
    
    def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get log statistics for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_logs = [log for log in self.logs if log.timestamp >= cutoff_time]
        
        # Count by level
        by_level = defaultdict(int)
        for log in recent_logs:
            by_level[log.level.value] += 1
        
        # Count by service
        by_service = defaultdict(int)
        for log in recent_logs:
            by_service[log.service_name] += 1
        
        # Count by service role
        by_service_role = defaultdict(int)
        for log in recent_logs:
            by_service_role[log.service_role] += 1
        
        # Error analysis
        error_logs = [log for log in recent_logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        return {
            "time_period_hours": hours,
            "total_logs": len(recent_logs),
            "by_level": dict(by_level),
            "by_service": dict(sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_service_role": dict(by_service_role),
            "error_count": len(error_logs),
            "error_rate": len(error_logs) / len(recent_logs) * 100 if recent_logs else 0,
            "top_errors": self._get_top_error_messages(error_logs),
            "logs_per_minute": len(recent_logs) / (hours * 60) if hours > 0 else 0
        }
    
    def get_service_log_summary(self, service_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get log summary for a specific service"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        service_logs = [
            log for log in self.logs
            if log.service_name == service_name and log.timestamp >= cutoff_time
        ]
        
        if not service_logs:
            return {
                "service_name": service_name,
                "total_logs": 0,
                "message": "No logs found for service in time period"
            }
        
        # Analyze logs
        by_level = defaultdict(int)
        by_logger = defaultdict(int)
        
        for log in service_logs:
            by_level[log.level.value] += 1
            by_logger[log.logger_name] += 1
        
        error_logs = [log for log in service_logs if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        
        return {
            "service_name": service_name,
            "time_period_hours": hours,
            "total_logs": len(service_logs),
            "by_level": dict(by_level),
            "by_logger": dict(by_logger),
            "error_count": len(error_logs),
            "error_rate": len(error_logs) / len(service_logs) * 100,
            "recent_errors": [
                {
                    "timestamp": log.timestamp,
                    "message": log.message,
                    "logger": log.logger_name,
                    "trace_id": log.trace_id
                }
                for log in error_logs[-5:]  # Last 5 errors
            ],
            "logs_per_minute": len(service_logs) / (hours * 60) if hours > 0 else 0
        }
    
    def analyze_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns and trends"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        error_logs = [
            log for log in self.logs
            if log.level in [LogLevel.ERROR, LogLevel.CRITICAL] and log.timestamp >= cutoff_time
        ]
        
        if not error_logs:
            return {"total_errors": 0, "message": "No errors found in time period"}
        
        # Group by service
        errors_by_service = defaultdict(list)
        for log in error_logs:
            errors_by_service[log.service_name].append(log)
        
        # Group by error message pattern
        error_patterns = defaultdict(list)
        for log in error_logs:
            # Extract error pattern (first 100 chars, normalized)
            pattern = re.sub(r'\d+', 'N', log.message[:100]).strip()
            error_patterns[pattern].append(log)
        
        # Analyze trends (hourly buckets)
        hourly_errors = defaultdict(int)
        for log in error_logs:
            hour_key = log.timestamp.strftime('%Y-%m-%d %H:00')
            hourly_errors[hour_key] += 1
        
        return {
            "total_errors": len(error_logs),
            "time_period_hours": hours,
            "errors_by_service": {
                service: len(logs) for service, logs in errors_by_service.items()
            },
            "top_error_patterns": [
                {
                    "pattern": pattern,
                    "count": len(logs),
                    "services": list(set(log.service_name for log in logs)),
                    "last_occurrence": max(log.timestamp for log in logs)
                }
                for pattern, logs in sorted(error_patterns.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            ],
            "hourly_trend": dict(sorted(hourly_errors.items())),
            "error_rate_trend": self._calculate_error_rate_trend(error_logs, hours)
        }
    
    def _get_top_error_messages(self, error_logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Get most common error messages"""
        error_counts = defaultdict(int)
        
        for log in error_logs:
            # Normalize error message (first 150 chars)
            error_msg = log.message[:150]
            error_counts[error_msg] += 1
        
        return [
            {"message": msg, "count": count}
            for msg, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def _calculate_error_rate_trend(self, error_logs: List[LogEntry], hours: int) -> str:
        """Calculate error rate trend"""
        if hours < 2:
            return "insufficient_data"
        
        # Split into two halves
        midpoint = datetime.utcnow() - timedelta(hours=hours/2)
        
        first_half = [log for log in error_logs if log.timestamp < midpoint]
        second_half = [log for log in error_logs if log.timestamp >= midpoint]
        
        if not first_half:
            return "new_errors" if second_half else "stable"
        
        first_rate = len(first_half) / (hours/2 * 60)  # errors per minute
        second_rate = len(second_half) / (hours/2 * 60) if second_half else 0
        
        if second_rate > first_rate * 1.5:
            return "increasing"
        elif second_rate < first_rate * 0.5:
            return "decreasing"
        else:
            return "stable"
    
    # === Background Tasks ===
    
    async def start_log_processing(self):
        """Start background log processing"""
        if self._running:
            return
        
        self._running = True
        
        # Start processor tasks
        self._processor_task = asyncio.create_task(self._process_logs())
        self._analysis_task = asyncio.create_task(self._analyze_logs())
        self._cleanup_task = asyncio.create_task(self._cleanup_old_logs())
        self._metrics_task = asyncio.create_task(self._generate_log_metrics())
        
        logger.info("Log processing started")
    
    async def stop_log_processing(self):
        """Stop background log processing"""
        self._running = False
        
        # Cancel tasks
        for task in [self._processor_task, self._analysis_task, self._cleanup_task, self._metrics_task]:
            if task:
                task.cancel()
        
        logger.info("Log processing stopped")
    
    async def _process_logs(self):
        """Main log processing loop"""
        while self._running:
            try:
                # Get log from queue with timeout
                log_entry = await asyncio.wait_for(self.log_queue.get(), timeout=1.0)
                
                # Pattern matching
                if self.enable_pattern_matching:
                    matches = self._match_log_patterns(log_entry)
                    if matches:
                        log_entry.fields["pattern_matches"] = matches
                
                # Send to analysis queue if enabled
                if self.enable_real_time_analysis:
                    await self.analysis_queue.put(log_entry)
                
                # Send metrics if available
                if self.metrics_aggregator:
                    await self._send_log_metrics(log_entry)
                
                # Mark task as done
                self.log_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing log: {e}")
                await asyncio.sleep(1)
    
    async def _analyze_logs(self):
        """Log analysis loop"""
        while self._running:
            try:
                # Get log from analysis queue with timeout
                log_entry = await asyncio.wait_for(self.analysis_queue.get(), timeout=1.0)
                
                # Perform analysis (error detection, alerting, etc.)
                await self._analyze_log_entry(log_entry)
                
                # Mark task as done
                self.analysis_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in log analysis: {e}")
                await asyncio.sleep(1)
    
    async def _cleanup_old_logs(self):
        """Clean up old logs"""
        while self._running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
                
                # Remove from index
                old_log_ids = [
                    log_id for log_id, log_entry in self.log_index.items()
                    if log_entry.timestamp < cutoff_time
                ]
                
                for log_id in old_log_ids:
                    del self.log_index[log_id]
                
                if old_log_ids:
                    logger.info(f"Cleaned up {len(old_log_ids)} old log entries from index")
                
                await asyncio.sleep(3600)  # Run every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)
    
    async def _generate_log_metrics(self):
        """Generate metrics from log analysis"""
        while self._running:
            try:
                if not self.enable_metrics_generation:
                    await asyncio.sleep(60)
                    continue
                
                # Generate metrics every minute
                await self._calculate_and_store_metrics()
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error generating log metrics: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_log_entry(self, log_entry: LogEntry):
        """Analyze a single log entry"""
        try:
            # Check for critical errors that should trigger alerts
            if log_entry.level == LogLevel.CRITICAL and self.alert_manager:
                await self._trigger_critical_log_alert(log_entry)
            
            # Look for specific error patterns
            if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                await self._analyze_error_log(log_entry)
        
        except Exception as e:
            logger.error(f"Error analyzing log entry: {e}")
    
    async def _trigger_critical_log_alert(self, log_entry: LogEntry):
        """Trigger alert for critical log entry"""
        try:
            alert_data = {
                "title": f"Critical Log Alert: {log_entry.service_name}",
                "description": log_entry.message,
                "service_name": log_entry.service_name,
                "service_role": log_entry.service_role,
                "severity": "critical",
                "source": "log_aggregator",
                "log_id": log_entry.log_id,
                "timestamp": log_entry.timestamp,
                "tags": {
                    "logger": log_entry.logger_name,
                    "level": log_entry.level.value,
                    **log_entry.tags
                },
                "metadata": {
                    "trace_id": log_entry.trace_id,
                    "span_id": log_entry.span_id,
                    "user_id": log_entry.user_id,
                    "request_id": log_entry.request_id
                }
            }
            
            # Use alert manager to trigger alert
            # await self.alert_manager.trigger_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Error triggering log alert: {e}")
    
    async def _analyze_error_log(self, log_entry: LogEntry):
        """Analyze error log for patterns and insights"""
        # This could implement ML-based error classification,
        # correlation with other system events, etc.
        pass
    
    async def _calculate_and_store_metrics(self):
        """Calculate and store log-based metrics"""
        try:
            current_time = datetime.utcnow()
            last_minute = current_time - timedelta(minutes=1)
            
            # Get logs from last minute
            recent_logs = [log for log in self.logs if log.timestamp >= last_minute]
            
            if not recent_logs:
                return
            
            # Calculate metrics by service
            by_service = defaultdict(lambda: defaultdict(int))
            
            for log in recent_logs:
                by_service[log.service_name]["total"] += 1
                by_service[log.service_name][log.level.value] += 1
            
            # Store metrics
            for service_name, counts in by_service.items():
                service_role = next((log.service_role for log in recent_logs if log.service_name == service_name), "unknown")
                
                # Total logs metric
                metric = LogMetric(
                    metric_name="logs_per_minute",
                    value=counts["total"],
                    timestamp=current_time,
                    service_name=service_name,
                    service_role=service_role,
                    tags={"window": "1m"}
                )
                self.log_metrics.append(metric)
                
                # Error rate metric
                error_count = counts.get("error", 0) + counts.get("critical", 0)
                if counts["total"] > 0:
                    error_rate = error_count / counts["total"] * 100
                    metric = LogMetric(
                        metric_name="log_error_rate",
                        value=error_rate,
                        timestamp=current_time,
                        service_name=service_name,
                        service_role=service_role,
                        tags={"window": "1m"}
                    )
                    self.log_metrics.append(metric)
            
            self.stats["metrics_generated"] += len(by_service) * 2
            
        except Exception as e:
            logger.error(f"Error calculating log metrics: {e}")
    
    # === Event Handling ===
    
    async def _notify_log_received_handlers(self, log_entry: LogEntry):
        """Notify log received handlers"""
        for handler in self.log_received_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(log_entry)
                else:
                    handler(log_entry)
            except Exception as e:
                logger.error(f"Error in log received handler: {e}")
    
    async def _send_log_metrics(self, log_entry: LogEntry):
        """Send log metrics to metrics aggregator"""
        try:
            # Send log count metric
            await self.metrics_aggregator.collect_metric_point(
                name="log_entries_total",
                value=1,
                service_role=log_entry.service_role,
                service_name=log_entry.service_name,
                tags={
                    "level": log_entry.level.value,
                    "logger": log_entry.logger_name
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending log metrics: {e}")
    
    # === Handler Management ===
    
    def add_log_received_handler(self, handler: Callable):
        """Add handler for log received events"""
        self.log_received_handlers.append(handler)
    
    def add_alert_handler(self, handler: Callable):
        """Add handler for log alerts"""
        self.alert_handlers.append(handler)
    
    def add_metric_handler(self, handler: Callable):
        """Add handler for log metrics"""
        self.metric_handlers.append(handler)
    
    # === Health and Status ===
    
    def get_log_aggregator_health(self) -> Dict[str, Any]:
        """Get health status of the log aggregator"""
        return {
            "status": "running" if self._running else "stopped",
            "total_logs": len(self.logs),
            "indexed_logs": len(self.log_index),
            "log_patterns": len(self.log_patterns),
            "queue_sizes": {
                "log_queue": self.log_queue.qsize(),
                "analysis_queue": self.analysis_queue.qsize()
            },
            "configuration": {
                "retention_hours": self.retention_hours,
                "real_time_analysis": self.enable_real_time_analysis,
                "metrics_generation": self.enable_metrics_generation,
                "pattern_matching": self.enable_pattern_matching
            },
            "statistics": dict(self.stats)
        }


# Global instance for platform-wide access
log_aggregator = LogAggregator()


# Setup functions for easy integration
async def setup_default_log_patterns():
    """Setup default log patterns for common use cases"""
    
    # Authentication patterns
    log_aggregator.add_log_pattern(
        pattern_id="auth_failure",
        name="Authentication Failure",
        description="Detect authentication failures",
        regex_pattern=r"authentication failed|login failed|invalid credentials",
        field_mappings={"0": "auth_event"},
        level_filters=[LogLevel.ERROR, LogLevel.WARNING],
        priority=100
    )
    
    # Database patterns
    log_aggregator.add_log_pattern(
        pattern_id="db_connection_error",
        name="Database Connection Error",
        description="Detect database connection issues",
        regex_pattern=r"database connection|connection refused|connection timeout",
        field_mappings={"0": "db_event"},
        level_filters=[LogLevel.ERROR, LogLevel.CRITICAL],
        priority=90
    )
    
    # API patterns
    log_aggregator.add_log_pattern(
        pattern_id="api_error",
        name="API Error",
        description="Detect API errors",
        regex_pattern=r"HTTP (\d{3})|status code (\d{3})",
        field_mappings={"1": "status_code", "2": "status_code"},
        level_filters=[LogLevel.ERROR, LogLevel.WARNING],
        priority=80
    )
    
    logger.info("Default log patterns setup completed")


class PlatformLogHandler(logging.Handler):
    """Custom log handler that sends logs to the aggregator"""
    
    def __init__(self, service_name: str, service_role: str):
        super().__init__()
        self.service_name = service_name
        self.service_role = service_role
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record to the aggregator"""
        try:
            # Convert logging level to LogLevel enum
            level_mapping = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.CRITICAL
            }
            
            level = level_mapping.get(record.levelno, LogLevel.INFO)
            
            # Extract additional fields
            fields = {}
            if hasattr(record, 'trace_id'):
                fields['trace_id'] = record.trace_id
            if hasattr(record, 'span_id'):
                fields['span_id'] = record.span_id
            if hasattr(record, 'user_id'):
                fields['user_id'] = record.user_id
            if hasattr(record, 'request_id'):
                fields['request_id'] = record.request_id
            
            # Format exception info
            exception_info = None
            if record.exc_info:
                exception_info = {
                    "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                    "stack_trace": self.format(record) if record.exc_text else None
                }
            
            # Ingest log asynchronously
            asyncio.create_task(log_aggregator.ingest_log_entry(
                message=record.getMessage(),
                level=level,
                service_name=self.service_name,
                service_role=self.service_role,
                logger_name=record.name,
                timestamp=datetime.fromtimestamp(record.created),
                trace_id=fields.get('trace_id'),
                span_id=fields.get('span_id'),
                user_id=fields.get('user_id'),
                request_id=fields.get('request_id'),
                fields={
                    "module": record.module,
                    "function": record.funcName,
                    "line_number": record.lineno,
                    "thread_id": str(record.thread),
                    **fields
                },
                exception_info=exception_info
            ))
            
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Error in PlatformLogHandler: {e}")


async def shutdown_log_aggregation():
    """Shutdown log aggregation"""
    await log_aggregator.stop_log_processing()
    logger.info("Log aggregation shutdown completed")