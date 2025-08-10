"""
Unit Tests for SAP S/4HANA Integration

This module provides comprehensive unit tests for the SAP S/4HANA integration
including mock responses, connector testing, data transformation, and FIRS
compliance validation.

Test Coverage:
- SAP Connector functionality
- Mock SAP Connector
- OAuth 2.0 authentication
- OData API integration
- Data transformation and mapping
- FIRS compliance validation
- Error handling and edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import json

from app.services.firs_si.mock_sap_connector import MockSAPConnector
from app.services.firs_si.sap_connector import SAPConnector
from app.services.firs_si.sap_oauth import SAPOAuthClient
from app.services.firs_si.sap_firs_mapping import SAPFIRSMapping
from app.services.firs_si.sap_firs_transformer import SAPFIRSTransformer
from app.services.firs_si.erp_connector_factory import ERPConnectorFactory, ERPType
from app.schemas.integration import IntegrationTestResult


class TestSAPIntegration:
    """Test suite for SAP S/4HANA integration"""
    
    @pytest.fixture
    def mock_sap_config(self):
        """Mock SAP configuration for testing"""
        return {
            'host': 'test-sap.taxpoynt.com',
            'client': '100',
            'username': 'TAXPOYNT_USER',
            'password': 'test_password',
            'client_id': 'taxpoynt_client',
            'client_secret': 'test_secret',
            'use_oauth': True,
            'use_https': True,
            'verify_ssl': False,
            'use_mock': True
        }
    
    @pytest.fixture
    def sample_billing_document(self):
        """Sample SAP billing document for testing"""
        return {
            'BillingDocument': '9000000001',
            'BillingDocumentType': 'F2',
            'BillingDocumentDate': '2024-01-15',
            'SoldToParty': 'BP000001',
            'BillToParty': 'BP000001',
            'BillingDocumentIsCancelled': False,
            'NetAmount': 10000.00,
            'TaxAmount': 750.00,
            'TotalGrossAmount': 10750.00,
            'TransactionCurrency': 'NGN',
            'PaymentTerms': 'NT30',
            'SalesOrganization': '1000',
            'DistributionChannel': '10',
            'OrganizationDivision': '01',
            'to_Item': {
                'results': [
                    {
                        'BillingDocument': '9000000001',
                        'BillingDocumentItem': '000010',
                        'Material': 'MAT001',
                        'MaterialDescription': 'Test Product 1',
                        'BillingQuantity': 10.0,
                        'BillingQuantityUnit': 'EA',
                        'NetAmount': 5000.00,
                        'GrossAmount': 5375.00,
                        'TaxAmount': 375.00,
                        'MaterialGroup': 'MG01'
                    },
                    {
                        'BillingDocument': '9000000001',
                        'BillingDocumentItem': '000020',
                        'Material': 'MAT002',
                        'MaterialDescription': 'Test Product 2',
                        'BillingQuantity': 5.0,
                        'BillingQuantityUnit': 'EA',
                        'NetAmount': 5000.00,
                        'GrossAmount': 5375.00,
                        'TaxAmount': 375.00,
                        'MaterialGroup': 'MG02'
                    }
                ]
            }
        }
    
    @pytest.fixture
    def sample_journal_entries(self):
        """Sample SAP journal entries for testing"""
        return [
            {
                'AccountingDocument': '4900000001',
                'AccountingDocumentType': 'DR',
                'PostingDate': '2024-01-15',
                'CompanyCode': '1000',
                'FiscalYear': '2024',
                'Customer': 'BP000001',
                'GLAccount': '40000000',
                'GLAccountName': 'Revenue - Products',
                'AmountInTransactionCurrency': -10000.00,
                'TransactionCurrency': 'NGN',
                'DebitCreditCode': 'H',
                'LineNumber': '001'
            },
            {
                'AccountingDocument': '4900000001',
                'AccountingDocumentType': 'DR',
                'PostingDate': '2024-01-15',
                'CompanyCode': '1000',
                'FiscalYear': '2024',
                'Customer': 'BP000001',
                'GLAccount': '21100000',
                'GLAccountName': 'VAT Payable',
                'AmountInTransactionCurrency': -750.00,
                'TransactionCurrency': 'NGN',
                'DebitCreditCode': 'H',
                'LineNumber': '002'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_mock_sap_connector_initialization(self, mock_sap_config):
        """Test MockSAPConnector initialization"""
        connector = MockSAPConnector(mock_sap_config)
        
        assert connector.erp_type == "sap"
        assert connector.erp_version == "S/4HANA 2023 Cloud (Mock)"
        assert 'oauth2_authentication' in connector.supported_features
        assert 'odata_api' in connector.supported_features
        assert 'mock_environment' in connector.supported_features
    
    @pytest.mark.asyncio
    async def test_mock_sap_connector_connection(self, mock_sap_config):
        """Test MockSAPConnector connection and authentication"""
        connector = MockSAPConnector(mock_sap_config)
        
        # Test connection
        test_result = await connector.test_connection()
        assert test_result.success == True
        assert 'Mock SAP S/4HANA' in test_result.message
        assert test_result.details['mock_data_loaded'] == True
        
        # Test authentication
        auth_result = await connector.authenticate()
        assert auth_result == True
        assert connector.authenticated == True
        assert connector.connected == True
    
    @pytest.mark.asyncio
    async def test_mock_sap_connector_get_invoices(self, mock_sap_config):
        """Test MockSAPConnector invoice retrieval"""
        connector = MockSAPConnector(mock_sap_config)
        await connector.authenticate()
        
        # Test get invoices
        invoices = await connector.get_invoices(page=1, page_size=10)
        
        assert 'invoices' in invoices
        assert 'total' in invoices
        assert 'page' in invoices
        assert invoices['data_source'] == 'mock_sap_billing_document_api'
        assert len(invoices['invoices']) <= 10
        
        # Verify invoice structure
        if invoices['invoices']:
            invoice = invoices['invoices'][0]
            assert 'id' in invoice
            assert 'invoice_number' in invoice
            assert 'partner' in invoice
            assert 'lines' in invoice
            assert 'currency' in invoice
    
    @pytest.mark.asyncio
    async def test_mock_sap_connector_get_invoice_by_id(self, mock_sap_config):
        """Test MockSAPConnector specific invoice retrieval"""
        connector = MockSAPConnector(mock_sap_config)
        await connector.authenticate()
        
        # Test get invoice by ID
        invoice = await connector.get_invoice_by_id('9000000001')
        
        assert invoice['id'] == '9000000001'
        assert invoice['invoice_number'] == '9000000001'
        assert 'partner' in invoice
        assert 'lines' in invoice
        assert 'attachments' in invoice
        assert 'sap_metadata' in invoice
    
    @pytest.mark.asyncio
    async def test_mock_sap_connector_search_invoices(self, mock_sap_config):
        """Test MockSAPConnector invoice search"""
        connector = MockSAPConnector(mock_sap_config)
        await connector.authenticate()
        
        # Test search invoices
        search_result = await connector.search_invoices('9000000001', page=1, page_size=5)
        
        assert 'invoices' in search_result
        assert 'search_term' in search_result
        assert search_result['search_term'] == '9000000001'
        assert search_result['data_source'] == 'mock_sap_billing_document_api'
    
    @pytest.mark.asyncio
    async def test_mock_sap_connector_get_partners(self, mock_sap_config):
        """Test MockSAPConnector partner retrieval"""
        connector = MockSAPConnector(mock_sap_config)
        await connector.authenticate()
        
        # Test get partners
        partners = await connector.get_partners(limit=10)
        
        assert isinstance(partners, list)
        assert len(partners) <= 10
        
        if partners:
            partner = partners[0]
            assert 'id' in partner
            assert 'name' in partner
            assert 'vat' in partner
            assert 'email' in partner
    
    @pytest.mark.asyncio
    async def test_mock_sap_connector_data_transformation(self, mock_sap_config, sample_billing_document):
        """Test MockSAPConnector data transformation"""
        connector = MockSAPConnector(mock_sap_config)
        await connector.authenticate()
        
        # Test data validation
        validation_result = await connector.validate_invoice_data(sample_billing_document)
        assert validation_result['is_valid'] == True
        
        # Test transformation to FIRS format
        transformation_result = await connector.transform_to_firs_format(sample_billing_document)
        
        assert 'firs_invoice' in transformation_result
        assert 'source_format' in transformation_result
        assert 'target_format' in transformation_result
        assert 'transformation_metadata' in transformation_result
        
        firs_invoice = transformation_result['firs_invoice']
        assert 'invoice_type_code' in firs_invoice
        assert 'id' in firs_invoice
        assert 'accounting_supplier_party' in firs_invoice
        assert 'accounting_customer_party' in firs_invoice
        assert 'legal_monetary_total' in firs_invoice
        assert 'invoice_line' in firs_invoice
    
    def test_sap_firs_mapping_document_types(self):
        """Test SAP document type mapping"""
        # Test standard document types
        assert SAPFIRSMapping.map_document_type('F2') == '380'  # Invoice
        assert SAPFIRSMapping.map_document_type('G2') == '381'  # Credit Note
        assert SAPFIRSMapping.map_document_type('L2') == '383'  # Debit Note
        assert SAPFIRSMapping.map_document_type('S1') == '384'  # Cancellation
        
        # Test unknown document type (should default to invoice)
        assert SAPFIRSMapping.map_document_type('UNKNOWN') == '380'
    
    def test_sap_firs_mapping_tax_categories(self):
        """Test SAP tax category mapping"""
        # Test Nigerian VAT
        vat_mapping = SAPFIRSMapping.map_tax_category('UTXJ')
        assert vat_mapping['id'] == 'S'
        assert vat_mapping['percent'] == 7.5
        assert vat_mapping['tax_scheme_id'] == 'VAT'
        
        # Test VAT exempt
        exempt_mapping = SAPFIRSMapping.map_tax_category('UTXE')
        assert exempt_mapping['id'] == 'E'
        assert exempt_mapping['percent'] == 0.0
        
        # Test withholding tax
        wht_mapping = SAPFIRSMapping.map_tax_category('WHVT')
        assert wht_mapping['id'] == 'WHT'
        assert wht_mapping['percent'] == 5.0
    
    def test_sap_firs_mapping_units(self):
        """Test SAP unit of measure mapping"""
        # Test common units
        assert SAPFIRSMapping.map_unit_of_measure('EA') == 'C62'  # Each
        assert SAPFIRSMapping.map_unit_of_measure('KG') == 'KGM'  # Kilogram
        assert SAPFIRSMapping.map_unit_of_measure('L') == 'LTR'   # Liter
        assert SAPFIRSMapping.map_unit_of_measure('M') == 'MTR'   # Meter
        
        # Test unknown unit (should default to Each)
        assert SAPFIRSMapping.map_unit_of_measure('UNKNOWN') == 'C62'
    
    def test_sap_firs_mapping_payment_terms(self):
        """Test SAP payment terms mapping"""
        # Test standard payment terms
        nt30_mapping = SAPFIRSMapping.map_payment_terms('NT30')
        assert nt30_mapping['code'] == 'NET_30'
        assert nt30_mapping['days'] == 30
        
        cod_mapping = SAPFIRSMapping.map_payment_terms('COD')
        assert cod_mapping['code'] == 'COD'
        assert cod_mapping['days'] == 0
        
        # Test unknown payment terms (should default to NET 30)
        unknown_mapping = SAPFIRSMapping.map_payment_terms('UNKNOWN')
        assert unknown_mapping['code'] == 'NET_30'
        assert unknown_mapping['days'] == 30
    
    def test_sap_firs_mapping_due_date_calculation(self):
        """Test due date calculation"""
        invoice_date = '2024-01-15'
        
        # Test NET 30
        due_date = SAPFIRSMapping.calculate_due_date(invoice_date, 'NT30')
        assert due_date == '2024-02-14'
        
        # Test immediate payment
        due_date = SAPFIRSMapping.calculate_due_date(invoice_date, 'NT00')
        assert due_date == '2024-01-15'
        
        # Test NET 60
        due_date = SAPFIRSMapping.calculate_due_date(invoice_date, 'NT60')
        assert due_date == '2024-03-15'
    
    def test_sap_firs_mapping_currency_validation(self):
        """Test currency validation"""
        # Test valid currencies
        assert SAPFIRSMapping.validate_currency('NGN') == True
        assert SAPFIRSMapping.validate_currency('USD') == True
        assert SAPFIRSMapping.validate_currency('EUR') == True
        
        # Test invalid currency
        assert SAPFIRSMapping.validate_currency('INVALID') == False
    
    @pytest.mark.asyncio
    async def test_sap_firs_transformer_billing_document(self, sample_billing_document):
        """Test SAP FIRS transformer with billing document"""
        transformer = SAPFIRSTransformer()
        
        # Test transformation
        result = await transformer.transform_billing_document(sample_billing_document)
        
        assert result['success'] == True
        assert 'firs_invoice' in result
        assert 'transformation_metadata' in result
        assert 'validation_result' in result
        
        firs_invoice = result['firs_invoice']
        assert firs_invoice['ID'] == '9000000001'
        assert firs_invoice['InvoiceTypeCode'] == '380'
        assert firs_invoice['DocumentCurrencyCode'] == 'NGN'
        assert len(firs_invoice['InvoiceLine']) == 2
    
    @pytest.mark.asyncio
    async def test_sap_firs_transformer_journal_entries(self, sample_journal_entries):
        """Test SAP FIRS transformer with journal entries"""
        transformer = SAPFIRSTransformer()
        
        # Test transformation
        result = await transformer.transform_journal_entries(sample_journal_entries)
        
        assert result['success'] == True
        assert 'firs_invoice' in result
        assert 'transformation_metadata' in result
        assert 'validation_result' in result
        
        firs_invoice = result['firs_invoice']
        assert firs_invoice['ID'] == '4900000001'
        assert firs_invoice['InvoiceTypeCode'] == '380'
        assert firs_invoice['DocumentCurrencyCode'] == 'NGN'
    
    def test_sap_oauth_client_initialization(self, mock_sap_config):
        """Test SAP OAuth client initialization"""
        oauth_client = SAPOAuthClient(mock_sap_config)
        
        assert oauth_client.client_id == 'taxpoynt_client'
        assert oauth_client.client_secret == 'test_secret'
        assert oauth_client.grant_type == 'client_credentials'
        assert oauth_client.base_url == 'https://test-sap.taxpoynt.com'
    
    def test_sap_oauth_client_state_generation(self, mock_sap_config):
        """Test OAuth state generation"""
        oauth_client = SAPOAuthClient(mock_sap_config)
        
        state1 = oauth_client.generate_state()
        state2 = oauth_client.generate_state()
        
        assert state1 != state2
        assert len(state1) > 20
        assert oauth_client.state == state2
    
    def test_sap_oauth_client_pkce_generation(self, mock_sap_config):
        """Test PKCE code generation"""
        oauth_client = SAPOAuthClient(mock_sap_config)
        
        verifier, challenge = oauth_client.generate_pkce_pair()
        
        assert verifier != challenge
        assert len(verifier) > 40
        assert len(challenge) > 40
        assert oauth_client.code_verifier == verifier
        assert oauth_client.code_challenge == challenge
    
    def test_sap_oauth_client_authorization_url(self, mock_sap_config):
        """Test authorization URL generation"""
        oauth_client = SAPOAuthClient(mock_sap_config)
        oauth_client.redirect_uri = 'https://taxpoynt.com/callback'
        
        auth_url = oauth_client.build_authorization_url()
        
        assert 'https://test-sap.taxpoynt.com/sap/bc/sec/oauth2/authorize' in auth_url
        assert 'response_type=code' in auth_url
        assert 'client_id=taxpoynt_client' in auth_url
        assert 'state=' in auth_url
        assert 'code_challenge=' in auth_url
        assert 'code_challenge_method=S256' in auth_url
    
    def test_sap_oauth_client_token_info(self, mock_sap_config):
        """Test token information retrieval"""
        oauth_client = SAPOAuthClient(mock_sap_config)
        
        token_info = oauth_client.get_token_info()
        
        assert 'has_access_token' in token_info
        assert 'has_refresh_token' in token_info
        assert 'token_type' in token_info
        assert 'grant_type' in token_info
        assert 'client_id' in token_info
        assert token_info['client_id'] == 'taxpoynt_client'
    
    def test_erp_connector_factory_sap_support(self):
        """Test ERP connector factory SAP support"""
        factory = ERPConnectorFactory()
        
        # Check SAP is supported
        supported_types = factory.get_supported_erp_types()
        assert ERPType.SAP in supported_types
        
        # Check available connectors
        available_connectors = factory.get_available_connectors()
        assert ERPType.SAP in available_connectors
        
        sap_info = available_connectors[ERPType.SAP]
        assert sap_info['production_available'] == True
        assert sap_info['mock_available'] == True
        assert sap_info['production_class'] == 'SAPConnector'
        assert sap_info['mock_class'] == 'MockSAPConnector'
    
    def test_erp_connector_factory_create_sap_connector(self, mock_sap_config):
        """Test creating SAP connector through factory"""
        factory = ERPConnectorFactory()
        
        # Create mock SAP connector
        mock_connector = factory.create_sap_connector(mock_sap_config, use_mock=True)
        
        assert mock_connector is not None
        assert mock_connector.erp_type == 'sap'
        assert isinstance(mock_connector, MockSAPConnector)
        
        # Test factory convenience method
        mock_connector2 = factory.create_connector(ERPType.SAP, mock_sap_config, use_mock=True)
        assert isinstance(mock_connector2, MockSAPConnector)
    
    def test_erp_connector_factory_sap_config_validation(self):
        """Test SAP configuration validation in factory"""
        factory = ERPConnectorFactory()
        
        # Test missing required fields for OAuth
        invalid_config = {
            'host': 'test.sap.com',
            'use_oauth': True
            # Missing client_id and client_secret
        }
        
        with pytest.raises(ValueError, match="Missing required field 'client_id'"):
            factory.create_connector(ERPType.SAP, invalid_config)
        
        # Test valid OAuth config
        valid_oauth_config = {
            'host': 'test.sap.com',
            'client_id': 'test_client',
            'client_secret': 'test_secret',
            'use_oauth': True,
            'use_mock': True
        }
        
        connector = factory.create_connector(ERPType.SAP, valid_oauth_config)
        assert connector is not None
        
        # Test valid basic auth config
        valid_basic_config = {
            'host': 'test.sap.com',
            'username': 'test_user',
            'password': 'test_password',
            'use_oauth': False,
            'use_mock': True
        }
        
        connector = factory.create_connector(ERPType.SAP, valid_basic_config)
        assert connector is not None
    
    @pytest.mark.asyncio
    async def test_erp_connector_factory_test_all_connectors(self):
        """Test factory's test all connectors functionality"""
        factory = ERPConnectorFactory()
        
        test_results = await factory.test_all_connectors()
        
        assert isinstance(test_results, dict)
        assert 'sap_production' in test_results or 'sap_mock' in test_results
        
        if 'sap_mock' in test_results:
            sap_mock_result = test_results['sap_mock']
            assert sap_mock_result['available'] == True
            assert sap_mock_result['connector_class'] == 'MockSAPConnector'
            assert sap_mock_result['erp_type'] == 'sap'
            assert 'supported_features' in sap_mock_result
    
    @pytest.mark.asyncio
    async def test_integration_end_to_end_workflow(self, mock_sap_config, sample_billing_document):
        """Test complete end-to-end integration workflow"""
        # Step 1: Create connector through factory
        factory = ERPConnectorFactory()
        connector = factory.create_sap_connector(mock_sap_config, use_mock=True)
        
        # Step 2: Test connection
        connection_result = await connector.test_connection()
        assert connection_result.success == True
        
        # Step 3: Authenticate
        auth_result = await connector.authenticate()
        assert auth_result == True
        
        # Step 4: Get invoices
        invoices = await connector.get_invoices(page=1, page_size=5)
        assert len(invoices['invoices']) > 0
        
        # Step 5: Transform invoice data
        first_invoice = invoices['invoices'][0]
        transformation_result = await connector.transform_to_firs_format(first_invoice)
        
        assert transformation_result['firs_invoice'] is not None
        assert transformation_result['transformation_metadata'] is not None
        
        # Step 6: Validate FIRS compliance
        validation_result = await connector.validate_invoice_data(first_invoice)
        assert validation_result['is_valid'] == True
        
        # Step 7: Test company and tax info
        company_info = await connector.get_company_info()
        assert company_info['name'] is not None
        
        tax_config = await connector.get_tax_configuration()
        assert tax_config['country'] == 'NG'
        assert len(tax_config['taxes']) > 0
        
        # Step 8: Disconnect
        disconnect_result = await connector.disconnect()
        assert disconnect_result == True
    
    def test_sap_integration_error_handling(self, mock_sap_config):
        """Test error handling in SAP integration"""
        # Test with invalid configuration
        invalid_config = {
            'host': '',  # Empty host
            'use_mock': True
        }
        
        factory = ERPConnectorFactory()
        
        with pytest.raises(ValueError):
            factory.create_connector(ERPType.SAP, invalid_config)
        
        # Test with unsupported ERP type
        with pytest.raises(Exception):
            factory.create_connector('unsupported_erp', mock_sap_config)
    
    def test_sap_integration_mock_data_quality(self, mock_sap_config):
        """Test quality of mock data generated"""
        connector = MockSAPConnector(mock_sap_config)
        
        # Test mock data summary
        mock_summary = connector.get_mock_data_summary()
        
        assert mock_summary['mock_invoices'] > 0
        assert mock_summary['mock_partners'] > 0
        assert mock_summary['mock_products'] > 0
        assert 'date_range' in mock_summary
        assert 'document_types' in mock_summary
        assert 'currencies' in mock_summary
        assert 'mock_features' in mock_summary
        
        # Verify data consistency
        assert len(mock_summary['document_types']) > 0
        assert 'NGN' in mock_summary['currencies']
        assert 'billing_document_api' in mock_summary['mock_features']
    
    @pytest.mark.asyncio
    async def test_performance_considerations(self, mock_sap_config):
        """Test performance aspects of SAP integration"""
        connector = MockSAPConnector(mock_sap_config)
        await connector.authenticate()
        
        # Test pagination performance
        start_time = datetime.now()
        invoices = await connector.get_invoices(page=1, page_size=100)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        assert processing_time < 5.0  # Should complete within 5 seconds
        assert len(invoices['invoices']) <= 100
        
        # Test search performance
        start_time = datetime.now()
        search_result = await connector.search_invoices('9000', page=1, page_size=50)
        end_time = datetime.now()
        
        search_time = (end_time - start_time).total_seconds()
        assert search_time < 3.0  # Should complete within 3 seconds
    
    def test_sap_integration_security_considerations(self, mock_sap_config):
        """Test security aspects of SAP integration"""
        # Test OAuth configuration
        oauth_client = SAPOAuthClient(mock_sap_config)
        
        # Test secure token generation
        state = oauth_client.generate_state()
        assert len(state) >= 32  # Should be at least 32 characters
        
        verifier, challenge = oauth_client.generate_pkce_pair()
        assert len(verifier) >= 43  # PKCE verifier should be at least 43 characters
        assert len(challenge) >= 43  # PKCE challenge should be at least 43 characters
        assert verifier != challenge  # Should be different
        
        # Test nonce generation
        nonce = oauth_client.generate_nonce()
        assert len(nonce) >= 16  # Should be at least 16 characters
        
        # Test token info doesn't expose sensitive data
        token_info = oauth_client.get_token_info()
        assert 'client_secret' not in token_info
        assert 'access_token' not in token_info
        assert 'refresh_token' not in token_info
    
    def test_sap_integration_compliance_validation(self, sample_billing_document):
        """Test FIRS compliance validation"""
        # Test mapping compliance
        firs_mapping = SAPFIRSMapping.transform_billing_document_to_ubl(sample_billing_document)
        
        # Test validation
        compliance_result = SAPFIRSMapping.validate_firs_compliance(firs_mapping)
        
        assert 'is_valid' in compliance_result
        assert 'errors' in compliance_result
        assert 'warnings' in compliance_result
        
        # Test required fields are present
        required_fields = ['ID', 'IssueDate', 'InvoiceTypeCode', 'DocumentCurrencyCode']
        for field in required_fields:
            assert field in firs_mapping
    
    @pytest.mark.asyncio
    async def test_sap_integration_resilience(self, mock_sap_config):
        """Test resilience and error recovery"""
        connector = MockSAPConnector(mock_sap_config)
        await connector.authenticate()
        
        # Test handling of invalid invoice ID
        try:
            await connector.get_invoice_by_id('INVALID_ID')
            assert False, "Should have raised an exception"
        except Exception as e:
            assert 'not found' in str(e).lower()
        
        # Test handling of empty search results
        empty_result = await connector.search_invoices('NONEXISTENT_TERM')
        assert empty_result['total'] == 0
        assert len(empty_result['invoices']) == 0
        
        # Test connection status tracking
        assert connector.is_healthy() == True
        
        # Test health check
        health_result = await connector.health_check()
        assert health_result['healthy'] == True
        assert health_result['status'] == 'healthy'


