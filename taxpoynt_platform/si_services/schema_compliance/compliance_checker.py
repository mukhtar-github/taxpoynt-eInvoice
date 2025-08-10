"""
Compliance Checker

Overall compliance verification orchestrating all validation components.
Provides comprehensive document compliance checking against UBL, FIRS, and custom rules.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ComplianceLevel(Enum):
    """Compliance verification levels"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    CUSTOM = "custom"


class ComplianceStatus(Enum):
    """Overall compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    ERROR = "error"


class ComplianceChecker:
    """
    Main compliance verification orchestrator.
    Coordinates UBL validation, business rules, and custom validation.
    """
    
    def __init__(self):
        # Dependencies will be injected
        self.ubl_validator = None
        self.schema_transformer = None
        self.business_rule_engine = None
        self.custom_validator = None
        
        # Configuration
        self.compliance_levels = self._load_compliance_levels()
        self.validation_sequence = ["ubl", "business_rules", "custom"]
        self.stop_on_error = False
    
    def set_dependencies(self, ubl_validator, schema_transformer, business_rule_engine, custom_validator):
        """Inject validation component dependencies"""
        self.ubl_validator = ubl_validator
        self.schema_transformer = schema_transformer
        self.business_rule_engine = business_rule_engine
        self.custom_validator = custom_validator
    
    def check_full_compliance(
        self,
        document: Dict[str, Any],
        compliance_level: ComplianceLevel = ComplianceLevel.STANDARD,
        transform_if_needed: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive compliance check on a document.
        
        Args:
            document: Document to validate
            compliance_level: Level of compliance checking
            transform_if_needed: Whether to transform document to UBL if needed
            context: Additional validation context
            
        Returns:
            Comprehensive compliance report
        """
        logger.info("Starting full compliance check")
        
        validation_report = {
            "document_id": document.get("id") or document.get("invoice_number", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "compliance_level": compliance_level.value,
            "overall_status": ComplianceStatus.COMPLIANT.value,
            "validation_results": {},
            "summary": {
                "total_errors": 0,
                "total_warnings": 0,
                "validation_stages_passed": 0,
                "validation_stages_total": 0
            },
            "recommendations": [],
            "metadata": {
                "transform_applied": False,
                "validation_duration_ms": 0
            }
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Prepare document for validation
            working_document = document.copy()
            
            # Transform document if needed and requested
            if transform_if_needed and not self._is_ubl_format(working_document):
                logger.info("Document is not in UBL format, attempting transformation")
                try:
                    if self.schema_transformer:
                        # Detect source format and transform
                        source_format = self._detect_document_format(working_document)
                        working_document = self.schema_transformer.transform_to_ubl_invoice(
                            working_document, source_format
                        )
                        validation_report["metadata"]["transform_applied"] = True
                        logger.info(f"Successfully transformed document from {source_format} to UBL")
                    else:
                        logger.warning("Schema transformer not available for document transformation")
                except Exception as e:
                    logger.error(f"Document transformation failed: {e}")
                    validation_report["validation_results"]["transformation"] = {
                        "status": "error",
                        "message": f"Document transformation failed: {str(e)}",
                        "errors": [{"message": str(e), "severity": "error"}]
                    }
                    validation_report["overall_status"] = ComplianceStatus.ERROR.value
                    return validation_report
            
            # Get validation stages for compliance level
            validation_stages = self._get_validation_stages(compliance_level)
            validation_report["summary"]["validation_stages_total"] = len(validation_stages)
            
            # Execute validation stages
            for stage in validation_stages:
                stage_result = self._execute_validation_stage(
                    stage, working_document, context
                )
                
                validation_report["validation_results"][stage] = stage_result
                
                # Update summary counters
                errors = len([e for e in stage_result.get("errors", []) if e.get("severity") == "error"])
                warnings = len([e for e in stage_result.get("errors", []) if e.get("severity") == "warning"])
                
                validation_report["summary"]["total_errors"] += errors
                validation_report["summary"]["total_warnings"] += warnings
                
                if stage_result.get("status") != "error":
                    validation_report["summary"]["validation_stages_passed"] += 1
                
                # Stop on error if configured
                if self.stop_on_error and stage_result.get("status") == "error":
                    logger.warning(f"Stopping validation due to errors in stage: {stage}")
                    break
            
            # Determine overall compliance status
            validation_report["overall_status"] = self._determine_overall_status(validation_report)
            
            # Generate recommendations
            validation_report["recommendations"] = self._generate_recommendations(validation_report)
            
            # Calculate validation duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            validation_report["metadata"]["validation_duration_ms"] = duration_ms
            
            logger.info(f"Compliance check completed. Status: {validation_report['overall_status']}")
            return validation_report
            
        except Exception as e:
            logger.error(f"Error during compliance check: {e}")
            validation_report["overall_status"] = ComplianceStatus.ERROR.value
            validation_report["validation_results"]["system_error"] = {
                "status": "error",
                "message": f"Compliance check failed: {str(e)}",
                "errors": [{"message": str(e), "severity": "error"}]
            }
            return validation_report
    
    def check_ubl_compliance(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Check UBL schema compliance only"""
        if not self.ubl_validator:
            return {
                "status": "error",
                "message": "UBL validator not available",
                "errors": [{"message": "UBL validator not configured", "severity": "error"}]
            }
        
        try:
            is_valid, validation_errors = self.ubl_validator.validate_ubl_document(document)
            
            return {
                "status": "passed" if is_valid else "failed",
                "message": "UBL validation completed",
                "errors": validation_errors,
                "is_valid": is_valid
            }
            
        except Exception as e:
            logger.error(f"UBL validation error: {e}")
            return {
                "status": "error",
                "message": f"UBL validation failed: {str(e)}",
                "errors": [{"message": str(e), "severity": "error"}]
            }
    
    def check_business_rules(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Check business rule compliance only"""
        if not self.business_rule_engine:
            return {
                "status": "error",
                "message": "Business rule engine not available",
                "errors": [{"message": "Business rule engine not configured", "severity": "error"}]
            }
        
        try:
            is_valid, validation_errors = self.business_rule_engine.validate_business_rules(document)
            
            return {
                "status": "passed" if is_valid else "failed",
                "message": "Business rule validation completed",
                "errors": validation_errors,
                "is_valid": is_valid
            }
            
        except Exception as e:
            logger.error(f"Business rule validation error: {e}")
            return {
                "status": "error",
                "message": f"Business rule validation failed: {str(e)}",
                "errors": [{"message": str(e), "severity": "error"}]
            }
    
    def check_custom_rules(
        self, 
        document: Dict[str, Any], 
        rule_group: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check custom rule compliance only"""
        if not self.custom_validator:
            return {
                "status": "error",
                "message": "Custom validator not available",
                "errors": [{"message": "Custom validator not configured", "severity": "error"}]
            }
        
        try:
            is_valid, validation_errors = self.custom_validator.validate_with_custom_rules(
                document, rule_group, context
            )
            
            return {
                "status": "passed" if is_valid else "failed",
                "message": "Custom rule validation completed",
                "errors": validation_errors,
                "is_valid": is_valid
            }
            
        except Exception as e:
            logger.error(f"Custom rule validation error: {e}")
            return {
                "status": "error",
                "message": f"Custom rule validation failed: {str(e)}",
                "errors": [{"message": str(e), "severity": "error"}]
            }
    
    def validate_and_transform(
        self,
        document: Dict[str, Any],
        target_format: str = "ubl",
        source_format: str = "auto"
    ) -> Tuple[bool, Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Validate document and transform to target format if needed.
        
        Args:
            document: Source document
            target_format: Target format (ubl, firs)
            source_format: Source format (auto-detect if "auto")
            
        Returns:
            Tuple of (success, validation_result, transformed_document)
        """
        try:
            # Detect source format if needed
            if source_format == "auto":
                source_format = self._detect_document_format(document)
            
            logger.info(f"Validating and transforming from {source_format} to {target_format}")
            
            # Transform document
            if self.schema_transformer:
                if target_format == "ubl":
                    transformed_doc = self.schema_transformer.transform_to_ubl_invoice(document, source_format)
                elif target_format == "firs":
                    # First transform to UBL, then to FIRS format
                    ubl_doc = self.schema_transformer.transform_to_ubl_invoice(document, source_format)
                    transformed_doc = self.schema_transformer.transform_to_firs_format(ubl_doc)
                else:
                    raise ValueError(f"Unsupported target format: {target_format}")
                
                # Validate transformed document
                validation_result = self.check_full_compliance(transformed_doc, transform_if_needed=False)
                
                success = validation_result["overall_status"] in [
                    ComplianceStatus.COMPLIANT.value,
                    ComplianceStatus.WARNING.value
                ]
                
                return success, validation_result, transformed_doc
            else:
                return False, {
                    "status": "error",
                    "message": "Schema transformer not available"
                }, None
                
        except Exception as e:
            logger.error(f"Validation and transformation error: {e}")
            return False, {
                "status": "error",
                "message": f"Validation and transformation failed: {str(e)}"
            }, None
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get summary of compliance checking capabilities"""
        return {
            "available_validators": {
                "ubl_validator": bool(self.ubl_validator),
                "business_rule_engine": bool(self.business_rule_engine),
                "custom_validator": bool(self.custom_validator),
                "schema_transformer": bool(self.schema_transformer)
            },
            "compliance_levels": [level.value for level in ComplianceLevel],
            "validation_sequence": self.validation_sequence,
            "stop_on_error": self.stop_on_error
        }
    
    def configure_validation(
        self,
        validation_sequence: Optional[List[str]] = None,
        stop_on_error: Optional[bool] = None
    ):
        """Configure validation behavior"""
        if validation_sequence is not None:
            self.validation_sequence = validation_sequence
            logger.info(f"Updated validation sequence: {validation_sequence}")
        
        if stop_on_error is not None:
            self.stop_on_error = stop_on_error
            logger.info(f"Updated stop_on_error: {stop_on_error}")
    
    def _execute_validation_stage(
        self,
        stage: str,
        document: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a specific validation stage"""
        try:
            if stage == "ubl":
                return self.check_ubl_compliance(document)
            elif stage == "business_rules":
                return self.check_business_rules(document)
            elif stage == "custom":
                return self.check_custom_rules(document, context=context)
            else:
                logger.warning(f"Unknown validation stage: {stage}")
                return {
                    "status": "skipped",
                    "message": f"Unknown validation stage: {stage}",
                    "errors": []
                }
                
        except Exception as e:
            logger.error(f"Error executing validation stage {stage}: {e}")
            return {
                "status": "error",
                "message": f"Validation stage {stage} failed: {str(e)}",
                "errors": [{"message": str(e), "severity": "error"}]
            }
    
    def _get_validation_stages(self, compliance_level: ComplianceLevel) -> List[str]:
        """Get validation stages for compliance level"""
        level_config = self.compliance_levels.get(compliance_level, {})
        return level_config.get("stages", self.validation_sequence)
    
    def _determine_overall_status(self, validation_report: Dict[str, Any]) -> str:
        """Determine overall compliance status from validation results"""
        total_errors = validation_report["summary"]["total_errors"]
        total_warnings = validation_report["summary"]["total_warnings"]
        
        # Check if any stage had a system error
        for stage_result in validation_report["validation_results"].values():
            if stage_result.get("status") == "error":
                return ComplianceStatus.ERROR.value
        
        # Determine status based on errors and warnings
        if total_errors > 0:
            return ComplianceStatus.NON_COMPLIANT.value
        elif total_warnings > 0:
            return ComplianceStatus.WARNING.value
        else:
            return ComplianceStatus.COMPLIANT.value
    
    def _generate_recommendations(self, validation_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Analyze validation results for recommendations
        for stage, result in validation_report["validation_results"].items():
            errors = result.get("errors", [])
            
            # Count error types
            error_categories = {}
            for error in errors:
                category = error.get("category", "general")
                error_categories[category] = error_categories.get(category, 0) + 1
            
            # Generate stage-specific recommendations
            if stage == "ubl" and errors:
                recommendations.append("Review UBL schema compliance - ensure all required fields are present and properly formatted")
            
            if stage == "business_rules" and errors:
                if "nigerian_tax" in error_categories:
                    recommendations.append("Review Nigerian tax compliance - verify VAT rates and TIN requirements")
                if "currency_rules" in error_categories:
                    recommendations.append("Consider using NGN currency for Nigerian business transactions")
            
            if stage == "custom" and errors:
                recommendations.append("Review custom validation rules and ensure document meets organization-specific requirements")
        
        # General recommendations based on overall status
        overall_status = validation_report["overall_status"]
        if overall_status == ComplianceStatus.NON_COMPLIANT.value:
            recommendations.append("Document requires correction before submission to FIRS")
        elif overall_status == ComplianceStatus.WARNING.value:
            recommendations.append("Document is acceptable but could be improved for better compliance")
        
        # Remove duplicates and return
        return list(set(recommendations))
    
    def _is_ubl_format(self, document: Dict[str, Any]) -> bool:
        """Check if document is already in UBL format"""
        ubl_indicators = [
            "accounting_supplier_party",
            "accounting_customer_party",
            "invoice_lines",
            "tax_total",
            "legal_monetary_total"
        ]
        
        return all(indicator in document for indicator in ubl_indicators)
    
    def _detect_document_format(self, document: Dict[str, Any]) -> str:
        """Detect the format of source document"""
        # Check for Odoo format indicators
        if any(key in document for key in ["invoice_line_ids", "partner_id", "company_id"]):
            return "odoo"
        
        # Check for SAP format indicators
        if any(key in document for key in ["BUKRS", "BELNR", "GJAHR"]):
            return "sap"
        
        # Check for QuickBooks format indicators
        if any(key in document for key in ["TxnID", "CustomerRef", "Line"]):
            return "quickbooks"
        
        # Default to generic format
        return "generic"
    
    def _load_compliance_levels(self) -> Dict[ComplianceLevel, Dict[str, Any]]:
        """Load compliance level configurations"""
        return {
            ComplianceLevel.BASIC: {
                "description": "Basic UBL schema validation only",
                "stages": ["ubl"]
            },
            ComplianceLevel.STANDARD: {
                "description": "UBL schema + Nigerian business rules",
                "stages": ["ubl", "business_rules"]
            },
            ComplianceLevel.STRICT: {
                "description": "Full validation including custom rules",
                "stages": ["ubl", "business_rules", "custom"]
            },
            ComplianceLevel.CUSTOM: {
                "description": "User-defined validation stages",
                "stages": []  # Will be configured by user
            }
        }


# Global instance for easy access
compliance_checker = ComplianceChecker()