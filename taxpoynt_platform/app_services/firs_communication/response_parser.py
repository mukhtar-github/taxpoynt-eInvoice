"""
FIRS Response Parser - APP Services

Specialized response parser for FIRS API responses in the APP (Access Point Provider) role.
Parses and interprets FIRS API responses with proper error handling and data extraction.

Features:
- Type-safe response parsing
- Comprehensive error handling
- FIRS-specific response interpretation
- Automatic validation of response structure
- Business rule validation
- Response caching and optimization
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class FIRSResponseStatus(Enum):
    """FIRS response status codes"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SYSTEM_ERROR = "system_error"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class FIRSErrorCode(Enum):
    """FIRS error codes"""
    # Authentication errors
    AUTH_INVALID_TOKEN = "AUTH_001"
    AUTH_EXPIRED_TOKEN = "AUTH_002"
    AUTH_INVALID_SIGNATURE = "AUTH_003"
    AUTH_MISSING_CREDENTIALS = "AUTH_004"
    
    # Validation errors
    VAL_INVALID_FORMAT = "VAL_001"
    VAL_MISSING_FIELD = "VAL_002"
    VAL_INVALID_VALUE = "VAL_003"
    VAL_BUSINESS_RULE = "VAL_004"
    
    # Processing errors
    PROC_IRN_EXISTS = "PROC_001"
    PROC_INVALID_IRN = "PROC_002"
    PROC_DOCUMENT_ERROR = "PROC_003"
    PROC_SYSTEM_ERROR = "PROC_004"
    
    # Rate limiting
    RATE_LIMIT_MINUTE = "RATE_001"
    RATE_LIMIT_HOUR = "RATE_002"
    RATE_LIMIT_DAILY = "RATE_003"
    
    # System errors
    SYS_MAINTENANCE = "SYS_001"
    SYS_OVERLOAD = "SYS_002"
    SYS_TIMEOUT = "SYS_003"


@dataclass
class FIRSError:
    """FIRS error information"""
    code: str
    message: str
    field: Optional[str] = None
    severity: str = "error"  # error, warning, info
    details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)


@dataclass
class FIRSResponseMetadata:
    """Metadata from FIRS response"""
    request_id: str
    response_id: str
    timestamp: datetime
    processing_time_ms: Optional[int] = None
    environment: str = "sandbox"
    api_version: str = "v1"
    server_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    # Rate limiting info
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    
    # Pagination info
    page: Optional[int] = None
    page_size: Optional[int] = None
    total_records: Optional[int] = None
    has_more: bool = False


@dataclass
class ParsedFIRSResponse:
    """Parsed FIRS API response"""
    status: FIRSResponseStatus
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[FIRSError] = field(default_factory=list)
    warnings: List[FIRSError] = field(default_factory=list)
    metadata: Optional[FIRSResponseMetadata] = None
    raw_response: Optional[str] = None
    
    # Specific data fields for common operations
    irn_value: Optional[str] = None
    qr_code: Optional[str] = None
    verification_code: Optional[str] = None
    document_id: Optional[str] = None
    status_info: Optional[Dict[str, Any]] = None
    
    # Business-specific fields
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    invoice_number: Optional[str] = None
    processed_documents: List[Dict[str, Any]] = field(default_factory=list)


