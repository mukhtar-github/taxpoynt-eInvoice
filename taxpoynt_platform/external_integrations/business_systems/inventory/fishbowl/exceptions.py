"""
Fishbowl Exceptions
Custom exception classes for Fishbowl inventory integration errors.
"""
from typing import Optional, Dict, Any


class FishbowlException(Exception):
    """Base exception for all Fishbowl integration errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class FishbowlAuthenticationError(FishbowlException):
    """Raised when Fishbowl authentication fails."""
    pass


class FishbowlAuthorizationError(FishbowlException):
    """Raised when Fishbowl authorization fails (insufficient permissions)."""
    pass


class FishbowlAPIError(FishbowlException):
    """Raised when Fishbowl API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class FishbowlConnectionError(FishbowlException):
    """Raised when connection to Fishbowl API fails."""
    pass


class FishbowlConfigurationError(FishbowlException):
    """Raised when Fishbowl configuration is invalid."""
    pass


class FishbowlDataError(FishbowlException):
    """Raised when Fishbowl data is invalid or cannot be processed."""
    pass


class FishbowlProductNotFoundError(FishbowlException):
    """Raised when specified Fishbowl product is not found."""
    pass


class FishbowlWarehouseNotFoundError(FishbowlException):
    """Raised when specified Fishbowl warehouse is not found."""
    pass


class FishbowlInventoryNotFoundError(FishbowlException):
    """Raised when specified Fishbowl inventory item is not found."""
    pass


class FishbowlWorkOrderNotFoundError(FishbowlException):
    """Raised when specified Fishbowl work order is not found."""
    pass


class FishbowlPurchaseOrderNotFoundError(FishbowlException):
    """Raised when specified Fishbowl purchase order is not found."""
    pass


class FishbowlSalesOrderNotFoundError(FishbowlException):
    """Raised when specified Fishbowl sales order is not found."""
    pass


class FishbowlVendorNotFoundError(FishbowlException):
    """Raised when specified Fishbowl vendor is not found."""
    pass


class FishbowlCustomerNotFoundError(FishbowlException):
    """Raised when specified Fishbowl customer is not found."""
    pass


class FishbowlValidationError(FishbowlDataError):
    """Raised when Fishbowl data validation fails."""
    pass


class FishbowlTransformationError(FishbowlDataError):
    """Raised when transforming Fishbowl data to standard format fails."""
    pass


class FishbowlSyncError(FishbowlException):
    """Raised when Fishbowl data synchronization fails."""
    pass


class FishbowlDatabaseError(FishbowlException):
    """Raised when Fishbowl database operations fail."""
    pass


class FishbowlXMLError(FishbowlException):
    """Raised when XML parsing or generation fails."""
    pass


class FishbowlSessionError(FishbowlException):
    """Raised when Fishbowl session management fails."""
    pass


class FishbowlInventoryAdjustmentError(FishbowlException):
    """Raised when inventory adjustment operations fail."""
    pass


class FishbowlManufacturingError(FishbowlException):
    """Raised when manufacturing operations fail."""
    pass