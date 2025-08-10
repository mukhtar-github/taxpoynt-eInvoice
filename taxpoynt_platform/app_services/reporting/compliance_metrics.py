"""
APP Service: Compliance Metrics
Monitors and tracks FIRS compliance metrics and regulatory adherence
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, Counter


class ComplianceStatus(str, Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    PENDING_REVIEW = "pending_review"
    UNKNOWN = "unknown"


class ComplianceCategory(str, Enum):
    """Categories of compliance metrics"""
    TRANSMISSION_COMPLIANCE = "transmission_compliance"
    SIGNATURE_COMPLIANCE = "signature_compliance"
    TIMESTAMP_COMPLIANCE = "timestamp_compliance"
    CERTIFICATE_COMPLIANCE = "certificate_compliance"
    VALIDATION_COMPLIANCE = "validation_compliance"
    RETENTION_COMPLIANCE = "retention_compliance"
    AUDIT_COMPLIANCE = "audit_compliance"
    SECURITY_COMPLIANCE = "security_compliance"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class ComplianceRule:
    """Definition of a compliance rule"""
    rule_id: str
    name: str
    description: str
    category: ComplianceCategory
    requirement: str
    threshold: Union[float, int, str]
    operator: str  # >=, <=, ==, !=, contains, etc.
    alert_level: AlertLevel
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceViolation:
    """Record of a compliance violation"""
    violation_id: str
    rule_id: str
    rule_name: str
    category: ComplianceCategory
    description: str
    severity: AlertLevel
    detected_at: datetime
    current_value: Union[float, int, str]
    expected_value: Union[float, int, str]
    affected_entities: List[str]
    remediation_steps: List[str]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data


@dataclass
class ComplianceMetric:
    """Individual compliance metric measurement"""
    metric_id: str
    name: str
    category: ComplianceCategory
    value: Union[float, int, str]
    unit: str
    status: ComplianceStatus
    measured_at: datetime
    benchmark: Optional[Union[float, int, str]] = None
    trend: Optional[str] = None  # improving, declining, stable
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['measured_at'] = self.measured_at.isoformat()
        return data


@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    overall_status: ComplianceStatus
    overall_score: float
    metrics: List[ComplianceMetric]
    violations: List[ComplianceViolation]
    recommendations: List[str]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        data['period_start'] = self.period_start.isoformat()
        data['period_end'] = self.period_end.isoformat()
        return data


class ComplianceDataProvider:
    """Data provider for compliance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Mock data for demonstration
        self._mock_transmission_data = self._generate_mock_transmission_data()
        self._mock_certificate_data = self._generate_mock_certificate_data()
        self._mock_audit_data = self._generate_mock_audit_data()
    
    def _generate_mock_transmission_data(self) -> Dict[str, Any]:
        """Generate mock transmission data"""
        import random
        
        now = datetime.now(timezone.utc)
        data = {
            'total_transmissions': 1500,
            'successful_transmissions': 1425,
            'failed_transmissions': 75,
            'average_response_time': 2.3,
            'signature_validation_failures': 12,
            'timestamp_violations': 8,
            'retry_attempts': 89,
            'transmission_by_hour': {
                str(hour): random.randint(20, 100) for hour in range(24)
            },
            'last_24h_transmissions': random.randint(150, 200),
            'peak_transmission_time': '14:00',
            'compliance_failures_by_type': {
                'signature_invalid': 12,
                'timestamp_expired': 8,
                'certificate_expired': 3,
                'payload_too_large': 5
            }
        }
        return data
    
    def _generate_mock_certificate_data(self) -> Dict[str, Any]:
        """Generate mock certificate data"""
        now = datetime.now(timezone.utc)
        return {
            'total_certificates': 25,
            'active_certificates': 23,
            'expiring_soon': 3,  # Within 30 days
            'expired_certificates': 2,
            'certificate_utilization': 87.5,
            'average_certificate_age': 180,  # days
            'certificates_by_type': {
                'transmission': 15,
                'signature': 8,
                'encryption': 2
            },
            'next_expiry_date': (now + timedelta(days=15)).isoformat(),
            'rotation_compliance': 92.3
        }
    
    def _generate_mock_audit_data(self) -> Dict[str, Any]:
        """Generate mock audit data"""
        return {
            'audit_logs_retention_days': 365,
            'audit_events_last_24h': 2450,
            'successful_audits': 2398,
            'failed_audits': 52,
            'audit_log_size_mb': 1250,
            'integrity_checks_passed': 99.8,
            'unauthorized_access_attempts': 3,
            'audit_trail_completeness': 99.95,
            'log_retention_compliance': 100.0
        }
    
    async def get_transmission_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get transmission-related compliance metrics"""
        return self._mock_transmission_data
    
    async def get_certificate_metrics(self) -> Dict[str, Any]:
        """Get certificate-related compliance metrics"""
        return self._mock_certificate_data
    
    async def get_audit_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get audit-related compliance metrics"""
        return self._mock_audit_data
    
    async def get_security_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get security events for compliance monitoring"""
        import random
        
        events = []
        event_types = [
            'failed_authentication',
            'unauthorized_access',
            'certificate_mismatch',
            'signature_validation_failure',
            'timestamp_violation'
        ]
        
        for i in range(random.randint(5, 15)):
            event_time = start_date + timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )
            
            events.append({
                'event_id': f"SEC_{i+1:06d}",
                'event_type': random.choice(event_types),
                'timestamp': event_time.isoformat(),
                'source_ip': f"192.168.1.{random.randint(1, 254)}",
                'severity': random.choice(['low', 'medium', 'high']),
                'details': f"Security event {i+1}"
            })
        
        return events


class FIRSComplianceRules:
    """Predefined FIRS compliance rules"""
    
    @staticmethod
    def get_default_rules() -> List[ComplianceRule]:
        """Get default FIRS compliance rules"""
        return [
            # Transmission Compliance Rules
            ComplianceRule(
                rule_id="TRANS_001",
                name="Transmission Success Rate",
                description="Minimum 95% transmission success rate required",
                category=ComplianceCategory.TRANSMISSION_COMPLIANCE,
                requirement="Transmission success rate must be >= 95%",
                threshold=95.0,
                operator=">=",
                alert_level=AlertLevel.CRITICAL
            ),
            ComplianceRule(
                rule_id="TRANS_002",
                name="Response Time Compliance",
                description="Average response time must be under 5 seconds",
                category=ComplianceCategory.TRANSMISSION_COMPLIANCE,
                requirement="Average response time <= 5 seconds",
                threshold=5.0,
                operator="<=",
                alert_level=AlertLevel.WARNING
            ),
            
            # Signature Compliance Rules
            ComplianceRule(
                rule_id="SIG_001",
                name="Signature Validation Rate",
                description="Signature validation failure rate must be < 1%",
                category=ComplianceCategory.SIGNATURE_COMPLIANCE,
                requirement="Signature validation failure rate < 1%",
                threshold=1.0,
                operator="<",
                alert_level=AlertLevel.CRITICAL
            ),
            
            # Timestamp Compliance Rules
            ComplianceRule(
                rule_id="TIME_001",
                name="Timestamp Compliance",
                description="Timestamp violations must be < 0.5%",
                category=ComplianceCategory.TIMESTAMP_COMPLIANCE,
                requirement="Timestamp violations < 0.5% of total transmissions",
                threshold=0.5,
                operator="<",
                alert_level=AlertLevel.WARNING
            ),
            
            # Certificate Compliance Rules
            ComplianceRule(
                rule_id="CERT_001",
                name="Certificate Expiry Warning",
                description="No certificates should expire within 30 days without renewal plan",
                category=ComplianceCategory.CERTIFICATE_COMPLIANCE,
                requirement="Certificates expiring within 30 days <= 2",
                threshold=2,
                operator="<=",
                alert_level=AlertLevel.WARNING
            ),
            ComplianceRule(
                rule_id="CERT_002",
                name="Certificate Utilization",
                description="Certificate utilization should be < 90%",
                category=ComplianceCategory.CERTIFICATE_COMPLIANCE,
                requirement="Certificate utilization < 90%",
                threshold=90.0,
                operator="<",
                alert_level=AlertLevel.INFO
            ),
            
            # Audit Compliance Rules
            ComplianceRule(
                rule_id="AUDIT_001",
                name="Audit Log Retention",
                description="Audit logs must be retained for minimum 365 days",
                category=ComplianceCategory.AUDIT_COMPLIANCE,
                requirement="Audit log retention >= 365 days",
                threshold=365,
                operator=">=",
                alert_level=AlertLevel.CRITICAL
            ),
            ComplianceRule(
                rule_id="AUDIT_002",
                name="Audit Trail Completeness",
                description="Audit trail completeness must be >= 99%",
                category=ComplianceCategory.AUDIT_COMPLIANCE,
                requirement="Audit trail completeness >= 99%",
                threshold=99.0,
                operator=">=",
                alert_level=AlertLevel.CRITICAL
            ),
            
            # Security Compliance Rules
            ComplianceRule(
                rule_id="SEC_001",
                name="Unauthorized Access Attempts",
                description="Unauthorized access attempts must be < 10 per day",
                category=ComplianceCategory.SECURITY_COMPLIANCE,
                requirement="Unauthorized access attempts < 10 per day",
                threshold=10,
                operator="<",
                alert_level=AlertLevel.WARNING
            )
        ]


class ComplianceMetricsMonitor:
    """
    Monitors FIRS compliance metrics and generates compliance reports
    Tracks regulatory adherence and identifies compliance violations
    """
    
    def __init__(self, data_provider: Optional[ComplianceDataProvider] = None):
        self.data_provider = data_provider or ComplianceDataProvider()
        self.logger = logging.getLogger(__name__)
        
        # Compliance rules
        self.rules = {rule.rule_id: rule for rule in FIRSComplianceRules.get_default_rules()}
        
        # Violation tracking
        self.active_violations: Dict[str, ComplianceViolation] = {}
        self.violation_history: List[ComplianceViolation] = []
        
        # Monitoring statistics
        self.stats = {
            'total_checks_performed': 0,
            'violations_detected': 0,
            'violations_resolved': 0,
            'last_check_at': None,
            'average_compliance_score': 0.0,
            'compliance_trend': 'stable',
            'category_scores': {}
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 1,
            AlertLevel.CRITICAL: 3,
            AlertLevel.EMERGENCY: 5
        }
    
    async def check_compliance(self, 
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> ComplianceReport:
        """
        Perform comprehensive compliance check
        
        Args:
            start_date: Start date for compliance period
            end_date: End date for compliance period
            
        Returns:
            Comprehensive compliance report
        """
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        self.logger.info(f"Starting compliance check for period {start_date} to {end_date}")
        
        try:
            # Collect all metrics
            metrics = await self._collect_all_metrics(start_date, end_date)
            
            # Evaluate compliance rules
            violations = await self._evaluate_compliance_rules(metrics)
            
            # Calculate overall compliance score
            overall_score, overall_status = self._calculate_compliance_score(metrics, violations)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(violations)
            
            # Create summary
            summary = self._create_compliance_summary(metrics, violations)
            
            # Create report
            report = ComplianceReport(
                report_id=f"COMP_{int(datetime.now(timezone.utc).timestamp())}",
                generated_at=datetime.now(timezone.utc),
                period_start=start_date,
                period_end=end_date,
                overall_status=overall_status,
                overall_score=overall_score,
                metrics=metrics,
                violations=violations,
                recommendations=recommendations,
                summary=summary
            )
            
            # Update statistics
            self._update_stats(overall_score, violations)
            
            self.logger.info(
                f"Compliance check completed: Score {overall_score:.1f}%, "
                f"Status {overall_status.value}, {len(violations)} violations"
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error during compliance check: {str(e)}")
            raise
    
    async def _collect_all_metrics(self, start_date: datetime, end_date: datetime) -> List[ComplianceMetric]:
        """Collect all compliance metrics from various sources"""
        metrics = []
        
        # Transmission metrics
        transmission_data = await self.data_provider.get_transmission_metrics(start_date, end_date)
        metrics.extend(self._create_transmission_metrics(transmission_data))
        
        # Certificate metrics
        certificate_data = await self.data_provider.get_certificate_metrics()
        metrics.extend(self._create_certificate_metrics(certificate_data))
        
        # Audit metrics
        audit_data = await self.data_provider.get_audit_metrics(start_date, end_date)
        metrics.extend(self._create_audit_metrics(audit_data))
        
        # Security metrics
        security_events = await self.data_provider.get_security_events(start_date, end_date)
        metrics.extend(self._create_security_metrics(security_events))
        
        return metrics
    
    def _create_transmission_metrics(self, data: Dict[str, Any]) -> List[ComplianceMetric]:
        """Create transmission compliance metrics"""
        now = datetime.now(timezone.utc)
        metrics = []
        
        # Success rate
        total = data.get('total_transmissions', 0)
        successful = data.get('successful_transmissions', 0)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        metrics.append(ComplianceMetric(
            metric_id="TRANS_SUCCESS_RATE",
            name="Transmission Success Rate",
            category=ComplianceCategory.TRANSMISSION_COMPLIANCE,
            value=success_rate,
            unit="%",
            status=ComplianceStatus.COMPLIANT if success_rate >= 95 else ComplianceStatus.NON_COMPLIANT,
            measured_at=now,
            benchmark=95.0
        ))
        
        # Response time
        avg_response_time = data.get('average_response_time', 0)
        metrics.append(ComplianceMetric(
            metric_id="TRANS_RESPONSE_TIME",
            name="Average Response Time",
            category=ComplianceCategory.TRANSMISSION_COMPLIANCE,
            value=avg_response_time,
            unit="seconds",
            status=ComplianceStatus.COMPLIANT if avg_response_time <= 5.0 else ComplianceStatus.NON_COMPLIANT,
            measured_at=now,
            benchmark=5.0
        ))
        
        # Signature validation failures
        sig_failures = data.get('signature_validation_failures', 0)
        sig_failure_rate = (sig_failures / total * 100) if total > 0 else 0
        
        metrics.append(ComplianceMetric(
            metric_id="SIG_VALIDATION_RATE",
            name="Signature Validation Failure Rate",
            category=ComplianceCategory.SIGNATURE_COMPLIANCE,
            value=sig_failure_rate,
            unit="%",
            status=ComplianceStatus.COMPLIANT if sig_failure_rate < 1.0 else ComplianceStatus.NON_COMPLIANT,
            measured_at=now,
            benchmark=1.0
        ))
        
        return metrics
    
    def _create_certificate_metrics(self, data: Dict[str, Any]) -> List[ComplianceMetric]:
        """Create certificate compliance metrics"""
        now = datetime.now(timezone.utc)
        metrics = []
        
        # Certificate expiry
        expiring_soon = data.get('expiring_soon', 0)
        metrics.append(ComplianceMetric(
            metric_id="CERT_EXPIRY_WARNING",
            name="Certificates Expiring Soon",
            category=ComplianceCategory.CERTIFICATE_COMPLIANCE,
            value=expiring_soon,
            unit="count",
            status=ComplianceStatus.COMPLIANT if expiring_soon <= 2 else ComplianceStatus.NON_COMPLIANT,
            measured_at=now,
            benchmark=2
        ))
        
        # Certificate utilization
        utilization = data.get('certificate_utilization', 0)
        metrics.append(ComplianceMetric(
            metric_id="CERT_UTILIZATION",
            name="Certificate Utilization",
            category=ComplianceCategory.CERTIFICATE_COMPLIANCE,
            value=utilization,
            unit="%",
            status=ComplianceStatus.COMPLIANT if utilization < 90 else ComplianceStatus.NON_COMPLIANT,
            measured_at=now,
            benchmark=90.0
        ))
        
        return metrics
    
    def _create_audit_metrics(self, data: Dict[str, Any]) -> List[ComplianceMetric]:
        """Create audit compliance metrics"""
        now = datetime.now(timezone.utc)
        metrics = []
        
        # Audit log retention
        retention_days = data.get('audit_logs_retention_days', 0)
        metrics.append(ComplianceMetric(
            metric_id="AUDIT_RETENTION",
            name="Audit Log Retention",
            category=ComplianceCategory.AUDIT_COMPLIANCE,
            value=retention_days,
            unit="days",
            status=ComplianceStatus.COMPLIANT if retention_days >= 365 else ComplianceStatus.NON_COMPLIANT,
            measured_at=now,
            benchmark=365
        ))
        
        # Audit trail completeness
        completeness = data.get('audit_trail_completeness', 0)
        metrics.append(ComplianceMetric(
            metric_id="AUDIT_COMPLETENESS",
            name="Audit Trail Completeness",
            category=ComplianceCategory.AUDIT_COMPLIANCE,
            value=completeness,
            unit="%",
            status=ComplianceStatus.COMPLIANT if completeness >= 99.0 else ComplianceStatus.NON_COMPLIANT,
            measured_at=now,
            benchmark=99.0
        ))
        
        return metrics
    
    def _create_security_metrics(self, events: List[Dict[str, Any]]) -> List[ComplianceMetric]:
        """Create security compliance metrics"""
        now = datetime.now(timezone.utc)
        metrics = []
        
        # Unauthorized access attempts
        unauthorized_attempts = len([
            event for event in events 
            if event.get('event_type') == 'unauthorized_access'
        ])
        
        metrics.append(ComplianceMetric(
            metric_id="SEC_UNAUTHORIZED_ACCESS",
            name="Unauthorized Access Attempts",
            category=ComplianceCategory.SECURITY_COMPLIANCE,
            value=unauthorized_attempts,
            unit="count",
            status=ComplianceStatus.COMPLIANT if unauthorized_attempts < 10 else ComplianceStatus.NON_COMPLIANT,
            measured_at=now,
            benchmark=10
        ))
        
        return metrics
    
    async def _evaluate_compliance_rules(self, metrics: List[ComplianceMetric]) -> List[ComplianceViolation]:
        """Evaluate compliance rules against collected metrics"""
        violations = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Find matching metric
            matching_metric = None
            for metric in metrics:
                if self._rule_matches_metric(rule, metric):
                    matching_metric = metric
                    break
            
            if not matching_metric:
                continue
            
            # Evaluate rule
            violation = self._evaluate_single_rule(rule, matching_metric)
            if violation:
                violations.append(violation)
                
                # Track violation
                self.active_violations[violation.violation_id] = violation
        
        return violations
    
    def _rule_matches_metric(self, rule: ComplianceRule, metric: ComplianceMetric) -> bool:
        """Check if a rule applies to a metric"""
        return (
            rule.category == metric.category or
            rule.rule_id.startswith(metric.metric_id[:4]) or
            rule.name.lower() in metric.name.lower()
        )
    
    def _evaluate_single_rule(self, rule: ComplianceRule, metric: ComplianceMetric) -> Optional[ComplianceViolation]:
        """Evaluate a single compliance rule"""
        try:
            current_value = metric.value
            threshold = rule.threshold
            operator = rule.operator
            
            # Convert values to comparable types
            if isinstance(current_value, str) and isinstance(threshold, (int, float)):
                try:
                    current_value = float(current_value)
                except ValueError:
                    return None
            
            # Evaluate condition
            violation_detected = False
            
            if operator == ">=":
                violation_detected = current_value < threshold
            elif operator == "<=":
                violation_detected = current_value > threshold
            elif operator == ">":
                violation_detected = current_value <= threshold
            elif operator == "<":
                violation_detected = current_value >= threshold
            elif operator == "==":
                violation_detected = current_value != threshold
            elif operator == "!=":
                violation_detected = current_value == threshold
            
            if violation_detected:
                return ComplianceViolation(
                    violation_id=f"VIO_{rule.rule_id}_{int(datetime.now(timezone.utc).timestamp())}",
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    category=rule.category,
                    description=f"Rule violation: {rule.description}",
                    severity=rule.alert_level,
                    detected_at=datetime.now(timezone.utc),
                    current_value=current_value,
                    expected_value=threshold,
                    affected_entities=[metric.metric_id],
                    remediation_steps=self._get_remediation_steps(rule)
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error evaluating rule {rule.rule_id}: {str(e)}")
            return None
    
    def _get_remediation_steps(self, rule: ComplianceRule) -> List[str]:
        """Get remediation steps for a compliance rule"""
        remediation_map = {
            "TRANS_001": [
                "Review failed transmission logs",
                "Check network connectivity to FIRS",
                "Validate payload formats",
                "Implement retry mechanisms"
            ],
            "TRANS_002": [
                "Optimize payload size",
                "Review network latency",
                "Implement connection pooling",
                "Consider timeout adjustments"
            ],
            "SIG_001": [
                "Verify signature algorithms",
                "Check certificate validity",
                "Review HMAC key configuration",
                "Validate timestamp synchronization"
            ],
            "CERT_001": [
                "Schedule certificate renewal",
                "Request new certificates from CA",
                "Update certificate deployment process",
                "Set up expiry monitoring alerts"
            ],
            "AUDIT_001": [
                "Extend audit log retention policy",
                "Implement log archival system",
                "Review storage capacity",
                "Update log rotation settings"
            ]
        }
        
        return remediation_map.get(rule.rule_id, ["Review compliance requirements", "Contact system administrator"])
    
    def _calculate_compliance_score(self, 
                                   metrics: List[ComplianceMetric],
                                   violations: List[ComplianceViolation]) -> Tuple[float, ComplianceStatus]:
        """Calculate overall compliance score and status"""
        if not metrics:
            return 0.0, ComplianceStatus.UNKNOWN
        
        # Calculate score based on compliant metrics
        compliant_metrics = len([m for m in metrics if m.status == ComplianceStatus.COMPLIANT])
        total_metrics = len(metrics)
        base_score = (compliant_metrics / total_metrics) * 100
        
        # Apply penalties for violations
        violation_penalties = {
            AlertLevel.INFO: 1,
            AlertLevel.WARNING: 3,
            AlertLevel.CRITICAL: 10,
            AlertLevel.EMERGENCY: 25
        }
        
        total_penalty = sum(
            violation_penalties.get(violation.severity, 0)
            for violation in violations
        )
        
        final_score = max(0, base_score - total_penalty)
        
        # Determine status
        if final_score >= 95:
            status = ComplianceStatus.COMPLIANT
        elif final_score >= 80:
            status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        return round(final_score, 1), status
    
    def _generate_recommendations(self, violations: List[ComplianceViolation]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Group violations by category
        category_violations = defaultdict(list)
        for violation in violations:
            category_violations[violation.category].append(violation)
        
        # Generate category-specific recommendations
        for category, category_violations_list in category_violations.items():
            if category == ComplianceCategory.TRANSMISSION_COMPLIANCE:
                recommendations.append(
                    f"Address {len(category_violations_list)} transmission compliance issues by reviewing "
                    "network connectivity, payload validation, and retry mechanisms."
                )
            elif category == ComplianceCategory.CERTIFICATE_COMPLIANCE:
                recommendations.append(
                    f"Resolve {len(category_violations_list)} certificate compliance issues by "
                    "implementing proactive certificate renewal and monitoring."
                )
            elif category == ComplianceCategory.AUDIT_COMPLIANCE:
                recommendations.append(
                    f"Fix {len(category_violations_list)} audit compliance issues by "
                    "extending retention policies and improving log management."
                )
        
        # General recommendations
        critical_violations = [v for v in violations if v.severity == AlertLevel.CRITICAL]
        if critical_violations:
            recommendations.append(
                f"Immediately address {len(critical_violations)} critical compliance violations "
                "as they pose significant regulatory risk."
            )
        
        if not recommendations:
            recommendations.append("Maintain current compliance practices and continue monitoring.")
        
        return recommendations
    
    def _create_compliance_summary(self, 
                                  metrics: List[ComplianceMetric],
                                  violations: List[ComplianceViolation]) -> Dict[str, Any]:
        """Create compliance summary statistics"""
        # Category breakdown
        category_scores = {}
        for category in ComplianceCategory:
            category_metrics = [m for m in metrics if m.category == category]
            if category_metrics:
                compliant_count = len([m for m in category_metrics if m.status == ComplianceStatus.COMPLIANT])
                category_scores[category.value] = {
                    'total_metrics': len(category_metrics),
                    'compliant_metrics': compliant_count,
                    'compliance_rate': round(compliant_count / len(category_metrics) * 100, 1)
                }
        
        # Violation summary
        violation_summary = {
            'total_violations': len(violations),
            'by_severity': Counter(v.severity.value for v in violations),
            'by_category': Counter(v.category.value for v in violations)
        }
        
        # Trend analysis (mock implementation)
        trend_data = {
            'compliance_trend': 'improving',  # Would be calculated from historical data
            'key_improvements': ['Response time optimization', 'Certificate management'],
            'areas_of_concern': ['Signature validation', 'Audit log retention']
        }
        
        return {
            'category_scores': category_scores,
            'violation_summary': violation_summary,
            'trend_analysis': trend_data,
            'metric_count': len(metrics),
            'compliant_metrics': len([m for m in metrics if m.status == ComplianceStatus.COMPLIANT])
        }
    
    def _update_stats(self, compliance_score: float, violations: List[ComplianceViolation]):
        """Update monitoring statistics"""
        self.stats['total_checks_performed'] += 1
        self.stats['violations_detected'] += len(violations)
        self.stats['last_check_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update average compliance score
        current_avg = self.stats['average_compliance_score']
        total_checks = self.stats['total_checks_performed']
        self.stats['average_compliance_score'] = (
            (current_avg * (total_checks - 1) + compliance_score) / total_checks
        )
    
    async def get_compliance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get compliance trends over specified period"""
        # Mock implementation - would query historical data
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Generate mock trend data
        import random
        
        daily_scores = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            score = 85 + random.uniform(-5, 10)  # Mock score variation
            score = min(100, max(0, score))
            
            daily_scores.append({
                'date': date.strftime('%Y-%m-%d'),
                'compliance_score': round(score, 1),
                'violations_count': random.randint(0, 5)
            })
        
        return {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'daily_scores': daily_scores,
            'average_score': round(statistics.mean([d['compliance_score'] for d in daily_scores]), 1),
            'trend_direction': 'improving' if daily_scores[-1]['compliance_score'] > daily_scores[0]['compliance_score'] else 'declining'
        }
    
    async def resolve_violation(self, violation_id: str, resolution_notes: str) -> bool:
        """Mark a compliance violation as resolved"""
        if violation_id in self.active_violations:
            violation = self.active_violations.pop(violation_id)
            violation.resolved = True
            violation.resolved_at = datetime.now(timezone.utc)
            
            self.violation_history.append(violation)
            self.stats['violations_resolved'] += 1
            
            self.logger.info(f"Compliance violation {violation_id} resolved: {resolution_notes}")
            return True
        
        return False
    
    def add_custom_rule(self, rule: ComplianceRule):
        """Add a custom compliance rule"""
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added custom compliance rule: {rule.rule_id}")
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a compliance rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            self.logger.info(f"Disabled compliance rule: {rule_id}")
            return True
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Get compliance monitor health status"""
        active_violations_count = len(self.active_violations)
        critical_violations = len([
            v for v in self.active_violations.values() 
            if v.severity == AlertLevel.CRITICAL
        ])
        
        status = "healthy"
        if critical_violations > 0:
            status = "critical"
        elif active_violations_count > 10:
            status = "degraded"
        
        return {
            'status': status,
            'service': 'compliance_metrics',
            'active_violations': active_violations_count,
            'critical_violations': critical_violations,
            'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
            'total_rules': len(self.rules),
            'stats': self.stats.copy(),
            'supported_categories': [cat.value for cat in ComplianceCategory],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup compliance monitor resources"""
        self.logger.info("Compliance metrics monitor cleanup initiated")
        
        # Log final statistics
        self.logger.info(f"Final compliance monitoring statistics: {self.stats}")
        
        # Clear active violations
        self.active_violations.clear()
        
        self.logger.info("Compliance metrics monitor cleanup completed")


# Factory functions
def create_compliance_monitor() -> ComplianceMetricsMonitor:
    """Create compliance metrics monitor with standard configuration"""
    return ComplianceMetricsMonitor()


def create_custom_rule(rule_id: str,
                      name: str,
                      category: ComplianceCategory,
                      threshold: Union[float, int, str],
                      operator: str = ">=",
                      alert_level: AlertLevel = AlertLevel.WARNING) -> ComplianceRule:
    """Create a custom compliance rule"""
    return ComplianceRule(
        rule_id=rule_id,
        name=name,
        description=f"Custom rule: {name}",
        category=category,
        requirement=f"{name} {operator} {threshold}",
        threshold=threshold,
        operator=operator,
        alert_level=alert_level
    )