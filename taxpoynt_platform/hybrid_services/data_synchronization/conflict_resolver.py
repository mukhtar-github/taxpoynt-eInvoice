"""
Hybrid Service: Conflict Resolver
Resolves data conflicts in distributed synchronization
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import difflib
import copy

from core_platform.database import get_db_session
from core_platform.models.conflicts import Conflict, ConflictResolution, ConflictHistory
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class ConflictType(str, Enum):
    """Types of data conflicts"""
    UPDATE_UPDATE = "update_update"
    DELETE_UPDATE = "delete_update"
    INSERT_INSERT = "insert_insert"
    VERSION_MISMATCH = "version_mismatch"
    SCHEMA_CONFLICT = "schema_conflict"
    BUSINESS_LOGIC = "business_logic"
    REFERENTIAL = "referential"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"


class ConflictSeverity(str, Enum):
    """Conflict severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"


class ResolutionMethod(str, Enum):
    """Conflict resolution methods"""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE = "merge"
    CUSTOM_LOGIC = "custom_logic"
    MANUAL = "manual"
    ROLLBACK = "rollback"
    COMPENSATE = "compensate"
    IGNORE = "ignore"


class ConflictStatus(str, Enum):
    """Conflict resolution status"""
    DETECTED = "detected"
    ANALYZING = "analyzing"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    FAILED = "failed"
    ESCALATED = "escalated"
    IGNORED = "ignored"


