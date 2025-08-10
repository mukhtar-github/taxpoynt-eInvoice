"""
Hybrid Service: Consistency Manager
Ensures data consistency across the platform between SI and APP roles
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
from core_platform.models.consistency import ConsistencyRule, ConsistencyViolation, ConsistencyCheck
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class ConsistencyLevel(str, Enum):
    """Data consistency levels"""
    STRONG = "strong"
    EVENTUAL = "eventual"
    WEAK = "weak"
    SESSION = "session"
    CAUSAL = "causal"
    MONOTONIC_READ = "monotonic_read"
    MONOTONIC_WRITE = "monotonic_write"


class ConsistencyScope(str, Enum):
    """Scope of consistency checks"""
    SI_ONLY = "si_only"
    APP_ONLY = "app_only"
    CROSS_ROLE = "cross_role"
    GLOBAL = "global"
    TRANSACTION = "transaction"


class ViolationType(str, Enum):
    """Types of consistency violations"""
    DATA_MISMATCH = "data_mismatch"
    VERSION_CONFLICT = "version_conflict"
    TIMESTAMP_INCONSISTENCY = "timestamp_inconsistency"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    BUSINESS_RULE = "business_rule"
    SCHEMA_VIOLATION = "schema_violation"
    ORDERING_VIOLATION = "ordering_violation"
    ISOLATION_VIOLATION = "isolation_violation"


class ViolationSeverity(str, Enum):
    """Severity levels for violations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"


class ResolutionStrategy(str, Enum):
    """Strategies for resolving violations"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE = "merge"
    ROLLBACK = "rollback"
    COMPENSATE = "compensate"


@dataclass
class ConsistencyRule:
    """Rule for checking data consistency"""
    rule_id: str
    name: str
    description: str
    consistency_level: ConsistencyLevel
    scope: ConsistencyScope
    data_entities: List[str]
    validation_logic: str
    auto_resolve: bool
    resolution_strategy: ResolutionStrategy
    priority: int
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DataSnapshot:
    """Snapshot of data for consistency checking"""
    snapshot_id: str
    entity_id: str
    entity_type: str
    data: Dict[str, Any]
    version: int
    timestamp: datetime
    source_role: str
    checksum: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for data"""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


