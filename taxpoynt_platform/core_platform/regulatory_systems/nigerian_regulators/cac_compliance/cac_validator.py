"""
CAC Compliance Validator
=======================
Comprehensive validator for CAC (Corporate Affairs Commission) compliance
with Nigerian corporate entity registration and filing requirements.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import (
    CACValidationResult, NigerianEntityInfo, RCValidationResult,
    CACComplianceStatus, EntityRegistration, CACFilingStatus,
    BusinessNameValidation, DirectorInfo, ShareholderInfo,
    EntityType, EntityStatus, ComplianceStatus, FilingType
)

logger = logging.getLogger(__name__)

class CACValidator:
    """
    Comprehensive CAC compliance validator for Nigerian corporate entities
    """
    
    def __init__(self):
        """Initialize CAC validator with Nigerian corporate rules"""
        self.logger = logging.getLogger(__name__)
        
        # CAC validation rules
        self.business_rules = self._load_cac_business_rules()
        self.state_offices = self._load_cac_state_offices()
        self.entity_type_requirements = self._load_entity_type_requirements()
        
        # Filing requirements and deadlines
        self.filing_deadlines = self._load_filing_deadlines()
        self.penalty_rates = self._load_penalty_rates()
        
        # Reserved words and restricted names
        self.reserved_words = self._load_reserved_words()
        self.restricted_suffixes = self._load_restricted_suffixes()
        
        # Minimum capital requirements
        self.minimum_capital_requirements = {
            EntityType.PRIVATE_LIMITED_COMPANY: Decimal('100000'),     # N100,000
            EntityType.PUBLIC_LIMITED_COMPANY: Decimal('2000000'),     # N2,000,000
            EntityType.LIMITED_LIABILITY_PARTNERSHIP: Decimal('500000'), # N500,000
            EntityType.BUSINESS_NAME: Decimal('10000'),                # N10,000
            EntityType.INCORPORATED_TRUSTEES: Decimal('100000')        # N100,000
        }
        
    def validate_rc_number(self, rc_number: str) -> RCValidationResult:
        """
        Validate Nigerian RC (Registration Certificate) number
        
        Args:
            rc_number: RC number to validate
            
        Returns:
            RCValidationResult with validation details
        """
        try:
            self.logger.info(f"Validating RC number: {rc_number}")
            
            # Clean and format RC number
            clean_rc = self._clean_rc_number(rc_number)
            
            # Format validation
            if not self._validate_rc_format(clean_rc):
                return RCValidationResult(
                    rc_number=clean_rc,
                    is_valid=False,
                    error_message="Invalid RC number format. Must be 6-7 digits."
                )
            
            # Registry lookup (placeholder for actual CAC integration)
            registry_result = self._lookup_rc_registry(clean_rc)
            
            return RCValidationResult(
                rc_number=clean_rc,
                is_valid=registry_result['is_valid'],
                entity_name=registry_result.get('entity_name'),
                entity_type=registry_result.get('entity_type'),
                registration_date=registry_result.get('registration_date'),
                registration_state=registry_result.get('registration_state'),
                entity_status=registry_result.get('entity_status'),
                error_message=registry_result.get('error_message')
            )
            
        except Exception as e:
            self.logger.error(f"RC validation failed: {str(e)}")
            return RCValidationResult(
                rc_number=rc_number,
                is_valid=False,
                error_message=f"RC validation error: {str(e)}"
            )
    
    def validate_business_name(self, proposed_name: str, entity_type: EntityType) -> BusinessNameValidation:
        """
        Validate business name availability and format
        
        Args:
            proposed_name: Proposed business name
            entity_type: Type of entity
            
        Returns:
            BusinessNameValidation with validation results
        """
        try:
            self.logger.info(f"Validating business name: {proposed_name}")
            
            validation_result = BusinessNameValidation(
                proposed_name=proposed_name,
                is_available=True,
                is_valid_format=True
            )
            
            # Format validation
            format_issues = self._validate_name_format(proposed_name, entity_type)
            if format_issues:
                validation_result.is_valid_format = False
                validation_result.format_violations = format_issues
            
            # Reserved words check
            reserved_violations = self._check_reserved_words(proposed_name)
            if reserved_violations:
                validation_result.is_valid_format = False
                validation_result.reserved_words_violations = reserved_violations
            
            # Availability check (placeholder for actual CAC search)
            availability_result = self._check_name_availability(proposed_name)
            validation_result.is_available = availability_result['is_available']
            validation_result.similarity_matches = availability_result.get('similar_names', [])
            
            # Generate suggestions if name is not available
            if not validation_result.is_available or not validation_result.is_valid_format:
                validation_result.suggestions = self._generate_name_suggestions(proposed_name, entity_type)
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Business name validation failed: {str(e)}")
            return BusinessNameValidation(
                proposed_name=proposed_name,
                is_available=False,
                is_valid_format=False,
                format_violations=[f"Validation error: {str(e)}"]
            )
    
    def validate_entity_compliance(self, rc_number: str) -> CACValidationResult:
        """
        Comprehensive CAC compliance validation for an entity
        
        Args:
            rc_number: Entity RC number
            
        Returns:
            CACValidationResult with detailed compliance assessment
        """
        try:
            self.logger.info(f"Validating CAC compliance for RC: {rc_number}")
            
            # Initialize result
            result = CACValidationResult(
                rc_number=rc_number,
                is_compliant=True,
                compliance_status=ComplianceStatus.COMPLIANT,
                rc_validation=self.validate_rc_number(rc_number),
                compliance_score=0.0
            )
            
            # If RC is not valid, return early
            if not result.rc_validation.is_valid:
                result.is_compliant = False
                result.compliance_status = ComplianceStatus.NON_COMPLIANT
                result.errors.append("Invalid RC number")
                return result
            
            # Get entity registration details
            result.entity_registration = self._get_entity_registration(rc_number)
            
            # Validate entity structure
            self._validate_entity_structure(result)
            
            # Check filing compliance
            result.filing_status = self._check_filing_compliance(rc_number)
            self._validate_filing_compliance(result)
            
            # Validate directors and shareholders
            self._validate_governance_structure(result)
            
            # Check business rules compliance
            self._validate_business_rules_compliance(result)
            
            # Calculate compliance metrics
            result.compliance_score = self._calculate_compliance_score(result)
            result.filing_compliance_rate = self._calculate_filing_compliance_rate(result)
            
            # Determine final compliance status
            result.compliance_status = self._determine_compliance_status(result)
            result.is_compliant = result.compliance_status in [ComplianceStatus.COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT]
            
            # Generate recommendations
            result.recommendations = self._generate_compliance_recommendations(result)
            result.required_actions = self._generate_required_actions(result)
            
            self.logger.info(f"CAC compliance validation completed. Score: {result.compliance_score}")
            return result
            
        except Exception as e:
            self.logger.error(f"CAC compliance validation failed: {str(e)}")
            return CACValidationResult(
                rc_number=rc_number,
                is_compliant=False,
                compliance_status=ComplianceStatus.NON_COMPLIANT,
                rc_validation=RCValidationResult(rc_number=rc_number, is_valid=False),
                errors=[f"Compliance validation error: {str(e)}"]
            )
    
    def assess_entity_status(self, rc_number: str) -> CACComplianceStatus:
        """
        Assess overall CAC compliance status for an entity
        
        Args:
            rc_number: Entity RC number
            
        Returns:
            CACComplianceStatus with comprehensive status assessment
        """
        try:
            self.logger.info(f"Assessing CAC entity status for RC: {rc_number}")
            
            # Get entity details
            entity_details = self._get_entity_registration(rc_number)
            filing_status = self._check_filing_compliance(rc_number)
            
            # Calculate filing metrics
            total_required = self._count_required_filings(entity_details.entity_type)
            completed = filing_status.annual_return_filed + filing_status.financial_statements_filed
            overdue = self._count_overdue_filings(filing_status)
            
            # Calculate compliance metrics
            completion_rate = (completed / total_required * 100) if total_required > 0 else 100
            compliance_score = self._calculate_entity_compliance_score(entity_details, filing_status)
            
            # Determine risk level
            risk_level, risk_factors = self._assess_compliance_risk(entity_details, filing_status)
            
            # Determine compliance level
            if completion_rate >= 100 and filing_status.outstanding_penalties == 0:
                compliance_level = ComplianceStatus.COMPLIANT
            elif completion_rate >= 80:
                compliance_level = ComplianceStatus.PARTIALLY_COMPLIANT
            elif overdue > 0:
                compliance_level = ComplianceStatus.FILING_OVERDUE
            elif filing_status.outstanding_penalties > 0:
                compliance_level = ComplianceStatus.PENALTIES_OUTSTANDING
            else:
                compliance_level = ComplianceStatus.NON_COMPLIANT
            
            return CACComplianceStatus(
                rc_number=rc_number,
                entity_name=entity_details.entity_name,
                entity_type=entity_details.entity_type,
                current_status=entity_details.entity_status,
                compliance_level=compliance_level,
                last_assessment_date=datetime.now(),
                total_required_filings=total_required,
                completed_filings=completed,
                overdue_filings=overdue,
                pending_filings=max(0, total_required - completed - overdue),
                filing_completion_rate=completion_rate,
                compliance_score=compliance_score,
                total_fees_due=filing_status.outstanding_penalties,
                penalties_outstanding=filing_status.outstanding_penalties,
                risk_level=risk_level,
                risk_factors=risk_factors,
                immediate_actions=self._generate_immediate_actions(filing_status, compliance_level),
                upcoming_deadlines=self._get_upcoming_deadlines(entity_details.entity_type),
                recommendations=self._generate_entity_recommendations(entity_details, filing_status)
            )
            
        except Exception as e:
            self.logger.error(f"Entity status assessment failed: {str(e)}")
            # Return minimal status with error
            return CACComplianceStatus(
                rc_number=rc_number,
                entity_name="Unknown",
                entity_type=EntityType.PRIVATE_LIMITED_COMPANY,
                current_status=EntityStatus.INACTIVE,
                compliance_level=ComplianceStatus.NON_COMPLIANT,
                last_assessment_date=datetime.now(),
                immediate_actions=[f"Assessment error: {str(e)}"]
            )
    
    def validate_director_information(self, director_info: DirectorInfo) -> Dict[str, Any]:
        """
        Validate director information against CAC requirements
        
        Args:
            director_info: Director information to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation_result = {
                'is_valid': True,
                'violations': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Age validation (minimum 18 years)
            if director_info.date_of_birth:
                age = (date.today() - director_info.date_of_birth).days // 365
                if age < 18:
                    validation_result['is_valid'] = False
                    validation_result['violations'].append("Director must be at least 18 years old")
            
            # Nigerian director BVN requirement
            if director_info.nationality.upper() == 'NIGERIAN':
                if not director_info.bvn:
                    validation_result['warnings'].append("BVN is recommended for Nigerian directors")
                if not director_info.nin:
                    validation_result['warnings'].append("NIN is required for Nigerian directors")
            
            # Foreign director requirements
            if director_info.nationality.upper() != 'NIGERIAN':
                if not director_info.passport_number:
                    validation_result['violations'].append("Passport number required for foreign directors")
                    validation_result['is_valid'] = False
            
            # Contact information validation
            if not director_info.phone_number and not director_info.email:
                validation_result['warnings'].append("At least one contact method (phone or email) should be provided")
            
            return validation_result
            
        except Exception as e:
            return {
                'is_valid': False,
                'violations': [f"Director validation error: {str(e)}"],
                'warnings': [],
                'recommendations': []
            }
    
    # Private helper methods
    
    def _clean_rc_number(self, rc_number: str) -> str:
        """Clean and format RC number"""
        if not rc_number:
            return ""
        
        # Remove common prefixes and formatting
        clean = rc_number.upper().replace('RC', '').replace('-', '').replace('/', '').strip()
        return clean
    
    def _validate_rc_format(self, rc_number: str) -> bool:
        """Validate RC number format"""
        if not rc_number:
            return False
        
        # RC numbers are typically 6-7 digits
        return rc_number.isdigit() and 6 <= len(rc_number) <= 7
    
    def _lookup_rc_registry(self, rc_number: str) -> Dict[str, Any]:
        """Lookup RC in CAC registry (placeholder for actual CAC integration)"""
        # This would integrate with actual CAC registry API
        # For now, return mock data based on RC number patterns
        
        if rc_number.startswith('1'):
            return {
                'is_valid': True,
                'entity_name': f'Sample Company {rc_number} Limited',
                'entity_type': EntityType.PRIVATE_LIMITED_COMPANY,
                'registration_date': date(2020, 1, 15),
                'registration_state': 'Lagos',
                'entity_status': EntityStatus.ACTIVE
            }
        elif len(rc_number) == 6:
            return {
                'is_valid': True,
                'entity_name': f'Business Name {rc_number}',
                'entity_type': EntityType.BUSINESS_NAME,
                'registration_date': date(2021, 6, 10),
                'registration_state': 'Abuja',
                'entity_status': EntityStatus.ACTIVE
            }
        else:
            return {
                'is_valid': False,
                'error_message': 'RC number not found in registry'
            }
    
    def _validate_name_format(self, name: str, entity_type: EntityType) -> List[str]:
        """Validate business name format"""
        violations = []
        
        # Length validation
        if len(name) < 3:
            violations.append("Name must be at least 3 characters long")
        elif len(name) > 100:
            violations.append("Name must not exceed 100 characters")
        
        # Character validation
        if not re.match(r'^[a-zA-Z0-9\s\-&\(\)\.]+$', name):
            violations.append("Name contains invalid characters")
        
        # Suffix validation for companies
        if entity_type == EntityType.PRIVATE_LIMITED_COMPANY:
            if not (name.upper().endswith(' LIMITED') or name.upper().endswith(' LTD')):
                violations.append("Private limited company name must end with 'Limited' or 'Ltd'")
        elif entity_type == EntityType.PUBLIC_LIMITED_COMPANY:
            if not name.upper().endswith(' PLC'):
                violations.append("Public limited company name must end with 'Plc'")
        
        # Prohibited patterns
        prohibited_patterns = [
            r'\b(BANK|INSURANCE|MICROFINANCE)\b',  # Financial services
            r'\b(UNIVERSITY|COLLEGE)\b',           # Educational institutions
            r'\b(GOVERNMENT|FEDERAL|STATE)\b'      # Government terms
        ]
        
        for pattern in prohibited_patterns:
            if re.search(pattern, name.upper()):
                violations.append(f"Name contains restricted words requiring special approval")
        
        return violations
    
    def _check_reserved_words(self, name: str) -> List[str]:
        """Check for reserved words in business name"""
        reserved_violations = []
        name_upper = name.upper()
        
        for word in self.reserved_words:
            if word.upper() in name_upper:
                reserved_violations.append(f"Reserved word '{word}' requires CAC approval")
        
        return reserved_violations
    
    def _check_name_availability(self, name: str) -> Dict[str, Any]:
        """Check business name availability (placeholder)"""
        # This would integrate with actual CAC name search API
        
        # Simulate availability check
        import hashlib
        name_hash = int(hashlib.md5(name.encode()).hexdigest()[:8], 16)
        
        # 80% chance of availability
        is_available = (name_hash % 10) < 8
        
        similar_names = []
        if not is_available:
            similar_names = [
                f"{name} Limited",
                f"{name} Nigeria Limited",
                f"New {name} Limited"
            ]
        
        return {
            'is_available': is_available,
            'similar_names': similar_names
        }
    
    def _generate_name_suggestions(self, original_name: str, entity_type: EntityType) -> List[str]:
        """Generate alternative name suggestions"""
        suggestions = []
        
        base_name = original_name.replace(' Limited', '').replace(' Ltd', '').replace(' Plc', '')
        
        # Add geographical variations
        suggestions.extend([
            f"{base_name} Nigeria Limited",
            f"{base_name} West Africa Limited",
            f"New {base_name} Limited"
        ])
        
        # Add descriptive variations
        suggestions.extend([
            f"{base_name} Enterprises Limited",
            f"{base_name} Global Limited",
            f"{base_name} International Limited"
        ])
        
        # Ensure proper suffix for entity type
        if entity_type == EntityType.PUBLIC_LIMITED_COMPANY:
            suggestions = [s.replace(' Limited', ' Plc') for s in suggestions]
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _get_entity_registration(self, rc_number: str) -> EntityRegistration:
        """Get complete entity registration details (placeholder)"""
        # This would query actual CAC database
        
        rc_result = self.validate_rc_number(rc_number)
        
        return EntityRegistration(
            rc_number=rc_number,
            entity_name=rc_result.entity_name or f"Entity {rc_number}",
            entity_type=rc_result.entity_type or EntityType.PRIVATE_LIMITED_COMPANY,
            registration_date=rc_result.registration_date or date(2020, 1, 1),
            registration_state=rc_result.registration_state or "Lagos",
            registered_address="Sample Address, Lagos, Nigeria",
            authorized_share_capital=Decimal('1000000'),
            issued_share_capital=Decimal('500000'),
            paid_up_share_capital=Decimal('500000'),
            principal_business_activity="General Trading",
            entity_status=rc_result.entity_status or EntityStatus.ACTIVE
        )
    
    def _check_filing_compliance(self, rc_number: str) -> CACFilingStatus:
        """Check entity filing compliance status (placeholder)"""
        current_year = date.today().year
        
        # Mock filing status
        return CACFilingStatus(
            rc_number=rc_number,
            entity_name=f"Entity {rc_number}",
            filing_year=current_year,
            annual_return_filed=True,
            annual_return_due_date=date(current_year, 6, 30),
            annual_return_filed_date=date(current_year, 5, 15),
            financial_statements_filed=False,
            financial_statements_due_date=date(current_year, 9, 30),
            total_penalties=Decimal('50000'),
            outstanding_penalties=Decimal('25000'),
            is_compliant=False,
            compliance_issues=["Financial statements overdue"],
            next_filing_due_date=date(current_year, 9, 30)
        )
    
    def _validate_entity_structure(self, result: CACValidationResult):
        """Validate entity structure requirements"""
        if not result.entity_registration:
            result.errors.append("Entity registration details not available")
            return
        
        entity = result.entity_registration
        
        # Capital requirements validation
        min_capital = self.minimum_capital_requirements.get(entity.entity_type, Decimal('0'))
        if entity.authorized_share_capital < min_capital:
            result.failed_checks.append(f"CAPITAL_REQ_001: Insufficient authorized capital")
            result.errors.append(f"Authorized capital below minimum requirement of ₦{min_capital:,}")
        else:
            result.passed_checks.append("CAPITAL_REQ_001: Authorized capital meets requirements")
        
        # Paid up capital validation
        if entity.paid_up_share_capital > entity.issued_share_capital:
            result.failed_checks.append("CAPITAL_REQ_002: Paid up capital exceeds issued capital")
            result.errors.append("Paid up share capital cannot exceed issued share capital")
        else:
            result.passed_checks.append("CAPITAL_REQ_002: Share capital structure is valid")
    
    def _validate_filing_compliance(self, result: CACValidationResult):
        """Validate filing compliance"""
        if not result.filing_status:
            result.warnings.append("Filing status information not available")
            return
        
        filing = result.filing_status
        
        # Annual return compliance
        if filing.annual_return_filed:
            result.passed_checks.append("FILING_001: Annual return filed")
        else:
            result.failed_checks.append("FILING_001: Annual return not filed")
            result.errors.append("Annual return filing is overdue")
        
        # Financial statements compliance
        if filing.financial_statements_filed:
            result.passed_checks.append("FILING_002: Financial statements filed")
        else:
            result.failed_checks.append("FILING_002: Financial statements not filed")
            if filing.financial_statements_due_date and filing.financial_statements_due_date < date.today():
                result.errors.append("Financial statements filing is overdue")
            else:
                result.warnings.append("Financial statements filing due soon")
        
        # Penalties check
        if filing.outstanding_penalties > 0:
            result.failed_checks.append("PENALTY_001: Outstanding penalties exist")
            result.errors.append(f"Outstanding penalties: ₦{filing.outstanding_penalties:,}")
        else:
            result.passed_checks.append("PENALTY_001: No outstanding penalties")
    
    def _validate_governance_structure(self, result: CACValidationResult):
        """Validate directors and shareholders structure"""
        if not result.entity_registration:
            return
        
        entity = result.entity_registration
        
        # Directors validation
        if not entity.directors:
            result.warnings.append("Director information not available for validation")
        else:
            # Minimum directors requirement
            if entity.entity_type == EntityType.PUBLIC_LIMITED_COMPANY and len(entity.directors) < 2:
                result.failed_checks.append("GOV_001: Insufficient directors for public company")
                result.errors.append("Public limited company requires minimum 2 directors")
            else:
                result.passed_checks.append("GOV_001: Adequate number of directors")
            
            # Nigerian director requirement
            nigerian_directors = [d for d in entity.directors if d.nationality.upper() == 'NIGERIAN']
            if not nigerian_directors:
                result.failed_checks.append("GOV_002: No Nigerian director found")
                result.errors.append("At least one director must be Nigerian")
            else:
                result.passed_checks.append("GOV_002: Nigerian director requirement met")
    
    def _validate_business_rules_compliance(self, result: CACValidationResult):
        """Validate business rules compliance"""
        # Address validation
        if result.entity_registration and result.entity_registration.registered_address:
            if len(result.entity_registration.registered_address.strip()) < 10:
                result.failed_checks.append("ADDR_001: Incomplete registered address")
                result.warnings.append("Registered address appears incomplete")
            else:
                result.passed_checks.append("ADDR_001: Registered address provided")
        
        # Business activity validation
        if result.entity_registration and not result.entity_registration.principal_business_activity:
            result.failed_checks.append("BIZ_001: Principal business activity not specified")
            result.warnings.append("Principal business activity should be specified")
        else:
            result.passed_checks.append("BIZ_001: Principal business activity specified")
    
    def _calculate_compliance_score(self, result: CACValidationResult) -> float:
        """Calculate overall compliance score"""
        total_checks = len(result.passed_checks) + len(result.failed_checks)
        if total_checks == 0:
            return 0.0
        
        passed_checks = len(result.passed_checks)
        base_score = (passed_checks / total_checks) * 100
        
        # Penalty deductions
        penalty_deduction = min(len(result.errors) * 10, 50)  # Max 50 points deduction
        warning_deduction = min(len(result.warnings) * 2, 20)  # Max 20 points deduction
        
        final_score = max(0, base_score - penalty_deduction - warning_deduction)
        return round(final_score, 2)
    
    def _calculate_filing_compliance_rate(self, result: CACValidationResult) -> float:
        """Calculate filing compliance rate"""
        if not result.filing_status:
            return 0.0
        
        filing = result.filing_status
        total_filings = 2  # Annual return + Financial statements
        completed_filings = 0
        
        if filing.annual_return_filed:
            completed_filings += 1
        if filing.financial_statements_filed:
            completed_filings += 1
        
        return (completed_filings / total_filings) * 100
    
    def _determine_compliance_status(self, result: CACValidationResult) -> ComplianceStatus:
        """Determine final compliance status"""
        if result.errors:
            if len(result.errors) > 3:
                return ComplianceStatus.NON_COMPLIANT
            else:
                return ComplianceStatus.PARTIALLY_COMPLIANT
        elif result.warnings:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        elif result.filing_status and result.filing_status.outstanding_penalties > 0:
            return ComplianceStatus.PENALTIES_OUTSTANDING
        elif result.filing_status and not result.filing_status.is_compliant:
            return ComplianceStatus.FILING_OVERDUE
        else:
            return ComplianceStatus.COMPLIANT
    
    def _generate_compliance_recommendations(self, result: CACValidationResult) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if result.errors:
            recommendations.append("Address all compliance errors immediately")
        
        if result.warnings:
            recommendations.append("Review and resolve compliance warnings")
        
        if result.filing_status and result.filing_status.outstanding_penalties > 0:
            recommendations.append("Pay outstanding penalties to avoid further sanctions")
        
        if result.filing_status and not result.filing_status.financial_statements_filed:
            recommendations.append("Submit financial statements to avoid penalties")
        
        if result.compliance_score < 80:
            recommendations.append("Improve compliance practices and documentation")
        
        return recommendations
    
    def _generate_required_actions(self, result: CACValidationResult) -> List[str]:
        """Generate required compliance actions"""
        actions = []
        
        for error in result.errors:
            if "capital" in error.lower():
                actions.append("Increase authorized share capital to meet minimum requirements")
            elif "director" in error.lower():
                actions.append("Appoint required directors to meet governance requirements")
            elif "filing" in error.lower():
                actions.append("Submit overdue filings immediately")
            elif "penalty" in error.lower():
                actions.append("Pay outstanding penalties")
        
        return actions
    
    # Helper methods for entity status assessment
    
    def _count_required_filings(self, entity_type: EntityType) -> int:
        """Count required annual filings for entity type"""
        base_filings = 2  # Annual return + Financial statements
        
        if entity_type == EntityType.PUBLIC_LIMITED_COMPANY:
            return base_filings + 1  # Additional regulatory filings
        
        return base_filings
    
    def _count_overdue_filings(self, filing_status: CACFilingStatus) -> int:
        """Count overdue filings"""
        overdue = 0
        today = date.today()
        
        if not filing_status.annual_return_filed and filing_status.annual_return_due_date and filing_status.annual_return_due_date < today:
            overdue += 1
        
        if not filing_status.financial_statements_filed and filing_status.financial_statements_due_date and filing_status.financial_statements_due_date < today:
            overdue += 1
        
        return overdue
    
    def _calculate_entity_compliance_score(self, entity: EntityRegistration, filing: CACFilingStatus) -> float:
        """Calculate entity compliance score"""
        score = 100.0
        
        # Filing compliance (50% weight)
        filing_score = 0
        if filing.annual_return_filed:
            filing_score += 25
        if filing.financial_statements_filed:
            filing_score += 25
        
        # Penalty compliance (30% weight)
        penalty_score = 30
        if filing.outstanding_penalties > 0:
            penalty_score = max(0, 30 - (float(filing.outstanding_penalties) / 10000))
        
        # Structure compliance (20% weight)
        structure_score = 20
        if entity.entity_status != EntityStatus.ACTIVE:
            structure_score = 10
        
        final_score = filing_score + penalty_score + structure_score
        return round(final_score, 2)
    
    def _assess_compliance_risk(self, entity: EntityRegistration, filing: CACFilingStatus) -> Tuple[str, List[str]]:
        """Assess compliance risk level"""
        risk_factors = []
        
        if filing.outstanding_penalties > Decimal('100000'):
            risk_factors.append("High outstanding penalties")
        
        if not filing.annual_return_filed:
            risk_factors.append("Annual return not filed")
        
        if not filing.financial_statements_filed:
            risk_factors.append("Financial statements not filed")
        
        if entity.entity_status != EntityStatus.ACTIVE:
            risk_factors.append("Entity status is not active")
        
        # Determine risk level
        if len(risk_factors) >= 3:
            risk_level = "high"
        elif len(risk_factors) >= 1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return risk_level, risk_factors
    
    def _generate_immediate_actions(self, filing: CACFilingStatus, compliance_level: ComplianceStatus) -> List[str]:
        """Generate immediate required actions"""
        actions = []
        
        if compliance_level == ComplianceStatus.FILING_OVERDUE:
            if not filing.annual_return_filed:
                actions.append("Submit annual return immediately")
            if not filing.financial_statements_filed:
                actions.append("Submit financial statements immediately")
        
        if filing.outstanding_penalties > 0:
            actions.append(f"Pay outstanding penalties of ₦{filing.outstanding_penalties:,}")
        
        return actions
    
    def _get_upcoming_deadlines(self, entity_type: EntityType) -> List[Dict[str, Any]]:
        """Get upcoming filing deadlines"""
        current_year = date.today().year
        
        deadlines = [
            {
                'filing_type': 'Annual Return',
                'due_date': date(current_year + 1, 6, 30),
                'days_remaining': (date(current_year + 1, 6, 30) - date.today()).days
            },
            {
                'filing_type': 'Financial Statements',
                'due_date': date(current_year + 1, 9, 30),
                'days_remaining': (date(current_year + 1, 9, 30) - date.today()).days
            }
        ]
        
        return [d for d in deadlines if d['days_remaining'] > 0]
    
    def _generate_entity_recommendations(self, entity: EntityRegistration, filing: CACFilingStatus) -> List[str]:
        """Generate entity-specific recommendations"""
        recommendations = []
        
        if not filing.is_compliant:
            recommendations.append("Ensure all filings are submitted on time")
        
        if filing.outstanding_penalties > 0:
            recommendations.append("Set up payment plan for outstanding penalties")
        
        if entity.entity_status == EntityStatus.ACTIVE:
            recommendations.append("Maintain good standing through timely compliance")
        
        recommendations.append("Consider setting up automated compliance reminders")
        
        return recommendations
    
    # Configuration methods
    
    def _load_cac_business_rules(self) -> List[Dict[str, Any]]:
        """Load CAC business rules"""
        return [
            {
                'rule_id': 'CAC_001',
                'category': 'CAPITAL_REQUIREMENTS',
                'description': 'Minimum capital requirements for entity types',
                'applies_to': ['private_limited_company', 'public_limited_company']
            },
            {
                'rule_id': 'CAC_002',
                'category': 'DIRECTOR_REQUIREMENTS',
                'description': 'Director nationality and minimum requirements',
                'applies_to': ['all_companies']
            },
            {
                'rule_id': 'CAC_003',
                'category': 'FILING_REQUIREMENTS',
                'description': 'Annual filing obligations',
                'applies_to': ['all_entities']
            }
        ]
    
    def _load_cac_state_offices(self) -> Dict[str, str]:
        """Load CAC state office locations"""
        return {
            'LAGOS': 'Lagos State Office',
            'ABUJA': 'Federal Capital Territory Office',
            'KANO': 'Kano State Office',
            'RIVERS': 'Port Harcourt Office',
            'OGUN': 'Abeokuta Office',
            'ANAMBRA': 'Awka Office'
        }
    
    def _load_entity_type_requirements(self) -> Dict[EntityType, Dict[str, Any]]:
        """Load entity type specific requirements"""
        return {
            EntityType.PRIVATE_LIMITED_COMPANY: {
                'min_directors': 1,
                'min_shareholders': 1,
                'max_shareholders': 50,
                'nigerian_director_required': True,
                'name_suffix': ['Limited', 'Ltd']
            },
            EntityType.PUBLIC_LIMITED_COMPANY: {
                'min_directors': 2,
                'min_shareholders': 2,
                'max_shareholders': None,
                'nigerian_director_required': True,
                'name_suffix': ['Plc']
            },
            EntityType.BUSINESS_NAME: {
                'min_directors': 0,
                'min_shareholders': 0,
                'max_shareholders': None,
                'nigerian_director_required': False,
                'name_suffix': []
            }
        }
    
    def _load_filing_deadlines(self) -> Dict[str, Dict[str, Any]]:
        """Load filing deadlines configuration"""
        return {
            'annual_return': {
                'due_date': '30-Jun',
                'penalty_per_month': Decimal('10000'),
                'grace_period_days': 30
            },
            'financial_statements': {
                'due_date': '30-Sep',
                'penalty_per_month': Decimal('25000'),
                'grace_period_days': 0
            }
        }
    
    def _load_penalty_rates(self) -> Dict[str, Decimal]:
        """Load penalty rates for late filings"""
        return {
            'annual_return_monthly': Decimal('10000'),
            'financial_statements_monthly': Decimal('25000'),
            'change_of_directors': Decimal('5000'),
            'change_of_address': Decimal('2000')
        }
    
    def _load_reserved_words(self) -> List[str]:
        """Load reserved words requiring special approval"""
        return [
            'BANK', 'BANKING', 'INSURANCE', 'ASSURANCE', 'REINSURANCE',
            'MICROFINANCE', 'MORTGAGE', 'UNIVERSITY', 'POLYTECHNIC',
            'COLLEGE', 'FEDERAL', 'NATIONAL', 'STATE', 'GOVERNMENT',
            'MINISTRY', 'COMMISSION', 'AGENCY', 'AUTHORITY', 'BOARD',
            'COOPERATIVE', 'SOCIETY', 'ASSOCIATION', 'FOUNDATION',
            'TRUST', 'CHAMBER', 'STOCK', 'EXCHANGE', 'SECURITIES'
        ]
    
    def _load_restricted_suffixes(self) -> List[str]:
        """Load restricted name suffixes"""
        return [
            'LIMITED', 'LTD', 'PLC', 'LLP', 'LP', 'INC', 'CORP',
            'COMPANY', 'CO', 'ENTERPRISES', 'GROUP', 'HOLDINGS'
        ]