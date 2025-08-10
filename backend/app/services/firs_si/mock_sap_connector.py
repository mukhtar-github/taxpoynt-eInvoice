"""
Mock SAP Connector for TaxPoynt eInvoice - System Integrator Development

This module provides a mock implementation of SAP S/4HANA connector for
immediate development capability while actual SAP system access is being arranged.

The mock connector simulates SAP OData API responses and provides realistic
test data for development and testing purposes.

Mock SAP API Endpoints Simulated:
- /API_BILLING_DOCUMENT_SRV/A_BillingDocument
- /API_OPLACCTGDOCITEMCUBE_SRV/A_JournalEntryItem
- /API_BUSINESS_PARTNER/A_BusinessPartner
- /oauth/token (OAuth 2.0 authentication)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4
import asyncio

from app.services.firs_si.base_erp_connector import BaseERPConnector, ERPConnectionError, ERPAuthenticationError, ERPDataError
from app.schemas.integration import IntegrationTestResult

logger = logging.getLogger(__name__)


class MockSAPConnector(BaseERPConnector):
    """
    Mock SAP S/4HANA connector for development and testing
    
    This connector simulates SAP OData API responses to enable development
    of FIRS integration without requiring actual SAP system access.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Mock SAP connector
        
        Args:
            config: Configuration dictionary containing SAP connection parameters
        """
        super().__init__(config)
        self.host = config.get('host', 'mock-sap-dev.taxpoynt.com')
        self.client = config.get('client', '100')
        self.username = config.get('username', 'TAXPOYNT_USER')
        self.password = config.get('password', 'mock_password')
        self.oauth_client_id = config.get('oauth_client_id', 'taxpoynt_client')
        self.oauth_client_secret = config.get('oauth_client_secret', 'mock_secret')
        
        # Mock data storage
        self._mock_access_token = None
        self._mock_token_expiry = None
        self._mock_invoices = self._generate_mock_invoices()
        self._mock_partners = self._generate_mock_partners()
        self._mock_products = self._generate_mock_products()
        
        logger.info(f"Initialized MockSAPConnector for host: {self.host}")
    
    @property
    def erp_type(self) -> str:
        """Return the ERP system type"""
        return "sap"
    
    @property
    def erp_version(self) -> str:
        """Return the ERP system version"""
        return "S/4HANA 2023 Cloud (Mock)"
    
    @property
    def supported_features(self) -> List[str]:
        """Return list of supported features for this ERP connector"""
        return [
            'invoice_extraction',
            'partner_management',
            'product_management',
            'company_info',
            'invoice_search',
            'pagination',
            'attachments',
            'firs_transformation',
            'oauth2_authentication',
            'odata_api',
            'billing_document_api',
            'journal_entry_api',
            'business_partner_api',
            'mock_environment'
        ]
    
    async def test_connection(self) -> IntegrationTestResult:
        """Test connection to the mock SAP system"""
        try:
            # Simulate connection test
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Validate basic config
            if not self.host or not self.username:
                return IntegrationTestResult(
                    success=False,
                    message="Missing required SAP connection parameters",
                    details={"error": "host or username not configured"}
                )
            
            # Test OAuth authentication
            auth_result = await self._mock_oauth_authentication()
            if not auth_result['success']:
                return IntegrationTestResult(
                    success=False,
                    message=f"OAuth authentication failed: {auth_result['error']}",
                    details=auth_result
                )
            
            # Test basic OData service access
            service_test = await self._test_odata_services()
            
            return IntegrationTestResult(
                success=True,
                message="Successfully connected to Mock SAP S/4HANA system",
                details={
                    "host": self.host,
                    "client": self.client,
                    "username": self.username,
                    "auth_method": "OAuth 2.0",
                    "available_services": service_test['available_services'],
                    "mock_data_loaded": True,
                    "mock_invoices_count": len(self._mock_invoices),
                    "mock_partners_count": len(self._mock_partners),
                    "supported_features": self.supported_features
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                success=False,
                message=f"Connection test failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    async def authenticate(self) -> bool:
        """Authenticate with the mock SAP system using OAuth 2.0"""
        try:
            # Simulate OAuth 2.0 authentication
            auth_result = await self._mock_oauth_authentication()
            
            if auth_result['success']:
                self.authenticated = True
                self.connected = True
                self.last_connection_time = datetime.utcnow()
                self._mock_access_token = auth_result['access_token']
                self._mock_token_expiry = datetime.utcnow() + timedelta(hours=1)
                
                logger.info(f"Successfully authenticated with Mock SAP system")
                return True
            else:
                raise ERPAuthenticationError(f"Authentication failed: {auth_result['error']}")
                
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            self.authenticated = False
            self.connected = False
            raise ERPAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def _mock_oauth_authentication(self) -> Dict[str, Any]:
        """Mock OAuth 2.0 authentication process"""
        await asyncio.sleep(0.2)  # Simulate network delay
        
        # Validate credentials
        if not self.oauth_client_id or not self.oauth_client_secret:
            return {
                'success': False,
                'error': 'Missing OAuth credentials'
            }
        
        # Generate mock access token
        mock_token = f"sap_mock_token_{uuid4().hex[:16]}"
        
        return {
            'success': True,
            'access_token': mock_token,
            'token_type': 'Bearer',
            'expires_in': 3600,
            'scope': 'API_BILLING_DOCUMENT_SRV_0001 API_OPLACCTGDOCITEMCUBE_SRV_0001 API_BUSINESS_PARTNER_0001'
        }
    
    async def _test_odata_services(self) -> Dict[str, Any]:
        """Test availability of mock OData services"""
        available_services = [
            {
                'name': 'API_BILLING_DOCUMENT_SRV',
                'description': 'Billing Document API for SD invoices',
                'version': '0001',
                'status': 'active'
            },
            {
                'name': 'API_OPLACCTGDOCITEMCUBE_SRV',
                'description': 'Journal Entry API for FI invoices',
                'version': '0001',
                'status': 'active'
            },
            {
                'name': 'API_BUSINESS_PARTNER',
                'description': 'Business Partner API',
                'version': '0001',
                'status': 'active'
            }
        ]
        
        return {
            'available_services': available_services,
            'total_services': len(available_services)
        }
    
    def _generate_mock_invoices(self) -> List[Dict[str, Any]]:
        """Generate mock SAP invoice data"""
        mock_invoices = []
        
        for i in range(1, 51):  # Generate 50 mock invoices
            invoice_date = datetime.now() - timedelta(days=i)
            due_date = invoice_date + timedelta(days=30)
            
            mock_invoice = {
                'BillingDocument': f'9000{i:06d}',
                'BillingDocumentType': 'F2',  # Invoice
                'SoldToParty': f'BP{i:06d}',
                'BillToParty': f'BP{i:06d}',
                'BillingDocumentDate': invoice_date.strftime('%Y-%m-%d'),
                'BillingDocumentIsCancelled': False,
                'CancelledBillingDocument': '',
                'BillingDocumentCategory': 'M',
                'SDDocumentCategory': 'C',
                'CreatedByUser': 'TAXPOYNT_USER',
                'CreationDate': invoice_date.strftime('%Y-%m-%d'),
                'LastChangeDate': invoice_date.strftime('%Y-%m-%d'),
                'OrganizationDivision': '01',
                'DistributionChannel': '10',
                'SalesOrganization': '1000',
                'NetAmount': round(10000 + (i * 150.75), 2),
                'TaxAmount': round((10000 + (i * 150.75)) * 0.075, 2),
                'TotalGrossAmount': round((10000 + (i * 150.75)) * 1.075, 2),
                'TransactionCurrency': 'NGN',
                'PaymentTerms': 'NT30',
                'CustomerPaymentTerms': 'NT30',
                'IncotermsClassification': 'EXW',
                'CustomerAccountAssignmentGroup': '01',
                'to_Item': self._generate_mock_invoice_items(f'9000{i:06d}'),
                'to_Partner': self._generate_mock_invoice_partners(f'BP{i:06d}'),
                'to_PricingElement': self._generate_mock_pricing_elements(f'9000{i:06d}')
            }
            
            mock_invoices.append(mock_invoice)
        
        return mock_invoices
    
    def _generate_mock_invoice_items(self, billing_document: str) -> List[Dict[str, Any]]:
        """Generate mock invoice line items"""
        items = []
        
        for item_num in range(1, 4):  # 3 items per invoice
            item = {
                'BillingDocument': billing_document,
                'BillingDocumentItem': f'{item_num:06d}',
                'BillingDocumentItemCategory': 'TAN',
                'SalesDocumentItemType': 'TAN',
                'Material': f'MAT{item_num:06d}',
                'MaterialByCustomer': f'CUST_MAT_{item_num}',
                'Plant': '1000',
                'StorageLocation': '0001',
                'BillingQuantity': 10.0 + item_num,
                'BillingQuantityUnit': 'EA',
                'NetAmount': round(3000 + (item_num * 500), 2),
                'GrossAmount': round((3000 + (item_num * 500)) * 1.075, 2),
                'TaxAmount': round((3000 + (item_num * 500)) * 0.075, 2),
                'TransactionCurrency': 'NGN',
                'MaterialGroup': f'MG{item_num:02d}',
                'ProductHierarchy': f'PH{item_num:06d}',
                'MaterialDescription': f'Mock Product {item_num} - SAP Test Item',
                'ItemDescription': f'Mock Product {item_num} - SAP Test Item',
                'ProfitCenter': '1000',
                'OrderReason': '001',
                'ItemIsRelevantForCredit': True,
                'WBSElement': '',
                'ControllingArea': '1000',
                'ProfitabilitySegment': '1000000001',
                'OrderID': f'ORD{item_num:06d}',
                'SalesDocument': f'SD{item_num:06d}',
                'SalesDocumentItem': f'{item_num:06d}'
            }
            
            items.append(item)
        
        return items
    
    def _generate_mock_invoice_partners(self, partner_id: str) -> List[Dict[str, Any]]:
        """Generate mock invoice partner data"""
        return [
            {
                'BillingDocument': partner_id.replace('BP', '9000'),
                'PartnerFunction': 'AG',  # Sold-to party
                'Customer': partner_id,
                'Supplier': '',
                'Personnel': '',
                'ContactPerson': ''
            },
            {
                'BillingDocument': partner_id.replace('BP', '9000'),
                'PartnerFunction': 'RE',  # Bill-to party
                'Customer': partner_id,
                'Supplier': '',
                'Personnel': '',
                'ContactPerson': ''
            }
        ]
    
    def _generate_mock_pricing_elements(self, billing_document: str) -> List[Dict[str, Any]]:
        """Generate mock pricing elements (taxes, discounts)"""
        return [
            {
                'BillingDocument': billing_document,
                'PricingProcedureStep': '010',
                'PricingProcedureCounter': '01',
                'ConditionType': 'PR00',  # Price
                'ConditionRateValue': 100.0,
                'ConditionCurrency': 'NGN',
                'ConditionAmount': 10000.0,
                'TransactionCurrency': 'NGN',
                'PricingScaleType': '',
                'IsManuallyChanged': False
            },
            {
                'BillingDocument': billing_document,
                'PricingProcedureStep': '050',
                'PricingProcedureCounter': '01',
                'ConditionType': 'UTXJ',  # Tax
                'ConditionRateValue': 7.5,
                'ConditionCurrency': 'NGN',
                'ConditionAmount': 750.0,
                'TransactionCurrency': 'NGN',
                'PricingScaleType': '',
                'IsManuallyChanged': False
            }
        ]
    
    def _generate_mock_partners(self) -> List[Dict[str, Any]]:
        """Generate mock business partner data"""
        partners = []
        
        for i in range(1, 26):  # Generate 25 mock partners
            partner = {
                'BusinessPartner': f'BP{i:06d}',
                'BusinessPartnerCategory': '2',  # Customer
                'BusinessPartnerFullName': f'Mock Customer {i} Limited',
                'BusinessPartnerName': f'Mock Customer {i}',
                'BusinessPartnerUUID': str(uuid4()),
                'CreatedByUser': 'TAXPOYNT_USER',
                'CreationDate': datetime.now().strftime('%Y-%m-%d'),
                'LastChangeDate': datetime.now().strftime('%Y-%m-%d'),
                'LastChangedByUser': 'TAXPOYNT_USER',
                'IsNaturalPerson': '',
                'IsOneTimeAccount': False,
                'BusinessPartnerType': 'ORG',
                'ETag': f'W/"datetime\'{datetime.now().isoformat()}\'"',
                'BusinessPartnerIsBlocked': False,
                'GroupBusinessPartnerName1': f'Mock Customer {i} Limited',
                'GroupBusinessPartnerName2': '',
                'IndependentAddressID': '',
                'InternationalLocationNumber1': '',
                'InternationalLocationNumber2': '',
                'InternationalLocationNumber3': '',
                'NameCountry': 'NG',
                'NameFormat': '',
                'PersonFullName': f'Mock Customer {i} Limited',
                'PersonNumber': '',
                'IsMarkedForArchiving': False,
                'BusinessPartnerIDByExtSystem': '',
                'BusinessPartnerPrintFormat': 'BP',
                'BusinessPartnerOccupation': '',
                'BusPartMaritalStatus': '',
                'BusPartNationality': 'NG',
                'BusinessPartnerBirthDate': None,
                'BusinessPartnerDeathDate': None,
                'BusinessPartnerIsBlocked': False,
                'NaturalPersonEmployerName': '',
                'BusinessPartnerPlaceOfBirth': '',
                'BusinessPartnerPlaceOfDeath': '',
                'NaturalPersonEmployerName': '',
                'LastCustomerContactDate': None,
                'LastSupplierContactDate': None,
                'LastVendorContactDate': None,
                'BusinessPartnerTaxNumber': f'NG{i:010d}',
                'ResponsibleType': '',
                'TaxID1': f'NG{i:010d}',
                'TaxID2': '',
                'TaxID3': '',
                'TaxID4': '',
                'TaxID5': '',
                'VATRegistration': f'VAT{i:010d}',
                'CustomerIsBlocked': False,
                'SupplierIsBlocked': False
            }
            
            partners.append(partner)
        
        return partners
    
    def _generate_mock_products(self) -> List[Dict[str, Any]]:
        """Generate mock product data"""
        products = []
        
        for i in range(1, 21):  # Generate 20 mock products
            product = {
                'Material': f'MAT{i:06d}',
                'MaterialType': 'FERT',  # Finished product
                'MaterialGroup': f'MG{i:02d}',
                'MaterialDescription': f'Mock Product {i} - SAP Test Item',
                'MaterialBaseUnit': 'EA',
                'MaterialWeightUnit': 'KG',
                'MaterialNetWeight': 1.5 + (i * 0.1),
                'MaterialGrossWeight': 2.0 + (i * 0.1),
                'MaterialVolume': 0.5 + (i * 0.05),
                'MaterialVolumeUnit': 'L',
                'CreatedByUser': 'TAXPOYNT_USER',
                'CreationDate': datetime.now().strftime('%Y-%m-%d'),
                'LastChangeDate': datetime.now().strftime('%Y-%m-%d'),
                'LastChangedByUser': 'TAXPOYNT_USER',
                'IsMarkedForDeletion': False,
                'ProductHierarchy': f'PH{i:06d}',
                'SizeOrDimensionText': f'Size {i}',
                'IndustryStandardName': 'ISO',
                'MaterialFreightGroup': '01',
                'ProductAllocationDeterminationProcedure': '1',
                'IsConfigurableProduct': False,
                'IsBatchManagementRequired': False,
                'IsSerialNumberProfileRequired': False,
                'HasMaterialLedger': False,
                'IsActivated': True,
                'MaterialPrice': 1000.0 + (i * 50),
                'MaterialPriceUnit': 'NGN',
                'MaterialPriceValidFrom': datetime.now().strftime('%Y-%m-%d'),
                'MaterialPriceValidTo': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'TaxClassification': 'MWST',
                'MaterialUsage': 'PROD',
                'MaterialOrigin': 'NG'
            }
            
            products.append(product)
        
        return products
    
    async def get_invoices(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        include_draft: bool = False,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Fetch invoices from mock SAP system"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            # Filter invoices by date if provided
            filtered_invoices = self._mock_invoices
            
            if from_date:
                filtered_invoices = [
                    inv for inv in filtered_invoices 
                    if datetime.strptime(inv['BillingDocumentDate'], '%Y-%m-%d') >= from_date
                ]
            
            if to_date:
                filtered_invoices = [
                    inv for inv in filtered_invoices 
                    if datetime.strptime(inv['BillingDocumentDate'], '%Y-%m-%d') <= to_date
                ]
            
            # Calculate pagination
            total_invoices = len(filtered_invoices)
            offset = (page - 1) * page_size
            paginated_invoices = filtered_invoices[offset:offset + page_size]
            
            # Calculate pagination info
            total_pages = (total_invoices + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            # Format invoices for response
            formatted_invoices = []
            for invoice in paginated_invoices:
                formatted_invoice = await self._format_sap_invoice_data(invoice, include_attachments)
                formatted_invoices.append(formatted_invoice)
            
            return {
                "invoices": formatted_invoices,
                "total": total_invoices,
                "page": page,
                "page_size": page_size,
                "pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": page + 1 if has_next else None,
                "prev_page": page - 1 if has_prev else None,
                "data_source": "mock_sap_billing_document_api"
            }
            
        except Exception as e:
            logger.error(f"Error fetching mock SAP invoices: {str(e)}")
            raise ERPDataError(f"Error fetching mock SAP invoices: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: Union[int, str]) -> Dict[str, Any]:
        """Get specific invoice by ID from mock SAP system"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            invoice_id_str = str(invoice_id)
            
            # Find invoice in mock data
            invoice = next(
                (inv for inv in self._mock_invoices if inv['BillingDocument'] == invoice_id_str),
                None
            )
            
            if not invoice:
                raise ERPDataError(f"Invoice with ID {invoice_id} not found in mock SAP system")
            
            return await self._format_sap_invoice_data(invoice, include_attachments=True)
            
        except Exception as e:
            logger.error(f"Error fetching mock SAP invoice {invoice_id}: {str(e)}")
            raise ERPDataError(f"Error fetching mock SAP invoice {invoice_id}: {str(e)}")
    
    async def search_invoices(
        self,
        search_term: str,
        include_attachments: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search for invoices in mock SAP system"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            # Filter invoices by search term
            filtered_invoices = []
            search_term_lower = search_term.lower()
            
            for invoice in self._mock_invoices:
                # Search in invoice number, partner, and items
                if (search_term_lower in invoice['BillingDocument'].lower() or
                    search_term_lower in invoice['SoldToParty'].lower() or
                    any(search_term_lower in item['MaterialDescription'].lower() 
                        for item in invoice.get('to_Item', []))):
                    filtered_invoices.append(invoice)
            
            # Calculate pagination
            total_invoices = len(filtered_invoices)
            offset = (page - 1) * page_size
            paginated_invoices = filtered_invoices[offset:offset + page_size]
            
            # Calculate pagination info
            total_pages = (total_invoices + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            # Format invoices for response
            formatted_invoices = []
            for invoice in paginated_invoices:
                formatted_invoice = await self._format_sap_invoice_data(invoice, include_attachments)
                formatted_invoices.append(formatted_invoice)
            
            return {
                "invoices": formatted_invoices,
                "total": total_invoices,
                "page": page,
                "page_size": page_size,
                "pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": page + 1 if has_next else None,
                "prev_page": page - 1 if has_prev else None,
                "search_term": search_term,
                "data_source": "mock_sap_billing_document_api"
            }
            
        except Exception as e:
            logger.error(f"Error searching mock SAP invoices: {str(e)}")
            raise ERPDataError(f"Error searching mock SAP invoices: {str(e)}")
    
    async def get_partners(
        self,
        search_term: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get partners from mock SAP system"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            filtered_partners = self._mock_partners
            
            if search_term:
                search_term_lower = search_term.lower()
                filtered_partners = [
                    partner for partner in filtered_partners
                    if (search_term_lower in partner['BusinessPartnerName'].lower() or
                        search_term_lower in partner['BusinessPartnerFullName'].lower() or
                        search_term_lower in partner['BusinessPartner'].lower())
                ]
            
            # Apply limit
            limited_partners = filtered_partners[:limit]
            
            # Format partners for response
            formatted_partners = []
            for partner in limited_partners:
                formatted_partner = {
                    "id": partner['BusinessPartner'],
                    "name": partner['BusinessPartnerFullName'],
                    "short_name": partner['BusinessPartnerName'],
                    "vat": partner.get('VATRegistration', ''),
                    "tax_id": partner.get('TaxID1', ''),
                    "email": f"{partner['BusinessPartnerName'].lower().replace(' ', '.')}@mock-customer.com",
                    "phone": f"+234-{partner['BusinessPartner'][-6:]}",
                    "street": f"{partner['BusinessPartner']} Mock Street",
                    "city": "Lagos",
                    "state": "Lagos State",
                    "country": "Nigeria",
                    "country_code": "NG",
                    "postal_code": f"{partner['BusinessPartner'][-5:]}",
                    "business_partner_category": partner['BusinessPartnerCategory'],
                    "is_blocked": partner['BusinessPartnerIsBlocked'],
                    "creation_date": partner['CreationDate'],
                    "last_change_date": partner['LastChangeDate']
                }
                formatted_partners.append(formatted_partner)
            
            return formatted_partners
            
        except Exception as e:
            logger.error(f"Error fetching mock SAP partners: {str(e)}")
            raise ERPDataError(f"Error fetching mock SAP partners: {str(e)}")
    
    async def _format_sap_invoice_data(self, invoice: Dict[str, Any], include_attachments: bool = False) -> Dict[str, Any]:
        """Format SAP invoice data into standardized format"""
        try:
            # Find corresponding partner data
            partner_data = next(
                (partner for partner in self._mock_partners 
                 if partner['BusinessPartner'] == invoice['SoldToParty']),
                None
            )
            
            if not partner_data:
                # Create default partner data if not found
                partner_data = {
                    'BusinessPartner': invoice['SoldToParty'],
                    'BusinessPartnerFullName': f'Mock Partner {invoice["SoldToParty"]}',
                    'BusinessPartnerName': f'Mock Partner {invoice["SoldToParty"]}',
                    'VATRegistration': f'VAT{invoice["SoldToParty"][2:]}',
                    'TaxID1': f'NG{invoice["SoldToParty"][2:]}',
                }
            
            # Format invoice data
            formatted_invoice = {
                "id": invoice['BillingDocument'],
                "name": invoice['BillingDocument'],
                "invoice_number": invoice['BillingDocument'],
                "reference": invoice.get('CustomerReference', ''),
                "invoice_date": invoice['BillingDocumentDate'],
                "invoice_date_due": (datetime.strptime(invoice['BillingDocumentDate'], '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d'),
                "state": "posted" if not invoice['BillingDocumentIsCancelled'] else "cancelled",
                "document_type": invoice['BillingDocumentType'],
                "document_type_name": self._get_document_type_name(invoice['BillingDocumentType']),
                "amount_total": invoice['TotalGrossAmount'],
                "amount_untaxed": invoice['NetAmount'],
                "amount_tax": invoice['TaxAmount'],
                "currency": {
                    "id": invoice['TransactionCurrency'],
                    "name": invoice['TransactionCurrency'],
                    "symbol": "₦" if invoice['TransactionCurrency'] == 'NGN' else invoice['TransactionCurrency']
                },
                "partner": {
                    "id": partner_data['BusinessPartner'],
                    "name": partner_data['BusinessPartnerFullName'],
                    "short_name": partner_data['BusinessPartnerName'],
                    "vat": partner_data.get('VATRegistration', ''),
                    "tax_id": partner_data.get('TaxID1', ''),
                    "email": f"{partner_data['BusinessPartnerName'].lower().replace(' ', '.')}@mock-customer.com",
                    "phone": f"+234-{partner_data['BusinessPartner'][-6:]}",
                },
                "sales_organization": invoice.get('SalesOrganization', ''),
                "distribution_channel": invoice.get('DistributionChannel', ''),
                "division": invoice.get('OrganizationDivision', ''),
                "payment_terms": invoice.get('PaymentTerms', ''),
                "incoterms": invoice.get('IncotermsClassification', ''),
                "created_by": invoice.get('CreatedByUser', ''),
                "creation_date": invoice.get('CreationDate', ''),
                "last_change_date": invoice.get('LastChangeDate', ''),
                "lines": []
            }
            
            # Format invoice lines
            for line in invoice.get('to_Item', []):
                line_data = {
                    "id": line['BillingDocumentItem'],
                    "name": line['MaterialDescription'],
                    "quantity": line['BillingQuantity'],
                    "unit": line['BillingQuantityUnit'],
                    "price_unit": line['NetAmount'] / line['BillingQuantity'] if line['BillingQuantity'] > 0 else 0,
                    "price_subtotal": line['NetAmount'],
                    "price_total": line['GrossAmount'],
                    "tax_amount": line['TaxAmount'],
                    "material": line['Material'],
                    "material_group": line.get('MaterialGroup', ''),
                    "product_hierarchy": line.get('ProductHierarchy', ''),
                    "plant": line.get('Plant', ''),
                    "storage_location": line.get('StorageLocation', ''),
                    "profit_center": line.get('ProfitCenter', ''),
                    "controlling_area": line.get('ControllingArea', ''),
                    "sales_document": line.get('SalesDocument', ''),
                    "sales_document_item": line.get('SalesDocumentItem', ''),
                    "taxes": self._get_line_taxes(line),
                    "product": {
                        "id": line['Material'],
                        "name": line['MaterialDescription'],
                        "code": line['Material'],
                        "customer_material": line.get('MaterialByCustomer', ''),
                    }
                }
                formatted_invoice["lines"].append(line_data)
            
            # Add mock attachments if requested
            if include_attachments:
                formatted_invoice["attachments"] = self._generate_mock_attachments(invoice['BillingDocument'])
            
            # Add SAP-specific metadata
            formatted_invoice["sap_metadata"] = {
                "client": self.client,
                "billing_document_category": invoice.get('BillingDocumentCategory', ''),
                "sd_document_category": invoice.get('SDDocumentCategory', ''),
                "is_cancelled": invoice['BillingDocumentIsCancelled'],
                "cancelled_document": invoice.get('CancelledBillingDocument', ''),
                "pricing_elements": invoice.get('to_PricingElement', []),
                "partner_functions": invoice.get('to_Partner', [])
            }
            
            return formatted_invoice
            
        except Exception as e:
            logger.error(f"Error formatting SAP invoice data: {str(e)}")
            raise ERPDataError(f"Error formatting SAP invoice data: {str(e)}")
    
    def _get_document_type_name(self, doc_type: str) -> str:
        """Get document type name from SAP document type code"""
        type_mapping = {
            'F2': 'Invoice',
            'G2': 'Credit Note',
            'L2': 'Debit Note',
            'S1': 'Cancellation',
            'RE': 'Invoice for Returns'
        }
        return type_mapping.get(doc_type, 'Unknown Document Type')
    
    def _get_line_taxes(self, line: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tax information for invoice line"""
        return [
            {
                "id": "UTXJ",
                "name": "Nigerian VAT",
                "amount": 7.5,
                "tax_amount": line['TaxAmount'],
                "tax_base": line['NetAmount'],
                "tax_type": "VAT",
                "tax_code": "UTXJ"
            }
        ]
    
    def _generate_mock_attachments(self, billing_document: str) -> List[Dict[str, Any]]:
        """Generate mock attachments for SAP invoice"""
        return [
            {
                "id": f"ATT_{billing_document}_001",
                "name": f"Invoice_{billing_document}.pdf",
                "mimetype": "application/pdf",
                "size": 245760,
                "url": f"https://mock-sap-dev.taxpoynt.com/attachments/{billing_document}/Invoice_{billing_document}.pdf",
                "created_date": datetime.now().strftime('%Y-%m-%d'),
                "description": "SAP Billing Document PDF"
            },
            {
                "id": f"ATT_{billing_document}_002",
                "name": f"DeliveryNote_{billing_document}.pdf",
                "mimetype": "application/pdf",
                "size": 156432,
                "url": f"https://mock-sap-dev.taxpoynt.com/attachments/{billing_document}/DeliveryNote_{billing_document}.pdf",
                "created_date": datetime.now().strftime('%Y-%m-%d'),
                "description": "Delivery Note PDF"
            }
        ]
    
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate invoice data for FIRS compliance"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # SAP-specific validation rules
        required_fields = [
            'BillingDocument', 'BillingDocumentDate', 'SoldToParty', 
            'NetAmount', 'TaxAmount', 'TransactionCurrency', 'to_Item'
        ]
        
        for field in required_fields:
            if field not in invoice_data:
                validation_result['errors'].append(f"Missing required SAP field: {field}")
                validation_result['is_valid'] = False
        
        # Validate invoice items
        if 'to_Item' in invoice_data:
            if not invoice_data['to_Item']:
                validation_result['errors'].append("SAP invoice must have at least one billing item")
                validation_result['is_valid'] = False
            else:
                for i, item in enumerate(invoice_data['to_Item']):
                    if 'Material' not in item:
                        validation_result['errors'].append(f"Item {i+1}: Material is required")
                        validation_result['is_valid'] = False
                    if 'BillingQuantity' not in item or item['BillingQuantity'] <= 0:
                        validation_result['errors'].append(f"Item {i+1}: Billing quantity must be positive")
                        validation_result['is_valid'] = False
        
        # SAP-specific business rules
        if 'BillingDocumentIsCancelled' in invoice_data and invoice_data['BillingDocumentIsCancelled']:
            validation_result['warnings'].append("Invoice is cancelled in SAP system")
        
        return validation_result
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform SAP invoice data to FIRS-compliant format"""
        try:
            # Get partner data
            partner_data = next(
                (partner for partner in self._mock_partners 
                 if partner['BusinessPartner'] == invoice_data['SoldToParty']),
                {}
            )
            
            # Get company info
            company_info = await self.get_company_info()
            
            # Transform to UBL BIS 3.0 format
            firs_invoice = {
                'invoice_type_code': self._map_sap_doc_type_to_firs(invoice_data.get('BillingDocumentType', 'F2')),
                'id': invoice_data['BillingDocument'],
                'issue_date': invoice_data['BillingDocumentDate'],
                'due_date': (datetime.strptime(invoice_data['BillingDocumentDate'], '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d'),
                'document_currency_code': invoice_data['TransactionCurrency'],
                'accounting_supplier_party': {
                    'party': {
                        'party_name': {
                            'name': company_info.get('name', 'Mock SAP Company')
                        },
                        'party_tax_scheme': {
                            'company_id': company_info.get('vat', 'NG0123456789')
                        },
                        'party_legal_entity': {
                            'registration_name': company_info.get('name', 'Mock SAP Company'),
                            'company_id': company_info.get('registration_number', 'RC123456')
                        }
                    }
                },
                'accounting_customer_party': {
                    'party': {
                        'party_name': {
                            'name': partner_data.get('BusinessPartnerFullName', 'Mock Customer')
                        },
                        'party_tax_scheme': {
                            'company_id': partner_data.get('VATRegistration', '')
                        },
                        'party_legal_entity': {
                            'registration_name': partner_data.get('BusinessPartnerFullName', 'Mock Customer'),
                            'company_id': partner_data.get('BusinessPartner', '')
                        }
                    }
                },
                'legal_monetary_total': {
                    'line_extension_amount': invoice_data['NetAmount'],
                    'tax_exclusive_amount': invoice_data['NetAmount'],
                    'tax_inclusive_amount': invoice_data['TotalGrossAmount'],
                    'allowance_total_amount': 0,
                    'charge_total_amount': 0,
                    'prepaid_amount': 0,
                    'payable_amount': invoice_data['TotalGrossAmount']
                },
                'invoice_line': [],
                'payment_terms': {
                    'payment_terms_code': invoice_data.get('PaymentTerms', 'NT30'),
                    'payment_due_date': (datetime.strptime(invoice_data['BillingDocumentDate'], '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
                }
            }
            
            # Transform invoice lines
            for line in invoice_data.get('to_Item', []):
                firs_line = {
                    'id': line['BillingDocumentItem'],
                    'invoiced_quantity': {
                        'quantity': line['BillingQuantity'],
                        'unit_code': self._map_sap_unit_to_ubl(line['BillingQuantityUnit'])
                    },
                    'line_extension_amount': line['NetAmount'],
                    'item': {
                        'description': line['MaterialDescription'],
                        'name': line['MaterialDescription'],
                        'sellers_item_identification': {
                            'id': line['Material']
                        },
                        'buyers_item_identification': {
                            'id': line.get('MaterialByCustomer', '')
                        },
                        'commodity_classification': {
                            'item_classification_code': line.get('MaterialGroup', ''),
                            'list_id': 'SAP_MATERIAL_GROUP'
                        }
                    },
                    'price': {
                        'price_amount': line['NetAmount'] / line['BillingQuantity'] if line['BillingQuantity'] > 0 else 0,
                        'base_quantity': {
                            'quantity': 1,
                            'unit_code': self._map_sap_unit_to_ubl(line['BillingQuantityUnit'])
                        }
                    },
                    'tax_total': {
                        'tax_amount': line['TaxAmount'],
                        'tax_subtotal': [{
                            'taxable_amount': line['NetAmount'],
                            'tax_amount': line['TaxAmount'],
                            'tax_category': {
                                'id': 'S',
                                'percent': 7.5,
                                'tax_scheme': {
                                    'id': 'VAT',
                                    'name': 'Nigerian VAT'
                                }
                            }
                        }]
                    }
                }
                firs_invoice['invoice_line'].append(firs_line)
            
            # Add tax totals
            firs_invoice['tax_total'] = {
                'tax_amount': invoice_data['TaxAmount'],
                'tax_subtotal': [{
                    'taxable_amount': invoice_data['NetAmount'],
                    'tax_amount': invoice_data['TaxAmount'],
                    'tax_category': {
                        'id': 'S',
                        'percent': 7.5,
                        'tax_scheme': {
                            'id': 'VAT',
                            'name': 'Nigerian VAT'
                        }
                    }
                }]
            }
            
            return {
                'firs_invoice': firs_invoice,
                'source_format': 'sap_billing_document',
                'target_format': target_format,
                'transformation_metadata': {
                    'transformation_date': datetime.utcnow().isoformat(),
                    'source_invoice_id': invoice_data['BillingDocument'],
                    'erp_type': self.erp_type,
                    'erp_version': self.erp_version,
                    'sap_client': self.client,
                    'sap_document_type': invoice_data.get('BillingDocumentType', 'F2'),
                    'sap_sales_organization': invoice_data.get('SalesOrganization', ''),
                    'sap_distribution_channel': invoice_data.get('DistributionChannel', ''),
                    'mock_transformation': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error transforming SAP invoice to FIRS format: {str(e)}")
            raise ERPDataError(f"Error transforming SAP invoice to FIRS format: {str(e)}")
    
    def _map_sap_doc_type_to_firs(self, sap_doc_type: str) -> str:
        """Map SAP document type to FIRS invoice type code"""
        mapping = {
            'F2': '380',  # Invoice
            'G2': '381',  # Credit Note
            'L2': '383',  # Debit Note
            'S1': '384',  # Cancellation
            'RE': '380'   # Invoice for Returns
        }
        return mapping.get(sap_doc_type, '380')
    
    def _map_sap_unit_to_ubl(self, sap_unit: str) -> str:
        """Map SAP unit of measure to UBL unit code"""
        mapping = {
            'EA': 'C62',  # Each
            'PC': 'C62',  # Piece
            'KG': 'KGM',  # Kilogram
            'L': 'LTR',   # Liter
            'M': 'MTR',   # Meter
            'H': 'HUR',   # Hour
            'ST': 'C62',  # Set
            'BOX': 'BX',  # Box
            'PAL': 'PF'   # Pallet
        }
        return mapping.get(sap_unit, 'C62')
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in mock SAP system"""
        try:
            # Simulate status update
            await asyncio.sleep(0.1)
            
            # Find invoice in mock data
            invoice_id_str = str(invoice_id)
            invoice = next(
                (inv for inv in self._mock_invoices if inv['BillingDocument'] == invoice_id_str),
                None
            )
            
            if not invoice:
                return {
                    'success': False,
                    'error': f'Invoice {invoice_id} not found in mock SAP system',
                    'invoice_id': invoice_id
                }
            
            # Update mock invoice status
            # In real implementation, this would call SAP API
            logger.info(f"Mock SAP: Updating invoice {invoice_id} status: {status_data}")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'status_updated': True,
                'new_status': status_data.get('status'),
                'updated_at': datetime.utcnow().isoformat(),
                'sap_response': {
                    'billing_document': invoice_id_str,
                    'status_code': '200',
                    'message': 'Status updated successfully in mock SAP system'
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating mock SAP invoice status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'invoice_id': invoice_id
            }
    
    async def get_company_info(self) -> Dict[str, Any]:
        """Get company information from mock SAP system"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            return {
                "id": "1000",
                "name": "Mock SAP Company Limited",
                "code": "1000",
                "client": self.client,
                "vat": "NG0123456789",
                "tax_number": "NG0123456789",
                "registration_number": "RC123456",
                "email": "info@mock-sap-company.com",
                "phone": "+234-1-2345678",
                "website": "https://mock-sap-company.com",
                "currency": "NGN",
                "address": {
                    "street": "1 Mock SAP Street",
                    "street2": "Victoria Island",
                    "city": "Lagos",
                    "state": "Lagos State",
                    "zip": "101001",
                    "country": "Nigeria",
                    "country_code": "NG"
                },
                "fiscal_year_variant": "K4",
                "controlling_area": "1000",
                "company_type": "Limited Company",
                "industry": "Technology Services",
                "establishment_date": "2020-01-01",
                "sap_metadata": {
                    "company_code": "1000",
                    "controlling_area": "1000",
                    "fiscal_year_variant": "K4",
                    "chart_of_accounts": "NGAAP",
                    "country_key": "NG",
                    "currency_key": "NGN",
                    "language_key": "EN"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting mock SAP company info: {str(e)}")
            raise ERPDataError(f"Error getting mock SAP company info: {str(e)}")
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from mock SAP system"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            return {
                "country": "NG",
                "tax_system": "Nigerian VAT",
                "default_currency": "NGN",
                "taxes": [
                    {
                        "id": "UTXJ",
                        "name": "Nigerian VAT",
                        "description": "Value Added Tax - Nigeria",
                        "rate": 7.5,
                        "type": "VAT",
                        "calculation_type": "percentage",
                        "is_active": True,
                        "effective_from": "2020-01-01",
                        "applicable_to": "goods_and_services"
                    },
                    {
                        "id": "UTXE",
                        "name": "VAT Exempt",
                        "description": "VAT Exempt Items",
                        "rate": 0.0,
                        "type": "VAT",
                        "calculation_type": "percentage",
                        "is_active": True,
                        "effective_from": "2020-01-01",
                        "applicable_to": "exempt_items"
                    }
                ],
                "tax_procedures": [
                    {
                        "procedure": "TAXNG",
                        "description": "Nigerian Tax Procedure",
                        "country": "NG",
                        "is_default": True
                    }
                ],
                "withholding_taxes": [
                    {
                        "id": "WHVT",
                        "name": "Withholding Tax on VAT",
                        "rate": 5.0,
                        "type": "WHT",
                        "applicable_to": "services"
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting mock SAP tax configuration: {str(e)}")
            return {
                "taxes": [],
                "error": str(e)
            }
    
    async def disconnect(self) -> bool:
        """Disconnect from mock SAP system"""
        try:
            # Simulate disconnection
            await asyncio.sleep(0.1)
            
            self.connected = False
            self.authenticated = False
            self.last_connection_time = None
            self._mock_access_token = None
            self._mock_token_expiry = None
            
            logger.info("Disconnected from Mock SAP system")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from mock SAP system: {str(e)}")
            return False
    
    def get_mock_data_summary(self) -> Dict[str, Any]:
        """Get summary of mock data available"""
        return {
            "mock_invoices": len(self._mock_invoices),
            "mock_partners": len(self._mock_partners),
            "mock_products": len(self._mock_products),
            "date_range": {
                "oldest_invoice": min(inv['BillingDocumentDate'] for inv in self._mock_invoices),
                "newest_invoice": max(inv['BillingDocumentDate'] for inv in self._mock_invoices)
            },
            "document_types": list(set(inv['BillingDocumentType'] for inv in self._mock_invoices)),
            "currencies": list(set(inv['TransactionCurrency'] for inv in self._mock_invoices)),
            "sales_organizations": list(set(inv['SalesOrganization'] for inv in self._mock_invoices)),
            "mock_features": [
                "billing_document_api",
                "business_partner_api",
                "oauth2_authentication",
                "odata_responses",
                "firs_transformation",
                "pagination_support",
                "search_functionality",
                "attachment_simulation"
            ]
        }