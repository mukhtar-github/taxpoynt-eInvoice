"""
Automated Invoice Generator
===========================

Core engine for automatically generating FIRS-compliant e-invoices from banking transactions.
Transforms Open Banking transaction data into structured invoice documents.

Features:
- Transaction-to-invoice mapping
- Customer identification and matching
- VAT calculation and compliance
- FIRS format generation
- Bulk processing capabilities
"""

from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import logging

from .....core.models.invoice import Invoice, InvoiceItem, CustomerInfo
from .....core.exceptions import InvoiceGenerationError, ValidationError
from .....core.utils.validation import validate_tin, validate_amount
from .customer_matcher import CustomerMatcher
from .vat_calculator import VATCalculator
from .firs_formatter import FIRSFormatter

# Import processed transaction model
from ..transaction_processing.processed_transaction import ProcessedTransaction

logger = logging.getLogger(__name__)


class InvoiceGenerationStrategy(Enum):
    """Invoice generation strategies."""
    SINGLE_TRANSACTION = "single_transaction"  # One invoice per transaction
    DAILY_BATCH = "daily_batch"               # Daily consolidated invoices
    WEEKLY_BATCH = "weekly_batch"             # Weekly consolidated invoices
    MONTHLY_BATCH = "monthly_batch"           # Monthly consolidated invoices
    THRESHOLD_BASED = "threshold_based"       # Generate when amount threshold reached


@dataclass
class GenerationRule:
    """Rules for automated invoice generation."""
    strategy: InvoiceGenerationStrategy
    minimum_amount: Optional[Decimal] = None
    exclude_categories: List[str] = None
    include_categories: List[str] = None
    customer_types: List[str] = None
    batch_threshold: Optional[Decimal] = None
    schedule_time: Optional[str] = None  # HH:MM format for scheduled generation


@dataclass
class InvoiceGenerationResult:
    """Result of invoice generation process."""
    success: bool
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    total_amount: Optional[Decimal] = None
    items_count: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None


