"""
Stitch Open Banking Exceptions
==============================

Enterprise-grade exception handling for Stitch API operations.
Provides detailed error information, enterprise-specific error codes,
and enhanced error recovery mechanisms.

Exception Hierarchy:
- StitchAPIError: Base exception for all Stitch API errors
  - StitchAuthenticationError: Authentication and authorization failures
  - StitchRateLimitError: Rate limiting and quota exceeded errors
  - StitchWebhookError: Webhook verification and processing errors
  - StitchBulkOperationError: Bulk operation specific errors
  - StitchComplianceError: Compliance and regulatory errors
  - StitchNetworkError: Network connectivity and timeout errors
  - StitchDataError: Data validation and format errors

Enterprise Features:
- Detailed error categorization for enterprise monitoring
- Retry strategy recommendations
- Compliance impact assessment
- Audit trail integration
- Multi-tenant error isolation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class StitchAPIError(Exception):
    """
    Base exception for all Stitch API errors.
    
    Provides comprehensive error information for enterprise monitoring
    and automated error recovery systems.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        retry_after: Optional[int] = None,
        enterprise_context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.response_data = response_data or {}
        self.request_id = request_id
        self.timestamp = timestamp or datetime.now()
        self.retry_after = retry_after
        self.enterprise_context = enterprise_context or {}
        
        # Enterprise-specific fields
        self.tenant_id = self.enterprise_context.get('tenant_id')
        self.organization_id = self.enterprise_context.get('organization_id')
        self.operation_type = self.enterprise_context.get('operation_type')
        self.compliance_impact = self.enterprise_context.get('compliance_impact', 'low')
        self.business_criticality = self.enterprise_context.get('business_criticality', 'medium')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and monitoring"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'status_code': self.status_code,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
            'retry_after': self.retry_after,
            'tenant_id': self.tenant_id,
            'organization_id': self.organization_id,
            'operation_type': self.operation_type,
            'compliance_impact': self.compliance_impact,
            'business_criticality': self.business_criticality,
            'response_data': self.response_data,
            'enterprise_context': self.enterprise_context
        }
    
    def to_json(self) -> str:
        """Convert exception to JSON for structured logging"""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @property
    def is_retryable(self) -> bool:
        """Determine if the error is retryable"""
        # Override in subclasses for specific retry logic
        return self.status_code in [429, 500, 502, 503, 504] if self.status_code else False
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Determine if error requires immediate attention"""
        return (
            self.compliance_impact in ['high', 'critical'] or
            self.business_criticality in ['high', 'critical'] or
            self.status_code in [401, 403]
        )


class StitchAuthenticationError(StitchAPIError):
    """
    Authentication and authorization errors for enterprise customers.
    
    Common scenarios:
    - OAuth 2.0 token expiration
    - Invalid client credentials
    - Insufficient permissions for enterprise operations
    - Certificate validation failures
    """
    
    def __init__(
        self,
        message: str,
        auth_type: str = "oauth2",
        expired_token: bool = False,
        invalid_credentials: bool = False,
        insufficient_permissions: bool = False,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.auth_type = auth_type
        self.expired_token = expired_token
        self.invalid_credentials = invalid_credentials
        self.insufficient_permissions = insufficient_permissions
        
        # Authentication errors are typically retryable if token expired
        self._is_retryable = expired_token
    
    @property
    def is_retryable(self) -> bool:
        """Authentication errors are retryable only if token expired"""
        return self._is_retryable
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Invalid credentials or insufficient permissions require immediate attention"""
        return self.invalid_credentials or self.insufficient_permissions


