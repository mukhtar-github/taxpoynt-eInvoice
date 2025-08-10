"""
Cin7 Exceptions
Custom exception classes for Cin7 inventory integration errors.
"""
from typing import Optional, Dict, Any


class Cin7Exception(Exception):
    """Base exception for all Cin7 integration errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class Cin7AuthenticationError(Cin7Exception):
    """Raised when Cin7 authentication fails."""
    pass


class Cin7AuthorizationError(Cin7Exception):
    """Raised when Cin7 authorization fails (insufficient permissions)."""
    pass


class Cin7APIError(Cin7Exception):
    """Raised when Cin7 API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class Cin7RateLimitError(Cin7APIError):
    """Raised when Cin7 API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class Cin7ConnectionError(Cin7Exception):
    """Raised when connection to Cin7 API fails."""
    pass


class Cin7ConfigurationError(Cin7Exception):
    """Raised when Cin7 configuration is invalid."""
    pass


class Cin7DataError(Cin7Exception):
    """Raised when Cin7 data is invalid or cannot be processed."""
    pass


class Cin7ProductNotFoundError(Cin7Exception):
    """Raised when specified Cin7 product is not found."""
    pass


class Cin7StockLocationNotFoundError(Cin7Exception):
    """Raised when specified Cin7 stock location is not found."""
    pass


class Cin7PurchaseOrderNotFoundError(Cin7Exception):
    """Raised when specified Cin7 purchase order is not found."""
    pass


class Cin7SalesOrderNotFoundError(Cin7Exception):
    """Raised when specified Cin7 sales order is not found."""
    pass


class Cin7SupplierNotFoundError(Cin7Exception):
    """Raised when specified Cin7 supplier is not found."""
    pass


class Cin7ValidationError(Cin7DataError):
    """Raised when Cin7 data validation fails."""
    pass


class Cin7TransformationError(Cin7DataError):
    """Raised when transforming Cin7 data to standard format fails."""
    pass


class Cin7SyncError(Cin7Exception):
    """Raised when Cin7 data synchronization fails."""
    pass


class Cin7QuotaExceededError(Cin7Exception):
    """Raised when Cin7 account quota is exceeded."""
    pass


class Cin7MaintenanceError(Cin7APIError):
    """Raised when Cin7 API is under maintenance."""
    pass


class Cin7DeprecationError(Cin7APIError):
    """Raised when using deprecated Cin7 API endpoints."""
    pass


class Cin7StockAdjustmentError(Cin7Exception):
    """Raised when stock adjustment operations fail."""
    pass


class Cin7WarehouseError(Cin7Exception):
    """Raised when warehouse operations fail."""
    pass