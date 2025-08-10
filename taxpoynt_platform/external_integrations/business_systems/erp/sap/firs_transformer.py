"""
SAP FIRS Transformation Module
Handles transformation of SAP invoice data to FIRS-compliant formats.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Union

from ....connector_framework import ERPDataError
from .exceptions import SAPODataError

logger = logging.getLogger(__name__)


class SAPFIRSTransformer:
    """Handles transformation of SAP data to FIRS-compliant formats."""
    
    def __init__(self, data_extractor):
        """Initialize with a data extractor instance."""
        self.data_extractor = data_extractor
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform SAP invoice data to FIRS-compliant format"""
        try:
            # Determine document type mapping
            firs_doc_type = self._map_sap_doc_type_to_firs(
                invoice_data.get('sap_document_type', invoice_data.get('document_type', ''))
            )
            
            # Basic UBL BIS 3.0 transformation
            firs_invoice = {
                'invoice_type_code': firs_doc_type,
                'id': invoice_data.get('name', invoice_data.get('id', '')),
                'issue_date': invoice_data.get('invoice_date', ''),
                'due_date': invoice_data.get('invoice_date_due', ''),
                'document_currency_code': invoice_data.get('currency', 'EUR'),
                'accounting_supplier_party': {
                    'party': {
                        'party_name': {
                            'name': invoice_data.get('company', {}).get('name', 'SAP Company')
                        },
                        'party_tax_scheme': {
                            'company_id': invoice_data.get('company', {}).get('tax_id', ''),
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }
                },
                'accounting_customer_party': {
                    'party': {
                        'party_name': {
                            'name': invoice_data.get('partner', {}).get('name', 'SAP Customer')
                        },
                        'party_tax_scheme': {
                            'company_id': invoice_data.get('partner', {}).get('tax_number', ''),
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }
                },
                'legal_monetary_total': {
                    'line_extension_amount': invoice_data.get('amount_untaxed', invoice_data.get('amount_total', 0)),
                    'tax_exclusive_amount': invoice_data.get('amount_untaxed', invoice_data.get('amount_total', 0)),
                    'tax_inclusive_amount': invoice_data.get('amount_total', 0),
                    'allowance_total_amount': 0,
                    'charge_total_amount': 0,
                    'prepaid_amount': 0,
                    'payable_amount': invoice_data.get('amount_total', 0)
                },
                'invoice_line': []
            }
            
            # Transform invoice lines (if available)
            invoice_lines = invoice_data.get('invoice_lines', [])
            if not invoice_lines and invoice_data.get('journal_lines'):
                # Handle journal entries differently
                invoice_lines = self._convert_journal_lines_to_invoice_lines(
                    invoice_data.get('journal_lines', [])
                )
            
            for i, line in enumerate(invoice_lines):
                firs_line = {
                    'id': str(line.get('id', i + 1)),
                    'invoiced_quantity': {
                        'quantity': line.get('quantity', 1),
                        'unit_code': 'C62'  # Default unit
                    },
                    'line_extension_amount': line.get('amount', line.get('price_subtotal', 0)),
                    'item': {
                        'description': line.get('description', line.get('name', 'SAP Line Item')),
                        'name': line.get('product_name', line.get('gl_account', '')),
                        'sellers_item_identification': {
                            'id': line.get('product_code', line.get('gl_account', ''))
                        }
                    },
                    'price': {
                        'price_amount': line.get('price_unit', line.get('amount', 0)),
                        'base_quantity': {
                            'quantity': 1,
                            'unit_code': 'C62'
                        }
                    }
                }
                
                # Add tax information if available
                tax_amount = line.get('tax_amount', 0)
                if tax_amount > 0:
                    firs_line['tax_total'] = {
                        'tax_amount': tax_amount,
                        'tax_subtotal': [{
                            'taxable_amount': line.get('amount', line.get('price_subtotal', 0)),
                            'tax_amount': tax_amount,
                            'tax_category': {
                                'id': 'S',  # Standard rate
                                'percent': 19.0,  # Default German VAT rate for SAP
                                'tax_scheme': {
                                    'id': 'VAT'
                                }
                            }
                        }]
                    }
                
                firs_invoice['invoice_line'].append(firs_line)
            
            # Add tax totals
            tax_amount = invoice_data.get('amount_tax', 0)
            if tax_amount > 0:
                firs_invoice['tax_total'] = {
                    'tax_amount': tax_amount,
                    'tax_subtotal': [{
                        'taxable_amount': invoice_data.get('amount_untaxed', invoice_data.get('amount_total', 0)),
                        'tax_amount': tax_amount,
                        'tax_category': {
                            'id': 'S',
                            'percent': 19.0,  # Default German VAT rate
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }]
                }
            
            return {
                'firs_invoice': firs_invoice,
                'source_format': 'sap_native',
                'target_format': target_format,
                'transformation_metadata': {
                    'transformation_date': datetime.utcnow().isoformat(),
                    'source_invoice_id': invoice_data.get('id'),
                    'sap_document_type': invoice_data.get('sap_document_type', ''),
                    'sap_document_number': invoice_data.get('sap_billing_document', invoice_data.get('sap_accounting_document', '')),
                    'erp_type': 'sap',
                    'data_source': invoice_data.get('source', 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"Error transforming SAP invoice to FIRS format: {str(e)}")
            raise ERPDataError(f"Error transforming SAP invoice to FIRS format: {str(e)}")
    
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate SAP invoice data before FIRS submission.
        
        Args:
            invoice_data: Invoice data to validate
            
        Returns:
            Validation result with errors and warnings
        """
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'invoice_id': invoice_data.get('id')
            }
            
            # Required field validations
            required_fields = ['id', 'name', 'invoice_date', 'amount_total']
            
            for field in required_fields:
                if not invoice_data.get(field):
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['is_valid'] = False
            
            # Partner validation
            partner = invoice_data.get('partner', {})
            if partner:
                if not partner.get('id') and not partner.get('sap_business_partner'):
                    validation_result['errors'].append("Customer/Partner ID is required")
                    validation_result['is_valid'] = False
                
                if not partner.get('name'):
                    validation_result['warnings'].append("Customer/Partner name is missing")
            else:
                validation_result['warnings'].append("No partner information available")
            
            # Amount validation
            amount_total = invoice_data.get('amount_total', 0)
            if isinstance(amount_total, (int, float)) and amount_total <= 0:
                validation_result['errors'].append("Invoice total must be greater than 0")
                validation_result['is_valid'] = False
            
            # Date validation
            invoice_date = invoice_data.get('invoice_date')
            if invoice_date:
                try:
                    datetime.fromisoformat(invoice_date.replace('Z', '+00:00'))
                except ValueError:
                    validation_result['errors'].append("Invalid invoice date format")
                    validation_result['is_valid'] = False
            
            # SAP-specific validations
            if not invoice_data.get('sap_document_type') and not invoice_data.get('document_type'):
                validation_result['warnings'].append("SAP document type not specified")
            
            # Currency validation
            currency = invoice_data.get('currency', '')
            if currency and len(currency) != 3:
                validation_result['warnings'].append("Currency code should be 3 characters (ISO 4217)")
            
            # Line items validation (if available)
            invoice_lines = invoice_data.get('invoice_lines', [])
            journal_lines = invoice_data.get('journal_lines', [])
            
            if not invoice_lines and not journal_lines:
                validation_result['warnings'].append("No line items found - this may affect FIRS transformation quality")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating SAP invoice data: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'invoice_id': invoice_data.get('id')
            }
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in SAP system"""
        try:
            # Note: SAP invoice status updates would typically require
            # different APIs and might not be possible for posted documents
            logger.info(f"Updating SAP invoice {invoice_id} status: {status_data}")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'status_updated': False,  # SAP documents are typically immutable once posted
                'message': 'SAP documents cannot be modified after posting',
                'new_status': status_data.get('status'),
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating SAP invoice status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'invoice_id': invoice_id
            }
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from SAP"""
        try:
            # In a real implementation, this would query SAP tax configuration
            # For now, return common German/European tax settings
            return {
                'default_vat_rate': 19.0,  # German standard VAT rate
                'reduced_vat_rate': 7.0,   # German reduced VAT rate
                'tax_codes': {
                    'VAT': 'Value Added Tax',
                    'MWST': 'Mehrwertsteuer (German VAT)'
                },
                'supported_tax_schemes': ['VAT', 'MWST'],
                'currency': 'EUR',
                'country_codes': ['DE', 'AT', 'CH'],  # Common SAP deployment countries
                'sap_tax_procedures': ['TAXDEU', 'TAXAUT', 'TAXCHE']
            }
            
        except Exception as e:
            logger.error(f"Error retrieving SAP tax configuration: {str(e)}")
            raise SAPODataError(f"Error retrieving SAP tax configuration: {str(e)}")
    
    def _map_sap_doc_type_to_firs(self, sap_doc_type: str) -> str:
        """
        Map SAP document types to FIRS invoice type codes.
        
        Args:
            sap_doc_type: SAP document type code
            
        Returns:
            FIRS invoice type code
        """
        # SAP document type mappings to UBL invoice type codes
        sap_to_firs_mapping = {
            # Billing Document Types
            'F2': '380',    # Standard Invoice
            'F5': '381',    # Credit Memo
            'F8': '380',    # Pro Forma Invoice
            'G2': '326',    # Partial Invoice
            'L2': '380',    # Debit Memo
            'RE': '380',    # Invoice (Billing)
            'RK': '381',    # Credit Memo (Billing)
            
            # Accounting Document Types
            'RV': '380',    # Customer Invoice
            'DG': '381',    # Customer Credit Memo
            'DR': '380',    # Customer Invoice
            'KR': '380',    # Vendor Invoice
            'KG': '381',    # Vendor Credit Memo
            
            # Default fallback
            '': '380'       # Standard Invoice
        }
        
        return sap_to_firs_mapping.get(sap_doc_type, '380')
    
    def _convert_journal_lines_to_invoice_lines(self, journal_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert SAP journal entry lines to invoice line format."""
        invoice_lines = []
        
        for line in journal_lines:
            # Skip zero amount lines or control accounts
            amount = line.get('amount', 0)
            if amount == 0:
                continue
            
            # Convert journal line to invoice line format
            invoice_line = {
                'id': line.get('gl_account', ''),
                'description': f"GL Account: {line.get('gl_account', '')}",
                'gl_account': line.get('gl_account', ''),
                'amount': abs(amount),  # Use absolute value
                'quantity': 1,
                'price_unit': abs(amount),
                'currency': line.get('currency', 'EUR'),
                'business_partner': line.get('business_partner', ''),
                'debit_credit': line.get('debit_credit_indicator', '')
            }
            
            invoice_lines.append(invoice_line)
        
        return invoice_lines