class FIRSResponseParser:
    """
    Specialized parser for FIRS API responses.
    
    Provides comprehensive parsing, validation, and interpretation
    of FIRS API responses with proper error handling.
    """
    
    def __init__(
        self,
        environment: str = "sandbox",
        strict_validation: bool = False
    ):
        self.environment = environment
        self.strict_validation = strict_validation
        
        # Response schema definitions
        self.response_schemas = self._load_response_schemas()
        
        # Error code mappings
        self.error_mappings = self._load_error_mappings()
    
    def parse_response(
        self,
        response_data: Dict[str, Any],
        response_headers: Dict[str, str],
        status_code: int,
        raw_response: Optional[str] = None
    ) -> ParsedFIRSResponse:
        """
        Parse FIRS API response
        
        Args:
            response_data: Parsed JSON response data
            response_headers: HTTP response headers
            status_code: HTTP status code
            raw_response: Raw response text
            
        Returns:
            Parsed FIRS response object
        """
        try:
            logger.debug("Parsing FIRS API response")
            
            # Initialize parsed response
            parsed = ParsedFIRSResponse(
                status=self._determine_status(status_code, response_data),
                success=self._is_success_response(status_code, response_data),
                raw_response=raw_response
            )
            
            # Parse metadata
            parsed.metadata = self._parse_metadata(response_data, response_headers)
            
            # Parse main response data
            if parsed.success:
                parsed.data = self._parse_success_data(response_data)
                parsed = self._extract_business_data(parsed, response_data)
            else:
                parsed.errors = self._parse_errors(response_data)
                parsed.warnings = self._parse_warnings(response_data)
            
            # Validate response structure
            if self.strict_validation:
                validation_errors = self._validate_response_structure(response_data)
                if validation_errors:
                    parsed.errors.extend(validation_errors)
                    parsed.success = False
            
            logger.debug(f"Response parsed successfully: {parsed.status.value}")
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse FIRS response: {e}")
            return ParsedFIRSResponse(
                status=FIRSResponseStatus.SYSTEM_ERROR,
                success=False,
                errors=[FIRSError(
                    code="PARSE_001",
                    message=f"Response parsing failed: {str(e)}"
                )],
                raw_response=raw_response
            )
    
    def parse_irn_generation_response(
        self,
        response_data: Dict[str, Any],
        response_headers: Dict[str, str],
        status_code: int
    ) -> ParsedFIRSResponse:
        """Parse IRN generation response specifically"""
        try:
            parsed = self.parse_response(response_data, response_headers, status_code)
            
            if parsed.success and 'irn_data' in response_data:
                irn_data = response_data['irn_data']
                parsed.irn_value = irn_data.get('irn_value')
                parsed.qr_code = irn_data.get('qr_code')
                parsed.verification_code = irn_data.get('verification_code')
                
                # Extract additional IRN metadata
                if 'metadata' in irn_data:
                    metadata = irn_data['metadata']
                    parsed.data.update({
                        'irn_metadata': metadata,
                        'generation_timestamp': metadata.get('generated_at'),
                        'expiry_date': metadata.get('expires_at'),
                        'issuer_info': metadata.get('issuer')
                    })
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse IRN generation response: {e}")
            return ParsedFIRSResponse(
                status=FIRSResponseStatus.SYSTEM_ERROR,
                success=False,
                errors=[FIRSError(
                    code="PARSE_IRN_001",
                    message=f"IRN response parsing failed: {str(e)}"
                )]
            )
    
    def parse_document_submission_response(
        self,
        response_data: Dict[str, Any],
        response_headers: Dict[str, str],
        status_code: int
    ) -> ParsedFIRSResponse:
        """Parse document submission response specifically"""
        try:
            parsed = self.parse_response(response_data, response_headers, status_code)
            
            if parsed.success and 'submission_data' in response_data:
                submission = response_data['submission_data']
                parsed.document_id = submission.get('document_id')
                parsed.status_info = submission.get('status_info', {})
                
                # Extract processing results
                if 'processing_results' in submission:
                    results = submission['processing_results']
                    parsed.processed_documents = results.get('documents', [])
                    parsed.data.update({
                        'processing_summary': results.get('summary', {}),
                        'receipt_id': results.get('receipt_id'),
                        'confirmation_number': results.get('confirmation_number')
                    })
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse document submission response: {e}")
            return ParsedFIRSResponse(
                status=FIRSResponseStatus.SYSTEM_ERROR,
                success=False,
                errors=[FIRSError(
                    code="PARSE_DOC_001",
                    message=f"Document response parsing failed: {str(e)}"
                )]
            )
    
    def parse_status_inquiry_response(
        self,
        response_data: Dict[str, Any],
        response_headers: Dict[str, str],
        status_code: int
    ) -> ParsedFIRSResponse:
        """Parse status inquiry response specifically"""
        try:
            parsed = self.parse_response(response_data, response_headers, status_code)
            
            if parsed.success and 'status_data' in response_data:
                status_data = response_data['status_data']
                parsed.status_info = status_data
                
                # Extract specific status information
                parsed.data.update({
                    'current_status': status_data.get('status'),
                    'last_updated': status_data.get('last_updated'),
                    'processing_stage': status_data.get('processing_stage'),
                    'completion_percentage': status_data.get('completion_percentage'),
                    'estimated_completion': status_data.get('estimated_completion'),
                    'status_history': status_data.get('history', [])
                })
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse status inquiry response: {e}")
            return ParsedFIRSResponse(
                status=FIRSResponseStatus.SYSTEM_ERROR,
                success=False,
                errors=[FIRSError(
                    code="PARSE_STATUS_001",
                    message=f"Status response parsing failed: {str(e)}"
                )]
            )
    
    def parse_report_response(
        self,
        response_data: Dict[str, Any],
        response_headers: Dict[str, str],
        status_code: int
    ) -> ParsedFIRSResponse:
        """Parse report response specifically"""
        try:
            parsed = self.parse_response(response_data, response_headers, status_code)
            
            if parsed.success and 'report_data' in response_data:
                report = response_data['report_data']
                
                # Extract report metadata
                if 'metadata' in report:
                    report_metadata = report['metadata']
                    parsed.data.update({
                        'report_type': report_metadata.get('type'),
                        'date_range': report_metadata.get('date_range'),
                        'generated_at': report_metadata.get('generated_at'),
                        'total_records': report_metadata.get('total_records'),
                        'filters_applied': report_metadata.get('filters')
                    })
                
                # Extract report data
                if 'data' in report:
                    parsed.data['report_records'] = report['data']
                
                # Extract summary information
                if 'summary' in report:
                    summary = report['summary']
                    parsed.data.update({
                        'summary_totals': summary.get('totals', {}),
                        'summary_counts': summary.get('counts', {}),
                        'summary_statistics': summary.get('statistics', {})
                    })
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse report response: {e}")
            return ParsedFIRSResponse(
                status=FIRSResponseStatus.SYSTEM_ERROR,
                success=False,
                errors=[FIRSError(
                    code="PARSE_REPORT_001",
                    message=f"Report response parsing failed: {str(e)}"
                )]
            )
    
    def _determine_status(
        self,
        status_code: int,
        response_data: Dict[str, Any]
    ) -> FIRSResponseStatus:
        """Determine response status from HTTP code and response data"""
        try:
            # Check HTTP status code first
            if status_code == 200:
                # Check for business-level errors in successful HTTP response
                if 'errors' in response_data and response_data['errors']:
                    return FIRSResponseStatus.VALIDATION_ERROR
                elif 'warnings' in response_data and response_data['warnings']:
                    return FIRSResponseStatus.PARTIAL_SUCCESS
                else:
                    return FIRSResponseStatus.SUCCESS
            elif status_code == 401:
                return FIRSResponseStatus.AUTHENTICATION_ERROR
            elif status_code == 403:
                return FIRSResponseStatus.AUTHORIZATION_ERROR
            elif status_code == 429:
                return FIRSResponseStatus.RATE_LIMIT_EXCEEDED
            elif status_code == 503:
                return FIRSResponseStatus.MAINTENANCE
            elif status_code >= 500:
                return FIRSResponseStatus.SYSTEM_ERROR
            elif status_code >= 400:
                return FIRSResponseStatus.VALIDATION_ERROR
            else:
                return FIRSResponseStatus.UNKNOWN
                
        except Exception:
            return FIRSResponseStatus.UNKNOWN
    
    def _is_success_response(
        self,
        status_code: int,
        response_data: Dict[str, Any]
    ) -> bool:
        """Determine if response represents success"""
        try:
            # HTTP level success
            if status_code != 200:
                return False
            
            # Business level success
            status = response_data.get('status', '').lower()
            if status in ['success', 'completed', 'processed']:
                return True
            
            # Check for explicit success indicators
            if response_data.get('success') is True:
                return True
            
            # Check for absence of critical errors
            errors = response_data.get('errors', [])
            if errors:
                # Check if any errors are critical
                for error in errors:
                    if isinstance(error, dict) and error.get('severity') == 'error':
                        return False
            
            return True
            
        except Exception:
            return False
    
    def _parse_metadata(
        self,
        response_data: Dict[str, Any],
        response_headers: Dict[str, str]
    ) -> FIRSResponseMetadata:
        """Parse response metadata"""
        try:
            metadata_section = response_data.get('metadata', {})
            
            # Extract timestamp
            timestamp_str = (
                metadata_section.get('timestamp') or
                response_headers.get('X-Timestamp') or
                datetime.now().isoformat()
            )
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception:
                timestamp = datetime.now()
            
            # Extract rate limiting info
            rate_limit_remaining = None
            rate_limit_reset = None
            
            if 'X-RateLimit-Remaining' in response_headers:
                try:
                    rate_limit_remaining = int(response_headers['X-RateLimit-Remaining'])
                except ValueError:
                    pass
            
            if 'X-RateLimit-Reset' in response_headers:
                try:
                    reset_timestamp = int(response_headers['X-RateLimit-Reset'])
                    rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
                except ValueError:
                    pass
            
            return FIRSResponseMetadata(
                request_id=metadata_section.get('request_id', response_headers.get('X-Request-ID', '')),
                response_id=metadata_section.get('response_id', response_headers.get('X-Response-ID', '')),
                timestamp=timestamp,
                processing_time_ms=metadata_section.get('processing_time_ms'),
                environment=metadata_section.get('environment', self.environment),
                api_version=metadata_section.get('api_version', response_headers.get('X-API-Version', 'v1')),
                server_id=response_headers.get('X-Server-ID'),
                trace_id=response_headers.get('X-Trace-ID'),
                rate_limit_remaining=rate_limit_remaining,
                rate_limit_reset=rate_limit_reset,
                page=metadata_section.get('page'),
                page_size=metadata_section.get('page_size'),
                total_records=metadata_section.get('total_records'),
                has_more=metadata_section.get('has_more', False)
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse response metadata: {e}")
            return FIRSResponseMetadata(
                request_id='',
                response_id='',
                timestamp=datetime.now()
            )
    
    def _parse_success_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse success response data"""
        try:
            data = {}
            
            # Extract main data section
            if 'data' in response_data:
                data.update(response_data['data'])
            
            # Extract result section
            if 'result' in response_data:
                data.update(response_data['result'])
            
            # Extract any additional fields that aren't metadata or errors
            excluded_keys = {'metadata', 'errors', 'warnings', 'status', 'success'}
            for key, value in response_data.items():
                if key not in excluded_keys:
                    data[key] = value
            
            return data
            
        except Exception as e:
            logger.warning(f"Failed to parse success data: {e}")
            return {}
    
    def _parse_errors(self, response_data: Dict[str, Any]) -> List[FIRSError]:
        """Parse error information from response"""
        try:
            errors = []
            error_data = response_data.get('errors', [])
            
            if not isinstance(error_data, list):
                error_data = [error_data]
            
            for error_item in error_data:
                if isinstance(error_item, dict):
                    error = FIRSError(
                        code=error_item.get('code', 'UNKNOWN'),
                        message=error_item.get('message', 'Unknown error'),
                        field=error_item.get('field'),
                        severity=error_item.get('severity', 'error'),
                        details=error_item.get('details'),
                        suggestions=error_item.get('suggestions', [])
                    )
                    errors.append(error)
                elif isinstance(error_item, str):
                    errors.append(FIRSError(
                        code='GENERIC',
                        message=error_item
                    ))
            
            return errors
            
        except Exception as e:
            logger.warning(f"Failed to parse errors: {e}")
            return []
    
    def _parse_warnings(self, response_data: Dict[str, Any]) -> List[FIRSError]:
        """Parse warning information from response"""
        try:
            warnings = []
            warning_data = response_data.get('warnings', [])
            
            if not isinstance(warning_data, list):
                warning_data = [warning_data]
            
            for warning_item in warning_data:
                if isinstance(warning_item, dict):
                    warning = FIRSError(
                        code=warning_item.get('code', 'WARNING'),
                        message=warning_item.get('message', 'Unknown warning'),
                        field=warning_item.get('field'),
                        severity='warning',
                        details=warning_item.get('details'),
                        suggestions=warning_item.get('suggestions', [])
                    )
                    warnings.append(warning)
                elif isinstance(warning_item, str):
                    warnings.append(FIRSError(
                        code='GENERIC_WARNING',
                        message=warning_item,
                        severity='warning'
                    ))
            
            return warnings
            
        except Exception as e:
            logger.warning(f"Failed to parse warnings: {e}")
            return []
    
    def _extract_business_data(
        self,
        parsed: ParsedFIRSResponse,
        response_data: Dict[str, Any]
    ) -> ParsedFIRSResponse:
        """Extract business-specific data fields"""
        try:
            # Extract financial amounts
            if 'tax_amount' in response_data:
                parsed.tax_amount = float(response_data['tax_amount'])
            if 'total_amount' in response_data:
                parsed.total_amount = float(response_data['total_amount'])
            
            # Extract document identifiers
            if 'invoice_number' in response_data:
                parsed.invoice_number = response_data['invoice_number']
            
            # Look for amounts in nested data
            for section in ['data', 'result', 'invoice_data']:
                if section in response_data:
                    section_data = response_data[section]
                    if isinstance(section_data, dict):
                        if 'tax_amount' in section_data and parsed.tax_amount is None:
                            parsed.tax_amount = float(section_data['tax_amount'])
                        if 'total_amount' in section_data and parsed.total_amount is None:
                            parsed.total_amount = float(section_data['total_amount'])
            
            return parsed
            
        except Exception as e:
            logger.warning(f"Failed to extract business data: {e}")
            return parsed
    
    def _validate_response_structure(self, response_data: Dict[str, Any]) -> List[FIRSError]:
        """Validate response structure against expected schema"""
        try:
            errors = []
            
            # Basic structure validation
            if not isinstance(response_data, dict):
                errors.append(FIRSError(
                    code="STRUCT_001",
                    message="Response must be a JSON object"
                ))
                return errors
            
            # Check for required top-level fields in error responses
            if 'errors' in response_data:
                if not isinstance(response_data['errors'], list):
                    errors.append(FIRSError(
                        code="STRUCT_002",
                        message="Errors field must be an array"
                    ))
            
            return errors
            
        except Exception as e:
            logger.warning(f"Response structure validation failed: {e}")
            return []
    
    def _load_response_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load response schema definitions"""
        return {
            "irn_generation": {
                "required_fields": ["irn_data.irn_value"],
                "optional_fields": ["irn_data.qr_code", "irn_data.verification_code"]
            },
            "document_submission": {
                "required_fields": ["submission_data.document_id"],
                "optional_fields": ["submission_data.status_info"]
            }
        }
    
    def _load_error_mappings(self) -> Dict[str, str]:
        """Load error code to message mappings"""
        return {
            "AUTH_001": "Invalid authentication token",
            "AUTH_002": "Authentication token has expired",
            "VAL_001": "Invalid request format",
            "VAL_002": "Required field is missing",
            "PROC_001": "IRN already exists for this invoice",
            "RATE_001": "Rate limit exceeded - too many requests per minute"
        }


# Factory function for creating FIRS response parser
def create_firs_response_parser(
    environment: str = "sandbox",
    strict_validation: bool = False
) -> FIRSResponseParser:
    """
    Factory function to create FIRS response parser
    
    Args:
        environment: FIRS environment
        strict_validation: Enable strict validation mode
        
    Returns:
        Configured FIRS response parser
    """
    return FIRSResponseParser(
        environment=environment,
        strict_validation=strict_validation
    )