"""
GDPR Compliance Engine
=====================
Central orchestrator for European General Data Protection Regulation (GDPR) compliance
with EU/EEA regulatory requirements and cross-border data protection.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from .models import (
    GDPRComplianceResult, EuropeanConsentRecord, GDPRBreachNotification,
    GDPRDataProcessingActivity, EuropeanPrivacySettings,
    EuropeanDataCategory, EuropeanLawfulBasis, GDPRBreachSeverity,
    TransferMechanism
)


class GDPRComplianceLevel(str, Enum):
    """GDPR compliance levels."""
    FULLY_COMPLIANT = "fully_compliant"        # 90%+ compliance
    SUBSTANTIALLY_COMPLIANT = "substantially_compliant"  # 70-89% compliance
    PARTIALLY_COMPLIANT = "partially_compliant"  # 50-69% compliance
    NON_COMPLIANT = "non_compliant"            # <50% compliance


class EUSupervisoryAuthority(str, Enum):
    """EU/EEA Supervisory Authorities for GDPR enforcement."""
    AUSTRIA_DSB = "austria_dsb"
    BELGIUM_APD = "belgium_apd"
    BULGARIA_CPDP = "bulgaria_cpdp"
    CROATIA_AZOP = "croatia_azop"
    CYPRUS_DPC = "cyprus_dpc"
    CZECH_UOOU = "czech_uoou"
    DENMARK_DT = "denmark_dt"
    ESTONIA_AKI = "estonia_aki"
    FINLAND_TIETOSUOJA = "finland_tietosuoja"
    FRANCE_CNIL = "france_cnil"
    GERMANY_BfDI = "germany_bfdi"
    GREECE_HDPA = "greece_hdpa"
    HUNGARY_NAIH = "hungary_naih"
    IRELAND_DPC = "ireland_dpc"
    ITALY_GPDP = "italy_gpdp"
    LATVIA_DVI = "latvia_dvi"
    LITHUANIA_ADA = "lithuania_ada"
    LUXEMBOURG_CNPD = "luxembourg_cnpd"
    MALTA_IDPC = "malta_idpc"
    NETHERLANDS_AP = "netherlands_ap"
    POLAND_PUODO = "poland_puodo"
    PORTUGAL_CNPD = "portugal_cnpd"
    ROMANIA_ANSPDCP = "romania_anspdcp"
    SLOVAKIA_UOOU = "slovakia_uoou"
    SLOVENIA_IP = "slovenia_ip"
    SPAIN_AEPD = "spain_aepd"
    SWEDEN_IMY = "sweden_imy"
    ICELAND_DPA = "iceland_dpa"
    LIECHTENSTEIN_DSS = "liechtenstein_dss"
    NORWAY_DT = "norway_dt"


class GDPRComplianceEngine:
    """
    Central GDPR compliance engine for European data protection.
    
    Features:
    - EU/EEA regulatory compliance validation
    - European data subject rights management
    - Cross-border transfer validation (adequacy decisions, SCCs)
    - One-stop-shop mechanism support
    - EUR penalty calculations (up to 4% of turnover)
    - Article 30 record-keeping compliance
    - DPIA requirement assessment
    - Multi-jurisdictional compliance coordination
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize GDPR compliance engine.
        
        Args:
            config: Engine configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # EU/EEA compliance settings
        self.eu_focus = self.config.get('eu_focus', True)
        self.one_stop_shop = self.config.get('one_stop_shop', True)
        self.lead_sa = self.config.get('lead_supervisory_authority')
        self.dpo_required = self.config.get('dpo_required', False)
        
        # Penalty calculations (in EUR)
        self.administrative_fine_tiers = {
            'tier_1_max': Decimal('10000000'),      # EUR 10M or 2% of turnover
            'tier_1_percentage': Decimal('2.0'),
            'tier_2_max': Decimal('20000000'),      # EUR 20M or 4% of turnover  
            'tier_2_percentage': Decimal('4.0')
        }
        
        # EU adequacy countries (as of 2024)
        self.adequacy_countries = {
            'andorra', 'argentina', 'canada', 'faroe_islands', 'guernsey',
            'israel', 'isle_of_man', 'japan', 'jersey', 'new_zealand',
            'south_korea', 'switzerland', 'united_kingdom', 'uruguay'
        }
        
        self.logger.info("GDPR Compliance Engine initialized for EU/EEA operations")
    
    def assess_compliance(self, 
                         data_processing_activities: List[GDPRDataProcessingActivity],
                         consent_records: List[EuropeanConsentRecord] = None,
                         breach_history: List[GDPRBreachNotification] = None,
                         privacy_settings: EuropeanPrivacySettings = None,
                         annual_turnover_eur: Optional[Decimal] = None) -> GDPRComplianceResult:
        """
        Comprehensive GDPR compliance assessment.
        
        Args:
            data_processing_activities: Data processing activities to assess
            consent_records: Consent records for validation
            breach_history: Historical breach notifications
            privacy_settings: Privacy configuration settings
            annual_turnover_eur: Annual turnover for penalty calculation
            
        Returns:
            GDPRComplianceResult: Complete compliance assessment
        """
        self.logger.info("Starting comprehensive GDPR compliance assessment")
        
        try:
            # Initialize compliance result
            result = self._initialize_compliance_result()
            
            # 1. Assess Article 30 record-keeping
            article30_score = self._assess_article30_compliance(
                data_processing_activities, result
            )
            
            # 2. Assess consent management (Articles 6-9)
            consent_score = self._assess_consent_compliance(
                consent_records or [], result
            )
            
            # 3. Assess data processing activities (Articles 5-6)
            processing_score = self._assess_data_processing_compliance(
                data_processing_activities, result
            )
            
            # 4. Assess security measures (Article 32)
            security_score = self._assess_security_compliance(
                data_processing_activities, result
            )
            
            # 5. Assess international transfers (Chapter V)
            transfer_score = self._assess_transfer_compliance(
                data_processing_activities, result
            )
            
            # 6. Assess breach management (Articles 33-34)
            breach_score = self._assess_breach_management_compliance(
                breach_history or [], result
            )
            
            # 7. Assess DPIA requirements (Article 35)
            dpia_score = self._assess_dpia_compliance(
                data_processing_activities, result
            )
            
            # 8. Assess data subject rights (Chapter III)
            rights_score = self._assess_data_subject_rights_compliance(
                privacy_settings, result
            )
            
            # 9. Calculate overall compliance score
            overall_score = self._calculate_overall_score(
                article30_score, consent_score, processing_score, security_score,
                transfer_score, breach_score, dpia_score, rights_score
            )
            
            result.compliance_score = overall_score
            result.compliant = overall_score >= 70.0  # 70% threshold for compliance
            result.risk_level = self._determine_risk_level(overall_score, result)
            
            # 10. Calculate potential penalties
            result.potential_penalties_eur, result.max_fine_applicable = self._calculate_potential_penalties(
                result, annual_turnover_eur
            )
            
            # 11. Determine supervisory authorities
            self._determine_supervisory_authorities(data_processing_activities, result)
            
            # 12. Generate recommendations
            self._generate_recommendations(result)
            
            self.logger.info(f"GDPR compliance assessment completed: {overall_score:.1f}% compliant")
            return result
            
        except Exception as e:
            self.logger.error(f"GDPR compliance assessment failed: {str(e)}")
            return self._create_failed_assessment(str(e))
    
    def validate_data_processing_activity(self, activity: GDPRDataProcessingActivity) -> Dict[str, Any]:
        """
        Validate individual data processing activity for GDPR compliance.
        
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
        
        # 1. Validate lawful basis (Article 6)
        if not self._validate_article6_lawful_basis(activity):
            validation_result['issues'].append("Invalid or insufficient Article 6 lawful basis")
            validation_result['valid'] = False
        
        # 2. Validate special category processing (Article 9)
        if activity.special_category_processing:
            if not activity.article_9_condition:
                validation_result['issues'].append("Special category processing requires Article 9 condition")
                validation_result['valid'] = False
            
            # Check if special categories are actually present
            special_categories = {
                EuropeanDataCategory.SPECIAL, EuropeanDataCategory.BIOMETRIC,
                EuropeanDataCategory.GENETIC, EuropeanDataCategory.HEALTH
            }
            
            if not any(cat in special_categories for cat in activity.data_categories):
                validation_result['warnings'].append("Special category processing flag set but no special categories detected")
        
        # 3. Validate international transfers
        if activity.international_transfers:
            if not activity.transfer_mechanism:
                validation_result['issues'].append("International transfers require specified transfer mechanism")
                validation_result['valid'] = False
            
            # Validate transfer mechanism
            if activity.transfer_mechanism == TransferMechanism.ADEQUACY_DECISION:
                if not activity.adequacy_decision:
                    validation_result['issues'].append("Adequacy decision transfers require decision reference")
                    validation_result['valid'] = False
            
            elif activity.transfer_mechanism == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES:
                if not activity.safeguards_applied:
                    validation_result['warnings'].append("SCC transfers should specify applied safeguards")
        
        # 4. Validate DPIA requirements (Article 35)
        if self._requires_dpia(activity):
            if not activity.dpia_required:
                validation_result['warnings'].append("Activity likely requires Data Protection Impact Assessment")
            elif not activity.dpia_completed:
                validation_result['issues'].append("DPIA required but not completed")
                validation_result['valid'] = False
        
        # 5. Validate retention periods (Article 5(1)(e))
        if self._is_excessive_retention(activity.retention_period):
            validation_result['warnings'].append(f"Retention period may violate storage limitation: {activity.retention_period}")
        
        # 6. Validate security measures (Article 32)
        if not activity.technical_safeguards and not activity.organizational_measures:
            validation_result['issues'].append("Article 32 requires appropriate technical and organizational measures")
            validation_result['valid'] = False
        
        return validation_result
    
    def validate_consent_record(self, consent: EuropeanConsentRecord) -> Dict[str, Any]:
        """
        Validate European consent record for GDPR compliance.
        
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
        
        # 1. Validate Article 7 consent requirements
        if consent.lawful_basis == EuropeanLawfulBasis.CONSENT:
            if not all([consent.freely_given, consent.specific, consent.informed, consent.unambiguous]):
                validation_result['issues'].append("Consent must be freely given, specific, informed, and unambiguous (Article 7)")
                validation_result['valid'] = False
        
        # 2. Validate special category consent (Article 9)
        special_categories = {
            EuropeanDataCategory.SPECIAL, EuropeanDataCategory.BIOMETRIC,
            EuropeanDataCategory.GENETIC, EuropeanDataCategory.HEALTH
        }
        
        if any(cat in special_categories for cat in consent.data_categories):
            if not consent.special_category_consent:
                validation_result['issues'].append("Special category data requires explicit consent (Article 9)")
                validation_result['valid'] = False
        
        # 3. Validate consent withdrawal
        if consent.withdrawn_date:
            if consent.withdrawn_date <= consent.given_date:
                validation_result['issues'].append("Consent withdrawal date cannot be before given date")
                validation_result['valid'] = False
            
            validation_result['recommendations'].append("Ensure processing ceased after consent withdrawal")
        
        # 4. Validate consent freshness
        if consent.given_date:
            age_days = (datetime.now() - consent.given_date).days
            if age_days > 1095:  # 3 years
                validation_result['warnings'].append(f"Consent is {age_days} days old, consider renewal")
        
        # 5. Validate children's consent (Article 8)
        if EuropeanDataCategory.CHILDREN in consent.data_categories:
            validation_result['warnings'].append("Children's data processing requires parental consent verification")
        
        return validation_result
    
    def assess_breach_notification_compliance(self, breach: GDPRBreachNotification) -> Dict[str, Any]:
        """
        Assess data breach notification compliance with GDPR requirements.
        
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
        
        # 1. Check DPA notification timeline (Article 33 - 72 hours)
        if breach.dpa_notification_date:
            notification_delay = (breach.dpa_notification_date - breach.discovery_date).total_seconds() / 3600
            if notification_delay > 72:
                assessment['issues'].append(
                    f"DPA notification delayed by {notification_delay:.1f} hours (>72 hour limit, Article 33)"
                )
                assessment['compliant'] = False
                assessment['timeline_compliance'] = False
        else:
            if breach.severity in [GDPRBreachSeverity.MEDIUM, GDPRBreachSeverity.HIGH, GDPRBreachSeverity.CRITICAL]:
                assessment['issues'].append("DPA notification required for breaches likely to result in risk (Article 33)")
                assessment['compliant'] = False
        
        # 2. Check data subject notification (Article 34)
        if breach.severity in [GDPRBreachSeverity.HIGH, GDPRBreachSeverity.CRITICAL]:
            if not breach.subject_notification_date:
                assessment['warnings'].append(
                    "High risk breaches typically require data subject notification (Article 34)"
                )
        
        # 3. Cross-border breach handling
        if breach.cross_border_breach:
            if not breach.lead_sa:
                assessment['warnings'].append("Cross-border breaches should identify lead supervisory authority")
            
            if not breach.concerned_sas:
                assessment['warnings'].append("Cross-border breaches should identify concerned supervisory authorities")
            
            if not breach.one_stop_shop:
                assessment['warnings'].append("Consider one-stop-shop mechanism for cross-border breaches")
        
        # 4. DPO involvement
        if self.dpo_required and not breach.dpo_involved:
            assessment['warnings'].append("Data Protection Officer should be involved in breach response")
        
        return assessment
    
    def validate_international_transfer(self, activity: GDPRDataProcessingActivity) -> Dict[str, Any]:
        """
        Validate international data transfer compliance (Chapter V).
        
        Args:
            activity: Data processing activity with international transfers
            
        Returns:
            Dict: Transfer validation results
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        if not activity.international_transfers:
            return validation_result
        
        # 1. Validate transfer mechanism
        if not activity.transfer_mechanism:
            validation_result['issues'].append("International transfers require valid transfer mechanism")
            validation_result['valid'] = False
            return validation_result
        
        # 2. Adequacy decision validation
        if activity.transfer_mechanism == TransferMechanism.ADEQUACY_DECISION:
            # Check if destination countries have adequacy decisions
            for recipient in activity.third_country_recipients:
                country = recipient.lower().replace(' ', '_')
                if country not in self.adequacy_countries:
                    validation_result['warnings'].append(f"No adequacy decision for {recipient}")
        
        # 3. Standard Contractual Clauses validation
        elif activity.transfer_mechanism == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES:
            if not activity.safeguards_applied:
                validation_result['issues'].append("SCC transfers require specified safeguards")
                validation_result['valid'] = False
            
            # Check for additional safeguards
            recommended_safeguards = ['encryption', 'pseudonymization', 'access_controls']
            applied_safeguards = [s.lower() for s in activity.safeguards_applied]
            
            missing_safeguards = [s for s in recommended_safeguards if s not in applied_safeguards]
            if missing_safeguards:
                validation_result['recommendations'].extend([
                    f"Consider implementing {s} for enhanced transfer protection" 
                    for s in missing_safeguards
                ])
        
        # 4. Binding Corporate Rules validation
        elif activity.transfer_mechanism == TransferMechanism.BINDING_CORPORATE_RULES:
            validation_result['recommendations'].append("Ensure BCRs are approved by competent supervisory authority")
        
        # 5. Derogations validation (Article 49)
        elif activity.transfer_mechanism == TransferMechanism.DEROGATION:
            validation_result['warnings'].append("Derogations should only be used for occasional, non-repetitive transfers")
            
            # Check if transfer is appropriate for derogations
            if len(activity.third_country_recipients) > 1:
                validation_result['warnings'].append("Multiple recipients may not be suitable for derogations")
        
        return validation_result
    
    def _initialize_compliance_result(self) -> GDPRComplianceResult:
        """Initialize empty compliance result."""
        return GDPRComplianceResult(
            compliant=False,
            compliance_score=0.0,
            risk_level="unknown",
            assessor="GDPR Compliance Engine",
            next_assessment_due=datetime.now() + timedelta(days=90)
        )
    
    def _assess_article30_compliance(self, 
                                   activities: List[GDPRDataProcessingActivity],
                                   result: GDPRComplianceResult) -> float:
        """Assess Article 30 record-keeping compliance."""
        if not activities:
            result.critical_issues.append("No Article 30 records of processing activities found")
            result.article_30_compliance = {'score': 0.0, 'records_count': 0}
            return 0.0
        
        compliant_records = 0
        
        for activity in activities:
            record_complete = True
            
            # Check required Article 30 fields
            required_fields = [
                'activity_name', 'purposes', 'data_categories', 'lawful_basis',
                'data_controller', 'retention_period'
            ]
            
            for field in required_fields:
                if not getattr(activity, field, None):
                    record_complete = False
                    break
            
            if record_complete:
                compliant_records += 1
        
        article30_score = (compliant_records / len(activities)) * 100
        
        result.article_30_compliance = {
            'score': article30_score,
            'records_count': len(activities),
            'compliant_records': compliant_records,
            'completion_rate': article30_score
        }
        
        if article30_score < 80:
            result.critical_issues.append("Article 30 record-keeping requirements not fully met")
        
        return article30_score
    
    def _assess_consent_compliance(self, 
                                 consents: List[EuropeanConsentRecord],
                                 result: GDPRComplianceResult) -> float:
        """Assess consent management compliance."""
        if not consents:
            result.warnings.append("No consent records found for assessment")
            result.consent_compliance = {'score': 50.0, 'consents_assessed': 0}
            return 50.0
        
        valid_consents = 0
        total_score = 0.0
        
        for consent in consents:
            consent_validation = self.validate_consent_record(consent)
            
            if consent_validation['valid']:
                valid_consents += 1
                total_score += 100.0
            else:
                result.critical_issues.extend(consent_validation['issues'])
            
            result.warnings.extend(consent_validation['warnings'])
        
        consent_score = total_score / len(consents) if consents else 0.0
        
        result.consent_compliance = {
            'score': consent_score,
            'consents_assessed': len(consents),
            'valid_consents': valid_consents,
            'consent_coverage': (valid_consents / len(consents)) * 100 if consents else 0
        }
        
        return consent_score
    
    def _assess_data_processing_compliance(self, 
                                         activities: List[GDPRDataProcessingActivity],
                                         result: GDPRComplianceResult) -> float:
        """Assess data processing activities compliance."""
        if not activities:
            return 0.0
        
        total_score = 0.0
        compliant_activities = 0
        
        for activity in activities:
            activity_validation = self.validate_data_processing_activity(activity)
            
            if activity_validation['valid']:
                compliant_activities += 1
                total_score += 100.0
            else:
                result.critical_issues.extend(activity_validation['issues'])
            
            result.warnings.extend(activity_validation['warnings'])
        
        processing_score = total_score / len(activities) if activities else 0.0
        
        result.data_processing_compliance = {
            'score': processing_score,
            'activities_assessed': len(activities),
            'compliant_activities': compliant_activities,
            'compliance_rate': processing_score
        }
        
        return processing_score
    
    def _assess_security_compliance(self, 
                                  activities: List[GDPRDataProcessingActivity],
                                  result: GDPRComplianceResult) -> float:
        """Assess Article 32 security measures compliance."""
        if not activities:
            return 0.0
        
        security_scores = []
        
        for activity in activities:
            activity_score = 0.0
            
            # Technical measures (50%)
            if activity.technical_safeguards:
                activity_score += 25.0
                
                # Bonus for encryption and pseudonymization
                safeguards_lower = [s.lower() for s in activity.technical_safeguards]
                if activity.encryption or 'encryption' in safeguards_lower:
                    activity_score += 15.0
                else:
                    result.warnings.append(f"Consider encryption for activity: {activity.activity_name}")
                
                if activity.pseudonymization or 'pseudonymization' in safeguards_lower:
                    activity_score += 10.0
            else:
                result.critical_issues.append(f"No technical safeguards for activity: {activity.activity_name}")
            
            # Organizational measures (50%)
            if activity.organizational_measures:
                activity_score += 50.0
            else:
                result.critical_issues.append(f"No organizational measures for activity: {activity.activity_name}")
            
            security_scores.append(activity_score)
        
        security_score = sum(security_scores) / len(security_scores) if security_scores else 0.0
        
        result.security_compliance = {
            'score': security_score,
            'activities_with_technical_measures': sum(1 for a in activities if a.technical_safeguards),
            'activities_with_organizational_measures': sum(1 for a in activities if a.organizational_measures),
            'encryption_adoption': sum(1 for a in activities if a.encryption),
            'pseudonymization_adoption': sum(1 for a in activities if a.pseudonymization)
        }
        
        return security_score
    
    def _assess_transfer_compliance(self, 
                                  activities: List[GDPRDataProcessingActivity],
                                  result: GDPRComplianceResult) -> float:
        """Assess Chapter V international transfer compliance."""
        transfer_activities = [a for a in activities if a.international_transfers]
        
        if not transfer_activities:
            result.transfer_compliance = {
                'score': 100.0,  # No transfers = full compliance
                'transfer_activities': 0,
                'compliant_transfers': 0
            }
            return 100.0
        
        compliant_transfers = 0
        
        for activity in transfer_activities:
            transfer_validation = self.validate_international_transfer(activity)
            
            if transfer_validation['valid']:
                compliant_transfers += 1
            else:
                result.critical_issues.extend(transfer_validation['issues'])
            
            result.warnings.extend(transfer_validation['warnings'])
        
        transfer_score = (compliant_transfers / len(transfer_activities)) * 100
        
        result.transfer_compliance = {
            'score': transfer_score,
            'transfer_activities': len(transfer_activities),
            'compliant_transfers': compliant_transfers,
            'adequacy_transfers': sum(1 for a in transfer_activities 
                                    if a.transfer_mechanism == TransferMechanism.ADEQUACY_DECISION),
            'scc_transfers': sum(1 for a in transfer_activities 
                               if a.transfer_mechanism == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES)
        }
        
        return transfer_score
    
    def _assess_breach_management_compliance(self, 
                                           breaches: List[GDPRBreachNotification],
                                           result: GDPRComplianceResult) -> float:
        """Assess Articles 33-34 breach management compliance."""
        if not breaches:
            result.breach_management_compliance = {
                'score': 80.0,  # Good score if no breaches
                'breaches_assessed': 0,
                'compliant_notifications': 0
            }
            return 80.0
        
        compliant_breaches = 0
        
        for breach in breaches:
            breach_assessment = self.assess_breach_notification_compliance(breach)
            
            if breach_assessment['compliant']:
                compliant_breaches += 1
            else:
                result.critical_issues.extend(breach_assessment['issues'])
            
            result.warnings.extend(breach_assessment['warnings'])
        
        breach_score = (compliant_breaches / len(breaches)) * 100 if breaches else 0.0
        
        result.breach_management_compliance = {
            'score': breach_score,
            'breaches_assessed': len(breaches),
            'compliant_notifications': compliant_breaches,
            'cross_border_breaches': sum(1 for b in breaches if b.cross_border_breach)
        }
        
        return breach_score
    
    def _assess_dpia_compliance(self, 
                              activities: List[GDPRDataProcessingActivity],
                              result: GDPRComplianceResult) -> float:
        """Assess Article 35 DPIA compliance."""
        dpia_required_activities = [a for a in activities if self._requires_dpia(a)]
        
        if not dpia_required_activities:
            result.dpia_compliance = {
                'score': 100.0,  # No DPIAs required = full compliance
                'dpia_required_activities': 0,
                'completed_dpias': 0
            }
            return 100.0
        
        completed_dpias = sum(1 for a in dpia_required_activities if a.dpia_completed)
        
        # Check if activities correctly identified DPIA requirement
        correctly_identified = sum(1 for a in dpia_required_activities if a.dpia_required)
        
        if correctly_identified < len(dpia_required_activities):
            result.warnings.append(f"{len(dpia_required_activities) - correctly_identified} activities require DPIA but not identified")
        
        dpia_score = (completed_dpias / len(dpia_required_activities)) * 100
        
        result.dpia_compliance = {
            'score': dpia_score,
            'dpia_required_activities': len(dpia_required_activities),
            'completed_dpias': completed_dpias,
            'correctly_identified': correctly_identified
        }
        
        if dpia_score < 100:
            result.critical_issues.append("Some activities require DPIA but assessment not completed")
        
        return dpia_score
    
    def _assess_data_subject_rights_compliance(self, 
                                             privacy_settings: Optional[EuropeanPrivacySettings],
                                             result: GDPRComplianceResult) -> float:
        """Assess Chapter III data subject rights compliance."""
        if not privacy_settings:
            result.warnings.append("No privacy settings provided for data subject rights assessment")
            result.data_subject_rights_compliance = {'score': 50.0}
            return 50.0
        
        rights_score = 0.0
        
        # Access rights (Article 15)
        if privacy_settings.automated_access_requests:
            rights_score += 15.0
        else:
            result.warnings.append("Consider implementing automated access request handling")
        
        # Rectification (Article 16) - assumed if system allows data updates
        rights_score += 15.0
        
        # Erasure (Article 17)
        if privacy_settings.erasure_verification:
            rights_score += 15.0
        else:
            result.warnings.append("Erasure verification recommended for right to be forgotten")
        
        # Data portability (Article 20)
        if privacy_settings.data_portability_format:
            rights_score += 15.0
        else:
            result.warnings.append("Data portability format should be specified")
        
        # Consent withdrawal
        if privacy_settings.consent_withdrawal:
            rights_score += 20.0
        else:
            result.critical_issues.append("Consent withdrawal mechanism is required")
        
        # Granular consent
        if privacy_settings.granular_consent:
            rights_score += 20.0
        else:
            result.warnings.append("Granular consent options recommended")
        
        result.data_subject_rights_compliance = {
            'score': rights_score,
            'automated_access': privacy_settings.automated_access_requests,
            'erasure_verification': privacy_settings.erasure_verification,
            'consent_withdrawal': privacy_settings.consent_withdrawal,
            'granular_consent': privacy_settings.granular_consent
        }
        
        return rights_score
    
    def _calculate_overall_score(self, article30: float, consent: float, processing: float,
                               security: float, transfer: float, breach: float, 
                               dpia: float, rights: float) -> float:
        """Calculate weighted overall compliance score."""
        weights = {
            'article30': 0.15,    # Record-keeping
            'consent': 0.15,      # Consent management
            'processing': 0.20,   # Data processing
            'security': 0.15,     # Security measures
            'transfer': 0.10,     # International transfers
            'breach': 0.10,       # Breach management
            'dpia': 0.05,         # DPIA
            'rights': 0.10        # Data subject rights
        }
        
        return (
            article30 * weights['article30'] +
            consent * weights['consent'] +
            processing * weights['processing'] +
            security * weights['security'] +
            transfer * weights['transfer'] +
            breach * weights['breach'] +
            dpia * weights['dpia'] +
            rights * weights['rights']
        )
    
    def _determine_risk_level(self, score: float, result: GDPRComplianceResult) -> str:
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
    
    def _calculate_potential_penalties(self, result: GDPRComplianceResult, 
                                     annual_turnover_eur: Optional[Decimal]) -> tuple[Optional[Decimal], Optional[Decimal]]:
        """Calculate potential GDPR penalties in EUR."""
        if result.compliant:
            return None, None
        
        # Determine fine tier based on violations
        tier_2_violations = [
            "Article 6 lawful basis", "Article 9 special categories", 
            "Article 7 consent", "Chapter V transfers"
        ]
        
        use_tier_2 = any(
            any(violation in issue for violation in tier_2_violations)
            for issue in result.critical_issues
        )
        
        if use_tier_2:
            max_fixed = self.administrative_fine_tiers['tier_2_max']
            turnover_percentage = self.administrative_fine_tiers['tier_2_percentage']
        else:
            max_fixed = self.administrative_fine_tiers['tier_1_max']
            turnover_percentage = self.administrative_fine_tiers['tier_1_percentage']
        
        # Calculate turnover-based fine
        turnover_fine = None
        if annual_turnover_eur:
            turnover_fine = annual_turnover_eur * (turnover_percentage / 100)
        
        # Maximum applicable fine
        if turnover_fine:
            max_fine = max(max_fixed, turnover_fine)
        else:
            max_fine = max_fixed
        
        # Estimate potential penalty based on compliance score
        severity_multiplier = max(0.1, (100 - result.compliance_score) / 100)
        potential_penalty = max_fine * Decimal(str(severity_multiplier))
        
        return potential_penalty, max_fine
    
    def _determine_supervisory_authorities(self, 
                                         activities: List[GDPRDataProcessingActivity],
                                         result: GDPRComplianceResult):
        """Determine applicable supervisory authorities."""
        # This is a simplified implementation
        # In practice, this would involve complex jurisdictional analysis
        
        if self.lead_sa:
            result.lead_supervisory_authority = self.lead_sa
        
        # Determine from processing locations and establishments
        eu_countries = set()
        for activity in activities:
            if activity.establishment_in_eu:
                # Would need to parse processing location
                # For now, use a default
                eu_countries.add("ireland")  # Many tech companies use Ireland
        
        result.applicable_member_states = list(eu_countries)
    
    def _generate_recommendations(self, result: GDPRComplianceResult):
        """Generate compliance improvement recommendations."""
        if result.compliance_score < 70:
            result.recommendations.append("Priority: Achieve basic GDPR compliance (70% threshold)")
        
        if len(result.critical_issues) > 0:
            result.recommendations.append("Immediate: Address all critical compliance issues")
        
        if result.article_30_compliance.get('score', 0) < 80:
            result.recommendations.append("Improve Article 30 record-keeping documentation")
        
        if result.consent_compliance.get('score', 0) < 80:
            result.recommendations.append("Enhance consent management processes and record-keeping")
        
        if result.security_compliance.get('score', 0) < 80:
            result.recommendations.append("Strengthen Article 32 technical and organizational measures")
        
        if result.transfer_compliance.get('score', 0) < 100:
            result.recommendations.append("Review international transfer mechanisms and safeguards")
        
        if result.dpia_compliance.get('score', 0) < 100:
            result.recommendations.append("Complete required Data Protection Impact Assessments")
    
    def _create_failed_assessment(self, error_message: str) -> GDPRComplianceResult:
        """Create failed assessment result."""
        return GDPRComplianceResult(
            compliant=False,
            compliance_score=0.0,
            risk_level="critical",
            critical_issues=[f"Assessment failed: {error_message}"],
            assessor="GDPR Compliance Engine",
            next_assessment_due=datetime.now() + timedelta(days=30)
        )
    
    def _validate_article6_lawful_basis(self, activity: GDPRDataProcessingActivity) -> bool:
        """Validate Article 6 lawful basis."""
        if not activity.lawful_basis:
            return False
        
        # Additional validation based on processing type
        if activity.lawful_basis == EuropeanLawfulBasis.LEGITIMATE_INTERESTS:
            # Should have legitimate interests assessment
            # This would be more complex in practice
            pass
        
        return True
    
    def _requires_dpia(self, activity: GDPRDataProcessingActivity) -> bool:
        """Determine if activity requires DPIA under Article 35."""
        # High risk processing indicators
        risk_indicators = 0
        
        # Special category processing
        if activity.special_category_processing:
            risk_indicators += 1
        
        # Large scale processing (simplified heuristic)
        if len(activity.data_categories) > 3:
            risk_indicators += 1
        
        # International transfers to non-adequacy countries
        if activity.international_transfers:
            if activity.transfer_mechanism != TransferMechanism.ADEQUACY_DECISION:
                risk_indicators += 1
        
        # Systematic monitoring (would need more context)
        if 'monitoring' in activity.activity_name.lower():
            risk_indicators += 1
        
        # Automated decision-making (would need more context)
        if 'automated' in activity.activity_name.lower() or 'profiling' in activity.activity_name.lower():
            risk_indicators += 1
        
        return risk_indicators >= 2
    
    def _is_excessive_retention(self, retention_period: str) -> bool:
        """Check if retention period violates storage limitation principle."""
        # Simplified implementation
        if 'indefinite' in retention_period.lower() or 'permanent' in retention_period.lower():
            return True
        
        # Extract years if possible
        if 'year' in retention_period:
            try:
                years = int(''.join(filter(str.isdigit, retention_period)))
                return years > 10  # More than 10 years might be excessive for most purposes
            except ValueError:
                return False
        
        return False