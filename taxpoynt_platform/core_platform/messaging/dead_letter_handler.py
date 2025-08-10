"""
Core Platform: Dead Letter Handler
Advanced dead letter queue management for failed message processing
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import aiofiles

from .event_bus import Event, EventBus, EventScope, EventPriority, get_event_bus
from .queue_manager import QueuedMessage, MessageStatus

logger = logging.getLogger(__name__)


class FailureReason(str, Enum):
    """Reasons for message failure"""
    PROCESSING_ERROR = "processing_error"
    TIMEOUT = "timeout"
    INVALID_FORMAT = "invalid_format"
    CONSUMER_UNAVAILABLE = "consumer_unavailable"
    RETRY_EXHAUSTED = "retry_exhausted"
    POISON_MESSAGE = "poison_message"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    PERMISSION_DENIED = "permission_denied"
    DEPENDENCY_FAILURE = "dependency_failure"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"


class RecoveryAction(str, Enum):
    """Actions for message recovery"""
    RETRY = "retry"                 # Retry message processing
    ROUTE_ALTERNATIVE = "route_alternative"  # Route to alternative handler
    TRANSFORM_RETRY = "transform_retry"      # Transform and retry
    MANUAL_INTERVENTION = "manual_intervention"  # Requires manual review
    DISCARD = "discard"            # Permanently discard message
    ARCHIVE = "archive"            # Archive for analysis


class AlertLevel(str, Enum):
    """Alert levels for dead letter events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class FailureContext:
    """Context information for message failure"""
    failure_id: str
    original_message_id: str
    failure_reason: FailureReason
    error_message: str
    failure_time: datetime
    source_queue: str
    source_service: str
    retry_count: int = 0
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DeadLetterMessage:
    """Dead letter message with enhanced context"""
    dead_letter_id: str
    original_message: QueuedMessage
    failure_context: FailureContext
    received_time: datetime
    last_analysis: Optional[datetime] = None
    recovery_attempts: int = 0
    analysis_results: Dict[str, Any] = None
    recovery_actions: List[RecoveryAction] = None
    priority_score: float = 0.0
    tags: List[str] = None
    is_poison: bool = False
    
    def __post_init__(self):
        if self.analysis_results is None:
            self.analysis_results = {}
        if self.recovery_actions is None:
            self.recovery_actions = []
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects
        data['received_time'] = self.received_time.isoformat()
        if self.last_analysis:
            data['last_analysis'] = self.last_analysis.isoformat()
        data['failure_context']['failure_time'] = self.failure_context.failure_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeadLetterMessage':
        """Create from dictionary"""
        data = data.copy()
        data['received_time'] = datetime.fromisoformat(data['received_time'])
        if data.get('last_analysis'):
            data['last_analysis'] = datetime.fromisoformat(data['last_analysis'])
        
        # Convert failure context
        failure_data = data['failure_context']
        failure_data['failure_time'] = datetime.fromisoformat(failure_data['failure_time'])
        failure_data['failure_reason'] = FailureReason(failure_data['failure_reason'])
        data['failure_context'] = FailureContext(**failure_data)
        
        # Convert original message
        original_data = data['original_message']
        data['original_message'] = QueuedMessage.from_dict(original_data)
        
        return cls(**data)


@dataclass
class RecoveryPlan:
    """Recovery plan for dead letter messages"""
    plan_id: str
    dead_letter_id: str
    recommended_actions: List[RecoveryAction]
    confidence_score: float
    estimated_success_rate: float
    prerequisites: List[str] = None
    risk_assessment: Dict[str, Any] = None
    created_time: datetime = None
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.risk_assessment is None:
            self.risk_assessment = {}
        if self.created_time is None:
            self.created_time = datetime.now(timezone.utc)


@dataclass
class DeadLetterStats:
    """Dead letter queue statistics"""
    total_messages: int = 0
    messages_by_reason: Dict[FailureReason, int] = None
    messages_by_source: Dict[str, int] = None
    recovered_messages: int = 0
    discarded_messages: int = 0
    poison_messages: int = 0
    average_recovery_time: float = 0.0
    recovery_success_rate: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.messages_by_reason is None:
            self.messages_by_reason = {}
        if self.messages_by_source is None:
            self.messages_by_source = {}
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)


