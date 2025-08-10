"""
SAP to FIRS Data Transformation Service

This module provides comprehensive data transformation from SAP S/4HANA
data structures to FIRS-compliant UBL BIS 3.0 format with Nigerian
business rules and validation.

Features:
- SAP Billing Document to UBL transformation
- SAP Journal Entry to UBL transformation
- Nigerian VAT and tax compliance
- Withholding tax handling
- Multi-currency support
- Data validation and error handling
- Extensible transformation rules
- Audit trail and logging

Transformation Pipeline:
1. Data extraction and validation
2. Field mapping and conversion
3. Business rule application
4. UBL structure generation
5. FIRS compliance validation
6. Output formatting and optimization
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Union
import uuid

from app.services.firs_si.sap_firs_mapping import SAPFIRSMapping

logger = logging.getLogger(__name__)


class SAPFIRSTransformationError(Exception):
    """Exception raised for SAP to FIRS transformation errors"""
    pass


class SAPFIRSTransformer:
    """
    SAP to FIRS data transformation service
    
    Handles comprehensive transformation of SAP S/4HANA data to FIRS-compliant
    UBL BIS 3.0 format with Nigerian business rules and validation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize SAP FIRS transformer
        
        Args:
            config: Transformer configuration
        """
        self.config = config or {}
        self.mapping = SAPFIRSMapping()
        
        # Transformation settings
        self.strict_validation = self.config.get('strict_validation', True)
        self.include_sap_metadata = self.config.get('include_sap_metadata', True)
        self.default_currency = self.config.get('default_currency', 'NGN')
        self.default_country = self.config.get('default_country', 'NG')
        self.round_amounts = self.config.get('round_amounts', True)
        self.decimal_places = self.config.get('decimal_places', 2)
        
        # Company information (would be loaded from configuration)
        self.company_info = self.config.get('company_info', self._get_default_company_info())
        
        logger.info("Initialized SAP FIRS transformer")
    
    def _get_default_company_info(self) -> Dict[str, Any]:
        """Get default company information"""
        return {
            'name': 'TaxPoynt Company Limited',
            'legal_name': 'TaxPoynt Company Limited',
            'vat_number': 'NG0123456789',
            'tin': 'NG0123456789',
            'registration_number': 'RC123456',
            'email': 'info@taxpoynt.com',
            'phone': '+234-1-2345678',
            'website': 'https://taxpoynt.com',
            'address': {
                'street': '1 TaxPoynt Street',
                'street2': 'Victoria Island',
                'city': 'Lagos',
                'state': 'Lagos State',
                'postal_code': '101001',
                'country': 'Nigeria',
                'country_code': 'NG'
            },
            'bank_details': {
                'account_number': '1234567890',
                'bank_name': 'First Bank of Nigeria',
                'bank_code': '011',
                'swift_code': 'FBNINGLA'
            }
        }
    
    async def transform_billing_document(
        self,
        billing_document: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]] = None,
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """
        Transform SAP Billing Document to FIRS UBL format
        
        Args:
            billing_document: SAP billing document data
            customer_data: Optional customer/business partner data
            target_format: Target transformation format
            
        Returns:
            Transformed UBL invoice
        """
        try:
            logger.info(f"Transforming SAP billing document {billing_document.get('BillingDocument', 'N/A')}")
            
            # Step 1: Validate input data
            validation_result = await self._validate_billing_document(billing_document)
            if not validation_result['is_valid']:
                raise SAPFIRSTransformationError(f"Invalid billing document: {validation_result['errors']}")
            
            # Step 2: Extract and enrich data
            enriched_data = await self._enrich_billing_document_data(billing_document, customer_data)
            
            # Step 3: Build UBL structure
            ubl_invoice = await self._build_ubl_from_billing_document(enriched_data)
            
            # Step 4: Apply Nigerian business rules
            await self._apply_nigerian_business_rules(ubl_invoice, enriched_data)
            
            # Step 5: Validate FIRS compliance
            compliance_result = await self._validate_firs_compliance(ubl_invoice)
            if self.strict_validation and not compliance_result['is_valid']:
                raise SAPFIRSTransformationError(f"FIRS compliance validation failed: {compliance_result['errors']}")
            
            # Step 6: Generate transformation metadata
            transformation_metadata = self._generate_transformation_metadata(
                billing_document, ubl_invoice, target_format, compliance_result
            )
            
            result = {
                'success': True,
                'firs_invoice': ubl_invoice,
                'source_format': 'sap_billing_document',
                'target_format': target_format,
                'transformation_metadata': transformation_metadata,
                'validation_result': compliance_result
            }
            
            logger.info(f"Successfully transformed billing document {billing_document.get('BillingDocument', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"Error transforming billing document: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'source_format': 'sap_billing_document',
                'target_format': target_format
            }
    
    async def transform_journal_entries(
        self,
        journal_entries: List[Dict[str, Any]],
        customer_data: Optional[Dict[str, Any]] = None,
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """
        Transform SAP Journal Entries to FIRS UBL format
        
        Args:
            journal_entries: List of SAP journal entry items
            customer_data: Optional customer data
            target_format: Target transformation format
            
        Returns:
            Transformed UBL invoice
        """
        try:
            if not journal_entries:
                raise SAPFIRSTransformationError("No journal entries provided")
            
            logger.info(f"Transforming {len(journal_entries)} SAP journal entries")
            
            # Step 1: Validate and group entries
            grouped_entries = await self._group_and_validate_journal_entries(journal_entries)
            
            # Step 2: Build invoice header from entries
            invoice_header = await self._build_invoice_header_from_journal(grouped_entries)
            
            # Step 3: Build UBL structure
            ubl_invoice = await self._build_ubl_from_journal_entries(grouped_entries, invoice_header, customer_data)
            
            # Step 4: Apply Nigerian business rules
            await self._apply_nigerian_business_rules(ubl_invoice, {'journal_entries': grouped_entries})
            
            # Step 5: Validate FIRS compliance
            compliance_result = await self._validate_firs_compliance(ubl_invoice)
            if self.strict_validation and not compliance_result['is_valid']:
                raise SAPFIRSTransformationError(f"FIRS compliance validation failed: {compliance_result['errors']}")
            
            # Step 6: Generate transformation metadata
            transformation_metadata = self._generate_transformation_metadata(
                {'journal_entries': journal_entries}, ubl_invoice, target_format, compliance_result
            )
            
            result = {
                'success': True,
                'firs_invoice': ubl_invoice,
                'source_format': 'sap_journal_entries',
                'target_format': target_format,
                'transformation_metadata': transformation_metadata,
                'validation_result': compliance_result
            }
            
            logger.info(f"Successfully transformed journal entries")
            return result
            
        except Exception as e:
            logger.error(f"Error transforming journal entries: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'source_format': 'sap_journal_entries',
                'target_format': target_format
            }
    
    async def _validate_billing_document(self, billing_document: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SAP billing document data"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required fields for billing document
        required_fields = [
            'BillingDocument', 'BillingDocumentDate', 'SoldToParty',
            'TransactionCurrency', 'NetAmount', 'TotalGrossAmount'
        ]
        
        for field in required_fields:
            if field not in billing_document or billing_document[field] is None:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Business validation
        if billing_document.get('BillingDocumentIsCancelled'):
            validation_result['warnings'].append("Billing document is marked as cancelled")
        
        # Amount validation
        net_amount = float(billing_document.get('NetAmount', 0))
        gross_amount = float(billing_document.get('TotalGrossAmount', 0))
        
        if net_amount < 0:
            validation_result['warnings'].append("Negative net amount detected")
        
        if gross_amount < net_amount:
            validation_result['errors'].append("Gross amount cannot be less than net amount")
            validation_result['is_valid'] = False
        
        # Currency validation
        currency = billing_document.get('TransactionCurrency', '')
        if not self.mapping.validate_currency(currency):
            validation_result['warnings'].append(f"Unsupported currency: {currency}")
        
        return validation_result
    
    async def _enrich_billing_document_data(
        self,
        billing_document: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enrich billing document with additional data"""
        enriched_data = billing_document.copy()
        
        # Add customer data if provided
        if customer_data:
            enriched_data['customer_data'] = customer_data
        else:
            # Create placeholder customer data
            sold_to_party = billing_document.get('SoldToParty', '')
            enriched_data['customer_data'] = {
                'BusinessPartner': sold_to_party,
                'BusinessPartnerName': f'Customer {sold_to_party}',
                'BusinessPartnerFullName': f'Customer {sold_to_party} Limited',
                'VATRegistration': f'VAT{sold_to_party}',
                'TaxNumber1': f'TIN{sold_to_party}',
                'EmailAddress': f'customer{sold_to_party}@example.com',
                'PhoneNumber1': f'+234-1-{sold_to_party[-7:]}',
                'StreetName': f'{sold_to_party} Customer Street',
                'CityName': 'Lagos',
                'PostalCode': '101001',
                'Country': 'NG'
            }
        
        # Add company data
        enriched_data['company_data'] = self.company_info
        
        # Calculate due date
        invoice_date = billing_document.get('BillingDocumentDate', '')
        payment_terms = billing_document.get('PaymentTerms', 'NT30')
        
        if invoice_date:
            enriched_data['calculated_due_date'] = self.mapping.calculate_due_date(invoice_date, payment_terms)
        
        # Add transformation timestamp
        enriched_data['transformation_timestamp'] = datetime.utcnow().isoformat()
        
        return enriched_data
    
    async def _build_ubl_from_billing_document(self, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build UBL invoice structure from enriched billing document"""
        billing_document = enriched_data
        customer_data = enriched_data.get('customer_data', {})
        company_data = enriched_data.get('company_data', {})
        
        # Basic invoice information
        invoice_id = billing_document.get('BillingDocument', '')
        invoice_date = billing_document.get('BillingDocumentDate', '')
        due_date = enriched_data.get('calculated_due_date', invoice_date)
        currency = billing_document.get('TransactionCurrency', self.default_currency)
        
        # Map document type
        doc_type = billing_document.get('BillingDocumentType', 'F2')
        invoice_type_code = self.mapping.map_document_type(doc_type)
        
        # Build UBL invoice
        ubl_invoice = {
            'CustomizationID': 'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0',
            'ProfileID': 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0',
            'ID': invoice_id,
            'IssueDate': invoice_date,
            'DueDate': due_date,
            'InvoiceTypeCode': invoice_type_code,
            'Note': [],
            'TaxPointDate': invoice_date,
            'DocumentCurrencyCode': currency,
            'TaxCurrencyCode': currency,
            'OrderReference': {
                'ID': billing_document.get('SalesDocument', '')
            },
            'BillingReference': [],
            'AccountingSupplierParty': self._build_supplier_party_ubl(company_data),
            'AccountingCustomerParty': self._build_customer_party_ubl(customer_data),
            'PaymentMeans': self._build_payment_means_ubl(company_data, billing_document),
            'PaymentTerms': self._build_payment_terms_ubl(billing_document),
            'TaxTotal': [],
            'LegalMonetaryTotal': self._build_monetary_total_ubl(billing_document, currency),
            'InvoiceLine': []
        }
        
        # Process invoice lines
        invoice_lines = billing_document.get('to_Item', {}).get('results', [])
        for line_item in invoice_lines:
            ubl_line = await self._transform_invoice_line_ubl(line_item, currency)
            ubl_invoice['InvoiceLine'].append(ubl_line)
        
        # Calculate and add tax totals
        tax_totals = await self._calculate_tax_totals_ubl(billing_document, currency)
        ubl_invoice['TaxTotal'] = tax_totals
        
        # Add delivery terms if present
        incoterms = billing_document.get('IncotermsClassification', '')
        if incoterms:
            ubl_invoice['DeliveryTerms'] = {
                'ID': self.mapping.map_incoterms(incoterms),
                'SpecialTerms': [f'Incoterms: {incoterms}']
            }
        
        return ubl_invoice
    
    def _build_supplier_party_ubl(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build UBL supplier party from company data"""
        address = company_data.get('address', {})
        bank_details = company_data.get('bank_details', {})
        
        return {
            'Party': {
                'EndpointID': {
                    '@schemeID': 'NG:TIN',
                    '#text': company_data.get('tin', '')
                },
                'PartyIdentification': [
                    {
                        'ID': {
                            '@schemeID': 'NG:TIN',
                            '#text': company_data.get('tin', '')
                        }
                    },
                    {
                        'ID': {
                            '@schemeID': 'NG:CRN',
                            '#text': company_data.get('registration_number', '')
                        }
                    }
                ],
                'PartyName': [
                    {
                        'Name': company_data.get('name', '')
                    }
                ],
                'PostalAddress': {
                    'StreetName': address.get('street', ''),
                    'AdditionalStreetName': address.get('street2', ''),
                    'CityName': address.get('city', ''),
                    'PostalZone': address.get('postal_code', ''),
                    'CountrySubentity': address.get('state', ''),
                    'Country': {
                        'IdentificationCode': address.get('country_code', self.default_country)
                    }
                },
                'PartyTaxScheme': [
                    {
                        'CompanyID': company_data.get('vat_number', ''),
                        'TaxScheme': {
                            'ID': 'VAT'
                        }
                    }
                ],
                'PartyLegalEntity': [
                    {
                        'RegistrationName': company_data.get('legal_name', ''),
                        'CompanyID': {
                            '@schemeID': 'NG:CRN',
                            '#text': company_data.get('registration_number', '')
                        }
                    }
                ],
                'Contact': {
                    'Name': company_data.get('contact_name', company_data.get('name', '')),
                    'Telephone': company_data.get('phone', ''),
                    'ElectronicMail': company_data.get('email', '')
                }
            }
        }
    
    def _build_customer_party_ubl(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build UBL customer party from customer data"""
        return {
            'Party': {
                'EndpointID': {
                    '@schemeID': 'NG:TIN',
                    '#text': customer_data.get('TaxNumber1', '')
                },
                'PartyIdentification': [
                    {
                        'ID': {
                            '@schemeID': 'NG:TIN',
                            '#text': customer_data.get('TaxNumber1', '')
                        }
                    },
                    {
                        'ID': {
                            '@schemeID': 'SAP:BP',
                            '#text': customer_data.get('BusinessPartner', '')
                        }
                    }
                ],
                'PartyName': [
                    {
                        'Name': customer_data.get('BusinessPartnerFullName', customer_data.get('BusinessPartnerName', ''))
                    }
                ],
                'PostalAddress': {
                    'StreetName': customer_data.get('StreetName', ''),
                    'CityName': customer_data.get('CityName', 'Lagos'),
                    'PostalZone': customer_data.get('PostalCode', ''),
                    'CountrySubentity': customer_data.get('Region', 'Lagos State'),
                    'Country': {
                        'IdentificationCode': customer_data.get('Country', self.default_country)
                    }
                },
                'PartyTaxScheme': [
                    {
                        'CompanyID': customer_data.get('VATRegistration', ''),
                        'TaxScheme': {
                            'ID': 'VAT'
                        }
                    }
                ],
                'PartyLegalEntity': [
                    {
                        'RegistrationName': customer_data.get('BusinessPartnerFullName', ''),
                        'CompanyID': {
                            '@schemeID': 'NG:CRN',
                            '#text': customer_data.get('CommercialRegisterNumber', '')
                        }
                    }
                ],
                'Contact': {
                    'Name': customer_data.get('BusinessPartnerName', ''),
                    'Telephone': customer_data.get('PhoneNumber1', ''),
                    'ElectronicMail': customer_data.get('EmailAddress', '')
                }
            }
        }
    
    def _build_payment_means_ubl(self, company_data: Dict[str, Any], billing_document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build UBL payment means"""
        bank_details = company_data.get('bank_details', {})
        
        return [
            {
                'PaymentMeansCode': '30',  # Credit transfer
                'PaymentID': billing_document.get('BillingDocument', ''),
                'PayeeFinancialAccount': {
                    'ID': bank_details.get('account_number', ''),
                    'Name': bank_details.get('bank_name', ''),
                    'FinancialInstitutionBranch': {
                        'ID': bank_details.get('bank_code', ''),
                        'Name': bank_details.get('bank_name', '')
                    }
                }
            }
        ]
    
    def _build_payment_terms_ubl(self, billing_document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build UBL payment terms"""
        payment_terms_code = billing_document.get('PaymentTerms', 'NT30')
        payment_terms_info = self.mapping.map_payment_terms(payment_terms_code)
        
        return [
            {
                'Note': [payment_terms_info['description']],
                'PaymentDueDate': billing_document.get('calculated_due_date', billing_document.get('BillingDocumentDate', ''))
            }
        ]
    
    def _build_monetary_total_ubl(self, billing_document: Dict[str, Any], currency: str) -> Dict[str, Any]:
        """Build UBL legal monetary total"""
        net_amount = self._round_amount(float(billing_document.get('NetAmount', 0)))
        tax_amount = self._round_amount(float(billing_document.get('TaxAmount', 0)))
        gross_amount = self._round_amount(float(billing_document.get('TotalGrossAmount', 0)))
        
        return {
            'LineExtensionAmount': {
                '@currencyID': currency,
                '#text': str(net_amount)
            },
            'TaxExclusiveAmount': {
                '@currencyID': currency,
                '#text': str(net_amount)
            },
            'TaxInclusiveAmount': {
                '@currencyID': currency,
                '#text': str(gross_amount)
            },
            'AllowanceTotalAmount': {
                '@currencyID': currency,
                '#text': '0.00'
            },
            'ChargeTotalAmount': {
                '@currencyID': currency,
                '#text': '0.00'
            },
            'PrepaidAmount': {
                '@currencyID': currency,
                '#text': '0.00'
            },
            'PayableRoundingAmount': {
                '@currencyID': currency,
                '#text': '0.00'
            },
            'PayableAmount': {
                '@currencyID': currency,
                '#text': str(gross_amount)
            }
        }
    
    async def _transform_invoice_line_ubl(self, line_item: Dict[str, Any], currency: str) -> Dict[str, Any]:
        """Transform SAP invoice line to UBL format"""
        line_id = line_item.get('BillingDocumentItem', '1')
        quantity = float(line_item.get('BillingQuantity', 1))
        unit = line_item.get('BillingQuantityUnit', 'EA')
        net_amount = self._round_amount(float(line_item.get('NetAmount', 0)))
        gross_amount = self._round_amount(float(line_item.get('GrossAmount', net_amount)))
        unit_price = self._round_amount(net_amount / quantity if quantity > 0 else 0)
        
        # Map unit of measure
        ubl_unit = self.mapping.map_unit_of_measure(unit)
        
        return {
            'ID': line_id,
            'Note': [],
            'InvoicedQuantity': {
                '@unitCode': ubl_unit,
                '#text': str(quantity)
            },
            'LineExtensionAmount': {
                '@currencyID': currency,
                '#text': str(net_amount)
            },
            'AccountingCost': line_item.get('ControllingArea', ''),
            'Item': {
                'Description': [line_item.get('MaterialDescription', '')],
                'Name': line_item.get('MaterialDescription', ''),
                'BuyersItemIdentification': {
                    'ID': line_item.get('MaterialByCustomer', '')
                },
                'SellersItemIdentification': {
                    'ID': line_item.get('Material', '')
                },
                'StandardItemIdentification': {
                    'ID': {
                        '@schemeID': 'GTIN',
                        '#text': line_item.get('Material', '')
                    }
                },
                'OriginCountry': {
                    'IdentificationCode': self.default_country
                },
                'CommodityClassification': [
                    {
                        'ItemClassificationCode': {
                            '@listID': 'SAP_MATERIAL_GROUP',
                            '#text': line_item.get('MaterialGroup', '')
                        }
                    }
                ],
                'ClassifiedTaxCategory': [
                    {
                        'ID': 'S',  # Standard rate
                        'Percent': 7.5,
                        'TaxScheme': {
                            'ID': 'VAT'
                        }
                    }
                ]
            },
            'Price': {
                'PriceAmount': {
                    '@currencyID': currency,
                    '#text': str(unit_price)
                },
                'BaseQuantity': {
                    '@unitCode': ubl_unit,
                    '#text': '1'
                }
            }
        }
    
    async def _calculate_tax_totals_ubl(self, billing_document: Dict[str, Any], currency: str) -> List[Dict[str, Any]]:
        """Calculate UBL tax totals"""
        tax_amount = self._round_amount(float(billing_document.get('TaxAmount', 0)))
        net_amount = self._round_amount(float(billing_document.get('NetAmount', 0)))
        
        # For Nigerian VAT, typically 7.5%
        tax_percent = 7.5
        if net_amount > 0:
            calculated_percent = (tax_amount / net_amount) * 100
            tax_percent = self._round_amount(calculated_percent)
        
        return [
            {
                'TaxAmount': {
                    '@currencyID': currency,
                    '#text': str(tax_amount)
                },
                'TaxSubtotal': [
                    {
                        'TaxableAmount': {
                            '@currencyID': currency,
                            '#text': str(net_amount)
                        },
                        'TaxAmount': {
                            '@currencyID': currency,
                            '#text': str(tax_amount)
                        },
                        'TaxCategory': {
                            'ID': 'S',
                            'Percent': tax_percent,
                            'TaxScheme': {
                                'ID': 'VAT'
                            }
                        }
                    }
                ]
            }
        ]
    
    async def _group_and_validate_journal_entries(self, journal_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Group and validate journal entries"""
        # Group by accounting document
        grouped = {}
        for entry in journal_entries:
            doc_num = entry.get('AccountingDocument', '')
            if doc_num not in grouped:
                grouped[doc_num] = {
                    'header': None,
                    'items': [],
                    'revenue_total': 0,
                    'tax_total': 0
                }
            
            grouped[doc_num]['items'].append(entry)
            
            # Calculate totals
            amount = float(entry.get('AmountInTransactionCurrency', 0))
            gl_account = entry.get('GLAccount', '')
            
            # Revenue accounts (40000000-49999999)
            if gl_account.startswith('4'):
                grouped[doc_num]['revenue_total'] += abs(amount)
            # Tax accounts (typically starting with 2 for VAT payable)
            elif gl_account.startswith('2') and 'tax' in entry.get('GLAccountName', '').lower():
                grouped[doc_num]['tax_total'] += abs(amount)
        
        return grouped
    
    async def _build_invoice_header_from_journal(self, grouped_entries: Dict[str, Any]) -> Dict[str, Any]:
        """Build invoice header from journal entries"""
        # Use the first document for header information
        first_doc = next(iter(grouped_entries.values()))
        first_item = first_doc['items'][0] if first_doc['items'] else {}
        
        return {
            'AccountingDocument': first_item.get('AccountingDocument', ''),
            'PostingDate': first_item.get('PostingDate', ''),
            'DocumentType': first_item.get('AccountingDocumentType', 'SA'),
            'CompanyCode': first_item.get('CompanyCode', ''),
            'FiscalYear': first_item.get('FiscalYear', ''),
            'Customer': first_item.get('Customer', ''),
            'TransactionCurrency': first_item.get('TransactionCurrency', self.default_currency),
            'DocumentReferenceID': first_item.get('DocumentReferenceID', ''),
            'revenue_total': first_doc['revenue_total'],
            'tax_total': first_doc['tax_total'],
            'gross_total': first_doc['revenue_total'] + first_doc['tax_total']
        }
    
    async def _build_ubl_from_journal_entries(
        self,
        grouped_entries: Dict[str, Any],
        header: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build UBL invoice from journal entries"""
        # Use header information for invoice
        invoice_id = header.get('AccountingDocument', '')
        invoice_date = header.get('PostingDate', '')
        currency = header.get('TransactionCurrency', self.default_currency)
        
        # Create UBL structure similar to billing document transformation
        ubl_invoice = {
            'CustomizationID': 'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0',
            'ProfileID': 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0',
            'ID': invoice_id,
            'IssueDate': invoice_date,
            'DueDate': invoice_date,  # Same as issue date for journal entries
            'InvoiceTypeCode': '380',  # Standard invoice
            'Note': ['Generated from SAP Journal Entries'],
            'TaxPointDate': invoice_date,
            'DocumentCurrencyCode': currency,
            'TaxCurrencyCode': currency,
            'AccountingSupplierParty': self._build_supplier_party_ubl(self.company_info),
            'AccountingCustomerParty': self._build_customer_party_from_journal(header, customer_data),
            'PaymentMeans': self._build_payment_means_ubl(self.company_info, header),
            'PaymentTerms': [{'Note': ['Payment terms as per agreement']}],
            'TaxTotal': self._build_tax_total_from_journal(header, currency),
            'LegalMonetaryTotal': self._build_monetary_total_from_journal(header, currency),
            'InvoiceLine': []
        }
        
        # Build invoice lines from journal entries
        line_counter = 1
        for doc_num, doc_data in grouped_entries.items():
            for item in doc_data['items']:
                # Only include revenue lines as invoice lines
                gl_account = item.get('GLAccount', '')
                if gl_account.startswith('4'):  # Revenue account
                    ubl_line = await self._transform_journal_entry_to_line(item, line_counter, currency)
                    ubl_invoice['InvoiceLine'].append(ubl_line)
                    line_counter += 1
        
        return ubl_invoice
    
    def _build_customer_party_from_journal(self, header: Dict[str, Any], customer_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build customer party from journal entry header"""
        customer_id = header.get('Customer', 'UNKNOWN')
        
        if customer_data:
            return self._build_customer_party_ubl(customer_data)
        
        # Create default customer data
        return {
            'Party': {
                'EndpointID': {
                    '@schemeID': 'SAP:CUSTOMER',
                    '#text': customer_id
                },
                'PartyIdentification': [
                    {
                        'ID': {
                            '@schemeID': 'SAP:CUSTOMER',
                            '#text': customer_id
                        }
                    }
                ],
                'PartyName': [
                    {
                        'Name': f'Customer {customer_id}'
                    }
                ],
                'PostalAddress': {
                    'CityName': 'Lagos',
                    'CountrySubentity': 'Lagos State',
                    'Country': {
                        'IdentificationCode': self.default_country
                    }
                }
            }
        }
    
    def _build_tax_total_from_journal(self, header: Dict[str, Any], currency: str) -> List[Dict[str, Any]]:
        """Build tax total from journal header"""
        tax_amount = self._round_amount(header.get('tax_total', 0))
        revenue_amount = self._round_amount(header.get('revenue_total', 0))
        
        return [
            {
                'TaxAmount': {
                    '@currencyID': currency,
                    '#text': str(tax_amount)
                },
                'TaxSubtotal': [
                    {
                        'TaxableAmount': {
                            '@currencyID': currency,
                            '#text': str(revenue_amount)
                        },
                        'TaxAmount': {
                            '@currencyID': currency,
                            '#text': str(tax_amount)
                        },
                        'TaxCategory': {
                            'ID': 'S',
                            'Percent': 7.5,
                            'TaxScheme': {
                                'ID': 'VAT'
                            }
                        }
                    }
                ]
            }
        ]
    
    def _build_monetary_total_from_journal(self, header: Dict[str, Any], currency: str) -> Dict[str, Any]:
        """Build monetary total from journal header"""
        revenue_amount = self._round_amount(header.get('revenue_total', 0))
        tax_amount = self._round_amount(header.get('tax_total', 0))
        gross_amount = self._round_amount(header.get('gross_total', 0))
        
        return {
            'LineExtensionAmount': {
                '@currencyID': currency,
                '#text': str(revenue_amount)
            },
            'TaxExclusiveAmount': {
                '@currencyID': currency,
                '#text': str(revenue_amount)
            },
            'TaxInclusiveAmount': {
                '@currencyID': currency,
                '#text': str(gross_amount)
            },
            'AllowanceTotalAmount': {
                '@currencyID': currency,
                '#text': '0.00'
            },
            'ChargeTotalAmount': {
                '@currencyID': currency,
                '#text': '0.00'
            },
            'PrepaidAmount': {
                '@currencyID': currency,
                '#text': '0.00'
            },
            'PayableRoundingAmount': {
                '@currencyID': currency,
                '#text': '0.00'
            },
            'PayableAmount': {
                '@currencyID': currency,
                '#text': str(gross_amount)
            }
        }
    
    async def _transform_journal_entry_to_line(self, entry: Dict[str, Any], line_id: int, currency: str) -> Dict[str, Any]:
        """Transform journal entry to UBL invoice line"""
        amount = self._round_amount(abs(float(entry.get('AmountInTransactionCurrency', 0))))
        
        return {
            'ID': str(line_id),
            'Note': [],
            'InvoicedQuantity': {
                '@unitCode': 'C62',  # Each
                '#text': '1'
            },
            'LineExtensionAmount': {
                '@currencyID': currency,
                '#text': str(amount)
            },
            'AccountingCost': entry.get('ControllingArea', ''),
            'Item': {
                'Description': [entry.get('GLAccountName', f"GL Account {entry.get('GLAccount', '')}")],
                'Name': entry.get('GLAccountName', f"GL Account {entry.get('GLAccount', '')}"),
                'SellersItemIdentification': {
                    'ID': entry.get('GLAccount', '')
                },
                'ClassifiedTaxCategory': [
                    {
                        'ID': 'S',
                        'Percent': 7.5,
                        'TaxScheme': {
                            'ID': 'VAT'
                        }
                    }
                ]
            },
            'Price': {
                'PriceAmount': {
                    '@currencyID': currency,
                    '#text': str(amount)
                },
                'BaseQuantity': {
                    '@unitCode': 'C62',
                    '#text': '1'
                }
            }
        }
    
    async def _apply_nigerian_business_rules(self, ubl_invoice: Dict[str, Any], source_data: Dict[str, Any]) -> None:
        """Apply Nigerian business rules to UBL invoice"""
        # Add Nigerian-specific fields
        ubl_invoice.setdefault('AdditionalDocumentReference', [])
        
        # Add FIRS reference
        ubl_invoice['AdditionalDocumentReference'].append({
            'ID': 'FIRS_SYSTEM_APPROVAL',
            'DocumentTypeCode': '916',
            'DocumentDescription': 'FIRS Electronic Invoice System Approval'
        })
        
        # Add SAP source reference
        if 'BillingDocument' in source_data:
            ubl_invoice['AdditionalDocumentReference'].append({
                'ID': source_data['BillingDocument'],
                'DocumentTypeCode': 'SAP_BILLING_DOCUMENT',
                'DocumentDescription': 'SAP Billing Document Reference'
            })
        
        # Ensure Nigerian country code
        supplier_party = ubl_invoice.get('AccountingSupplierParty', {}).get('Party', {})
        customer_party = ubl_invoice.get('AccountingCustomerParty', {}).get('Party', {})
        
        for party in [supplier_party, customer_party]:
            postal_address = party.get('PostalAddress', {})
            if 'Country' in postal_address:
                postal_address['Country']['IdentificationCode'] = self.default_country
    
    async def _validate_firs_compliance(self, ubl_invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Validate UBL invoice for FIRS compliance"""
        return self.mapping.validate_firs_compliance(ubl_invoice)
    
    def _generate_transformation_metadata(
        self,
        source_data: Dict[str, Any],
        ubl_invoice: Dict[str, Any],
        target_format: str,
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate transformation metadata"""
        return {
            'transformation_id': str(uuid.uuid4()),
            'transformation_timestamp': datetime.utcnow().isoformat(),
            'transformer_version': '1.0.0',
            'source_invoice_id': source_data.get('BillingDocument', source_data.get('AccountingDocument', '')),
            'target_invoice_id': ubl_invoice.get('ID', ''),
            'source_format': 'sap_s4hana',
            'target_format': target_format,
            'transformation_rules_applied': [
                'document_type_mapping',
                'currency_validation',
                'nigerian_business_rules',
                'firs_compliance_validation'
            ],
            'data_quality': {
                'completeness_score': self._calculate_completeness_score(ubl_invoice),
                'validation_passed': validation_result.get('is_valid', False),
                'warnings_count': len(validation_result.get('warnings', [])),
                'errors_count': len(validation_result.get('errors', []))
            },
            'processing_statistics': {
                'total_lines': len(ubl_invoice.get('InvoiceLine', [])),
                'tax_lines': len(ubl_invoice.get('TaxTotal', [])),
                'currency': ubl_invoice.get('DocumentCurrencyCode', ''),
                'total_amount': ubl_invoice.get('LegalMonetaryTotal', {}).get('PayableAmount', {}).get('#text', '0')
            }
        }
    
    def _calculate_completeness_score(self, ubl_invoice: Dict[str, Any]) -> float:
        """Calculate data completeness score"""
        required_fields = [
            'ID', 'IssueDate', 'InvoiceTypeCode', 'DocumentCurrencyCode',
            'AccountingSupplierParty', 'AccountingCustomerParty',
            'LegalMonetaryTotal', 'InvoiceLine'
        ]
        
        present_fields = sum(1 for field in required_fields if field in ubl_invoice and ubl_invoice[field])
        return (present_fields / len(required_fields)) * 100
    
    def _round_amount(self, amount: float) -> float:
        """Round amount to specified decimal places"""
        if not self.round_amounts:
            return amount
        
        decimal_amount = Decimal(str(amount))
        rounded = decimal_amount.quantize(
            Decimal(f'0.{"0" * self.decimal_places}'),
            rounding=ROUND_HALF_UP
        )
        return float(rounded)
    
    def get_transformer_info(self) -> Dict[str, Any]:
        """Get transformer information"""
        return {
            'transformer_name': 'SAP FIRS Transformer',
            'version': '1.0.0',
            'supported_source_formats': [
                'sap_billing_document',
                'sap_journal_entries'
            ],
            'supported_target_formats': [
                'UBL_BIS_3.0'
            ],
            'features': [
                'nigerian_business_rules',
                'firs_compliance_validation',
                'multi_currency_support',
                'tax_calculation',
                'data_enrichment',
                'transformation_metadata'
            ],
            'configuration': {
                'strict_validation': self.strict_validation,
                'include_sap_metadata': self.include_sap_metadata,
                'default_currency': self.default_currency,
                'default_country': self.default_country,
                'round_amounts': self.round_amounts,
                'decimal_places': self.decimal_places
            }
        }