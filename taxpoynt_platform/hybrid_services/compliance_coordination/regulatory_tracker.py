"""
Hybrid Service: Regulatory Tracker
Tracks regulatory changes and updates compliance requirements
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib

from core_platform.database import get_db_session
from core_platform.models.regulatory import RegulatoryChange, RegulatorySubscription, RegulatoryNotification
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService
from core_platform.data_management.grant_tracking_repository import GrantTrackingRepository
from hybrid_services.analytics_aggregation.kpi_calculator import KPICalculator

logger = logging.getLogger(__name__)


class RegulatorySource(str, Enum):
    """Regulatory information sources"""
    FIRS = "firs"
    CAC = "cac"
    PENCOM = "pencom"
    CBN = "cbn"
    NAICOM = "naicom"
    SEC = "sec"
    NITDA = "nitda"
    INTERNAL = "internal"
    EXTERNAL_FEED = "external_feed"


class ChangeType(str, Enum):
    """Types of regulatory changes"""
    NEW_REGULATION = "new_regulation"
    REGULATION_UPDATE = "regulation_update"
    REGULATION_REVOCATION = "regulation_revocation"
    COMPLIANCE_DEADLINE = "compliance_deadline"
    TECHNICAL_SPECIFICATION = "technical_specification"
    OPERATIONAL_GUIDELINE = "operational_guideline"
    REPORTING_REQUIREMENT = "reporting_requirement"
    PENALTY_STRUCTURE = "penalty_structure"


class ImpactLevel(str, Enum):
    """Impact levels for regulatory changes"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ChangeStatus(str, Enum):
    """Status of regulatory changes"""
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    EFFECTIVE = "effective"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class NotificationStatus(str, Enum):
    """Notification status"""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    ACTIONED = "actioned"
    EXPIRED = "expired"


class FIRSGrantMilestone(str, Enum):
    """FIRS Grant milestones"""
    MILESTONE_1 = "milestone_1"  # 20 users, 80% active
    MILESTONE_2 = "milestone_2"  # 40 users, large + SME
    MILESTONE_3 = "milestone_3"  # 60 users, cross-sector
    MILESTONE_4 = "milestone_4"  # 80 users, sustained compliance
    MILESTONE_5 = "milestone_5"  # 100 users, full validation


