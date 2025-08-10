"""
Nigerian Corporate Entity Validator
==================================
Specialized validator for Nigerian corporate entities with focus on structure validation,
governance compliance, and regulatory requirements specific to different entity types.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import (
    EntityRegistration, DirectorInfo, ShareholderInfo, EntityType,
    EntityStatus, DirectorType, ShareholderType
)

logger = logging.getLogger(__name__)

class NigerianEntityValidator:
    """
    Specialized validator for Nigerian corporate entity structures and governance
    """
    
    def __init__(self):
        """Initialize Nigerian entity validator"""
        self.logger = logging.getLogger(__name__)
        
        # Load entity-specific rules
        self.governance_rules = self._load_governance_rules()
        self.capital_structure_rules = self._load_capital_structure_rules()
        self.director_requirements = self._load_director_requirements()
        self.shareholder_rules = self._load_shareholder_rules()
        
        # Nigerian regulatory limits
        self.foreign_ownership_limits = {
            EntityType.PRIVATE_LIMITED_COMPANY: Decimal('100'),  # No limit
            EntityType.PUBLIC_LIMITED_COMPANY: Decimal('100'),   # No limit
            EntityType.BUSINESS_NAME: Decimal('100')             # No limit
        }
        
        # Sector-specific foreign ownership restrictions
        self.restricted_sectors = {
            'telecommunications': Decimal('60'),
            'banking': Decimal('70'),
            'insurance': Decimal('49'),
            'oil_and_gas': Decimal('40'),
            'media': Decimal('30')
        }
    
    def validate_entity_structure(self, entity: EntityRegistration) -> Dict[str, Any]:
        """
        Comprehensive validation of entity structure
        
        Args:
            entity: EntityRegistration to validate
            
        Returns:
            Dictionary with detailed validation results
        """
        try:
            self.logger.info(f"Validating entity structure for RC: {entity.rc_number}")
            
            validation_result = {
                'is_valid': True,
                'entity_type': entity.entity_type,
                'violations': [],
                'warnings': [],
                'recommendations': [],
                'compliance_score': 0.0,
                'structure_analysis': {}
            }
            
            # Validate by entity type
            if entity.entity_type == EntityType.PRIVATE_LIMITED_COMPANY:
                self._validate_private_limited_company(entity, validation_result)
            elif entity.entity_type == EntityType.PUBLIC_LIMITED_COMPANY:
                self._validate_public_limited_company(entity, validation_result)
            elif entity.entity_type == EntityType.LIMITED_LIABILITY_PARTNERSHIP:
                self._validate_llp(entity, validation_result)
            elif entity.entity_type == EntityType.BUSINESS_NAME:
                self._validate_business_name(entity, validation_result)
            elif entity.entity_type == EntityType.INCORPORATED_TRUSTEES:
                self._validate_incorporated_trustees(entity, validation_result)
            
            # Common validations for all entity types
            self._validate_capital_structure(entity, validation_result)
            self._validate_directors_structure(entity, validation_result)
            self._validate_shareholders_structure(entity, validation_result)
            self._validate_foreign_ownership(entity, validation_result)
            
            # Calculate compliance score
            validation_result['compliance_score'] = self._calculate_structure_score(validation_result)
            
            # Generate structure analysis
            validation_result['structure_analysis'] = self._analyze_entity_structure(entity)
            
            self.logger.info(f"Entity structure validation completed. Score: {validation_result['compliance_score']}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Entity structure validation failed: {str(e)}")
            return {
                'is_valid': False,
                'violations': [f"Structure validation error: {str(e)}"],
                'warnings': [],
                'recommendations': [],
                'compliance_score': 0.0,
                'structure_analysis': {}
            }
    
    def validate_governance_compliance(self, entity: EntityRegistration) -> Dict[str, Any]:
        """
        Validate corporate governance compliance
        
        Args:
            entity: EntityRegistration to validate
            
        Returns:
            Dictionary with governance validation results
        """
        try:
            self.logger.info(f"Validating governance compliance for RC: {entity.rc_number}")
            
            governance_result = {
                'is_compliant': True,
                'governance_score': 0.0,
                'board_composition': {},
                'violations': [],
                'recommendations': [],
                'best_practices': []
            }
            
            # Validate board composition
            self._validate_board_composition(entity, governance_result)
            
            # Validate director qualifications
            self._validate_director_qualifications(entity, governance_result)
            
            # Validate independence requirements
            self._validate_director_independence(entity, governance_result)
            
            # Validate key positions
            self._validate_key_positions(entity, governance_result)
            
            # Calculate governance score
            governance_result['governance_score'] = self._calculate_governance_score(governance_result)
            
            return governance_result
            
        except Exception as e:
            self.logger.error(f"Governance validation failed: {str(e)}")
            return {
                'is_compliant': False,
                'governance_score': 0.0,
                'violations': [f"Governance validation error: {str(e)}"],
                'recommendations': [],
                'best_practices': []
            }
    
    def validate_capital_adequacy(self, entity: EntityRegistration) -> Dict[str, Any]:
        """
        Validate capital adequacy and structure
        
        Args:
            entity: EntityRegistration to validate
            
        Returns:
            Dictionary with capital validation results
        """
        try:
            capital_result = {
                'is_adequate': True,
                'capital_analysis': {},
                'violations': [],
                'recommendations': []
            }
            
            # Minimum capital requirements
            min_capital = self._get_minimum_capital_requirement(entity.entity_type)
            if entity.authorized_share_capital < min_capital:
                capital_result['is_adequate'] = False
                capital_result['violations'].append(
                    f"Authorized capital (₦{entity.authorized_share_capital:,}) below minimum requirement (₦{min_capital:,})"
                )
            
            # Capital structure ratios
            capital_analysis = {
                'authorized_capital': entity.authorized_share_capital,
                'issued_capital': entity.issued_share_capital,
                'paid_up_capital': entity.paid_up_share_capital,
                'issued_to_authorized_ratio': (entity.issued_share_capital / entity.authorized_share_capital * 100) if entity.authorized_share_capital > 0 else 0,
                'paid_up_to_issued_ratio': (entity.paid_up_share_capital / entity.issued_share_capital * 100) if entity.issued_share_capital > 0 else 0
            }
            
            capital_result['capital_analysis'] = capital_analysis
            
            # Validate capital structure consistency
            if entity.issued_share_capital > entity.authorized_share_capital:
                capital_result['violations'].append("Issued capital cannot exceed authorized capital")
                capital_result['is_adequate'] = False
            
            if entity.paid_up_share_capital > entity.issued_share_capital:
                capital_result['violations'].append("Paid up capital cannot exceed issued capital")
                capital_result['is_adequate'] = False
            
            # Recommendations for capital optimization
            if capital_analysis['paid_up_to_issued_ratio'] < 25:
                capital_result['recommendations'].append("Consider increasing paid up capital for better financial standing")
            
            return capital_result
            
        except Exception as e:
            self.logger.error(f"Capital validation failed: {str(e)}")
            return {
                'is_adequate': False,
                'violations': [f"Capital validation error: {str(e)}"],
                'recommendations': [],
                'capital_analysis': {}
            }
    
    def analyze_ownership_structure(self, entity: EntityRegistration) -> Dict[str, Any]:
        """
        Analyze shareholding and ownership structure
        
        Args:
            entity: EntityRegistration to analyze
            
        Returns:
            Dictionary with ownership analysis
        """
        try:
            ownership_analysis = {
                'total_shareholders': len(entity.shareholders),
                'ownership_distribution': {},
                'foreign_ownership_percentage': 0.0,
                'concentrated_ownership': False,
                'majority_shareholder': None,
                'ownership_compliance': True,
                'issues': []
            }
            
            if not entity.shareholders:
                ownership_analysis['issues'].append("No shareholder information available")
                return ownership_analysis
            
            # Calculate ownership distribution
            total_shares = sum(sh.shares_held for sh in entity.shareholders)
            ownership_dist = {}
            foreign_shares = 0
            
            for shareholder in entity.shareholders:
                percentage = (shareholder.shares_held / total_shares * 100) if total_shares > 0 else 0
                ownership_dist[shareholder.name] = {
                    'shares': shareholder.shares_held,
                    'percentage': percentage,
                    'shareholder_type': shareholder.shareholder_type,
                    'nationality': shareholder.nationality
                }
                
                # Track foreign ownership
                if shareholder.nationality.upper() != 'NIGERIAN':
                    foreign_shares += shareholder.shares_held
            
            ownership_analysis['ownership_distribution'] = ownership_dist
            ownership_analysis['foreign_ownership_percentage'] = (foreign_shares / total_shares * 100) if total_shares > 0 else 0
            
            # Find majority shareholder
            max_percentage = 0
            majority_holder = None
            for name, details in ownership_dist.items():
                if details['percentage'] > max_percentage:
                    max_percentage = details['percentage']
                    majority_holder = name
            
            if max_percentage > 50:
                ownership_analysis['majority_shareholder'] = {
                    'name': majority_holder,
                    'percentage': max_percentage
                }
            
            # Check for concentrated ownership (top 3 shareholders own >75%)
            sorted_shareholders = sorted(ownership_dist.items(), key=lambda x: x[1]['percentage'], reverse=True)
            top_3_percentage = sum(sh[1]['percentage'] for sh in sorted_shareholders[:3])
            ownership_analysis['concentrated_ownership'] = top_3_percentage > 75
            
            # Validate foreign ownership limits
            sector_limit = self.foreign_ownership_limits.get(entity.entity_type, Decimal('100'))
            if ownership_analysis['foreign_ownership_percentage'] > float(sector_limit):
                ownership_analysis['ownership_compliance'] = False
                ownership_analysis['issues'].append(
                    f"Foreign ownership ({ownership_analysis['foreign_ownership_percentage']:.1f}%) exceeds limit ({sector_limit}%)"
                )
            
            return ownership_analysis
            
        except Exception as e:
            self.logger.error(f"Ownership analysis failed: {str(e)}")
            return {
                'total_shareholders': 0,
                'ownership_compliance': False,
                'issues': [f"Ownership analysis error: {str(e)}"]
            }
    
    # Private validation methods for specific entity types
    
    def _validate_private_limited_company(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate Private Limited Company specific requirements"""
        requirements = self.director_requirements[EntityType.PRIVATE_LIMITED_COMPANY]
        
        # Director requirements
        if len(entity.directors) < requirements['min_directors']:
            result['violations'].append(f"Minimum {requirements['min_directors']} director(s) required")
            result['is_valid'] = False
        
        # Shareholder limits
        if len(entity.shareholders) > 50:
            result['violations'].append("Private limited company cannot have more than 50 shareholders")
            result['is_valid'] = False
        
        # Name suffix validation
        if not (entity.entity_name.upper().endswith(' LIMITED') or entity.entity_name.upper().endswith(' LTD')):
            result['violations'].append("Company name must end with 'Limited' or 'Ltd'")
            result['is_valid'] = False
    
    def _validate_public_limited_company(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate Public Limited Company specific requirements"""
        requirements = self.director_requirements[EntityType.PUBLIC_LIMITED_COMPANY]
        
        # Director requirements
        if len(entity.directors) < requirements['min_directors']:
            result['violations'].append(f"Minimum {requirements['min_directors']} directors required")
            result['is_valid'] = False
        
        # Shareholder requirements
        if len(entity.shareholders) < 2:
            result['violations'].append("Public limited company requires minimum 2 shareholders")
            result['is_valid'] = False
        
        # Name suffix validation
        if not entity.entity_name.upper().endswith(' PLC'):
            result['violations'].append("Public company name must end with 'Plc'")
            result['is_valid'] = False
        
        # Additional requirements for public companies
        company_secretary = any(d.director_type == DirectorType.COMPANY_SECRETARY for d in entity.directors)
        if not company_secretary:
            result['warnings'].append("Public company should have a qualified company secretary")
    
    def _validate_llp(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate Limited Liability Partnership requirements"""
        # LLP requires minimum 2 partners
        if len(entity.shareholders) < 2:
            result['violations'].append("LLP requires minimum 2 partners")
            result['is_valid'] = False
        
        # Name suffix validation
        if not entity.entity_name.upper().endswith(' LLP'):
            result['violations'].append("LLP name must end with 'LLP'")
            result['is_valid'] = False
    
    def _validate_business_name(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate Business Name requirements"""
        # Business names have fewer structural requirements
        if entity.entity_name.upper().endswith((' LIMITED', ' LTD', ' PLC')):
            result['violations'].append("Business name cannot use corporate suffixes")
            result['is_valid'] = False
    
    def _validate_incorporated_trustees(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate Incorporated Trustees (NGO) requirements"""
        # IT requires minimum 3 trustees
        if len(entity.directors) < 3:
            result['violations'].append("Incorporated Trustees requires minimum 3 trustees")
            result['is_valid'] = False
        
        # Non-profit nature validation
        if entity.authorized_share_capital > Decimal('1000000'):
            result['warnings'].append("High authorized capital unusual for non-profit organization")
    
    def _validate_capital_structure(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate capital structure consistency"""
        # Capital hierarchy validation
        if entity.issued_share_capital > entity.authorized_share_capital:
            result['violations'].append("Issued capital exceeds authorized capital")
            result['is_valid'] = False
        
        if entity.paid_up_share_capital > entity.issued_share_capital:
            result['violations'].append("Paid up capital exceeds issued capital")
            result['is_valid'] = False
        
        # Minimum capital requirements
        min_capital = self._get_minimum_capital_requirement(entity.entity_type)
        if entity.authorized_share_capital < min_capital:
            result['violations'].append(f"Authorized capital below minimum requirement of ₦{min_capital:,}")
            result['is_valid'] = False
    
    def _validate_directors_structure(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate directors structure"""
        if not entity.directors:
            result['warnings'].append("No director information available")
            return
        
        # Nigerian director requirement
        nigerian_directors = [d for d in entity.directors if d.nationality.upper() == 'NIGERIAN']
        if not nigerian_directors and entity.entity_type != EntityType.BUSINESS_NAME:
            result['violations'].append("At least one director must be Nigerian")
            result['is_valid'] = False
        
        # Age validation
        for director in entity.directors:
            if director.date_of_birth:
                age = (date.today() - director.date_of_birth).days // 365
                if age < 18:
                    result['violations'].append(f"Director {director.full_name} is below minimum age of 18")
                    result['is_valid'] = False
        
        # Active status validation
        active_directors = [d for d in entity.directors if d.is_active]
        if len(active_directors) == 0:
            result['violations'].append("No active directors found")
            result['is_valid'] = False
    
    def _validate_shareholders_structure(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate shareholders structure"""
        if not entity.shareholders:
            result['warnings'].append("No shareholder information available")
            return
        
        # Shareholding percentage validation
        total_percentage = sum(sh.share_percentage for sh in entity.shareholders)
        if abs(total_percentage - 100) > 0.01:  # Allow for rounding errors
            result['violations'].append(f"Shareholding percentages do not sum to 100% (current: {total_percentage}%)")
            result['is_valid'] = False
        
        # Share count consistency
        total_shares_held = sum(sh.shares_held for sh in entity.shareholders)
        if total_shares_held > entity.issued_share_capital:
            result['violations'].append("Total shares held exceeds issued share capital")
            result['is_valid'] = False
    
    def _validate_foreign_ownership(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate foreign ownership compliance"""
        if not entity.shareholders:
            return
        
        total_shares = sum(sh.shares_held for sh in entity.shareholders)
        foreign_shares = sum(sh.shares_held for sh in entity.shareholders if sh.nationality.upper() != 'NIGERIAN')
        
        foreign_percentage = (foreign_shares / total_shares * 100) if total_shares > 0 else 0
        
        # Check general foreign ownership limits
        entity_limit = self.foreign_ownership_limits.get(entity.entity_type, Decimal('100'))
        if foreign_percentage > float(entity_limit):
            result['violations'].append(
                f"Foreign ownership ({foreign_percentage:.1f}%) exceeds limit ({entity_limit}%)"
            )
            result['is_valid'] = False
        
        # Sector-specific checks would go here
        # This would require additional business activity classification
    
    def _validate_board_composition(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate board composition requirements"""
        if not entity.directors:
            result['violations'].append("No board composition available")
            return
        
        board_composition = {
            'total_directors': len(entity.directors),
            'executive_directors': 0,
            'non_executive_directors': 0,
            'independent_directors': 0,
            'nigerian_directors': 0,
            'foreign_directors': 0
        }
        
        for director in entity.directors:
            if director.director_type == DirectorType.EXECUTIVE_DIRECTOR:
                board_composition['executive_directors'] += 1
            elif director.director_type == DirectorType.NON_EXECUTIVE_DIRECTOR:
                board_composition['non_executive_directors'] += 1
            elif director.director_type == DirectorType.INDEPENDENT_DIRECTOR:
                board_composition['independent_directors'] += 1
            
            if director.nationality.upper() == 'NIGERIAN':
                board_composition['nigerian_directors'] += 1
            else:
                board_composition['foreign_directors'] += 1
        
        result['board_composition'] = board_composition
        
        # Validate composition requirements for public companies
        if entity.entity_type == EntityType.PUBLIC_LIMITED_COMPANY:
            total_directors = board_composition['total_directors']
            independent_directors = board_composition['independent_directors']
            
            if total_directors >= 3 and independent_directors == 0:
                result['recommendations'].append("Consider appointing independent directors for better governance")
    
    def _validate_director_qualifications(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate director qualifications"""
        for director in entity.directors:
            # Nigerian directors should have BVN/NIN
            if director.nationality.upper() == 'NIGERIAN':
                if not director.bvn and not director.nin:
                    result['recommendations'].append(f"Nigerian director {director.full_name} should provide BVN or NIN")
            
            # Foreign directors should have passport
            if director.nationality.upper() != 'NIGERIAN' and not director.passport_number:
                result['violations'].append(f"Foreign director {director.full_name} must provide passport number")
    
    def _validate_director_independence(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate director independence requirements"""
        # This would implement independence criteria based on Nigerian corporate governance codes
        independent_count = sum(1 for d in entity.directors if d.director_type == DirectorType.INDEPENDENT_DIRECTOR)
        
        if entity.entity_type == EntityType.PUBLIC_LIMITED_COMPANY and len(entity.directors) >= 5:
            if independent_count < 2:
                result['recommendations'].append("Consider appointing at least 2 independent directors")
    
    def _validate_key_positions(self, entity: EntityRegistration, result: Dict[str, Any]):
        """Validate key management positions"""
        has_chairman = any(d.director_type == DirectorType.CHAIRMAN for d in entity.directors)
        has_md = any(d.director_type == DirectorType.MANAGING_DIRECTOR for d in entity.directors)
        has_secretary = any(d.director_type == DirectorType.COMPANY_SECRETARY for d in entity.directors)
        
        if not has_chairman:
            result['recommendations'].append("Consider appointing a Board Chairman")
        
        if entity.entity_type == EntityType.PUBLIC_LIMITED_COMPANY and not has_secretary:
            result['violations'].append("Public company must have a qualified Company Secretary")
    
    # Helper methods
    
    def _get_minimum_capital_requirement(self, entity_type: EntityType) -> Decimal:
        """Get minimum capital requirement for entity type"""
        return {
            EntityType.PRIVATE_LIMITED_COMPANY: Decimal('100000'),
            EntityType.PUBLIC_LIMITED_COMPANY: Decimal('2000000'),
            EntityType.LIMITED_LIABILITY_PARTNERSHIP: Decimal('500000'),
            EntityType.BUSINESS_NAME: Decimal('10000'),
            EntityType.INCORPORATED_TRUSTEES: Decimal('100000')
        }.get(entity_type, Decimal('100000'))
    
    def _calculate_structure_score(self, result: Dict[str, Any]) -> float:
        """Calculate structure compliance score"""
        total_checks = len(result['violations']) + len(result['warnings'])
        if total_checks == 0:
            return 100.0
        
        violation_penalty = len(result['violations']) * 15  # 15 points per violation
        warning_penalty = len(result['warnings']) * 5      # 5 points per warning
        
        score = max(0, 100 - violation_penalty - warning_penalty)
        return round(score, 2)
    
    def _calculate_governance_score(self, result: Dict[str, Any]) -> float:
        """Calculate governance compliance score"""
        base_score = 100.0
        
        # Deduct points for violations and missing best practices
        violation_penalty = len(result['violations']) * 20
        recommendation_penalty = len(result['recommendations']) * 5
        
        score = max(0, base_score - violation_penalty - recommendation_penalty)
        return round(score, 2)
    
    def _analyze_entity_structure(self, entity: EntityRegistration) -> Dict[str, Any]:
        """Perform comprehensive structure analysis"""
        analysis = {
            'entity_maturity': self._calculate_entity_maturity(entity),
            'governance_maturity': self._assess_governance_maturity(entity),
            'capital_adequacy': self._assess_capital_adequacy(entity),
            'ownership_structure': self._assess_ownership_structure(entity),
            'compliance_readiness': self._assess_compliance_readiness(entity)
        }
        
        return analysis
    
    def _calculate_entity_maturity(self, entity: EntityRegistration) -> str:
        """Calculate entity maturity level"""
        years_in_operation = (date.today() - entity.registration_date).days // 365
        
        if years_in_operation < 1:
            return "startup"
        elif years_in_operation < 5:
            return "early_stage"
        elif years_in_operation < 10:
            return "growth_stage"
        else:
            return "mature"
    
    def _assess_governance_maturity(self, entity: EntityRegistration) -> str:
        """Assess governance maturity"""
        score = 0
        
        if len(entity.directors) >= 3:
            score += 25
        
        director_types = set(d.director_type for d in entity.directors)
        if DirectorType.INDEPENDENT_DIRECTOR in director_types:
            score += 25
        
        if DirectorType.COMPANY_SECRETARY in director_types:
            score += 25
        
        nigerian_directors = sum(1 for d in entity.directors if d.nationality.upper() == 'NIGERIAN')
        if nigerian_directors >= 1:
            score += 25
        
        if score >= 75:
            return "advanced"
        elif score >= 50:
            return "intermediate"
        else:
            return "basic"
    
    def _assess_capital_adequacy(self, entity: EntityRegistration) -> str:
        """Assess capital adequacy"""
        min_capital = self._get_minimum_capital_requirement(entity.entity_type)
        
        if entity.authorized_share_capital >= min_capital * 5:
            return "strong"
        elif entity.authorized_share_capital >= min_capital * 2:
            return "adequate"
        elif entity.authorized_share_capital >= min_capital:
            return "minimum"
        else:
            return "inadequate"
    
    def _assess_ownership_structure(self, entity: EntityRegistration) -> str:
        """Assess ownership structure complexity"""
        if not entity.shareholders:
            return "unknown"
        
        if len(entity.shareholders) <= 3:
            return "simple"
        elif len(entity.shareholders) <= 10:
            return "moderate"
        else:
            return "complex"
    
    def _assess_compliance_readiness(self, entity: EntityRegistration) -> str:
        """Assess overall compliance readiness"""
        # This would be based on completeness of information and structure
        completeness_score = 0
        
        if entity.directors:
            completeness_score += 30
        if entity.shareholders:
            completeness_score += 30
        if entity.authorized_share_capital > 0:
            completeness_score += 20
        if entity.registered_address:
            completeness_score += 20
        
        if completeness_score >= 90:
            return "ready"
        elif completeness_score >= 70:
            return "mostly_ready"
        elif completeness_score >= 50:
            return "partially_ready"
        else:
            return "not_ready"
    
    # Configuration methods
    
    def _load_governance_rules(self) -> Dict[str, Any]:
        """Load governance rules configuration"""
        return {
            'board_size_limits': {
                EntityType.PRIVATE_LIMITED_COMPANY: {'min': 1, 'max': 15},
                EntityType.PUBLIC_LIMITED_COMPANY: {'min': 2, 'max': 20},
                EntityType.LIMITED_LIABILITY_PARTNERSHIP: {'min': 2, 'max': 10}
            },
            'independence_requirements': {
                EntityType.PUBLIC_LIMITED_COMPANY: {
                    'min_independent_directors': 1,
                    'min_independent_percentage': 25
                }
            }
        }
    
    def _load_capital_structure_rules(self) -> Dict[str, Any]:
        """Load capital structure rules"""
        return {
            'minimum_paid_up_percentage': {
                EntityType.PRIVATE_LIMITED_COMPANY: 25,
                EntityType.PUBLIC_LIMITED_COMPANY: 25,
                EntityType.LIMITED_LIABILITY_PARTNERSHIP: 50
            }
        }
    
    def _load_director_requirements(self) -> Dict[EntityType, Dict[str, Any]]:
        """Load director requirements by entity type"""
        return {
            EntityType.PRIVATE_LIMITED_COMPANY: {
                'min_directors': 1,
                'max_directors': 15,
                'nigerian_director_required': True,
                'company_secretary_required': False
            },
            EntityType.PUBLIC_LIMITED_COMPANY: {
                'min_directors': 2,
                'max_directors': 20,
                'nigerian_director_required': True,
                'company_secretary_required': True
            },
            EntityType.LIMITED_LIABILITY_PARTNERSHIP: {
                'min_directors': 2,
                'max_directors': 10,
                'nigerian_director_required': True,
                'company_secretary_required': False
            },
            EntityType.BUSINESS_NAME: {
                'min_directors': 0,
                'max_directors': 5,
                'nigerian_director_required': False,
                'company_secretary_required': False
            },
            EntityType.INCORPORATED_TRUSTEES: {
                'min_directors': 3,
                'max_directors': 15,
                'nigerian_director_required': True,
                'company_secretary_required': False
            }
        }
    
    def _load_shareholder_rules(self) -> Dict[EntityType, Dict[str, Any]]:
        """Load shareholder rules by entity type"""
        return {
            EntityType.PRIVATE_LIMITED_COMPANY: {
                'min_shareholders': 1,
                'max_shareholders': 50,
                'transferability': 'restricted'
            },
            EntityType.PUBLIC_LIMITED_COMPANY: {
                'min_shareholders': 2,
                'max_shareholders': None,
                'transferability': 'free'
            },
            EntityType.LIMITED_LIABILITY_PARTNERSHIP: {
                'min_shareholders': 2,
                'max_shareholders': None,
                'transferability': 'restricted'
            }
        }