if __name__ == '__main__':
    """
    Run tests manually for development
    """
    import asyncio
    
    async def run_basic_tests():
        """Run basic tests manually"""
        print("Running SAP Integration Tests...")
        
        # Test configuration
        config = {
            'host': 'test-sap.taxpoynt.com',
            'client': '100',
            'client_id': 'taxpoynt_client',
            'client_secret': 'test_secret',
            'use_oauth': True,
            'use_mock': True
        }
        
        # Test factory
        factory = ERPConnectorFactory()
        print(f"Supported ERP types: {factory.get_supported_erp_types()}")
        
        # Test connector creation
        connector = factory.create_sap_connector(config, use_mock=True)
        print(f"Created connector: {connector.__class__.__name__}")
        
        # Test connection
        test_result = await connector.test_connection()
        print(f"Connection test: {test_result.success}")
        
        # Test authentication
        auth_result = await connector.authenticate()
        print(f"Authentication: {auth_result}")
        
        # Test invoice retrieval
        invoices = await connector.get_invoices(page=1, page_size=5)
        print(f"Retrieved {len(invoices['invoices'])} invoices")
        
        # Test transformation
        if invoices['invoices']:
            first_invoice = invoices['invoices'][0]
            transform_result = await connector.transform_to_firs_format(first_invoice)
            print(f"Transformation successful: {transform_result.get('firs_invoice') is not None}")
        
        print("Basic tests completed successfully!")
    
    # Run tests
    asyncio.run(run_basic_tests())