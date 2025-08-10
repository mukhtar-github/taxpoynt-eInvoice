"""
Lightspeed POS Connector Exceptions

Comprehensive exception hierarchy for Lightspeed POS integration errors,
providing detailed error handling for TaxPoynt eInvoice System Integrator functions.
"""

from typing import Any, Dict, Optional


class LightspeedError(Exception):
    """Base exception for all Lightspeed POS connector errors."""
    
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


class LightspeedConnectionError(LightspeedError):
    """Raised when connection to Lightspeed API fails."""
    
    def __init__(self, message: str = "Failed to connect to Lightspeed API", **kwargs):
        super().__init__(message, **kwargs)


class LightspeedAuthenticationError(LightspeedError):
    """Raised when Lightspeed authentication fails."""
    
    def __init__(self, message: str = "Lightspeed authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class LightspeedAPIError(LightspeedError):
    """Raised when Lightspeed API returns an error response."""
    
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


class LightspeedRateLimitError(LightspeedError):
    """Raised when Lightspeed API rate limit is exceeded."""
    
    def __init__(self, message: str = "Lightspeed API rate limit exceeded", 
                 retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['retry_after'] = self.retry_after
        return result


class LightspeedNotFoundError(LightspeedError):
    """Raised when requested Lightspeed resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        message = f"Lightspeed {resource_type} with ID {resource_id} not found"
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, **kwargs)


class LightspeedValidationError(LightspeedError):
    """Raised when data validation fails for Lightspeed operations."""
    
    def __init__(self, field: str, value: Any, expected: str, **kwargs):
        message = f"Invalid {field}: got {value}, expected {expected}"
        self.field = field
        self.value = value
        self.expected = expected
        super().__init__(message, **kwargs)


class LightspeedWebhookError(LightspeedError):
    """Raised when webhook processing fails."""
    
    def __init__(self, message: str = "Lightspeed webhook processing failed", 
                 webhook_event: Optional[str] = None, **kwargs):
        self.webhook_event = webhook_event
        super().__init__(message, **kwargs)


class LightspeedSaleError(LightspeedError):
    """Raised when sale operations fail."""
    
    def __init__(self, message: str = "Lightspeed sale operation failed", 
                 sale_id: Optional[str] = None, **kwargs):
        self.sale_id = sale_id
        super().__init__(message, **kwargs)


class LightspeedCustomerError(LightspeedError):
    """Raised when customer operations fail."""
    
    def __init__(self, message: str = "Lightspeed customer operation failed", 
                 customer_id: Optional[str] = None, **kwargs):
        self.customer_id = customer_id
        super().__init__(message, **kwargs)


class LightspeedProductError(LightspeedError):
    """Raised when product operations fail."""
    
    def __init__(self, message: str = "Lightspeed product operation failed", 
                 product_id: Optional[str] = None, **kwargs):
        self.product_id = product_id
        super().__init__(message, **kwargs)


class LightspeedInventoryError(LightspeedError):
    """Raised when inventory operations fail."""
    
    def __init__(self, message: str = "Lightspeed inventory operation failed", 
                 item_id: Optional[str] = None, **kwargs):
        self.item_id = item_id
        super().__init__(message, **kwargs)


class LightspeedConfigurationError(LightspeedError):
    """Raised when connector configuration is invalid."""
    
    def __init__(self, config_field: str, issue: str, **kwargs):
        message = f"Invalid Lightspeed configuration - {config_field}: {issue}"
        self.config_field = config_field
        self.issue = issue
        super().__init__(message, **kwargs)


class LightspeedTimeoutError(LightspeedError):
    """Raised when Lightspeed API request times out."""
    
    def __init__(self, operation: str, timeout_seconds: int, **kwargs):
        message = f"Lightspeed {operation} timed out after {timeout_seconds} seconds"
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(message, **kwargs)


class LightspeedLocationError(LightspeedError):
    """Raised when location operations fail."""
    
    def __init__(self, message: str = "Lightspeed location operation failed", 
                 location_id: Optional[str] = None, **kwargs):
        self.location_id = location_id
        super().__init__(message, **kwargs)


def create_lightspeed_exception(error_data: Dict[str, Any]) -> LightspeedError:
    """
    Factory function to create appropriate Lightspeed exception from error data.
    
    Args:
        error_data: Dictionary containing error information
        
    Returns:
        Appropriate LightspeedError subclass instance
    """
    error_type = error_data.get('type', '').lower()
    message = error_data.get('message', 'Unknown Lightspeed error')
    status_code = error_data.get('status_code')
    
    # Map common HTTP status codes to specific exceptions
    if status_code == 401:
        return LightspeedAuthenticationError(message, error_code=error_data.get('code'))
    elif status_code == 404:
        resource_type = error_data.get('resource_type', 'resource')
        resource_id = error_data.get('resource_id', 'unknown')
        return LightspeedNotFoundError(resource_type, resource_id)
    elif status_code == 429:
        retry_after = error_data.get('retry_after')
        return LightspeedRateLimitError(message, retry_after=retry_after)
    elif status_code and 500 <= status_code < 600:
        return LightspeedConnectionError(f"Lightspeed server error: {message}")
    
    # Map error types to specific exceptions
    if 'authentication' in error_type or 'auth' in error_type:
        return LightspeedAuthenticationError(message, error_code=error_data.get('code'))
    elif 'validation' in error_type or 'invalid' in error_type:
        field = error_data.get('field', 'unknown')
        value = error_data.get('value')
        expected = error_data.get('expected', 'valid value')
        return LightspeedValidationError(field, value, expected)
    elif 'rate' in error_type or 'limit' in error_type:
        retry_after = error_data.get('retry_after')
        return LightspeedRateLimitError(message, retry_after=retry_after)
    elif 'connection' in error_type or 'network' in error_type:
        return LightspeedConnectionError(message, error_code=error_data.get('code'))
    elif 'webhook' in error_type:
        webhook_event = error_data.get('webhook_event')
        return LightspeedWebhookError(message, webhook_event=webhook_event)
    elif 'sale' in error_type or 'transaction' in error_type:
        sale_id = error_data.get('sale_id')
        return LightspeedSaleError(message, sale_id=sale_id)
    elif 'customer' in error_type:
        customer_id = error_data.get('customer_id')
        return LightspeedCustomerError(message, customer_id=customer_id)
    elif 'product' in error_type or 'item' in error_type:
        product_id = error_data.get('product_id')
        return LightspeedProductError(message, product_id=product_id)
    elif 'inventory' in error_type:
        item_id = error_data.get('item_id')
        return LightspeedInventoryError(message, item_id=item_id)
    elif 'config' in error_type:
        config_field = error_data.get('config_field', 'unknown')
        issue = error_data.get('issue', 'invalid configuration')
        return LightspeedConfigurationError(config_field, issue)
    elif 'timeout' in error_type:
        operation = error_data.get('operation', 'request')
        timeout_seconds = error_data.get('timeout_seconds', 30)
        return LightspeedTimeoutError(operation, timeout_seconds)
    elif 'location' in error_type:
        location_id = error_data.get('location_id')
        return LightspeedLocationError(message, location_id=location_id)
    else:
        # Generic API error for unmatched cases
        return LightspeedAPIError(
            message,
            status_code=status_code,
            response_data=error_data.get('response_data'),
            error_code=error_data.get('code')
        )