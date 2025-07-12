"""
Base ERP Connector Interface

This module provides the abstract base class for all ERP system connectors,
ensuring consistent interface across different ERP integrations (Odoo, SAP, Oracle).

All ERP connectors must implement this interface to ensure compatibility
with the ERPConnectorFactory and FIRSSIERPIntegrationService.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import UUID
import logging

from app.schemas.integration import IntegrationTestResult


class ERPConnectionError(Exception):
    """Exception raised for ERP connection errors"""
    pass


class ERPAuthenticationError(Exception):
    """Exception raised for ERP authentication errors"""
    pass


class ERPDataError(Exception):
    """Exception raised for ERP data extraction errors"""
    pass


class ERPValidationError(Exception):
    """Exception raised for ERP data validation errors"""
    pass


class BaseERPConnector(ABC):
    """
    Abstract base class for all ERP system connectors
    
    This interface ensures consistency across different ERP system integrations
    and provides a common contract for the ERPConnectorFactory.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ERP connector
        
        Args:
            config: Configuration dictionary containing connection parameters
        """
        self.config = config
        self.logger = logging.getLogger(f"erp.{self.__class__.__name__}")
        self.connected = False
        self.authenticated = False
        self.last_connection_time = None
        self.connection_timeout = config.get('timeout', 30)
        
    @property
    @abstractmethod
    def erp_type(self) -> str:
        """Return the ERP system type (e.g., 'odoo', 'sap', 'oracle')"""
        pass
    
    @property
    @abstractmethod
    def erp_version(self) -> str:
        """Return the ERP system version"""
        pass
    
    @property
    @abstractmethod
    def supported_features(self) -> List[str]:
        """Return list of supported features for this ERP connector"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to the ERP system
        
        Returns:
            IntegrationTestResult with success status, message, and details
        """
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the ERP system
        
        Returns:
            True if authentication successful, False otherwise
            
        Raises:
            ERPAuthenticationError: If authentication fails
        """
        pass
    
    @abstractmethod
    async def get_invoices(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        include_draft: bool = False,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Fetch invoices from the ERP system
        
        Args:
            from_date: Fetch invoices from this date
            to_date: Fetch invoices up to this date
            include_draft: Whether to include draft invoices
            include_attachments: Whether to include document attachments
            page: Page number for pagination
            page_size: Number of records per page
            
        Returns:
            Dictionary with invoices and pagination metadata
        """
        pass
    
    @abstractmethod
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a specific invoice by ID
        
        Args:
            invoice_id: ID of the invoice to retrieve
            
        Returns:
            Dictionary containing invoice data
            
        Raises:
            ERPDataError: If invoice not found or data retrieval fails
        """
        pass
    
    @abstractmethod
    async def search_invoices(
        self,
        search_term: str,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search for invoices by various criteria
        
        Args:
            search_term: Text to search for in invoice number, reference, or partner name
            include_attachments: Whether to include document attachments
            page: Page number for pagination
            page_size: Number of records per page
            
        Returns:
            Dictionary with matching invoices and pagination metadata
        """
        pass
    
    @abstractmethod
    async def get_partners(
        self,
        search_term: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetch partners/customers from the ERP system
        
        Args:
            search_term: Optional term to search for in partner name or reference
            limit: Maximum number of partners to return
            
        Returns:
            List of partner dictionaries
        """
        pass
    
    @abstractmethod
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate invoice data for FIRS compliance
        
        Args:
            invoice_data: Invoice data to validate
            
        Returns:
            Dictionary with validation results
        """
        pass
    
    @abstractmethod
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """
        Transform ERP invoice data to FIRS-compliant format
        
        Args:
            invoice_data: Raw invoice data from ERP
            target_format: Target FIRS format (default: UBL_BIS_3.0)
            
        Returns:
            Dictionary with transformed invoice data
        """
        pass
    
    @abstractmethod
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update invoice status in the ERP system
        
        Args:
            invoice_id: ID of the invoice to update
            status_data: Status update data
            
        Returns:
            Dictionary with update results
        """
        pass
    
    @abstractmethod
    async def get_company_info(self) -> Dict[str, Any]:
        """
        Get company information from the ERP system
        
        Returns:
            Dictionary with company information
        """
        pass
    
    @abstractmethod
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """
        Get tax configuration from the ERP system
        
        Returns:
            Dictionary with tax configuration
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the ERP system
        
        Returns:
            True if disconnection successful
        """
        pass
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status
        
        Returns:
            Dictionary with connection status information
        """
        return {
            'connected': self.connected,
            'authenticated': self.authenticated,
            'last_connection_time': self.last_connection_time.isoformat() if self.last_connection_time else None,
            'erp_type': self.erp_type,
            'erp_version': self.erp_version,
            'supported_features': self.supported_features
        }
    
    def is_healthy(self) -> bool:
        """
        Check if the connector is healthy and ready to process requests
        
        Returns:
            True if connector is healthy
        """
        return self.connected and self.authenticated
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the ERP connection
        
        Returns:
            Dictionary with health check results
        """
        try:
            # Test basic connectivity
            test_result = await self.test_connection()
            
            return {
                'healthy': test_result.success,
                'status': 'healthy' if test_result.success else 'unhealthy',
                'message': test_result.message,
                'details': test_result.details,
                'timestamp': datetime.utcnow().isoformat(),
                'erp_type': self.erp_type,
                'erp_version': self.erp_version
            }
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'message': f"Health check failed: {str(e)}",
                'error_type': type(e).__name__,
                'timestamp': datetime.utcnow().isoformat(),
                'erp_type': self.erp_type
            }
    
    def get_connector_info(self) -> Dict[str, Any]:
        """
        Get information about this connector
        
        Returns:
            Dictionary with connector information
        """
        return {
            'connector_class': self.__class__.__name__,
            'erp_type': self.erp_type,
            'erp_version': self.erp_version,
            'supported_features': self.supported_features,
            'connection_status': self.get_connection_status(),
            'config_keys': list(self.config.keys())
        }