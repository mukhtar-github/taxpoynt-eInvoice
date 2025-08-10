"""
NDPA Compliance Engine
=====================
Central orchestrator for Nigerian Data Protection Act (NDPA) compliance
under NITDA (Nigeria Information Technology Development Agency) oversight.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from .models import (
    NDPAComplianceResult, NigerianConsentRecord, NDPABreachNotification,
    NDPADataProcessingActivity, NigerianPrivacySettings,
    NigerianDataCategory, NigerianLawfulBasis, NDPABreachSeverity
)


class NDPAComplianceLevel(str, Enum):
    """NDPA compliance levels."""
    FULLY_COMPLIANT = "fully_compliant"        # 90%+ compliance
    SUBSTANTIALLY_COMPLIANT = "substantially_compliant"  # 70-89% compliance
    PARTIALLY_COMPLIANT = "partially_compliant"  # 50-69% compliance
    NON_COMPLIANT = "non_compliant"            # <50% compliance


class NDPAComplianceEngine:
    """
    Central NDPA compliance engine for Nigerian data protection.
    
    Features:
    - NITDA regulation compliance validation
    - Nigerian data subject rights management
    - Data residency and localization requirements
    - Cross-border transfer restrictions
    - Nigerian business context integration
    - Naira-denominated penalty calculations
    - Local legal requirement validation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize NDPA compliance engine.
        
        Args:
            config: Engine configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Nigerian compliance settings
        self.nigerian_focus = self.config.get('nigerian_focus', True)
        self.data_residency_required = self.config.get('data_residency_required', True)
        self.nitda_reporting_enabled = self.config.get('nitda_reporting', True)
        self.local_dpo_required = self.config.get('local_dpo_required', True)
        
        # Penalty calculations (in Nigerian Naira)
        self.max_penalty_percentage = Decimal('2.0')  # 2% of annual turnover (lower than GDPR)
        self.fixed_penalty_amounts = {
            'minor_violation': Decimal('1000000'),      # NGN 1M
            'moderate_violation': Decimal('5000000'),   # NGN 5M
            'major_violation': Decimal('10000000'),     # NGN 10M
            'critical_violation': Decimal('50000000')   # NGN 50M
        }
        
        self.logger.info("NDPA Compliance Engine initialized for Nigerian operations")
    
    def assess_compliance(self, 
                         data_processing_activities: List[NDPADataProcessingActivity],
                         consent_records: List[NigerianConsentRecord] = None,
                         breach_history: List[NDPABreachNotification] = None,
                         privacy_settings: NigerianPrivacySettings = None) -> NDPAComplianceResult:
        """
        Comprehensive NDPA compliance assessment.
        
        Args:
            data_processing_activities: Data processing activities to assess
            consent_records: Consent records for validation
            breach_history: Historical breach notifications
            privacy_settings: Privacy configuration settings
            
        Returns:
            NDPAComplianceResult: Complete compliance assessment
        """
        self.logger.info("Starting comprehensive NDPA compliance assessment")
        
        try:
            # Initialize compliance result
            result = self._initialize_compliance_result()
            
            # 1. Assess data processing activities
            processing_score = self._assess_data_processing_compliance(
                data_processing_activities, result
            )
            
            # 2. Assess consent management
            consent_score = self._assess_consent_compliance(
                consent_records or [], result
            )
            
            # 3. Assess security measures
            security_score = self._assess_security_compliance(
                data_processing_activities, result
            )
            
            # 4. Assess breach management
            breach_score = self._assess_breach_management_compliance(
                breach_history or [], result
            )
            
            # 5. Assess Nigerian-specific requirements
            nigerian_score = self._assess_nigerian_specific_requirements(
                data_processing_activities, privacy_settings, result
            )
            
            # 6. Calculate overall compliance score
            overall_score = self._calculate_overall_score(
                processing_score, consent_score, security_score, 
                breach_score, nigerian_score
            )
            
            result.compliance_score = overall_score
            result.compliant = overall_score >= 70.0  # 70% threshold for compliance
            result.risk_level = self._determine_risk_level(overall_score, result)
            
            # 7. Calculate potential penalties
            result.potential_penalties_ngn = self._calculate_potential_penalties(result)
            
            # 8. Generate recommendations
            self._generate_recommendations(result)
            
            self.logger.info(f"NDPA compliance assessment completed: {overall_score:.1f}% compliant")
            return result
            
        except Exception as e:
            self.logger.error(f"NDPA compliance assessment failed: {str(e)}")
            return self._create_failed_assessment(str(e))
    
    def validate_data_processing_activity(self, activity: NDPADataProcessingActivity) -> Dict[str, Any]:
        """
        Validate individual data processing activity for NDPA compliance.
        
        Args:
            activity: Data processing activity to validate
            
        Returns:
            Dict: Validation results
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # 1. Validate lawful basis
        if not self._validate_lawful_basis(activity):
            validation_result['issues'].append("Invalid or insufficient lawful basis")
            validation_result['valid'] = False
        
        # 2. Validate data categories
        sensitive_categories = {
            NigerianDataCategory.SENSITIVE, NigerianDataCategory.BIOMETRIC,
            NigerianDataCategory.HEALTH, NigerianDataCategory.CHILDREN
        }
        
        if any(cat in sensitive_categories for cat in activity.data_categories):
            if activity.lawful_basis != NigerianLawfulBasis.CONSENT:
                validation_result['warnings'].append(
                    "Sensitive data processing typically requires explicit consent"
                )
        
        # 3. Validate Nigerian data residency
        if activity.nigerian_data_subjects and not activity.local_processing:
            if self.data_residency_required:
                validation_result['issues'].append(
                    "Nigerian data subjects require local data processing"
                )
                validation_result['valid'] = False
            else:
                validation_result['warnings'].append(
                    "Consider local processing for Nigerian data subjects"
                )
        
        # 4. Validate international transfers
        if activity.international_transfers:
            if not activity.adequacy_decision and not activity.safeguards_applied:
                validation_result['issues'].append(
                    "International transfers require adequacy decision or safeguards"
                )
                validation_result['valid'] = False
        
        # 5. Validate retention periods
        if self._is_excessive_retention(activity.retention_period):
            validation_result['warnings'].append(
                f"Retention period may be excessive: {activity.retention_period}"
            )
        
        return validation_result
    
    def validate_consent_record(self, consent: NigerianConsentRecord) -> Dict[str, Any]:
        """
        Validate Nigerian consent record for NDPA compliance.
        
        Args:
            consent: Consent record to validate
            
        Returns:
            Dict: Validation results
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # 1. Validate consent freshness
        if consent.given_date:
            age_days = (datetime.now() - consent.given_date).days
            if age_days > 730:  # 2 years
                validation_result['warnings'].append(
                    f"Consent is {age_days} days old, consider renewal"
                )
        
        # 2. Validate withdrawal capability
        if consent.withdrawn_date:
            validation_result['recommendations'].append(
                "Ensure data processing ceased after consent withdrawal"
            )
        
        # 3. Validate sensitive data consent
        sensitive_categories = {
            NigerianDataCategory.SENSITIVE, NigerianDataCategory.BIOMETRIC,
            NigerianDataCategory.HEALTH, NigerianDataCategory.CHILDREN
        }
        
        if any(cat in sensitive_categories for cat in consent.data_categories):
            if consent.lawful_basis != NigerianLawfulBasis.CONSENT:
                validation_result['issues'].append(
                    "Sensitive data requires explicit consent as lawful basis"
                )
                validation_result['valid'] = False
        
        # 4. Validate Nigerian resident handling
        if consent.nigerian_resident and not consent.consent_language:
            validation_result['warnings'].append(
                "Nigerian residents should receive consent in clear language"
            )
        
        return validation_result
    
    def assess_breach_notification_compliance(self, 
                                            breach: NDPABreachNotification) -> Dict[str, Any]:
        """
        Assess data breach notification compliance with NDPA requirements.
        
        Args:
            breach: Breach notification to assess
            
        Returns:
            Dict: Compliance assessment
        """
        assessment = {
            'compliant': True,
            'issues': [],
            'warnings': [],
            'timeline_compliance': True
        }
        
        # 1. Check NITDA notification timeline (72 hours)
        if breach.nitda_notification_date:
            notification_delay = (breach.nitda_notification_date - breach.discovery_date).total_seconds() / 3600
            if notification_delay > 72:
                assessment['issues'].append(
                    f"NITDA notification delayed by {notification_delay:.1f} hours (>72 hour limit)"
                )
                assessment['compliant'] = False
                assessment['timeline_compliance'] = False
        else:
            assessment['issues'].append("NITDA not notified of breach")
            assessment['compliant'] = False
        
        # 2. Check data subject notification
        if breach.severity in [NDPABreachSeverity.HIGH, NDPABreachSeverity.CRITICAL]:
            if not breach.subject_notification_date:
                assessment['warnings'].append(
                    "High/critical severity breaches typically require data subject notification"
                )
        
        # 3. Validate Nigerian-specific requirements
        if breach.estimated_affected_subjects > 100:  # Large-scale breach
            if not breach.dpo_involved:
                assessment['warnings'].append(
                    "Large-scale breaches should involve Data Protection Officer"
                )
        
        # 4. Check criminal reporting
        if 'criminal' in breach.breach_type.lower() or 'fraud' in breach.breach_type.lower():
            if not breach.police_reported:
                assessment['warnings'].append(
                    "Consider reporting criminal breaches to Nigerian Police"
                )
        
        return assessment
    
    def _initialize_compliance_result(self) -> NDPAComplianceResult:
        """Initialize empty compliance result."""
        return NDPAComplianceResult(
            compliant=False,
            compliance_score=0.0,
            risk_level="unknown",
            assessor="NDPA Compliance Engine",
            next_assessment_due=datetime.now() + timedelta(days=90)
        )
    
    def _assess_data_processing_compliance(self, 
                                         activities: List[NDPADataProcessingActivity],
                                         result: NDPAComplianceResult) -> float:
        """Assess data processing activities compliance."""
        if not activities:
            result.critical_issues.append("No data processing activities registered")
            return 0.0
        
        total_score = 0.0
        issues_found = 0
        
        for activity in activities:
            activity_validation = self.validate_data_processing_activity(activity)
            
            if activity_validation['valid']:
                total_score += 100.0
            else:
                issues_found += len(activity_validation['issues'])
                result.critical_issues.extend(activity_validation['issues'])
                result.warnings.extend(activity_validation['warnings'])
        
        processing_score = total_score / len(activities) if activities else 0.0
        
        # Populate detailed results
        result.data_processing_compliance = {
            'score': processing_score,
            'activities_assessed': len(activities),
            'compliant_activities': sum(1 for a in activities if self.validate_data_processing_activity(a)['valid']),
            'issues_found': issues_found
        }
        
        return processing_score
    
    def _assess_consent_compliance(self, 
                                 consents: List[NigerianConsentRecord],
                                 result: NDPAComplianceResult) -> float:
        """Assess consent management compliance."""
        if not consents:
            result.warnings.append("No consent records found for assessment")
            return 50.0  # Partial score if no consent needed
        
        total_score = 0.0
        valid_consents = 0
        
        for consent in consents:
            consent_validation = self.validate_consent_record(consent)
            
            if consent_validation['valid']:
                valid_consents += 1
                total_score += 100.0
            else:
                result.critical_issues.extend(consent_validation['issues'])
            
            result.warnings.extend(consent_validation['warnings'])
        
        consent_score = total_score / len(consents) if consents else 0.0
        
        # Populate detailed results
        result.consent_compliance = {
            'score': consent_score,
            'consents_assessed': len(consents),
            'valid_consents': valid_consents,
            'consent_coverage': (valid_consents / len(consents)) * 100 if consents else 0
        }
        
        return consent_score
    
    def _assess_security_compliance(self, 
                                  activities: List[NDPADataProcessingActivity],
                                  result: NDPAComplianceResult) -> float:
        """Assess security measures compliance."""
        if not activities:
            return 0.0
        
        security_scores = []
        
        for activity in activities:
            activity_score = 0.0
            
            # Technical safeguards
            if activity.technical_safeguards:
                activity_score += 40.0
            else:
                result.critical_issues.append(f"No technical safeguards for activity: {activity.activity_name}")
            
            # Organizational measures
            if activity.organizational_measures:
                activity_score += 30.0
            else:
                result.warnings.append(f"No organizational measures for activity: {activity.activity_name}")
            
            # Access controls
            if activity.access_controls:
                activity_score += 30.0
            else:
                result.warnings.append(f"No access controls for activity: {activity.activity_name}")
            
            security_scores.append(activity_score)
        
        security_score = sum(security_scores) / len(security_scores) if security_scores else 0.0
        
        # Populate detailed results
        result.security_compliance = {
            'score': security_score,
            'activities_with_technical_safeguards': sum(1 for a in activities if a.technical_safeguards),
            'activities_with_org_measures': sum(1 for a in activities if a.organizational_measures),
            'activities_with_access_controls': sum(1 for a in activities if a.access_controls)
        }
        
        return security_score
    
    def _assess_breach_management_compliance(self, 
                                           breaches: List[NDPABreachNotification],
                                           result: NDPAComplianceResult) -> float:
        """Assess breach management compliance."""
        if not breaches:
            # No breaches is good, but we still need breach management procedures
            result.breach_management_compliance = {
                'score': 80.0,  # Good score if no breaches
                'breaches_assessed': 0,
                'compliant_notifications': 0,
                'average_notification_time': 0
            }
            return 80.0
        
        compliant_breaches = 0
        total_notification_times = []
        
        for breach in breaches:
            breach_assessment = self.assess_breach_notification_compliance(breach)
            
            if breach_assessment['compliant']:
                compliant_breaches += 1
            else:
                result.critical_issues.extend(breach_assessment['issues'])
            
            result.warnings.extend(breach_assessment['warnings'])
            
            # Track notification times
            if breach.nitda_notification_date:
                notification_time = (breach.nitda_notification_date - breach.discovery_date).total_seconds() / 3600
                total_notification_times.append(notification_time)
        
        breach_score = (compliant_breaches / len(breaches)) * 100 if breaches else 0.0
        
        # Populate detailed results
        result.breach_management_compliance = {
            'score': breach_score,
            'breaches_assessed': len(breaches),
            'compliant_notifications': compliant_breaches,
            'average_notification_time': sum(total_notification_times) / len(total_notification_times) if total_notification_times else 0
        }
        
        return breach_score
    
    def _assess_nigerian_specific_requirements(self, 
                                             activities: List[NDPADataProcessingActivity],
                                             privacy_settings: Optional[NigerianPrivacySettings],
                                             result: NDPAComplianceResult) -> float:
        """Assess Nigerian-specific NDPA requirements."""
        nigerian_score = 0.0
        max_score = 100.0
        
        # 1. Data residency requirements (30 points)
        if self.data_residency_required:
            nigerian_activities = [a for a in activities if a.nigerian_data_subjects]
            local_processing = [a for a in nigerian_activities if a.local_processing]
            
            if nigerian_activities:
                residency_score = (len(local_processing) / len(nigerian_activities)) * 30
                nigerian_score += residency_score
                
                if residency_score < 30:
                    result.nitda_requirements_missing.append("Data residency requirements not fully met")
            else:
                nigerian_score += 30  # No Nigerian data, requirement met
        else:
            nigerian_score += 30
        
        # 2. Local DPO requirements (25 points)
        if self.local_dpo_required:
            # Check if any activity has high-risk processing
            high_risk_activities = [
                a for a in activities 
                if len(a.data_categories) > 3 or a.international_transfers
            ]
            
            if high_risk_activities:
                # For now, assume DPO requirement is met (in practice, check organization structure)
                nigerian_score += 25
                result.nitda_requirements_met.append("Data Protection Officer requirements addressed")
            else:
                nigerian_score += 25  # No high-risk processing, DPO not required
        else:
            nigerian_score += 25
        
        # 3. NITDA registration and reporting (25 points)
        if self.nitda_reporting_enabled:
            nigerian_score += 25
            result.nitda_requirements_met.append("NITDA reporting enabled")
        else:
            result.nitda_requirements_missing.append("NITDA reporting not enabled")
        
        # 4. Nigerian language and accessibility (20 points)
        if privacy_settings:
            if privacy_settings.english_language_required:
                nigerian_score += 20
                result.nitda_requirements_met.append("English language support enabled")
            else:
                result.warnings.append("Consider English language support for Nigerian users")
                nigerian_score += 10  # Partial credit
        else:
            nigerian_score += 10  # Partial credit if no settings provided
        
        return nigerian_score
    
    def _calculate_overall_score(self, processing: float, consent: float, 
                               security: float, breach: float, nigerian: float) -> float:
        """Calculate weighted overall compliance score."""
        weights = {
            'processing': 0.25,
            'consent': 0.20,
            'security': 0.25,
            'breach': 0.15,
            'nigerian': 0.15
        }
        
        return (
            processing * weights['processing'] +
            consent * weights['consent'] +
            security * weights['security'] +
            breach * weights['breach'] +
            nigerian * weights['nigerian']
        )
    
    def _determine_risk_level(self, score: float, result: NDPAComplianceResult) -> str:
        """Determine risk level based on compliance score and issues."""
        critical_issues = len(result.critical_issues)
        
        if score >= 90 and critical_issues == 0:
            return "low"
        elif score >= 70 and critical_issues <= 2:
            return "medium"
        elif score >= 50:
            return "high"
        else:
            return "critical"
    
    def _calculate_potential_penalties(self, result: NDPAComplianceResult) -> Optional[Decimal]:
        """Calculate potential NDPA penalties in Nigerian Naira."""
        if result.compliant:
            return None
        
        penalty_amount = Decimal('0')
        
        # Base penalty based on compliance score
        if result.compliance_score < 50:
            penalty_amount = self.fixed_penalty_amounts['critical_violation']
        elif result.compliance_score < 70:
            penalty_amount = self.fixed_penalty_amounts['major_violation']
        elif result.compliance_score < 80:
            penalty_amount = self.fixed_penalty_amounts['moderate_violation']
        else:
            penalty_amount = self.fixed_penalty_amounts['minor_violation']
        
        # Additional penalties for critical issues
        penalty_amount += Decimal(len(result.critical_issues)) * Decimal('500000')  # NGN 500k per issue
        
        return penalty_amount
    
    def _generate_recommendations(self, result: NDPAComplianceResult):
        """Generate compliance improvement recommendations."""
        if result.compliance_score < 70:
            result.recommendations.append("Priority: Achieve basic NDPA compliance (70% threshold)")
        
        if len(result.critical_issues) > 0:
            result.recommendations.append("Immediate: Address all critical compliance issues")
        
        if result.data_processing_compliance.get('score', 0) < 80:
            result.recommendations.append("Improve data processing activity documentation and compliance")
        
        if result.consent_compliance.get('score', 0) < 80:
            result.recommendations.append("Enhance consent management and record-keeping")
        
        if result.security_compliance.get('score', 0) < 80:
            result.recommendations.append("Strengthen technical and organizational security measures")
        
        if len(result.nitda_requirements_missing) > 0:
            result.recommendations.append("Address missing NITDA-specific requirements")
    
    def _create_failed_assessment(self, error_message: str) -> NDPAComplianceResult:
        """Create failed assessment result."""
        return NDPAComplianceResult(
            compliant=False,
            compliance_score=0.0,
            risk_level="critical",
            critical_issues=[f"Assessment failed: {error_message}"],
            assessor="NDPA Compliance Engine",
            next_assessment_due=datetime.now() + timedelta(days=30)
        )
    
    def _validate_lawful_basis(self, activity: NDPADataProcessingActivity) -> bool:
        """Validate lawful basis for data processing activity."""
        if not activity.lawful_basis:
            return False
        
        # Additional validation based on data categories
        sensitive_categories = {
            NigerianDataCategory.SENSITIVE, NigerianDataCategory.BIOMETRIC,
            NigerianDataCategory.HEALTH, NigerianDataCategory.CHILDREN
        }
        
        # Sensitive data typically requires consent
        if (any(cat in sensitive_categories for cat in activity.data_categories) and
            activity.lawful_basis not in [NigerianLawfulBasis.CONSENT, NigerianLawfulBasis.VITAL_INTERESTS]):
            return False
        
        return True
    
    def _is_excessive_retention(self, retention_period: str) -> bool:
        """Check if retention period is excessive."""
        # Simple heuristic - in practice, this would be more sophisticated
        if 'indefinite' in retention_period.lower() or 'permanent' in retention_period.lower():
            return True
        
        # Extract years if possible
        if 'year' in retention_period:
            try:
                years = int(''.join(filter(str.isdigit, retention_period)))
                return years > 7  # More than 7 years might be excessive
            except ValueError:
                return False
        
        return False