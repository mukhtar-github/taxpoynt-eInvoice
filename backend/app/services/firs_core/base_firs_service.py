"""
FIRS Base Service Foundation

This module provides the abstract base class for all FIRS-compliant services
in the TaxPoynt e-Invoice platform, ensuring consistent FIRS compliance
across all service implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
import hashlib
from datetime import datetime
from enum import Enum

from app.services.firs_core.audit_service import AuditService
from app.services.firs_core.firs_api_client import FIRSService


class FIRSComplianceError(Exception):
    """Exception raised for FIRS compliance violations"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code or "COMPLIANCE_ERROR"
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()


class FIRSComplianceStatus(str, Enum):
    """FIRS compliance status enumeration"""
    PENDING = "PENDING"
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNKNOWN = "UNKNOWN"


class FIRSBaseService(ABC):
    """
    Base class for all FIRS-compliant services
    
    Ensures consistent FIRS compliance across all service implementations
    by providing common validation, audit, and logging functionality.
    
    All services that interact with FIRS API or handle FIRS-related
    operations should inherit from this base class.
    """

    def __init__(self, audit_service: Optional[AuditService] = None):
        """
        Initialize the FIRS base service
        
        Args:
            audit_service: Optional audit service instance for logging
        """
        self.firs_api_version = "2025.1"
        self.logger = logging.getLogger(f"firs.{self.__class__.__name__}")
        self.audit_trail = []
        self.audit_service = audit_service
        
        # Initialize FIRS API client
        self.firs_client = FIRSService()
        
        # Service identification
        self.service_name = self.__class__.__name__
        self.service_version = "1.0.0"
        
        self.logger.info(f"FIRS service initialized: {self.service_name} v{self.service_version}")

    async def validate_firs_compliance(
        self, 
        operation: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate operation against FIRS compliance requirements
        
        Args:
            operation: Name of the operation being validated
            data: Data to validate for FIRS compliance
            
        Returns:
            Dictionary containing compliance validation results
        """
        compliance_check = {
            'operation': operation,
            'service': self.service_name,
            'timestamp': datetime.utcnow().isoformat(),
            'firs_api_version': self.firs_api_version,
            'compliance_status': FIRSComplianceStatus.PENDING,
            'validation_errors': [],
            'warnings': []
        }

        try:
            self.logger.debug(f"Starting FIRS compliance validation for operation: {operation}")
            
            # Check FIRS API version compatibility
            if not await self._check_firs_api_compatibility(data):
                raise FIRSComplianceError(
                    "API version incompatibility detected",
                    error_code="API_VERSION_INCOMPATIBLE"
                )

            # Validate required FIRS fields
            field_validation = await self._validate_required_firs_fields(operation, data)
            if not field_validation['is_valid']:
                compliance_check['validation_errors'].extend(field_validation['errors'])
                raise FIRSComplianceError(
                    "Missing required FIRS fields",
                    error_code="MISSING_REQUIRED_FIELDS",
                    details=field_validation
                )

            # Check FIRS business rules
            business_rule_validation = await self._validate_firs_business_rules(operation, data)
            if not business_rule_validation['is_valid']:
                compliance_check['validation_errors'].extend(business_rule_validation['errors'])
                raise FIRSComplianceError(
                    "FIRS business rule violation",
                    error_code="BUSINESS_RULE_VIOLATION",
                    details=business_rule_validation
                )

            # Additional service-specific validation
            service_validation = await self._validate_service_specific_rules(operation, data)
            if not service_validation['is_valid']:
                compliance_check['validation_errors'].extend(service_validation['errors'])
                compliance_check['warnings'].extend(service_validation.get('warnings', []))
                
                if service_validation.get('is_critical', False):
                    raise FIRSComplianceError(
                        "Service-specific validation failed",
                        error_code="SERVICE_VALIDATION_FAILED",
                        details=service_validation
                    )

            compliance_check['compliance_status'] = FIRSComplianceStatus.COMPLIANT
            self.logger.info(f"FIRS compliance validation successful for operation: {operation}")

        except FIRSComplianceError as e:
            compliance_check['compliance_status'] = FIRSComplianceStatus.NON_COMPLIANT
            compliance_check['error'] = str(e)
            compliance_check['error_code'] = e.error_code
            compliance_check['error_details'] = e.details
            self.logger.error(f"FIRS compliance validation failed for {operation}: {str(e)}")
            
        except Exception as e:
            compliance_check['compliance_status'] = FIRSComplianceStatus.VALIDATION_FAILED
            compliance_check['error'] = f"Unexpected validation error: {str(e)}"
            compliance_check['error_code'] = "VALIDATION_SYSTEM_ERROR"
            self.logger.error(f"Unexpected error during FIRS compliance validation: {str(e)}", exc_info=True)

        # Add to audit trail
        self.audit_trail.append(compliance_check)

        return compliance_check

    async def log_firs_operation(
        self,
        operation: str,
        organization_id: UUID,
        data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Log FIRS operation for audit purposes
        
        Args:
            operation: Name of the operation performed
            organization_id: UUID of the organization
            data: Input data for the operation
            result: Result of the operation
        """
        audit_entry = {
            'service': self.service_name,
            'operation': operation,
            'organization_id': str(organization_id),
            'timestamp': datetime.utcnow().isoformat(),
            'input_data_hash': self._calculate_data_hash(data),
            'result_status': result.get('status', 'UNKNOWN'),
            'firs_compliant': result.get('firs_compliant', False),
            'firs_api_version': self.firs_api_version,
            'service_version': self.service_version
        }

        # Store in FIRS audit database if audit service is available
        if self.audit_service:
            try:
                await self._store_firs_audit_entry(audit_entry)
            except Exception as e:
                self.logger.error(f"Failed to store FIRS audit entry: {str(e)}")

        self.logger.info(f"FIRS operation logged: {operation}", extra=audit_entry)

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of input data for audit purposes"""
        try:
            # Convert data to a stable string representation
            data_str = str(sorted(data.items()))
            return hashlib.sha256(data_str.encode()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Error calculating data hash: {str(e)}")
            return "HASH_ERROR"

    async def _check_firs_api_compatibility(self, data: Dict[str, Any]) -> bool:
        """Check if data is compatible with current FIRS API version"""
        try:
            # Check for version-specific fields or formats
            required_version_fields = ['business_id', 'irn', 'invoice_type_code']
            
            # Basic compatibility check
            for field in required_version_fields:
                if field in data:
                    # Validate field format based on API version
                    if not self._validate_field_format(field, data[field]):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking FIRS API compatibility: {str(e)}")
            return False

    async def _validate_required_firs_fields(
        self, 
        operation: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate required FIRS fields based on operation type"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'operation': operation
        }
        
        try:
            # Define required fields per operation type
            required_fields_map = {
                'invoice_submission': [
                    'business_id', 'irn', 'issue_date', 'invoice_type_code',
                    'document_currency_code', 'accounting_supplier_party',
                    'accounting_customer_party', 'legal_monetary_total', 'invoice_line'
                ],
                'irn_validation': ['business_id', 'irn', 'invoice_reference'],
                'invoice_validation': ['business_id', 'invoice_number', 'invoice_type_code'],
                'party_creation': ['party_name', 'party_type', 'tax_identifier'],
                'entity_lookup': ['entity_id']
            }
            
            required_fields = required_fields_map.get(operation, [])
            
            for field in required_fields:
                if field not in data:
                    validation_result['errors'].append({
                        'field': field,
                        'error': f"Required field '{field}' is missing",
                        'error_code': 'MISSING_REQUIRED_FIELD'
                    })
                elif not data[field]:
                    validation_result['errors'].append({
                        'field': field,
                        'error': f"Required field '{field}' is empty",
                        'error_code': 'EMPTY_REQUIRED_FIELD'
                    })
            
            if validation_result['errors']:
                validation_result['is_valid'] = False
                
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append({
                'error': f"Field validation error: {str(e)}",
                'error_code': 'FIELD_VALIDATION_ERROR'
            })
            
        return validation_result

    async def _validate_firs_business_rules(
        self, 
        operation: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate FIRS business rules based on operation type"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'operation': operation
        }
        
        try:
            # Currency validation
            if 'document_currency_code' in data:
                if not self._validate_currency_code(data['document_currency_code']):
                    validation_result['errors'].append({
                        'field': 'document_currency_code',
                        'error': 'Invalid currency code',
                        'error_code': 'INVALID_CURRENCY_CODE'
                    })
            
            # Date validation
            if 'issue_date' in data:
                if not self._validate_date_format(data['issue_date']):
                    validation_result['errors'].append({
                        'field': 'issue_date',
                        'error': 'Invalid date format',
                        'error_code': 'INVALID_DATE_FORMAT'
                    })
            
            # Invoice type validation
            if 'invoice_type_code' in data:
                if not self._validate_invoice_type_code(data['invoice_type_code']):
                    validation_result['errors'].append({
                        'field': 'invoice_type_code',
                        'error': 'Invalid invoice type code',
                        'error_code': 'INVALID_INVOICE_TYPE'
                    })
            
            # Tax identifier validation
            if 'tax_identifier' in data:
                if not self._validate_tax_identifier(data['tax_identifier']):
                    validation_result['errors'].append({
                        'field': 'tax_identifier',
                        'error': 'Invalid tax identifier format',
                        'error_code': 'INVALID_TAX_IDENTIFIER'
                    })
            
            if validation_result['errors']:
                validation_result['is_valid'] = False
                
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append({
                'error': f"Business rule validation error: {str(e)}",
                'error_code': 'BUSINESS_RULE_VALIDATION_ERROR'
            })
            
        return validation_result

    @abstractmethod
    async def _validate_service_specific_rules(
        self, 
        operation: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate service-specific rules - must be implemented by subclasses
        
        Args:
            operation: Name of the operation being validated
            data: Data to validate
            
        Returns:
            Dictionary with validation results containing:
            - is_valid: boolean
            - errors: list of error objects
            - warnings: list of warning objects
            - is_critical: boolean indicating if failures are critical
        """
        pass

    async def _store_firs_audit_entry(self, audit_entry: Dict[str, Any]) -> None:
        """Store FIRS audit entry in database"""
        try:
            if self.audit_service:
                # Use the audit service to store the entry
                await self.audit_service.log_transmission_action(
                    action_type="FIRS_OPERATION",
                    organization_id=audit_entry.get('organization_id'),
                    action_status=audit_entry.get('result_status', 'UNKNOWN'),
                    context_data=audit_entry
                )
        except Exception as e:
            self.logger.error(f"Failed to store FIRS audit entry: {str(e)}")

    def _validate_field_format(self, field: str, value: Any) -> bool:
        """Validate field format based on FIRS requirements"""
        try:
            if field == 'business_id':
                # Business ID should be alphanumeric
                return isinstance(value, str) and value.isalnum()
            elif field == 'irn':
                # IRN should follow specific format
                return isinstance(value, str) and len(value) >= 10
            elif field == 'invoice_type_code':
                # Invoice type codes are numeric
                return isinstance(value, str) and value.isdigit()
            else:
                return True
        except Exception:
            return False

    def _validate_currency_code(self, currency_code: str) -> bool:
        """Validate currency code format (ISO 4217)"""
        try:
            return (
                isinstance(currency_code, str) and 
                len(currency_code) == 3 and 
                currency_code.isalpha() and
                currency_code.isupper()
            )
        except Exception:
            return False

    def _validate_date_format(self, date_str: str) -> bool:
        """Validate date format (ISO 8601)"""
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except Exception:
            return False

    def _validate_invoice_type_code(self, invoice_type_code: str) -> bool:
        """Validate invoice type code against FIRS allowed values"""
        try:
            allowed_codes = ['380', '381', '383', '325', '389']  # Common FIRS invoice types
            return invoice_type_code in allowed_codes
        except Exception:
            return False

    def _validate_tax_identifier(self, tax_identifier: str) -> bool:
        """Validate tax identifier format"""
        try:
            # Basic validation - should be alphanumeric with minimum length
            return (
                isinstance(tax_identifier, str) and 
                len(tax_identifier) >= 8 and
                tax_identifier.replace('-', '').isalnum()
            )
        except Exception:
            return False

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get the current audit trail for this service instance"""
        return self.audit_trail.copy()

    def clear_audit_trail(self) -> None:
        """Clear the audit trail"""
        self.audit_trail.clear()
        self.logger.debug("Audit trail cleared")

    def get_service_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            'service_name': self.service_name,
            'service_version': self.service_version,
            'firs_api_version': self.firs_api_version,
            'audit_trail_length': len(self.audit_trail),
            'initialized_at': datetime.utcnow().isoformat()
        }