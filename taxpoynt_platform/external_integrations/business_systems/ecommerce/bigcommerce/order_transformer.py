"""
BigCommerce E-commerce Order Transformer
Transforms BigCommerce orders to FIRS-compliant UBL BIS 3.0 invoices.
Handles BigCommerce-specific data structures and Nigerian tax compliance.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal

from .exceptions import BigCommerceTransformationError

logger = logging.getLogger(__name__)


class BigCommerceOrderTransformer:
    """
    BigCommerce E-commerce Order Transformer
    
    Transforms BigCommerce orders to FIRS-compliant UBL BIS 3.0 invoices.
    Supports multi-channel operations and Nigerian market compliance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize BigCommerce order transformer.
        
        Args:
            config: Configuration dictionary for transformation settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Nigerian tax configuration
        self.vat_rate = Decimal(str(self.config.get('vat_rate', '0.075')))  # 7.5% VAT
        self.default_currency = self.config.get('default_currency', 'NGN')
        self.default_country = self.config.get('default_country', 'NG')
        self.default_tin = self.config.get('default_tin', '00000000-0001')
    
    async def transform_order_to_invoice(
        self,
        order_data: Dict[str, Any],
        store_config: Optional[Dict[str, Any]] = None,
        channel_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform BigCommerce order to FIRS-compliant UBL BIS 3.0 invoice.
        
        Args:
            order_data: BigCommerce order data from API
            store_config: Store configuration for compliance
            channel_config: Channel configuration for multi-channel support
            
        Returns:
            FIRS-compliant UBL BIS 3.0 invoice dictionary
        """
        try:
            # Extract basic order information
            order_id = str(order_data.get('id', ''))
            order_date = self._parse_date(order_data.get('date_created'))
            
            # Build invoice header
            invoice_header = await self._build_invoice_header(order_data, store_config)
            
            # Build supplier information (store/merchant)
            supplier_party = await self._build_supplier_party(order_data, store_config, channel_config)
            
            # Build customer information
            customer_party = await self._build_customer_party(order_data)
            
            # Build invoice lines from order products
            invoice_lines = await self._build_invoice_lines(order_data)
            
            # Calculate tax totals
            tax_totals = await self._calculate_tax_totals(order_data, invoice_lines)
            
            # Calculate monetary totals
            monetary_totals = await self._calculate_monetary_totals(order_data, tax_totals)
            
            # Build payment information
            payment_means = await self._build_payment_means(order_data)
            
            # Construct UBL BIS 3.0 compliant invoice
            ubl_invoice = {
                'Invoice': {
                    '@xmlns': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
                    '@xmlns:cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                    '@xmlns:cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
                    
                    # Header information
                    **invoice_header,
                    
                    # Party information
                    'cac:AccountingSupplierParty': supplier_party,
                    'cac:AccountingCustomerParty': customer_party,
                    
                    # Payment information
                    'cac:PaymentMeans': payment_means,
                    
                    # Tax information
                    'cac:TaxTotal': tax_totals,
                    
                    # Monetary totals
                    'cac:LegalMonetaryTotal': monetary_totals,
                    
                    # Invoice lines
                    'cac:InvoiceLine': invoice_lines
                }
            }
            
            self.logger.info(f"Successfully transformed BigCommerce order {order_id} to UBL invoice")
            return ubl_invoice
            
        except Exception as e:
            self.logger.error(f"Failed to transform order to invoice: {e}")
            raise BigCommerceTransformationError(f"Order transformation failed: {e}")
    
    async def _build_invoice_header(
        self,
        order_data: Dict[str, Any],
        store_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build invoice header information."""
        try:
            order_date = self._parse_date(order_data.get('date_created'))
            order_id = str(order_data.get('id', ''))
            
            return {
                'cbc:ID': order_id,
                'cbc:IssueDate': order_date.strftime('%Y-%m-%d'),
                'cbc:IssueTime': order_date.strftime('%H:%M:%S'),
                'cbc:InvoiceTypeCode': '380',  # Commercial invoice
                'cbc:DocumentCurrencyCode': order_data.get('currency_code', self.default_currency),
                'cbc:BuyerReference': order_data.get('billing_address', {}).get('email', ''),
                'cbc:OrderReference': {
                    'cbc:ID': order_id
                },
                'cbc:Note': f"BigCommerce Order #{order_id}"
            }
            
        except Exception as e:
            raise BigCommerceTransformationError(f"Failed to build invoice header: {e}")
    
    async def _build_supplier_party(
        self,
        order_data: Dict[str, Any],
        store_config: Optional[Dict[str, Any]] = None,
        channel_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build supplier (merchant/store) party information."""
        try:
            # Use channel config if available, otherwise store config
            config = channel_config or store_config or {}
            
            # Extract store information
            store_name = config.get('name', 'BigCommerce Store')
            store_email = config.get('email', 'store@example.com')
            store_phone = config.get('phone', '')
            
            # Build store address (default to Lagos, Nigeria if not specified)
            store_address = {
                'cbc:StreetName': config.get('street', 'Victoria Island'),
                'cbc:CityName': config.get('city', 'Lagos'),
                'cbc:PostalZone': config.get('postcode', '100001'),
                'cbc:CountrySubentity': config.get('region', 'Lagos State'),
                'cac:Country': {
                    'cbc:IdentificationCode': config.get('country_id', self.default_country)
                }
            }
            
            return {
                'cac:Party': {
                    'cbc:EndpointID': {
                        '@schemeID': 'NG:TIN',
                        '#text': config.get('tin', self.default_tin)
                    },
                    'cac:PartyName': {
                        'cbc:Name': store_name
                    },
                    'cac:PostalAddress': store_address,
                    'cac:PartyTaxScheme': {
                        'cbc:CompanyID': config.get('tin', self.default_tin),
                        'cac:TaxScheme': {
                            'cbc:ID': 'VAT'
                        }
                    },
                    'cac:PartyLegalEntity': {
                        'cbc:RegistrationName': store_name,
                        'cbc:CompanyID': {
                            '@schemeID': 'NG:TIN',
                            '#text': config.get('tin', self.default_tin)
                        }
                    },
                    'cac:Contact': {
                        'cbc:ElectronicMail': store_email,
                        'cbc:Telephone': store_phone
                    }
                }
            }
            
        except Exception as e:
            raise BigCommerceTransformationError(f"Failed to build supplier party: {e}")
    
    async def _build_customer_party(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build customer party information."""
        try:
            # Extract customer information
            customer_details = order_data.get('customer_details', {})
            billing_address = order_data.get('billing_address', {})
            
            # Get customer name
            customer_name = self._get_customer_name(order_data, customer_details, billing_address)
            customer_email = billing_address.get('email', customer_details.get('email', ''))
            customer_phone = billing_address.get('phone', customer_details.get('phone', ''))
            
            # Build customer address
            customer_address = {
                'cbc:StreetName': ' '.join(filter(None, [
                    billing_address.get('street_1', ''),
                    billing_address.get('street_2', '')
                ])) or 'Lagos',
                'cbc:CityName': billing_address.get('city', 'Lagos'),
                'cbc:PostalZone': billing_address.get('zip', '100001'),
                'cbc:CountrySubentity': billing_address.get('state', 'Lagos State'),
                'cac:Country': {
                    'cbc:IdentificationCode': billing_address.get('country_iso2', self.default_country)
                }
            }
            
            # Get customer TIN (if available in custom fields)
            customer_tin = self.default_tin
            if customer_details.get('form_fields'):
                for field in customer_details.get('form_fields', []):
                    if field.get('name', '').lower() in ['tin', 'tax_id', 'vat_number']:
                        customer_tin = field.get('value', self.default_tin)
                        break
            
            return {
                'cac:Party': {
                    'cbc:EndpointID': {
                        '@schemeID': 'NG:TIN',
                        '#text': customer_tin
                    },
                    'cac:PartyName': {
                        'cbc:Name': customer_name
                    },
                    'cac:PostalAddress': customer_address,
                    'cac:PartyTaxScheme': {
                        'cbc:CompanyID': customer_tin,
                        'cac:TaxScheme': {
                            'cbc:ID': 'VAT'
                        }
                    },
                    'cac:PartyLegalEntity': {
                        'cbc:RegistrationName': customer_name,
                        'cbc:CompanyID': {
                            '@schemeID': 'NG:TIN',
                            '#text': customer_tin
                        }
                    },
                    'cac:Contact': {
                        'cbc:ElectronicMail': customer_email,
                        'cbc:Telephone': customer_phone
                    }
                }
            }
            
        except Exception as e:
            raise BigCommerceTransformationError(f"Failed to build customer party: {e}")
    
    def _get_customer_name(
        self,
        order_data: Dict[str, Any],
        customer_details: Dict[str, Any],
        billing_address: Dict[str, Any]
    ) -> str:
        """Extract customer name from various sources."""
        # Try different sources for customer name
        if billing_address.get('first_name') and billing_address.get('last_name'):
            return f"{billing_address['first_name']} {billing_address['last_name']}"
        elif customer_details.get('first_name') and customer_details.get('last_name'):
            return f"{customer_details['first_name']} {customer_details['last_name']}"
        elif billing_address.get('company'):
            return billing_address['company']
        elif customer_details.get('company'):
            return customer_details['company']
        else:
            return billing_address.get('email', customer_details.get('email', 'Customer'))
    
    async def _build_invoice_lines(self, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build invoice lines from order products."""
        try:
            invoice_lines = []
            products = order_data.get('products', [])
            
            for index, product in enumerate(products, 1):
                # Calculate line totals
                quantity = Decimal(str(product.get('quantity', 1)))
                unit_price = Decimal(str(product.get('price_inc_tax', 0))) / quantity if quantity > 0 else Decimal('0')
                line_total = Decimal(str(product.get('total_ex_tax', 0)))
                tax_amount = Decimal(str(product.get('total_tax', 0)))
                
                # Build invoice line
                invoice_line = {
                    'cbc:ID': str(index),
                    'cbc:InvoicedQuantity': {
                        '@unitCode': 'EA',  # Each
                        '#text': str(quantity)
                    },
                    'cbc:LineExtensionAmount': {
                        '@currencyID': order_data.get('currency_code', self.default_currency),
                        '#text': str(line_total)
                    },
                    'cac:Item': {
                        'cbc:Name': product.get('name', 'Product'),
                        'cbc:Description': product.get('name', 'Product'),
                        'cac:SellersItemIdentification': {
                            'cbc:ID': product.get('sku', str(product.get('product_id', '')))
                        },
                        'cac:ClassifiedTaxCategory': {
                            'cbc:ID': 'S',  # Standard rate
                            'cbc:Percent': str(self.vat_rate * 100),
                            'cac:TaxScheme': {
                                'cbc:ID': 'VAT'
                            }
                        }
                    },
                    'cac:Price': {
                        'cbc:PriceAmount': {
                            '@currencyID': order_data.get('currency_code', self.default_currency),
                            '#text': str(unit_price)
                        },
                        'cbc:BaseQuantity': {
                            '@unitCode': 'EA',
                            '#text': '1'
                        }
                    }
                }
                
                # Add tax information if tax amount exists
                if tax_amount > 0:
                    invoice_line['cac:TaxTotal'] = {
                        'cbc:TaxAmount': {
                            '@currencyID': order_data.get('currency_code', self.default_currency),
                            '#text': str(tax_amount)
                        },
                        'cac:TaxSubtotal': {
                            'cbc:TaxableAmount': {
                                '@currencyID': order_data.get('currency_code', self.default_currency),
                                '#text': str(line_total)
                            },
                            'cbc:TaxAmount': {
                                '@currencyID': order_data.get('currency_code', self.default_currency),
                                '#text': str(tax_amount)
                            },
                            'cac:TaxCategory': {
                                'cbc:ID': 'S',
                                'cbc:Percent': str(self.vat_rate * 100),
                                'cac:TaxScheme': {
                                    'cbc:ID': 'VAT'
                                }
                            }
                        }
                    }
                
                invoice_lines.append(invoice_line)
            
            return invoice_lines
            
        except Exception as e:
            raise BigCommerceTransformationError(f"Failed to build invoice lines: {e}")
    
    async def _calculate_tax_totals(
        self,
        order_data: Dict[str, Any],
        invoice_lines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate tax totals for the invoice."""
        try:
            tax_amount = Decimal(str(order_data.get('total_tax', 0)))
            subtotal = Decimal(str(order_data.get('subtotal_ex_tax', 0)))
            
            # If no tax amount in order, calculate from subtotal
            if tax_amount == 0 and subtotal > 0:
                # Calculate VAT based on tax-exclusive subtotal
                tax_amount = subtotal * self.vat_rate
            
            return [{
                'cbc:TaxAmount': {
                    '@currencyID': order_data.get('currency_code', self.default_currency),
                    '#text': str(tax_amount)
                },
                'cac:TaxSubtotal': {
                    'cbc:TaxableAmount': {
                        '@currencyID': order_data.get('currency_code', self.default_currency),
                        '#text': str(subtotal)
                    },
                    'cbc:TaxAmount': {
                        '@currencyID': order_data.get('currency_code', self.default_currency),
                        '#text': str(tax_amount)
                    },
                    'cac:TaxCategory': {
                        'cbc:ID': 'S',
                        'cbc:Percent': str(self.vat_rate * 100),
                        'cac:TaxScheme': {
                            'cbc:ID': 'VAT'
                        }
                    }
                }
            }]
            
        except Exception as e:
            raise BigCommerceTransformationError(f"Failed to calculate tax totals: {e}")
    
    async def _calculate_monetary_totals(
        self,
        order_data: Dict[str, Any],
        tax_totals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate monetary totals for the invoice."""
        try:
            subtotal_ex_tax = Decimal(str(order_data.get('subtotal_ex_tax', 0)))
            tax_amount = Decimal(str(order_data.get('total_tax', 0)))
            discount_amount = abs(Decimal(str(order_data.get('discount_amount', 0))))
            shipping_cost = Decimal(str(order_data.get('shipping_cost_ex_tax', 0)))
            total_inc_tax = Decimal(str(order_data.get('total_inc_tax', 0)))
            
            # Calculate line extension amount (subtotal before tax and shipping)
            line_extension_amount = subtotal_ex_tax
            
            # Calculate tax exclusive amount (includes shipping but not tax)
            tax_exclusive_amount = subtotal_ex_tax - discount_amount + shipping_cost
            
            # Calculate tax inclusive amount
            tax_inclusive_amount = tax_exclusive_amount + tax_amount
            
            # Calculate payable amount (should match total_inc_tax)
            payable_amount = total_inc_tax
            
            return {
                'cbc:LineExtensionAmount': {
                    '@currencyID': order_data.get('currency_code', self.default_currency),
                    '#text': str(line_extension_amount)
                },
                'cbc:TaxExclusiveAmount': {
                    '@currencyID': order_data.get('currency_code', self.default_currency),
                    '#text': str(tax_exclusive_amount)
                },
                'cbc:TaxInclusiveAmount': {
                    '@currencyID': order_data.get('currency_code', self.default_currency),
                    '#text': str(tax_inclusive_amount)
                },
                'cbc:AllowanceTotalAmount': {
                    '@currencyID': order_data.get('currency_code', self.default_currency),
                    '#text': str(discount_amount)
                },
                'cbc:PayableAmount': {
                    '@currencyID': order_data.get('currency_code', self.default_currency),
                    '#text': str(payable_amount)
                }
            }
            
        except Exception as e:
            raise BigCommerceTransformationError(f"Failed to calculate monetary totals: {e}")
    
    async def _build_payment_means(self, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build payment means information."""
        try:
            payment_method = order_data.get('payment_method', 'unknown')
            
            # Map BigCommerce payment methods to standard codes
            payment_code_mapping = {
                'manual': '1',         # Other
                'cash': '10',          # Cash
                'check': '20',         # Check
                'bank_deposit': '30',  # Credit transfer
                'credit_card': '48',   # Card payment
                'paypal': '48',        # Card payment
                'store_credit': '1',   # Other
                'gift_certificate': '1',  # Other
                'custom': '1',         # Other
                # Nigerian payment methods
                'paystack': '48',      # Card payment
                'flutterwave': '48',   # Card payment
                'interswitch': '48',   # Card payment
            }
            
            payment_code = payment_code_mapping.get(payment_method.lower(), '1')  # Default: other
            
            return [{
                'cbc:PaymentMeansCode': payment_code,
                'cbc:PaymentID': str(order_data.get('id', '')),
                'cac:PayeeFinancialAccount': {
                    'cbc:ID': 'N/A',
                    'cbc:Name': payment_method.replace('_', ' ').title()
                }
            }]
            
        except Exception as e:
            raise BigCommerceTransformationError(f"Failed to build payment means: {e}")
    
    def _parse_date(self, date_string: Optional[str]) -> datetime:
        """Parse date string to datetime object."""
        if not date_string:
            return datetime.now()
        
        try:
            # Handle various BigCommerce date formats
            # BigCommerce typically uses RFC 3339 format
            for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                try:
                    # Remove timezone info if present for simple parsing
                    clean_date = date_string.replace('Z', '').split('+')[0].split('-')
                    if len(clean_date) > 3:  # Has timezone
                        clean_date = '-'.join(clean_date[:3]) + 'T' + clean_date[3] if 'T' not in clean_date[3] else '-'.join(clean_date[:3]) + clean_date[3]
                    else:
                        clean_date = date_string.replace('Z', '').split('+')[0]
                    
                    return datetime.strptime(clean_date, fmt)
                except ValueError:
                    continue
            
            # If all parsing attempts fail, return current time
            self.logger.warning(f"Could not parse date string: {date_string}")
            return datetime.now()
            
        except Exception as e:
            self.logger.warning(f"Date parsing error: {e}")
            return datetime.now()
    
    async def validate_transformation(self, ubl_invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the transformed UBL invoice.
        
        Args:
            ubl_invoice: UBL BIS 3.0 invoice dictionary
            
        Returns:
            Validation result dictionary
        """
        try:
            validation_errors = []
            validation_warnings = []
            
            # Check required fields
            invoice = ubl_invoice.get('Invoice', {})
            
            required_fields = [
                'cbc:ID',
                'cbc:IssueDate',
                'cbc:InvoiceTypeCode',
                'cbc:DocumentCurrencyCode',
                'cac:AccountingSupplierParty',
                'cac:AccountingCustomerParty',
                'cac:InvoiceLine'
            ]
            
            for field in required_fields:
                if field not in invoice:
                    validation_errors.append(f"Missing required field: {field}")
            
            # Validate supplier TIN
            supplier_tin = invoice.get('cac:AccountingSupplierParty', {}).get('cac:Party', {}).get('cbc:EndpointID', {}).get('#text')
            if not supplier_tin or supplier_tin == self.default_tin:
                validation_warnings.append("Using default TIN for supplier - should be updated with actual TIN")
            
            # Validate customer TIN
            customer_tin = invoice.get('cac:AccountingCustomerParty', {}).get('cac:Party', {}).get('cbc:EndpointID', {}).get('#text')
            if not customer_tin or customer_tin == self.default_tin:
                validation_warnings.append("Using default TIN for customer - should be updated with actual TIN")
            
            # Validate currency
            currency = invoice.get('cbc:DocumentCurrencyCode')
            if currency != 'NGN':
                validation_warnings.append(f"Currency is {currency}, not NGN - ensure compliance with Nigerian regulations")
            
            # Validate invoice lines
            invoice_lines = invoice.get('cac:InvoiceLine', [])
            if not isinstance(invoice_lines, list):
                invoice_lines = [invoice_lines]
            
            if not invoice_lines:
                validation_errors.append("No invoice lines found")
            
            return {
                'is_valid': len(validation_errors) == 0,
                'errors': validation_errors,
                'warnings': validation_warnings,
                'summary': {
                    'total_errors': len(validation_errors),
                    'total_warnings': len(validation_warnings),
                    'invoice_lines_count': len(invoice_lines)
                }
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f"Validation failed: {e}"],
                'warnings': [],
                'summary': {
                    'total_errors': 1,
                    'total_warnings': 0,
                    'invoice_lines_count': 0
                }
            }