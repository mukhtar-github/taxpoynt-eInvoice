"""
ISO 27001 Certification Readiness Assessment
===========================================
Certification readiness tools for PEPPOL Access Point Provider requirements.
Supports preparation for Stage 1 and Stage 2 audits with accredited certification bodies.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from .models import (
    SecurityControl, ControlAssessment, CertificationReadiness,
    AuditEvidence, ComplianceGap, CertificationPhase
)


class ISO27001CertificationReadiness:
    """
    ISO 27001 certification readiness assessment for PEPPOL compliance
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.certification_requirements = self._initialize_certification_requirements()
        self.audit_evidence_templates = self._initialize_evidence_templates()
        self.peppol_specific_requirements = self._initialize_peppol_requirements()
        
    def _initialize_certification_requirements(self) -> Dict[str, Dict]:
        """Initialize ISO 27001 certification requirements matrix"""
        return {
            # Stage 1 Audit Requirements (Documentation Review)
            "stage1_requirements": {
                "ISMS_scope": {
                    "requirement": "Defined scope of Information Security Management System",
                    "evidence_needed": ["scope_document", "boundary_definition", "exclusions_rationale"],
                    "audit_focus": "Clarity and appropriateness of scope definition",
                    "peppol_relevance": "Must include PEPPOL Access Point operations"
                },
                "information_security_policy": {
                    "requirement": "Top management approved information security policy",
                    "evidence_needed": ["policy_document", "management_approval", "communication_records"],
                    "audit_focus": "Policy alignment with business objectives",
                    "peppol_relevance": "Must address PEPPOL network security requirements"
                },
                "risk_assessment_methodology": {
                    "requirement": "Documented risk assessment methodology",
                    "evidence_needed": ["methodology_document", "risk_criteria", "assessment_procedures"],
                    "audit_focus": "Systematic and repeatable approach",
                    "peppol_relevance": "Must include risks from PEPPOL network participation"
                },
                "risk_treatment_plan": {
                    "requirement": "Risk treatment plan with controls selection",
                    "evidence_needed": ["treatment_plan", "controls_justification", "implementation_timeline"],
                    "audit_focus": "Appropriateness of control selection",
                    "peppol_relevance": "Controls must address PEPPOL-specific threats"
                },
                "statement_of_applicability": {
                    "requirement": "Statement of Applicability (SoA) for all Annex A controls",
                    "evidence_needed": ["soa_document", "inclusion_exclusion_rationale", "controls_mapping"],
                    "audit_focus": "Completeness and justification of decisions",
                    "peppol_relevance": "Must justify PEPPOL-relevant controls inclusion"
                },
                "isms_objectives": {
                    "requirement": "Information security objectives and plans",
                    "evidence_needed": ["objectives_document", "measurement_criteria", "monitoring_plans"],
                    "audit_focus": "Alignment with policy and business needs",
                    "peppol_relevance": "Must include PEPPOL compliance objectives"
                }
            },
            
            # Stage 2 Audit Requirements (Implementation Assessment)
            "stage2_requirements": {
                "implemented_controls": {
                    "requirement": "Evidence of implemented security controls",
                    "evidence_needed": ["implementation_records", "configuration_documentation", "testing_results"],
                    "audit_focus": "Effectiveness of control implementation",
                    "peppol_relevance": "AS4, PKI, MLR security controls operational"
                },
                "management_review": {
                    "requirement": "Management review of ISMS performance",
                    "evidence_needed": ["review_meeting_minutes", "performance_reports", "improvement_decisions"],
                    "audit_focus": "Leadership engagement and decision-making",
                    "peppol_relevance": "PEPPOL security performance reviewed"
                },
                "internal_audit": {
                    "requirement": "Internal audit program and results",
                    "evidence_needed": ["audit_program", "audit_reports", "corrective_actions"],
                    "audit_focus": "Systematic evaluation of ISMS",
                    "peppol_relevance": "PEPPOL operations included in audit scope"
                },
                "incident_management": {
                    "requirement": "Information security incident management",
                    "evidence_needed": ["incident_procedures", "incident_logs", "response_records"],
                    "audit_focus": "Incident detection, response, and learning",
                    "peppol_relevance": "PEPPOL network incidents properly managed"
                },
                "continuous_improvement": {
                    "requirement": "Continual improvement of ISMS",
                    "evidence_needed": ["improvement_records", "performance_trends", "corrective_actions"],
                    "audit_focus": "ISMS enhancement over time",
                    "peppol_relevance": "PEPPOL security continuously improved"
                },
                "competence_awareness": {
                    "requirement": "Staff competence and security awareness",
                    "evidence_needed": ["training_records", "competence_assessments", "awareness_programs"],
                    "audit_focus": "Personnel security capability",
                    "peppol_relevance": "PEPPOL-specific security training provided"
                }
            }
        }
    
    def _initialize_evidence_templates(self) -> Dict[str, Dict]:
        """Initialize audit evidence templates"""
        return {
            "policy_documents": {
                "information_security_policy": {
                    "template_sections": [
                        "Purpose and scope",
                        "Information security principles", 
                        "Management commitment",
                        "Legal and regulatory compliance",
                        "Incident management",
                        "Business continuity",
                        "Review and update procedures"
                    ],
                    "peppol_additions": [
                        "PEPPOL network security requirements",
                        "Cross-border data protection",
                        "Access Point security obligations"
                    ]
                },
                "risk_management_policy": {
                    "template_sections": [
                        "Risk management framework",
                        "Risk assessment methodology",
                        "Risk treatment options",
                        "Risk monitoring and review",
                        "Risk communication"
                    ],
                    "peppol_additions": [
                        "PEPPOL network risk considerations",
                        "Cross-border transaction risks",
                        "Regulatory compliance risks"
                    ]
                }
            },
            "procedural_documents": {
                "incident_response_procedure": {
                    "template_sections": [
                        "Incident classification",
                        "Response team roles",
                        "Response procedures",
                        "Communication protocols",
                        "Recovery procedures",
                        "Lessons learned process"
                    ],
                    "peppol_additions": [
                        "PEPPOL network incident reporting",
                        "Cross-border incident coordination",
                        "Regulatory notification requirements"
                    ]
                },
                "access_control_procedure": {
                    "template_sections": [
                        "User access provisioning",
                        "Privileged access management",
                        "Access review procedures",
                        "Access termination process",
                        "Remote access controls"
                    ],
                    "peppol_additions": [
                        "PEPPOL participant access controls",
                        "Cross-border access considerations",
                        "Network certificate management"
                    ]
                }
            }
        }
    
    def _initialize_peppol_requirements(self) -> Dict[str, Dict]:
        """Initialize PEPPOL-specific ISO 27001 requirements"""
        return {
            "technical_controls": {
                "A.13.1.1_network_controls": {
                    "standard_requirement": "Networks shall be managed and controlled",
                    "peppol_specifics": [
                        "AS4 messaging protocol security",
                        "PEPPOL network segregation",
                        "Message routing security",
                        "Network participant authentication"
                    ]
                },
                "A.10.1.1_cryptographic_policy": {
                    "standard_requirement": "Policy on use of cryptographic controls",
                    "peppol_specifics": [
                        "PKI certificate management for PEPPOL",
                        "Digital signature requirements",
                        "Message encryption standards",
                        "Key lifecycle management"
                    ]
                },
                "A.12.6.1_vulnerability_management": {
                    "standard_requirement": "Management of technical vulnerabilities",
                    "peppol_specifics": [
                        "PEPPOL network vulnerability monitoring",
                        "AS4/SBDH security updates",
                        "Certificate vulnerability management",
                        "Cross-border threat intelligence"
                    ]
                }
            },
            "operational_controls": {
                "A.16.1.1_incident_responsibilities": {
                    "standard_requirement": "Incident management responsibilities",
                    "peppol_specifics": [
                        "PEPPOL network incident reporting",
                        "Cross-border incident coordination",
                        "Message delivery failure handling",
                        "Security breach notification"
                    ]
                },
                "A.17.1.1_business_continuity": {
                    "standard_requirement": "Planning information security continuity",
                    "peppol_specifics": [
                        "PEPPOL service availability requirements",
                        "Cross-border service continuity",
                        "Message queuing and failover",
                        "Alternative Access Point arrangements"
                    ]
                }
            },
            "organizational_controls": {
                "A.7.2.1_employment_terms": {
                    "standard_requirement": "Terms and conditions of employment",
                    "peppol_specifics": [
                        "PEPPOL confidentiality requirements",
                        "Cross-border data handling obligations",
                        "Network participant data protection",
                        "International compliance responsibilities"
                    ]
                }
            }
        }
    
    def assess_certification_readiness(self, current_implementation: Dict[str, Any]) -> CertificationReadiness:
        """
        Assess readiness for ISO 27001 certification with PEPPOL focus
        
        Args:
            current_implementation: Current ISMS implementation status
            
        Returns:
            Comprehensive certification readiness assessment
        """
        try:
            readiness = CertificationReadiness(
                assessment_date=datetime.now(),
                overall_readiness_score=0.0,
                certification_phase=CertificationPhase.PREPARATION,
                gaps_identified=[],
                evidence_status={},
                recommendations=[],
                estimated_certification_timeline=timedelta(days=180)
            )
            
            # Assess Stage 1 readiness (Documentation)
            stage1_score = self._assess_stage1_readiness(current_implementation, readiness)
            
            # Assess Stage 2 readiness (Implementation)
            stage2_score = self._assess_stage2_readiness(current_implementation, readiness)
            
            # Calculate overall readiness
            readiness.overall_readiness_score = (stage1_score + stage2_score) / 2
            
            # Determine certification phase
            readiness.certification_phase = self._determine_certification_phase(readiness.overall_readiness_score)
            
            # Generate timeline estimate
            readiness.estimated_certification_timeline = self._estimate_certification_timeline(readiness)
            
            # Generate PEPPOL-specific recommendations
            readiness.recommendations.extend(self._generate_peppol_recommendations(readiness))
            
            return readiness
            
        except Exception as e:
            self.logger.error(f"Certification readiness assessment failed: {str(e)}")
            raise
    
    def _assess_stage1_readiness(self, implementation: Dict[str, Any], 
                                readiness: CertificationReadiness) -> float:
        """Assess Stage 1 (Documentation) readiness"""
        
        stage1_requirements = self.certification_requirements["stage1_requirements"]
        total_requirements = len(stage1_requirements)
        met_requirements = 0
        
        for req_id, requirement in stage1_requirements.items():
            evidence_available = 0
            total_evidence = len(requirement["evidence_needed"])
            
            for evidence_type in requirement["evidence_needed"]:
                if self._check_evidence_availability(evidence_type, implementation):
                    evidence_available += 1
                    
            evidence_score = evidence_available / total_evidence if total_evidence > 0 else 0
            
            if evidence_score >= 0.8:  # 80% threshold for "met"
                met_requirements += 1
            else:
                # Record gap
                gap = ComplianceGap(
                    gap_id=f"STAGE1_{req_id.upper()}",
                    requirement=requirement["requirement"],
                    current_status=f"Evidence available: {evidence_available}/{total_evidence}",
                    gap_description=f"Missing evidence for {requirement['requirement']}",
                    impact_level="high" if evidence_score < 0.5 else "medium",
                    recommended_action=f"Prepare missing evidence: {requirement['evidence_needed']}",
                    peppol_relevance=requirement.get("peppol_relevance", "")
                )
                readiness.gaps_identified.append(gap)
            
            readiness.evidence_status[req_id] = {
                "score": evidence_score,
                "available_evidence": evidence_available,
                "total_evidence": total_evidence,
                "status": "ready" if evidence_score >= 0.8 else "incomplete"
            }
        
        return (met_requirements / total_requirements) * 100 if total_requirements > 0 else 0
    
    def _assess_stage2_readiness(self, implementation: Dict[str, Any],
                                readiness: CertificationReadiness) -> float:
        """Assess Stage 2 (Implementation) readiness"""
        
        stage2_requirements = self.certification_requirements["stage2_requirements"]
        total_requirements = len(stage2_requirements)
        met_requirements = 0
        
        for req_id, requirement in stage2_requirements.items():
            implementation_score = self._assess_implementation_evidence(req_id, requirement, implementation)
            
            if implementation_score >= 0.8:  # 80% threshold for "implemented"
                met_requirements += 1
            else:
                # Record implementation gap
                gap = ComplianceGap(
                    gap_id=f"STAGE2_{req_id.upper()}",
                    requirement=requirement["requirement"],
                    current_status=f"Implementation score: {implementation_score:.2f}",
                    gap_description=f"Insufficient implementation evidence for {requirement['requirement']}",
                    impact_level="critical" if implementation_score < 0.5 else "high",
                    recommended_action=f"Strengthen implementation and evidence collection",
                    peppol_relevance=requirement.get("peppol_relevance", "")
                )
                readiness.gaps_identified.append(gap)
            
            readiness.evidence_status[f"impl_{req_id}"] = {
                "score": implementation_score,
                "status": "implemented" if implementation_score >= 0.8 else "partial"
            }
        
        return (met_requirements / total_requirements) * 100 if total_requirements > 0 else 0
    
    def _check_evidence_availability(self, evidence_type: str, implementation: Dict[str, Any]) -> bool:
        """Check if specific evidence type is available"""
        
        evidence_mapping = {
            "scope_document": implementation.get("isms_scope_defined", False),
            "policy_document": implementation.get("security_policy_exists", False),
            "management_approval": implementation.get("management_approved_policy", False),
            "risk_criteria": implementation.get("risk_assessment_criteria_defined", False),
            "controls_justification": implementation.get("controls_selection_justified", False),
            "soa_document": implementation.get("statement_of_applicability_complete", False),
            "implementation_records": implementation.get("controls_implemented", False),
            "audit_program": implementation.get("internal_audit_program_exists", False),
            "incident_procedures": implementation.get("incident_procedures_documented", False),
            "training_records": implementation.get("security_training_conducted", False)
        }
        
        return evidence_mapping.get(evidence_type, False)
    
    def _assess_implementation_evidence(self, req_id: str, requirement: Dict[str, Any],
                                      implementation: Dict[str, Any]) -> float:
        """Assess implementation evidence quality"""
        
        # Implementation assessment logic based on requirement type
        implementation_scores = {
            "implemented_controls": implementation.get("controls_implementation_score", 0.0),
            "management_review": implementation.get("management_review_score", 0.0),
            "internal_audit": implementation.get("internal_audit_score", 0.0),
            "incident_management": implementation.get("incident_management_score", 0.0),
            "continuous_improvement": implementation.get("improvement_program_score", 0.0),
            "competence_awareness": implementation.get("training_effectiveness_score", 0.0)
        }
        
        return implementation_scores.get(req_id, 0.0) / 100.0  # Convert percentage to decimal
    
    def _determine_certification_phase(self, readiness_score: float) -> CertificationPhase:
        """Determine current certification phase based on readiness score"""
        
        if readiness_score >= 90:
            return CertificationPhase.READY_FOR_CERTIFICATION
        elif readiness_score >= 70:
            return CertificationPhase.IMPLEMENTATION_REVIEW
        elif readiness_score >= 50:
            return CertificationPhase.IMPLEMENTATION
        else:
            return CertificationPhase.PREPARATION
    
    def _estimate_certification_timeline(self, readiness: CertificationReadiness) -> timedelta:
        """Estimate certification timeline based on current readiness"""
        
        base_timeline = {
            CertificationPhase.PREPARATION: timedelta(days=180),  # 6 months
            CertificationPhase.IMPLEMENTATION: timedelta(days=120),  # 4 months
            CertificationPhase.IMPLEMENTATION_REVIEW: timedelta(days=60),  # 2 months
            CertificationPhase.READY_FOR_CERTIFICATION: timedelta(days=30)  # 1 month
        }
        
        base_time = base_timeline.get(readiness.certification_phase, timedelta(days=180))
        
        # Adjust for number of gaps
        critical_gaps = sum(1 for gap in readiness.gaps_identified if gap.impact_level == "critical")
        high_gaps = sum(1 for gap in readiness.gaps_identified if gap.impact_level == "high")
        
        # Add time for gap resolution
        additional_time = timedelta(days=(critical_gaps * 14 + high_gaps * 7))
        
        return base_time + additional_time
    
    def _generate_peppol_recommendations(self, readiness: CertificationReadiness) -> List[str]:
        """Generate PEPPOL-specific certification recommendations"""
        
        recommendations = []
        
        # PEPPOL timeline urgency
        if readiness.certification_phase in [CertificationPhase.PREPARATION, CertificationPhase.IMPLEMENTATION]:
            recommendations.append(
                "URGENT: Nigeria PEPPOL pilot starts July 2025. Consider hiring ISO 27001 consultant to accelerate certification."
            )
        
        # PEPPOL-specific controls
        peppol_gaps = [gap for gap in readiness.gaps_identified if gap.peppol_relevance]
        if peppol_gaps:
            recommendations.append(
                f"Address {len(peppol_gaps)} PEPPOL-specific security requirements for Access Point certification."
            )
        
        # Certification body selection
        if readiness.overall_readiness_score >= 60:
            recommendations.append(
                "Contact accredited certification bodies in Nigeria (BSI, SGS, Bureau Veritas) to schedule preliminary assessment."
            )
        
        # Alternative approach if timeline is tight
        if readiness.estimated_certification_timeline.days > 150:  # More than 5 months
            recommendations.append(
                "Consider partnering with ISO 27001 certified company initially while pursuing independent certification."
            )
        
        return recommendations
    
    def generate_audit_evidence_package(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive audit evidence package
        
        Args:
            implementation: Current ISMS implementation
            
        Returns:
            Organized audit evidence package
        """
        try:
            evidence_package = {
                "package_date": datetime.now().isoformat(),
                "stage1_evidence": {},
                "stage2_evidence": {},
                "peppol_specific_evidence": {},
                "evidence_summary": {}
            }
            
            # Stage 1 Evidence (Documentation)
            for req_id, requirement in self.certification_requirements["stage1_requirements"].items():
                evidence_package["stage1_evidence"][req_id] = {
                    "requirement": requirement["requirement"],
                    "evidence_files": [],
                    "completion_status": "pending",
                    "peppol_additions_needed": requirement.get("peppol_relevance", "")
                }
                
                # Check for available evidence
                for evidence_type in requirement["evidence_needed"]:
                    if self._check_evidence_availability(evidence_type, implementation):
                        evidence_package["stage1_evidence"][req_id]["evidence_files"].append(evidence_type)
                
                # Update completion status
                total_evidence = len(requirement["evidence_needed"])
                available_evidence = len(evidence_package["stage1_evidence"][req_id]["evidence_files"])
                completion_ratio = available_evidence / total_evidence if total_evidence > 0 else 0
                
                if completion_ratio >= 0.8:
                    evidence_package["stage1_evidence"][req_id]["completion_status"] = "complete"
                elif completion_ratio >= 0.5:
                    evidence_package["stage1_evidence"][req_id]["completion_status"] = "partial"
                else:
                    evidence_package["stage1_evidence"][req_id]["completion_status"] = "incomplete"
            
            # Stage 2 Evidence (Implementation)
            for req_id, requirement in self.certification_requirements["stage2_requirements"].items():
                implementation_score = self._assess_implementation_evidence(req_id, requirement, implementation)
                
                evidence_package["stage2_evidence"][req_id] = {
                    "requirement": requirement["requirement"],
                    "implementation_score": implementation_score,
                    "evidence_strength": "strong" if implementation_score >= 0.8 else "weak",
                    "audit_focus": requirement["audit_focus"],
                    "peppol_considerations": requirement.get("peppol_relevance", "")
                }
            
            # PEPPOL-specific evidence
            evidence_package["peppol_specific_evidence"] = self._compile_peppol_evidence(implementation)
            
            # Evidence summary
            evidence_package["evidence_summary"] = {
                "stage1_completion": self._calculate_stage1_completion(evidence_package["stage1_evidence"]),
                "stage2_readiness": self._calculate_stage2_readiness(evidence_package["stage2_evidence"]),
                "peppol_compliance": self._calculate_peppol_compliance(evidence_package["peppol_specific_evidence"]),
                "overall_readiness": 0.0
            }
            
            # Calculate overall readiness
            summary = evidence_package["evidence_summary"]
            summary["overall_readiness"] = (
                summary["stage1_completion"] + 
                summary["stage2_readiness"] + 
                summary["peppol_compliance"]
            ) / 3
            
            return evidence_package
            
        except Exception as e:
            self.logger.error(f"Audit evidence package generation failed: {str(e)}")
            raise
    
    def _compile_peppol_evidence(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Compile PEPPOL-specific evidence"""
        
        peppol_evidence = {}
        
        for control_category, controls in self.peppol_specific_requirements.items():
            peppol_evidence[control_category] = {}
            
            for control_id, control_info in controls.items():
                evidence_score = implementation.get(f"peppol_{control_id}_score", 0.0)
                
                peppol_evidence[control_category][control_id] = {
                    "standard_requirement": control_info["standard_requirement"],
                    "peppol_specifics": control_info["peppol_specifics"],
                    "evidence_score": evidence_score,
                    "compliance_status": "compliant" if evidence_score >= 0.8 else "non_compliant"
                }
        
        return peppol_evidence
    
    def _calculate_stage1_completion(self, stage1_evidence: Dict[str, Any]) -> float:
        """Calculate Stage 1 evidence completion percentage"""
        
        total_requirements = len(stage1_evidence)
        complete_requirements = sum(1 for req in stage1_evidence.values() 
                                  if req["completion_status"] == "complete")
        
        return (complete_requirements / total_requirements) * 100 if total_requirements > 0 else 0
    
    def _calculate_stage2_readiness(self, stage2_evidence: Dict[str, Any]) -> float:
        """Calculate Stage 2 implementation readiness percentage"""
        
        total_scores = [req["implementation_score"] for req in stage2_evidence.values()]
        average_score = sum(total_scores) / len(total_scores) if total_scores else 0
        
        return average_score * 100  # Convert to percentage
    
    def _calculate_peppol_compliance(self, peppol_evidence: Dict[str, Any]) -> float:
        """Calculate PEPPOL-specific compliance percentage"""
        
        all_scores = []
        for category in peppol_evidence.values():
            for control in category.values():
                all_scores.append(control["evidence_score"])
        
        average_score = sum(all_scores) / len(all_scores) if all_scores else 0
        return average_score * 100  # Convert to percentage
    
    def create_certification_roadmap(self, readiness: CertificationReadiness) -> Dict[str, Any]:
        """
        Create detailed certification roadmap with timeline and milestones
        
        Args:
            readiness: Current certification readiness assessment
            
        Returns:
            Detailed certification roadmap
        """
        try:
            roadmap = {
                "roadmap_date": datetime.now().isoformat(),
                "current_phase": readiness.certification_phase.value,
                "target_certification_date": (datetime.now() + readiness.estimated_certification_timeline).isoformat(),
                "phases": {},
                "milestones": [],
                "critical_path": [],
                "risk_factors": []
            }
            
            # Define phase-specific activities
            phase_activities = {
                CertificationPhase.PREPARATION: [
                    "Conduct comprehensive gap analysis",
                    "Develop ISMS documentation suite",
                    "Create PEPPOL-specific security policies",
                    "Establish risk management framework",
                    "Design control implementation plan"
                ],
                CertificationPhase.IMPLEMENTATION: [
                    "Implement security controls",
                    "Deploy PEPPOL-specific controls (AS4, PKI, MLR)",
                    "Conduct staff security training",
                    "Establish monitoring and measurement",
                    "Perform internal audits"
                ],
                CertificationPhase.IMPLEMENTATION_REVIEW: [
                    "Review control effectiveness",
                    "Address internal audit findings",
                    "Conduct management review",
                    "Prepare certification application",
                    "Select certification body"
                ],
                CertificationPhase.READY_FOR_CERTIFICATION: [
                    "Submit certification application",
                    "Prepare for Stage 1 audit",
                    "Address Stage 1 findings",
                    "Prepare for Stage 2 audit",
                    "Achieve certification"
                ]
            }
            
            # Build phase roadmap
            current_date = datetime.now()
            for phase in CertificationPhase:
                if phase.value >= readiness.certification_phase.value:
                    phase_duration = self._estimate_phase_duration(phase, readiness)
                    
                    roadmap["phases"][phase.value] = {
                        "start_date": current_date.isoformat(),
                        "end_date": (current_date + phase_duration).isoformat(),
                        "duration_days": phase_duration.days,
                        "activities": phase_activities.get(phase, []),
                        "deliverables": self._get_phase_deliverables(phase),
                        "success_criteria": self._get_phase_success_criteria(phase)
                    }
                    
                    current_date += phase_duration
            
            # Define milestones
            roadmap["milestones"] = [
                {
                    "milestone": "ISMS Documentation Complete",
                    "target_date": (datetime.now() + timedelta(days=60)).isoformat(),
                    "critical": True
                },
                {
                    "milestone": "PEPPOL Controls Implemented",
                    "target_date": (datetime.now() + timedelta(days=90)).isoformat(),
                    "critical": True
                },
                {
                    "milestone": "Internal Audit Complete",
                    "target_date": (datetime.now() + timedelta(days=120)).isoformat(),
                    "critical": True
                },
                {
                    "milestone": "Certification Body Selected",
                    "target_date": (datetime.now() + timedelta(days=140)).isoformat(),
                    "critical": False
                },
                {
                    "milestone": "Stage 1 Audit Passed",
                    "target_date": (datetime.now() + readiness.estimated_certification_timeline - timedelta(days=30)).isoformat(),
                    "critical": True
                }
            ]
            
            # Identify critical path and risks
            roadmap["critical_path"] = self._identify_critical_path(readiness)
            roadmap["risk_factors"] = self._identify_certification_risks(readiness)
            
            return roadmap
            
        except Exception as e:
            self.logger.error(f"Certification roadmap creation failed: {str(e)}")
            raise
    
    def _estimate_phase_duration(self, phase: CertificationPhase, 
                                readiness: CertificationReadiness) -> timedelta:
        """Estimate duration for specific certification phase"""
        
        base_durations = {
            CertificationPhase.PREPARATION: timedelta(days=90),
            CertificationPhase.IMPLEMENTATION: timedelta(days=60),
            CertificationPhase.IMPLEMENTATION_REVIEW: timedelta(days=30),
            CertificationPhase.READY_FOR_CERTIFICATION: timedelta(days=30)
        }
        
        # Adjust based on gaps
        phase_gaps = [gap for gap in readiness.gaps_identified 
                     if self._gap_affects_phase(gap, phase)]
        
        additional_time = timedelta(days=len(phase_gaps) * 7)  # 1 week per gap
        
        return base_durations.get(phase, timedelta(days=30)) + additional_time
    
    def _gap_affects_phase(self, gap: ComplianceGap, phase: CertificationPhase) -> bool:
        """Check if compliance gap affects specific phase"""
        
        phase_mappings = {
            CertificationPhase.PREPARATION: ["STAGE1_"],
            CertificationPhase.IMPLEMENTATION: ["STAGE2_"],
            CertificationPhase.IMPLEMENTATION_REVIEW: ["STAGE2_"],
            CertificationPhase.READY_FOR_CERTIFICATION: ["STAGE1_", "STAGE2_"]
        }
        
        relevant_prefixes = phase_mappings.get(phase, [])
        return any(gap.gap_id.startswith(prefix) for prefix in relevant_prefixes)
    
    def _get_phase_deliverables(self, phase: CertificationPhase) -> List[str]:
        """Get deliverables for certification phase"""
        
        deliverables = {
            CertificationPhase.PREPARATION: [
                "ISMS Scope Document",
                "Information Security Policy",
                "Risk Assessment Report",
                "Statement of Applicability",
                "PEPPOL Security Requirements Analysis"
            ],
            CertificationPhase.IMPLEMENTATION: [
                "Implemented Security Controls",
                "PEPPOL Technical Controls (AS4, PKI, MLR)",
                "Staff Training Records",
                "Internal Audit Program",
                "Incident Response Capability"
            ],
            CertificationPhase.IMPLEMENTATION_REVIEW: [
                "Internal Audit Report",
                "Management Review Output",
                "Corrective Action Records",
                "Certification Application",
                "Pre-certification Assessment"
            ],
            CertificationPhase.READY_FOR_CERTIFICATION: [
                "Stage 1 Audit Evidence",
                "Stage 2 Audit Evidence",
                "ISO 27001 Certificate",
                "PEPPOL Certification Readiness",
                "Surveillance Audit Plan"
            ]
        }
        
        return deliverables.get(phase, [])
    
    def _get_phase_success_criteria(self, phase: CertificationPhase) -> List[str]:
        """Get success criteria for certification phase"""
        
        criteria = {
            CertificationPhase.PREPARATION: [
                "All ISMS documentation complete and approved",
                "PEPPOL security requirements integrated",
                "Risk assessment covers all business processes",
                "Control selection justified and documented"
            ],
            CertificationPhase.IMPLEMENTATION: [
                "All selected controls implemented and operational",
                "PEPPOL technical controls tested and validated",
                "Staff trained and competent",
                "Monitoring and measurement systems operational"
            ],
            CertificationPhase.IMPLEMENTATION_REVIEW: [
                "Internal audit completed without major non-conformities",
                "Management review demonstrates ISMS effectiveness",
                "All corrective actions completed",
                "Certification body application accepted"
            ],
            CertificationPhase.READY_FOR_CERTIFICATION: [
                "Stage 1 audit passed successfully",
                "Stage 2 audit passed successfully",
                "ISO 27001 certificate issued",
                "PEPPOL certification requirements met"
            ]
        }
        
        return criteria.get(phase, [])
    
    def _identify_critical_path(self, readiness: CertificationReadiness) -> List[str]:
        """Identify critical path activities for certification"""
        
        critical_activities = [
            "ISMS scope definition and approval",
            "Risk assessment methodology development",
            "PEPPOL-specific control implementation",
            "Internal audit program execution",
            "Management review completion",
            "Certification body selection and application"
        ]
        
        # Add gap-specific critical activities
        for gap in readiness.gaps_identified:
            if gap.impact_level == "critical":
                critical_activities.append(f"Resolve critical gap: {gap.requirement}")
        
        return critical_activities
    
    def _identify_certification_risks(self, readiness: CertificationReadiness) -> List[Dict[str, Any]]:
        """Identify risks to certification timeline and success"""
        
        risks = [
            {
                "risk": "Nigeria PEPPOL timeline pressure",
                "impact": "high",
                "probability": "high",
                "mitigation": "Accelerate certification process, consider consultant"
            },
            {
                "risk": "Certification body availability",
                "impact": "medium",
                "probability": "medium", 
                "mitigation": "Contact multiple bodies early, book audit slots"
            },
            {
                "risk": "PEPPOL-specific requirements complexity",
                "impact": "high",
                "probability": "medium",
                "mitigation": "Engage PEPPOL specialists, thorough requirements analysis"
            }
        ]
        
        # Add readiness-specific risks
        if readiness.overall_readiness_score < 50:
            risks.append({
                "risk": "Low current readiness level",
                "impact": "high",
                "probability": "high",
                "mitigation": "Intensive gap remediation program, external support"
            })
        
        critical_gaps = sum(1 for gap in readiness.gaps_identified if gap.impact_level == "critical")
        if critical_gaps > 3:
            risks.append({
                "risk": "Multiple critical compliance gaps",
                "impact": "high",
                "probability": "high",
                "mitigation": "Prioritize critical gaps, parallel resolution activities"
            })
        
        return risks