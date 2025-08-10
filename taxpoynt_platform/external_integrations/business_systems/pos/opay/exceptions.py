"""
OPay POS Connector Exceptions
Comprehensive exception hierarchy for OPay POS integration errors,
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


class OPayConnectionError(ConnectionError):
    """OPay POS connection-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_type = "opay_connection_error"


class OPayAuthenticationError(AuthenticationError):
    """OPay POS authentication and authorization errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.error_type = "opay_authentication_error"


class OPayAPIError(APIError):
    """OPay POS API-specific errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, error_code, details)
        self.error_type = "opay_api_error"


class OPayRateLimitError(RateLimitError):
    """OPay POS rate limiting errors."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, retry_after, details)
        self.error_type = "opay_rate_limit_error"


class OPayValidationError(ValidationError):
    """OPay POS data validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, field, details)
        self.error_type = "opay_validation_error"


class OPayWebhookError(WebhookError):
    """OPay POS webhook processing errors."""
    
    def __init__(
        self,
        message: str,
        webhook_event: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, webhook_event, details)
        self.error_type = "opay_webhook_error"


class OPayDataExtractionError(Exception):
    """OPay POS data extraction specific errors."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.transaction_id = transaction_id
        self.details = details or {}
        self.error_type = "opay_data_extraction_error"
        super().__init__(self.message)


class OPayTransformationError(Exception):
    """OPay POS transaction transformation errors."""
    
    def __init__(
        self,
        message: str,
        transaction_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.transaction_id = transaction_id
        self.details = details or {}
        self.error_type = "opay_transformation_error"
        super().__init__(self.message)


class OPayConfigurationError(Exception):
    """OPay POS configuration and setup errors."""
    
    def __init__(self, message: str, config_field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.config_field = config_field
        self.details = details or {}
        self.error_type = "opay_configuration_error"
        super().__init__(self.message)


class OPayWalletError(Exception):
    """OPay wallet and mobile money specific errors."""
    
    def __init__(
        self,
        message: str,
        wallet_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.wallet_id = wallet_id
        self.details = details or {}
        self.error_type = "opay_wallet_error"
        super().__init__(self.message)


def create_opay_exception(error: Exception, context: Optional[Dict[str, Any]] = None) -> Exception:
    """
    Create appropriate OPay exception from generic error.
    
    Args:
        error: Original exception
        context: Additional context information
        
    Returns:
        Exception: OPay-specific exception
    """
    error_str = str(error).lower()
    context = context or {}
    
    # Authentication errors
    if any(keyword in error_str for keyword in ['unauthorized', 'authentication', 'token', 'access denied', 'invalid credentials']):
        return OPayAuthenticationError(
            f"OPay authentication failed: {str(error)}",
            details={'original_error': str(error), **context}
        )
    
    # Connection errors
    if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable', 'host']):
        return OPayConnectionError(
            f"OPay connection failed: {str(error)}",
            details={'original_error': str(error), **context}
        )
    
    # Rate limit errors
    if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429', 'quota exceeded']):
        return OPayRateLimitError(
            f"OPay rate limit exceeded: {str(error)}",
            retry_after=context.get('retry_after'),
            details={'original_error': str(error), **context}
        )
    
    # Validation errors
    if any(keyword in error_str for keyword in ['validation', 'invalid', 'bad request', '400', 'malformed']):
        return OPayValidationError(
            f"OPay validation failed: {str(error)}",
            field=context.get('field'),
            details={'original_error': str(error), **context}
        )
    
    # Wallet specific errors
    if any(keyword in error_str for keyword in ['wallet', 'insufficient funds', 'account blocked', 'mobile money']):
        return OPayWalletError(
            f"OPay wallet error: {str(error)}",
            wallet_id=context.get('wallet_id'),
            details={'original_error': str(error), **context}
        )
    
    # API errors with status codes
    if hasattr(error, 'status_code'):
        return OPayAPIError(
            f"OPay API error: {str(error)}",
            status_code=getattr(error, 'status_code'),
            error_code=context.get('error_code'),
            details={'original_error': str(error), **context}
        )
    
    # Generic API error
    return OPayAPIError(
        f"OPay API error: {str(error)}",
        details={'original_error': str(error), **context}
    )