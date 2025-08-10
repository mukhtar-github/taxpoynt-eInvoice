"""
Compliance Dashboard Service

This module provides SI-specific compliance dashboards for monitoring adherence to
e-invoicing regulations, audit trails, data integrity, and regulatory compliance metrics.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNKNOWN = "unknown"


class ComplianceCategory(Enum):
    """Categories of compliance requirements"""
    DATA_INTEGRITY = "data_integrity"
    AUDIT_TRAIL = "audit_trail"
    REGULATORY_STANDARDS = "regulatory_standards"
    SECURITY_COMPLIANCE = "security_compliance"
    BUSINESS_RULES = "business_rules"
    TECHNICAL_STANDARDS = "technical_standards"
    CERTIFICATION = "certification"


class ViolationSeverity(Enum):
    """Severity levels for compliance violations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RegulatoryFramework(Enum):
    """Supported regulatory frameworks"""
    FIRS_NIGERIA = "firs_nigeria"
    PEPPOL = "peppol"
    EN16931 = "en16931"
    UBL = "ubl"
    ZATCA_SAUDI = "zatca_saudi"
    KSA_EINVOICING = "ksa_einvoicing"
    CUSTOM = "custom"


@dataclass
class ComplianceRule:
    """Defines a compliance rule"""
    rule_id: str
    rule_name: str
    category: ComplianceCategory
    framework: RegulatoryFramework
    description: str
    validation_criteria: str
    severity: ViolationSeverity
    enabled: bool = True
    auto_check: bool = True
    manual_review_required: bool = False
    documentation_url: Optional[str] = None


@dataclass
class ComplianceViolation:
    """Represents a compliance violation"""
    violation_id: str
    rule_id: str
    entity_type: str
    entity_id: str
    severity: ViolationSeverity
    category: ComplianceCategory
    description: str
    detected_at: datetime
    violation_details: Dict[str, Any] = field(default_factory=dict)
    remediation_status: str = "open"  # open, in_progress, resolved, false_positive
    remediation_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    source_system: Optional[str] = None


@dataclass
class AuditEvent:
    """Represents an audit trail event"""
    event_id: str
    timestamp: datetime
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[str]
    action: str
    changes: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    system_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceMetrics:
    """Compliance metrics for a specific category or framework"""
    category: ComplianceCategory
    framework: RegulatoryFramework
    total_entities: int
    compliant_entities: int
    non_compliant_entities: int
    compliance_rate: float
    total_violations: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    resolved_violations: int
    open_violations: int
    trend_direction: str = "stable"  # improving, declining, stable


@dataclass
class CertificationStatus:
    """Status of regulatory certifications"""
    certification_id: str
    framework: RegulatoryFramework
    certificate_type: str
    status: str  # active, expired, pending, revoked
    issued_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    issuing_authority: Optional[str] = None
    certificate_number: Optional[str] = None
    scope: Optional[str] = None
    renewal_required: bool = False
    days_until_expiry: Optional[int] = None


@dataclass
class DataIntegrityCheck:
    """Data integrity check result"""
    check_id: str
    check_name: str
    entity_type: str
    check_type: str  # hash_validation, digital_signature, timestamp_validation
    status: ComplianceStatus
    checked_at: datetime
    total_records: int
    valid_records: int
    invalid_records: int
    integrity_score: float
    findings: List[str] = field(default_factory=list)


@dataclass
class ComplianceDashboard:
    """Main compliance dashboard data structure"""
    dashboard_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    overall_compliance_score: float
    framework_metrics: List[ComplianceMetrics] = field(default_factory=list)
    category_metrics: List[ComplianceMetrics] = field(default_factory=list)
    active_violations: List[ComplianceViolation] = field(default_factory=list)
    recent_audit_events: List[AuditEvent] = field(default_factory=list)
    certification_status: List[CertificationStatus] = field(default_factory=list)
    data_integrity_checks: List[DataIntegrityCheck] = field(default_factory=list)
    compliance_trends: Dict[str, List[Tuple[datetime, float]]] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardConfig:
    """Configuration for compliance dashboard"""
    enabled_frameworks: List[RegulatoryFramework] = field(default_factory=lambda: [RegulatoryFramework.FIRS_NIGERIA])
    enabled_categories: List[ComplianceCategory] = field(default_factory=lambda: list(ComplianceCategory))
    auto_refresh_interval_minutes: int = 60
    violation_retention_days: int = 365
    audit_retention_days: int = 2555  # 7 years
    enable_real_time_monitoring: bool = True
    enable_automated_remediation: bool = False
    compliance_threshold: float = 95.0  # Minimum compliance percentage
    data_storage_path: Optional[str] = None
    dashboard_export_format: str = "json"
    notification_webhooks: List[str] = field(default_factory=list)


