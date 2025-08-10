"""
Grant Tracking Repository for FIRS Milestone Management
Handles FIRS grant milestone tracking for Access Point Provider (APP) services.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
from dataclasses import dataclass, asdict
from enum import Enum

from .repository_base import RepositoryBase
from .multi_tenant_manager import ServiceType, GrantStatus

logger = logging.getLogger(__name__)


class MilestoneType(Enum):
    """FIRS milestone types."""
    MILESTONE_1 = "milestone_1"  # 20 taxpayers, 80% active
    MILESTONE_2 = "milestone_2"  # 40 taxpayers, Large + SME
    MILESTONE_3 = "milestone_3"  # 60 taxpayers, cross-sector
    MILESTONE_4 = "milestone_4"  # 80 taxpayers, sustained compliance
    MILESTONE_5 = "milestone_5"  # 100 taxpayers, full validation


class TaxpayerSize(Enum):
    """Taxpayer size classification."""
    LARGE = "large"      # Large taxpayers
    SME = "sme"          # Small and Medium Enterprises


class ComplianceStatus(Enum):
    """Compliance status for milestone tracking."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"


@dataclass
class MilestoneDefinition:
    """FIRS milestone definition with requirements."""
    milestone_type: MilestoneType
    taxpayer_threshold: int
    requirements: Dict[str, Any]
    grant_amount: float  # FIRS grant amount for this milestone
    description: str


