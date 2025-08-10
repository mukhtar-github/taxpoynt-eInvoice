"""
ISO 27001 Security Controls Assessment
====================================
Comprehensive assessment engine for ISO 27001 security controls with automated
monitoring, compliance checking, and Nigerian regulatory alignment.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from .models import (
    SecurityControl, ControlAssessment, AssessmentResult,
    RiskLevel, ControlStatus, ComplianceFramework,
    SecurityMetrics, AuditEvent, VulnerabilityReport
)


class ISO27001ControlAssessor:
    """
    Comprehensive ISO 27001 security controls assessment engine
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.assessment_cache = {}
        self.control_matrix = self._initialize_control_matrix()
        
    def _initialize_control_matrix(self) -> Dict[str, Dict]:
        """Initialize ISO 27001 control assessment matrix"""
        return {
            # Annex A.5: Information Security Policies
            "A.5.1.1": {
                "title": "Information Security Policy",
                "category": "policies",
                "requirements": ["policy_document", "management_approval", "communication"],
                "assessment_criteria": ["documented", "approved", "communicated", "reviewed"]
            },
            "A.5.1.2": {
                "title": "Information Security in Project Management",
                "category": "policies",
                "requirements": ["project_security_requirements", "security_reviews"],
                "assessment_criteria": ["integrated", "reviewed", "approved"]
            },
            
            # Annex A.6: Organization of Information Security
            "A.6.1.1": {
                "title": "Information Security Roles and Responsibilities",
                "category": "organization",
                "requirements": ["defined_roles", "assigned_responsibilities", "segregation_duties"],
                "assessment_criteria": ["documented", "assigned", "segregated", "monitored"]
            },
            "A.6.2.1": {
                "title": "Mobile Device Policy",
                "category": "organization",
                "requirements": ["mobile_device_management", "security_requirements"],
                "assessment_criteria": ["managed", "secured", "monitored", "compliant"]
            },
            
            # Annex A.7: Human Resource Security
            "A.7.1.1": {
                "title": "Screening",
                "category": "human_resources",
                "requirements": ["background_verification", "screening_procedures"],
                "assessment_criteria": ["verified", "documented", "approved", "current"]
            },
            "A.7.2.1": {
                "title": "Terms and Conditions of Employment",
                "category": "human_resources", 
                "requirements": ["security_responsibilities", "confidentiality_agreements"],
                "assessment_criteria": ["defined", "signed", "understood", "enforced"]
            },
            "A.7.3.1": {
                "title": "Termination or Change of Employment",
                "category": "human_resources",
                "requirements": ["termination_procedures", "asset_return", "access_removal"],
                "assessment_criteria": ["executed", "verified", "documented", "complete"]
            },
            
            # Annex A.8: Asset Management
            "A.8.1.1": {
                "title": "Inventory of Assets",
                "category": "asset_management",
                "requirements": ["asset_inventory", "asset_owners", "classification"],
                "assessment_criteria": ["inventoried", "owned", "classified", "maintained"]
            },
            "A.8.2.1": {
                "title": "Classification of Information",
                "category": "asset_management",
                "requirements": ["classification_scheme", "labeling", "handling_procedures"],
                "assessment_criteria": ["classified", "labeled", "handled", "protected"]
            },
            
            # Annex A.9: Access Control
            "A.9.1.1": {
                "title": "Access Control Policy",
                "category": "access_control",
                "requirements": ["access_policy", "user_registration", "access_provisioning"],
                "assessment_criteria": ["documented", "implemented", "enforced", "monitored"]
            },
            "A.9.2.1": {
                "title": "User Registration and De-registration",
                "category": "access_control",
                "requirements": ["formal_process", "unique_user_ids", "access_removal"],
                "assessment_criteria": ["formal", "unique", "removed", "audited"]
            },
            "A.9.4.1": {
                "title": "Information Access Restriction",
                "category": "access_control",
                "requirements": ["need_to_know", "authorization", "access_controls"],
                "assessment_criteria": ["restricted", "authorized", "controlled", "monitored"]
            },
            
            # Annex A.10: Cryptography
            "A.10.1.1": {
                "title": "Policy on the Use of Cryptographic Controls",
                "category": "cryptography",
                "requirements": ["crypto_policy", "key_management", "algorithm_standards"],
                "assessment_criteria": ["documented", "implemented", "compliant", "maintained"]
            },
            
            # Annex A.11: Physical and Environmental Security
            "A.11.1.1": {
                "title": "Physical Security Perimeter",
                "category": "physical_security",
                "requirements": ["security_perimeter", "physical_barriers", "access_controls"],
                "assessment_criteria": ["defined", "protected", "controlled", "monitored"]
            },
            "A.11.2.1": {
                "title": "Physical Entry Controls",
                "category": "physical_security",
                "requirements": ["access_authorization", "visitor_controls", "monitoring"],
                "assessment_criteria": ["authorized", "controlled", "monitored", "logged"]
            },
            
            # Annex A.12: Operations Security
            "A.12.1.1": {
                "title": "Documented Operating Procedures",
                "category": "operations_security",
                "requirements": ["operating_procedures", "documentation", "availability"],
                "assessment_criteria": ["documented", "available", "current", "followed"]
            },
            "A.12.6.1": {
                "title": "Management of Technical Vulnerabilities",
                "category": "operations_security",
                "requirements": ["vulnerability_management", "patch_management", "monitoring"],
                "assessment_criteria": ["identified", "assessed", "remediated", "monitored"]
            },
            
            # Annex A.13: Communications Security
            "A.13.1.1": {
                "title": "Network Controls",
                "category": "communications_security",
                "requirements": ["network_controls", "segregation", "monitoring"],
                "assessment_criteria": ["controlled", "segregated", "monitored", "protected"]
            },
            "A.13.2.1": {
                "title": "Information Transfer Policies and Procedures",
                "category": "communications_security",
                "requirements": ["transfer_policies", "formal_procedures", "protection"],
                "assessment_criteria": ["documented", "implemented", "protected", "monitored"]
            },
            
            # Annex A.14: System Acquisition, Development and Maintenance
            "A.14.1.1": {
                "title": "Information Security Requirements Analysis and Specification",
                "category": "system_development",
                "requirements": ["security_requirements", "analysis", "specification"],
                "assessment_criteria": ["identified", "analyzed", "specified", "implemented"]
            },
            "A.14.2.1": {
                "title": "Secure Development Policy",
                "category": "system_development",
                "requirements": ["development_policy", "secure_coding", "testing"],
                "assessment_criteria": ["documented", "implemented", "tested", "maintained"]
            },
            
            # Annex A.15: Supplier Relationships
            "A.15.1.1": {
                "title": "Information Security Policy for Supplier Relationships",
                "category": "supplier_relationships",
                "requirements": ["supplier_policy", "agreements", "monitoring"],
                "assessment_criteria": ["documented", "agreed", "monitored", "enforced"]
            },
            
            # Annex A.16: Information Security Incident Management
            "A.16.1.1": {
                "title": "Responsibilities and Procedures",
                "category": "incident_management",
                "requirements": ["incident_procedures", "response_team", "escalation"],
                "assessment_criteria": ["documented", "assigned", "tested", "effective"]
            },
            "A.16.1.2": {
                "title": "Reporting Information Security Events",
                "category": "incident_management",
                "requirements": ["reporting_procedures", "channels", "timeframes"],
                "assessment_criteria": ["reported", "channeled", "timely", "documented"]
            },
            
            # Annex A.17: Information Security Aspects of Business Continuity Management
            "A.17.1.1": {
                "title": "Planning Information Security Continuity",
                "category": "business_continuity",
                "requirements": ["continuity_planning", "security_requirements", "testing"],
                "assessment_criteria": ["planned", "implemented", "tested", "maintained"]
            },
            
            # Annex A.18: Compliance
            "A.18.1.1": {
                "title": "Identification of Applicable Legislation and Contractual Requirements",
                "category": "compliance",
                "requirements": ["legal_requirements", "contractual_obligations", "compliance_procedures"],
                "assessment_criteria": ["identified", "documented", "compliant", "monitored"]
            }
        }
    
    def assess_control(self, control_id: str, evidence: Dict[str, Any]) -> ControlAssessment:
        """
        Assess individual ISO 27001 security control
        
        Args:
            control_id: ISO 27001 control identifier (e.g., 'A.9.1.1')
            evidence: Evidence for control assessment
            
        Returns:
            ControlAssessment with detailed results
        """
        try:
            if control_id not in self.control_matrix:
                raise ValueError(f"Unknown control ID: {control_id}")
            
            control_spec = self.control_matrix[control_id]
            assessment_results = []
            
            # Assess each criteria
            for criteria in control_spec["assessment_criteria"]:
                result = self._assess_criteria(criteria, evidence, control_spec)
                assessment_results.append(result)
            
            # Calculate overall control status
            status = self._calculate_control_status(assessment_results)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(control_id, assessment_results)
            
            return ControlAssessment(
                control_id=control_id,
                control_title=control_spec["title"],
                assessment_date=datetime.now(),
                assessor="ISO27001ControlAssessor",
                status=status,
                results=assessment_results,
                recommendations=recommendations,
                next_review_date=datetime.now() + timedelta(days=90),
                evidence_provided=evidence,
                compliance_score=self._calculate_compliance_score(assessment_results)
            )
            
        except Exception as e:
            self.logger.error(f"Control assessment failed for {control_id}: {str(e)}")
            raise
    
    def _assess_criteria(self, criteria: str, evidence: Dict[str, Any], 
                        control_spec: Dict) -> AssessmentResult:
        """Assess individual assessment criteria"""
        
        # Check if evidence supports the criteria
        evidence_score = self._evaluate_evidence(criteria, evidence)
        
        # Determine compliance level
        if evidence_score >= 0.8:
            compliance_level = "Fully Compliant"
            risk_level = RiskLevel.LOW
        elif evidence_score >= 0.6:
            compliance_level = "Largely Compliant"
            risk_level = RiskLevel.MEDIUM
        elif evidence_score >= 0.4:
            compliance_level = "Partially Compliant"
            risk_level = RiskLevel.HIGH
        else:
            compliance_level = "Non-Compliant"
            risk_level = RiskLevel.CRITICAL
        
        return AssessmentResult(
            criteria=criteria,
            status=compliance_level,
            score=evidence_score,
            risk_level=risk_level,
            findings=self._generate_findings(criteria, evidence, evidence_score),
            evidence_quality=self._assess_evidence_quality(evidence),
            remediation_required=evidence_score < 0.8
        )
    
    def _evaluate_evidence(self, criteria: str, evidence: Dict[str, Any]) -> float:
        """Evaluate evidence quality and completeness for criteria"""
        
        evidence_weights = {
            "documented": 0.9 if evidence.get("documentation") else 0.1,
            "implemented": 0.9 if evidence.get("implementation") else 0.1,
            "approved": 0.9 if evidence.get("approvals") else 0.1,
            "communicated": 0.8 if evidence.get("communication") else 0.2,
            "reviewed": 0.8 if evidence.get("reviews") else 0.2,
            "monitored": 0.8 if evidence.get("monitoring") else 0.2,
            "tested": 0.8 if evidence.get("testing") else 0.2,
            "enforced": 0.9 if evidence.get("enforcement") else 0.1,
            "maintained": 0.7 if evidence.get("maintenance") else 0.3,
            "current": 0.8 if evidence.get("currency_check") else 0.2
        }
        
        return evidence_weights.get(criteria, 0.5)
    
    def _calculate_control_status(self, results: List[AssessmentResult]) -> ControlStatus:
        """Calculate overall control status from assessment results"""
        
        if not results:
            return ControlStatus.NOT_ASSESSED
        
        avg_score = sum(r.score for r in results) / len(results)
        
        if avg_score >= 0.8:
            return ControlStatus.EFFECTIVE
        elif avg_score >= 0.6:
            return ControlStatus.PARTIALLY_EFFECTIVE
        else:
            return ControlStatus.INEFFECTIVE
    
    def _calculate_compliance_score(self, results: List[AssessmentResult]) -> float:
        """Calculate overall compliance score"""
        if not results:
            return 0.0
        return sum(r.score for r in results) / len(results)
    
    def _generate_recommendations(self, control_id: str, 
                                results: List[AssessmentResult]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        for result in results:
            if result.remediation_required:
                recommendations.append(
                    f"Improve {result.criteria} for control {control_id}: "
                    f"Current score {result.score:.2f}, target ≥0.8"
                )
        
        return recommendations
    
    def _generate_findings(self, criteria: str, evidence: Dict[str, Any], 
                         score: float) -> List[str]:
        """Generate assessment findings"""
        findings = []
        
        if score < 0.8:
            findings.append(f"Insufficient evidence for {criteria}")
            
        if score < 0.4:
            findings.append(f"Critical gap identified in {criteria}")
            
        return findings
    
    def _assess_evidence_quality(self, evidence: Dict[str, Any]) -> str:
        """Assess quality of provided evidence"""
        if not evidence:
            return "No Evidence"
        
        quality_indicators = sum([
            1 for key in ["documentation", "implementation", "approvals", 
                         "testing", "monitoring"] 
            if evidence.get(key)
        ])
        
        if quality_indicators >= 4:
            return "High Quality"
        elif quality_indicators >= 2:
            return "Medium Quality"
        else:
            return "Low Quality"
    
    def assess_all_controls(self, evidence_package: Dict[str, Dict[str, Any]]) -> Dict[str, ControlAssessment]:
        """
        Assess all ISO 27001 controls
        
        Args:
            evidence_package: Dictionary mapping control IDs to evidence
            
        Returns:
            Dictionary of control assessments
        """
        assessments = {}
        
        for control_id in self.control_matrix.keys():
            evidence = evidence_package.get(control_id, {})
            try:
                assessments[control_id] = self.assess_control(control_id, evidence)
            except Exception as e:
                self.logger.error(f"Failed to assess control {control_id}: {str(e)}")
                
        return assessments
    
    def generate_compliance_report(self, assessments: Dict[str, ControlAssessment]) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        total_controls = len(assessments)
        effective_controls = sum(1 for a in assessments.values() 
                               if a.status == ControlStatus.EFFECTIVE)
        
        compliance_percentage = (effective_controls / total_controls * 100) if total_controls > 0 else 0
        
        # Category analysis
        category_analysis = {}
        for control_id, assessment in assessments.items():
            category = self.control_matrix[control_id]["category"]
            if category not in category_analysis:
                category_analysis[category] = {"total": 0, "effective": 0}
            
            category_analysis[category]["total"] += 1
            if assessment.status == ControlStatus.EFFECTIVE:
                category_analysis[category]["effective"] += 1
        
        # Risk analysis
        risk_summary = {
            "critical": sum(1 for a in assessments.values() 
                          if any(r.risk_level == RiskLevel.CRITICAL for r in a.results)),
            "high": sum(1 for a in assessments.values() 
                       if any(r.risk_level == RiskLevel.HIGH for r in a.results)),
            "medium": sum(1 for a in assessments.values() 
                         if any(r.risk_level == RiskLevel.MEDIUM for r in a.results)),
            "low": sum(1 for a in assessments.values() 
                      if all(r.risk_level == RiskLevel.LOW for r in a.results))
        }
        
        return {
            "assessment_date": datetime.now().isoformat(),
            "total_controls_assessed": total_controls,
            "effective_controls": effective_controls,
            "compliance_percentage": compliance_percentage,
            "category_analysis": category_analysis,
            "risk_summary": risk_summary,
            "recommendations": self._generate_overall_recommendations(assessments),
            "next_assessment_date": (datetime.now() + timedelta(days=365)).isoformat()
        }
    
    def _generate_overall_recommendations(self, assessments: Dict[str, ControlAssessment]) -> List[str]:
        """Generate overall improvement recommendations"""
        recommendations = []
        
        # Priority recommendations for critical/high risk controls
        critical_controls = [
            control_id for control_id, assessment in assessments.items()
            if any(r.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH] for r in assessment.results)
        ]
        
        if critical_controls:
            recommendations.append(
                f"Priority attention required for {len(critical_controls)} high-risk controls: "
                f"{', '.join(critical_controls[:5])}"
            )
        
        # Category-specific recommendations
        category_scores = {}
        for control_id, assessment in assessments.items():
            category = self.control_matrix[control_id]["category"]
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(assessment.compliance_score)
        
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.7:
                recommendations.append(
                    f"Strengthen {category.replace('_', ' ')} controls - "
                    f"current average score: {avg_score:.2f}"
                )
        
        return recommendations