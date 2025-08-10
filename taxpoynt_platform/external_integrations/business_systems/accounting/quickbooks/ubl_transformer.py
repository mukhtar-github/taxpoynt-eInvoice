"""
QuickBooks UBL Transformer
Transforms QuickBooks accounting data to UBL 2.1 format for FIRS e-invoicing.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from .exceptions import QuickBooksTransformationError
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


class QuickBooksUBLTransformer:
    """
    Transforms QuickBooks data to UBL 2.1 format.
    
    Handles:
    - Invoice transformation to UBL Invoice
    - Customer/vendor transformation to UBL Party
    - Line item transformation to UBL InvoiceLine
    - Tax calculation and UBL TaxTotal generation
    """
    
    def __init__(self, company_info: Dict[str, Any]):
        """
        Initialize UBL transformer.
        
        Args:
            company_info: QuickBooks company information
        """
        self.company_info = company_info
        self.logger = logging.getLogger(__name__)
        
        # Nigerian tax configuration
        self.vat_rate = Decimal('0.075')  # 7.5% VAT
        self.default_currency = 'NGN'
        self.country_code = 'NG'
    
    def transform_invoice_to_ubl(self, transaction: AccountingTransaction) -> UBLInvoice:
        """
        Transform QuickBooks invoice to UBL Invoice.
        
        Args:
            transaction: Normalized accounting transaction
            
        Returns:
            UBL Invoice document
            
        Raises:
            QuickBooksTransformationError: Transformation errors
        """
        try:
            self.logger.info(f"Transforming QuickBooks invoice {transaction.id} to UBL")
            
            # Generate UBL UUID
            ubl_uuid = uuid.uuid4()
            
            # Create UBL Invoice
            ubl_invoice = UBLInvoice(
                ubl_version_id="2.1",
                customization_id="urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
                profile_id="urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
                id=transaction.document_number or transaction.id,
                issue_date=transaction.date,
                due_date=transaction.due_date,
                invoice_type_code="380",  # Commercial invoice
                note=[transaction.notes] if transaction.notes else [],
                document_currency_code=transaction.currency_code or self.default_currency,
                accounting_supplier_party=self._create_supplier_party(),
                accounting_customer_party=self._create_customer_party(transaction.contact),
                legal_monetary_total=self._create_monetary_total(transaction),
                invoice_line=self._create_invoice_lines(transaction.line_items),
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
            
            self.logger.info(f"Successfully transformed invoice {transaction.id} to UBL")
            return ubl_invoice
            
        except Exception as e:
            self.logger.error(f"Failed to transform invoice {transaction.id} to UBL: {str(e)}")
            raise QuickBooksTransformationError(f"UBL transformation failed: {str(e)}")
    
    def _create_supplier_party(self) -> UBLParty:
        """Create UBL supplier party from company info."""
        company_data = self.company_info.get('QueryResponse', {}).get('CompanyInfo', [{}])[0]
        
        # Company address
        company_addr = company_data.get('CompanyAddr', {})
        supplier_address = UBLAddress(
            street_name=company_addr.get('Line1', ''),
            additional_street_name=company_addr.get('Line2', ''),
            city_name=company_addr.get('City', ''),
            postal_zone=company_addr.get('PostalCode', ''),
            country_subentity=company_addr.get('CountrySubDivisionCode', ''),
            country_identification_code=self.country_code
        )
        
        # Company contact
        supplier_contact = UBLContactInfo(
            name=company_data.get('LegalName', company_data.get('CompanyName', '')),
            telephone=company_data.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
            electronic_mail=company_data.get('Email', {}).get('Address', '')
        )
        
        return UBLParty(
            party_name=[{"name": company_data.get('LegalName', company_data.get('CompanyName', ''))}],
            postal_address=supplier_address,
            party_tax_scheme=[{
                "company_id": company_data.get('LegalAddr', {}).get('CountrySubDivisionCode', ''),
                "tax_scheme": {
                    "id": "VAT",
                    "name": "Value Added Tax"
                }
            }],
            party_legal_entity=[{
                "registration_name": company_data.get('LegalName', company_data.get('CompanyName', '')),
                "company_id": company_data.get('QBORealmID', '')
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
            country_subentity=contact.address.get('state', ''),
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
        return UBLMonetaryTotal(
            line_extension_amount={
                "value": float(transaction.subtotal_amount),
                "currency_id": transaction.currency_code or self.default_currency
            },
            tax_exclusive_amount={
                "value": float(transaction.subtotal_amount),
                "currency_id": transaction.currency_code or self.default_currency
            },
            tax_inclusive_amount={
                "value": float(transaction.total_amount),
                "currency_id": transaction.currency_code or self.default_currency
            },
            allowance_total_amount={
                "value": 0.0,
                "currency_id": transaction.currency_code or self.default_currency
            },
            charge_total_amount={
                "value": 0.0,
                "currency_id": transaction.currency_code or self.default_currency
            },
            payable_amount={
                "value": float(transaction.balance_amount),
                "currency_id": transaction.currency_code or self.default_currency
            }
        )
    
    def _create_invoice_lines(self, line_items: List[Dict[str, Any]]) -> List[UBLInvoiceLine]:
        """Create UBL invoice lines from line items."""
        ubl_lines = []
        
        for idx, line_item in enumerate(line_items, 1):
            try:
                # Calculate line amounts
                quantity = Decimal(str(line_item.get('quantity', 1)))
                unit_price = Decimal(str(line_item.get('unit_price', 0)))
                line_amount = Decimal(str(line_item.get('amount', 0)))
                tax_amount = Decimal(str(line_item.get('tax_amount', 0)))
                
                # Create UBL line
                ubl_line = UBLInvoiceLine(
                    id=str(idx),
                    note=[line_item.get('description', '')] if line_item.get('description') else [],
                    invoiced_quantity={
                        "value": float(quantity),
                        "unit_code": "EA"  # Each (default unit)
                    },
                    line_extension_amount={
                        "value": float(line_amount),
                        "currency_id": self.default_currency
                    },
                    item=UBLItem(
                        description=[line_item.get('item_name', '')],
                        name=line_item.get('item_name', ''),
                        sellers_item_identification={
                            "id": line_item.get('item_id', '')
                        } if line_item.get('item_id') else None,
                        classified_tax_category=[
                            UBLClassifiedTaxCategory(
                                id="S",  # Standard rate
                                percent=float(self.vat_rate * 100),
                                tax_scheme={
                                    "id": "VAT",
                                    "name": "Value Added Tax"
                                }
                            )
                        ] if tax_amount > 0 else []
                    ),
                    price=UBLPrice(
                        price_amount={
                            "value": float(unit_price),
                            "currency_id": self.default_currency
                        }
                    )
                )
                
                # Add tax total for line if applicable
                if tax_amount > 0:
                    ubl_line.tax_total = [{
                        "tax_amount": {
                            "value": float(tax_amount),
                            "currency_id": self.default_currency
                        },
                        "tax_subtotal": [{
                            "taxable_amount": {
                                "value": float(line_amount),
                                "currency_id": self.default_currency
                            },
                            "tax_amount": {
                                "value": float(tax_amount),
                                "currency_id": self.default_currency
                            },
                            "tax_category": {
                                "id": "S",
                                "percent": float(self.vat_rate * 100),
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
        # Calculate tax details
        taxable_amount = transaction.subtotal_amount
        tax_amount = transaction.tax_amount
        tax_percent = float((tax_amount / taxable_amount * 100) if taxable_amount > 0 else self.vat_rate * 100)
        
        return UBLTaxTotal(
            tax_amount={
                "value": float(tax_amount),
                "currency_id": transaction.currency_code or self.default_currency
            },
            tax_subtotal=[
                UBLTaxSubtotal(
                    taxable_amount={
                        "value": float(taxable_amount),
                        "currency_id": transaction.currency_code or self.default_currency
                    },
                    tax_amount={
                        "value": float(tax_amount),
                        "currency_id": transaction.currency_code or self.default_currency
                    },
                    tax_category=UBLTaxCategory(
                        id="S",  # Standard rate
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
            if ubl_invoice.document_currency_code not in ['NGN', 'USD', 'EUR', 'GBP']:
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
            
            # Tax validation for Nigerian invoices
            if ubl_invoice.document_currency_code == 'NGN':
                if not ubl_invoice.tax_total:
                    # Check if VAT should be applied (for amounts above threshold)
                    total_amount = ubl_invoice.legal_monetary_total.tax_inclusive_amount.get('value', 0)
                    if total_amount > 25000:  # NGN 25,000 VAT threshold
                        errors.append("VAT is required for invoices above NGN 25,000")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def create_credit_note_ubl(self, transaction: AccountingTransaction) -> UBLInvoice:
        """
        Create UBL credit note from accounting transaction.
        
        Args:
            transaction: Credit memo transaction
            
        Returns:
            UBL Invoice with credit note type
        """
        try:
            # Transform as regular invoice but adjust for credit note
            ubl_invoice = self.transform_invoice_to_ubl(transaction)
            
            # Modify for credit note
            ubl_invoice.invoice_type_code = "381"  # Credit note
            ubl_invoice.customization_id = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0#creditnote"
            
            # Invert amounts for credit note
            if ubl_invoice.legal_monetary_total:
                monetary_total = ubl_invoice.legal_monetary_total
                monetary_total.line_extension_amount['value'] *= -1
                monetary_total.tax_exclusive_amount['value'] *= -1
                monetary_total.tax_inclusive_amount['value'] *= -1
                monetary_total.payable_amount['value'] *= -1
            
            # Invert line amounts
            for line in ubl_invoice.invoice_line:
                if line.line_extension_amount:
                    line.line_extension_amount['value'] *= -1
                if line.price and line.price.price_amount:
                    line.price.price_amount['value'] *= -1
            
            # Invert tax amounts
            if ubl_invoice.tax_total:
                for tax_total in ubl_invoice.tax_total:
                    tax_total.tax_amount['value'] *= -1
                    for tax_subtotal in tax_total.tax_subtotal:
                        tax_subtotal.tax_amount['value'] *= -1
                        tax_subtotal.taxable_amount['value'] *= -1
            
            return ubl_invoice
            
        except Exception as e:
            raise QuickBooksTransformationError(f"Credit note transformation failed: {str(e)}")
    
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
            'source_system': 'QuickBooks Online',
            'source_transaction_id': transaction.id,
            'source_document_number': transaction.document_number,
            'quickbooks_id': metadata.get('quickbooks_id'),
            'sync_token': metadata.get('sync_token'),
            'created_time': metadata.get('created_time'),
            'last_updated_time': metadata.get('last_updated_time'),
            'transformation_timestamp': datetime.now().isoformat(),
            'currency_code': transaction.currency_code,
            'total_amount': float(transaction.total_amount),
            'tax_amount': float(transaction.tax_amount),
            'customer_id': transaction.contact.id if transaction.contact else None,
            'customer_name': transaction.contact.name if transaction.contact else None,
            'business_type': 'accounting_software',
            'integration_version': '1.0.0'
        }