class ResolutionOutcome(str, Enum):
    """Resolution outcome types"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    REQUIRES_MANUAL = "requires_manual"
    ESCALATED = "escalated"


@dataclass
class ConflictData:
    """Data involved in a conflict"""
    data_id: str
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    version: int
    timestamp: datetime
    source_role: str
    checksum: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Conflict:
    """Data conflict representation"""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    entity_type: str
    entity_id: str
    conflicting_data: List[ConflictData]
    detected_at: datetime
    detected_by: str
    description: str
    impact_assessment: Dict[str, Any]
    auto_resolvable: bool
    resolution_method: Optional[ResolutionMethod] = None
    status: ConflictStatus = ConflictStatus.DETECTED
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConflictResolution:
    """Conflict resolution result"""
    resolution_id: str
    conflict_id: str
    resolution_method: ResolutionMethod
    resolved_by: str
    resolved_at: datetime
    resolution_data: Dict[str, Any]
    outcome: ResolutionOutcome
    success: bool
    error_message: Optional[str] = None
    rollback_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConflictRule:
    """Rule for conflict detection and resolution"""
    rule_id: str
    name: str
    description: str
    conflict_types: List[ConflictType]
    entity_types: List[str]
    detection_logic: str
    resolution_method: ResolutionMethod
    priority: int
    auto_resolve: bool
    escalation_threshold: int
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MergeStrategy:
    """Strategy for merging conflicting data"""
    strategy_id: str
    name: str
    entity_types: List[str]
    field_priorities: Dict[str, str]  # field -> priority_rule
    merge_functions: Dict[str, str]  # field -> merge_function
    conflict_resolution: Dict[str, str]  # conflict_type -> resolution
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConflictResolver:
    """
    Conflict Resolver service
    Resolves data conflicts in distributed synchronization
    """
    
    def __init__(self):
        """Initialize conflict resolver service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.conflicts: Dict[str, Conflict] = {}
        self.conflict_rules: Dict[str, ConflictRule] = {}
        self.merge_strategies: Dict[str, MergeStrategy] = {}
        self.resolutions: Dict[str, ConflictResolution] = {}
        self.resolution_functions: Dict[ResolutionMethod, Callable] = {}
        self.escalation_queue: List[str] = []
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour
        self.resolution_timeout = 1800  # 30 minutes
        self.escalation_threshold = 3
        self.max_resolution_attempts = 3
        self.conflict_retention_days = 7
        
        # Initialize components
        self._initialize_default_rules()
        self._initialize_merge_strategies()
        self._initialize_resolution_functions()
    
    def _initialize_default_rules(self):
        """Initialize default conflict rules"""
        default_rules = [
            # Update-Update conflict rule
            ConflictRule(
                rule_id="update_update_rule",
                name="Update-Update Conflict Detection",
                description="Detect conflicts when multiple roles update same entity",
                conflict_types=[ConflictType.UPDATE_UPDATE],
                entity_types=["invoice", "transaction", "certificate"],
                detection_logic="timestamp_overlap",
                resolution_method=ResolutionMethod.LAST_WRITE_WINS,
                priority=1,
                auto_resolve=True,
                escalation_threshold=2
            ),
            
            # Version mismatch rule
            ConflictRule(
                rule_id="version_mismatch_rule",
                name="Version Mismatch Detection",
                description="Detect version conflicts across roles",
                conflict_types=[ConflictType.VERSION_MISMATCH],
                entity_types=["state", "configuration"],
                detection_logic="version_check",
                resolution_method=ResolutionMethod.MERGE,
                priority=2,
                auto_resolve=True,
                escalation_threshold=1
            ),
            
            # Business logic conflict rule
            ConflictRule(
                rule_id="business_logic_rule",
                name="Business Logic Conflict Detection",
                description="Detect business logic conflicts",
                conflict_types=[ConflictType.BUSINESS_LOGIC],
                entity_types=["invoice", "validation_result"],
                detection_logic="business_validation",
                resolution_method=ResolutionMethod.CUSTOM_LOGIC,
                priority=1,
                auto_resolve=False,
                escalation_threshold=1
            ),
            
            # Schema conflict rule
            ConflictRule(
                rule_id="schema_conflict_rule",
                name="Schema Conflict Detection",
                description="Detect schema incompatibilities",
                conflict_types=[ConflictType.SCHEMA_CONFLICT],
                entity_types=["*"],
                detection_logic="schema_validation",
                resolution_method=ResolutionMethod.MANUAL,
                priority=1,
                auto_resolve=False,
                escalation_threshold=1
            ),
            
            # Delete-Update conflict rule
            ConflictRule(
                rule_id="delete_update_rule",
                name="Delete-Update Conflict Detection",
                description="Detect conflicts between delete and update operations",
                conflict_types=[ConflictType.DELETE_UPDATE],
                entity_types=["*"],
                detection_logic="operation_conflict",
                resolution_method=ResolutionMethod.MANUAL,
                priority=1,
                auto_resolve=False,
                escalation_threshold=1
            )
        ]
        
        for rule in default_rules:
            self.conflict_rules[rule.rule_id] = rule
    
    def _initialize_merge_strategies(self):
        """Initialize merge strategies"""
        default_strategies = [
            # Invoice merge strategy
            MergeStrategy(
                strategy_id="invoice_merge",
                name="Invoice Data Merge Strategy",
                entity_types=["invoice"],
                field_priorities={
                    "amount": "latest_timestamp",
                    "tax": "latest_timestamp",
                    "total": "calculated",
                    "status": "highest_priority",
                    "created_at": "earliest_timestamp",
                    "updated_at": "latest_timestamp"
                },
                merge_functions={
                    "amount": "take_latest",
                    "tax": "take_latest",
                    "total": "calculate_sum",
                    "status": "priority_merge",
                    "items": "array_merge"
                },
                conflict_resolution={
                    "amount_mismatch": "take_latest",
                    "tax_calculation": "recalculate",
                    "status_conflict": "escalate"
                }
            ),
            
            # Configuration merge strategy
            MergeStrategy(
                strategy_id="config_merge",
                name="Configuration Merge Strategy",
                entity_types=["configuration"],
                field_priorities={
                    "system_settings": "merge_objects",
                    "user_preferences": "merge_objects",
                    "security_config": "highest_security",
                    "version": "latest_version"
                },
                merge_functions={
                    "system_settings": "deep_merge",
                    "user_preferences": "user_preference_merge",
                    "security_config": "security_merge"
                },
                conflict_resolution={
                    "setting_conflict": "merge_with_precedence",
                    "security_conflict": "highest_security"
                }
            ),
            
            # Session merge strategy
            MergeStrategy(
                strategy_id="session_merge",
                name="Session Data Merge Strategy",
                entity_types=["user_session"],
                field_priorities={
                    "last_activity": "latest_timestamp",
                    "permissions": "union",
                    "session_data": "merge_objects",
                    "expires_at": "latest_expiry"
                },
                merge_functions={
                    "last_activity": "take_latest",
                    "permissions": "permission_union",
                    "session_data": "session_merge"
                },
                conflict_resolution={
                    "permission_conflict": "union",
                    "expiry_conflict": "latest_expiry"
                }
            )
        ]
        
        for strategy in default_strategies:
            self.merge_strategies[strategy.strategy_id] = strategy
    
    def _initialize_resolution_functions(self):
        """Initialize resolution functions"""
        self.resolution_functions = {
            ResolutionMethod.LAST_WRITE_WINS: self._resolve_last_write_wins,
            ResolutionMethod.FIRST_WRITE_WINS: self._resolve_first_write_wins,
            ResolutionMethod.MERGE: self._resolve_merge,
            ResolutionMethod.CUSTOM_LOGIC: self._resolve_custom_logic,
            ResolutionMethod.MANUAL: self._resolve_manual,
            ResolutionMethod.ROLLBACK: self._resolve_rollback,
            ResolutionMethod.COMPENSATE: self._resolve_compensate,
            ResolutionMethod.IGNORE: self._resolve_ignore
        }
    
    async def initialize(self):
        """Initialize the conflict resolver service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing conflict resolver service")
        
        try:
            # Initialize dependencies
            await self.cache.initialize()
            await self.event_bus.initialize()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._conflict_detector())
            asyncio.create_task(self._auto_resolver())
            asyncio.create_task(self._escalation_handler())
            asyncio.create_task(self._cleanup_resolved_conflicts())
            
            self.is_initialized = True
            self.logger.info("Conflict resolver service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing conflict resolver service: {str(e)}")
            raise
    
    async def detect_conflict(
        self,
        entity_type: str,
        entity_id: str,
        conflicting_data: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> Optional[Conflict]:
        """Detect and analyze potential conflicts"""
        try:
            if len(conflicting_data) < 2:
                return None  # Need at least 2 data versions to have conflict
            
            # Convert to ConflictData objects
            conflict_data_objects = []
            for i, data_item in enumerate(conflicting_data):
                conflict_data = ConflictData(
                    data_id=str(uuid.uuid4()),
                    entity_type=entity_type,
                    entity_id=entity_id,
                    data=data_item.get("data", {}),
                    version=data_item.get("version", 1),
                    timestamp=datetime.fromisoformat(data_item.get("timestamp", datetime.now(timezone.utc).isoformat())),
                    source_role=data_item.get("source_role", "unknown"),
                    checksum=hashlib.sha256(json.dumps(data_item.get("data", {}), sort_keys=True).encode()).hexdigest(),
                    metadata=data_item.get("metadata", {})
                )
                conflict_data_objects.append(conflict_data)
            
            # Analyze conflict type
            conflict_type = await self._analyze_conflict_type(conflict_data_objects)
            
            if conflict_type == ConflictType.UPDATE_UPDATE:
                # No actual conflict if data is identical
                checksums = set(cd.checksum for cd in conflict_data_objects)
                if len(checksums) == 1:
                    return None
            
            # Determine conflict severity
            severity = await self._assess_conflict_severity(conflict_type, conflict_data_objects, context)
            
            # Find applicable rule
            applicable_rule = await self._find_applicable_rule(conflict_type, entity_type)
            
            # Assess impact
            impact_assessment = await self._assess_conflict_impact(conflict_data_objects, context)
            
            # Create conflict
            conflict = Conflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=conflict_type,
                severity=severity,
                entity_type=entity_type,
                entity_id=entity_id,
                conflicting_data=conflict_data_objects,
                detected_at=datetime.now(timezone.utc),
                detected_by="conflict_resolver",
                description=await self._generate_conflict_description(conflict_type, conflict_data_objects),
                impact_assessment=impact_assessment,
                auto_resolvable=applicable_rule.auto_resolve if applicable_rule else False,
                resolution_method=applicable_rule.resolution_method if applicable_rule else ResolutionMethod.MANUAL,
                status=ConflictStatus.DETECTED,
                metadata={"context": context, "rule_id": applicable_rule.rule_id if applicable_rule else None}
            )
            
            # Store conflict
            self.conflicts[conflict.conflict_id] = conflict
            
            # Cache conflict
            await self.cache.set(
                f"conflict:{conflict.conflict_id}",
                conflict.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit conflict detection event
            await self.event_bus.emit(
                "conflict.detected",
                {
                    "conflict_id": conflict.conflict_id,
                    "conflict_type": conflict_type,
                    "severity": severity,
                    "entity_id": entity_id,
                    "auto_resolvable": conflict.auto_resolvable
                }
            )
            
            self.logger.info(f"Conflict detected: {conflict_type} for entity {entity_id}")
            
            return conflict
            
        except Exception as e:
            self.logger.error(f"Error detecting conflict: {str(e)}")
            return None
    
    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_method: ResolutionMethod = None,
        manual_data: Dict[str, Any] = None
    ) -> ConflictResolution:
        """Resolve a specific conflict"""
        try:
            if conflict_id not in self.conflicts:
                raise ValueError(f"Conflict not found: {conflict_id}")
            
            conflict = self.conflicts[conflict_id]
            conflict.status = ConflictStatus.RESOLVING
            
            # Determine resolution method
            method = resolution_method or conflict.resolution_method or ResolutionMethod.MANUAL
            
            resolution_start = datetime.now(timezone.utc)
            
            # Execute resolution
            if method in self.resolution_functions:
                resolution_result = await self.resolution_functions[method](conflict, manual_data)
            else:
                resolution_result = {
                    "success": False,
                    "error": f"Unknown resolution method: {method}",
                    "data": None
                }
            
            # Create resolution record
            resolution = ConflictResolution(
                resolution_id=str(uuid.uuid4()),
                conflict_id=conflict_id,
                resolution_method=method,
                resolved_by="conflict_resolver",
                resolved_at=datetime.now(timezone.utc),
                resolution_data=resolution_result.get("data", {}),
                outcome=ResolutionOutcome.SUCCESS if resolution_result["success"] else ResolutionOutcome.FAILURE,
                success=resolution_result["success"],
                error_message=resolution_result.get("error"),
                rollback_data=resolution_result.get("rollback_data"),
                metadata={
                    "resolution_duration": (datetime.now(timezone.utc) - resolution_start).total_seconds(),
                    "method_used": method
                }
            )
            
            # Update conflict status
            if resolution.success:
                conflict.status = ConflictStatus.RESOLVED
            else:
                conflict.status = ConflictStatus.FAILED
                
                # Add to escalation queue if not manual
                if method != ResolutionMethod.MANUAL:
                    self.escalation_queue.append(conflict_id)
            
            # Store resolution
            self.resolutions[resolution.resolution_id] = resolution
            
            # Cache resolution
            await self.cache.set(
                f"resolution:{resolution.resolution_id}",
                resolution.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit resolution event
            await self.event_bus.emit(
                "conflict.resolved",
                {
                    "conflict_id": conflict_id,
                    "resolution_id": resolution.resolution_id,
                    "success": resolution.success,
                    "method": method,
                    "outcome": resolution.outcome
                }
            )
            
            self.logger.info(f"Conflict {conflict_id} resolved: {resolution.outcome}")
            
            return resolution
            
        except Exception as e:
            self.logger.error(f"Error resolving conflict: {str(e)}")
            raise
    
    async def bulk_resolve_conflicts(
        self,
        conflict_ids: List[str],
        resolution_method: ResolutionMethod = ResolutionMethod.LAST_WRITE_WINS
    ) -> List[ConflictResolution]:
        """Bulk resolve multiple conflicts"""
        try:
            resolutions = []
            
            for conflict_id in conflict_ids:
                try:
                    resolution = await self.resolve_conflict(conflict_id, resolution_method)
                    resolutions.append(resolution)
                except Exception as e:
                    self.logger.error(f"Error resolving conflict {conflict_id}: {str(e)}")
                    continue
            
            self.logger.info(f"Bulk resolved {len(resolutions)} out of {len(conflict_ids)} conflicts")
            
            return resolutions
            
        except Exception as e:
            self.logger.error(f"Error in bulk resolve conflicts: {str(e)}")
            return []
    
    async def get_conflict_status(self, conflict_id: str) -> Dict[str, Any]:
        """Get status of a specific conflict"""
        try:
            if conflict_id not in self.conflicts:
                return {"status": "not_found"}
            
            conflict = self.conflicts[conflict_id]
            
            # Get related resolutions
            related_resolutions = [
                r for r in self.resolutions.values()
                if r.conflict_id == conflict_id
            ]
            
            return {
                "conflict_id": conflict_id,
                "status": conflict.status,
                "conflict_type": conflict.conflict_type,
                "severity": conflict.severity,
                "detected_at": conflict.detected_at.isoformat(),
                "auto_resolvable": conflict.auto_resolvable,
                "resolution_attempts": len(related_resolutions),
                "last_resolution": related_resolutions[-1].to_dict() if related_resolutions else None,
                "in_escalation": conflict_id in self.escalation_queue
            }
            
        except Exception as e:
            self.logger.error(f"Error getting conflict status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_conflicts_summary(
        self,
        entity_type: str = None,
        severity: ConflictSeverity = None,
        status: ConflictStatus = None
    ) -> Dict[str, Any]:
        """Get summary of conflicts"""
        try:
            # Filter conflicts
            filtered_conflicts = list(self.conflicts.values())
            
            if entity_type:
                filtered_conflicts = [c for c in filtered_conflicts if c.entity_type == entity_type]
            
            if severity:
                filtered_conflicts = [c for c in filtered_conflicts if c.severity == severity]
            
            if status:
                filtered_conflicts = [c for c in filtered_conflicts if c.status == status]
            
            # Calculate statistics
            total_conflicts = len(filtered_conflicts)
            resolved_conflicts = len([c for c in filtered_conflicts if c.status == ConflictStatus.RESOLVED])
            failed_conflicts = len([c for c in filtered_conflicts if c.status == ConflictStatus.FAILED])
            pending_conflicts = len([c for c in filtered_conflicts if c.status in [ConflictStatus.DETECTED, ConflictStatus.ANALYZING]])
            
            # Group by type and severity
            conflicts_by_type = {}
            for conflict_type in ConflictType:
                conflicts_by_type[conflict_type] = len([c for c in filtered_conflicts if c.conflict_type == conflict_type])
            
            conflicts_by_severity = {}
            for sev in ConflictSeverity:
                conflicts_by_severity[sev] = len([c for c in filtered_conflicts if c.severity == sev])
            
            return {
                "total_conflicts": total_conflicts,
                "resolved_conflicts": resolved_conflicts,
                "failed_conflicts": failed_conflicts,
                "pending_conflicts": pending_conflicts,
                "resolution_rate": (resolved_conflicts / total_conflicts) * 100 if total_conflicts > 0 else 0,
                "conflicts_by_type": conflicts_by_type,
                "conflicts_by_severity": conflicts_by_severity,
                "escalation_queue_size": len(self.escalation_queue),
                "auto_resolvable": len([c for c in filtered_conflicts if c.auto_resolvable])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting conflicts summary: {str(e)}")
            return {}
    
    async def _analyze_conflict_type(self, conflict_data: List[ConflictData]) -> ConflictType:
        """Analyze the type of conflict"""
        try:
            if len(conflict_data) < 2:
                return ConflictType.UPDATE_UPDATE
            
            # Sort by timestamp
            sorted_data = sorted(conflict_data, key=lambda x: x.timestamp)
            
            # Check for version conflicts
            versions = [cd.version for cd in conflict_data]
            if len(set(versions)) > 1:
                max_version = max(versions)
                min_version = min(versions)
                if max_version - min_version > 1:
                    return ConflictType.VERSION_MISMATCH
            
            # Check for schema conflicts
            schemas = []
            for cd in conflict_data:
                schema = set(cd.data.keys())
                schemas.append(schema)
            
            if not all(s == schemas[0] for s in schemas):
                return ConflictType.SCHEMA_CONFLICT
            
            # Check for business logic conflicts
            for cd in conflict_data:
                if cd.entity_type == "invoice":
                    amount = cd.data.get("amount", 0)
                    tax = cd.data.get("tax", 0)
                    total = cd.data.get("total", 0)
                    
                    if abs(total - (amount + tax)) > 0.01:
                        return ConflictType.BUSINESS_LOGIC
            
            # Check for temporal conflicts (overlapping operations)
            timestamps = [cd.timestamp for cd in conflict_data]
            time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
            
            if any(diff < 1 for diff in time_diffs):  # Operations within 1 second
                return ConflictType.TEMPORAL
            
            # Default to update-update conflict
            return ConflictType.UPDATE_UPDATE
            
        except Exception as e:
            self.logger.error(f"Error analyzing conflict type: {str(e)}")
            return ConflictType.UPDATE_UPDATE
    
    async def _assess_conflict_severity(
        self,
        conflict_type: ConflictType,
        conflict_data: List[ConflictData],
        context: Dict[str, Any]
    ) -> ConflictSeverity:
        """Assess the severity of a conflict"""
        try:
            # Critical conflicts
            if conflict_type in [ConflictType.BUSINESS_LOGIC, ConflictType.REFERENTIAL]:
                return ConflictSeverity.CRITICAL
            
            # High severity conflicts
            if conflict_type in [ConflictType.DELETE_UPDATE, ConflictType.SCHEMA_CONFLICT]:
                return ConflictSeverity.HIGH
            
            # Check data importance
            entity_type = conflict_data[0].entity_type if conflict_data else "unknown"
            critical_entities = ["invoice", "transaction", "certificate", "payment"]
            
            if entity_type in critical_entities:
                return ConflictSeverity.HIGH
            
            # Check number of conflicting versions
            if len(conflict_data) > 3:
                return ConflictSeverity.HIGH
            
            # Check time spread
            if conflict_data:
                timestamps = [cd.timestamp for cd in conflict_data]
                time_spread = (max(timestamps) - min(timestamps)).total_seconds()
                
                if time_spread > 3600:  # More than 1 hour
                    return ConflictSeverity.MEDIUM
            
            return ConflictSeverity.LOW
            
        except Exception as e:
            self.logger.error(f"Error assessing conflict severity: {str(e)}")
            return ConflictSeverity.MEDIUM
    
    async def _find_applicable_rule(
        self,
        conflict_type: ConflictType,
        entity_type: str
    ) -> Optional[ConflictRule]:
        """Find applicable conflict rule"""
        try:
            applicable_rules = []
            
            for rule in self.conflict_rules.values():
                if not rule.enabled:
                    continue
                
                if conflict_type in rule.conflict_types:
                    if "*" in rule.entity_types or entity_type in rule.entity_types:
                        applicable_rules.append(rule)
            
            if applicable_rules:
                # Return highest priority rule
                return max(applicable_rules, key=lambda r: r.priority)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding applicable rule: {str(e)}")
            return None
    
    async def _assess_conflict_impact(
        self,
        conflict_data: List[ConflictData],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the impact of a conflict"""
        try:
            impact = {
                "data_integrity": "medium",
                "business_operations": "low",
                "user_experience": "low",
                "compliance": "low"
            }
            
            if not conflict_data:
                return impact
            
            entity_type = conflict_data[0].entity_type
            
            # High-impact entities
            if entity_type in ["invoice", "transaction", "payment"]:
                impact["business_operations"] = "high"
                impact["compliance"] = "high"
            
            # User-facing entities
            if entity_type in ["user_session", "authentication", "configuration"]:
                impact["user_experience"] = "high"
            
            # Check data size
            total_data_size = sum(len(json.dumps(cd.data)) for cd in conflict_data)
            if total_data_size > 10000:  # Large data conflicts
                impact["data_integrity"] = "high"
            
            # Check number of roles involved
            roles = set(cd.source_role for cd in conflict_data)
            if len(roles) > 2:
                impact["business_operations"] = "high"
            
            return impact
            
        except Exception as e:
            self.logger.error(f"Error assessing conflict impact: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_conflict_description(
        self,
        conflict_type: ConflictType,
        conflict_data: List[ConflictData]
    ) -> str:
        """Generate human-readable conflict description"""
        try:
            if not conflict_data:
                return f"Unknown {conflict_type} conflict"
            
            entity_id = conflict_data[0].entity_id
            entity_type = conflict_data[0].entity_type
            roles = list(set(cd.source_role for cd in conflict_data))
            
            if conflict_type == ConflictType.UPDATE_UPDATE:
                return f"Concurrent updates to {entity_type} {entity_id} from roles: {', '.join(roles)}"
            elif conflict_type == ConflictType.VERSION_MISMATCH:
                versions = [cd.version for cd in conflict_data]
                return f"Version mismatch for {entity_type} {entity_id}: versions {versions}"
            elif conflict_type == ConflictType.BUSINESS_LOGIC:
                return f"Business logic violation in {entity_type} {entity_id}"
            elif conflict_type == ConflictType.SCHEMA_CONFLICT:
                return f"Schema incompatibility for {entity_type} {entity_id}"
            elif conflict_type == ConflictType.DELETE_UPDATE:
                return f"Delete-update conflict for {entity_type} {entity_id}"
            else:
                return f"{conflict_type} conflict for {entity_type} {entity_id}"
                
        except Exception as e:
            self.logger.error(f"Error generating conflict description: {str(e)}")
            return "Unknown conflict"
    
    async def _resolve_last_write_wins(self, conflict: Conflict, manual_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve conflict using last write wins strategy"""
        try:
            if not conflict.conflicting_data:
                return {"success": False, "error": "No conflicting data"}
            
            # Find latest data
            latest_data = max(conflict.conflicting_data, key=lambda x: x.timestamp)
            
            # Create resolution data
            resolution_data = {
                "chosen_data": latest_data.to_dict(),
                "strategy": "last_write_wins",
                "winning_source": latest_data.source_role,
                "winning_timestamp": latest_data.timestamp.isoformat()
            }
            
            # Apply resolution
            await self._apply_resolution_data(conflict.entity_id, latest_data.data)
            
            return {
                "success": True,
                "data": resolution_data,
                "message": f"Conflict resolved using last write wins: {latest_data.source_role}"
            }
            
        except Exception as e:
            self.logger.error(f"Error in last write wins resolution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_first_write_wins(self, conflict: Conflict, manual_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve conflict using first write wins strategy"""
        try:
            if not conflict.conflicting_data:
                return {"success": False, "error": "No conflicting data"}
            
            # Find earliest data
            earliest_data = min(conflict.conflicting_data, key=lambda x: x.timestamp)
            
            # Create resolution data
            resolution_data = {
                "chosen_data": earliest_data.to_dict(),
                "strategy": "first_write_wins",
                "winning_source": earliest_data.source_role,
                "winning_timestamp": earliest_data.timestamp.isoformat()
            }
            
            # Apply resolution
            await self._apply_resolution_data(conflict.entity_id, earliest_data.data)
            
            return {
                "success": True,
                "data": resolution_data,
                "message": f"Conflict resolved using first write wins: {earliest_data.source_role}"
            }
            
        except Exception as e:
            self.logger.error(f"Error in first write wins resolution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_merge(self, conflict: Conflict, manual_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve conflict using merge strategy"""
        try:
            if len(conflict.conflicting_data) < 2:
                return {"success": False, "error": "Need at least 2 data versions to merge"}
            
            # Find applicable merge strategy
            merge_strategy = await self._find_merge_strategy(conflict.entity_type)
            
            if not merge_strategy:
                return {"success": False, "error": "No merge strategy available"}
            
            # Perform merge
            merged_data = await self._perform_merge(conflict.conflicting_data, merge_strategy)
            
            # Create resolution data
            resolution_data = {
                "merged_data": merged_data,
                "strategy": "merge",
                "merge_strategy_id": merge_strategy.strategy_id,
                "sources_merged": [cd.source_role for cd in conflict.conflicting_data]
            }
            
            # Apply resolution
            await self._apply_resolution_data(conflict.entity_id, merged_data)
            
            return {
                "success": True,
                "data": resolution_data,
                "message": f"Conflict resolved using merge strategy: {merge_strategy.name}"
            }
            
        except Exception as e:
            self.logger.error(f"Error in merge resolution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_custom_logic(self, conflict: Conflict, manual_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve conflict using custom business logic"""
        try:
            entity_type = conflict.entity_type
            
            if entity_type == "invoice":
                return await self._resolve_invoice_conflict(conflict)
            elif entity_type == "transaction":
                return await self._resolve_transaction_conflict(conflict)
            elif entity_type == "configuration":
                return await self._resolve_configuration_conflict(conflict)
            else:
                return {"success": False, "error": f"No custom logic for entity type: {entity_type}"}
                
        except Exception as e:
            self.logger.error(f"Error in custom logic resolution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_manual(self, conflict: Conflict, manual_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve conflict manually"""
        try:
            if not manual_data:
                return {"success": False, "error": "Manual resolution requires manual_data"}
            
            # Use provided manual data
            resolution_data = {
                "manual_data": manual_data,
                "strategy": "manual",
                "resolved_by": manual_data.get("resolved_by", "manual")
            }
            
            # Apply resolution
            resolved_data = manual_data.get("resolved_data", {})
            await self._apply_resolution_data(conflict.entity_id, resolved_data)
            
            return {
                "success": True,
                "data": resolution_data,
                "message": "Conflict resolved manually"
            }
            
        except Exception as e:
            self.logger.error(f"Error in manual resolution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_rollback(self, conflict: Conflict, manual_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve conflict by rolling back to previous state"""
        try:
            # Find last known good state (simplified)
            # In practice, this would involve database transactions
            
            if not conflict.conflicting_data:
                return {"success": False, "error": "No data to rollback"}
            
            # Use earliest data as "last known good"
            rollback_data = min(conflict.conflicting_data, key=lambda x: x.timestamp)
            
            resolution_data = {
                "rollback_data": rollback_data.to_dict(),
                "strategy": "rollback",
                "rollback_to": rollback_data.timestamp.isoformat()
            }
            
            # Apply rollback
            await self._apply_resolution_data(conflict.entity_id, rollback_data.data)
            
            return {
                "success": True,
                "data": resolution_data,
                "rollback_data": rollback_data.to_dict(),
                "message": f"Conflict resolved by rolling back to {rollback_data.timestamp}"
            }
            
        except Exception as e:
            self.logger.error(f"Error in rollback resolution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_compensate(self, conflict: Conflict, manual_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve conflict using compensating transactions"""
        try:
            # Create compensating actions
            compensation_actions = []
            
            for conflict_data in conflict.conflicting_data:
                # Create compensating action based on entity type
                if conflict_data.entity_type == "invoice":
                    # Compensate invoice conflicts
                    action = {
                        "action_type": "recalculate_totals",
                        "entity_id": conflict.entity_id,
                        "data": conflict_data.data
                    }
                    compensation_actions.append(action)
            
            # Execute compensation actions
            for action in compensation_actions:
                await self._execute_compensation_action(action)
            
            resolution_data = {
                "compensation_actions": compensation_actions,
                "strategy": "compensate"
            }
            
            return {
                "success": True,
                "data": resolution_data,
                "message": f"Conflict resolved using {len(compensation_actions)} compensating actions"
            }
            
        except Exception as e:
            self.logger.error(f"Error in compensate resolution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_ignore(self, conflict: Conflict, manual_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Resolve conflict by ignoring it"""
        try:
            resolution_data = {
                "strategy": "ignore",
                "reason": "Conflict marked as ignorable"
            }
            
            return {
                "success": True,
                "data": resolution_data,
                "message": "Conflict ignored as requested"
            }
            
        except Exception as e:
            self.logger.error(f"Error in ignore resolution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _find_merge_strategy(self, entity_type: str) -> Optional[MergeStrategy]:
        """Find applicable merge strategy for entity type"""
        try:
            for strategy in self.merge_strategies.values():
                if entity_type in strategy.entity_types:
                    return strategy
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding merge strategy: {str(e)}")
            return None
    
    async def _perform_merge(
        self,
        conflicting_data: List[ConflictData],
        merge_strategy: MergeStrategy
    ) -> Dict[str, Any]:
        """Perform data merge using strategy"""
        try:
            if not conflicting_data:
                return {}
            
            # Start with base data
            merged_data = {}
            base_data = conflicting_data[0].data
            merged_data.update(base_data)
            
            # Merge other data according to strategy
            for field, priority_rule in merge_strategy.field_priorities.items():
                field_values = []
                
                for cd in conflicting_data:
                    if field in cd.data:
                        field_values.append({
                            "value": cd.data[field],
                            "timestamp": cd.timestamp,
                            "source": cd.source_role,
                            "version": cd.version
                        })
                
                if field_values:
                    merged_value = await self._merge_field_values(field, field_values, priority_rule)
                    merged_data[field] = merged_value
            
            # Apply merge functions
            for field, merge_function in merge_strategy.merge_functions.items():
                if field in merged_data:
                    merged_data[field] = await self._apply_merge_function(
                        merge_function,
                        field,
                        [cd.data.get(field) for cd in conflicting_data if field in cd.data]
                    )
            
            return merged_data
            
        except Exception as e:
            self.logger.error(f"Error performing merge: {str(e)}")
            return {}
    
    async def _merge_field_values(
        self,
        field: str,
        field_values: List[Dict[str, Any]],
        priority_rule: str
    ) -> Any:
        """Merge field values according to priority rule"""
        try:
            if not field_values:
                return None
            
            if priority_rule == "latest_timestamp":
                return max(field_values, key=lambda x: x["timestamp"])["value"]
            elif priority_rule == "earliest_timestamp":
                return min(field_values, key=lambda x: x["timestamp"])["value"]
            elif priority_rule == "highest_priority":
                # Define role priorities
                role_priorities = {"app": 3, "si": 2, "system": 1}
                return max(field_values, key=lambda x: role_priorities.get(x["source"], 0))["value"]
            elif priority_rule == "latest_version":
                return max(field_values, key=lambda x: x["version"])["value"]
            elif priority_rule == "calculated":
                # For calculated fields, recalculate
                if field == "total":
                    # Find amount and tax from same data
                    for fv in field_values:
                        if isinstance(fv["value"], dict):
                            amount = fv["value"].get("amount", 0)
                            tax = fv["value"].get("tax", 0)
                            return amount + tax
                return field_values[0]["value"]
            else:
                return field_values[0]["value"]
                
        except Exception as e:
            self.logger.error(f"Error merging field values: {str(e)}")
            return field_values[0]["value"] if field_values else None
    
    async def _apply_merge_function(self, merge_function: str, field: str, values: List[Any]) -> Any:
        """Apply merge function to field values"""
        try:
            if not values:
                return None
            
            if merge_function == "take_latest":
                return values[-1]
            elif merge_function == "take_first":
                return values[0]
            elif merge_function == "calculate_sum":
                if field in ["amount", "tax", "total"]:
                    return sum(v for v in values if isinstance(v, (int, float)))
            elif merge_function == "array_merge":
                if all(isinstance(v, list) for v in values):
                    merged = []
                    for v in values:
                        merged.extend(v)
                    return merged
            elif merge_function == "deep_merge":
                if all(isinstance(v, dict) for v in values):
                    merged = {}
                    for v in values:
                        merged.update(v)
                    return merged
            
            return values[0]
            
        except Exception as e:
            self.logger.error(f"Error applying merge function: {str(e)}")
            return values[0] if values else None
    
    async def _resolve_invoice_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """Resolve invoice-specific conflicts"""
        try:
            if not conflict.conflicting_data:
                return {"success": False, "error": "No invoice data to resolve"}
            
            # Invoice business logic resolution
            latest_data = max(conflict.conflicting_data, key=lambda x: x.timestamp)
            invoice_data = latest_data.data.copy()
            
            # Recalculate totals
            amount = invoice_data.get("amount", 0)
            tax = invoice_data.get("tax", 0)
            invoice_data["total"] = amount + tax
            
            # Validate invoice status
            status = invoice_data.get("status", "draft")
            if status not in ["draft", "sent", "paid", "cancelled"]:
                invoice_data["status"] = "draft"
            
            resolution_data = {
                "resolved_data": invoice_data,
                "strategy": "invoice_business_logic",
                "recalculated_fields": ["total"],
                "validated_fields": ["status"]
            }
            
            await self._apply_resolution_data(conflict.entity_id, invoice_data)
            
            return {
                "success": True,
                "data": resolution_data,
                "message": "Invoice conflict resolved using business logic"
            }
            
        except Exception as e:
            self.logger.error(f"Error resolving invoice conflict: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_transaction_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """Resolve transaction-specific conflicts"""
        try:
            # Transaction conflicts require careful handling
            # Use last write wins for most fields, but preserve audit trail
            
            latest_data = max(conflict.conflicting_data, key=lambda x: x.timestamp)
            transaction_data = latest_data.data.copy()
            
            # Preserve audit information
            transaction_data["conflict_resolved"] = True
            transaction_data["original_sources"] = [cd.source_role for cd in conflict.conflicting_data]
            
            resolution_data = {
                "resolved_data": transaction_data,
                "strategy": "transaction_preservation",
                "audit_preserved": True
            }
            
            await self._apply_resolution_data(conflict.entity_id, transaction_data)
            
            return {
                "success": True,
                "data": resolution_data,
                "message": "Transaction conflict resolved with audit preservation"
            }
            
        except Exception as e:
            self.logger.error(f"Error resolving transaction conflict: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_configuration_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """Resolve configuration-specific conflicts"""
        try:
            # Configuration conflicts use merge strategy
            merged_config = {}
            
            for cd in conflict.conflicting_data:
                config_data = cd.data
                
                # Merge configurations with precedence rules
                for key, value in config_data.items():
                    if key not in merged_config:
                        merged_config[key] = value
                    elif key.startswith("security_"):
                        # Security settings: use most restrictive
                        if isinstance(value, bool) and not value:
                            merged_config[key] = value
                    elif key.startswith("user_"):
                        # User settings: use latest
                        if cd.timestamp >= max(other.timestamp for other in conflict.conflicting_data if other != cd):
                            merged_config[key] = value
            
            resolution_data = {
                "resolved_data": merged_config,
                "strategy": "configuration_merge",
                "merge_rules_applied": ["security_restrictive", "user_latest"]
            }
            
            await self._apply_resolution_data(conflict.entity_id, merged_config)
            
            return {
                "success": True,
                "data": resolution_data,
                "message": "Configuration conflict resolved using merge rules"
            }
            
        except Exception as e:
            self.logger.error(f"Error resolving configuration conflict: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _apply_resolution_data(self, entity_id: str, resolved_data: Dict[str, Any]):
        """Apply resolved data to the entity"""
        try:
            # This would typically update the database or notify other services
            # For now, we'll cache the resolved data
            
            await self.cache.set(
                f"resolved_entity:{entity_id}",
                {
                    "entity_id": entity_id,
                    "resolved_data": resolved_data,
                    "resolved_at": datetime.now(timezone.utc).isoformat()
                },
                ttl=self.cache_ttl
            )
            
            # Emit data resolution event
            await self.event_bus.emit(
                "data.resolved",
                {
                    "entity_id": entity_id,
                    "resolved_data": resolved_data,
                    "resolved_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error applying resolution data: {str(e)}")
    
    async def _execute_compensation_action(self, action: Dict[str, Any]):
        """Execute a compensating action"""
        try:
            action_type = action.get("action_type")
            entity_id = action.get("entity_id")
            data = action.get("data", {})
            
            if action_type == "recalculate_totals":
                # Recalculate invoice totals
                amount = data.get("amount", 0)
                tax = data.get("tax", 0)
                corrected_data = data.copy()
                corrected_data["total"] = amount + tax
                
                await self._apply_resolution_data(entity_id, corrected_data)
            
            # Add more compensation action types as needed
            
        except Exception as e:
            self.logger.error(f"Error executing compensation action: {str(e)}")
    
    async def _conflict_detector(self):
        """Background conflict detector"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # This would typically monitor data changes and detect conflicts
                # For now, it's a placeholder for future implementation
                
            except Exception as e:
                self.logger.error(f"Error in conflict detector: {str(e)}")
    
    async def _auto_resolver(self):
        """Background auto resolver"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Find auto-resolvable conflicts
                auto_resolvable = [
                    c for c in self.conflicts.values()
                    if c.auto_resolvable and c.status == ConflictStatus.DETECTED
                ]
                
                for conflict in auto_resolvable:
                    try:
                        await self.resolve_conflict(conflict.conflict_id)
                    except Exception as e:
                        self.logger.error(f"Error auto-resolving conflict {conflict.conflict_id}: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"Error in auto resolver: {str(e)}")
    
    async def _escalation_handler(self):
        """Background escalation handler"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Process escalation queue
                for conflict_id in self.escalation_queue[:]:
                    try:
                        # Send escalation notification
                        await self.notification_service.send_notification(
                            type="conflict_escalation",
                            data={
                                "conflict_id": conflict_id,
                                "escalated_at": datetime.now(timezone.utc).isoformat()
                            }
                        )
                        
                        # Update conflict status
                        if conflict_id in self.conflicts:
                            self.conflicts[conflict_id].status = ConflictStatus.ESCALATED
                        
                        # Remove from queue
                        self.escalation_queue.remove(conflict_id)
                        
                    except Exception as e:
                        self.logger.error(f"Error handling escalation for {conflict_id}: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"Error in escalation handler: {str(e)}")
    
    async def _cleanup_resolved_conflicts(self):
        """Cleanup resolved conflicts periodically"""
        while True:
            try:
                await asyncio.sleep(86400)  # Run daily
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.conflict_retention_days)
                
                # Remove old resolved conflicts
                resolved_conflicts = [
                    c_id for c_id, c in self.conflicts.items()
                    if c.status == ConflictStatus.RESOLVED and c.detected_at < cutoff_time
                ]
                
                for conflict_id in resolved_conflicts:
                    del self.conflicts[conflict_id]
                
                # Remove old resolutions
                old_resolutions = [
                    r_id for r_id, r in self.resolutions.items()
                    if r.resolved_at < cutoff_time
                ]
                
                for resolution_id in old_resolutions:
                    del self.resolutions[resolution_id]
                
                self.logger.info(f"Cleaned up {len(resolved_conflicts)} old conflicts and {len(old_resolutions)} old resolutions")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "data.conflict_suspected",
                self._handle_conflict_suspected
            )
            
            await self.event_bus.subscribe(
                "sync.conflict_detected",
                self._handle_sync_conflict
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_conflict_suspected(self, event_data: Dict[str, Any]):
        """Handle conflict suspected event"""
        try:
            entity_type = event_data.get("entity_type")
            entity_id = event_data.get("entity_id")
            conflicting_data = event_data.get("conflicting_data", [])
            
            if entity_type and entity_id and conflicting_data:
                await self.detect_conflict(entity_type, entity_id, conflicting_data)
            
        except Exception as e:
            self.logger.error(f"Error handling conflict suspected: {str(e)}")
    
    async def _handle_sync_conflict(self, event_data: Dict[str, Any]):
        """Handle sync conflict event"""
        try:
            conflict_data = event_data.get("conflict_data")
            
            if conflict_data:
                entity_type = conflict_data.get("entity_type")
                entity_id = conflict_data.get("entity_id")
                data_versions = conflict_data.get("data_versions", [])
                
                await self.detect_conflict(entity_type, entity_id, data_versions)
            
        except Exception as e:
            self.logger.error(f"Error handling sync conflict: {str(e)}")
    
    async def get_resolver_summary(self) -> Dict[str, Any]:
        """Get conflict resolver summary"""
        try:
            return {
                "total_conflicts": len(self.conflicts),
                "total_rules": len(self.conflict_rules),
                "total_merge_strategies": len(self.merge_strategies),
                "total_resolutions": len(self.resolutions),
                "escalation_queue_size": len(self.escalation_queue),
                "conflicts_by_status": {
                    status.value: len([c for c in self.conflicts.values() if c.status == status])
                    for status in ConflictStatus
                },
                "conflicts_by_type": {
                    conf_type.value: len([c for c in self.conflicts.values() if c.conflict_type == conf_type])
                    for conf_type in ConflictType
                },
                "resolution_success_rate": self._calculate_resolution_success_rate(),
                "is_initialized": self.is_initialized
            }
            
        except Exception as e:
            self.logger.error(f"Error getting resolver summary: {str(e)}")
            return {}
    
    def _calculate_resolution_success_rate(self) -> float:
        """Calculate resolution success rate"""
        try:
            if not self.resolutions:
                return 0.0
            
            successful = len([r for r in self.resolutions.values() if r.success])
            return (successful / len(self.resolutions)) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating resolution success rate: {str(e)}")
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "conflict_resolver",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_conflicts": len(self.conflicts),
                    "pending_conflicts": len([c for c in self.conflicts.values() if c.status == ConflictStatus.DETECTED]),
                    "escalation_queue": len(self.escalation_queue)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "conflict_resolver",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Conflict resolver service cleanup initiated")
        
        try:
            # Clear all state
            self.conflicts.clear()
            self.resolutions.clear()
            self.escalation_queue.clear()
            
            # Cleanup dependencies
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Conflict resolver service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_conflict_resolver() -> ConflictResolver:
    """Create conflict resolver service"""
    return ConflictResolver()