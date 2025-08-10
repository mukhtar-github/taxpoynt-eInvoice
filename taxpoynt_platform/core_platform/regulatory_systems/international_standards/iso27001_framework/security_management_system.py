"""
ISO 27001 Information Security Management System
===============================================
Central ISMS implementation for comprehensive information security management
according to ISO 27001 standard with Nigerian regulatory integration.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum

from .models import (
    ISO27001Control, SecurityRisk, ComplianceResult, SecurityIncident,
    AuditFinding, ControlStatus, RiskLevel, ControlDomain, ISMSScope,
    PolicyDocument, SecurityMetrics, ThreatType, IncidentSeverity
)


class ISMSMaturityLevel(str, Enum):
    """ISMS maturity levels."""
    INITIAL = "initial"         # Ad-hoc, reactive
    MANAGED = "managed"         # Basic processes in place
    DEFINED = "defined"         # Documented processes
    QUANTITATIVELY_MANAGED = "quantitatively_managed"  # Measured processes
    OPTIMIZING = "optimizing"   # Continuous improvement


class CertificationStatus(str, Enum):
    """ISO 27001 certification status."""
    NOT_CERTIFIED = "not_certified"
    PREPARING = "preparing"
    AUDIT_SCHEDULED = "audit_scheduled"
    AUDIT_IN_PROGRESS = "audit_in_progress"
    CERTIFIED = "certified"
    SURVEILLANCE = "surveillance"
    RECERTIFICATION = "recertification"
    SUSPENDED = "suspended"


class ISMSResult(BaseModel):
    """ISMS assessment result."""
    # Assessment overview
    assessment_date: datetime = Field(default_factory=datetime.now)
    overall_maturity: ISMSMaturityLevel = Field(...)
    certification_status: CertificationStatus = Field(...)
    
    # Compliance metrics
    compliance_percentage: float = Field(..., ge=0.0, le=100.0)
    implemented_controls: int = Field(..., ge=0)
    total_applicable_controls: int = Field(..., ge=0)
    
    # Risk metrics
    total_risks: int = Field(0)
    critical_risks: int = Field(0)
    high_risks: int = Field(0)
    residual_risk_level: RiskLevel = Field(...)
    
    # Findings and incidents
    open_findings: int = Field(0)
    security_incidents_ytd: int = Field(0)
    
    # Improvement areas
    priority_improvements: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    
    # Nigerian compliance
    nitda_compliance_score: Optional[float] = Field(None)
    cbn_compliance_score: Optional[float] = Field(None)


class ISO27001ISMS:
    """
    ISO 27001 Information Security Management System.
    
    Features:
    - Complete ISMS lifecycle management
    - 114 ISO 27001 controls assessment
    - Risk management and treatment
    - Incident management
    - Audit and compliance monitoring
    - Nigerian regulatory integration (NITDA, CBN)
    - Continuous improvement framework
    - Certification readiness assessment
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize ISO 27001 ISMS.
        
        Args:
            config: ISMS configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # ISMS configuration
        self.organization_name = self.config.get('organization_name', 'TaxPoynt')
        self.nigerian_operations = self.config.get('nigerian_operations', True)
        self.certification_target = self.config.get('certification_target', False)
        
        # Control framework
        self.controls_database = self._initialize_controls_database()
        self.risk_register = {}
        self.incident_register = {}
        self.audit_findings = {}
        
        # Nigerian regulatory context
        self.nitda_compliance = self.config.get('nitda_compliance', True)
        self.cbn_compliance = self.config.get('cbn_compliance', False)
        
        # Maturity and certification
        self.current_maturity = ISMSMaturityLevel.INITIAL
        self.certification_status = CertificationStatus.NOT_CERTIFIED
        
        self.logger.info(f"ISO 27001 ISMS initialized for {self.organization_name}")
    
    def assess_isms_maturity(self) -> ISMSResult:
        """
        Comprehensive ISMS maturity assessment.
        
        Returns:
            ISMSResult: Complete ISMS assessment results
        """
        self.logger.info("Starting comprehensive ISMS maturity assessment")
        
        try:
            # 1. Control implementation assessment
            control_results = self._assess_control_implementation()
            
            # 2. Risk management maturity
            risk_maturity = self._assess_risk_management_maturity()
            
            # 3. Incident management effectiveness
            incident_effectiveness = self._assess_incident_management()
            
            # 4. Audit and review effectiveness
            audit_effectiveness = self._assess_audit_framework()
            
            # 5. Nigerian regulatory compliance
            nigerian_compliance = self._assess_nigerian_compliance()
            
            # 6. Calculate overall maturity
            overall_maturity = self._calculate_overall_maturity(
                control_results, risk_maturity, incident_effectiveness,
                audit_effectiveness, nigerian_compliance
            )
            
            # 7. Determine certification readiness
            certification_status = self._assess_certification_readiness(overall_maturity)
            
            # 8. Generate improvement recommendations
            recommendations = self._generate_improvement_recommendations(
                control_results, risk_maturity, nigerian_compliance
            )
            
            result = ISMSResult(
                overall_maturity=overall_maturity,
                certification_status=certification_status,
                compliance_percentage=control_results['compliance_percentage'],
                implemented_controls=control_results['implemented_controls'],
                total_applicable_controls=control_results['total_controls'],
                total_risks=len(self.risk_register),
                critical_risks=sum(1 for r in self.risk_register.values() if r.risk_level == RiskLevel.CRITICAL),
                high_risks=sum(1 for r in self.risk_register.values() if r.risk_level == RiskLevel.HIGH),
                residual_risk_level=self._calculate_residual_risk_level(),
                open_findings=len([f for f in self.audit_findings.values() if f.status == 'open']),
                security_incidents_ytd=self._count_incidents_ytd(),
                priority_improvements=recommendations['priority'],
                recommended_actions=recommendations['actions'],
                nitda_compliance_score=nigerian_compliance.get('nitda_score'),
                cbn_compliance_score=nigerian_compliance.get('cbn_score')
            )
            
            self.current_maturity = overall_maturity
            self.certification_status = certification_status
            
            self.logger.info(f"ISMS assessment completed: {overall_maturity.value} maturity, {control_results['compliance_percentage']:.1f}% compliant")
            return result
            
        except Exception as e:
            self.logger.error(f"ISMS assessment failed: {str(e)}")
            raise
    
    def perform_control_assessment(self, domain: Optional[ControlDomain] = None) -> Dict[str, Any]:
        """
        Perform detailed control assessment.
        
        Args:
            domain: Specific domain to assess (optional)
            
        Returns:
            Dict: Control assessment results
        """
        controls_to_assess = self.controls_database
        
        if domain:
            controls_to_assess = {
                k: v for k, v in self.controls_database.items()
                if v.domain == domain
            }
        
        assessment_results = {
            'total_controls': len(controls_to_assess),
            'compliant_controls': 0,
            'partially_compliant': 0,
            'non_compliant': 0,
            'not_applicable': 0,
            'domain_results': {},
            'critical_gaps': [],
            'improvement_priorities': []
        }
        
        # Assess each control
        for control_id, control in controls_to_assess.items():
            # Perform detailed control assessment
            control_result = self._assess_individual_control(control)
            
            # Update counters
            if control_result['status'] == ControlStatus.COMPLIANT:
                assessment_results['compliant_controls'] += 1
            elif control_result['status'] == ControlStatus.PARTIALLY_COMPLIANT:
                assessment_results['partially_compliant'] += 1
            elif control_result['status'] == ControlStatus.NON_COMPLIANT:
                assessment_results['non_compliant'] += 1
                if control_result['risk_level'] in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                    assessment_results['critical_gaps'].append(control_id)
            elif control_result['status'] == ControlStatus.NOT_APPLICABLE:
                assessment_results['not_applicable'] += 1
            
            # Domain aggregation
            domain_key = control.domain.value
            if domain_key not in assessment_results['domain_results']:
                assessment_results['domain_results'][domain_key] = {
                    'total': 0, 'compliant': 0, 'compliance_percentage': 0.0
                }
            
            assessment_results['domain_results'][domain_key]['total'] += 1
            if control_result['status'] == ControlStatus.COMPLIANT:
                assessment_results['domain_results'][domain_key]['compliant'] += 1
        
        # Calculate domain compliance percentages
        for domain_key, domain_data in assessment_results['domain_results'].items():
            if domain_data['total'] > 0:
                domain_data['compliance_percentage'] = (
                    domain_data['compliant'] / domain_data['total']
                ) * 100
        
        # Overall compliance percentage
        applicable_controls = assessment_results['total_controls'] - assessment_results['not_applicable']
        if applicable_controls > 0:
            assessment_results['compliance_percentage'] = (
                assessment_results['compliant_controls'] / applicable_controls
            ) * 100
        else:
            assessment_results['compliance_percentage'] = 0.0
        
        return assessment_results
    
    def manage_security_risk(self, risk: SecurityRisk) -> Dict[str, Any]:
        """
        Add or update security risk in risk register.
        
        Args:
            risk: Security risk to manage
            
        Returns:
            Dict: Risk management result
        """
        # Add to risk register
        self.risk_register[risk.risk_id] = risk
        
        # Determine treatment requirements
        treatment_required = risk.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
        
        # Generate risk treatment recommendations
        recommendations = self._generate_risk_treatment_recommendations(risk)
        
        result = {
            'risk_registered': True,
            'risk_level': risk.risk_level.value,
            'treatment_required': treatment_required,
            'recommendations': recommendations,
            'affected_controls': self._identify_affected_controls(risk),
            'escalation_required': risk.risk_level == RiskLevel.CRITICAL
        }
        
        # Log critical risks
        if risk.risk_level == RiskLevel.CRITICAL:
            self.logger.warning(f"Critical risk registered: {risk.risk_name}")
        
        return result
    
    def handle_security_incident(self, incident: SecurityIncident) -> Dict[str, Any]:
        """
        Handle security incident according to ISO 27001.
        
        Args:
            incident: Security incident to handle
            
        Returns:
            Dict: Incident handling result
        """
        # Add to incident register
        self.incident_register[incident.incident_id] = incident
        
        # Determine response requirements
        response_requirements = self._determine_incident_response_requirements(incident)
        
        # Nigerian regulatory reporting requirements
        nigerian_reporting = self._assess_nigerian_incident_reporting(incident)
        
        # Generate lessons learned
        if incident.resolved_date:
            lessons_learned = self._extract_lessons_learned(incident)
        else:
            lessons_learned = []
        
        result = {
            'incident_registered': True,
            'severity': incident.severity.value,
            'immediate_actions': response_requirements['immediate'],
            'follow_up_actions': response_requirements['follow_up'],
            'regulatory_reporting': nigerian_reporting,
            'lessons_learned': lessons_learned,
            'control_improvements': self._identify_control_improvements(incident)
        }
        
        # Log critical incidents
        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            self.logger.error(f"High-severity incident: {incident.title}")
        
        return result
    
    def generate_compliance_report(self) -> ComplianceResult:
        """
        Generate comprehensive ISO 27001 compliance report.
        
        Returns:
            ComplianceResult: Detailed compliance assessment
        """
        # Perform control assessment
        control_assessment = self.perform_control_assessment()
        
        # Risk assessment summary
        risk_summary = self._generate_risk_summary()
        
        # Calculate domain compliance
        domain_compliance = control_assessment['domain_results']
        domain_compliance_dict = {
            domain: data['compliance_percentage']
            for domain, data in domain_compliance.items()
        }
        
        # Audit findings summary
        findings_summary = self._generate_findings_summary()
        
        # Maturity assessment
        maturity_assessment = self._assess_current_maturity()
        
        # Nigerian compliance assessment
        nigerian_assessment = self._assess_nigerian_compliance()
        
        result = ComplianceResult(
            assessment_id=f"ISMS-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            assessor=f"TaxPoynt ISMS Engine",
            overall_compliance_percentage=control_assessment['compliance_percentage'],
            compliant_controls=control_assessment['compliant_controls'],
            total_controls=control_assessment['total_controls'],
            domain_compliance=domain_compliance_dict,
            overall_risk_level=risk_summary['overall_level'],
            critical_risks=risk_summary['critical_count'],
            high_risks=risk_summary['high_count'],
            total_findings=findings_summary['total'],
            critical_findings=findings_summary['critical'],
            high_findings=findings_summary['high'],
            certification_ready=control_assessment['compliance_percentage'] >= 80,
            improvement_areas=control_assessment['improvement_priorities'],
            nitda_compliance=nigerian_assessment.get('nitda_score'),
            cbn_compliance=nigerian_assessment.get('cbn_score'),
            maturity_level=maturity_assessment['overall_score'],
            maturity_by_domain=maturity_assessment['domain_scores']
        )
        
        # Add specific recommendations
        result.add_recommendation("Implement continuous monitoring for critical controls")
        result.add_recommendation("Conduct regular security awareness training")
        result.add_recommendation("Review and update risk assessments quarterly")
        
        if self.nigerian_operations:
            result.add_recommendation("Ensure NITDA cybersecurity guidelines compliance")
            if self.cbn_compliance:
                result.add_recommendation("Maintain CBN information security requirements")
        
        return result
    
    def _initialize_controls_database(self) -> Dict[str, ISO27001Control]:
        """Initialize ISO 27001 controls database."""
        controls = {}
        
        # Sample critical controls (in practice, would load all 114 controls)
        sample_controls = [
            {
                'control_id': 'A.5.1.1',
                'control_name': 'Policies for information security',
                'domain': ControlDomain.A05_POLICIES,
                'objective': 'To provide management direction and support for information security',
                'description': 'A set of policies for information security shall be defined, approved by management, published and communicated to employees and relevant external parties.'
            },
            {
                'control_id': 'A.6.1.1',
                'control_name': 'Information security roles and responsibilities',
                'domain': ControlDomain.A06_ORGANIZATION,
                'objective': 'To ensure that information security responsibilities are defined and allocated',
                'description': 'All information security responsibilities shall be defined and allocated.'
            },
            {
                'control_id': 'A.9.1.1',
                'control_name': 'Access control policy',
                'domain': ControlDomain.A09_ACCESS_CONTROL,
                'objective': 'To limit access to information and information processing facilities',
                'description': 'An access control policy shall be established, documented and reviewed based on business and information security requirements.'
            },
            {
                'control_id': 'A.12.6.1',
                'control_name': 'Management of technical vulnerabilities',
                'domain': ControlDomain.A12_OPERATIONS,
                'objective': 'To prevent exploitation of technical vulnerabilities',
                'description': 'Information about technical vulnerabilities of information systems being used shall be obtained in a timely fashion, the organization\'s exposure to such vulnerabilities evaluated and appropriate measures taken to address the associated risk.'
            },
            {
                'control_id': 'A.16.1.1',
                'control_name': 'Responsibilities and procedures',
                'domain': ControlDomain.A16_INCIDENTS,
                'objective': 'To ensure a consistent and effective approach to the management of information security incidents',
                'description': 'Management responsibilities and procedures shall be established to ensure a quick, effective and orderly response to information security incidents.'
            }
        ]
        
        for control_data in sample_controls:
            control = ISO27001Control(**control_data)
            controls[control.control_id] = control
        
        return controls
    
    def _assess_control_implementation(self) -> Dict[str, Any]:
        """Assess overall control implementation status."""
        return self.perform_control_assessment()
    
    def _assess_risk_management_maturity(self) -> Dict[str, Any]:
        """Assess risk management process maturity."""
        return {
            'maturity_score': 3.0,  # Would be calculated based on actual risk management practices
            'processes_documented': True,
            'regular_assessments': True,
            'treatment_plans': len(self.risk_register) > 0,
            'monitoring_active': True
        }
    
    def _assess_incident_management(self) -> Dict[str, Any]:
        """Assess incident management effectiveness."""
        incidents_this_year = self._count_incidents_ytd()
        
        return {
            'incidents_ytd': incidents_this_year,
            'average_response_time': self._calculate_average_response_time(),
            'procedures_documented': True,
            'training_completed': True,
            'effectiveness_score': 4.0 if incidents_this_year < 10 else 3.0
        }
    
    def _assess_audit_framework(self) -> Dict[str, Any]:
        """Assess internal audit framework effectiveness."""
        return {
            'audit_program_established': True,
            'regular_audits_conducted': True,
            'findings_tracked': len(self.audit_findings) > 0,
            'management_review_active': True,
            'effectiveness_score': 3.5
        }
    
    def _assess_nigerian_compliance(self) -> Dict[str, Any]:
        """Assess Nigerian regulatory compliance."""
        nigerian_score = 0.0
        cbn_score = 0.0
        
        if self.nigerian_operations:
            # NITDA compliance assessment
            if self.nitda_compliance:
                nigerian_score = 75.0  # Would be calculated based on actual NITDA requirements
            
            # CBN compliance assessment
            if self.cbn_compliance:
                cbn_score = 80.0  # Would be calculated based on actual CBN requirements
        
        return {
            'nitda_score': nigerian_score if self.nigerian_operations else None,
            'cbn_score': cbn_score if self.cbn_compliance else None,
            'overall_nigerian_compliance': max(nigerian_score, cbn_score) if self.nigerian_operations else None
        }
    
    def _calculate_overall_maturity(self, control_results: Dict, risk_maturity: Dict,
                                   incident_effectiveness: Dict, audit_effectiveness: Dict,
                                   nigerian_compliance: Dict) -> ISMSMaturityLevel:
        """Calculate overall ISMS maturity level."""
        # Weighted scoring
        control_score = control_results['compliance_percentage'] / 100 * 5
        risk_score = risk_maturity['maturity_score']
        incident_score = incident_effectiveness['effectiveness_score']
        audit_score = audit_effectiveness['effectiveness_score']
        
        # Calculate weighted average
        overall_score = (
            control_score * 0.4 +
            risk_score * 0.25 +
            incident_score * 0.2 +
            audit_score * 0.15
        )
        
        # Map to maturity levels
        if overall_score >= 4.5:
            return ISMSMaturityLevel.OPTIMIZING
        elif overall_score >= 3.5:
            return ISMSMaturityLevel.QUANTITATIVELY_MANAGED
        elif overall_score >= 2.5:
            return ISMSMaturityLevel.DEFINED
        elif overall_score >= 1.5:
            return ISMSMaturityLevel.MANAGED
        else:
            return ISMSMaturityLevel.INITIAL
    
    def _assess_certification_readiness(self, maturity: ISMSMaturityLevel) -> CertificationStatus:
        """Assess certification readiness."""
        if maturity in [ISMSMaturityLevel.QUANTITATIVELY_MANAGED, ISMSMaturityLevel.OPTIMIZING]:
            return CertificationStatus.CERTIFIED
        elif maturity == ISMSMaturityLevel.DEFINED:
            return CertificationStatus.PREPARING
        else:
            return CertificationStatus.NOT_CERTIFIED
    
    def _generate_improvement_recommendations(self, control_results: Dict, 
                                            risk_maturity: Dict, 
                                            nigerian_compliance: Dict) -> Dict[str, List[str]]:
        """Generate improvement recommendations."""
        priority_improvements = []
        recommended_actions = []
        
        # Control-based recommendations
        if control_results['compliance_percentage'] < 80:
            priority_improvements.append("Increase control implementation to achieve 80% compliance")
            recommended_actions.append("Focus on critical security controls implementation")
        
        # Risk management recommendations
        if risk_maturity['maturity_score'] < 3.0:
            priority_improvements.append("Enhance risk management processes")
            recommended_actions.append("Implement regular risk assessment procedures")
        
        # Nigerian compliance recommendations
        if self.nigerian_operations:
            if nigerian_compliance.get('nitda_score', 0) < 70:
                priority_improvements.append("Improve NITDA guidelines compliance")
                recommended_actions.append("Review and implement NITDA cybersecurity framework")
        
        return {
            'priority': priority_improvements,
            'actions': recommended_actions
        }
    
    def _assess_individual_control(self, control: ISO27001Control) -> Dict[str, Any]:
        """Assess individual control implementation."""
        # Simplified assessment - in practice would involve detailed evaluation
        return {
            'control_id': control.control_id,
            'status': control.status,
            'effectiveness_score': control.effectiveness_score,
            'risk_level': control.risk_level,
            'implementation_gaps': [],
            'evidence_quality': 'adequate'
        }
    
    def _calculate_residual_risk_level(self) -> RiskLevel:
        """Calculate overall residual risk level."""
        if not self.risk_register:
            return RiskLevel.LOW
        
        risk_levels = [risk.risk_level for risk in self.risk_register.values()]
        
        if RiskLevel.CRITICAL in risk_levels:
            return RiskLevel.CRITICAL
        elif RiskLevel.HIGH in risk_levels:
            return RiskLevel.HIGH
        elif RiskLevel.MEDIUM in risk_levels:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _count_incidents_ytd(self) -> int:
        """Count security incidents year-to-date."""
        current_year = datetime.now().year
        return sum(
            1 for incident in self.incident_register.values()
            if incident.detected_date.year == current_year
        )
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average incident response time in hours."""
        response_times = []
        
        for incident in self.incident_register.values():
            if incident.resolved_date:
                response_time = (incident.resolved_date - incident.detected_date).total_seconds() / 3600
                response_times.append(response_time)
        
        return sum(response_times) / len(response_times) if response_times else 0.0
    
    def _generate_risk_summary(self) -> Dict[str, Any]:
        """Generate risk register summary."""
        if not self.risk_register:
            return {
                'total_risks': 0,
                'critical_count': 0,
                'high_count': 0,
                'overall_level': RiskLevel.LOW
            }
        
        risk_counts = {level.value: 0 for level in RiskLevel}
        
        for risk in self.risk_register.values():
            risk_counts[risk.risk_level.value] += 1
        
        return {
            'total_risks': len(self.risk_register),
            'critical_count': risk_counts['critical'],
            'high_count': risk_counts['high'],
            'medium_count': risk_counts['medium'],
            'low_count': risk_counts['low'],
            'overall_level': self._calculate_residual_risk_level()
        }
    
    def _generate_findings_summary(self) -> Dict[str, int]:
        """Generate audit findings summary."""
        if not self.audit_findings:
            return {'total': 0, 'critical': 0, 'high': 0, 'open': 0}
        
        findings_by_severity = {level.value: 0 for level in RiskLevel}
        open_findings = 0
        
        for finding in self.audit_findings.values():
            findings_by_severity[finding.severity.value] += 1
            if finding.status == 'open':
                open_findings += 1
        
        return {
            'total': len(self.audit_findings),
            'critical': findings_by_severity['critical'],
            'high': findings_by_severity['high'],
            'medium': findings_by_severity['medium'],
            'open': open_findings
        }
    
    def _assess_current_maturity(self) -> Dict[str, Any]:
        """Assess current security maturity."""
        # Domain-specific maturity assessment
        domain_scores = {}
        for domain in ControlDomain:
            domain_controls = [c for c in self.controls_database.values() if c.domain == domain]
            if domain_controls:
                avg_maturity = sum(c.maturity_level for c in domain_controls) / len(domain_controls)
                domain_scores[domain.value] = avg_maturity
        
        overall_score = sum(domain_scores.values()) / len(domain_scores) if domain_scores else 1.0
        
        return {
            'overall_score': overall_score,
            'domain_scores': domain_scores
        }
    
    # Additional helper methods for incident and risk management...
    
    def _generate_risk_treatment_recommendations(self, risk: SecurityRisk) -> List[str]:
        """Generate risk treatment recommendations."""
        recommendations = []
        
        if risk.risk_level == RiskLevel.CRITICAL:
            recommendations.append("Immediate executive attention required")
            recommendations.append("Implement emergency controls")
            recommendations.append("Consider business operations suspension if necessary")
        elif risk.risk_level == RiskLevel.HIGH:
            recommendations.append("Senior management review required")
            recommendations.append("Implement risk mitigation controls within 30 days")
            recommendations.append("Monitor closely until risk is reduced")
        
        return recommendations
    
    def _identify_affected_controls(self, risk: SecurityRisk) -> List[str]:
        """Identify controls affected by risk."""
        # Simplified mapping - in practice would be more sophisticated
        affected_controls = []
        
        if risk.threat_type == ThreatType.MALWARE:
            affected_controls.extend(['A.12.2.1', 'A.12.6.1', 'A.13.1.1'])
        elif risk.threat_type == ThreatType.DATA_BREACH:
            affected_controls.extend(['A.9.1.1', 'A.9.2.1', 'A.10.1.1'])
        elif risk.threat_type == ThreatType.PHYSICAL_THEFT:
            affected_controls.extend(['A.11.1.1', 'A.11.2.1', 'A.8.1.1'])
        
        return affected_controls
    
    def _determine_incident_response_requirements(self, incident: SecurityIncident) -> Dict[str, List[str]]:
        """Determine incident response requirements."""
        immediate_actions = []
        follow_up_actions = []
        
        if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            immediate_actions.extend([
                "Activate incident response team",
                "Contain the incident",
                "Notify senior management"
            ])
            
            follow_up_actions.extend([
                "Conduct forensic analysis",
                "Review and update controls",
                "Provide lessons learned training"
            ])
        
        return {
            'immediate': immediate_actions,
            'follow_up': follow_up_actions
        }
    
    def _assess_nigerian_incident_reporting(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Assess Nigerian regulatory reporting requirements."""
        reporting_requirements = {
            'nitda_required': False,
            'cbn_required': False,
            'timeline_hours': None,
            'reporting_format': None
        }
        
        if self.nigerian_operations and incident.data_compromised:
            if incident.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
                reporting_requirements['nitda_required'] = True
                reporting_requirements['timeline_hours'] = 72
                
                if self.cbn_compliance:
                    reporting_requirements['cbn_required'] = True
        
        return reporting_requirements
    
    def _extract_lessons_learned(self, incident: SecurityIncident) -> List[str]:
        """Extract lessons learned from resolved incident."""
        lessons = []
        
        if incident.root_cause:
            lessons.append(f"Root cause identified: {incident.root_cause}")
        
        if incident.preventive_measures:
            lessons.extend([f"Preventive measure: {measure}" for measure in incident.preventive_measures])
        
        return lessons
    
    def _identify_control_improvements(self, incident: SecurityIncident) -> List[str]:
        """Identify control improvements based on incident."""
        improvements = []
        
        # Map incident types to control improvements
        if incident.category == ThreatType.MALWARE:
            improvements.append("Enhance endpoint protection controls")
            improvements.append("Improve email security filtering")
        elif incident.category == ThreatType.PHISHING:
            improvements.append("Increase security awareness training frequency")
            improvements.append("Implement advanced email authentication")
        
        return improvements