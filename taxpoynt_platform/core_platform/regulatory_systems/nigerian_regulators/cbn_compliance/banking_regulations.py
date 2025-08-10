"""
CBN Banking Regulations Validator
=================================
Specialized validator for Central Bank of Nigeria (CBN) banking license compliance
and prudential guidelines enforcement.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import (
    BankingLicense, BankingLicenseType, CBNComplianceStatus,
    CBNRiskLevel, RiskAssessment
)

logger = logging.getLogger(__name__)


class BankingRegulationsValidator:
    """
    Validates compliance with CBN banking regulations including:
    - Banking license requirements and conditions
    - Prudential guidelines and ratios
    - Capital adequacy requirements
    - Risk management standards
    - Corporate governance requirements
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.minimum_capital_requirements = self._initialize_capital_requirements()
        self.prudential_ratios = self._initialize_prudential_ratios()
        self.governance_requirements = self._initialize_governance_requirements()

    def _initialize_capital_requirements(self) -> Dict[BankingLicenseType, Decimal]:
        """Initialize minimum capital requirements by license type."""
        return {
            BankingLicenseType.COMMERCIAL_BANK: Decimal("25000000000"),  # ₦25 billion
            BankingLicenseType.MERCHANT_BANK: Decimal("15000000000"),    # ₦15 billion
            BankingLicenseType.MICROFINANCE_BANK: Decimal("5000000000"), # ₦5 billion (State MFB)
            BankingLicenseType.SPECIALIZED_BANK: Decimal("10000000000"), # ₦10 billion
            BankingLicenseType.DEVELOPMENT_FINANCE_INSTITUTION: Decimal("10000000000"), # ₦10 billion
            BankingLicenseType.PRIMARY_MORTGAGE_INSTITUTION: Decimal("5000000000"), # ₦5 billion
            BankingLicenseType.FINANCE_COMPANY: Decimal("1000000000"),   # ₦1 billion
            BankingLicenseType.BUREAU_DE_CHANGE: Decimal("35000000"),    # ₦35 million
            BankingLicenseType.PAYMENT_SERVICE_BANK: Decimal("5000000000"), # ₦5 billion
        }

    def _initialize_prudential_ratios(self) -> Dict[str, Dict[str, float]]:
        """Initialize prudential ratio requirements."""
        return {
            "capital_adequacy": {
                "minimum_car": 15.0,      # Minimum Capital Adequacy Ratio
                "well_capitalized": 20.0,  # Well-capitalized threshold
                "tier1_minimum": 10.0,     # Minimum Tier 1 ratio
                "leverage_minimum": 3.0    # Minimum leverage ratio
            },
            "liquidity": {
                "minimum_ratio": 30.0,     # Minimum liquidity ratio
                "lcr_minimum": 100.0,      # Liquidity Coverage Ratio
                "nsfr_minimum": 100.0      # Net Stable Funding Ratio
            },
            "asset_quality": {
                "maximum_npl": 5.0,        # Maximum NPL ratio
                "provisioning_coverage": 100.0  # Minimum provision coverage
            },
            "concentration": {
                "single_obligor_limit": 20.0,     # Single obligor limit (% of capital)
                "related_party_limit": 10.0,      # Related party exposure limit
                "sectoral_concentration": 30.0     # Sectoral concentration limit
            }
        }

    def _initialize_governance_requirements(self) -> Dict[str, Any]:
        """Initialize corporate governance requirements."""
        return {
            "board_composition": {
                "minimum_size": 5,
                "maximum_size": 20,
                "minimum_independent_directors": 30,  # Percentage
                "minimum_meetings_per_year": 4
            },
            "committees": {
                "required_committees": [
                    "audit_committee",
                    "risk_management_committee",
                    "nomination_committee",
                    "remuneration_committee"
                ],
                "audit_committee_min_members": 3,
                "risk_committee_min_members": 3
            },
            "key_personnel": {
                "ceo_tenure_limit": 10,  # Years
                "fit_and_proper_validity": 3,  # Years
                "mandatory_positions": [
                    "chief_executive_officer",
                    "chief_financial_officer",
                    "chief_risk_officer",
                    "chief_compliance_officer",
                    "chief_audit_executive"
                ]
            }
        }

    async def validate_banking_license(
        self,
        license_data: Dict[str, Any],
        financial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate banking license compliance.
        
        Args:
            license_data: Banking license information
            financial_data: Financial statements and ratios
            
        Returns:
            Validation result with compliance status and recommendations
        """
        try:
            self.logger.info("Validating banking license compliance")
            
            violations = []
            recommendations = []
            compliance_score = 100.0
            
            # Parse license information
            license_number = license_data.get("license_number")
            license_type = license_data.get("license_type")
            institution_name = license_data.get("institution_name")
            issued_date = license_data.get("issued_date")
            expiry_date = license_data.get("expiry_date")
            status = license_data.get("status", "").lower()
            
            # Validate license number format
            if not license_number or not self._validate_license_number_format(license_number):
                violations.append("Invalid or missing CBN license number format")
                compliance_score -= 20
                recommendations.append("Ensure valid CBN license number is provided")
            
            # Validate license type
            try:
                license_type_enum = BankingLicenseType(license_type)
            except ValueError:
                violations.append(f"Invalid banking license type: {license_type}")
                compliance_score -= 15
                recommendations.append("Verify correct banking license type with CBN")
                license_type_enum = None
            
            # Validate license status
            valid_statuses = ["active", "valid", "current"]
            if status not in valid_statuses:
                violations.append(f"Invalid license status: {status}")
                compliance_score -= 25
                recommendations.append("Ensure banking license is active and valid")
            
            # Check license expiry
            if expiry_date:
                try:
                    expiry_date_obj = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                    days_to_expiry = (expiry_date_obj - date.today()).days
                    
                    if days_to_expiry < 0:
                        violations.append("Banking license has expired")
                        compliance_score -= 50
                        recommendations.append("Renew expired banking license immediately")
                    elif days_to_expiry < 90:
                        recommendations.append(f"Banking license expires in {days_to_expiry} days - initiate renewal process")
                    elif days_to_expiry < 180:
                        recommendations.append("Consider early renewal of banking license")
                except ValueError:
                    violations.append("Invalid license expiry date format")
                    compliance_score -= 10
            
            # Validate capital requirements
            if license_type_enum and financial_data:
                capital_validation = await self._validate_capital_requirements(
                    license_type_enum, financial_data
                )
                violations.extend(capital_validation["violations"])
                recommendations.extend(capital_validation["recommendations"])
                compliance_score -= capital_validation["score_deduction"]
            
            # Validate authorized activities
            authorized_activities = license_data.get("authorized_activities", [])
            current_activities = license_data.get("current_activities", [])
            
            unauthorized_activities = set(current_activities) - set(authorized_activities)
            if unauthorized_activities:
                violations.append(f"Unauthorized banking activities: {list(unauthorized_activities)}")
                compliance_score -= 20
                recommendations.append("Cease unauthorized activities or obtain CBN approval")
            
            # Validate operating locations
            authorized_locations = license_data.get("authorized_locations", [])
            current_locations = license_data.get("current_locations", [])
            
            unauthorized_locations = set(current_locations) - set(authorized_locations)
            if unauthorized_locations:
                violations.append(f"Operating in unauthorized locations: {list(unauthorized_locations)}")
                compliance_score -= 15
                recommendations.append("Obtain CBN approval for new operating locations")
            
            # Check conditions and restrictions compliance
            conditions = license_data.get("conditions", [])
            conditions_compliance = license_data.get("conditions_compliance", {})
            
            for condition in conditions:
                if not conditions_compliance.get(condition, False):
                    violations.append(f"License condition not met: {condition}")
                    compliance_score -= 10
                    recommendations.append(f"Ensure compliance with license condition: {condition}")
            
            # Determine compliance status
            if compliance_score >= 85:
                status = CBNComplianceStatus.COMPLIANT
            elif compliance_score >= 70:
                status = CBNComplianceStatus.CONDITIONAL_COMPLIANCE
            else:
                status = CBNComplianceStatus.NON_COMPLIANT
            
            return {
                "validation_type": "banking_license",
                "compliance_status": status.value,
                "compliance_score": max(0, compliance_score),
                "violations": violations,
                "recommendations": recommendations,
                "license_number": license_number,
                "license_type": license_type,
                "license_status": license_data.get("status"),
                "days_to_expiry": days_to_expiry if expiry_date else None
            }
            
        except Exception as e:
            self.logger.error(f"Error validating banking license: {str(e)}")
            raise

    async def validate_prudential_guidelines(
        self,
        financial_data: Dict[str, Any],
        license_type: Optional[BankingLicenseType] = None
    ) -> Dict[str, Any]:
        """
        Validate compliance with CBN prudential guidelines.
        
        Args:
            financial_data: Financial statements and ratios
            license_type: Type of banking license
            
        Returns:
            Validation result for prudential guidelines
        """
        try:
            self.logger.info("Validating prudential guidelines compliance")
            
            violations = []
            recommendations = []
            compliance_score = 100.0
            ratio_analysis = {}
            
            # Capital Adequacy Validation
            capital_validation = await self._validate_capital_adequacy_ratios(financial_data)
            violations.extend(capital_validation["violations"])
            recommendations.extend(capital_validation["recommendations"])
            compliance_score -= capital_validation["score_deduction"]
            ratio_analysis.update(capital_validation["ratios"])
            
            # Liquidity Validation
            liquidity_validation = await self._validate_liquidity_ratios(financial_data)
            violations.extend(liquidity_validation["violations"])
            recommendations.extend(liquidity_validation["recommendations"])
            compliance_score -= liquidity_validation["score_deduction"]
            ratio_analysis.update(liquidity_validation["ratios"])
            
            # Asset Quality Validation
            asset_validation = await self._validate_asset_quality(financial_data)
            violations.extend(asset_validation["violations"])
            recommendations.extend(asset_validation["recommendations"])
            compliance_score -= asset_validation["score_deduction"]
            ratio_analysis.update(asset_validation["ratios"])
            
            # Concentration Risk Validation
            concentration_validation = await self._validate_concentration_limits(financial_data)
            violations.extend(concentration_validation["violations"])
            recommendations.extend(concentration_validation["recommendations"])
            compliance_score -= concentration_validation["score_deduction"]
            ratio_analysis.update(concentration_validation["ratios"])
            
            # Large Exposures Validation
            exposures_validation = await self._validate_large_exposures(financial_data)
            violations.extend(exposures_validation["violations"])
            recommendations.extend(exposures_validation["recommendations"])
            compliance_score -= exposures_validation["score_deduction"]
            
            # Determine compliance status
            if compliance_score >= 85:
                status = CBNComplianceStatus.COMPLIANT
            elif compliance_score >= 70:
                status = CBNComplianceStatus.CONDITIONAL_COMPLIANCE
            else:
                status = CBNComplianceStatus.NON_COMPLIANT
            
            return {
                "validation_type": "prudential_guidelines",
                "compliance_status": status.value,
                "compliance_score": max(0, compliance_score),
                "violations": violations,
                "recommendations": recommendations,
                "ratio_analysis": ratio_analysis,
                "risk_assessment": self._assess_prudential_risk(ratio_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating prudential guidelines: {str(e)}")
            raise

    async def validate_corporate_governance(
        self,
        governance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate corporate governance compliance.
        
        Args:
            governance_data: Corporate governance information
            
        Returns:
            Validation result for corporate governance
        """
        try:
            self.logger.info("Validating corporate governance compliance")
            
            violations = []
            recommendations = []
            compliance_score = 100.0
            
            # Board Composition Validation
            board_validation = await self._validate_board_composition(governance_data)
            violations.extend(board_validation["violations"])
            recommendations.extend(board_validation["recommendations"])
            compliance_score -= board_validation["score_deduction"]
            
            # Committee Structure Validation
            committee_validation = await self._validate_committee_structure(governance_data)
            violations.extend(committee_validation["violations"])
            recommendations.extend(committee_validation["recommendations"])
            compliance_score -= committee_validation["score_deduction"]
            
            # Key Personnel Validation
            personnel_validation = await self._validate_key_personnel(governance_data)
            violations.extend(personnel_validation["violations"])
            recommendations.extend(personnel_validation["recommendations"])
            compliance_score -= personnel_validation["score_deduction"]
            
            # Policies and Procedures Validation
            policies_validation = await self._validate_policies_procedures(governance_data)
            violations.extend(policies_validation["violations"])
            recommendations.extend(policies_validation["recommendations"])
            compliance_score -= policies_validation["score_deduction"]
            
            # Determine compliance status
            if compliance_score >= 85:
                status = CBNComplianceStatus.COMPLIANT
            elif compliance_score >= 70:
                status = CBNComplianceStatus.CONDITIONAL_COMPLIANCE
            else:
                status = CBNComplianceStatus.NON_COMPLIANT
            
            return {
                "validation_type": "corporate_governance",
                "compliance_status": status.value,
                "compliance_score": max(0, compliance_score),
                "violations": violations,
                "recommendations": recommendations,
                "governance_rating": self._calculate_governance_rating(compliance_score)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating corporate governance: {str(e)}")
            raise

    async def _validate_capital_requirements(
        self,
        license_type: BankingLicenseType,
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate minimum capital requirements."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        minimum_required = self.minimum_capital_requirements.get(license_type, Decimal("1000000000"))
        paid_up_capital = Decimal(str(financial_data.get("paid_up_capital", 0)))
        
        if paid_up_capital < minimum_required:
            shortfall = minimum_required - paid_up_capital
            violations.append(f"Capital shortfall: ₦{shortfall:,} below minimum requirement")
            score_deduction = 30
            recommendations.append(f"Increase paid-up capital to meet minimum requirement of ₦{minimum_required:,}")
        
        # Check if capital is well above minimum (buffer)
        buffer_ratio = float(paid_up_capital / minimum_required) if minimum_required > 0 else 0
        if buffer_ratio < 1.2:  # Less than 20% buffer
            recommendations.append("Consider maintaining capital buffer above minimum requirements")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction,
            "minimum_required": float(minimum_required),
            "current_capital": float(paid_up_capital),
            "buffer_ratio": buffer_ratio
        }

    async def _validate_capital_adequacy_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate capital adequacy ratios."""
        violations = []
        recommendations = []
        score_deduction = 0
        ratios = {}
        
        # Capital Adequacy Ratio (CAR)
        car = float(financial_data.get("capital_adequacy_ratio", 0))
        minimum_car = self.prudential_ratios["capital_adequacy"]["minimum_car"]
        
        ratios["capital_adequacy_ratio"] = car
        
        if car < minimum_car:
            violations.append(f"Capital Adequacy Ratio below minimum: {car}% < {minimum_car}%")
            score_deduction += 25
            recommendations.append(f"Increase capital or reduce risk-weighted assets to achieve minimum CAR of {minimum_car}%")
        
        # Tier 1 Capital Ratio
        tier1_ratio = float(financial_data.get("tier1_capital_ratio", 0))
        minimum_tier1 = self.prudential_ratios["capital_adequacy"]["tier1_minimum"]
        
        ratios["tier1_capital_ratio"] = tier1_ratio
        
        if tier1_ratio < minimum_tier1:
            violations.append(f"Tier 1 capital ratio below minimum: {tier1_ratio}% < {minimum_tier1}%")
            score_deduction += 20
            recommendations.append(f"Increase Tier 1 capital to meet minimum {minimum_tier1}% requirement")
        
        # Leverage Ratio
        leverage_ratio = float(financial_data.get("leverage_ratio", 0))
        minimum_leverage = self.prudential_ratios["capital_adequacy"]["leverage_minimum"]
        
        ratios["leverage_ratio"] = leverage_ratio
        
        if leverage_ratio < minimum_leverage:
            violations.append(f"Leverage ratio below minimum: {leverage_ratio}% < {minimum_leverage}%")
            score_deduction += 15
            recommendations.append(f"Improve leverage ratio to meet minimum {minimum_leverage}% requirement")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction,
            "ratios": ratios
        }

    async def _validate_liquidity_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate liquidity ratios."""
        violations = []
        recommendations = []
        score_deduction = 0
        ratios = {}
        
        # Liquidity Ratio
        liquidity_ratio = float(financial_data.get("liquidity_ratio", 0))
        minimum_liquidity = self.prudential_ratios["liquidity"]["minimum_ratio"]
        
        ratios["liquidity_ratio"] = liquidity_ratio
        
        if liquidity_ratio < minimum_liquidity:
            violations.append(f"Liquidity ratio below minimum: {liquidity_ratio}% < {minimum_liquidity}%")
            score_deduction += 20
            recommendations.append(f"Maintain minimum liquidity ratio of {minimum_liquidity}%")
        
        # Liquidity Coverage Ratio (LCR)
        lcr = float(financial_data.get("liquidity_coverage_ratio", 0))
        minimum_lcr = self.prudential_ratios["liquidity"]["lcr_minimum"]
        
        ratios["liquidity_coverage_ratio"] = lcr
        
        if lcr < minimum_lcr:
            violations.append(f"Liquidity Coverage Ratio below minimum: {lcr}% < {minimum_lcr}%")
            score_deduction += 15
            recommendations.append(f"Improve LCR to meet minimum {minimum_lcr}% requirement")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction,
            "ratios": ratios
        }

    async def _validate_asset_quality(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate asset quality metrics."""
        violations = []
        recommendations = []
        score_deduction = 0
        ratios = {}
        
        # Non-Performing Loans Ratio
        npl_ratio = float(financial_data.get("non_performing_loans_ratio", 0))
        maximum_npl = self.prudential_ratios["asset_quality"]["maximum_npl"]
        
        ratios["npl_ratio"] = npl_ratio
        
        if npl_ratio > maximum_npl:
            violations.append(f"NPL ratio exceeds maximum: {npl_ratio}% > {maximum_npl}%")
            score_deduction += 20
            recommendations.append("Implement robust credit risk management and recovery strategies")
        
        # Provision Coverage Ratio
        provision_coverage = float(financial_data.get("provision_coverage_ratio", 0))
        minimum_coverage = self.prudential_ratios["asset_quality"]["provisioning_coverage"]
        
        ratios["provision_coverage_ratio"] = provision_coverage
        
        if provision_coverage < minimum_coverage:
            violations.append(f"Provision coverage below minimum: {provision_coverage}% < {minimum_coverage}%")
            score_deduction += 15
            recommendations.append(f"Increase loan loss provisions to {minimum_coverage}% coverage")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction,
            "ratios": ratios
        }

    async def _validate_concentration_limits(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate concentration limits."""
        violations = []
        recommendations = []
        score_deduction = 0
        ratios = {}
        
        # Single Obligor Limit
        max_single_exposure = float(financial_data.get("max_single_obligor_exposure", 0))
        single_obligor_limit = self.prudential_ratios["concentration"]["single_obligor_limit"]
        
        ratios["max_single_obligor_exposure"] = max_single_exposure
        
        if max_single_exposure > single_obligor_limit:
            violations.append(f"Single obligor exposure exceeds limit: {max_single_exposure}% > {single_obligor_limit}%")
            score_deduction += 20
            recommendations.append(f"Reduce single obligor exposures to within {single_obligor_limit}% limit")
        
        # Related Party Exposure
        related_party_exposure = float(financial_data.get("related_party_exposure", 0))
        related_party_limit = self.prudential_ratios["concentration"]["related_party_limit"]
        
        ratios["related_party_exposure"] = related_party_exposure
        
        if related_party_exposure > related_party_limit:
            violations.append(f"Related party exposure exceeds limit: {related_party_exposure}% > {related_party_limit}%")
            score_deduction += 15
            recommendations.append(f"Reduce related party exposures to within {related_party_limit}% limit")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction,
            "ratios": ratios
        }

    async def _validate_large_exposures(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate large exposures compliance."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        large_exposures = financial_data.get("large_exposures", [])
        
        for i, exposure in enumerate(large_exposures):
            exposure_percentage = float(exposure.get("percentage", 0))
            obligor_name = exposure.get("obligor", f"Obligor {i+1}")
            
            if exposure_percentage > 20:  # CBN large exposure limit
                violations.append(f"Large exposure exceeds 20% limit: {obligor_name} ({exposure_percentage}%)")
                score_deduction += 10
                recommendations.append(f"Reduce exposure to {obligor_name} to comply with large exposure limits")
        
        # Check aggregate large exposures
        total_large_exposures = sum(float(exp.get("percentage", 0)) for exp in large_exposures)
        if total_large_exposures > 800:  # Aggregate limit typically 800% of capital
            violations.append(f"Aggregate large exposures exceed prudential limit: {total_large_exposures}%")
            score_deduction += 15
            recommendations.append("Reduce aggregate large exposures to prudential levels")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction,
            "total_large_exposures": total_large_exposures
        }

    async def _validate_board_composition(self, governance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate board composition requirements."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        requirements = self.governance_requirements["board_composition"]
        
        # Board size
        board_size = governance_data.get("board_size", 0)
        if board_size < requirements["minimum_size"] or board_size > requirements["maximum_size"]:
            violations.append(f"Board size outside acceptable range: {board_size} (should be {requirements['minimum_size']}-{requirements['maximum_size']})")
            score_deduction += 15
            recommendations.append(f"Adjust board size to {requirements['minimum_size']}-{requirements['maximum_size']} members")
        
        # Independent directors
        independent_directors = governance_data.get("independent_directors", 0)
        if board_size > 0:
            independence_ratio = (independent_directors / board_size) * 100
            min_independence = requirements["minimum_independent_directors"]
            
            if independence_ratio < min_independence:
                violations.append(f"Insufficient independent directors: {independence_ratio:.1f}% < {min_independence}%")
                score_deduction += 20
                recommendations.append(f"Increase independent director representation to at least {min_independence}%")
        
        # Board meetings
        board_meetings = governance_data.get("board_meetings_per_year", 0)
        min_meetings = requirements["minimum_meetings_per_year"]
        
        if board_meetings < min_meetings:
            violations.append(f"Insufficient board meetings: {board_meetings} < {min_meetings} per year")
            score_deduction += 10
            recommendations.append(f"Conduct minimum of {min_meetings} board meetings per year")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_committee_structure(self, governance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate board committee structure."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        requirements = self.governance_requirements["committees"]
        established_committees = governance_data.get("established_committees", [])
        
        # Check required committees
        for required_committee in requirements["required_committees"]:
            if required_committee not in established_committees:
                violations.append(f"Required committee not established: {required_committee}")
                score_deduction += 15
                recommendations.append(f"Establish {required_committee.replace('_', ' ').title()}")
        
        # Validate audit committee composition
        audit_committee_members = governance_data.get("audit_committee_members", 0)
        min_audit_members = requirements["audit_committee_min_members"]
        
        if "audit_committee" in established_committees and audit_committee_members < min_audit_members:
            violations.append(f"Audit committee has insufficient members: {audit_committee_members} < {min_audit_members}")
            score_deduction += 10
            recommendations.append(f"Increase audit committee to minimum {min_audit_members} members")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_key_personnel(self, governance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate key personnel requirements."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        requirements = self.governance_requirements["key_personnel"]
        appointed_positions = governance_data.get("appointed_positions", [])
        
        # Check mandatory positions
        for mandatory_position in requirements["mandatory_positions"]:
            if mandatory_position not in appointed_positions:
                violations.append(f"Mandatory position not filled: {mandatory_position}")
                score_deduction += 15
                recommendations.append(f"Appoint qualified {mandatory_position.replace('_', ' ').title()}")
        
        # Check fit and proper assessments
        fit_proper_current = governance_data.get("fit_and_proper_assessments_current", False)
        if not fit_proper_current:
            violations.append("Fit and proper assessments not current for key personnel")
            score_deduction += 20
            recommendations.append("Conduct current fit and proper assessments for all key management personnel")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_policies_procedures(self, governance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate policies and procedures."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        required_policies = [
            "risk_management_policy",
            "credit_policy",
            "liquidity_management_policy",
            "aml_cft_policy",
            "corporate_governance_policy",
            "internal_audit_policy",
            "compliance_policy"
        ]
        
        approved_policies = governance_data.get("board_approved_policies", [])
        
        for policy in required_policies:
            if policy not in approved_policies:
                violations.append(f"Required policy not approved by board: {policy}")
                score_deduction += 5
                recommendations.append(f"Develop and obtain board approval for {policy.replace('_', ' ').title()}")
        
        # Check policy review frequency
        policy_review_frequency = governance_data.get("policy_review_frequency", "never")
        if policy_review_frequency not in ["annual", "biannual"]:
            violations.append("Policies not reviewed regularly")
            score_deduction += 10
            recommendations.append("Establish annual policy review process")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    def _validate_license_number_format(self, license_number: str) -> bool:
        """Validate CBN license number format."""
        # CBN license numbers typically follow specific formats
        # This is a simplified validation - actual format may vary
        if not license_number:
            return False
        
        # Remove spaces and special characters for validation
        clean_number = license_number.replace(" ", "").replace("-", "").replace("/", "")
        
        # Check if it contains required components (simplified check)
        if len(clean_number) < 8:
            return False
        
        return True

    def _assess_prudential_risk(self, ratio_analysis: Dict[str, float]) -> str:
        """Assess overall prudential risk based on ratios."""
        risk_score = 0
        
        # Capital adequacy risk
        car = ratio_analysis.get("capital_adequacy_ratio", 0)
        if car < 10:
            risk_score += 3
        elif car < 15:
            risk_score += 2
        elif car < 20:
            risk_score += 1
        
        # Liquidity risk
        liquidity_ratio = ratio_analysis.get("liquidity_ratio", 0)
        if liquidity_ratio < 20:
            risk_score += 3
        elif liquidity_ratio < 30:
            risk_score += 2
        elif liquidity_ratio < 40:
            risk_score += 1
        
        # Asset quality risk
        npl_ratio = ratio_analysis.get("npl_ratio", 0)
        if npl_ratio > 10:
            risk_score += 3
        elif npl_ratio > 5:
            risk_score += 2
        elif npl_ratio > 3:
            risk_score += 1
        
        # Risk assessment
        if risk_score >= 7:
            return "High Risk"
        elif risk_score >= 4:
            return "Moderate Risk"
        elif risk_score >= 2:
            return "Low Risk"
        else:
            return "Minimal Risk"

    def _calculate_governance_rating(self, compliance_score: float) -> str:
        """Calculate governance rating based on compliance score."""
        if compliance_score >= 90:
            return "Excellent"
        elif compliance_score >= 80:
            return "Good"
        elif compliance_score >= 70:
            return "Satisfactory"
        elif compliance_score >= 60:
            return "Needs Improvement"
        else:
            return "Poor"