class DeadLetterHandler:
    """
    Dead Letter Handler for TaxPoynt Platform
    
    Advanced dead letter queue management with:
    - Automatic failure analysis
    - Recovery plan generation
    - Message replay capabilities
    - Poison message detection
    - Pattern-based routing
    - Performance monitoring
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None, storage_path: Optional[Path] = None):
        """Initialize the dead letter handler"""
        self.event_bus = event_bus or get_event_bus()
        self.storage_path = storage_path or Path("./dead_letter_data")
        
        # Dead letter storage
        self.dead_letters: Dict[str, DeadLetterMessage] = {}
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.failure_patterns: Dict[str, List[str]] = {}
        
        # Analysis and recovery
        self.analyzers: Dict[FailureReason, Callable] = {}
        self.recovery_handlers: Dict[RecoveryAction, Callable] = {}
        self.poison_detectors: List[Callable] = []
        
        # Configuration
        self.max_recovery_attempts = 3
        self.poison_threshold = 5
        self.analysis_interval = timedelta(minutes=15)
        self.cleanup_interval = timedelta(days=7)
        
        # Statistics
        self.stats = DeadLetterStats()
        
        # Processing state
        self.is_running = False
        self.processing_tasks: Set[asyncio.Task] = set()
        
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize the dead letter handler"""
        self.logger.info("Initializing Dead Letter Handler")
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load persisted dead letters
        await self._load_persisted_data()
        
        # Set up analyzers and recovery handlers
        await self._setup_analyzers()
        await self._setup_recovery_handlers()
        await self._setup_poison_detectors()
        
        # Register with event bus
        await self._register_event_handlers()
        
        self.logger.info("Dead Letter Handler initialized")
    
    async def start(self):
        """Start the dead letter handler"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Starting Dead Letter Handler")
        
        # Start background tasks
        tasks = [
            self._analysis_loop(),
            self._recovery_loop(),
            self._cleanup_loop(),
            self._monitoring_loop()
        ]
        
        for coro in tasks:
            task = asyncio.create_task(coro)
            self.processing_tasks.add(task)
            task.add_done_callback(self.processing_tasks.discard)
        
        self.logger.info("Dead Letter Handler started")
    
    async def stop(self):
        """Stop the dead letter handler"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping Dead Letter Handler")
        self.is_running = False
        
        # Cancel background tasks
        for task in self.processing_tasks:
            task.cancel()
        
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        # Persist current state
        await self._persist_data()
        
        self.logger.info("Dead Letter Handler stopped")
    
    async def handle_failed_message(
        self,
        message: QueuedMessage,
        failure_reason: FailureReason,
        error_message: str,
        source_queue: str,
        source_service: str,
        stack_trace: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Handle a failed message"""
        try:
            failure_context = FailureContext(
                failure_id=str(uuid.uuid4()),
                original_message_id=message.message_id,
                failure_reason=failure_reason,
                error_message=error_message,
                failure_time=datetime.now(timezone.utc),
                source_queue=source_queue,
                source_service=source_service,
                retry_count=message.retry_count,
                stack_trace=stack_trace,
                metadata=metadata or {}
            )
            
            dead_letter = DeadLetterMessage(
                dead_letter_id=str(uuid.uuid4()),
                original_message=message,
                failure_context=failure_context,
                received_time=datetime.now(timezone.utc)
            )
            
            # Check for poison message
            dead_letter.is_poison = await self._detect_poison_message(dead_letter)
            
            # Calculate priority score
            dead_letter.priority_score = await self._calculate_priority_score(dead_letter)
            
            # Store dead letter
            self.dead_letters[dead_letter.dead_letter_id] = dead_letter
            
            # Update statistics
            self.stats.total_messages += 1
            self.stats.messages_by_reason[failure_reason] = (
                self.stats.messages_by_reason.get(failure_reason, 0) + 1
            )
            self.stats.messages_by_source[source_service] = (
                self.stats.messages_by_source.get(source_service, 0) + 1
            )
            
            if dead_letter.is_poison:
                self.stats.poison_messages += 1
            
            # Track failure patterns
            await self._track_failure_pattern(dead_letter)
            
            # Trigger immediate analysis for critical messages
            if dead_letter.priority_score > 0.8:
                await self._analyze_dead_letter(dead_letter)
            
            # Emit dead letter event
            await self._emit_dead_letter_event(dead_letter)
            
            self.logger.warning(f"Message sent to dead letter queue: {dead_letter.dead_letter_id}")
            
            return dead_letter.dead_letter_id
            
        except Exception as e:
            self.logger.error(f"Error handling failed message: {str(e)}")
            raise
    
    async def recover_message(self, dead_letter_id: str, recovery_action: RecoveryAction) -> bool:
        """Attempt to recover a dead letter message"""
        try:
            if dead_letter_id not in self.dead_letters:
                return False
            
            dead_letter = self.dead_letters[dead_letter_id]
            
            # Check recovery attempts limit
            if dead_letter.recovery_attempts >= self.max_recovery_attempts:
                self.logger.warning(f"Max recovery attempts exceeded for {dead_letter_id}")
                return False
            
            dead_letter.recovery_attempts += 1
            
            # Execute recovery action
            if recovery_action in self.recovery_handlers:
                recovery_handler = self.recovery_handlers[recovery_action]
                success = await recovery_handler(dead_letter)
                
                if success:
                    # Move to recovered
                    await self._mark_as_recovered(dead_letter)
                    self.stats.recovered_messages += 1
                    
                    self.logger.info(f"Message recovered: {dead_letter_id}")
                    
                    return True
                else:
                    self.logger.warning(f"Recovery failed for {dead_letter_id}")
            else:
                self.logger.error(f"Unknown recovery action: {recovery_action}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error recovering message {dead_letter_id}: {str(e)}")
            return False
    
    async def replay_message(self, dead_letter_id: str, target_queue: str) -> bool:
        """Replay a dead letter message to a specific queue"""
        try:
            if dead_letter_id not in self.dead_letters:
                return False
            
            dead_letter = self.dead_letters[dead_letter_id]
            original_message = dead_letter.original_message
            
            # Reset message state
            original_message.retry_count = 0
            original_message.status = MessageStatus.QUEUED
            original_message.processing_time = None
            original_message.consumer_id = None
            
            # Add replay metadata
            if not original_message.metadata:
                original_message.metadata = {}
            original_message.metadata.update({
                'replayed_from_dead_letter': True,
                'original_dead_letter_id': dead_letter_id,
                'replay_time': datetime.now(timezone.utc).isoformat()
            })
            
            # Emit replay event (other systems should handle actual queueing)
            await self.event_bus.emit(
                event_type="dead_letter.message.replay",
                payload={
                    "dead_letter_id": dead_letter_id,
                    "target_queue": target_queue,
                    "message": original_message.to_dict()
                },
                source="dead_letter_handler",
                scope=EventScope.GLOBAL,
                priority=EventPriority.HIGH
            )
            
            # Mark as recovered
            await self._mark_as_recovered(dead_letter)
            
            self.logger.info(f"Message replayed: {dead_letter_id} -> {target_queue}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error replaying message {dead_letter_id}: {str(e)}")
            return False
    
    async def discard_message(self, dead_letter_id: str, reason: str) -> bool:
        """Permanently discard a dead letter message"""
        try:
            if dead_letter_id not in self.dead_letters:
                return False
            
            dead_letter = self.dead_letters[dead_letter_id]
            
            # Archive before discarding
            await self._archive_dead_letter(dead_letter, reason)
            
            # Remove from active dead letters
            del self.dead_letters[dead_letter_id]
            
            # Update statistics
            self.stats.discarded_messages += 1
            
            # Emit discard event
            await self.event_bus.emit(
                event_type="dead_letter.message.discarded",
                payload={
                    "dead_letter_id": dead_letter_id,
                    "reason": reason,
                    "original_message_id": dead_letter.original_message.message_id
                },
                source="dead_letter_handler",
                scope=EventScope.GLOBAL
            )
            
            self.logger.info(f"Message discarded: {dead_letter_id} - {reason}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error discarding message {dead_letter_id}: {str(e)}")
            return False
    
    async def _setup_analyzers(self):
        """Set up failure analyzers"""
        self.analyzers = {
            FailureReason.PROCESSING_ERROR: self._analyze_processing_error,
            FailureReason.TIMEOUT: self._analyze_timeout,
            FailureReason.INVALID_FORMAT: self._analyze_invalid_format,
            FailureReason.CONSUMER_UNAVAILABLE: self._analyze_consumer_unavailable,
            FailureReason.RETRY_EXHAUSTED: self._analyze_retry_exhausted,
            FailureReason.POISON_MESSAGE: self._analyze_poison_message,
            FailureReason.RESOURCE_UNAVAILABLE: self._analyze_resource_unavailable,
            FailureReason.PERMISSION_DENIED: self._analyze_permission_denied,
            FailureReason.DEPENDENCY_FAILURE: self._analyze_dependency_failure,
            FailureReason.CIRCUIT_BREAKER_OPEN: self._analyze_circuit_breaker
        }
    
    async def _setup_recovery_handlers(self):
        """Set up recovery action handlers"""
        self.recovery_handlers = {
            RecoveryAction.RETRY: self._handle_retry_recovery,
            RecoveryAction.ROUTE_ALTERNATIVE: self._handle_alternative_routing,
            RecoveryAction.TRANSFORM_RETRY: self._handle_transform_retry,
            RecoveryAction.MANUAL_INTERVENTION: self._handle_manual_intervention,
            RecoveryAction.DISCARD: self._handle_discard_recovery,
            RecoveryAction.ARCHIVE: self._handle_archive_recovery
        }
    
    async def _setup_poison_detectors(self):
        """Set up poison message detectors"""
        self.poison_detectors = [
            self._detect_high_retry_count,
            self._detect_recurring_failure,
            self._detect_malformed_payload,
            self._detect_suspicious_patterns
        ]
    
    async def _detect_poison_message(self, dead_letter: DeadLetterMessage) -> bool:
        """Detect if message is poisonous"""
        for detector in self.poison_detectors:
            try:
                if await detector(dead_letter):
                    return True
            except Exception as e:
                self.logger.error(f"Error in poison detector: {str(e)}")
        
        return False
    
    async def _detect_high_retry_count(self, dead_letter: DeadLetterMessage) -> bool:
        """Detect poison based on high retry count"""
        return dead_letter.failure_context.retry_count >= self.poison_threshold
    
    async def _detect_recurring_failure(self, dead_letter: DeadLetterMessage) -> bool:
        """Detect poison based on recurring failures"""
        message_id = dead_letter.original_message.message_id
        
        # Count similar failures in recent history
        similar_failures = 0
        for dl in self.dead_letters.values():
            if (dl.original_message.message_id == message_id or
                dl.original_message.correlation_id == dead_letter.original_message.correlation_id):
                similar_failures += 1
        
        return similar_failures >= 3
    
    async def _detect_malformed_payload(self, dead_letter: DeadLetterMessage) -> bool:
        """Detect poison based on malformed payload"""
        failure_reason = dead_letter.failure_context.failure_reason
        error_message = dead_letter.failure_context.error_message.lower()
        
        return (failure_reason == FailureReason.INVALID_FORMAT or
                any(keyword in error_message for keyword in 
                    ['json', 'parse', 'decode', 'format', 'schema', 'validation']))
    
    async def _detect_suspicious_patterns(self, dead_letter: DeadLetterMessage) -> bool:
        """Detect poison based on suspicious patterns"""
        payload = dead_letter.original_message.payload
        
        # Check for suspicious payload characteristics
        if isinstance(payload, dict):
            # Extremely large payload
            if len(str(payload)) > 1000000:  # 1MB
                return True
            
            # Suspicious nested depth
            def get_depth(obj, depth=0):
                if isinstance(obj, dict) and obj:
                    return max(get_depth(v, depth + 1) for v in obj.values())
                elif isinstance(obj, list) and obj:
                    return max(get_depth(v, depth + 1) for v in obj)
                return depth
            
            if get_depth(payload) > 20:
                return True
        
        return False
    
    async def _calculate_priority_score(self, dead_letter: DeadLetterMessage) -> float:
        """Calculate priority score for dead letter message"""
        score = 0.0
        
        # Base score from failure reason
        reason_scores = {
            FailureReason.CIRCUIT_BREAKER_OPEN: 0.9,
            FailureReason.DEPENDENCY_FAILURE: 0.8,
            FailureReason.RESOURCE_UNAVAILABLE: 0.7,
            FailureReason.CONSUMER_UNAVAILABLE: 0.6,
            FailureReason.TIMEOUT: 0.5,
            FailureReason.PROCESSING_ERROR: 0.4,
            FailureReason.RETRY_EXHAUSTED: 0.3,
            FailureReason.PERMISSION_DENIED: 0.2,
            FailureReason.INVALID_FORMAT: 0.1,
            FailureReason.POISON_MESSAGE: 0.0
        }
        
        score += reason_scores.get(dead_letter.failure_context.failure_reason, 0.3)
        
        # Adjust for message priority
        original_message = dead_letter.original_message
        if hasattr(original_message, 'priority'):
            priority_boost = {
                'critical': 0.3,
                'high': 0.2,
                'normal': 0.1,
                'low': 0.0
            }.get(str(original_message.priority).lower(), 0.1)
            score += priority_boost
        
        # Adjust for tenant importance
        if original_message.tenant_id:
            # This would be configured based on tenant tiers
            score += 0.1
        
        # Reduce score for poison messages
        if dead_letter.is_poison:
            score *= 0.1
        
        return min(1.0, score)
    
    async def _track_failure_pattern(self, dead_letter: DeadLetterMessage):
        """Track failure patterns for analysis"""
        pattern_key = f"{dead_letter.failure_context.failure_reason}:{dead_letter.failure_context.source_service}"
        
        if pattern_key not in self.failure_patterns:
            self.failure_patterns[pattern_key] = []
        
        self.failure_patterns[pattern_key].append(dead_letter.dead_letter_id)
        
        # Keep only recent failures (last 100)
        if len(self.failure_patterns[pattern_key]) > 100:
            self.failure_patterns[pattern_key] = self.failure_patterns[pattern_key][-100:]
    
    async def _analyze_dead_letter(self, dead_letter: DeadLetterMessage):
        """Analyze a dead letter message"""
        try:
            failure_reason = dead_letter.failure_context.failure_reason
            
            if failure_reason in self.analyzers:
                analyzer = self.analyzers[failure_reason]
                analysis_results = await analyzer(dead_letter)
                
                dead_letter.analysis_results = analysis_results
                dead_letter.last_analysis = datetime.now(timezone.utc)
                
                # Generate recovery plan
                recovery_plan = await self._generate_recovery_plan(dead_letter)
                if recovery_plan:
                    self.recovery_plans[recovery_plan.plan_id] = recovery_plan
                    dead_letter.recovery_actions = recovery_plan.recommended_actions
                
        except Exception as e:
            self.logger.error(f"Error analyzing dead letter {dead_letter.dead_letter_id}: {str(e)}")
    
    async def _generate_recovery_plan(self, dead_letter: DeadLetterMessage) -> Optional[RecoveryPlan]:
        """Generate recovery plan based on analysis"""
        try:
            failure_reason = dead_letter.failure_context.failure_reason
            analysis = dead_letter.analysis_results
            
            recommended_actions = []
            confidence_score = 0.0
            success_rate = 0.0
            
            # Plan based on failure reason
            if failure_reason == FailureReason.TIMEOUT:
                recommended_actions = [RecoveryAction.RETRY]
                confidence_score = 0.8
                success_rate = 0.7
            
            elif failure_reason == FailureReason.CONSUMER_UNAVAILABLE:
                recommended_actions = [RecoveryAction.ROUTE_ALTERNATIVE, RecoveryAction.RETRY]
                confidence_score = 0.7
                success_rate = 0.6
            
            elif failure_reason == FailureReason.INVALID_FORMAT:
                recommended_actions = [RecoveryAction.TRANSFORM_RETRY, RecoveryAction.MANUAL_INTERVENTION]
                confidence_score = 0.6
                success_rate = 0.4
            
            elif failure_reason == FailureReason.PROCESSING_ERROR:
                recommended_actions = [RecoveryAction.RETRY, RecoveryAction.MANUAL_INTERVENTION]
                confidence_score = 0.5
                success_rate = 0.5
            
            elif failure_reason == FailureReason.POISON_MESSAGE:
                recommended_actions = [RecoveryAction.DISCARD]
                confidence_score = 0.9
                success_rate = 1.0
            
            else:
                recommended_actions = [RecoveryAction.MANUAL_INTERVENTION]
                confidence_score = 0.3
                success_rate = 0.2
            
            if not recommended_actions:
                return None
            
            return RecoveryPlan(
                plan_id=str(uuid.uuid4()),
                dead_letter_id=dead_letter.dead_letter_id,
                recommended_actions=recommended_actions,
                confidence_score=confidence_score,
                estimated_success_rate=success_rate
            )
            
        except Exception as e:
            self.logger.error(f"Error generating recovery plan: {str(e)}")
            return None
    
    # Analyzer implementations
    async def _analyze_processing_error(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze processing error"""
        error_message = dead_letter.failure_context.error_message
        
        return {
            "error_type": self._classify_error(error_message),
            "is_transient": self._is_transient_error(error_message),
            "suggested_action": "retry" if self._is_transient_error(error_message) else "investigate"
        }
    
    async def _analyze_timeout(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze timeout error"""
        return {
            "likely_cause": "resource_contention",
            "suggested_action": "retry_with_backoff",
            "confidence": 0.8
        }
    
    async def _analyze_invalid_format(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze invalid format error"""
        payload = dead_letter.original_message.payload
        
        return {
            "payload_type": type(payload).__name__,
            "payload_size": len(str(payload)),
            "suggested_action": "transform_or_discard",
            "transformable": self._is_transformable(payload)
        }
    
    async def _analyze_consumer_unavailable(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze consumer unavailable error"""
        return {
            "likely_cause": "service_down",
            "suggested_action": "route_alternative",
            "retry_recommended": True
        }
    
    async def _analyze_retry_exhausted(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze retry exhausted error"""
        return {
            "retry_count": dead_letter.failure_context.retry_count,
            "suggested_action": "manual_review",
            "escalation_required": True
        }
    
    async def _analyze_poison_message(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze poison message"""
        return {
            "poison_indicators": await self._get_poison_indicators(dead_letter),
            "suggested_action": "discard",
            "safety_risk": "high"
        }
    
    async def _analyze_resource_unavailable(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze resource unavailable error"""
        return {
            "resource_type": "unknown",
            "suggested_action": "retry_later",
            "backoff_required": True
        }
    
    async def _analyze_permission_denied(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze permission denied error"""
        return {
            "access_issue": True,
            "suggested_action": "check_permissions",
            "manual_intervention": True
        }
    
    async def _analyze_dependency_failure(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze dependency failure error"""
        return {
            "dependency_issue": True,
            "suggested_action": "check_dependencies",
            "retry_after_fix": True
        }
    
    async def _analyze_circuit_breaker(self, dead_letter: DeadLetterMessage) -> Dict[str, Any]:
        """Analyze circuit breaker error"""
        return {
            "circuit_open": True,
            "suggested_action": "retry_later",
            "wait_for_recovery": True
        }
    
    # Recovery handler implementations
    async def _handle_retry_recovery(self, dead_letter: DeadLetterMessage) -> bool:
        """Handle retry recovery"""
        try:
            # Emit retry event
            await self.event_bus.emit(
                event_type="dead_letter.recovery.retry",
                payload={
                    "dead_letter_id": dead_letter.dead_letter_id,
                    "original_message": dead_letter.original_message.to_dict()
                },
                source="dead_letter_handler",
                scope=EventScope.GLOBAL,
                priority=EventPriority.HIGH
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in retry recovery: {str(e)}")
            return False
    
    async def _handle_alternative_routing(self, dead_letter: DeadLetterMessage) -> bool:
        """Handle alternative routing recovery"""
        try:
            # Emit alternative routing event
            await self.event_bus.emit(
                event_type="dead_letter.recovery.alternative_route",
                payload={
                    "dead_letter_id": dead_letter.dead_letter_id,
                    "original_message": dead_letter.original_message.to_dict(),
                    "original_source": dead_letter.failure_context.source_service
                },
                source="dead_letter_handler",
                scope=EventScope.GLOBAL,
                priority=EventPriority.HIGH
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in alternative routing: {str(e)}")
            return False
    
    async def _handle_transform_retry(self, dead_letter: DeadLetterMessage) -> bool:
        """Handle transform and retry recovery"""
        try:
            # Simple transformation (this would be more sophisticated in practice)
            original_payload = dead_letter.original_message.payload
            transformed_payload = await self._transform_payload(original_payload)
            
            if transformed_payload != original_payload:
                # Update message with transformed payload
                dead_letter.original_message.payload = transformed_payload
                
                # Emit transform retry event
                await self.event_bus.emit(
                    event_type="dead_letter.recovery.transform_retry",
                    payload={
                        "dead_letter_id": dead_letter.dead_letter_id,
                        "transformed_message": dead_letter.original_message.to_dict()
                    },
                    source="dead_letter_handler",
                    scope=EventScope.GLOBAL,
                    priority=EventPriority.HIGH
                )
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in transform retry: {str(e)}")
            return False
    
    async def _handle_manual_intervention(self, dead_letter: DeadLetterMessage) -> bool:
        """Handle manual intervention recovery"""
        try:
            # Emit manual intervention alert
            await self.event_bus.emit(
                event_type="dead_letter.alert.manual_intervention",
                payload={
                    "dead_letter_id": dead_letter.dead_letter_id,
                    "failure_reason": dead_letter.failure_context.failure_reason.value,
                    "error_message": dead_letter.failure_context.error_message,
                    "priority_score": dead_letter.priority_score,
                    "analysis_results": dead_letter.analysis_results
                },
                source="dead_letter_handler",
                scope=EventScope.GLOBAL,
                priority=EventPriority.CRITICAL
            )
            
            # Mark for manual review
            dead_letter.tags.append("manual_review_required")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in manual intervention: {str(e)}")
            return False
    
    async def _handle_discard_recovery(self, dead_letter: DeadLetterMessage) -> bool:
        """Handle discard recovery"""
        return await self.discard_message(dead_letter.dead_letter_id, "automatic_discard")
    
    async def _handle_archive_recovery(self, dead_letter: DeadLetterMessage) -> bool:
        """Handle archive recovery"""
        try:
            await self._archive_dead_letter(dead_letter, "automatic_archive")
            return True
        except Exception as e:
            self.logger.error(f"Error in archive recovery: {str(e)}")
            return False
    
    # Helper methods
    def _classify_error(self, error_message: str) -> str:
        """Classify error type from message"""
        error_lower = error_message.lower()
        
        if any(keyword in error_lower for keyword in ['timeout', 'time out']):
            return "timeout"
        elif any(keyword in error_lower for keyword in ['connection', 'network']):
            return "connectivity"
        elif any(keyword in error_lower for keyword in ['permission', 'access', 'auth']):
            return "authorization"
        elif any(keyword in error_lower for keyword in ['format', 'parse', 'json', 'xml']):
            return "format"
        else:
            return "unknown"
    
    def _is_transient_error(self, error_message: str) -> bool:
        """Check if error is likely transient"""
        transient_keywords = [
            'timeout', 'connection', 'network', 'temporary', 'unavailable',
            'busy', 'overload', 'rate limit', 'throttle'
        ]
        
        error_lower = error_message.lower()
        return any(keyword in error_lower for keyword in transient_keywords)
    
    def _is_transformable(self, payload: Any) -> bool:
        """Check if payload can be transformed"""
        try:
            # Basic checks for transformability
            if isinstance(payload, dict):
                return True
            elif isinstance(payload, str):
                # Try to parse as JSON
                json.loads(payload)
                return True
            else:
                return False
        except:
            return False
    
    async def _transform_payload(self, payload: Any) -> Any:
        """Transform payload to fix common issues"""
        try:
            if isinstance(payload, str):
                # Try to parse as JSON
                try:
                    return json.loads(payload)
                except:
                    return payload
            elif isinstance(payload, dict):
                # Clean up common issues
                cleaned = {}
                for key, value in payload.items():
                    if key and value is not None:
                        cleaned[str(key).strip()] = value
                return cleaned
            
            return payload
            
        except Exception as e:
            self.logger.error(f"Error transforming payload: {str(e)}")
            return payload
    
    async def _get_poison_indicators(self, dead_letter: DeadLetterMessage) -> List[str]:
        """Get indicators that make this a poison message"""
        indicators = []
        
        if dead_letter.failure_context.retry_count >= self.poison_threshold:
            indicators.append("high_retry_count")
        
        if dead_letter.failure_context.failure_reason == FailureReason.INVALID_FORMAT:
            indicators.append("invalid_format")
        
        # Check payload characteristics
        payload = dead_letter.original_message.payload
        if isinstance(payload, str) and len(payload) > 1000000:
            indicators.append("oversized_payload")
        
        return indicators
    
    async def _mark_as_recovered(self, dead_letter: DeadLetterMessage):
        """Mark dead letter as recovered"""
        # Remove from active dead letters
        if dead_letter.dead_letter_id in self.dead_letters:
            del self.dead_letters[dead_letter.dead_letter_id]
        
        # Archive recovery record
        await self._archive_dead_letter(dead_letter, "recovered")
    
    async def _archive_dead_letter(self, dead_letter: DeadLetterMessage, reason: str):
        """Archive dead letter to storage"""
        try:
            archive_file = self.storage_path / "archived" / f"{dead_letter.dead_letter_id}.json"
            archive_file.parent.mkdir(exist_ok=True)
            
            archive_data = dead_letter.to_dict()
            archive_data['archived_at'] = datetime.now(timezone.utc).isoformat()
            archive_data['archive_reason'] = reason
            
            async with aiofiles.open(archive_file, 'w') as f:
                await f.write(json.dumps(archive_data, indent=2))
            
        except Exception as e:
            self.logger.error(f"Error archiving dead letter: {str(e)}")
    
    async def _emit_dead_letter_event(self, dead_letter: DeadLetterMessage):
        """Emit dead letter event"""
        alert_level = AlertLevel.CRITICAL if dead_letter.priority_score > 0.8 else AlertLevel.WARNING
        
        await self.event_bus.emit(
            event_type="dead_letter.message.received",
            payload={
                "dead_letter_id": dead_letter.dead_letter_id,
                "failure_reason": dead_letter.failure_context.failure_reason.value,
                "source_service": dead_letter.failure_context.source_service,
                "priority_score": dead_letter.priority_score,
                "is_poison": dead_letter.is_poison,
                "alert_level": alert_level.value
            },
            source="dead_letter_handler",
            scope=EventScope.GLOBAL,
            priority=EventPriority.HIGH if alert_level == AlertLevel.CRITICAL else EventPriority.NORMAL
        )
    
    async def _analysis_loop(self):
        """Periodic analysis of dead letters"""
        while self.is_running:
            try:
                await asyncio.sleep(self.analysis_interval.total_seconds())
                
                # Analyze unanalyzed dead letters
                for dead_letter in self.dead_letters.values():
                    if not dead_letter.last_analysis:
                        await self._analyze_dead_letter(dead_letter)
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {str(e)}")
    
    async def _recovery_loop(self):
        """Periodic automatic recovery attempts"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Attempt automatic recovery for high-confidence plans
                for plan in self.recovery_plans.values():
                    if (plan.confidence_score > 0.8 and 
                        plan.dead_letter_id in self.dead_letters):
                        
                        dead_letter = self.dead_letters[plan.dead_letter_id]
                        if dead_letter.recovery_attempts < self.max_recovery_attempts:
                            for action in plan.recommended_actions:
                                if await self.recover_message(plan.dead_letter_id, action):
                                    break
                
            except Exception as e:
                self.logger.error(f"Error in recovery loop: {str(e)}")
    
    async def _cleanup_loop(self):
        """Periodic cleanup of old data"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=30)
                
                # Clean old dead letters
                old_letters = [
                    dl_id for dl_id, dl in self.dead_letters.items()
                    if dl.received_time < cutoff_time
                ]
                
                for dl_id in old_letters:
                    dead_letter = self.dead_letters[dl_id]
                    await self._archive_dead_letter(dead_letter, "cleanup")
                    del self.dead_letters[dl_id]
                
                # Clean old recovery plans
                old_plans = [
                    plan_id for plan_id, plan in self.recovery_plans.items()
                    if plan.created_time < cutoff_time
                ]
                
                for plan_id in old_plans:
                    del self.recovery_plans[plan_id]
                
                if old_letters or old_plans:
                    self.logger.info(f"Cleaned up {len(old_letters)} dead letters and {len(old_plans)} recovery plans")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}")
    
    async def _monitoring_loop(self):
        """Periodic monitoring and metrics emission"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Emit every minute
                
                # Update statistics
                self.stats.last_updated = datetime.now(timezone.utc)
                
                # Emit metrics
                await self.event_bus.emit(
                    event_type="dead_letter.metrics",
                    payload=asdict(self.stats),
                    source="dead_letter_handler",
                    scope=EventScope.GLOBAL,
                    priority=EventPriority.LOW
                )
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        await self.event_bus.subscribe(
            event_pattern="dead_letter.*",
            callback=self._handle_dead_letter_event,
            subscriber="dead_letter_handler"
        )
    
    async def _handle_dead_letter_event(self, event: Event):
        """Handle dead letter related events"""
        try:
            if event.event_type == "dead_letter.recovery.request":
                dead_letter_id = event.payload.get("dead_letter_id")
                recovery_action = event.payload.get("recovery_action")
                
                if dead_letter_id and recovery_action:
                    await self.recover_message(dead_letter_id, RecoveryAction(recovery_action))
            
        except Exception as e:
            self.logger.error(f"Error handling dead letter event: {str(e)}")
    
    async def _load_persisted_data(self):
        """Load persisted dead letter data"""
        try:
            data_file = self.storage_path / "dead_letters.json"
            
            if data_file.exists():
                async with aiofiles.open(data_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                
                # Load dead letters
                for dl_data in data.get('dead_letters', []):
                    dead_letter = DeadLetterMessage.from_dict(dl_data)
                    self.dead_letters[dead_letter.dead_letter_id] = dead_letter
                
                # Load statistics
                if 'stats' in data:
                    stats_data = data['stats']
                    self.stats = DeadLetterStats(**stats_data)
                
                self.logger.info(f"Loaded {len(self.dead_letters)} dead letters from storage")
                
        except Exception as e:
            self.logger.error(f"Error loading persisted data: {str(e)}")
    
    async def _persist_data(self):
        """Persist dead letter data"""
        try:
            data_file = self.storage_path / "dead_letters.json"
            
            data = {
                'dead_letters': [dl.to_dict() for dl in self.dead_letters.values()],
                'stats': asdict(self.stats),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            async with aiofiles.open(data_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            
        except Exception as e:
            self.logger.error(f"Error persisting data: {str(e)}")
    
    async def get_stats(self) -> DeadLetterStats:
        """Get dead letter statistics"""
        self.stats.last_updated = datetime.now(timezone.utc)
        return self.stats
    
    async def get_dead_letter_info(self, dead_letter_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a dead letter"""
        if dead_letter_id not in self.dead_letters:
            return None
        
        dead_letter = self.dead_letters[dead_letter_id]
        recovery_plan = None
        
        for plan in self.recovery_plans.values():
            if plan.dead_letter_id == dead_letter_id:
                recovery_plan = asdict(plan)
                break
        
        return {
            "dead_letter": dead_letter.to_dict(),
            "recovery_plan": recovery_plan
        }
    
    async def list_dead_letters(
        self,
        filter_by: Dict[str, Any] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List dead letters with optional filtering"""
        dead_letters = list(self.dead_letters.values())
        
        # Apply filters
        if filter_by:
            if 'failure_reason' in filter_by:
                reason = FailureReason(filter_by['failure_reason'])
                dead_letters = [dl for dl in dead_letters if dl.failure_context.failure_reason == reason]
            
            if 'source_service' in filter_by:
                service = filter_by['source_service']
                dead_letters = [dl for dl in dead_letters if dl.failure_context.source_service == service]
            
            if 'is_poison' in filter_by:
                is_poison = filter_by['is_poison']
                dead_letters = [dl for dl in dead_letters if dl.is_poison == is_poison]
        
        # Sort by priority score (highest first)
        dead_letters.sort(key=lambda dl: dl.priority_score, reverse=True)
        
        # Limit results
        dead_letters = dead_letters[:limit]
        
        return [dl.to_dict() for dl in dead_letters]


# Global dead letter handler instance
_global_dead_letter_handler: Optional[DeadLetterHandler] = None


def get_dead_letter_handler() -> DeadLetterHandler:
    """Get global dead letter handler instance"""
    global _global_dead_letter_handler
    if _global_dead_letter_handler is None:
        _global_dead_letter_handler = DeadLetterHandler()
    return _global_dead_letter_handler


async def initialize_dead_letter_handler(
    event_bus: Optional[EventBus] = None,
    storage_path: Optional[Path] = None
) -> DeadLetterHandler:
    """Initialize and start the global dead letter handler"""
    global _global_dead_letter_handler
    _global_dead_letter_handler = DeadLetterHandler(event_bus, storage_path)
    await _global_dead_letter_handler.initialize()
    await _global_dead_letter_handler.start()
    return _global_dead_letter_handler