"""
Multi-Tenant Manager for TaxPoynt Platform

Enterprise-grade multi-tenancy with data isolation, performance optimization,
and scalability patterns for 100K+ invoices across multiple organizations.
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Set, Tuple
from uuid import UUID
from contextlib import contextmanager
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import Select
from enum import Enum
import json
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class TenantIsolationLevel(Enum):
    """Tenant data isolation levels."""
    BASIC = "basic"              # Row-level security with organization_id
    ENHANCED = "enhanced"        # Schema-level isolation
    STRICT = "strict"           # Database-level isolation
    ENCRYPTED = "encrypted"     # Encrypted data with tenant-specific keys


class ServiceType(Enum):
    """Service types for dual revenue model."""
    SI = "si"           # System Integrator (Commercial)
    APP = "app"         # Access Point Provider (Grant-funded)
    HYBRID = "hybrid"   # Both services under one account


class TenantTier(Enum):
    """Tenant service tiers for different scale levels."""
    STARTER = "starter"         # < 1K invoices/month
    PROFESSIONAL = "professional"  # 1K-10K invoices/month  
    ENTERPRISE = "enterprise"   # 10K-100K invoices/month
    SCALE = "scale"            # 100K+ invoices/month


class GrantStatus(Enum):
    """FIRS grant status for APP users."""
    NOT_ELIGIBLE = "not_eligible"
    ELIGIBLE = "eligible"
    APPLIED = "applied"
    MILESTONE_1 = "milestone_1"    # 20 taxpayers
    MILESTONE_2 = "milestone_2"    # 40 taxpayers  
    MILESTONE_3 = "milestone_3"    # 60 taxpayers
    MILESTONE_4 = "milestone_4"    # 80 taxpayers
    MILESTONE_5 = "milestone_5"    # 100 taxpayers
    COMPLETED = "completed"


class BillingStatus(Enum):
    """Billing status for SI users."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class TenantConfig:
    """Tenant configuration and metadata."""
    tenant_id: UUID
    organization_id: UUID
    tenant_name: str
    tier: TenantTier
    isolation_level: TenantIsolationLevel
    max_invoices_per_month: int
    max_users: int
    features_enabled: Set[str]
    data_retention_days: int
    backup_frequency_hours: int
    cache_ttl_seconds: int
    rate_limit_per_minute: int
    database_shard: Optional[str] = None
    encryption_key_id: Optional[str] = None
    created_at: datetime = None
    last_accessed_at: datetime = None
    
    # Dual Revenue Model Fields
    service_types: List[ServiceType] = None  # SI, APP, or both (HYBRID)
    
    # SI (Commercial) Fields
    billing_tier: Optional[str] = None        # For SI users (starter, professional, etc.)
    billing_status: BillingStatus = BillingStatus.ACTIVE
    usage_quotas: Dict[str, Any] = None       # Usage limits per tier
    subscription_start_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    monthly_invoice_limit: Optional[int] = None
    overage_rate_per_invoice: Optional[float] = None
    
    # APP (Grant-funded) Fields  
    grant_status: GrantStatus = GrantStatus.NOT_ELIGIBLE
    milestone_progress: Dict[str, Any] = None  # FIRS milestone tracking
    grant_eligibility_date: Optional[datetime] = None
    current_milestone: Optional[str] = None
    taxpayer_count: int = 0
    large_taxpayer_count: int = 0
    sme_taxpayer_count: int = 0
    sector_representation: List[str] = None    # List of sectors represented
    transmission_rate: Optional[float] = None  # % of active taxpayers
    compliance_sustained: bool = False         # For milestone 4
    full_validation_completed: bool = False    # For milestone 5
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_accessed_at is None:
            self.last_accessed_at = datetime.utcnow()
        
        # Initialize dual revenue model defaults
        if self.service_types is None:
            self.service_types = [ServiceType.SI]  # Default to SI
        if self.usage_quotas is None:
            self.usage_quotas = {}
        if self.milestone_progress is None:
            self.milestone_progress = {}
        if self.sector_representation is None:
            self.sector_representation = []


@dataclass
class TenantMetrics:
    """Tenant usage metrics for monitoring and scaling."""
    tenant_id: UUID
    invoice_count_current_month: int
    user_count_active: int
    storage_usage_mb: float
    api_requests_last_hour: int
    cache_hit_ratio: float
    avg_response_time_ms: float
    error_rate_percentage: float
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


