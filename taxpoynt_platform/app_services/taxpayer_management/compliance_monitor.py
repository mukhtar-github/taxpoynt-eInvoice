"""
APP Service: Taxpayer Compliance Monitor
Monitors taxpayer compliance requirements and regulatory adherence
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter

from .taxpayer_onboarding import TaxpayerProfile, TaxpayerType


class ComplianceRequirement(str, Enum):
    """Taxpayer compliance requirements"""
    TIN_VALIDATION = "tin_validation"
    BUSINESS_REGISTRATION = "business_registration"
    TAX_CLEARANCE = "tax_clearance"
    FINANCIAL_STATEMENTS = "financial_statements"
    MONTHLY_RETURNS = "monthly_returns"
    ANNUAL_RETURNS = "annual_returns"
    WITHHOLDING_TAX = "withholding_tax"
    VAT_REGISTRATION = "vat_registration"
    AUDIT_REQUIREMENTS = "audit_requirements"
    SECTOR_SPECIFIC = "sector_specific"


class ComplianceStatus(str, Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    PENDING_REVIEW = "pending_review"
    EXEMPTED = "exempted"
    SUSPENDED = "suspended"


class ComplianceSeverity(str, Enum):
    """Compliance violation severity"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRule:
    """Taxpayer compliance rule definition"""
    rule_id: str
    requirement: ComplianceRequirement
    taxpayer_type: TaxpayerType
    sector: Optional[str]
    description: str
    frequency: str  # daily, weekly, monthly, quarterly, annually
    grace_period_days: int
    severity: ComplianceSeverity
    mandatory: bool
    penalty_description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceRecord:
    """Individual compliance record for a taxpayer"""
    record_id: str
    taxpayer_id: str
    requirement: ComplianceRequirement
    status: ComplianceStatus
    due_date: datetime
    submitted_date: Optional[datetime]
    verified_date: Optional[datetime]
    compliance_score: float
    violations: List[str]
    remediation_steps: List[str]
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['due_date'] = self.due_date.isoformat()
        if self.submitted_date:
            data['submitted_date'] = self.submitted_date.isoformat()
        if self.verified_date:
            data['verified_date'] = self.verified_date.isoformat()
        return data


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    violation_id: str
    taxpayer_id: str
    requirement: ComplianceRequirement
    violation_type: str
    severity: ComplianceSeverity
    detected_date: datetime
    description: str
    impact: str
    remediation_deadline: datetime
    resolved: bool = False
    resolved_date: Optional[datetime] = None
    penalty_applied: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['detected_date'] = self.detected_date.isoformat()
        data['remediation_deadline'] = self.remediation_deadline.isoformat()
        if self.resolved_date:
            data['resolved_date'] = self.resolved_date.isoformat()
        return data


@dataclass
class ComplianceAssessment:
    """Comprehensive compliance assessment"""
    assessment_id: str
    taxpayer_id: str
    assessment_date: datetime
    overall_score: float
    overall_status: ComplianceStatus
    requirements_assessed: int
    compliant_requirements: int
    violations_count: int
    recommendations: List[str]
    next_assessment_date: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['assessment_date'] = self.assessment_date.isoformat()
        data['next_assessment_date'] = self.next_assessment_date.isoformat()
        return data


