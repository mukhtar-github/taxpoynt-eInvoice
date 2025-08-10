"""
Sage Business Cloud Accounting UBL Transformer
Transforms Sage accounting data to UBL 2.1 format for FIRS e-invoicing.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from .exceptions import SageTransformationError
from ....connector_framework.base_accounting_connector import AccountingTransaction, AccountingContact
from .....core.invoice_processing.ubl_models import (
    UBLInvoice,
    UBLDocumentReference,
    UBLParty,
    UBLAddress,
    UBLContact as UBLContactInfo,
    UBLMonetaryTotal,
    UBLInvoiceLine,
    UBLTaxTotal,
    UBLTaxSubtotal,
    UBLTaxCategory,
    UBLClassifiedTaxCategory,
    UBLItem,
    UBLPrice,
    UBLAllowanceCharge
)


class SageUBLTransformer:
    """
    Transforms Sage Business Cloud Accounting data to UBL 2.1 format.
    
    Handles:
    - Invoice transformation to UBL Invoice
    - Contact transformation to UBL Party
    - Line item transformation to UBL InvoiceLine
    - Sage-specific tax handling and UBL TaxTotal generation
    - Multi-currency support with exchange rates
    - UK/Nigerian tax compliance
    """
    
    def __init__(self, business_info: Dict[str, Any]):
        """
        Initialize UBL transformer.
        
        Args:
            business_info: Sage business information
        """
        self.business_info = business_info
        self.logger = logging.getLogger(__name__)
        
        # Nigerian tax configuration
        self.vat_rate = Decimal('0.075')  # 7.5% VAT
        self.default_currency = 'NGN'
        self.country_code = 'NG'
        
        # UK tax configuration (Sage is UK-based)
        self.uk_vat_rate = Decimal('0.20')  # 20% VAT
        self.uk_currency = 'GBP'
        self.uk_country_code = 'GB'
        
        # Sage tax type mappings
        self.tax_category_mappings = {
            'STANDARD': 'S',  # Standard rate
            'REDUCED': 'AA',  # Reduced rate
            'ZERO': 'Z',      # Zero rated
            'EXEMPT': 'E',    # Exempt
            'REVERSE_CHARGE': 'AE',  # Reverse charge
            'OUT_OF_SCOPE': 'O'      # Out of scope
        }
    
    def transform_invoice_to_ubl(self, transaction: AccountingTransaction) -> UBLInvoice:
        """
        Transform Sage invoice to UBL Invoice.
        
        Args:
            transaction: Normalized accounting transaction from Sage
            
        Returns:
            UBL Invoice document
            
        Raises:
            SageTransformationError: Transformation errors
        """
        try:
            self.logger.info(f"Transforming Sage invoice {transaction.id} to UBL")
            
            # Generate UBL UUID
            ubl_uuid = uuid.uuid4()
            
            # Determine invoice type code based on transaction type
            invoice_type_code = "380"  # Commercial invoice (default)
            customization_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
            
            if hasattr(transaction, 'metadata') and transaction.metadata:
                sage_type = transaction.metadata.get('sage_type', 'SALES_INVOICE')
                if sage_type == 'PURCHASE_INVOICE':
                    invoice_type_code = "380"  # Still commercial invoice but from supplier perspective
                elif sage_type in ['SALES_CREDIT_NOTE', 'PURCHASE_CREDIT_NOTE']:
                    invoice_type_code = "381"  # Credit note
                    customization_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0#creditnote"
            
            # Create UBL Invoice
            ubl_invoice = UBLInvoice(
                ubl_version_id="2.1",
                customization_id=customization_id,
                profile_id="urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
                id=transaction.document_number or transaction.id,
                issue_date=transaction.date,
                due_date=transaction.due_date,
                invoice_type_code=invoice_type_code,
                note=[transaction.notes] if transaction.notes else [],
                document_currency_code=transaction.currency_code or self.default_currency,
                accounting_supplier_party=self._create_supplier_party(),
                accounting_customer_party=self._create_customer_party(transaction.contact),
                legal_monetary_total=self._create_monetary_total(transaction),
                invoice_line=self._create_invoice_lines(transaction.line_items, transaction.currency_code),
                uuid=str(ubl_uuid)
            )
            
            # Add tax totals if there are taxes
            if transaction.tax_amount and transaction.tax_amount > 0:
                ubl_invoice.tax_total = [self._create_tax_total(transaction)]
            
            # Add document references if available
            if transaction.reference:
                ubl_invoice.order_reference = UBLDocumentReference(
                    id=transaction.reference
                )
            
            # Add payment terms if due date is available
            if transaction.due_date and transaction.date:
                payment_days = (transaction.due_date - transaction.date).days
                if payment_days > 0:
                    ubl_invoice.payment_terms = [{
                        "note": [f"Payment due within {payment_days} days"],
                        "settlement_period": {
                            "duration_measure": {
                                "value": payment_days,
                                "unit_code": "DAY"
                            }
                        }
                    }]
            
            # Add exchange rate information for multi-currency invoices
            if hasattr(transaction, 'metadata') and transaction.metadata:
                exchange_rate = transaction.metadata.get('exchange_rate')
                if exchange_rate and exchange_rate != 1.0:
                    ubl_invoice.exchange_rate = [{
                        "source_currency_code": transaction.currency_code,
                        "target_currency_code": self.default_currency,
                        "calculation_rate": float(exchange_rate),
                        "date": transaction.date.strftime('%Y-%m-%d') if transaction.date else None
                    }]
            
            self.logger.info(f"Successfully transformed Sage invoice {transaction.id} to UBL")
            return ubl_invoice
            
        except Exception as e:
            self.logger.error(f"Failed to transform Sage invoice {transaction.id} to UBL: {str(e)}")
            raise SageTransformationError(f"UBL transformation failed: {str(e)}")
    
    def _create_supplier_party(self) -> UBLParty:
        """Create UBL supplier party from business info."""
        business_data = self.business_info if isinstance(self.business_info, dict) else {}
        
        # Business address
        main_address = business_data.get('main_address', {})
        
        supplier_address = UBLAddress(
            street_name=main_address.get('address_line_1', ''),
            additional_street_name=main_address.get('address_line_2', ''),
            city_name=main_address.get('city', ''),
            postal_zone=main_address.get('postal_code', ''),
            country_subentity=main_address.get('region', ''),
            country_identification_code=main_address.get('country', {}).get('id', self.country_code) if main_address.get('country') else self.country_code
        )
        
        # Business contact
        supplier_contact = UBLContactInfo(
            name=business_data.get('name', ''),
            telephone=business_data.get('telephone', ''),
            electronic_mail=business_data.get('email', '')
        )
        
        # Tax registration
        tax_number = business_data.get('tax_number', '')
        
        return UBLParty(
            party_name=[{"name": business_data.get('name', '')}],
            postal_address=supplier_address,
            party_tax_scheme=[{
                "company_id": tax_number,
                "tax_scheme": {
                    "id": "VAT",
                    "name": "Value Added Tax"
                }
            }] if tax_number else [],
            party_legal_entity=[{
                "registration_name": business_data.get('name', ''),
                "company_id": business_data.get('id', ''),
                "company_legal_form": business_data.get('business_type', '')
            }],
            contact=supplier_contact
        )
    
    def _create_customer_party(self, contact: AccountingContact) -> UBLParty:
        """Create UBL customer party from contact."""
        # Customer address
        customer_address = UBLAddress(
            street_name=contact.address.get('line1', ''),
            additional_street_name=contact.address.get('line2', ''),
            city_name=contact.address.get('city', ''),
            postal_zone=contact.address.get('postal_code', ''),
            country_subentity=contact.address.get('region', contact.address.get('state', '')),
            country_identification_code=contact.address.get('country', self.country_code)
        )
        
        # Customer contact
        customer_contact = UBLContactInfo(
            name=contact.name,
            telephone=contact.phone,
            electronic_mail=contact.email
        )
        
        return UBLParty(
            party_name=[{"name": contact.name}],
            postal_address=customer_address,
            party_tax_scheme=[{
                "company_id": contact.tax_number or '',
                "tax_scheme": {
                    "id": "VAT",
                    "name": "Value Added Tax"
                }
            }] if contact.tax_number else [],
            party_legal_entity=[{
                "registration_name": contact.name,
                "company_id": contact.tax_number or contact.id
            }],
            contact=customer_contact
        )
    
    def _create_monetary_total(self, transaction: AccountingTransaction) -> UBLMonetaryTotal:
        """Create UBL monetary total from transaction."""
        currency_code = transaction.currency_code or self.default_currency
        
        return UBLMonetaryTotal(
            line_extension_amount={
                "value": float(transaction.subtotal_amount),
                "currency_id": currency_code
            },
            tax_exclusive_amount={
                "value": float(transaction.subtotal_amount),
                "currency_id": currency_code
            },
            tax_inclusive_amount={
                "value": float(transaction.total_amount),
                "currency_id": currency_code
            },
            allowance_total_amount={
                "value": 0.0,  # Calculate from line items if needed
                "currency_id": currency_code
            },
            charge_total_amount={
                "value": 0.0,  # Calculate from line items if needed
                "currency_id": currency_code
            },
            payable_amount={
                "value": float(transaction.balance_amount),
                "currency_id": currency_code
            }
        )
    
    def _create_invoice_lines(self, line_items: List[Dict[str, Any]], currency_code: Optional[str]) -> List[UBLInvoiceLine]:
        """Create UBL invoice lines from Sage line items."""
        ubl_lines = []
        currency = currency_code or self.default_currency
        
        for idx, line_item in enumerate(line_items, 1):
            try:
                # Extract line item data
                quantity = Decimal(str(line_item.get('quantity', 1)))
                unit_price = Decimal(str(line_item.get('unit_price', 0)))
                net_amount = Decimal(str(line_item.get('net_amount', 0)))
                tax_amount = Decimal(str(line_item.get('tax_amount', 0)))
                total_amount = Decimal(str(line_item.get('total_amount', 0)))
                discount_percentage = Decimal(str(line_item.get('discount_percentage', 0)))
                
                # Calculate discount amount if percentage is given
                discount_amount = Decimal('0')
                if discount_percentage > 0:
                    gross_amount = net_amount / (1 - (discount_percentage / 100))
                    discount_amount = gross_amount - net_amount
                
                # Get tax information
                tax_rate_percentage = Decimal(str(line_item.get('tax_rate_percentage', 0)))
                tax_rate_name = line_item.get('tax_rate_name', '')
                
                # Determine tax category based on tax rate
                tax_category_id = 'S'  # Standard rate default
                if tax_rate_percentage == 0:
                    if 'zero' in tax_rate_name.lower():
                        tax_category_id = 'Z'  # Zero rated
                    elif 'exempt' in tax_rate_name.lower():
                        tax_category_id = 'E'  # Exempt
                    else:
                        tax_category_id = 'O'  # Out of scope
                elif tax_rate_percentage < 10:
                    tax_category_id = 'AA'  # Reduced rate
                
                # Create UBL line
                ubl_line = UBLInvoiceLine(
                    id=str(idx),
                    note=[line_item.get('description', '')] if line_item.get('description') else [],
                    invoiced_quantity={
                        "value": float(quantity),
                        "unit_code": "EA"  # Each (default unit)
                    },
                    line_extension_amount={
                        "value": float(net_amount),
                        "currency_id": currency
                    },
                    item=UBLItem(
                        description=[line_item.get('description', '')],
                        name=line_item.get('product_code', '') or line_item.get('description', ''),
                        sellers_item_identification={
                            "id": line_item.get('product_code', '')
                        } if line_item.get('product_code') else None,
                        classified_tax_category=[
                            UBLClassifiedTaxCategory(
                                id=tax_category_id,
                                percent=float(tax_rate_percentage),
                                tax_scheme={
                                    "id": "VAT",
                                    "name": "Value Added Tax"
                                }
                            )
                        ]
                    ),
                    price=UBLPrice(
                        price_amount={
                            "value": float(unit_price),
                            "currency_id": currency
                        }
                    )
                )
                
                # Add allowance/charge for discounts
                if discount_amount > 0:
                    ubl_line.allowance_charge = [
                        UBLAllowanceCharge(
                            charge_indicator=False,  # False = allowance (discount)
                            allowance_charge_reason_code="95",  # Discount
                            allowance_charge_reason="Discount",
                            multiplier_factor_numeric=float(discount_percentage / 100) if discount_percentage > 0 else None,
                            amount={
                                "value": float(discount_amount),
                                "currency_id": currency
                            },
                            base_amount={
                                "value": float(net_amount + discount_amount),
                                "currency_id": currency
                            }
                        )
                    ]
                
                # Add tax total for line if applicable
                if tax_amount > 0:
                    ubl_line.tax_total = [{
                        "tax_amount": {
                            "value": float(tax_amount),
                            "currency_id": currency
                        },
                        "tax_subtotal": [{
                            "taxable_amount": {
                                "value": float(net_amount),
                                "currency_id": currency
                            },
                            "tax_amount": {
                                "value": float(tax_amount),
                                "currency_id": currency
                            },
                            "tax_category": {
                                "id": tax_category_id,
                                "percent": float(tax_rate_percentage),
                                "tax_scheme": {
                                    "id": "VAT",
                                    "name": "Value Added Tax"
                                }
                            }
                        }]
                    }]
                
                ubl_lines.append(ubl_line)
                
            except Exception as e:
                self.logger.warning(f"Failed to transform line item {idx}: {str(e)}")
                continue
        
        return ubl_lines
    
    def _create_tax_total(self, transaction: AccountingTransaction) -> UBLTaxTotal:
        """Create UBL tax total from transaction."""
        currency_code = transaction.currency_code or self.default_currency
        
        # Calculate tax details
        taxable_amount = transaction.subtotal_amount
        tax_amount = transaction.tax_amount
        
        # Determine tax percentage
        if tax_amount > 0 and taxable_amount > 0:
            tax_percent = float((tax_amount / taxable_amount * 100))
        else:
            tax_percent = 0.0
        
        # Determine tax category based on currency and percentage
        tax_category_id = "S"  # Standard rate
        if currency_code == 'NGN':
            # Nigerian VAT
            if tax_percent == 0:
                tax_category_id = "Z"  # Zero rated
            elif abs(tax_percent - 7.5) < 0.1:
                tax_category_id = "S"  # Standard rate (7.5%)
        elif currency_code == 'GBP':
            # UK VAT
            if tax_percent == 0:
                tax_category_id = "Z"  # Zero rated
            elif abs(tax_percent - 20.0) < 0.1:
                tax_category_id = "S"  # Standard rate (20%)
            elif abs(tax_percent - 5.0) < 0.1:
                tax_category_id = "AA"  # Reduced rate (5%)
        
        return UBLTaxTotal(
            tax_amount={
                "value": float(tax_amount),
                "currency_id": currency_code
            },
            tax_subtotal=[
                UBLTaxSubtotal(
                    taxable_amount={
                        "value": float(taxable_amount),
                        "currency_id": currency_code
                    },
                    tax_amount={
                        "value": float(tax_amount),
                        "currency_id": currency_code
                    },
                    tax_category=UBLTaxCategory(
                        id=tax_category_id,
                        percent=tax_percent,
                        tax_scheme={
                            "id": "VAT",
                            "name": "Value Added Tax"
                        }
                    )
                )
            ]
        )
    
    def validate_ubl_invoice(self, ubl_invoice: UBLInvoice) -> List[str]:
        """
        Validate UBL invoice for FIRS compliance.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Required fields validation
            if not ubl_invoice.id:
                errors.append("Invoice ID is required")
            
            if not ubl_invoice.issue_date:
                errors.append("Issue date is required")
            
            if not ubl_invoice.accounting_supplier_party:
                errors.append("Supplier party is required")
            
            if not ubl_invoice.accounting_customer_party:
                errors.append("Customer party is required")
            
            if not ubl_invoice.legal_monetary_total:
                errors.append("Monetary total is required")
            
            if not ubl_invoice.invoice_line:
                errors.append("At least one invoice line is required")
            
            # Currency validation
            supported_currencies = ['NGN', 'GBP', 'USD', 'EUR']
            if ubl_invoice.document_currency_code not in supported_currencies:
                errors.append(f"Unsupported currency: {ubl_invoice.document_currency_code}")
            
            # Supplier validation
            supplier = ubl_invoice.accounting_supplier_party
            if supplier and not supplier.party_name:
                errors.append("Supplier name is required")
            
            # Customer validation
            customer = ubl_invoice.accounting_customer_party
            if customer and not customer.party_name:
                errors.append("Customer name is required")
            
            # Line items validation
            for idx, line in enumerate(ubl_invoice.invoice_line, 1):
                if not line.item or not line.item.name:
                    errors.append(f"Line {idx}: Item name is required")
                
                if not line.invoiced_quantity or line.invoiced_quantity.get('value', 0) <= 0:
                    errors.append(f"Line {idx}: Quantity must be positive")
                
                if not line.line_extension_amount or line.line_extension_amount.get('value', 0) < 0:
                    errors.append(f"Line {idx}: Line amount cannot be negative")
            
            # Nigerian specific validation
            if ubl_invoice.document_currency_code == 'NGN':
                if not ubl_invoice.tax_total:
                    # Check if VAT should be applied (for amounts above threshold)
                    total_amount = ubl_invoice.legal_monetary_total.tax_inclusive_amount.get('value', 0)
                    if total_amount > 25000:  # NGN 25,000 VAT threshold
                        errors.append("VAT is required for invoices above NGN 25,000")
                
                # Validate supplier tax number for Nigerian transactions
                supplier_tax_schemes = ubl_invoice.accounting_supplier_party.party_tax_scheme or []
                if not any(scheme.get('company_id') for scheme in supplier_tax_schemes):
                    errors.append("Supplier tax number (TIN) is required for Nigerian invoices")
            
            # UK specific validation
            elif ubl_invoice.document_currency_code == 'GBP':
                # UK VAT validation
                if ubl_invoice.tax_total:
                    for tax_total in ubl_invoice.tax_total:
                        for tax_subtotal in tax_total.tax_subtotal:
                            tax_percent = tax_subtotal.tax_category.percent
                            if tax_percent not in [0, 5, 20]:  # UK VAT rates
                                errors.append(f"Invalid UK VAT rate: {tax_percent}%. Valid rates are 0%, 5%, 20%")
        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def create_credit_note_ubl(self, transaction: AccountingTransaction) -> UBLInvoice:
        """
        Create UBL credit note from accounting transaction.
        
        Args:
            transaction: Credit note transaction
            
        Returns:
            UBL Invoice with credit note type
        """
        try:
            # Transform as regular invoice but adjust for credit note
            ubl_invoice = self.transform_invoice_to_ubl(transaction)
            
            # Modify for credit note
            ubl_invoice.invoice_type_code = "381"  # Credit note
            ubl_invoice.customization_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0#creditnote"
            
            # Note: Sage credit notes typically already have correct amounts
            # No need to invert amounts as they're already correctly signed
            
            return ubl_invoice
            
        except Exception as e:
            raise SageTransformationError(f"Credit note transformation failed: {str(e)}")
    
    def extract_metadata_for_firs(self, transaction: AccountingTransaction) -> Dict[str, Any]:
        """
        Extract metadata required for FIRS submission.
        
        Args:
            transaction: Accounting transaction
            
        Returns:
            FIRS metadata dictionary
        """
        metadata = transaction.metadata or {}
        
        return {
            'source_system': 'Sage Business Cloud Accounting',
            'source_transaction_id': transaction.id,
            'source_document_number': transaction.document_number,
            'sage_id': metadata.get('sage_id'),
            'sage_type': metadata.get('sage_type'),
            'created_at': metadata.get('created_at'),
            'updated_at': metadata.get('updated_at'),
            'transformation_timestamp': datetime.now().isoformat(),
            'currency_code': transaction.currency_code,
            'exchange_rate': metadata.get('exchange_rate'),
            'inverse_exchange_rate': metadata.get('inverse_exchange_rate'),
            'base_currency_total_amount': metadata.get('base_currency_total_amount'),
            'base_currency_net_amount': metadata.get('base_currency_net_amount'),
            'base_currency_tax_amount': metadata.get('base_currency_tax_amount'),
            'total_amount': float(transaction.total_amount),
            'tax_amount': float(transaction.tax_amount),
            'contact_id': transaction.contact.id if transaction.contact else None,
            'contact_name': transaction.contact.name if transaction.contact else None,
            'business_type': 'accounting_software',
            'integration_version': '1.0.0',
            'sage_status_code': metadata.get('sage_status_code'),
            'tax_analysis': metadata.get('tax_analysis', []),
            'payments_count': len(metadata.get('payments', []))
        }
    
    def handle_multi_currency_transaction(self, transaction: AccountingTransaction, base_currency: str = 'NGN') -> Dict[str, Any]:
        """
        Handle multi-currency transactions for FIRS reporting.
        
        Args:
            transaction: Transaction in foreign currency
            base_currency: Base currency for reporting (default NGN)
            
        Returns:
            Currency conversion information
        """
        if not transaction.currency_code or transaction.currency_code == base_currency:
            return {
                'requires_conversion': False,
                'original_currency': transaction.currency_code or base_currency,
                'base_currency': base_currency
            }
        
        metadata = transaction.metadata or {}
        exchange_rate = metadata.get('exchange_rate', 1.0)
        inverse_exchange_rate = metadata.get('inverse_exchange_rate', 1.0)
        
        # Use appropriate exchange rate
        conversion_rate = exchange_rate if exchange_rate != 1.0 else inverse_exchange_rate
        
        # Get base currency amounts if available from Sage
        base_currency_amounts = {
            'subtotal_amount': metadata.get('base_currency_net_amount'),
            'tax_amount': metadata.get('base_currency_tax_amount'),
            'total_amount': metadata.get('base_currency_total_amount')
        }
        
        # Calculate if not provided
        if not base_currency_amounts['total_amount']:
            base_currency_amounts = {
                'subtotal_amount': float(transaction.subtotal_amount * Decimal(str(conversion_rate))),
                'tax_amount': float(transaction.tax_amount * Decimal(str(conversion_rate))),
                'total_amount': float(transaction.total_amount * Decimal(str(conversion_rate))),
                'paid_amount': float(transaction.paid_amount * Decimal(str(conversion_rate))),
                'balance_amount': float(transaction.balance_amount * Decimal(str(conversion_rate)))
            }
        
        return {
            'requires_conversion': True,
            'original_currency': transaction.currency_code,
            'base_currency': base_currency,
            'exchange_rate': conversion_rate,
            'inverse_exchange_rate': inverse_exchange_rate,
            'conversion_date': transaction.date.isoformat() if transaction.date else None,
            'original_amounts': {
                'subtotal_amount': float(transaction.subtotal_amount),
                'tax_amount': float(transaction.tax_amount),
                'total_amount': float(transaction.total_amount),
                'paid_amount': float(transaction.paid_amount),
                'balance_amount': float(transaction.balance_amount)
            },
            'converted_amounts': base_currency_amounts,
            'sage_base_currency_data': {
                'base_currency_total_amount': metadata.get('base_currency_total_amount'),
                'base_currency_net_amount': metadata.get('base_currency_net_amount'),
                'base_currency_tax_amount': metadata.get('base_currency_tax_amount')
            }
        }