"""
Toast POS Connector Exceptions
Comprehensive exception hierarchy for Toast POS integration errors,
providing detailed error handling for TaxPoynt eInvoice System Integrator functions.
"""

from typing import Any, Dict, Optional
from ....shared.exceptions.integration_exceptions import (
    ConnectionError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ValidationError,
    WebhookError
)


class ToastConnectionError(ConnectionError):
    """Toast POS connection-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_type = "toast_connection_error"


class ToastAuthenticationError(AuthenticationError):
    """Toast POS authentication and authorization errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_type = "toast_authentication_error"


class ToastAPIError(APIError):
    """Toast POS API-specific errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, error_code, details)
        self.error_type = "toast_api_error"


class ToastRateLimitError(RateLimitError):
    """Toast POS rate limiting errors."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, retry_after, details)
        self.error_type = "toast_rate_limit_error"


class ToastValidationError(ValidationError):
    """Toast POS data validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field, details)
        self.error_type = "toast_validation_error"


class ToastWebhookError(WebhookError):
    """Toast POS webhook processing errors."""
    
    def __init__(
        self,
        message: str,
        webhook_event: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, webhook_event, details)
        self.error_type = "toast_webhook_error"


class ToastDataExtractionError(Exception):
    """Toast POS data extraction specific errors."""
    
    def __init__(self, message: str, check_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.check_id = check_id
        self.details = details or {}
        self.error_type = "toast_data_extraction_error"
        super().__init__(self.message)


class ToastTransformationError(Exception):
    """Toast POS transaction transformation errors."""
    
    def __init__(
        self,
        message: str,
        transaction_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.transaction_id = transaction_id
        self.details = details or {}
        self.error_type = "toast_transformation_error"
        super().__init__(self.message)


class ToastConfigurationError(Exception):
    """Toast POS configuration and setup errors."""
    
    def __init__(self, message: str, config_field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.config_field = config_field
        self.details = details or {}
        self.error_type = "toast_configuration_error"
        super().__init__(self.message)


def create_toast_exception(error: Exception, context: Optional[Dict[str, Any]] = None) -> Exception:
    """
    Create appropriate Toast exception from generic error.
    
    Args:
        error: Original exception
        context: Additional context information
        
    Returns:
        Exception: Toast-specific exception
    """
    error_str = str(error).lower()
    context = context or {}
    
    # Authentication errors
    if any(keyword in error_str for keyword in ['unauthorized', 'authentication', 'token', 'access denied']):
        return ToastAuthenticationError(
            f"Toast authentication failed: {str(error)}",
            details={'original_error': str(error), **context}
        )
    
    # Connection errors
    if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable']):
        return ToastConnectionError(
            f"Toast connection failed: {str(error)}",
            details={'original_error': str(error), **context}
        )
    
    # Rate limit errors
    if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429']):
        return ToastRateLimitError(
            f"Toast rate limit exceeded: {str(error)}",
            retry_after=context.get('retry_after'),
            details={'original_error': str(error), **context}
        )
    
    # Validation errors
    if any(keyword in error_str for keyword in ['validation', 'invalid', 'bad request', '400']):
        return ToastValidationError(
            f"Toast validation failed: {str(error)}",
            field=context.get('field'),
            details={'original_error': str(error), **context}
        )
    
    # API errors with status codes
    if hasattr(error, 'status_code'):
        return ToastAPIError(
            f"Toast API error: {str(error)}",
            status_code=getattr(error, 'status_code'),
            error_code=context.get('error_code'),
            details={'original_error': str(error), **context}
        )
    
    # Generic API error
    return ToastAPIError(
        f"Toast API error: {str(error)}",
        details={'original_error': str(error), **context}
    )