@dataclass
class TaxpayerRecord:
    """Taxpayer record for milestone tracking."""
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    taxpayer_tin: str
    taxpayer_name: str
    taxpayer_size: TaxpayerSize
    sector: str
    onboard_date: datetime
    last_transmission: Optional[datetime] = None
    transmission_count: int = 0
    compliance_status: ComplianceStatus = ComplianceStatus.PENDING
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class MilestoneProgress:
    """Milestone progress tracking."""
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    milestone_type: MilestoneType
    target_date: datetime
    current_taxpayer_count: int
    required_taxpayer_count: int
    large_taxpayer_count: int
    sme_taxpayer_count: int
    sector_count: int
    required_sectors: int
    transmission_rate: float
    required_transmission_rate: float
    compliance_sustained: bool
    validation_completed: bool
    achievement_date: Optional[datetime] = None
    grant_claimed: bool = False
    grant_amount: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class GrantTrackingRepository(RepositoryBase):
    """Repository for FIRS grant milestone tracking."""
    
    # FIRS milestone definitions
    MILESTONE_DEFINITIONS = {
        MilestoneType.MILESTONE_1: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_1,
            taxpayer_threshold=20,
            requirements={
                "transmission_rate": 80.0,
                "active_taxpayers": True,
                "timeframe_months": 6
            },
            grant_amount=50000.0,  # Example amount
            description="20 taxpayers with 80% transmission rate"
        ),
        MilestoneType.MILESTONE_2: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_2,
            taxpayer_threshold=40,
            requirements={
                "large_taxpayers": True,
                "sme_taxpayers": True,
                "transmission_rate": 80.0
            },
            grant_amount=100000.0,
            description="40 taxpayers with Large + SME representation"
        ),
        MilestoneType.MILESTONE_3: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_3,
            taxpayer_threshold=60,
            requirements={
                "cross_sector": True,
                "min_sectors": 2,
                "transmission_rate": 80.0
            },
            grant_amount=200000.0,
            description="60 taxpayers with cross-sector representation"
        ),
        MilestoneType.MILESTONE_4: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_4,
            taxpayer_threshold=80,
            requirements={
                "sustained_compliance": True,
                "compliance_period_months": 6,
                "transmission_rate": 80.0
            },
            grant_amount=400000.0,
            description="80 taxpayers with sustained compliance"
        ),
        MilestoneType.MILESTONE_5: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_5,
            taxpayer_threshold=100,
            requirements={
                "full_validation": True,
                "transmission_rate": 80.0,
                "all_previous_milestones": True
            },
            grant_amount=800000.0,
            description="100 taxpayers with full validation"
        )
    }
    
    def __init__(self, db_layer, cache_manager=None):
        super().__init__(db_layer, cache_manager)
        self.model_name = "grant_tracking"
        self.cache_prefix = "grant"
    
    async def register_taxpayer(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        taxpayer_tin: str,
        taxpayer_name: str,
        taxpayer_size: TaxpayerSize,
        sector: str
    ) -> Dict[str, Any]:
        """Register new taxpayer for milestone tracking."""
        try:
            taxpayer_record = TaxpayerRecord(
                id=self._generate_id(),
                tenant_id=tenant_id,
                organization_id=organization_id,
                taxpayer_tin=taxpayer_tin,
                taxpayer_name=taxpayer_name,
                taxpayer_size=taxpayer_size,
                sector=sector,
                onboard_date=datetime.utcnow()
            )
            
            with self.db_layer.get_session() as session:
                await self._execute_query(
                    "INSERT INTO taxpayer_records",
                    asdict(taxpayer_record)
                )
                
                # Update milestone progress
                await self._recalculate_milestone_progress(tenant_id)
                
                # Invalidate cache
                await self._invalidate_cache(f"taxpayers:{tenant_id}")
                
                return {
                    "status": "success",
                    "taxpayer_id": taxpayer_record.id,
                    "message": "Taxpayer registered successfully"
                }
                
        except Exception as e:
            logger.error(f"Failed to register taxpayer for {tenant_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def record_transmission(
        self,
        tenant_id: UUID,
        taxpayer_tin: str,
        transmission_count: int = 1
    ) -> bool:
        """Record invoice transmission for taxpayer."""
        try:
            with self.db_layer.get_session() as session:
                # Update taxpayer transmission data
                await self._execute_query("""
                    UPDATE taxpayer_records 
                    SET 
                        last_transmission = :now,
                        transmission_count = transmission_count + :count
                    WHERE tenant_id = :tenant_id 
                    AND taxpayer_tin = :tin
                """, {
                    "now": datetime.utcnow(),
                    "count": transmission_count,
                    "tenant_id": tenant_id,
                    "tin": taxpayer_tin
                })
                
                # Recalculate milestone progress
                await self._recalculate_milestone_progress(tenant_id)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to record transmission for {tenant_id}: {e}")
            return False
    
    async def get_milestone_progress(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get current milestone progress for tenant."""
        try:
            # Check cache first
            cache_key = f"milestone_progress:{tenant_id}"
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            progress_data = {}
            
            for milestone_type in MilestoneType:
                milestone_progress = await self._get_milestone_progress(tenant_id, milestone_type)
                if milestone_progress:
                    progress_data[milestone_type.value] = asdict(milestone_progress)
            
            # Cache for 30 minutes
            await self._set_cache(cache_key, progress_data, ttl=1800)
            
            return progress_data
            
        except Exception as e:
            logger.error(f"Failed to get milestone progress for {tenant_id}: {e}")
            return {}
    
    async def _get_milestone_progress(
        self, 
        tenant_id: UUID, 
        milestone_type: MilestoneType
    ) -> Optional[MilestoneProgress]:
        """Get specific milestone progress."""
        try:
            with self.db_layer.get_session() as session:
                result = await self._execute_query("""
                    SELECT * FROM milestone_progress 
                    WHERE tenant_id = :tenant_id 
                    AND milestone_type = :milestone_type
                """, {
                    "tenant_id": tenant_id,
                    "milestone_type": milestone_type.value
                })
                
                if result:
                    data = dict(result)
                    data["milestone_type"] = MilestoneType(data["milestone_type"])
                    return MilestoneProgress(**data)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get milestone progress: {e}")
            return None
    
    async def _recalculate_milestone_progress(self, tenant_id: UUID) -> bool:
        """Recalculate milestone progress based on current taxpayer data."""
        try:
            # Get current taxpayer statistics
            taxpayer_stats = await self._get_taxpayer_statistics(tenant_id)
            
            # Calculate progress for each milestone
            for milestone_type, definition in self.MILESTONE_DEFINITIONS.items():
                progress = await self._calculate_milestone_progress(
                    tenant_id, 
                    milestone_type, 
                    definition, 
                    taxpayer_stats
                )
                
                await self._update_milestone_progress(tenant_id, progress)
            
            # Invalidate cache
            await self._invalidate_cache(f"milestone_progress:{tenant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to recalculate milestone progress for {tenant_id}: {e}")
            return False
    
    async def _get_taxpayer_statistics(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get comprehensive taxpayer statistics."""
        try:
            with self.db_layer.get_session() as session:
                # Get basic counts
                result = await self._execute_query("""
                    SELECT 
                        COUNT(*) as total_taxpayers,
                        COUNT(CASE WHEN taxpayer_size = 'large' THEN 1 END) as large_count,
                        COUNT(CASE WHEN taxpayer_size = 'sme' THEN 1 END) as sme_count,
                        COUNT(DISTINCT sector) as sector_count,
                        COUNT(CASE WHEN last_transmission >= :active_threshold THEN 1 END) as active_taxpayers
                    FROM taxpayer_records 
                    WHERE tenant_id = :tenant_id 
                    AND is_active = true
                """, {
                    "tenant_id": tenant_id,
                    "active_threshold": datetime.utcnow() - timedelta(days=30)
                })
                
                stats = dict(result)
                
                # Calculate transmission rate
                if stats["total_taxpayers"] > 0:
                    transmission_rate = (stats["active_taxpayers"] / stats["total_taxpayers"]) * 100
                else:
                    transmission_rate = 0.0
                
                stats["transmission_rate"] = transmission_rate
                
                # Get sector list
                sector_result = await self._execute_query("""
                    SELECT DISTINCT sector 
                    FROM taxpayer_records 
                    WHERE tenant_id = :tenant_id 
                    AND is_active = true
                """, {"tenant_id": tenant_id})
                
                stats["sectors"] = [row["sector"] for row in sector_result] if sector_result else []
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get taxpayer statistics: {e}")
            return {}
    
    async def _calculate_milestone_progress(
        self,
        tenant_id: UUID,
        milestone_type: MilestoneType,
        definition: MilestoneDefinition,
        taxpayer_stats: Dict[str, Any]
    ) -> MilestoneProgress:
        """Calculate milestone progress based on requirements."""
        total_taxpayers = taxpayer_stats.get("total_taxpayers", 0)
        large_count = taxpayer_stats.get("large_count", 0)
        sme_count = taxpayer_stats.get("sme_count", 0)
        sector_count = taxpayer_stats.get("sector_count", 0)
        transmission_rate = taxpayer_stats.get("transmission_rate", 0.0)
        
        # Check milestone-specific requirements
        compliance_sustained = await self._check_sustained_compliance(tenant_id)
        validation_completed = await self._check_full_validation(tenant_id)
        
        # Determine if milestone is achieved
        achievement_date = None
        if milestone_type == MilestoneType.MILESTONE_1:
            if total_taxpayers >= 20 and transmission_rate >= 80.0:
                achievement_date = datetime.utcnow()
        elif milestone_type == MilestoneType.MILESTONE_2:
            if total_taxpayers >= 40 and large_count > 0 and sme_count > 0:
                achievement_date = datetime.utcnow()
        elif milestone_type == MilestoneType.MILESTONE_3:
            if total_taxpayers >= 60 and sector_count >= 2:
                achievement_date = datetime.utcnow()
        elif milestone_type == MilestoneType.MILESTONE_4:
            if total_taxpayers >= 80 and compliance_sustained:
                achievement_date = datetime.utcnow()
        elif milestone_type == MilestoneType.MILESTONE_5:
            if total_taxpayers >= 100 and validation_completed:
                achievement_date = datetime.utcnow()
        
        return MilestoneProgress(
            id=self._generate_id(),
            tenant_id=tenant_id,
            organization_id=tenant_id,  # Assuming same for simplicity
            milestone_type=milestone_type,
            target_date=datetime.utcnow() + timedelta(days=180),  # 6 months target
            current_taxpayer_count=total_taxpayers,
            required_taxpayer_count=definition.taxpayer_threshold,
            large_taxpayer_count=large_count,
            sme_taxpayer_count=sme_count,
            sector_count=sector_count,
            required_sectors=definition.requirements.get("min_sectors", 1),
            transmission_rate=transmission_rate,
            required_transmission_rate=definition.requirements.get("transmission_rate", 80.0),
            compliance_sustained=compliance_sustained,
            validation_completed=validation_completed,
            achievement_date=achievement_date,
            grant_amount=definition.grant_amount if achievement_date else None
        )
    
    async def _check_sustained_compliance(self, tenant_id: UUID) -> bool:
        """Check if tenant has sustained compliance for 6 months."""
        try:
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            
            with self.db_layer.get_session() as session:
                result = await self._execute_query("""
                    SELECT COUNT(*) as compliant_count
                    FROM taxpayer_records 
                    WHERE tenant_id = :tenant_id 
                    AND compliance_status = 'compliant'
                    AND last_transmission >= :threshold
                """, {
                    "tenant_id": tenant_id,
                    "threshold": six_months_ago
                })
                
                compliant_count = result.get("compliant_count", 0) if result else 0
                return compliant_count >= 80  # Threshold for sustained compliance
                
        except Exception as e:
            logger.error(f"Failed to check sustained compliance: {e}")
            return False
    
    async def _check_full_validation(self, tenant_id: UUID) -> bool:
        """Check if tenant has completed full validation requirements."""
        try:
            # Check if all previous milestones are achieved
            previous_milestones = [
                MilestoneType.MILESTONE_1,
                MilestoneType.MILESTONE_2,
                MilestoneType.MILESTONE_3,
                MilestoneType.MILESTONE_4
            ]
            
            for milestone in previous_milestones:
                progress = await self._get_milestone_progress(tenant_id, milestone)
                if not progress or not progress.achievement_date:
                    return False
            
            # Additional validation checks can be added here
            return True
            
        except Exception as e:
            logger.error(f"Failed to check full validation: {e}")
            return False
    
    async def _update_milestone_progress(
        self, 
        tenant_id: UUID, 
        progress: MilestoneProgress
    ) -> bool:
        """Update milestone progress in database."""
        try:
            with self.db_layer.get_session() as session:
                # Check if record exists
                existing = await self._get_milestone_progress(tenant_id, progress.milestone_type)
                
                if existing:
                    # Update existing record
                    progress.id = existing.id
                    progress.created_at = existing.created_at
                    progress.updated_at = datetime.utcnow()
                    
                    await self._execute_query(
                        "UPDATE milestone_progress SET ... WHERE id = :id",
                        asdict(progress)
                    )
                else:
                    # Create new record
                    await self._execute_query(
                        "INSERT INTO milestone_progress",
                        asdict(progress)
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update milestone progress: {e}")
            return False
    
    async def get_grant_summary(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get grant summary and achievement status."""
        try:
            progress_data = await self.get_milestone_progress(tenant_id)
            
            summary = {
                "total_potential_grants": sum(d.grant_amount for d in self.MILESTONE_DEFINITIONS.values()),
                "achieved_grants": 0.0,
                "pending_grants": 0.0,
                "milestones": {},
                "next_milestone": None,
                "progress_percentage": 0.0
            }
            
            achieved_count = 0
            total_milestones = len(self.MILESTONE_DEFINITIONS)
            
            for milestone_type, definition in self.MILESTONE_DEFINITIONS.items():
                milestone_key = milestone_type.value
                progress = progress_data.get(milestone_key)
                
                if progress and progress.get("achievement_date"):
                    summary["achieved_grants"] += definition.grant_amount
                    achieved_count += 1
                    status = "achieved"
                else:
                    summary["pending_grants"] += definition.grant_amount
                    status = "pending"
                    if not summary["next_milestone"]:
                        summary["next_milestone"] = milestone_key
                
                summary["milestones"][milestone_key] = {
                    "status": status,
                    "grant_amount": definition.grant_amount,
                    "description": definition.description,
                    "progress": progress
                }
            
            summary["progress_percentage"] = (achieved_count / total_milestones) * 100
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get grant summary for {tenant_id}: {e}")
            return {}
    
    async def get_taxpayer_analytics(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get taxpayer analytics for dashboard."""
        try:
            stats = await self._get_taxpayer_statistics(tenant_id)
            
            # Get onboarding trends (last 6 months)
            monthly_onboarding = await self._get_monthly_onboarding_trends(tenant_id)
            
            return {
                "total_taxpayers": stats.get("total_taxpayers", 0),
                "large_taxpayers": stats.get("large_count", 0),
                "sme_taxpayers": stats.get("sme_count", 0),
                "sectors_represented": stats.get("sector_count", 0),
                "transmission_rate": stats.get("transmission_rate", 0.0),
                "active_taxpayers": stats.get("active_taxpayers", 0),
                "onboarding_trends": monthly_onboarding,
                "sector_breakdown": stats.get("sectors", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get taxpayer analytics: {e}")
            return {}
    
    async def _get_monthly_onboarding_trends(self, tenant_id: UUID) -> List[Dict[str, Any]]:
        """Get monthly taxpayer onboarding trends."""
        try:
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            
            with self.db_layer.get_session() as session:
                results = await self._execute_query("""
                    SELECT 
                        DATE_TRUNC('month', onboard_date) as month,
                        COUNT(*) as onboarded_count,
                        COUNT(CASE WHEN taxpayer_size = 'large' THEN 1 END) as large_count,
                        COUNT(CASE WHEN taxpayer_size = 'sme' THEN 1 END) as sme_count
                    FROM taxpayer_records 
                    WHERE tenant_id = :tenant_id 
                    AND onboard_date >= :start_date
                    GROUP BY DATE_TRUNC('month', onboard_date)
                    ORDER BY month
                """, {
                    "tenant_id": tenant_id,
                    "start_date": six_months_ago
                })
                
                return [dict(row) for row in results] if results else []
                
        except Exception as e:
            logger.error(f"Failed to get onboarding trends: {e}")
            return []