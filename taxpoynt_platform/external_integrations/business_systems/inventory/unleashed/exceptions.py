"""
Unleashed Exceptions
Custom exception classes for Unleashed inventory integration errors.
"""
from typing import Optional, Dict, Any


class UnleashedException(Exception):
    """Base exception for all Unleashed integration errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class UnleashedAuthenticationError(UnleashedException):
    """Raised when Unleashed authentication fails."""
    pass


class UnleashedAuthorizationError(UnleashedException):
    """Raised when Unleashed authorization fails (insufficient permissions)."""
    pass


class UnleashedAPIError(UnleashedException):
    """Raised when Unleashed API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class UnleashedRateLimitError(UnleashedAPIError):
    """Raised when Unleashed API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class UnleashedConnectionError(UnleashedException):
    """Raised when connection to Unleashed API fails."""
    pass


class UnleashedConfigurationError(UnleashedException):
    """Raised when Unleashed configuration is invalid."""
    pass


class UnleashedDataError(UnleashedException):
    """Raised when Unleashed data is invalid or cannot be processed."""
    pass


class UnleashedProductNotFoundError(UnleashedException):
    """Raised when specified Unleashed product is not found."""
    pass


class UnleashedWarehouseNotFoundError(UnleashedException):
    """Raised when specified Unleashed warehouse is not found."""
    pass


class UnleashedStockOnHandNotFoundError(UnleashedException):
    """Raised when specified Unleashed stock on hand record is not found."""
    pass


class UnleashedPurchaseOrderNotFoundError(UnleashedException):
    """Raised when specified Unleashed purchase order is not found."""
    pass


class UnleashedSalesOrderNotFoundError(UnleashedException):
    """Raised when specified Unleashed sales order is not found."""
    pass


class UnleashedSupplierNotFoundError(UnleashedException):
    """Raised when specified Unleashed supplier is not found."""
    pass


class UnleashedCustomerNotFoundError(UnleashedException):
    """Raised when specified Unleashed customer is not found."""
    pass


class UnleashedValidationError(UnleashedDataError):
    """Raised when Unleashed data validation fails."""
    pass


class UnleashedTransformationError(UnleashedDataError):
    """Raised when transforming Unleashed data to standard format fails."""
    pass


class UnleashedSyncError(UnleashedException):
    """Raised when Unleashed data synchronization fails."""
    pass


class UnleashedQuotaExceededError(UnleashedException):
    """Raised when Unleashed account quota is exceeded."""
    pass


class UnleashedMaintenanceError(UnleashedAPIError):
    """Raised when Unleashed API is under maintenance."""
    pass


class UnleashedDeprecationError(UnleashedAPIError):
    """Raised when using deprecated Unleashed API endpoints."""
    pass


class UnleashedStockAdjustmentError(UnleashedException):
    """Raised when stock adjustment operations fail."""
    pass


class UnleashedTransactionError(UnleashedException):
    """Raised when transaction operations fail."""
    pass


class UnleashedReportError(UnleashedException):
    """Raised when report generation fails."""
    pass