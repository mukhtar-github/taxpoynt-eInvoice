"""
APP Service: Registration Tracker
Tracks taxpayer registration progress and KPI compliance
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import statistics

from .taxpayer_onboarding import OnboardingStatus, TaxpayerType, OnboardingApplication


class RegistrationMetric(str, Enum):
    """Registration tracking metrics"""
    TOTAL_REGISTRATIONS = "total_registrations"
    ACTIVE_TAXPAYERS = "active_taxpayers"
    MONTHLY_REGISTRATIONS = "monthly_registrations"
    AVERAGE_ONBOARDING_TIME = "average_onboarding_time"
    APPROVAL_RATE = "approval_rate"
    REJECTION_RATE = "rejection_rate"
    DROPOUT_RATE = "dropout_rate"
    TAXPAYER_TYPE_DISTRIBUTION = "taxpayer_type_distribution"
    SECTOR_DISTRIBUTION = "sector_distribution"


class KPIStatus(str, Enum):
    """KPI compliance status"""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BEHIND = "behind"
    EXCEEDED = "exceeded"


@dataclass
class RegistrationKPI:
    """KPI tracking for taxpayer registration"""
    kpi_id: str
    name: str
    description: str
    target_value: float
    current_value: float
    unit: str
    period: str
    status: KPIStatus
    trend: str
    last_updated: datetime
    progress_percentage: float
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data


@dataclass
class RegistrationMilestone:
    """Registration milestone tracking"""
    milestone_id: str
    title: str
    description: str
    target_date: datetime
    target_value: float
    current_value: float
    achieved: bool
    achieved_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['target_date'] = self.target_date.isoformat()
        if self.achieved_date:
            data['achieved_date'] = self.achieved_date.isoformat()
        return data


@dataclass
class RegistrationForecast:
    """Registration forecast data"""
    forecast_id: str
    period: str
    forecasted_registrations: int
    confidence_level: float
    factors: List[str]
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data


class RegistrationTracker:
    """
    Comprehensive registration tracking service
    Monitors taxpayer registration progress and KPI compliance
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Registration tracking data
        self.registration_history: List[Dict[str, Any]] = []
        self.kpi_history: List[Dict[str, Any]] = []
        self.milestones: Dict[str, RegistrationMilestone] = {}
        
        # KPI targets (FIRS requirements)
        self.kpi_targets = {
            'taxpayers_per_6_months': 100,
            'approval_rate_minimum': 85.0,
            'max_onboarding_days': 30,
            'dropout_rate_maximum': 15.0,
            'minimum_sectors': 4
        }
        
        # Tracking statistics
        self.stats = {
            'total_tracked_periods': 0,
            'kpi_breaches': 0,
            'successful_periods': 0,
            'last_update': None,
            'forecast_accuracy': 0.0
        }
        
        # Initialize milestones
        self._initialize_milestones()
    
    def _initialize_milestones(self):
        """Initialize registration milestones"""
        now = datetime.now(timezone.utc)
        
        # 6-month milestone
        self.milestones['6_month_target'] = RegistrationMilestone(
            milestone_id='6_month_target',
            title='6-Month Registration Target',
            description='Achieve 100 taxpayer registrations in 6 months',
            target_date=now + timedelta(days=180),
            target_value=100.0,
            current_value=0.0,
            achieved=False
        )
        
        # Monthly milestones
        for month in range(1, 7):
            milestone_date = now + timedelta(days=30 * month)
            target_value = (100 / 6) * month  # Linear target
            
            self.milestones[f'month_{month}_target'] = RegistrationMilestone(
                milestone_id=f'month_{month}_target',
                title=f'Month {month} Target',
                description=f'Target {target_value:.0f} registrations by month {month}',
                target_date=milestone_date,
                target_value=target_value,
                current_value=0.0,
                achieved=False
            )
    
    async def track_registration(self, 
                               application: OnboardingApplication,
                               event_type: str):
        """
        Track a registration event
        
        Args:
            application: Onboarding application
            event_type: Type of event (submitted, approved, rejected, etc.)
        """
        try:
            registration_event = {
                'event_id': f"REG_{datetime.now(timezone.utc).timestamp()}",
                'application_id': application.application_id,
                'taxpayer_id': application.taxpayer_profile.taxpayer_id,
                'taxpayer_name': application.taxpayer_profile.business_name,
                'taxpayer_type': application.taxpayer_profile.taxpayer_type.value,
                'sector': application.taxpayer_profile.sector,
                'event_type': event_type,
                'status': application.status.value,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'processing_time_days': (
                    (datetime.now(timezone.utc) - application.submitted_at).days
                    if application.actual_completion else None
                )
            }
            
            self.registration_history.append(registration_event)
            
            # Update milestones if approved
            if event_type == 'approved':
                await self._update_milestones()
            
            # Update KPI tracking
            await self._update_kpi_tracking()
            
            self.logger.info(f"Registration event tracked: {event_type} for {application.application_id}")
            
        except Exception as e:
            self.logger.error(f"Error tracking registration: {str(e)}")
            raise
    
    async def _update_milestones(self):
        """Update milestone progress"""
        now = datetime.now(timezone.utc)
        
        # Count approved registrations
        approved_count = len([
            event for event in self.registration_history
            if event['event_type'] == 'approved'
        ])
        
        # Update all milestones
        for milestone in self.milestones.values():
            milestone.current_value = approved_count
            
            if not milestone.achieved and approved_count >= milestone.target_value:
                milestone.achieved = True
                milestone.achieved_date = now
                
                self.logger.info(f"Milestone achieved: {milestone.title}")
    
    async def _update_kpi_tracking(self):
        """Update KPI tracking data"""
        now = datetime.now(timezone.utc)
        
        # Calculate current KPI values
        kpi_values = await self._calculate_current_kpis()
        
        # Create KPI snapshot
        kpi_snapshot = {
            'timestamp': now.isoformat(),
            'kpis': kpi_values,
            'period': 'current'
        }
        
        self.kpi_history.append(kpi_snapshot)
        
        # Keep only last 100 snapshots
        if len(self.kpi_history) > 100:
            self.kpi_history = self.kpi_history[-100:]
        
        self.stats['last_update'] = now.isoformat()
    
    async def _calculate_current_kpis(self) -> Dict[str, Any]:
        """Calculate current KPI values"""
        now = datetime.now(timezone.utc)
        six_months_ago = now - timedelta(days=180)
        
        # Filter events for last 6 months
        recent_events = [
            event for event in self.registration_history
            if datetime.fromisoformat(event['timestamp']) >= six_months_ago
        ]
        
        # Calculate KPIs
        total_applications = len([e for e in recent_events if e['event_type'] == 'submitted'])
        approved_applications = len([e for e in recent_events if e['event_type'] == 'approved'])
        rejected_applications = len([e for e in recent_events if e['event_type'] == 'rejected'])
        
        # Approval rate
        approval_rate = (
            (approved_applications / total_applications * 100) 
            if total_applications > 0 else 0
        )
        
        # Rejection rate
        rejection_rate = (
            (rejected_applications / total_applications * 100) 
            if total_applications > 0 else 0
        )
        
        # Average onboarding time
        completed_events = [e for e in recent_events if e['processing_time_days'] is not None]
        avg_onboarding_time = (
            statistics.mean([e['processing_time_days'] for e in completed_events])
            if completed_events else 0
        )
        
        # Sector distribution
        sectors = [e['sector'] for e in recent_events if e['event_type'] == 'approved']
        unique_sectors = len(set(sectors))
        
        return {
            'total_registrations_6_months': approved_applications,
            'approval_rate': round(approval_rate, 1),
            'rejection_rate': round(rejection_rate, 1),
            'average_onboarding_time': round(avg_onboarding_time, 1),
            'unique_sectors_covered': unique_sectors,
            'monthly_average': round(approved_applications / 6, 1) if approved_applications > 0 else 0
        }
    
    async def get_kpi_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive KPI dashboard"""
        try:
            current_kpis = await self._calculate_current_kpis()
            
            # Create KPI objects with status
            kpis = []
            
            # Taxpayer Registration KPI
            taxpayer_kpi = RegistrationKPI(
                kpi_id='taxpayer_registrations',
                name='Taxpayer Registrations (6 months)',
                description='Number of taxpayers onboarded in 6 months',
                target_value=self.kpi_targets['taxpayers_per_6_months'],
                current_value=current_kpis['total_registrations_6_months'],
                unit='taxpayers',
                period='6_months',
                status=self._get_kpi_status(
                    current_kpis['total_registrations_6_months'],
                    self.kpi_targets['taxpayers_per_6_months']
                ),
                trend=self._calculate_trend('total_registrations_6_months'),
                last_updated=datetime.now(timezone.utc),
                progress_percentage=round(
                    (current_kpis['total_registrations_6_months'] / 
                     self.kpi_targets['taxpayers_per_6_months'] * 100), 1
                )
            )
            kpis.append(taxpayer_kpi)
            
            # Approval Rate KPI
            approval_kpi = RegistrationKPI(
                kpi_id='approval_rate',
                name='Approval Rate',
                description='Percentage of applications approved',
                target_value=self.kpi_targets['approval_rate_minimum'],
                current_value=current_kpis['approval_rate'],
                unit='percentage',
                period='6_months',
                status=self._get_kpi_status(
                    current_kpis['approval_rate'],
                    self.kpi_targets['approval_rate_minimum']
                ),
                trend=self._calculate_trend('approval_rate'),
                last_updated=datetime.now(timezone.utc),
                progress_percentage=round(
                    (current_kpis['approval_rate'] / 
                     self.kpi_targets['approval_rate_minimum'] * 100), 1
                )
            )
            kpis.append(approval_kpi)
            
            # Onboarding Time KPI
            onboarding_kpi = RegistrationKPI(
                kpi_id='onboarding_time',
                name='Average Onboarding Time',
                description='Average time to complete onboarding',
                target_value=self.kpi_targets['max_onboarding_days'],
                current_value=current_kpis['average_onboarding_time'],
                unit='days',
                period='6_months',
                status=self._get_kpi_status(
                    self.kpi_targets['max_onboarding_days'],  # Reversed for time
                    current_kpis['average_onboarding_time']
                ),
                trend=self._calculate_trend('average_onboarding_time'),
                last_updated=datetime.now(timezone.utc),
                progress_percentage=round(
                    (self.kpi_targets['max_onboarding_days'] / 
                     max(current_kpis['average_onboarding_time'], 1) * 100), 1
                )
            )
            kpis.append(onboarding_kpi)
            
            # Sector Coverage KPI
            sector_kpi = RegistrationKPI(
                kpi_id='sector_coverage',
                name='Sector Coverage',
                description='Number of different sectors covered',
                target_value=self.kpi_targets['minimum_sectors'],
                current_value=current_kpis['unique_sectors_covered'],
                unit='sectors',
                period='6_months',
                status=self._get_kpi_status(
                    current_kpis['unique_sectors_covered'],
                    self.kpi_targets['minimum_sectors']
                ),
                trend=self._calculate_trend('unique_sectors_covered'),
                last_updated=datetime.now(timezone.utc),
                progress_percentage=round(
                    (current_kpis['unique_sectors_covered'] / 
                     self.kpi_targets['minimum_sectors'] * 100), 1
                )
            )
            kpis.append(sector_kpi)
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'kpis': [kpi.to_dict() for kpi in kpis],
                'overall_compliance': self._calculate_overall_compliance(kpis),
                'milestones': [milestone.to_dict() for milestone in self.milestones.values()],
                'summary': {
                    'total_kpis': len(kpis),
                    'compliant_kpis': len([kpi for kpi in kpis if kpi.status == KPIStatus.ON_TRACK]),
                    'at_risk_kpis': len([kpi for kpi in kpis if kpi.status == KPIStatus.AT_RISK]),
                    'behind_kpis': len([kpi for kpi in kpis if kpi.status == KPIStatus.BEHIND])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating KPI dashboard: {str(e)}")
            raise
    
    def _get_kpi_status(self, current: float, target: float) -> KPIStatus:
        """Determine KPI status based on current vs target"""
        if current >= target:
            return KPIStatus.ON_TRACK
        elif current >= target * 0.8:
            return KPIStatus.AT_RISK
        else:
            return KPIStatus.BEHIND
    
    def _calculate_trend(self, metric: str) -> str:
        """Calculate trend for a metric"""
        if len(self.kpi_history) < 2:
            return 'stable'
        
        recent_values = [
            snapshot['kpis'].get(metric, 0) 
            for snapshot in self.kpi_history[-5:]
        ]
        
        if len(recent_values) < 2:
            return 'stable'
        
        # Simple trend calculation
        if recent_values[-1] > recent_values[0]:
            return 'improving'
        elif recent_values[-1] < recent_values[0]:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_overall_compliance(self, kpis: List[RegistrationKPI]) -> Dict[str, Any]:
        """Calculate overall compliance score"""
        if not kpis:
            return {'score': 0, 'status': 'unknown'}
        
        total_score = 0
        max_score = len(kpis) * 100
        
        for kpi in kpis:
            if kpi.status == KPIStatus.ON_TRACK:
                total_score += 100
            elif kpi.status == KPIStatus.AT_RISK:
                total_score += 70
            elif kpi.status == KPIStatus.BEHIND:
                total_score += 30
        
        overall_score = (total_score / max_score) * 100
        
        if overall_score >= 90:
            status = 'excellent'
        elif overall_score >= 80:
            status = 'good'
        elif overall_score >= 60:
            status = 'acceptable'
        else:
            status = 'poor'
        
        return {
            'score': round(overall_score, 1),
            'status': status,
            'max_possible': max_score,
            'current_score': total_score
        }
    
    async def generate_forecast(self, months_ahead: int = 6) -> RegistrationForecast:
        """Generate registration forecast"""
        try:
            # Simple linear forecast based on current trend
            recent_events = self.registration_history[-30:]  # Last 30 events
            
            if not recent_events:
                return RegistrationForecast(
                    forecast_id=f"FORECAST_{datetime.now(timezone.utc).timestamp()}",
                    period=f"{months_ahead}_months",
                    forecasted_registrations=0,
                    confidence_level=0.0,
                    factors=['insufficient_data'],
                    generated_at=datetime.now(timezone.utc)
                )
            
            # Calculate average monthly registrations
            approved_events = [e for e in recent_events if e['event_type'] == 'approved']
            monthly_average = len(approved_events) / 1  # Assume 1 month of data
            
            # Simple forecast
            forecasted_registrations = int(monthly_average * months_ahead)
            
            # Calculate confidence based on data consistency
            confidence = min(90.0, len(recent_events) / 30 * 100)
            
            return RegistrationForecast(
                forecast_id=f"FORECAST_{datetime.now(timezone.utc).timestamp()}",
                period=f"{months_ahead}_months",
                forecasted_registrations=forecasted_registrations,
                confidence_level=round(confidence, 1),
                factors=['historical_trend', 'seasonal_patterns', 'current_pipeline'],
                generated_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating forecast: {str(e)}")
            raise
    
    async def get_registration_analytics(self) -> Dict[str, Any]:
        """Get comprehensive registration analytics"""
        try:
            current_kpis = await self._calculate_current_kpis()
            
            # Time series analysis
            monthly_registrations = self._analyze_monthly_trends()
            
            # Taxpayer type analysis
            type_distribution = self._analyze_taxpayer_types()
            
            # Sector analysis
            sector_distribution = self._analyze_sector_coverage()
            
            # Performance metrics
            performance_metrics = self._calculate_performance_metrics()
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'current_kpis': current_kpis,
                'monthly_trends': monthly_registrations,
                'taxpayer_distribution': type_distribution,
                'sector_analysis': sector_distribution,
                'performance_metrics': performance_metrics,
                'forecast': (await self.generate_forecast()).to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating analytics: {str(e)}")
            raise
    
    def _analyze_monthly_trends(self) -> Dict[str, Any]:
        """Analyze monthly registration trends"""
        monthly_data = defaultdict(int)
        
        for event in self.registration_history:
            if event['event_type'] == 'approved':
                month_key = datetime.fromisoformat(event['timestamp']).strftime('%Y-%m')
                monthly_data[month_key] += 1
        
        return {
            'monthly_registrations': dict(monthly_data),
            'trend': 'increasing' if len(monthly_data) > 1 else 'stable',
            'peak_month': max(monthly_data.items(), key=lambda x: x[1])[0] if monthly_data else None
        }
    
    def _analyze_taxpayer_types(self) -> Dict[str, Any]:
        """Analyze taxpayer type distribution"""
        type_counts = Counter()
        
        for event in self.registration_history:
            if event['event_type'] == 'approved':
                type_counts[event['taxpayer_type']] += 1
        
        total = sum(type_counts.values())
        
        return {
            'distribution': dict(type_counts),
            'percentages': {
                type_name: round((count / total * 100), 1) 
                for type_name, count in type_counts.items()
            } if total > 0 else {},
            'most_common': type_counts.most_common(3)
        }
    
    def _analyze_sector_coverage(self) -> Dict[str, Any]:
        """Analyze sector coverage"""
        sector_counts = Counter()
        
        for event in self.registration_history:
            if event['event_type'] == 'approved':
                sector_counts[event['sector']] += 1
        
        return {
            'sectors_covered': len(sector_counts),
            'sector_distribution': dict(sector_counts),
            'target_sectors': self.kpi_targets['minimum_sectors'],
            'coverage_status': 'achieved' if len(sector_counts) >= self.kpi_targets['minimum_sectors'] else 'in_progress'
        }
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        total_events = len(self.registration_history)
        
        if total_events == 0:
            return {
                'total_processed': 0,
                'success_rate': 0,
                'average_processing_time': 0,
                'efficiency_score': 0
            }
        
        approved_count = len([e for e in self.registration_history if e['event_type'] == 'approved'])
        success_rate = (approved_count / total_events * 100) if total_events > 0 else 0
        
        # Calculate average processing time
        processing_times = [
            e['processing_time_days'] for e in self.registration_history 
            if e['processing_time_days'] is not None
        ]
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        
        # Calculate efficiency score
        efficiency_score = (success_rate * 0.6) + ((30 - avg_processing_time) * 2 if avg_processing_time > 0 else 0)
        efficiency_score = max(0, min(100, efficiency_score))
        
        return {
            'total_processed': total_events,
            'success_rate': round(success_rate, 1),
            'average_processing_time': round(avg_processing_time, 1),
            'efficiency_score': round(efficiency_score, 1)
        }
    
    async def get_milestone_status(self) -> Dict[str, Any]:
        """Get milestone achievement status"""
        milestone_data = []
        
        for milestone in self.milestones.values():
            milestone_info = milestone.to_dict()
            milestone_info['progress_percentage'] = round(
                (milestone.current_value / milestone.target_value * 100), 1
            ) if milestone.target_value > 0 else 0
            
            milestone_data.append(milestone_info)
        
        # Sort by target date
        milestone_data.sort(key=lambda x: x['target_date'])
        
        achieved_count = len([m for m in self.milestones.values() if m.achieved])
        total_count = len(self.milestones)
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'milestones': milestone_data,
            'summary': {
                'total_milestones': total_count,
                'achieved_milestones': achieved_count,
                'achievement_rate': round((achieved_count / total_count * 100), 1) if total_count > 0 else 0,
                'next_milestone': self._get_next_milestone()
            }
        }
    
    def _get_next_milestone(self) -> Optional[Dict[str, Any]]:
        """Get the next upcoming milestone"""
        now = datetime.now(timezone.utc)
        
        upcoming_milestones = [
            m for m in self.milestones.values()
            if not m.achieved and m.target_date > now
        ]
        
        if not upcoming_milestones:
            return None
        
        next_milestone = min(upcoming_milestones, key=lambda x: x.target_date)
        days_until = (next_milestone.target_date - now).days
        
        return {
            'milestone_id': next_milestone.milestone_id,
            'title': next_milestone.title,
            'target_date': next_milestone.target_date.isoformat(),
            'days_until': days_until,
            'progress_percentage': round(
                (next_milestone.current_value / next_milestone.target_value * 100), 1
            )
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Get tracker health status"""
        current_kpis = await self._calculate_current_kpis()
        
        # Check KPI health
        behind_kpis = 0
        if current_kpis['total_registrations_6_months'] < self.kpi_targets['taxpayers_per_6_months'] * 0.8:
            behind_kpis += 1
        if current_kpis['approval_rate'] < self.kpi_targets['approval_rate_minimum']:
            behind_kpis += 1
        
        status = "healthy"
        if behind_kpis >= 2:
            status = "critical"
        elif behind_kpis >= 1:
            status = "degraded"
        
        return {
            'status': status,
            'service': 'registration_tracker',
            'tracked_events': len(self.registration_history),
            'kpi_compliance': 4 - behind_kpis,
            'total_kpis': 4,
            'last_update': self.stats['last_update'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup tracker resources"""
        self.logger.info("Registration tracker cleanup initiated")
        
        # Log final statistics
        self.logger.info(f"Final tracking statistics: {self.stats}")
        
        self.logger.info("Registration tracker cleanup completed")


# Factory function
def create_registration_tracker() -> RegistrationTracker:
    """Create registration tracker with standard configuration"""
    return RegistrationTracker()