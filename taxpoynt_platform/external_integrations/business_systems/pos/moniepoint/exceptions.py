"""
Moniepoint POS Connector Exceptions
Comprehensive exception hierarchy for Moniepoint POS integration errors,
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


class MoniepointConnectionError(ConnectionError):
    """Moniepoint POS connection-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_type = "moniepoint_connection_error"


class MoniepointAuthenticationError(AuthenticationError):
    """Moniepoint POS authentication and authorization errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_type = "moniepoint_authentication_error"


class MoniepointAPIError(APIError):
    """Moniepoint POS API-specific errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, error_code, details)
        self.error_type = "moniepoint_api_error"


class MoniepointRateLimitError(RateLimitError):
    """Moniepoint POS rate limiting errors."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, retry_after, details)
        self.error_type = "moniepoint_rate_limit_error"


class MoniepointValidationError(ValidationError):
    """Moniepoint POS data validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field, details)
        self.error_type = "moniepoint_validation_error"


class MoniepointWebhookError(WebhookError):
    """Moniepoint POS webhook processing errors."""
    
    def __init__(
        self,
        message: str,
        webhook_event: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, webhook_event, details)
        self.error_type = "moniepoint_webhook_error"


class MoniepointDataExtractionError(Exception):
    """Moniepoint POS data extraction specific errors."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.transaction_id = transaction_id
        self.details = details or {}
        self.error_type = "moniepoint_data_extraction_error"
        super().__init__(self.message)


class MoniepointTransformationError(Exception):
    """Moniepoint POS transaction transformation errors."""
    
    def __init__(
        self,
        message: str,
        transaction_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.transaction_id = transaction_id
        self.details = details or {}
        self.error_type = "moniepoint_transformation_error"
        super().__init__(self.message)


class MoniepointConfigurationError(Exception):
    """Moniepoint POS configuration and setup errors."""
    
    def __init__(self, message: str, config_field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.config_field = config_field
        self.details = details or {}
        self.error_type = "moniepoint_configuration_error"
        super().__init__(self.message)


class MoniepointNIPError(Exception):
    """Moniepoint NIP (Nigeria Instant Payment) specific errors."""
    
    def __init__(
        self,
        message: str,
        nip_response_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.nip_response_code = nip_response_code
        self.details = details or {}
        self.error_type = "moniepoint_nip_error"
        super().__init__(self.message)


def create_moniepoint_exception(error: Exception, context: Optional[Dict[str, Any]] = None) -> Exception:
    """
    Create appropriate Moniepoint exception from generic error.
    
    Args:
        error: Original exception
        context: Additional context information
        
    Returns:
        Exception: Moniepoint-specific exception
    """
    error_str = str(error).lower()
    context = context or {}
    
    # Authentication errors
    if any(keyword in error_str for keyword in ['unauthorized', 'authentication', 'token', 'access denied', 'invalid credentials']):
        return MoniepointAuthenticationError(
            f"Moniepoint authentication failed: {str(error)}",
            details={'original_error': str(error), **context}
        )
    
    # Connection errors
    if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable', 'host']):
        return MoniepointConnectionError(
            f"Moniepoint connection failed: {str(error)}",
            details={'original_error': str(error), **context}
        )
    
    # Rate limit errors
    if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429', 'quota exceeded']):
        return MoniepointRateLimitError(
            f"Moniepoint rate limit exceeded: {str(error)}",
            retry_after=context.get('retry_after'),
            details={'original_error': str(error), **context}
        )
    
    # Validation errors
    if any(keyword in error_str for keyword in ['validation', 'invalid', 'bad request', '400', 'malformed']):
        return MoniepointValidationError(
            f"Moniepoint validation failed: {str(error)}",
            field=context.get('field'),
            details={'original_error': str(error), **context}
        )
    
    # NIP specific errors
    if any(keyword in error_str for keyword in ['nip', 'nibss', 'instant payment', 'transfer failed']):
        return MoniepointNIPError(
            f"Moniepoint NIP error: {str(error)}",
            nip_response_code=context.get('nip_response_code'),
            details={'original_error': str(error), **context}
        )
    
    # API errors with status codes
    if hasattr(error, 'status_code'):
        return MoniepointAPIError(
            f"Moniepoint API error: {str(error)}",
            status_code=getattr(error, 'status_code'),
            error_code=context.get('error_code'),
            details={'original_error': str(error), **context}
        )
    
    # Generic API error
    return MoniepointAPIError(
        f"Moniepoint API error: {str(error)}",
        details={'original_error': str(error), **context}
    )