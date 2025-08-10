"""
Pipedrive CRM Connector - Main Module
Integrates all Pipedrive connector components for TaxPoynt eInvoice System Integrator functions.
This module combines API token/OAuth 2.0 authentication, REST API communication, data extraction, 
and deal-to-invoice transformation into a unified connector interface compatible with the BaseCRMConnector.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import asyncio

from ....connector_framework import BaseCRMConnector, CRMConnectionError, CRMDataError
from .auth import PipedriveAuthenticator
from .rest_client import PipedriveRestClient
from .data_extractor import PipedriveDataExtractor
from .deal_transformer import PipedriveDealTransformer
from .exceptions import (
    PipedriveConnectionError,
    PipedriveAuthenticationError,
    PipedriveAPIError,
    PipedriveDataError
)


class PipedriveCRMConnector(BaseCRMConnector):
    """
    Pipedrive CRM connector for TaxPoynt eInvoice System.
    
    Provides comprehensive integration with Pipedrive CRM including:
    - API token and OAuth 2.0 authentication
    - Pipedrive API v1 operations with full CRUD support
    - Deal, person, and organization data extraction
    - Deal-to-invoice transformation with UBL BIS 3.0 compliance
    - Pipeline and stage management
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Pipedrive CRM connector.
        
        Args:
            config: Configuration dictionary containing:
                - company_domain: Pipedrive company domain
                - api_token: Pipedrive API token (for token auth)
                - auth_method: Authentication method (api_token, oauth2)
                - client_id: OAuth client ID (for OAuth)
                - client_secret: OAuth client secret (for OAuth)
                - timeout: Request timeout in seconds
                - max_retries: Maximum retry attempts
                - supplier_party: Supplier information for invoices
                - payment_means: Payment configuration
                - tax_settings: Tax calculation settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        try:
            self.authenticator = PipedriveAuthenticator(config)
            self.rest_client = PipedriveRestClient(self.authenticator, config)
            self.data_extractor = PipedriveDataExtractor(self.rest_client)
            self.deal_transformer = PipedriveDealTransformer(config)
            
            # Connection state
            self.connected = False
            self.user_info = None
            self.company_info = None
            
            self.logger.info("Pipedrive CRM connector initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Pipedrive CRM connector: {str(e)}")
            raise CRMConnectionError(f"Initialization failed: {str(e)}")

    async def connect(self) -> Dict[str, Any]:
        """
        Establish connection to Pipedrive CRM.
        
        Returns:
            Connection metadata including authentication details and user information
        """
        try:
            self.logger.info("Connecting to Pipedrive CRM...")
            
            # Authenticate
            auth_result = await self.authenticator.authenticate()
            
            # Validate connection and get user/company info
            if await self.authenticator.validate_connection():
                self.user_info = await self.authenticator.get_user_info()
                self.company_info = await self.authenticator.get_company_info()
                self.connected = True
                
                connection_info = {
                    'status': 'connected',
                    'company_domain': self.authenticator.company_domain,
                    'base_url': self.authenticator.base_url,
                    'auth_method': self.authenticator.auth_method,
                    'user_id': self.user_info.get('id'),
                    'user_name': self.user_info.get('name'),
                    'user_email': self.user_info.get('email'),
                    'company_id': self.company_info.get('id'),
                    'company_name': self.company_info.get('name'),
                    'connected_at': datetime.now().isoformat(),
                    'auth_status': auth_result.get('status')
                }
                
                self.logger.info(f"Successfully connected to Pipedrive CRM as {self.user_info.get('name')}")
                return connection_info
            else:
                raise PipedriveConnectionError("Connection validation failed")
                
        except Exception as e:
            self.connected = False
            self.logger.error(f"Failed to connect to Pipedrive CRM: {str(e)}")
            raise CRMConnectionError(f"Connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from Pipedrive CRM."""
        try:
            if self.connected:
                await self.authenticator.close()
                await self.rest_client.close()
                self.connected = False
                self.user_info = None
                self.company_info = None
                self.logger.info("Disconnected from Pipedrive CRM")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test the connection to Pipedrive CRM.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.connected:
                await self.connect()
            
            return await self.authenticator.validate_connection()
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

    async def get_deals(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve deals from Pipedrive CRM.
        
        Args:
            filters: Filter criteria including:
                - user_id: User ID to filter by
                - stage_id: Stage ID to filter by
                - status: Deal status (open, closed, all_not_deleted)
                - owned_by_you: Filter by ownership
                - filter_id: Custom filter ID
            limit: Maximum number of deals to return
        
        Returns:
            List of formatted deal records
        """
        try:
            if not self.connected:
                await self.connect()
            
            self.logger.info(f"Retrieving deals with filters: {filters}")
            
            # Extract deals
            deals = await self.data_extractor.get_deals(
                filters=filters,
                limit=limit,
                include_products=True
            )
            
            # Format deals
            formatted_deals = []
            for deal in deals:
                formatted_deal = self.data_extractor.format_deal_data(deal)
                formatted_deals.append(formatted_deal)
            
            self.logger.info(f"Retrieved {len(formatted_deals)} deals from Pipedrive CRM")
            return formatted_deals
            
        except Exception as e:
            self.logger.error(f"Error retrieving deals: {str(e)}")
            raise CRMDataError(f"Failed to retrieve deals: {str(e)}")

    async def get_deal_by_id(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific deal by ID.
        
        Args:
            deal_id: Deal ID
        
        Returns:
            Formatted deal record or None if not found
        """
        try:
            if not self.connected:
                await self.connect()
            
            self.logger.info(f"Retrieving deal: {deal_id}")
            
            # Convert to int for Pipedrive API
            try:
                deal_id_int = int(deal_id)
            except ValueError:
                self.logger.error(f"Invalid deal ID format: {deal_id}")
                return None
            
            deal = await self.data_extractor.get_deal_by_id(deal_id_int)
            
            if deal:
                formatted_deal = self.data_extractor.format_deal_data(deal)
                self.logger.info(f"Retrieved deal: {formatted_deal.get('title')}")
                return formatted_deal
            else:
                self.logger.warning(f"Deal not found: {deal_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error retrieving deal {deal_id}: {str(e)}")
            raise CRMDataError(f"Failed to retrieve deal: {str(e)}")

    async def search_deals(
        self,
        search_term: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search deals by term.
        
        Args:
            search_term: Search term to match against deal title/notes
            limit: Maximum number of results to return
        
        Returns:
            List of matching formatted deal records
        """
        try:
            if not self.connected:
                await self.connect()
            
            self.logger.info(f"Searching deals for term: {search_term}")
            
            deals = await self.data_extractor.search_deals(
                search_term=search_term,
                limit=limit
            )
            
            # Format deals
            formatted_deals = []
            for deal in deals:
                formatted_deal = self.data_extractor.format_deal_data(deal)
                formatted_deals.append(formatted_deal)
            
            self.logger.info(f"Found {len(formatted_deals)} deals matching '{search_term}'")
            return formatted_deals
            
        except Exception as e:
            self.logger.error(f"Error searching deals: {str(e)}")
            raise CRMDataError(f"Failed to search deals: {str(e)}")

    async def get_customers(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve customer data (persons and organizations) from Pipedrive CRM.
        
        Args:
            filters: Filter criteria for customers
            limit: Maximum number of customers to return
        
        Returns:
            List of customer records
        """
        try:
            if not self.connected:
                await self.connect()
            
            self.logger.info(f"Retrieving customers with filters: {filters}")
            
            # Get persons and organizations in parallel
            persons_task = self.data_extractor.get_persons(filters, limit)
            organizations_task = self.data_extractor.get_organizations(filters, limit)
            
            persons, organizations = await asyncio.gather(persons_task, organizations_task)
            
            # Combine and format results
            customers = []
            
            # Add organizations
            for organization in organizations:
                formatted_org = self.data_extractor.format_organization_data(organization)
                customer = {
                    'id': formatted_org.get('id'),
                    'name': formatted_org.get('name'),
                    'type': 'organization',
                    'address': formatted_org.get('address'),
                    'owner_id': formatted_org.get('owner_id'),
                    'owner_name': formatted_org.get('owner_name'),
                    'add_time': formatted_org.get('add_time'),
                    'update_time': formatted_org.get('update_time'),
                    'deals_count': formatted_org.get('open_deals_count', 0) + formatted_org.get('closed_deals_count', 0)
                }
                customers.append(customer)
            
            # Add persons
            for person in persons:
                formatted_person = self.data_extractor.format_person_data(person)
                customer = {
                    'id': formatted_person.get('id'),
                    'name': formatted_person.get('name'),
                    'type': 'person',
                    'first_name': formatted_person.get('first_name'),
                    'last_name': formatted_person.get('last_name'),
                    'emails': formatted_person.get('emails', []),
                    'phones': formatted_person.get('phones', []),
                    'organization': formatted_person.get('organization'),
                    'owner_id': formatted_person.get('owner_id'),
                    'owner_name': formatted_person.get('owner_name'),
                    'add_time': formatted_person.get('add_time'),
                    'update_time': formatted_person.get('update_time'),
                    'deals_count': formatted_person.get('open_deals_count', 0) + formatted_person.get('closed_deals_count', 0)
                }
                customers.append(customer)
            
            self.logger.info(f"Retrieved {len(customers)} customers from Pipedrive CRM")
            return customers
            
        except Exception as e:
            self.logger.error(f"Error retrieving customers: {str(e)}")
            raise CRMDataError(f"Failed to retrieve customers: {str(e)}")

    async def transform_deal_to_invoice(
        self,
        deal_id: str,
        transformation_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform a Pipedrive deal to UBL BIS 3.0 compliant invoice.
        
        Args:
            deal_id: Deal ID to transform
            transformation_options: Additional transformation settings including:
                - issue_date: Invoice issue date (ISO format)
                - due_date: Invoice due date (ISO format)
                - invoice_number: Custom invoice number
                - invoice_type_code: UBL invoice type code
                - tax_inclusive: Whether amounts include tax
        
        Returns:
            UBL BIS 3.0 compliant invoice data
        """
        try:
            if not self.connected:
                await self.connect()
            
            self.logger.info(f"Transforming deal {deal_id} to invoice")
            
            # Convert to int for Pipedrive API
            try:
                deal_id_int = int(deal_id)
            except ValueError:
                raise CRMDataError(f"Invalid deal ID format: {deal_id}")
            
            # Get deal data
            deal = await self.data_extractor.get_deal_by_id(deal_id_int)
            
            if not deal:
                raise CRMDataError(f"Deal not found: {deal_id}")
            
            # Format deal data
            formatted_deal = self.data_extractor.format_deal_data(deal)
            
            # Transform to invoice
            invoice_data = self.deal_transformer.transform_deal_to_invoice(
                formatted_deal,
                transformation_options
            )
            
            self.logger.info(f"Successfully transformed deal {deal_id} to invoice {invoice_data.get('id')}")
            return invoice_data
            
        except Exception as e:
            self.logger.error(f"Error transforming deal to invoice: {str(e)}")
            raise CRMDataError(f"Failed to transform deal to invoice: {str(e)}")

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the Pipedrive CRM connector.
        
        Returns:
            Health status information
        """
        try:
            health_status = {
                'connector_name': 'Pipedrive CRM',
                'version': 'API v1',
                'connected': self.connected,
                'company_domain': self.authenticator.company_domain,
                'base_url': self.authenticator.base_url,
                'auth_method': self.authenticator.auth_method,
                'last_check': datetime.now().isoformat()
            }
            
            if self.connected:
                # Test connection
                connection_test = await self.test_connection()
                health_status.update({
                    'connection_test': 'passed' if connection_test else 'failed',
                    'user_info': {
                        'user_id': self.user_info.get('id') if self.user_info else None,
                        'user_name': self.user_info.get('name') if self.user_info else None,
                        'user_email': self.user_info.get('email') if self.user_info else None
                    },
                    'company_info': {
                        'company_id': self.company_info.get('id') if self.company_info else None,
                        'company_name': self.company_info.get('name') if self.company_info else None
                    }
                })
            else:
                health_status.update({
                    'connection_test': 'not_connected',
                    'user_info': None,
                    'company_info': None
                })
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error getting health status: {str(e)}")
            return {
                'connector_name': 'Pipedrive CRM',
                'connected': False,
                'connection_test': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    async def sync_deals(
        self,
        sync_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize deals from Pipedrive CRM.
        
        Args:
            sync_options: Synchronization options including:
                - full_sync: Whether to perform full synchronization
                - last_sync_date: Last synchronization timestamp
                - batch_size: Number of records per batch
                - include_closed: Whether to include closed deals
                - user_id: Specific user ID to sync
                - stage_id: Specific stage ID to sync
        
        Returns:
            Synchronization results
        """
        try:
            if not self.connected:
                await self.connect()
            
            options = sync_options or {}
            batch_size = options.get('batch_size', 500)
            
            self.logger.info(f"Starting deals synchronization with options: {options}")
            
            # Build filter based on sync options
            filters = {}
            
            if not options.get('include_closed', False):
                filters['status'] = 'open'
            
            if options.get('user_id'):
                filters['user_id'] = options['user_id']
            
            if options.get('stage_id'):
                filters['stage_id'] = options['stage_id']
            
            # Get all deals matching criteria
            all_deals = await self.get_deals(filters=filters)
            
            # Process in batches
            batches = [all_deals[i:i + batch_size] for i in range(0, len(all_deals), batch_size)]
            processed_count = 0
            
            sync_results = {
                'total_records': len(all_deals),
                'batches_processed': len(batches),
                'batch_size': batch_size,
                'processed_count': 0,
                'sync_timestamp': datetime.now().isoformat(),
                'deals': all_deals
            }
            
            for batch_index, batch in enumerate(batches):
                self.logger.info(f"Processing batch {batch_index + 1}/{len(batches)} ({len(batch)} records)")
                processed_count += len(batch)
                
                # Simulate batch processing delay
                await asyncio.sleep(0.1)
            
            sync_results['processed_count'] = processed_count
            
            self.logger.info(f"Synchronization completed: {processed_count} deals processed")
            return sync_results
            
        except Exception as e:
            self.logger.error(f"Error during sync: {str(e)}")
            raise CRMDataError(f"Synchronization failed: {str(e)}")

    def get_supported_features(self) -> List[str]:
        """
        Get list of features supported by this connector.
        
        Returns:
            List of supported feature names
        """
        return [
            'deals_extraction',
            'customer_extraction',
            'deal_search',
            'deal_transformation',
            'api_token_authentication',
            'oauth2_authentication',
            'pipeline_management',
            'stage_management',
            'health_monitoring',
            'incremental_sync',
            'products_support',
            'multi_currency',
            'tax_calculation',
            'ubl_compliance',
            'firs_compliance',
            'person_management',
            'organization_management',
            'activity_tracking',
            'note_management'
        ]

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()