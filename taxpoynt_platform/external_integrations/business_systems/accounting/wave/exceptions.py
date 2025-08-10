"""
Wave Accounting Exceptions
Custom exception classes for Wave Accounting integration errors.
"""
from typing import Optional, Dict, Any


class WaveException(Exception):
    """Base exception for all Wave Accounting integration errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class WaveAuthenticationError(WaveException):
    """Raised when Wave authentication fails."""
    pass


class WaveAuthorizationError(WaveException):
    """Raised when Wave authorization fails (insufficient permissions)."""
    pass


class WaveAPIError(WaveException):
    """Raised when Wave API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class WaveRateLimitError(WaveAPIError):
    """Raised when Wave API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class WaveConnectionError(WaveException):
    """Raised when connection to Wave API fails."""
    pass


class WaveConfigurationError(WaveException):
    """Raised when Wave configuration is invalid."""
    pass


class WaveDataError(WaveException):
    """Raised when Wave data is invalid or cannot be processed."""
    pass


class WaveBusinessNotFoundError(WaveException):
    """Raised when specified Wave business is not found."""
    pass


class WaveCustomerNotFoundError(WaveException):
    """Raised when specified Wave customer is not found."""
    pass


class WaveInvoiceNotFoundError(WaveException):
    """Raised when specified Wave invoice is not found."""
    pass


class WaveProductNotFoundError(WaveException):
    """Raised when specified Wave product is not found."""
    pass


class WaveValidationError(WaveDataError):
    """Raised when Wave data validation fails."""
    pass


class WaveTransformationError(WaveDataError):
    """Raised when transforming Wave data to UBL format fails."""
    pass


class WaveSyncError(WaveException):
    """Raised when Wave data synchronization fails."""
    pass


class WaveQuotaExceededError(WaveException):
    """Raised when Wave account quota is exceeded."""
    pass


class WaveMaintenanceError(WaveAPIError):
    """Raised when Wave API is under maintenance."""
    pass


class WaveDeprecationError(WaveAPIError):
    """Raised when using deprecated Wave API endpoints."""
    pass