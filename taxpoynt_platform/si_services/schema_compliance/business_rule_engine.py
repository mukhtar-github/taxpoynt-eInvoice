"""
Business Rule Engine

Validates documents against Nigerian business rules and tax regulations.
Extracted from schema_compliance_service.py - provides granular business rule validation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import re

logger = logging.getLogger(__name__)


class BusinessRule:
    """Represents a single business validation rule"""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        category: str,
        severity: str,
        validator: Callable[[Dict[str, Any]], Tuple[bool, str]]
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.category = category
        self.severity = severity  # error, warning, info
        self.validator = validator
        self.enabled = True


class BusinessRuleEngine:
    """
    Engine for applying Nigerian business rules to invoice data.
    Validates compliance with Nigerian tax and business regulations.
    """
    
    def __init__(self):
        self.rules: Dict[str, BusinessRule] = {}
        self.rule_categories = {
            "nigerian_tax": "Nigerian tax regulation compliance",
            "business_logic": "General business logic validation",
            "data_consistency": "Data consistency and integrity checks",
            "firs_specific": "FIRS-specific e-invoice requirements",
            "vat_compliance": "VAT calculation and reporting rules",
            "currency_rules": "Currency and monetary value rules"
        }
        self.load_default_rules()
    
    def validate_business_rules(self, invoice_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate invoice data against all enabled business rules.
        
        Args:
            invoice_data: Invoice data to validate
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        try:
            logger.info("Starting business rule validation")
            
            for rule_id, rule in self.rules.items():
                if not rule.enabled:
                    continue
                
                try:
                    is_valid, error_message = rule.validator(invoice_data)
                    
                    if not is_valid:
                        validation_errors.append({
                            "rule_id": rule_id,
                            "rule_name": rule.name,
                            "category": rule.category,
                            "severity": rule.severity,
                            "message": error_message,
                            "description": rule.description
                        })
                        
                        logger.warning(f"Business rule violation: {rule_id} - {error_message}")
                
                except Exception as e:
                    logger.error(f"Error executing business rule {rule_id}: {e}")
                    validation_errors.append({
                        "rule_id": rule_id,
                        "rule_name": rule.name,
                        "category": "system_error",
                        "severity": "error",
                        "message": f"Rule execution failed: {str(e)}",
                        "description": rule.description
                    })
            
            is_valid = not any(error["severity"] == "error" for error in validation_errors)
            
            logger.info(f"Business rule validation completed. Valid: {is_valid}, Errors: {len(validation_errors)}")
            return is_valid, validation_errors
            
        except Exception as e:
            logger.error(f"Error during business rule validation: {e}")
            return False, [{
                "rule_id": "system_error",
                "rule_name": "System Error",
                "category": "system_error",
                "severity": "error",
                "message": f"Business rule validation failed: {str(e)}",
                "description": "System error during validation"
            }]
    
    def validate_specific_category(
        self, 
        invoice_data: Dict[str, Any], 
        category: str
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate invoice data against rules in a specific category.
        
        Args:
            invoice_data: Invoice data to validate
            category: Rule category to validate
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        category_rules = {rule_id: rule for rule_id, rule in self.rules.items() 
                         if rule.category == category and rule.enabled}
        
        if not category_rules:
            logger.warning(f"No enabled rules found for category: {category}")
            return True, []
        
        for rule_id, rule in category_rules.items():
            try:
                is_valid, error_message = rule.validator(invoice_data)
                
                if not is_valid:
                    validation_errors.append({
                        "rule_id": rule_id,
                        "rule_name": rule.name,
                        "category": rule.category,
                        "severity": rule.severity,
                        "message": error_message,
                        "description": rule.description
                    })
            
            except Exception as e:
                logger.error(f"Error executing rule {rule_id}: {e}")
                validation_errors.append({
                    "rule_id": rule_id,
                    "rule_name": rule.name,
                    "category": "system_error",
                    "severity": "error",
                    "message": f"Rule execution failed: {str(e)}",
                    "description": rule.description
                })
        
        is_valid = not any(error["severity"] == "error" for error in validation_errors)
        return is_valid, validation_errors
    
    def add_custom_rule(self, rule: BusinessRule) -> bool:
        """
        Add a custom business rule to the engine.
        
        Args:
            rule: Business rule to add
            
        Returns:
            Success status
        """
        try:
            if rule.rule_id in self.rules:
                logger.warning(f"Rule {rule.rule_id} already exists, replacing")
            
            self.rules[rule.rule_id] = rule
            logger.info(f"Added custom business rule: {rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom rule: {e}")
            return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a specific rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a specific rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of all rules"""
        summary = {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled),
            "categories": {}
        }
        
        for category in self.rule_categories:
            category_rules = [rule for rule in self.rules.values() if rule.category == category]
            summary["categories"][category] = {
                "total": len(category_rules),
                "enabled": sum(1 for rule in category_rules if rule.enabled)
            }
        
        return summary
    
    def load_default_rules(self):
        """Load default Nigerian business rules"""
        
        # Nigerian Tax Rules
        self._add_nigerian_tax_rules()
        
        # Business Logic Rules
        self._add_business_logic_rules()
        
        # Data Consistency Rules
        self._add_data_consistency_rules()
        
        # FIRS Specific Rules
        self._add_firs_specific_rules()
        
        # VAT Compliance Rules
        self._add_vat_compliance_rules()
        
        # Currency Rules
        self._add_currency_rules()
    
    def _add_nigerian_tax_rules(self):
        """Add Nigerian tax regulation rules"""
        
        # Nigerian VAT Rate Rule
        self.rules["NG_VAT_RATE"] = BusinessRule(
            rule_id="NG_VAT_RATE",
            name="Nigerian VAT Rate Validation",
            description="Validates that VAT rate is 7.5% for Nigerian transactions",
            category="nigerian_tax",
            severity="error",
            validator=self._validate_nigerian_vat_rate
        )
        
        # Supplier TIN Requirement
        self.rules["NG_SUPPLIER_TIN"] = BusinessRule(
            rule_id="NG_SUPPLIER_TIN",
            name="Supplier TIN Required",
            description="Nigerian suppliers must have valid Tax Identification Number",
            category="nigerian_tax",
            severity="error",
            validator=self._validate_supplier_tin
        )
        
        # Minimum Transaction Value for VAT
        self.rules["NG_VAT_THRESHOLD"] = BusinessRule(
            rule_id="NG_VAT_THRESHOLD",
            name="VAT Threshold Validation",
            description="Validates VAT application based on Nigerian thresholds",
            category="nigerian_tax",
            severity="warning",
            validator=self._validate_vat_threshold
        )
    
    def _add_business_logic_rules(self):
        """Add general business logic rules"""
        
        # Invoice Total Calculation
        self.rules["TOTAL_CALCULATION"] = BusinessRule(
            rule_id="TOTAL_CALCULATION",
            name="Invoice Total Calculation",
            description="Validates that invoice totals are calculated correctly",
            category="business_logic",
            severity="error",
            validator=self._validate_total_calculation
        )
        
        # Line Extension Calculation
        self.rules["LINE_EXTENSION"] = BusinessRule(
            rule_id="LINE_EXTENSION",
            name="Line Extension Calculation",
            description="Validates line extension amounts (quantity × unit price)",
            category="business_logic",
            severity="error",
            validator=self._validate_line_extensions
        )
        
        # Future Date Validation
        self.rules["FUTURE_DATE"] = BusinessRule(
            rule_id="FUTURE_DATE",
            name="Future Date Validation",
            description="Invoice date cannot be in the future",
            category="business_logic",
            severity="error",
            validator=self._validate_future_date
        )
    
    def _add_data_consistency_rules(self):
        """Add data consistency rules"""
        
        # Currency Consistency
        self.rules["CURRENCY_CONSISTENCY"] = BusinessRule(
            rule_id="CURRENCY_CONSISTENCY",
            name="Currency Consistency",
            description="All monetary amounts must use consistent currency",
            category="data_consistency",
            severity="error",
            validator=self._validate_currency_consistency
        )
        
        # Party Information Consistency
        self.rules["PARTY_CONSISTENCY"] = BusinessRule(
            rule_id="PARTY_CONSISTENCY",
            name="Party Information Consistency",
            description="Supplier and customer information must be consistent",
            category="data_consistency",
            severity="warning",
            validator=self._validate_party_consistency
        )
    
    def _add_firs_specific_rules(self):
        """Add FIRS-specific rules"""
        
        # Document Type Classification
        self.rules["FIRS_DOC_TYPE"] = BusinessRule(
            rule_id="FIRS_DOC_TYPE",
            name="FIRS Document Type",
            description="Document must have valid FIRS classification",
            category="firs_specific",
            severity="error",
            validator=self._validate_firs_document_type
        )
        
        # Nigerian Business Registration
        self.rules["NG_BUSINESS_REG"] = BusinessRule(
            rule_id="NG_BUSINESS_REG",
            name="Nigerian Business Registration",
            description="Supplier must have valid Nigerian business registration",
            category="firs_specific",
            severity="warning",
            validator=self._validate_business_registration
        )
    
    def _add_vat_compliance_rules(self):
        """Add VAT compliance rules"""
        
        # VAT Calculation Accuracy
        self.rules["VAT_CALCULATION"] = BusinessRule(
            rule_id="VAT_CALCULATION",
            name="VAT Calculation Accuracy",
            description="VAT amounts must be calculated accurately",
            category="vat_compliance",
            severity="error",
            validator=self._validate_vat_calculation
        )
        
        # VAT Registration Validation
        self.rules["VAT_REGISTRATION"] = BusinessRule(
            rule_id="VAT_REGISTRATION",
            name="VAT Registration Validation",
            description="Validates VAT registration status for applicable businesses",
            category="vat_compliance",
            severity="warning",
            validator=self._validate_vat_registration
        )
    
    def _add_currency_rules(self):
        """Add currency-related rules"""
        
        # Nigerian Currency Primary
        self.rules["NG_CURRENCY_PRIMARY"] = BusinessRule(
            rule_id="NG_CURRENCY_PRIMARY",
            name="Nigerian Currency Primary",
            description="Nigerian businesses should primarily use NGN currency",
            category="currency_rules",
            severity="warning",
            validator=self._validate_nigerian_currency_primary
        )
    
    # Validator Methods
    
    def _validate_nigerian_vat_rate(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Nigerian VAT rate is 7.5%"""
        try:
            tax_total = data.get("tax_total", {})
            tax_subtotals = tax_total.get("tax_subtotals", [])
            
            for subtotal in tax_subtotals:
                tax_category = subtotal.get("tax_category", {})
                if tax_category.get("id") == "VAT":
                    percent = tax_category.get("percent")
                    if percent is not None:
                        vat_rate = float(percent)
                        if abs(vat_rate - 7.5) > 0.01:  # Allow small floating point differences
                            return False, f"Nigerian VAT rate should be 7.5%, found {vat_rate}%"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating VAT rate: {str(e)}"
    
    def _validate_supplier_tin(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate supplier has Nigerian TIN"""
        try:
            supplier = data.get("accounting_supplier_party", {}).get("party", {})
            tax_schemes = supplier.get("party_tax_scheme", [])
            
            for scheme in tax_schemes:
                company_id = scheme.get("company_id", "")
                if company_id and re.match(r'^\d{8,14}$', company_id.strip()):
                    return True, ""
            
            return False, "Supplier must have valid Nigerian Tax Identification Number (8-14 digits)"
        except Exception as e:
            return False, f"Error validating supplier TIN: {str(e)}"
    
    def _validate_vat_threshold(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate VAT threshold compliance"""
        try:
            total_amount = 0
            monetary_total = data.get("legal_monetary_total", {})
            
            if "tax_exclusive_amount" in monetary_total:
                total_amount = float(monetary_total["tax_exclusive_amount"].get("value", 0))
            
            # Nigerian VAT threshold is NGN 25,000,000 annually
            # For individual invoices, check if over NGN 100,000 (rough monthly threshold)
            if total_amount > 100000:
                tax_total = data.get("tax_total", {})
                tax_amount = float(tax_total.get("tax_amount", {}).get("value", 0))
                
                if tax_amount == 0:
                    return False, "Invoice over NGN 100,000 should include VAT"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating VAT threshold: {str(e)}"
    
    def _validate_total_calculation(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate invoice total calculations"""
        try:
            monetary_total = data.get("legal_monetary_total", {})
            
            line_extension = float(monetary_total.get("line_extension_amount", {}).get("value", 0))
            tax_amount = float(data.get("tax_total", {}).get("tax_amount", {}).get("value", 0))
            tax_inclusive = float(monetary_total.get("tax_inclusive_amount", {}).get("value", 0))
            
            calculated_total = line_extension + tax_amount
            
            if abs(calculated_total - tax_inclusive) > 0.01:
                return False, f"Tax inclusive amount ({tax_inclusive}) does not match calculated total ({calculated_total:.2f})"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating total calculation: {str(e)}"
    
    def _validate_line_extensions(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate line extension calculations"""
        try:
            lines = data.get("invoice_lines", [])
            
            for i, line in enumerate(lines):
                quantity = float(line.get("invoiced_quantity", {}).get("value", 0))
                unit_price = float(line.get("price", {}).get("price_amount", {}).get("value", 0))
                line_extension = float(line.get("line_extension_amount", {}).get("value", 0))
                
                calculated_extension = quantity * unit_price
                
                if abs(calculated_extension - line_extension) > 0.01:
                    return False, f"Line {i+1} extension amount ({line_extension}) does not match calculated amount ({calculated_extension:.2f})"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating line extensions: {str(e)}"
    
    def _validate_future_date(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate invoice date is not in future"""
        try:
            invoice_date_str = data.get("invoice_date", "")
            if not invoice_date_str:
                return True, ""  # Date validation handled elsewhere
            
            invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            if invoice_date > today:
                return False, f"Invoice date ({invoice_date}) cannot be in the future"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating invoice date: {str(e)}"
    
    def _validate_currency_consistency(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate currency consistency across document"""
        try:
            document_currency = data.get("currency_code", "")
            
            # Check monetary total currencies
            monetary_total = data.get("legal_monetary_total", {})
            for field_name, field_data in monetary_total.items():
                if isinstance(field_data, dict) and "currency_id" in field_data:
                    if field_data["currency_id"] != document_currency:
                        return False, f"Currency mismatch in {field_name}: expected {document_currency}, found {field_data['currency_id']}"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating currency consistency: {str(e)}"
    
    def _validate_party_consistency(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate party information consistency"""
        try:
            supplier = data.get("accounting_supplier_party", {}).get("party", {})
            customer = data.get("accounting_customer_party", {}).get("party", {})
            
            # Check if supplier and customer are the same (self-billing validation)
            supplier_name = supplier.get("party_name", [{}])[0].get("name", "")
            customer_name = customer.get("party_name", [{}])[0].get("name", "")
            
            if supplier_name and customer_name and supplier_name.lower() == customer_name.lower():
                return False, "Supplier and customer cannot be the same entity"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating party consistency: {str(e)}"
    
    def _validate_firs_document_type(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate FIRS document type classification"""
        try:
            firs_doc_type = data.get("firs_document_type", "")
            valid_types = ["INVOICE", "CREDIT_NOTE", "DEBIT_NOTE"]
            
            if firs_doc_type not in valid_types:
                return False, f"Invalid FIRS document type: {firs_doc_type}. Must be one of {valid_types}"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating FIRS document type: {str(e)}"
    
    def _validate_business_registration(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Nigerian business registration"""
        try:
            supplier = data.get("accounting_supplier_party", {}).get("party", {})
            legal_entities = supplier.get("party_legal_entity", [])
            
            for entity in legal_entities:
                company_id = entity.get("company_id", "")
                if company_id and company_id != "Required but not provided":
                    return True, ""
            
            return False, "Supplier should have Nigerian business registration number"
        except Exception as e:
            return False, f"Error validating business registration: {str(e)}"
    
    def _validate_vat_calculation(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate VAT calculation accuracy"""
        try:
            tax_total = data.get("tax_total", {})
            tax_subtotals = tax_total.get("tax_subtotals", [])
            
            total_calculated_tax = 0
            
            for subtotal in tax_subtotals:
                taxable_amount = float(subtotal.get("taxable_amount", {}).get("value", 0))
                tax_amount = float(subtotal.get("tax_amount", {}).get("value", 0))
                tax_category = subtotal.get("tax_category", {})
                tax_percent = float(tax_category.get("percent", 0))
                
                calculated_tax = (taxable_amount * tax_percent) / 100
                
                if abs(calculated_tax - tax_amount) > 0.01:
                    return False, f"VAT calculation error: expected {calculated_tax:.2f}, found {tax_amount}"
                
                total_calculated_tax += tax_amount
            
            declared_tax_total = float(tax_total.get("tax_amount", {}).get("value", 0))
            
            if abs(total_calculated_tax - declared_tax_total) > 0.01:
                return False, f"Total VAT amount mismatch: expected {total_calculated_tax:.2f}, found {declared_tax_total}"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating VAT calculation: {str(e)}"
    
    def _validate_vat_registration(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate VAT registration status"""
        try:
            # Check if supplier is charging VAT
            tax_total = data.get("tax_total", {})
            tax_amount = float(tax_total.get("tax_amount", {}).get("value", 0))
            
            if tax_amount > 0:
                # If charging VAT, must have VAT registration
                supplier = data.get("accounting_supplier_party", {}).get("party", {})
                tax_schemes = supplier.get("party_tax_scheme", [])
                
                vat_registered = any(
                    scheme.get("tax_scheme", {}).get("id") == "VAT" and scheme.get("company_id")
                    for scheme in tax_schemes
                )
                
                if not vat_registered:
                    return False, "Supplier charging VAT must be VAT registered"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating VAT registration: {str(e)}"
    
    def _validate_nigerian_currency_primary(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate Nigerian currency usage"""
        try:
            currency_code = data.get("currency_code", "")
            
            if currency_code != "NGN":
                return False, f"Nigerian businesses should primarily use NGN currency, found {currency_code}"
            
            return True, ""
        except Exception as e:
            return False, f"Error validating Nigerian currency usage: {str(e)}"


# Global instance for easy access
business_rule_engine = BusinessRuleEngine()