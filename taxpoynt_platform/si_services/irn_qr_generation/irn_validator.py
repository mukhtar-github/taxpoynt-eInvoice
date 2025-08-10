"""
IRN Validator

Validates IRN format compliance and business rules.
Ensures IRNs meet FIRS requirements and organizational standards.
"""

import re
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """IRN validation levels"""
    BASIC = "basic"          # Format validation only
    STANDARD = "standard"    # Format + business rules
    STRICT = "strict"        # All validations + compliance checks


@dataclass
class ValidationResult:
    """IRN validation result"""
    is_valid: bool
    validation_level: ValidationLevel
    errors: List[str]
    warnings: List[str]
    irn_info: Optional[Dict[str, Any]] = None


class IRNValidator:
    """Validate IRN format and compliance"""
    
    def __init__(self):
        self.irn_patterns = {
            'standard': r'^IRN\d{14}[A-Z0-9]{8}$',  # IRN + timestamp + unique_id
            'legacy': r'^IRN\d{12}[A-Z0-9]{6}$',    # Legacy format
            'custom': r'^[A-Z]{3}\d{14}[A-Z0-9]{8}$'  # Custom prefix
        }
        
        self.max_irn_age_days = 365  # Maximum age for IRN validity
        self.min_verification_code_length = 6
        self.max_verification_code_length = 12
    
    def validate_irn(
        self,
        irn_value: str,
        verification_code: Optional[str] = None,
        validation_level: ValidationLevel = ValidationLevel.STANDARD,
        organization_rules: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Comprehensive IRN validation
        
        Args:
            irn_value: IRN to validate
            verification_code: Optional verification code
            validation_level: Level of validation to perform
            organization_rules: Organization-specific validation rules
            
        Returns:
            Validation result with details
        """
        errors = []
        warnings = []
        irn_info = {}
        
        # Basic format validation
        format_valid, format_errors = self._validate_format(irn_value)
        errors.extend(format_errors)
        
        if format_valid:
            irn_info = self._extract_irn_info(irn_value)
        
        # Stop here for basic validation
        if validation_level == ValidationLevel.BASIC:
            return ValidationResult(
                is_valid=len(errors) == 0,
                validation_level=validation_level,
                errors=errors,
                warnings=warnings,
                irn_info=irn_info
            )
        
        # Standard validation
        if format_valid:
            business_errors, business_warnings = self._validate_business_rules(
                irn_value, irn_info, organization_rules
            )
            errors.extend(business_errors)
            warnings.extend(business_warnings)
        
        # Verification code validation
        if verification_code:
            verification_errors = self._validate_verification_code(verification_code)
            errors.extend(verification_errors)
        
        # Stop here for standard validation
        if validation_level == ValidationLevel.STANDARD:
            return ValidationResult(
                is_valid=len(errors) == 0,
                validation_level=validation_level,
                errors=errors,
                warnings=warnings,
                irn_info=irn_info
            )
        
        # Strict validation (compliance checks)
        if format_valid:
            compliance_errors, compliance_warnings = self._validate_compliance(
                irn_value, irn_info, verification_code
            )
            errors.extend(compliance_errors)
            warnings.extend(compliance_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            validation_level=validation_level,
            errors=errors,
            warnings=warnings,
            irn_info=irn_info
        )
    
    def validate_irn_batch(
        self,
        irn_list: List[str],
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Dict[str, ValidationResult]:
        """Validate multiple IRNs"""
        results = {}
        
        for irn_value in irn_list:
            results[irn_value] = self.validate_irn(irn_value, validation_level=validation_level)
        
        return results
    
    def check_irn_uniqueness(
        self,
        irn_value: str,
        existing_irns: List[str]
    ) -> Tuple[bool, List[str]]:
        """Check if IRN is unique in the provided list"""
        errors = []
        
        if irn_value in existing_irns:
            errors.append(f"IRN {irn_value} already exists")
            return False, errors
        
        return True, errors
    
    def _validate_format(self, irn_value: str) -> Tuple[bool, List[str]]:
        """Validate IRN format structure"""
        errors = []
        
        if not irn_value:
            errors.append("IRN value is required")
            return False, errors
        
        if not isinstance(irn_value, str):
            errors.append("IRN must be a string")
            return False, errors
        
        # Check against known patterns
        pattern_matched = False
        for pattern_name, pattern in self.irn_patterns.items():
            if re.match(pattern, irn_value):
                pattern_matched = True
                break
        
        if not pattern_matched:
            errors.append(f"IRN format does not match any known pattern: {irn_value}")
            return False, errors
        
        # Additional format checks
        if len(irn_value) < 15:  # Minimum length
            errors.append(f"IRN too short: {len(irn_value)} characters")
        
        if len(irn_value) > 30:  # Maximum length
            errors.append(f"IRN too long: {len(irn_value)} characters")
        
        return len(errors) == 0, errors
    
    def _validate_business_rules(
        self,
        irn_value: str,
        irn_info: Dict[str, Any],
        organization_rules: Optional[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Validate business rules"""
        errors = []
        warnings = []
        
        # Check IRN age
        if 'timestamp' in irn_info:
            irn_age = datetime.now() - irn_info['timestamp']
            if irn_age.days > self.max_irn_age_days:
                warnings.append(f"IRN is {irn_age.days} days old (max recommended: {self.max_irn_age_days})")
        
        # Organization-specific rules
        if organization_rules:
            org_errors, org_warnings = self._validate_organization_rules(
                irn_value, irn_info, organization_rules
            )
            errors.extend(org_errors)
            warnings.extend(org_warnings)
        
        return errors, warnings
    
    def _validate_verification_code(self, verification_code: str) -> List[str]:
        """Validate verification code format"""
        errors = []
        
        if not verification_code:
            errors.append("Verification code is required")
            return errors
        
        if len(verification_code) < self.min_verification_code_length:
            errors.append(f"Verification code too short: {len(verification_code)}")
        
        if len(verification_code) > self.max_verification_code_length:
            errors.append(f"Verification code too long: {len(verification_code)}")
        
        # Check if it's base64-like (alphanumeric + / + =)
        if not re.match(r'^[A-Za-z0-9+/=]+$', verification_code):
            errors.append("Verification code contains invalid characters")
        
        return errors
    
    def _validate_compliance(
        self,
        irn_value: str,
        irn_info: Dict[str, Any],
        verification_code: Optional[str]
    ) -> Tuple[List[str], List[str]]:
        """Validate FIRS compliance requirements"""
        errors = []
        warnings = []
        
        # FIRS-specific validation rules
        
        # 1. IRN must have verification code for compliance
        if not verification_code:
            errors.append("Verification code required for FIRS compliance")
        
        # 2. Check timestamp validity
        if 'timestamp' in irn_info:
            # IRN shouldn't be from future
            if irn_info['timestamp'] > datetime.now():
                errors.append("IRN timestamp is in the future")
            
            # IRN shouldn't be too old for active use
            age = datetime.now() - irn_info['timestamp']
            if age.days > 30:
                warnings.append("IRN is older than 30 days - may need renewal")
        
        # 3. Check prefix compliance
        if not irn_value.startswith('IRN'):
            warnings.append("Non-standard IRN prefix - FIRS prefers 'IRN' prefix")
        
        return errors, warnings
    
    def _validate_organization_rules(
        self,
        irn_value: str,
        irn_info: Dict[str, Any],
        org_rules: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Validate organization-specific rules"""
        errors = []
        warnings = []
        
        # Custom prefix validation
        if 'required_prefix' in org_rules:
            required_prefix = org_rules['required_prefix']
            if not irn_value.startswith(required_prefix):
                errors.append(f"IRN must start with '{required_prefix}'")
        
        # Custom length validation
        if 'max_length' in org_rules:
            max_length = org_rules['max_length']
            if len(irn_value) > max_length:
                errors.append(f"IRN exceeds organization maximum length: {max_length}")
        
        # Time-based rules
        if 'business_hours_only' in org_rules and org_rules['business_hours_only']:
            if 'timestamp' in irn_info:
                hour = irn_info['timestamp'].hour
                if hour < 8 or hour > 18:  # Outside business hours
                    warnings.append("IRN generated outside business hours")
        
        return errors, warnings
    
    def _extract_irn_info(self, irn_value: str) -> Dict[str, Any]:
        """Extract information from IRN structure"""
        irn_info = {
            'irn_value': irn_value,
            'length': len(irn_value),
            'prefix': '',
            'timestamp': None,
            'unique_part': ''
        }
        
        # Extract prefix (first 3 characters typically)
        if len(irn_value) >= 3:
            irn_info['prefix'] = irn_value[:3]
        
        # Try to extract timestamp for standard format
        if re.match(self.irn_patterns['standard'], irn_value):
            try:
                # IRN + 14 digit timestamp + 8 char unique
                timestamp_str = irn_value[3:17]  # Skip 'IRN' prefix
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                irn_info['timestamp'] = timestamp
                irn_info['unique_part'] = irn_value[17:]
            except ValueError:
                pass  # Invalid timestamp format
        
        return irn_info
    
    def get_validation_summary(self, results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Get summary statistics for batch validation"""
        total = len(results)
        valid = sum(1 for result in results.values() if result.is_valid)
        invalid = total - valid
        
        error_counts = {}
        warning_counts = {}
        
        for result in results.values():
            for error in result.errors:
                error_counts[error] = error_counts.get(error, 0) + 1
            
            for warning in result.warnings:
                warning_counts[warning] = warning_counts.get(warning, 0) + 1
        
        return {
            'total_irns': total,
            'valid_irns': valid,
            'invalid_irns': invalid,
            'success_rate': (valid / total * 100) if total > 0 else 0,
            'common_errors': sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'common_warnings': sorted(warning_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }