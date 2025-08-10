"""
Billing Repository for SI Commercial Model
Handles subscription management, usage tracking, and billing operations for System Integrator services.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal
from dataclasses import dataclass, asdict
from enum import Enum

from .repository_base import RepositoryBase
from .multi_tenant_manager import ServiceType, BillingStatus

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """SI subscription tiers with pricing and limits."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    SCALE = "scale"


class PaymentStatus(Enum):
    """Payment status for invoices."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class SubscriptionPlan:
    """Subscription plan definition."""
    tier: SubscriptionTier
    monthly_price: Decimal
    invoice_limit: int
    user_limit: int
    api_rate_limit: int
    storage_gb: int
    features: List[str]
    overage_rate: Decimal  # Per invoice above limit


@dataclass
class BillingRecord:
    """Billing record for SI customers."""
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    subscription_tier: SubscriptionTier
    billing_period_start: datetime
    billing_period_end: datetime
    base_amount: Decimal
    usage_amount: Decimal  # Overage charges
    tax_amount: Decimal
    total_amount: Decimal
    invoice_count: int
    overage_invoices: int
    payment_status: PaymentStatus
    payment_date: Optional[datetime] = None
    created_at: datetime = None
    due_date: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.due_date is None:
            self.due_date = self.created_at + timedelta(days=30)


@dataclass
class UsageRecord:
    """Usage tracking record for billing calculations."""
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    usage_date: datetime
    invoice_count: int
    api_calls: int
    storage_usage_mb: float
    feature_usage: Dict[str, Any]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class BillingRepository(RepositoryBase):
    """Repository for SI billing operations."""
    
    # Subscription tier definitions
    SUBSCRIPTION_TIERS = {
        SubscriptionTier.STARTER: SubscriptionPlan(
            tier=SubscriptionTier.STARTER,
            monthly_price=Decimal("50.00"),
            invoice_limit=1000,
            user_limit=5,
            api_rate_limit=100,
            storage_gb=10,
            features=["basic_erp", "standard_support", "basic_analytics"],
            overage_rate=Decimal("0.05")  # $0.05 per invoice
        ),
        SubscriptionTier.PROFESSIONAL: SubscriptionPlan(
            tier=SubscriptionTier.PROFESSIONAL,
            monthly_price=Decimal("200.00"),
            invoice_limit=10000,
            user_limit=25,
            api_rate_limit=500,
            storage_gb=100,
            features=["advanced_erp", "priority_support", "advanced_analytics", "webhooks"],
            overage_rate=Decimal("0.02")  # $0.02 per invoice
        ),
        SubscriptionTier.ENTERPRISE: SubscriptionPlan(
            tier=SubscriptionTier.ENTERPRISE,
            monthly_price=Decimal("800.00"),
            invoice_limit=100000,
            user_limit=100,
            api_rate_limit=2000,
            storage_gb=1000,
            features=["all_features", "dedicated_support", "custom_integrations", "white_label"],
            overage_rate=Decimal("0.008")  # $0.008 per invoice
        ),
        SubscriptionTier.SCALE: SubscriptionPlan(
            tier=SubscriptionTier.SCALE,
            monthly_price=Decimal("2000.00"),
            invoice_limit=1000000,
            user_limit=500,
            api_rate_limit=10000,
            storage_gb=5000,
            features=["enterprise_features", "24_7_support", "custom_deployment", "sla_guarantee"],
            overage_rate=Decimal("0.002")  # $0.002 per invoice
        )
    }
    
    def __init__(self, db_layer, cache_manager=None):
        super().__init__(db_layer, cache_manager)
        self.model_name = "billing"
        self.cache_prefix = "billing"
    
    async def create_subscription(
        self, 
        tenant_id: UUID, 
        organization_id: UUID, 
        tier: SubscriptionTier,
        start_date: datetime = None
    ) -> Dict[str, Any]:
        """Create new SI subscription."""
        try:
            start_date = start_date or datetime.utcnow()
            plan = self.SUBSCRIPTION_TIERS[tier]
            
            with self.db_layer.get_session() as session:
                # Create subscription record
                subscription_data = {
                    "tenant_id": tenant_id,
                    "organization_id": organization_id,
                    "subscription_tier": tier.value,
                    "monthly_price": plan.monthly_price,
                    "invoice_limit": plan.invoice_limit,
                    "user_limit": plan.user_limit,
                    "api_rate_limit": plan.api_rate_limit,
                    "storage_gb": plan.storage_gb,
                    "overage_rate": plan.overage_rate,
                    "features": plan.features,
                    "start_date": start_date,
                    "next_billing_date": start_date + timedelta(days=30),
                    "status": BillingStatus.ACTIVE.value,
                    "created_at": datetime.utcnow()
                }
                
                result = await self._execute_query(
                    "INSERT INTO subscriptions",
                    subscription_data
                )
                
                # Create initial billing record
                billing_record = BillingRecord(
                    id=self._generate_id(),
                    tenant_id=tenant_id,
                    organization_id=organization_id,
                    subscription_tier=tier,
                    billing_period_start=start_date,
                    billing_period_end=start_date + timedelta(days=30),
                    base_amount=plan.monthly_price,
                    usage_amount=Decimal("0.00"),
                    tax_amount=Decimal("0.00"),
                    total_amount=plan.monthly_price,
                    invoice_count=0,
                    overage_invoices=0,
                    payment_status=PaymentStatus.PENDING
                )
                
                await self.create_billing_record(billing_record)
                
                # Invalidate cache
                await self._invalidate_cache(f"subscription:{tenant_id}")
                
                return {
                    "status": "success",
                    "subscription_id": result.get("id"),
                    "plan": asdict(plan),
                    "next_billing_date": subscription_data["next_billing_date"]
                }
                
        except Exception as e:
            logger.error(f"Failed to create subscription for {tenant_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_subscription(self, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current subscription for tenant."""
        try:
            # Check cache first
            cache_key = f"subscription:{tenant_id}"
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            with self.db_layer.get_session() as session:
                result = await self._execute_query(
                    "SELECT * FROM subscriptions WHERE tenant_id = :tenant_id AND status = 'active'",
                    {"tenant_id": tenant_id}
                )
                
                if result:
                    subscription = dict(result)
                    # Cache for 1 hour
                    await self._set_cache(cache_key, subscription, ttl=3600)
                    return subscription
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get subscription for {tenant_id}: {e}")
            return None
    
    async def record_usage(
        self, 
        tenant_id: UUID, 
        organization_id: UUID,
        invoice_count: int = 0,
        api_calls: int = 0,
        storage_usage_mb: float = 0.0,
        feature_usage: Dict[str, Any] = None
    ) -> bool:
        """Record usage for billing calculations."""
        try:
            usage_record = UsageRecord(
                id=self._generate_id(),
                tenant_id=tenant_id,
                organization_id=organization_id,
                usage_date=datetime.utcnow(),
                invoice_count=invoice_count,
                api_calls=api_calls,
                storage_usage_mb=storage_usage_mb,
                feature_usage=feature_usage or {}
            )
            
            with self.db_layer.get_session() as session:
                await self._execute_query(
                    "INSERT INTO usage_records",
                    asdict(usage_record)
                )
                
                # Invalidate usage cache
                await self._invalidate_cache(f"usage:{tenant_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to record usage for {tenant_id}: {e}")
            return False
    
    async def calculate_monthly_bill(
        self, 
        tenant_id: UUID, 
        billing_period_start: datetime,
        billing_period_end: datetime
    ) -> Optional[BillingRecord]:
        """Calculate monthly bill based on usage."""
        try:
            subscription = await self.get_subscription(tenant_id)
            if not subscription:
                return None
            
            # Get usage for billing period
            usage_stats = await self.get_usage_stats(
                tenant_id, 
                billing_period_start, 
                billing_period_end
            )
            
            tier = SubscriptionTier(subscription["subscription_tier"])
            plan = self.SUBSCRIPTION_TIERS[tier]
            
            # Calculate base and overage charges
            base_amount = plan.monthly_price
            total_invoices = usage_stats.get("total_invoices", 0)
            overage_invoices = max(0, total_invoices - plan.invoice_limit)
            usage_amount = Decimal(str(overage_invoices)) * plan.overage_rate
            
            # Calculate tax (8% for example)
            subtotal = base_amount + usage_amount
            tax_amount = subtotal * Decimal("0.08")
            total_amount = subtotal + tax_amount
            
            billing_record = BillingRecord(
                id=self._generate_id(),
                tenant_id=tenant_id,
                organization_id=UUID(subscription["organization_id"]),
                subscription_tier=tier,
                billing_period_start=billing_period_start,
                billing_period_end=billing_period_end,
                base_amount=base_amount,
                usage_amount=usage_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                invoice_count=total_invoices,
                overage_invoices=overage_invoices,
                payment_status=PaymentStatus.PENDING
            )
            
            return billing_record
            
        except Exception as e:
            logger.error(f"Failed to calculate bill for {tenant_id}: {e}")
            return None
    
    async def create_billing_record(self, billing_record: BillingRecord) -> bool:
        """Create billing record in database."""
        try:
            with self.db_layer.get_session() as session:
                await self._execute_query(
                    "INSERT INTO billing_records",
                    asdict(billing_record)
                )
                
                # Invalidate cache
                await self._invalidate_cache(f"billing:{billing_record.tenant_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to create billing record: {e}")
            return False
    
    async def get_usage_stats(
        self, 
        tenant_id: UUID, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage statistics for billing period."""
        try:
            with self.db_layer.get_session() as session:
                result = await self._execute_query("""
                    SELECT 
                        SUM(invoice_count) as total_invoices,
                        SUM(api_calls) as total_api_calls,
                        AVG(storage_usage_mb) as avg_storage_usage,
                        COUNT(*) as usage_records
                    FROM usage_records 
                    WHERE tenant_id = :tenant_id 
                    AND usage_date >= :start_date 
                    AND usage_date <= :end_date
                """, {
                    "tenant_id": tenant_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                return dict(result) if result else {}
                
        except Exception as e:
            logger.error(f"Failed to get usage stats for {tenant_id}: {e}")
            return {}
    
    async def update_payment_status(
        self, 
        billing_record_id: UUID, 
        status: PaymentStatus,
        payment_date: datetime = None
    ) -> bool:
        """Update payment status for billing record."""
        try:
            with self.db_layer.get_session() as session:
                update_data = {
                    "payment_status": status.value,
                    "payment_date": payment_date or datetime.utcnow()
                }
                
                await self._execute_query(
                    f"UPDATE billing_records SET payment_status = :payment_status, payment_date = :payment_date WHERE id = :id",
                    {**update_data, "id": billing_record_id}
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update payment status: {e}")
            return False
    
    async def get_billing_history(
        self, 
        tenant_id: UUID, 
        limit: int = 12
    ) -> List[Dict[str, Any]]:
        """Get billing history for tenant."""
        try:
            with self.db_layer.get_session() as session:
                results = await self._execute_query("""
                    SELECT * FROM billing_records 
                    WHERE tenant_id = :tenant_id 
                    ORDER BY billing_period_start DESC 
                    LIMIT :limit
                """, {
                    "tenant_id": tenant_id,
                    "limit": limit
                })
                
                return [dict(row) for row in results] if results else []
                
        except Exception as e:
            logger.error(f"Failed to get billing history for {tenant_id}: {e}")
            return []
    
    async def get_subscription_metrics(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get subscription metrics and analytics."""
        try:
            subscription = await self.get_subscription(tenant_id)
            if not subscription:
                return {}
            
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_month_end = datetime.utcnow()
            
            usage_stats = await self.get_usage_stats(tenant_id, current_month_start, current_month_end)
            plan = self.SUBSCRIPTION_TIERS[SubscriptionTier(subscription["subscription_tier"])]
            
            invoice_usage_pct = (usage_stats.get("total_invoices", 0) / plan.invoice_limit) * 100
            
            return {
                "subscription_tier": subscription["subscription_tier"],
                "monthly_price": float(subscription["monthly_price"]),
                "current_usage": {
                    "invoices": usage_stats.get("total_invoices", 0),
                    "invoice_limit": plan.invoice_limit,
                    "usage_percentage": min(invoice_usage_pct, 100),
                    "api_calls": usage_stats.get("total_api_calls", 0),
                    "storage_usage_mb": usage_stats.get("avg_storage_usage", 0)
                },
                "next_billing_date": subscription["next_billing_date"],
                "status": subscription["status"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscription metrics for {tenant_id}: {e}")
            return {}