"""
HubSpot CRM integration connector.

This module provides integration with the HubSpot CRM platform,
handling authentication, data retrieval, and transformation.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx

from app.integrations.base.connector import BaseConnector, IntegrationTestResult
from app.integrations.base.auth import create_auth_handler, OAuth2Auth
from app.integrations.base.monitor import IntegrationMonitor, OperationTimer
from app.integrations.base.errors import (
    IntegrationError,
    AuthenticationError,
    handle_integration_error
)

logger = logging.getLogger(__name__)


class HubSpotConnector(BaseConnector):
    """HubSpot CRM integration connector."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize HubSpot connector.
        
        Args:
            connection_config: Connection configuration including credentials
        """
        super().__init__(connection_config)
        
        # Set up authentication handler
        auth_config = connection_config.get("auth", {})
        auth_config["auth_type"] = auth_config.get("auth_type", "oauth2")
        self.auth_handler = create_auth_handler(auth_config)
        
        # Create HTTP client
        self.api_base_url = "https://api.hubapi.com"
        
        # Set up monitoring
        self.monitor = IntegrationMonitor(
            integration_type="crm",
            integration_name="hubspot",
            connection_id=connection_config.get("connection_id", "unknown")
        )
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with HubSpot API using OAuth2.
        
        Returns:
            Dict with authentication results
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            with OperationTimer(self.monitor, "authenticate"):
                # For OAuth2, we need to get a valid access token
                if isinstance(self.auth_handler, OAuth2Auth):
                    token, expiry = await self.auth_handler.get_access_token()
                    return {
                        "access_token": token,
                        "expires_at": expiry.isoformat()
                    }
                else:
                    raise AuthenticationError(
                        "Unsupported authentication method for HubSpot",
                        details={"auth_type": self.auth_handler.type}
                    )
        except Exception as e:
            error = handle_integration_error(e, "HubSpot", "authenticate")
            raise error
    
    async def get_deals(
        self,
        limit: int = 100,
        offset: int = 0,
        properties: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get deals from HubSpot.
        
        Args:
            limit: Maximum number of deals to return
            offset: Offset for pagination
            properties: List of deal properties to include
            filters: Filters to apply
            
        Returns:
            Dict with deals data
            
        Raises:
            IntegrationError: If the operation fails
        """
        # Default properties if not specified
        if not properties:
            properties = [
                "dealname",
                "amount",
                "dealstage",
                "closedate",
                "hubspot_owner_id",
                "createdate"
            ]
            
        try:
            with OperationTimer(self.monitor, "get_deals"):
                # Make sure we're authenticated
                if not self.is_authenticated():
                    await self.authenticate()
                
                # Prepare headers
                headers = await self.auth_handler.prepare_headers()
                headers["Content-Type"] = "application/json"
                
                # Prepare query parameters
                params = {
                    "limit": limit,
                    "offset": offset,
                    "properties": properties
                }
                
                # Prepare request URL
                url = f"{self.api_base_url}/crm/v3/objects/deals"
                
                # Make the API request
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    return response.json()
                    
        except Exception as e:
            error = handle_integration_error(e, "HubSpot", "get_deals")
            raise error
    
    async def get_deal_by_id(self, deal_id: str, properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get a specific deal from HubSpot by ID.
        
        Args:
            deal_id: HubSpot deal ID
            properties: List of deal properties to include
            
        Returns:
            Dict with deal data
            
        Raises:
            IntegrationError: If the operation fails
        """
        # Default properties if not specified
        if not properties:
            properties = [
                "dealname",
                "amount",
                "dealstage",
                "closedate",
                "hubspot_owner_id",
                "createdate"
            ]
            
        try:
            with OperationTimer(self.monitor, "get_deal_by_id"):
                # Make sure we're authenticated
                if not self.is_authenticated():
                    await self.authenticate()
                
                # Prepare headers
                headers = await self.auth_handler.prepare_headers()
                headers["Content-Type"] = "application/json"
                
                # Prepare query parameters
                params = {
                    "properties": properties
                }
                
                # Prepare request URL
                url = f"{self.api_base_url}/crm/v3/objects/deals/{deal_id}"
                
                # Make the API request
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    return response.json()
                    
        except Exception as e:
            error = handle_integration_error(e, "HubSpot", "get_deal_by_id")
            raise error
    
    async def transform_deal_to_invoice(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform HubSpot deal data to invoice format.
        
        Args:
            deal_data: HubSpot deal data
            
        Returns:
            Dict with invoice data
            
        Raises:
            IntegrationError: If the transformation fails
        """
        try:
            with OperationTimer(self.monitor, "transform_deal_to_invoice"):
                # Extract properties from deal data
                properties = deal_data.get("properties", {})
                
                # Get associated contact/company data for invoice recipient
                customer_data = await self._get_deal_customer_data(deal_data.get("id"))
                
                # Create basic invoice structure
                invoice_data = {
                    "invoice_number": f"HUB-{deal_data.get('id', '')}",
                    "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                    "due_date": properties.get("closedate", ""),
                    "currency": "NGN",  # Default to Nigerian Naira
                    "amount": properties.get("amount", 0),
                    "status": "draft",
                    "description": properties.get("dealname", ""),
                    "customer": customer_data,
                    "line_items": [
                        {
                            "description": properties.get("dealname", "HubSpot Deal"),
                            "quantity": 1,
                            "unit_price": properties.get("amount", 0),
                            "amount": properties.get("amount", 0)
                        }
                    ],
                    "metadata": {
                        "source": "hubspot",
                        "deal_id": deal_data.get("id", ""),
                        "deal_stage": properties.get("dealstage", "")
                    }
                }
                
                return invoice_data
                
        except Exception as e:
            error = handle_integration_error(e, "HubSpot", "transform_deal_to_invoice")
            raise error
    
    async def _get_deal_customer_data(self, deal_id: str) -> Dict[str, Any]:
        """
        Get customer data associated with a deal.
        
        Args:
            deal_id: HubSpot deal ID
            
        Returns:
            Dict with customer data
            
        Raises:
            IntegrationError: If the operation fails
        """
        try:
            # Make sure we're authenticated
            if not self.is_authenticated():
                await self.authenticate()
            
            # Prepare headers
            headers = await self.auth_handler.prepare_headers()
            headers["Content-Type"] = "application/json"
            
            # Prepare request URL for associations
            url = f"{self.api_base_url}/crm/v3/objects/deals/{deal_id}/associations/contacts"
            
            # Make the API request to get associated contacts
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                associations = response.json()
                
                # If there are associated contacts, get the first one
                if associations.get("results"):
                    contact_id = associations["results"][0].get("id")
                    
                    # Get contact details
                    contact_url = f"{self.api_base_url}/crm/v3/objects/contacts/{contact_id}"
                    contact_response = await client.get(
                        contact_url,
                        headers=headers,
                        params={"properties": ["firstname", "lastname", "email", "phone", "address"]}
                    )
                    contact_response.raise_for_status()
                    contact = contact_response.json()
                    
                    contact_props = contact.get("properties", {})
                    return {
                        "name": f"{contact_props.get('firstname', '')} {contact_props.get('lastname', '')}".strip(),
                        "email": contact_props.get("email", ""),
                        "phone": contact_props.get("phone", ""),
                        "address": contact_props.get("address", ""),
                        "external_id": contact_id
                    }
                
                # If no contacts, try to get company
                company_url = f"{self.api_base_url}/crm/v3/objects/deals/{deal_id}/associations/companies"
                company_assoc_response = await client.get(company_url, headers=headers)
                company_assoc_response.raise_for_status()
                company_associations = company_assoc_response.json()
                
                if company_associations.get("results"):
                    company_id = company_associations["results"][0].get("id")
                    
                    # Get company details
                    company_detail_url = f"{self.api_base_url}/crm/v3/objects/companies/{company_id}"
                    company_response = await client.get(
                        company_detail_url,
                        headers=headers,
                        params={"properties": ["name", "domain", "phone", "address"]}
                    )
                    company_response.raise_for_status()
                    company = company_response.json()
                    
                    company_props = company.get("properties", {})
                    return {
                        "name": company_props.get("name", ""),
                        "email": f"info@{company_props.get('domain', '')}",
                        "phone": company_props.get("phone", ""),
                        "address": company_props.get("address", ""),
                        "external_id": company_id,
                        "is_company": True
                    }
            
            # Default if no associations found
            return {
                "name": "Unknown Customer",
                "email": "",
                "phone": "",
                "address": "",
                "external_id": ""
            }
                
        except Exception as e:
            logger.warning(f"Error getting customer data for deal {deal_id}: {str(e)}")
            # Return empty customer data on error to avoid failing the whole transformation
            return {
                "name": "Unknown Customer",
                "email": "",
                "phone": "",
                "address": "",
                "external_id": ""
            }


# Create a singleton instance
hubspot_connector = None


def get_hubspot_connector(connection_config: Dict[str, Any]) -> HubSpotConnector:
    """
    Get or create a HubSpot connector instance.
    
    Args:
        connection_config: Connection configuration
        
    Returns:
        HubSpotConnector instance
    """
    global hubspot_connector
    
    # Create new instance if not exists or if config has changed
    if hubspot_connector is None or hubspot_connector.config != connection_config:
        hubspot_connector = HubSpotConnector(connection_config)
        
    return hubspot_connector
