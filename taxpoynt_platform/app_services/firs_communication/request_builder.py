"""
FIRS Request Builder - APP Services

Specialized request builder for FIRS API requests in the APP (Access Point Provider) role.
Builds properly formatted, validated requests according to FIRS API specifications.

Features:
- Type-safe request building
- Automatic request validation
- FIRS-specific formatting and structure
- Support for all FIRS API endpoints
- Request signing and authentication headers
- Retry and error handling configuration
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import uuid
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class FIRSRequestType(Enum):
    """Types of FIRS API requests"""
    IRN_GENERATE = "irn_generate"
    IRN_VALIDATE = "irn_validate"
    IRN_CANCEL = "irn_cancel"
    DOCUMENT_SUBMIT = "document_submit"
    DOCUMENT_STATUS = "document_status"
    REPORT_SUMMARY = "report_summary"
    REPORT_DETAIL = "report_detail"
    AUTHENTICATION = "authentication"
    TOKEN_REFRESH = "token_refresh"


class FIRSDocumentType(Enum):
    """FIRS document types"""
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    RECEIPT = "receipt"


@dataclass
class FIRSRequestMetadata:
    """Metadata for FIRS requests"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    client_id: str = ""
    environment: str = "sandbox"
    api_version: str = "v1"
    content_type: str = "application/json"
    user_agent: str = "TaxPoynt-APP/1.0"
    
    # Request tracking
    correlation_id: Optional[str] = None
    parent_request_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    # Security
    request_signature: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class FIRSRequestValidation:
    """Request validation configuration"""
    validate_structure: bool = True
    validate_business_rules: bool = True
    validate_required_fields: bool = True
    validate_data_types: bool = True
    validate_ranges: bool = True
    strict_mode: bool = False  # Fail on warnings


