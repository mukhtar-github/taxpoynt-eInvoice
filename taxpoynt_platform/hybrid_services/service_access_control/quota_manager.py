"""
Quota Manager - Usage quotas and enforcement

This module provides comprehensive quota management capabilities that integrate with
the existing usage tracker and tier manager to provide granular usage control,
enforcement, and intelligent alerting across the TaxPoynt platform.

Integrates with:
- billing_orchestration/usage_tracker.py for usage tracking
- billing_orchestration/tier_manager.py for tier-based quotas
- core platform monitoring and notifications
"""

import asyncio
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID, uuid4
from decimal import Decimal

# Import existing platform services
from ...billing_orchestration.usage_tracker import (
    UsageTracker, UsageMetric, UsageAlertType, UsageEnforcementAction
)
from ...billing_orchestration.tier_manager import TierManager, QuotaType
from ....core_platform.monitoring import MetricsCollector
from ....core_platform.data_management.cache_manager import CacheManager
from ....core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class QuotaScope(str, Enum):
    """Scope of quota application"""
    ORGANIZATION = "organization"
    USER = "user"
    API_KEY = "api_key"
    FEATURE = "feature"
    GLOBAL = "global"


class QuotaWindow(str, Enum):
    """Time windows for quota calculation"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    LIFETIME = "lifetime"


class QuotaEnforcementLevel(str, Enum):
    """Levels of quota enforcement"""
    SOFT = "soft"          # Log and alert only
    HARD = "hard"          # Block access when exceeded
    THROTTLE = "throttle"  # Reduce access rate when approaching limit
    OVERAGE = "overage"    # Allow overage with billing


class QuotaStatus(str, Enum):
    """Status of quota usage"""
    NORMAL = "normal"              # Usage below warning threshold
    WARNING = "warning"            # Usage above warning threshold (80%)
    CRITICAL = "critical"          # Usage above critical threshold (95%)
    EXCEEDED = "exceeded"          # Usage at or above limit (100%)
    SUSPENDED = "suspended"        # Quota temporarily suspended


@dataclass
class QuotaConfig:
    """Configuration for a quota"""
    quota_id: str
    name: str
    description: str
    metric: UsageMetric
    scope: QuotaScope
    window: QuotaWindow
    limit: int
    enforcement_level: QuotaEnforcementLevel
    warning_threshold: float = 0.8  # 80%
    critical_threshold: float = 0.95  # 95%
    reset_schedule: Optional[str] = None
    overage_rate: Optional[Decimal] = None
    grace_period_minutes: int = 0
    auto_increase: bool = False
    max_auto_limit: Optional[int] = None
    tags: Dict[str, str] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class QuotaUsage:
    """Current usage for a quota"""
    quota_id: str
    scope_id: str
    current_usage: int
    limit: int
    remaining: int
    usage_percentage: float
    window_start: datetime
    window_end: datetime
    last_updated: datetime
    status: QuotaStatus
    
    def __post_init__(self):
        self.remaining = max(0, self.limit - self.current_usage)
        self.usage_percentage = (self.current_usage / self.limit * 100) if self.limit > 0 else 0


@dataclass
class QuotaEnforcement:
    """Result of quota enforcement evaluation"""
    quota_id: str
    scope_id: str
    allowed: bool
    reason: str
    current_usage: int
    limit: int
    remaining: int
    enforcement_action: UsageEnforcementAction
    retry_after: Optional[datetime] = None
    overage_cost: Optional[Decimal] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QuotaAlert:
    """Quota alert information"""
    alert_id: str
    quota_id: str
    scope_id: str
    alert_type: UsageAlertType
    message: str
    current_usage: int
    limit: int
    timestamp: datetime
    resolved: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QuotaManager:
    """
    Comprehensive quota management system that provides granular usage control,
    enforcement, and intelligent alerting for the TaxPoynt platform.
    """
    
    def __init__(
        self,
        usage_tracker: UsageTracker,
        tier_manager: TierManager,
        metrics_collector: MetricsCollector,
        cache_manager: CacheManager,
        notification_service: NotificationService,
        config: Optional[Dict[str, Any]] = None
    ):
        self.usage_tracker = usage_tracker
        self.tier_manager = tier_manager
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.notification_service = notification_service
        self.config = config or {}
        
        # Quota configurations
        self.quota_configs: Dict[str, QuotaConfig] = {}
        self.scope_quotas: Dict[str, List[str]] = {}  # scope_id -> quota_ids
        
        # Configuration
        self.cache_ttl = self.config.get("cache_ttl", 60)  # 1 minute
        self.alert_cooldown = self.config.get("alert_cooldown", 300)  # 5 minutes
        self.enable_auto_scaling = self.config.get("enable_auto_scaling", False)
        self.overage_billing_enabled = self.config.get("overage_billing_enabled", True)
        
        # Load default quota configurations
        self._load_default_quotas()
    
    def _load_default_quotas(self):
        """Load default quota configurations for TaxPoynt platform"""
        default_quotas = [
            # Organization-level quotas
            QuotaConfig(
                quota_id="org_api_calls_daily",
                name="Daily API Calls",
                description="Maximum API calls per organization per day",
                metric=UsageMetric.API_CALLS,
                scope=QuotaScope.ORGANIZATION,
                window=QuotaWindow.DAY,
                limit=10000,  # Default, will be overridden by tier
                enforcement_level=QuotaEnforcementLevel.HARD,
                auto_increase=True,
                max_auto_limit=50000
            ),
            
            QuotaConfig(
                quota_id="org_invoices_monthly",
                name="Monthly Invoices",
                description="Maximum invoices processed per organization per month",
                metric=UsageMetric.INVOICES_PROCESSED,
                scope=QuotaScope.ORGANIZATION,
                window=QuotaWindow.MONTH,
                limit=1000,  # Default, will be overridden by tier
                enforcement_level=QuotaEnforcementLevel.OVERAGE,
                overage_rate=Decimal("0.01")  # $0.01 per extra invoice
            ),
            
            QuotaConfig(
                quota_id="org_storage_total",
                name="Total Storage",
                description="Maximum storage usage per organization",
                metric=UsageMetric.STORAGE_USAGE,
                scope=QuotaScope.ORGANIZATION,
                window=QuotaWindow.LIFETIME,
                limit=1000000000,  # 1GB default
                enforcement_level=QuotaEnforcementLevel.HARD
            ),
            
            QuotaConfig(
                quota_id="org_users_total",
                name="Total User Accounts",
                description="Maximum user accounts per organization",
                metric=UsageMetric.USER_ACCOUNTS,
                scope=QuotaScope.ORGANIZATION,
                window=QuotaWindow.LIFETIME,
                limit=5,  # Default, will be overridden by tier
                enforcement_level=QuotaEnforcementLevel.HARD
            ),
            
            # User-level quotas
            QuotaConfig(
                quota_id="user_api_calls_hourly",
                name="Hourly API Calls per User",
                description="Maximum API calls per user per hour",
                metric=UsageMetric.API_CALLS,
                scope=QuotaScope.USER,
                window=QuotaWindow.HOUR,
                limit=1000,
                enforcement_level=QuotaEnforcementLevel.THROTTLE
            ),
            
            QuotaConfig(
                quota_id="user_batch_operations_daily",
                name="Daily Batch Operations per User",
                description="Maximum batch operations per user per day",
                metric=UsageMetric.BATCH_OPERATIONS,
                scope=QuotaScope.USER,
                window=QuotaWindow.DAY,
                limit=10,
                enforcement_level=QuotaEnforcementLevel.HARD
            ),
            
            # API Key quotas
            QuotaConfig(
                quota_id="apikey_calls_minute",
                name="API Key Rate Limit",
                description="Maximum API calls per API key per minute",
                metric=UsageMetric.API_CALLS,
                scope=QuotaScope.API_KEY,
                window=QuotaWindow.MINUTE,
                limit=60,
                enforcement_level=QuotaEnforcementLevel.THROTTLE
            ),
            
            # Feature-specific quotas
            QuotaConfig(
                quota_id="feature_webhooks_daily",
                name="Daily Webhook Calls",
                description="Maximum webhook calls per organization per day",
                metric=UsageMetric.WEBHOOK_CALLS,
                scope=QuotaScope.FEATURE,
                window=QuotaWindow.DAY,
                limit=1000,
                enforcement_level=QuotaEnforcementLevel.SOFT
            ),
            
            QuotaConfig(
                quota_id="feature_exports_monthly",
                name="Monthly Data Exports",
                description="Maximum data exports per organization per month",
                metric=UsageMetric.DATA_EXPORTS,
                scope=QuotaScope.FEATURE,
                window=QuotaWindow.MONTH,
                limit=50,
                enforcement_level=QuotaEnforcementLevel.HARD
            )
        ]
        
        for quota in default_quotas:
            self.register_quota(quota)
    
    def register_quota(self, quota_config: QuotaConfig):
        """Register a new quota configuration"""
        self.quota_configs[quota_config.quota_id] = quota_config
        logger.info(f"Registered quota: {quota_config.quota_id}")
    
    def assign_quota_to_scope(self, quota_id: str, scope_id: str):
        """Assign a quota to a specific scope"""
        if scope_id not in self.scope_quotas:
            self.scope_quotas[scope_id] = []
        
        if quota_id not in self.scope_quotas[scope_id]:
            self.scope_quotas[scope_id].append(quota_id)
    
    async def check_quota_enforcement(
        self,
        quota_id: str,
        scope_id: str,
        requested_amount: int = 1
    ) -> QuotaEnforcement:
        """
        Check if a quota allows the requested usage and return enforcement decision
        """
        try:
            # Get quota configuration
            quota_config = self.quota_configs.get(quota_id)
            if not quota_config or not quota_config.enabled:
                return QuotaEnforcement(
                    quota_id=quota_id,
                    scope_id=scope_id,
                    allowed=True,
                    reason="Quota not configured or disabled",
                    current_usage=0,
                    limit=0,
                    remaining=0,
                    enforcement_action=UsageEnforcementAction.LOG_ONLY
                )
            
            # Get current usage
            current_usage = await self.get_current_usage(quota_id, scope_id)
            
            # Get effective limit (may be overridden by tier)
            effective_limit = await self._get_effective_limit(quota_config, scope_id)
            
            # Calculate projected usage
            projected_usage = current_usage.current_usage + requested_amount
            
            # Check enforcement based on level
            if quota_config.enforcement_level == QuotaEnforcementLevel.SOFT:
                # Soft enforcement - always allow but alert
                if projected_usage >= effective_limit:
                    await self._trigger_quota_alert(
                        quota_config, scope_id, current_usage, UsageAlertType.LIMIT_EXCEEDED
                    )
                
                return QuotaEnforcement(
                    quota_id=quota_id,
                    scope_id=scope_id,
                    allowed=True,
                    reason="Soft enforcement - allowed with alert",
                    current_usage=current_usage.current_usage,
                    limit=effective_limit,
                    remaining=max(0, effective_limit - projected_usage),
                    enforcement_action=UsageEnforcementAction.LOG_ONLY
                )
            
            elif quota_config.enforcement_level == QuotaEnforcementLevel.HARD:
                # Hard enforcement - block if exceeded
                if projected_usage > effective_limit:
                    await self._trigger_quota_alert(
                        quota_config, scope_id, current_usage, UsageAlertType.LIMIT_EXCEEDED
                    )
                    
                    return QuotaEnforcement(
                        quota_id=quota_id,
                        scope_id=scope_id,
                        allowed=False,
                        reason="Hard quota limit exceeded",
                        current_usage=current_usage.current_usage,
                        limit=effective_limit,
                        remaining=0,
                        enforcement_action=UsageEnforcementAction.BLOCK,
                        retry_after=self._calculate_retry_after(quota_config)
                    )
                
                # Check for warning/critical thresholds
                await self._check_usage_thresholds(quota_config, scope_id, current_usage, effective_limit)
                
                return QuotaEnforcement(
                    quota_id=quota_id,
                    scope_id=scope_id,
                    allowed=True,
                    reason="Within hard quota limit",
                    current_usage=current_usage.current_usage,
                    limit=effective_limit,
                    remaining=effective_limit - projected_usage,
                    enforcement_action=UsageEnforcementAction.LOG_ONLY
                )
            
            elif quota_config.enforcement_level == QuotaEnforcementLevel.THROTTLE:
                # Throttle enforcement - reduce rate as approaching limit
                if projected_usage > effective_limit:
                    await self._trigger_quota_alert(
                        quota_config, scope_id, current_usage, UsageAlertType.LIMIT_EXCEEDED
                    )
                    
                    return QuotaEnforcement(
                        quota_id=quota_id,
                        scope_id=scope_id,
                        allowed=False,
                        reason="Throttle quota limit exceeded",
                        current_usage=current_usage.current_usage,
                        limit=effective_limit,
                        remaining=0,
                        enforcement_action=UsageEnforcementAction.THROTTLE,
                        retry_after=self._calculate_throttle_delay(quota_config, current_usage.usage_percentage)
                    )
                
                # Check if throttling should be applied
                if current_usage.usage_percentage >= quota_config.warning_threshold * 100:
                    throttle_delay = self._calculate_throttle_delay(quota_config, current_usage.usage_percentage)
                    
                    return QuotaEnforcement(
                        quota_id=quota_id,
                        scope_id=scope_id,
                        allowed=True,
                        reason="Throttling applied due to high usage",
                        current_usage=current_usage.current_usage,
                        limit=effective_limit,
                        remaining=effective_limit - projected_usage,
                        enforcement_action=UsageEnforcementAction.THROTTLE,
                        retry_after=throttle_delay
                    )
                
                return QuotaEnforcement(
                    quota_id=quota_id,
                    scope_id=scope_id,
                    allowed=True,
                    reason="Within throttle quota limit",
                    current_usage=current_usage.current_usage,
                    limit=effective_limit,
                    remaining=effective_limit - projected_usage,
                    enforcement_action=UsageEnforcementAction.LOG_ONLY
                )
            
            elif quota_config.enforcement_level == QuotaEnforcementLevel.OVERAGE:
                # Overage enforcement - allow with billing
                if projected_usage > effective_limit and self.overage_billing_enabled:
                    overage_amount = projected_usage - effective_limit
                    overage_cost = overage_amount * (quota_config.overage_rate or Decimal("0"))
                    
                    await self._trigger_quota_alert(
                        quota_config, scope_id, current_usage, UsageAlertType.OVERAGE
                    )
                    
                    return QuotaEnforcement(
                        quota_id=quota_id,
                        scope_id=scope_id,
                        allowed=True,
                        reason="Overage billing applied",
                        current_usage=current_usage.current_usage,
                        limit=effective_limit,
                        remaining=0,
                        enforcement_action=UsageEnforcementAction.CHARGE_OVERAGE,
                        overage_cost=overage_cost,
                        metadata={"overage_amount": overage_amount}
                    )
                elif projected_usage > effective_limit:
                    # Overage billing disabled, block access
                    return QuotaEnforcement(
                        quota_id=quota_id,
                        scope_id=scope_id,
                        allowed=False,
                        reason="Overage billing disabled",
                        current_usage=current_usage.current_usage,
                        limit=effective_limit,
                        remaining=0,
                        enforcement_action=UsageEnforcementAction.BLOCK
                    )
                
                return QuotaEnforcement(
                    quota_id=quota_id,
                    scope_id=scope_id,
                    allowed=True,
                    reason="Within overage quota limit",
                    current_usage=current_usage.current_usage,
                    limit=effective_limit,
                    remaining=effective_limit - projected_usage,
                    enforcement_action=UsageEnforcementAction.LOG_ONLY
                )
            
            else:
                # Unknown enforcement level, default to allow
                return QuotaEnforcement(
                    quota_id=quota_id,
                    scope_id=scope_id,
                    allowed=True,
                    reason="Unknown enforcement level",
                    current_usage=current_usage.current_usage,
                    limit=effective_limit,
                    remaining=effective_limit - projected_usage,
                    enforcement_action=UsageEnforcementAction.LOG_ONLY
                )
        
        except Exception as e:
            logger.error(f"Error checking quota enforcement for {quota_id}:{scope_id}: {e}")
            # Fail open - allow access but log error
            return QuotaEnforcement(
                quota_id=quota_id,
                scope_id=scope_id,
                allowed=True,
                reason=f"Quota check error: {str(e)}",
                current_usage=0,
                limit=0,
                remaining=0,
                enforcement_action=UsageEnforcementAction.LOG_ONLY
            )
    
    async def record_usage(
        self,
        quota_id: str,
        scope_id: str,
        amount: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record usage for a quota"""
        try:
            quota_config = self.quota_configs.get(quota_id)
            if not quota_config or not quota_config.enabled:
                return True
            
            # Record usage through usage tracker
            await self.usage_tracker.record_usage(
                organization_id=scope_id if quota_config.scope == QuotaScope.ORGANIZATION else None,
                action=quota_config.metric.value,
                resource=quota_id,
                amount=amount,
                metadata=metadata or {}
            )
            
            # Update cache
            cache_key = self._get_usage_cache_key(quota_id, scope_id, quota_config.window)
            current_usage = await self.cache_manager.get(cache_key) or 0
            new_usage = current_usage + amount
            
            # Calculate window boundaries
            window_start, window_end = self._calculate_window_boundaries(quota_config.window)
            
            await self.cache_manager.set(
                cache_key,
                new_usage,
                ttl=int((window_end - datetime.now(timezone.utc)).total_seconds())
            )
            
            # Record metrics
            await self.metrics_collector.record_counter(
                "quota_usage_recorded",
                tags={
                    "quota_id": quota_id,
                    "scope": quota_config.scope.value,
                    "metric": quota_config.metric.value
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording usage for {quota_id}:{scope_id}: {e}")
            return False
    
    async def get_current_usage(self, quota_id: str, scope_id: str) -> QuotaUsage:
        """Get current usage for a quota"""
        quota_config = self.quota_configs.get(quota_id)
        if not quota_config:
            raise ValueError(f"Quota not found: {quota_id}")
        
        # Get effective limit
        effective_limit = await self._get_effective_limit(quota_config, scope_id)
        
        # Calculate window boundaries
        window_start, window_end = self._calculate_window_boundaries(quota_config.window)
        
        # Get usage from cache first
        cache_key = self._get_usage_cache_key(quota_id, scope_id, quota_config.window)
        cached_usage = await self.cache_manager.get(cache_key)
        
        if cached_usage is not None:
            current_usage = int(cached_usage)
        else:
            # Get usage from usage tracker
            current_usage = await self._get_usage_from_tracker(
                quota_config, scope_id, window_start, window_end
            )
            
            # Cache for next time
            await self.cache_manager.set(
                cache_key,
                current_usage,
                ttl=int((window_end - datetime.now(timezone.utc)).total_seconds())
            )
        
        # Determine status
        usage_percentage = (current_usage / effective_limit * 100) if effective_limit > 0 else 0
        
        if usage_percentage >= 100:
            status = QuotaStatus.EXCEEDED
        elif usage_percentage >= quota_config.critical_threshold * 100:
            status = QuotaStatus.CRITICAL
        elif usage_percentage >= quota_config.warning_threshold * 100:
            status = QuotaStatus.WARNING
        else:
            status = QuotaStatus.NORMAL
        
        return QuotaUsage(
            quota_id=quota_id,
            scope_id=scope_id,
            current_usage=current_usage,
            limit=effective_limit,
            remaining=max(0, effective_limit - current_usage),
            usage_percentage=usage_percentage,
            window_start=window_start,
            window_end=window_end,
            last_updated=datetime.now(timezone.utc),
            status=status
        )
    
    async def get_scope_quotas(self, scope_id: str) -> List[QuotaUsage]:
        """Get all quota usage for a scope"""
        quota_ids = self.scope_quotas.get(scope_id, [])
        quotas = []
        
        for quota_id in quota_ids:
            try:
                usage = await self.get_current_usage(quota_id, scope_id)
                quotas.append(usage)
            except Exception as e:
                logger.error(f"Error getting usage for {quota_id}:{scope_id}: {e}")
        
        return quotas
    
    async def reset_quota(self, quota_id: str, scope_id: str) -> bool:
        """Reset quota usage for a scope"""
        try:
            quota_config = self.quota_configs.get(quota_id)
            if not quota_config:
                return False
            
            # Clear cache
            cache_key = self._get_usage_cache_key(quota_id, scope_id, quota_config.window)
            await self.cache_manager.delete(cache_key)
            
            logger.info(f"Reset quota {quota_id} for scope {scope_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting quota {quota_id}:{scope_id}: {e}")
            return False
    
    async def _get_effective_limit(self, quota_config: QuotaConfig, scope_id: str) -> int:
        """Get effective limit for quota, considering tier overrides"""
        base_limit = quota_config.limit
        
        # Check if this is an organization scope with tier-based overrides
        if quota_config.scope == QuotaScope.ORGANIZATION:
            try:
                # Get organization's tier limits from tier manager
                tier_limits = await self.tier_manager.get_organization_quotas(scope_id)
                
                # Look for matching quota
                for tier_quota in tier_limits:
                    if tier_quota.get("metric") == quota_config.metric.value:
                        return tier_quota.get("limit", base_limit)
                        
            except Exception as e:
                logger.warning(f"Error getting tier limits for {scope_id}: {e}")
        
        return base_limit
    
    def _calculate_window_boundaries(self, window: QuotaWindow) -> Tuple[datetime, datetime]:
        """Calculate start and end boundaries for quota window"""
        now = datetime.now(timezone.utc)
        
        if window == QuotaWindow.MINUTE:
            start = now.replace(second=0, microsecond=0)
            end = start + timedelta(minutes=1)
        elif window == QuotaWindow.HOUR:
            start = now.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif window == QuotaWindow.DAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif window == QuotaWindow.WEEK:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start = start - timedelta(days=start.weekday())  # Start of week (Monday)
            end = start + timedelta(weeks=1)
        elif window == QuotaWindow.MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        elif window == QuotaWindow.YEAR:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
        else:  # LIFETIME
            start = datetime.min.replace(tzinfo=timezone.utc)
            end = datetime.max.replace(tzinfo=timezone.utc)
        
        return start, end
    
    def _get_usage_cache_key(self, quota_id: str, scope_id: str, window: QuotaWindow) -> str:
        """Generate cache key for quota usage"""
        window_start, _ = self._calculate_window_boundaries(window)
        window_key = window_start.isoformat() if window != QuotaWindow.LIFETIME else "lifetime"
        return f"quota_usage:{quota_id}:{scope_id}:{window_key}"
    
    async def _get_usage_from_tracker(
        self,
        quota_config: QuotaConfig,
        scope_id: str,
        window_start: datetime,
        window_end: datetime
    ) -> int:
        """Get usage from usage tracker for time window"""
        # This would query the usage tracker for specific metrics
        # For now, return 0 as placeholder
        return 0
    
    def _calculate_retry_after(self, quota_config: QuotaConfig) -> datetime:
        """Calculate when to retry after quota exceeded"""
        _, window_end = self._calculate_window_boundaries(quota_config.window)
        return window_end
    
    def _calculate_throttle_delay(self, quota_config: QuotaConfig, usage_percentage: float) -> datetime:
        """Calculate throttle delay based on usage percentage"""
        # Progressive throttling: more delay as usage increases
        base_delay = 1  # 1 second base
        if usage_percentage >= 95:
            delay = base_delay * 10  # 10 seconds
        elif usage_percentage >= 90:
            delay = base_delay * 5   # 5 seconds
        elif usage_percentage >= 80:
            delay = base_delay * 2   # 2 seconds
        else:
            delay = base_delay
        
        return datetime.now(timezone.utc) + timedelta(seconds=delay)
    
    async def _check_usage_thresholds(
        self,
        quota_config: QuotaConfig,
        scope_id: str,
        current_usage: QuotaUsage,
        effective_limit: int
    ):
        """Check and trigger alerts for usage thresholds"""
        usage_percentage = current_usage.usage_percentage
        
        if usage_percentage >= quota_config.critical_threshold * 100:
            await self._trigger_quota_alert(
                quota_config, scope_id, current_usage, UsageAlertType.CRITICAL
            )
        elif usage_percentage >= quota_config.warning_threshold * 100:
            await self._trigger_quota_alert(
                quota_config, scope_id, current_usage, UsageAlertType.WARNING
            )
    
    async def _trigger_quota_alert(
        self,
        quota_config: QuotaConfig,
        scope_id: str,
        current_usage: QuotaUsage,
        alert_type: UsageAlertType
    ):
        """Trigger quota alert with cooldown"""
        # Check alert cooldown
        cooldown_key = f"quota_alert_cooldown:{quota_config.quota_id}:{scope_id}:{alert_type.value}"
        if await self.cache_manager.get(cooldown_key):
            return  # Still in cooldown
        
        # Create alert
        alert = QuotaAlert(
            alert_id=str(uuid4()),
            quota_id=quota_config.quota_id,
            scope_id=scope_id,
            alert_type=alert_type,
            message=f"Quota {quota_config.name} {alert_type.value}: {current_usage.usage_percentage:.1f}% used",
            current_usage=current_usage.current_usage,
            limit=current_usage.limit,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Send notification
        await self.notification_service.send_quota_alert(alert)
        
        # Set cooldown
        await self.cache_manager.set(cooldown_key, True, ttl=self.alert_cooldown)
        
        # Record metrics
        await self.metrics_collector.record_counter(
            "quota_alerts_triggered",
            tags={
                "quota_id": quota_config.quota_id,
                "alert_type": alert_type.value,
                "scope": quota_config.scope.value
            }
        )


# Decorator for quota enforcement

def enforce_quota(quota_id: str, scope_attr: str = "organization_id", amount: int = 1):
    """
    Decorator to enforce quota on FastAPI endpoints
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request and scope from function parameters
            request = None
            scope_id = None
            
            for arg in args:
                if hasattr(arg, 'url') and hasattr(arg, 'headers'):  # FastAPI Request
                    request = arg
                    scope_id = getattr(request.state, scope_attr, None)
                    break
            
            if not request or not scope_id:
                raise HTTPException(
                    status_code=400,
                    detail="Quota enforcement: Request or scope not found"
                )
            
            # Get quota manager from request state
            quota_manager = getattr(request.state, 'quota_manager', None)
            if not quota_manager:
                raise HTTPException(
                    status_code=500,
                    detail="Quota manager not available"
                )
            
            # Check quota
            enforcement = await quota_manager.check_quota_enforcement(
                quota_id, scope_id, amount
            )
            
            if not enforcement.allowed:
                headers = {}
                if enforcement.retry_after:
                    headers["Retry-After"] = str(int(
                        (enforcement.retry_after - datetime.now(timezone.utc)).total_seconds()
                    ))
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Quota exceeded: {enforcement.reason}",
                    headers=headers
                )
            
            # Record usage
            await quota_manager.record_usage(quota_id, scope_id, amount)
            
            # Store enforcement result for potential use
            request.state.quota_enforcement = enforcement
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator