"""
Salesforce Data Extraction Module
Handles data extraction and formatting from Salesforce CRM services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .exceptions import SalesforceAPIError, SalesforceDataError

logger = logging.getLogger(__name__)


class SalesforceDataExtractor:
    """Handles data extraction and formatting from Salesforce CRM."""
    
    def __init__(self, rest_client):
        """Initialize with a Salesforce REST client instance."""
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
        Get deals/opportunities from Salesforce CRM - SI Role Function.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            start_date: Filter deals from this date
            end_date: Filter deals until this date
            stage: Filter by deal stage
            owner_id: Filter by deal owner
            status: Filter by deal status (maps to StageName)
            
        Returns:
            List of deal/opportunity records
        """
        try:
            # Map date parameters to close date filters
            close_date_from = start_date.strftime('%Y-%m-%d') if start_date else None
            close_date_to = end_date.strftime('%Y-%m-%d') if end_date else None
            
            # Use stage or status for stage filtering
            stage_filter = stage or status
            
            response = await self.rest_client.get_opportunities(
                limit=limit,
                offset=offset,
                stage=stage_filter,
                owner_id=owner_id,
                close_date_from=close_date_from,
                close_date_to=close_date_to
            )
            
            if not response.get('success'):
                raise SalesforceDataError(f"Failed to retrieve opportunities: {response.get('error')}")
            
            deals = []
            for opportunity_data in response.get('records', []):
                formatted_deal = await self._format_opportunity_data(opportunity_data)
                deals.append(formatted_deal)
            
            return deals
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce opportunities: {str(e)}")
            raise SalesforceDataError(f"Error retrieving Salesforce opportunities: {str(e)}")
    
    async def get_deal_by_id(self, deal_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get a specific deal/opportunity by ID from Salesforce - SI Role Function.
        
        Args:
            deal_id: The opportunity ID to retrieve
            
        Returns:
            Deal/opportunity record data
        """
        try:
            fields = [
                'Id', 'Name', 'AccountId', 'Account.Name', 'Amount', 'CloseDate',
                'StageName', 'Probability', 'OwnerId', 'Owner.Name', 'Description',
                'CreatedDate', 'LastModifiedDate', 'Type', 'LeadSource',
                'NextStep', 'ForecastCategoryName', 'Campaign.Name'
            ]
            
            response = await self.rest_client.get_sobject_by_id('Opportunity', str(deal_id), fields)
            if not response.get('success'):
                raise SalesforceDataError(f"Failed to retrieve opportunity {deal_id}: {response.get('error')}")
            
            # Also get line items
            line_items_response = await self.rest_client.get_opportunity_line_items(str(deal_id))
            line_items = line_items_response.get('records', []) if line_items_response.get('success') else []
            
            opportunity_data = response.get('data', {})
            return await self._format_opportunity_data(opportunity_data, line_items)
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce opportunity {deal_id}: {str(e)}")
            raise SalesforceDataError(f"Error retrieving Salesforce opportunity {deal_id}: {str(e)}")
    
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
        Search deals/opportunities with specific criteria - SI Role Function.
        
        Args:
            company_name: Filter by company/account name
            contact_name: Filter by contact name (not directly supported in Opportunities)
            deal_name: Filter by opportunity name
            amount_range: Tuple of (min_amount, max_amount)
            date_range: Tuple of (start_date, end_date)
            stage: Filter by opportunity stage
            limit: Maximum number of records to return
            
        Returns:
            List of matching deal/opportunity records
        """
        try:
            # Build SOQL query with search criteria
            fields = [
                'Id', 'Name', 'AccountId', 'Account.Name', 'Amount', 'CloseDate',
                'StageName', 'Probability', 'OwnerId', 'Owner.Name', 'Description',
                'CreatedDate', 'LastModifiedDate', 'Type', 'LeadSource'
            ]
            
            where_conditions = []
            
            if company_name:
                where_conditions.append(f"Account.Name LIKE '%{company_name}%'")
            
            if deal_name:
                where_conditions.append(f"Name LIKE '%{deal_name}%'")
            
            if amount_range:
                min_amount, max_amount = amount_range
                if min_amount is not None:
                    where_conditions.append(f"Amount >= {min_amount}")
                if max_amount is not None:
                    where_conditions.append(f"Amount <= {max_amount}")
            
            if date_range:
                start_date, end_date = date_range
                if start_date:
                    where_conditions.append(f"CloseDate >= {start_date}")
                if end_date:
                    where_conditions.append(f"CloseDate <= {end_date}")
            
            if stage:
                where_conditions.append(f"StageName = '{stage}'")
            
            where_clause = ' AND '.join(where_conditions) if where_conditions else None
            
            response = await self.rest_client.get_sobject_records(
                'Opportunity',
                fields=fields,
                limit=limit,
                where_clause=where_clause,
                order_by='LastModifiedDate DESC'
            )
            
            if not response.get('success'):
                raise SalesforceDataError(f"Failed to search opportunities: {response.get('error')}")
            
            deals = []
            for opportunity_data in response.get('records', []):
                formatted_deal = await self._format_opportunity_data(opportunity_data)
                deals.append(formatted_deal)
            
            return deals
            
        except Exception as e:
            logger.error(f"Error searching Salesforce opportunities: {str(e)}")
            raise SalesforceDataError(f"Error searching Salesforce opportunities: {str(e)}")
    
    async def get_customers(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get customers/accounts from Salesforce - SI Role Function.
        
        Args:
            search_term: Optional search term to filter customers
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of customer/account records
        """
        try:
            response = await self.rest_client.get_accounts(
                limit=limit,
                offset=offset,
                search_term=search_term
            )
            
            if not response.get('success'):
                raise SalesforceDataError(f"Failed to retrieve accounts: {response.get('error')}")
            
            customers = []
            for account_data in response.get('records', []):
                customer = {
                    "id": account_data.get('Id', ''),
                    "name": account_data.get('Name', ''),
                    "type": account_data.get('Type', ''),
                    "industry": account_data.get('Industry', ''),
                    "phone": account_data.get('Phone', ''),
                    "website": account_data.get('Website', ''),
                    "billing_address": self._format_salesforce_address(account_data.get('BillingAddress', {})),
                    "shipping_address": self._format_salesforce_address(account_data.get('ShippingAddress', {})),
                    "description": account_data.get('Description', ''),
                    "annual_revenue": account_data.get('AnnualRevenue'),
                    "number_of_employees": account_data.get('NumberOfEmployees'),
                    "owner_id": account_data.get('OwnerId', ''),
                    "owner_name": account_data.get('Owner', {}).get('Name', ''),
                    "source": "salesforce_accounts"
                }
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce accounts: {str(e)}")
            raise SalesforceDataError(f"Error retrieving Salesforce accounts: {str(e)}")
    
    async def get_contacts(
        self,
        search_term: Optional[str] = None,
        company_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get contacts from Salesforce - SI Role Function.
        
        Args:
            search_term: Optional search term to filter contacts
            company_id: Filter by account/company ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of contact records
        """
        try:
            response = await self.rest_client.get_contacts(
                limit=limit,
                offset=offset,
                account_id=company_id,
                search_term=search_term
            )
            
            if not response.get('success'):
                raise SalesforceDataError(f"Failed to retrieve contacts: {response.get('error')}")
            
            contacts = []
            for contact_data in response.get('records', []):
                contact = {
                    "id": contact_data.get('Id', ''),
                    "first_name": contact_data.get('FirstName', ''),
                    "last_name": contact_data.get('LastName', ''),
                    "name": contact_data.get('Name', ''),
                    "email": contact_data.get('Email', ''),
                    "phone": contact_data.get('Phone', ''),
                    "account_id": contact_data.get('AccountId', ''),
                    "account_name": contact_data.get('Account', {}).get('Name', ''),
                    "title": contact_data.get('Title', ''),
                    "department": contact_data.get('Department', ''),
                    "mailing_address": self._format_salesforce_address(contact_data.get('MailingAddress', {})),
                    "description": contact_data.get('Description', ''),
                    "owner_id": contact_data.get('OwnerId', ''),
                    "owner_name": contact_data.get('Owner', {}).get('Name', ''),
                    "source": "salesforce_contacts"
                }
                contacts.append(contact)
            
            return contacts
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce contacts: {str(e)}")
            raise SalesforceDataError(f"Error retrieving Salesforce contacts: {str(e)}")
    
    async def get_products(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get products from Salesforce - SI Role Function.
        
        Args:
            search_term: Optional search term to filter products
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of product records
        """
        try:
            response = await self.rest_client.get_products(
                limit=limit,
                offset=offset,
                search_term=search_term
            )
            
            if not response.get('success'):
                raise SalesforceDataError(f"Failed to retrieve products: {response.get('error')}")
            
            products = []
            for product_data in response.get('records', []):
                product = {
                    "id": product_data.get('Id', ''),
                    "name": product_data.get('Name', ''),
                    "product_code": product_data.get('ProductCode', ''),
                    "description": product_data.get('Description', ''),
                    "is_active": product_data.get('IsActive', False),
                    "family": product_data.get('Family', ''),
                    "created_date": self._format_salesforce_date(product_data.get('CreatedDate')),
                    "last_modified_date": self._format_salesforce_date(product_data.get('LastModifiedDate')),
                    "source": "salesforce_products"
                }
                products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Error retrieving Salesforce products: {str(e)}")
            raise SalesforceDataError(f"Error retrieving Salesforce products: {str(e)}")
    
    async def _format_opportunity_data(self, opportunity: Dict[str, Any], line_items: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Format opportunity data for consistent output - SI Role Function.
        
        Args:
            opportunity: Salesforce opportunity record
            line_items: Optional opportunity line items
            
        Returns:
            Formatted deal/opportunity data
        """
        try:
            deal_data = {
                "id": opportunity.get('Id', ''),
                "name": opportunity.get('Name', ''),
                "deal_name": opportunity.get('Name', ''),
                "amount": float(opportunity.get('Amount', 0)) if opportunity.get('Amount') else 0,
                "close_date": self._format_salesforce_date(opportunity.get('CloseDate')),
                "stage": opportunity.get('StageName', ''),
                "stage_name": opportunity.get('StageName', ''),
                "probability": float(opportunity.get('Probability', 0)) if opportunity.get('Probability') else 0,
                "description": opportunity.get('Description', ''),
                "type": opportunity.get('Type', ''),
                "lead_source": opportunity.get('LeadSource', ''),
                "next_step": opportunity.get('NextStep', ''),
                "forecast_category": opportunity.get('ForecastCategoryName', ''),
                "created_date": self._format_salesforce_date(opportunity.get('CreatedDate')),
                "last_modified_date": self._format_salesforce_date(opportunity.get('LastModifiedDate')),
                
                # Account/Company information
                "company": {
                    "id": opportunity.get('AccountId', ''),
                    "name": opportunity.get('Account', {}).get('Name', ''),
                    "salesforce_account_id": opportunity.get('AccountId', '')
                },
                
                # Owner information
                "owner": {
                    "id": opportunity.get('OwnerId', ''),
                    "name": opportunity.get('Owner', {}).get('Name', ''),
                    "salesforce_user_id": opportunity.get('OwnerId', '')
                },
                
                # Campaign information
                "campaign": {
                    "name": opportunity.get('Campaign', {}).get('Name', ''),
                    "salesforce_campaign_id": opportunity.get('CampaignId', '')
                },
                
                # Salesforce-specific fields
                "salesforce_opportunity_id": opportunity.get('Id', ''),
                "salesforce_stage_name": opportunity.get('StageName', ''),
                "source": "salesforce_opportunities",
                
                # Line items
                "line_items": self._format_opportunity_line_items(line_items) if line_items else []
            }
            
            return deal_data
            
        except Exception as e:
            logger.error(f"Error formatting Salesforce opportunity data: {str(e)}")
            raise SalesforceDataError(f"Error formatting Salesforce opportunity data: {str(e)}")
    
    def _format_opportunity_line_items(self, line_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format Salesforce opportunity line items."""
        formatted_lines = []
        
        for i, line in enumerate(line_items):
            formatted_line = {
                "id": line.get('Id', ''),
                "line_number": i + 1,
                "opportunity_id": line.get('OpportunityId', ''),
                "product_id": line.get('Product2Id', ''),
                "product_name": line.get('Product2', {}).get('Name', ''),
                "product_code": line.get('Product2', {}).get('ProductCode', ''),
                "description": line.get('Description', ''),
                "quantity": float(line.get('Quantity', 1)),
                "unit_price": float(line.get('UnitPrice', 0)),
                "total_price": float(line.get('TotalPrice', 0)),
                "service_date": self._format_salesforce_date(line.get('ServiceDate')),
                "source": "salesforce_opportunity_line_items"
            }
            formatted_lines.append(formatted_line)
        
        return formatted_lines
    
    def _format_salesforce_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """Format Salesforce address object."""
        if not address:
            return {}
        
        return {
            "street": address.get('street', ''),
            "city": address.get('city', ''),
            "state": address.get('state', ''),
            "postal_code": address.get('postalCode', ''),
            "country": address.get('country', ''),
            "latitude": address.get('latitude'),
            "longitude": address.get('longitude')
        }
    
    def _format_salesforce_date(self, salesforce_date) -> Optional[str]:
        """Format Salesforce date to ISO format."""
        if not salesforce_date:
            return None
        
        try:
            # Salesforce API dates are typically in ISO format already
            if isinstance(salesforce_date, str):
                # Handle different Salesforce date formats
                if 'T' in salesforce_date:
                    # ISO format with time
                    return salesforce_date
                else:
                    # Date only, add time
                    return f"{salesforce_date}T00:00:00"
            
            # If it's a datetime object, convert to ISO
            if hasattr(salesforce_date, 'isoformat'):
                return salesforce_date.isoformat()
            
            return str(salesforce_date)
            
        except Exception as e:
            logger.warning(f"Error formatting Salesforce date {salesforce_date}: {str(e)}")
            return str(salesforce_date) if salesforce_date else None
    
    def _map_salesforce_stage(self, salesforce_stage: str) -> str:
        """Map Salesforce opportunity stage to standard stage."""
        stage_mapping = {
            'Prospecting': 'prospecting',
            'Qualification': 'qualification',
            'Needs Analysis': 'needs_analysis',
            'Value Proposition': 'proposal',
            'Id. Decision Makers': 'decision_makers',
            'Perception Analysis': 'perception_analysis',
            'Proposal/Price Quote': 'proposal',
            'Negotiation/Review': 'negotiation',
            'Closed Won': 'won',
            'Closed Lost': 'lost'
        }
        
        return stage_mapping.get(salesforce_stage, 'unknown')