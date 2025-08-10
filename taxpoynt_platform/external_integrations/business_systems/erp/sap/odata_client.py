"""
SAP OData Client Module
Handles OData API communication for SAP ERP services.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

from .exceptions import SAPODataError

logger = logging.getLogger(__name__)


class SAPODataClient:
    """Handles OData API communication with SAP services."""
    
    def __init__(self, authenticator):
        """Initialize with a SAP authenticator instance."""
        self.authenticator = authenticator
    
    async def make_odata_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = 'GET',
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an OData request to SAP services.
        
        Args:
            endpoint: The OData endpoint to call
            params: Query parameters
            method: HTTP method (GET, POST, etc.)
            data: Request body data
            
        Returns:
            Response data from SAP OData service
        """
        try:
            if not self.authenticator.session:
                self.authenticator.session = await self.authenticator._create_session()
            
            # Build URL
            base_url = self.authenticator._build_base_url()
            url = urljoin(base_url, endpoint)
            
            # Prepare headers
            headers = await self.authenticator._get_auth_headers()
            
            # Prepare auth
            auth = self.authenticator.get_basic_auth() if not self.authenticator.use_oauth else None
            
            # Set default params
            if params is None:
                params = {}
            params.setdefault('$format', 'json')
            
            # Make request
            async with self.authenticator.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                auth=auth
            ) as response:
                return await self._handle_odata_response(response)
                
        except Exception as e:
            logger.error(f"OData request failed: {str(e)}")
            raise SAPODataError(f"OData request failed: {str(e)}")
    
    async def _handle_odata_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle OData response and error cases."""
        try:
            if response.status == 200:
                data = await response.json()
                
                # OData responses are wrapped in 'd' property
                if 'd' in data:
                    if 'results' in data['d']:
                        return {
                            'success': True,
                            'data': data['d']['results'],
                            'count': len(data['d']['results']),
                            'metadata': data['d'].get('__metadata', {})
                        }
                    else:
                        return {
                            'success': True,
                            'data': data['d'],
                            'metadata': data['d'].get('__metadata', {})
                        }
                else:
                    return {
                        'success': True,
                        'data': data
                    }
            
            elif response.status == 401:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': 'Authentication failed',
                    'status_code': 401,
                    'details': error_text
                }
            
            elif response.status == 403:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': 'Access forbidden - insufficient permissions',
                    'status_code': 403,
                    'details': error_text
                }
            
            elif response.status == 404:
                return {
                    'success': False,
                    'error': 'Resource not found',
                    'status_code': 404
                }
            
            else:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': f'Request failed with status {response.status}',
                    'status_code': response.status,
                    'details': error_text
                }
                
        except Exception as e:
            logger.error(f"Error handling OData response: {str(e)}")
            return {
                'success': False,
                'error': f'Response handling error: {str(e)}'
            }
    
    async def get_billing_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get billing documents from SAP."""
        try:
            params = {
                '$top': limit,
                '$skip': offset,
                '$select': 'BillingDocument,BillingDocumentDate,BillingDocumentType,SoldToParty,NetAmount,TaxAmount,TotalAmount,TransactionCurrency',
                '$format': 'json'
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = []
                
                if filters.get('start_date'):
                    filter_conditions.append(f"BillingDocumentDate ge datetime'{filters['start_date']}'")
                
                if filters.get('end_date'):
                    filter_conditions.append(f"BillingDocumentDate le datetime'{filters['end_date']}'")
                
                if filters.get('document_type'):
                    filter_conditions.append(f"BillingDocumentType eq '{filters['document_type']}'")
                
                if filter_conditions:
                    params['$filter'] = ' and '.join(filter_conditions)
            
            return await self.make_odata_request(
                self.authenticator.endpoints['billing_document'],
                params=params
            )
            
        except Exception as e:
            logger.error(f"Error retrieving billing documents: {str(e)}")
            raise SAPODataError(f"Error retrieving billing documents: {str(e)}")
    
    async def get_journal_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get journal entries from SAP."""
        try:
            params = {
                '$top': limit,
                '$skip': offset,
                '$select': 'CompanyCode,AccountingDocument,FiscalYear,PostingDate,DocumentDate,AccountingDocumentType,BusinessPartner,GLAccount,AmountInCompanyCodeCurrency,CompanyCodeCurrency',
                '$format': 'json'
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = []
                
                if filters.get('company_code'):
                    filter_conditions.append(f"CompanyCode eq '{filters['company_code']}'")
                
                if filters.get('start_date'):
                    filter_conditions.append(f"PostingDate ge datetime'{filters['start_date']}'")
                
                if filters.get('end_date'):
                    filter_conditions.append(f"PostingDate le datetime'{filters['end_date']}'")
                
                if filters.get('document_type'):
                    filter_conditions.append(f"AccountingDocumentType eq '{filters['document_type']}'")
                
                if filter_conditions:
                    params['$filter'] = ' and '.join(filter_conditions)
            
            return await self.make_odata_request(
                self.authenticator.endpoints['journal_entry'],
                params=params
            )
            
        except Exception as e:
            logger.error(f"Error retrieving journal entries: {str(e)}")
            raise SAPODataError(f"Error retrieving journal entries: {str(e)}")
    
    async def get_business_partners(
        self,
        limit: int = 100,
        offset: int = 0,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get business partners from SAP."""
        try:
            params = {
                '$top': limit,
                '$skip': offset,
                '$select': 'BusinessPartner,BusinessPartnerName,BusinessPartnerCategory,Customer,Supplier,TaxNumber1,TaxNumber2',
                '$format': 'json'
            }
            
            # Add search filter if provided
            if search_term:
                params['$filter'] = f"substringof('{search_term}', BusinessPartnerName)"
            
            return await self.make_odata_request(
                self.authenticator.endpoints['business_partner'],
                params=params
            )
            
        except Exception as e:
            logger.error(f"Error retrieving business partners: {str(e)}")
            raise SAPODataError(f"Error retrieving business partners: {str(e)}")
    
    async def get_billing_document_by_id(self, document_id: str) -> Dict[str, Any]:
        """Get a specific billing document by ID."""
        try:
            endpoint = f"{self.authenticator.endpoints['billing_document']}('{document_id}')"
            
            params = {
                '$format': 'json'
            }
            
            return await self.make_odata_request(endpoint, params=params)
            
        except Exception as e:
            logger.error(f"Error retrieving billing document {document_id}: {str(e)}")
            raise SAPODataError(f"Error retrieving billing document {document_id}: {str(e)}")
    
    async def search_documents(
        self,
        search_criteria: Dict[str, Any],
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search documents with specific criteria."""
        try:
            filter_conditions = []
            
            # Build filter conditions based on search criteria
            if search_criteria.get('customer_name'):
                # This would need to be joined with customer master data
                filter_conditions.append(f"substringof('{search_criteria['customer_name']}', SoldToParty)")
            
            if search_criteria.get('document_number'):
                filter_conditions.append(f"substringof('{search_criteria['document_number']}', BillingDocument)")
            
            if search_criteria.get('amount_range'):
                min_amount, max_amount = search_criteria['amount_range']
                if min_amount is not None:
                    filter_conditions.append(f"NetAmount ge {min_amount}")
                if max_amount is not None:
                    filter_conditions.append(f"NetAmount le {max_amount}")
            
            if search_criteria.get('date_range'):
                start_date, end_date = search_criteria['date_range']
                if start_date:
                    filter_conditions.append(f"BillingDocumentDate ge datetime'{start_date}'")
                if end_date:
                    filter_conditions.append(f"BillingDocumentDate le datetime'{end_date}'")
            
            params = {
                '$top': limit,
                '$select': 'BillingDocument,BillingDocumentDate,BillingDocumentType,SoldToParty,NetAmount,TaxAmount,TotalAmount,TransactionCurrency',
                '$format': 'json'
            }
            
            if filter_conditions:
                params['$filter'] = ' and '.join(filter_conditions)
            
            return await self.make_odata_request(
                self.authenticator.endpoints['billing_document'],
                params=params
            )
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise SAPODataError(f"Error searching documents: {str(e)}")
    
    async def get_metadata(self, service: str) -> Dict[str, Any]:
        """Get OData metadata for a service."""
        try:
            endpoint_map = {
                'billing': self.authenticator.endpoints['billing_document'],
                'journal': self.authenticator.endpoints['journal_entry'], 
                'partner': self.authenticator.endpoints['business_partner']
            }
            
            if service not in endpoint_map:
                raise SAPODataError(f"Unknown service: {service}")
            
            endpoint = f"{endpoint_map[service]}/{self.authenticator.endpoints['metadata']}"
            
            return await self.make_odata_request(endpoint)
            
        except Exception as e:
            logger.error(f"Error retrieving metadata for {service}: {str(e)}")
            raise SAPODataError(f"Error retrieving metadata for {service}: {str(e)}")