class ComplianceRuleEngine:
    """Rule engine for taxpayer compliance requirements"""
    
    @staticmethod
    def get_compliance_rules() -> List[ComplianceRule]:
        """Get all compliance rules"""
        return [
            # TIN Validation Rules
            ComplianceRule(
                rule_id="TIN_001",
                requirement=ComplianceRequirement.TIN_VALIDATION,
                taxpayer_type=TaxpayerType.LARGE_TAXPAYER,
                sector=None,
                description="Valid TIN certificate must be maintained",
                frequency="annually",
                grace_period_days=30,
                severity=ComplianceSeverity.CRITICAL,
                mandatory=True,
                penalty_description="Account suspension until TIN is validated"
            ),
            
            # Business Registration Rules
            ComplianceRule(
                rule_id="BR_001",
                requirement=ComplianceRequirement.BUSINESS_REGISTRATION,
                taxpayer_type=TaxpayerType.MEDIUM_TAXPAYER,
                sector=None,
                description="Valid business registration certificate required",
                frequency="annually",
                grace_period_days=60,
                severity=ComplianceSeverity.HIGH,
                mandatory=True,
                penalty_description="Penalty fee and compliance review"
            ),
            
            # Tax Clearance Rules
            ComplianceRule(
                rule_id="TC_001",
                requirement=ComplianceRequirement.TAX_CLEARANCE,
                taxpayer_type=TaxpayerType.LARGE_TAXPAYER,
                sector=None,
                description="Current tax clearance certificate required",
                frequency="annually",
                grace_period_days=30,
                severity=ComplianceSeverity.HIGH,
                mandatory=True,
                penalty_description="Service restrictions until clearance obtained"
            ),
            
            # Financial Statements Rules
            ComplianceRule(
                rule_id="FS_001",
                requirement=ComplianceRequirement.FINANCIAL_STATEMENTS,
                taxpayer_type=TaxpayerType.LARGE_TAXPAYER,
                sector=None,
                description="Audited financial statements required annually",
                frequency="annually",
                grace_period_days=90,
                severity=ComplianceSeverity.MEDIUM,
                mandatory=True,
                penalty_description="Compliance monitoring increase"
            ),
            
            # Monthly Returns Rules
            ComplianceRule(
                rule_id="MR_001",
                requirement=ComplianceRequirement.MONTHLY_RETURNS,
                taxpayer_type=TaxpayerType.LARGE_TAXPAYER,
                sector=None,
                description="Monthly tax returns must be filed",
                frequency="monthly",
                grace_period_days=15,
                severity=ComplianceSeverity.HIGH,
                mandatory=True,
                penalty_description="Late filing penalties apply"
            ),
            
            # VAT Registration Rules
            ComplianceRule(
                rule_id="VAT_001",
                requirement=ComplianceRequirement.VAT_REGISTRATION,
                taxpayer_type=TaxpayerType.LARGE_TAXPAYER,
                sector=None,
                description="VAT registration required for eligible taxpayers",
                frequency="annually",
                grace_period_days=30,
                severity=ComplianceSeverity.HIGH,
                mandatory=True,
                penalty_description="VAT penalties and interest charges"
            ),
            
            # Sector-Specific Rules
            ComplianceRule(
                rule_id="SEC_001",
                requirement=ComplianceRequirement.SECTOR_SPECIFIC,
                taxpayer_type=TaxpayerType.LARGE_TAXPAYER,
                sector="financial_services",
                description="Financial services sector compliance requirements",
                frequency="quarterly",
                grace_period_days=30,
                severity=ComplianceSeverity.HIGH,
                mandatory=True,
                penalty_description="Sector-specific penalties"
            )
        ]
    
    @staticmethod
    def get_rules_for_taxpayer(taxpayer_profile: TaxpayerProfile) -> List[ComplianceRule]:
        """Get applicable compliance rules for a taxpayer"""
        all_rules = ComplianceRuleEngine.get_compliance_rules()
        applicable_rules = []
        
        for rule in all_rules:
            # Check taxpayer type
            if rule.taxpayer_type == taxpayer_profile.taxpayer_type:
                # Check sector if specified
                if rule.sector is None or rule.sector == taxpayer_profile.sector:
                    applicable_rules.append(rule)
        
        return applicable_rules
    
    @staticmethod
    def calculate_compliance_score(compliant_count: int, total_count: int, violations: int) -> float:
        """Calculate compliance score"""
        if total_count == 0:
            return 100.0
        
        base_score = (compliant_count / total_count) * 100
        violation_penalty = violations * 5  # 5% penalty per violation
        
        return max(0, base_score - violation_penalty)