class FIRSGrantStatus(str, Enum):
    """FIRS Grant status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    MILESTONE_ACHIEVED = "milestone_achieved"
    GRANT_COMPLETED = "grant_completed"
    AT_RISK = "at_risk"
    NON_COMPLIANT = "non_compliant"


class ComplianceRiskLevel(str, Enum):
    """Compliance risk levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RegulatoryChange:
    """Regulatory change record"""
    change_id: str
    source: RegulatorySource
    change_type: ChangeType
    title: str
    description: str
    impact_level: ImpactLevel
    status: ChangeStatus
    affected_services: List[str]
    compliance_deadline: Optional[datetime]
    effective_date: datetime
    published_date: datetime
    reference_number: Optional[str]
    document_url: Optional[str]
    details: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RegulatorySubscription:
    """Regulatory subscription"""
    subscription_id: str
    subscriber_id: str
    subscriber_type: str  # 'service', 'user', 'system'
    sources: List[RegulatorySource]
    change_types: List[ChangeType]
    impact_levels: List[ImpactLevel]
    notification_methods: List[str]
    filters: Dict[str, Any]
    active: bool
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RegulatoryNotification:
    """Regulatory notification"""
    notification_id: str
    change_id: str
    subscription_id: str
    subscriber_id: str
    title: str
    message: str
    priority: str
    status: NotificationStatus
    delivery_method: str
    created_at: datetime
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceGap:
    """Compliance gap analysis"""
    gap_id: str
    change_id: str
    affected_service: str
    gap_type: str
    description: str
    current_state: str
    required_state: str
    remediation_steps: List[str]
    estimated_effort: str
    deadline: datetime
    priority: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceStatus:
    """Compliance status tracking"""
    status_id: str
    change_id: str
    service_name: str
    compliance_percentage: float
    status: str
    last_assessed: datetime
    next_assessment: datetime
    gaps: List[ComplianceGap]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FIRSGrantRule:
    """FIRS Grant compliance rule"""
    rule_id: str
    milestone: FIRSGrantMilestone
    rule_type: str  # 'user_count', 'activity_rate', 'sector_diversity', 'transmission_rate'
    description: str
    requirement: Dict[str, Any]  # Specific requirements
    validation_logic: str  # How to validate compliance
    priority: str
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FIRSMilestoneStatus:
    """TaxPoynt's FIRS Grant Milestone status tracking"""
    milestone_id: str
    service_provider: str  # "taxpoynt"
    milestone: FIRSGrantMilestone
    status: FIRSGrantStatus
    progress_percentage: float
    requirements_met: List[str]
    requirements_pending: List[str]
    target_date: Optional[datetime]
    actual_completion_date: Optional[datetime]
    risk_level: ComplianceRiskLevel
    risk_factors: List[str]
    action_items: List[str]
    compliance_score: float
    last_assessed: datetime
    next_assessment: datetime
    # Grant-specific metrics
    taxpayers_onboarded: int
    active_transmission_rate: float
    sector_diversity_score: float
    large_taxpayer_count: int
    sme_taxpayer_count: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GrantEligibilityAssessment:
    """TaxPoynt's FIRS Grant eligibility assessment"""
    assessment_id: str
    service_provider: str  # "taxpoynt"
    assessed_at: datetime
    eligibility_score: float
    eligible_milestones: List[FIRSGrantMilestone]
    current_performance: Dict[str, Any]  # Current taxpayer onboarding metrics
    readiness_factors: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    estimated_timeline: Dict[str, int]  # milestone -> days
    grant_payment_projection: Dict[str, float]  # milestone -> projected payment
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MilestoneNotification:
    """Milestone-specific notification"""
    notification_id: str
    organization_id: str
    milestone: FIRSGrantMilestone
    notification_type: str  # 'milestone_achieved', 'at_risk', 'deadline_approaching', 'requirement_change'
    title: str
    message: str
    priority: str
    status: NotificationStatus
    delivery_method: str
    created_at: datetime
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    action_required: bool
    action_deadline: Optional[datetime]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RegulatoryTracker:
    """Regulatory tracking and monitoring service"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.grant_tracking_repository = GrantTrackingRepository()
        self.kpi_calculator = KPICalculator()
        self.logger = logging.getLogger(__name__)
        
        # Regulatory changes registry
        self.regulatory_changes: Dict[str, RegulatoryChange] = {}
        
        # Subscriptions registry
        self.subscriptions: Dict[str, RegulatorySubscription] = {}
        
        # Notifications registry
        self.notifications: Dict[str, RegulatoryNotification] = {}
        
        # Compliance status tracking
        self.compliance_status: Dict[str, ComplianceStatus] = {}
        
        # Source connectors
        self.source_connectors: Dict[RegulatorySource, Any] = {}
        
        # FIRS Grant tracking registries
        self.firs_grant_rules: Dict[str, FIRSGrantRule] = {}
        self.milestone_statuses: Dict[str, FIRSMilestoneStatus] = {}
        self.eligibility_assessments: Dict[str, GrantEligibilityAssessment] = {}
        self.milestone_notifications: Dict[str, MilestoneNotification] = {}
        
        # Monitoring configuration
        self.monitoring_config = {
            "check_interval": 3600,  # 1 hour
            "notification_delay": 300,  # 5 minutes
            "max_retries": 3,
            "milestone_check_interval": 1800,  # 30 minutes
            "grant_assessment_interval": 86400  # 24 hours
        }
        
        # Initialize default subscriptions and FIRS grant rules
        self._initialize_default_subscriptions()
        self._initialize_firs_grant_rules()
    
    async def register_regulatory_change(self, change: RegulatoryChange) -> bool:
        """Register a new regulatory change"""
        try:
            # Validate change
            if not await self._validate_regulatory_change(change):
                raise ValueError(f"Invalid regulatory change: {change.change_id}")
            
            # Store change
            self.regulatory_changes[change.change_id] = change
            
            # Cache change
            await self.cache_service.set(
                f"regulatory_change:{change.change_id}",
                change.to_dict(),
                ttl=86400 * 7  # 7 days
            )
            
            # Analyze impact
            impact_analysis = await self._analyze_change_impact(change)
            
            # Identify compliance gaps
            compliance_gaps = await self._identify_compliance_gaps(change)
            
            # Notify subscribers
            await self._notify_subscribers(change)
            
            # Update compliance status
            await self._update_compliance_status(change, compliance_gaps)
            
            # Emit event
            await self.event_bus.emit("regulatory_change_registered", {
                "change_id": change.change_id,
                "source": change.source,
                "change_type": change.change_type,
                "impact_level": change.impact_level,
                "affected_services": change.affected_services,
                "compliance_deadline": change.compliance_deadline.isoformat() if change.compliance_deadline else None,
                "impact_analysis": impact_analysis,
                "compliance_gaps": len(compliance_gaps),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Regulatory change registered: {change.change_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering regulatory change: {str(e)}")
            raise
    
    async def create_subscription(
        self,
        subscriber_id: str,
        subscriber_type: str,
        sources: List[RegulatorySource],
        change_types: List[ChangeType],
        impact_levels: List[ImpactLevel],
        notification_methods: List[str],
        filters: Dict[str, Any] = None
    ) -> RegulatorySubscription:
        """Create a regulatory subscription"""
        try:
            subscription_id = str(uuid.uuid4())
            
            # Create subscription
            subscription = RegulatorySubscription(
                subscription_id=subscription_id,
                subscriber_id=subscriber_id,
                subscriber_type=subscriber_type,
                sources=sources,
                change_types=change_types,
                impact_levels=impact_levels,
                notification_methods=notification_methods,
                filters=filters or {},
                active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Store subscription
            self.subscriptions[subscription_id] = subscription
            
            # Cache subscription
            await self.cache_service.set(
                f"regulatory_subscription:{subscription_id}",
                subscription.to_dict(),
                ttl=86400  # 24 hours
            )
            
            # Emit event
            await self.event_bus.emit("regulatory_subscription_created", {
                "subscription_id": subscription_id,
                "subscriber_id": subscriber_id,
                "subscriber_type": subscriber_type,
                "sources": sources,
                "change_types": change_types,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Regulatory subscription created: {subscription_id}")
            return subscription
            
        except Exception as e:
            self.logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    async def update_subscription(
        self,
        subscription_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a regulatory subscription"""
        try:
            if subscription_id not in self.subscriptions:
                return False
            
            subscription = self.subscriptions[subscription_id]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(subscription, field):
                    setattr(subscription, field, value)
            
            subscription.updated_at = datetime.now(timezone.utc)
            
            # Update cache
            await self.cache_service.set(
                f"regulatory_subscription:{subscription_id}",
                subscription.to_dict(),
                ttl=86400
            )
            
            # Emit event
            await self.event_bus.emit("regulatory_subscription_updated", {
                "subscription_id": subscription_id,
                "updates": updates,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating subscription: {str(e)}")
            return False
    
    async def get_regulatory_changes(
        self,
        source: Optional[RegulatorySource] = None,
        change_type: Optional[ChangeType] = None,
        impact_level: Optional[ImpactLevel] = None,
        status: Optional[ChangeStatus] = None,
        date_range: Optional[tuple] = None,
        limit: int = 100
    ) -> List[RegulatoryChange]:
        """Get regulatory changes with filters"""
        try:
            changes = list(self.regulatory_changes.values())
            
            # Apply filters
            if source:
                changes = [c for c in changes if c.source == source]
            
            if change_type:
                changes = [c for c in changes if c.change_type == change_type]
            
            if impact_level:
                changes = [c for c in changes if c.impact_level == impact_level]
            
            if status:
                changes = [c for c in changes if c.status == status]
            
            if date_range:
                start_date, end_date = date_range
                changes = [
                    c for c in changes
                    if start_date <= c.published_date <= end_date
                ]
            
            # Sort by published date (newest first)
            changes.sort(key=lambda x: x.published_date, reverse=True)
            
            # Apply limit
            return changes[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting regulatory changes: {str(e)}")
            return []
    
    async def get_compliance_status(
        self,
        service_name: Optional[str] = None,
        change_id: Optional[str] = None
    ) -> List[ComplianceStatus]:
        """Get compliance status"""
        try:
            status_list = list(self.compliance_status.values())
            
            # Apply filters
            if service_name:
                status_list = [s for s in status_list if s.service_name == service_name]
            
            if change_id:
                status_list = [s for s in status_list if s.change_id == change_id]
            
            return status_list
            
        except Exception as e:
            self.logger.error(f"Error getting compliance status: {str(e)}")
            return []
    
    async def check_compliance_deadlines(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Check for upcoming compliance deadlines"""
        try:
            upcoming_deadlines = []
            cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
            
            for change in self.regulatory_changes.values():
                if change.compliance_deadline and change.compliance_deadline <= cutoff_date:
                    # Check compliance status
                    compliance_status = await self._get_change_compliance_status(change.change_id)
                    
                    # Calculate days remaining
                    days_remaining = (change.compliance_deadline - datetime.now(timezone.utc)).days
                    
                    upcoming_deadlines.append({
                        "change_id": change.change_id,
                        "title": change.title,
                        "compliance_deadline": change.compliance_deadline.isoformat(),
                        "days_remaining": days_remaining,
                        "impact_level": change.impact_level,
                        "affected_services": change.affected_services,
                        "compliance_status": compliance_status,
                        "priority": "critical" if days_remaining <= 7 else "high" if days_remaining <= 14 else "medium"
                    })
            
            # Sort by deadline
            upcoming_deadlines.sort(key=lambda x: x["compliance_deadline"])
            
            return upcoming_deadlines
            
        except Exception as e:
            self.logger.error(f"Error checking compliance deadlines: {str(e)}")
            return []
    
    async def generate_compliance_report(
        self,
        service_name: Optional[str] = None,
        report_type: str = "summary"
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        try:
            # Get compliance status
            compliance_statuses = await self.get_compliance_status(service_name)
            
            # Get regulatory changes
            changes = await self.get_regulatory_changes()
            
            # Get upcoming deadlines
            upcoming_deadlines = await self.check_compliance_deadlines()
            
            # Calculate metrics
            total_changes = len(changes)
            critical_changes = len([c for c in changes if c.impact_level == ImpactLevel.CRITICAL])
            high_changes = len([c for c in changes if c.impact_level == ImpactLevel.HIGH])
            
            # Calculate compliance percentage
            if compliance_statuses:
                avg_compliance = sum(s.compliance_percentage for s in compliance_statuses) / len(compliance_statuses)
            else:
                avg_compliance = 0.0
            
            # Count gaps
            total_gaps = sum(len(s.gaps) for s in compliance_statuses)
            
            report = {
                "report_id": f"compliance_report_{int(datetime.now().timestamp())}",
                "report_type": report_type,
                "service_name": service_name,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_regulatory_changes": total_changes,
                    "critical_changes": critical_changes,
                    "high_impact_changes": high_changes,
                    "average_compliance_percentage": avg_compliance,
                    "total_compliance_gaps": total_gaps,
                    "upcoming_deadlines": len(upcoming_deadlines)
                },
                "compliance_status": [s.to_dict() for s in compliance_statuses],
                "upcoming_deadlines": upcoming_deadlines,
                "regulatory_changes": [c.to_dict() for c in changes[:10]],  # Latest 10
                "recommendations": await self._generate_compliance_recommendations(compliance_statuses)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {str(e)}")
            raise
    
    async def start_monitoring(self) -> bool:
        """Start regulatory monitoring"""
        try:
            # Start monitoring task
            asyncio.create_task(self._monitoring_loop())
            
            # Emit event
            await self.event_bus.emit("regulatory_monitoring_started", {
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info("Regulatory monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring: {str(e)}")
            return False
    
    async def acknowledge_notification(
        self,
        notification_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge a regulatory notification"""
        try:
            if notification_id not in self.notifications:
                return False
            
            notification = self.notifications[notification_id]
            notification.status = NotificationStatus.ACKNOWLEDGED
            notification.acknowledged_at = datetime.now(timezone.utc)
            
            # Emit event
            await self.event_bus.emit("regulatory_notification_acknowledged", {
                "notification_id": notification_id,
                "acknowledged_by": acknowledged_by,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error acknowledging notification: {str(e)}")
            return False
    
    async def register_source_connector(
        self,
        source: RegulatorySource,
        connector: Any
    ) -> bool:
        """Register a source connector"""
        try:
            self.source_connectors[source] = connector
            self.logger.info(f"Source connector registered: {source}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering source connector: {str(e)}")
            return False
    
    async def get_regulatory_metrics(
        self,
        time_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """Get regulatory tracking metrics"""
        try:
            # Filter changes by time range
            changes = list(self.regulatory_changes.values())
            if time_range:
                start_date, end_date = time_range
                changes = [
                    c for c in changes
                    if start_date <= c.published_date <= end_date
                ]
            
            # Calculate metrics
            total_changes = len(changes)
            changes_by_source = {}
            changes_by_type = {}
            changes_by_impact = {}
            
            for change in changes:
                # By source
                source = change.source
                changes_by_source[source] = changes_by_source.get(source, 0) + 1
                
                # By type
                change_type = change.change_type
                changes_by_type[change_type] = changes_by_type.get(change_type, 0) + 1
                
                # By impact
                impact = change.impact_level
                changes_by_impact[impact] = changes_by_impact.get(impact, 0) + 1
            
            # Subscription metrics
            total_subscriptions = len(self.subscriptions)
            active_subscriptions = len([s for s in self.subscriptions.values() if s.active])
            
            # Notification metrics
            total_notifications = len(self.notifications)
            pending_notifications = len([n for n in self.notifications.values() if n.status == NotificationStatus.PENDING])
            
            # Compliance metrics
            compliance_statuses = list(self.compliance_status.values())
            avg_compliance = sum(s.compliance_percentage for s in compliance_statuses) / len(compliance_statuses) if compliance_statuses else 0
            
            return {
                "total_regulatory_changes": total_changes,
                "changes_by_source": changes_by_source,
                "changes_by_type": changes_by_type,
                "changes_by_impact": changes_by_impact,
                "total_subscriptions": total_subscriptions,
                "active_subscriptions": active_subscriptions,
                "total_notifications": total_notifications,
                "pending_notifications": pending_notifications,
                "average_compliance_percentage": avg_compliance,
                "registered_sources": len(self.source_connectors),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting regulatory metrics: {str(e)}")
            raise
    
    # FIRS Grant Compliance Methods
    
    async def track_grant_eligibility(
        self, 
        force_refresh: bool = False
    ) -> GrantEligibilityAssessment:
        """Assess and track TaxPoynt's FIRS grant eligibility based on taxpayer onboarding performance"""
        try:
            # Check cache first
            cache_key = "firs_grant_eligibility:taxpoynt"
            if not force_refresh:
                cached_assessment = await self.cache_service.get(cache_key)
                if cached_assessment:
                    return GrantEligibilityAssessment(**cached_assessment)
            
            # Perform fresh assessment of TaxPoynt's performance
            assessment = await self._perform_taxpoynt_eligibility_assessment()
            
            # Store assessment
            self.eligibility_assessments[assessment.assessment_id] = assessment
            
            # Cache for 4 hours
            await self.cache_service.set(cache_key, assessment.to_dict(), ttl=14400)
            
            # Emit event
            await self.event_bus.emit("firs_grant_eligibility_assessed", {
                "service_provider": "taxpoynt",
                "assessment_id": assessment.assessment_id,
                "eligibility_score": assessment.eligibility_score,
                "eligible_milestones": [m.value for m in assessment.eligible_milestones],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info("TaxPoynt FIRS grant eligibility assessed")
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error tracking grant eligibility: {str(e)}")
            raise
    
    async def monitor_milestone_requirements(
        self,
        milestone: Optional[FIRSGrantMilestone] = None
    ) -> List[FIRSMilestoneStatus]:
        """Monitor TaxPoynt's progress toward FIRS grant milestones based on taxpayer onboarding"""
        try:
            # Get current KPI data for TaxPoynt's overall taxpayer onboarding performance
            kpi_data = await self.kpi_calculator.calculate_firs_grant_kpis()
            
            # Get milestone statuses
            if milestone:
                milestones_to_check = [milestone]
            else:
                milestones_to_check = list(FIRSGrantMilestone)
            
            milestone_statuses = []
            
            for ms in milestones_to_check:
                status = await self._assess_taxpoynt_milestone_status(ms, kpi_data)
                milestone_statuses.append(status)
                
                # Store status
                self.milestone_statuses[status.milestone_id] = status
                
                # Check for status changes and notifications
                await self._check_milestone_status_changes(status)
            
            # Cache milestone statuses
            cache_key = "milestone_statuses:taxpoynt"
            await self.cache_service.set(
                cache_key,
                [status.to_dict() for status in milestone_statuses],
                ttl=1800  # 30 minutes
            )
            
            # Store in grant tracking repository
            for status in milestone_statuses:
                await self.grant_tracking_repository.record_milestone_progress(
                    organization_id="taxpoynt",  # TaxPoynt as the grant recipient
                    milestone=status.milestone.value,
                    progress_data={
                        "status": status.status.value,
                        "progress_percentage": status.progress_percentage,
                        "compliance_score": status.compliance_score,
                        "requirements_met": status.requirements_met,
                        "requirements_pending": status.requirements_pending,
                        "risk_level": status.risk_level.value,
                        "last_assessed": status.last_assessed.isoformat(),
                        "taxpayers_onboarded": kpi_data.get("total_taxpayers_onboarded", 0),
                        "active_transmission_rate": kpi_data.get("active_transmission_rate", 0)
                    }
                )
            
            self.logger.info("TaxPoynt milestone requirements monitored")
            return milestone_statuses
            
        except Exception as e:
            self.logger.error(f"Error monitoring milestone requirements: {str(e)}")
            raise
    
    async def generate_grant_compliance_report(
        self,
        organization_id: Optional[str] = None,
        milestone: Optional[FIRSGrantMilestone] = None,
        report_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate comprehensive FIRS grant compliance report"""
        try:
            # Get base data
            if organization_id:
                # Single organization report
                eligibility_assessment = await self.track_grant_eligibility(organization_id)
                milestone_statuses = await self.monitor_milestone_requirements(organization_id, milestone)
                organizations_data = {organization_id: {
                    "eligibility": eligibility_assessment,
                    "milestones": milestone_statuses
                }}
            else:
                # Multi-organization report
                organizations_data = await self._get_all_organizations_grant_data()
            
            # Generate report based on type
            if report_type == "executive":
                report = await self._generate_executive_grant_report(organizations_data, milestone)
            elif report_type == "operational":
                report = await self._generate_operational_grant_report(organizations_data, milestone)
            elif report_type == "risk_assessment":
                report = await self._generate_grant_risk_report(organizations_data, milestone)
            else:  # comprehensive
                report = await self._generate_comprehensive_grant_report(organizations_data, milestone)
            
            # Add metadata
            report.update({
                "report_id": f"firs_grant_compliance_{int(datetime.now().timestamp())}",
                "report_type": report_type,
                "organization_id": organization_id,
                "milestone_filter": milestone.value if milestone else None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generated_by": "regulatory_tracker"
            })
            
            # Emit event
            await self.event_bus.emit("firs_grant_compliance_report_generated", {
                "report_id": report["report_id"],
                "report_type": report_type,
                "organization_id": organization_id,
                "milestone": milestone.value if milestone else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"FIRS grant compliance report generated: {report['report_id']}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating grant compliance report: {str(e)}")
            raise
    
    async def send_milestone_notification(
        self,
        organization_id: str,
        milestone: FIRSGrantMilestone,
        notification_type: str,
        priority: str = "medium",
        action_required: bool = False,
        action_deadline: Optional[datetime] = None,
        custom_message: Optional[str] = None
    ) -> MilestoneNotification:
        """Send automated milestone notification"""
        try:
            notification_id = str(uuid.uuid4())
            
            # Generate notification content
            title, message = await self._generate_milestone_notification_content(
                organization_id, milestone, notification_type, custom_message
            )
            
            # Create notification
            notification = MilestoneNotification(
                notification_id=notification_id,
                organization_id=organization_id,
                milestone=milestone,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                status=NotificationStatus.PENDING,
                delivery_method="system",  # Default to system notifications
                created_at=datetime.now(timezone.utc),
                action_required=action_required,
                action_deadline=action_deadline,
                metadata={
                    "auto_generated": True,
                    "source": "regulatory_tracker"
                }
            )
            
            # Store notification
            self.milestone_notifications[notification_id] = notification
            
            # Deliver notification
            await self._deliver_milestone_notification(notification)
            
            # Emit event
            await self.event_bus.emit("firs_milestone_notification_sent", {
                "notification_id": notification_id,
                "organization_id": organization_id,
                "milestone": milestone.value,
                "notification_type": notification_type,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Milestone notification sent: {notification_id}")
            return notification
            
        except Exception as e:
            self.logger.error(f"Error sending milestone notification: {str(e)}")
            raise
    
    async def add_firs_grant_rule(
        self,
        milestone: FIRSGrantMilestone,
        rule_type: str,
        description: str,
        requirement: Dict[str, Any],
        validation_logic: str,
        priority: str = "medium"
    ) -> FIRSGrantRule:
        """Add a new FIRS grant compliance rule"""
        try:
            rule_id = f"firs_rule_{milestone.value}_{rule_type}_{int(datetime.now().timestamp())}"
            
            rule = FIRSGrantRule(
                rule_id=rule_id,
                milestone=milestone,
                rule_type=rule_type,
                description=description,
                requirement=requirement,
                validation_logic=validation_logic,
                priority=priority,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Store rule
            self.firs_grant_rules[rule_id] = rule
            
            # Cache rule
            await self.cache_service.set(
                f"firs_grant_rule:{rule_id}",
                rule.to_dict(),
                ttl=86400  # 24 hours
            )
            
            # Emit event
            await self.event_bus.emit("firs_grant_rule_added", {
                "rule_id": rule_id,
                "milestone": milestone.value,
                "rule_type": rule_type,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"FIRS grant rule added: {rule_id}")
            return rule
            
        except Exception as e:
            self.logger.error(f"Error adding FIRS grant rule: {str(e)}")
            raise
    
    async def get_milestone_progress_summary(
        self,
        organization_id: str,
        time_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """Get milestone progress summary for organization"""
        try:
            # Get current milestone statuses
            milestone_statuses = await self.monitor_milestone_requirements(organization_id)
            
            # Get historical data if time range specified
            historical_data = []
            if time_range:
                historical_data = await self.grant_tracking_repository.get_milestone_history(
                    organization_id, time_range[0], time_range[1]
                )
            
            # Calculate progress metrics
            total_milestones = len(FIRSGrantMilestone)
            completed_milestones = len([s for s in milestone_statuses if s.status == FIRSGrantStatus.MILESTONE_ACHIEVED])
            in_progress_milestones = len([s for s in milestone_statuses if s.status == FIRSGrantStatus.IN_PROGRESS])
            at_risk_milestones = len([s for s in milestone_statuses if s.status == FIRSGrantStatus.AT_RISK])
            
            # Calculate overall progress
            overall_progress = sum(s.progress_percentage for s in milestone_statuses) / total_milestones
            overall_compliance_score = sum(s.compliance_score for s in milestone_statuses) / total_milestones
            
            # Determine overall status
            if completed_milestones == total_milestones:
                overall_status = FIRSGrantStatus.GRANT_COMPLETED
            elif at_risk_milestones > 0:
                overall_status = FIRSGrantStatus.AT_RISK
            elif in_progress_milestones > 0:
                overall_status = FIRSGrantStatus.IN_PROGRESS
            else:
                overall_status = FIRSGrantStatus.NOT_STARTED
            
            # Get next actionable milestone
            next_milestone = None
            for status in milestone_statuses:
                if status.status in [FIRSGrantStatus.NOT_STARTED, FIRSGrantStatus.IN_PROGRESS]:
                    next_milestone = status
                    break
            
            summary = {
                "organization_id": organization_id,
                "overall_status": overall_status.value,
                "overall_progress_percentage": round(overall_progress, 2),
                "overall_compliance_score": round(overall_compliance_score, 2),
                "milestones_summary": {
                    "total": total_milestones,
                    "completed": completed_milestones,
                    "in_progress": in_progress_milestones,
                    "at_risk": at_risk_milestones,
                    "not_started": total_milestones - completed_milestones - in_progress_milestones - at_risk_milestones
                },
                "milestone_details": [status.to_dict() for status in milestone_statuses],
                "next_milestone": next_milestone.to_dict() if next_milestone else None,
                "critical_action_items": [
                    item for status in milestone_statuses 
                    for item in status.action_items
                    if status.risk_level in [ComplianceRiskLevel.HIGH, ComplianceRiskLevel.CRITICAL]
                ],
                "historical_progress": historical_data,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting milestone progress summary: {str(e)}")
            raise
    
    # Private helper methods
    
    # FIRS Grant Helper Methods
    
    async def _perform_taxpoynt_eligibility_assessment(self) -> GrantEligibilityAssessment:
        """Perform TaxPoynt's FIRS grant eligibility assessment"""
        try:
            assessment_id = f"firs_eligibility_{int(datetime.now().timestamp())}"
            
            # Get current performance metrics
            kpi_data = await self.kpi_calculator.calculate_firs_grant_kpis()
            
            # Calculate eligibility score based on current performance
            eligibility_score = await self._calculate_eligibility_score(kpi_data)
            
            # Determine eligible milestones
            eligible_milestones = await self._determine_eligible_milestones(kpi_data)
            
            # Assess readiness factors
            readiness_factors = await self._assess_readiness_factors(kpi_data)
            
            # Perform risk assessment
            risk_assessment = await self._assess_grant_risk_factors(kpi_data)
            
            # Generate recommendations
            recommendations = await self._generate_grant_recommendations(kpi_data, eligible_milestones)
            
            # Estimate timeline
            estimated_timeline = await self._estimate_milestone_timeline(kpi_data, eligible_milestones)
            
            # Project grant payments
            grant_payment_projection = await self._project_grant_payments(eligible_milestones)
            
            assessment = GrantEligibilityAssessment(
                assessment_id=assessment_id,
                service_provider="taxpoynt",
                assessed_at=datetime.now(timezone.utc),
                eligibility_score=eligibility_score,
                eligible_milestones=eligible_milestones,
                current_performance=kpi_data,
                readiness_factors=readiness_factors,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                estimated_timeline=estimated_timeline,
                grant_payment_projection=grant_payment_projection
            )
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error performing eligibility assessment: {str(e)}")
            raise
    
    async def _assess_taxpoynt_milestone_status(
        self, 
        milestone: FIRSGrantMilestone, 
        kpi_data: Dict[str, Any]
    ) -> FIRSMilestoneStatus:
        """Assess TaxPoynt's status for a specific milestone"""
        try:
            milestone_id = f"taxpoynt_{milestone.value}_{int(datetime.now().timestamp())}"
            
            # Get rules for this milestone
            milestone_rules = [rule for rule in self.firs_grant_rules.values() if rule.milestone == milestone]
            
            # Evaluate each rule
            requirements_met = []
            requirements_pending = []
            progress_details = {}
            
            for rule in milestone_rules:
                is_met, progress_info = await self._evaluate_grant_rule(rule, kpi_data)
                if is_met:
                    requirements_met.append(rule.description)
                else:
                    requirements_pending.append(rule.description)
                progress_details[rule.rule_type] = progress_info
            
            # Calculate progress percentage
            total_rules = len(milestone_rules)
            met_rules = len(requirements_met)
            progress_percentage = (met_rules / total_rules * 100) if total_rules > 0 else 0
            
            # Determine status
            if progress_percentage == 100:
                status = FIRSGrantStatus.MILESTONE_ACHIEVED
            elif progress_percentage >= 80:
                status = FIRSGrantStatus.IN_PROGRESS
            elif progress_percentage >= 50:
                status = FIRSGrantStatus.IN_PROGRESS
            else:
                status = FIRSGrantStatus.NOT_STARTED
            
            # Assess risk level
            risk_level, risk_factors = await self._assess_milestone_risk(milestone, kpi_data, progress_percentage)
            
            # Generate action items
            action_items = await self._generate_milestone_action_items(milestone, requirements_pending, progress_details)
            
            # Calculate compliance score
            compliance_score = await self._calculate_milestone_compliance_score(milestone, kpi_data, progress_percentage)
            
            milestone_status = FIRSMilestoneStatus(
                milestone_id=milestone_id,
                service_provider="taxpoynt",
                milestone=milestone,
                status=status,
                progress_percentage=round(progress_percentage, 2),
                requirements_met=requirements_met,
                requirements_pending=requirements_pending,
                target_date=await self._get_milestone_target_date(milestone),
                actual_completion_date=datetime.now(timezone.utc) if status == FIRSGrantStatus.MILESTONE_ACHIEVED else None,
                risk_level=risk_level,
                risk_factors=risk_factors,
                action_items=action_items,
                compliance_score=round(compliance_score, 2),
                last_assessed=datetime.now(timezone.utc),
                next_assessment=datetime.now(timezone.utc) + timedelta(hours=6),
                taxpayers_onboarded=kpi_data.get("total_taxpayers_onboarded", 0),
                active_transmission_rate=kpi_data.get("active_transmission_rate", 0.0),
                sector_diversity_score=kpi_data.get("sector_diversity_score", 0.0),
                large_taxpayer_count=kpi_data.get("large_taxpayer_count", 0),
                sme_taxpayer_count=kpi_data.get("sme_taxpayer_count", 0),
                metadata={
                    "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
                    "kpi_data_snapshot": kpi_data,
                    "rules_evaluated": len(milestone_rules),
                    "progress_details": progress_details
                }
            )
            
            return milestone_status
            
        except Exception as e:
            self.logger.error(f"Error assessing milestone status: {str(e)}")
            raise
    
    async def _check_milestone_status_changes(self, current_status: FIRSMilestoneStatus) -> None:
        """Check for milestone status changes and trigger notifications"""
        try:
            # Get previous status from cache
            cache_key = f"milestone_status_history:{current_status.milestone.value}"
            previous_status_data = await self.cache_service.get(cache_key)
            
            # Check if status changed
            status_changed = False
            notification_type = None
            
            if previous_status_data:
                previous_status = FIRSMilestoneStatus(**previous_status_data)
                
                # Check for status changes
                if previous_status.status != current_status.status:
                    status_changed = True
                    
                    if current_status.status == FIRSGrantStatus.MILESTONE_ACHIEVED:
                        notification_type = "milestone_achieved"
                    elif current_status.status == FIRSGrantStatus.AT_RISK:
                        notification_type = "at_risk"
                    elif current_status.risk_level in [ComplianceRiskLevel.HIGH, ComplianceRiskLevel.CRITICAL]:
                        notification_type = "risk_escalation"
                
                # Check for significant progress changes
                progress_change = abs(current_status.progress_percentage - previous_status.progress_percentage)
                if progress_change >= 10:  # 10% or more change
                    notification_type = "progress_update"
                    status_changed = True
            else:
                # First assessment
                status_changed = True
                notification_type = "initial_assessment"
            
            # Store current status for future comparison
            await self.cache_service.set(cache_key, current_status.to_dict(), ttl=86400)
            
            # Send notification if status changed
            if status_changed and notification_type:
                priority = "critical" if current_status.risk_level == ComplianceRiskLevel.CRITICAL else "high"
                
                await self.send_milestone_notification(
                    organization_id="taxpoynt",
                    milestone=current_status.milestone,
                    notification_type=notification_type,
                    priority=priority,
                    action_required=len(current_status.action_items) > 0
                )
            
        except Exception as e:
            self.logger.error(f"Error checking milestone status changes: {str(e)}")
    
    async def _generate_milestone_notification_content(
        self,
        organization_id: str,
        milestone: FIRSGrantMilestone,
        notification_type: str,
        custom_message: Optional[str] = None
    ) -> tuple:
        """Generate milestone notification content"""
        try:
            if custom_message:
                return f"FIRS Grant Milestone {milestone.value.upper()}", custom_message
            
            # Get current milestone status
            milestone_statuses = await self.monitor_milestone_requirements(milestone)
            current_status = milestone_statuses[0] if milestone_statuses else None
            
            if notification_type == "milestone_achieved":
                title = f"🎉 FIRS Grant Milestone {milestone.value.upper()} Achieved!"
                message = f"""
Congratulations! TaxPoynt has successfully achieved FIRS Grant Milestone {milestone.value.upper()}.

Current Status:
- Progress: {current_status.progress_percentage}%
- Taxpayers Onboarded: {current_status.taxpayers_onboarded}
- Active Transmission Rate: {current_status.active_transmission_rate:.1%}
- Compliance Score: {current_status.compliance_score}

Grant payment eligibility confirmed. FIRS will be notified of milestone completion.
                """
            
            elif notification_type == "at_risk":
                title = f"⚠️ FIRS Grant Milestone {milestone.value.upper()} At Risk"
                message = f"""
Alert: TaxPoynt's progress toward FIRS Grant Milestone {milestone.value.upper()} is at risk.

Current Status:
- Progress: {current_status.progress_percentage}%
- Risk Level: {current_status.risk_level.value.upper()}
- Taxpayers Onboarded: {current_status.taxpayers_onboarded}

Risk Factors:
{chr(10).join(f"• {factor}" for factor in current_status.risk_factors[:3])}

Immediate Action Required:
{chr(10).join(f"• {item}" for item in current_status.action_items[:3])}
                """
            
            elif notification_type == "progress_update":
                title = f"📊 FIRS Grant Milestone {milestone.value.upper()} Progress Update"
                message = f"""
Progress update for FIRS Grant Milestone {milestone.value.upper()}:

Current Status:
- Progress: {current_status.progress_percentage}%
- Taxpayers Onboarded: {current_status.taxpayers_onboarded}
- Active Transmission Rate: {current_status.active_transmission_rate:.1%}

Requirements Met: {len(current_status.requirements_met)}
Requirements Pending: {len(current_status.requirements_pending)}
                """
            
            elif notification_type == "deadline_approaching":
                title = f"⏰ FIRS Grant Milestone {milestone.value.upper()} Deadline Approaching"
                message = f"""
Reminder: FIRS Grant Milestone {milestone.value.upper()} deadline is approaching.

Current Status:
- Progress: {current_status.progress_percentage}%
- Target Date: {current_status.target_date.strftime('%Y-%m-%d') if current_status.target_date else 'TBD'}
- Days Remaining: {(current_status.target_date - datetime.now(timezone.utc)).days if current_status.target_date else 'TBD'}

Action Items:
{chr(10).join(f"• {item}" for item in current_status.action_items[:5])}
                """
            
            else:  # default/initial_assessment
                title = f"📋 FIRS Grant Milestone {milestone.value.upper()} Assessment"
                message = f"""
Initial assessment completed for FIRS Grant Milestone {milestone.value.upper()}.

Current Status:
- Progress: {current_status.progress_percentage}%
- Taxpayers Onboarded: {current_status.taxpayers_onboarded}
- Compliance Score: {current_status.compliance_score}

Next Steps:
{chr(10).join(f"• {item}" for item in current_status.action_items[:3])}
                """
            
            return title, message.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating notification content: {str(e)}")
            return f"FIRS Grant Milestone {milestone.value.upper()} Notification", "Status update available in dashboard."
    
    async def _deliver_milestone_notification(self, notification: MilestoneNotification) -> None:
        """Deliver milestone notification"""
        try:
            # Deliver based on method
            if notification.delivery_method == "email":
                await self.notification_service.send_email(
                    to="grants@taxpoynt.com",  # Grant management team
                    subject=notification.title,
                    body=notification.message,
                    priority=notification.priority
                )
            elif notification.delivery_method == "webhook":
                await self.notification_service.send_webhook(
                    url="/api/webhooks/firs-grant-notifications",
                    data={
                        "notification_id": notification.notification_id,
                        "milestone": notification.milestone.value,
                        "notification_type": notification.notification_type,
                        "title": notification.title,
                        "message": notification.message,
                        "priority": notification.priority,
                        "action_required": notification.action_required,
                        "action_deadline": notification.action_deadline.isoformat() if notification.action_deadline else None
                    }
                )
            else:  # system notification
                await self.notification_service.send_system_notification(
                    user_id="grant_managers",
                    title=notification.title,
                    message=notification.message,
                    priority=notification.priority,
                    metadata={
                        "milestone": notification.milestone.value,
                        "notification_type": notification.notification_type,
                        "action_required": notification.action_required
                    }
                )
            
            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            
        except Exception as e:
            self.logger.error(f"Error delivering milestone notification: {str(e)}")
            notification.status = NotificationStatus.PENDING  # Retry later
    
    async def _validate_regulatory_change(self, change: RegulatoryChange) -> bool:
        """Validate regulatory change"""
        try:
            # Check required fields
            if not change.change_id or not change.title:
                return False
            
            # Check dates
            if change.compliance_deadline and change.compliance_deadline <= datetime.now(timezone.utc):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating regulatory change: {str(e)}")
            return False
    
    async def _analyze_change_impact(self, change: RegulatoryChange) -> Dict[str, Any]:
        """Analyze impact of regulatory change"""
        try:
            impact_analysis = {
                "affected_services_count": len(change.affected_services),
                "estimated_implementation_effort": "medium",  # This would be calculated
                "compliance_complexity": "medium",  # This would be analyzed
                "business_impact": "medium",  # This would be assessed
                "technical_requirements": [],  # This would be extracted
                "training_requirements": [],  # This would be identified
                "cost_implications": "medium"  # This would be estimated
            }
            
            # Analyze based on change type
            if change.change_type == ChangeType.TECHNICAL_SPECIFICATION:
                impact_analysis["technical_requirements"].append("System updates required")
                impact_analysis["estimated_implementation_effort"] = "high"
            
            if change.impact_level == ImpactLevel.CRITICAL:
                impact_analysis["business_impact"] = "high"
                impact_analysis["compliance_complexity"] = "high"
            
            return impact_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing change impact: {str(e)}")
            return {}
    
    async def _identify_compliance_gaps(self, change: RegulatoryChange) -> List[ComplianceGap]:
        """Identify compliance gaps for regulatory change"""
        try:
            gaps = []
            
            for service in change.affected_services:
                # This would analyze the service against the new requirements
                # For now, create a sample gap
                gap = ComplianceGap(
                    gap_id=f"gap_{change.change_id}_{service}",
                    change_id=change.change_id,
                    affected_service=service,
                    gap_type="implementation",
                    description=f"Service {service} needs to implement new requirements",
                    current_state="non_compliant",
                    required_state="compliant",
                    remediation_steps=[
                        "Analyze new requirements",
                        "Design implementation plan",
                        "Implement changes",
                        "Test compliance",
                        "Deploy to production"
                    ],
                    estimated_effort="medium",
                    deadline=change.compliance_deadline or change.effective_date,
                    priority="high" if change.impact_level == ImpactLevel.CRITICAL else "medium"
                )
                gaps.append(gap)
            
            return gaps
            
        except Exception as e:
            self.logger.error(f"Error identifying compliance gaps: {str(e)}")
            return []
    
    async def _notify_subscribers(self, change: RegulatoryChange) -> None:
        """Notify subscribers about regulatory change"""
        try:
            # Get matching subscriptions
            matching_subscriptions = []
            
            for subscription in self.subscriptions.values():
                if not subscription.active:
                    continue
                
                # Check if subscription matches the change
                if await self._subscription_matches_change(subscription, change):
                    matching_subscriptions.append(subscription)
            
            # Send notifications
            for subscription in matching_subscriptions:
                await self._send_notification(subscription, change)
                
        except Exception as e:
            self.logger.error(f"Error notifying subscribers: {str(e)}")
    
    async def _subscription_matches_change(
        self,
        subscription: RegulatorySubscription,
        change: RegulatoryChange
    ) -> bool:
        """Check if subscription matches change"""
        try:
            # Check source
            if subscription.sources and change.source not in subscription.sources:
                return False
            
            # Check change type
            if subscription.change_types and change.change_type not in subscription.change_types:
                return False
            
            # Check impact level
            if subscription.impact_levels and change.impact_level not in subscription.impact_levels:
                return False
            
            # Check filters
            if subscription.filters:
                # Apply custom filters
                if "affected_services" in subscription.filters:
                    filter_services = subscription.filters["affected_services"]
                    if not any(service in change.affected_services for service in filter_services):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking subscription match: {str(e)}")
            return False
    
    async def _send_notification(
        self,
        subscription: RegulatorySubscription,
        change: RegulatoryChange
    ) -> None:
        """Send notification to subscriber"""
        try:
            notification_id = str(uuid.uuid4())
            
            # Create notification
            notification = RegulatoryNotification(
                notification_id=notification_id,
                change_id=change.change_id,
                subscription_id=subscription.subscription_id,
                subscriber_id=subscription.subscriber_id,
                title=f"Regulatory Change: {change.title}",
                message=self._generate_notification_message(change),
                priority=self._map_impact_to_priority(change.impact_level),
                status=NotificationStatus.PENDING,
                delivery_method=subscription.notification_methods[0],  # Use first method
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30)
            )
            
            # Store notification
            self.notifications[notification_id] = notification
            
            # Send notification
            await self._deliver_notification(notification)
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {str(e)}")
    
    def _generate_notification_message(self, change: RegulatoryChange) -> str:
        """Generate notification message"""
        try:
            message = f"""
            New regulatory change detected:
            
            Title: {change.title}
            Source: {change.source.value}
            Type: {change.change_type.value}
            Impact Level: {change.impact_level.value}
            
            Description: {change.description}
            
            Affected Services: {', '.join(change.affected_services)}
            
            Effective Date: {change.effective_date.strftime('%Y-%m-%d')}
            Compliance Deadline: {change.compliance_deadline.strftime('%Y-%m-%d') if change.compliance_deadline else 'Not specified'}
            
            Please review and take necessary action.
            """
            
            return message.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating notification message: {str(e)}")
            return f"Regulatory change notification: {change.title}"
    
    def _map_impact_to_priority(self, impact_level: ImpactLevel) -> str:
        """Map impact level to priority"""
        mapping = {
            ImpactLevel.CRITICAL: "critical",
            ImpactLevel.HIGH: "high",
            ImpactLevel.MEDIUM: "medium",
            ImpactLevel.LOW: "low",
            ImpactLevel.INFORMATIONAL: "info"
        }
        return mapping.get(impact_level, "medium")
    
    async def _deliver_notification(self, notification: RegulatoryNotification) -> None:
        """Deliver notification"""
        try:
            # Deliver notification based on method
            if notification.delivery_method == "email":
                await self.notification_service.send_email(
                    to=notification.subscriber_id,
                    subject=notification.title,
                    body=notification.message,
                    priority=notification.priority
                )
            elif notification.delivery_method == "webhook":
                await self.notification_service.send_webhook(
                    url=notification.subscriber_id,
                    data={
                        "notification_id": notification.notification_id,
                        "title": notification.title,
                        "message": notification.message,
                        "priority": notification.priority
                    }
                )
            elif notification.delivery_method == "system":
                await self.notification_service.send_system_notification(
                    user_id=notification.subscriber_id,
                    title=notification.title,
                    message=notification.message,
                    priority=notification.priority
                )
            
            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            
        except Exception as e:
            self.logger.error(f"Error delivering notification: {str(e)}")
    
    async def _update_compliance_status(
        self,
        change: RegulatoryChange,
        gaps: List[ComplianceGap]
    ) -> None:
        """Update compliance status"""
        try:
            for service in change.affected_services:
                status_id = f"status_{change.change_id}_{service}"
                
                # Calculate compliance percentage
                if gaps:
                    service_gaps = [g for g in gaps if g.affected_service == service]
                    compliance_percentage = max(0, 100 - (len(service_gaps) * 20))  # Simple calculation
                else:
                    compliance_percentage = 100.0
                
                # Determine status
                if compliance_percentage == 100:
                    status = "compliant"
                elif compliance_percentage >= 80:
                    status = "partially_compliant"
                else:
                    status = "non_compliant"
                
                # Create or update compliance status
                compliance_status = ComplianceStatus(
                    status_id=status_id,
                    change_id=change.change_id,
                    service_name=service,
                    compliance_percentage=compliance_percentage,
                    status=status,
                    last_assessed=datetime.now(timezone.utc),
                    next_assessment=datetime.now(timezone.utc) + timedelta(days=7),
                    gaps=[g for g in gaps if g.affected_service == service]
                )
                
                self.compliance_status[status_id] = compliance_status
                
        except Exception as e:
            self.logger.error(f"Error updating compliance status: {str(e)}")
    
    async def _get_change_compliance_status(self, change_id: str) -> Dict[str, Any]:
        """Get compliance status for a change"""
        try:
            statuses = [s for s in self.compliance_status.values() if s.change_id == change_id]
            
            if not statuses:
                return {"overall_status": "unknown", "services": []}
            
            # Calculate overall status
            avg_compliance = sum(s.compliance_percentage for s in statuses) / len(statuses)
            
            if avg_compliance == 100:
                overall_status = "compliant"
            elif avg_compliance >= 80:
                overall_status = "partially_compliant"
            else:
                overall_status = "non_compliant"
            
            return {
                "overall_status": overall_status,
                "average_compliance": avg_compliance,
                "services": [
                    {
                        "service_name": s.service_name,
                        "compliance_percentage": s.compliance_percentage,
                        "status": s.status,
                        "gaps_count": len(s.gaps)
                    }
                    for s in statuses
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting change compliance status: {str(e)}")
            return {"overall_status": "unknown", "services": []}
    
    async def _generate_compliance_recommendations(
        self,
        compliance_statuses: List[ComplianceStatus]
    ) -> List[str]:
        """Generate compliance recommendations"""
        try:
            recommendations = []
            
            # Analyze compliance gaps
            all_gaps = []
            for status in compliance_statuses:
                all_gaps.extend(status.gaps)
            
            if not all_gaps:
                recommendations.append("All services are compliant with current regulations")
                return recommendations
            
            # Count gaps by type
            gap_types = {}
            for gap in all_gaps:
                gap_types[gap.gap_type] = gap_types.get(gap.gap_type, 0) + 1
            
            # Generate recommendations based on gap analysis
            for gap_type, count in gap_types.items():
                if count > 1:
                    recommendations.append(f"Address {count} {gap_type} gaps across services")
            
            # Check for upcoming deadlines
            urgent_gaps = [g for g in all_gaps if g.deadline and g.deadline <= datetime.now(timezone.utc) + timedelta(days=30)]
            if urgent_gaps:
                recommendations.append(f"Prioritize {len(urgent_gaps)} gaps with upcoming deadlines")
            
            # High priority gaps
            high_priority_gaps = [g for g in all_gaps if g.priority == "high"]
            if high_priority_gaps:
                recommendations.append(f"Focus on {len(high_priority_gaps)} high-priority compliance gaps")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating compliance recommendations: {str(e)}")
            return ["Review compliance status and address identified gaps"]
    
    async def _monitoring_loop(self) -> None:
        """Monitoring loop for regulatory changes"""
        try:
            while True:
                await asyncio.sleep(self.monitoring_config["check_interval"])
                
                # Check for new changes from sources
                await self._check_sources_for_updates()
                
                # Check compliance deadlines
                await self._check_compliance_deadlines()
                
                # Process pending notifications
                await self._process_pending_notifications()
                
                # Update compliance assessments
                await self._update_compliance_assessments()
                
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {str(e)}")
    
    async def _check_sources_for_updates(self) -> None:
        """Check registered sources for updates"""
        try:
            for source, connector in self.source_connectors.items():
                try:
                    # Get updates from source
                    updates = await connector.get_updates()
                    
                    # Process updates
                    for update in updates:
                        # Convert to RegulatoryChange
                        change = await self._convert_update_to_change(update, source)
                        
                        # Register change
                        await self.register_regulatory_change(change)
                        
                except Exception as e:
                    self.logger.error(f"Error checking source {source}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error checking sources for updates: {str(e)}")
    
    async def _convert_update_to_change(self, update: Dict[str, Any], source: RegulatorySource) -> RegulatoryChange:
        """Convert source update to regulatory change"""
        try:
            change = RegulatoryChange(
                change_id=update.get("id", str(uuid.uuid4())),
                source=source,
                change_type=ChangeType(update.get("type", "regulation_update")),
                title=update.get("title", ""),
                description=update.get("description", ""),
                impact_level=ImpactLevel(update.get("impact_level", "medium")),
                status=ChangeStatus(update.get("status", "effective")),
                affected_services=update.get("affected_services", []),
                compliance_deadline=datetime.fromisoformat(update["compliance_deadline"]) if update.get("compliance_deadline") else None,
                effective_date=datetime.fromisoformat(update.get("effective_date", datetime.now(timezone.utc).isoformat())),
                published_date=datetime.fromisoformat(update.get("published_date", datetime.now(timezone.utc).isoformat())),
                reference_number=update.get("reference_number"),
                document_url=update.get("document_url"),
                details=update.get("details", {}),
                metadata=update.get("metadata", {})
            )
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error converting update to change: {str(e)}")
            raise
    
    async def _check_compliance_deadlines(self) -> None:
        """Check for compliance deadlines"""
        try:
            upcoming_deadlines = await self.check_compliance_deadlines(7)  # 7 days ahead
            
            for deadline in upcoming_deadlines:
                if deadline["priority"] == "critical":
                    # Send urgent notification
                    await self.notification_service.send_urgent_alert(
                        title=f"URGENT: Compliance Deadline Approaching",
                        message=f"Compliance deadline for '{deadline['title']}' is in {deadline['days_remaining']} days",
                        affected_services=deadline["affected_services"]
                    )
                    
        except Exception as e:
            self.logger.error(f"Error checking compliance deadlines: {str(e)}")
    
    async def _process_pending_notifications(self) -> None:
        """Process pending notifications"""
        try:
            pending_notifications = [
                n for n in self.notifications.values()
                if n.status == NotificationStatus.PENDING
            ]
            
            for notification in pending_notifications:
                # Check if notification has expired
                if notification.expires_at and notification.expires_at <= datetime.now(timezone.utc):
                    notification.status = NotificationStatus.EXPIRED
                    continue
                
                # Retry delivery
                await self._deliver_notification(notification)
                
        except Exception as e:
            self.logger.error(f"Error processing pending notifications: {str(e)}")
    
    async def _update_compliance_assessments(self) -> None:
        """Update compliance assessments"""
        try:
            for status in self.compliance_status.values():
                if status.next_assessment <= datetime.now(timezone.utc):
                    # Reassess compliance
                    await self._reassess_compliance(status)
                    
        except Exception as e:
            self.logger.error(f"Error updating compliance assessments: {str(e)}")
    
    async def _reassess_compliance(self, status: ComplianceStatus) -> None:
        """Reassess compliance status"""
        try:
            # This would implement compliance reassessment logic
            # For now, just update the assessment date
            status.last_assessed = datetime.now(timezone.utc)
            status.next_assessment = datetime.now(timezone.utc) + timedelta(days=7)
            
        except Exception as e:
            self.logger.error(f"Error reassessing compliance: {str(e)}")
    
    def _initialize_default_subscriptions(self):
        """Initialize default subscriptions"""
        try:
            # System-wide subscription for critical changes
            system_subscription = RegulatorySubscription(
                subscription_id="system_critical",
                subscriber_id="system",
                subscriber_type="system",
                sources=list(RegulatorySource),
                change_types=list(ChangeType),
                impact_levels=[ImpactLevel.CRITICAL, ImpactLevel.HIGH],
                notification_methods=["system"],
                filters={},
                active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.subscriptions[system_subscription.subscription_id] = system_subscription
            
        except Exception as e:
            self.logger.error(f"Error initializing default subscriptions: {str(e)}")
    
    def _initialize_firs_grant_rules(self):
        """Initialize FIRS grant compliance rules"""
        try:
            # Milestone 1 Rules: 20 users, 80% active
            milestone_1_rules = [
                FIRSGrantRule(
                    rule_id="firs_m1_user_count",
                    milestone=FIRSGrantMilestone.MILESTONE_1,
                    rule_type="user_count",
                    description="Minimum 20 taxpayers successfully onboarded",
                    requirement={"min_taxpayers": 20, "verification_required": True},
                    validation_logic="total_taxpayers_onboarded >= 20",
                    priority="high",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                FIRSGrantRule(
                    rule_id="firs_m1_activity_rate",
                    milestone=FIRSGrantMilestone.MILESTONE_1,
                    rule_type="activity_rate",
                    description="80% of onboarded taxpayers must have active transmission",
                    requirement={"min_activity_rate": 0.8, "measurement_period_days": 30},
                    validation_logic="active_transmission_rate >= 0.8",
                    priority="high",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            ]
            
            # Milestone 2 Rules: 40 users, large + SME mix
            milestone_2_rules = [
                FIRSGrantRule(
                    rule_id="firs_m2_user_count",
                    milestone=FIRSGrantMilestone.MILESTONE_2,
                    rule_type="user_count",
                    description="Minimum 40 taxpayers successfully onboarded",
                    requirement={"min_taxpayers": 40, "verification_required": True},
                    validation_logic="total_taxpayers_onboarded >= 40",
                    priority="high",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                FIRSGrantRule(
                    rule_id="firs_m2_taxpayer_mix",
                    milestone=FIRSGrantMilestone.MILESTONE_2,
                    rule_type="taxpayer_diversity",
                    description="Mix of large taxpayers and SMEs required",
                    requirement={"min_large_taxpayers": 5, "min_sme_taxpayers": 15},
                    validation_logic="large_taxpayer_count >= 5 AND sme_taxpayer_count >= 15",
                    priority="medium",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            ]
            
            # Milestone 3 Rules: 60 users, cross-sector
            milestone_3_rules = [
                FIRSGrantRule(
                    rule_id="firs_m3_user_count",
                    milestone=FIRSGrantMilestone.MILESTONE_3,
                    rule_type="user_count",
                    description="Minimum 60 taxpayers successfully onboarded",
                    requirement={"min_taxpayers": 60, "verification_required": True},
                    validation_logic="total_taxpayers_onboarded >= 60",
                    priority="high",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                FIRSGrantRule(
                    rule_id="firs_m3_sector_diversity",
                    milestone=FIRSGrantMilestone.MILESTONE_3,
                    rule_type="sector_diversity",
                    description="Cross-sector representation required",
                    requirement={"min_sectors": 5, "min_diversity_score": 0.6},
                    validation_logic="sector_count >= 5 AND sector_diversity_score >= 0.6",
                    priority="medium",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            ]
            
            # Milestone 4 Rules: 80 users, sustained compliance
            milestone_4_rules = [
                FIRSGrantRule(
                    rule_id="firs_m4_user_count",
                    milestone=FIRSGrantMilestone.MILESTONE_4,
                    rule_type="user_count",
                    description="Minimum 80 taxpayers successfully onboarded",
                    requirement={"min_taxpayers": 80, "verification_required": True},
                    validation_logic="total_taxpayers_onboarded >= 80",
                    priority="high",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                FIRSGrantRule(
                    rule_id="firs_m4_sustained_compliance",
                    milestone=FIRSGrantMilestone.MILESTONE_4,
                    rule_type="sustained_performance",
                    description="Sustained compliance and transmission rates",
                    requirement={"min_sustained_period_days": 90, "min_compliance_score": 0.85},
                    validation_logic="sustained_compliance_days >= 90 AND compliance_score >= 0.85",
                    priority="high",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            ]
            
            # Milestone 5 Rules: 100 users, full validation
            milestone_5_rules = [
                FIRSGrantRule(
                    rule_id="firs_m5_user_count",
                    milestone=FIRSGrantMilestone.MILESTONE_5,
                    rule_type="user_count",
                    description="Minimum 100 taxpayers successfully onboarded",
                    requirement={"min_taxpayers": 100, "verification_required": True},
                    validation_logic="total_taxpayers_onboarded >= 100",
                    priority="high",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                FIRSGrantRule(
                    rule_id="firs_m5_full_validation",
                    milestone=FIRSGrantMilestone.MILESTONE_5,
                    rule_type="comprehensive_validation",
                    description="Full FIRS validation and audit compliance",
                    requirement={"audit_compliance": True, "validation_score": 0.95},
                    validation_logic="audit_compliant == True AND validation_score >= 0.95",
                    priority="critical",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            ]
            
            # Store all rules
            all_rules = milestone_1_rules + milestone_2_rules + milestone_3_rules + milestone_4_rules + milestone_5_rules
            for rule in all_rules:
                self.firs_grant_rules[rule.rule_id] = rule
            
            self.logger.info(f"Initialized {len(all_rules)} FIRS grant compliance rules")
            
        except Exception as e:
            self.logger.error(f"Error initializing FIRS grant rules: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for regulatory tracker"""
        try:
            return {
                "status": "healthy",
                "service": "regulatory_tracker",
                "regulatory_changes": len(self.regulatory_changes),
                "subscriptions": len(self.subscriptions),
                "active_subscriptions": len([s for s in self.subscriptions.values() if s.active]),
                "notifications": len(self.notifications),
                "compliance_statuses": len(self.compliance_status),
                "source_connectors": len(self.source_connectors),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "regulatory_tracker",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup tracker resources"""
        try:
            # Clear registries
            self.regulatory_changes.clear()
            self.subscriptions.clear()
            self.notifications.clear()
            self.compliance_status.clear()
            self.source_connectors.clear()
            
            self.logger.info("Regulatory tracker cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_regulatory_tracker() -> RegulatoryTracker:
    """Create regulatory tracker instance"""
    return RegulatoryTracker()