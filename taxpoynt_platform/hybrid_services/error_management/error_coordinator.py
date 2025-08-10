"""
Hybrid Service: Error Coordinator
Coordinates error handling across SI and APP roles
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import traceback
import hashlib

from core_platform.database import get_db_session
from core_platform.models.errors import ErrorRecord, ErrorContext, ErrorPattern
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Types of errors in the platform"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    INTEGRATION = "integration"
    NETWORK = "network"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    CONCURRENCY = "concurrency"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorSource(str, Enum):
    """Source of the error"""
    SI_SERVICE = "si_service"
    APP_SERVICE = "app_service"
    CORE_PLATFORM = "core_platform"
    HYBRID_SERVICE = "hybrid_service"
    EXTERNAL_SYSTEM = "external_system"
    USER_INPUT = "user_input"


class ErrorStatus(str, Enum):
    """Status of error handling"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    IGNORED = "ignored"


class RecoveryAction(str, Enum):
    """Types of recovery actions"""
    RETRY = "retry"
    ROLLBACK = "rollback"
    COMPENSATE = "compensate"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    MANUAL_INTERVENTION = "manual_intervention"
    CIRCUIT_BREAK = "circuit_break"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class ErrorContext:
    """Context information for an error"""
    context_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    operation_name: str
    service_name: str
    role: str  # SI, APP, Core, Hybrid
    tenant_id: Optional[str]
    trace_id: Optional[str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ErrorRecord:
    """Detailed error record"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    source: ErrorSource
    context: ErrorContext
    error_message: str
    error_code: Optional[str]
    stack_trace: Optional[str]
    occurred_at: datetime
    fingerprint: str  # Hash for grouping similar errors
    correlation_id: Optional[str]
    retry_count: int = 0
    status: ErrorStatus = ErrorStatus.NEW
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ErrorPattern:
    """Pattern for grouping and analyzing errors"""
    pattern_id: str
    fingerprint: str
    error_type: ErrorType
    source: ErrorSource
    frequency: int
    first_occurrence: datetime
    last_occurrence: datetime
    affected_operations: List[str]
    common_characteristics: Dict[str, Any]
    suggested_actions: List[str]
    escalation_threshold: int
    auto_recovery_enabled: bool = False
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecoveryPlan:
    """Recovery plan for error handling"""
    plan_id: str
    error_id: str
    actions: List[RecoveryAction]
    priority: int
    estimated_duration_minutes: int
    success_probability: float
    rollback_plan: Optional[str] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ErrorCoordinator:
    """
    Error Coordinator service
    Coordinates error handling across SI and APP roles
    """
    
    def __init__(self):
        """Initialize error coordinator service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.error_records: Dict[str, ErrorRecord] = {}
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.error_handlers: Dict[ErrorType, List[Callable]] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 86400  # 24 hours
        self.pattern_detection_window = 3600  # 1 hour
        self.max_retry_attempts = 3
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        self.error_retention_days = 30
        
        # Initialize default handlers
        self._initialize_default_handlers()
    
    def _initialize_default_handlers(self):
        """Initialize default error handlers"""
        # Validation error handlers
        self.error_handlers[ErrorType.VALIDATION] = [
            self._handle_validation_error
        ]
        
        # Authentication error handlers
        self.error_handlers[ErrorType.AUTHENTICATION] = [
            self._handle_authentication_error
        ]
        
        # Integration error handlers
        self.error_handlers[ErrorType.INTEGRATION] = [
            self._handle_integration_error
        ]
        
        # Network error handlers
        self.error_handlers[ErrorType.NETWORK] = [
            self._handle_network_error
        ]
        
        # Database error handlers
        self.error_handlers[ErrorType.DATABASE] = [
            self._handle_database_error
        ]
        
        # System error handlers
        self.error_handlers[ErrorType.SYSTEM] = [
            self._handle_system_error
        ]
    
    async def initialize(self):
        """Initialize the error coordinator service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing error coordinator service")
        
        try:
            # Initialize dependencies
            await self.cache.initialize()
            await self.event_bus.initialize()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._pattern_detector())
            asyncio.create_task(self._recovery_monitor())
            asyncio.create_task(self._circuit_breaker_monitor())
            asyncio.create_task(self._cleanup_old_errors())
            
            self.is_initialized = True
            self.logger.info("Error coordinator service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing error coordinator service: {str(e)}")
            raise
    
    async def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        error_type: ErrorType = ErrorType.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retry_count: int = 0
    ) -> str:
        """Handle an error with full coordination"""
        try:
            # Create error record
            error_record = await self._create_error_record(
                error, context, error_type, severity, retry_count
            )
            
            # Store error
            self.error_records[error_record.error_id] = error_record
            
            # Cache error
            await self.cache.set(
                f"error:{error_record.error_id}",
                error_record.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Update pattern detection
            await self._update_error_patterns(error_record)
            
            # Execute error handlers
            await self._execute_error_handlers(error_record)
            
            # Check for circuit breaker action
            await self._check_circuit_breaker(error_record)
            
            # Emit error event
            await self.event_bus.emit(
                "error.occurred",
                {
                    "error_id": error_record.error_id,
                    "error_type": error_type,
                    "severity": severity,
                    "source": error_record.source,
                    "context": context.to_dict()
                }
            )
            
            # Update metrics
            await self.metrics_collector.increment(
                f"errors.{error_type}.{severity}",
                tags={
                    "source": error_record.source,
                    "service": context.service_name
                }
            )
            
            self.logger.error(
                f"Error handled: {error_type} from {error_record.source} - {error_record.error_message}",
                extra={
                    "error_id": error_record.error_id,
                    "context": context.to_dict()
                }
            )
            
            return error_record.error_id
            
        except Exception as e:
            self.logger.error(f"Error in error handling: {str(e)}")
            return ""
    
    async def _create_error_record(
        self,
        error: Exception,
        context: ErrorContext,
        error_type: ErrorType,
        severity: ErrorSeverity,
        retry_count: int
    ) -> ErrorRecord:
        """Create detailed error record"""
        try:
            error_message = str(error)
            stack_trace = traceback.format_exc() if hasattr(error, '__traceback__') else None
            
            # Generate fingerprint for grouping
            fingerprint_data = {
                "error_type": error_type,
                "error_class": error.__class__.__name__,
                "service": context.service_name,
                "operation": context.operation_name,
                "message_template": self._extract_message_template(error_message)
            }
            fingerprint = hashlib.sha256(
                json.dumps(fingerprint_data, sort_keys=True).encode()
            ).hexdigest()[:16]
            
            # Determine error source
            source = self._determine_error_source(context, error)
            
            # Generate correlation ID
            correlation_id = context.trace_id or context.request_id or str(uuid.uuid4())
            
            return ErrorRecord(
                error_id=str(uuid.uuid4()),
                error_type=error_type,
                severity=severity,
                source=source,
                context=context,
                error_message=error_message,
                error_code=getattr(error, 'code', None),
                stack_trace=stack_trace,
                occurred_at=datetime.now(timezone.utc),
                fingerprint=fingerprint,
                correlation_id=correlation_id,
                retry_count=retry_count,
                metadata={
                    "error_class": error.__class__.__name__,
                    "error_module": error.__class__.__module__,
                    "context_metadata": context.metadata or {}
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating error record: {str(e)}")
            raise
    
    def _extract_message_template(self, error_message: str) -> str:
        """Extract template from error message for pattern matching"""
        try:
            # Replace dynamic content with placeholders
            import re
            
            # Replace numbers with placeholder
            template = re.sub(r'\d+', '{number}', error_message)
            
            # Replace UUIDs with placeholder
            template = re.sub(
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                '{uuid}',
                template,
                flags=re.IGNORECASE
            )
            
            # Replace email addresses
            template = re.sub(r'\S+@\S+\.\S+', '{email}', template)
            
            # Replace URLs
            template = re.sub(r'https?://\S+', '{url}', template)
            
            # Replace file paths
            template = re.sub(r'/[\w/.-]+', '{path}', template)
            
            return template
            
        except Exception as e:
            self.logger.error(f"Error extracting message template: {str(e)}")
            return error_message
    
    def _determine_error_source(self, context: ErrorContext, error: Exception) -> ErrorSource:
        """Determine the source of the error"""
        try:
            role = context.role.lower()
            service_name = context.service_name.lower()
            
            if role == "si" or "si_" in service_name:
                return ErrorSource.SI_SERVICE
            elif role == "app" or "app_" in service_name:
                return ErrorSource.APP_SERVICE
            elif role == "hybrid" or "hybrid_" in service_name:
                return ErrorSource.HYBRID_SERVICE
            elif "core_" in service_name:
                return ErrorSource.CORE_PLATFORM
            elif "external" in service_name or "api" in service_name:
                return ErrorSource.EXTERNAL_SYSTEM
            else:
                return ErrorSource.CORE_PLATFORM
                
        except Exception as e:
            self.logger.error(f"Error determining error source: {str(e)}")
            return ErrorSource.CORE_PLATFORM
    
    async def _update_error_patterns(self, error_record: ErrorRecord):
        """Update error patterns for pattern detection"""
        try:
            fingerprint = error_record.fingerprint
            
            if fingerprint in self.error_patterns:
                # Update existing pattern
                pattern = self.error_patterns[fingerprint]
                pattern.frequency += 1
                pattern.last_occurrence = error_record.occurred_at
                
                # Update affected operations
                if error_record.context.operation_name not in pattern.affected_operations:
                    pattern.affected_operations.append(error_record.context.operation_name)
                
                # Update common characteristics
                self._update_pattern_characteristics(pattern, error_record)
                
            else:
                # Create new pattern
                pattern = ErrorPattern(
                    pattern_id=str(uuid.uuid4()),
                    fingerprint=fingerprint,
                    error_type=error_record.error_type,
                    source=error_record.source,
                    frequency=1,
                    first_occurrence=error_record.occurred_at,
                    last_occurrence=error_record.occurred_at,
                    affected_operations=[error_record.context.operation_name],
                    common_characteristics={
                        "error_class": error_record.metadata.get("error_class"),
                        "service_name": error_record.context.service_name,
                        "role": error_record.context.role
                    },
                    suggested_actions=await self._generate_suggested_actions(error_record),
                    escalation_threshold=self._determine_escalation_threshold(error_record),
                    auto_recovery_enabled=self._is_auto_recoverable(error_record)
                )
                
                self.error_patterns[fingerprint] = pattern
            
            # Cache pattern
            await self.cache.set(
                f"error_pattern:{fingerprint}",
                pattern.to_dict(),
                ttl=self.cache_ttl
            )
            
        except Exception as e:
            self.logger.error(f"Error updating error patterns: {str(e)}")
    
    def _update_pattern_characteristics(self, pattern: ErrorPattern, error_record: ErrorRecord):
        """Update pattern characteristics with new error data"""
        try:
            # Update common characteristics
            characteristics = pattern.common_characteristics
            
            # Count occurrences of characteristics
            for key, value in {
                "tenant_id": error_record.context.tenant_id,
                "user_id": error_record.context.user_id,
                "severity": error_record.severity
            }.items():
                if value:
                    if f"{key}_counts" not in characteristics:
                        characteristics[f"{key}_counts"] = {}
                    
                    if value not in characteristics[f"{key}_counts"]:
                        characteristics[f"{key}_counts"][value] = 0
                    
                    characteristics[f"{key}_counts"][value] += 1
            
        except Exception as e:
            self.logger.error(f"Error updating pattern characteristics: {str(e)}")
    
    async def _generate_suggested_actions(self, error_record: ErrorRecord) -> List[str]:
        """Generate suggested actions for error resolution"""
        try:
            actions = []
            error_type = error_record.error_type
            
            if error_type == ErrorType.VALIDATION:
                actions.extend([
                    "Review input validation rules",
                    "Check data format and constraints",
                    "Verify schema compatibility"
                ])
            elif error_type == ErrorType.AUTHENTICATION:
                actions.extend([
                    "Verify authentication credentials",
                    "Check token expiration",
                    "Review authentication service status"
                ])
            elif error_type == ErrorType.INTEGRATION:
                actions.extend([
                    "Check external service availability",
                    "Verify API endpoints and credentials",
                    "Review integration configuration"
                ])
            elif error_type == ErrorType.NETWORK:
                actions.extend([
                    "Check network connectivity",
                    "Verify firewall and proxy settings",
                    "Review DNS resolution"
                ])
            elif error_type == ErrorType.DATABASE:
                actions.extend([
                    "Check database connectivity",
                    "Review query performance",
                    "Verify database constraints"
                ])
            elif error_type == ErrorType.TIMEOUT:
                actions.extend([
                    "Increase timeout values",
                    "Optimize operation performance",
                    "Check system load"
                ])
            elif error_type == ErrorType.RESOURCE:
                actions.extend([
                    "Monitor system resources",
                    "Scale system capacity",
                    "Optimize resource usage"
                ])
            else:
                actions.extend([
                    "Review error logs and stack trace",
                    "Check system configuration",
                    "Contact system administrator"
                ])
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Error generating suggested actions: {str(e)}")
            return ["Review error details and contact support"]
    
    def _determine_escalation_threshold(self, error_record: ErrorRecord) -> int:
        """Determine escalation threshold for error pattern"""
        try:
            # Base threshold on severity
            if error_record.severity == ErrorSeverity.CRITICAL:
                return 1
            elif error_record.severity == ErrorSeverity.HIGH:
                return 3
            elif error_record.severity == ErrorSeverity.MEDIUM:
                return 5
            else:
                return 10
                
        except Exception as e:
            self.logger.error(f"Error determining escalation threshold: {str(e)}")
            return 5
    
    def _is_auto_recoverable(self, error_record: ErrorRecord) -> bool:
        """Determine if error is auto-recoverable"""
        try:
            # Auto-recoverable error types
            auto_recoverable_types = [
                ErrorType.NETWORK,
                ErrorType.TIMEOUT,
                ErrorType.EXTERNAL_API
            ]
            
            # Not auto-recoverable for critical errors
            if error_record.severity == ErrorSeverity.CRITICAL:
                return False
            
            return error_record.error_type in auto_recoverable_types
            
        except Exception as e:
            self.logger.error(f"Error checking auto-recovery: {str(e)}")
            return False
    
    async def _execute_error_handlers(self, error_record: ErrorRecord):
        """Execute registered error handlers"""
        try:
            handlers = self.error_handlers.get(error_record.error_type, [])
            
            for handler in handlers:
                try:
                    await handler(error_record)
                except Exception as e:
                    self.logger.error(f"Error in error handler: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error executing error handlers: {str(e)}")
    
    async def _handle_validation_error(self, error_record: ErrorRecord):
        """Handle validation errors"""
        try:
            # For validation errors, typically no automatic recovery
            # Log for analysis and potential rule updates
            self.logger.info(f"Validation error handled: {error_record.error_message}")
            
            # Emit validation error event for further processing
            await self.event_bus.emit(
                "error.validation_failed",
                {
                    "error_id": error_record.error_id,
                    "operation": error_record.context.operation_name,
                    "service": error_record.context.service_name
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error handling validation error: {str(e)}")
    
    async def _handle_authentication_error(self, error_record: ErrorRecord):
        """Handle authentication errors"""
        try:
            # Check if token refresh is possible
            if "token" in error_record.error_message.lower() and "expired" in error_record.error_message.lower():
                # Trigger token refresh
                await self.event_bus.emit(
                    "auth.token_refresh_required",
                    {
                        "error_id": error_record.error_id,
                        "user_id": error_record.context.user_id,
                        "session_id": error_record.context.session_id
                    }
                )
            
            self.logger.warning(f"Authentication error handled: {error_record.error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling authentication error: {str(e)}")
    
    async def _handle_integration_error(self, error_record: ErrorRecord):
        """Handle integration errors"""
        try:
            # Check circuit breaker status
            service_name = error_record.context.service_name
            
            if service_name not in self.circuit_breakers:
                self.circuit_breakers[service_name] = {
                    "failure_count": 0,
                    "last_failure": None,
                    "state": "closed"  # closed, open, half-open
                }
            
            breaker = self.circuit_breakers[service_name]
            breaker["failure_count"] += 1
            breaker["last_failure"] = datetime.now(timezone.utc)
            
            # Open circuit breaker if threshold reached
            if breaker["failure_count"] >= self.circuit_breaker_threshold:
                breaker["state"] = "open"
                
                await self.event_bus.emit(
                    "circuit_breaker.opened",
                    {
                        "service_name": service_name,
                        "error_id": error_record.error_id
                    }
                )
            
            self.logger.warning(f"Integration error handled: {error_record.error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling integration error: {str(e)}")
    
    async def _handle_network_error(self, error_record: ErrorRecord):
        """Handle network errors"""
        try:
            # Network errors are often transient - suggest retry
            if error_record.retry_count < self.max_retry_attempts:
                # Create recovery plan with retry
                recovery_plan = RecoveryPlan(
                    plan_id=str(uuid.uuid4()),
                    error_id=error_record.error_id,
                    actions=[RecoveryAction.RETRY],
                    priority=2,
                    estimated_duration_minutes=1,
                    success_probability=0.7,
                    metadata={"retry_delay_seconds": min(30 * (error_record.retry_count + 1), 300)}
                )
                
                self.recovery_plans[recovery_plan.plan_id] = recovery_plan
                
                await self.event_bus.emit(
                    "error.recovery_plan_created",
                    {
                        "error_id": error_record.error_id,
                        "plan_id": recovery_plan.plan_id,
                        "actions": recovery_plan.actions
                    }
                )
            
            self.logger.warning(f"Network error handled: {error_record.error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling network error: {str(e)}")
    
    async def _handle_database_error(self, error_record: ErrorRecord):
        """Handle database errors"""
        try:
            # Database errors may require rollback
            if "constraint" in error_record.error_message.lower():
                # Constraint violation - no retry, needs data correction
                await self.event_bus.emit(
                    "error.constraint_violation",
                    {
                        "error_id": error_record.error_id,
                        "operation": error_record.context.operation_name
                    }
                )
            elif "timeout" in error_record.error_message.lower():
                # Database timeout - may retry with optimization
                recovery_plan = RecoveryPlan(
                    plan_id=str(uuid.uuid4()),
                    error_id=error_record.error_id,
                    actions=[RecoveryAction.RETRY],
                    priority=3,
                    estimated_duration_minutes=2,
                    success_probability=0.5,
                    metadata={"optimize_query": True}
                )
                
                self.recovery_plans[recovery_plan.plan_id] = recovery_plan
            
            self.logger.error(f"Database error handled: {error_record.error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling database error: {str(e)}")
    
    async def _handle_system_error(self, error_record: ErrorRecord):
        """Handle system errors"""
        try:
            # System errors often require escalation
            if error_record.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                await self.event_bus.emit(
                    "error.escalation_required",
                    {
                        "error_id": error_record.error_id,
                        "severity": error_record.severity,
                        "source": error_record.source
                    }
                )
            
            self.logger.critical(f"System error handled: {error_record.error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling system error: {str(e)}")
    
    async def _check_circuit_breaker(self, error_record: ErrorRecord):
        """Check and update circuit breaker state"""
        try:
            service_name = error_record.context.service_name
            
            if service_name in self.circuit_breakers:
                breaker = self.circuit_breakers[service_name]
                
                if breaker["state"] == "open":
                    # Check if we should try half-open
                    if breaker["last_failure"]:
                        time_since_failure = (datetime.now(timezone.utc) - breaker["last_failure"]).total_seconds()
                        if time_since_failure >= self.circuit_breaker_timeout:
                            breaker["state"] = "half-open"
                            
                            await self.event_bus.emit(
                                "circuit_breaker.half_open",
                                {"service_name": service_name}
                            )
                            
        except Exception as e:
            self.logger.error(f"Error checking circuit breaker: {str(e)}")
    
    async def get_error_status(self, error_id: str) -> Dict[str, Any]:
        """Get status of a specific error"""
        try:
            if error_id not in self.error_records:
                return {"status": "not_found"}
            
            error_record = self.error_records[error_id]
            
            # Get related recovery plans
            related_plans = [
                p for p in self.recovery_plans.values()
                if p.error_id == error_id
            ]
            
            # Get pattern information
            pattern = self.error_patterns.get(error_record.fingerprint)
            
            return {
                "error_id": error_id,
                "status": error_record.status,
                "error_type": error_record.error_type,
                "severity": error_record.severity,
                "occurred_at": error_record.occurred_at.isoformat(),
                "retry_count": error_record.retry_count,
                "recovery_plans": len(related_plans),
                "pattern_frequency": pattern.frequency if pattern else 1,
                "auto_recoverable": pattern.auto_recovery_enabled if pattern else False,
                "resolution_notes": error_record.resolution_notes
            }
            
        except Exception as e:
            self.logger.error(f"Error getting error status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_error_patterns(
        self,
        error_type: ErrorType = None,
        source: ErrorSource = None,
        min_frequency: int = 1
    ) -> List[Dict[str, Any]]:
        """Get error patterns matching criteria"""
        try:
            patterns = list(self.error_patterns.values())
            
            # Filter by error type
            if error_type:
                patterns = [p for p in patterns if p.error_type == error_type]
            
            # Filter by source
            if source:
                patterns = [p for p in patterns if p.source == source]
            
            # Filter by frequency
            patterns = [p for p in patterns if p.frequency >= min_frequency]
            
            # Sort by frequency (descending)
            patterns.sort(key=lambda x: x.frequency, reverse=True)
            
            return [p.to_dict() for p in patterns]
            
        except Exception as e:
            self.logger.error(f"Error getting error patterns: {str(e)}")
            return []
    
    async def get_error_summary(
        self,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """Get error summary statistics"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
            recent_errors = [
                e for e in self.error_records.values()
                if e.occurred_at >= cutoff_time
            ]
            
            # Calculate statistics
            total_errors = len(recent_errors)
            errors_by_type = {}
            errors_by_severity = {}
            errors_by_source = {}
            
            for error_type in ErrorType:
                errors_by_type[error_type.value] = len([e for e in recent_errors if e.error_type == error_type])
            
            for severity in ErrorSeverity:
                errors_by_severity[severity.value] = len([e for e in recent_errors if e.severity == severity])
            
            for source in ErrorSource:
                errors_by_source[source.value] = len([e for e in recent_errors if e.source == source])
            
            # Calculate resolution rate
            resolved_errors = len([e for e in recent_errors if e.status == ErrorStatus.RESOLVED])
            resolution_rate = (resolved_errors / total_errors) * 100 if total_errors > 0 else 0
            
            # Get most frequent patterns
            frequent_patterns = sorted(
                self.error_patterns.values(),
                key=lambda x: x.frequency,
                reverse=True
            )[:5]
            
            return {
                "time_range_hours": time_range_hours,
                "total_errors": total_errors,
                "resolution_rate": resolution_rate,
                "errors_by_type": errors_by_type,
                "errors_by_severity": errors_by_severity,
                "errors_by_source": errors_by_source,
                "most_frequent_patterns": [p.to_dict() for p in frequent_patterns],
                "active_circuit_breakers": len([b for b in self.circuit_breakers.values() if b["state"] == "open"]),
                "recovery_plans_active": len(self.recovery_plans)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting error summary: {str(e)}")
            return {}
    
    async def resolve_error(
        self,
        error_id: str,
        resolution_notes: str,
        resolved_by: str = "system"
    ) -> bool:
        """Mark an error as resolved"""
        try:
            if error_id not in self.error_records:
                return False
            
            error_record = self.error_records[error_id]
            error_record.status = ErrorStatus.RESOLVED
            error_record.resolved_at = datetime.now(timezone.utc)
            error_record.resolution_notes = resolution_notes
            error_record.metadata = error_record.metadata or {}
            error_record.metadata["resolved_by"] = resolved_by
            
            # Update cache
            await self.cache.set(
                f"error:{error_id}",
                error_record.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit resolution event
            await self.event_bus.emit(
                "error.resolved",
                {
                    "error_id": error_id,
                    "resolved_by": resolved_by,
                    "resolution_notes": resolution_notes
                }
            )
            
            self.logger.info(f"Error {error_id} resolved by {resolved_by}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving error: {str(e)}")
            return False
    
    async def register_error_handler(
        self,
        error_type: ErrorType,
        handler: Callable
    ):
        """Register custom error handler"""
        try:
            if error_type not in self.error_handlers:
                self.error_handlers[error_type] = []
            
            self.error_handlers[error_type].append(handler)
            
            self.logger.info(f"Registered error handler for {error_type}")
            
        except Exception as e:
            self.logger.error(f"Error registering error handler: {str(e)}")
    
    async def _pattern_detector(self):
        """Background pattern detection task"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Analyze recent errors for patterns
                cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.pattern_detection_window)
                recent_errors = [
                    e for e in self.error_records.values()
                    if e.occurred_at >= cutoff_time
                ]
                
                # Check for escalation triggers
                for pattern in self.error_patterns.values():
                    if pattern.frequency >= pattern.escalation_threshold:
                        await self.event_bus.emit(
                            "error.pattern_escalation",
                            {
                                "pattern_id": pattern.pattern_id,
                                "frequency": pattern.frequency,
                                "threshold": pattern.escalation_threshold
                            }
                        )
                
            except Exception as e:
                self.logger.error(f"Error in pattern detector: {str(e)}")
    
    async def _recovery_monitor(self):
        """Background recovery monitoring task"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Monitor recovery plan execution
                # This would typically check status of recovery actions
                
            except Exception as e:
                self.logger.error(f"Error in recovery monitor: {str(e)}")
    
    async def _circuit_breaker_monitor(self):
        """Background circuit breaker monitoring task"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                current_time = datetime.now(timezone.utc)
                
                for service_name, breaker in self.circuit_breakers.items():
                    if breaker["state"] == "open" and breaker["last_failure"]:
                        time_since_failure = (current_time - breaker["last_failure"]).total_seconds()
                        
                        if time_since_failure >= self.circuit_breaker_timeout:
                            breaker["state"] = "half-open"
                            breaker["failure_count"] = 0
                            
                            await self.event_bus.emit(
                                "circuit_breaker.half_open",
                                {"service_name": service_name}
                            )
                
            except Exception as e:
                self.logger.error(f"Error in circuit breaker monitor: {str(e)}")
    
    async def _cleanup_old_errors(self):
        """Cleanup old error records periodically"""
        while True:
            try:
                await asyncio.sleep(86400)  # Run daily
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.error_retention_days)
                
                # Remove old resolved errors
                old_errors = [
                    e_id for e_id, e in self.error_records.items()
                    if e.status == ErrorStatus.RESOLVED and e.resolved_at and e.resolved_at < cutoff_time
                ]
                
                for error_id in old_errors:
                    del self.error_records[error_id]
                
                self.logger.info(f"Cleaned up {len(old_errors)} old error records")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "service.operation_failed",
                self._handle_service_operation_failed
            )
            
            await self.event_bus.subscribe(
                "integration.failure",
                self._handle_integration_failure
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_service_operation_failed(self, event_data: Dict[str, Any]):
        """Handle service operation failure event"""
        try:
            service_name = event_data.get("service_name")
            operation_name = event_data.get("operation_name")
            error_message = event_data.get("error_message")
            
            if service_name and operation_name:
                context = ErrorContext(
                    context_id=str(uuid.uuid4()),
                    user_id=event_data.get("user_id"),
                    session_id=event_data.get("session_id"),
                    request_id=event_data.get("request_id"),
                    operation_name=operation_name,
                    service_name=service_name,
                    role=event_data.get("role", "unknown"),
                    tenant_id=event_data.get("tenant_id"),
                    trace_id=event_data.get("trace_id")
                )
                
                # Create mock exception for error handling
                error = Exception(error_message or "Service operation failed")
                
                await self.handle_error(
                    error,
                    context,
                    ErrorType.SYSTEM,
                    ErrorSeverity.HIGH
                )
            
        except Exception as e:
            self.logger.error(f"Error handling service operation failed: {str(e)}")
    
    async def _handle_integration_failure(self, event_data: Dict[str, Any]):
        """Handle integration failure event"""
        try:
            integration_name = event_data.get("integration_name")
            error_details = event_data.get("error_details")
            
            if integration_name:
                context = ErrorContext(
                    context_id=str(uuid.uuid4()),
                    user_id=event_data.get("user_id"),
                    session_id=None,
                    request_id=event_data.get("request_id"),
                    operation_name="integration_operation",
                    service_name=integration_name,
                    role="integration",
                    tenant_id=event_data.get("tenant_id"),
                    trace_id=event_data.get("trace_id")
                )
                
                error = Exception(error_details or "Integration failure")
                
                await self.handle_error(
                    error,
                    context,
                    ErrorType.INTEGRATION,
                    ErrorSeverity.HIGH
                )
            
        except Exception as e:
            self.logger.error(f"Error handling integration failure: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            
            # Calculate error rates
            recent_errors = [
                e for e in self.error_records.values()
                if e.occurred_at >= datetime.now(timezone.utc) - timedelta(hours=1)
            ]
            
            critical_errors = len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL])
            open_circuit_breakers = len([b for b in self.circuit_breakers.values() if b["state"] == "open"])
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "error_coordinator",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_errors_stored": len(self.error_records),
                    "error_patterns": len(self.error_patterns),
                    "recent_errors": len(recent_errors),
                    "critical_errors": critical_errors,
                    "open_circuit_breakers": open_circuit_breakers,
                    "recovery_plans": len(self.recovery_plans)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "error_coordinator",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Error coordinator service cleanup initiated")
        
        try:
            # Clear all state
            self.error_records.clear()
            self.error_patterns.clear()
            self.recovery_plans.clear()
            self.circuit_breakers.clear()
            
            # Cleanup dependencies
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Error coordinator service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_error_coordinator() -> ErrorCoordinator:
    """Create error coordinator service"""
    return ErrorCoordinator()