class TaxpayerComplianceMonitor:
    """
    Comprehensive taxpayer compliance monitoring service
    Tracks compliance requirements and violations for all taxpayers
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Compliance tracking data
        self.compliance_records: Dict[str, List[ComplianceRecord]] = defaultdict(list)
        self.violations: Dict[str, List[ComplianceViolation]] = defaultdict(list)
        self.assessments: Dict[str, List[ComplianceAssessment]] = defaultdict(list)
        
        # Rule engine
        self.rule_engine = ComplianceRuleEngine()
        
        # Monitoring statistics
        self.stats = {
            'total_taxpayers_monitored': 0,
            'compliant_taxpayers': 0,
            'non_compliant_taxpayers': 0,
            'total_violations': 0,
            'resolved_violations': 0,
            'average_compliance_score': 0.0,
            'last_assessment_run': None,
            'compliance_trend': 'stable'
        }
    
    async def register_taxpayer_for_monitoring(self, taxpayer_profile: TaxpayerProfile):
        """
        Register taxpayer for compliance monitoring
        
        Args:
            taxpayer_profile: Taxpayer profile to monitor
        """
        try:
            taxpayer_id = taxpayer_profile.taxpayer_id
            
            # Get applicable compliance rules
            applicable_rules = self.rule_engine.get_rules_for_taxpayer(taxpayer_profile)
            
            # Create initial compliance records
            for rule in applicable_rules:
                record = ComplianceRecord(
                    record_id=f"CR_{taxpayer_id}_{rule.rule_id}",
                    taxpayer_id=taxpayer_id,
                    requirement=rule.requirement,
                    status=ComplianceStatus.PENDING_REVIEW,
                    due_date=self._calculate_due_date(rule),
                    submitted_date=None,
                    verified_date=None,
                    compliance_score=0.0,
                    violations=[],
                    remediation_steps=[]
                )
                
                self.compliance_records[taxpayer_id].append(record)
            
            # Update statistics
            self.stats['total_taxpayers_monitored'] += 1
            
            self.logger.info(f"Taxpayer registered for compliance monitoring: {taxpayer_id}")
            
        except Exception as e:
            self.logger.error(f"Error registering taxpayer for monitoring: {str(e)}")
            raise
    
    def _calculate_due_date(self, rule: ComplianceRule) -> datetime:
        """Calculate next due date for compliance requirement"""
        now = datetime.now(timezone.utc)
        
        if rule.frequency == "monthly":
            return now.replace(day=1) + timedelta(days=32)
        elif rule.frequency == "quarterly":
            return now + timedelta(days=90)
        elif rule.frequency == "annually":
            return now + timedelta(days=365)
        else:
            return now + timedelta(days=30)
    
    async def assess_taxpayer_compliance(self, taxpayer_id: str) -> ComplianceAssessment:
        """
        Assess compliance status for a taxpayer
        
        Args:
            taxpayer_id: Taxpayer ID to assess
            
        Returns:
            Comprehensive compliance assessment
        """
        try:
            records = self.compliance_records.get(taxpayer_id, [])
            violations = self.violations.get(taxpayer_id, [])
            
            if not records:
                raise ValueError(f"No compliance records found for taxpayer: {taxpayer_id}")
            
            # Calculate compliance metrics
            total_requirements = len(records)
            compliant_requirements = len([r for r in records if r.status == ComplianceStatus.COMPLIANT])
            active_violations = len([v for v in violations if not v.resolved])
            
            # Calculate compliance score
            compliance_score = self.rule_engine.calculate_compliance_score(
                compliant_requirements, total_requirements, active_violations
            )
            
            # Determine overall status
            if compliance_score >= 90:
                overall_status = ComplianceStatus.COMPLIANT
            elif compliance_score >= 70:
                overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
            else:
                overall_status = ComplianceStatus.NON_COMPLIANT
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(records, violations)
            
            # Create assessment
            assessment = ComplianceAssessment(
                assessment_id=f"ASSESS_{taxpayer_id}_{int(datetime.now(timezone.utc).timestamp())}",
                taxpayer_id=taxpayer_id,
                assessment_date=datetime.now(timezone.utc),
                overall_score=compliance_score,
                overall_status=overall_status,
                requirements_assessed=total_requirements,
                compliant_requirements=compliant_requirements,
                violations_count=active_violations,
                recommendations=recommendations,
                next_assessment_date=datetime.now(timezone.utc) + timedelta(days=90)
            )
            
            # Store assessment
            self.assessments[taxpayer_id].append(assessment)
            
            # Update statistics
            self._update_compliance_stats(overall_status)
            
            self.logger.info(f"Compliance assessment completed for taxpayer: {taxpayer_id}")
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing taxpayer compliance: {str(e)}")
            raise
    
    def _generate_compliance_recommendations(self, 
                                           records: List[ComplianceRecord],
                                           violations: List[ComplianceViolation]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Check for overdue requirements
        overdue_requirements = [
            r for r in records 
            if r.due_date < datetime.now(timezone.utc) and r.status != ComplianceStatus.COMPLIANT
        ]
        
        if overdue_requirements:
            recommendations.append(
                f"Address {len(overdue_requirements)} overdue compliance requirements immediately"
            )
        
        # Check for critical violations
        critical_violations = [v for v in violations if v.severity == ComplianceSeverity.CRITICAL and not v.resolved]
        if critical_violations:
            recommendations.append(
                f"Resolve {len(critical_violations)} critical compliance violations"
            )
        
        # Check for upcoming deadlines
        upcoming_deadlines = [
            r for r in records 
            if r.due_date <= datetime.now(timezone.utc) + timedelta(days=30)
            and r.status != ComplianceStatus.COMPLIANT
        ]
        
        if upcoming_deadlines:
            recommendations.append(
                f"Prepare for {len(upcoming_deadlines)} compliance requirements due within 30 days"
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("Maintain current compliance practices")
        
        return recommendations
    
    def _update_compliance_stats(self, status: ComplianceStatus):
        """Update compliance statistics"""
        if status == ComplianceStatus.COMPLIANT:
            self.stats['compliant_taxpayers'] += 1
        elif status == ComplianceStatus.NON_COMPLIANT:
            self.stats['non_compliant_taxpayers'] += 1
        
        # Update average compliance score
        total_assessments = self.stats['compliant_taxpayers'] + self.stats['non_compliant_taxpayers']
        if total_assessments > 0:
            compliant_rate = (self.stats['compliant_taxpayers'] / total_assessments) * 100
            self.stats['average_compliance_score'] = round(compliant_rate, 1)
    
    async def report_violation(self, 
                             taxpayer_id: str,
                             requirement: ComplianceRequirement,
                             violation_type: str,
                             description: str,
                             severity: ComplianceSeverity) -> str:
        """
        Report a compliance violation
        
        Args:
            taxpayer_id: Taxpayer ID
            requirement: Compliance requirement violated
            violation_type: Type of violation
            description: Violation description
            severity: Violation severity
            
        Returns:
            Violation ID
        """
        try:
            violation_id = f"VIO_{taxpayer_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            violation = ComplianceViolation(
                violation_id=violation_id,
                taxpayer_id=taxpayer_id,
                requirement=requirement,
                violation_type=violation_type,
                severity=severity,
                detected_date=datetime.now(timezone.utc),
                description=description,
                impact=self._calculate_violation_impact(severity),
                remediation_deadline=self._calculate_remediation_deadline(severity)
            )
            
            self.violations[taxpayer_id].append(violation)
            
            # Update compliance record
            await self._update_compliance_record_for_violation(taxpayer_id, requirement, violation_id)
            
            # Update statistics
            self.stats['total_violations'] += 1
            
            self.logger.warning(f"Compliance violation reported: {violation_id}")
            
            return violation_id
            
        except Exception as e:
            self.logger.error(f"Error reporting violation: {str(e)}")
            raise
    
    def _calculate_violation_impact(self, severity: ComplianceSeverity) -> str:
        """Calculate violation impact description"""
        impact_map = {
            ComplianceSeverity.CRITICAL: "Service suspension, immediate action required",
            ComplianceSeverity.HIGH: "Service restrictions, compliance review triggered",
            ComplianceSeverity.MEDIUM: "Monitoring increase, penalty may apply",
            ComplianceSeverity.LOW: "Warning issued, continued monitoring"
        }
        return impact_map.get(severity, "Unknown impact")
    
    def _calculate_remediation_deadline(self, severity: ComplianceSeverity) -> datetime:
        """Calculate remediation deadline based on severity"""
        now = datetime.now(timezone.utc)
        
        deadline_map = {
            ComplianceSeverity.CRITICAL: 7,   # 7 days
            ComplianceSeverity.HIGH: 30,      # 30 days
            ComplianceSeverity.MEDIUM: 60,    # 60 days
            ComplianceSeverity.LOW: 90        # 90 days
        }
        
        days = deadline_map.get(severity, 30)
        return now + timedelta(days=days)
    
    async def _update_compliance_record_for_violation(self, 
                                                    taxpayer_id: str,
                                                    requirement: ComplianceRequirement,
                                                    violation_id: str):
        """Update compliance record when violation is reported"""
        records = self.compliance_records.get(taxpayer_id, [])
        
        for record in records:
            if record.requirement == requirement:
                record.status = ComplianceStatus.NON_COMPLIANT
                record.violations.append(violation_id)
                record.remediation_steps.append("Address reported violation")
                break
    
    async def resolve_violation(self, violation_id: str, resolution_notes: str) -> bool:
        """
        Resolve a compliance violation
        
        Args:
            violation_id: Violation ID to resolve
            resolution_notes: Resolution notes
            
        Returns:
            True if violation was resolved
        """
        try:
            # Find violation
            violation = None
            taxpayer_id = None
            
            for tid, violations in self.violations.items():
                for v in violations:
                    if v.violation_id == violation_id:
                        violation = v
                        taxpayer_id = tid
                        break
                if violation:
                    break
            
            if not violation:
                return False
            
            # Mark as resolved
            violation.resolved = True
            violation.resolved_date = datetime.now(timezone.utc)
            
            # Update compliance record
            await self._update_compliance_record_for_resolution(taxpayer_id, violation.requirement)
            
            # Update statistics
            self.stats['resolved_violations'] += 1
            
            self.logger.info(f"Violation resolved: {violation_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving violation: {str(e)}")
            return False
    
    async def _update_compliance_record_for_resolution(self, 
                                                     taxpayer_id: str,
                                                     requirement: ComplianceRequirement):
        """Update compliance record when violation is resolved"""
        records = self.compliance_records.get(taxpayer_id, [])
        
        for record in records:
            if record.requirement == requirement:
                # Check if all violations for this requirement are resolved
                taxpayer_violations = self.violations.get(taxpayer_id, [])
                requirement_violations = [
                    v for v in taxpayer_violations 
                    if v.requirement == requirement and not v.resolved
                ]
                
                if not requirement_violations:
                    record.status = ComplianceStatus.COMPLIANT
                    record.compliance_score = 100.0
                
                break
    
    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive compliance dashboard"""
        try:
            # Calculate overall metrics
            total_taxpayers = self.stats['total_taxpayers_monitored']
            compliant_taxpayers = self.stats['compliant_taxpayers']
            
            compliance_rate = (
                (compliant_taxpayers / total_taxpayers * 100) 
                if total_taxpayers > 0 else 0
            )
            
            # Get violation statistics
            violation_stats = self._calculate_violation_statistics()
            
            # Get requirement compliance breakdown
            requirement_breakdown = self._calculate_requirement_breakdown()
            
            # Get trending data
            trending_data = self._calculate_compliance_trends()
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overview': {
                    'total_taxpayers_monitored': total_taxpayers,
                    'compliant_taxpayers': compliant_taxpayers,
                    'compliance_rate': round(compliance_rate, 1),
                    'total_violations': self.stats['total_violations'],
                    'resolved_violations': self.stats['resolved_violations'],
                    'average_compliance_score': self.stats['average_compliance_score']
                },
                'violation_statistics': violation_stats,
                'requirement_breakdown': requirement_breakdown,
                'trending_data': trending_data,
                'alerts': self._generate_compliance_alerts()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating compliance dashboard: {str(e)}")
            raise
    
    def _calculate_violation_statistics(self) -> Dict[str, Any]:
        """Calculate violation statistics"""
        all_violations = []
        for violations in self.violations.values():
            all_violations.extend(violations)
        
        if not all_violations:
            return {
                'total_violations': 0,
                'by_severity': {},
                'by_requirement': {},
                'resolution_rate': 0
            }
        
        # Group by severity
        severity_counts = Counter(v.severity.value for v in all_violations)
        
        # Group by requirement
        requirement_counts = Counter(v.requirement.value for v in all_violations)
        
        # Calculate resolution rate
        resolved_count = len([v for v in all_violations if v.resolved])
        resolution_rate = (resolved_count / len(all_violations) * 100) if all_violations else 0
        
        return {
            'total_violations': len(all_violations),
            'by_severity': dict(severity_counts),
            'by_requirement': dict(requirement_counts),
            'resolution_rate': round(resolution_rate, 1)
        }
    
    def _calculate_requirement_breakdown(self) -> Dict[str, Any]:
        """Calculate compliance breakdown by requirement"""
        requirement_stats = defaultdict(lambda: {'total': 0, 'compliant': 0})
        
        for records in self.compliance_records.values():
            for record in records:
                requirement_stats[record.requirement.value]['total'] += 1
                if record.status == ComplianceStatus.COMPLIANT:
                    requirement_stats[record.requirement.value]['compliant'] += 1
        
        # Calculate compliance rates
        for requirement, stats in requirement_stats.items():
            stats['compliance_rate'] = (
                (stats['compliant'] / stats['total'] * 100) 
                if stats['total'] > 0 else 0
            )
        
        return dict(requirement_stats)
    
    def _calculate_compliance_trends(self) -> Dict[str, Any]:
        """Calculate compliance trending data"""
        # Simple trend calculation (would use historical data in production)
        return {
            'trend_direction': self.stats['compliance_trend'],
            'monthly_compliance_rate': self.stats['average_compliance_score'],
            'violation_trend': 'decreasing' if self.stats['resolved_violations'] > 0 else 'stable'
        }
    
    def _generate_compliance_alerts(self) -> List[Dict[str, Any]]:
        """Generate compliance alerts"""
        alerts = []
        
        # Critical violations alert
        critical_violations = []
        for violations in self.violations.values():
            critical_violations.extend([
                v for v in violations 
                if v.severity == ComplianceSeverity.CRITICAL and not v.resolved
            ])
        
        if critical_violations:
            alerts.append({
                'type': 'critical_violations',
                'count': len(critical_violations),
                'message': f'{len(critical_violations)} critical compliance violations require immediate attention',
                'priority': 'high'
            })
        
        # Low compliance rate alert
        if self.stats['average_compliance_score'] < 70:
            alerts.append({
                'type': 'low_compliance',
                'score': self.stats['average_compliance_score'],
                'message': 'Overall compliance rate is below acceptable threshold',
                'priority': 'medium'
            })
        
        return alerts
    
    async def get_taxpayer_compliance_report(self, taxpayer_id: str) -> Dict[str, Any]:
        """Get detailed compliance report for a taxpayer"""
        try:
            # Get latest assessment
            assessments = self.assessments.get(taxpayer_id, [])
            latest_assessment = assessments[-1] if assessments else None
            
            # Get compliance records
            records = self.compliance_records.get(taxpayer_id, [])
            
            # Get violations
            violations = self.violations.get(taxpayer_id, [])
            
            return {
                'taxpayer_id': taxpayer_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'latest_assessment': latest_assessment.to_dict() if latest_assessment else None,
                'compliance_records': [record.to_dict() for record in records],
                'violations': [violation.to_dict() for violation in violations],
                'summary': {
                    'total_requirements': len(records),
                    'compliant_requirements': len([r for r in records if r.status == ComplianceStatus.COMPLIANT]),
                    'active_violations': len([v for v in violations if not v.resolved]),
                    'compliance_score': latest_assessment.overall_score if latest_assessment else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating taxpayer compliance report: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Get compliance monitor health status"""
        critical_violations = 0
        for violations in self.violations.values():
            critical_violations += len([
                v for v in violations 
                if v.severity == ComplianceSeverity.CRITICAL and not v.resolved
            ])
        
        status = "healthy"
        if critical_violations > 10:
            status = "critical"
        elif critical_violations > 5:
            status = "degraded"
        elif self.stats['average_compliance_score'] < 70:
            status = "degraded"
        
        return {
            'status': status,
            'service': 'taxpayer_compliance_monitor',
            'monitored_taxpayers': self.stats['total_taxpayers_monitored'],
            'critical_violations': critical_violations,
            'compliance_rate': self.stats['average_compliance_score'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup monitor resources"""
        self.logger.info("Taxpayer compliance monitor cleanup initiated")
        
        # Log final statistics
        self.logger.info(f"Final compliance statistics: {self.stats}")
        
        self.logger.info("Taxpayer compliance monitor cleanup completed")


# Factory function
def create_taxpayer_compliance_monitor() -> TaxpayerComplianceMonitor:
    """Create taxpayer compliance monitor with standard configuration"""
    return TaxpayerComplianceMonitor()


# Helper functions
def get_compliance_requirements_by_type(taxpayer_type: TaxpayerType) -> List[ComplianceRequirement]:
    """Get compliance requirements by taxpayer type"""
    requirements_map = {
        TaxpayerType.LARGE_TAXPAYER: [
            ComplianceRequirement.TIN_VALIDATION,
            ComplianceRequirement.BUSINESS_REGISTRATION,
            ComplianceRequirement.TAX_CLEARANCE,
            ComplianceRequirement.FINANCIAL_STATEMENTS,
            ComplianceRequirement.MONTHLY_RETURNS,
            ComplianceRequirement.ANNUAL_RETURNS,
            ComplianceRequirement.VAT_REGISTRATION,
            ComplianceRequirement.AUDIT_REQUIREMENTS
        ],
        TaxpayerType.MEDIUM_TAXPAYER: [
            ComplianceRequirement.TIN_VALIDATION,
            ComplianceRequirement.BUSINESS_REGISTRATION,
            ComplianceRequirement.TAX_CLEARANCE,
            ComplianceRequirement.MONTHLY_RETURNS,
            ComplianceRequirement.ANNUAL_RETURNS,
            ComplianceRequirement.VAT_REGISTRATION
        ],
        TaxpayerType.SMALL_TAXPAYER: [
            ComplianceRequirement.TIN_VALIDATION,
            ComplianceRequirement.BUSINESS_REGISTRATION,
            ComplianceRequirement.ANNUAL_RETURNS
        ]
    }
    
    return requirements_map.get(taxpayer_type, [])