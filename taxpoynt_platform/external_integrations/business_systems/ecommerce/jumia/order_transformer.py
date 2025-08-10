"""
Jumia E-commerce Order Transformer
Transforms Jumia orders to FIRS-compliant UBL BIS 3.0 invoices.
Handles African marketplace operations and Nigerian tax compliance.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal

from .exceptions import JumiaTransformationError

logger = logging.getLogger(__name__)


class JumiaOrderTransformer:
    """
    Jumia E-commerce Order Transformer
    
    Transforms Jumia marketplace orders to FIRS-compliant UBL BIS 3.0 invoices.
    Supports African marketplace operations with Nigerian tax compliance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Jumia order transformer.
        
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
        
        # Jumia marketplace configuration
        self.seller_tin = self.config.get('seller_tin', self.default_tin)
        self.seller_name = self.config.get('seller_name', 'Jumia Seller')
        self.seller_address = self.config.get('seller_address', {})
    
    async def transform_order_to_invoice(
        self,
        order_data: Dict[str, Any],
        seller_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Jumia order to FIRS-compliant UBL BIS 3.0 invoice.
        
        Args:
            order_data: Jumia order data from API
            seller_profile: Seller profile information for compliance
            
        Returns:
            FIRS-compliant UBL BIS 3.0 invoice dictionary
        """
        try:
            # Extract basic order information
            order_id = str(order_data.get('id', order_data.get('order_id', '')))
            order_date = self._parse_date(order_data.get('created_at'))
            
            # Build invoice header
            invoice_header = await self._build_invoice_header(order_data, seller_profile)
            
            # Build supplier information (seller on Jumia)
            supplier_party = await self._build_supplier_party(order_data, seller_profile)
            
            # Build customer information
            customer_party = await self._build_customer_party(order_data)
            
            # Build invoice lines from order items
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
            
            self.logger.info(f"Successfully transformed Jumia order {order_id} to UBL invoice")
            return ubl_invoice
            
        except Exception as e:
            self.logger.error(f"Failed to transform order to invoice: {e}")
            raise JumiaTransformationError(f"Order transformation failed: {e}")
    
    async def _build_invoice_header(
        self,
        order_data: Dict[str, Any],
        seller_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build invoice header information."""
        try:
            order_date = self._parse_date(order_data.get('created_at'))
            order_id = str(order_data.get('id', order_data.get('order_id', '')))
            order_number = order_data.get('order_number', order_id)
            
            return {
                'cbc:ID': order_number,
                'cbc:IssueDate': order_date.strftime('%Y-%m-%d'),
                'cbc:IssueTime': order_date.strftime('%H:%M:%S'),
                'cbc:InvoiceTypeCode': '380',  # Commercial invoice
                'cbc:DocumentCurrencyCode': order_data.get('currency', self.default_currency),
                'cbc:BuyerReference': order_data.get('customer', {}).get('email', ''),
                'cbc:OrderReference': {
                    'cbc:ID': order_number
                },
                'cbc:Note': f"Jumia Marketplace Order #{order_number}"
            }
            
        except Exception as e:
            raise JumiaTransformationError(f"Failed to build invoice header: {e}")
    
    async def _build_supplier_party(
        self,
        order_data: Dict[str, Any],
        seller_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build supplier (seller) party information."""
        try:
            # Use seller profile if available, otherwise config
            if seller_profile:
                seller_name = seller_profile.get('name', self.seller_name)
                seller_email = seller_profile.get('email', 'seller@jumia.com')
                seller_phone = seller_profile.get('phone', '')
            else:
                seller_name = self.seller_name
                seller_email = 'seller@jumia.com'
                seller_phone = ''
            
            # Build seller address (default to Nigeria if not specified)
            seller_address = self.seller_address or {}
            address_info = {
                'cbc:StreetName': seller_address.get('street', 'Victoria Island'),
                'cbc:CityName': seller_address.get('city', 'Lagos'),
                'cbc:PostalZone': seller_address.get('postcode', '100001'),
                'cbc:CountrySubentity': seller_address.get('region', 'Lagos State'),
                'cac:Country': {
                    'cbc:IdentificationCode': seller_address.get('country_id', self.default_country)
                }
            }
            
            return {
                'cac:Party': {
                    'cbc:EndpointID': {
                        '@schemeID': 'NG:TIN',
                        '#text': self.seller_tin
                    },
                    'cac:PartyName': {
                        'cbc:Name': seller_name
                    },
                    'cac:PostalAddress': address_info,
                    'cac:PartyTaxScheme': {
                        'cbc:CompanyID': self.seller_tin,
                        'cac:TaxScheme': {
                            'cbc:ID': 'VAT'
                        }
                    },
                    'cac:PartyLegalEntity': {
                        'cbc:RegistrationName': seller_name,
                        'cbc:CompanyID': {
                            '@schemeID': 'NG:TIN',
                            '#text': self.seller_tin
                        }
                    },
                    'cac:Contact': {
                        'cbc:ElectronicMail': seller_email,
                        'cbc:Telephone': seller_phone
                    }
                }
            }
            
        except Exception as e:
            raise JumiaTransformationError(f"Failed to build supplier party: {e}")
    
    async def _build_customer_party(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build customer party information."""
        try:
            # Extract customer information
            customer = order_data.get('customer', {})
            shipping_address = order_data.get('shipping_address', {})
            billing_address = order_data.get('billing_address', shipping_address)
            
            # Get customer name
            customer_name = customer.get('name', '').strip()
            if not customer_name:
                customer_name = shipping_address.get('name', 'Customer').strip()
            
            customer_email = customer.get('email', '')
            customer_phone = customer.get('phone', shipping_address.get('phone', ''))
            
            # Build customer address (prefer billing, fallback to shipping)
            address_source = billing_address if billing_address else shipping_address
            customer_address = {
                'cbc:StreetName': address_source.get('address', 'Lagos'),
                'cbc:CityName': address_source.get('city', 'Lagos'),
                'cbc:PostalZone': address_source.get('postcode', '100001'),
                'cbc:CountrySubentity': address_source.get('region', 'Lagos State'),
                'cac:Country': {
                    'cbc:IdentificationCode': address_source.get('country', self.default_country)
                }
            }
            
            # Use default TIN for customer (Jumia doesn't typically provide customer TIN)
            customer_tin = self.default_tin
            
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
            raise JumiaTransformationError(f"Failed to build customer party: {e}")
    
    async def _build_invoice_lines(self, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build invoice lines from order items."""
        try:
            invoice_lines = []
            items = order_data.get('items', [])
            
            for index, item in enumerate(items, 1):
                # Calculate line totals
                quantity = Decimal(str(item.get('quantity', 1)))
                unit_price = Decimal(str(item.get('unit_price', item.get('price', 0))))
                line_total = Decimal(str(item.get('total_price', unit_price * quantity)))
                
                # Calculate tax amount (assume VAT-inclusive pricing)
                tax_amount = line_total * self.vat_rate / (1 + self.vat_rate)
                line_total_ex_tax = line_total - tax_amount
                
                # Build invoice line
                invoice_line = {
                    'cbc:ID': str(index),
                    'cbc:InvoicedQuantity': {
                        '@unitCode': 'EA',  # Each
                        '#text': str(quantity)
                    },
                    'cbc:LineExtensionAmount': {
                        '@currencyID': order_data.get('currency', self.default_currency),
                        '#text': str(line_total_ex_tax)
                    },
                    'cac:Item': {
                        'cbc:Name': item.get('name', 'Product'),
                        'cbc:Description': item.get('description', item.get('name', 'Product')),
                        'cac:SellersItemIdentification': {
                            'cbc:ID': item.get('sku', str(item.get('product_id', '')))
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
                            '@currencyID': order_data.get('currency', self.default_currency),
                            '#text': str(unit_price / (1 + self.vat_rate))  # Price excluding VAT
                        },
                        'cbc:BaseQuantity': {
                            '@unitCode': 'EA',
                            '#text': '1'
                        }
                    }
                }
                
                # Add tax information
                if tax_amount > 0:
                    invoice_line['cac:TaxTotal'] = {
                        'cbc:TaxAmount': {
                            '@currencyID': order_data.get('currency', self.default_currency),
                            '#text': str(tax_amount)
                        },
                        'cac:TaxSubtotal': {
                            'cbc:TaxableAmount': {
                                '@currencyID': order_data.get('currency', self.default_currency),
                                '#text': str(line_total_ex_tax)
                            },
                            'cbc:TaxAmount': {
                                '@currencyID': order_data.get('currency', self.default_currency),
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
            raise JumiaTransformationError(f"Failed to build invoice lines: {e}")
    
    async def _calculate_tax_totals(
        self,
        order_data: Dict[str, Any],
        invoice_lines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate tax totals for the invoice."""
        try:
            # Get tax amount from order data or calculate from total
            tax_amount = Decimal(str(order_data.get('tax_amount', 0)))
            total_amount = Decimal(str(order_data.get('total_amount', 0)))
            
            # If no tax amount in order, calculate from total (assume VAT-inclusive)
            if tax_amount == 0 and total_amount > 0:
                # Consider shipping and voucher amounts
                shipping_fee = Decimal(str(order_data.get('shipping_fee', 0)))
                voucher_amount = Decimal(str(order_data.get('voucher_amount', 0)))
                
                # Calculate taxable amount (total - shipping + vouchers)
                taxable_total = total_amount - shipping_fee + voucher_amount
                tax_amount = taxable_total * self.vat_rate / (1 + self.vat_rate)
            
            # Calculate subtotal (tax-exclusive)
            subtotal = total_amount - tax_amount
            
            return [{
                'cbc:TaxAmount': {
                    '@currencyID': order_data.get('currency', self.default_currency),
                    '#text': str(tax_amount)
                },
                'cac:TaxSubtotal': {
                    'cbc:TaxableAmount': {
                        '@currencyID': order_data.get('currency', self.default_currency),
                        '#text': str(subtotal)
                    },
                    'cbc:TaxAmount': {
                        '@currencyID': order_data.get('currency', self.default_currency),
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
            raise JumiaTransformationError(f"Failed to calculate tax totals: {e}")
    
    async def _calculate_monetary_totals(
        self,
        order_data: Dict[str, Any],
        tax_totals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate monetary totals for the invoice."""
        try:
            total_amount = Decimal(str(order_data.get('total_amount', 0)))
            tax_amount = Decimal(str(order_data.get('tax_amount', 0)))
            shipping_fee = Decimal(str(order_data.get('shipping_fee', 0)))
            voucher_amount = Decimal(str(order_data.get('voucher_amount', 0)))
            
            # If no tax amount specified, calculate it
            if tax_amount == 0 and total_amount > 0:
                taxable_total = total_amount - shipping_fee + voucher_amount
                tax_amount = taxable_total * self.vat_rate / (1 + self.vat_rate)
            
            # Calculate components
            line_extension_amount = total_amount - tax_amount - shipping_fee
            tax_exclusive_amount = line_extension_amount + shipping_fee - voucher_amount
            tax_inclusive_amount = tax_exclusive_amount + tax_amount
            payable_amount = total_amount - voucher_amount
            
            return {
                'cbc:LineExtensionAmount': {
                    '@currencyID': order_data.get('currency', self.default_currency),
                    '#text': str(line_extension_amount)
                },
                'cbc:TaxExclusiveAmount': {
                    '@currencyID': order_data.get('currency', self.default_currency),
                    '#text': str(tax_exclusive_amount)
                },
                'cbc:TaxInclusiveAmount': {
                    '@currencyID': order_data.get('currency', self.default_currency),
                    '#text': str(tax_inclusive_amount)
                },
                'cbc:AllowanceTotalAmount': {
                    '@currencyID': order_data.get('currency', self.default_currency),
                    '#text': str(voucher_amount)
                },
                'cbc:PayableAmount': {
                    '@currencyID': order_data.get('currency', self.default_currency),
                    '#text': str(payable_amount)
                }
            }
            
        except Exception as e:
            raise JumiaTransformationError(f"Failed to calculate monetary totals: {e}")
    
    async def _build_payment_means(self, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build payment means information."""
        try:
            payment_method = order_data.get('payment_method', 'unknown')
            
            # Map Jumia payment methods to standard codes
            payment_code_mapping = {
                'cod': '10',           # Cash on Delivery
                'card': '48',          # Card payment
                'bank_transfer': '30', # Credit transfer
                'wallet': '48',        # Electronic payment
                'installment': '48',   # Card payment (installment)
                'voucher': '1',        # Other
                'jumia_pay': '48',     # Electronic payment
                'mobile_money': '48',  # Mobile payment
            }
            
            payment_code = payment_code_mapping.get(payment_method.lower(), '1')  # Default: other
            
            return [{
                'cbc:PaymentMeansCode': payment_code,
                'cbc:PaymentID': str(order_data.get('order_number', order_data.get('id', ''))),
                'cac:PayeeFinancialAccount': {
                    'cbc:ID': 'N/A',
                    'cbc:Name': payment_method.replace('_', ' ').title()
                }
            }]
            
        except Exception as e:
            raise JumiaTransformationError(f"Failed to build payment means: {e}")
    
    def _parse_date(self, date_string: Optional[str]) -> datetime:
        """Parse date string to datetime object."""
        if not date_string:
            return datetime.now()
        
        try:
            # Handle various Jumia date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']:
                try:
                    # Remove timezone info if present
                    clean_date = date_string.replace('Z', '').split('+')[0].split('T')
                    if len(clean_date) == 2:
                        clean_date = f"{clean_date[0]} {clean_date[1]}"
                    else:
                        clean_date = clean_date[0]
                    
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
                validation_warnings.append("Using default TIN for supplier - should be updated with actual seller TIN")
            
            # Validate customer TIN
            customer_tin = invoice.get('cac:AccountingCustomerParty', {}).get('cac:Party', {}).get('cbc:EndpointID', {}).get('#text')
            if not customer_tin or customer_tin == self.default_tin:
                validation_warnings.append("Using default TIN for customer - customer TIN not available from Jumia")
            
            # Validate currency for Nigerian marketplace
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