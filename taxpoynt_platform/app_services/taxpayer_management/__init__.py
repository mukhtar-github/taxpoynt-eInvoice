"""
TaxPoynt Platform - APP Services: Taxpayer Management
Comprehensive taxpayer onboarding and registration tracking for FIRS KPI compliance
"""

from .taxpayer_onboarding import (
    TaxpayerOnboardingService,
    TaxpayerProfile,
    OnboardingApplication,
    OnboardingDocument,
    OnboardingTask,
    OnboardingWorkflow,
    OnboardingStatus,
    TaxpayerType,
    OnboardingStep,
    create_taxpayer_onboarding_service,
    get_taxpayer_classification,
    get_required_documents_by_type
)

from .registration_tracker import (
    RegistrationTracker,
    RegistrationKPI,
    RegistrationMilestone,
    RegistrationForecast,
    RegistrationMetric,
    KPIStatus,
    create_registration_tracker
)

from .compliance_monitor import (
    ComplianceMonitor,
    ComplianceCheck,
    ComplianceIssue,
    ComplianceRule,
    ComplianceStatus,
    ComplianceMetrics,
    ComplianceAlert,
    ComplianceRemediation,
    create_compliance_monitor
)

from .analytics_service import (
    TaxpayerAnalyticsService,
    AnalyticsReport,
    AnalyticsFilter,
    KPIMetrics,
    OnboardingMetrics,
    ComplianceMetrics,
    PerformanceMetrics,
    TrendAnalysis,
    ReportType,
    TimeFrame
)

__version__ = "1.0.0"

__all__ = [
    # Taxpayer Onboarding
    "TaxpayerOnboardingService",
    "TaxpayerProfile",
    "OnboardingApplication",
    "OnboardingDocument",
    "OnboardingTask",
    "OnboardingWorkflow",
    "OnboardingStatus",
    "TaxpayerType",
    "OnboardingStep",
    "create_taxpayer_onboarding_service",
    "get_taxpayer_classification",
    "get_required_documents_by_type",
    
    # Registration Tracker
    "RegistrationTracker",
    "RegistrationKPI",
    "RegistrationMilestone",
    "RegistrationForecast",
    "RegistrationMetric",
    "KPIStatus",
    "create_registration_tracker",
    
    # Compliance Monitor
    "ComplianceMonitor",
    "ComplianceCheck",
    "ComplianceIssue",
    "ComplianceRule",
    "ComplianceStatus",
    "ComplianceMetrics",
    "ComplianceAlert",
    "ComplianceRemediation",
    "create_compliance_monitor",
    
    # Analytics Service
    "TaxpayerAnalyticsService",
    "AnalyticsReport",
    "AnalyticsFilter",
    "KPIMetrics",
    "OnboardingMetrics",
    "ComplianceMetrics",
    "PerformanceMetrics",
    "TrendAnalysis",
    "ReportType",
    "TimeFrame"
]


