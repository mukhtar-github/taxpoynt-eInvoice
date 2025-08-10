"""
Pipedrive Data Extraction Module
Handles data extraction and formatting from Pipedrive CRM services.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from .exceptions import PipedriveAPIError, PipedriveDataError


class PipedriveDataExtractor:
    """
    Data extraction and formatting for Pipedrive CRM.
    Handles deals, persons, organizations, and related entity data extraction.
    """

    def __init__(self, rest_client):
        """
        Initialize the Pipedrive data extractor.
        
        Args:
            rest_client: PipedriveRestClient instance
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
        Extract deal data from Pipedrive.
        
        Args:
            filters: Filter criteria for deals
            limit: Maximum number of deals to return
            include_products: Whether to include deal products
        
        Returns:
            List of deal records with related data
        """
        try:
            # Build filter parameters
            params = {}
            
            if filters:
                if 'user_id' in filters:
                    params['user_id'] = filters['user_id']
                
                if 'stage_id' in filters:
                    params['stage_id'] = filters['stage_id']
                
                if 'status' in filters:
                    params['status'] = filters['status']
                
                if 'owned_by_you' in filters:
                    params['owned_by_you'] = filters['owned_by_you']
                
                if 'filter_id' in filters:
                    params['filter_id'] = filters['filter_id']
            
            # Configure pagination
            per_page = min(limit or 500, 500)
            start = 0
            all_deals = []
            
            while True:
                params['start'] = start
                params['limit'] = per_page
                
                response = await self.rest_client.get_deals(**params)
                
                if not response.get('success'):
                    break
                
                deals = response.get('data', [])
                if not deals:
                    break
                
                all_deals.extend(deals)
                
                # Check if we have enough records or reached the end
                if limit and len(all_deals) >= limit:
                    all_deals = all_deals[:limit]
                    break
                
                # Check pagination info
                additional_data = response.get('additional_data', {})
                pagination = additional_data.get('pagination', {})
                
                if not pagination.get('more_items_in_collection', False):
                    break
                
                start = pagination.get('next_start', start + per_page)
            
            # Enhance deals with product information if requested
            if include_products:
                for deal in all_deals:
                    deal_id = deal.get('id')
                    if deal_id:
                        products = await self.get_deal_products(deal_id)
                        deal['products'] = products
            
            self.logger.info(f"Extracted {len(all_deals)} deals from Pipedrive")
            return all_deals
            
        except Exception as e:
            self.logger.error(f"Error extracting deals: {str(e)}")
            raise PipedriveDataError(f"Failed to extract deals: {str(e)}")

    async def get_deal_products(self, deal_id: int) -> List[Dict[str, Any]]:
        """
        Get products for a specific deal.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            List of product records
        """
        try:
            response = await self.rest_client.get_deal_products(deal_id)
            
            if response.get('success'):
                return response.get('data', [])
            else:
                return []
            
        except Exception as e:
            self.logger.error(f"Error extracting deal products: {str(e)}")
            return []

    async def get_persons(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract person data from Pipedrive.
        
        Args:
            filters: Filter criteria for persons
            limit: Maximum number of persons to return
        
        Returns:
            List of person records
        """
        try:
            # Build filter parameters
            params = {}
            
            if filters:
                if 'user_id' in filters:
                    params['user_id'] = filters['user_id']
                
                if 'filter_id' in filters:
                    params['filter_id'] = filters['filter_id']
                
                if 'first_char' in filters:
                    params['first_char'] = filters['first_char']
            
            # Configure pagination
            per_page = min(limit or 500, 500)
            start = 0
            all_persons = []
            
            while True:
                params['start'] = start
                params['limit'] = per_page
                
                response = await self.rest_client.get_persons(**params)
                
                if not response.get('success'):
                    break
                
                persons = response.get('data', [])
                if not persons:
                    break
                
                all_persons.extend(persons)
                
                # Check if we have enough records or reached the end
                if limit and len(all_persons) >= limit:
                    all_persons = all_persons[:limit]
                    break
                
                # Check pagination info
                additional_data = response.get('additional_data', {})
                pagination = additional_data.get('pagination', {})
                
                if not pagination.get('more_items_in_collection', False):
                    break
                
                start = pagination.get('next_start', start + per_page)
            
            self.logger.info(f"Extracted {len(all_persons)} persons from Pipedrive")
            return all_persons
            
        except Exception as e:
            self.logger.error(f"Error extracting persons: {str(e)}")
            raise PipedriveDataError(f"Failed to extract persons: {str(e)}")

    async def get_organizations(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract organization data from Pipedrive.
        
        Args:
            filters: Filter criteria for organizations
            limit: Maximum number of organizations to return
        
        Returns:
            List of organization records
        """
        try:
            # Build filter parameters
            params = {}
            
            if filters:
                if 'user_id' in filters:
                    params['user_id'] = filters['user_id']
                
                if 'filter_id' in filters:
                    params['filter_id'] = filters['filter_id']
                
                if 'first_char' in filters:
                    params['first_char'] = filters['first_char']
            
            # Configure pagination
            per_page = min(limit or 500, 500)
            start = 0
            all_organizations = []
            
            while True:
                params['start'] = start
                params['limit'] = per_page
                
                response = await self.rest_client.get_organizations(**params)
                
                if not response.get('success'):
                    break
                
                organizations = response.get('data', [])
                if not organizations:
                    break
                
                all_organizations.extend(organizations)
                
                # Check if we have enough records or reached the end
                if limit and len(all_organizations) >= limit:
                    all_organizations = all_organizations[:limit]
                    break
                
                # Check pagination info
                additional_data = response.get('additional_data', {})
                pagination = additional_data.get('pagination', {})
                
                if not pagination.get('more_items_in_collection', False):
                    break
                
                start = pagination.get('next_start', start + per_page)
            
            self.logger.info(f"Extracted {len(all_organizations)} organizations from Pipedrive")
            return all_organizations
            
        except Exception as e:
            self.logger.error(f"Error extracting organizations: {str(e)}")
            raise PipedriveDataError(f"Failed to extract organizations: {str(e)}")

    async def get_deal_by_id(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific deal by ID.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            Deal record or None if not found
        """
        try:
            response = await self.rest_client.get_deal(deal_id)
            
            if response.get('success'):
                deal = response.get('data')
                if deal:
                    # Add products
                    products = await self.get_deal_products(deal_id)
                    deal['products'] = products
                    return deal
            
            return None
                
        except PipedriveAPIError as e:
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            raise
        except Exception as e:
            self.logger.error(f"Error getting deal {deal_id}: {str(e)}")
            raise PipedriveDataError(f"Failed to get deal: {str(e)}")

    async def search_deals(
        self,
        search_term: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search deals by term.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
        
        Returns:
            List of matching deal records
        """
        try:
            params = {
                'term': search_term,
                'fields': 'title,notes'
            }
            
            if limit:
                params['limit'] = min(limit, 500)
            
            response = await self.rest_client.search_deals(**params)
            
            if response.get('success'):
                search_results = response.get('data', {})
                items = search_results.get('items', [])
                
                # Extract deal data from search results
                deals = []
                for item in items:
                    if item.get('item', {}).get('id'):
                        deal_data = item.get('item', {})
                        deals.append(deal_data)
                
                # Enhance with products if requested
                for deal in deals:
                    deal_id = deal.get('id')
                    if deal_id:
                        products = await self.get_deal_products(deal_id)
                        deal['products'] = products
                
                self.logger.info(f"Found {len(deals)} deals matching '{search_term}'")
                return deals
            else:
                return []
            
        except Exception as e:
            self.logger.error(f"Error searching deals: {str(e)}")
            raise PipedriveDataError(f"Failed to search deals: {str(e)}")

    def format_deal_data(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format deal data for standardized output.
        
        Args:
            deal: Raw deal data from Pipedrive
        
        Returns:
            Formatted deal data
        """
        try:
            # Extract person information
            person_info = {}
            if deal.get('person_id'):
                person_data = deal.get('person_id')
                if isinstance(person_data, dict):
                    person_info = {
                        'id': person_data.get('value'),
                        'name': person_data.get('name'),
                        'email': person_data.get('email', [{}])[0].get('value', '') if person_data.get('email') else '',
                        'phone': person_data.get('phone', [{}])[0].get('value', '') if person_data.get('phone') else ''
                    }
                else:
                    person_info = {
                        'id': person_data,
                        'name': deal.get('person_name', '')
                    }
            
            # Extract organization information
            organization_info = {}
            if deal.get('org_id'):
                org_data = deal.get('org_id')
                if isinstance(org_data, dict):
                    organization_info = {
                        'id': org_data.get('value'),
                        'name': org_data.get('name'),
                        'address': org_data.get('address', '')
                    }
                else:
                    organization_info = {
                        'id': org_data,
                        'name': deal.get('org_name', '')
                    }
            
            # Extract owner information
            owner_info = {}
            if deal.get('user_id'):
                user_data = deal.get('user_id')
                if isinstance(user_data, dict):
                    owner_info = {
                        'id': user_data.get('value'),
                        'name': user_data.get('name'),
                        'email': user_data.get('email')
                    }
                else:
                    owner_info = {
                        'id': user_data,
                        'name': deal.get('owner_name', '')
                    }
            
            # Extract stage information
            stage_info = {}
            if deal.get('stage_id'):
                stage_data = deal.get('stage_id')
                if isinstance(stage_data, dict):
                    stage_info = {
                        'id': stage_data.get('value'),
                        'name': stage_data.get('name'),
                        'order_nr': stage_data.get('order_nr')
                    }
                else:
                    stage_info = {
                        'id': stage_data
                    }
            
            # Format products
            products = []
            for product in deal.get('products', []):
                formatted_product = {
                    'id': product.get('id'),
                    'product_id': product.get('product_id'),
                    'name': product.get('name'),
                    'quantity': product.get('quantity', 0),
                    'item_price': product.get('item_price', 0),
                    'sum': product.get('sum', 0),
                    'discount_percentage': product.get('discount_percentage', 0),
                    'discount': product.get('discount', 0),
                    'sum_no_discount': product.get('sum_no_discount', 0),
                    'tax': product.get('tax', 0),
                    'enabled_flag': product.get('enabled_flag', True)
                }
                products.append(formatted_product)
            
            # Format currency information
            currency = deal.get('currency', 'USD')
            
            return {
                'id': deal.get('id'),
                'title': deal.get('title'),
                'value': deal.get('value', 0),
                'currency': currency,
                'status': deal.get('status'),
                'stage': stage_info,
                'probability': deal.get('probability'),
                'expected_close_date': deal.get('expected_close_date'),
                'close_time': deal.get('close_time'),
                'won_time': deal.get('won_time'),
                'lost_time': deal.get('lost_time'),
                'lost_reason': deal.get('lost_reason'),
                'add_time': deal.get('add_time'),
                'update_time': deal.get('update_time'),
                'pipeline_id': deal.get('pipeline_id'),
                'notes_count': deal.get('notes_count', 0),
                'activities_count': deal.get('activities_count', 0),
                'done_activities_count': deal.get('done_activities_count', 0),
                'undone_activities_count': deal.get('undone_activities_count', 0),
                'files_count': deal.get('files_count', 0),
                'next_activity_date': deal.get('next_activity_date'),
                'next_activity_time': deal.get('next_activity_time'),
                'next_activity_id': deal.get('next_activity_id'),
                'last_activity_id': deal.get('last_activity_id'),
                'last_activity_date': deal.get('last_activity_date'),
                'person': person_info,
                'organization': organization_info,
                'owner': owner_info,
                'products': products,
                'formatted_value': deal.get('formatted_value', ''),
                'formatted_weighted_value': deal.get('formatted_weighted_value', ''),
                'weighted_value': deal.get('weighted_value', 0),
                'rotten_time': deal.get('rotten_time'),
                'visible_to': deal.get('visible_to', '1'),  # 1 = Owner & followers, 3 = Entire company
                'cc_email': deal.get('cc_email')
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting deal data: {str(e)}")
            raise PipedriveDataError(f"Failed to format deal data: {str(e)}")

    def format_person_data(self, person: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format person data for standardized output.
        
        Args:
            person: Raw person data from Pipedrive
        
        Returns:
            Formatted person data
        """
        try:
            # Extract email information
            emails = []
            if person.get('email'):
                if isinstance(person['email'], list):
                    emails = [{'value': email.get('value', ''), 'primary': email.get('primary', False)} 
                             for email in person['email']]
                else:
                    emails = [{'value': person['email'], 'primary': True}]
            
            # Extract phone information
            phones = []
            if person.get('phone'):
                if isinstance(person['phone'], list):
                    phones = [{'value': phone.get('value', ''), 'primary': phone.get('primary', False)} 
                             for phone in person['phone']]
                else:
                    phones = [{'value': person['phone'], 'primary': True}]
            
            # Extract organization information
            organization_info = {}
            if person.get('org_id'):
                org_data = person.get('org_id')
                if isinstance(org_data, dict):
                    organization_info = {
                        'id': org_data.get('value'),
                        'name': org_data.get('name')
                    }
                else:
                    organization_info = {
                        'id': org_data,
                        'name': person.get('org_name', '')
                    }
            
            return {
                'id': person.get('id'),
                'name': person.get('name'),
                'first_name': person.get('first_name'),
                'last_name': person.get('last_name'),
                'emails': emails,
                'phones': phones,
                'organization': organization_info,
                'owner_id': person.get('owner_id', {}).get('value') if isinstance(person.get('owner_id'), dict) else person.get('owner_id'),
                'owner_name': person.get('owner_id', {}).get('name') if isinstance(person.get('owner_id'), dict) else '',
                'add_time': person.get('add_time'),
                'update_time': person.get('update_time'),
                'visible_to': person.get('visible_to', '1'),
                'picture_id': person.get('picture_id', {}).get('value') if isinstance(person.get('picture_id'), dict) else person.get('picture_id'),
                'label': person.get('label'),
                'next_activity_date': person.get('next_activity_date'),
                'next_activity_time': person.get('next_activity_time'),
                'next_activity_id': person.get('next_activity_id'),
                'last_activity_id': person.get('last_activity_id'),
                'last_activity_date': person.get('last_activity_date'),
                'open_deals_count': person.get('open_deals_count', 0),
                'related_open_deals_count': person.get('related_open_deals_count', 0),
                'closed_deals_count': person.get('closed_deals_count', 0),
                'related_closed_deals_count': person.get('related_closed_deals_count', 0),
                'won_deals_count': person.get('won_deals_count', 0),
                'related_won_deals_count': person.get('related_won_deals_count', 0),
                'lost_deals_count': person.get('lost_deals_count', 0),
                'related_lost_deals_count': person.get('related_lost_deals_count', 0),
                'activities_count': person.get('activities_count', 0),
                'done_activities_count': person.get('done_activities_count', 0),
                'undone_activities_count': person.get('undone_activities_count', 0),
                'files_count': person.get('files_count', 0),
                'notes_count': person.get('notes_count', 0),
                'email_messages_count': person.get('email_messages_count', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting person data: {str(e)}")
            raise PipedriveDataError(f"Failed to format person data: {str(e)}")

    def format_organization_data(self, organization: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format organization data for standardized output.
        
        Args:
            organization: Raw organization data from Pipedrive
        
        Returns:
            Formatted organization data
        """
        try:
            return {
                'id': organization.get('id'),
                'name': organization.get('name'),
                'address': organization.get('address'),
                'address_subpremise': organization.get('address_subpremise'),
                'address_street_number': organization.get('address_street_number'),
                'address_route': organization.get('address_route'),
                'address_sublocality': organization.get('address_sublocality'),
                'address_locality': organization.get('address_locality'),
                'address_admin_area_level_1': organization.get('address_admin_area_level_1'),
                'address_admin_area_level_2': organization.get('address_admin_area_level_2'),
                'address_country': organization.get('address_country'),
                'address_postal_code': organization.get('address_postal_code'),
                'address_formatted_address': organization.get('address_formatted_address'),
                'owner_id': organization.get('owner_id', {}).get('value') if isinstance(organization.get('owner_id'), dict) else organization.get('owner_id'),
                'owner_name': organization.get('owner_id', {}).get('name') if isinstance(organization.get('owner_id'), dict) else '',
                'add_time': organization.get('add_time'),
                'update_time': organization.get('update_time'),
                'visible_to': organization.get('visible_to', '1'),
                'picture_id': organization.get('picture_id', {}).get('value') if isinstance(organization.get('picture_id'), dict) else organization.get('picture_id'),
                'label': organization.get('label'),
                'cc_email': organization.get('cc_email'),
                'open_deals_count': organization.get('open_deals_count', 0),
                'related_open_deals_count': organization.get('related_open_deals_count', 0),
                'closed_deals_count': organization.get('closed_deals_count', 0),
                'related_closed_deals_count': organization.get('related_closed_deals_count', 0),
                'won_deals_count': organization.get('won_deals_count', 0),
                'related_won_deals_count': organization.get('related_won_deals_count', 0),
                'lost_deals_count': organization.get('lost_deals_count', 0),
                'related_lost_deals_count': organization.get('related_lost_deals_count', 0),
                'people_count': organization.get('people_count', 0),
                'activities_count': organization.get('activities_count', 0),
                'done_activities_count': organization.get('done_activities_count', 0),
                'undone_activities_count': organization.get('undone_activities_count', 0),
                'files_count': organization.get('files_count', 0),
                'notes_count': organization.get('notes_count', 0),
                'email_messages_count': organization.get('email_messages_count', 0),
                'next_activity_date': organization.get('next_activity_date'),
                'next_activity_time': organization.get('next_activity_time'),
                'next_activity_id': organization.get('next_activity_id'),
                'last_activity_id': organization.get('last_activity_id'),
                'last_activity_date': organization.get('last_activity_date')
            }
            
        except Exception as e:
            self.logger.error(f"Error formatting organization data: {str(e)}")
            raise PipedriveDataError(f"Failed to format organization data: {str(e)}")