class ComplianceDashboardService:
    """
    Service for generating and managing SI compliance dashboards
    """
    
    def __init__(self, config: DashboardConfig):
        self.config = config
        self.compliance_rules: Dict[str, ComplianceRule] = {}
        self.violations: Dict[str, ComplianceViolation] = {}
        self.audit_events: List[AuditEvent] = []
        self.certifications: Dict[str, CertificationStatus] = {}
        self.data_integrity_checks: List[DataIntegrityCheck] = []
        
        # Dashboard cache
        self.dashboard_cache: Dict[str, ComplianceDashboard] = {}
        
        # Setup storage
        if config.data_storage_path:
            self.storage_path = Path(config.data_storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = None
        
        # Initialize compliance rules
        asyncio.create_task(self._load_compliance_rules())
        
        # Load existing data
        asyncio.create_task(self._load_compliance_data())
    
    async def generate_compliance_dashboard(
        self,
        frameworks: Optional[List[RegulatoryFramework]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ComplianceDashboard:
        """Generate a comprehensive compliance dashboard"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        if not frameworks:
            frameworks = self.config.enabled_frameworks
        
        dashboard_id = f"compliance_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        try:
            dashboard = ComplianceDashboard(
                dashboard_id=dashboard_id,
                generated_at=datetime.now(),
                period_start=start_date,
                period_end=end_date,
                overall_compliance_score=0.0
            )
            
            # Calculate framework-specific metrics
            for framework in frameworks:
                framework_metrics = await self._calculate_framework_metrics(
                    framework, start_date, end_date
                )
                dashboard.framework_metrics.append(framework_metrics)
            
            # Calculate category-specific metrics
            for category in self.config.enabled_categories:
                category_metrics = await self._calculate_category_metrics(
                    category, start_date, end_date
                )
                dashboard.category_metrics.append(category_metrics)
            
            # Get active violations
            dashboard.active_violations = await self._get_active_violations(start_date, end_date)
            
            # Get recent audit events
            dashboard.recent_audit_events = await self._get_recent_audit_events(start_date, end_date)
            
            # Get certification status
            dashboard.certification_status = await self._get_certification_status()
            
            # Perform data integrity checks
            dashboard.data_integrity_checks = await self._perform_data_integrity_checks()
            
            # Calculate overall compliance score
            dashboard.overall_compliance_score = self._calculate_overall_compliance_score(dashboard)
            
            # Generate compliance trends
            dashboard.compliance_trends = await self._generate_compliance_trends(frameworks)
            
            # Perform risk assessment
            dashboard.risk_assessment = await self._perform_risk_assessment(dashboard)
            
            # Generate recommendations
            dashboard.recommendations = self._generate_compliance_recommendations(dashboard)
            
            # Calculate summary statistics
            dashboard.summary_stats = self._calculate_dashboard_summary(dashboard)
            
            # Cache the dashboard
            self.dashboard_cache[dashboard_id] = dashboard
            
            # Export if configured
            if self.storage_path:
                await self._export_dashboard(dashboard)
            
            logger.info(f"Generated compliance dashboard {dashboard_id}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to generate compliance dashboard: {e}")
            raise
    
    async def _calculate_framework_metrics(
        self,
        framework: RegulatoryFramework,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceMetrics:
        """Calculate compliance metrics for a specific framework"""
        
        try:
            # Get all entities subject to this framework
            total_entities = await self._count_entities_for_framework(framework, start_date, end_date)
            
            # Get framework-specific violations
            framework_violations = [
                v for v in self.violations.values()
                if (v.detected_at >= start_date and v.detected_at <= end_date and
                    self._get_rule_framework(v.rule_id) == framework)
            ]
            
            # Count violations by severity
            critical_violations = sum(1 for v in framework_violations if v.severity == ViolationSeverity.CRITICAL)
            high_violations = sum(1 for v in framework_violations if v.severity == ViolationSeverity.HIGH)
            medium_violations = sum(1 for v in framework_violations if v.severity == ViolationSeverity.MEDIUM)
            low_violations = sum(1 for v in framework_violations if v.severity == ViolationSeverity.LOW)
            
            # Count resolved vs open violations
            resolved_violations = sum(1 for v in framework_violations if v.remediation_status == "resolved")
            open_violations = len(framework_violations) - resolved_violations
            
            # Calculate compliance
            non_compliant_entities = len(set(v.entity_id for v in framework_violations if v.remediation_status != "resolved"))
            compliant_entities = total_entities - non_compliant_entities
            compliance_rate = (compliant_entities / total_entities * 100) if total_entities > 0 else 100
            
            # Calculate trend
            trend_direction = await self._calculate_framework_trend(framework)
            
            return ComplianceMetrics(
                category=ComplianceCategory.REGULATORY_STANDARDS,  # Default category for framework metrics
                framework=framework,
                total_entities=total_entities,
                compliant_entities=compliant_entities,
                non_compliant_entities=non_compliant_entities,
                compliance_rate=compliance_rate,
                total_violations=len(framework_violations),
                critical_violations=critical_violations,
                high_violations=high_violations,
                medium_violations=medium_violations,
                low_violations=low_violations,
                resolved_violations=resolved_violations,
                open_violations=open_violations,
                trend_direction=trend_direction
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate framework metrics for {framework}: {e}")
            return ComplianceMetrics(
                category=ComplianceCategory.REGULATORY_STANDARDS,
                framework=framework,
                total_entities=0,
                compliant_entities=0,
                non_compliant_entities=0,
                compliance_rate=0.0,
                total_violations=0,
                critical_violations=0,
                high_violations=0,
                medium_violations=0,
                low_violations=0,
                resolved_violations=0,
                open_violations=0
            )
    
    async def _calculate_category_metrics(
        self,
        category: ComplianceCategory,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceMetrics:
        """Calculate compliance metrics for a specific category"""
        
        try:
            # Get all entities subject to this category
            total_entities = await self._count_entities_for_category(category, start_date, end_date)
            
            # Get category-specific violations
            category_violations = [
                v for v in self.violations.values()
                if (v.detected_at >= start_date and v.detected_at <= end_date and
                    v.category == category)
            ]
            
            # Count violations by severity
            critical_violations = sum(1 for v in category_violations if v.severity == ViolationSeverity.CRITICAL)
            high_violations = sum(1 for v in category_violations if v.severity == ViolationSeverity.HIGH)
            medium_violations = sum(1 for v in category_violations if v.severity == ViolationSeverity.MEDIUM)
            low_violations = sum(1 for v in category_violations if v.severity == ViolationSeverity.LOW)
            
            # Count resolved vs open violations
            resolved_violations = sum(1 for v in category_violations if v.remediation_status == "resolved")
            open_violations = len(category_violations) - resolved_violations
            
            # Calculate compliance
            non_compliant_entities = len(set(v.entity_id for v in category_violations if v.remediation_status != "resolved"))
            compliant_entities = total_entities - non_compliant_entities
            compliance_rate = (compliant_entities / total_entities * 100) if total_entities > 0 else 100
            
            # Calculate trend
            trend_direction = await self._calculate_category_trend(category)
            
            return ComplianceMetrics(
                category=category,
                framework=RegulatoryFramework.FIRS_NIGERIA,  # Default framework
                total_entities=total_entities,
                compliant_entities=compliant_entities,
                non_compliant_entities=non_compliant_entities,
                compliance_rate=compliance_rate,
                total_violations=len(category_violations),
                critical_violations=critical_violations,
                high_violations=high_violations,
                medium_violations=medium_violations,
                low_violations=low_violations,
                resolved_violations=resolved_violations,
                open_violations=open_violations,
                trend_direction=trend_direction
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate category metrics for {category}: {e}")
            return ComplianceMetrics(
                category=category,
                framework=RegulatoryFramework.FIRS_NIGERIA,
                total_entities=0,
                compliant_entities=0,
                non_compliant_entities=0,
                compliance_rate=0.0,
                total_violations=0,
                critical_violations=0,
                high_violations=0,
                medium_violations=0,
                low_violations=0,
                resolved_violations=0,
                open_violations=0
            )
    
    async def _get_active_violations(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ComplianceViolation]:
        """Get active compliance violations for the period"""
        
        active_violations = [
            v for v in self.violations.values()
            if (v.detected_at >= start_date and v.detected_at <= end_date and
                v.remediation_status in ["open", "in_progress"])
        ]
        
        # Sort by severity and detection date
        severity_order = {
            ViolationSeverity.CRITICAL: 0,
            ViolationSeverity.HIGH: 1,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.LOW: 3,
            ViolationSeverity.INFO: 4
        }
        
        active_violations.sort(
            key=lambda v: (severity_order.get(v.severity, 5), v.detected_at),
            reverse=True
        )
        
        return active_violations[:100]  # Limit to top 100 violations
    
    async def _get_recent_audit_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[AuditEvent]:
        """Get recent audit events for the period"""
        
        recent_events = [
            event for event in self.audit_events
            if start_date <= event.timestamp <= end_date
        ]
        
        # Sort by timestamp (most recent first)
        recent_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return recent_events[:500]  # Limit to 500 most recent events
    
    async def _get_certification_status(self) -> List[CertificationStatus]:
        """Get current certification status"""
        current_time = datetime.now()
        
        for cert in self.certifications.values():
            if cert.expiry_date:
                cert.days_until_expiry = (cert.expiry_date - current_time).days
                cert.renewal_required = cert.days_until_expiry <= 90  # 3 months warning
                
                if cert.days_until_expiry <= 0:
                    cert.status = "expired"
        
        return list(self.certifications.values())
    
    async def _perform_data_integrity_checks(self) -> List[DataIntegrityCheck]:
        """Perform data integrity checks"""
        
        integrity_checks = []
        
        try:
            # Hash validation check
            hash_check = await self._perform_hash_validation()
            if hash_check:
                integrity_checks.append(hash_check)
            
            # Digital signature check
            signature_check = await self._perform_signature_validation()
            if signature_check:
                integrity_checks.append(signature_check)
            
            # Timestamp validation check
            timestamp_check = await self._perform_timestamp_validation()
            if timestamp_check:
                integrity_checks.append(timestamp_check)
            
        except Exception as e:
            logger.error(f"Failed to perform data integrity checks: {e}")
        
        return integrity_checks
    
    async def _perform_hash_validation(self) -> Optional[DataIntegrityCheck]:
        """Perform hash validation check"""
        try:
            # This would validate data hashes against stored hashes
            # For now, simulate a check
            
            total_records = 1000  # Mock data
            valid_records = 985
            invalid_records = total_records - valid_records
            integrity_score = (valid_records / total_records * 100)
            
            status = ComplianceStatus.COMPLIANT if integrity_score >= 95 else ComplianceStatus.NON_COMPLIANT
            
            findings = []
            if invalid_records > 0:
                findings.append(f"{invalid_records} records failed hash validation")
            
            return DataIntegrityCheck(
                check_id=f"hash_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                check_name="Data Hash Validation",
                entity_type="invoice",
                check_type="hash_validation",
                status=status,
                checked_at=datetime.now(),
                total_records=total_records,
                valid_records=valid_records,
                invalid_records=invalid_records,
                integrity_score=integrity_score,
                findings=findings
            )
            
        except Exception as e:
            logger.error(f"Hash validation check failed: {e}")
            return None
    
    async def _perform_signature_validation(self) -> Optional[DataIntegrityCheck]:
        """Perform digital signature validation check"""
        try:
            # This would validate digital signatures
            # For now, simulate a check
            
            total_records = 800  # Mock data (not all records have signatures)
            valid_records = 792
            invalid_records = total_records - valid_records
            integrity_score = (valid_records / total_records * 100)
            
            status = ComplianceStatus.COMPLIANT if integrity_score >= 98 else ComplianceStatus.NON_COMPLIANT
            
            findings = []
            if invalid_records > 0:
                findings.append(f"{invalid_records} records have invalid or missing signatures")
            
            return DataIntegrityCheck(
                check_id=f"signature_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                check_name="Digital Signature Validation",
                entity_type="invoice",
                check_type="digital_signature",
                status=status,
                checked_at=datetime.now(),
                total_records=total_records,
                valid_records=valid_records,
                invalid_records=invalid_records,
                integrity_score=integrity_score,
                findings=findings
            )
            
        except Exception as e:
            logger.error(f"Signature validation check failed: {e}")
            return None
    
    async def _perform_timestamp_validation(self) -> Optional[DataIntegrityCheck]:
        """Perform timestamp validation check"""
        try:
            # This would validate timestamps for authenticity
            # For now, simulate a check
            
            total_records = 1000  # Mock data
            valid_records = 998
            invalid_records = total_records - valid_records
            integrity_score = (valid_records / total_records * 100)
            
            status = ComplianceStatus.COMPLIANT if integrity_score >= 95 else ComplianceStatus.NON_COMPLIANT
            
            findings = []
            if invalid_records > 0:
                findings.append(f"{invalid_records} records have invalid timestamps")
            
            return DataIntegrityCheck(
                check_id=f"timestamp_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                check_name="Timestamp Validation",
                entity_type="invoice",
                check_type="timestamp_validation",
                status=status,
                checked_at=datetime.now(),
                total_records=total_records,
                valid_records=valid_records,
                invalid_records=invalid_records,
                integrity_score=integrity_score,
                findings=findings
            )
            
        except Exception as e:
            logger.error(f"Timestamp validation check failed: {e}")
            return None
    
    def _calculate_overall_compliance_score(self, dashboard: ComplianceDashboard) -> float:
        """Calculate overall compliance score"""
        try:
            if not dashboard.framework_metrics and not dashboard.category_metrics:
                return 0.0
            
            all_metrics = dashboard.framework_metrics + dashboard.category_metrics
            
            # Weight by total entities
            total_weighted_score = 0.0
            total_entities = 0
            
            for metric in all_metrics:
                if metric.total_entities > 0:
                    total_weighted_score += metric.compliance_rate * metric.total_entities
                    total_entities += metric.total_entities
            
            if total_entities == 0:
                return 0.0
            
            return total_weighted_score / total_entities
            
        except Exception as e:
            logger.error(f"Failed to calculate overall compliance score: {e}")
            return 0.0
    
    async def _generate_compliance_trends(
        self,
        frameworks: List[RegulatoryFramework]
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """Generate compliance trend data"""
        trends = {}
        
        try:
            # Generate trends for the last 30 days
            end_date = datetime.now()
            
            for framework in frameworks:
                framework_trends = []
                
                for i in range(30):
                    date = end_date - timedelta(days=i)
                    
                    # Calculate compliance score for this date
                    # This would typically query historical data
                    # For now, simulate trend data
                    base_score = 85.0
                    variation = (hash(f"{framework.value}_{date.strftime('%Y%m%d')}") % 20) - 10
                    score = max(60.0, min(100.0, base_score + variation))
                    
                    framework_trends.append((date, score))
                
                # Sort by date
                framework_trends.sort(key=lambda x: x[0])
                trends[framework.value] = framework_trends
            
            # Generate category trends
            for category in self.config.enabled_categories:
                category_trends = []
                
                for i in range(30):
                    date = end_date - timedelta(days=i)
                    
                    # Simulate category trend data
                    base_score = 82.0
                    variation = (hash(f"{category.value}_{date.strftime('%Y%m%d')}") % 15) - 7
                    score = max(70.0, min(100.0, base_score + variation))
                    
                    category_trends.append((date, score))
                
                category_trends.sort(key=lambda x: x[0])
                trends[f"category_{category.value}"] = category_trends
            
        except Exception as e:
            logger.error(f"Failed to generate compliance trends: {e}")
        
        return trends
    
    async def _perform_risk_assessment(self, dashboard: ComplianceDashboard) -> Dict[str, Any]:
        """Perform compliance risk assessment"""
        try:
            risk_assessment = {
                "overall_risk_level": "medium",
                "risk_factors": [],
                "mitigation_recommendations": [],
                "risk_score": 0.0
            }
            
            # Calculate risk based on violations
            critical_violations = sum(v.critical_violations for v in dashboard.framework_metrics)
            high_violations = sum(v.high_violations for v in dashboard.framework_metrics)
            
            # Risk scoring
            risk_score = 0.0
            
            if critical_violations > 0:
                risk_score += critical_violations * 10
                risk_assessment["risk_factors"].append(f"{critical_violations} critical violations")
            
            if high_violations > 0:
                risk_score += high_violations * 5
                risk_assessment["risk_factors"].append(f"{high_violations} high-severity violations")
            
            # Certification expiry risk
            expiring_certs = [
                cert for cert in dashboard.certification_status
                if cert.days_until_expiry and cert.days_until_expiry <= 90
            ]
            
            if expiring_certs:
                risk_score += len(expiring_certs) * 15
                risk_assessment["risk_factors"].append(f"{len(expiring_certs)} certifications expiring soon")
            
            # Low compliance rate risk
            if dashboard.overall_compliance_score < 80:
                risk_score += (80 - dashboard.overall_compliance_score) * 2
                risk_assessment["risk_factors"].append("Overall compliance rate below 80%")
            
            # Data integrity risk
            integrity_issues = sum(
                1 for check in dashboard.data_integrity_checks
                if check.status != ComplianceStatus.COMPLIANT
            )
            
            if integrity_issues > 0:
                risk_score += integrity_issues * 8
                risk_assessment["risk_factors"].append(f"{integrity_issues} data integrity issues")
            
            # Determine overall risk level
            if risk_score >= 50:
                risk_assessment["overall_risk_level"] = "high"
            elif risk_score >= 25:
                risk_assessment["overall_risk_level"] = "medium"
            else:
                risk_assessment["overall_risk_level"] = "low"
            
            risk_assessment["risk_score"] = risk_score
            
            # Generate mitigation recommendations
            if critical_violations > 0:
                risk_assessment["mitigation_recommendations"].append(
                    "Immediate remediation of critical compliance violations required"
                )
            
            if expiring_certs:
                risk_assessment["mitigation_recommendations"].append(
                    "Renew expiring certifications to maintain compliance status"
                )
            
            if dashboard.overall_compliance_score < 90:
                risk_assessment["mitigation_recommendations"].append(
                    "Implement automated compliance monitoring to improve overall compliance rate"
                )
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Failed to perform risk assessment: {e}")
            return {"overall_risk_level": "unknown", "risk_factors": [], "mitigation_recommendations": [], "risk_score": 0.0}
    
    def _generate_compliance_recommendations(self, dashboard: ComplianceDashboard) -> List[str]:
        """Generate compliance improvement recommendations"""
        recommendations = []
        
        try:
            # Overall compliance recommendations
            if dashboard.overall_compliance_score < self.config.compliance_threshold:
                recommendations.append(
                    f"Overall compliance score ({dashboard.overall_compliance_score:.1f}%) is below threshold "
                    f"({self.config.compliance_threshold}%). Implement comprehensive compliance review."
                )
            
            # Violation-based recommendations
            critical_violations = sum(len([v for v in dashboard.active_violations if v.severity == ViolationSeverity.CRITICAL]))
            if critical_violations > 0:
                recommendations.append(
                    f"Address {critical_violations} critical compliance violations immediately."
                )
            
            # Framework-specific recommendations
            for metric in dashboard.framework_metrics:
                if metric.compliance_rate < 90:
                    recommendations.append(
                        f"Improve {metric.framework.value} compliance rate from {metric.compliance_rate:.1f}% to above 90%."
                    )
            
            # Category-specific recommendations
            for metric in dashboard.category_metrics:
                if metric.compliance_rate < 85:
                    recommendations.append(
                        f"Focus on improving {metric.category.value} compliance (currently {metric.compliance_rate:.1f}%)."
                    )
            
            # Certification recommendations
            expiring_soon = [
                cert for cert in dashboard.certification_status
                if cert.days_until_expiry and cert.days_until_expiry <= 90
            ]
            
            if expiring_soon:
                recommendations.append(
                    f"Renew {len(expiring_soon)} certifications expiring within 90 days."
                )
            
            # Data integrity recommendations
            integrity_issues = [
                check for check in dashboard.data_integrity_checks
                if check.status != ComplianceStatus.COMPLIANT
            ]
            
            if integrity_issues:
                recommendations.append(
                    "Address data integrity issues to ensure regulatory compliance."
                )
            
            # Audit trail recommendations
            if len(dashboard.recent_audit_events) < 100:  # Threshold for sufficient audit coverage
                recommendations.append(
                    "Enhance audit trail coverage to ensure comprehensive compliance monitoring."
                )
            
            # Trending recommendations
            declining_trends = [
                trend_name for trend_name, trend_data in dashboard.compliance_trends.items()
                if len(trend_data) >= 2 and trend_data[-1][1] < trend_data[0][1] - 5
            ]
            
            if declining_trends:
                recommendations.append(
                    f"Address declining compliance trends in: {', '.join(declining_trends)}"
                )
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
        
        return recommendations
    
    def _calculate_dashboard_summary(self, dashboard: ComplianceDashboard) -> Dict[str, Any]:
        """Calculate dashboard summary statistics"""
        try:
            total_entities = sum(m.total_entities for m in dashboard.framework_metrics)
            total_violations = sum(m.total_violations for m in dashboard.framework_metrics)
            
            return {
                "reporting_period_days": (dashboard.period_end - dashboard.period_start).days,
                "overall_compliance_score": dashboard.overall_compliance_score,
                "total_entities_monitored": total_entities,
                "total_compliance_violations": total_violations,
                "critical_violations": sum(len([v for v in dashboard.active_violations if v.severity == ViolationSeverity.CRITICAL])),
                "open_violations": sum(len([v for v in dashboard.active_violations if v.remediation_status == "open"])),
                "resolved_violations": sum(m.resolved_violations for m in dashboard.framework_metrics),
                "active_certifications": len([c for c in dashboard.certification_status if c.status == "active"]),
                "expiring_certifications": len([c for c in dashboard.certification_status if c.renewal_required]),
                "data_integrity_score": sum(c.integrity_score for c in dashboard.data_integrity_checks) / len(dashboard.data_integrity_checks) if dashboard.data_integrity_checks else 0,
                "audit_events_recorded": len(dashboard.recent_audit_events),
                "frameworks_monitored": len(dashboard.framework_metrics),
                "compliance_categories": len(dashboard.category_metrics),
                "risk_level": dashboard.risk_assessment.get("overall_risk_level", "unknown"),
                "recommendations_count": len(dashboard.recommendations)
            }
        except Exception as e:
            logger.error(f"Failed to calculate dashboard summary: {e}")
            return {}
    
    # Helper methods and data access methods (would be implemented based on actual data sources)
    
    def _get_rule_framework(self, rule_id: str) -> RegulatoryFramework:
        """Get framework for a compliance rule"""
        rule = self.compliance_rules.get(rule_id)
        return rule.framework if rule else RegulatoryFramework.FIRS_NIGERIA
    
    async def _count_entities_for_framework(
        self,
        framework: RegulatoryFramework,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Count entities subject to a framework"""
        # This would query the actual data store
        # For now, return mock data
        return 1000
    
    async def _count_entities_for_category(
        self,
        category: ComplianceCategory,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Count entities subject to a category"""
        # This would query the actual data store
        # For now, return mock data
        return 1000
    
    async def _calculate_framework_trend(self, framework: RegulatoryFramework) -> str:
        """Calculate trend direction for a framework"""
        # This would analyze historical compliance data
        # For now, return mock trend
        return "improving"
    
    async def _calculate_category_trend(self, category: ComplianceCategory) -> str:
        """Calculate trend direction for a category"""
        # This would analyze historical compliance data
        # For now, return mock trend
        return "stable"
    
    async def _load_compliance_rules(self) -> None:
        """Load compliance rules from configuration"""
        try:
            # Load default FIRS compliance rules
            default_rules = [
                ComplianceRule(
                    rule_id="FIRS_001",
                    rule_name="Invoice Number Format",
                    category=ComplianceCategory.BUSINESS_RULES,
                    framework=RegulatoryFramework.FIRS_NIGERIA,
                    description="Invoice numbers must follow FIRS specified format",
                    validation_criteria="regex:^[A-Z]{2,3}[0-9]{6,}$",
                    severity=ViolationSeverity.HIGH
                ),
                ComplianceRule(
                    rule_id="FIRS_002",
                    rule_name="TIN Validation",
                    category=ComplianceCategory.DATA_INTEGRITY,
                    framework=RegulatoryFramework.FIRS_NIGERIA,
                    description="All invoices must contain valid TIN numbers",
                    validation_criteria="tin_format_check",
                    severity=ViolationSeverity.CRITICAL
                ),
                ComplianceRule(
                    rule_id="FIRS_003",
                    rule_name="Digital Signature Required",
                    category=ComplianceCategory.SECURITY_COMPLIANCE,
                    framework=RegulatoryFramework.FIRS_NIGERIA,
                    description="All invoices must be digitally signed",
                    validation_criteria="digital_signature_present",
                    severity=ViolationSeverity.CRITICAL
                )
            ]
            
            for rule in default_rules:
                self.compliance_rules[rule.rule_id] = rule
            
            logger.info(f"Loaded {len(default_rules)} compliance rules")
            
        except Exception as e:
            logger.error(f"Failed to load compliance rules: {e}")
    
    async def _load_compliance_data(self) -> None:
        """Load existing compliance data"""
        try:
            # Load mock certification data
            self.certifications["FIRS_CERT_001"] = CertificationStatus(
                certification_id="FIRS_CERT_001",
                framework=RegulatoryFramework.FIRS_NIGERIA,
                certificate_type="SI_PROVIDER",
                status="active",
                issued_date=datetime.now() - timedelta(days=365),
                expiry_date=datetime.now() + timedelta(days=365),
                issuing_authority="FIRS Nigeria",
                certificate_number="SI2024001",
                scope="System Integrator Services"
            )
            
            # Load mock violations
            self.violations["VIOL_001"] = ComplianceViolation(
                violation_id="VIOL_001",
                rule_id="FIRS_002",
                entity_type="invoice",
                entity_id="INV-001",
                severity=ViolationSeverity.HIGH,
                category=ComplianceCategory.DATA_INTEGRITY,
                description="Invalid TIN format detected",
                detected_at=datetime.now() - timedelta(hours=2),
                remediation_status="open"
            )
            
            logger.info("Loaded compliance data")
            
        except Exception as e:
            logger.error(f"Failed to load compliance data: {e}")
    
    async def _export_dashboard(self, dashboard: ComplianceDashboard) -> None:
        """Export dashboard to storage"""
        if not self.storage_path:
            return
        
        try:
            filename = f"{dashboard.dashboard_id}.{self.config.dashboard_export_format}"
            filepath = self.storage_path / filename
            
            if self.config.dashboard_export_format == "json":
                dashboard_dict = self._dashboard_to_dict(dashboard)
                with open(filepath, 'w') as f:
                    json.dump(dashboard_dict, f, indent=2, default=str)
            
            logger.info(f"Exported compliance dashboard to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export dashboard: {e}")
    
    def _dashboard_to_dict(self, dashboard: ComplianceDashboard) -> Dict[str, Any]:
        """Convert dashboard to dictionary for export"""
        return {
            "dashboard_id": dashboard.dashboard_id,
            "generated_at": dashboard.generated_at.isoformat(),
            "period_start": dashboard.period_start.isoformat(),
            "period_end": dashboard.period_end.isoformat(),
            "overall_compliance_score": dashboard.overall_compliance_score,
            "framework_metrics": [
                {
                    "framework": m.framework.value,
                    "compliance_rate": m.compliance_rate,
                    "total_entities": m.total_entities,
                    "total_violations": m.total_violations,
                    "critical_violations": m.critical_violations,
                    "trend_direction": m.trend_direction
                }
                for m in dashboard.framework_metrics
            ],
            "active_violations": [
                {
                    "violation_id": v.violation_id,
                    "severity": v.severity.value,
                    "category": v.category.value,
                    "description": v.description,
                    "entity_type": v.entity_type,
                    "remediation_status": v.remediation_status
                }
                for v in dashboard.active_violations[:20]  # Limit for export
            ],
            "certification_status": [
                {
                    "certification_id": c.certification_id,
                    "framework": c.framework.value,
                    "status": c.status,
                    "days_until_expiry": c.days_until_expiry,
                    "renewal_required": c.renewal_required
                }
                for c in dashboard.certification_status
            ],
            "data_integrity_checks": [
                {
                    "check_name": c.check_name,
                    "status": c.status.value,
                    "integrity_score": c.integrity_score,
                    "total_records": c.total_records,
                    "valid_records": c.valid_records
                }
                for c in dashboard.data_integrity_checks
            ],
            "risk_assessment": dashboard.risk_assessment,
            "recommendations": dashboard.recommendations,
            "summary_stats": dashboard.summary_stats
        }
    
    # Public methods for managing compliance
    
    async def record_violation(
        self,
        rule_id: str,
        entity_type: str,
        entity_id: str,
        description: str,
        violation_details: Dict[str, Any] = None
    ) -> str:
        """Record a new compliance violation"""
        try:
            rule = self.compliance_rules.get(rule_id)
            if not rule:
                raise ValueError(f"Unknown compliance rule: {rule_id}")
            
            violation_id = f"VIOL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{entity_id}"
            
            violation = ComplianceViolation(
                violation_id=violation_id,
                rule_id=rule_id,
                entity_type=entity_type,
                entity_id=entity_id,
                severity=rule.severity,
                category=rule.category,
                description=description,
                detected_at=datetime.now(),
                violation_details=violation_details or {}
            )
            
            self.violations[violation_id] = violation
            
            logger.warning(f"Compliance violation recorded: {violation_id}")
            return violation_id
            
        except Exception as e:
            logger.error(f"Failed to record violation: {e}")
            raise
    
    async def resolve_violation(
        self,
        violation_id: str,
        resolution_notes: str,
        resolved_by: str
    ) -> bool:
        """Mark a violation as resolved"""
        try:
            violation = self.violations.get(violation_id)
            if not violation:
                return False
            
            violation.remediation_status = "resolved"
            violation.remediation_notes = resolution_notes
            violation.assigned_to = resolved_by
            
            logger.info(f"Violation {violation_id} resolved by {resolved_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve violation {violation_id}: {e}")
            return False
    
    async def record_audit_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: Optional[str] = None,
        changes: Dict[str, Any] = None,
        system_context: Dict[str, Any] = None
    ) -> str:
        """Record an audit event"""
        try:
            event_id = f"AUDIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{entity_id}"
            
            event = AuditEvent(
                event_id=event_id,
                timestamp=datetime.now(),
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                action=action,
                changes=changes or {},
                system_context=system_context or {}
            )
            
            self.audit_events.append(event)
            
            # Maintain retention limit
            cutoff_time = datetime.now() - timedelta(days=self.config.audit_retention_days)
            self.audit_events = [
                e for e in self.audit_events
                if e.timestamp > cutoff_time
            ]
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to record audit event: {e}")
            raise
    
    def get_cached_dashboard(self, dashboard_id: str) -> Optional[ComplianceDashboard]:
        """Get a cached compliance dashboard"""
        return self.dashboard_cache.get(dashboard_id)
    
    def list_cached_dashboards(self) -> List[str]:
        """List all cached dashboard IDs"""
        return list(self.dashboard_cache.keys())


# Factory function for creating compliance dashboard service
def create_compliance_dashboard_service(config: Optional[DashboardConfig] = None) -> ComplianceDashboardService:
    """Factory function to create a compliance dashboard service"""
    if config is None:
        config = DashboardConfig()
    
    return ComplianceDashboardService(config)