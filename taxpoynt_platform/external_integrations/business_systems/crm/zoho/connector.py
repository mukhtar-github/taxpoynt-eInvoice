"""
Zoho CRM Connector - Main Module
Integrates all Zoho CRM connector components for TaxPoynt eInvoice System Integrator functions.
This module combines OAuth 2.0 authentication, REST API communication, data extraction, 
and deal-to-invoice transformation into a unified connector interface compatible with the BaseCRMConnector.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import asyncio

from ....connector_framework import BaseCRMConnector, CRMConnectionError, CRMDataError
from .auth import ZohoCRMAuthenticator
from .rest_client import ZohoCRMRestClient
from .data_extractor import ZohoCRMDataExtractor
from .deal_transformer import ZohoCRMDealTransformer
from .exceptions import (
    ZohoCRMConnectionError,
    ZohoCRMAuthenticationError,
    ZohoCRMAPIError,
    ZohoCRMDataError
)


class ZohoCRMConnector(BaseCRMConnector):
    """
    Zoho CRM connector for TaxPoynt eInvoice System.
    
    Provides comprehensive integration with Zoho CRM including:
    - Multi-flow OAuth 2.0 authentication (Authorization Code, Self-Client)
    - CRM API v2 operations with module support
    - Deal and customer data extraction
    - Deal-to-invoice transformation with UBL BIS 3.0 compliance
    - Bulk operations and search capabilities
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Zoho CRM connector.
        
        Args:
            config: Configuration dictionary containing:
                - client_id: Zoho OAuth client ID
                - client_secret: Zoho OAuth client secret
                - data_center: Zoho data center (us, eu, in, au, jp, ca)
                - scope: OAuth scope permissions
                - auth_flow: Authentication flow type
                - access_token: Direct access token (optional)
                - refresh_token: Refresh token (optional)
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
            self.authenticator = ZohoCRMAuthenticator(config)
            self.rest_client = ZohoCRMRestClient(self.authenticator, config)
            self.data_extractor = ZohoCRMDataExtractor(self.rest_client)
            self.deal_transformer = ZohoCRMDealTransformer(config)
            
            # Connection state
            self.connected = False
            self.user_info = None
            self.org_info = None
            
            self.logger.info("Zoho CRM connector initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Zoho CRM connector: {str(e)}")
            raise CRMConnectionError(f"Initialization failed: {str(e)}")

    async def connect(self) -> Dict[str, Any]:
        """
        Establish connection to Zoho CRM.
        
        Returns:
            Connection metadata including authentication details and user information
        """
        try:
            self.logger.info("Connecting to Zoho CRM...")
            
            # Authenticate
            auth_result = await self.authenticator.authenticate()
            
            # Validate connection and get user/org info
            if await self.authenticator.validate_connection():
                self.user_info = await self.authenticator.get_user_info()
                self.org_info = await self.authenticator.get_organization_info()
                self.connected = True
                
                connection_info = {
                    'status': 'connected',
                    'data_center': self.authenticator.data_center,
                    'api_base_url': self.authenticator.api_base_url,
                    'auth_flow': self.authenticator.auth_flow,
                    'user_id': self.user_info.get('id'),
                    'user_name': self.user_info.get('full_name'),
                    'user_email': self.user_info.get('email'),
                    'organization_id': self.org_info.get('id'),
                    'organization_name': self.org_info.get('company_name'),
                    'connected_at': datetime.now().isoformat(),
                    'token_expires_at': auth_result.get('expires_at')
                }
                
                self.logger.info(f"Successfully connected to Zoho CRM as {self.user_info.get('full_name')}")
                return connection_info
            else:
                raise ZohoCRMConnectionError("Connection validation failed")
                
        except Exception as e:
            self.connected = False
            self.logger.error(f"Failed to connect to Zoho CRM: {str(e)}")
            raise CRMConnectionError(f"Connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from Zoho CRM."""
        try:
            if self.connected:
                await self.authenticator.close()
                await self.rest_client.close()
                self.connected = False
                self.user_info = None
                self.org_info = None
                self.logger.info("Disconnected from Zoho CRM")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test the connection to Zoho CRM.
        
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
        Retrieve deals from Zoho CRM.
        
        Args:
            filters: Filter criteria including:
                - stage: Deal stage
                - min_amount: Minimum deal amount
                - max_amount: Maximum deal amount
                - created_after: ISO date string
                - created_before: ISO date string
                - owner_id: Deal owner ID
                - account_id: Account ID
                - criteria: Custom search criteria
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
            
            self.logger.info(f"Retrieved {len(formatted_deals)} deals from Zoho CRM")
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
            
            deal = await self.data_extractor.get_deal_by_id(deal_id)
            
            if deal:
                formatted_deal = self.data_extractor.format_deal_data(deal)
                self.logger.info(f"Retrieved deal: {formatted_deal.get('name')}")
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
        Search deals by name or description.
        
        Args:
            search_term: Search term to match against deal name/description
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
        Retrieve customer data (accounts and contacts) from Zoho CRM.
        
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
                    'id': account.get('id'),
                    'name': account.get('Account_Name'),
                    'type': 'account',
                    'phone': account.get('Phone'),
                    'website': account.get('Website'),
                    'industry': account.get('Industry'),
                    'revenue': account.get('Annual_Revenue'),
                    'employees': account.get('Employees'),
                    'billing_address': {
                        'street': account.get('Billing_Street'),
                        'city': account.get('Billing_City'),
                        'state': account.get('Billing_State'),
                        'postal_code': account.get('Billing_Code'),
                        'country': account.get('Billing_Country')
                    },
                    'created_date': account.get('Created_Time'),
                    'modified_date': account.get('Modified_Time')
                }
                customers.append(customer)
            
            # Add contacts
            for contact in contacts:
                customer = {
                    'id': contact.get('id'),
                    'name': contact.get('Full_Name'),
                    'type': 'contact',
                    'first_name': contact.get('First_Name'),
                    'last_name': contact.get('Last_Name'),
                    'email': contact.get('Email'),
                    'phone': contact.get('Phone'),
                    'mobile': contact.get('Mobile'),
                    'title': contact.get('Title'),
                    'department': contact.get('Department'),
                    'account': {
                        'id': contact.get('Account_Name', {}).get('id') if isinstance(contact.get('Account_Name'), dict) else None,
                        'name': contact.get('Account_Name', {}).get('name') if isinstance(contact.get('Account_Name'), dict) else contact.get('Account_Name')
                    } if contact.get('Account_Name') else None,
                    'mailing_address': {
                        'street': contact.get('Mailing_Street'),
                        'city': contact.get('Mailing_City'),
                        'state': contact.get('Mailing_State'),
                        'postal_code': contact.get('Mailing_Zip'),
                        'country': contact.get('Mailing_Country')
                    },
                    'created_date': contact.get('Created_Time'),
                    'modified_date': contact.get('Modified_Time')
                }
                customers.append(customer)
            
            self.logger.info(f"Retrieved {len(customers)} customers from Zoho CRM")
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
        Transform a Zoho CRM deal to UBL BIS 3.0 compliant invoice.
        
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
            
            # Get deal data
            deal = await self.data_extractor.get_deal_by_id(deal_id)
            
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
        Get health status of the Zoho CRM connector.
        
        Returns:
            Health status information
        """
        try:
            health_status = {
                'connector_name': 'Zoho CRM',
                'version': 'API v2',
                'connected': self.connected,
                'data_center': self.authenticator.data_center,
                'api_base_url': self.authenticator.api_base_url,
                'last_check': datetime.now().isoformat()
            }
            
            if self.connected:
                # Test connection
                connection_test = await self.test_connection()
                health_status.update({
                    'connection_test': 'passed' if connection_test else 'failed',
                    'user_info': {
                        'user_id': self.user_info.get('id') if self.user_info else None,
                        'user_name': self.user_info.get('full_name') if self.user_info else None,
                        'user_email': self.user_info.get('email') if self.user_info else None
                    },
                    'organization_info': {
                        'org_id': self.org_info.get('id') if self.org_info else None,
                        'org_name': self.org_info.get('company_name') if self.org_info else None
                    },
                    'token_expires_at': self.authenticator.token_expires_at.isoformat() if self.authenticator.token_expires_at else None
                })
            else:
                health_status.update({
                    'connection_test': 'not_connected',
                    'user_info': None,
                    'organization_info': None,
                    'token_expires_at': None
                })
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error getting health status: {str(e)}")
            return {
                'connector_name': 'Zoho CRM',
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
        Synchronize deals from Zoho CRM.
        
        Args:
            sync_options: Synchronization options including:
                - full_sync: Whether to perform full synchronization
                - last_sync_date: Last synchronization timestamp
                - batch_size: Number of records per batch
                - include_closed: Whether to include closed deals
        
        Returns:
            Synchronization results
        """
        try:
            if not self.connected:
                await self.connect()
            
            options = sync_options or {}
            batch_size = options.get('batch_size', 200)
            
            self.logger.info(f"Starting deals synchronization with options: {options}")
            
            # Build filter based on sync options
            filters = {}
            
            if not options.get('include_closed', False):
                filters['criteria'] = "Stage:not_equal:Closed Won and Stage:not_equal:Closed Lost"
            
            if options.get('last_sync_date') and not options.get('full_sync', False):
                sync_date_filter = f"Modified_Time:greater_than:{options['last_sync_date']}"
                if 'criteria' in filters:
                    filters['criteria'] += f" and {sync_date_filter}"
                else:
                    filters['criteria'] = sync_date_filter
            
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
            'bulk_operations',
            'module_metadata',
            'health_monitoring',
            'incremental_sync',
            'products_support',
            'multi_currency',
            'tax_calculation',
            'ubl_compliance',
            'firs_compliance',
            'multi_datacenter'
        ]

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()