class AutoInvoiceGenerator:
    """
    Automated invoice generator for Open Banking transactions.
    
    Processes banking transactions and generates FIRS-compliant invoices
    based on configurable rules and strategies.
    """
    
    def __init__(
        self,
        customer_matcher: CustomerMatcher,
        vat_calculator: VATCalculator,
        firs_formatter: FIRSFormatter,
        default_rules: Optional[List[GenerationRule]] = None
    ):
        self.customer_matcher = customer_matcher
        self.vat_calculator = vat_calculator
        self.firs_formatter = firs_formatter
        self.default_rules = default_rules or []
        
        # Configuration
        self.auto_generate = True
        self.validate_customers = True
        self.require_tin = True
        self.default_currency = "NGN"
        
        # Statistics
        self.stats = {
            'generated': 0,
            'failed': 0,
            'skipped': 0,
            'total_amount': Decimal('0')
        }
    
    async def generate_from_transaction(
        self,
        transaction: ProcessedTransaction,
        rules: Optional[List[GenerationRule]] = None
    ) -> InvoiceGenerationResult:
        """
        Generate invoice from a processed banking transaction.
        
        Args:
            transaction: Processed banking transaction data
            rules: Custom generation rules (optional)
            
        Returns:
            InvoiceGenerationResult with generation details
        """
        try:
            logger.info(f"Generating invoice for transaction: {transaction.id}")
            
            # Check if transaction is ready for invoice generation
            if not transaction.is_ready_for_invoice():
                return InvoiceGenerationResult(
                    success=False,
                    errors=["Transaction not ready for invoice generation"],
                    warnings=["Check validation and duplicate detection results"]
                )

            # Apply generation rules
            applicable_rules = rules or self.default_rules
            if not self._should_generate_invoice(transaction, applicable_rules):
                return InvoiceGenerationResult(
                    success=False,
                    errors=["Transaction does not meet generation criteria"]
                )
            
            # Use enriched customer information if available
            customer_info = self._extract_customer_info(transaction)
            if not customer_info and self.validate_customers:
                return InvoiceGenerationResult(
                    success=False,
                    errors=["Customer information not available"]
                )
            
            # Create invoice
            invoice = await self._create_invoice_from_transaction(
                transaction, 
                customer_info
            )
            
            # Validate invoice
            validation_result = await self._validate_invoice(invoice)
            if not validation_result.valid:
                return InvoiceGenerationResult(
                    success=False,
                    errors=validation_result.errors
                )
            
            # Format for FIRS
            firs_data = await self.firs_formatter.format_invoice(invoice)
            
            # Update statistics
            self.stats['generated'] += 1
            self.stats['total_amount'] += invoice.total_amount
            
            logger.info(f"Successfully generated invoice: {invoice.invoice_number}")
            
            return InvoiceGenerationResult(
                success=True,
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                total_amount=invoice.total_amount,
                items_count=len(invoice.items),
                metadata={
                    'transaction_id': transaction.id,
                    'processing_metadata': transaction.processing_metadata,
                    'enrichment_data': transaction.enrichment_data,
                    'firs_data': firs_data
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate invoice for transaction {transaction.id}: {e}")
            self.stats['failed'] += 1
            
            return InvoiceGenerationResult(
                success=False,
                errors=[str(e)]
            )
    
    async def generate_batch_invoices(
        self,
        transactions: List[ProcessedTransaction],
        strategy: InvoiceGenerationStrategy = InvoiceGenerationStrategy.DAILY_BATCH,
        rules: Optional[List[GenerationRule]] = None
    ) -> List[InvoiceGenerationResult]:
        """
        Generate invoices in batch mode.
        
        Args:
            transactions: List of banking transactions
            strategy: Batching strategy
            rules: Custom generation rules
            
        Returns:
            List of InvoiceGenerationResult objects
        """
        logger.info(f"Starting batch invoice generation for {len(transactions)} transactions")
        
        try:
            # Group transactions based on strategy
            grouped_transactions = self._group_transactions_by_strategy(
                transactions, strategy
            )
            
            results = []
            for group_key, group_transactions in grouped_transactions.items():
                logger.info(f"Processing group: {group_key} ({len(group_transactions)} transactions)")
                
                if strategy == InvoiceGenerationStrategy.SINGLE_TRANSACTION:
                    # Generate individual invoices
                    for transaction in group_transactions:
                        result = await self.generate_from_transaction(transaction, rules)
                        results.append(result)
                else:
                    # Generate consolidated invoice
                    result = await self._generate_consolidated_invoice(
                        group_transactions, group_key, rules
                    )
                    results.append(result)
            
            logger.info(f"Batch generation completed. Generated {len(results)} invoices")
            return results
            
        except Exception as e:
            logger.error(f"Batch invoice generation failed: {e}")
            raise InvoiceGenerationError(f"Batch generation failed: {e}")
    
    async def _create_invoice_from_transaction(
        self,
        transaction: ProcessedTransaction,
        customer_info: Optional[CustomerInfo]
    ) -> Invoice:
        """Create invoice object from transaction data."""
        
        # Generate invoice number
        invoice_number = self._generate_invoice_number(transaction.date)
        
        # Calculate VAT
        vat_result = await self.vat_calculator.calculate_vat(
            amount=transaction.amount,
            transaction_type=transaction.category,
            customer_type=customer_info.customer_type if customer_info else "individual"
        )
        
        # Create invoice items
        items = [
            InvoiceItem(
                id=str(uuid.uuid4()),
                description=transaction.description or f"Banking transaction - {transaction.category}",
                quantity=Decimal('1'),
                unit_price=transaction.amount,
                total_amount=transaction.amount,
                vat_rate=vat_result.vat_rate,
                vat_amount=vat_result.vat_amount,
                category=transaction.category,
                reference=transaction.reference
            )
        ]
        
        # Create invoice
        invoice = Invoice(
            id=str(uuid.uuid4()),
            invoice_number=invoice_number,
            date=transaction.date,
            due_date=transaction.date + timedelta(days=30),  # Default 30 days
            customer_info=customer_info,
            items=items,
            subtotal=transaction.amount,
            vat_amount=vat_result.vat_amount,
            total_amount=transaction.amount + vat_result.vat_amount,
            currency=transaction.currency or self.default_currency,
            status="draft",
            metadata={
                'source': 'open_banking',
                'provider': transaction.provider,
                'transaction_id': transaction.id,
                'auto_generated': True,
                'generation_timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return invoice
    
    async def _generate_consolidated_invoice(
        self,
        transactions: List[ProcessedTransaction],
        group_key: str,
        rules: Optional[List[GenerationRule]]
    ) -> InvoiceGenerationResult:
        """Generate a consolidated invoice from multiple transactions."""
        
        try:
            if not transactions:
                return InvoiceGenerationResult(
                    success=False,
                    errors=["No transactions provided for consolidation"]
                )
            
            # Use first transaction's customer info as primary
            primary_transaction = transactions[0]
            customer_info = self._extract_customer_info(primary_transaction)
            
            # Generate consolidated invoice number
            invoice_number = self._generate_consolidated_invoice_number(
                group_key, len(transactions)
            )
            
            # Create consolidated items
            items = []
            total_amount = Decimal('0')
            total_vat = Decimal('0')
            
            for transaction in transactions:
                vat_result = await self.vat_calculator.calculate_vat(
                    amount=transaction.amount,
                    transaction_type=transaction.category,
                    customer_type=customer_info.customer_type if customer_info else "individual"
                )
                
                item = InvoiceItem(
                    id=str(uuid.uuid4()),
                    description=f"{transaction.description or transaction.category} - {transaction.date.strftime('%Y-%m-%d')}",
                    quantity=Decimal('1'),
                    unit_price=transaction.amount,
                    total_amount=transaction.amount,
                    vat_rate=vat_result.vat_rate,
                    vat_amount=vat_result.vat_amount,
                    category=transaction.category,
                    reference=transaction.reference
                )
                
                items.append(item)
                total_amount += transaction.amount
                total_vat += vat_result.vat_amount
            
            # Create consolidated invoice
            invoice = Invoice(
                id=str(uuid.uuid4()),
                invoice_number=invoice_number,
                date=primary_transaction.date,
                due_date=primary_transaction.date + timedelta(days=30),
                customer_info=customer_info,
                items=items,
                subtotal=total_amount,
                vat_amount=total_vat,
                total_amount=total_amount + total_vat,
                currency=primary_transaction.currency or self.default_currency,
                status="draft",
                metadata={
                    'source': 'open_banking_consolidated',
                    'provider': primary_transaction.provider,
                    'transaction_count': len(transactions),
                    'transaction_ids': [t.id for t in transactions],
                    'consolidation_key': group_key,
                    'auto_generated': True,
                    'generation_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Validate consolidated invoice
            validation_result = await self._validate_invoice(invoice)
            if not validation_result.valid:
                return InvoiceGenerationResult(
                    success=False,
                    errors=validation_result.errors
                )
            
            # Format for FIRS
            firs_data = await self.firs_formatter.format_invoice(invoice)
            
            # Update statistics
            self.stats['generated'] += 1
            self.stats['total_amount'] += invoice.total_amount
            
            logger.info(f"Generated consolidated invoice: {invoice.invoice_number}")
            
            return InvoiceGenerationResult(
                success=True,
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                total_amount=invoice.total_amount,
                items_count=len(invoice.items),
                metadata={
                    'transaction_count': len(transactions),
                    'consolidation_key': group_key,
                    'customer_info': customer_info.__dict__ if customer_info else None,
                    'firs_data': firs_data
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate consolidated invoice for group {group_key}: {e}")
            return InvoiceGenerationResult(
                success=False,
                errors=[str(e)]
            )
    
    def _extract_customer_info(self, transaction: ProcessedTransaction) -> Optional[CustomerInfo]:
        """Extract customer information from processed transaction."""
        
        if not transaction.enrichment_data.customer_matched:
            return None
            
        return CustomerInfo(
            id=transaction.enrichment_data.customer_id,
            name=transaction.enrichment_data.customer_name,
            customer_type=transaction.enrichment_data.customer_type or "individual",
            # Additional fields would be populated from enrichment data
        )
    
    def _should_generate_invoice(
        self,
        transaction: ProcessedTransaction,
        rules: List[GenerationRule]
    ) -> bool:
        """Check if invoice should be generated based on rules."""
        
        if not rules:
            return True
        
        for rule in rules:
            # Check minimum amount
            if rule.minimum_amount and transaction.amount < rule.minimum_amount:
                continue
            
            # Check excluded categories
            if rule.exclude_categories and transaction.category in rule.exclude_categories:
                continue
            
            # Check included categories
            if rule.include_categories and transaction.category not in rule.include_categories:
                continue
            
            # If we reach here, rule matches
            return True
        
        return False
    
    def _group_transactions_by_strategy(
        self,
        transactions: List[ProcessedTransaction],
        strategy: InvoiceGenerationStrategy
    ) -> Dict[str, List[ProcessedTransaction]]:
        """Group transactions based on batching strategy."""
        
        groups = {}
        
        for transaction in transactions:
            if strategy == InvoiceGenerationStrategy.SINGLE_TRANSACTION:
                key = f"single_{transaction.id}"
            elif strategy == InvoiceGenerationStrategy.DAILY_BATCH:
                key = transaction.date.strftime("%Y-%m-%d")
            elif strategy == InvoiceGenerationStrategy.WEEKLY_BATCH:
                # Get week number
                week = transaction.date.isocalendar()[1]
                key = f"{transaction.date.year}-W{week:02d}"
            elif strategy == InvoiceGenerationStrategy.MONTHLY_BATCH:
                key = transaction.date.strftime("%Y-%m")
            else:
                key = "default"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(transaction)
        
        return groups
    
    def _generate_invoice_number(self, date: datetime) -> str:
        """Generate unique invoice number."""
        timestamp = date.strftime("%Y%m%d")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"INV-OB-{timestamp}-{random_suffix}"
    
    def _generate_consolidated_invoice_number(
        self,
        group_key: str,
        transaction_count: int
    ) -> str:
        """Generate invoice number for consolidated invoice."""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        group_suffix = group_key.replace("-", "").replace("_", "")[:8].upper()
        return f"INV-OB-CONS-{timestamp}-{group_suffix}-{transaction_count}"
    
    async def _validate_invoice(self, invoice: Invoice) -> Any:
        """Validate generated invoice."""
        # This should return a validation result object
        # Implementation depends on your validation framework
        class ValidationResult:
            def __init__(self, valid: bool, errors: List[str] = None):
                self.valid = valid
                self.errors = errors or []
        
        errors = []
        
        # Basic validation
        if not invoice.invoice_number:
            errors.append("Invoice number is required")
        
        if not invoice.items:
            errors.append("Invoice must have at least one item")
        
        if invoice.total_amount <= 0:
            errors.append("Invoice total must be positive")
        
        # Customer validation
        if self.validate_customers and invoice.customer_info:
            if self.require_tin and not invoice.customer_info.tin:
                errors.append("Customer TIN is required")
            elif invoice.customer_info.tin and not validate_tin(invoice.customer_info.tin):
                errors.append("Invalid customer TIN format")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get invoice generation statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset generation statistics."""
        self.stats = {
            'generated': 0,
            'failed': 0,
            'skipped': 0,
            'total_amount': Decimal('0')
        }