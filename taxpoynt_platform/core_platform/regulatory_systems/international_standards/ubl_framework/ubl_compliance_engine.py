"""
UBL Compliance Engine
====================
Central orchestrator for UBL transformation and validation across all business systems.
Provides unified UBL 2.1 compliance management and Nigerian FIRS integration.
"""
import logging
from typing import Dict, Any, List, Optional, Type, Union
from datetime import datetime
from enum import Enum

from .base_ubl_transformer import BaseUBLTransformer, UBLTransformationError
from .base_ubl_validator import BaseUBLValidator, ValidationResult
from .ubl_models import UBLInvoice


class BusinessSystemType(Enum):
    """Supported business system types."""
    ERP_SAP = "erp_sap"
    ERP_ORACLE = "erp_oracle"
    ERP_DYNAMICS = "erp_dynamics"
    ERP_NETSUITE = "erp_netsuite"
    ERP_ODOO = "erp_odoo"
    ERP_SAGE = "erp_sage"
    
    ACCOUNTING_QUICKBOOKS = "accounting_quickbooks"
    ACCOUNTING_XERO = "accounting_xero"
    ACCOUNTING_WAVE = "accounting_wave"
    ACCOUNTING_FRESHBOOKS = "accounting_freshbooks"
    
    CRM_SALESFORCE = "crm_salesforce"
    CRM_HUBSPOT = "crm_hubspot"
    CRM_DYNAMICS = "crm_dynamics"
    CRM_ZOHO = "crm_zoho"
    CRM_PIPEDRIVE = "crm_pipedrive"
    
    POS_SQUARE = "pos_square"
    POS_SHOPIFY = "pos_shopify"
    POS_LIGHTSPEED = "pos_lightspeed"
    POS_CLOVER = "pos_clover"
    POS_TOAST = "pos_toast"
    
    ECOMMERCE_SHOPIFY = "ecommerce_shopify"
    ECOMMERCE_WOOCOMMERCE = "ecommerce_woocommerce"
    ECOMMERCE_MAGENTO = "ecommerce_magento"
    ECOMMERCE_JUMIA = "ecommerce_jumia"


class UBLComplianceResult:
    """Container for UBL compliance results."""
    
    def __init__(self):
        self.success = False
        self.ubl_invoice: Optional[UBLInvoice] = None
        self.validation_result: Optional[ValidationResult] = None
        self.transformation_errors: List[str] = []
        self.compliance_level: str = "unknown"
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            'success': self.success,
            'compliance_level': self.compliance_level,
            'timestamp': self.timestamp.isoformat(),
            'transformation_errors': self.transformation_errors
        }
        
        if self.validation_result:
            result['validation'] = self.validation_result.to_dict()
            
        if self.ubl_invoice:
            result['invoice_id'] = getattr(self.ubl_invoice, 'id', None)
            result['invoice_type'] = getattr(self.ubl_invoice, 'invoice_type_code', None)
            
        return result


