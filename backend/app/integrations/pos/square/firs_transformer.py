"""Square POS to FIRS invoice format transformer."""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal, ROUND_HALF_UP

from app.integrations.pos.base_pos_connector import POSTransaction, POSLocation
from app.utils.irn_generator import generate_irn  # Assuming this exists based on docs


class SquareToFIRSTransformer:
    """Transforms Square POS transactions to FIRS-compliant invoice format."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize transformer with configuration.
        
        Args:
            config: Dictionary containing transformation configuration
                - business_id: TaxPoynt business UUID
                - service_id: FIRS-assigned service ID
                - default_currency: Default currency (NGN)
                - tax_rate: Default VAT rate (7.5% in Nigeria)
                - tin: Business Tax Identification Number
        """
        self.business_id = config.get("business_id")
        self.service_id = config.get("service_id")
        self.default_currency = config.get("default_currency", "NGN")
        self.default_tax_rate = config.get("tax_rate", 7.5)
        self.business_tin = config.get("tin")
        self.business_name = config.get("business_name")
        self.business_address = config.get("business_address", {})
        
    def transform_transaction_to_firs_invoice(
        self,
        transaction: POSTransaction,
        location: POSLocation,
        customer_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Square POS transaction to FIRS-compliant invoice format.
        
        Args:
            transaction: POS transaction object
            location: POS location information
            customer_info: Optional customer information
            
        Returns:
            Dict: FIRS-compliant invoice structure
        """
        try:
            # Generate IRN according to FIRS format
            invoice_number = self._generate_invoice_number(transaction)
            irn = generate_irn(invoice_number, self.service_id, transaction.timestamp)
            
            # Convert amounts to Naira if necessary
            converted_amounts = self._convert_currency_to_ngn(transaction)
            
            # Build FIRS invoice structure
            firs_invoice = {
                "business_id": self.business_id,
                "irn": irn,
                "issue_date": transaction.timestamp.strftime("%Y-%m-%d"),
                "issue_time": transaction.timestamp.strftime("%H:%M:%S"),
                "invoice_type_code": "380",  # Commercial Invoice
                "document_currency_code": self.default_currency,
                "accounting_supplier_party": self._build_supplier_party(location),
                "accounting_customer_party": self._build_customer_party(customer_info),
                "invoice_line": self._build_invoice_lines(transaction, converted_amounts),
                "tax_total": self._build_tax_totals(converted_amounts),
                "legal_monetary_total": self._build_monetary_totals(converted_amounts),
                "payment_means": self._build_payment_means(transaction),
                "note": f"Square POS Transaction ID: {transaction.transaction_id}",
                "metadata": {
                    "source": "square_pos",
                    "location_id": transaction.location_id,
                    "payment_method": transaction.payment_method,
                    "original_currency": transaction.currency,
                    "original_amount": transaction.amount,
                    "square_transaction_id": transaction.transaction_id
                }
            }
            
            # Add optional fields if available
            self._add_optional_fields(firs_invoice, transaction, customer_info)
            
            return firs_invoice
            
        except Exception as e:
            raise ValueError(f"Failed to transform Square transaction to FIRS invoice: {str(e)}")
    
    def _generate_invoice_number(self, transaction: POSTransaction) -> str:
        """Generate unique invoice number for FIRS."""
        # Use Square transaction ID or generate unique number
        base_number = transaction.metadata.get("receipt_number") or transaction.transaction_id
        
        # Clean and format for FIRS compliance
        invoice_number = f"SQ{base_number.replace('-', '')[:10]}"
        return invoice_number
    
    def _convert_currency_to_ngn(self, transaction: POSTransaction) -> Dict[str, Decimal]:
        """
        Convert transaction amounts to Nigerian Naira.
        
        For now, this assumes direct conversion. In production, you would
        use real-time exchange rates.
        """
        # For demo purposes, assuming 1 USD = 800 NGN (use real exchange rate API)
        if transaction.currency.upper() == "NGN":
            conversion_rate = Decimal("1.0")
        elif transaction.currency.upper() == "USD":
            conversion_rate = Decimal("800.0")  # Use real-time rate in production
        else:
            conversion_rate = Decimal("800.0")  # Default fallback
        
        # Convert amounts
        line_extension_amount = Decimal(str(transaction.amount)) * conversion_rate
        
        # Calculate tax (7.5% VAT in Nigeria)
        tax_rate = Decimal(str(self.default_tax_rate)) / Decimal("100")
        tax_amount = line_extension_amount * tax_rate
        
        # Round to 2 decimal places
        line_extension_amount = line_extension_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax_amount = tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        return {
            "line_extension_amount": line_extension_amount,
            "tax_exclusive_amount": line_extension_amount,
            "tax_amount": tax_amount,
            "tax_inclusive_amount": line_extension_amount + tax_amount,
            "payable_amount": line_extension_amount + tax_amount
        }
    
    def _build_supplier_party(self, location: POSLocation) -> Dict[str, Any]:
        """Build accounting supplier party information."""
        return {
            "party": {
                "party_name": [{"name": self.business_name or location.name}],
                "postal_address": {
                    "street_name": self.business_address.get("street_name", location.address.get("address_line_1", "") if location.address else ""),
                    "city_name": self.business_address.get("city_name", location.address.get("locality", "") if location.address else ""),
                    "postal_zone": self.business_address.get("postal_zone", location.address.get("postal_code", "") if location.address else ""),
                    "country_subentity": self.business_address.get("country_subentity", location.address.get("administrative_district_level_1", "") if location.address else ""),
                    "country": {
                        "identification_code": "NG"
                    },
                    "tin": self.business_tin
                }
            }
        }
    
    def _build_customer_party(self, customer_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build accounting customer party information."""
        if customer_info and customer_info.get("customer_id"):
            # Known customer
            return {
                "party": {
                    "party_name": [{"name": customer_info.get("name", "Square Customer")}],
                    "postal_address": {
                        "street_name": customer_info.get("address", {}).get("address_line_1", ""),
                        "city_name": customer_info.get("address", {}).get("locality", ""),
                        "postal_zone": customer_info.get("address", {}).get("postal_code", ""),
                        "country_subentity": customer_info.get("address", {}).get("administrative_district_level_1", ""),
                        "country": {
                            "identification_code": customer_info.get("address", {}).get("country", "NG")
                        },
                        "tin": customer_info.get("tin", "00000000-0001")  # Default for retail customers
                    }
                }
            }
        else:
            # Anonymous retail customer
            return {
                "party": {
                    "party_name": [{"name": "Retail Customer"}],
                    "postal_address": {
                        "street_name": "N/A",
                        "city_name": "N/A",
                        "postal_zone": "N/A",
                        "country_subentity": "N/A",
                        "country": {
                            "identification_code": "NG"
                        },
                        "tin": "00000000-0001"  # Standard TIN for retail customers
                    }
                }
            }
    
    def _build_invoice_lines(self, transaction: POSTransaction, amounts: Dict[str, Decimal]) -> List[Dict[str, Any]]:
        """Build invoice line items from transaction."""
        invoice_lines = []
        
        if transaction.items:
            # Process individual items
            for idx, item in enumerate(transaction.items, 1):
                line_amount = Decimal(str(item.get("total_price", 0)))
                if transaction.currency != self.default_currency:
                    # Convert to NGN (simplified - use real rates in production)
                    line_amount *= Decimal("800") if transaction.currency == "USD" else Decimal("1")
                
                invoice_lines.append({
                    "id": str(idx),
                    "invoiced_quantity": {
                        "quantity": str(item.get("quantity", 1)),
                        "unit_code": "PCE"  # Piece
                    },
                    "line_extension_amount": {
                        "amount": str(line_amount.quantize(Decimal("0.01"))),
                        "currency_id": self.default_currency
                    },
                    "item": {
                        "name": item.get("name", "Square Item"),
                        "sellers_item_identification": {
                            "id": item.get("catalog_object_id", f"SQ-ITEM-{idx}")
                        },
                        "classified_tax_category": {
                            "id": "S",  # Standard rate
                            "percent": str(self.default_tax_rate),
                            "tax_scheme": {
                                "id": "VAT"
                            }
                        }
                    },
                    "price": {
                        "price_amount": {
                            "amount": str(Decimal(str(item.get("unit_price", 0))).quantize(Decimal("0.01"))),
                            "currency_id": self.default_currency
                        }
                    }
                })
        else:
            # Single line item for the entire transaction
            invoice_lines.append({
                "id": "1",
                "invoiced_quantity": {
                    "quantity": "1",
                    "unit_code": "SRV"  # Service
                },
                "line_extension_amount": {
                    "amount": str(amounts["line_extension_amount"]),
                    "currency_id": self.default_currency
                },
                "item": {
                    "name": f"Square POS Transaction - {transaction.payment_method}",
                    "sellers_item_identification": {
                        "id": f"SQ-TXN-{transaction.transaction_id[:10]}"
                    },
                    "classified_tax_category": {
                        "id": "S",  # Standard rate
                        "percent": str(self.default_tax_rate),
                        "tax_scheme": {
                            "id": "VAT"
                        }
                    }
                },
                "price": {
                    "price_amount": {
                        "amount": str(amounts["line_extension_amount"]),
                        "currency_id": self.default_currency
                    }
                }
            })
        
        return invoice_lines
    
    def _build_tax_totals(self, amounts: Dict[str, Decimal]) -> List[Dict[str, Any]]:
        """Build tax total information."""
        return [{
            "tax_amount": {
                "amount": str(amounts["tax_amount"]),
                "currency_id": self.default_currency
            },
            "tax_subtotal": [{
                "taxable_amount": {
                    "amount": str(amounts["tax_exclusive_amount"]),
                    "currency_id": self.default_currency
                },
                "tax_amount": {
                    "amount": str(amounts["tax_amount"]),
                    "currency_id": self.default_currency
                },
                "tax_category": {
                    "id": "S",  # Standard rate
                    "percent": str(self.default_tax_rate),
                    "tax_scheme": {
                        "id": "VAT"
                    }
                }
            }]
        }]
    
    def _build_monetary_totals(self, amounts: Dict[str, Decimal]) -> Dict[str, Any]:
        """Build legal monetary total information."""
        return {
            "line_extension_amount": {
                "amount": str(amounts["line_extension_amount"]),
                "currency_id": self.default_currency
            },
            "tax_exclusive_amount": {
                "amount": str(amounts["tax_exclusive_amount"]),
                "currency_id": self.default_currency
            },
            "tax_inclusive_amount": {
                "amount": str(amounts["tax_inclusive_amount"]),
                "currency_id": self.default_currency
            },
            "payable_amount": {
                "amount": str(amounts["payable_amount"]),
                "currency_id": self.default_currency
            }
        }
    
    def _build_payment_means(self, transaction: POSTransaction) -> List[Dict[str, Any]]:
        """Build payment means information."""
        # Map Square payment methods to FIRS codes
        payment_method_mapping = {
            "CARD_VISA": {"code": 48, "name": "Bank card"},
            "CARD_MASTERCARD": {"code": 48, "name": "Bank card"},
            "CARD_AMEX": {"code": 48, "name": "Bank card"},
            "CARD_DISCOVER": {"code": 48, "name": "Bank card"},
            "CASH": {"code": 10, "name": "Cash"},
            "EXTERNAL": {"code": 97, "name": "Other"},
            "GIFT_CARD": {"code": 97, "name": "Other"}
        }
        
        payment_info = payment_method_mapping.get(
            transaction.payment_method,
            {"code": 97, "name": "Other"}
        )
        
        return [{
            "payment_means_code": payment_info["code"],
            "payment_due_date": transaction.timestamp.strftime("%Y-%m-%d")
        }]
    
    def _add_optional_fields(
        self,
        firs_invoice: Dict[str, Any],
        transaction: POSTransaction,
        customer_info: Optional[Dict[str, Any]]
    ) -> None:
        """Add optional fields to FIRS invoice if available."""
        # Add delivery date if available
        if transaction.timestamp:
            firs_invoice["actual_delivery_date"] = transaction.timestamp.strftime("%Y-%m-%d")
        
        # Add customer reference if available
        if customer_info and customer_info.get("reference_id"):
            firs_invoice["buyer_reference"] = customer_info["reference_id"]
        
        # Add order reference if available from metadata
        if transaction.metadata and transaction.metadata.get("order_id"):
            firs_invoice["order_reference"] = {
                "id": transaction.metadata["order_id"],
                "issue_date": transaction.timestamp.strftime("%Y-%m-%d")
            }
    
    def validate_firs_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate FIRS invoice structure and data.
        
        Args:
            invoice: FIRS invoice dictionary
            
        Returns:
            Dict containing validation results
        """
        validation_errors = []
        validation_warnings = []
        
        # Required field validation
        required_fields = [
            "business_id", "irn", "issue_date", "invoice_type_code",
            "document_currency_code", "accounting_supplier_party",
            "accounting_customer_party", "legal_monetary_total", "invoice_line"
        ]
        
        for field in required_fields:
            if field not in invoice:
                validation_errors.append(f"Required field '{field}' is missing")
        
        # IRN format validation
        if "irn" in invoice:
            irn = invoice["irn"]
            if not self._validate_irn_format(irn):
                validation_errors.append(f"IRN format is invalid: {irn}")
        
        # TIN validation
        supplier_tin = invoice.get("accounting_supplier_party", {}).get("party", {}).get("postal_address", {}).get("tin")
        if supplier_tin and not self._validate_tin_format(supplier_tin):
            validation_errors.append(f"Supplier TIN format is invalid: {supplier_tin}")
        
        # Monetary total validation
        if "legal_monetary_total" in invoice:
            monetary_errors = self._validate_monetary_totals(invoice["legal_monetary_total"])
            validation_errors.extend(monetary_errors)
        
        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": validation_warnings
        }
    
    def _validate_irn_format(self, irn: str) -> bool:
        """Validate IRN format: InvoiceNumber-ServiceID-YYYYMMDD"""
        try:
            parts = irn.split("-")
            if len(parts) != 3:
                return False
            
            invoice_number, service_id, date_part = parts
            
            # Validate date part
            datetime.strptime(date_part, "%Y%m%d")
            
            return True
        except (ValueError, IndexError):
            return False
    
    def _validate_tin_format(self, tin: str) -> bool:
        """Validate TIN format: 12345678-0001"""
        try:
            parts = tin.split("-")
            if len(parts) != 2:
                return False
            
            first_part, second_part = parts
            
            # First part should be 8 digits
            if len(first_part) != 8 or not first_part.isdigit():
                return False
            
            # Second part should be 4 digits
            if len(second_part) != 4 or not second_part.isdigit():
                return False
            
            return True
        except:
            return False
    
    def _validate_monetary_totals(self, monetary_total: Dict[str, Any]) -> List[str]:
        """Validate monetary total calculations."""
        errors = []
        
        try:
            line_extension = Decimal(monetary_total["line_extension_amount"]["amount"])
            tax_exclusive = Decimal(monetary_total["tax_exclusive_amount"]["amount"])
            tax_inclusive = Decimal(monetary_total["tax_inclusive_amount"]["amount"])
            payable = Decimal(monetary_total["payable_amount"]["amount"])
            
            # Validate relationships
            if tax_inclusive < tax_exclusive:
                errors.append("Tax inclusive amount must be >= tax exclusive amount")
            
            if payable != tax_inclusive:
                errors.append("Payable amount must equal tax inclusive amount")
            
            if line_extension != tax_exclusive:
                errors.append("Line extension amount must equal tax exclusive amount")
            
        except (KeyError, ValueError, TypeError) as e:
            errors.append(f"Invalid monetary total format: {str(e)}")
        
        return errors