class StitchRateLimitError(StitchAPIError):
    """
    Rate limiting and quota exceeded errors for enterprise operations.
    
    Enterprise customers may have higher rate limits but still need
    proper handling for burst operations and bulk processing.
    """
    
    def __init__(
        self,
        message: str,
        rate_limit_type: str = "requests_per_minute",
        current_usage: Optional[int] = None,
        limit: Optional[int] = None,
        reset_time: Optional[datetime] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.rate_limit_type = rate_limit_type
        self.current_usage = current_usage
        self.limit = limit
        self.reset_time = reset_time
    
    @property
    def is_retryable(self) -> bool:
        """Rate limit errors are always retryable"""
        return True
    
    @property
    def recommended_retry_delay(self) -> int:
        """Recommend retry delay based on reset time or retry_after"""
        if self.retry_after:
            return self.retry_after
        elif self.reset_time:
            delta = self.reset_time - datetime.now()
            return max(60, int(delta.total_seconds()))
        else:
            return 60  # Default 1 minute


class StitchWebhookError(StitchAPIError):
    """
    Webhook verification and processing errors for enterprise notifications.
    
    Enterprise webhooks have enhanced security and processing requirements.
    """
    
    def __init__(
        self,
        message: str,
        webhook_type: Optional[str] = None,
        signature_verification_failed: bool = False,
        payload_invalid: bool = False,
        processing_failed: bool = False,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.webhook_type = webhook_type
        self.signature_verification_failed = signature_verification_failed
        self.payload_invalid = payload_invalid
        self.processing_failed = processing_failed
    
    @property
    def is_retryable(self) -> bool:
        """Webhook errors are retryable unless signature verification failed"""
        return not self.signature_verification_failed
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Signature verification failures require immediate attention"""
        return self.signature_verification_failed


class StitchBulkOperationError(StitchAPIError):
    """
    Bulk operation specific errors for enterprise customers.
    
    Handles errors related to batch processing, bulk transactions,
    and enterprise-scale operations.
    """
    
    def __init__(
        self,
        message: str,
        operation_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        failed_items: Optional[List[Dict[str, Any]]] = None,
        partial_success: bool = False,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.failed_items = failed_items or []
        self.partial_success = partial_success
    
    @property
    def is_retryable(self) -> bool:
        """Bulk operations with partial success are retryable"""
        return self.partial_success or self.status_code in [500, 502, 503, 504]
    
    @property
    def retry_eligible_items(self) -> List[Dict[str, Any]]:
        """Get items that are eligible for retry"""
        return [
            item for item in self.failed_items
            if item.get('error_code') not in ['INVALID_DATA', 'DUPLICATE_TRANSACTION']
        ]


class StitchComplianceError(StitchAPIError):
    """
    Compliance and regulatory errors for enterprise customers.
    
    Handles errors related to AML, KYC, sanctions screening,
    and other regulatory compliance requirements.
    """
    
    def __init__(
        self,
        message: str,
        compliance_type: str = "general",
        regulation: Optional[str] = None,
        severity: str = "medium",
        action_required: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.compliance_type = compliance_type  # aml, kyc, sanctions, etc.
        self.regulation = regulation  # NDPR, AML Act, etc.
        self.severity = severity  # low, medium, high, critical
        self.action_required = action_required
        
        # Compliance errors always have high compliance impact
        self.compliance_impact = 'high'
    
    @property
    def is_retryable(self) -> bool:
        """Compliance errors are generally not retryable without intervention"""
        return False
    
    @property
    def requires_immediate_attention(self) -> bool:
        """All compliance errors require immediate attention"""
        return True


class StitchNetworkError(StitchAPIError):
    """
    Network connectivity and timeout errors.
    
    Handles network-related issues that may affect enterprise operations.
    """
    
    def __init__(
        self,
        message: str,
        network_type: str = "connectivity",
        timeout_duration: Optional[float] = None,
        connection_attempts: int = 1,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.network_type = network_type  # connectivity, timeout, dns, ssl
        self.timeout_duration = timeout_duration
        self.connection_attempts = connection_attempts
    
    @property
    def is_retryable(self) -> bool:
        """Network errors are retryable with exponential backoff"""
        return True
    
    @property
    def recommended_retry_delay(self) -> int:
        """Calculate retry delay based on attempt count"""
        base_delay = 5
        return min(300, base_delay * (2 ** (self.connection_attempts - 1)))


class StitchDataError(StitchAPIError):
    """
    Data validation and format errors.
    
    Handles errors related to invalid data formats, missing required fields,
    and data validation failures.
    """
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        field_errors: Optional[Dict[str, str]] = None,
        data_format: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []
        self.field_errors = field_errors or {}
        self.data_format = data_format
    
    @property
    def is_retryable(self) -> bool:
        """Data errors are not retryable without fixing the data"""
        return False
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Data errors require immediate attention to fix data issues"""
        return True


class StitchConfigurationError(StitchAPIError):
    """
    Configuration and setup errors for enterprise deployments.
    
    Handles errors related to incorrect configuration, missing settings,
    and deployment issues.
    """
    
    def __init__(
        self,
        message: str,
        config_section: Optional[str] = None,
        missing_settings: Optional[List[str]] = None,
        invalid_settings: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.config_section = config_section
        self.missing_settings = missing_settings or []
        self.invalid_settings = invalid_settings or {}
    
    @property
    def is_retryable(self) -> bool:
        """Configuration errors are not retryable without fixing configuration"""
        return False
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Configuration errors require immediate attention"""
        return True


# Utility functions for error handling

def categorize_stitch_error(
    status_code: int,
    error_code: Optional[str],
    response_data: Dict[str, Any]
) -> type:
    """
    Categorize Stitch API errors based on status code and error details.
    
    Returns the appropriate exception class for the error.
    """
    if status_code == 401:
        return StitchAuthenticationError
    elif status_code == 403:
        return StitchAuthenticationError
    elif status_code == 429:
        return StitchRateLimitError
    elif status_code in [500, 502, 503, 504]:
        return StitchAPIError
    elif status_code == 400:
        # Check if it's a compliance or data validation error
        if error_code and 'compliance' in error_code.lower():
            return StitchComplianceError
        else:
            return StitchDataError
    else:
        return StitchAPIError


def create_stitch_error(
    message: str,
    status_code: Optional[int] = None,
    error_code: Optional[str] = None,
    response_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> StitchAPIError:
    """
    Factory function to create appropriate Stitch exception based on error details.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Stitch-specific error code
        response_data: Full API response data
        **kwargs: Additional context for specific exception types
    
    Returns:
        Appropriate StitchAPIError subclass instance
    """
    response_data = response_data or {}
    
    # Determine exception class
    if status_code:
        exception_class = categorize_stitch_error(status_code, error_code, response_data)
    else:
        exception_class = StitchAPIError
    
    # Create exception with common parameters
    common_params = {
        'message': message,
        'error_code': error_code,
        'status_code': status_code,
        'response_data': response_data,
        **kwargs
    }
    
    # Add specific parameters based on exception type
    if exception_class == StitchRateLimitError:
        if 'retry_after' in response_data:
            common_params['retry_after'] = response_data['retry_after']
    elif exception_class == StitchComplianceError:
        if 'compliance_type' in response_data:
            common_params['compliance_type'] = response_data['compliance_type']
        if 'regulation' in response_data:
            common_params['regulation'] = response_data['regulation']
    
    return exception_class(**common_params)