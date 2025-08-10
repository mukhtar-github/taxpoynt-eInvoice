"""
Microsoft Dynamics CRM Connector - Main Module
Integrates all Dynamics CRM connector components for TaxPoynt eInvoice System Integrator functions.
This module combines OAuth 2.0 authentication, REST API communication, data extraction, 
and deal-to-invoice transformation into a unified connector interface compatible with the BaseCRMConnector.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import asyncio

from ....connector_framework import BaseCRMConnector, CRMConnectionError, CRMDataError
from .auth import DynamicsCRMAuthenticator
from .rest_client import DynamicsCRMRestClient
from .data_extractor import DynamicsCRMDataExtractor
from .deal_transformer import DynamicsCRMDealTransformer
from .exceptions import (
    DynamicsCRMConnectionError,
    DynamicsCRMAuthenticationError,
    DynamicsCRMAPIError,
    DynamicsCRMDataError
)


class MicrosoftDynamicsCRMConnector(BaseCRMConnector):
    """
    Microsoft Dynamics CRM connector for TaxPoynt eInvoice System.
    
    Provides comprehensive integration with Microsoft Dynamics CRM including:
    - Multi-flow OAuth 2.0 authentication (Authorization Code, Client Credentials, Password)
    - Web API OData queries and operations
    - Opportunity and customer data extraction
    - Deal-to-invoice transformation with UBL BIS 3.0 compliance
    - Batch operations and metadata management
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Microsoft Dynamics CRM connector.
        
        Args:
            config: Configuration dictionary containing:
                - environment_url: Dynamics CRM environment URL
                - client_id: Azure AD application ID
                - client_secret: Azure AD application secret
                - tenant_id: Azure AD tenant ID
                - auth_flow: Authentication flow type
                - api_version: Web API version (default: v9.2)
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
            self.authenticator = DynamicsCRMAuthenticator(config)
            self.rest_client = DynamicsCRMRestClient(self.authenticator, config)
            self.data_extractor = DynamicsCRMDataExtractor(self.rest_client)
            self.deal_transformer = DynamicsCRMDealTransformer(config)
            
            # Connection state
            self.connected = False
            self.user_info = None
            
            self.logger.info("Microsoft Dynamics CRM connector initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Dynamics CRM connector: {str(e)}")
            raise CRMConnectionError(f"Initialization failed: {str(e)}")

    async def connect(self) -> Dict[str, Any]:
        """
        Establish connection to Microsoft Dynamics CRM.
        
        Returns:
            Connection metadata including authentication details and user information
        """
        try:
            self.logger.info("Connecting to Microsoft Dynamics CRM...")
            
            # Authenticate
            auth_result = await self.authenticator.authenticate()
            
            # Validate connection and get user info
            if await self.authenticator.validate_connection():
                self.user_info = await self.authenticator.get_user_info()
                self.connected = True
                
                connection_info = {
                    'status': 'connected',
                    'environment_url': self.authenticator.environment_url,
                    'api_version': self.authenticator.api_version,
                    'auth_flow': self.authenticator.auth_flow,
                    'user_id': self.user_info.get('UserId'),
                    'user_name': self.user_info.get('fullname'),
                    'organization_id': self.user_info.get('OrganizationId'),
                    'business_unit_id': self.user_info.get('BusinessUnitId'),
                    'connected_at': auth_result.get('expires_at'),
                    'token_expires_at': auth_result.get('expires_at')
                }
                
                self.logger.info(f"Successfully connected to Dynamics CRM as {self.user_info.get('fullname')}")
                return connection_info
            else:
                raise DynamicsCRMConnectionError("Connection validation failed")
                
        except Exception as e:
            self.connected = False
            self.logger.error(f"Failed to connect to Dynamics CRM: {str(e)}")
            raise CRMConnectionError(f"Connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from Microsoft Dynamics CRM."""
        try:
            if self.connected:
                await self.authenticator.close()
                await self.rest_client.close()
                self.connected = False
                self.user_info = None
                self.logger.info("Disconnected from Microsoft Dynamics CRM")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test the connection to Microsoft Dynamics CRM.
        
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
        Retrieve opportunities (deals) from Microsoft Dynamics CRM.
        
        Args:
            filters: Filter criteria including:
                - state: 'open' or 'closed'
                - created_after: ISO date string
                - created_before: ISO date string
                - owner_id: Owner user ID
                - customer_id: Customer account/contact ID
                - min_amount: Minimum opportunity amount
                - max_amount: Maximum opportunity amount
                - custom_filter: Custom OData filter expression
            limit: Maximum number of deals to return
        
        Returns:
            List of formatted deal records
        """
        try:
            if not self.connected:
                await self.connect()
            
            self.logger.info(f"Retrieving opportunities with filters: {filters}")
            
            # Extract opportunities
            opportunities = await self.data_extractor.get_opportunities(
                filters=filters,
                limit=limit,
                include_line_items=True
            )
            
            # Format opportunities
            formatted_deals = []
            for opportunity in opportunities:
                formatted_deal = self.data_extractor.format_opportunity_data(opportunity)
                formatted_deals.append(formatted_deal)
            
            self.logger.info(f"Retrieved {len(formatted_deals)} opportunities from Dynamics CRM")
            return formatted_deals
            
        except Exception as e:
            self.logger.error(f"Error retrieving deals: {str(e)}")
            raise CRMDataError(f"Failed to retrieve deals: {str(e)}")

    async def get_deal_by_id(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific opportunity by ID.
        
        Args:
            deal_id: Opportunity ID (GUID)
        
        Returns:
            Formatted deal record or None if not found
        """
        try:
            if not self.connected:
                await self.connect()
            
            self.logger.info(f"Retrieving opportunity: {deal_id}")
            
            opportunity = await self.data_extractor.get_opportunity_by_id(deal_id)
            
            if opportunity:
                formatted_deal = self.data_extractor.format_opportunity_data(opportunity)
                self.logger.info(f"Retrieved opportunity: {formatted_deal.get('name')}")
                return formatted_deal
            else:
                self.logger.warning(f"Opportunity not found: {deal_id}")
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
        Search opportunities by name or description.
        
        Args:
            search_term: Search term to match against opportunity name/description
            limit: Maximum number of results to return
        
        Returns:
            List of matching formatted deal records
        """
        try:
            if not self.connected:
                await self.connect()
            
            self.logger.info(f"Searching opportunities for term: {search_term}")
            
            opportunities = await self.data_extractor.search_opportunities(
                search_term=search_term,
                limit=limit
            )
            
            # Format opportunities
            formatted_deals = []
            for opportunity in opportunities:
                formatted_deal = self.data_extractor.format_opportunity_data(opportunity)
                formatted_deals.append(formatted_deal)
            
            self.logger.info(f"Found {len(formatted_deals)} opportunities matching '{search_term}'")
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
        Retrieve customer data (accounts and contacts) from Dynamics CRM.
        
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
            
            # Get accounts and contacts in parallel
            accounts_task = self.data_extractor.get_accounts(filters, limit)
            contacts_task = self.data_extractor.get_contacts(filters, limit)
            
            accounts, contacts = await asyncio.gather(accounts_task, contacts_task)
            
            # Combine and format results
            customers = []
            
            # Add accounts
            for account in accounts:
                customer = {
                    'id': account.get('accountid'),
                    'name': account.get('name'),
                    'type': 'account',
                    'email': account.get('emailaddress1'),
                    'phone': account.get('telephone1'),
                    'website': account.get('websiteurl'),
                    'address': account.get('address1_composite'),
                    'revenue': account.get('revenue'),
                    'employees': account.get('numberofemployees'),
                    'created_date': account.get('createdon'),
                    'modified_date': account.get('modifiedon')
                }
                customers.append(customer)
            
            # Add contacts
            for contact in contacts:
                customer = {
                    'id': contact.get('contactid'),
                    'name': contact.get('fullname'),
                    'type': 'contact',
                    'email': contact.get('emailaddress1'),
                    'phone': contact.get('telephone1'),
                    'mobile': contact.get('mobilephone'),
                    'job_title': contact.get('jobtitle'),
                    'address': contact.get('address1_composite'),
                    'account': {
                        'id': contact.get('parentcustomerid_account', {}).get('accountid'),
                        'name': contact.get('parentcustomerid_account', {}).get('name')
                    } if 'parentcustomerid_account' in contact else None,
                    'created_date': contact.get('createdon'),
                    'modified_date': contact.get('modifiedon')
                }
                customers.append(customer)
            
            self.logger.info(f"Retrieved {len(customers)} customers from Dynamics CRM")
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
        Transform a Dynamics CRM opportunity to UBL BIS 3.0 compliant invoice.
        
        Args:
            deal_id: Opportunity ID to transform
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
            
            self.logger.info(f"Transforming opportunity {deal_id} to invoice")
            
            # Get opportunity data
            opportunity = await self.data_extractor.get_opportunity_by_id(deal_id)
            
            if not opportunity:
                raise CRMDataError(f"Opportunity not found: {deal_id}")
            
            # Format opportunity data
            formatted_opportunity = self.data_extractor.format_opportunity_data(opportunity)
            
            # Transform to invoice
            invoice_data = self.deal_transformer.transform_opportunity_to_invoice(
                formatted_opportunity,
                transformation_options
            )
            
            self.logger.info(f"Successfully transformed opportunity {deal_id} to invoice {invoice_data.get('id')}")
            return invoice_data
            
        except Exception as e:
            self.logger.error(f"Error transforming deal to invoice: {str(e)}")
            raise CRMDataError(f"Failed to transform deal to invoice: {str(e)}")

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the Dynamics CRM connector.
        
        Returns:
            Health status information
        """
        try:
            health_status = {
                'connector_name': 'Microsoft Dynamics CRM',
                'version': self.authenticator.api_version,
                'connected': self.connected,
                'environment_url': self.authenticator.environment_url,
                'last_check': datetime.now().isoformat()
            }
            
            if self.connected:
                # Test connection
                connection_test = await self.test_connection()
                health_status.update({
                    'connection_test': 'passed' if connection_test else 'failed',
                    'user_info': {
                        'user_id': self.user_info.get('UserId') if self.user_info else None,
                        'user_name': self.user_info.get('fullname') if self.user_info else None,
                        'organization_id': self.user_info.get('OrganizationId') if self.user_info else None
                    },
                    'token_expires_at': self.authenticator.token_expires_at.isoformat() if self.authenticator.token_expires_at else None
                })
            else:
                health_status.update({
                    'connection_test': 'not_connected',
                    'user_info': None,
                    'token_expires_at': None
                })
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error getting health status: {str(e)}")
            return {
                'connector_name': 'Microsoft Dynamics CRM',
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
        Synchronize deals from Dynamics CRM.
        
        Args:
            sync_options: Synchronization options including:
                - full_sync: Whether to perform full synchronization
                - last_sync_date: Last synchronization timestamp
                - batch_size: Number of records per batch
                - include_closed: Whether to include closed opportunities
        
        Returns:
            Synchronization results
        """
        try:
            if not self.connected:
                await self.connect()
            
            options = sync_options or {}
            batch_size = options.get('batch_size', 100)
            
            self.logger.info(f"Starting deals synchronization with options: {options}")
            
            # Build filter based on sync options
            filters = {}
            
            if not options.get('include_closed', False):
                filters['state'] = 'open'
            
            if options.get('last_sync_date') and not options.get('full_sync', False):
                filters['created_after'] = options['last_sync_date']
            
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
            'oauth2_authentication',
            'odata_queries',
            'batch_operations',
            'metadata_access',
            'health_monitoring',
            'incremental_sync',
            'line_items_support',
            'multi_currency',
            'tax_calculation',
            'ubl_compliance',
            'firs_compliance'
        ]

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()