class TaxpayerManagementService:
    """
    Comprehensive taxpayer management service
    Coordinates onboarding and registration tracking for FIRS KPI compliance
    """
    
    def __init__(self):
        """Initialize taxpayer management service"""
        self.onboarding_service = create_taxpayer_onboarding_service()
        self.registration_tracker = create_registration_tracker()
        self.compliance_monitor = create_compliance_monitor()
        self.analytics_service = TaxpayerAnalyticsService()
        self.logger = __import__('logging').getLogger(__name__)
        
        # Integration state
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the taxpayer management service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing taxpayer management service")
        
        # Services are primarily synchronous, but we can add async initialization here
        self.is_initialized = True
        
        self.logger.info("Taxpayer management service initialized")
    
    async def onboard_taxpayer(self, taxpayer_profile: TaxpayerProfile) -> dict:
        """
        Complete taxpayer onboarding process
        
        Args:
            taxpayer_profile: Taxpayer profile information
            
        Returns:
            Onboarding result with tracking information
        """
        try:
            # Submit onboarding application
            application_id = await self.onboarding_service.submit_application(taxpayer_profile)
            
            # Get the application for tracking
            application_status = await self.onboarding_service.get_application_status(application_id)
            application = application_status['application']
            
            # Create application object for tracking
            from .taxpayer_onboarding import OnboardingApplication
            app_obj = OnboardingApplication(
                application_id=application['application_id'],
                taxpayer_profile=taxpayer_profile,
                status=OnboardingStatus(application['status']),
                current_step=OnboardingStep(application['current_step']),
                submitted_at=__import__('datetime').datetime.fromisoformat(application['submitted_at']),
                expected_completion=__import__('datetime').datetime.fromisoformat(application['expected_completion']) if application.get('expected_completion') else None
            )
            
            # Track the submission
            await self.registration_tracker.track_registration(app_obj, 'submitted')
            
            return {
                'application_id': application_id,
                'status': 'submitted',
                'expected_completion': application.get('expected_completion'),
                'tracking_enabled': True,
                'kpi_impact': await self._calculate_kpi_impact(taxpayer_profile)
            }
            
        except Exception as e:
            self.logger.error(f"Error onboarding taxpayer: {str(e)}")
            raise
    
    async def _calculate_kpi_impact(self, taxpayer_profile: TaxpayerProfile) -> dict:
        """Calculate KPI impact of new taxpayer"""
        kpi_dashboard = await self.registration_tracker.get_kpi_dashboard()
        
        # Calculate impact on KPIs
        current_registrations = None
        current_sectors = None
        
        for kpi in kpi_dashboard['kpis']:
            if kpi['kpi_id'] == 'taxpayer_registrations':
                current_registrations = kpi['current_value']
            elif kpi['kpi_id'] == 'sector_coverage':
                current_sectors = kpi['current_value']
        
        return {
            'registration_progress': f"{current_registrations + 1}/100" if current_registrations is not None else "1/100",
            'sector_impact': f"New sector: {taxpayer_profile.sector}",
            'taxpayer_type_diversity': f"Added {taxpayer_profile.taxpayer_type.value}"
        }
    
    async def approve_taxpayer(self, application_id: str) -> dict:
        """
        Approve taxpayer application and update tracking
        
        Args:
            application_id: Application ID to approve
            
        Returns:
            Approval result with tracking update
        """
        try:
            # Get application details
            application_status = await self.onboarding_service.get_application_status(application_id)
            application = application_status['application']
            
            # Create application object for tracking
            from .taxpayer_onboarding import OnboardingApplication, TaxpayerProfile
            
            taxpayer_profile = TaxpayerProfile(
                taxpayer_id=application['taxpayer_profile']['taxpayer_id'],
                tin=application['taxpayer_profile']['tin'],
                business_name=application['taxpayer_profile']['business_name'],
                business_registration_number=application['taxpayer_profile']['business_registration_number'],
                taxpayer_type=TaxpayerType(application['taxpayer_profile']['taxpayer_type']),
                sector=application['taxpayer_profile']['sector'],
                contact_email=application['taxpayer_profile']['contact_email'],
                contact_phone=application['taxpayer_profile']['contact_phone'],
                address=application['taxpayer_profile']['address'],
                state=application['taxpayer_profile']['state'],
                lga=application['taxpayer_profile']['lga']
            )
            
            app_obj = OnboardingApplication(
                application_id=application['application_id'],
                taxpayer_profile=taxpayer_profile,
                status=OnboardingStatus.ACTIVE,
                current_step=OnboardingStep.ACTIVATION,
                submitted_at=__import__('datetime').datetime.fromisoformat(application['submitted_at']),
                actual_completion=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            )
            
            # Track the approval
            await self.registration_tracker.track_registration(app_obj, 'approved')
            
            # Get updated KPI status
            kpi_dashboard = await self.registration_tracker.get_kpi_dashboard()
            
            return {
                'application_id': application_id,
                'status': 'approved',
                'taxpayer_active': True,
                'kpi_update': kpi_dashboard['summary'],
                'milestone_progress': await self._check_milestone_progress()
            }
            
        except Exception as e:
            self.logger.error(f"Error approving taxpayer: {str(e)}")
            raise
    
    async def _check_milestone_progress(self) -> dict:
        """Check milestone progress after approval"""
        milestone_status = await self.registration_tracker.get_milestone_status()
        
        return {
            'milestones_achieved': milestone_status['summary']['achieved_milestones'],
            'total_milestones': milestone_status['summary']['total_milestones'],
            'next_milestone': milestone_status['summary']['next_milestone']
        }
    
    async def get_kpi_compliance_report(self) -> dict:
        """Get comprehensive KPI compliance report"""
        try:
            # Get KPI dashboard
            kpi_dashboard = await self.registration_tracker.get_kpi_dashboard()
            
            # Get onboarding analytics
            onboarding_analytics = await self.onboarding_service.get_onboarding_analytics()
            
            # Get registration analytics
            registration_analytics = await self.registration_tracker.get_registration_analytics()
            
            # Get milestone status
            milestone_status = await self.registration_tracker.get_milestone_status()
            
            # Calculate overall compliance
            overall_compliance = self._calculate_overall_compliance(kpi_dashboard['kpis'])
            
            return {
                'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'overall_compliance': overall_compliance,
                'kpi_dashboard': kpi_dashboard,
                'onboarding_analytics': onboarding_analytics,
                'registration_analytics': registration_analytics,
                'milestone_status': milestone_status,
                'firs_readiness': self._assess_firs_readiness(kpi_dashboard['kpis']),
                'recommendations': self._generate_recommendations(kpi_dashboard['kpis'])
            }
            
        except Exception as e:
            self.logger.error(f"Error generating KPI compliance report: {str(e)}")
            raise
    
    def _calculate_overall_compliance(self, kpis: list) -> dict:
        """Calculate overall KPI compliance score"""
        if not kpis:
            return {'score': 0, 'status': 'unknown', 'compliant_kpis': 0}
        
        total_score = 0
        compliant_count = 0
        
        for kpi in kpis:
            if kpi['status'] == 'on_track':
                total_score += 100
                compliant_count += 1
            elif kpi['status'] == 'at_risk':
                total_score += 70
            elif kpi['status'] == 'behind':
                total_score += 30
        
        overall_score = total_score / len(kpis)
        
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
            'compliant_kpis': compliant_count,
            'total_kpis': len(kpis)
        }
    
    def _assess_firs_readiness(self, kpis: list) -> dict:
        """Assess readiness for FIRS KPI compliance"""
        taxpayer_kpi = next((kpi for kpi in kpis if kpi['kpi_id'] == 'taxpayer_registrations'), None)
        
        if not taxpayer_kpi:
            return {'ready': False, 'reason': 'No taxpayer registration data'}
        
        progress = taxpayer_kpi['progress_percentage']
        
        if progress >= 100:
            return {
                'ready': True,
                'status': 'compliant',
                'progress': progress,
                'message': 'FIRS KPI target achieved'
            }
        elif progress >= 80:
            return {
                'ready': True,
                'status': 'on_track',
                'progress': progress,
                'message': 'On track to meet FIRS KPI target'
            }
        elif progress >= 60:
            return {
                'ready': False,
                'status': 'at_risk',
                'progress': progress,
                'message': 'At risk of missing FIRS KPI target'
            }
        else:
            return {
                'ready': False,
                'status': 'behind',
                'progress': progress,
                'message': 'Behind FIRS KPI target'
            }
    
    def _generate_recommendations(self, kpis: list) -> list:
        """Generate recommendations based on KPI status"""
        recommendations = []
        
        for kpi in kpis:
            if kpi['status'] == 'behind':
                if kpi['kpi_id'] == 'taxpayer_registrations':
                    recommendations.append({
                        'priority': 'high',
                        'category': 'registration',
                        'action': 'Accelerate taxpayer onboarding campaigns',
                        'target': 'Increase monthly registration rate by 50%'
                    })
                elif kpi['kpi_id'] == 'approval_rate':
                    recommendations.append({
                        'priority': 'high',
                        'category': 'process',
                        'action': 'Improve onboarding process efficiency',
                        'target': 'Reduce rejection rate and processing time'
                    })
                elif kpi['kpi_id'] == 'sector_coverage':
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'outreach',
                        'action': 'Target underrepresented sectors',
                        'target': 'Achieve minimum 4 sector coverage'
                    })
            elif kpi['status'] == 'at_risk':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'monitoring',
                    'action': f'Monitor {kpi["name"]} closely',
                    'target': 'Prevent KPI degradation'
                })
        
        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'category': 'maintenance',
                'action': 'Maintain current performance levels',
                'target': 'Continue meeting all KPI targets'
            })
        
        return recommendations
    
    async def get_taxpayer_pipeline(self) -> dict:
        """Get taxpayer pipeline status"""
        try:
            # Get pending applications
            pending_apps = await self.onboarding_service.get_pending_applications()
            
            # Get onboarding analytics
            analytics = await self.onboarding_service.get_onboarding_analytics()
            
            # Calculate pipeline metrics
            pipeline_metrics = {
                'total_in_pipeline': len(pending_apps),
                'high_priority': len([app for app in pending_apps if app['priority'] == 'high']),
                'average_processing_time': analytics['kpi_metrics']['average_onboarding_time'],
                'monthly_completion_rate': analytics['kpi_metrics']['approval_rate']
            }
            
            return {
                'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'pipeline_metrics': pipeline_metrics,
                'pending_applications': pending_apps,
                'capacity_analysis': self._analyze_processing_capacity(pending_apps),
                'bottlenecks': self._identify_bottlenecks(pending_apps)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting taxpayer pipeline: {str(e)}")
            raise
    
    def _analyze_processing_capacity(self, pending_apps: list) -> dict:
        """Analyze processing capacity"""
        if not pending_apps:
            return {'status': 'available', 'utilization': 0}
        
        high_priority_count = len([app for app in pending_apps if app['priority'] == 'high'])
        total_count = len(pending_apps)
        
        utilization = min(100, (total_count / 50) * 100)  # Assume capacity of 50
        
        if utilization >= 90:
            status = 'overloaded'
        elif utilization >= 70:
            status = 'high'
        elif utilization >= 50:
            status = 'medium'
        else:
            status = 'available'
        
        return {
            'status': status,
            'utilization': round(utilization, 1),
            'high_priority_count': high_priority_count,
            'total_pending': total_count
        }
    
    def _identify_bottlenecks(self, pending_apps: list) -> list:
        """Identify processing bottlenecks"""
        bottlenecks = []
        
        if not pending_apps:
            return bottlenecks
        
        # Analyze by processing step
        step_counts = {}
        for app in pending_apps:
            step = app['current_step']
            step_counts[step] = step_counts.get(step, 0) + 1
        
        # Find bottlenecks
        total_apps = len(pending_apps)
        for step, count in step_counts.items():
            if count > total_apps * 0.3:  # More than 30% stuck in one step
                bottlenecks.append({
                    'type': 'processing_step',
                    'step': step,
                    'affected_applications': count,
                    'percentage': round((count / total_apps) * 100, 1),
                    'recommendation': f'Increase resources for {step} processing'
                })
        
        # Check for overdue applications
        overdue_count = len([app for app in pending_apps if app['days_pending'] > 30])
        if overdue_count > 0:
            bottlenecks.append({
                'type': 'overdue_applications',
                'affected_applications': overdue_count,
                'percentage': round((overdue_count / total_apps) * 100, 1),
                'recommendation': 'Prioritize overdue applications for immediate processing'
            })
        
        return bottlenecks
    
    async def health_check(self) -> dict:
        """Get service health status"""
        try:
            # Check individual service health
            onboarding_health = await self.onboarding_service.health_check()
            tracker_health = await self.registration_tracker.health_check()
            compliance_health = await self.compliance_monitor.health_check()
            
            # Determine overall health
            overall_status = "healthy"
            if (onboarding_health['status'] == 'degraded' or 
                tracker_health['status'] == 'degraded' or
                compliance_health['status'] == 'degraded'):
                overall_status = "degraded"
            elif (onboarding_health['status'] == 'critical' or 
                  tracker_health['status'] == 'critical' or
                  compliance_health['status'] == 'critical'):
                overall_status = "critical"
            
            return {
                'status': overall_status,
                'service': 'taxpayer_management',
                'components': {
                    'onboarding_service': onboarding_health,
                    'registration_tracker': tracker_health,
                    'compliance_monitor': compliance_health,
                    'analytics_service': {'status': 'healthy'}  # Analytics service doesn't need health check
                },
                'is_initialized': self.is_initialized,
                'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                'status': 'error',
                'service': 'taxpayer_management',
                'error': str(e),
                'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Taxpayer management service cleanup initiated")
        
        try:
            # Cleanup individual services
            await self.onboarding_service.cleanup()
            await self.registration_tracker.cleanup()
            await self.compliance_monitor.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Taxpayer management service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_taxpayer_management_service() -> TaxpayerManagementService:
    """Create taxpayer management service with all components"""
    return TaxpayerManagementService()


def get_firs_kpi_requirements() -> dict:
    """Get FIRS KPI requirements for taxpayer management"""
    return {
        'taxpayer_onboarding': {
            'target': 100,
            'period': '6 months',
            'description': 'Minimum 100 taxpayers onboarded per APP within 6 months'
        },
        'approval_rate': {
            'target': 85.0,
            'unit': 'percentage',
            'description': 'Minimum 85% approval rate for applications'
        },
        'processing_time': {
            'target': 30,
            'unit': 'days',
            'description': 'Maximum 30 days for onboarding process completion'
        },
        'sector_coverage': {
            'target': 4,
            'unit': 'sectors',
            'description': 'Minimum 4 major sectors represented in taxpayer base'
        }
    }