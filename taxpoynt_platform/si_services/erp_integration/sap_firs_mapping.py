"""
SAP to FIRS Data Mapping Rules for TaxPoynt eInvoice

This module provides comprehensive data mapping rules for transforming
SAP S/4HANA data to FIRS-compliant UBL BIS 3.0 format.

Key Mappings:
- SAP Document Types to FIRS Invoice Type Codes
- SAP Tax Codes to FIRS Tax Categories
- SAP Units of Measure to UBL Unit Codes
- SAP Payment Terms to FIRS Payment Terms
- SAP Business Partner Fields to UBL Party Fields
- SAP Pricing Elements to UBL Tax Information

FIRS Compliance Features:
- Nigerian VAT handling
- Withholding Tax mapping
- Currency code validation
- Document type validation
- Tax calculation verification
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class SAPFIRSMapping:
    """
    SAP to FIRS data mapping utility class
    
    Provides methods for transforming SAP S/4HANA data structures
    to FIRS-compliant UBL BIS 3.0 format with Nigerian business rules.
    """
    
    # SAP Document Type to FIRS Invoice Type Code mapping
    DOCUMENT_TYPE_MAPPING = {
        'F2': '380',    # Invoice -> Invoice
        'G2': '381',    # Credit Memo -> Credit Note
        'L2': '383',    # Debit Memo -> Debit Note
        'S1': '384',    # Cancellation -> Corrected Invoice
        'RE': '380',    # Returns Invoice -> Invoice
        'IG': '325',    # Pro Forma Invoice
        'IV': '326',    # Partial Invoice
        'AB': '380',    # Debit Memo Request -> Invoice
        'AG': '381',    # Credit Memo Request -> Credit Note
        'F5': '380',    # Invoice List -> Invoice
        'F8': '380'     # Cancelled Invoice -> Invoice
    }
    
    # SAP Tax Code to FIRS Tax Category mapping (Nigerian specific)
    TAX_CATEGORY_MAPPING = {
        'UTXJ': {          # Output VAT for Nigeria
            'id': 'S',
            'name': 'Standard Rate',
            'percent': 7.5,
            'tax_scheme_id': 'VAT',
            'tax_scheme_name': 'Nigerian VAT'
        },
        'UTXE': {          # VAT Exempt
            'id': 'E',
            'name': 'Exempt',
            'percent': 0.0,
            'tax_scheme_id': 'VAT',
            'tax_scheme_name': 'Nigerian VAT'
        },
        'UTXZ': {          # Zero-rated VAT
            'id': 'Z',
            'name': 'Zero Rate',
            'percent': 0.0,
            'tax_scheme_id': 'VAT',
            'tax_scheme_name': 'Nigerian VAT'
        },
        'WHVT': {          # Withholding VAT
            'id': 'WHT',
            'name': 'Withholding VAT',
            'percent': 5.0,
            'tax_scheme_id': 'WHT',
            'tax_scheme_name': 'Withholding Tax'
        },
        'WHTX': {          # General Withholding Tax
            'id': 'WHT',
            'name': 'Withholding Tax',
            'percent': 10.0,
            'tax_scheme_id': 'WHT',
            'tax_scheme_name': 'Withholding Tax'
        },
        'MWST': {          # General VAT
            'id': 'S',
            'name': 'Standard Rate',
            'percent': 7.5,
            'tax_scheme_id': 'VAT',
            'tax_scheme_name': 'Nigerian VAT'
        }
    }
    
    # SAP Unit of Measure to UBL Unit Code mapping
    UNIT_OF_MEASURE_MAPPING = {
        'EA': 'C62',    # Each -> Each
        'PC': 'C62',    # Piece -> Each
        'PCS': 'C62',   # Pieces -> Each
        'ST': 'C62',    # Set -> Each
        'KG': 'KGM',    # Kilogram -> Kilogram
        'G': 'GRM',     # Gram -> Gram
        'L': 'LTR',     # Liter -> Liter
        'ML': 'MLT',    # Milliliter -> Milliliter
        'M': 'MTR',     # Meter -> Meter
        'CM': 'CMT',    # Centimeter -> Centimeter
        'MM': 'MMT',    # Millimeter -> Millimeter
        'M2': 'MTK',    # Square Meter -> Square Meter
        'M3': 'MTQ',    # Cubic Meter -> Cubic Meter
        'H': 'HUR',     # Hour -> Hour
        'MIN': 'C26',   # Minute -> Minute
        'DAY': 'DAY',   # Day -> Day
        'WK': 'WEE',    # Week -> Week
        'MO': 'MON',    # Month -> Month
        'YR': 'ANN',    # Year -> Year
        'TON': 'TNE',   # Ton -> Tonne
        'LB': 'LBR',    # Pound -> Pound
        'OZ': 'ONZ',    # Ounce -> Ounce
        'FT': 'FOT',    # Foot -> Foot
        'IN': 'INH',    # Inch -> Inch
        'GAL': 'GLL',   # Gallon -> Gallon
        'QT': 'QT',     # Quart -> Quart
        'PT': 'PT',     # Pint -> Pint
        'BOX': 'BX',    # Box -> Box
        'CTN': 'CT',    # Carton -> Carton
        'PAL': 'PF',    # Pallet -> Pallet
        'BAG': 'BG',    # Bag -> Bag
        'CAN': 'CA',    # Can -> Can
        'BTL': 'BO',    # Bottle -> Bottle
        'TUB': 'TU',    # Tube -> Tube
        'PKG': 'PK',    # Package -> Package
        'ROL': 'RO',    # Roll -> Roll
        'SHT': 'EA',    # Sheet -> Each
        'PR': 'PR',     # Pair -> Pair
        'SET': 'C62',   # Set -> Each
        'KIT': 'C62',   # Kit -> Each
        'LOT': 'C62',   # Lot -> Each
        'DOZ': 'DZN',   # Dozen -> Dozen
        'GRS': 'GRO'    # Gross -> Gross
    }
    
    # SAP Payment Terms to FIRS Payment Terms mapping
    PAYMENT_TERMS_MAPPING = {
        'NT00': {
            'code': 'NET_0',
            'name': 'Due Immediately',
            'days': 0,
            'description': 'Payment due immediately'
        },
        'NT07': {
            'code': 'NET_7',
            'name': 'Net 7 Days',
            'days': 7,
            'description': 'Payment due within 7 days'
        },
        'NT15': {
            'code': 'NET_15',
            'name': 'Net 15 Days',
            'days': 15,
            'description': 'Payment due within 15 days'
        },
        'NT30': {
            'code': 'NET_30',
            'name': 'Net 30 Days',
            'days': 30,
            'description': 'Payment due within 30 days'
        },
        'NT45': {
            'code': 'NET_45',
            'name': 'Net 45 Days',
            'days': 45,
            'description': 'Payment due within 45 days'
        },
        'NT60': {
            'code': 'NET_60',
            'name': 'Net 60 Days',
            'days': 60,
            'description': 'Payment due within 60 days'
        },
        'NT90': {
            'code': 'NET_90',
            'name': 'Net 90 Days',
            'days': 90,
            'description': 'Payment due within 90 days'
        },
        'COD': {
            'code': 'COD',
            'name': 'Cash on Delivery',
            'days': 0,
            'description': 'Cash on delivery'
        },
        'CIA': {
            'code': 'CIA',
            'name': 'Cash in Advance',
            'days': -1,
            'description': 'Cash in advance'
        }
    }
    
    # SAP Incoterms to UBL Incoterms mapping
    INCOTERMS_MAPPING = {
        'EXW': 'EXW',   # Ex Works
        'FCA': 'FCA',   # Free Carrier
        'CPT': 'CPT',   # Carriage Paid To
        'CIP': 'CIP',   # Carriage and Insurance Paid To
        'DAT': 'DAT',   # Delivered At Terminal
        'DAP': 'DAP',   # Delivered At Place
        'DDP': 'DDP',   # Delivered Duty Paid
        'FAS': 'FAS',   # Free Alongside Ship
        'FOB': 'FOB',   # Free On Board
        'CFR': 'CFR',   # Cost and Freight
        'CIF': 'CIF'    # Cost, Insurance and Freight
    }
    
    # SAP Currency Codes (Nigerian focus)
    CURRENCY_MAPPING = {
        'NGN': 'NGN',   # Nigerian Naira
        'USD': 'USD',   # US Dollar
        'EUR': 'EUR',   # Euro
        'GBP': 'GBP',   # British Pound
        'JPY': 'JPY',   # Japanese Yen
        'CAD': 'CAD',   # Canadian Dollar
        'AUD': 'AUD',   # Australian Dollar
        'CHF': 'CHF',   # Swiss Franc
        'CNY': 'CNY',   # Chinese Yuan
        'ZAR': 'ZAR',   # South African Rand
        'GHS': 'GHS',   # Ghanaian Cedi
        'KES': 'KES',   # Kenyan Shilling
        'UGX': 'UGX',   # Ugandan Shilling
        'TZS': 'TZS',   # Tanzanian Shilling
        'ETB': 'ETB',   # Ethiopian Birr
        'EGP': 'EGP',   # Egyptian Pound
        'MAD': 'MAD'    # Moroccan Dirham
    }
    
    @classmethod
    def map_document_type(cls, sap_doc_type: str) -> str:
        """
        Map SAP document type to FIRS invoice type code
        
        Args:
            sap_doc_type: SAP document type (e.g., 'F2', 'G2')
            
        Returns:
            FIRS invoice type code (e.g., '380', '381')
        """
        mapped_type = cls.DOCUMENT_TYPE_MAPPING.get(sap_doc_type, '380')
        logger.debug(f"Mapped SAP document type {sap_doc_type} to FIRS type {mapped_type}")
        return mapped_type
    
    @classmethod
    def map_tax_category(cls, sap_tax_code: str, tax_rate: Optional[float] = None) -> Dict[str, Any]:
        """
        Map SAP tax code to FIRS tax category
        
        Args:
            sap_tax_code: SAP tax code (e.g., 'UTXJ', 'UTXE')
            tax_rate: Optional tax rate override
            
        Returns:
            FIRS tax category information
        """
        if sap_tax_code in cls.TAX_CATEGORY_MAPPING:
            tax_info = cls.TAX_CATEGORY_MAPPING[sap_tax_code].copy()
            
            # Override rate if provided
            if tax_rate is not None:
                tax_info['percent'] = float(tax_rate)
            
            logger.debug(f"Mapped SAP tax code {sap_tax_code} to FIRS category {tax_info['id']}")
            return tax_info
        else:
            # Default to standard rate for unknown tax codes
            logger.warning(f"Unknown SAP tax code {sap_tax_code}, using default standard rate")
            return {
                'id': 'S',
                'name': 'Standard Rate',
                'percent': tax_rate if tax_rate is not None else 7.5,
                'tax_scheme_id': 'VAT',
                'tax_scheme_name': 'Nigerian VAT'
            }
    
    @classmethod
    def map_unit_of_measure(cls, sap_unit: str) -> str:
        """
        Map SAP unit of measure to UBL unit code
        
        Args:
            sap_unit: SAP unit code (e.g., 'EA', 'KG', 'L')
            
        Returns:
            UBL unit code (e.g., 'C62', 'KGM', 'LTR')
        """
        mapped_unit = cls.UNIT_OF_MEASURE_MAPPING.get(sap_unit, 'C62')
        logger.debug(f"Mapped SAP unit {sap_unit} to UBL unit {mapped_unit}")
        return mapped_unit
    
    @classmethod
    def map_payment_terms(cls, sap_payment_terms: str) -> Dict[str, Any]:
        """
        Map SAP payment terms to FIRS payment terms
        
        Args:
            sap_payment_terms: SAP payment terms code (e.g., 'NT30', 'COD')
            
        Returns:
            FIRS payment terms information
        """
        if sap_payment_terms in cls.PAYMENT_TERMS_MAPPING:
            terms_info = cls.PAYMENT_TERMS_MAPPING[sap_payment_terms].copy()
            logger.debug(f"Mapped SAP payment terms {sap_payment_terms} to FIRS terms {terms_info['code']}")
            return terms_info
        else:
            # Default to NET 30 for unknown payment terms
            logger.warning(f"Unknown SAP payment terms {sap_payment_terms}, using default NET 30")
            return {
                'code': 'NET_30',
                'name': 'Net 30 Days',
                'days': 30,
                'description': 'Payment due within 30 days'
            }
    
    @classmethod
    def map_incoterms(cls, sap_incoterms: str) -> str:
        """
        Map SAP Incoterms to UBL Incoterms
        
        Args:
            sap_incoterms: SAP Incoterms code (e.g., 'EXW', 'FOB')
            
        Returns:
            UBL Incoterms code
        """
        mapped_incoterms = cls.INCOTERMS_MAPPING.get(sap_incoterms, sap_incoterms)
        logger.debug(f"Mapped SAP Incoterms {sap_incoterms} to UBL Incoterms {mapped_incoterms}")
        return mapped_incoterms
    
    @classmethod
    def validate_currency(cls, currency_code: str) -> bool:
        """
        Validate currency code against supported currencies
        
        Args:
            currency_code: Currency code to validate (e.g., 'NGN', 'USD')
            
        Returns:
            True if currency is supported
        """
        is_valid = currency_code in cls.CURRENCY_MAPPING
        if not is_valid:
            logger.warning(f"Unsupported currency code: {currency_code}")
        return is_valid
    
    @classmethod
    def calculate_due_date(cls, invoice_date: str, payment_terms: str) -> str:
        """
        Calculate due date based on invoice date and payment terms
        
        Args:
            invoice_date: Invoice date in YYYY-MM-DD format
            payment_terms: SAP payment terms code
            
        Returns:
            Due date in YYYY-MM-DD format
        """
        try:
            invoice_dt = datetime.strptime(invoice_date, '%Y-%m-%d')
            terms_info = cls.map_payment_terms(payment_terms)
            
            if terms_info['days'] >= 0:
                due_date = invoice_dt + timedelta(days=terms_info['days'])
            else:
                # Cash in advance - due date is before invoice date
                due_date = invoice_dt
            
            return due_date.strftime('%Y-%m-%d')
            
        except ValueError as e:
            logger.error(f"Error calculating due date: {str(e)}")
            # Default to 30 days from invoice date
            invoice_dt = datetime.strptime(invoice_date, '%Y-%m-%d')
            due_date = invoice_dt + timedelta(days=30)
            return due_date.strftime('%Y-%m-%d')
    
    @classmethod
    def transform_billing_document_to_ubl(cls, billing_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform SAP Billing Document to UBL BIS 3.0 format
        
        Args:
            billing_document: SAP billing document data
            
        Returns:
            UBL BIS 3.0 formatted invoice
        """
        try:
            # Extract basic invoice information
            invoice_date = billing_document.get('BillingDocumentDate', '')
            payment_terms = billing_document.get('PaymentTerms', 'NT30')
            
            # Map document type
            invoice_type_code = cls.map_document_type(
                billing_document.get('BillingDocumentType', 'F2')
            )
            
            # Calculate due date
            due_date = cls.calculate_due_date(invoice_date, payment_terms)
            
            # Map payment terms
            payment_terms_info = cls.map_payment_terms(payment_terms)
            
            # Build UBL invoice structure
            ubl_invoice = {
                'CustomizationID': 'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0',
                'ProfileID': 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0',
                'ID': billing_document.get('BillingDocument', ''),
                'IssueDate': invoice_date,
                'DueDate': due_date,
                'InvoiceTypeCode': invoice_type_code,
                'Note': [],
                'TaxPointDate': invoice_date,
                'DocumentCurrencyCode': billing_document.get('TransactionCurrency', 'NGN'),
                'TaxCurrencyCode': billing_document.get('TransactionCurrency', 'NGN'),
                'OrderReference': {
                    'ID': billing_document.get('SalesDocument', '')
                },
                'BillingReference': [],
                'DespatchDocumentReference': [],
                'ReceiptDocumentReference': [],
                'OriginatorDocumentReference': [],
                'ContractDocumentReference': [],
                'AdditionalDocumentReference': [],
                'ProjectReference': [],
                'AccountingSupplierParty': cls._build_supplier_party(billing_document),
                'AccountingCustomerParty': cls._build_customer_party(billing_document),
                'PayeeParty': None,
                'TaxRepresentativeParty': None,
                'Delivery': [],
                'DeliveryTerms': cls._build_delivery_terms(billing_document),
                'PaymentMeans': cls._build_payment_means(billing_document, payment_terms_info),
                'PaymentTerms': cls._build_payment_terms(payment_terms_info),
                'AllowanceCharge': [],
                'TaxTotal': [],
                'LegalMonetaryTotal': cls._build_monetary_total(billing_document),
                'InvoiceLine': []
            }
            
            # Process invoice lines
            for line in billing_document.get('to_Item', {}).get('results', []):
                ubl_line = cls._transform_invoice_line(line)
                ubl_invoice['InvoiceLine'].append(ubl_line)
            
            # Process tax totals
            tax_totals = cls._calculate_tax_totals(billing_document)
            ubl_invoice['TaxTotal'] = tax_totals
            
            # Add Nigerian-specific fields
            cls._add_nigerian_specific_fields(ubl_invoice, billing_document)
            
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Error transforming billing document to UBL: {str(e)}")
            raise
    
    @classmethod
    def _build_supplier_party(cls, billing_document: Dict[str, Any]) -> Dict[str, Any]:
        """Build supplier party information"""
        return {
            'Party': {
                'EndpointID': {
                    '@schemeID': 'NG:TIN',
                    '#text': 'SUPPLIER_TIN_HERE'  # Would be populated from company config
                },
                'PartyIdentification': [{
                    'ID': {
                        '@schemeID': 'NG:TIN',
                        '#text': 'SUPPLIER_TIN_HERE'
                    }
                }],
                'PartyName': [{
                    'Name': 'SUPPLIER_NAME_HERE'  # Would be populated from company config
                }],
                'PostalAddress': {
                    'StreetName': 'SUPPLIER_STREET_HERE',
                    'CityName': 'SUPPLIER_CITY_HERE',
                    'PostalZone': 'SUPPLIER_POSTAL_CODE_HERE',
                    'CountrySubentity': 'SUPPLIER_STATE_HERE',
                    'Country': {
                        'IdentificationCode': 'NG'
                    }
                },
                'PartyTaxScheme': [{
                    'CompanyID': 'SUPPLIER_VAT_HERE',
                    'TaxScheme': {
                        'ID': 'VAT'
                    }
                }],
                'PartyLegalEntity': [{
                    'RegistrationName': 'SUPPLIER_LEGAL_NAME_HERE',
                    'CompanyID': {
                        '@schemeID': 'NG:CRN',
                        '#text': 'SUPPLIER_CRN_HERE'
                    }
                }],
                'Contact': {
                    'Name': 'SUPPLIER_CONTACT_NAME_HERE',
                    'Telephone': 'SUPPLIER_PHONE_HERE',
                    'ElectronicMail': 'SUPPLIER_EMAIL_HERE'
                }
            }
        }
    
    @classmethod
    def _build_customer_party(cls, billing_document: Dict[str, Any]) -> Dict[str, Any]:
        """Build customer party information"""
        sold_to_party = billing_document.get('SoldToParty', '')
        
        return {
            'Party': {
                'EndpointID': {
                    '@schemeID': 'NG:TIN',
                    '#text': f'CUSTOMER_TIN_{sold_to_party}'
                },
                'PartyIdentification': [{
                    'ID': {
                        '@schemeID': 'NG:TIN',
                        '#text': f'CUSTOMER_TIN_{sold_to_party}'
                    }
                }],
                'PartyName': [{
                    'Name': f'Customer {sold_to_party}'  # Would be populated from business partner data
                }],
                'PostalAddress': {
                    'StreetName': f'Customer Street {sold_to_party}',
                    'CityName': 'Lagos',
                    'PostalZone': '101001',
                    'CountrySubentity': 'Lagos State',
                    'Country': {
                        'IdentificationCode': 'NG'
                    }
                },
                'PartyTaxScheme': [{
                    'CompanyID': f'CUSTOMER_VAT_{sold_to_party}',
                    'TaxScheme': {
                        'ID': 'VAT'
                    }
                }],
                'PartyLegalEntity': [{
                    'RegistrationName': f'Customer {sold_to_party} Legal Name',
                    'CompanyID': {
                        '@schemeID': 'NG:CRN',
                        '#text': f'CUSTOMER_CRN_{sold_to_party}'
                    }
                }]
            }
        }
    
    @classmethod
    def _build_delivery_terms(cls, billing_document: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build delivery terms information"""
        incoterms = billing_document.get('IncotermsClassification', '')
        
        if incoterms:
            mapped_incoterms = cls.map_incoterms(incoterms)
            return {
                'ID': mapped_incoterms,
                'SpecialTerms': f'Incoterms: {mapped_incoterms}'
            }
        
        return None
    
    @classmethod
    def _build_payment_means(cls, billing_document: Dict[str, Any], payment_terms_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build payment means information"""
        return [{
            'PaymentMeansCode': '30',  # Credit transfer
            'PaymentID': billing_document.get('BillingDocument', ''),
            'PayeeFinancialAccount': {
                'ID': 'SUPPLIER_BANK_ACCOUNT_HERE',
                'Name': 'SUPPLIER_BANK_NAME_HERE',
                'FinancialInstitutionBranch': {
                    'ID': 'SUPPLIER_BANK_CODE_HERE'
                }
            }
        }]
    
    @classmethod
    def _build_payment_terms(cls, payment_terms_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build payment terms information"""
        return [{
            'Note': [payment_terms_info['description']],
            'PaymentDueDate': None  # Will be set elsewhere
        }]
    
    @classmethod
    def _build_monetary_total(cls, billing_document: Dict[str, Any]) -> Dict[str, Any]:
        """Build legal monetary total"""
        return {
            'LineExtensionAmount': {
                '@currencyID': billing_document.get('TransactionCurrency', 'NGN'),
                '#text': str(billing_document.get('NetAmount', 0))
            },
            'TaxExclusiveAmount': {
                '@currencyID': billing_document.get('TransactionCurrency', 'NGN'),
                '#text': str(billing_document.get('NetAmount', 0))
            },
            'TaxInclusiveAmount': {
                '@currencyID': billing_document.get('TransactionCurrency', 'NGN'),
                '#text': str(billing_document.get('TotalGrossAmount', 0))
            },
            'AllowanceTotalAmount': {
                '@currencyID': billing_document.get('TransactionCurrency', 'NGN'),
                '#text': '0'
            },
            'ChargeTotalAmount': {
                '@currencyID': billing_document.get('TransactionCurrency', 'NGN'),
                '#text': '0'
            },
            'PrepaidAmount': {
                '@currencyID': billing_document.get('TransactionCurrency', 'NGN'),
                '#text': '0'
            },
            'PayableRoundingAmount': {
                '@currencyID': billing_document.get('TransactionCurrency', 'NGN'),
                '#text': '0'
            },
            'PayableAmount': {
                '@currencyID': billing_document.get('TransactionCurrency', 'NGN'),
                '#text': str(billing_document.get('TotalGrossAmount', 0))
            }
        }
    
    @classmethod
    def _transform_invoice_line(cls, line: Dict[str, Any]) -> Dict[str, Any]:
        """Transform SAP invoice line to UBL invoice line"""
        line_id = line.get('BillingDocumentItem', '1')
        quantity = float(line.get('BillingQuantity', 1))
        unit = line.get('BillingQuantityUnit', 'EA')
        net_amount = float(line.get('NetAmount', 0))
        unit_price = net_amount / quantity if quantity > 0 else 0
        
        return {
            'ID': line_id,
            'Note': [],
            'InvoicedQuantity': {
                '@unitCode': cls.map_unit_of_measure(unit),
                '#text': str(quantity)
            },
            'LineExtensionAmount': {
                '@currencyID': line.get('TransactionCurrency', 'NGN'),
                '#text': str(net_amount)
            },
            'AccountingCost': line.get('ControllingArea', ''),
            'InvoicePeriod': [],
            'OrderLineReference': [],
            'DespatchLineReference': [],
            'ReceiptLineReference': [],
            'BillingReference': [],
            'DocumentReference': [],
            'AllowanceCharge': [],
            'Item': {
                'Description': [line.get('MaterialDescription', '')],
                'Name': line.get('MaterialDescription', ''),
                'BuyersItemIdentification': {
                    'ID': line.get('MaterialByCustomer', '')
                },
                'SellersItemIdentification': {
                    'ID': line.get('Material', '')
                },
                'StandardItemIdentification': {
                    'ID': {
                        '@schemeID': 'GTIN',
                        '#text': line.get('Material', '')
                    }
                },
                'OriginCountry': {
                    'IdentificationCode': 'NG'  # Default to Nigeria
                },
                'CommodityClassification': [{
                    'ItemClassificationCode': {
                        '@listID': 'SAP_MATERIAL_GROUP',
                        '#text': line.get('MaterialGroup', '')
                    }
                }],
                'ClassifiedTaxCategory': [{
                    'ID': 'S',  # Standard rate
                    'Percent': 7.5,
                    'TaxScheme': {
                        'ID': 'VAT'
                    }
                }],
                'AdditionalItemProperty': []
            },
            'Price': {
                'PriceAmount': {
                    '@currencyID': line.get('TransactionCurrency', 'NGN'),
                    '#text': str(unit_price)
                },
                'BaseQuantity': {
                    '@unitCode': cls.map_unit_of_measure(unit),
                    '#text': '1'
                },
                'AllowanceCharge': []
            }
        }
    
    @classmethod
    def _calculate_tax_totals(cls, billing_document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate tax totals from billing document"""
        currency = billing_document.get('TransactionCurrency', 'NGN')
        tax_amount = float(billing_document.get('TaxAmount', 0))
        net_amount = float(billing_document.get('NetAmount', 0))
        
        return [{
            'TaxAmount': {
                '@currencyID': currency,
                '#text': str(tax_amount)
            },
            'TaxSubtotal': [{
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
                    'Percent': 7.5,
                    'TaxScheme': {
                        'ID': 'VAT'
                    }
                }
            }]
        }]
    
    @classmethod
    def _add_nigerian_specific_fields(cls, ubl_invoice: Dict[str, Any], billing_document: Dict[str, Any]) -> None:
        """Add Nigerian-specific fields to UBL invoice"""
        # Add FIRS-specific additional document references
        ubl_invoice['AdditionalDocumentReference'].extend([
            {
                'ID': 'FIRS_APPROVAL_NUMBER',
                'DocumentTypeCode': 'FIRS_APPROVAL',
                'DocumentDescription': 'FIRS System Approval Number'
            },
            {
                'ID': billing_document.get('BillingDocument', ''),
                'DocumentTypeCode': 'SAP_BILLING_DOCUMENT',
                'DocumentDescription': 'SAP Billing Document Number'
            }
        ])
        
        # Add Nigerian tax information
        ubl_invoice['TaxTotal'][0]['TaxSubtotal'][0]['TaxCategory']['TaxExemptionReason'] = None
        ubl_invoice['TaxTotal'][0]['TaxSubtotal'][0]['TaxCategory']['TaxExemptionReasonCode'] = None
        
        # Add SAP-specific project references
        if billing_document.get('WBSElement'):
            ubl_invoice['ProjectReference'].append({
                'ID': billing_document.get('WBSElement', ''),
                'IssueDate': billing_document.get('BillingDocumentDate', '')
            })
    
    @classmethod
    def validate_firs_compliance(cls, ubl_invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate UBL invoice for FIRS compliance
        
        Args:
            ubl_invoice: UBL formatted invoice
            
        Returns:
            Validation result with errors and warnings
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required fields validation
        required_fields = [
            'ID', 'IssueDate', 'InvoiceTypeCode', 'DocumentCurrencyCode',
            'AccountingSupplierParty', 'AccountingCustomerParty', 'LegalMonetaryTotal',
            'InvoiceLine'
        ]
        
        for field in required_fields:
            if field not in ubl_invoice or not ubl_invoice[field]:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Nigerian business rules
        if ubl_invoice.get('DocumentCurrencyCode') != 'NGN':
            validation_result['warnings'].append("Non-NGN currency detected")
        
        # Tax validation
        if 'TaxTotal' in ubl_invoice and ubl_invoice['TaxTotal']:
            for tax_total in ubl_invoice['TaxTotal']:
                for tax_subtotal in tax_total.get('TaxSubtotal', []):
                    tax_category = tax_subtotal.get('TaxCategory', {})
                    tax_scheme = tax_category.get('TaxScheme', {})
                    
                    if tax_scheme.get('ID') == 'VAT':
                        percent = tax_category.get('Percent', 0)
                        if percent not in [0, 7.5]:
                            validation_result['warnings'].append(f"Non-standard VAT rate: {percent}%")
        
        # Invoice line validation
        if not ubl_invoice.get('InvoiceLine'):
            validation_result['errors'].append("Invoice must have at least one line")
            validation_result['is_valid'] = False
        
        return validation_result