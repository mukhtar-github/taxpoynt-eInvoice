"""
Microsoft Dynamics CRM Data Extraction Module
Handles data extraction and formatting from Microsoft Dynamics CRM services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from .exceptions import DynamicsCRMAPIError, DynamicsCRMDataError


class DynamicsCRMDataExtractor:
    """
    Data extraction and formatting for Microsoft Dynamics CRM.
    Handles opportunities, accounts, contacts, and related entity data extraction.
    """

    def __init__(self, rest_client):
        """
        Initialize the Dynamics CRM data extractor.
        
        Args:
            rest_client: DynamicsCRMRestClient instance
        """
        self.logger = logging.getLogger(__name__)
        self.rest_client = rest_client

    async def get_opportunities(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        include_line_items: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract opportunity data from Dynamics CRM.
        
        Args:
            filters: Filter criteria for opportunities
            limit: Maximum number of opportunities to return
            include_line_items: Whether to include opportunity line items
        
        Returns:
            List of opportunity records with related data
        """
        try:
            # Build OData query
            select_fields = [
                'opportunityid', 'name', 'description', 'totalamount',
                'estimatedvalue', 'actualvalue', 'estimatedclosedate',
                'actualclosedate', 'closeprobability', 'salesstage',
                'stepname', 'statecode', 'statuscode', 'budgetamount',
                'currencyid', 'exchangerate', 'freightamount',
                'discountamount', 'totallineitemamount', 'totalamountlessfreight',
                'totaldiscountamount', 'totaltax', 'createdon', 'modifiedon'
            ]
            
            expand_fields = [
                'customerid_account($select=accountid,name,accountnumber,emailaddress1,telephone1,address1_composite)',
                'customerid_contact($select=contactid,fullname,emailaddress1,telephone1,address1_composite)',
                'ownerid($select=systemuserid,fullname,internalemailaddress)',
                'transactioncurrencyid($select=transactioncurrencyid,currencyname,currencysymbol,exchangerate)'
            ]
            
            # Build filter clause
            filter_clause = self._build_opportunity_filter(filters)
            
            # Execute query
            response = await self.rest_client.odata_query(
                entity_set='opportunities',
                select=select_fields,
                expand=expand_fields,
                filter_clause=filter_clause,
                orderby='modifiedon desc',
                top=limit
            )
            
            opportunities = response.get('value', [])
            
            # Enhance opportunities with line items if requested
            if include_line_items:
                for opportunity in opportunities:
                    opportunity_id = opportunity.get('opportunityid')
                    if opportunity_id:
                        line_items = await self.get_opportunity_line_items(opportunity_id)
                        opportunity['line_items'] = line_items
            
            self.logger.info(f"Extracted {len(opportunities)} opportunities from Dynamics CRM")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error extracting opportunities: {str(e)}")
            raise DynamicsCRMDataError(f"Failed to extract opportunities: {str(e)}")

    async def get_opportunity_line_items(self, opportunity_id: str) -> List[Dict[str, Any]]:
        """
        Get line items for a specific opportunity.
        
        Args:
            opportunity_id: Opportunity ID
        
        Returns:
            List of opportunity product records
        """
        try:
            select_fields = [
                'opportunityproductid', 'productdescription', 'quantity',
                'priceperunit', 'baseamount', 'extendedamount', 'manualdiscountamount',
                'tax', 'volumediscountamount', 'lineitemnumber', 'ispriceoverridden',
                'isproductoverridden', 'createdon', 'modifiedon'
            ]
            
            expand_fields = [
                'productid($select=productid,name,productstructure,price,quantitydecimal)',
                'uomid($select=uomid,name,quantity)'
            ]
            
            filter_clause = f"_opportunityid_value eq {opportunity_id}"
            
            response = await self.rest_client.odata_query(
                entity_set='opportunityproducts',
                select=select_fields,
                expand=expand_fields,
                filter_clause=filter_clause,
                orderby='lineitemnumber asc'
            )
            
            return response.get('value', [])
            
        except Exception as e:
            self.logger.error(f"Error extracting opportunity line items: {str(e)}")
            return []

    async def get_accounts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract account data from Dynamics CRM.
        
        Args:
            filters: Filter criteria for accounts
            limit: Maximum number of accounts to return
        
        Returns:
            List of account records
        """
        try:
            select_fields = [
                'accountid', 'name', 'accountnumber', 'description',
                'emailaddress1', 'telephone1', 'fax', 'websiteurl',
                'revenue', 'numberofemployees', 'sic', 'tickersymbol',
                'address1_composite', 'address1_line1', 'address1_line2',
                'address1_city', 'address1_stateorprovince', 'address1_postalcode',
                'address1_country', 'createdon', 'modifiedon'
            ]
            
            expand_fields = [
                'ownerid($select=systemuserid,fullname,internalemailaddress)',
                'transactioncurrencyid($select=transactioncurrencyid,currencyname,currencysymbol)'
            ]
            
            filter_clause = self._build_account_filter(filters)
            
            response = await self.rest_client.odata_query(
                entity_set='accounts',
                select=select_fields,
                expand=expand_fields,
                filter_clause=filter_clause,
                orderby='modifiedon desc',
                top=limit
            )
            
            accounts = response.get('value', [])
            self.logger.info(f"Extracted {len(accounts)} accounts from Dynamics CRM")
            return accounts
            
        except Exception as e:
            self.logger.error(f"Error extracting accounts: {str(e)}")
            raise DynamicsCRMDataError(f"Failed to extract accounts: {str(e)}")

    async def get_contacts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract contact data from Dynamics CRM.
        
        Args:
            filters: Filter criteria for contacts
            limit: Maximum number of contacts to return
        
        Returns:
            List of contact records
        """
        try:
            select_fields = [
                'contactid', 'fullname', 'firstname', 'lastname',
                'emailaddress1', 'telephone1', 'mobilephone', 'jobtitle',
                'description', 'address1_composite', 'address1_line1',
                'address1_line2', 'address1_city', 'address1_stateorprovince',
                'address1_postalcode', 'address1_country', 'createdon', 'modifiedon'
            ]
            
            expand_fields = [
                'parentcustomerid_account($select=accountid,name,accountnumber)',
                'ownerid($select=systemuserid,fullname,internalemailaddress)'
            ]
            
            filter_clause = self._build_contact_filter(filters)
            
            response = await self.rest_client.odata_query(
                entity_set='contacts',
                select=select_fields,
                expand=expand_fields,
                filter_clause=filter_clause,
                orderby='modifiedon desc',
                top=limit
            )
            
            contacts = response.get('value', [])
            self.logger.info(f"Extracted {len(contacts)} contacts from Dynamics CRM")
            return contacts
            
        except Exception as e:
            self.logger.error(f"Error extracting contacts: {str(e)}")
            raise DynamicsCRMDataError(f"Failed to extract contacts: {str(e)}")

    async def get_opportunity_by_id(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific opportunity by ID.
        
        Args:
            opportunity_id: Opportunity ID
        
        Returns:
            Opportunity record or None if not found
        """
        try:
            select_fields = [
                'opportunityid', 'name', 'description', 'totalamount',
                'estimatedvalue', 'actualvalue', 'estimatedclosedate',
                'actualclosedate', 'closeprobability', 'salesstage',
                'stepname', 'statecode', 'statuscode', 'createdon', 'modifiedon'
            ]
            
            expand_fields = [
                'customerid_account($select=accountid,name,accountnumber,emailaddress1)',
                'customerid_contact($select=contactid,fullname,emailaddress1)',
                'ownerid($select=systemuserid,fullname,internalemailaddress)',
                'transactioncurrencyid($select=transactioncurrencyid,currencyname,currencysymbol)'
            ]
            
            opportunity = await self.rest_client.get_entity(
                entity_set='opportunities',
                entity_id=opportunity_id,
                select=select_fields,
                expand=expand_fields
            )
            
            # Add line items
            line_items = await self.get_opportunity_line_items(opportunity_id)
            opportunity['line_items'] = line_items
            
            return opportunity
            
        except DynamicsCRMAPIError as e:
            if "404" in str(e):
                return None
            raise
        except Exception as e:
            self.logger.error(f"Error getting opportunity {opportunity_id}: {str(e)}")
            raise DynamicsCRMDataError(f"Failed to get opportunity: {str(e)}")

    async def search_opportunities(
        self,
        search_term: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search opportunities by name or description.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
        
        Returns:
            List of matching opportunity records
        """
        try:
            # Use contains function for case-insensitive search
            filter_clause = f"contains(name,'{search_term}') or contains(description,'{search_term}')"
            
            return await self.get_opportunities(
                filters={'custom_filter': filter_clause},
                limit=limit
            )
            
        except Exception as e:
            self.logger.error(f"Error searching opportunities: {str(e)}")
            raise DynamicsCRMDataError(f"Failed to search opportunities: {str(e)}")

    def _build_opportunity_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build OData filter clause for opportunities."""
        if not filters:
            return None
        
        filter_parts = []
        
        # Custom filter clause
        if 'custom_filter' in filters:
            filter_parts.append(filters['custom_filter'])
        
        # State filter
        if 'state' in filters:
            state_value = 0 if filters['state'] == 'open' else 1
            filter_parts.append(f"statecode eq {state_value}")
        
        # Date range filter
        if 'created_after' in filters:
            date_str = filters['created_after']
            filter_parts.append(f"createdon ge {date_str}")
        
        if 'created_before' in filters:
            date_str = filters['created_before']
            filter_parts.append(f"createdon le {date_str}")
        
        # Owner filter
        if 'owner_id' in filters:
            filter_parts.append(f"_ownerid_value eq {filters['owner_id']}")
        
        # Customer filter
        if 'customer_id' in filters:
            filter_parts.append(f"_customerid_value eq {filters['customer_id']}")
        
        # Amount range filter
        if 'min_amount' in filters:
            filter_parts.append(f"totalamount ge {filters['min_amount']}")
        
        if 'max_amount' in filters:
            filter_parts.append(f"totalamount le {filters['max_amount']}")
        
        return ' and '.join(filter_parts) if filter_parts else None

    def _build_account_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build OData filter clause for accounts."""
        if not filters:
            return None
        
        filter_parts = []
        
        # Custom filter clause
        if 'custom_filter' in filters:
            filter_parts.append(filters['custom_filter'])
        
        # Name filter
        if 'name' in filters:
            filter_parts.append(f"contains(name,'{filters['name']}')")
        
        # Date range filter
        if 'created_after' in filters:
            date_str = filters['created_after']
            filter_parts.append(f"createdon ge {date_str}")
        
        if 'created_before' in filters:
            date_str = filters['created_before']
            filter_parts.append(f"createdon le {date_str}")
        
        # Owner filter
        if 'owner_id' in filters:
            filter_parts.append(f"_ownerid_value eq {filters['owner_id']}")
        
        return ' and '.join(filter_parts) if filter_parts else None

    def _build_contact_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build OData filter clause for contacts."""
        if not filters:
            return None
        
        filter_parts = []
        
        # Custom filter clause
        if 'custom_filter' in filters:
            filter_parts.append(filters['custom_filter'])
        
        # Name filter
        if 'name' in filters:
            filter_parts.append(f"contains(fullname,'{filters['name']}')")
        
        # Email filter
        if 'email' in filters:
            filter_parts.append(f"contains(emailaddress1,'{filters['email']}')")
        
        # Account filter
        if 'account_id' in filters:
            filter_parts.append(f"_parentcustomerid_value eq {filters['account_id']}")
        
        # Date range filter
        if 'created_after' in filters:
            date_str = filters['created_after']
            filter_parts.append(f"createdon ge {date_str}")
        
        if 'created_before' in filters:
            date_str = filters['created_before']
            filter_parts.append(f"createdon le {date_str}")
        
        return ' and '.join(filter_parts) if filter_parts else None

    def format_opportunity_data(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format opportunity data for standardized output.
        
        Args:
            opportunity: Raw opportunity data from Dynamics CRM
        
        Returns:
            Formatted opportunity data
        """
        try:
            # Extract customer information
            customer_info = {}
            if 'customerid_account' in opportunity:
                account = opportunity['customerid_account']
                customer_info = {
                    'type': 'account',
                    'id': account.get('accountid'),
                    'name': account.get('name'),
                    'email': account.get('emailaddress1'),
                    'phone': account.get('telephone1'),
                    'address': account.get('address1_composite')
                }
            elif 'customerid_contact' in opportunity:
                contact = opportunity['customerid_contact']
                customer_info = {
                    'type': 'contact',
                    'id': contact.get('contactid'),
                    'name': contact.get('fullname'),
                    'email': contact.get('emailaddress1'),
                    'phone': contact.get('telephone1'),
                    'address': contact.get('address1_composite')
                }
            
            # Format line items
            line_items = []
            for item in opportunity.get('line_items', []):
                formatted_item = {
                    'id': item.get('opportunityproductid'),
                    'description': item.get('productdescription'),
                    'quantity': item.get('quantity', 0),
                    'unit_price': item.get('priceperunit', 0),
                    'total_amount': item.get('extendedamount', 0),
                    'discount': item.get('manualdiscountamount', 0),
                    'tax': item.get('tax', 0),
                    'line_number': item.get('lineitemnumber')
                }
                
                if 'productid' in item:
                    product = item['productid']
                    formatted_item['product'] = {
                        'id': product.get('productid'),
                        'name': product.get('name'),
                        'list_price': product.get('price')
                    }
                
                line_items.append(formatted_item)
            
            # Format currency information
            currency_info = {}
            if 'transactioncurrencyid' in opportunity:
                currency = opportunity['transactioncurrencyid']
                currency_info = {
                    'id': currency.get('transactioncurrencyid'),
                    'name': currency.get('currencyname'),
                    'symbol': currency.get('currencysymbol'),
                    'exchange_rate': opportunity.get('exchangerate', 1)
                }
            
            return {
                'id': opportunity.get('opportunityid'),
                'name': opportunity.get('name'),
                'description': opportunity.get('description'),
                'stage': opportunity.get('salesstage'),
                'step': opportunity.get('stepname'),
                'state': 'open' if opportunity.get('statecode') == 0 else 'closed',
                'status': opportunity.get('statuscode'),
                'probability': opportunity.get('closeprobability', 0),
                'estimated_value': opportunity.get('estimatedvalue', 0),
                'actual_value': opportunity.get('actualvalue', 0),
                'total_amount': opportunity.get('totalamount', 0),
                'estimated_close_date': opportunity.get('estimatedclosedate'),
                'actual_close_date': opportunity.get('actualclosedate'),
                'created_date': opportunity.get('createdon'),
                'modified_date': opportunity.get('modifiedon'),
                'customer': customer_info,
                'line_items': line_items,
                'currency': currency_info,
                'owner': {
                    'id': opportunity.get('ownerid', {}).get('systemuserid'),
                    'name': opportunity.get('ownerid', {}).get('fullname'),
                    'email': opportunity.get('ownerid', {}).get('internalemailaddress')
                } if 'ownerid' in opportunity else {}
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting opportunity data: {str(e)}")
            raise DynamicsCRMDataError(f"Failed to format opportunity data: {str(e)}")