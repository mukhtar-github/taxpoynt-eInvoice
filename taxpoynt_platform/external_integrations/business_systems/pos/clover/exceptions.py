"""
Clover POS Connector Exceptions

Comprehensive exception hierarchy for Clover POS integration errors,
providing detailed error handling for TaxPoynt eInvoice System Integrator functions.
"""

from typing import Any, Dict, Optional


class CloverError(Exception):
    """Base exception for all Clover POS connector errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class CloverConnectionError(CloverError):
    """Raised when connection to Clover API fails."""
    
    def __init__(self, message: str = "Failed to connect to Clover API", **kwargs):
        super().__init__(message, **kwargs)


class CloverAuthenticationError(CloverError):
    """Raised when Clover authentication fails."""
    
    def __init__(self, message: str = "Clover authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class CloverAPIError(CloverError):
    """Raised when Clover API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None, **kwargs):
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            'status_code': self.status_code,
            'response_data': self.response_data
        })
        return result


class CloverRateLimitError(CloverError):
    """Raised when Clover API rate limit is exceeded."""
    
    def __init__(self, message: str = "Clover API rate limit exceeded", 
                 retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['retry_after'] = self.retry_after
        return result


class CloverNotFoundError(CloverError):
    """Raised when requested Clover resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        message = f"Clover {resource_type} with ID {resource_id} not found"
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, **kwargs)


class CloverValidationError(CloverError):
    """Raised when data validation fails for Clover operations."""
    
    def __init__(self, field: str, value: Any, expected: str, **kwargs):
        message = f"Invalid {field}: got {value}, expected {expected}"
        self.field = field
        self.value = value
        self.expected = expected
        super().__init__(message, **kwargs)


class CloverWebhookError(CloverError):
    """Raised when webhook processing fails."""
    
    def __init__(self, message: str = "Clover webhook processing failed", 
                 webhook_event: Optional[str] = None, **kwargs):
        self.webhook_event = webhook_event
        super().__init__(message, **kwargs)


class CloverOrderError(CloverError):
    """Raised when order operations fail."""
    
    def __init__(self, message: str = "Clover order operation failed", 
                 order_id: Optional[str] = None, **kwargs):
        self.order_id = order_id
        super().__init__(message, **kwargs)


class CloverPaymentError(CloverError):
    """Raised when payment operations fail."""
    
    def __init__(self, message: str = "Clover payment operation failed", 
                 payment_id: Optional[str] = None, **kwargs):
        self.payment_id = payment_id
        super().__init__(message, **kwargs)


class CloverCustomerError(CloverError):
    """Raised when customer operations fail."""
    
    def __init__(self, message: str = "Clover customer operation failed", 
                 customer_id: Optional[str] = None, **kwargs):
        self.customer_id = customer_id
        super().__init__(message, **kwargs)


class CloverInventoryError(CloverError):
    """Raised when inventory operations fail."""
    
    def __init__(self, message: str = "Clover inventory operation failed", 
                 item_id: Optional[str] = None, **kwargs):
        self.item_id = item_id
        super().__init__(message, **kwargs)


class CloverMerchantError(CloverError):
    """Raised when merchant operations fail."""
    
    def __init__(self, message: str = "Clover merchant operation failed", 
                 merchant_id: Optional[str] = None, **kwargs):
        self.merchant_id = merchant_id
        super().__init__(message, **kwargs)


class CloverConfigurationError(CloverError):
    """Raised when connector configuration is invalid."""
    
    def __init__(self, config_field: str, issue: str, **kwargs):
        message = f"Invalid Clover configuration - {config_field}: {issue}"
        self.config_field = config_field
        self.issue = issue
        super().__init__(message, **kwargs)


class CloverTimeoutError(CloverError):
    """Raised when Clover API request times out."""
    
    def __init__(self, operation: str, timeout_seconds: int, **kwargs):
        message = f"Clover {operation} timed out after {timeout_seconds} seconds"
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(message, **kwargs)


class CloverDeviceError(CloverError):
    """Raised when device operations fail."""
    
    def __init__(self, message: str = "Clover device operation failed", 
                 device_id: Optional[str] = None, **kwargs):
        self.device_id = device_id
        super().__init__(message, **kwargs)


class CloverAppError(CloverError):
    """Raised when app-specific operations fail."""
    
    def __init__(self, message: str = "Clover app operation failed", 
                 app_id: Optional[str] = None, **kwargs):
        self.app_id = app_id
        super().__init__(message, **kwargs)


def create_clover_exception(error_data: Dict[str, Any]) -> CloverError:
    """
    Factory function to create appropriate Clover exception from error data.
    
    Args:
        error_data: Dictionary containing error information
        
    Returns:
        Appropriate CloverError subclass instance
    """
    error_type = error_data.get('type', '').lower()
    message = error_data.get('message', 'Unknown Clover error')
    status_code = error_data.get('status_code')
    
    # Map common HTTP status codes to specific exceptions
    if status_code == 401:
        return CloverAuthenticationError(message, error_code=error_data.get('code'))
    elif status_code == 404:
        resource_type = error_data.get('resource_type', 'resource')
        resource_id = error_data.get('resource_id', 'unknown')
        return CloverNotFoundError(resource_type, resource_id)
    elif status_code == 429:
        retry_after = error_data.get('retry_after')
        return CloverRateLimitError(message, retry_after=retry_after)
    elif status_code and 500 <= status_code < 600:
        return CloverConnectionError(f"Clover server error: {message}")
    
    # Map Clover-specific error types
    if 'authentication' in error_type or 'auth' in error_type:
        return CloverAuthenticationError(message, error_code=error_data.get('code'))
    elif 'validation' in error_type or 'invalid' in error_type:
        field = error_data.get('field', 'unknown')
        value = error_data.get('value')
        expected = error_data.get('expected', 'valid value')
        return CloverValidationError(field, value, expected)
    elif 'rate' in error_type or 'limit' in error_type:
        retry_after = error_data.get('retry_after')
        return CloverRateLimitError(message, retry_after=retry_after)
    elif 'connection' in error_type or 'network' in error_type:
        return CloverConnectionError(message, error_code=error_data.get('code'))
    elif 'webhook' in error_type:
        webhook_event = error_data.get('webhook_event')
        return CloverWebhookError(message, webhook_event=webhook_event)
    elif 'order' in error_type:
        order_id = error_data.get('order_id')
        return CloverOrderError(message, order_id=order_id)
    elif 'payment' in error_type:
        payment_id = error_data.get('payment_id')
        return CloverPaymentError(message, payment_id=payment_id)
    elif 'customer' in error_type:
        customer_id = error_data.get('customer_id')
        return CloverCustomerError(message, customer_id=customer_id)
    elif 'inventory' in error_type or 'item' in error_type:
        item_id = error_data.get('item_id')
        return CloverInventoryError(message, item_id=item_id)
    elif 'merchant' in error_type:
        merchant_id = error_data.get('merchant_id')
        return CloverMerchantError(message, merchant_id=merchant_id)
    elif 'config' in error_type:
        config_field = error_data.get('config_field', 'unknown')
        issue = error_data.get('issue', 'invalid configuration')
        return CloverConfigurationError(config_field, issue)
    elif 'timeout' in error_type:
        operation = error_data.get('operation', 'request')
        timeout_seconds = error_data.get('timeout_seconds', 30)
        return CloverTimeoutError(operation, timeout_seconds)
    elif 'device' in error_type:
        device_id = error_data.get('device_id')
        return CloverDeviceError(message, device_id=device_id)
    elif 'app' in error_type:
        app_id = error_data.get('app_id')
        return CloverAppError(message, app_id=app_id)
    else:
        # Generic API error for unmatched cases
        return CloverAPIError(
            message,
            status_code=status_code,
            response_data=error_data.get('response_data'),
            error_code=error_data.get('code')
        )