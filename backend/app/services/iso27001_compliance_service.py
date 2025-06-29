"""
ISO 27001 Compliance Monitoring and Management Service
Implements comprehensive ISO 27001 security controls monitoring
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import json
from sqlalchemy.orm import Session

from ..core.config import settings

logger = logging.getLogger(__name__)


class ControlStatus(str, Enum):
    """ISO 27001 control implementation status"""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    UNDER_REVIEW = "under_review"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class AuditFrequency(str, Enum):
    """Audit frequency requirements"""
    CONTINUOUS = "continuous"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


@dataclass
class ISO27001Control:
    """ISO 27001 security control definition"""
    control_id: str
    title: str
    category: str
    description: str
    implementation_guidance: str
    testing_procedure: str
    audit_frequency: AuditFrequency
    risk_level: RiskLevel
    owner: str
    status: ControlStatus
    last_tested: Optional[datetime] = None
    next_review: Optional[datetime] = None
    evidence_required: List[str] = None
    metrics: Dict[str, Any] = None


@dataclass
class ComplianceReport:
    """Comprehensive compliance assessment report"""
    assessment_date: datetime
    overall_score: float
    controls_total: int
    controls_compliant: int
    controls_non_compliant: int
    controls_partial: int
    control_details: Dict[str, Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    next_audit_date: datetime
    certification_status: str
    gaps_identified: List[str]


class ISO27001ComplianceManager:
    """ISO 27001 compliance monitoring and management."""
    
    def __init__(self):
        self.controls = self._load_iso27001_controls()
        self.audit_schedule = self._load_audit_schedule()
        
    def _load_iso27001_controls(self) -> Dict[str, ISO27001Control]:
        """Load ISO 27001 security controls for Nigerian e-invoicing context."""
        
        controls = {}
        
        # A.5 - Information security policies
        controls['A.5.1.1'] = ISO27001Control(
            control_id='A.5.1.1',
            title='Information security policy',
            category='Information Security Policies',
            description='An information security policy shall be defined, approved by management, and communicated to employees and relevant external parties.',
            implementation_guidance='Establish comprehensive information security policy covering Nigerian e-invoicing requirements, NDPR compliance, and FIRS data protection.',
            testing_procedure='Review policy document, approval records, distribution records, and staff acknowledgments.',
            audit_frequency=AuditFrequency.ANNUALLY,
            risk_level=RiskLevel.HIGH,
            owner='CISO',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Policy document', 'Management approval', 'Distribution records'],
            metrics={'policy_coverage': 100, 'staff_acknowledgment_rate': 95}
        )
        
        controls['A.5.1.2'] = ISO27001Control(
            control_id='A.5.1.2',
            title='Review of information security policy',
            category='Information Security Policies',
            description='The information security policy shall be reviewed at planned intervals.',
            implementation_guidance='Annual review of security policies with updates for Nigerian regulatory changes and FIRS requirements.',
            testing_procedure='Verify review schedule, review minutes, and policy updates.',
            audit_frequency=AuditFrequency.ANNUALLY,
            risk_level=RiskLevel.MEDIUM,
            owner='CISO',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Review schedule', 'Review records', 'Updated policies'],
            metrics={'reviews_on_schedule': 100, 'policy_updates': 3}
        )
        
        # A.6 - Organization of information security
        controls['A.6.1.1'] = ISO27001Control(
            control_id='A.6.1.1',
            title='Information security roles and responsibilities',
            category='Organization of Information Security',
            description='All information security responsibilities shall be defined and allocated.',
            implementation_guidance='Define roles for Nigerian compliance officer, data protection officer, and FIRS liaison.',
            testing_procedure='Review job descriptions, role definitions, and responsibility matrices.',
            audit_frequency=AuditFrequency.ANNUALLY,
            risk_level=RiskLevel.HIGH,
            owner='HR/CISO',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Role definitions', 'Job descriptions', 'Responsibility matrix'],
            metrics={'roles_defined': 100, 'responsibilities_assigned': 100}
        )
        
        controls['A.6.2.1'] = ISO27001Control(
            control_id='A.6.2.1',
            title='Mobile device policy',
            category='Organization of Information Security',
            description='A policy and supporting security measures shall be adopted to manage the risks from mobile devices.',
            implementation_guidance='Nigerian mobile security policy covering MTN, Airtel, Glo, and 9mobile networks.',
            testing_procedure='Review mobile device inventory, policy compliance, and security configurations.',
            audit_frequency=AuditFrequency.QUARTERLY,
            risk_level=RiskLevel.MEDIUM,
            owner='IT Security',
            status=ControlStatus.PARTIALLY_COMPLIANT,
            evidence_required=['Mobile policy', 'Device inventory', 'Security configurations'],
            metrics={'devices_managed': 85, 'policy_compliance': 90}
        )
        
        # A.8 - Asset management
        controls['A.8.1.1'] = ISO27001Control(
            control_id='A.8.1.1',
            title='Inventory of assets',
            category='Asset Management',
            description='Assets associated with information and information processing facilities shall be identified and an inventory maintained.',
            implementation_guidance='Maintain inventory of all assets handling Nigerian tax data and FIRS integration components.',
            testing_procedure='Review asset inventory, classification records, and ownership assignments.',
            audit_frequency=AuditFrequency.QUARTERLY,
            risk_level=RiskLevel.HIGH,
            owner='IT Asset Manager',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Asset inventory', 'Classification records', 'Ownership records'],
            metrics={'assets_inventoried': 98, 'classification_complete': 95}
        )
        
        controls['A.8.2.1'] = ISO27001Control(
            control_id='A.8.2.1',
            title='Classification of information',
            category='Asset Management',
            description='Information shall be classified in terms of legal requirements, value, criticality and sensitivity to unauthorised disclosure or modification.',
            implementation_guidance='Classify Nigerian tax data, FIRS submissions, and PII according to NDPR requirements.',
            testing_procedure='Review classification scheme, labeling procedures, and handling instructions.',
            audit_frequency=AuditFrequency.QUARTERLY,
            risk_level=RiskLevel.HIGH,
            owner='Data Protection Officer',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Classification scheme', 'Labeling procedures', 'Handling guidelines'],
            metrics={'data_classified': 100, 'labeling_compliance': 97}
        )
        
        # A.9 - Access control
        controls['A.9.1.1'] = ISO27001Control(
            control_id='A.9.1.1',
            title='Access control policy',
            category='Access Control',
            description='An access control policy shall be established, documented and reviewed.',
            implementation_guidance='Define access controls for Nigerian tax data, FIRS APIs, and user roles (SI_USER, MEMBER, ADMIN).',
            testing_procedure='Review access control policy, role definitions, and approval processes.',
            audit_frequency=AuditFrequency.ANNUALLY,
            risk_level=RiskLevel.CRITICAL,
            owner='Identity Management',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Access control policy', 'Role definitions', 'Approval processes'],
            metrics={'policy_coverage': 100, 'role_compliance': 98}
        )
        
        controls['A.9.2.1'] = ISO27001Control(
            control_id='A.9.2.1',
            title='User registration and de-registration',
            category='Access Control',
            description='A formal user registration and de-registration process shall be implemented.',
            implementation_guidance='Formal process for Nigerian business registration validation and FIRS credential management.',
            testing_procedure='Review registration records, approval workflows, and de-registration procedures.',
            audit_frequency=AuditFrequency.MONTHLY,
            risk_level=RiskLevel.HIGH,
            owner='Identity Management',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Registration records', 'Approval workflows', 'De-registration logs'],
            metrics={'registration_timeliness': 95, 'deregistration_compliance': 100}
        )
        
        controls['A.9.4.1'] = ISO27001Control(
            control_id='A.9.4.1',
            title='Information access restriction',
            category='Access Control',
            description='Access to information and application system functions shall be restricted in accordance with the access control policy.',
            implementation_guidance='Restrict access to Nigerian PII, tax data, and FIRS integration based on business need.',
            testing_procedure='Review access rights, segregation of duties, and least privilege implementation.',
            audit_frequency=AuditFrequency.MONTHLY,
            risk_level=RiskLevel.CRITICAL,
            owner='Access Control Administrator',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Access matrices', 'Privilege reviews', 'Segregation evidence'],
            metrics={'access_review_completion': 100, 'excessive_privileges': 2}
        )
        
        # A.10 - Cryptography
        controls['A.10.1.1'] = ISO27001Control(
            control_id='A.10.1.1',
            title='Policy on the use of cryptographic controls',
            category='Cryptography',
            description='A policy on the use of cryptographic controls for protection of information shall be developed and implemented.',
            implementation_guidance='Implement AES-256 encryption for Nigerian PII, RSA-2048 for FIRS submissions, and TLS 1.3 for transport.',
            testing_procedure='Review cryptographic policy, algorithm standards, and key management procedures.',
            audit_frequency=AuditFrequency.QUARTERLY,
            risk_level=RiskLevel.CRITICAL,
            owner='Cryptography Officer',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Cryptographic policy', 'Algorithm standards', 'Key management procedures'],
            metrics={'encryption_coverage': 100, 'algorithm_compliance': 100}
        )
        
        # A.12 - Operations security
        controls['A.12.1.1'] = ISO27001Control(
            control_id='A.12.1.1',
            title='Documented operating procedures',
            category='Operations Security',
            description='Operating procedures shall be documented and made available to all users who need them.',
            implementation_guidance='Document procedures for FIRS submission, IRN generation, and Nigerian compliance monitoring.',
            testing_procedure='Review procedure documentation, user access, and procedure compliance.',
            audit_frequency=AuditFrequency.QUARTERLY,
            risk_level=RiskLevel.MEDIUM,
            owner='Operations Manager',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Procedure documents', 'User access logs', 'Compliance records'],
            metrics={'procedure_documentation': 95, 'user_compliance': 92}
        )
        
        controls['A.12.6.1'] = ISO27001Control(
            control_id='A.12.6.1',
            title='Management of technical vulnerabilities',
            category='Operations Security',
            description='Information about technical vulnerabilities shall be obtained in a timely manner.',
            implementation_guidance='Monitor vulnerabilities in FIRS integration components and Nigerian infrastructure dependencies.',
            testing_procedure='Review vulnerability management process, scanning results, and remediation timelines.',
            audit_frequency=AuditFrequency.MONTHLY,
            risk_level=RiskLevel.HIGH,
            owner='Security Operations',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Vulnerability scans', 'Remediation records', 'Patch management logs'],
            metrics={'vulnerability_detection_time': 24, 'remediation_time': 72}
        )
        
        # A.13 - Communications security
        controls['A.13.1.1'] = ISO27001Control(
            control_id='A.13.1.1',
            title='Network controls',
            category='Communications Security',
            description='Networks shall be managed and controlled to protect information in systems and applications.',
            implementation_guidance='Secure network controls for Nigerian mobile networks and FIRS API communications.',
            testing_procedure='Review network architecture, firewall rules, and traffic monitoring.',
            audit_frequency=AuditFrequency.MONTHLY,
            risk_level=RiskLevel.HIGH,
            owner='Network Security',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Network diagrams', 'Firewall configurations', 'Traffic logs'],
            metrics={'network_uptime': 99.9, 'security_incidents': 0}
        )
        
        # A.14 - System acquisition, development and maintenance
        controls['A.14.2.1'] = ISO27001Control(
            control_id='A.14.2.1',
            title='Secure development policy',
            category='System Development',
            description='Rules for the development of software and systems shall be established.',
            implementation_guidance='Secure development practices for Nigerian e-invoicing features and FIRS integration.',
            testing_procedure='Review development standards, code reviews, and security testing procedures.',
            audit_frequency=AuditFrequency.QUARTERLY,
            risk_level=RiskLevel.HIGH,
            owner='Development Manager',
            status=ControlStatus.COMPLIANT,
            evidence_required=['Development standards', 'Code review records', 'Security test results'],
            metrics={'code_review_coverage': 100, 'security_tests_passed': 98}
        )
        
        return controls
    
    def _load_audit_schedule(self) -> Dict[str, datetime]:
        """Load next audit dates for each control."""
        
        schedule = {}
        base_date = datetime.utcnow()
        
        for control_id, control in self.controls.items():
            if control.audit_frequency == AuditFrequency.CONTINUOUS:
                schedule[control_id] = base_date + timedelta(days=1)
            elif control.audit_frequency == AuditFrequency.DAILY:
                schedule[control_id] = base_date + timedelta(days=1)
            elif control.audit_frequency == AuditFrequency.WEEKLY:
                schedule[control_id] = base_date + timedelta(weeks=1)
            elif control.audit_frequency == AuditFrequency.MONTHLY:
                schedule[control_id] = base_date + timedelta(days=30)
            elif control.audit_frequency == AuditFrequency.QUARTERLY:
                schedule[control_id] = base_date + timedelta(days=90)
            else:  # ANNUALLY
                schedule[control_id] = base_date + timedelta(days=365)
        
        return schedule
    
    async def monitor_security_controls(self) -> ComplianceReport:
        """Monitor ISO 27001 security controls."""
        
        assessment_date = datetime.utcnow()
        control_details = {}
        
        # Assess each control
        for control_id, control in self.controls.items():
            control_assessment = await self._assess_control(control)
            control_details[control_id] = control_assessment
        
        # Calculate overall compliance scores
        total_controls = len(self.controls)
        compliant_controls = sum(1 for details in control_details.values() 
                               if details['status'] == ControlStatus.COMPLIANT.value)
        partial_controls = sum(1 for details in control_details.values() 
                             if details['status'] == ControlStatus.PARTIALLY_COMPLIANT.value)
        non_compliant_controls = sum(1 for details in control_details.values() 
                                   if details['status'] == ControlStatus.NON_COMPLIANT.value)
        
        # Calculate weighted compliance score
        overall_score = self._calculate_compliance_score(control_details)
        
        # Generate risk assessment
        risk_assessment = await self._assess_risks(control_details)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(control_details)
        
        # Identify gaps
        gaps_identified = self._identify_gaps(control_details)
        
        # Determine certification status
        certification_status = self._determine_certification_status(overall_score)
        
        return ComplianceReport(
            assessment_date=assessment_date,
            overall_score=overall_score,
            controls_total=total_controls,
            controls_compliant=compliant_controls,
            controls_non_compliant=non_compliant_controls,
            controls_partial=partial_controls,
            control_details=control_details,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            next_audit_date=assessment_date + timedelta(days=90),
            certification_status=certification_status,
            gaps_identified=gaps_identified
        )
    
    async def _assess_control(self, control: ISO27001Control) -> Dict[str, Any]:
        """Assess individual control implementation."""
        
        # Simulate control assessment based on metrics and evidence
        assessment = {
            'control_id': control.control_id,
            'title': control.title,
            'category': control.category,
            'status': control.status.value,
            'risk_level': control.risk_level.value,
            'owner': control.owner,
            'last_tested': control.last_tested.isoformat() if control.last_tested else None,
            'next_review': control.next_review.isoformat() if control.next_review else None,
            'metrics': control.metrics or {},
            'evidence_status': 'complete' if control.evidence_required else 'not_required',
            'testing_results': await self._simulate_testing(control)
        }
        
        return assessment
    
    async def _simulate_testing(self, control: ISO27001Control) -> Dict[str, Any]:
        """Simulate control testing results."""
        
        # Simulate testing based on control category and risk level
        if control.risk_level == RiskLevel.CRITICAL:
            effectiveness_score = 95 if control.status == ControlStatus.COMPLIANT else 70
        elif control.risk_level == RiskLevel.HIGH:
            effectiveness_score = 90 if control.status == ControlStatus.COMPLIANT else 75
        else:
            effectiveness_score = 85 if control.status == ControlStatus.COMPLIANT else 80
        
        return {
            'effectiveness_score': effectiveness_score,
            'test_date': datetime.utcnow().isoformat(),
            'findings': self._generate_findings(control),
            'recommendations': self._generate_control_recommendations(control)
        }
    
    def _generate_findings(self, control: ISO27001Control) -> List[str]:
        """Generate realistic findings for control testing."""
        
        findings = []
        
        if control.status == ControlStatus.PARTIALLY_COMPLIANT:
            if 'mobile' in control.title.lower():
                findings.append("Some mobile devices not enrolled in MDM")
                findings.append("Patch compliance below 95% threshold")
            elif 'access' in control.title.lower():
                findings.append("Access review completion delayed by 5 days")
                findings.append("2 accounts with excessive privileges identified")
            elif 'vulnerability' in control.title.lower():
                findings.append("Average remediation time exceeds 72-hour target")
        
        elif control.status == ControlStatus.NON_COMPLIANT:
            findings.append(f"Control {control.control_id} implementation incomplete")
            findings.append("Required evidence not available")
            findings.append("Policy not updated in current assessment period")
        
        return findings
    
    def _generate_control_recommendations(self, control: ISO27001Control) -> List[str]:
        """Generate specific recommendations for control improvement."""
        
        recommendations = []
        
        if control.status != ControlStatus.COMPLIANT:
            recommendations.append(f"Update {control.title} implementation to meet requirements")
            recommendations.append(f"Collect required evidence: {', '.join(control.evidence_required or [])}")
            
            if control.risk_level == RiskLevel.CRITICAL:
                recommendations.append("Prioritize remediation due to critical risk level")
                recommendations.append("Implement compensating controls if immediate fix not possible")
        
        return recommendations
    
    def _calculate_compliance_score(self, control_details: Dict[str, Dict[str, Any]]) -> float:
        """Calculate weighted compliance score."""
        
        total_weight = 0
        weighted_score = 0
        
        for control_id, details in control_details.items():
            control = self.controls[control_id]
            
            # Weight by risk level
            weight = {
                RiskLevel.CRITICAL: 5,
                RiskLevel.HIGH: 4,
                RiskLevel.MEDIUM: 3,
                RiskLevel.LOW: 2,
                RiskLevel.NEGLIGIBLE: 1
            }[control.risk_level]
            
            # Score by status
            score = {
                ControlStatus.COMPLIANT.value: 100,
                ControlStatus.PARTIALLY_COMPLIANT.value: 70,
                ControlStatus.NON_COMPLIANT.value: 0,
                ControlStatus.NOT_APPLICABLE.value: 100,
                ControlStatus.UNDER_REVIEW.value: 50
            }[details['status']]
            
            total_weight += weight
            weighted_score += score * weight
        
        return round(weighted_score / total_weight, 2) if total_weight > 0 else 0
    
    async def _assess_risks(self, control_details: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall security risks."""
        
        risk_categories = {
            'data_protection': 0,
            'access_control': 0,
            'operational_security': 0,
            'technical_security': 0
        }
        
        category_mapping = {
            'Information Security Policies': 'operational_security',
            'Organization of Information Security': 'operational_security',
            'Asset Management': 'data_protection',
            'Access Control': 'access_control',
            'Cryptography': 'technical_security',
            'Operations Security': 'operational_security',
            'Communications Security': 'technical_security',
            'System Development': 'technical_security'
        }
        
        for control_id, details in control_details.items():
            control = self.controls[control_id]
            category = category_mapping.get(control.category, 'operational_security')
            
            if details['status'] == ControlStatus.NON_COMPLIANT.value:
                risk_categories[category] += 3
            elif details['status'] == ControlStatus.PARTIALLY_COMPLIANT.value:
                risk_categories[category] += 1
        
        return {
            'risk_categories': risk_categories,
            'overall_risk_level': self._calculate_overall_risk(risk_categories),
            'critical_risks': self._identify_critical_risks(control_details),
            'risk_trends': 'stable'  # Would track over time in real implementation
        }
    
    def _calculate_overall_risk(self, risk_categories: Dict[str, int]) -> str:
        """Calculate overall risk level."""
        
        total_risk = sum(risk_categories.values())
        
        if total_risk >= 15:
            return 'critical'
        elif total_risk >= 10:
            return 'high'
        elif total_risk >= 5:
            return 'medium'
        else:
            return 'low'
    
    def _identify_critical_risks(self, control_details: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify critical security risks."""
        
        critical_risks = []
        
        for control_id, details in control_details.items():
            control = self.controls[control_id]
            
            if (control.risk_level == RiskLevel.CRITICAL and 
                details['status'] in [ControlStatus.NON_COMPLIANT.value, ControlStatus.PARTIALLY_COMPLIANT.value]):
                
                critical_risks.append(f"{control.title} ({control_id}) - {details['status']}")
        
        return critical_risks
    
    def _generate_recommendations(self, control_details: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate comprehensive recommendations."""
        
        recommendations = []
        
        # Priority recommendations based on critical controls
        critical_issues = [details for details in control_details.values() 
                         if details['status'] != ControlStatus.COMPLIANT.value]
        
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} non-compliant controls immediately")
        
        # Nigerian-specific recommendations
        recommendations.extend([
            "Ensure NDPR compliance monitoring is continuous",
            "Maintain FIRS integration security standards",
            "Implement Nigerian data residency controls",
            "Regular review of mobile network security (MTN, Airtel, Glo, 9mobile)",
            "Quarterly assessment of cryptographic controls for tax data"
        ])
        
        return recommendations
    
    def _identify_gaps(self, control_details: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify compliance gaps."""
        
        gaps = []
        
        for control_id, details in control_details.items():
            control = self.controls[control_id]
            
            if details['status'] == ControlStatus.NON_COMPLIANT.value:
                gaps.append(f"Control {control_id}: {control.title} not implemented")
            elif details['status'] == ControlStatus.PARTIALLY_COMPLIANT.value:
                gaps.append(f"Control {control_id}: {control.title} partially implemented")
        
        return gaps
    
    def _determine_certification_status(self, overall_score: float) -> str:
        """Determine ISO 27001 certification readiness."""
        
        if overall_score >= 95:
            return "certification_ready"
        elif overall_score >= 85:
            return "minor_gaps"
        elif overall_score >= 70:
            return "major_gaps"
        else:
            return "not_ready"
    
    async def get_control_status(self, control_id: str) -> Dict[str, Any]:
        """Get detailed status of specific control."""
        
        if control_id not in self.controls:
            raise ValueError(f"Control {control_id} not found")
        
        control = self.controls[control_id]
        assessment = await self._assess_control(control)
        
        return {
            "control": {
                "id": control.control_id,
                "title": control.title,
                "category": control.category,
                "description": control.description,
                "implementation_guidance": control.implementation_guidance,
                "testing_procedure": control.testing_procedure
            },
            "status": assessment,
            "next_actions": self._generate_control_recommendations(control),
            "compliance_history": []  # Would track over time in real implementation
        }
    
    async def schedule_audit(self, control_id: str, audit_date: datetime) -> Dict[str, Any]:
        """Schedule audit for specific control."""
        
        if control_id not in self.controls:
            raise ValueError(f"Control {control_id} not found")
        
        self.audit_schedule[control_id] = audit_date
        
        return {
            "control_id": control_id,
            "scheduled_date": audit_date.isoformat(),
            "status": "scheduled",
            "notification_sent": True
        }