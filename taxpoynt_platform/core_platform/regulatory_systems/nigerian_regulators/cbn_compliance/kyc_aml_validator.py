"""
CBN KYC/AML Validator
====================
Specialized validator for Central Bank of Nigeria (CBN) Know Your Customer (KYC)
and Anti-Money Laundering (AML) compliance requirements.
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import (
    KYCProfile, KYCTier, AMLTransaction, AMLRiskRating,
    TransactionType, CBNComplianceStatus, CBNRiskLevel
)

logger = logging.getLogger(__name__)


class KYCAMLValidator:
    """
    Validates compliance with CBN KYC and AML requirements including:
    - Customer identification and verification requirements
    - Enhanced due diligence for high-risk customers
    - Transaction monitoring and suspicious activity reporting
    - AML program effectiveness and staff training
    - Sanctions screening and PEP identification
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.kyc_requirements = self._initialize_kyc_requirements()
        self.aml_thresholds = self._initialize_aml_thresholds()
        self.high_risk_indicators = self._initialize_risk_indicators()
        self.sanctions_lists = self._initialize_sanctions_lists()

    def _initialize_kyc_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Initialize KYC requirements by tier."""
        return {
            "tier_1": {
                "required_documents": ["valid_id", "passport_photo"],
                "verification_level": "basic",
                "transaction_limit_daily": 50000,     # ₦50,000
                "transaction_limit_monthly": 200000,   # ₦200,000
                "cumulative_limit": 300000,           # ₦300,000
                "bvn_required": False,
                "address_verification": False
            },
            "tier_2": {
                "required_documents": ["valid_id", "passport_photo", "utility_bill"],
                "verification_level": "enhanced", 
                "transaction_limit_daily": 200000,    # ₦200,000
                "transaction_limit_monthly": 1000000, # ₦1,000,000
                "cumulative_limit": 5000000,          # ₦5,000,000
                "bvn_required": True,
                "address_verification": True
            },
            "tier_3": {
                "required_documents": ["valid_id", "passport_photo", "utility_bill", "income_proof"],
                "verification_level": "full",
                "transaction_limit_daily": 5000000,   # ₦5,000,000
                "transaction_limit_monthly": 20000000, # ₦20,000,000
                "cumulative_limit": None,             # No limit
                "bvn_required": True,
                "address_verification": True,
                "income_verification": True
            },
            "corporate": {
                "required_documents": [
                    "certificate_of_incorporation", "tax_clearance", 
                    "cac_form", "board_resolution", "authorized_signatories"
                ],
                "verification_level": "corporate",
                "bvn_required": False,
                "enhanced_due_diligence": True,
                "beneficial_ownership_required": True
            }
        }

    def _initialize_aml_thresholds(self) -> Dict[str, Any]:
        """Initialize AML transaction thresholds and reporting requirements."""
        return {
            "cash_transaction_reporting": {
                "ctr_threshold": 5000000,        # ₦5,000,000 for CTR
                "multiple_transaction_threshold": 1000000,  # ₦1,000,000 for related transactions
                "reporting_deadline_days": 7
            },
            "suspicious_activity": {
                "str_reporting_deadline_days": 3,
                "minimum_suspicious_amount": 100000,  # ₦100,000
                "velocity_threshold": 10,             # 10 transactions per day
                "round_amount_threshold": 1000000     # Round amounts above ₦1M
            },
            "international_transfers": {
                "swift_reporting_threshold": 10000,   # $10,000 USD equivalent
                "forex_documentation_required": 1000, # $1,000 USD equivalent
                "pep_enhanced_monitoring": True
            },
            "high_risk_thresholds": {
                "cash_intensive_business": 10000000,  # ₦10M monthly cash
                "politically_exposed_person": 1000000, # ₦1M any transaction
                "non_resident_account": 5000000,      # ₦5M any transaction
                "shell_company_indicators": True
            }
        }

    def _initialize_risk_indicators(self) -> Dict[str, List[str]]:
        """Initialize risk indicators for customer and transaction assessment."""
        return {
            "customer_risk_indicators": [
                "politically_exposed_person",
                "high_net_worth_individual",
                "cash_intensive_business",
                "non_resident_customer",
                "complex_ownership_structure",
                "bearer_share_company",
                "trust_or_foundation",
                "money_service_business",
                "precious_metals_dealer",
                "real_estate_broker",
                "casino_or_gambling",
                "art_dealer",
                "lawyer_or_accountant",
                "embassy_or_consulate"
            ],
            "transaction_risk_indicators": [
                "unusual_transaction_pattern",
                "round_dollar_amounts",
                "just_below_reporting_threshold",
                "rapid_movement_of_funds",
                "multiple_accounts_same_day",
                "wire_transfers_to_high_risk_countries",
                "cash_deposits_followed_by_wire_transfers",
                "transactions_with_no_apparent_purpose",
                "customer_reluctant_to_provide_information",
                "transactions_inconsistent_with_business",
                "use_of_multiple_accounts",
                "frequent_large_currency_exchanges"
            ],
            "geographic_risk_indicators": [
                "high_risk_jurisdictions",
                "sanctions_countries",
                "non_cooperative_countries",
                "tax_haven_jurisdictions",
                "conflict_zones",
                "narcotics_producing_countries"
            ]
        }

    def _initialize_sanctions_lists(self) -> Dict[str, List[str]]:
        """Initialize sanctions screening lists."""
        return {
            "un_sanctions": ["UN Consolidated List"],
            "ofac_sanctions": ["SDN List", "Sectoral Sanctions", "Non-SDN Lists"],
            "eu_sanctions": ["EU Consolidated List"],
            "uk_sanctions": ["UK Sanctions List"],
            "local_sanctions": ["Nigeria Terrorism Prevention List"],
            "pep_lists": ["World-Check PEP Database", "Local PEP Lists"]
        }

    async def validate_kyc_compliance(
        self,
        customer_data: Dict[str, Any],
        transaction_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Validate KYC compliance for a customer.
        
        Args:
            customer_data: Customer KYC information
            transaction_history: Customer transaction history
            
        Returns:
            KYC validation result with compliance status
        """
        try:
            self.logger.info(f"Validating KYC compliance for customer {customer_data.get('customer_id')}")
            
            violations = []
            recommendations = []
            compliance_score = 100.0
            
            # Extract customer information
            customer_id = customer_data.get("customer_id")
            kyc_tier = customer_data.get("kyc_tier", "tier_1")
            customer_type = customer_data.get("customer_type", "individual")
            
            # Validate KYC tier appropriateness
            tier_validation = await self._validate_kyc_tier_appropriateness(
                customer_data, transaction_history
            )
            violations.extend(tier_validation["violations"])
            recommendations.extend(tier_validation["recommendations"])
            compliance_score -= tier_validation["score_deduction"]
            
            # Validate required documentation
            doc_validation = await self._validate_kyc_documentation(customer_data, kyc_tier)
            violations.extend(doc_validation["violations"])
            recommendations.extend(doc_validation["recommendations"])
            compliance_score -= doc_validation["score_deduction"]
            
            # Validate identity verification
            identity_validation = await self._validate_identity_verification(customer_data)
            violations.extend(identity_validation["violations"])
            recommendations.extend(identity_validation["recommendations"])
            compliance_score -= identity_validation["score_deduction"]
            
            # Validate BVN/NIN requirements
            bvn_validation = await self._validate_bvn_nin_requirements(customer_data, kyc_tier)
            violations.extend(bvn_validation["violations"])
            recommendations.extend(bvn_validation["recommendations"])
            compliance_score -= bvn_validation["score_deduction"]
            
            # Validate transaction limits compliance
            if transaction_history:
                limits_validation = await self._validate_transaction_limits(
                    customer_data, transaction_history, kyc_tier
                )
                violations.extend(limits_validation["violations"])
                recommendations.extend(limits_validation["recommendations"])
                compliance_score -= limits_validation["score_deduction"]
            
            # Enhanced Due Diligence validation for high-risk customers
            edd_validation = await self._validate_enhanced_due_diligence(customer_data)
            violations.extend(edd_validation["violations"])
            recommendations.extend(edd_validation["recommendations"])
            compliance_score -= edd_validation["score_deduction"]
            
            # PEP screening validation
            pep_validation = await self._validate_pep_screening(customer_data)
            violations.extend(pep_validation["violations"])
            recommendations.extend(pep_validation["recommendations"])
            compliance_score -= pep_validation["score_deduction"]
            
            # Determine compliance status
            if compliance_score >= 85:
                status = CBNComplianceStatus.COMPLIANT
            elif compliance_score >= 70:
                status = CBNComplianceStatus.CONDITIONAL_COMPLIANCE
            else:
                status = CBNComplianceStatus.NON_COMPLIANT
            
            return {
                "validation_type": "kyc_compliance",
                "customer_id": customer_id,
                "compliance_status": status.value,
                "compliance_score": max(0, compliance_score),
                "violations": violations,
                "recommendations": recommendations,
                "kyc_tier": kyc_tier,
                "risk_rating": self._assess_customer_risk(customer_data),
                "next_review_date": self._calculate_kyc_review_date(customer_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating KYC compliance: {str(e)}")
            raise

    async def validate_aml_compliance(
        self,
        aml_program_data: Dict[str, Any],
        transaction_data: Optional[List[Dict[str, Any]]] = None,
        reporting_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate AML program compliance.
        
        Args:
            aml_program_data: AML program information
            transaction_data: Transaction monitoring data
            reporting_data: STR/CTR reporting data
            
        Returns:
            AML validation result with compliance status
        """
        try:
            self.logger.info("Validating AML compliance")
            
            violations = []
            recommendations = []
            compliance_score = 100.0
            
            # Validate AML program components
            program_validation = await self._validate_aml_program_components(aml_program_data)
            violations.extend(program_validation["violations"])
            recommendations.extend(program_validation["recommendations"])
            compliance_score -= program_validation["score_deduction"]
            
            # Validate transaction monitoring
            if transaction_data:
                monitoring_validation = await self._validate_transaction_monitoring(transaction_data)
                violations.extend(monitoring_validation["violations"])
                recommendations.extend(monitoring_validation["recommendations"])
                compliance_score -= monitoring_validation["score_deduction"]
            
            # Validate suspicious activity reporting
            if reporting_data:
                reporting_validation = await self._validate_suspicious_activity_reporting(reporting_data)
                violations.extend(reporting_validation["violations"])
                recommendations.extend(reporting_validation["recommendations"])
                compliance_score -= reporting_validation["score_deduction"]
            
            # Validate sanctions screening
            sanctions_validation = await self._validate_sanctions_screening(aml_program_data)
            violations.extend(sanctions_validation["violations"])
            recommendations.extend(sanctions_validation["recommendations"])
            compliance_score -= sanctions_validation["score_deduction"]
            
            # Validate staff training
            training_validation = await self._validate_aml_training(aml_program_data)
            violations.extend(training_validation["violations"])
            recommendations.extend(training_validation["recommendations"])
            compliance_score -= training_validation["score_deduction"]
            
            # Validate record keeping
            records_validation = await self._validate_aml_record_keeping(aml_program_data)
            violations.extend(records_validation["violations"])
            recommendations.extend(records_validation["recommendations"])
            compliance_score -= records_validation["score_deduction"]
            
            # Determine compliance status
            if compliance_score >= 85:
                status = CBNComplianceStatus.COMPLIANT
            elif compliance_score >= 70:
                status = CBNComplianceStatus.CONDITIONAL_COMPLIANCE
            else:
                status = CBNComplianceStatus.NON_COMPLIANT
            
            return {
                "validation_type": "aml_compliance",
                "compliance_status": status.value,
                "compliance_score": max(0, compliance_score),
                "violations": violations,
                "recommendations": recommendations,
                "program_effectiveness": self._assess_aml_program_effectiveness(compliance_score),
                "risk_exposure": self._assess_aml_risk_exposure(aml_program_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating AML compliance: {str(e)}")
            raise

    async def _validate_kyc_tier_appropriateness(
        self,
        customer_data: Dict[str, Any],
        transaction_history: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Validate if KYC tier is appropriate for customer profile and transactions."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        kyc_tier = customer_data.get("kyc_tier", "tier_1")
        customer_type = customer_data.get("customer_type", "individual")
        
        # For corporate customers, should use corporate KYC
        if customer_type == "corporate" and kyc_tier != "corporate":
            violations.append("Corporate customer not using corporate KYC tier")
            score_deduction += 20
            recommendations.append("Upgrade to corporate KYC tier for corporate customers")
        
        # Check transaction volumes against tier limits
        if transaction_history and kyc_tier in self.kyc_requirements:
            tier_requirements = self.kyc_requirements[kyc_tier]
            daily_limit = tier_requirements.get("transaction_limit_daily")
            monthly_limit = tier_requirements.get("transaction_limit_monthly")
            
            # Calculate transaction volumes
            monthly_volume = sum(t.get("amount", 0) for t in transaction_history[-30:])
            max_daily_volume = max([t.get("amount", 0) for t in transaction_history[-30:]], default=0)
            
            if daily_limit and max_daily_volume > daily_limit:
                violations.append(f"Transaction volume exceeds tier limit: {max_daily_volume} > {daily_limit}")
                score_deduction += 15
                recommendations.append("Upgrade KYC tier to accommodate transaction volumes")
            
            if monthly_limit and monthly_volume > monthly_limit:
                violations.append(f"Monthly volume exceeds tier limit: {monthly_volume} > {monthly_limit}")
                score_deduction += 15
                recommendations.append("Upgrade to higher KYC tier for current transaction volumes")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_kyc_documentation(
        self,
        customer_data: Dict[str, Any],
        kyc_tier: str
    ) -> Dict[str, Any]:
        """Validate KYC documentation completeness."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        if kyc_tier not in self.kyc_requirements:
            violations.append(f"Invalid KYC tier: {kyc_tier}")
            score_deduction += 20
            return {
                "violations": violations,
                "recommendations": ["Use valid KYC tier"],
                "score_deduction": score_deduction
            }
        
        tier_requirements = self.kyc_requirements[kyc_tier]
        required_documents = tier_requirements["required_documents"]
        provided_documents = customer_data.get("provided_documents", [])
        
        # Check for missing documents
        missing_documents = set(required_documents) - set(provided_documents)
        for doc in missing_documents:
            violations.append(f"Missing required document: {doc}")
            score_deduction += 10
            recommendations.append(f"Obtain and verify {doc.replace('_', ' ')}")
        
        # Validate document expiry
        document_details = customer_data.get("document_details", {})
        for doc in provided_documents:
            doc_info = document_details.get(doc, {})
            expiry_date = doc_info.get("expiry_date")
            
            if expiry_date:
                try:
                    expiry_date_obj = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                    if expiry_date_obj < date.today():
                        violations.append(f"Expired document: {doc}")
                        score_deduction += 15
                        recommendations.append(f"Update expired {doc.replace('_', ' ')}")
                    elif (expiry_date_obj - date.today()).days < 30:
                        recommendations.append(f"Document expiring soon: {doc}")
                except ValueError:
                    violations.append(f"Invalid expiry date format for {doc}")
                    score_deduction += 5
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_identity_verification(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate identity verification requirements."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        # Check identification number format
        id_number = customer_data.get("identification_number")
        id_type = customer_data.get("identification_type", "").lower()
        
        if not id_number:
            violations.append("Missing identification number")
            score_deduction += 20
            recommendations.append("Provide valid identification number")
        elif id_type in ["drivers_license", "national_id", "passport"]:
            # Validate format based on ID type
            if not self._validate_id_format(id_number, id_type):
                violations.append(f"Invalid {id_type} format")
                score_deduction += 15
                recommendations.append(f"Verify correct {id_type} format")
        
        # Check photo verification
        photo_verified = customer_data.get("photo_verified", False)
        if not photo_verified:
            violations.append("Customer photo not verified")
            score_deduction += 10
            recommendations.append("Complete photo verification process")
        
        # Check address verification
        address_verified = customer_data.get("address_verified", False)
        kyc_tier = customer_data.get("kyc_tier", "tier_1")
        
        if kyc_tier in ["tier_2", "tier_3", "corporate"] and not address_verified:
            violations.append("Address verification required but not completed")
            score_deduction += 15
            recommendations.append("Complete address verification with utility bill or bank statement")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_bvn_nin_requirements(
        self,
        customer_data: Dict[str, Any],
        kyc_tier: str
    ) -> Dict[str, Any]:
        """Validate BVN/NIN requirements."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        # BVN validation
        bvn = customer_data.get("bvn")
        bvn_required = self.kyc_requirements.get(kyc_tier, {}).get("bvn_required", False)
        
        if bvn_required:
            if not bvn:
                violations.append("BVN required but not provided")
                score_deduction += 20
                recommendations.append("Obtain and verify customer BVN")
            elif not self._validate_bvn_format(bvn):
                violations.append("Invalid BVN format")
                score_deduction += 15
                recommendations.append("Verify correct BVN format (11 digits)")
            else:
                # Check BVN verification status
                bvn_verified = customer_data.get("bvn_verified", False)
                if not bvn_verified:
                    violations.append("BVN not verified with NIBSS")
                    score_deduction += 15
                    recommendations.append("Verify BVN with NIBSS database")
        
        # NIN validation (for Nigerian customers)
        nationality = customer_data.get("nationality", "").lower()
        nin = customer_data.get("nin")
        
        if nationality == "nigerian" and not nin:
            recommendations.append("Consider obtaining NIN for enhanced verification")
        elif nin and not self._validate_nin_format(nin):
            violations.append("Invalid NIN format")
            score_deduction += 10
            recommendations.append("Verify correct NIN format (11 digits)")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_transaction_limits(
        self,
        customer_data: Dict[str, Any],
        transaction_history: List[Dict[str, Any]],
        kyc_tier: str
    ) -> Dict[str, Any]:
        """Validate transaction limits compliance."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        if kyc_tier not in self.kyc_requirements:
            return {"violations": [], "recommendations": [], "score_deduction": 0}
        
        tier_requirements = self.kyc_requirements[kyc_tier]
        daily_limit = tier_requirements.get("transaction_limit_daily")
        monthly_limit = tier_requirements.get("transaction_limit_monthly")
        cumulative_limit = tier_requirements.get("cumulative_limit")
        
        # Check daily limits
        if daily_limit:
            today = date.today()
            today_transactions = [
                t for t in transaction_history 
                if datetime.strptime(t.get("date", ""), "%Y-%m-%d").date() == today
            ]
            daily_total = sum(t.get("amount", 0) for t in today_transactions)
            
            if daily_total > daily_limit:
                violations.append(f"Daily transaction limit exceeded: {daily_total} > {daily_limit}")
                score_deduction += 15
                recommendations.append("Implement daily transaction limit controls")
        
        # Check monthly limits
        if monthly_limit:
            current_month_start = date.today().replace(day=1)
            month_transactions = [
                t for t in transaction_history 
                if datetime.strptime(t.get("date", ""), "%Y-%m-%d").date() >= current_month_start
            ]
            monthly_total = sum(t.get("amount", 0) for t in month_transactions)
            
            if monthly_total > monthly_limit:
                violations.append(f"Monthly transaction limit exceeded: {monthly_total} > {monthly_limit}")
                score_deduction += 20
                recommendations.append("Upgrade KYC tier or implement monthly limit controls")
        
        # Check cumulative limits
        if cumulative_limit:
            total_transactions = sum(t.get("amount", 0) for t in transaction_history)
            
            if total_transactions > cumulative_limit:
                violations.append(f"Cumulative transaction limit exceeded: {total_transactions} > {cumulative_limit}")
                score_deduction += 25
                recommendations.append("Upgrade to higher KYC tier for continued service")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_enhanced_due_diligence(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Enhanced Due Diligence for high-risk customers."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        risk_rating = customer_data.get("risk_rating", "low_risk")
        edd_completed = customer_data.get("enhanced_due_diligence_completed", False)
        
        # Check if EDD is required
        if risk_rating in ["high_risk", "very_high_risk"] and not edd_completed:
            violations.append("Enhanced Due Diligence required but not completed for high-risk customer")
            score_deduction += 25
            recommendations.append("Complete Enhanced Due Diligence for high-risk customer")
        
        # Validate EDD components for high-risk customers
        if edd_completed:
            edd_components = customer_data.get("edd_components", {})
            
            required_edd_components = [
                "source_of_wealth_verification",
                "source_of_funds_verification", 
                "purpose_of_relationship",
                "expected_transaction_patterns",
                "senior_management_approval"
            ]
            
            for component in required_edd_components:
                if not edd_components.get(component, False):
                    violations.append(f"EDD component missing: {component}")
                    score_deduction += 5
                    recommendations.append(f"Complete {component.replace('_', ' ')} for EDD")
        
        # Check PEP status and requirements
        is_pep = customer_data.get("is_politically_exposed_person", False)
        pep_approval = customer_data.get("pep_senior_management_approval", False)
        
        if is_pep and not pep_approval:
            violations.append("PEP customer lacks required senior management approval")
            score_deduction += 20
            recommendations.append("Obtain senior management approval for PEP customer")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_pep_screening(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PEP screening requirements."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        pep_screening_completed = customer_data.get("pep_screening_completed", False)
        if not pep_screening_completed:
            violations.append("PEP screening not completed")
            score_deduction += 15
            recommendations.append("Complete PEP screening for all customers")
        
        # Check screening date recency
        pep_screening_date = customer_data.get("pep_screening_date")
        if pep_screening_date:
            try:
                screening_date = datetime.strptime(pep_screening_date, "%Y-%m-%d").date()
                days_since_screening = (date.today() - screening_date).days
                
                if days_since_screening > 365:  # Annual screening requirement
                    violations.append("PEP screening outdated (over 1 year old)")
                    score_deduction += 10
                    recommendations.append("Update PEP screening annually")
            except ValueError:
                violations.append("Invalid PEP screening date format")
                score_deduction += 5
        
        # Validate sanctions screening
        sanctions_screening = customer_data.get("sanctions_screening_completed", False)
        if not sanctions_screening:
            violations.append("Sanctions screening not completed")
            score_deduction += 20
            recommendations.append("Complete sanctions screening against all applicable lists")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_aml_program_components(self, aml_program_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AML program components."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        required_components = [
            "written_aml_policy",
            "compliance_officer_designated",
            "employee_training_program",
            "independent_audit_function",
            "customer_risk_assessment",
            "transaction_monitoring_system",
            "suspicious_activity_reporting",
            "record_keeping_procedures"
        ]
        
        for component in required_components:
            if not aml_program_data.get(component, False):
                violations.append(f"AML program component missing: {component}")
                score_deduction += 10
                recommendations.append(f"Implement {component.replace('_', ' ')}")
        
        # Validate policy approval and updates
        policy_board_approved = aml_program_data.get("aml_policy_board_approved", False)
        if not policy_board_approved:
            violations.append("AML policy not approved by board")
            score_deduction += 15
            recommendations.append("Obtain board approval for AML policy")
        
        policy_last_updated = aml_program_data.get("aml_policy_last_updated")
        if policy_last_updated:
            try:
                last_updated = datetime.strptime(policy_last_updated, "%Y-%m-%d").date()
                days_since_update = (date.today() - last_updated).days
                
                if days_since_update > 365:
                    violations.append("AML policy not updated in over 1 year")
                    score_deduction += 10
                    recommendations.append("Update AML policy annually")
            except ValueError:
                violations.append("Invalid AML policy update date")
                score_deduction += 5
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_transaction_monitoring(self, transaction_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate transaction monitoring effectiveness."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        # Check for suspicious transaction patterns
        suspicious_patterns = self._detect_suspicious_patterns(transaction_data)
        
        if suspicious_patterns["unmonitored_patterns"] > 0:
            violations.append(f"Suspicious patterns not flagged: {suspicious_patterns['unmonitored_patterns']}")
            score_deduction += 20
            recommendations.append("Enhance transaction monitoring rules and thresholds")
        
        # Validate monitoring coverage
        total_transactions = len(transaction_data)
        monitored_transactions = len([t for t in transaction_data if t.get("monitoring_applied", False)])
        
        if total_transactions > 0:
            monitoring_coverage = (monitored_transactions / total_transactions) * 100
            if monitoring_coverage < 95:
                violations.append(f"Insufficient monitoring coverage: {monitoring_coverage:.1f}%")
                score_deduction += 15
                recommendations.append("Ensure comprehensive transaction monitoring coverage")
        
        # Check threshold appropriateness
        threshold_violations = self._check_threshold_violations(transaction_data)
        if threshold_violations > 0:
            violations.append(f"Threshold violations detected: {threshold_violations}")
            score_deduction += 10
            recommendations.append("Review and adjust monitoring thresholds")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_suspicious_activity_reporting(self, reporting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate suspicious activity reporting compliance."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        # STR filing requirements
        suspicious_identified = reporting_data.get("suspicious_transactions_identified", 0)
        str_filed = reporting_data.get("str_filed", 0)
        
        if suspicious_identified > str_filed:
            violations.append(f"STR not filed for all suspicious transactions: {suspicious_identified - str_filed} missing")
            score_deduction += 30
            recommendations.append("File STR for all identified suspicious transactions")
        
        # Check filing timeliness
        overdue_str = reporting_data.get("overdue_str_filings", 0)
        if overdue_str > 0:
            violations.append(f"Overdue STR filings: {overdue_str}")
            score_deduction += 20
            recommendations.append("File STR within required 3-day deadline")
        
        # CTR filing for cash transactions
        cash_transactions_over_threshold = reporting_data.get("cash_transactions_over_5m", 0)
        ctr_filed = reporting_data.get("ctr_filed", 0)
        
        if cash_transactions_over_threshold > ctr_filed:
            violations.append(f"CTR not filed for cash transactions: {cash_transactions_over_threshold - ctr_filed} missing")
            score_deduction += 25
            recommendations.append("File CTR for all cash transactions over ₦5,000,000")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_sanctions_screening(self, aml_program_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate sanctions screening compliance."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        screening_system = aml_program_data.get("automated_sanctions_screening", False)
        if not screening_system:
            violations.append("Automated sanctions screening not implemented")
            score_deduction += 25
            recommendations.append("Implement automated sanctions screening system")
        
        # Check screening list coverage
        screening_lists = aml_program_data.get("sanctions_lists_covered", [])
        required_lists = ["un_sanctions", "ofac_sanctions", "local_sanctions"]
        
        missing_lists = set(required_lists) - set(screening_lists)
        for missing_list in missing_lists:
            violations.append(f"Sanctions list not covered: {missing_list}")
            score_deduction += 10
            recommendations.append(f"Include {missing_list.replace('_', ' ')} in screening")
        
        # Check screening frequency
        screening_frequency = aml_program_data.get("screening_frequency", "never")
        if screening_frequency not in ["real_time", "daily"]:
            violations.append("Insufficient sanctions screening frequency")
            score_deduction += 15
            recommendations.append("Implement real-time or daily sanctions screening")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_aml_training(self, aml_program_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AML training compliance."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        total_staff = aml_program_data.get("total_staff", 0)
        trained_staff = aml_program_data.get("aml_trained_staff", 0)
        
        if total_staff > 0:
            training_coverage = (trained_staff / total_staff) * 100
            if training_coverage < 100:
                violations.append(f"Incomplete AML training coverage: {training_coverage:.1f}%")
                score_deduction += 20
                recommendations.append("Ensure all staff receive AML training")
        
        # Check training recency
        last_training_date = aml_program_data.get("last_aml_training_date")
        if last_training_date:
            try:
                training_date = datetime.strptime(last_training_date, "%Y-%m-%d").date()
                days_since_training = (date.today() - training_date).days
                
                if days_since_training > 365:
                    violations.append("AML training not conducted in over 1 year")
                    score_deduction += 15
                    recommendations.append("Conduct annual AML training for all staff")
            except ValueError:
                violations.append("Invalid AML training date")
                score_deduction += 5
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    async def _validate_aml_record_keeping(self, aml_program_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AML record keeping compliance."""
        violations = []
        recommendations = []
        score_deduction = 0
        
        record_retention_policy = aml_program_data.get("record_retention_policy", False)
        if not record_retention_policy:
            violations.append("AML record retention policy not established")
            score_deduction += 15
            recommendations.append("Establish comprehensive record retention policy")
        
        # Check minimum retention periods
        retention_periods = aml_program_data.get("retention_periods", {})
        
        required_retentions = {
            "customer_records": 5,      # 5 years after account closure
            "transaction_records": 5,   # 5 years after transaction
            "str_records": 7,          # 7 years
            "training_records": 3       # 3 years
        }
        
        for record_type, required_years in required_retentions.items():
            actual_years = retention_periods.get(record_type, 0)
            if actual_years < required_years:
                violations.append(f"Insufficient retention period for {record_type}: {actual_years} < {required_years} years")
                score_deduction += 5
                recommendations.append(f"Extend {record_type} retention to {required_years} years")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "score_deduction": score_deduction
        }

    def _validate_id_format(self, id_number: str, id_type: str) -> bool:
        """Validate identification number format."""
        if not id_number:
            return False
        
        # Remove spaces and hyphens for validation
        clean_id = re.sub(r'[\s\-]', '', id_number)
        
        if id_type == "drivers_license":
            # Nigerian driver's license format (simplified)
            return len(clean_id) >= 10 and clean_id.isalnum()
        elif id_type == "national_id":
            # Nigerian National ID format
            return len(clean_id) == 11 and clean_id.isdigit()
        elif id_type == "passport":
            # Nigerian passport format
            return len(clean_id) >= 8 and clean_id.isalnum()
        
        return True  # Default to valid for other types

    def _validate_bvn_format(self, bvn: str) -> bool:
        """Validate BVN format."""
        if not bvn:
            return False
        return len(bvn.replace(' ', '')) == 11 and bvn.replace(' ', '').isdigit()

    def _validate_nin_format(self, nin: str) -> bool:
        """Validate NIN format.""" 
        if not nin:
            return False
        return len(nin.replace(' ', '')) == 11 and nin.replace(' ', '').isdigit()

    def _assess_customer_risk(self, customer_data: Dict[str, Any]) -> str:
        """Assess customer risk level."""
        risk_score = 0
        
        # Check risk indicators
        customer_type = customer_data.get("customer_type", "individual")
        if customer_type == "corporate":
            risk_score += 1
        
        # High-risk occupations/businesses
        occupation = customer_data.get("occupation", "").lower()
        high_risk_occupations = ["money_changer", "precious_metals", "real_estate", "gambling"]
        if any(occ in occupation for occ in high_risk_occupations):
            risk_score += 2
        
        # PEP status
        if customer_data.get("is_politically_exposed_person", False):
            risk_score += 3
        
        # Geographic risk
        country = customer_data.get("country_of_residence", "nigeria").lower()
        if country != "nigeria":
            risk_score += 1
        
        # Transaction patterns
        expected_monthly_volume = customer_data.get("expected_monthly_volume", 0)
        if expected_monthly_volume > 10000000:  # ₦10M
            risk_score += 2
        
        # Risk assessment
        if risk_score >= 6:
            return "very_high_risk"
        elif risk_score >= 4:
            return "high_risk"
        elif risk_score >= 2:
            return "medium_risk"
        else:
            return "low_risk"

    def _calculate_kyc_review_date(self, customer_data: Dict[str, Any]) -> str:
        """Calculate next KYC review date based on risk level."""
        risk_rating = self._assess_customer_risk(customer_data)
        today = date.today()
        
        if risk_rating == "very_high_risk":
            next_review = today + timedelta(days=180)  # 6 months
        elif risk_rating == "high_risk":
            next_review = today + timedelta(days=365)  # 1 year
        elif risk_rating == "medium_risk":
            next_review = today + timedelta(days=730)  # 2 years
        else:
            next_review = today + timedelta(days=1095)  # 3 years
        
        return next_review.isoformat()

    def _detect_suspicious_patterns(self, transaction_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect suspicious transaction patterns."""
        suspicious_count = 0
        unmonitored_count = 0
        
        for transaction in transaction_data:
            amount = transaction.get("amount", 0)
            transaction_type = transaction.get("type", "")
            flagged = transaction.get("flagged_suspicious", False)
            
            # Round amount pattern
            if amount % 1000000 == 0 and amount >= 1000000:  # Round millions
                if not flagged:
                    unmonitored_count += 1
                suspicious_count += 1
            
            # Just below threshold pattern
            if 4900000 <= amount <= 4999999:  # Just below CTR threshold
                if not flagged:
                    unmonitored_count += 1
                suspicious_count += 1
        
        return {
            "suspicious_patterns": suspicious_count,
            "unmonitored_patterns": unmonitored_count
        }

    def _check_threshold_violations(self, transaction_data: List[Dict[str, Any]]) -> int:
        """Check for threshold violations."""
        violations = 0
        
        cash_threshold = self.aml_thresholds["cash_transaction_reporting"]["ctr_threshold"]
        
        for transaction in transaction_data:
            amount = transaction.get("amount", 0)
            transaction_type = transaction.get("type", "")
            reported = transaction.get("ctr_filed", False)
            
            if transaction_type == "cash_deposit" and amount >= cash_threshold and not reported:
                violations += 1
        
        return violations

    def _assess_aml_program_effectiveness(self, compliance_score: float) -> str:
        """Assess AML program effectiveness."""
        if compliance_score >= 90:
            return "Highly Effective"
        elif compliance_score >= 80:
            return "Effective"
        elif compliance_score >= 70:
            return "Moderately Effective"
        elif compliance_score >= 60:
            return "Needs Improvement"
        else:
            return "Ineffective"

    def _assess_aml_risk_exposure(self, aml_program_data: Dict[str, Any]) -> str:
        """Assess institutional AML risk exposure."""
        risk_factors = 0
        
        # Check high-risk customer percentage
        high_risk_customers = aml_program_data.get("high_risk_customer_percentage", 0)
        if high_risk_customers > 20:
            risk_factors += 2
        elif high_risk_customers > 10:
            risk_factors += 1
        
        # Check geographic risk
        international_customers = aml_program_data.get("international_customer_percentage", 0)
        if international_customers > 30:
            risk_factors += 2
        elif international_customers > 15:
            risk_factors += 1
        
        # Check business model risk
        cash_intensive_business = aml_program_data.get("cash_intensive_business_percentage", 0)
        if cash_intensive_business > 50:
            risk_factors += 2
        elif cash_intensive_business > 25:
            risk_factors += 1
        
        # Risk assessment
        if risk_factors >= 5:
            return "High Risk"
        elif risk_factors >= 3:
            return "Moderate Risk"
        elif risk_factors >= 1:
            return "Low Risk"
        else:
            return "Minimal Risk"