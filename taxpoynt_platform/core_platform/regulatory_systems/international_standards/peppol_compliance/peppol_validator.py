"""
PEPPOL Standards Validator
=========================
Comprehensive PEPPOL (Pan-European Public Procurement On-Line) validation engine
for international invoice safety and standardized document exchange.
"""
import logging
import hashlib
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from .models import (
    PEPPOLDocument, PEPPOLValidationResult, ValidationLevel,
    DocumentType, PEPPOLParticipant, NigerianPEPPOLExtension
)


class PEPPOLValidator:
    """
    Comprehensive PEPPOL standards validator for international invoice safety
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_rules = self._initialize_validation_rules()
        self.business_rules = self._initialize_business_rules()
        self.peppol_rules = self._initialize_peppol_rules()
        self.national_rules = self._initialize_national_rules()
        
    def _initialize_validation_rules(self) -> Dict[str, Dict]:
        """Initialize PEPPOL validation rules matrix"""
        return {
            # Document structure rules
            "PEPPOL-EN16931-R001": {
                "description": "Invoice must contain invoice number",
                "xpath": "//cbc:ID",
                "mandatory": True,
                "rule_type": "existence"
            },
            "PEPPOL-EN16931-R002": {
                "description": "Invoice must contain invoice issue date",
                "xpath": "//cbc:IssueDate",
                "mandatory": True,
                "rule_type": "existence"
            },
            "PEPPOL-EN16931-R003": {
                "description": "Invoice must contain invoice type code",
                "xpath": "//cbc:InvoiceTypeCode",
                "mandatory": True,
                "rule_type": "existence"
            },
            "PEPPOL-EN16931-R004": {
                "description": "Invoice currency must be specified",
                "xpath": "//cbc:DocumentCurrencyCode",
                "mandatory": True,
                "rule_type": "existence"
            },
            "PEPPOL-EN16931-R005": {
                "description": "Seller must be specified",
                "xpath": "//cac:AccountingSupplierParty",
                "mandatory": True,
                "rule_type": "existence"
            },
            "PEPPOL-EN16931-R006": {
                "description": "Buyer must be specified",
                "xpath": "//cac:AccountingCustomerParty",
                "mandatory": True,
                "rule_type": "existence"
            },
            
            # Calculation rules
            "PEPPOL-EN16931-R100": {
                "description": "Invoice line net amount must equal quantity × unit price",
                "xpath": "//cac:InvoiceLine",
                "mandatory": True,
                "rule_type": "calculation"
            },
            "PEPPOL-EN16931-R101": {
                "description": "Invoice total must equal sum of line amounts",
                "xpath": "//cac:LegalMonetaryTotal",
                "mandatory": True,
                "rule_type": "calculation"
            },
            "PEPPOL-EN16931-R102": {
                "description": "Tax amount must be calculated correctly",
                "xpath": "//cac:TaxTotal",
                "mandatory": True,
                "rule_type": "calculation"
            },
            
            # Party identification rules
            "PEPPOL-EN16931-R200": {
                "description": "Seller must have a valid identifier",
                "xpath": "//cac:AccountingSupplierParty//cbc:EndpointID",
                "mandatory": True,
                "rule_type": "identification"
            },
            "PEPPOL-EN16931-R201": {
                "description": "Buyer must have a valid identifier",
                "xpath": "//cac:AccountingCustomerParty//cbc:EndpointID",
                "mandatory": True,
                "rule_type": "identification"
            },
            
            # Nigerian-specific rules
            "PEPPOL-NG-R001": {
                "description": "Nigerian TIN must be provided for Nigerian entities",
                "xpath": "//cac:PartyTaxScheme[cac:TaxScheme/cbc:ID='TIN']",
                "mandatory": True,
                "rule_type": "nigerian_compliance"
            },
            "PEPPOL-NG-R002": {
                "description": "VAT registration required for VAT-registered entities",
                "xpath": "//cac:PartyTaxScheme[cac:TaxScheme/cbc:ID='VAT']",
                "mandatory": False,
                "rule_type": "nigerian_compliance"
            }
        }
    
    def _initialize_business_rules(self) -> Dict[str, Dict]:
        """Initialize PEPPOL business rules"""
        return {
            "BII2-T10-R001": {
                "description": "Invoice must contain at least one invoice line",
                "validation_logic": "count(//cac:InvoiceLine) >= 1",
                "severity": "fatal"
            },
            "BII2-T10-R002": {
                "description": "Invoice amounts must be positive",
                "validation_logic": "all_amounts_positive",
                "severity": "error"
            },
            "BII2-T10-R003": {
                "description": "Currency codes must be valid ISO 4217",
                "validation_logic": "valid_currency_codes",
                "severity": "error"
            },
            "BII2-T10-R004": {
                "description": "Tax percentages must be between 0 and 100",
                "validation_logic": "valid_tax_percentages",
                "severity": "error"
            },
            "BII2-T10-R005": {
                "description": "Due date must be after issue date",
                "validation_logic": "due_date_after_issue_date",
                "severity": "warning"
            }
        }
    
    def _initialize_peppol_rules(self) -> Dict[str, Dict]:
        """Initialize PEPPOL-specific rules"""
        return {
            "PEPPOL-COMMON-R001": {
                "description": "Customization ID must be from PEPPOL specifications",
                "valid_values": [
                    "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
                    "urn:cen.eu:en16931:2017#conformant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
                ],
                "severity": "error"
            },
            "PEPPOL-COMMON-R002": {
                "description": "Profile ID must be from PEPPOL BIS specifications",
                "valid_values": [
                    "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
                ],
                "severity": "error"
            },
            "PEPPOL-COMMON-R003": {
                "description": "Endpoint IDs must use valid PEPPOL schemes",
                "valid_schemes": ["0088", "0060", "0199", "0007", "9906", "9999"],
                "severity": "error"
            },
            "PEPPOL-COMMON-R004": {
                "description": "Document must be digitally signed for PEPPOL network",
                "validation_logic": "check_digital_signature",
                "severity": "error"
            }
        }
    
    def _initialize_national_rules(self) -> Dict[str, Dict]:
        """Initialize national/regional specific rules"""
        return {
            # Nigerian national rules
            "NG-R001": {
                "description": "Nigerian entities must provide TIN in correct format",
                "country": "NG",
                "validation_logic": "validate_nigerian_tin",
                "severity": "error"
            },
            "NG-R002": {
                "description": "VAT must be calculated according to Nigerian rates",
                "country": "NG",
                "validation_logic": "validate_nigerian_vat",
                "severity": "error"
            },
            "NG-R003": {
                "description": "Currency must be NGN for domestic transactions",
                "country": "NG",
                "validation_logic": "validate_domestic_currency",
                "severity": "warning"
            },
            
            # Generic international rules
            "INTL-R001": {
                "description": "Cross-border transactions must include country codes",
                "validation_logic": "validate_country_codes",
                "severity": "error"
            },
            "INTL-R002": {
                "description": "International transactions require exchange rate info",
                "validation_logic": "validate_exchange_rates",
                "severity": "warning"
            }
        }
    
    def validate_document(self, document: PEPPOLDocument, 
                         validation_level: ValidationLevel = ValidationLevel.PEPPOL_RULES) -> PEPPOLValidationResult:
        """
        Validate PEPPOL document according to specified validation level
        
        Args:
            document: PEPPOL document to validate
            validation_level: Level of validation to perform
            
        Returns:
            Comprehensive validation result
        """
        try:
            validation_result = PEPPOLValidationResult(
                document_id=document.document_id,
                validation_timestamp=datetime.now(),
                validation_level=validation_level,
                is_valid=True,  # Will be updated based on validation results
                validation_score=0.0  # Will be calculated
            )
            
            # Perform validation based on level
            if validation_level in [ValidationLevel.SYNTAX, ValidationLevel.BUSINESS_RULES, 
                                  ValidationLevel.PEPPOL_RULES, ValidationLevel.NATIONAL_RULES]:
                validation_result.syntax_validation = self._validate_syntax(document)
            
            if validation_level in [ValidationLevel.BUSINESS_RULES, 
                                  ValidationLevel.PEPPOL_RULES, ValidationLevel.NATIONAL_RULES]:
                validation_result.business_rules_validation = self._validate_business_rules(document)
            
            if validation_level in [ValidationLevel.PEPPOL_RULES, ValidationLevel.NATIONAL_RULES]:
                validation_result.peppol_rules_validation = self._validate_peppol_rules(document)
            
            if validation_level == ValidationLevel.NATIONAL_RULES:
                validation_result.national_rules_validation = self._validate_national_rules(document)
            
            # Compile overall results
            self._compile_validation_results(validation_result)
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"PEPPOL validation failed for document {document.document_id}: {str(e)}")
            raise
    
    def _validate_syntax(self, document: PEPPOLDocument) -> Dict[str, Any]:
        """Validate document syntax and structure"""
        results = {
            "passed_checks": [],
            "failed_checks": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Validate XML structure if document_content contains XML
            if isinstance(document.document_content, dict):
                xml_content = document.document_content.get('xml_content')
                if xml_content:
                    try:
                        root = ET.fromstring(xml_content)
                        results["passed_checks"].append("Valid XML structure")
                    except ET.ParseError as e:
                        results["failed_checks"].append("Invalid XML structure")
                        results["errors"].append(f"XML parsing error: {str(e)}")
            
            # Validate required fields
            required_fields = [
                ('document_id', document.document_id),
                ('document_type', document.document_type),
                ('document_date', document.document_date),
                ('currency_code', document.currency_code),
                ('total_amount', document.total_amount)
            ]
            
            for field_name, field_value in required_fields:
                if field_value is not None and field_value != "":
                    results["passed_checks"].append(f"Required field '{field_name}' present")
                else:
                    results["failed_checks"].append(f"Required field '{field_name}' missing")
                    results["errors"].append(f"Missing required field: {field_name}")
            
            # Validate data types and formats
            try:
                if len(document.currency_code) == 3:
                    results["passed_checks"].append("Currency code format valid")
                else:
                    results["failed_checks"].append("Currency code format invalid")
                    results["errors"].append("Currency code must be 3 characters")
            except:
                results["failed_checks"].append("Currency code validation failed")
            
            # Validate amounts
            if document.total_amount >= 0:
                results["passed_checks"].append("Total amount is non-negative")
            else:
                results["failed_checks"].append("Total amount is negative")
                results["errors"].append("Total amount cannot be negative")
            
        except Exception as e:
            results["errors"].append(f"Syntax validation error: {str(e)}")
            
        return results
    
    def _validate_business_rules(self, document: PEPPOLDocument) -> Dict[str, Any]:
        """Validate business rules"""
        results = {
            "passed_checks": [],
            "failed_checks": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Rule: Invoice must have at least basic content
            if document.document_content:
                results["passed_checks"].append("Document contains content")
            else:
                results["failed_checks"].append("Document content is empty")
                results["errors"].append("Document must contain business content")
            
            # Rule: Currency consistency
            if document.currency_code:
                results["passed_checks"].append("Currency code specified")
            else:
                results["failed_checks"].append("Currency code missing")
                results["errors"].append("Currency code is required for business transactions")
            
            # Rule: Amount consistency
            if document.payable_amount <= (document.total_amount + document.tax_amount):
                results["passed_checks"].append("Payable amount calculation consistent")
            else:
                results["failed_checks"].append("Payable amount calculation inconsistent")
                results["warnings"].append("Payable amount exceeds total + tax amounts")
            
            # Rule: Valid participants
            if document.sender_participant and document.receiver_participant:
                results["passed_checks"].append("Both sender and receiver specified")
                
                if document.sender_participant.participant_id != document.receiver_participant.participant_id:
                    results["passed_checks"].append("Sender and receiver are different entities")
                else:
                    results["failed_checks"].append("Sender and receiver are the same entity")
                    results["errors"].append("Sender and receiver must be different entities")
            else:
                results["failed_checks"].append("Missing sender or receiver information")
                results["errors"].append("Both sender and receiver must be specified")
            
            # Rule: Due date logic
            if document.due_date:
                if document.due_date >= document.document_date:
                    results["passed_checks"].append("Due date is after or equal to document date")
                else:
                    results["failed_checks"].append("Due date is before document date")
                    results["warnings"].append("Due date should be after document date")
            
        except Exception as e:
            results["errors"].append(f"Business rules validation error: {str(e)}")
            
        return results
    
    def _validate_peppol_rules(self, document: PEPPOLDocument) -> Dict[str, Any]:
        """Validate PEPPOL-specific rules"""
        results = {
            "passed_checks": [],
            "failed_checks": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Rule: Valid PEPPOL profile
            if hasattr(document, 'profile_id') and document.profile_id:
                valid_profiles = self.peppol_rules["PEPPOL-COMMON-R002"]["valid_values"]
                if document.profile_id in valid_profiles:
                    results["passed_checks"].append("Valid PEPPOL profile ID")
                else:
                    results["failed_checks"].append("Invalid PEPPOL profile ID")
                    results["errors"].append(f"Profile ID must be one of: {', '.join(valid_profiles)}")
            
            # Rule: Valid participant identifiers
            for participant_type, participant in [("sender", document.sender_participant), 
                                                ("receiver", document.receiver_participant)]:
                if participant:
                    scheme_valid = str(participant.scheme_id.value) in self.peppol_rules["PEPPOL-COMMON-R003"]["valid_schemes"]
                    if scheme_valid:
                        results["passed_checks"].append(f"Valid {participant_type} identifier scheme")
                    else:
                        results["failed_checks"].append(f"Invalid {participant_type} identifier scheme")
                        results["errors"].append(f"{participant_type} must use valid PEPPOL identifier scheme")
            
            # Rule: Document type support
            if document.document_type in [DocumentType.INVOICE, DocumentType.CREDIT_NOTE]:
                results["passed_checks"].append("Supported PEPPOL document type")
            else:
                results["warnings"].append("Document type may not be fully supported in PEPPOL network")
            
            # Rule: Digital signature requirement
            if document.digital_signatures:
                results["passed_checks"].append("Document is digitally signed")
            else:
                results["failed_checks"].append("Document is not digitally signed")
                results["errors"].append("PEPPOL requires digital signatures for document integrity")
            
            # Rule: Routing metadata
            if document.routing_metadata:
                results["passed_checks"].append("PEPPOL routing metadata present")
            else:
                results["warnings"].append("PEPPOL routing metadata missing - may affect delivery")
            
        except Exception as e:
            results["errors"].append(f"PEPPOL rules validation error: {str(e)}")
            
        return results
    
    def _validate_national_rules(self, document: PEPPOLDocument) -> Dict[str, Any]:
        """Validate national/regional specific rules"""
        results = {
            "passed_checks": [],
            "failed_checks": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Detect if Nigerian entities are involved
            nigerian_entities = []
            for participant_type, participant in [("sender", document.sender_participant), 
                                                ("receiver", document.receiver_participant)]:
                if participant and participant.country_code == "NG":
                    nigerian_entities.append(participant_type)
            
            if nigerian_entities:
                results["passed_checks"].append(f"Nigerian entities detected: {', '.join(nigerian_entities)}")
                
                # Nigerian-specific validations
                for participant_type, participant in [("sender", document.sender_participant), 
                                                    ("receiver", document.receiver_participant)]:
                    if participant and participant.country_code == "NG":
                        # TIN validation
                        tin_valid = self._validate_nigerian_tin(participant.participant_id)
                        if tin_valid:
                            results["passed_checks"].append(f"Valid Nigerian TIN for {participant_type}")
                        else:
                            results["failed_checks"].append(f"Invalid Nigerian TIN for {participant_type}")
                            results["errors"].append(f"Nigerian {participant_type} must have valid TIN")
                
                # Currency validation for domestic transactions
                if len(nigerian_entities) == 2:  # Both parties are Nigerian
                    if document.currency_code == "NGN":
                        results["passed_checks"].append("Correct currency for Nigerian domestic transaction")
                    else:
                        results["warnings"].append("Non-NGN currency for Nigerian domestic transaction")
                
                # VAT validation
                vat_valid = self._validate_nigerian_vat(document)
                if vat_valid:
                    results["passed_checks"].append("Nigerian VAT calculation appears correct")
                else:
                    results["warnings"].append("Nigerian VAT calculation may be incorrect")
            
            # International transaction rules
            sender_country = document.sender_participant.country_code if document.sender_participant else None
            receiver_country = document.receiver_participant.country_code if document.receiver_participant else None
            
            if sender_country and receiver_country and sender_country != receiver_country:
                results["passed_checks"].append("Cross-border transaction detected")
                
                # Exchange rate information for international transactions
                if document.currency_code not in ["USD", "EUR"]:  # Major international currencies
                    results["warnings"].append("Consider providing exchange rate information for cross-border transaction")
            
        except Exception as e:
            results["errors"].append(f"National rules validation error: {str(e)}")
            
        return results
    
    def _validate_nigerian_tin(self, tin: str) -> bool:
        """Validate Nigerian Tax Identification Number format"""
        try:
            return tin.isdigit() and len(tin) in [10, 11]
        except:
            return False
    
    def _validate_nigerian_vat(self, document: PEPPOLDocument) -> bool:
        """Validate Nigerian VAT calculation"""
        try:
            # Nigerian VAT is typically 7.5%
            expected_vat_rate = 0.075
            calculated_vat = document.total_amount * Decimal(str(expected_vat_rate))
            
            # Allow for reasonable rounding differences
            vat_difference = abs(document.tax_amount - calculated_vat)
            return vat_difference <= Decimal('0.01')  # 1 kobo tolerance
            
        except:
            return False
    
    def _compile_validation_results(self, validation_result: PEPPOLValidationResult):
        """Compile overall validation results from individual validations"""
        
        all_results = [
            validation_result.syntax_validation,
            validation_result.business_rules_validation,
            validation_result.peppol_rules_validation,
            validation_result.national_rules_validation
        ]
        
        # Collect all passed and failed checks
        for result in all_results:
            if result:
                validation_result.passed_rules.extend(result.get("passed_checks", []))
                validation_result.failed_rules.extend(result.get("failed_checks", []))
                validation_result.warnings.extend(result.get("warnings", []))
                validation_result.errors.extend(result.get("errors", []))
        
        # Identify fatal errors
        validation_result.fatal_errors = [
            error for error in validation_result.errors 
            if any(keyword in error.lower() for keyword in ["missing", "invalid", "required", "must"])
        ]
        
        # Determine overall validity
        validation_result.is_valid = len(validation_result.fatal_errors) == 0
        
        # Calculate validation score
        total_checks = len(validation_result.passed_rules) + len(validation_result.failed_rules)
        if total_checks > 0:
            validation_result.validation_score = (len(validation_result.passed_rules) / total_checks) * 100
        else:
            validation_result.validation_score = 0.0
        
        # Generate recommendations
        validation_result.recommendations = self._generate_recommendations(validation_result)
        
        # Set next validation date
        validation_result.next_validation_date = datetime.now() + timedelta(days=30)
    
    def _generate_recommendations(self, validation_result: PEPPOLValidationResult) -> List[str]:
        """Generate improvement recommendations based on validation results"""
        recommendations = []
        
        # Recommendations based on errors
        if validation_result.fatal_errors:
            recommendations.append("Address all fatal errors before submitting to PEPPOL network")
        
        if validation_result.errors:
            recommendations.append(f"Resolve {len(validation_result.errors)} validation errors")
        
        if validation_result.warnings:
            recommendations.append(f"Review {len(validation_result.warnings)} warnings for best practices")
        
        # Score-based recommendations
        if validation_result.validation_score < 90:
            recommendations.append("Improve document quality to achieve >90% validation score")
        
        if validation_result.validation_score < 70:
            recommendations.append("Document requires significant improvements before PEPPOL submission")
        
        # Specific recommendations
        if not validation_result.passed_rules:
            recommendations.append("Ensure document meets basic PEPPOL structure requirements")
        
        return recommendations
    
    def validate_participant_readiness(self, participant: PEPPOLParticipant) -> Dict[str, Any]:
        """
        Validate participant readiness for PEPPOL network
        
        Args:
            participant: PEPPOL participant to validate
            
        Returns:
            Participant readiness assessment
        """
        try:
            readiness = {
                "participant_id": participant.participant_id,
                "assessment_timestamp": datetime.now(),
                "is_ready": True,
                "readiness_score": 0.0,
                "passed_checks": [],
                "failed_checks": [],
                "requirements": [],
                "recommendations": []
            }
            
            # Check identifier validity
            if participant.scheme_id and participant.participant_id:
                readiness["passed_checks"].append("Valid participant identifier")
                score_increment = 20
            else:
                readiness["failed_checks"].append("Invalid or missing participant identifier")
                readiness["requirements"].append("Obtain valid PEPPOL participant identifier")
                score_increment = 0
            
            readiness["readiness_score"] += score_increment
            
            # Check supported documents
            if participant.supported_documents:
                readiness["passed_checks"].append(f"Supports {len(participant.supported_documents)} document types")
                readiness["readiness_score"] += 15
            else:
                readiness["failed_checks"].append("No supported document types specified")
                readiness["requirements"].append("Configure supported document types")
            
            # Check certificates
            if participant.certificates:
                readiness["passed_checks"].append("Digital certificates configured")
                readiness["readiness_score"] += 25
            else:
                readiness["failed_checks"].append("No digital certificates found")
                readiness["requirements"].append("Install required digital certificates")
            
            # Check service metadata
            if participant.service_metadata:
                readiness["passed_checks"].append("Service metadata available")
                readiness["readiness_score"] += 20
            else:
                readiness["failed_checks"].append("Service metadata missing")
                readiness["requirements"].append("Configure service metadata location")
            
            # Check capabilities
            required_capabilities = ["send", "receive", "validate"]
            available_capabilities = participant.capabilities or []
            
            missing_capabilities = [cap for cap in required_capabilities if cap not in available_capabilities]
            if not missing_capabilities:
                readiness["passed_checks"].append("All required capabilities available")
                readiness["readiness_score"] += 20
            else:
                readiness["failed_checks"].append(f"Missing capabilities: {', '.join(missing_capabilities)}")
                readiness["requirements"].append("Configure missing capabilities")
            
            # Overall readiness determination
            readiness["is_ready"] = readiness["readiness_score"] >= 80 and not readiness["failed_checks"]
            
            # Generate recommendations
            if not readiness["is_ready"]:
                readiness["recommendations"].append("Complete all requirements before PEPPOL network participation")
            
            if readiness["readiness_score"] < 90:
                readiness["recommendations"].append("Consider additional testing and validation")
            
            return readiness
            
        except Exception as e:
            self.logger.error(f"Participant readiness validation failed: {str(e)}")
            raise