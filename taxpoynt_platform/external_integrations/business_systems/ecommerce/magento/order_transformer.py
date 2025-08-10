"""
Magento E-commerce Order Transformer
Transforms Magento orders to FIRS-compliant UBL BIS 3.0 invoices.
Handles Adobe Commerce and Magento Open Source with multi-store and Nigerian tax compliance.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal

from .exceptions import MagentoTransformationError

logger = logging.getLogger(__name__)


class MagentoOrderTransformer:
    """
    Magento E-commerce Order Transformer
    
    Transforms Magento orders to FIRS-compliant UBL BIS 3.0 invoices.
    Supports both Adobe Commerce and Magento Open Source with Nigerian market compliance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Magento order transformer.
        
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
        store_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Magento order to FIRS-compliant UBL BIS 3.0 invoice.
        
        Args:
            order_data: Magento order data from API
            store_config: Store configuration for multi-store support
            
        Returns:
            FIRS-compliant UBL BIS 3.0 invoice dictionary
        """
        try:
            # Extract basic order information
            order_id = str(order_data.get('entity_id', ''))
            increment_id = order_data.get('increment_id', order_id)
            order_date = self._parse_date(order_data.get('created_at'))
            
            # Build invoice header
            invoice_header = await self._build_invoice_header(order_data, store_config)
            
            # Build supplier information (store/merchant)
            supplier_party = await self._build_supplier_party(order_data, store_config)
            
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
            
            self.logger.info(f"Successfully transformed Magento order {increment_id} to UBL invoice")
            return ubl_invoice
            
        except Exception as e:
            self.logger.error(f"Failed to transform order to invoice: {e}")
            raise MagentoTransformationError(f"Order transformation failed: {e}")
    
    async def _build_invoice_header(
        self,
        order_data: Dict[str, Any],
        store_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build invoice header information."""
        try:
            order_date = self._parse_date(order_data.get('created_at'))
            increment_id = order_data.get('increment_id', str(order_data.get('entity_id', '')))
            
            return {
                'cbc:ID': increment_id,
                'cbc:IssueDate': order_date.strftime('%Y-%m-%d'),
                'cbc:IssueTime': order_date.strftime('%H:%M:%S'),
                'cbc:InvoiceTypeCode': '380',  # Commercial invoice
                'cbc:DocumentCurrencyCode': order_data.get('order_currency_code', self.default_currency),
                'cbc:BuyerReference': order_data.get('customer_email', ''),
                'cbc:OrderReference': {
                    'cbc:ID': increment_id
                },
                'cbc:Note': f"Magento Order #{increment_id}"
            }
            
        except Exception as e:
            raise MagentoTransformationError(f"Failed to build invoice header: {e}")
    
    async def _build_supplier_party(
        self,
        order_data: Dict[str, Any],
        store_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build supplier (merchant/store) party information."""
        try:
            store_info = order_data.get('store_info', {})
            
            # Extract store information
            store_name = store_info.get('name', store_config.get('store_name', 'Magento Store'))
            store_email = store_info.get('email', store_config.get('store_email', 'store@example.com'))
            store_phone = store_info.get('phone', store_config.get('store_phone', ''))
            
            # Build store address (default to Lagos, Nigeria if not specified)
            store_address = {
                'cbc:StreetName': store_config.get('street', 'Victoria Island'),
                'cbc:CityName': store_config.get('city', 'Lagos'),
                'cbc:PostalZone': store_config.get('postcode', '100001'),
                'cbc:CountrySubentity': store_config.get('region', 'Lagos State'),
                'cac:Country': {
                    'cbc:IdentificationCode': store_config.get('country_id', self.default_country)
                }
            }
            
            return {
                'cac:Party': {
                    'cbc:EndpointID': {
                        '@schemeID': 'NG:TIN',
                        '#text': store_config.get('tin', self.default_tin)
                    },
                    'cac:PartyName': {
                        'cbc:Name': store_name
                    },
                    'cac:PostalAddress': store_address,
                    'cac:PartyTaxScheme': {
                        'cbc:CompanyID': store_config.get('tin', self.default_tin),
                        'cac:TaxScheme': {
                            'cbc:ID': 'VAT'
                        }
                    },
                    'cac:PartyLegalEntity': {
                        'cbc:RegistrationName': store_name,
                        'cbc:CompanyID': {
                            '@schemeID': 'NG:TIN',
                            '#text': store_config.get('tin', self.default_tin)
                        }
                    },
                    'cac:Contact': {
                        'cbc:ElectronicMail': store_email,
                        'cbc:Telephone': store_phone
                    }
                }
            }
            
        except Exception as e:
            raise MagentoTransformationError(f"Failed to build supplier party: {e}")
    
    async def _build_customer_party(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build customer party information."""
        try:
            # Extract customer information
            customer = order_data.get('customer_details', {})
            billing_address = order_data.get('billing_address', {})
            
            customer_name = self._get_customer_name(order_data, customer, billing_address)
            customer_email = order_data.get('customer_email', customer.get('email', billing_address.get('email', '')))
            customer_phone = billing_address.get('telephone', customer.get('custom_attributes', {}).get('phone', ''))
            
            # Build customer address
            customer_address = {
                'cbc:StreetName': billing_address.get('street', [''])[0] if isinstance(billing_address.get('street'), list) else billing_address.get('street', ''),
                'cbc:CityName': billing_address.get('city', 'Lagos'),
                'cbc:PostalZone': billing_address.get('postcode', '100001'),
                'cbc:CountrySubentity': billing_address.get('region', 'Lagos State'),
                'cac:Country': {
                    'cbc:IdentificationCode': billing_address.get('country_id', self.default_country)
                }
            }
            
            return {
                'cac:Party': {
                    'cbc:EndpointID': {
                        '@schemeID': 'NG:TIN',
                        '#text': customer.get('taxvat', self.default_tin)
                    },
                    'cac:PartyName': {
                        'cbc:Name': customer_name
                    },
                    'cac:PostalAddress': customer_address,
                    'cac:PartyTaxScheme': {
                        'cbc:CompanyID': customer.get('taxvat', self.default_tin),
                        'cac:TaxScheme': {
                            'cbc:ID': 'VAT'
                        }
                    },
                    'cac:PartyLegalEntity': {
                        'cbc:RegistrationName': customer_name,
                        'cbc:CompanyID': {
                            '@schemeID': 'NG:TIN',
                            '#text': customer.get('taxvat', self.default_tin)
                        }
                    },
                    'cac:Contact': {
                        'cbc:ElectronicMail': customer_email,
                        'cbc:Telephone': customer_phone
                    }
                }
            }
            
        except Exception as e:
            raise MagentoTransformationError(f"Failed to build customer party: {e}")
    
    def _get_customer_name(
        self,
        order_data: Dict[str, Any],
        customer: Dict[str, Any],
        billing_address: Dict[str, Any]
    ) -> str:
        """Extract customer name from various sources."""
        # Try different sources for customer name
        if customer.get('firstname') and customer.get('lastname'):
            return f"{customer['firstname']} {customer['lastname']}"
        elif billing_address.get('firstname') and billing_address.get('lastname'):
            return f"{billing_address['firstname']} {billing_address['lastname']}"
        elif order_data.get('customer_firstname') and order_data.get('customer_lastname'):
            return f"{order_data['customer_firstname']} {order_data['customer_lastname']}"
        else:
            return order_data.get('customer_email', 'Customer')
    
    async def _build_invoice_lines(self, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build invoice lines from order items."""
        try:
            invoice_lines = []
            
            for index, item in enumerate(order_data.get('items', []), 1):
                # Skip if this is a child item of a configurable/bundle product
                if item.get('parent_item_id'):
                    continue
                
                product_details = item.get('product_details', {})
                
                # Calculate line totals
                quantity = Decimal(str(item.get('qty_ordered', 1)))
                unit_price = Decimal(str(item.get('price', 0)))
                line_total = Decimal(str(item.get('row_total', 0)))
                tax_amount = Decimal(str(item.get('tax_amount', 0)))
                
                # Build invoice line
                invoice_line = {
                    'cbc:ID': str(index),
                    'cbc:InvoicedQuantity': {
                        '@unitCode': 'EA',  # Each
                        '#text': str(quantity)
                    },
                    'cbc:LineExtensionAmount': {
                        '@currencyID': order_data.get('order_currency_code', self.default_currency),
                        '#text': str(line_total)
                    },
                    'cac:Item': {
                        'cbc:Name': item.get('name', product_details.get('name', 'Product')),
                        'cbc:Description': product_details.get('description', item.get('name', 'Product')),
                        'cac:SellersItemIdentification': {
                            'cbc:ID': item.get('sku', '')
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
                            '@currencyID': order_data.get('order_currency_code', self.default_currency),
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
                            '@currencyID': order_data.get('order_currency_code', self.default_currency),
                            '#text': str(tax_amount)
                        },
                        'cac:TaxSubtotal': {
                            'cbc:TaxableAmount': {
                                '@currencyID': order_data.get('order_currency_code', self.default_currency),
                                '#text': str(line_total)
                            },
                            'cbc:TaxAmount': {
                                '@currencyID': order_data.get('order_currency_code', self.default_currency),
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
            raise MagentoTransformationError(f"Failed to build invoice lines: {e}")
    
    async def _calculate_tax_totals(
        self,
        order_data: Dict[str, Any],
        invoice_lines: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate tax totals for the invoice."""
        try:
            tax_amount = Decimal(str(order_data.get('tax_amount', 0)))
            subtotal = Decimal(str(order_data.get('subtotal', 0)))
            
            # If no tax amount in order, calculate from subtotal
            if tax_amount == 0 and subtotal > 0:
                # Assume VAT-inclusive pricing
                tax_amount = subtotal * self.vat_rate / (1 + self.vat_rate)
                subtotal = subtotal - tax_amount
            
            return [{
                'cbc:TaxAmount': {
                    '@currencyID': order_data.get('order_currency_code', self.default_currency),
                    '#text': str(tax_amount)
                },
                'cac:TaxSubtotal': {
                    'cbc:TaxableAmount': {
                        '@currencyID': order_data.get('order_currency_code', self.default_currency),
                        '#text': str(subtotal)
                    },
                    'cbc:TaxAmount': {
                        '@currencyID': order_data.get('order_currency_code', self.default_currency),
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
            raise MagentoTransformationError(f"Failed to calculate tax totals: {e}")
    
    async def _calculate_monetary_totals(
        self,
        order_data: Dict[str, Any],
        tax_totals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate monetary totals for the invoice."""
        try:
            subtotal = Decimal(str(order_data.get('subtotal', 0)))
            tax_amount = Decimal(str(order_data.get('tax_amount', 0)))
            discount_amount = abs(Decimal(str(order_data.get('discount_amount', 0))))
            shipping_amount = Decimal(str(order_data.get('shipping_amount', 0)))
            grand_total = Decimal(str(order_data.get('grand_total', 0)))
            
            # Calculate line extension amount (subtotal before tax)
            line_extension_amount = subtotal
            
            # Calculate tax exclusive amount
            tax_exclusive_amount = line_extension_amount - discount_amount + shipping_amount
            
            # Calculate tax inclusive amount
            tax_inclusive_amount = tax_exclusive_amount + tax_amount
            
            # Calculate payable amount (should match grand_total)
            payable_amount = grand_total
            
            return {
                'cbc:LineExtensionAmount': {
                    '@currencyID': order_data.get('order_currency_code', self.default_currency),
                    '#text': str(line_extension_amount)
                },
                'cbc:TaxExclusiveAmount': {
                    '@currencyID': order_data.get('order_currency_code', self.default_currency),
                    '#text': str(tax_exclusive_amount)
                },
                'cbc:TaxInclusiveAmount': {
                    '@currencyID': order_data.get('order_currency_code', self.default_currency),
                    '#text': str(tax_inclusive_amount)
                },
                'cbc:AllowanceTotalAmount': {
                    '@currencyID': order_data.get('order_currency_code', self.default_currency),
                    '#text': str(discount_amount)
                },
                'cbc:PayableAmount': {
                    '@currencyID': order_data.get('order_currency_code', self.default_currency),
                    '#text': str(payable_amount)
                }
            }
            
        except Exception as e:
            raise MagentoTransformationError(f"Failed to calculate monetary totals: {e}")
    
    async def _build_payment_means(self, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build payment means information."""
        try:
            payment_info = order_data.get('payment', {})
            payment_method = payment_info.get('method', 'unknown')
            
            # Map Magento payment methods to standard codes
            payment_code_mapping = {
                'checkmo': '30',      # Credit transfer
                'banktransfer': '30', # Credit transfer
                'cashondelivery': '10', # Cash
                'paypal': '48',       # Card payment
                'stripe': '48',       # Card payment
                'square': '48',       # Card payment
                'authorizenet': '48', # Card payment
                'braintree': '48',    # Card payment
                'paystack': '48',     # Card payment (Nigerian)
                'flutterwave': '48',  # Card payment (Nigerian)
            }
            
            payment_code = payment_code_mapping.get(payment_method, '1')  # Default: other
            
            return [{
                'cbc:PaymentMeansCode': payment_code,
                'cbc:PaymentID': str(order_data.get('increment_id', '')),
                'cac:PayeeFinancialAccount': {
                    'cbc:ID': payment_info.get('account_number', 'N/A'),
                    'cbc:Name': payment_method.title()
                }
            }]
            
        except Exception as e:
            raise MagentoTransformationError(f"Failed to build payment means: {e}")
    
    def _parse_date(self, date_string: Optional[str]) -> datetime:
        """Parse date string to datetime object."""
        if not date_string:
            return datetime.now()
        
        try:
            # Handle various Magento date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_string, fmt)
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