class UBLComplianceEngine:
    """
    Central UBL compliance engine for all business systems.
    
    Features:
    - Business system detection and routing
    - Unified UBL transformation pipeline
    - Comprehensive validation framework
    - Nigerian FIRS compliance enforcement
    - Compliance reporting and analytics
    - Error handling and recovery
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize UBL compliance engine.
        
        Args:
            config: Engine configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Transformer and validator registries
        self._transformers: Dict[BusinessSystemType, Type[BaseUBLTransformer]] = {}
        self._validators: Dict[BusinessSystemType, Type[BaseUBLValidator]] = {}
        self._default_validator = BaseUBLValidator
        
        # Compliance settings
        self.strict_mode = self.config.get('strict_mode', True)
        self.nigerian_compliance = self.config.get('nigerian_compliance', True)
        self.auto_correction = self.config.get('auto_correction', False)
        
        self.logger.info("UBL Compliance Engine initialized")
    
    def register_transformer(self, business_system: BusinessSystemType, 
                           transformer_class: Type[BaseUBLTransformer]):
        """
        Register a transformer for a business system.
        
        Args:
            business_system: Business system type
            transformer_class: Transformer class extending BaseUBLTransformer
        """
        self._transformers[business_system] = transformer_class
        self.logger.info(f"Registered transformer for {business_system.value}")
    
    def register_validator(self, business_system: BusinessSystemType,
                          validator_class: Type[BaseUBLValidator]):
        """
        Register a validator for a business system.
        
        Args:
            business_system: Business system type
            validator_class: Validator class extending BaseUBLValidator
        """
        self._validators[business_system] = validator_class
        self.logger.info(f"Registered validator for {business_system.value}")
    
    def process_invoice(self, business_system: BusinessSystemType,
                       invoice_data: Dict[str, Any],
                       business_system_info: Dict[str, Any]) -> UBLComplianceResult:
        """
        Complete UBL processing pipeline for business system invoice.
        
        Args:
            business_system: Type of business system
            invoice_data: Raw invoice data from business system
            business_system_info: Business system configuration
            
        Returns:
            UBLComplianceResult: Complete processing results
        """
        result = UBLComplianceResult()
        
        try:
            # 1. Transform invoice to UBL format
            self.logger.info(f"Processing {business_system.value} invoice: {invoice_data.get('id', 'unknown')}")
            
            ubl_invoice = self._transform_invoice(
                business_system, invoice_data, business_system_info
            )
            result.ubl_invoice = ubl_invoice
            
            # 2. Validate UBL invoice
            validation_result = self._validate_invoice(business_system, ubl_invoice)
            result.validation_result = validation_result
            
            # 3. Determine compliance level
            result.compliance_level = self._determine_compliance_level(validation_result)
            
            # 4. Auto-correction if enabled and needed
            if self.auto_correction and not validation_result.is_valid:
                corrected_invoice = self._attempt_auto_correction(ubl_invoice, validation_result)
                if corrected_invoice:
                    result.ubl_invoice = corrected_invoice
                    # Re-validate corrected invoice
                    result.validation_result = self._validate_invoice(business_system, corrected_invoice)
                    result.compliance_level = self._determine_compliance_level(result.validation_result)
            
            # 5. Final success determination
            if self.strict_mode:
                result.success = validation_result.is_valid
            else:
                result.success = len(validation_result.errors) == 0  # Warnings allowed
                
        except UBLTransformationError as e:
            result.transformation_errors.append(str(e))
            self.logger.error(f"UBL transformation failed: {str(e)}")
            
        except Exception as e:
            result.transformation_errors.append(f"Unexpected error: {str(e)}")
            self.logger.error(f"UBL processing error: {str(e)}")
        
        self.logger.info(f"UBL processing completed: success={result.success}, level={result.compliance_level}")
        return result
    
    def validate_existing_ubl(self, business_system: BusinessSystemType,
                             ubl_invoice: UBLInvoice) -> ValidationResult:
        """
        Validate an existing UBL invoice.
        
        Args:
            business_system: Type of business system (for system-specific rules)
            ubl_invoice: UBL invoice to validate
            
        Returns:
            ValidationResult: Validation results
        """
        return self._validate_invoice(business_system, ubl_invoice)
    
    def get_supported_systems(self) -> List[BusinessSystemType]:
        """Get list of business systems with registered transformers."""
        return list(self._transformers.keys())
    
    def get_compliance_summary(self, results: List[UBLComplianceResult]) -> Dict[str, Any]:
        """
        Generate compliance summary from multiple results.
        
        Args:
            results: List of UBL compliance results
            
        Returns:
            Dict: Compliance summary statistics
        """
        if not results:
            return {'total': 0, 'success_rate': 0.0}
        
        total = len(results)
        successful = sum(1 for r in results if r.success)
        
        # Compliance level distribution
        levels = {}
        for result in results:
            level = result.compliance_level
            levels[level] = levels.get(level, 0) + 1
        
        # Common errors
        all_errors = []
        for result in results:
            if result.validation_result:
                all_errors.extend(result.validation_result.errors)
            all_errors.extend(result.transformation_errors)
        
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        return {
            'total': total,
            'successful': successful,
            'success_rate': (successful / total) * 100,
            'compliance_levels': levels,
            'common_errors': dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def _transform_invoice(self, business_system: BusinessSystemType,
                          invoice_data: Dict[str, Any],
                          business_system_info: Dict[str, Any]) -> UBLInvoice:
        """Transform business system invoice to UBL format."""
        transformer_class = self._transformers.get(business_system)
        
        if not transformer_class:
            raise UBLTransformationError(f"No transformer registered for {business_system.value}")
        
        transformer = transformer_class(business_system_info)
        return transformer.transform_invoice(invoice_data)
    
    def _validate_invoice(self, business_system: BusinessSystemType,
                         ubl_invoice: UBLInvoice) -> ValidationResult:
        """Validate UBL invoice using system-specific or default validator."""
        validator_class = self._validators.get(business_system, self._default_validator)
        
        validator_config = {
            'strict_compliance': self.strict_mode,
            'nigerian_compliance': self.nigerian_compliance
        }
        
        validator = validator_class(validator_config)
        return validator.validate_invoice(ubl_invoice)
    
    def _determine_compliance_level(self, validation_result: ValidationResult) -> str:
        """Determine compliance level based on validation results."""
        if validation_result.is_valid:
            if len(validation_result.warnings) == 0:
                return "full_compliance"
            else:
                return "compliant_with_warnings"
        else:
            if len(validation_result.errors) <= 2:
                return "minor_issues"
            elif len(validation_result.errors) <= 5:
                return "major_issues"
            else:
                return "non_compliant"
    
    def _attempt_auto_correction(self, ubl_invoice: UBLInvoice,
                               validation_result: ValidationResult) -> Optional[UBLInvoice]:
        """
        Attempt automatic correction of common UBL issues.
        
        Args:
            ubl_invoice: Original UBL invoice
            validation_result: Validation results with errors
            
        Returns:
            Optional[UBLInvoice]: Corrected invoice if successful
        """
        # This is a placeholder for auto-correction logic
        # In practice, this would implement common corrections like:
        # - Setting default values for missing required fields
        # - Correcting number formats
        # - Standardizing currency codes
        # - Fixing date formats
        
        self.logger.info("Auto-correction attempted (placeholder implementation)")
        return None  # No correction applied in this version