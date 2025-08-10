"""
Feature Flag Manager Service

This service manages feature flags for gradual rollouts, A/B testing, and controlled
feature deployment across the TaxPoynt platform.
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import random
from pathlib import Path

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    ConfigurationError,
    ValidationError,
    SecurityError
)


class FlagStatus(Enum):
    """Feature flag status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    TESTING = "testing"


class FlagType(Enum):
    """Feature flag type"""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    MULTIVARIATE = "multivariate"
    KILLSWITCH = "killswitch"


class RolloutStrategy(Enum):
    """Rollout strategy"""
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    TARGETED = "targeted"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"


class TargetingRule(Enum):
    """Targeting rule types"""
    USER_ID = "user_id"
    TENANT_ID = "tenant_id"
    ENVIRONMENT = "environment"
    ROLE = "role"
    SERVICE = "service"
    PERCENTAGE = "percentage"
    CUSTOM = "custom"


@dataclass
class FeatureFlag:
    """Feature flag definition"""
    key: str
    name: str
    description: str
    flag_type: FlagType
    status: FlagStatus
    default_value: Any
    variations: Dict[str, Any] = field(default_factory=dict)
    targeting_rules: List[Dict[str, Any]] = field(default_factory=list)
    rollout_strategy: RolloutStrategy = RolloutStrategy.IMMEDIATE
    rollout_percentage: float = 0.0
    environments: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_by: str = "system"
    version: int = 1
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    kill_switch: bool = False
    metrics_enabled: bool = True
    
    def __post_init__(self):
        """Validate flag after initialization"""
        if self.flag_type == FlagType.BOOLEAN and self.default_value not in [True, False]:
            raise ValidationError("Boolean flags must have boolean default value")
        if self.flag_type == FlagType.PERCENTAGE and not 0 <= self.rollout_percentage <= 100:
            raise ValidationError("Percentage must be between 0 and 100")


@dataclass
class FlagEvaluation:
    """Feature flag evaluation result"""
    flag_key: str
    value: Any
    variation: Optional[str] = None
    reason: str = "default"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    environment: Optional[str] = None
    service: Optional[str] = None


@dataclass
class FlagContext:
    """Context for flag evaluation"""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    environment: Optional[str] = None
    role: Optional[str] = None
    service: Optional[str] = None
    custom_attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlagMetrics:
    """Feature flag metrics"""
    flag_key: str
    evaluations: int = 0
    true_evaluations: int = 0
    false_evaluations: int = 0
    variation_counts: Dict[str, int] = field(default_factory=dict)
    error_count: int = 0
    last_evaluation: Optional[datetime] = None
    first_evaluation: Optional[datetime] = None