class TenantContext:
    """Thread-local tenant context for request-scoped operations."""
    
    def __init__(self):
        self._context: Dict[str, Any] = {}
    
    def set_tenant(self, tenant_id: UUID, organization_id: UUID, user_id: Optional[UUID] = None):
        """Set current tenant context."""
        self._context.update({
            "tenant_id": tenant_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "set_at": datetime.utcnow()
        })
    
    def get_tenant_id(self) -> Optional[UUID]:
        """Get current tenant ID."""
        return self._context.get("tenant_id")
    
    def get_organization_id(self) -> Optional[UUID]:
        """Get current organization ID."""
        return self._context.get("organization_id")
    
    def get_user_id(self) -> Optional[UUID]:
        """Get current user ID."""
        return self._context.get("user_id")
    
    def clear(self):
        """Clear tenant context."""
        self._context.clear()
    
    def is_set(self) -> bool:
        """Check if tenant context is set."""
        return "tenant_id" in self._context and "organization_id" in self._context


class MultiTenantManager:
    """
    Enterprise multi-tenant manager with scalability patterns.
    
    Features:
    - Row-level security with organization_id filtering
    - Tenant-aware query optimization
    - Data sharding strategies for scale
    - Performance monitoring and metrics
    - Tier-based resource allocation
    - Cloud migration patterns
    """
    
    def __init__(self, database_layer, cache_manager=None):
        """
        Initialize multi-tenant manager.
        
        Args:
            database_layer: Database abstraction layer
            cache_manager: Optional cache manager for tenant metadata
        """
        self.db_layer = database_layer
        self.cache_manager = cache_manager
        self.tenant_context = TenantContext()
        
        # Tenant configuration cache
        self._tenant_config_cache: Dict[UUID, TenantConfig] = {}
        self._tenant_metrics_cache: Dict[UUID, TenantMetrics] = {}
        
        # Performance tracking
        self._query_stats = {
            "total_queries": 0,
            "tenant_filtered_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tenant-mgr")
    
    def set_tenant_context(self, tenant_id: UUID, organization_id: UUID, user_id: Optional[UUID] = None, service_type: Optional[ServiceType] = None):
        """Set tenant context for current request/operation."""
        self.tenant_context.set_tenant(tenant_id, organization_id, user_id)
        
        # Add service type to context if provided
        if service_type:
            self.tenant_context._context["service_type"] = service_type
        
        # Update last accessed time
        if self.cache_manager:
            self._update_tenant_last_access_async(tenant_id)
    
    def clear_tenant_context(self):
        """Clear tenant context."""
        self.tenant_context.clear()
    
    @contextmanager
    def tenant_scope(self, tenant_id: UUID, organization_id: UUID, user_id: Optional[UUID] = None, service_type: Optional[ServiceType] = None):
        """Context manager for tenant-scoped operations."""
        # Store previous context
        prev_context = self.tenant_context._context.copy()
        
        try:
            self.set_tenant_context(tenant_id, organization_id, user_id, service_type)
            yield
        finally:
            # Restore previous context
            self.tenant_context._context = prev_context
    
    def get_tenant_config(self, tenant_id: UUID) -> Optional[TenantConfig]:
        """Get tenant configuration with caching."""
        # Check memory cache first
        if tenant_id in self._tenant_config_cache:
            self._query_stats["cache_hits"] += 1
            return self._tenant_config_cache[tenant_id]
        
        # Check Redis cache if available
        if self.cache_manager:
            cache_key = f"tenant_config:{tenant_id}"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                config = TenantConfig(**json.loads(cached_data))
                self._tenant_config_cache[tenant_id] = config
                self._query_stats["cache_hits"] += 1
                return config
        
        # Load from database
        self._query_stats["cache_misses"] += 1
        config = self._load_tenant_config_from_db(tenant_id)
        
        if config:
            # Cache in memory and Redis
            self._tenant_config_cache[tenant_id] = config
            if self.cache_manager:
                cache_key = f"tenant_config:{tenant_id}"
                self.cache_manager.set(
                    cache_key, 
                    json.dumps(asdict(config), default=str),
                    ttl=config.cache_ttl_seconds
                )
        
        return config
    
    def _load_tenant_config_from_db(self, tenant_id: UUID) -> Optional[TenantConfig]:
        """Load tenant configuration from database."""
        try:
            with self.db_layer.get_session() as session:
                # Query organizations table for tenant info
                result = session.execute(text("""
                    SELECT 
                        id as tenant_id,
                        id as organization_id,
                        name as tenant_name,
                        tier,
                        created_at,
                        updated_at as last_accessed_at
                    FROM organizations 
                    WHERE id = :tenant_id AND is_active = true
                """), {"tenant_id": tenant_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                # Map tier and create config with defaults
                tier_mapping = {
                    "starter": TenantTier.STARTER,
                    "professional": TenantTier.PROFESSIONAL, 
                    "enterprise": TenantTier.ENTERPRISE,
                    "scale": TenantTier.SCALE
                }
                
                tier = tier_mapping.get(row.tier, TenantTier.PROFESSIONAL)
                
                # Tier-based configurations
                tier_configs = {
                    TenantTier.STARTER: {
                        "max_invoices_per_month": 1000,
                        "max_users": 5,
                        "rate_limit_per_minute": 100,
                        "cache_ttl_seconds": 300,
                        "data_retention_days": 365
                    },
                    TenantTier.PROFESSIONAL: {
                        "max_invoices_per_month": 10000,
                        "max_users": 25,
                        "rate_limit_per_minute": 500,
                        "cache_ttl_seconds": 600,
                        "data_retention_days": 1095  # 3 years
                    },
                    TenantTier.ENTERPRISE: {
                        "max_invoices_per_month": 100000,
                        "max_users": 100,
                        "rate_limit_per_minute": 2000,
                        "cache_ttl_seconds": 1200,
                        "data_retention_days": 2555  # 7 years
                    },
                    TenantTier.SCALE: {
                        "max_invoices_per_month": 1000000,
                        "max_users": 500,
                        "rate_limit_per_minute": 10000,
                        "cache_ttl_seconds": 1800,
                        "data_retention_days": 3650  # 10 years
                    }
                }
                
                config_values = tier_configs[tier]
                
                return TenantConfig(
                    tenant_id=row.tenant_id,
                    organization_id=row.organization_id,
                    tenant_name=row.tenant_name,
                    tier=tier,
                    isolation_level=TenantIsolationLevel.BASIC,  # Default for Railway
                    features_enabled=self._get_tier_features(tier),
                    backup_frequency_hours=24 if tier in [TenantTier.STARTER, TenantTier.PROFESSIONAL] else 12,
                    database_shard=self._calculate_shard(row.tenant_id),
                    created_at=row.created_at,
                    last_accessed_at=row.last_accessed_at,
                    **config_values
                )
                
        except Exception as e:
            logger.error(f"Failed to load tenant config for {tenant_id}: {e}")
            return None
    
    def _get_tier_features(self, tier: TenantTier) -> Set[str]:
        """Get features enabled for tenant tier."""
        base_features = {"invoice_generation", "basic_reporting", "api_access"}
        
        if tier in [TenantTier.PROFESSIONAL, TenantTier.ENTERPRISE, TenantTier.SCALE]:
            base_features.update({"advanced_reporting", "bulk_operations", "webhooks"})
        
        if tier in [TenantTier.ENTERPRISE, TenantTier.SCALE]:
            base_features.update({"custom_integrations", "priority_support", "sla_guarantees"})
        
        if tier == TenantTier.SCALE:
            base_features.update({"dedicated_resources", "custom_deployment", "white_labeling"})
        
        return base_features
    
    def _calculate_shard(self, tenant_id: UUID) -> str:
        """Calculate database shard for tenant (for future sharding)."""
        # Use consistent hashing for shard distribution
        hash_value = int(hashlib.md5(str(tenant_id).encode()).hexdigest(), 16)
        shard_count = 4  # Start with 4 logical shards for future scaling
        shard_index = hash_value % shard_count
        return f"shard_{shard_index:02d}"
    
    def apply_tenant_filter(self, query: Union[Query, Select], model_class=None) -> Union[Query, Select]:
        """
        Apply tenant filtering to SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            model_class: Optional model class for filtering
            
        Returns:
            Query with tenant filtering applied
        """
        organization_id = self.tenant_context.get_organization_id()
        
        if not organization_id:
            logger.warning("No tenant context set for query filtering")
            return query
        
        self._query_stats["tenant_filtered_queries"] += 1
        
        # Apply organization_id filter
        if hasattr(query, 'filter'):
            # SQLAlchemy ORM Query
            if model_class and hasattr(model_class, 'organization_id'):
                return query.filter(model_class.organization_id == organization_id)
            else:
                # Try to apply filter dynamically
                return query.filter(text("organization_id = :org_id")).params(org_id=organization_id)
        else:
            # SQLAlchemy Core Select
            return query.where(text("organization_id = :org_id")).params(org_id=organization_id)
    
    def get_tenant_metrics(self, tenant_id: UUID) -> Optional[TenantMetrics]:
        """Get tenant usage metrics."""
        # Check cache first
        if tenant_id in self._tenant_metrics_cache:
            cached_metrics = self._tenant_metrics_cache[tenant_id]
            # Return if cache is fresh (< 5 minutes)
            if (datetime.utcnow() - cached_metrics.last_updated) < timedelta(minutes=5):
                return cached_metrics
        
        # Load fresh metrics from database
        metrics = self._load_tenant_metrics_from_db(tenant_id)
        if metrics:
            self._tenant_metrics_cache[tenant_id] = metrics
        
        return metrics
    
    def _load_tenant_metrics_from_db(self, tenant_id: UUID) -> Optional[TenantMetrics]:
        """Load tenant metrics from database."""
        try:
            with self.db_layer.get_session() as session:
                # Get invoice count for current month
                current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                invoice_count_result = session.execute(text("""
                    SELECT COUNT(*) as count
                    FROM invoices 
                    WHERE organization_id = :tenant_id 
                    AND created_at >= :month_start
                """), {
                    "tenant_id": tenant_id,
                    "month_start": current_month_start
                })
                
                invoice_count = invoice_count_result.scalar() or 0
                
                # Get active user count
                user_count_result = session.execute(text("""
                    SELECT COUNT(*) as count
                    FROM users 
                    WHERE organization_id = :tenant_id 
                    AND is_active = true
                    AND last_login >= :last_30_days
                """), {
                    "tenant_id": tenant_id,
                    "last_30_days": datetime.utcnow() - timedelta(days=30)
                })
                
                user_count = user_count_result.scalar() or 0
                
                return TenantMetrics(
                    tenant_id=tenant_id,
                    invoice_count_current_month=invoice_count,
                    user_count_active=user_count,
                    storage_usage_mb=0.0,  # Placeholder - calculate from file storage
                    api_requests_last_hour=0,  # Placeholder - get from monitoring
                    cache_hit_ratio=0.0,  # Placeholder - get from cache stats
                    avg_response_time_ms=0.0,  # Placeholder - get from monitoring
                    error_rate_percentage=0.0  # Placeholder - get from error tracking
                )
                
        except Exception as e:
            logger.error(f"Failed to load tenant metrics for {tenant_id}: {e}")
            return None
    
    def check_tenant_limits(self, tenant_id: UUID) -> Dict[str, Any]:
        """Check if tenant is within usage limits."""
        config = self.get_tenant_config(tenant_id)
        metrics = self.get_tenant_metrics(tenant_id)
        
        if not config or not metrics:
            return {"status": "error", "message": "Could not load tenant data"}
        
        limits_status = {
            "status": "ok",
            "limits": {
                "invoices": {
                    "current": metrics.invoice_count_current_month,
                    "limit": config.max_invoices_per_month,
                    "percentage": (metrics.invoice_count_current_month / config.max_invoices_per_month) * 100,
                    "exceeded": metrics.invoice_count_current_month > config.max_invoices_per_month
                },
                "users": {
                    "current": metrics.user_count_active,
                    "limit": config.max_users,
                    "percentage": (metrics.user_count_active / config.max_users) * 100,
                    "exceeded": metrics.user_count_active > config.max_users
                }
            }
        }
        
        # Check if any limits are exceeded
        if any(limit["exceeded"] for limit in limits_status["limits"].values()):
            limits_status["status"] = "exceeded"
        elif any(limit["percentage"] > 80 for limit in limits_status["limits"].values()):
            limits_status["status"] = "warning"
        
        return limits_status
    
    def _update_tenant_last_access_async(self, tenant_id: UUID):
        """Update tenant last access time asynchronously."""
        def update_access():
            try:
                with self.db_layer.get_session() as session:
                    session.execute(text("""
                        UPDATE organizations 
                        SET updated_at = :now 
                        WHERE id = :tenant_id
                    """), {
                        "now": datetime.utcnow(),
                        "tenant_id": tenant_id
                    })
            except Exception as e:
                logger.warning(f"Failed to update tenant last access: {e}")
        
        # Submit to thread pool
        self._executor.submit(update_access)
    
    def get_tenant_health_status(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get comprehensive tenant health status."""
        config = self.get_tenant_config(tenant_id)
        metrics = self.get_tenant_metrics(tenant_id)
        limits = self.check_tenant_limits(tenant_id)
        
        if not config or not metrics:
            return {"status": "error", "message": "Tenant data unavailable"}
        
        health_score = 100
        issues = []
        
        # Check limits
        if limits["status"] == "exceeded":
            health_score -= 40
            issues.append("Usage limits exceeded")
        elif limits["status"] == "warning":
            health_score -= 20
            issues.append("Approaching usage limits")
        
        # Check error rates
        if metrics.error_rate_percentage > 5:
            health_score -= 30
            issues.append("High error rate")
        elif metrics.error_rate_percentage > 1:
            health_score -= 10
            issues.append("Elevated error rate")
        
        # Check response times
        if metrics.avg_response_time_ms > 2000:
            health_score -= 20
            issues.append("Slow response times")
        elif metrics.avg_response_time_ms > 1000:
            health_score -= 10
            issues.append("Degraded performance")
        
        status = "healthy"
        if health_score < 60:
            status = "critical"
        elif health_score < 80:
            status = "degraded"
        elif health_score < 95:
            status = "warning"
        
        return {
            "status": status,
            "health_score": health_score,
            "issues": issues,
            "tenant_tier": config.tier.value,
            "limits": limits["limits"],
            "metrics": asdict(metrics),
            "last_checked": datetime.utcnow().isoformat()
        }
    
    def get_current_service_type(self) -> Optional[ServiceType]:
        """Get current service type from context."""
        return self.tenant_context._context.get("service_type")
    
    def is_si_service(self, tenant_id: Optional[UUID] = None) -> bool:
        """Check if tenant uses SI (System Integrator) service."""
        config = self.get_tenant_config(tenant_id or self.tenant_context.get_tenant_id())
        if config and config.service_types:
            return ServiceType.SI in config.service_types
        return False
    
    def is_app_service(self, tenant_id: Optional[UUID] = None) -> bool:
        """Check if tenant uses APP (Access Point Provider) service."""
        config = self.get_tenant_config(tenant_id or self.tenant_context.get_tenant_id())
        if config and config.service_types:
            return ServiceType.APP in config.service_types
        return False
    
    def is_hybrid_service(self, tenant_id: Optional[UUID] = None) -> bool:
        """Check if tenant uses both SI and APP services."""
        config = self.get_tenant_config(tenant_id or self.tenant_context.get_tenant_id())
        if config and config.service_types:
            return ServiceType.HYBRID in config.service_types or (
                ServiceType.SI in config.service_types and ServiceType.APP in config.service_types
            )
        return False
    
    def get_billing_context(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get billing context for tenant based on service type."""
        config = self.get_tenant_config(tenant_id)
        if not config:
            return {"status": "error", "message": "Tenant not found"}
        
        context = {
            "tenant_id": tenant_id,
            "service_types": [st.value for st in config.service_types],
            "billing_model": {}
        }
        
        # SI billing context
        if ServiceType.SI in config.service_types:
            context["billing_model"]["si"] = {
                "tier": config.billing_tier,
                "status": config.billing_status.value,
                "usage_quotas": config.usage_quotas,
                "next_billing_date": config.next_billing_date.isoformat() if config.next_billing_date else None,
                "monthly_limit": config.monthly_invoice_limit,
                "overage_rate": config.overage_rate_per_invoice
            }
        
        # APP grant context
        if ServiceType.APP in config.service_types:
            context["billing_model"]["app"] = {
                "grant_status": config.grant_status.value,
                "current_milestone": config.current_milestone,
                "taxpayer_count": config.taxpayer_count,
                "milestone_progress": config.milestone_progress,
                "transmission_rate": config.transmission_rate,
                "sectors": config.sector_representation
            }
        
        return context
    
    def update_milestone_progress(self, tenant_id: UUID, milestone_data: Dict[str, Any]) -> bool:
        """Update FIRS milestone progress for APP tenant."""
        config = self.get_tenant_config(tenant_id)
        if not config or ServiceType.APP not in config.service_types:
            return False
        
        try:
            # Update milestone fields
            if "taxpayer_count" in milestone_data:
                config.taxpayer_count = milestone_data["taxpayer_count"]
            if "large_taxpayer_count" in milestone_data:
                config.large_taxpayer_count = milestone_data["large_taxpayer_count"]
            if "sme_taxpayer_count" in milestone_data:
                config.sme_taxpayer_count = milestone_data["sme_taxpayer_count"]
            if "transmission_rate" in milestone_data:
                config.transmission_rate = milestone_data["transmission_rate"]
            if "sector_representation" in milestone_data:
                config.sector_representation = milestone_data["sector_representation"]
            if "compliance_sustained" in milestone_data:
                config.compliance_sustained = milestone_data["compliance_sustained"]
            if "full_validation_completed" in milestone_data:
                config.full_validation_completed = milestone_data["full_validation_completed"]
            
            # Update milestone progress
            config.milestone_progress.update(milestone_data.get("milestone_progress", {}))
            
            # Determine current milestone based on criteria
            config.current_milestone = self._calculate_current_milestone(config)
            
            # Update cache
            self._tenant_config_cache[tenant_id] = config
            
            # Invalidate Redis cache to force reload
            if self.cache_manager:
                cache_key = f"tenant_config:{tenant_id}"
                self.cache_manager.delete(cache_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update milestone progress for {tenant_id}: {e}")
            return False
    
    def _calculate_current_milestone(self, config: TenantConfig) -> Optional[str]:
        """Calculate current milestone based on tenant progress."""
        count = config.taxpayer_count
        transmission_rate = config.transmission_rate or 0
        
        # Milestone 5: 100+ taxpayers with full validation
        if count >= 100 and config.full_validation_completed:
            return "milestone_5"
        
        # Milestone 4: 80+ taxpayers with sustained compliance
        elif count >= 80 and config.compliance_sustained:
            return "milestone_4"
        
        # Milestone 3: 60+ taxpayers with cross-sector representation
        elif count >= 60 and len(config.sector_representation) >= 2:
            return "milestone_3"
        
        # Milestone 2: 40+ taxpayers with Large + SME mix
        elif count >= 40 and config.large_taxpayer_count > 0 and config.sme_taxpayer_count > 0:
            return "milestone_2"
        
        # Milestone 1: 20+ taxpayers with 80% transmission rate
        elif count >= 20 and transmission_rate >= 80.0:
            return "milestone_1"
        
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get tenant manager performance statistics."""
        return {
            "query_stats": self._query_stats.copy(),
            "cache_stats": {
                "tenant_configs_cached": len(self._tenant_config_cache),
                "tenant_metrics_cached": len(self._tenant_metrics_cache)
            },
            "context_status": {
                "has_context": self.tenant_context.is_set(),
                "current_tenant": str(self.tenant_context.get_tenant_id()) if self.tenant_context.is_set() else None
            }
        }
    
    def cleanup_cache(self, max_age_minutes: int = 30):
        """Clean up stale cache entries."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        # Clean tenant config cache
        stale_configs = [
            tenant_id for tenant_id, config in self._tenant_config_cache.items()
            if config.last_accessed_at < cutoff_time
        ]
        
        for tenant_id in stale_configs:
            del self._tenant_config_cache[tenant_id]
        
        # Clean metrics cache  
        stale_metrics = [
            tenant_id for tenant_id, metrics in self._tenant_metrics_cache.items()
            if metrics.last_updated < cutoff_time
        ]
        
        for tenant_id in stale_metrics:
            del self._tenant_metrics_cache[tenant_id]
        
        logger.info(f"Cleaned up {len(stale_configs)} config and {len(stale_metrics)} metrics cache entries")
    
    def close(self):
        """Cleanup resources."""
        if self._executor:
            self._executor.shutdown(wait=True)
        
        self._tenant_config_cache.clear()
        self._tenant_metrics_cache.clear()
        self.tenant_context.clear()


# Global tenant manager instance
_tenant_manager: Optional[MultiTenantManager] = None


def get_tenant_manager() -> Optional[MultiTenantManager]:
    """Get global tenant manager instance."""
    return _tenant_manager


def initialize_tenant_manager(database_layer, cache_manager=None) -> MultiTenantManager:
    """Initialize global tenant manager."""
    global _tenant_manager
    _tenant_manager = MultiTenantManager(database_layer, cache_manager)
    return _tenant_manager