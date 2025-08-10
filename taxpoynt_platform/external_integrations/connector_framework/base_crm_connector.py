"""
Base CRM Connector
Abstract base class for all CRM system connectors in the TaxPoynt eInvoice platform.

This module provides the foundation for CRM integrations, defining standard interfaces
for deal/opportunity management, customer data extraction, and invoice generation workflows.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# from app.schemas.integration import IntegrationTestResult  # TODO: Replace with taxpoynt_platform schema


class CRMConnectionError(Exception):
    """Base exception for CRM connection issues"""
    pass


class CRMAuthenticationError(Exception):
    """Base exception for CRM authentication issues"""
    pass


class CRMDataError(Exception):
    """Base exception for CRM data processing issues"""
    pass


class CRMValidationError(Exception):
    """Base exception for CRM data validation issues"""
    pass


class BaseCRMConnector(ABC):
    """
    Abstract base class for all CRM system connectors.
    
    This class defines the standard interface for CRM integrations in the TaxPoynt
    eInvoice system, focusing on deal/opportunity management and invoice generation
    workflows.
    
    CRM Role Responsibilities:
    - Deal/Opportunity data extraction and management
    - Customer/Contact information synchronization
    - Lead qualification and conversion tracking
    - Invoice generation from deals/opportunities
    - Sales pipeline management
    - Revenue forecasting and reporting
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the CRM connector with configuration.
        
        Args:
            config: Dictionary containing CRM-specific configuration parameters
        """
        self.config = config
    
    @property
    @abstractmethod
    def crm_type(self) -> str:
        """Return the CRM system type identifier"""
        pass
    
    @property
    @abstractmethod
    def crm_version(self) -> str:
        """Return the CRM system version"""
        pass
    
    @property
    @abstractmethod
    def supported_features(self) -> List[str]:
        """Return list of supported CRM features"""
        pass
    
    # Connection and Authentication Methods
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to the CRM system.
        
        Returns:
            Dict with connection status and details
        """
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the CRM system.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the CRM system and cleanup resources.
        
        Returns:
            bool: True if disconnection successful
        """
        pass
    
    # Deal/Opportunity Management Methods
    @abstractmethod
    async def get_deals(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        stage: Optional[str] = None,
        owner_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get deals/opportunities from the CRM system.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter deals from this date
            end_date: Filter deals until this date
            stage: Filter by deal stage
            owner_id: Filter by deal owner
            status: Filter by deal status
            
        Returns:
            List of deal/opportunity records
        """
        pass
    
    @abstractmethod
    async def get_deal_by_id(self, deal_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a specific deal/opportunity by ID.
        
        Args:
            deal_id: The deal/opportunity ID to retrieve
            
        Returns:
            Deal/opportunity record data
        """
        pass
    
    @abstractmethod
    async def search_deals(
        self,
        company_name: Optional[str] = None,
        contact_name: Optional[str] = None,
        deal_name: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        stage: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search deals/opportunities with specific criteria.
        
        Args:
            company_name: Filter by company name
            contact_name: Filter by contact name
            deal_name: Filter by deal name
            amount_range: Tuple of (min_amount, max_amount)
            date_range: Tuple of (start_date, end_date)
            stage: Filter by deal stage
            limit: Maximum number of records to return
            
        Returns:
            List of matching deal/opportunity records
        """
        pass
    
    # Customer/Contact Management Methods
    @abstractmethod
    async def get_customers(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get customers/companies from the CRM system.
        
        Args:
            search_term: Optional search term to filter customers
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of customer/company records
        """
        pass
    
    @abstractmethod
    async def get_contacts(
        self,
        search_term: Optional[str] = None,
        company_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get contacts from the CRM system.
        
        Args:
            search_term: Optional search term to filter contacts
            company_id: Filter by company/account ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of contact records
        """
        pass
    
    @abstractmethod
    async def get_products(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get products/services from the CRM system.
        
        Args:
            search_term: Optional search term to filter products
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of product/service records
        """
        pass
    
    # Invoice Generation Methods
    @abstractmethod
    async def validate_deal_data(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate deal data before invoice generation.
        
        Args:
            deal_data: Deal data to validate
            
        Returns:
            Validation result with errors and warnings
        """
        pass
    
    @abstractmethod
    async def transform_deal_to_invoice(
        self,
        deal_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """
        Transform CRM deal data to invoice format.
        
        Args:
            deal_data: Deal data to transform
            target_format: Target invoice format (default: UBL_BIS_3.0)
            
        Returns:
            Transformed invoice data
        """
        pass
    
    @abstractmethod
    async def update_deal_status(
        self,
        deal_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update deal status in the CRM system.
        
        Args:
            deal_id: Deal ID to update
            status_data: New status data
            
        Returns:
            Update result
        """
        pass
    
    # Pipeline and Sales Management Methods
    async def get_pipeline_stages(self) -> List[Dict[str, Any]]:
        """
        Get pipeline stages from the CRM system.
        
        Returns:
            List of pipeline stage definitions
        """
        # Default implementation - can be overridden by specific CRM connectors
        return []
    
    async def get_sales_forecast(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get sales forecast data from the CRM system.
        
        Args:
            start_date: Forecast start date
            end_date: Forecast end date
            
        Returns:
            Sales forecast data
        """
        # Default implementation - can be overridden by specific CRM connectors
        return {
            'forecast_period': f"{start_date} to {end_date}" if start_date and end_date else "N/A",
            'total_forecasted_revenue': 0,
            'deals_in_pipeline': 0,
            'conversion_rate': 0,
            'average_deal_size': 0
        }
    
    # Utility Methods
    def is_connected(self) -> bool:
        """
        Check if connected to the CRM system.
        
        Returns:
            bool: True if connected, False otherwise
        """
        # Default implementation - should be overridden by specific CRM connectors
        return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get detailed connection status.
        
        Returns:
            Dictionary with connection status information
        """
        return {
            "crm_type": self.crm_type,
            "crm_version": self.crm_version,
            "connected": self.is_connected(),
            "last_activity": datetime.now().isoformat(),
            "supported_features": self.supported_features
        }
    
    # Legacy compatibility methods
    async def get_partners(self, search_term: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get business partners (customers and contacts combined).
        
        Args:
            search_term: Optional search term
            limit: Maximum number of records to return
            
        Returns:
            List of partner records
        """
        # Combine customers and contacts
        customers = await self.get_customers(search_term=search_term, limit=limit//2)
        contacts = await self.get_contacts(search_term=search_term, limit=limit//2)
        
        partners = []
        for customer in customers:
            partner = {
                "id": customer.get('id', ''),
                "name": customer.get('name', ''),
                "partner_type": "customer",
                "source": f"{self.crm_type}_customers"
            }
            partners.append(partner)
        
        for contact in contacts:
            partner = {
                "id": contact.get('id', ''),
                "name": contact.get('name', ''),
                "partner_type": "contact",
                "source": f"{self.crm_type}_contacts"
            }
            partners.append(partner)
        
        return partners
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            Dictionary with user information
        """
        return {
            "crm_type": self.crm_type,
            "connected": self.is_connected()
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """
        Get information about the CRM system.
        
        Returns:
            Dictionary with CRM system information
        """
        return {
            "crm_type": self.crm_type,
            "crm_version": self.crm_version,
            "system_type": f"{self.crm_type.title()} CRM",
            "supported_features": self.supported_features
        }