class FeatureFlagManager(BaseService):
    """
    Feature Flag Manager Service
    
    Manages feature flags for gradual rollouts, A/B testing, and controlled
    feature deployment across the TaxPoynt platform.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Flag storage
        self.flags: Dict[str, FeatureFlag] = {}
        self.flag_cache: Dict[str, Any] = {}
        self.cache_ttl: timedelta = timedelta(minutes=1)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Evaluation tracking
        self.evaluations: List[FlagEvaluation] = []
        self.metrics: Dict[str, FlagMetrics] = {}
        
        # Rollout management
        self.rollout_schedules: Dict[str, asyncio.Task] = {}
        self.rollout_queue: asyncio.Queue = asyncio.Queue()
        
        # Targeting
        self.targeting_engines: Dict[str, Callable] = {}
        self.segment_cache: Dict[str, Set[str]] = {}
        
        # Event listeners
        self.flag_listeners: Dict[str, List[Callable]] = {}
        
        # Performance
        self.evaluation_cache: Dict[str, Dict[str, Any]] = {}
        self.evaluation_cache_ttl: timedelta = timedelta(seconds=30)
        
        # System metrics
        self.system_metrics = {
            'flags_managed': 0,
            'evaluations_performed': 0,
            'rollouts_executed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'targeting_evaluations': 0
        }
    
    async def initialize(self) -> None:
        """Initialize feature flag manager"""
        try:
            self.logger.info("Initializing FeatureFlagManager")
            
            # Load default flags
            await self._load_default_flags()
            
            # Initialize targeting engines
            await self._initialize_targeting_engines()
            
            # Start rollout worker
            await self._start_rollout_worker()
            
            self.logger.info("FeatureFlagManager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize FeatureFlagManager: {str(e)}")
            raise ConfigurationError(f"Initialization failed: {str(e)}")
    
    async def create_flag(
        self,
        key: str,
        name: str,
        description: str,
        flag_type: FlagType,
        default_value: Any,
        variations: Optional[Dict[str, Any]] = None,
        targeting_rules: Optional[List[Dict[str, Any]]] = None,
        rollout_strategy: RolloutStrategy = RolloutStrategy.IMMEDIATE,
        rollout_percentage: float = 0.0,
        environments: Optional[List[str]] = None,
        created_by: str = "system"
    ) -> FeatureFlag:
        """Create a new feature flag"""
        try:
            # Validate flag doesn't exist
            if key in self.flags:
                raise ValidationError(f"Flag {key} already exists")
            
            # Create flag
            flag = FeatureFlag(
                key=key,
                name=name,
                description=description,
                flag_type=flag_type,
                status=FlagStatus.INACTIVE,
                default_value=default_value,
                variations=variations or {},
                targeting_rules=targeting_rules or [],
                rollout_strategy=rollout_strategy,
                rollout_percentage=rollout_percentage,
                environments=environments or [],
                created_by=created_by
            )
            
            # Store flag
            self.flags[key] = flag
            
            # Initialize metrics
            self.metrics[key] = FlagMetrics(flag_key=key)
            
            # Clear cache
            await self._invalidate_cache(key)
            
            self.system_metrics['flags_managed'] += 1
            self.logger.info(f"Feature flag created: {key}")
            
            return flag
            
        except Exception as e:
            self.logger.error(f"Failed to create flag {key}: {str(e)}")
            raise ConfigurationError(f"Flag creation failed: {str(e)}")
    
    async def update_flag(
        self,
        key: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[FlagStatus] = None,
        default_value: Optional[Any] = None,
        variations: Optional[Dict[str, Any]] = None,
        targeting_rules: Optional[List[Dict[str, Any]]] = None,
        rollout_strategy: Optional[RolloutStrategy] = None,
        rollout_percentage: Optional[float] = None,
        updated_by: str = "system"
    ) -> FeatureFlag:
        """Update existing feature flag"""
        try:
            if key not in self.flags:
                raise ValidationError(f"Flag {key} not found")
            
            flag = self.flags[key]
            
            # Update fields
            if name is not None:
                flag.name = name
            if description is not None:
                flag.description = description
            if status is not None:
                flag.status = status
            if default_value is not None:
                flag.default_value = default_value
            if variations is not None:
                flag.variations = variations
            if targeting_rules is not None:
                flag.targeting_rules = targeting_rules
            if rollout_strategy is not None:
                flag.rollout_strategy = rollout_strategy
            if rollout_percentage is not None:
                flag.rollout_percentage = rollout_percentage
            
            flag.updated_at = datetime.utcnow()
            flag.updated_by = updated_by
            flag.version += 1
            
            # Clear cache
            await self._invalidate_cache(key)
            
            # Notify listeners
            await self._notify_flag_listeners(key, "updated")
            
            self.logger.info(f"Feature flag updated: {key}")
            return flag
            
        except Exception as e:
            self.logger.error(f"Failed to update flag {key}: {str(e)}")
            raise ConfigurationError(f"Flag update failed: {str(e)}")
    
    async def evaluate_flag(
        self,
        key: str,
        context: Optional[FlagContext] = None,
        use_cache: bool = True
    ) -> FlagEvaluation:
        """Evaluate feature flag for given context"""
        try:
            # Check cache first
            if use_cache:
                cached_result = await self._get_evaluation_from_cache(key, context)
                if cached_result:
                    return cached_result
            
            # Get flag
            if key not in self.flags:
                return FlagEvaluation(
                    flag_key=key,
                    value=False,
                    reason="flag_not_found"
                )
            
            flag = self.flags[key]
            
            # Check if flag is active
            if flag.status != FlagStatus.ACTIVE:
                return FlagEvaluation(
                    flag_key=key,
                    value=flag.default_value,
                    reason="flag_inactive"
                )
            
            # Check kill switch
            if flag.kill_switch:
                return FlagEvaluation(
                    flag_key=key,
                    value=False,
                    reason="kill_switch_active"
                )
            
            # Evaluate based on flag type
            evaluation = await self._evaluate_flag_by_type(flag, context)
            
            # Update metrics
            await self._update_flag_metrics(key, evaluation)
            
            # Cache result
            if use_cache:
                await self._cache_evaluation(key, context, evaluation)
            
            self.system_metrics['evaluations_performed'] += 1
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate flag {key}: {str(e)}")
            # Return safe default
            return FlagEvaluation(
                flag_key=key,
                value=False,
                reason=f"evaluation_error: {str(e)}"
            )
    
    async def is_enabled(
        self,
        key: str,
        context: Optional[FlagContext] = None,
        use_cache: bool = True
    ) -> bool:
        """Check if feature flag is enabled"""
        evaluation = await self.evaluate_flag(key, context, use_cache)
        return bool(evaluation.value)
    
    async def get_variation(
        self,
        key: str,
        context: Optional[FlagContext] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """Get feature flag variation"""
        evaluation = await self.evaluate_flag(key, context, use_cache)
        return evaluation.variation
    
    async def activate_flag(self, key: str, updated_by: str = "system") -> bool:
        """Activate feature flag"""
        try:
            await self.update_flag(
                key=key,
                status=FlagStatus.ACTIVE,
                updated_by=updated_by
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate flag {key}: {str(e)}")
            return False
    
    async def deactivate_flag(self, key: str, updated_by: str = "system") -> bool:
        """Deactivate feature flag"""
        try:
            await self.update_flag(
                key=key,
                status=FlagStatus.INACTIVE,
                updated_by=updated_by
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate flag {key}: {str(e)}")
            return False
    
    async def start_rollout(
        self,
        key: str,
        target_percentage: float,
        duration_minutes: int = 60,
        step_percentage: float = 10.0,
        updated_by: str = "system"
    ) -> bool:
        """Start gradual rollout of feature flag"""
        try:
            if key not in self.flags:
                raise ValidationError(f"Flag {key} not found")
            
            flag = self.flags[key]
            
            # Create rollout schedule
            rollout_task = asyncio.create_task(
                self._execute_rollout(
                    key, target_percentage, duration_minutes, step_percentage, updated_by
                )
            )
            
            self.rollout_schedules[key] = rollout_task
            
            self.logger.info(f"Rollout started for flag {key}: {target_percentage}% over {duration_minutes} minutes")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start rollout for flag {key}: {str(e)}")
            return False
    
    async def stop_rollout(self, key: str) -> bool:
        """Stop ongoing rollout"""
        try:
            if key in self.rollout_schedules:
                task = self.rollout_schedules[key]
                if not task.done():
                    task.cancel()
                del self.rollout_schedules[key]
                
                self.logger.info(f"Rollout stopped for flag {key}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to stop rollout for flag {key}: {str(e)}")
            return False
    
    async def enable_kill_switch(self, key: str, updated_by: str = "system") -> bool:
        """Enable kill switch for flag"""
        try:
            await self.update_flag(
                key=key,
                updated_by=updated_by
            )
            
            # Set kill switch
            if key in self.flags:
                self.flags[key].kill_switch = True
                self.flags[key].updated_at = datetime.utcnow()
                self.flags[key].updated_by = updated_by
            
            # Clear cache
            await self._invalidate_cache(key)
            
            self.logger.warning(f"Kill switch enabled for flag {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable kill switch for flag {key}: {str(e)}")
            return False
    
    async def disable_kill_switch(self, key: str, updated_by: str = "system") -> bool:
        """Disable kill switch for flag"""
        try:
            if key in self.flags:
                self.flags[key].kill_switch = False
                self.flags[key].updated_at = datetime.utcnow()
                self.flags[key].updated_by = updated_by
            
            # Clear cache
            await self._invalidate_cache(key)
            
            self.logger.info(f"Kill switch disabled for flag {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable kill switch for flag {key}: {str(e)}")
            return False
    
    async def get_flag_metrics(self, key: str) -> Optional[FlagMetrics]:
        """Get metrics for specific flag"""
        return self.metrics.get(key)
    
    async def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags"""
        return self.flags.copy()
    
    async def get_flags_by_environment(self, environment: str) -> Dict[str, FeatureFlag]:
        """Get flags for specific environment"""
        return {
            key: flag for key, flag in self.flags.items()
            if not flag.environments or environment in flag.environments
        }
    
    async def register_flag_listener(
        self,
        flag_key: str,
        listener: Callable[[str, str], None]
    ) -> None:
        """Register flag change listener"""
        if flag_key not in self.flag_listeners:
            self.flag_listeners[flag_key] = []
        
        self.flag_listeners[flag_key].append(listener)
        self.logger.info(f"Flag listener registered for {flag_key}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get feature flag manager health status"""
        try:
            return {
                'service': 'FeatureFlagManager',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.system_metrics,
                'flags': {
                    'total': len(self.flags),
                    'active': len([f for f in self.flags.values() if f.status == FlagStatus.ACTIVE]),
                    'inactive': len([f for f in self.flags.values() if f.status == FlagStatus.INACTIVE]),
                    'testing': len([f for f in self.flags.values() if f.status == FlagStatus.TESTING]),
                    'archived': len([f for f in self.flags.values() if f.status == FlagStatus.ARCHIVED])
                },
                'rollouts': {
                    'active': len(self.rollout_schedules),
                    'queue_size': self.rollout_queue.qsize()
                },
                'cache': {
                    'flag_cache_size': len(self.flag_cache),
                    'evaluation_cache_size': len(self.evaluation_cache)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                'service': 'FeatureFlagManager',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _load_default_flags(self) -> None:
        """Load default feature flags"""
        default_flags = [
            {
                'key': 'new_ui_enabled',
                'name': 'New UI Design',
                'description': 'Enable new user interface design',
                'flag_type': FlagType.BOOLEAN,
                'default_value': False
            },
            {
                'key': 'enhanced_logging',
                'name': 'Enhanced Logging',
                'description': 'Enable enhanced logging features',
                'flag_type': FlagType.BOOLEAN,
                'default_value': False
            },
            {
                'key': 'firs_integration_v2',
                'name': 'FIRS Integration V2',
                'description': 'Enable FIRS integration version 2',
                'flag_type': FlagType.BOOLEAN,
                'default_value': False
            }
        ]
        
        for flag_config in default_flags:
            if flag_config['key'] not in self.flags:
                await self.create_flag(**flag_config)
    
    async def _initialize_targeting_engines(self) -> None:
        """Initialize targeting engines"""
        self.targeting_engines = {
            'user_id': self._evaluate_user_id_targeting,
            'tenant_id': self._evaluate_tenant_id_targeting,
            'environment': self._evaluate_environment_targeting,
            'role': self._evaluate_role_targeting,
            'service': self._evaluate_service_targeting,
            'percentage': self._evaluate_percentage_targeting,
            'custom': self._evaluate_custom_targeting
        }
    
    async def _start_rollout_worker(self) -> None:
        """Start rollout worker"""
        async def rollout_worker():
            while True:
                try:
                    await asyncio.sleep(1)
                    # Process rollout queue if needed
                except Exception as e:
                    self.logger.error(f"Rollout worker error: {str(e)}")
                    await asyncio.sleep(5)
        
        asyncio.create_task(rollout_worker())
    
    async def _evaluate_flag_by_type(
        self,
        flag: FeatureFlag,
        context: Optional[FlagContext] = None
    ) -> FlagEvaluation:
        """Evaluate flag based on its type"""
        if flag.flag_type == FlagType.BOOLEAN:
            return await self._evaluate_boolean_flag(flag, context)
        elif flag.flag_type == FlagType.PERCENTAGE:
            return await self._evaluate_percentage_flag(flag, context)
        elif flag.flag_type == FlagType.MULTIVARIATE:
            return await self._evaluate_multivariate_flag(flag, context)
        elif flag.flag_type == FlagType.KILLSWITCH:
            return await self._evaluate_killswitch_flag(flag, context)
        else:
            return FlagEvaluation(
                flag_key=flag.key,
                value=flag.default_value,
                reason="unsupported_flag_type"
            )
    
    async def _evaluate_boolean_flag(
        self,
        flag: FeatureFlag,
        context: Optional[FlagContext] = None
    ) -> FlagEvaluation:
        """Evaluate boolean flag"""
        # Check targeting rules
        for rule in flag.targeting_rules:
            if await self._evaluate_targeting_rule(rule, context):
                return FlagEvaluation(
                    flag_key=flag.key,
                    value=rule.get('value', True),
                    reason="targeting_rule_matched"
                )
        
        # Check rollout percentage
        if flag.rollout_percentage > 0:
            if await self._evaluate_percentage_targeting({'percentage': flag.rollout_percentage}, context):
                return FlagEvaluation(
                    flag_key=flag.key,
                    value=True,
                    reason="rollout_percentage"
                )
        
        return FlagEvaluation(
            flag_key=flag.key,
            value=flag.default_value,
            reason="default_value"
        )
    
    async def _evaluate_percentage_flag(
        self,
        flag: FeatureFlag,
        context: Optional[FlagContext] = None
    ) -> FlagEvaluation:
        """Evaluate percentage flag"""
        # Similar to boolean but with percentage-based evaluation
        return await self._evaluate_boolean_flag(flag, context)
    
    async def _evaluate_multivariate_flag(
        self,
        flag: FeatureFlag,
        context: Optional[FlagContext] = None
    ) -> FlagEvaluation:
        """Evaluate multivariate flag"""
        # Check targeting rules for variations
        for rule in flag.targeting_rules:
            if await self._evaluate_targeting_rule(rule, context):
                variation = rule.get('variation', 'default')
                value = flag.variations.get(variation, flag.default_value)
                return FlagEvaluation(
                    flag_key=flag.key,
                    value=value,
                    variation=variation,
                    reason="targeting_rule_matched"
                )
        
        # Return default variation
        return FlagEvaluation(
            flag_key=flag.key,
            value=flag.default_value,
            variation="default",
            reason="default_variation"
        )
    
    async def _evaluate_killswitch_flag(
        self,
        flag: FeatureFlag,
        context: Optional[FlagContext] = None
    ) -> FlagEvaluation:
        """Evaluate killswitch flag"""
        return FlagEvaluation(
            flag_key=flag.key,
            value=not flag.kill_switch,
            reason="killswitch_evaluation"
        )
    
    async def _evaluate_targeting_rule(
        self,
        rule: Dict[str, Any],
        context: Optional[FlagContext] = None
    ) -> bool:
        """Evaluate targeting rule"""
        try:
            rule_type = rule.get('type')
            engine = self.targeting_engines.get(rule_type)
            
            if engine:
                return await engine(rule, context)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate targeting rule: {str(e)}")
            return False
    
    async def _evaluate_user_id_targeting(
        self,
        rule: Dict[str, Any],
        context: Optional[FlagContext] = None
    ) -> bool:
        """Evaluate user ID targeting"""
        if not context or not context.user_id:
            return False
        
        target_users = rule.get('values', [])
        return context.user_id in target_users
    
    async def _evaluate_tenant_id_targeting(
        self,
        rule: Dict[str, Any],
        context: Optional[FlagContext] = None
    ) -> bool:
        """Evaluate tenant ID targeting"""
        if not context or not context.tenant_id:
            return False
        
        target_tenants = rule.get('values', [])
        return context.tenant_id in target_tenants
    
    async def _evaluate_environment_targeting(
        self,
        rule: Dict[str, Any],
        context: Optional[FlagContext] = None
    ) -> bool:
        """Evaluate environment targeting"""
        if not context or not context.environment:
            return False
        
        target_environments = rule.get('values', [])
        return context.environment in target_environments
    
    async def _evaluate_role_targeting(
        self,
        rule: Dict[str, Any],
        context: Optional[FlagContext] = None
    ) -> bool:
        """Evaluate role targeting"""
        if not context or not context.role:
            return False
        
        target_roles = rule.get('values', [])
        return context.role in target_roles
    
    async def _evaluate_service_targeting(
        self,
        rule: Dict[str, Any],
        context: Optional[FlagContext] = None
    ) -> bool:
        """Evaluate service targeting"""
        if not context or not context.service:
            return False
        
        target_services = rule.get('values', [])
        return context.service in target_services
    
    async def _evaluate_percentage_targeting(
        self,
        rule: Dict[str, Any],
        context: Optional[FlagContext] = None
    ) -> bool:
        """Evaluate percentage targeting"""
        percentage = rule.get('percentage', 0)
        
        # Use user_id or tenant_id for consistent bucketing
        bucket_key = None
        if context:
            bucket_key = context.user_id or context.tenant_id
        
        if not bucket_key:
            bucket_key = "anonymous"
        
        # Generate consistent hash
        hash_value = hashlib.md5(bucket_key.encode()).hexdigest()
        bucket = int(hash_value[:8], 16) % 100
        
        return bucket < percentage
    
    async def _evaluate_custom_targeting(
        self,
        rule: Dict[str, Any],
        context: Optional[FlagContext] = None
    ) -> bool:
        """Evaluate custom targeting"""
        if not context or not context.custom_attributes:
            return False
        
        conditions = rule.get('conditions', [])
        
        for condition in conditions:
            attribute = condition.get('attribute')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if attribute not in context.custom_attributes:
                return False
            
            attr_value = context.custom_attributes[attribute]
            
            if operator == 'equals' and attr_value != value:
                return False
            elif operator == 'contains' and value not in str(attr_value):
                return False
            elif operator == 'starts_with' and not str(attr_value).startswith(value):
                return False
            elif operator == 'ends_with' and not str(attr_value).endswith(value):
                return False
        
        return True
    
    async def _execute_rollout(
        self,
        key: str,
        target_percentage: float,
        duration_minutes: int,
        step_percentage: float,
        updated_by: str
    ) -> None:
        """Execute gradual rollout"""
        try:
            current_percentage = self.flags[key].rollout_percentage
            step_duration = duration_minutes * 60 / ((target_percentage - current_percentage) / step_percentage)
            
            while current_percentage < target_percentage:
                current_percentage = min(current_percentage + step_percentage, target_percentage)
                
                await self.update_flag(
                    key=key,
                    rollout_percentage=current_percentage,
                    updated_by=updated_by
                )
                
                self.logger.info(f"Rollout step for {key}: {current_percentage}%")
                
                if current_percentage < target_percentage:
                    await asyncio.sleep(step_duration)
            
            self.system_metrics['rollouts_executed'] += 1
            self.logger.info(f"Rollout completed for {key}: {target_percentage}%")
            
        except Exception as e:
            self.logger.error(f"Rollout execution failed for {key}: {str(e)}")
    
    async def _update_flag_metrics(self, key: str, evaluation: FlagEvaluation) -> None:
        """Update flag metrics"""
        if key not in self.metrics:
            self.metrics[key] = FlagMetrics(flag_key=key)
        
        metrics = self.metrics[key]
        metrics.evaluations += 1
        
        if evaluation.value:
            metrics.true_evaluations += 1
        else:
            metrics.false_evaluations += 1
        
        if evaluation.variation:
            if evaluation.variation not in metrics.variation_counts:
                metrics.variation_counts[evaluation.variation] = 0
            metrics.variation_counts[evaluation.variation] += 1
        
        metrics.last_evaluation = datetime.utcnow()
        if metrics.first_evaluation is None:
            metrics.first_evaluation = datetime.utcnow()
    
    async def _get_evaluation_from_cache(
        self,
        key: str,
        context: Optional[FlagContext] = None
    ) -> Optional[FlagEvaluation]:
        """Get evaluation from cache"""
        cache_key = self._get_evaluation_cache_key(key, context)
        
        if cache_key in self.evaluation_cache:
            cached_data = self.evaluation_cache[cache_key]
            if datetime.utcnow() - cached_data['timestamp'] < self.evaluation_cache_ttl:
                self.system_metrics['cache_hits'] += 1
                return cached_data['evaluation']
            else:
                del self.evaluation_cache[cache_key]
        
        self.system_metrics['cache_misses'] += 1
        return None
    
    async def _cache_evaluation(
        self,
        key: str,
        context: Optional[FlagContext],
        evaluation: FlagEvaluation
    ) -> None:
        """Cache evaluation result"""
        cache_key = self._get_evaluation_cache_key(key, context)
        self.evaluation_cache[cache_key] = {
            'evaluation': evaluation,
            'timestamp': datetime.utcnow()
        }
        
        # Limit cache size
        if len(self.evaluation_cache) > 10000:
            # Remove oldest entries
            sorted_items = sorted(
                self.evaluation_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            for old_key, _ in sorted_items[:5000]:
                del self.evaluation_cache[old_key]
    
    def _get_evaluation_cache_key(self, key: str, context: Optional[FlagContext]) -> str:
        """Generate cache key for evaluation"""
        context_str = ""
        if context:
            context_str = f"{context.user_id}:{context.tenant_id}:{context.environment}:{context.role}:{context.service}"
        
        return f"{key}:{context_str}"
    
    async def _invalidate_cache(self, key: str) -> None:
        """Invalidate cache for flag"""
        # Remove from flag cache
        if key in self.flag_cache:
            del self.flag_cache[key]
        if key in self.cache_timestamps:
            del self.cache_timestamps[key]
        
        # Remove from evaluation cache
        keys_to_remove = [
            cache_key for cache_key in self.evaluation_cache.keys()
            if cache_key.startswith(f"{key}:")
        ]
        for cache_key in keys_to_remove:
            del self.evaluation_cache[cache_key]
    
    async def _notify_flag_listeners(self, key: str, event: str) -> None:
        """Notify flag listeners of changes"""
        if key in self.flag_listeners:
            for listener in self.flag_listeners[key]:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(key, event)
                    else:
                        listener(key, event)
                except Exception as e:
                    self.logger.error(f"Flag listener error: {str(e)}")
    
    async def cleanup(self) -> None:
        """Cleanup feature flag manager resources"""
        try:
            # Cancel rollout tasks
            for task in self.rollout_schedules.values():
                if not task.done():
                    task.cancel()
            
            # Clear caches
            self.flag_cache.clear()
            self.evaluation_cache.clear()
            self.segment_cache.clear()
            
            self.logger.info("FeatureFlagManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during FeatureFlagManager cleanup: {str(e)}")