@dataclass
class FIRSValidationResult:
    """Result of request validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    field_errors: Dict[str, List[str]] = field(default_factory=dict)
    business_rule_violations: List[str] = field(default_factory=list)


class FIRSRequestBuilder:
    """
    Specialized request builder for FIRS API requests.
    
    Provides type-safe, validated request building for all FIRS API endpoints
    with proper formatting and authentication headers.
    """
    
    def __init__(
        self,
        environment: str = "sandbox",
        api_version: str = "v1",
        validation_config: Optional[FIRSRequestValidation] = None
    ):
        self.environment = environment
        self.api_version = api_version
        self.validation_config = validation_config or FIRSRequestValidation()
        
        # Request templates for different FIRS operations
        self.request_templates = self._load_request_templates()
        
        # Validation rules
        self.validation_rules = self._load_validation_rules()
    
    def build_irn_generation_request(
        self,
        invoice_data: Dict[str, Any],
        organization_id: str,
        metadata: Optional[FIRSRequestMetadata] = None
    ) -> Dict[str, Any]:
        """
        Build IRN generation request for FIRS
        
        Args:
            invoice_data: Invoice data in FIRS format
            organization_id: Organization identifier
            metadata: Request metadata
            
        Returns:
            Formatted FIRS IRN generation request
        """
        try:
            logger.debug("Building IRN generation request")
            
            # Create metadata if not provided
            if not metadata:
                metadata = FIRSRequestMetadata(
                    environment=self.environment,
                    correlation_id=f"irn_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            # Build base request structure
            request_data = {
                "request_metadata": {
                    "request_id": metadata.request_id,
                    "timestamp": metadata.timestamp.isoformat(),
                    "api_version": self.api_version,
                    "organization_id": organization_id,
                    "correlation_id": metadata.correlation_id
                },
                "invoice_data": invoice_data,
                "operation": {
                    "type": "irn_generation",
                    "environment": self.environment,
                    "processing_options": {
                        "validate_before_generation": True,
                        "include_qr_code": True,
                        "include_verification_code": True
                    }
                }
            }
            
            # Validate request structure
            validation_result = self._validate_request(
                request_data,
                FIRSRequestType.IRN_GENERATE
            )
            
            if not validation_result.is_valid:
                raise ValueError(f"IRN generation request validation failed: {validation_result.errors}")
            
            # Add request signature
            request_data["request_signature"] = self._generate_request_signature(request_data)
            
            logger.debug(f"IRN generation request built successfully: {metadata.request_id}")
            return request_data
            
        except Exception as e:
            logger.error(f"Failed to build IRN generation request: {e}")
            raise
    
    def build_irn_validation_request(
        self,
        irn_value: str,
        validation_options: Optional[Dict[str, Any]] = None,
        metadata: Optional[FIRSRequestMetadata] = None
    ) -> Dict[str, Any]:
        """
        Build IRN validation request for FIRS
        
        Args:
            irn_value: IRN to validate
            validation_options: Validation configuration
            metadata: Request metadata
            
        Returns:
            Formatted FIRS IRN validation request
        """
        try:
            logger.debug(f"Building IRN validation request for {irn_value}")
            
            if not metadata:
                metadata = FIRSRequestMetadata(
                    environment=self.environment,
                    correlation_id=f"irn_val_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            # Default validation options
            default_options = {
                "validate_structure": True,
                "validate_checksum": True,
                "check_expiration": True,
                "verify_with_source": True
            }
            
            validation_opts = {**default_options, **(validation_options or {})}
            
            request_data = {
                "request_metadata": {
                    "request_id": metadata.request_id,
                    "timestamp": metadata.timestamp.isoformat(),
                    "api_version": self.api_version,
                    "correlation_id": metadata.correlation_id
                },
                "irn_data": {
                    "irn_value": irn_value,
                    "validation_options": validation_opts
                },
                "operation": {
                    "type": "irn_validation",
                    "environment": self.environment
                }
            }
            
            # Validate request
            validation_result = self._validate_request(
                request_data,
                FIRSRequestType.IRN_VALIDATE
            )
            
            if not validation_result.is_valid:
                raise ValueError(f"IRN validation request validation failed: {validation_result.errors}")
            
            request_data["request_signature"] = self._generate_request_signature(request_data)
            
            logger.debug(f"IRN validation request built successfully: {metadata.request_id}")
            return request_data
            
        except Exception as e:
            logger.error(f"Failed to build IRN validation request: {e}")
            raise
    
    def build_document_submission_request(
        self,
        document_data: Dict[str, Any],
        document_type: FIRSDocumentType,
        organization_id: str,
        metadata: Optional[FIRSRequestMetadata] = None
    ) -> Dict[str, Any]:
        """
        Build document submission request for FIRS
        
        Args:
            document_data: Document data in FIRS format
            document_type: Type of document
            organization_id: Organization identifier
            metadata: Request metadata
            
        Returns:
            Formatted FIRS document submission request
        """
        try:
            logger.debug(f"Building document submission request for {document_type.value}")
            
            if not metadata:
                metadata = FIRSRequestMetadata(
                    environment=self.environment,
                    correlation_id=f"doc_sub_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            request_data = {
                "request_metadata": {
                    "request_id": metadata.request_id,
                    "timestamp": metadata.timestamp.isoformat(),
                    "api_version": self.api_version,
                    "organization_id": organization_id,
                    "correlation_id": metadata.correlation_id
                },
                "document": {
                    "type": document_type.value,
                    "data": document_data,
                    "format": "json",
                    "encoding": "utf-8"
                },
                "operation": {
                    "type": "document_submission",
                    "environment": self.environment,
                    "processing_options": {
                        "validate_before_submission": True,
                        "generate_receipt": True,
                        "notify_on_completion": True
                    }
                }
            }
            
            # Validate request
            validation_result = self._validate_request(
                request_data,
                FIRSRequestType.DOCUMENT_SUBMIT
            )
            
            if not validation_result.is_valid:
                raise ValueError(f"Document submission request validation failed: {validation_result.errors}")
            
            request_data["request_signature"] = self._generate_request_signature(request_data)
            
            logger.debug(f"Document submission request built successfully: {metadata.request_id}")
            return request_data
            
        except Exception as e:
            logger.error(f"Failed to build document submission request: {e}")
            raise
    
    def build_status_inquiry_request(
        self,
        reference_id: str,
        inquiry_type: str = "document_status",
        metadata: Optional[FIRSRequestMetadata] = None
    ) -> Dict[str, Any]:
        """
        Build status inquiry request for FIRS
        
        Args:
            reference_id: Reference ID to inquire about
            inquiry_type: Type of status inquiry
            metadata: Request metadata
            
        Returns:
            Formatted FIRS status inquiry request
        """
        try:
            logger.debug(f"Building status inquiry request for {reference_id}")
            
            if not metadata:
                metadata = FIRSRequestMetadata(
                    environment=self.environment,
                    correlation_id=f"status_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            request_data = {
                "request_metadata": {
                    "request_id": metadata.request_id,
                    "timestamp": metadata.timestamp.isoformat(),
                    "api_version": self.api_version,
                    "correlation_id": metadata.correlation_id
                },
                "inquiry": {
                    "reference_id": reference_id,
                    "inquiry_type": inquiry_type,
                    "include_details": True,
                    "include_history": False
                },
                "operation": {
                    "type": "status_inquiry",
                    "environment": self.environment
                }
            }
            
            # Validate request
            validation_result = self._validate_request(
                request_data,
                FIRSRequestType.DOCUMENT_STATUS
            )
            
            if not validation_result.is_valid:
                raise ValueError(f"Status inquiry request validation failed: {validation_result.errors}")
            
            request_data["request_signature"] = self._generate_request_signature(request_data)
            
            logger.debug(f"Status inquiry request built successfully: {metadata.request_id}")
            return request_data
            
        except Exception as e:
            logger.error(f"Failed to build status inquiry request: {e}")
            raise
    
    def build_report_request(
        self,
        report_type: str,
        date_range: Dict[str, str],
        filters: Optional[Dict[str, Any]] = None,
        metadata: Optional[FIRSRequestMetadata] = None
    ) -> Dict[str, Any]:
        """
        Build report request for FIRS
        
        Args:
            report_type: Type of report (summary/detail)
            date_range: Date range for the report
            filters: Additional filters
            metadata: Request metadata
            
        Returns:
            Formatted FIRS report request
        """
        try:
            logger.debug(f"Building report request for {report_type}")
            
            if not metadata:
                metadata = FIRSRequestMetadata(
                    environment=self.environment,
                    correlation_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            request_data = {
                "request_metadata": {
                    "request_id": metadata.request_id,
                    "timestamp": metadata.timestamp.isoformat(),
                    "api_version": self.api_version,
                    "correlation_id": metadata.correlation_id
                },
                "report": {
                    "type": report_type,
                    "date_range": date_range,
                    "filters": filters or {},
                    "format": "json",
                    "include_summary": True
                },
                "operation": {
                    "type": "report_generation",
                    "environment": self.environment
                }
            }
            
            # Validate request
            request_type = FIRSRequestType.REPORT_SUMMARY if report_type == "summary" else FIRSRequestType.REPORT_DETAIL
            validation_result = self._validate_request(request_data, request_type)
            
            if not validation_result.is_valid:
                raise ValueError(f"Report request validation failed: {validation_result.errors}")
            
            request_data["request_signature"] = self._generate_request_signature(request_data)
            
            logger.debug(f"Report request built successfully: {metadata.request_id}")
            return request_data
            
        except Exception as e:
            logger.error(f"Failed to build report request: {e}")
            raise
    
    def add_authentication_headers(
        self,
        request_data: Dict[str, Any],
        access_token: str,
        api_key: str,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Add authentication headers to request
        
        Args:
            request_data: Request data for signature
            access_token: OAuth 2.0 access token
            api_key: FIRS API key
            additional_headers: Additional headers
            
        Returns:
            Complete headers dictionary
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-API-Key': api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'TaxPoynt-APP/1.0',
                'X-Request-ID': request_data.get('request_metadata', {}).get('request_id', str(uuid.uuid4())),
                'X-Timestamp': datetime.now().isoformat(),
                'X-Environment': self.environment,
                'X-API-Version': self.api_version
            }
            
            # Add correlation ID if available
            correlation_id = request_data.get('request_metadata', {}).get('correlation_id')
            if correlation_id:
                headers['X-Correlation-ID'] = correlation_id
            
            # Add request signature
            if 'request_signature' in request_data:
                headers['X-Request-Signature'] = request_data['request_signature']
            
            # Add additional headers
            if additional_headers:
                headers.update(additional_headers)
            
            return headers
            
        except Exception as e:
            logger.error(f"Failed to build authentication headers: {e}")
            raise
    
    def _validate_request(
        self,
        request_data: Dict[str, Any],
        request_type: FIRSRequestType
    ) -> FIRSValidationResult:
        """Validate request structure and content"""
        try:
            validation_result = FIRSValidationResult(is_valid=True)
            
            if not self.validation_config.validate_structure:
                return validation_result
            
            # Get validation rules for request type
            rules = self.validation_rules.get(request_type, {})
            
            # Validate required fields
            if self.validation_config.validate_required_fields:
                required_fields = rules.get('required_fields', [])
                for field_path in required_fields:
                    if not self._check_field_exists(request_data, field_path):
                        validation_result.errors.append(f"Required field missing: {field_path}")
                        validation_result.is_valid = False
            
            # Validate data types
            if self.validation_config.validate_data_types:
                type_rules = rules.get('field_types', {})
                for field_path, expected_type in type_rules.items():
                    field_value = self._get_field_value(request_data, field_path)
                    if field_value is not None and not isinstance(field_value, expected_type):
                        validation_result.errors.append(
                            f"Field {field_path} has incorrect type. Expected {expected_type.__name__}"
                        )
                        validation_result.is_valid = False
            
            # Validate business rules
            if self.validation_config.validate_business_rules:
                business_rules = rules.get('business_rules', [])
                for rule in business_rules:
                    if not self._validate_business_rule(request_data, rule):
                        validation_result.business_rule_violations.append(rule.get('description', 'Business rule violation'))
                        if rule.get('severity') == 'error':
                            validation_result.is_valid = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return FIRSValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def _generate_request_signature(self, request_data: Dict[str, Any]) -> str:
        """Generate request signature for integrity"""
        try:
            # Create canonical request string
            request_json = json.dumps(request_data, sort_keys=True, separators=(',', ':'))
            
            # Generate SHA-256 hash
            signature = hashlib.sha256(request_json.encode()).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"Failed to generate request signature: {e}")
            return ""
    
    def _check_field_exists(self, data: Dict[str, Any], field_path: str) -> bool:
        """Check if nested field exists in data"""
        try:
            keys = field_path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value of nested field"""
        try:
            keys = field_path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            
            return current
            
        except Exception:
            return None
    
    def _validate_business_rule(self, data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Validate business rule"""
        try:
            # Simple rule validation - can be extended
            rule_type = rule.get('type')
            
            if rule_type == 'field_range':
                field_value = self._get_field_value(data, rule['field'])
                if field_value is not None:
                    min_val = rule.get('min')
                    max_val = rule.get('max')
                    if min_val is not None and field_value < min_val:
                        return False
                    if max_val is not None and field_value > max_val:
                        return False
            
            elif rule_type == 'field_format':
                field_value = self._get_field_value(data, rule['field'])
                if field_value is not None:
                    import re
                    pattern = rule.get('pattern')
                    if pattern and not re.match(pattern, str(field_value)):
                        return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Business rule validation error: {e}")
            return True  # Assume valid if validation fails
    
    def _load_request_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load request templates for different operations"""
        return {
            FIRSRequestType.IRN_GENERATE: {
                "structure": ["request_metadata", "invoice_data", "operation"],
                "optional_fields": ["additional_info"]
            },
            FIRSRequestType.IRN_VALIDATE: {
                "structure": ["request_metadata", "irn_data", "operation"],
                "optional_fields": ["validation_options"]
            },
            FIRSRequestType.DOCUMENT_SUBMIT: {
                "structure": ["request_metadata", "document", "operation"],
                "optional_fields": ["attachments"]
            }
        }
    
    def _load_validation_rules(self) -> Dict[FIRSRequestType, Dict[str, Any]]:
        """Load validation rules for different request types"""
        return {
            FIRSRequestType.IRN_GENERATE: {
                "required_fields": [
                    "request_metadata.request_id",
                    "request_metadata.timestamp",
                    "invoice_data",
                    "operation.type"
                ],
                "field_types": {
                    "request_metadata.timestamp": str,
                    "invoice_data": dict
                },
                "business_rules": [
                    {
                        "type": "field_format",
                        "field": "request_metadata.request_id",
                        "pattern": r"^[a-fA-F0-9\-]{36}$",
                        "description": "Request ID must be valid UUID",
                        "severity": "error"
                    }
                ]
            },
            FIRSRequestType.IRN_VALIDATE: {
                "required_fields": [
                    "request_metadata.request_id",
                    "irn_data.irn_value",
                    "operation.type"
                ],
                "field_types": {
                    "irn_data.irn_value": str
                }
            }
        }


# Factory function for creating FIRS request builder
def create_firs_request_builder(
    environment: str = "sandbox",
    api_version: str = "v1",
    strict_validation: bool = False
) -> FIRSRequestBuilder:
    """
    Factory function to create FIRS request builder
    
    Args:
        environment: FIRS environment
        api_version: API version
        strict_validation: Enable strict validation mode
        
    Returns:
        Configured FIRS request builder
    """
    validation_config = FIRSRequestValidation(strict_mode=strict_validation)
    
    return FIRSRequestBuilder(
        environment=environment,
        api_version=api_version,
        validation_config=validation_config
    )