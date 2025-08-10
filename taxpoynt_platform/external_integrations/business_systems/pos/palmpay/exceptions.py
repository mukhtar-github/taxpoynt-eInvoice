"""
PalmPay POS Connector Exceptions
Comprehensive exception hierarchy for PalmPay POS integration errors,
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


class PalmPayConnectionError(ConnectionError):
    """PalmPay POS connection-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_type = "palmpay_connection_error"


class PalmPayAuthenticationError(AuthenticationError):
    """PalmPay POS authentication and authorization errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_type = "palmpay_authentication_error"


class PalmPayAPIError(APIError):
    """PalmPay POS API-specific errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, error_code, details)
        self.error_type = "palmpay_api_error"


class PalmPayRateLimitError(RateLimitError):
    """PalmPay POS rate limiting errors."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, retry_after, details)
        self.error_type = "palmpay_rate_limit_error"


class PalmPayValidationError(ValidationError):
    """PalmPay POS data validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field, details)
        self.error_type = "palmpay_validation_error"


class PalmPayWebhookError(WebhookError):
    """PalmPay POS webhook processing errors."""
    
    def __init__(
        self,
        message: str,
        webhook_event: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, webhook_event, details)
        self.error_type = "palmpay_webhook_error"


class PalmPayDataExtractionError(Exception):
    """PalmPay POS data extraction specific errors."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.transaction_id = transaction_id
        self.details = details or {}
        self.error_type = "palmpay_data_extraction_error"
        super().__init__(self.message)


class PalmPayTransformationError(Exception):
    """PalmPay POS transaction transformation errors."""
    
    def __init__(
        self,
        message: str,
        transaction_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.transaction_id = transaction_id
        self.details = details or {}
        self.error_type = "palmpay_transformation_error"
        super().__init__(self.message)


class PalmPayConfigurationError(Exception):
    """PalmPay POS configuration and setup errors."""
    
    def __init__(self, message: str, config_field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.config_field = config_field
        self.details = details or {}
        self.error_type = "palmpay_configuration_error"
        super().__init__(self.message)


class PalmPayMobileMoneyError(Exception):
    """PalmPay mobile money and wallet specific errors."""
    
    def __init__(
        self,
        message: str,
        wallet_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.wallet_id = wallet_id
        self.details = details or {}
        self.error_type = "palmpay_mobile_money_error"
        super().__init__(self.message)


def create_palmpay_exception(error: Exception, context: Optional[Dict[str, Any]] = None) -> Exception:
    """
    Create appropriate PalmPay exception from generic error.
    
    Args:
        error: Original exception
        context: Additional context information
        
    Returns:
        Exception: PalmPay-specific exception
    """
    error_str = str(error).lower()
    context = context or {}
    
    # Authentication errors
    if any(keyword in error_str for keyword in ['unauthorized', 'authentication', 'token', 'access denied', 'invalid credentials']):
        return PalmPayAuthenticationError(
            f"PalmPay authentication failed: {str(error)}",
            details={'original_error': str(error), **context}
        )
    
    # Connection errors
    if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable', 'host']):
        return PalmPayConnectionError(
            f"PalmPay connection failed: {str(error)}",
            details={'original_error': str(error), **context}
        )
    
    # Rate limit errors
    if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429', 'quota exceeded']):
        return PalmPayRateLimitError(
            f"PalmPay rate limit exceeded: {str(error)}",
            retry_after=context.get('retry_after'),
            details={'original_error': str(error), **context}
        )
    
    # Validation errors
    if any(keyword in error_str for keyword in ['validation', 'invalid', 'bad request', '400', 'malformed']):
        return PalmPayValidationError(
            f"PalmPay validation failed: {str(error)}",
            field=context.get('field'),
            details={'original_error': str(error), **context}
        )
    
    # Mobile money specific errors
    if any(keyword in error_str for keyword in ['wallet', 'insufficient funds', 'account blocked', 'mobile money']):
        return PalmPayMobileMoneyError(
            f"PalmPay mobile money error: {str(error)}",
            wallet_id=context.get('wallet_id'),
            details={'original_error': str(error), **context}
        )
    
    # API errors with status codes
    if hasattr(error, 'status_code'):
        return PalmPayAPIError(
            f"PalmPay API error: {str(error)}",
            status_code=getattr(error, 'status_code'),
            error_code=context.get('error_code'),
            details={'original_error': str(error), **context}
        )
    
    # Generic API error
    return PalmPayAPIError(
        f"PalmPay API error: {str(error)}",
        details={'original_error': str(error), **context}
    )