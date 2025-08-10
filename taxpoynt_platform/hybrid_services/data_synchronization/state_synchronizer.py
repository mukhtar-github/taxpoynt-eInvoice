"""
Hybrid Service: State Synchronizer
Synchronizes state information between SI and APP roles
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import time

from core_platform.database import get_db_session
from core_platform.models.synchronization import SyncState, SyncEvent, SyncConflict
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService
from core_platform.messaging import MessageQueue

logger = logging.getLogger(__name__)


class SyncScope(str, Enum):
    """Synchronization scope"""
    SI_TO_APP = "si_to_app"
    APP_TO_SI = "app_to_si"
    BIDIRECTIONAL = "bidirectional"
    BROADCAST = "broadcast"


class SyncStrategy(str, Enum):
    """Synchronization strategies"""
    IMMEDIATE = "immediate"
    BATCHED = "batched"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    CONFLICT_FREE = "conflict_free"


class SyncStatus(str, Enum):
    """Synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICTED = "conflicted"
    CANCELLED = "cancelled"


class StateType(str, Enum):
    """Types of state data"""
    CONFIGURATION = "configuration"
    SESSION = "session"
    TRANSACTION = "transaction"
    CACHE = "cache"
    METADATA = "metadata"
    SECURITY = "security"
    WORKFLOW = "workflow"
    BUSINESS_RULE = "business_rule"


class SyncPriority(str, Enum):
    """Synchronization priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


@dataclass
class StateData:
    """State data with metadata"""
    state_id: str
    state_type: StateType
    data: Dict[str, Any]
    version: int
    timestamp: datetime
    source_role: str
    checksum: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for state data"""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


