"""
HubSpot Data Extraction Module
Handles data extraction and formatting from HubSpot CRM services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .exceptions import HubSpotAPIError, HubSpotDataError

logger = logging.getLogger(__name__)


class HubSpotDataExtractor:
    """Handles data extraction and formatting from HubSpot CRM."""
    
    def __init__(self, rest_client):
        """Initialize with a HubSpot REST client instance."""
        self.rest_client = rest_client
    
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
        Get deals from HubSpot CRM - SI Role Function.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip (converted to 'after' for HubSpot)
            start_date: Filter deals from this date
            end_date: Filter deals until this date
            stage: Filter by deal stage
            owner_id: Filter by deal owner
            status: Filter by deal status (maps to dealstage)
            
        Returns:
            List of deal records
        """
        try:
            # Build search filters
            filters = []
            
            if start_date:
                filters.append({
                    'propertyName': 'createdate',
                    'operator': 'GTE',
                    'value': int(start_date.timestamp() * 1000)  # HubSpot uses milliseconds
                })
            
            if end_date:
                filters.append({
                    'propertyName': 'createdate',
                    'operator': 'LTE',
                    'value': int(end_date.timestamp() * 1000)
                })
            
            if stage or status:
                stage_filter = stage or status
                filters.append({
                    'propertyName': 'dealstage',
                    'operator': 'EQ',
                    'value': stage_filter
                })
            
            if owner_id:
                filters.append({
                    'propertyName': 'hubspot_owner_id',
                    'operator': 'EQ',
                    'value': owner_id
                })
            
            # Convert offset to after parameter (simplified pagination)
            after = str(offset) if offset > 0 else None
            
            # Use search if filters are present, otherwise get all deals
            if filters:
                response = await self.rest_client.search_crm_objects(
                    'deals',
                    filters=filters,
                    limit=limit,
                    after=after,
                    sorts=[{'propertyName': 'hs_lastmodifieddate', 'direction': 'DESCENDING'}]
                )
            else:
                response = await self.rest_client.get_deals(
                    limit=limit,
                    after=after
                )
            
            if not response.get('success'):
                raise HubSpotDataError(f"Failed to retrieve deals: {response.get('error')}")
            
            deals = []
            for deal_data in response.get('results', []):
                formatted_deal = await self._format_deal_data(deal_data)
                deals.append(formatted_deal)
            
            return deals
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot deals: {str(e)}")
            raise HubSpotDataError(f"Error retrieving HubSpot deals: {str(e)}")
    
    async def get_deal_by_id(self, deal_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a specific deal by ID from HubSpot - SI Role Function.
        
        Args:
            deal_id: The deal ID to retrieve
            
        Returns:
            Deal record data
        """
        try:
            response = await self.rest_client.get_crm_object_by_id(
                'deals',
                str(deal_id),
                associations=['companies', 'contacts', 'line_items']
            )
            
            if not response.get('success'):
                raise HubSpotDataError(f"Failed to retrieve deal {deal_id}: {response.get('error')}")
            
            # Also get line items
            line_items_response = await self.rest_client.get_deal_line_items(str(deal_id))
            line_items = line_items_response.get('data', []) if line_items_response.get('success') else []
            
            deal_data = response.get('data', {})
            return await self._format_deal_data(deal_data, line_items)
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot deal {deal_id}: {str(e)}")
            raise HubSpotDataError(f"Error retrieving HubSpot deal {deal_id}: {str(e)}")
    
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
        Search deals with specific criteria - SI Role Function.
        
        Args:
            company_name: Filter by company name (associated company)
            contact_name: Filter by contact name (associated contact)
            deal_name: Filter by deal name
            amount_range: Tuple of (min_amount, max_amount)
            date_range: Tuple of (start_date, end_date)
            stage: Filter by deal stage
            limit: Maximum number of records to return
            
        Returns:
            List of matching deal records
        """
        try:
            filters = []
            
            if deal_name:
                filters.append({
                    'propertyName': 'dealname',
                    'operator': 'CONTAINS_TOKEN',
                    'value': deal_name
                })
            
            if amount_range:
                min_amount, max_amount = amount_range
                if min_amount is not None:
                    filters.append({
                        'propertyName': 'amount',
                        'operator': 'GTE',
                        'value': min_amount
                    })
                if max_amount is not None:
                    filters.append({
                        'propertyName': 'amount',
                        'operator': 'LTE',
                        'value': max_amount
                    })
            
            if date_range:
                start_date, end_date = date_range
                if start_date:
                    filters.append({
                        'propertyName': 'closedate',
                        'operator': 'GTE',
                        'value': int(datetime.fromisoformat(start_date).timestamp() * 1000)
                    })
                if end_date:
                    filters.append({
                        'propertyName': 'closedate',
                        'operator': 'LTE',
                        'value': int(datetime.fromisoformat(end_date).timestamp() * 1000)
                    })
            
            if stage:
                filters.append({
                    'propertyName': 'dealstage',
                    'operator': 'EQ',
                    'value': stage
                })
            
            # Note: HubSpot search doesn't directly support filtering by associated object names
            # For company_name and contact_name, we would need to do a two-step process:
            # 1. Search companies/contacts by name first
            # 2. Search deals associated with those companies/contacts
            # For simplicity, we'll search deals and filter client-side if needed
            
            response = await self.rest_client.search_crm_objects(
                'deals',
                filters=filters,
                limit=limit,
                sorts=[{'propertyName': 'hs_lastmodifieddate', 'direction': 'DESCENDING'}]
            )
            
            if not response.get('success'):
                raise HubSpotDataError(f"Failed to search deals: {response.get('error')}")
            
            deals = []
            for deal_data in response.get('results', []):
                formatted_deal = await self._format_deal_data(deal_data)
                
                # Client-side filtering for company/contact names if specified
                if company_name or contact_name:
                    # Get associated companies and contacts
                    associations = deal_data.get('associations', {})
                    
                    # Check company name
                    if company_name:
                        companies = associations.get('companies', {}).get('results', [])
                        company_match = False
                        for company in companies:
                            # Would need to fetch company details to check name
                            # For now, skip this filtering
                            pass
                        if company_name and not company_match:
                            continue
                    
                    # Check contact name
                    if contact_name:
                        contacts = associations.get('contacts', {}).get('results', [])
                        contact_match = False
                        for contact in contacts:
                            # Would need to fetch contact details to check name
                            # For now, skip this filtering
                            pass
                        if contact_name and not contact_match:
                            continue
                
                deals.append(formatted_deal)
            
            return deals
            
        except Exception as e:
            logger.error(f"Error searching HubSpot deals: {str(e)}")
            raise HubSpotDataError(f"Error searching HubSpot deals: {str(e)}")
    
    async def get_customers(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get customers/companies from HubSpot - SI Role Function.
        
        Args:
            search_term: Optional search term to filter customers
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of customer/company records
        """
        try:
            after = str(offset) if offset > 0 else None
            
            # Use search if search term is provided
            if search_term:
                filters = [{
                    'propertyName': 'name',
                    'operator': 'CONTAINS_TOKEN',
                    'value': search_term
                }]
                
                response = await self.rest_client.search_crm_objects(
                    'companies',
                    filters=filters,
                    limit=limit,
                    after=after
                )
            else:
                response = await self.rest_client.get_companies(
                    limit=limit,
                    after=after
                )
            
            if not response.get('success'):
                raise HubSpotDataError(f"Failed to retrieve companies: {response.get('error')}")
            
            customers = []
            for company_data in response.get('results', []):
                customer = {
                    "id": company_data.get('id', ''),
                    "name": company_data.get('properties', {}).get('name', ''),
                    "domain": company_data.get('properties', {}).get('domain', ''),
                    "industry": company_data.get('properties', {}).get('industry', ''),
                    "phone": company_data.get('properties', {}).get('phone', ''),
                    "website": company_data.get('properties', {}).get('website', ''),
                    "address": {
                        "street": company_data.get('properties', {}).get('address', ''),
                        "city": company_data.get('properties', {}).get('city', ''),
                        "state": company_data.get('properties', {}).get('state', ''),
                        "postal_code": company_data.get('properties', {}).get('zip', ''),
                        "country": company_data.get('properties', {}).get('country', '')
                    },
                    "description": company_data.get('properties', {}).get('description', ''),
                    "created_date": self._format_hubspot_date(company_data.get('properties', {}).get('createdate')),
                    "last_modified_date": self._format_hubspot_date(company_data.get('properties', {}).get('hs_lastmodifieddate')),
                    "owner_id": company_data.get('properties', {}).get('hubspot_owner_id', ''),
                    "source": "hubspot_companies"
                }
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot companies: {str(e)}")
            raise HubSpotDataError(f"Error retrieving HubSpot companies: {str(e)}")
    
    async def get_contacts(
        self,
        search_term: Optional[str] = None,
        company_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get contacts from HubSpot - SI Role Function.
        
        Args:
            search_term: Optional search term to filter contacts
            company_id: Filter by company ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of contact records
        """
        try:
            after = str(offset) if offset > 0 else None
            
            # Build search filters
            filters = []
            
            if search_term:
                # Search by email or name
                filters.append({
                    'propertyName': 'email',
                    'operator': 'CONTAINS_TOKEN',
                    'value': search_term
                })
            
            if company_id:
                filters.append({
                    'propertyName': 'associatedcompanyid',
                    'operator': 'EQ',
                    'value': company_id
                })
            
            # Use search if filters are present
            if filters:
                response = await self.rest_client.search_crm_objects(
                    'contacts',
                    filters=filters,
                    limit=limit,
                    after=after
                )
            else:
                response = await self.rest_client.get_contacts(
                    limit=limit,
                    after=after
                )
            
            if not response.get('success'):
                raise HubSpotDataError(f"Failed to retrieve contacts: {response.get('error')}")
            
            contacts = []
            for contact_data in response.get('results', []):
                contact = {
                    "id": contact_data.get('id', ''),
                    "first_name": contact_data.get('properties', {}).get('firstname', ''),
                    "last_name": contact_data.get('properties', {}).get('lastname', ''),
                    "name": f"{contact_data.get('properties', {}).get('firstname', '')} {contact_data.get('properties', {}).get('lastname', '')}".strip(),
                    "email": contact_data.get('properties', {}).get('email', ''),
                    "phone": contact_data.get('properties', {}).get('phone', ''),
                    "company": contact_data.get('properties', {}).get('company', ''),
                    "job_title": contact_data.get('properties', {}).get('jobtitle', ''),
                    "address": {
                        "street": contact_data.get('properties', {}).get('address', ''),
                        "city": contact_data.get('properties', {}).get('city', ''),
                        "state": contact_data.get('properties', {}).get('state', ''),
                        "postal_code": contact_data.get('properties', {}).get('zip', ''),
                        "country": contact_data.get('properties', {}).get('country', '')
                    },
                    "created_date": self._format_hubspot_date(contact_data.get('properties', {}).get('createdate')),
                    "last_modified_date": self._format_hubspot_date(contact_data.get('properties', {}).get('lastmodifieddate')),
                    "owner_id": contact_data.get('properties', {}).get('hubspot_owner_id', ''),
                    "source": "hubspot_contacts"
                }
                contacts.append(contact)
            
            return contacts
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot contacts: {str(e)}")
            raise HubSpotDataError(f"Error retrieving HubSpot contacts: {str(e)}")
    
    async def get_products(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get products from HubSpot - SI Role Function.
        
        Args:
            search_term: Optional search term to filter products
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of product records
        """
        try:
            after = str(offset) if offset > 0 else None
            
            # Use search if search term is provided
            if search_term:
                filters = [{
                    'propertyName': 'name',
                    'operator': 'CONTAINS_TOKEN',
                    'value': search_term
                }]
                
                response = await self.rest_client.search_crm_objects(
                    'products',
                    filters=filters,
                    limit=limit,
                    after=after
                )
            else:
                response = await self.rest_client.get_products(
                    limit=limit,
                    after=after
                )
            
            if not response.get('success'):
                raise HubSpotDataError(f"Failed to retrieve products: {response.get('error')}")
            
            products = []
            for product_data in response.get('results', []):
                product = {
                    "id": product_data.get('id', ''),
                    "name": product_data.get('properties', {}).get('name', ''),
                    "description": product_data.get('properties', {}).get('description', ''),
                    "price": float(product_data.get('properties', {}).get('price', 0)) if product_data.get('properties', {}).get('price') else 0,
                    "sku": product_data.get('properties', {}).get('hs_sku', ''),
                    "cost_of_goods_sold": float(product_data.get('properties', {}).get('hs_cost_of_goods_sold', 0)) if product_data.get('properties', {}).get('hs_cost_of_goods_sold') else 0,
                    "product_type": product_data.get('properties', {}).get('hs_product_type', ''),
                    "created_date": self._format_hubspot_date(product_data.get('properties', {}).get('createdate')),
                    "last_modified_date": self._format_hubspot_date(product_data.get('properties', {}).get('hs_lastmodifieddate')),
                    "source": "hubspot_products"
                }
                products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot products: {str(e)}")
            raise HubSpotDataError(f"Error retrieving HubSpot products: {str(e)}")
    
    async def _format_deal_data(self, deal: Dict[str, Any], line_items: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Format deal data for consistent output - SI Role Function.
        
        Args:
            deal: HubSpot deal record
            line_items: Optional deal line items
            
        Returns:
            Formatted deal data
        """
        try:
            properties = deal.get('properties', {})
            associations = deal.get('associations', {})
            
            deal_data = {
                "id": deal.get('id', ''),
                "name": properties.get('dealname', ''),
                "deal_name": properties.get('dealname', ''),
                "amount": float(properties.get('amount', 0)) if properties.get('amount') else 0,
                "close_date": self._format_hubspot_date(properties.get('closedate')),
                "stage": properties.get('dealstage', ''),
                "stage_name": properties.get('dealstage', ''),
                "pipeline": properties.get('pipeline', ''),
                "deal_type": properties.get('dealtype', ''),
                "probability": float(properties.get('hs_deal_stage_probability', 0)) if properties.get('hs_deal_stage_probability') else 0,
                "description": properties.get('description', ''),
                "created_date": self._format_hubspot_date(properties.get('createdate')),
                "last_modified_date": self._format_hubspot_date(properties.get('hs_lastmodifieddate')),
                
                # Owner information
                "owner": {
                    "id": properties.get('hubspot_owner_id', ''),
                    "hubspot_owner_id": properties.get('hubspot_owner_id', '')
                },
                
                # Associated companies
                "companies": self._extract_associations(associations.get('companies', {})),
                
                # Associated contacts
                "contacts": self._extract_associations(associations.get('contacts', {})),
                
                # HubSpot-specific fields
                "hubspot_deal_id": deal.get('id', ''),
                "hubspot_deal_stage": properties.get('dealstage', ''),
                "hubspot_pipeline": properties.get('pipeline', ''),
                "source": "hubspot_deals",
                
                # Line items
                "line_items": self._format_deal_line_items(line_items) if line_items else []
            }
            
            # Set primary company if available
            if deal_data["companies"]:
                primary_company = deal_data["companies"][0]
                deal_data["company"] = {
                    "id": primary_company.get('id', ''),
                    "name": primary_company.get('name', ''),
                    "hubspot_company_id": primary_company.get('id', '')
                }
            else:
                deal_data["company"] = {"id": "", "name": "", "hubspot_company_id": ""}
            
            return deal_data
            
        except Exception as e:
            logger.error(f"Error formatting HubSpot deal data: {str(e)}")
            raise HubSpotDataError(f"Error formatting HubSpot deal data: {str(e)}")
    
    def _format_deal_line_items(self, line_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format HubSpot deal line items."""
        formatted_lines = []
        
        for i, line in enumerate(line_items):
            properties = line.get('properties', {})
            associations = line.get('associations', {})
            
            formatted_line = {
                "id": line.get('id', ''),
                "line_number": i + 1,
                "name": properties.get('name', ''),
                "quantity": float(properties.get('quantity', 1)),
                "price": float(properties.get('price', 0)),
                "amount": float(properties.get('amount', 0)),
                "product_id": properties.get('hs_product_id', ''),
                "created_date": self._format_hubspot_date(properties.get('createdate')),
                "last_modified_date": self._format_hubspot_date(properties.get('hs_lastmodifieddate')),
                "products": self._extract_associations(associations.get('products', {})),
                "source": "hubspot_line_items"
            }
            formatted_lines.append(formatted_line)
        
        return formatted_lines
    
    def _extract_associations(self, association_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract association data from HubSpot response."""
        associations = []
        results = association_data.get('results', [])
        
        for result in results:
            association = {
                "id": result.get('id', ''),
                "type": result.get('type', ''),
                "name": result.get('name', ''),  # This would need to be fetched separately
                "source": "hubspot_association"
            }
            associations.append(association)
        
        return associations
    
    def _format_hubspot_date(self, hubspot_date) -> Optional[str]:
        """Format HubSpot date to ISO format."""
        if not hubspot_date:
            return None
        
        try:
            # HubSpot timestamps are in milliseconds
            if isinstance(hubspot_date, (int, str)):
                timestamp = int(hubspot_date) / 1000  # Convert to seconds
                return datetime.fromtimestamp(timestamp).isoformat()
            
            # If it's already a datetime object, convert to ISO
            if hasattr(hubspot_date, 'isoformat'):
                return hubspot_date.isoformat()
            
            return str(hubspot_date)
            
        except Exception as e:
            logger.warning(f"Error formatting HubSpot date {hubspot_date}: {str(e)}")
            return str(hubspot_date) if hubspot_date else None
    
    def _map_hubspot_stage(self, hubspot_stage: str) -> str:
        """Map HubSpot deal stage to standard stage."""
        # HubSpot stages are often custom, but here are some common mappings
        stage_mapping = {
            'appointmentscheduled': 'appointment',
            'qualifiedtobuy': 'qualified',
            'presentationscheduled': 'presentation',
            'decisionmakerboughtin': 'decision_maker',
            'contractsent': 'contract_sent',
            'closedwon': 'won',
            'closedlost': 'lost'
        }
        
        return stage_mapping.get(hubspot_stage.lower(), 'unknown')