@dataclass
class ConsistencyViolation:
    """Detected consistency violation"""
    violation_id: str
    rule_id: str
    violation_type: ViolationType
    severity: ViolationSeverity
    affected_entities: List[str]
    description: str
    detected_at: datetime
    source_snapshots: List[DataSnapshot]
    expected_state: Dict[str, Any]
    actual_state: Dict[str, Any]
    auto_resolvable: bool
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyCheck:
    """Consistency check execution"""
    check_id: str
    rule_id: str
    check_type: str
    scope: ConsistencyScope
    start_time: datetime
    end_time: Optional[datetime]
    entities_checked: int
    violations_found: int
    violations: List[ConsistencyViolation]
    success: bool
    duration: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyReport:
    """Comprehensive consistency report"""
    report_id: str
    generation_time: datetime
    scope: ConsistencyScope
    time_range: Tuple[datetime, datetime]
    total_checks: int
    total_violations: int
    violations_by_type: Dict[ViolationType, int]
    violations_by_severity: Dict[ViolationSeverity, int]
    resolution_summary: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConsistencyManager:
    """
    Consistency Manager service
    Ensures data consistency across the platform between SI and APP roles
    """
    
    def __init__(self):
        """Initialize consistency manager service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.consistency_rules: Dict[str, ConsistencyRule] = {}
        self.data_snapshots: Dict[str, List[DataSnapshot]] = {}  # entity_id -> snapshots
        self.violations: Dict[str, ConsistencyViolation] = {}
        self.consistency_checks: Dict[str, ConsistencyCheck] = {}
        self.consistency_sessions: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour
        self.snapshot_retention_hours = 72  # 3 days
        self.check_interval = 300  # 5 minutes
        self.max_snapshots_per_entity = 100
        self.violation_resolution_timeout = 1800  # 30 minutes
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default consistency rules"""
        default_rules = [
            # Data integrity rule
            ConsistencyRule(
                rule_id="data_integrity_cross_role",
                name="Cross-Role Data Integrity",
                description="Ensure data integrity between SI and APP roles",
                consistency_level=ConsistencyLevel.STRONG,
                scope=ConsistencyScope.CROSS_ROLE,
                data_entities=["invoice", "transaction", "certificate"],
                validation_logic="checksum_validation",
                auto_resolve=True,
                resolution_strategy=ResolutionStrategy.LAST_WRITE_WINS,
                priority=1
            ),
            
            # Version consistency rule
            ConsistencyRule(
                rule_id="version_consistency",
                name="Version Consistency",
                description="Ensure version consistency across roles",
                consistency_level=ConsistencyLevel.EVENTUAL,
                scope=ConsistencyScope.CROSS_ROLE,
                data_entities=["state", "configuration", "session"],
                validation_logic="version_validation",
                auto_resolve=True,
                resolution_strategy=ResolutionStrategy.MERGE,
                priority=2
            ),
            
            # Referential integrity rule
            ConsistencyRule(
                rule_id="referential_integrity",
                name="Referential Integrity",
                description="Ensure referential integrity across entities",
                consistency_level=ConsistencyLevel.STRONG,
                scope=ConsistencyScope.GLOBAL,
                data_entities=["customer", "invoice", "transaction"],
                validation_logic="referential_validation",
                auto_resolve=False,
                resolution_strategy=ResolutionStrategy.MANUAL,
                priority=1
            ),
            
            # Business rule consistency
            ConsistencyRule(
                rule_id="business_rule_consistency",
                name="Business Rule Consistency",
                description="Ensure business rules are consistently applied",
                consistency_level=ConsistencyLevel.CAUSAL,
                scope=ConsistencyScope.CROSS_ROLE,
                data_entities=["validation_result", "compliance_check"],
                validation_logic="business_rule_validation",
                auto_resolve=True,
                resolution_strategy=ResolutionStrategy.COMPENSATE,
                priority=2
            ),
            
            # Session consistency rule
            ConsistencyRule(
                rule_id="session_consistency",
                name="Session Consistency",
                description="Ensure session data consistency",
                consistency_level=ConsistencyLevel.SESSION,
                scope=ConsistencyScope.CROSS_ROLE,
                data_entities=["user_session", "authentication"],
                validation_logic="session_validation",
                auto_resolve=True,
                resolution_strategy=ResolutionStrategy.ROLLBACK,
                priority=3
            ),
            
            # Temporal consistency rule
            ConsistencyRule(
                rule_id="temporal_consistency",
                name="Temporal Consistency",
                description="Ensure temporal ordering of operations",
                consistency_level=ConsistencyLevel.MONOTONIC_WRITE,
                scope=ConsistencyScope.CROSS_ROLE,
                data_entities=["audit_log", "event_sequence"],
                validation_logic="temporal_validation",
                auto_resolve=False,
                resolution_strategy=ResolutionStrategy.MANUAL,
                priority=2
            )
        ]
        
        for rule in default_rules:
            self.consistency_rules[rule.rule_id] = rule
    
    async def initialize(self):
        """Initialize the consistency manager service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing consistency manager service")
        
        try:
            # Initialize dependencies
            await self.cache.initialize()
            await self.event_bus.initialize()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._consistency_checker())
            asyncio.create_task(self._violation_resolver())
            asyncio.create_task(self._snapshot_cleaner())
            
            self.is_initialized = True
            self.logger.info("Consistency manager service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing consistency manager service: {str(e)}")
            raise
    
    async def register_consistency_rule(self, rule: ConsistencyRule):
        """Register a new consistency rule"""
        try:
            self.consistency_rules[rule.rule_id] = rule
            
            # Cache the rule
            await self.cache.set(
                f"consistency_rule:{rule.rule_id}",
                rule.to_dict(),
                ttl=self.cache_ttl
            )
            
            self.logger.info(f"Registered consistency rule: {rule.name}")
            
        except Exception as e:
            self.logger.error(f"Error registering consistency rule: {str(e)}")
            raise
    
    async def capture_data_snapshot(
        self,
        entity_id: str,
        entity_type: str,
        data: Dict[str, Any],
        source_role: str,
        version: int = None
    ) -> DataSnapshot:
        """Capture data snapshot for consistency checking"""
        try:
            # Create snapshot
            snapshot = DataSnapshot(
                snapshot_id=str(uuid.uuid4()),
                entity_id=entity_id,
                entity_type=entity_type,
                data=data,
                version=version or 1,
                timestamp=datetime.now(timezone.utc),
                source_role=source_role,
                checksum=hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
                metadata={"capture_method": "manual"}
            )
            
            # Store snapshot
            if entity_id not in self.data_snapshots:
                self.data_snapshots[entity_id] = []
            
            self.data_snapshots[entity_id].append(snapshot)
            
            # Limit snapshots per entity
            if len(self.data_snapshots[entity_id]) > self.max_snapshots_per_entity:
                self.data_snapshots[entity_id] = self.data_snapshots[entity_id][-self.max_snapshots_per_entity:]
            
            # Cache snapshot
            await self.cache.set(
                f"snapshot:{snapshot.snapshot_id}",
                snapshot.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit snapshot event
            await self.event_bus.emit(
                "consistency.snapshot_captured",
                {
                    "snapshot_id": snapshot.snapshot_id,
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "source_role": source_role,
                    "version": snapshot.version
                }
            )
            
            self.logger.debug(f"Captured snapshot for entity {entity_id}")
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error capturing data snapshot: {str(e)}")
            raise
    
    async def check_consistency(
        self,
        rule_id: str = None,
        entity_ids: List[str] = None,
        scope: ConsistencyScope = None
    ) -> ConsistencyCheck:
        """Check data consistency"""
        try:
            check_start = datetime.now(timezone.utc)
            
            # Determine rules to check
            if rule_id:
                rules_to_check = [self.consistency_rules[rule_id]] if rule_id in self.consistency_rules else []
            else:
                rules_to_check = [
                    rule for rule in self.consistency_rules.values()
                    if rule.enabled and (not scope or rule.scope == scope)
                ]
            
            # Determine entities to check
            if entity_ids:
                entities_to_check = entity_ids
            else:
                entities_to_check = list(self.data_snapshots.keys())
            
            # Execute consistency checks
            all_violations = []
            total_entities_checked = 0
            
            for rule in rules_to_check:
                rule_violations = await self._execute_consistency_rule(rule, entities_to_check)
                all_violations.extend(rule_violations)
                total_entities_checked += len([
                    eid for eid in entities_to_check
                    if any(eid.startswith(entity) for entity in rule.data_entities)
                ])
            
            # Create consistency check record
            check = ConsistencyCheck(
                check_id=str(uuid.uuid4()),
                rule_id=rule_id or "multiple",
                check_type="manual" if rule_id else "comprehensive",
                scope=scope or ConsistencyScope.GLOBAL,
                start_time=check_start,
                end_time=datetime.now(timezone.utc),
                entities_checked=total_entities_checked,
                violations_found=len(all_violations),
                violations=all_violations,
                success=len(all_violations) == 0,
                duration=(datetime.now(timezone.utc) - check_start).total_seconds(),
                metadata={
                    "rules_checked": len(rules_to_check),
                    "entities_scope": len(entities_to_check)
                }
            )
            
            # Store check
            self.consistency_checks[check.check_id] = check
            
            # Store violations
            for violation in all_violations:
                self.violations[violation.violation_id] = violation
            
            # Emit consistency check event
            await self.event_bus.emit(
                "consistency.check_completed",
                {
                    "check_id": check.check_id,
                    "violations_found": len(all_violations),
                    "entities_checked": total_entities_checked,
                    "success": check.success
                }
            )
            
            self.logger.info(f"Consistency check completed: {len(all_violations)} violations found")
            
            return check
            
        except Exception as e:
            self.logger.error(f"Error checking consistency: {str(e)}")
            raise
    
    async def resolve_violation(
        self,
        violation_id: str,
        resolution_strategy: ResolutionStrategy = None,
        manual_resolution: Dict[str, Any] = None
    ) -> bool:
        """Resolve a consistency violation"""
        try:
            if violation_id not in self.violations:
                raise ValueError(f"Violation not found: {violation_id}")
            
            violation = self.violations[violation_id]
            
            # Determine resolution strategy
            strategy = resolution_strategy or violation.resolution_strategy
            if not strategy:
                strategy = ResolutionStrategy.MANUAL
            
            # Execute resolution
            success = False
            
            if strategy == ResolutionStrategy.AUTOMATIC:
                success = await self._auto_resolve_violation(violation)
            elif strategy == ResolutionStrategy.MANUAL:
                success = await self._manual_resolve_violation(violation, manual_resolution)
            elif strategy == ResolutionStrategy.LAST_WRITE_WINS:
                success = await self._last_write_wins_resolution(violation)
            elif strategy == ResolutionStrategy.FIRST_WRITE_WINS:
                success = await self._first_write_wins_resolution(violation)
            elif strategy == ResolutionStrategy.MERGE:
                success = await self._merge_resolution(violation)
            elif strategy == ResolutionStrategy.ROLLBACK:
                success = await self._rollback_resolution(violation)
            elif strategy == ResolutionStrategy.COMPENSATE:
                success = await self._compensate_resolution(violation)
            
            # Update violation if resolved
            if success:
                violation.resolved_at = datetime.now(timezone.utc)
                violation.metadata = violation.metadata or {}
                violation.metadata["resolution_strategy"] = strategy
                violation.metadata["resolved_by"] = "consistency_manager"
                
                # Emit resolution event
                await self.event_bus.emit(
                    "consistency.violation_resolved",
                    {
                        "violation_id": violation_id,
                        "resolution_strategy": strategy,
                        "resolved_at": violation.resolved_at.isoformat()
                    }
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error resolving violation: {str(e)}")
            return False
    
    async def get_consistency_status(
        self,
        entity_id: str = None,
        scope: ConsistencyScope = None
    ) -> Dict[str, Any]:
        """Get consistency status"""
        try:
            # Filter violations
            filtered_violations = list(self.violations.values())
            
            if entity_id:
                filtered_violations = [
                    v for v in filtered_violations
                    if entity_id in v.affected_entities
                ]
            
            if scope:
                filtered_violations = [
                    v for v in filtered_violations
                    if self.consistency_rules.get(v.rule_id, {}).get("scope") == scope
                ]
            
            # Calculate status
            unresolved_violations = [v for v in filtered_violations if not v.resolved_at]
            critical_violations = [v for v in unresolved_violations if v.severity == ViolationSeverity.CRITICAL]
            
            # Get recent checks
            recent_checks = [
                check for check in self.consistency_checks.values()
                if (datetime.now(timezone.utc) - check.start_time).total_seconds() < 3600  # Last hour
            ]
            
            return {
                "overall_status": "healthy" if not critical_violations else "critical",
                "total_violations": len(filtered_violations),
                "unresolved_violations": len(unresolved_violations),
                "critical_violations": len(critical_violations),
                "violations_by_severity": {
                    severity.value: len([v for v in filtered_violations if v.severity == severity])
                    for severity in ViolationSeverity
                },
                "recent_checks": len(recent_checks),
                "successful_checks": len([c for c in recent_checks if c.success]),
                "entities_monitored": len(self.data_snapshots),
                "active_rules": len([r for r in self.consistency_rules.values() if r.enabled])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting consistency status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def generate_consistency_report(
        self,
        scope: ConsistencyScope = ConsistencyScope.GLOBAL,
        time_range: Tuple[datetime, datetime] = None
    ) -> ConsistencyReport:
        """Generate comprehensive consistency report"""
        try:
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                time_range = (start_time, end_time)
            
            # Filter data by time range and scope
            time_filtered_violations = [
                v for v in self.violations.values()
                if time_range[0] <= v.detected_at <= time_range[1]
            ]
            
            scope_filtered_violations = [
                v for v in time_filtered_violations
                if self.consistency_rules.get(v.rule_id, {}).get("scope") == scope or scope == ConsistencyScope.GLOBAL
            ]
            
            time_filtered_checks = [
                c for c in self.consistency_checks.values()
                if time_range[0] <= c.start_time <= time_range[1]
            ]
            
            # Count violations by type and severity
            violations_by_type = {}
            for violation_type in ViolationType:
                violations_by_type[violation_type] = len([
                    v for v in scope_filtered_violations if v.violation_type == violation_type
                ])
            
            violations_by_severity = {}
            for severity in ViolationSeverity:
                violations_by_severity[severity] = len([
                    v for v in scope_filtered_violations if v.severity == severity
                ])
            
            # Resolution summary
            resolved_violations = [v for v in scope_filtered_violations if v.resolved_at]
            resolution_summary = {
                "total_violations": len(scope_filtered_violations),
                "resolved_violations": len(resolved_violations),
                "resolution_rate": (len(resolved_violations) / len(scope_filtered_violations)) * 100 if scope_filtered_violations else 0,
                "avg_resolution_time": self._calculate_avg_resolution_time(resolved_violations)
            }
            
            # Generate recommendations
            recommendations = await self._generate_consistency_recommendations(
                scope_filtered_violations,
                time_filtered_checks
            )
            
            # Create report
            report = ConsistencyReport(
                report_id=str(uuid.uuid4()),
                generation_time=datetime.now(timezone.utc),
                scope=scope,
                time_range=time_range,
                total_checks=len(time_filtered_checks),
                total_violations=len(scope_filtered_violations),
                violations_by_type=violations_by_type,
                violations_by_severity=violations_by_severity,
                resolution_summary=resolution_summary,
                recommendations=recommendations,
                metadata={
                    "entities_analyzed": len(self.data_snapshots),
                    "rules_evaluated": len(self.consistency_rules)
                }
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating consistency report: {str(e)}")
            raise
    
    async def _execute_consistency_rule(
        self,
        rule: ConsistencyRule,
        entity_ids: List[str]
    ) -> List[ConsistencyViolation]:
        """Execute a specific consistency rule"""
        try:
            violations = []
            
            # Filter entities relevant to this rule
            relevant_entities = [
                eid for eid in entity_ids
                if any(eid.startswith(entity) or entity in eid for entity in rule.data_entities)
            ]
            
            for entity_id in relevant_entities:
                if entity_id not in self.data_snapshots:
                    continue
                
                snapshots = self.data_snapshots[entity_id]
                if len(snapshots) < 2:
                    continue  # Need at least 2 snapshots to check consistency
                
                # Execute validation logic
                rule_violations = await self._validate_entity_consistency(rule, entity_id, snapshots)
                violations.extend(rule_violations)
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error executing consistency rule {rule.rule_id}: {str(e)}")
            return []
    
    async def _validate_entity_consistency(
        self,
        rule: ConsistencyRule,
        entity_id: str,
        snapshots: List[DataSnapshot]
    ) -> List[ConsistencyViolation]:
        """Validate consistency for a specific entity"""
        try:
            violations = []
            
            # Sort snapshots by timestamp
            sorted_snapshots = sorted(snapshots, key=lambda s: s.timestamp)
            
            # Apply validation logic based on rule
            if rule.validation_logic == "checksum_validation":
                violations.extend(await self._validate_checksum_consistency(rule, entity_id, sorted_snapshots))
            elif rule.validation_logic == "version_validation":
                violations.extend(await self._validate_version_consistency(rule, entity_id, sorted_snapshots))
            elif rule.validation_logic == "referential_validation":
                violations.extend(await self._validate_referential_consistency(rule, entity_id, sorted_snapshots))
            elif rule.validation_logic == "business_rule_validation":
                violations.extend(await self._validate_business_rule_consistency(rule, entity_id, sorted_snapshots))
            elif rule.validation_logic == "session_validation":
                violations.extend(await self._validate_session_consistency(rule, entity_id, sorted_snapshots))
            elif rule.validation_logic == "temporal_validation":
                violations.extend(await self._validate_temporal_consistency(rule, entity_id, sorted_snapshots))
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error validating entity consistency: {str(e)}")
            return []
    
    async def _validate_checksum_consistency(
        self,
        rule: ConsistencyRule,
        entity_id: str,
        snapshots: List[DataSnapshot]
    ) -> List[ConsistencyViolation]:
        """Validate checksum consistency"""
        try:
            violations = []
            
            # Group snapshots by source role
            role_snapshots = {}
            for snapshot in snapshots:
                if snapshot.source_role not in role_snapshots:
                    role_snapshots[snapshot.source_role] = []
                role_snapshots[snapshot.source_role].append(snapshot)
            
            # Check if different roles have different data for same version
            if len(role_snapshots) > 1:
                for version in set(s.version for s in snapshots):
                    version_snapshots = [s for s in snapshots if s.version == version]
                    
                    if len(version_snapshots) > 1:
                        checksums = set(s.checksum for s in version_snapshots)
                        
                        if len(checksums) > 1:
                            violation = ConsistencyViolation(
                                violation_id=str(uuid.uuid4()),
                                rule_id=rule.rule_id,
                                violation_type=ViolationType.DATA_MISMATCH,
                                severity=ViolationSeverity.HIGH,
                                affected_entities=[entity_id],
                                description=f"Data mismatch detected for entity {entity_id} version {version}",
                                detected_at=datetime.now(timezone.utc),
                                source_snapshots=version_snapshots,
                                expected_state={"consistent_checksum": True},
                                actual_state={"checksums": list(checksums)},
                                auto_resolvable=rule.auto_resolve,
                                resolution_strategy=rule.resolution_strategy
                            )
                            violations.append(violation)
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error validating checksum consistency: {str(e)}")
            return []
    
    async def _validate_version_consistency(
        self,
        rule: ConsistencyRule,
        entity_id: str,
        snapshots: List[DataSnapshot]
    ) -> List[ConsistencyViolation]:
        """Validate version consistency"""
        try:
            violations = []
            
            # Check for version ordering violations
            for i in range(1, len(snapshots)):
                current = snapshots[i]
                previous = snapshots[i-1]
                
                # Version should be monotonically increasing
                if current.version < previous.version:
                    violation = ConsistencyViolation(
                        violation_id=str(uuid.uuid4()),
                        rule_id=rule.rule_id,
                        violation_type=ViolationType.VERSION_CONFLICT,
                        severity=ViolationSeverity.MEDIUM,
                        affected_entities=[entity_id],
                        description=f"Version ordering violation for entity {entity_id}",
                        detected_at=datetime.now(timezone.utc),
                        source_snapshots=[previous, current],
                        expected_state={"version_order": "monotonic_increasing"},
                        actual_state={"previous_version": previous.version, "current_version": current.version},
                        auto_resolvable=rule.auto_resolve,
                        resolution_strategy=rule.resolution_strategy
                    )
                    violations.append(violation)
                
                # Same version from different roles at different times
                if (current.version == previous.version and 
                    current.source_role != previous.source_role and
                    current.timestamp != previous.timestamp):
                    
                    violation = ConsistencyViolation(
                        violation_id=str(uuid.uuid4()),
                        rule_id=rule.rule_id,
                        violation_type=ViolationType.VERSION_CONFLICT,
                        severity=ViolationSeverity.HIGH,
                        affected_entities=[entity_id],
                        description=f"Concurrent version conflict for entity {entity_id}",
                        detected_at=datetime.now(timezone.utc),
                        source_snapshots=[previous, current],
                        expected_state={"unique_version_per_role": True},
                        actual_state={"conflicting_roles": [previous.source_role, current.source_role]},
                        auto_resolvable=rule.auto_resolve,
                        resolution_strategy=rule.resolution_strategy
                    )
                    violations.append(violation)
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error validating version consistency: {str(e)}")
            return []
    
    async def _validate_referential_consistency(
        self,
        rule: ConsistencyRule,
        entity_id: str,
        snapshots: List[DataSnapshot]
    ) -> List[ConsistencyViolation]:
        """Validate referential consistency"""
        try:
            violations = []
            
            # Check for broken references
            for snapshot in snapshots:
                # Look for reference fields in data
                for key, value in snapshot.data.items():
                    if key.endswith("_id") or key.endswith("_ref"):
                        # Check if referenced entity exists
                        if value and not await self._entity_exists(value):
                            violation = ConsistencyViolation(
                                violation_id=str(uuid.uuid4()),
                                rule_id=rule.rule_id,
                                violation_type=ViolationType.REFERENTIAL_INTEGRITY,
                                severity=ViolationSeverity.HIGH,
                                affected_entities=[entity_id, value],
                                description=f"Broken reference: {key} -> {value}",
                                detected_at=datetime.now(timezone.utc),
                                source_snapshots=[snapshot],
                                expected_state={"reference_exists": True},
                                actual_state={"referenced_entity": value, "exists": False},
                                auto_resolvable=False,
                                resolution_strategy=ResolutionStrategy.MANUAL
                            )
                            violations.append(violation)
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error validating referential consistency: {str(e)}")
            return []
    
    async def _validate_business_rule_consistency(
        self,
        rule: ConsistencyRule,
        entity_id: str,
        snapshots: List[DataSnapshot]
    ) -> List[ConsistencyViolation]:
        """Validate business rule consistency"""
        try:
            violations = []
            
            # Example business rule validation
            for snapshot in snapshots:
                # Check invoice amount consistency
                if snapshot.entity_type == "invoice":
                    amount = snapshot.data.get("amount", 0)
                    tax = snapshot.data.get("tax", 0)
                    total = snapshot.data.get("total", 0)
                    
                    if abs(total - (amount + tax)) > 0.01:  # Allow small rounding differences
                        violation = ConsistencyViolation(
                            violation_id=str(uuid.uuid4()),
                            rule_id=rule.rule_id,
                            violation_type=ViolationType.BUSINESS_RULE,
                            severity=ViolationSeverity.HIGH,
                            affected_entities=[entity_id],
                            description=f"Invoice calculation inconsistency: total != amount + tax",
                            detected_at=datetime.now(timezone.utc),
                            source_snapshots=[snapshot],
                            expected_state={"total": amount + tax},
                            actual_state={"amount": amount, "tax": tax, "total": total},
                            auto_resolvable=rule.auto_resolve,
                            resolution_strategy=rule.resolution_strategy
                        )
                        violations.append(violation)
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error validating business rule consistency: {str(e)}")
            return []
    
    async def _validate_session_consistency(
        self,
        rule: ConsistencyRule,
        entity_id: str,
        snapshots: List[DataSnapshot]
    ) -> List[ConsistencyViolation]:
        """Validate session consistency"""
        try:
            violations = []
            
            # Check session data consistency
            for snapshot in snapshots:
                if snapshot.entity_type == "user_session":
                    session_data = snapshot.data
                    
                    # Check session expiry
                    expires_at = session_data.get("expires_at")
                    if expires_at:
                        expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        if expiry_time < datetime.now(timezone.utc):
                            violation = ConsistencyViolation(
                                violation_id=str(uuid.uuid4()),
                                rule_id=rule.rule_id,
                                violation_type=ViolationType.BUSINESS_RULE,
                                severity=ViolationSeverity.MEDIUM,
                                affected_entities=[entity_id],
                                description=f"Expired session still active: {entity_id}",
                                detected_at=datetime.now(timezone.utc),
                                source_snapshots=[snapshot],
                                expected_state={"session_active": False},
                                actual_state={"expires_at": expires_at, "current_time": datetime.now(timezone.utc).isoformat()},
                                auto_resolvable=rule.auto_resolve,
                                resolution_strategy=rule.resolution_strategy
                            )
                            violations.append(violation)
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error validating session consistency: {str(e)}")
            return []
    
    async def _validate_temporal_consistency(
        self,
        rule: ConsistencyRule,
        entity_id: str,
        snapshots: List[DataSnapshot]
    ) -> List[ConsistencyViolation]:
        """Validate temporal consistency"""
        try:
            violations = []
            
            # Check timestamp ordering
            for i in range(1, len(snapshots)):
                current = snapshots[i]
                previous = snapshots[i-1]
                
                # Timestamps should be monotonically increasing
                if current.timestamp < previous.timestamp:
                    violation = ConsistencyViolation(
                        violation_id=str(uuid.uuid4()),
                        rule_id=rule.rule_id,
                        violation_type=ViolationType.TIMESTAMP_INCONSISTENCY,
                        severity=ViolationSeverity.MEDIUM,
                        affected_entities=[entity_id],
                        description=f"Timestamp ordering violation for entity {entity_id}",
                        detected_at=datetime.now(timezone.utc),
                        source_snapshots=[previous, current],
                        expected_state={"timestamp_order": "monotonic_increasing"},
                        actual_state={
                            "previous_timestamp": previous.timestamp.isoformat(),
                            "current_timestamp": current.timestamp.isoformat()
                        },
                        auto_resolvable=rule.auto_resolve,
                        resolution_strategy=rule.resolution_strategy
                    )
                    violations.append(violation)
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error validating temporal consistency: {str(e)}")
            return []
    
    async def _entity_exists(self, entity_id: str) -> bool:
        """Check if an entity exists"""
        try:
            # Check in snapshots
            return entity_id in self.data_snapshots
            
        except Exception as e:
            self.logger.error(f"Error checking entity existence: {str(e)}")
            return False
    
    async def _auto_resolve_violation(self, violation: ConsistencyViolation) -> bool:
        """Automatically resolve a violation"""
        try:
            if not violation.auto_resolvable:
                return False
            
            strategy = violation.resolution_strategy
            if not strategy:
                return False
            
            if strategy == ResolutionStrategy.LAST_WRITE_WINS:
                return await self._last_write_wins_resolution(violation)
            elif strategy == ResolutionStrategy.FIRST_WRITE_WINS:
                return await self._first_write_wins_resolution(violation)
            elif strategy == ResolutionStrategy.MERGE:
                return await self._merge_resolution(violation)
            elif strategy == ResolutionStrategy.ROLLBACK:
                return await self._rollback_resolution(violation)
            elif strategy == ResolutionStrategy.COMPENSATE:
                return await self._compensate_resolution(violation)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error auto resolving violation: {str(e)}")
            return False
    
    async def _manual_resolve_violation(
        self,
        violation: ConsistencyViolation,
        manual_resolution: Dict[str, Any]
    ) -> bool:
        """Manually resolve a violation"""
        try:
            if not manual_resolution:
                return False
            
            # Apply manual resolution
            resolution_action = manual_resolution.get("action")
            
            if resolution_action == "accept_latest":
                return await self._last_write_wins_resolution(violation)
            elif resolution_action == "accept_oldest":
                return await self._first_write_wins_resolution(violation)
            elif resolution_action == "merge_data":
                merged_data = manual_resolution.get("merged_data")
                if merged_data:
                    # Create new snapshot with merged data
                    entity_id = violation.affected_entities[0]
                    await self.capture_data_snapshot(
                        entity_id,
                        violation.source_snapshots[0].entity_type,
                        merged_data,
                        "consistency_manager"
                    )
                    return True
            elif resolution_action == "ignore":
                # Mark as resolved without action
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error manually resolving violation: {str(e)}")
            return False
    
    async def _last_write_wins_resolution(self, violation: ConsistencyViolation) -> bool:
        """Resolve using last write wins strategy"""
        try:
            if not violation.source_snapshots:
                return False
            
            # Find latest snapshot
            latest_snapshot = max(violation.source_snapshots, key=lambda s: s.timestamp)
            
            # Update all other snapshots to match latest
            for entity_id in violation.affected_entities:
                if entity_id in self.data_snapshots:
                    # Create new consistent snapshot
                    await self.capture_data_snapshot(
                        entity_id,
                        latest_snapshot.entity_type,
                        latest_snapshot.data,
                        "consistency_manager",
                        latest_snapshot.version + 1
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in last write wins resolution: {str(e)}")
            return False
    
    async def _first_write_wins_resolution(self, violation: ConsistencyViolation) -> bool:
        """Resolve using first write wins strategy"""
        try:
            if not violation.source_snapshots:
                return False
            
            # Find earliest snapshot
            earliest_snapshot = min(violation.source_snapshots, key=lambda s: s.timestamp)
            
            # Update all other snapshots to match earliest
            for entity_id in violation.affected_entities:
                if entity_id in self.data_snapshots:
                    # Create new consistent snapshot
                    await self.capture_data_snapshot(
                        entity_id,
                        earliest_snapshot.entity_type,
                        earliest_snapshot.data,
                        "consistency_manager",
                        earliest_snapshot.version + 1
                    )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in first write wins resolution: {str(e)}")
            return False
    
    async def _merge_resolution(self, violation: ConsistencyViolation) -> bool:
        """Resolve using merge strategy"""
        try:
            if len(violation.source_snapshots) < 2:
                return False
            
            # Simple merge strategy - combine non-conflicting fields
            merged_data = {}
            
            # Start with first snapshot
            base_snapshot = violation.source_snapshots[0]
            merged_data.update(base_snapshot.data)
            
            # Merge other snapshots
            for snapshot in violation.source_snapshots[1:]:
                for key, value in snapshot.data.items():
                    if key not in merged_data:
                        merged_data[key] = value
                    elif merged_data[key] != value:
                        # Conflict - use latest timestamp
                        if snapshot.timestamp > base_snapshot.timestamp:
                            merged_data[key] = value
            
            # Create merged snapshot
            entity_id = violation.affected_entities[0]
            await self.capture_data_snapshot(
                entity_id,
                base_snapshot.entity_type,
                merged_data,
                "consistency_manager",
                max(s.version for s in violation.source_snapshots) + 1
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in merge resolution: {str(e)}")
            return False
    
    async def _rollback_resolution(self, violation: ConsistencyViolation) -> bool:
        """Resolve using rollback strategy"""
        try:
            # Find last known good state
            for entity_id in violation.affected_entities:
                if entity_id in self.data_snapshots:
                    snapshots = self.data_snapshots[entity_id]
                    
                    # Find snapshot before violation
                    for snapshot in reversed(snapshots):
                        if snapshot.timestamp < violation.detected_at:
                            # Rollback to this snapshot
                            await self.capture_data_snapshot(
                                entity_id,
                                snapshot.entity_type,
                                snapshot.data,
                                "consistency_manager",
                                snapshot.version + 1
                            )
                            break
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in rollback resolution: {str(e)}")
            return False
    
    async def _compensate_resolution(self, violation: ConsistencyViolation) -> bool:
        """Resolve using compensating transaction strategy"""
        try:
            # Create compensating actions
            compensation_actions = []
            
            if violation.violation_type == ViolationType.BUSINESS_RULE:
                # Create compensation for business rule violations
                for snapshot in violation.source_snapshots:
                    if snapshot.entity_type == "invoice":
                        # Recalculate totals
                        amount = snapshot.data.get("amount", 0)
                        tax = snapshot.data.get("tax", 0)
                        corrected_data = snapshot.data.copy()
                        corrected_data["total"] = amount + tax
                        
                        await self.capture_data_snapshot(
                            snapshot.entity_id,
                            snapshot.entity_type,
                            corrected_data,
                            "consistency_manager",
                            snapshot.version + 1
                        )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in compensate resolution: {str(e)}")
            return False
    
    def _calculate_avg_resolution_time(self, resolved_violations: List[ConsistencyViolation]) -> float:
        """Calculate average resolution time"""
        try:
            if not resolved_violations:
                return 0.0
            
            resolution_times = []
            for violation in resolved_violations:
                if violation.resolved_at:
                    resolution_time = (violation.resolved_at - violation.detected_at).total_seconds()
                    resolution_times.append(resolution_time)
            
            return sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating average resolution time: {str(e)}")
            return 0.0
    
    async def _generate_consistency_recommendations(
        self,
        violations: List[ConsistencyViolation],
        checks: List[ConsistencyCheck]
    ) -> List[str]:
        """Generate consistency recommendations"""
        try:
            recommendations = []
            
            # High-frequency violations
            violation_counts = {}
            for violation in violations:
                violation_counts[violation.violation_type] = violation_counts.get(violation.violation_type, 0) + 1
            
            for violation_type, count in violation_counts.items():
                if count > 10:
                    recommendations.append(f"High frequency of {violation_type} violations detected - review processes")
            
            # Critical violations
            critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
            if critical_violations:
                recommendations.append(f"Address {len(critical_violations)} critical violations immediately")
            
            # Resolution efficiency
            auto_resolvable = [v for v in violations if v.auto_resolvable]
            if len(auto_resolvable) < len(violations) * 0.5:
                recommendations.append("Consider implementing more automated resolution strategies")
            
            # Check frequency
            if len(checks) < 5:  # Less than 5 checks in time period
                recommendations.append("Increase consistency check frequency for better monitoring")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    async def _consistency_checker(self):
        """Background consistency checker"""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                
                # Run consistency checks for all enabled rules
                await self.check_consistency()
                
            except Exception as e:
                self.logger.error(f"Error in consistency checker: {str(e)}")
    
    async def _violation_resolver(self):
        """Background violation resolver"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Find unresolved auto-resolvable violations
                unresolved_violations = [
                    v for v in self.violations.values()
                    if not v.resolved_at and v.auto_resolvable
                ]
                
                for violation in unresolved_violations:
                    # Check if violation is old enough to auto-resolve
                    age = (datetime.now(timezone.utc) - violation.detected_at).total_seconds()
                    if age > 300:  # 5 minutes old
                        await self.resolve_violation(violation.violation_id)
                
            except Exception as e:
                self.logger.error(f"Error in violation resolver: {str(e)}")
    
    async def _snapshot_cleaner(self):
        """Background snapshot cleaner"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.snapshot_retention_hours)
                
                # Clean old snapshots
                for entity_id, snapshots in self.data_snapshots.items():
                    # Keep only recent snapshots
                    recent_snapshots = [
                        s for s in snapshots
                        if s.timestamp >= cutoff_time
                    ]
                    
                    # Always keep at least one snapshot
                    if recent_snapshots:
                        self.data_snapshots[entity_id] = recent_snapshots
                    elif snapshots:
                        self.data_snapshots[entity_id] = snapshots[-1:]
                
                self.logger.debug("Cleaned up old snapshots")
                
            except Exception as e:
                self.logger.error(f"Error in snapshot cleaner: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "data.changed",
                self._handle_data_change
            )
            
            await self.event_bus.subscribe(
                "consistency.violation_detected",
                self._handle_violation_detected
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_data_change(self, event_data: Dict[str, Any]):
        """Handle data change event"""
        try:
            entity_id = event_data.get("entity_id")
            entity_type = event_data.get("entity_type")
            data = event_data.get("data")
            source_role = event_data.get("source_role")
            version = event_data.get("version")
            
            if entity_id and data:
                await self.capture_data_snapshot(entity_id, entity_type, data, source_role, version)
            
        except Exception as e:
            self.logger.error(f"Error handling data change: {str(e)}")
    
    async def _handle_violation_detected(self, event_data: Dict[str, Any]):
        """Handle violation detected event"""
        try:
            violation_id = event_data.get("violation_id")
            severity = event_data.get("severity")
            
            # Send notifications for critical violations
            if severity == ViolationSeverity.CRITICAL:
                await self.notification_service.send_notification(
                    type="critical_consistency_violation",
                    data=event_data
                )
            
        except Exception as e:
            self.logger.error(f"Error handling violation detected: {str(e)}")
    
    async def get_consistency_summary(self) -> Dict[str, Any]:
        """Get consistency management summary"""
        try:
            return {
                "total_rules": len(self.consistency_rules),
                "enabled_rules": len([r for r in self.consistency_rules.values() if r.enabled]),
                "total_snapshots": sum(len(snapshots) for snapshots in self.data_snapshots.values()),
                "entities_monitored": len(self.data_snapshots),
                "total_violations": len(self.violations),
                "unresolved_violations": len([v for v in self.violations.values() if not v.resolved_at]),
                "total_checks": len(self.consistency_checks),
                "successful_checks": len([c for c in self.consistency_checks.values() if c.success]),
                "is_initialized": self.is_initialized
            }
            
        except Exception as e:
            self.logger.error(f"Error getting consistency summary: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "consistency_manager",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_rules": len(self.consistency_rules),
                    "total_violations": len(self.violations),
                    "entities_monitored": len(self.data_snapshots)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "consistency_manager",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Consistency manager service cleanup initiated")
        
        try:
            # Clear all state
            self.data_snapshots.clear()
            self.violations.clear()
            self.consistency_checks.clear()
            self.consistency_sessions.clear()
            
            # Cleanup dependencies
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Consistency manager service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_consistency_manager() -> ConsistencyManager:
    """Create consistency manager service"""
    return ConsistencyManager()