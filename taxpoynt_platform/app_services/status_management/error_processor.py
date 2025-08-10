"""
Error Processor Service for APP Role

This service processes and categorizes submission errors including:
- Error classification and categorization
- Error analysis and pattern recognition
- Automatic error resolution suggestions
- Error reporting and analytics
- Integration with retry mechanisms
"""

import asyncio
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, Counter
import uuid

from .status_tracker import StatusTracker, SubmissionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """Error categories"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"
    DATA_FORMAT = "data_format"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"


class ErrorType(Enum):
    """Specific error types"""
    # Validation errors
    SCHEMA_VALIDATION = "schema_validation"
    FIELD_VALIDATION = "field_validation"
    BUSINESS_RULE_VALIDATION = "business_rule_validation"
    
    # Authentication/Authorization errors
    INVALID_CREDENTIALS = "invalid_credentials"
    EXPIRED_TOKEN = "expired_token"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    
    # Network errors
    CONNECTION_TIMEOUT = "connection_timeout"
    CONNECTION_REFUSED = "connection_refused"
    DNS_RESOLUTION = "dns_resolution"
    SSL_ERROR = "ssl_error"
    
    # System errors
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    DATABASE_ERROR = "database_error"
    MEMORY_ERROR = "memory_error"
    
    # Business logic errors
    DUPLICATE_SUBMISSION = "duplicate_submission"
    INVALID_DOCUMENT_STATE = "invalid_document_state"
    BUSINESS_CONSTRAINT_VIOLATION = "business_constraint_violation"
    
    # Data format errors
    INVALID_JSON = "invalid_json"
    INVALID_XML = "invalid_xml"
    ENCODING_ERROR = "encoding_error"
    
    # Other
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    QUOTA_EXCEEDED = "quota_exceeded"
    MAINTENANCE_MODE = "maintenance_mode"


class ResolutionStrategy(Enum):
    """Error resolution strategies"""
    RETRY_IMMEDIATE = "retry_immediate"
    RETRY_DELAYED = "retry_delayed"
    RETRY_EXPONENTIAL = "retry_exponential"
    MANUAL_INTERVENTION = "manual_intervention"
    IGNORE = "ignore"
    ESCALATE = "escalate"
    AUTO_FIX = "auto_fix"
    ROLLBACK = "rollback"


@dataclass
class ErrorPattern:
    """Error pattern for classification"""
    pattern_id: str
    pattern_name: str
    error_category: ErrorCategory
    error_type: ErrorType
    severity: ErrorSeverity
    patterns: List[str]  # Regex patterns to match
    fields_to_check: List[str]  # Fields in error data to check
    confidence_threshold: float = 0.8
    resolution_strategy: ResolutionStrategy = ResolutionStrategy.MANUAL_INTERVENTION
    resolution_steps: List[str] = field(default_factory=list)
    is_active: bool = True


@dataclass
class ErrorResolution:
    """Error resolution recommendation"""
    resolution_id: str
    error_type: ErrorType
    strategy: ResolutionStrategy
    description: str
    steps: List[str] = field(default_factory=list)
    estimated_time: int = 0  # minutes
    success_rate: float = 0.0
    prerequisites: List[str] = field(default_factory=list)
    automation_possible: bool = False


@dataclass
class SubmissionError:
    """Submission error structure"""
    error_id: str
    submission_id: str
    document_id: Optional[str]
    error_code: Optional[str]
    error_message: str
    error_details: Dict[str, Any]
    
    # Classification
    category: ErrorCategory
    error_type: ErrorType
    severity: ErrorSeverity
    confidence: float
    
    # Context
    occurred_at: datetime
    component: str  # Component where error occurred
    operation: str  # Operation being performed
    stage: str  # Processing stage
    
    # Resolution
    resolution_strategy: ResolutionStrategy
    resolution_attempts: int = 0
    max_resolution_attempts: int = 3
    next_retry_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: str = ""
    
    # Pattern matching
    matched_patterns: List[str] = field(default_factory=list)
    
    # Additional context
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorAnalysis:
    """Error analysis result"""
    analysis_id: str
    time_period: Tuple[datetime, datetime]
    total_errors: int
    errors_by_category: Dict[str, int]
    errors_by_type: Dict[str, int]
    errors_by_severity: Dict[str, int]
    top_error_patterns: List[Tuple[str, int]]
    resolution_success_rate: float
    most_common_resolutions: List[Tuple[str, int]]
    recommendations: List[str]
    trends: Dict[str, Any]


@dataclass
class ErrorReport:
    """Error report for specific submission"""
    submission_id: str
    document_id: Optional[str]
    total_errors: int
    errors_by_severity: Dict[str, int]
    critical_errors: List[SubmissionError]
    resolvable_errors: List[SubmissionError]
    resolution_recommendations: List[ErrorResolution]
    estimated_resolution_time: int
    next_actions: List[str]


class ErrorProcessor:
    """
    Error processor service for APP role
    
    Handles:
    - Error classification and categorization
    - Error analysis and pattern recognition
    - Automatic error resolution suggestions
    - Error reporting and analytics
    - Integration with retry mechanisms
    """
    
    def __init__(self,
                 status_tracker: Optional[StatusTracker] = None,
                 enable_auto_resolution: bool = True,
                 max_retry_attempts: int = 3):
        
        self.status_tracker = status_tracker
        self.enable_auto_resolution = enable_auto_resolution
        self.max_retry_attempts = max_retry_attempts
        
        # Storage
        self.errors: Dict[str, SubmissionError] = {}
        self.error_patterns: List[ErrorPattern] = []
        self.error_resolutions: Dict[ErrorType, List[ErrorResolution]] = defaultdict(list)
        
        # Setup default patterns and resolutions
        self._setup_default_patterns()
        self._setup_default_resolutions()
        
        # Error callbacks
        self.error_callbacks: Dict[ErrorType, List[Callable]] = defaultdict(list)
        
        # Background tasks
        self.resolution_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Metrics
        self.metrics = {
            'total_errors': 0,
            'processed_errors': 0,
            'resolved_errors': 0,
            'auto_resolved_errors': 0,
            'manual_resolution_required': 0,
            'errors_by_category': defaultdict(int),
            'errors_by_type': defaultdict(int),
            'errors_by_severity': defaultdict(int),
            'resolution_success_rate': 0.0,
            'average_resolution_time': 0.0,
            'pattern_matches': defaultdict(int),
            'resolution_strategies_used': defaultdict(int)
        }
    
    async def start(self):
        """Start error processor service"""
        self.running = True
        
        # Start background tasks
        self.resolution_task = asyncio.create_task(self._process_resolutions())
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Error processor service started")
    
    async def stop(self):
        """Stop error processor service"""
        self.running = False
        
        # Cancel background tasks
        if self.resolution_task:
            self.resolution_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        logger.info("Error processor service stopped")
    
    async def process_error(self,
                          submission_id: str,
                          error_message: str,
                          error_code: Optional[str] = None,
                          error_details: Optional[Dict[str, Any]] = None,
                          component: str = "unknown",
                          operation: str = "unknown",
                          stage: str = "unknown",
                          document_id: Optional[str] = None,
                          user_id: Optional[str] = None,
                          organization_id: Optional[str] = None) -> SubmissionError:
        """
        Process and classify submission error
        
        Args:
            submission_id: Submission identifier
            error_message: Error message
            error_code: Error code
            error_details: Additional error details
            component: Component where error occurred
            operation: Operation being performed
            stage: Processing stage
            document_id: Document identifier
            user_id: User identifier
            organization_id: Organization identifier
            
        Returns:
            SubmissionError with classification and resolution strategy
        """
        error_id = str(uuid.uuid4())
        
        # Create error record
        error = SubmissionError(
            error_id=error_id,
            submission_id=submission_id,
            document_id=document_id,
            error_code=error_code,
            error_message=error_message,
            error_details=error_details or {},
            category=ErrorCategory.UNKNOWN,
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            severity=ErrorSeverity.ERROR,
            confidence=0.0,
            occurred_at=datetime.utcnow(),
            component=component,
            operation=operation,
            stage=stage,
            resolution_strategy=ResolutionStrategy.MANUAL_INTERVENTION,
            user_id=user_id,
            organization_id=organization_id
        )
        
        # Classify error
        await self._classify_error(error)
        
        # Determine resolution strategy
        await self._determine_resolution_strategy(error)
        
        # Store error
        self.errors[error_id] = error
        
        # Update metrics
        self.metrics['total_errors'] += 1
        self.metrics['errors_by_category'][error.category.value] += 1
        self.metrics['errors_by_type'][error.error_type.value] += 1
        self.metrics['errors_by_severity'][error.severity.value] += 1
        
        # Execute callbacks
        await self._execute_error_callbacks(error)
        
        # Update submission status if critical
        if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL] and self.status_tracker:
            await self.status_tracker.update_status(
                submission_id=submission_id,
                new_status=SubmissionStatus.FAILED,
                reason=f"Critical error: {error.error_message}",
                metadata={
                    'error_id': error_id,
                    'error_type': error.error_type.value,
                    'error_category': error.category.value
                }
            )
        
        # Schedule automatic resolution if applicable
        if (self.enable_auto_resolution and 
            error.resolution_strategy in [ResolutionStrategy.RETRY_IMMEDIATE, 
                                         ResolutionStrategy.RETRY_DELAYED,
                                         ResolutionStrategy.AUTO_FIX]):
            await self._schedule_resolution(error)
        
        logger.warning(f"Processed error {error_id} for submission {submission_id}: "
                      f"{error.error_type.value} ({error.severity.value})")
        
        return error
    
    async def _classify_error(self, error: SubmissionError):
        """Classify error using pattern matching"""
        best_match = None
        best_confidence = 0.0
        
        # Check each pattern
        for pattern in self.error_patterns:
            if not pattern.is_active:
                continue
            
            confidence = await self._calculate_pattern_match(error, pattern)
            
            if confidence > best_confidence and confidence >= pattern.confidence_threshold:
                best_match = pattern
                best_confidence = confidence
        
        if best_match:
            error.category = best_match.error_category
            error.error_type = best_match.error_type
            error.severity = best_match.severity
            error.confidence = best_confidence
            error.resolution_strategy = best_match.resolution_strategy
            error.matched_patterns.append(best_match.pattern_id)
            
            self.metrics['pattern_matches'][best_match.pattern_id] += 1
        else:
            # Fallback classification
            error.category, error.error_type, error.severity = self._fallback_classification(error)
            error.confidence = 0.5
    
    async def _calculate_pattern_match(self, error: SubmissionError, pattern: ErrorPattern) -> float:
        """Calculate pattern match confidence"""
        scores = []
        
        # Check message patterns
        for regex_pattern in pattern.patterns:
            try:
                if re.search(regex_pattern, error.error_message, re.IGNORECASE):
                    scores.append(1.0)
                elif error.error_code and re.search(regex_pattern, error.error_code, re.IGNORECASE):
                    scores.append(0.8)
                else:
                    scores.append(0.0)
            except re.error:
                scores.append(0.0)
        
        # Check specific fields
        for field in pattern.fields_to_check:
            if field in error.error_details:
                field_value = str(error.error_details[field])
                for regex_pattern in pattern.patterns:
                    try:
                        if re.search(regex_pattern, field_value, re.IGNORECASE):
                            scores.append(0.9)
                            break
                    except re.error:
                        pass
        
        # Return average confidence
        return sum(scores) / len(scores) if scores else 0.0
    
    def _fallback_classification(self, error: SubmissionError) -> Tuple[ErrorCategory, ErrorType, ErrorSeverity]:
        """Fallback error classification"""
        message = error.error_message.lower()
        
        # Network errors
        if any(term in message for term in ['connection', 'timeout', 'network', 'dns']):
            if 'timeout' in message:
                return ErrorCategory.NETWORK, ErrorType.CONNECTION_TIMEOUT, ErrorSeverity.WARNING
            else:
                return ErrorCategory.NETWORK, ErrorType.CONNECTION_REFUSED, ErrorSeverity.ERROR
        
        # Validation errors
        elif any(term in message for term in ['validation', 'invalid', 'format', 'schema']):
            if 'schema' in message:
                return ErrorCategory.VALIDATION, ErrorType.SCHEMA_VALIDATION, ErrorSeverity.ERROR
            else:
                return ErrorCategory.VALIDATION, ErrorType.FIELD_VALIDATION, ErrorSeverity.WARNING
        
        # Authentication errors
        elif any(term in message for term in ['authentication', 'credential', 'token', 'unauthorized']):
            if 'token' in message:
                return ErrorCategory.AUTHENTICATION, ErrorType.EXPIRED_TOKEN, ErrorSeverity.ERROR
            else:
                return ErrorCategory.AUTHENTICATION, ErrorType.INVALID_CREDENTIALS, ErrorSeverity.ERROR
        
        # Rate limiting
        elif any(term in message for term in ['rate limit', 'quota', 'throttle']):
            return ErrorCategory.RATE_LIMIT, ErrorType.RATE_LIMIT_EXCEEDED, ErrorSeverity.WARNING
        
        # System errors
        elif any(term in message for term in ['server error', 'internal error', 'system error']):
            return ErrorCategory.SYSTEM, ErrorType.INTERNAL_SERVER_ERROR, ErrorSeverity.CRITICAL
        
        # Default classification
        else:
            return ErrorCategory.UNKNOWN, ErrorType.INTERNAL_SERVER_ERROR, ErrorSeverity.ERROR
    
    async def _determine_resolution_strategy(self, error: SubmissionError):
        """Determine resolution strategy for error"""
        # Check if there are specific resolutions for this error type
        resolutions = self.error_resolutions.get(error.error_type, [])
        
        if resolutions:
            # Use the resolution with highest success rate
            best_resolution = max(resolutions, key=lambda r: r.success_rate)
            error.resolution_strategy = best_resolution.strategy
        else:
            # Use default strategy based on error type and category
            if error.category == ErrorCategory.NETWORK:
                error.resolution_strategy = ResolutionStrategy.RETRY_DELAYED
            elif error.category == ErrorCategory.RATE_LIMIT:
                error.resolution_strategy = ResolutionStrategy.RETRY_EXPONENTIAL
            elif error.category == ErrorCategory.VALIDATION:
                error.resolution_strategy = ResolutionStrategy.MANUAL_INTERVENTION
            elif error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
                error.resolution_strategy = ResolutionStrategy.ESCALATE
            else:
                error.resolution_strategy = ResolutionStrategy.RETRY_DELAYED
    
    async def _schedule_resolution(self, error: SubmissionError):
        """Schedule automatic error resolution"""
        current_time = datetime.utcnow()
        
        if error.resolution_strategy == ResolutionStrategy.RETRY_IMMEDIATE:
            error.next_retry_at = current_time
        elif error.resolution_strategy == ResolutionStrategy.RETRY_DELAYED:
            delay_minutes = min(5 * (2 ** error.resolution_attempts), 60)  # Exponential backoff, max 60 min
            error.next_retry_at = current_time + timedelta(minutes=delay_minutes)
        elif error.resolution_strategy == ResolutionStrategy.RETRY_EXPONENTIAL:
            delay_minutes = min(1 * (2 ** error.resolution_attempts), 120)  # Exponential backoff, max 2 hours
            error.next_retry_at = current_time + timedelta(minutes=delay_minutes)
        elif error.resolution_strategy == ResolutionStrategy.AUTO_FIX:
            error.next_retry_at = current_time  # Immediate auto-fix attempt
    
    async def _process_resolutions(self):
        """Process scheduled error resolutions"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                resolutions_to_process = []
                
                # Find errors ready for resolution
                for error_id, error in self.errors.items():
                    if (error.next_retry_at and
                        current_time >= error.next_retry_at and
                        error.resolution_attempts < error.max_resolution_attempts and
                        not error.resolved_at):
                        resolutions_to_process.append(error_id)
                
                # Process resolutions
                for error_id in resolutions_to_process:
                    error = self.errors[error_id]
                    await self._attempt_resolution(error)
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing resolutions: {e}")
                await asyncio.sleep(60)
    
    async def _attempt_resolution(self, error: SubmissionError):
        """Attempt to resolve error"""
        error.resolution_attempts += 1
        start_time = time.time()
        
        try:
            if error.resolution_strategy == ResolutionStrategy.AUTO_FIX:
                success = await self._auto_fix_error(error)
            elif error.resolution_strategy in [ResolutionStrategy.RETRY_IMMEDIATE,
                                              ResolutionStrategy.RETRY_DELAYED,
                                              ResolutionStrategy.RETRY_EXPONENTIAL]:
                success = await self._retry_submission(error)
            else:
                # Manual intervention required
                success = False
                error.resolution_notes = "Manual intervention required"
            
            resolution_time = time.time() - start_time
            
            if success:
                error.resolved_at = datetime.utcnow()
                error.resolution_notes = f"Auto-resolved after {error.resolution_attempts} attempts"
                self.metrics['resolved_errors'] += 1
                self.metrics['auto_resolved_errors'] += 1
                
                # Update average resolution time
                self._update_average_resolution_time(resolution_time)
                
                logger.info(f"Successfully resolved error {error.error_id}")
                
                # Update submission status
                if self.status_tracker:
                    await self.status_tracker.update_status(
                        submission_id=error.submission_id,
                        new_status=SubmissionStatus.RETRY,
                        reason=f"Error resolved: {error.error_type.value}",
                        metadata={'error_id': error.error_id, 'resolution_strategy': error.resolution_strategy.value}
                    )
            else:
                # Schedule next retry if attempts remaining
                if error.resolution_attempts < error.max_resolution_attempts:
                    await self._schedule_resolution(error)
                else:
                    # Max attempts reached
                    error.resolution_notes = f"Failed to resolve after {error.resolution_attempts} attempts"
                    self.metrics['manual_resolution_required'] += 1
                    
                    logger.warning(f"Failed to resolve error {error.error_id} after {error.resolution_attempts} attempts")
            
            self.metrics['resolution_strategies_used'][error.resolution_strategy.value] += 1
            
        except Exception as e:
            error.resolution_notes = f"Resolution attempt failed: {str(e)}"
            logger.error(f"Error during resolution attempt for {error.error_id}: {e}")
    
    async def _auto_fix_error(self, error: SubmissionError) -> bool:
        """Attempt automatic error fix"""
        # This would implement specific auto-fix logic based on error type
        # For now, return False (no auto-fix implemented)
        return False
    
    async def _retry_submission(self, error: SubmissionError) -> bool:
        """Retry submission"""
        if self.status_tracker:
            try:
                success = await self.status_tracker.update_status(
                    submission_id=error.submission_id,
                    new_status=SubmissionStatus.RETRY,
                    reason=f"Retrying due to error: {error.error_type.value}"
                )
                return success
            except Exception:
                return False
        
        return False
    
    def _update_average_resolution_time(self, resolution_time: float):
        """Update average resolution time metric"""
        resolved_count = self.metrics['resolved_errors']
        current_avg = self.metrics['average_resolution_time']
        
        if resolved_count > 0:
            self.metrics['average_resolution_time'] = (
                (current_avg * (resolved_count - 1) + resolution_time) / resolved_count
            )
    
    async def _execute_error_callbacks(self, error: SubmissionError):
        """Execute registered error callbacks"""
        callbacks = self.error_callbacks.get(error.error_type, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error)
                else:
                    callback(error)
            except Exception as e:
                logger.error(f"Error executing error callback: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of resolved errors"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=24)
                
                # Remove old resolved errors
                resolved_errors = []
                for error_id, error in self.errors.items():
                    if error.resolved_at and error.resolved_at < cutoff_time:
                        resolved_errors.append(error_id)
                
                for error_id in resolved_errors:
                    del self.errors[error_id]
                
                if resolved_errors:
                    logger.info(f"Cleaned up {len(resolved_errors)} resolved errors")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def _setup_default_patterns(self):
        """Setup default error patterns"""
        # Validation error patterns
        self.error_patterns.append(ErrorPattern(
            pattern_id="schema_validation",
            pattern_name="Schema Validation Error",
            error_category=ErrorCategory.VALIDATION,
            error_type=ErrorType.SCHEMA_VALIDATION,
            severity=ErrorSeverity.ERROR,
            patterns=[r"schema.*validation.*failed", r"invalid.*schema", r"json.*schema.*error"],
            fields_to_check=["validation_errors", "schema_errors"],
            resolution_strategy=ResolutionStrategy.MANUAL_INTERVENTION
        ))
        
        # Network error patterns
        self.error_patterns.append(ErrorPattern(
            pattern_id="connection_timeout",
            pattern_name="Connection Timeout",
            error_category=ErrorCategory.NETWORK,
            error_type=ErrorType.CONNECTION_TIMEOUT,
            severity=ErrorSeverity.WARNING,
            patterns=[r"connection.*timeout", r"timeout.*error", r"read.*timeout"],
            fields_to_check=["network_error", "timeout_error"],
            resolution_strategy=ResolutionStrategy.RETRY_DELAYED
        ))
        
        # Authentication error patterns
        self.error_patterns.append(ErrorPattern(
            pattern_id="invalid_credentials",
            pattern_name="Invalid Credentials",
            error_category=ErrorCategory.AUTHENTICATION,
            error_type=ErrorType.INVALID_CREDENTIALS,
            severity=ErrorSeverity.ERROR,
            patterns=[r"invalid.*credentials", r"authentication.*failed", r"unauthorized"],
            fields_to_check=["auth_error", "credential_error"],
            resolution_strategy=ResolutionStrategy.MANUAL_INTERVENTION
        ))
        
        # Rate limit patterns
        self.error_patterns.append(ErrorPattern(
            pattern_id="rate_limit_exceeded",
            pattern_name="Rate Limit Exceeded",
            error_category=ErrorCategory.RATE_LIMIT,
            error_type=ErrorType.RATE_LIMIT_EXCEEDED,
            severity=ErrorSeverity.WARNING,
            patterns=[r"rate.*limit.*exceeded", r"too.*many.*requests", r"throttle"],
            fields_to_check=["rate_limit_error"],
            resolution_strategy=ResolutionStrategy.RETRY_EXPONENTIAL
        ))
        
        # System error patterns
        self.error_patterns.append(ErrorPattern(
            pattern_id="internal_server_error",
            pattern_name="Internal Server Error",
            error_category=ErrorCategory.SYSTEM,
            error_type=ErrorType.INTERNAL_SERVER_ERROR,
            severity=ErrorSeverity.CRITICAL,
            patterns=[r"internal.*server.*error", r"500.*error", r"system.*error"],
            fields_to_check=["system_error", "server_error"],
            resolution_strategy=ResolutionStrategy.ESCALATE
        ))
    
    def _setup_default_resolutions(self):
        """Setup default error resolutions"""
        # Network timeout resolution
        self.error_resolutions[ErrorType.CONNECTION_TIMEOUT].append(ErrorResolution(
            resolution_id="retry_timeout",
            error_type=ErrorType.CONNECTION_TIMEOUT,
            strategy=ResolutionStrategy.RETRY_DELAYED,
            description="Retry with increased timeout",
            steps=["Wait for 5 minutes", "Retry submission with increased timeout"],
            estimated_time=5,
            success_rate=0.7,
            automation_possible=True
        ))
        
        # Rate limit resolution
        self.error_resolutions[ErrorType.RATE_LIMIT_EXCEEDED].append(ErrorResolution(
            resolution_id="backoff_rate_limit",
            error_type=ErrorType.RATE_LIMIT_EXCEEDED,
            strategy=ResolutionStrategy.RETRY_EXPONENTIAL,
            description="Exponential backoff retry",
            steps=["Wait with exponential backoff", "Retry submission"],
            estimated_time=15,
            success_rate=0.9,
            automation_possible=True
        ))
        
        # Validation error resolution
        self.error_resolutions[ErrorType.SCHEMA_VALIDATION].append(ErrorResolution(
            resolution_id="fix_validation",
            error_type=ErrorType.SCHEMA_VALIDATION,
            strategy=ResolutionStrategy.MANUAL_INTERVENTION,
            description="Fix validation errors",
            steps=["Review validation errors", "Correct document format", "Resubmit"],
            estimated_time=30,
            success_rate=0.95,
            prerequisites=["Access to document editor", "Knowledge of schema requirements"],
            automation_possible=False
        ))
    
    async def get_error(self, error_id: str) -> Optional[SubmissionError]:
        """Get error by ID"""
        return self.errors.get(error_id)
    
    async def get_errors_by_submission(self, submission_id: str) -> List[SubmissionError]:
        """Get errors for submission"""
        return [error for error in self.errors.values() 
                if error.submission_id == submission_id]
    
    async def get_errors_by_type(self, error_type: ErrorType) -> List[SubmissionError]:
        """Get errors by type"""
        return [error for error in self.errors.values() 
                if error.error_type == error_type]
    
    async def get_unresolved_errors(self) -> List[SubmissionError]:
        """Get unresolved errors"""
        return [error for error in self.errors.values() 
                if not error.resolved_at]
    
    async def get_error_report(self, submission_id: str) -> ErrorReport:
        """Generate error report for submission"""
        submission_errors = await self.get_errors_by_submission(submission_id)
        
        if not submission_errors:
            return ErrorReport(
                submission_id=submission_id,
                document_id=None,
                total_errors=0,
                errors_by_severity={},
                critical_errors=[],
                resolvable_errors=[],
                resolution_recommendations=[],
                estimated_resolution_time=0,
                next_actions=[]
            )
        
        # Analyze errors
        errors_by_severity = defaultdict(int)
        critical_errors = []
        resolvable_errors = []
        
        for error in submission_errors:
            errors_by_severity[error.severity.value] += 1
            
            if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
                critical_errors.append(error)
            
            if (error.resolution_strategy in [ResolutionStrategy.RETRY_IMMEDIATE,
                                            ResolutionStrategy.RETRY_DELAYED,
                                            ResolutionStrategy.AUTO_FIX] and
                not error.resolved_at):
                resolvable_errors.append(error)
        
        # Get resolution recommendations
        resolution_recommendations = []
        for error in submission_errors:
            if not error.resolved_at:
                resolutions = self.error_resolutions.get(error.error_type, [])
                resolution_recommendations.extend(resolutions)
        
        # Calculate estimated resolution time
        estimated_time = sum(res.estimated_time for res in resolution_recommendations)
        
        # Determine next actions
        next_actions = []
        if critical_errors:
            next_actions.append("Address critical errors immediately")
        if resolvable_errors:
            next_actions.append(f"Retry {len(resolvable_errors)} resolvable errors")
        if not next_actions:
            next_actions.append("All errors resolved or require manual intervention")
        
        return ErrorReport(
            submission_id=submission_id,
            document_id=submission_errors[0].document_id,
            total_errors=len(submission_errors),
            errors_by_severity=dict(errors_by_severity),
            critical_errors=critical_errors,
            resolvable_errors=resolvable_errors,
            resolution_recommendations=resolution_recommendations,
            estimated_resolution_time=estimated_time,
            next_actions=next_actions
        )
    
    async def analyze_errors(self, 
                           start_time: datetime,
                           end_time: datetime) -> ErrorAnalysis:
        """Analyze errors over time period"""
        analysis_id = str(uuid.uuid4())
        
        # Filter errors by time period
        period_errors = [error for error in self.errors.values()
                        if start_time <= error.occurred_at <= end_time]
        
        if not period_errors:
            return ErrorAnalysis(
                analysis_id=analysis_id,
                time_period=(start_time, end_time),
                total_errors=0,
                errors_by_category={},
                errors_by_type={},
                errors_by_severity={},
                top_error_patterns=[],
                resolution_success_rate=0.0,
                most_common_resolutions=[],
                recommendations=[],
                trends={}
            )
        
        # Aggregate statistics
        errors_by_category = Counter(error.category.value for error in period_errors)
        errors_by_type = Counter(error.error_type.value for error in period_errors)
        errors_by_severity = Counter(error.severity.value for error in period_errors)
        
        # Top error patterns
        all_patterns = []
        for error in period_errors:
            all_patterns.extend(error.matched_patterns)
        top_patterns = Counter(all_patterns).most_common(10)
        
        # Resolution success rate
        resolved_errors = len([error for error in period_errors if error.resolved_at])
        resolution_success_rate = (resolved_errors / len(period_errors)) * 100
        
        # Most common resolutions
        resolution_strategies = Counter(error.resolution_strategy.value for error in period_errors)
        most_common_resolutions = resolution_strategies.most_common(5)
        
        # Generate recommendations
        recommendations = []
        if errors_by_category['validation'] > len(period_errors) * 0.3:
            recommendations.append("High validation error rate - review document schemas")
        if errors_by_category['network'] > len(period_errors) * 0.2:
            recommendations.append("Network issues detected - check connectivity")
        if resolution_success_rate < 50:
            recommendations.append("Low resolution success rate - review error handling")
        
        return ErrorAnalysis(
            analysis_id=analysis_id,
            time_period=(start_time, end_time),
            total_errors=len(period_errors),
            errors_by_category=dict(errors_by_category),
            errors_by_type=dict(errors_by_type),
            errors_by_severity=dict(errors_by_severity),
            top_error_patterns=top_patterns,
            resolution_success_rate=resolution_success_rate,
            most_common_resolutions=most_common_resolutions,
            recommendations=recommendations,
            trends={}
        )
    
    def add_error_pattern(self, pattern: ErrorPattern):
        """Add custom error pattern"""
        self.error_patterns.append(pattern)
    
    def add_error_resolution(self, error_type: ErrorType, resolution: ErrorResolution):
        """Add custom error resolution"""
        self.error_resolutions[error_type].append(resolution)
    
    def register_error_callback(self, error_type: ErrorType, callback: Callable):
        """Register callback for error type"""
        self.error_callbacks[error_type].append(callback)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get error processor metrics"""
        success_rate = 0
        if self.metrics['total_errors'] > 0:
            success_rate = (self.metrics['resolved_errors'] / self.metrics['total_errors']) * 100
        
        self.metrics['resolution_success_rate'] = success_rate
        
        return {
            **self.metrics,
            'active_errors': len(self.errors),
            'error_patterns': len(self.error_patterns),
            'resolution_strategies': len(self.error_resolutions),
            'registered_callbacks': sum(len(callbacks) for callbacks in self.error_callbacks.values())
        }


# Factory functions for easy setup
def create_error_processor(status_tracker: Optional[StatusTracker] = None,
                         enable_auto_resolution: bool = True) -> ErrorProcessor:
    """Create error processor instance"""
    return ErrorProcessor(
        status_tracker=status_tracker,
        enable_auto_resolution=enable_auto_resolution
    )


def create_error_pattern(pattern_id: str,
                        error_category: ErrorCategory,
                        error_type: ErrorType,
                        patterns: List[str],
                        **kwargs) -> ErrorPattern:
    """Create error pattern"""
    return ErrorPattern(
        pattern_id=pattern_id,
        pattern_name=pattern_id.replace('_', ' ').title(),
        error_category=error_category,
        error_type=error_type,
        patterns=patterns,
        fields_to_check=[],
        **kwargs
    )


async def process_submission_error(submission_id: str,
                                 error_message: str,
                                 processor: Optional[ErrorProcessor] = None,
                                 **kwargs) -> SubmissionError:
    """Process submission error"""
    if not processor:
        processor = create_error_processor()
        await processor.start()
    
    try:
        return await processor.process_error(submission_id, error_message, **kwargs)
    finally:
        if not processor.running:
            await processor.stop()


def get_error_summary(processor: ErrorProcessor) -> Dict[str, Any]:
    """Get error processor summary"""
    metrics = processor.get_metrics()
    
    return {
        'total_errors': metrics['total_errors'],
        'resolved_errors': metrics['resolved_errors'],
        'resolution_success_rate': metrics['resolution_success_rate'],
        'auto_resolved_errors': metrics['auto_resolved_errors'],
        'manual_resolution_required': metrics['manual_resolution_required'],
        'average_resolution_time': metrics['average_resolution_time'],
        'error_category_distribution': dict(metrics['errors_by_category']),
        'error_type_distribution': dict(metrics['errors_by_type']),
        'severity_distribution': dict(metrics['errors_by_severity'])
    }