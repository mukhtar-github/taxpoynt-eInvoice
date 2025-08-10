"""
ISO 20022 Financial Message Validator
====================================
Comprehensive validator for ISO 20022 financial messaging standard with Nigerian banking integration.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import re

from .models import (
    ISO20022Message, PaymentMessage, CashManagementMessage,
    ValidationResult, MessageValidationError, NigerianBankingContext,
    ISO20022MessageType, PaymentInstructionStatus, NigerianBankCode
)


class ISO20022Validator:
    """
    ISO 20022 financial message validator.
    
    Features:
    - ISO 20022 schema validation
    - Business rule validation
    - Nigerian banking compliance (CBN/NIBSS)
    - SWIFT network compatibility
    - Cross-border payment validation
    - Currency and amount validation
    - BIC/IBAN validation
    - Nigerian account number validation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize ISO 20022 validator.
        
        Args:
            config: Validator configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Validation settings
        self.strict_mode = self.config.get('strict_mode', True)
        self.nigerian_compliance = self.config.get('nigerian_compliance', True)
        self.swift_validation = self.config.get('swift_validation', False)
        
        # Nigerian banking context
        self.nigerian_context = self.config.get('nigerian_context')
        if isinstance(self.nigerian_context, dict):
            self.nigerian_context = NigerianBankingContext(**self.nigerian_context)
        elif not self.nigerian_context:
            self.nigerian_context = NigerianBankingContext()
        
        # Supported message types
        self.supported_message_types = {
            ISO20022MessageType.PAIN_001,  # CustomerCreditTransferInitiation
            ISO20022MessageType.PAIN_002,  # CustomerPaymentStatusReport
            ISO20022MessageType.PACS_008,  # FIToFICustomerCreditTransfer
            ISO20022MessageType.CAMT_053,  # BankToCustomerStatement
            ISO20022MessageType.CAMT_054,  # BankToCustomerDebitCreditNotification
        }
        
        self.logger.info("ISO 20022 Validator initialized")
    
    def validate_message(self, message: ISO20022Message) -> ValidationResult:
        """
        Validate ISO 20022 message comprehensively.
        
        Args:
            message: ISO 20022 message to validate
            
        Returns:
            ValidationResult: Detailed validation results
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Validating ISO 20022 message: {message.message_type.value}")
            
            # Initialize validation result
            result = ValidationResult(
                valid=True,
                message_type=message.message_type,
                schema_valid=True,
                business_rules_valid=True,
                nigerian_compliance_valid=True
            )
            
            # 1. Message type validation
            self._validate_message_type(message, result)
            
            # 2. Schema validation
            self._validate_schema(message, result)
            
            # 3. Business rules validation
            self._validate_business_rules(message, result)
            
            # 4. Nigerian banking compliance
            if self.nigerian_compliance and message.nigerian_processing:
                self._validate_nigerian_compliance(message, result)
            
            # 5. SWIFT network validation
            if self.swift_validation:
                self._validate_swift_compliance(message, result)
            
            # 6. Cross-border payment validation
            self._validate_cross_border_requirements(message, result)
            
            # Record validation time
            result.validation_time_ms = (time.time() - start_time) * 1000
            
            self.logger.info(f"ISO 20022 validation completed: {result.valid}")
            return result
            
        except Exception as e:
            self.logger.error(f"ISO 20022 validation error: {str(e)}")
            return self._create_failed_validation(message.message_type, str(e))
    
    def validate_payment_message(self, payment_msg: PaymentMessage) -> ValidationResult:
        """
        Validate payment message (pain.001).
        
        Args:
            payment_msg: Payment message to validate
            
        Returns:
            ValidationResult: Payment-specific validation results
        """
        result = ValidationResult(
            valid=True,
            message_type=payment_msg.message_type,
            schema_valid=True,
            business_rules_valid=True
        )
        
        # Group header validation
        if not payment_msg.group_header:
            result.add_error("Payment message requires group header")
            return result
        
        # Payment instructions validation
        if not payment_msg.payment_instructions:
            result.add_error("Payment message requires at least one payment instruction")
            return result
        
        # Validate each payment instruction
        for i, instruction in enumerate(payment_msg.payment_instructions, 1):
            self._validate_payment_instruction(instruction, f"Instruction {i}", result)
        
        # Validate control sum
        if payment_msg.group_header.control_sum:
            calculated_sum = sum(
                instr.instructed_amount.amount for instr in payment_msg.payment_instructions
            )
            if abs(calculated_sum - payment_msg.group_header.control_sum) > Decimal('0.01'):
                result.add_error(f"Control sum mismatch: calculated {calculated_sum}, stated {payment_msg.group_header.control_sum}")
        
        # Nigerian specific validation
        if payment_msg.nigerian_context:
            self._validate_nigerian_payment_context(payment_msg, result)
        
        return result
    
    def validate_cash_management_message(self, cash_msg: CashManagementMessage) -> ValidationResult:
        """
        Validate cash management message (camt.053).
        
        Args:
            cash_msg: Cash management message to validate
            
        Returns:
            ValidationResult: Cash management validation results
        """
        result = ValidationResult(
            valid=True,
            message_type=cash_msg.message_type,
            schema_valid=True,
            business_rules_valid=True
        )
        
        # Statement validation
        if not cash_msg.statement_id:
            result.add_error("Statement ID is required")
        
        if not cash_msg.account:
            result.add_error("Account identification is required")
        
        # Balance validation
        if not cash_msg.opening_balance or not cash_msg.closing_balance:
            result.add_error("Opening and closing balances are required")
        
        # Date range validation
        if cash_msg.from_date > cash_msg.to_date:
            result.add_error("Statement from date cannot be after to date")
        
        # Currency consistency
        if (cash_msg.opening_balance.currency != cash_msg.closing_balance.currency):
            result.add_error("Opening and closing balance currencies must match")
        
        # Nigerian specific validation
        if cash_msg.nigerian_context:
            self._validate_nigerian_cash_management(cash_msg, result)
        
        return result
    
    def _validate_message_type(self, message: ISO20022Message, result: ValidationResult):
        """Validate message type support."""
        if message.message_type not in self.supported_message_types:
            result.add_warning(f"Message type {message.message_type.value} has limited validation support")
    
    def _validate_schema(self, message: ISO20022Message, result: ValidationResult):
        """Validate message schema compliance."""
        # Message ID validation
        if not message.message_id:
            result.add_error("Message ID is required")
            result.schema_valid = False
        elif len(message.message_id) > 35:
            result.add_error("Message ID exceeds maximum length of 35 characters")
            result.schema_valid = False
        
        # Message content validation
        if message.payment_message:
            payment_result = self.validate_payment_message(message.payment_message)
            if not payment_result.valid:
                result.errors.extend(payment_result.errors)
                result.warnings.extend(payment_result.warnings)
                result.schema_valid = False
        
        elif message.cash_mgmt_message:
            cash_result = self.validate_cash_management_message(message.cash_mgmt_message)
            if not cash_result.valid:
                result.errors.extend(cash_result.errors)
                result.warnings.extend(cash_result.warnings)
                result.schema_valid = False
        
        else:
            result.add_error("Message must contain either payment or cash management content")
            result.schema_valid = False
    
    def _validate_business_rules(self, message: ISO20022Message, result: ValidationResult):
        """Validate business rules compliance."""
        # Creation timestamp validation
        if message.creation_timestamp:
            # Message shouldn't be too old (more than 30 days)
            age_days = (datetime.now() - message.creation_timestamp).days
            if age_days > 30:
                result.add_warning(f"Message is {age_days} days old")
            
            # Message shouldn't be future-dated
            if message.creation_timestamp > datetime.now():
                result.add_error("Message creation timestamp cannot be in the future")
                result.business_rules_valid = False
        
        # Processing status validation
        valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        if message.processing_status not in valid_statuses:
            result.add_error(f"Invalid processing status: {message.processing_status}")
            result.business_rules_valid = False
    
    def _validate_nigerian_compliance(self, message: ISO20022Message, result: ValidationResult):
        """Validate Nigerian banking compliance requirements."""
        if not self.nigerian_context:
            result.add_warning("Nigerian banking context not configured")
            return
        
        # CBN compliance validation
        if self.nigerian_context.cbn_compliance:
            if message.cbn_reporting_required:
                result.add_info("CBN reporting requirements apply")
            
            # Transaction limits validation
            if message.payment_message:
                for instruction in message.payment_message.payment_instructions:
                    if instruction.instructed_amount.currency.value == "NGN":
                        amount = instruction.instructed_amount.amount
                        
                        # Example CBN limits (simplified)
                        if amount > Decimal('50000000'):  # NGN 50M
                            result.add_warning("Transaction exceeds typical CBN reporting threshold")
        
        # Nigerian account number validation
        if message.payment_message:
            for instruction in message.payment_message.payment_instructions:
                if instruction.debtor_account and instruction.debtor_account.nigerian_account_number:
                    if not self._validate_nigerian_account_number(instruction.debtor_account.nigerian_account_number):
                        result.add_error("Invalid Nigerian account number format")
                        result.nigerian_compliance_valid = False
                
                if instruction.creditor_account and instruction.creditor_account.nigerian_account_number:
                    if not self._validate_nigerian_account_number(instruction.creditor_account.nigerian_account_number):
                        result.add_error("Invalid Nigerian account number format")
                        result.nigerian_compliance_valid = False
        
        # Nigerian bank code validation
        self._validate_nigerian_bank_codes(message, result)
    
    def _validate_swift_compliance(self, message: ISO20022Message, result: ValidationResult):
        """Validate SWIFT network compliance."""
        if message.payment_message:
            for instruction in message.payment_message.payment_instructions:
                # BIC validation for international transfers
                if instruction.debtor_agent and instruction.debtor_agent.bic:
                    if not self._validate_bic(instruction.debtor_agent.bic):
                        result.add_error(f"Invalid debtor agent BIC: {instruction.debtor_agent.bic}")
                
                if instruction.creditor_agent and instruction.creditor_agent.bic:
                    if not self._validate_bic(instruction.creditor_agent.bic):
                        result.add_error(f"Invalid creditor agent BIC: {instruction.creditor_agent.bic}")
        
        # SWIFT message length limitations
        if len(message.message_id) > 16:  # SWIFT has stricter limits
            result.add_warning("Message ID may exceed SWIFT limitations")
    
    def _validate_cross_border_requirements(self, message: ISO20022Message, result: ValidationResult):
        """Validate cross-border payment requirements."""
        if message.payment_message:
            for instruction in message.payment_message.payment_instructions:
                # Check if this is a cross-border payment
                is_cross_border = self._is_cross_border_payment(instruction)
                
                if is_cross_border:
                    result.add_info("Cross-border payment detected")
                    
                    # Additional requirements for cross-border
                    if not instruction.remittance_info:
                        result.add_warning("Cross-border payments should include remittance information")
                    
                    # Currency validation
                    if instruction.instructed_amount.currency.value == "NGN":
                        if not instruction.creditor_agent or not instruction.creditor_agent.nigerian_bank_code:
                            result.add_warning("NGN payments typically require Nigerian creditor agent")
    
    def _validate_payment_instruction(self, instruction, instruction_name: str, result: ValidationResult):
        """Validate individual payment instruction."""
        # Required fields
        if not instruction.instruction_id:
            result.add_error(f"{instruction_name}: Instruction ID is required")
        
        if not instruction.end_to_end_id:
            result.add_error(f"{instruction_name}: End-to-end ID is required")
        
        if not instruction.instructed_amount:
            result.add_error(f"{instruction_name}: Instructed amount is required")
        
        # Amount validation
        if instruction.instructed_amount and instruction.instructed_amount.amount <= 0:
            result.add_error(f"{instruction_name}: Amount must be positive")
        
        # Party validation
        if not instruction.debtor and not instruction.creditor:
            result.add_error(f"{instruction_name}: Either debtor or creditor must be specified")
        
        # Account validation
        if instruction.debtor_account:
            self._validate_account(instruction.debtor_account, f"{instruction_name} debtor", result)
        
        if instruction.creditor_account:
            self._validate_account(instruction.creditor_account, f"{instruction_name} creditor", result)
        
        # Status validation
        if instruction.status:
            valid_statuses = [status.value for status in PaymentInstructionStatus]
            if instruction.status.value not in valid_statuses:
                result.add_error(f"{instruction_name}: Invalid payment status")
    
    def _validate_account(self, account, account_name: str, result: ValidationResult):
        """Validate account information."""
        if not account.account_number and not account.iban and not account.nigerian_account_number:
            result.add_error(f"{account_name}: Account number, IBAN, or Nigerian account number required")
        
        # IBAN validation
        if account.iban:
            if not self._validate_iban(account.iban):
                result.add_error(f"{account_name}: Invalid IBAN format")
        
        # Nigerian account number validation
        if account.nigerian_account_number:
            if not self._validate_nigerian_account_number(account.nigerian_account_number):
                result.add_error(f"{account_name}: Invalid Nigerian account number")
    
    def _validate_nigerian_payment_context(self, payment_msg: PaymentMessage, result: ValidationResult):
        """Validate Nigerian payment context."""
        if not payment_msg.cbn_compliance:
            result.add_warning("CBN compliance not enabled for Nigerian payment")
        
        # NIBSS integration requirements
        for instruction in payment_msg.payment_instructions:
            if instruction.nigerian_processing:
                if not instruction.cbn_reference:
                    result.add_info("CBN reference number recommended for Nigerian processing")
                
                # Naira transaction validation
                if instruction.instructed_amount.currency.value == "NGN":
                    # Working days validation
                    if self.nigerian_context.working_days_only:
                        if instruction.requested_execution_date:
                            weekday = instruction.requested_execution_date.weekday()
                            if weekday >= 5:  # Saturday = 5, Sunday = 6
                                result.add_warning("Requested execution date falls on weekend")
    
    def _validate_nigerian_cash_management(self, cash_msg: CashManagementMessage, result: ValidationResult):
        """Validate Nigerian cash management context."""
        # Nigerian bank validation
        if cash_msg.bank_agent:
            if cash_msg.bank_agent.nigerian_bank_code:
                if not self._is_valid_nigerian_bank_code(cash_msg.bank_agent.nigerian_bank_code):
                    result.add_error("Invalid Nigerian bank code")
        
        # Currency validation for Nigerian context
        if cash_msg.opening_balance.currency.value != "NGN":
            result.add_info("Non-Naira currency in Nigerian context")
    
    def _validate_nigerian_bank_codes(self, message: ISO20022Message, result: ValidationResult):
        """Validate Nigerian bank codes."""
        if message.payment_message:
            for instruction in message.payment_message.payment_instructions:
                # Debtor agent bank code
                if (instruction.debtor_agent and 
                    instruction.debtor_agent.nigerian_bank_code):
                    
                    if not self._is_valid_nigerian_bank_code(instruction.debtor_agent.nigerian_bank_code):
                        result.add_error("Invalid debtor agent Nigerian bank code")
                        result.nigerian_compliance_valid = False
                
                # Creditor agent bank code
                if (instruction.creditor_agent and 
                    instruction.creditor_agent.nigerian_bank_code):
                    
                    if not self._is_valid_nigerian_bank_code(instruction.creditor_agent.nigerian_bank_code):
                        result.add_error("Invalid creditor agent Nigerian bank code")
                        result.nigerian_compliance_valid = False
    
    def _validate_bic(self, bic: str) -> bool:
        """Validate BIC/SWIFT code format."""
        if not bic:
            return False
        
        # BIC format: AAAABBCCXXX or AAAABBCC
        # AAAA = Bank code, BB = Country code, CC = Location code, XXX = Branch code (optional)
        if len(bic) not in [8, 11]:
            return False
        
        # Bank code (4 letters)
        if not bic[:4].isalpha():
            return False
        
        # Country code (2 letters)
        if not bic[4:6].isalpha():
            return False
        
        # Location code (2 alphanumeric)
        if not bic[6:8].isalnum():
            return False
        
        # Branch code (3 alphanumeric, optional)
        if len(bic) == 11 and not bic[8:11].isalnum():
            return False
        
        return True
    
    def _validate_iban(self, iban: str) -> bool:
        """Validate IBAN format (basic validation)."""
        if not iban:
            return False
        
        # Remove spaces and convert to uppercase
        iban = iban.replace(' ', '').upper()
        
        # Length check (15-34 characters)
        if len(iban) < 15 or len(iban) > 34:
            return False
        
        # Format check (2 letters + 2 digits + alphanumeric)
        if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', iban):
            return False
        
        # TODO: Implement mod-97 checksum validation
        return True
    
    def _validate_nigerian_account_number(self, account_number: str) -> bool:
        """Validate Nigerian account number format."""
        if not account_number:
            return False
        
        # Nigerian account numbers are typically 10 digits
        if not re.match(r'^\d{10}$', account_number):
            return False
        
        return True
    
    def _is_valid_nigerian_bank_code(self, bank_code) -> bool:
        """Check if Nigerian bank code is valid."""
        if isinstance(bank_code, str):
            # Try to match against enum values
            try:
                NigerianBankCode(bank_code)
                return True
            except ValueError:
                return False
        elif isinstance(bank_code, NigerianBankCode):
            return True
        
        return False
    
    def _is_cross_border_payment(self, instruction) -> bool:
        """Determine if payment instruction is cross-border."""
        # Simplified logic - in practice would be more complex
        debtor_country = None
        creditor_country = None
        
        if instruction.debtor and instruction.debtor.country:
            debtor_country = instruction.debtor.country
        
        if instruction.creditor and instruction.creditor.country:
            creditor_country = instruction.creditor.country
        
        # If countries are different, it's cross-border
        if debtor_country and creditor_country:
            return debtor_country != creditor_country
        
        # If one party has a foreign BIC, likely cross-border
        if instruction.debtor_agent and instruction.debtor_agent.bic:
            if not instruction.debtor_agent.bic.startswith('NG'):  # Non-Nigerian BIC
                return True
        
        if instruction.creditor_agent and instruction.creditor_agent.bic:
            if not instruction.creditor_agent.bic.startswith('NG'):  # Non-Nigerian BIC
                return True
        
        return False
    
    def _create_failed_validation(self, message_type: ISO20022MessageType, error: str) -> ValidationResult:
        """Create failed validation result."""
        result = ValidationResult(
            valid=False,
            message_type=message_type,
            schema_valid=False,
            business_rules_valid=False,
            nigerian_compliance_valid=False
        )
        result.add_error(f"Validation failed: {error}")
        return result