@dataclass
class SyncRequest:
    """State synchronization request"""
    request_id: str
    state_id: str
    source_role: str
    target_roles: List[str]
    sync_scope: SyncScope
    sync_strategy: SyncStrategy
    priority: SyncPriority
    state_data: StateData
    requested_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyncResult:
    """Synchronization result"""
    request_id: str
    state_id: str
    sync_status: SyncStatus
    target_role: str
    synced_at: datetime
    sync_duration: float
    conflicts: List[Dict[str, Any]]
    errors: List[str]
    version_after: int
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyncSession:
    """Synchronization session"""
    session_id: str
    initiated_by: str
    session_type: str
    start_time: datetime
    end_time: Optional[datetime]
    states_synced: List[str]
    sync_requests: List[str]
    total_conflicts: int
    success_rate: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StateSynchronizer:
    """
    State Synchronizer service
    Synchronizes state information between SI and APP roles
    """
    
    def __init__(self):
        """Initialize state synchronizer service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.message_queue = MessageQueue()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.state_registry: Dict[str, StateData] = {}
        self.sync_requests: Dict[str, SyncRequest] = {}
        self.sync_results: Dict[str, List[SyncResult]] = {}
        self.active_sessions: Dict[str, SyncSession] = {}
        self.sync_subscriptions: Dict[str, Set[str]] = {}  # state_id -> set of roles
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour
        self.max_retry_attempts = 3
        self.sync_timeout = 30  # seconds
        self.batch_size = 100
        self.sync_interval = 60  # seconds for scheduled sync
        
        # Synchronization strategies
        self.sync_strategies = {
            SyncStrategy.IMMEDIATE: self._immediate_sync,
            SyncStrategy.BATCHED: self._batched_sync,
            SyncStrategy.SCHEDULED: self._scheduled_sync,
            SyncStrategy.EVENT_DRIVEN: self._event_driven_sync,
            SyncStrategy.CONFLICT_FREE: self._conflict_free_sync
        }
    
    async def initialize(self):
        """Initialize the state synchronizer service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing state synchronizer service")
        
        try:
            # Initialize dependencies
            await self.cache.initialize()
            await self.event_bus.initialize()
            await self.message_queue.initialize()
            
            # Set up message queue topics
            await self._setup_message_queues()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._sync_worker())
            asyncio.create_task(self._cleanup_expired_requests())
            
            self.is_initialized = True
            self.logger.info("State synchronizer service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing state synchronizer service: {str(e)}")
            raise
    
    async def register_state(
        self,
        state_id: str,
        state_type: StateType,
        data: Dict[str, Any],
        source_role: str,
        metadata: Dict[str, Any] = None
    ) -> StateData:
        """Register state data for synchronization"""
        try:
            # Create state data
            state_data = StateData(
                state_id=state_id,
                state_type=state_type,
                data=data,
                version=1,
                timestamp=datetime.now(timezone.utc),
                source_role=source_role,
                checksum=hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
                metadata=metadata or {}
            )
            
            # Check for existing state
            if state_id in self.state_registry:
                existing_state = self.state_registry[state_id]
                state_data.version = existing_state.version + 1
                
                # Check if data actually changed
                if state_data.checksum == existing_state.checksum:
                    self.logger.debug(f"State {state_id} unchanged, skipping registration")
                    return existing_state
            
            # Store state
            self.state_registry[state_id] = state_data
            
            # Cache state
            await self.cache.set(
                f"state:{state_id}",
                state_data.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit state change event
            await self.event_bus.emit(
                "state.changed",
                {
                    "state_id": state_id,
                    "state_type": state_type,
                    "source_role": source_role,
                    "version": state_data.version,
                    "timestamp": state_data.timestamp.isoformat()
                }
            )
            
            self.logger.debug(f"Registered state: {state_id} v{state_data.version}")
            
            return state_data
            
        except Exception as e:
            self.logger.error(f"Error registering state: {str(e)}")
            raise
    
    async def subscribe_to_state(
        self,
        state_id: str,
        subscriber_role: str,
        sync_strategy: SyncStrategy = SyncStrategy.EVENT_DRIVEN
    ):
        """Subscribe to state changes"""
        try:
            if state_id not in self.sync_subscriptions:
                self.sync_subscriptions[state_id] = set()
            
            self.sync_subscriptions[state_id].add(subscriber_role)
            
            # Cache subscription
            await self.cache.set(
                f"subscription:{state_id}:{subscriber_role}",
                {
                    "state_id": state_id,
                    "subscriber_role": subscriber_role,
                    "sync_strategy": sync_strategy,
                    "subscribed_at": datetime.now(timezone.utc).isoformat()
                },
                ttl=self.cache_ttl
            )
            
            self.logger.debug(f"Role {subscriber_role} subscribed to state {state_id}")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to state: {str(e)}")
            raise
    
    async def synchronize_state(
        self,
        state_id: str,
        target_roles: List[str],
        sync_scope: SyncScope = SyncScope.BIDIRECTIONAL,
        sync_strategy: SyncStrategy = SyncStrategy.IMMEDIATE,
        priority: SyncPriority = SyncPriority.MEDIUM
    ) -> str:
        """Synchronize state to target roles"""
        try:
            if state_id not in self.state_registry:
                raise ValueError(f"State not found: {state_id}")
            
            state_data = self.state_registry[state_id]
            
            # Create sync request
            sync_request = SyncRequest(
                request_id=str(uuid.uuid4()),
                state_id=state_id,
                source_role=state_data.source_role,
                target_roles=target_roles,
                sync_scope=sync_scope,
                sync_strategy=sync_strategy,
                priority=priority,
                state_data=state_data,
                requested_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
                metadata={"initiated_by": "manual"}
            )
            
            # Store sync request
            self.sync_requests[sync_request.request_id] = sync_request
            
            # Execute synchronization based on strategy
            if sync_strategy == SyncStrategy.IMMEDIATE:
                await self._execute_sync_request(sync_request)
            else:
                # Queue for later processing
                await self.message_queue.publish(
                    "sync_requests",
                    sync_request.to_dict()
                )
            
            self.logger.info(f"Initiated sync for state {state_id} to roles {target_roles}")
            
            return sync_request.request_id
            
        except Exception as e:
            self.logger.error(f"Error synchronizing state: {str(e)}")
            raise
    
    async def get_state(self, state_id: str, role: str = None) -> Optional[StateData]:
        """Get state data"""
        try:
            # Check cache first
            cached_state = await self.cache.get(f"state:{state_id}")
            if cached_state:
                return StateData(**cached_state)
            
            # Check registry
            if state_id in self.state_registry:
                state_data = self.state_registry[state_id]
                
                # Cache for future use
                await self.cache.set(
                    f"state:{state_id}",
                    state_data.to_dict(),
                    ttl=self.cache_ttl
                )
                
                return state_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting state: {str(e)}")
            return None
    
    async def get_sync_status(self, request_id: str) -> Dict[str, Any]:
        """Get synchronization status"""
        try:
            if request_id not in self.sync_results:
                return {"status": "not_found"}
            
            results = self.sync_results[request_id]
            
            # Calculate overall status
            statuses = [r.sync_status for r in results]
            
            if all(s == SyncStatus.COMPLETED for s in statuses):
                overall_status = "completed"
            elif any(s == SyncStatus.FAILED for s in statuses):
                overall_status = "failed"
            elif any(s == SyncStatus.CONFLICTED for s in statuses):
                overall_status = "conflicted"
            elif any(s == SyncStatus.IN_PROGRESS for s in statuses):
                overall_status = "in_progress"
            else:
                overall_status = "pending"
            
            return {
                "request_id": request_id,
                "overall_status": overall_status,
                "results": [r.to_dict() for r in results],
                "total_targets": len(results),
                "completed": len([r for r in results if r.sync_status == SyncStatus.COMPLETED]),
                "failed": len([r for r in results if r.sync_status == SyncStatus.FAILED]),
                "conflicts": sum(len(r.conflicts) for r in results)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sync status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def bulk_synchronize(
        self,
        state_ids: List[str],
        target_roles: List[str],
        sync_strategy: SyncStrategy = SyncStrategy.BATCHED
    ) -> List[str]:
        """Bulk synchronize multiple states"""
        try:
            request_ids = []
            
            # Create sync session
            session = SyncSession(
                session_id=str(uuid.uuid4()),
                initiated_by="bulk_sync",
                session_type="bulk",
                start_time=datetime.now(timezone.utc),
                end_time=None,
                states_synced=state_ids,
                sync_requests=[],
                total_conflicts=0,
                success_rate=0.0,
                metadata={"target_roles": target_roles}
            )
            
            self.active_sessions[session.session_id] = session
            
            # Process in batches
            for i in range(0, len(state_ids), self.batch_size):
                batch = state_ids[i:i + self.batch_size]
                
                for state_id in batch:
                    try:
                        request_id = await self.synchronize_state(
                            state_id,
                            target_roles,
                            sync_strategy=sync_strategy,
                            priority=SyncPriority.MEDIUM
                        )
                        request_ids.append(request_id)
                        session.sync_requests.append(request_id)
                        
                    except Exception as e:
                        self.logger.error(f"Error syncing state {state_id}: {str(e)}")
                        continue
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            # Update session
            session.end_time = datetime.now(timezone.utc)
            
            self.logger.info(f"Bulk sync initiated for {len(state_ids)} states")
            
            return request_ids
            
        except Exception as e:
            self.logger.error(f"Error in bulk synchronize: {str(e)}")
            raise
    
    async def force_sync(
        self,
        state_id: str,
        target_role: str,
        override_conflicts: bool = False
    ) -> SyncResult:
        """Force synchronization ignoring conflicts"""
        try:
            if state_id not in self.state_registry:
                raise ValueError(f"State not found: {state_id}")
            
            state_data = self.state_registry[state_id]
            
            # Create sync request with high priority
            sync_request = SyncRequest(
                request_id=str(uuid.uuid4()),
                state_id=state_id,
                source_role=state_data.source_role,
                target_roles=[target_role],
                sync_scope=SyncScope.BIDIRECTIONAL,
                sync_strategy=SyncStrategy.IMMEDIATE,
                priority=SyncPriority.CRITICAL,
                state_data=state_data,
                requested_at=datetime.now(timezone.utc),
                metadata={"force_sync": True, "override_conflicts": override_conflicts}
            )
            
            # Execute immediately
            results = await self._execute_sync_request(sync_request)
            
            return results[0] if results else None
            
        except Exception as e:
            self.logger.error(f"Error in force sync: {str(e)}")
            raise
    
    async def _execute_sync_request(self, sync_request: SyncRequest) -> List[SyncResult]:
        """Execute synchronization request"""
        try:
            results = []
            
            for target_role in sync_request.target_roles:
                start_time = time.time()
                
                try:
                    # Check if target has conflicting state
                    conflicts = await self._check_conflicts(
                        sync_request.state_id,
                        target_role,
                        sync_request.state_data
                    )
                    
                    # Resolve conflicts if any
                    if conflicts and not sync_request.metadata.get("override_conflicts", False):
                        # Handle conflicts based on strategy
                        resolved_conflicts = await self._resolve_conflicts(
                            sync_request.state_id,
                            target_role,
                            conflicts,
                            sync_request.state_data
                        )
                        conflicts = resolved_conflicts
                    
                    # Perform actual synchronization
                    success = await self._sync_to_target(
                        sync_request.state_data,
                        target_role,
                        sync_request.sync_scope
                    )
                    
                    # Create result
                    result = SyncResult(
                        request_id=sync_request.request_id,
                        state_id=sync_request.state_id,
                        sync_status=SyncStatus.COMPLETED if success else SyncStatus.FAILED,
                        target_role=target_role,
                        synced_at=datetime.now(timezone.utc),
                        sync_duration=time.time() - start_time,
                        conflicts=[c.to_dict() for c in conflicts] if conflicts else [],
                        errors=[],
                        version_after=sync_request.state_data.version,
                        metadata={"sync_method": "direct"}
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    # Create error result
                    result = SyncResult(
                        request_id=sync_request.request_id,
                        state_id=sync_request.state_id,
                        sync_status=SyncStatus.FAILED,
                        target_role=target_role,
                        synced_at=datetime.now(timezone.utc),
                        sync_duration=time.time() - start_time,
                        conflicts=[],
                        errors=[str(e)],
                        version_after=sync_request.state_data.version,
                        metadata={"sync_method": "direct"}
                    )
                    
                    results.append(result)
                    self.logger.error(f"Error syncing to {target_role}: {str(e)}")
            
            # Store results
            self.sync_results[sync_request.request_id] = results
            
            # Emit sync completion event
            await self.event_bus.emit(
                "sync.completed",
                {
                    "request_id": sync_request.request_id,
                    "state_id": sync_request.state_id,
                    "results": len(results),
                    "success_count": len([r for r in results if r.sync_status == SyncStatus.COMPLETED])
                }
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing sync request: {str(e)}")
            raise
    
    async def _sync_to_target(
        self,
        state_data: StateData,
        target_role: str,
        sync_scope: SyncScope
    ) -> bool:
        """Sync state data to target role"""
        try:
            # Create sync message
            sync_message = {
                "state_id": state_data.state_id,
                "state_type": state_data.state_type,
                "data": state_data.data,
                "version": state_data.version,
                "timestamp": state_data.timestamp.isoformat(),
                "source_role": state_data.source_role,
                "checksum": state_data.checksum,
                "sync_scope": sync_scope,
                "metadata": state_data.metadata
            }
            
            # Publish to target role queue
            await self.message_queue.publish(
                f"sync_target_{target_role}",
                sync_message
            )
            
            # Cache the synchronized state
            await self.cache.set(
                f"synced_state:{state_data.state_id}:{target_role}",
                sync_message,
                ttl=self.cache_ttl
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error syncing to target {target_role}: {str(e)}")
            return False
    
    async def _check_conflicts(
        self,
        state_id: str,
        target_role: str,
        new_state: StateData
    ) -> List[Any]:
        """Check for conflicts with target role"""
        try:
            conflicts = []
            
            # Get current state in target role
            current_state = await self.cache.get(f"synced_state:{state_id}:{target_role}")
            
            if current_state:
                # Check version conflict
                if current_state.get("version", 0) > new_state.version:
                    conflicts.append({
                        "type": "version_conflict",
                        "current_version": current_state.get("version"),
                        "new_version": new_state.version,
                        "message": "Target has newer version"
                    })
                
                # Check data conflict
                current_checksum = current_state.get("checksum")
                if current_checksum and current_checksum != new_state.checksum:
                    conflicts.append({
                        "type": "data_conflict",
                        "current_checksum": current_checksum,
                        "new_checksum": new_state.checksum,
                        "message": "Data checksums differ"
                    })
                
                # Check timestamp conflict
                current_timestamp = current_state.get("timestamp")
                if current_timestamp:
                    current_time = datetime.fromisoformat(current_timestamp.replace('Z', '+00:00'))
                    if current_time > new_state.timestamp:
                        conflicts.append({
                            "type": "timestamp_conflict",
                            "current_timestamp": current_timestamp,
                            "new_timestamp": new_state.timestamp.isoformat(),
                            "message": "Target has newer timestamp"
                        })
            
            return conflicts
            
        except Exception as e:
            self.logger.error(f"Error checking conflicts: {str(e)}")
            return []
    
    async def _resolve_conflicts(
        self,
        state_id: str,
        target_role: str,
        conflicts: List[Dict[str, Any]],
        new_state: StateData
    ) -> List[Any]:
        """Resolve synchronization conflicts"""
        try:
            resolved_conflicts = []
            
            for conflict in conflicts:
                conflict_type = conflict.get("type")
                
                if conflict_type == "version_conflict":
                    # Version conflict - use latest timestamp
                    if new_state.timestamp > datetime.fromisoformat(conflict.get("current_timestamp", "1970-01-01T00:00:00Z")):
                        # New state wins
                        resolved_conflicts.append({
                            **conflict,
                            "resolution": "new_state_wins",
                            "reason": "newer_timestamp"
                        })
                    else:
                        # Current state wins
                        resolved_conflicts.append({
                            **conflict,
                            "resolution": "current_state_wins",
                            "reason": "newer_timestamp"
                        })
                
                elif conflict_type == "data_conflict":
                    # Data conflict - merge if possible
                    try:
                        # Simple merge strategy - could be enhanced
                        resolved_conflicts.append({
                            **conflict,
                            "resolution": "merged",
                            "reason": "data_merge_attempted"
                        })
                    except Exception:
                        # Fallback to new state
                        resolved_conflicts.append({
                            **conflict,
                            "resolution": "new_state_wins",
                            "reason": "merge_failed"
                        })
                
                elif conflict_type == "timestamp_conflict":
                    # Timestamp conflict - use newer version
                    if new_state.version > conflict.get("current_version", 0):
                        resolved_conflicts.append({
                            **conflict,
                            "resolution": "new_state_wins",
                            "reason": "newer_version"
                        })
                    else:
                        resolved_conflicts.append({
                            **conflict,
                            "resolution": "current_state_wins",
                            "reason": "newer_version"
                        })
                
                else:
                    # Unknown conflict type
                    resolved_conflicts.append({
                        **conflict,
                        "resolution": "unresolved",
                        "reason": "unknown_conflict_type"
                    })
            
            return resolved_conflicts
            
        except Exception as e:
            self.logger.error(f"Error resolving conflicts: {str(e)}")
            return conflicts
    
    async def _immediate_sync(self, sync_request: SyncRequest) -> List[SyncResult]:
        """Execute immediate synchronization"""
        return await self._execute_sync_request(sync_request)
    
    async def _batched_sync(self, sync_request: SyncRequest) -> List[SyncResult]:
        """Execute batched synchronization"""
        # Queue for batch processing
        await self.message_queue.publish(
            "sync_batch_queue",
            sync_request.to_dict()
        )
        
        # Return pending results
        return [
            SyncResult(
                request_id=sync_request.request_id,
                state_id=sync_request.state_id,
                sync_status=SyncStatus.PENDING,
                target_role=role,
                synced_at=datetime.now(timezone.utc),
                sync_duration=0.0,
                conflicts=[],
                errors=[],
                version_after=sync_request.state_data.version,
                metadata={"sync_method": "batched"}
            )
            for role in sync_request.target_roles
        ]
    
    async def _scheduled_sync(self, sync_request: SyncRequest) -> List[SyncResult]:
        """Execute scheduled synchronization"""
        # Schedule for later processing
        await self.cache.set(
            f"scheduled_sync:{sync_request.request_id}",
            sync_request.to_dict(),
            ttl=86400  # 24 hours
        )
        
        return [
            SyncResult(
                request_id=sync_request.request_id,
                state_id=sync_request.state_id,
                sync_status=SyncStatus.PENDING,
                target_role=role,
                synced_at=datetime.now(timezone.utc),
                sync_duration=0.0,
                conflicts=[],
                errors=[],
                version_after=sync_request.state_data.version,
                metadata={"sync_method": "scheduled"}
            )
            for role in sync_request.target_roles
        ]
    
    async def _event_driven_sync(self, sync_request: SyncRequest) -> List[SyncResult]:
        """Execute event-driven synchronization"""
        # Emit sync event
        await self.event_bus.emit(
            "sync.requested",
            sync_request.to_dict()
        )
        
        return [
            SyncResult(
                request_id=sync_request.request_id,
                state_id=sync_request.state_id,
                sync_status=SyncStatus.PENDING,
                target_role=role,
                synced_at=datetime.now(timezone.utc),
                sync_duration=0.0,
                conflicts=[],
                errors=[],
                version_after=sync_request.state_data.version,
                metadata={"sync_method": "event_driven"}
            )
            for role in sync_request.target_roles
        ]
    
    async def _conflict_free_sync(self, sync_request: SyncRequest) -> List[SyncResult]:
        """Execute conflict-free synchronization"""
        # Only sync if no conflicts
        results = []
        
        for target_role in sync_request.target_roles:
            conflicts = await self._check_conflicts(
                sync_request.state_id,
                target_role,
                sync_request.state_data
            )
            
            if not conflicts:
                # No conflicts, proceed with sync
                result = await self._sync_to_target(
                    sync_request.state_data,
                    target_role,
                    sync_request.sync_scope
                )
                
                results.append(SyncResult(
                    request_id=sync_request.request_id,
                    state_id=sync_request.state_id,
                    sync_status=SyncStatus.COMPLETED if result else SyncStatus.FAILED,
                    target_role=target_role,
                    synced_at=datetime.now(timezone.utc),
                    sync_duration=0.0,
                    conflicts=[],
                    errors=[],
                    version_after=sync_request.state_data.version,
                    metadata={"sync_method": "conflict_free"}
                ))
            else:
                # Conflicts found, skip sync
                results.append(SyncResult(
                    request_id=sync_request.request_id,
                    state_id=sync_request.state_id,
                    sync_status=SyncStatus.CONFLICTED,
                    target_role=target_role,
                    synced_at=datetime.now(timezone.utc),
                    sync_duration=0.0,
                    conflicts=conflicts,
                    errors=["Conflicts detected in conflict-free mode"],
                    version_after=sync_request.state_data.version,
                    metadata={"sync_method": "conflict_free"}
                ))
        
        return results
    
    async def _setup_message_queues(self):
        """Setup message queues for synchronization"""
        try:
            # Create sync queues
            await self.message_queue.create_queue("sync_requests")
            await self.message_queue.create_queue("sync_batch_queue")
            await self.message_queue.create_queue("sync_target_si")
            await self.message_queue.create_queue("sync_target_app")
            
            # Set up consumers
            await self.message_queue.subscribe(
                "sync_requests",
                self._handle_sync_request
            )
            
            await self.message_queue.subscribe(
                "sync_batch_queue",
                self._handle_batch_sync
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up message queues: {str(e)}")
    
    async def _handle_sync_request(self, message: Dict[str, Any]):
        """Handle sync request from queue"""
        try:
            sync_request = SyncRequest(**message)
            await self._execute_sync_request(sync_request)
            
        except Exception as e:
            self.logger.error(f"Error handling sync request: {str(e)}")
    
    async def _handle_batch_sync(self, message: Dict[str, Any]):
        """Handle batch sync request"""
        try:
            sync_request = SyncRequest(**message)
            await self._execute_sync_request(sync_request)
            
        except Exception as e:
            self.logger.error(f"Error handling batch sync: {str(e)}")
    
    async def _sync_worker(self):
        """Background sync worker"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                
                # Process scheduled syncs
                await self._process_scheduled_syncs()
                
                # Process subscription-based syncs
                await self._process_subscription_syncs()
                
            except Exception as e:
                self.logger.error(f"Error in sync worker: {str(e)}")
    
    async def _process_scheduled_syncs(self):
        """Process scheduled synchronizations"""
        try:
            # Get scheduled syncs from cache
            scheduled_keys = await self.cache.keys("scheduled_sync:*")
            
            for key in scheduled_keys:
                try:
                    sync_data = await self.cache.get(key)
                    if sync_data:
                        sync_request = SyncRequest(**sync_data)
                        
                        # Check if it's time to process
                        if datetime.now(timezone.utc) >= sync_request.requested_at:
                            await self._execute_sync_request(sync_request)
                            await self.cache.delete(key)
                
                except Exception as e:
                    self.logger.error(f"Error processing scheduled sync {key}: {str(e)}")
                    await self.cache.delete(key)
            
        except Exception as e:
            self.logger.error(f"Error processing scheduled syncs: {str(e)}")
    
    async def _process_subscription_syncs(self):
        """Process subscription-based synchronizations"""
        try:
            # Check for state changes that need to be synced to subscribers
            for state_id, subscribers in self.sync_subscriptions.items():
                if state_id in self.state_registry:
                    state_data = self.state_registry[state_id]
                    
                    # Check if state was recently updated
                    if (datetime.now(timezone.utc) - state_data.timestamp).total_seconds() < self.sync_interval:
                        # Sync to all subscribers
                        await self.synchronize_state(
                            state_id,
                            list(subscribers),
                            sync_strategy=SyncStrategy.EVENT_DRIVEN
                        )
            
        except Exception as e:
            self.logger.error(f"Error processing subscription syncs: {str(e)}")
    
    async def _cleanup_expired_requests(self):
        """Cleanup expired sync requests"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.now(timezone.utc)
                
                # Remove expired requests
                expired_requests = []
                for request_id, request in self.sync_requests.items():
                    if request.expires_at and current_time > request.expires_at:
                        expired_requests.append(request_id)
                
                for request_id in expired_requests:
                    del self.sync_requests[request_id]
                    if request_id in self.sync_results:
                        del self.sync_results[request_id]
                
                # Remove old results
                old_results = []
                for request_id, results in self.sync_results.items():
                    if results and (current_time - results[0].synced_at).total_seconds() > 86400:  # 24 hours
                        old_results.append(request_id)
                
                for request_id in old_results:
                    del self.sync_results[request_id]
                
                self.logger.debug(f"Cleaned up {len(expired_requests)} expired requests and {len(old_results)} old results")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "state.changed",
                self._handle_state_change
            )
            
            await self.event_bus.subscribe(
                "sync.requested",
                self._handle_sync_event
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_state_change(self, event_data: Dict[str, Any]):
        """Handle state change event"""
        try:
            state_id = event_data.get("state_id")
            
            # Check if there are subscribers for this state
            if state_id in self.sync_subscriptions:
                subscribers = list(self.sync_subscriptions[state_id])
                
                # Trigger synchronization to subscribers
                await self.synchronize_state(
                    state_id,
                    subscribers,
                    sync_strategy=SyncStrategy.EVENT_DRIVEN
                )
            
        except Exception as e:
            self.logger.error(f"Error handling state change: {str(e)}")
    
    async def _handle_sync_event(self, event_data: Dict[str, Any]):
        """Handle sync event"""
        try:
            sync_request = SyncRequest(**event_data)
            await self._execute_sync_request(sync_request)
            
        except Exception as e:
            self.logger.error(f"Error handling sync event: {str(e)}")
    
    async def get_sync_statistics(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        try:
            total_requests = len(self.sync_requests)
            total_results = len(self.sync_results)
            
            # Calculate success rate
            all_results = []
            for results in self.sync_results.values():
                all_results.extend(results)
            
            success_count = len([r for r in all_results if r.sync_status == SyncStatus.COMPLETED])
            total_count = len(all_results)
            success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
            
            # Calculate conflict rate
            conflict_count = len([r for r in all_results if r.conflicts])
            conflict_rate = (conflict_count / total_count) * 100 if total_count > 0 else 0
            
            return {
                "total_states": len(self.state_registry),
                "total_requests": total_requests,
                "total_results": total_results,
                "success_rate": success_rate,
                "conflict_rate": conflict_rate,
                "active_sessions": len(self.active_sessions),
                "total_subscriptions": sum(len(subs) for subs in self.sync_subscriptions.values()),
                "avg_sync_duration": statistics.mean([r.sync_duration for r in all_results]) if all_results else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sync statistics: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "state_synchronizer",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"},
                    "message_queue": {"status": "healthy"}
                },
                "metrics": {
                    "total_states": len(self.state_registry),
                    "active_requests": len(self.sync_requests),
                    "active_sessions": len(self.active_sessions),
                    "total_subscriptions": sum(len(subs) for subs in self.sync_subscriptions.values())
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "state_synchronizer",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("State synchronizer service cleanup initiated")
        
        try:
            # Clear all state
            self.state_registry.clear()
            self.sync_requests.clear()
            self.sync_results.clear()
            self.active_sessions.clear()
            self.sync_subscriptions.clear()
            
            # Cleanup dependencies
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("State synchronizer service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_state_synchronizer() -> StateSynchronizer:
    """Create state synchronizer service"""
    return StateSynchronizer()