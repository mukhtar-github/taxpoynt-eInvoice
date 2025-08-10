"""
Zoho CRM Data Extraction Module
Handles data extraction and formatting from Zoho CRM services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from .exceptions import ZohoCRMAPIError, ZohoCRMDataError


class ZohoCRMDataExtractor:
    """
    Data extraction and formatting for Zoho CRM.
    Handles deals, accounts, contacts, and related entity data extraction.
    """

    def __init__(self, rest_client):
        """
        Initialize the Zoho CRM data extractor.
        
        Args:
            rest_client: ZohoCRMRestClient instance
        """
        self.logger = logging.getLogger(__name__)
        self.rest_client = rest_client

    async def get_deals(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        include_products: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract deal data from Zoho CRM.
        
        Args:
            filters: Filter criteria for deals
            limit: Maximum number of deals to return
            include_products: Whether to include deal products
        
        Returns:
            List of deal records with related data
        """
        try:
            # Define fields to retrieve
            deal_fields = [
                'id', 'Deal_Name', 'Amount', 'Stage', 'Probability',
                'Expected_Revenue', 'Closing_Date', 'Deal_Owner',
                'Account_Name', 'Contact_Name', 'Lead_Source',
                'Type', 'Next_Step', 'Description', 'Currency',
                'Exchange_Rate', 'Created_Time', 'Modified_Time',
                'Created_By', 'Modified_By', 'Territory', 'Campaign_Source'
            ]
            
            # Build search criteria
            criteria = self._build_deal_criteria(filters)
            
            # Configure pagination
            per_page = min(limit or 200, 200)
            page = 1
            all_deals = []
            
            while True:
                if criteria:
                    # Use search if criteria is provided
                    response = await self.rest_client.search_records(
                        module='Deals',
                        criteria=criteria,
                        fields=deal_fields,
                        page=page,
                        per_page=per_page
                    )
                else:
                    # Use get_records for general retrieval
                    response = await self.rest_client.get_records(
                        module='Deals',
                        fields=deal_fields,
                        page=page,
                        per_page=per_page,
                        sort_by='Modified_Time',
                        sort_order='desc'
                    )
                
                deals = response.get('data', [])
                if not deals:
                    break
                
                all_deals.extend(deals)
                
                # Check if we have enough records or reached the end
                if limit and len(all_deals) >= limit:
                    all_deals = all_deals[:limit]
                    break
                
                # Check if there are more pages
                info = response.get('info', {})
                if not info.get('more_records', False):
                    break
                
                page += 1
            
            # Enhance deals with product information if requested
            if include_products:
                for deal in all_deals:
                    deal_id = deal.get('id')
                    if deal_id:
                        products = await self.get_deal_products(deal_id)
                        deal['products'] = products
            
            self.logger.info(f"Extracted {len(all_deals)} deals from Zoho CRM")
            return all_deals
            
        except Exception as e:
            self.logger.error(f"Error extracting deals: {str(e)}")
            raise ZohoCRMDataError(f"Failed to extract deals: {str(e)}")

    async def get_deal_products(self, deal_id: str) -> List[Dict[str, Any]]:
        """
        Get products for a specific deal.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            List of product records
        """
        try:
            product_fields = [
                'id', 'Product_Name', 'Quantity', 'List_Price',
                'Unit_Price', 'Total', 'Discount', 'Total_After_Discount',
                'Tax', 'Net_Total', 'Book', 'Quantity_in_Stock',
                'Product_Category', 'Line_Tax'
            ]
            
            response = await self.rest_client.get_related_records(
                module='Deals',
                record_id=deal_id,
                related_list='Products',
                fields=product_fields
            )
            
            return response.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error extracting deal products: {str(e)}")
            return []

    async def get_accounts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract account data from Zoho CRM.
        
        Args:
            filters: Filter criteria for accounts
            limit: Maximum number of accounts to return
        
        Returns:
            List of account records
        """
        try:
            account_fields = [
                'id', 'Account_Name', 'Account_Number', 'Account_Site',
                'Account_Type', 'Industry', 'Annual_Revenue', 'Rating',
                'Phone', 'Fax', 'Website', 'Ticker_Symbol', 'Ownership',
                'Employees', 'SIC_Code', 'Billing_Street', 'Billing_City',
                'Billing_State', 'Billing_Code', 'Billing_Country',
                'Shipping_Street', 'Shipping_City', 'Shipping_State',
                'Shipping_Code', 'Shipping_Country', 'Description',
                'Created_Time', 'Modified_Time', 'Account_Owner'
            ]
            
            # Build search criteria
            criteria = self._build_account_criteria(filters)
            
            # Configure pagination
            per_page = min(limit or 200, 200)
            page = 1
            all_accounts = []
            
            while True:
                if criteria:
                    response = await self.rest_client.search_records(
                        module='Accounts',
                        criteria=criteria,
                        fields=account_fields,
                        page=page,
                        per_page=per_page
                    )
                else:
                    response = await self.rest_client.get_records(
                        module='Accounts',
                        fields=account_fields,
                        page=page,
                        per_page=per_page,
                        sort_by='Modified_Time',
                        sort_order='desc'
                    )
                
                accounts = response.get('data', [])
                if not accounts:
                    break
                
                all_accounts.extend(accounts)
                
                if limit and len(all_accounts) >= limit:
                    all_accounts = all_accounts[:limit]
                    break
                
                info = response.get('info', {})
                if not info.get('more_records', False):
                    break
                
                page += 1
            
            self.logger.info(f"Extracted {len(all_accounts)} accounts from Zoho CRM")
            return all_accounts
            
        except Exception as e:
            self.logger.error(f"Error extracting accounts: {str(e)}")
            raise ZohoCRMDataError(f"Failed to extract accounts: {str(e)}")

    async def get_contacts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract contact data from Zoho CRM.
        
        Args:
            filters: Filter criteria for contacts
            limit: Maximum number of contacts to return
        
        Returns:
            List of contact records
        """
        try:
            contact_fields = [
                'id', 'First_Name', 'Last_Name', 'Full_Name', 'Account_Name',
                'Email', 'Phone', 'Mobile', 'Home_Phone', 'Other_Phone',
                'Fax', 'Date_of_Birth', 'Assistant', 'Asst_Phone',
                'Title', 'Department', 'Lead_Source', 'Mailing_Street',
                'Mailing_City', 'Mailing_State', 'Mailing_Zip',
                'Mailing_Country', 'Other_Street', 'Other_City',
                'Other_State', 'Other_Zip', 'Other_Country',
                'Description', 'Created_Time', 'Modified_Time', 'Owner'
            ]
            
            # Build search criteria
            criteria = self._build_contact_criteria(filters)
            
            # Configure pagination
            per_page = min(limit or 200, 200)
            page = 1
            all_contacts = []
            
            while True:
                if criteria:
                    response = await self.rest_client.search_records(
                        module='Contacts',
                        criteria=criteria,
                        fields=contact_fields,
                        page=page,
                        per_page=per_page
                    )
                else:
                    response = await self.rest_client.get_records(
                        module='Contacts',
                        fields=contact_fields,
                        page=page,
                        per_page=per_page,
                        sort_by='Modified_Time',
                        sort_order='desc'
                    )
                
                contacts = response.get('data', [])
                if not contacts:
                    break
                
                all_contacts.extend(contacts)
                
                if limit and len(all_contacts) >= limit:
                    all_contacts = all_contacts[:limit]
                    break
                
                info = response.get('info', {})
                if not info.get('more_records', False):
                    break
                
                page += 1
            
            self.logger.info(f"Extracted {len(all_contacts)} contacts from Zoho CRM")
            return all_contacts
            
        except Exception as e:
            self.logger.error(f"Error extracting contacts: {str(e)}")
            raise ZohoCRMDataError(f"Failed to extract contacts: {str(e)}")

    async def get_deal_by_id(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific deal by ID.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            Deal record or None if not found
        """
        try:
            deal_fields = [
                'id', 'Deal_Name', 'Amount', 'Stage', 'Probability',
                'Expected_Revenue', 'Closing_Date', 'Deal_Owner',
                'Account_Name', 'Contact_Name', 'Lead_Source',
                'Type', 'Next_Step', 'Description', 'Currency',
                'Exchange_Rate', 'Created_Time', 'Modified_Time'
            ]
            
            response = await self.rest_client.get_record(
                module='Deals',
                record_id=deal_id,
                fields=deal_fields
            )
            
            deals = response.get('data', [])
            if deals:
                deal = deals[0]
                
                # Add products
                products = await self.get_deal_products(deal_id)
                deal['products'] = products
                
                return deal
            else:
                return None
                
        except ZohoCRMAPIError as e:
            if "INVALID_DATA" in str(e) or "404" in str(e):
                return None
            raise
        except Exception as e:
            self.logger.error(f"Error getting deal {deal_id}: {str(e)}")
            raise ZohoCRMDataError(f"Failed to get deal: {str(e)}")

    async def search_deals(
        self,
        search_term: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search deals by name or description.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
        
        Returns:
            List of matching deal records
        """
        try:
            # Build search criteria
            criteria = f"(Deal_Name:contains:{search_term}) or (Description:contains:{search_term})"
            
            return await self.get_deals(
                filters={'criteria': criteria},
                limit=limit
            )
            
        except Exception as e:
            self.logger.error(f"Error searching deals: {str(e)}")
            raise ZohoCRMDataError(f"Failed to search deals: {str(e)}")

    def _build_deal_criteria(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build search criteria for deals."""
        if not filters:
            return None
        
        criteria_parts = []
        
        # Custom criteria
        if 'criteria' in filters:
            criteria_parts.append(filters['criteria'])
        
        # Stage filter
        if 'stage' in filters:
            criteria_parts.append(f"Stage:equals:{filters['stage']}")
        
        # Amount range filter
        if 'min_amount' in filters:
            criteria_parts.append(f"Amount:greater_than:{filters['min_amount']}")
        
        if 'max_amount' in filters:
            criteria_parts.append(f"Amount:less_than:{filters['max_amount']}")
        
        # Date range filter
        if 'created_after' in filters:
            criteria_parts.append(f"Created_Time:greater_than:{filters['created_after']}")
        
        if 'created_before' in filters:
            criteria_parts.append(f"Created_Time:less_than:{filters['created_before']}")
        
        # Owner filter
        if 'owner_id' in filters:
            criteria_parts.append(f"Deal_Owner:equals:{filters['owner_id']}")
        
        # Account filter
        if 'account_id' in filters:
            criteria_parts.append(f"Account_Name:equals:{filters['account_id']}")
        
        return ' and '.join(criteria_parts) if criteria_parts else None

    def _build_account_criteria(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build search criteria for accounts."""
        if not filters:
            return None
        
        criteria_parts = []
        
        # Custom criteria
        if 'criteria' in filters:
            criteria_parts.append(filters['criteria'])
        
        # Name filter
        if 'name' in filters:
            criteria_parts.append(f"Account_Name:contains:{filters['name']}")
        
        # Industry filter
        if 'industry' in filters:
            criteria_parts.append(f"Industry:equals:{filters['industry']}")
        
        # Date range filter
        if 'created_after' in filters:
            criteria_parts.append(f"Created_Time:greater_than:{filters['created_after']}")
        
        if 'created_before' in filters:
            criteria_parts.append(f"Created_Time:less_than:{filters['created_before']}")
        
        return ' and '.join(criteria_parts) if criteria_parts else None

    def _build_contact_criteria(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build search criteria for contacts."""
        if not filters:
            return None
        
        criteria_parts = []
        
        # Custom criteria
        if 'criteria' in filters:
            criteria_parts.append(filters['criteria'])
        
        # Name filter
        if 'name' in filters:
            criteria_parts.append(f"Full_Name:contains:{filters['name']}")
        
        # Email filter
        if 'email' in filters:
            criteria_parts.append(f"Email:contains:{filters['email']}")
        
        # Account filter
        if 'account_id' in filters:
            criteria_parts.append(f"Account_Name:equals:{filters['account_id']}")
        
        # Date range filter
        if 'created_after' in filters:
            criteria_parts.append(f"Created_Time:greater_than:{filters['created_after']}")
        
        if 'created_before' in filters:
            criteria_parts.append(f"Created_Time:less_than:{filters['created_before']}")
        
        return ' and '.join(criteria_parts) if criteria_parts else None

    def format_deal_data(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format deal data for standardized output.
        
        Args:
            deal: Raw deal data from Zoho CRM
        
        Returns:
            Formatted deal data
        """
        try:
            # Extract account information
            account_info = {}
            if deal.get('Account_Name'):
                if isinstance(deal['Account_Name'], dict):
                    account_info = {
                        'id': deal['Account_Name'].get('id'),
                        'name': deal['Account_Name'].get('name')
                    }
                else:
                    account_info = {
                        'name': str(deal['Account_Name'])
                    }
            
            # Extract contact information
            contact_info = {}
            if deal.get('Contact_Name'):
                if isinstance(deal['Contact_Name'], dict):
                    contact_info = {
                        'id': deal['Contact_Name'].get('id'),
                        'name': deal['Contact_Name'].get('name')
                    }
                else:
                    contact_info = {
                        'name': str(deal['Contact_Name'])
                    }
            
            # Format products
            products = []
            for product in deal.get('products', []):
                formatted_product = {
                    'id': product.get('id'),
                    'name': product.get('Product_Name', {}).get('name') if isinstance(product.get('Product_Name'), dict) else product.get('Product_Name'),
                    'quantity': product.get('Quantity', 0),
                    'list_price': product.get('List_Price', 0),
                    'unit_price': product.get('Unit_Price', 0),
                    'total': product.get('Total', 0),
                    'discount': product.get('Discount', 0),
                    'total_after_discount': product.get('Total_After_Discount', 0),
                    'tax': product.get('Tax', 0),
                    'net_total': product.get('Net_Total', 0)
                }
                products.append(formatted_product)
            
            # Format owner information
            owner_info = {}
            if deal.get('Deal_Owner'):
                if isinstance(deal['Deal_Owner'], dict):
                    owner_info = {
                        'id': deal['Deal_Owner'].get('id'),
                        'name': deal['Deal_Owner'].get('name'),
                        'email': deal['Deal_Owner'].get('email')
                    }
                else:
                    owner_info = {
                        'name': str(deal['Deal_Owner'])
                    }
            
            return {
                'id': deal.get('id'),
                'name': deal.get('Deal_Name'),
                'description': deal.get('Description'),
                'stage': deal.get('Stage'),
                'probability': deal.get('Probability', 0),
                'amount': deal.get('Amount', 0),
                'expected_revenue': deal.get('Expected_Revenue', 0),
                'closing_date': deal.get('Closing_Date'),
                'next_step': deal.get('Next_Step'),
                'lead_source': deal.get('Lead_Source'),
                'type': deal.get('Type'),
                'created_date': deal.get('Created_Time'),
                'modified_date': deal.get('Modified_Time'),
                'currency': deal.get('Currency'),
                'exchange_rate': deal.get('Exchange_Rate', 1),
                'account': account_info,
                'contact': contact_info,
                'owner': owner_info,
                'products': products
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting deal data: {str(e)}")
            raise ZohoCRMDataError(f"Failed to format deal data: {str(e)}")