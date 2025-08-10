"""
TradeGecko Exceptions
Custom exception classes for TradeGecko inventory integration errors.
"""
from typing import Optional, Dict, Any


class TradeGeckoException(Exception):
    """Base exception for all TradeGecko integration errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class TradeGeckoAuthenticationError(TradeGeckoException):
    """Raised when TradeGecko authentication fails."""
    pass


class TradeGeckoAuthorizationError(TradeGeckoException):
    """Raised when TradeGecko authorization fails (insufficient permissions)."""
    pass


class TradeGeckoAPIError(TradeGeckoException):
    """Raised when TradeGecko API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class TradeGeckoRateLimitError(TradeGeckoAPIError):
    """Raised when TradeGecko API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class TradeGeckoConnectionError(TradeGeckoException):
    """Raised when connection to TradeGecko API fails."""
    pass


class TradeGeckoConfigurationError(TradeGeckoException):
    """Raised when TradeGecko configuration is invalid."""
    pass


class TradeGeckoDataError(TradeGeckoException):
    """Raised when TradeGecko data is invalid or cannot be processed."""
    pass


class TradeGeckoProductNotFoundError(TradeGeckoException):
    """Raised when specified TradeGecko product is not found."""
    pass


class TradeGeckoVariantNotFoundError(TradeGeckoException):
    """Raised when specified TradeGecko product variant is not found."""
    pass


class TradeGeckoLocationNotFoundError(TradeGeckoException):
    """Raised when specified TradeGecko location is not found."""
    pass


class TradeGeckoOrderNotFoundError(TradeGeckoException):
    """Raised when specified TradeGecko order is not found."""
    pass


class TradeGeckoPurchaseOrderNotFoundError(TradeGeckoException):
    """Raised when specified TradeGecko purchase order is not found."""
    pass


class TradeGeckoSupplierNotFoundError(TradeGeckoException):
    """Raised when specified TradeGecko supplier is not found."""
    pass


class TradeGeckoCustomerNotFoundError(TradeGeckoException):
    """Raised when specified TradeGecko customer is not found."""
    pass


class TradeGeckoValidationError(TradeGeckoDataError):
    """Raised when TradeGecko data validation fails."""
    pass


class TradeGeckoTransformationError(TradeGeckoDataError):
    """Raised when transforming TradeGecko data to standard format fails."""
    pass


class TradeGeckoSyncError(TradeGeckoException):
    """Raised when TradeGecko data synchronization fails."""
    pass


class TradeGeckoQuotaExceededError(TradeGeckoException):
    """Raised when TradeGecko account quota is exceeded."""
    pass


class TradeGeckoMaintenanceError(TradeGeckoAPIError):
    """Raised when TradeGecko API is under maintenance."""
    pass


class TradeGeckoDeprecationError(TradeGeckoAPIError):
    """Raised when using deprecated TradeGecko API endpoints."""
    pass


class TradeGeckoStockAdjustmentError(TradeGeckoException):
    """Raised when stock adjustment operations fail."""
    pass


class TradeGeckoFulfillmentError(TradeGeckoException):
    """Raised when fulfillment operations fail."""
    pass


class TradeGeckoChannelError(TradeGeckoException):
    """Raised when sales channel operations fail."""
    pass