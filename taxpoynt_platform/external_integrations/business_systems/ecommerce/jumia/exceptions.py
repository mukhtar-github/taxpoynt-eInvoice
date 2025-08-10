"""
Jumia E-commerce Exception Classes
Custom exceptions for Jumia e-commerce platform integration errors.
"""
from typing import Optional, Dict, Any

from ....shared.exceptions.integration_exceptions import (
    ConnectionError,
    AuthenticationError,
    DataExtractionError,
    TransformationError,
    APIError
)


class JumiaConnectionError(ConnectionError):
    """Raised when Jumia marketplace connection fails."""
    
    def __init__(self, message: str, seller_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.seller_id = seller_id


class JumiaAuthenticationError(AuthenticationError):
    """Raised when Jumia API authentication fails."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.auth_type = auth_type


class JumiaDataExtractionError(DataExtractionError):
    """Raised when Jumia data extraction fails."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.resource_type = resource_type


class JumiaTransformationError(TransformationError):
    """Raised when Jumia order transformation fails."""
    
    def __init__(self, message: str, order_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.order_id = order_id


class JumiaAPIError(APIError):
    """Raised when Jumia API returns an error."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, response_data)
        self.endpoint = endpoint


class JumiaOrderNotFoundError(JumiaDataExtractionError):
    """Raised when a specific Jumia order is not found."""
    
    def __init__(self, order_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Jumia order not found: {order_id}"
        super().__init__(message, "order", details)
        self.order_id = order_id


class JumiaProductNotFoundError(JumiaDataExtractionError):
    """Raised when a specific Jumia product is not found."""
    
    def __init__(self, product_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Jumia product not found: {product_id}"
        super().__init__(message, "product", details)
        self.product_id = product_id


class JumiaSellerNotFoundError(JumiaConnectionError):
    """Raised when Jumia seller is not found or inaccessible."""
    
    def __init__(self, seller_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Jumia seller not found or inaccessible: {seller_id}"
        super().__init__(message, seller_id, details)


class JumiaRateLimitError(JumiaAPIError):
    """Raised when Jumia API rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Jumia API rate limit exceeded",
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 429, details)
        self.retry_after = retry_after
        self.limit_type = limit_type  # 'hourly', 'daily', etc.


class JumiaMarketplaceError(JumiaAPIError):
    """Raised when Jumia marketplace-specific operations fail."""
    
    def __init__(
        self,
        message: str,
        marketplace: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.marketplace = marketplace  # 'jumia-ng', 'jumia-ke', etc.
        self.operation = operation


class JumiaInventoryError(JumiaAPIError):
    """Raised when Jumia inventory operations fail."""
    
    def __init__(
        self,
        message: str,
        sku: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.sku = sku
        self.operation = operation


class JumiaFulfillmentError(JumiaAPIError):
    """Raised when Jumia fulfillment operations fail."""
    
    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        fulfillment_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.order_id = order_id
        self.fulfillment_type = fulfillment_type  # 'JFS', 'seller_fulfillment'


class JumiaPaymentError(JumiaAPIError):
    """Raised when Jumia payment operations fail."""
    
    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.order_id = order_id
        self.payment_method = payment_method


class JumiaCategoryError(JumiaAPIError):
    """Raised when Jumia category operations fail."""
    
    def __init__(
        self,
        message: str,
        category_id: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.category_id = category_id
        self.operation = operation


class JumiaRegionalError(JumiaAPIError):
    """Raised when Jumia regional operations fail."""
    
    def __init__(
        self,
        message: str,
        country_code: Optional[str] = None,
        region: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.country_code = country_code
        self.region = region


class JumiaComplianceError(JumiaAPIError):
    """Raised when Jumia compliance operations fail."""
    
    def __init__(
        self,
        message: str,
        compliance_type: Optional[str] = None,
        regulation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.compliance_type = compliance_type  # 'tax', 'product_safety', etc.
        self.regulation = regulation


# Exception mapping for API error codes
JUMIA_ERROR_CODE_MAPPING = {
    400: JumiaAPIError,
    401: JumiaAuthenticationError,
    403: JumiaAuthenticationError,
    404: JumiaAPIError,
    409: JumiaAPIError,
    422: JumiaAPIError,
    429: JumiaRateLimitError,
    500: JumiaAPIError,
    502: JumiaConnectionError,
    503: JumiaConnectionError,
    504: JumiaConnectionError
}


def map_api_error(
    status_code: int,
    message: str,
    response_data: Optional[Dict[str, Any]] = None,
    endpoint: Optional[str] = None
) -> JumiaAPIError:
    """
    Map HTTP status codes to appropriate Jumia exception types.
    
    Args:
        status_code: HTTP status code
        message: Error message
        response_data: API response data
        endpoint: API endpoint that failed
        
    Returns:
        Appropriate Jumia exception instance
    """
    exception_class = JUMIA_ERROR_CODE_MAPPING.get(status_code, JumiaAPIError)
    
    if exception_class == JumiaRateLimitError:
        retry_after = None
        if response_data and isinstance(response_data, dict):
            retry_after = response_data.get('retry_after')
        return exception_class(message, retry_after=retry_after, details=response_data)
    elif exception_class in (JumiaConnectionError, JumiaAuthenticationError):
        return exception_class(message, details=response_data)
    else:
        return exception_class(message, status_code, response_data, endpoint)


# Jumia marketplace mapping
JUMIA_MARKETPLACES = {
    'NG': 'jumia-ng',  # Nigeria
    'KE': 'jumia-ke',  # Kenya
    'UG': 'jumia-ug',  # Uganda
    'GH': 'jumia-gh',  # Ghana
    'CI': 'jumia-ci',  # Côte d'Ivoire
    'SN': 'jumia-sn',  # Senegal
    'MA': 'jumia-ma',  # Morocco
    'TN': 'jumia-tn',  # Tunisia
    'DZ': 'jumia-dz',  # Algeria
    'EG': 'jumia-eg',  # Egypt
}


def get_marketplace_code(country_code: str) -> str:
    """
    Get Jumia marketplace code for a country.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code
        
    Returns:
        Jumia marketplace code
        
    Raises:
        JumiaRegionalError: If country is not supported
    """
    marketplace = JUMIA_MARKETPLACES.get(country_code.upper())
    if not marketplace:
        raise JumiaRegionalError(
            f"Jumia marketplace not available in country: {country_code}",
            country_code=country_code
        )
    return marketplace


def get_supported_countries() -> List[str]:
    """
    Get list of countries where Jumia operates.
    
    Returns:
        List of ISO 3166-1 alpha-2 country codes
    """
    return list(JUMIA_MARKETPLACES.keys())