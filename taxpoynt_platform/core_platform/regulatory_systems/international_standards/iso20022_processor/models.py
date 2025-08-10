"""
ISO 20022 Data Models
=====================
Pydantic models for ISO 20022 financial messaging standard compliance and validation.
"""
from datetime import datetime, date, time
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import re


class MessageValidationError(Exception):
    """Raised when ISO 20022 message validation fails."""
    pass


class ISO20022MessageType(str, Enum):
    """ISO 20022 message types by business area."""
    # Payments (pacs)
    PACS_002 = "pacs.002"  # FIToFIPaymentStatusReport
    PACS_003 = "pacs.003"  # FIToFICustomerDirectDebit
    PACS_004 = "pacs.004"  # PaymentReturn
    PACS_007 = "pacs.007"  # FIToFIPaymentReversal
    PACS_008 = "pacs.008"  # FIToFICustomerCreditTransfer
    PACS_009 = "pacs.009"  # FinancialInstitutionCreditTransfer
    
    # Cash Management (camt)
    CAMT_052 = "camt.052"  # BankToCustomerAccountReport
    CAMT_053 = "camt.053"  # BankToCustomerStatement
    CAMT_054 = "camt.054"  # BankToCustomerDebitCreditNotification
    CAMT_056 = "camt.056"  # FIToFICancellationRequest
    
    # Payments Initiation (pain)
    PAIN_001 = "pain.001"  # CustomerCreditTransferInitiation
    PAIN_002 = "pain.002"  # CustomerPaymentStatusReport
    PAIN_007 = "pain.007"  # CustomerPaymentReversal
    PAIN_008 = "pain.008"  # CustomerDirectDebitInitiation
    
    # Trade Finance (tsmt)
    TSMT_018 = "tsmt.018"  # BankToCustomerTradeServiceStatus
    TSMT_019 = "tsmt.019"  # CustomerToCustomerTradeServiceStatus


class NigerianBankCode(str, Enum):
    """Nigerian bank codes for domestic processing."""
    ACCESS_BANK = "044"
    CITIBANK = "023"
    DIAMOND_BANK = "063"  # Now Access Bank
    ECOBANK = "050"
    FIDELITY_BANK = "070"
    FIRST_BANK = "011"
    FIRST_CITY_MONUMENT_BANK = "214"
    GUARANTY_TRUST_BANK = "058"
    HERITAGE_BANK = "030"
    KEYSTONE_BANK = "082"
    POLARIS_BANK = "076"  # Former Skye Bank
    PROVIDUS_BANK = "101"
    STANBIC_IBTC = "221"
    STANDARD_CHARTERED = "068"
    STERLING_BANK = "232"
    UNION_BANK = "032"
    UNITED_BANK_FOR_AFRICA = "033"
    UNITY_BANK = "215"
    WEMA_BANK = "035"
    ZENITH_BANK = "057"


class CurrencyCode(str, Enum):
    """ISO 4217 currency codes (common ones)."""
    NGN = "NGN"  # Nigerian Naira
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    JPY = "JPY"  # Japanese Yen
    CHF = "CHF"  # Swiss Franc
    CAD = "CAD"  # Canadian Dollar
    AUD = "AUD"  # Australian Dollar
    ZAR = "ZAR"  # South African Rand
    GHS = "GHS"  # Ghanaian Cedi
    KES = "KES"  # Kenyan Shilling


class PaymentInstructionStatus(str, Enum):
    """Payment instruction status codes."""
    ACCC = "ACCC"  # AcceptedSettlementCompleted
    ACCP = "ACCP"  # AcceptedCustomerProfile
    ACSC = "ACSC"  # AcceptedSettlementCompleted
    ACSP = "ACSP"  # AcceptedSettlementInProcess
    ACTC = "ACTC"  # AcceptedTechnicalValidation
    ACWC = "ACWC"  # AcceptedWithChange
    ACWP = "ACWP"  # AcceptedWithoutPosting
    RCVD = "RCVD"  # Received
    PDNG = "PDNG"  # Pending
    RJCT = "RJCT"  # Rejected
    CANC = "CANC"  # Cancelled


class PartyIdentification(BaseModel):
    """Party identification information."""
    name: str = Field(..., max_length=140, description="Party name")
    identification: Optional[str] = Field(None, description="Party identification")
    country: Optional[str] = Field(None, regex=r"^[A-Z]{2}$", description="ISO country code")
    
    # Address information
    address_line1: Optional[str] = Field(None, max_length=70, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=70, description="Address line 2")
    city: Optional[str] = Field(None, max_length=35, description="City")
    postal_code: Optional[str] = Field(None, max_length=16, description="Postal code")
    
    # Contact information
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if v and not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError("Invalid email format")
        return v


class FinancialInstitution(BaseModel):
    """Financial institution identification."""
    bic: Optional[str] = Field(None, regex=r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$", 
                              description="Bank Identifier Code (BIC/SWIFT)")
    name: Optional[str] = Field(None, max_length=140, description="Institution name")
    
    # Nigerian specific
    nigerian_bank_code: Optional[NigerianBankCode] = Field(None, description="CBN bank code")
    sort_code: Optional[str] = Field(None, regex=r"^\d{6}$", description="UK sort code format")
    
    # International
    clearing_system_id: Optional[str] = Field(None, description="Clearing system identification")
    member_id: Optional[str] = Field(None, description="Member identification")
    
    @validator('bic')
    def validate_bic(cls, v):
        """Validate BIC format."""
        if v:
            if len(v) not in [8, 11]:
                raise ValueError("BIC must be 8 or 11 characters")
            if not v[:4].isalpha() or not v[4:6].isalpha():
                raise ValueError("Invalid BIC format")
        return v


class AccountIdentification(BaseModel):
    """Account identification information."""
    iban: Optional[str] = Field(None, description="International Bank Account Number")
    account_number: Optional[str] = Field(None, description="Account number")
    account_name: Optional[str] = Field(None, max_length=70, description="Account name")
    
    # Nigerian specific
    nigerian_account_number: Optional[str] = Field(None, regex=r"^\d{10}$", 
                                                  description="10-digit Nigerian account number")
    
    @validator('iban')
    def validate_iban(cls, v):
        """Validate IBAN format (basic check)."""
        if v:
            # Remove spaces and convert to uppercase
            iban = v.replace(' ', '').upper()
            if len(iban) < 15 or len(iban) > 34:
                raise ValueError("IBAN length must be between 15 and 34 characters")
            if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', iban):
                raise ValueError("Invalid IBAN format")
        return v


class MonetaryAmount(BaseModel):
    """Monetary amount with currency."""
    amount: Decimal = Field(..., description="Amount value")
    currency: CurrencyCode = Field(..., description="ISO 4217 currency code")
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount precision."""
        if v < 0:
            raise ValueError("Amount cannot be negative")
        
        # Check decimal places (max 5 for most currencies, 2 for major ones)
        decimal_places = abs(v.as_tuple().exponent)
        if decimal_places > 5:
            raise ValueError("Amount has too many decimal places")
        
        return v


class PaymentTypeInformation(BaseModel):
    """Payment type and categorization."""
    instruction_priority: Optional[str] = Field("NORM", description="Instruction priority")
    service_level: Optional[str] = Field(None, description="Service level")
    clearing_channel: Optional[str] = Field(None, description="Clearing channel")
    sequence_type: Optional[str] = Field(None, description="Sequence type for direct debits")
    
    # Nigerian specific
    nigerian_payment_type: Optional[str] = Field(None, description="Nigerian payment type")
    nibss_category: Optional[str] = Field(None, description="NIBSS category code")


class RemittanceInformation(BaseModel):
    """Remittance information for payment reference."""
    unstructured: List[str] = Field(default_factory=list, description="Unstructured remittance info")
    structured_reference: Optional[str] = Field(None, description="Structured reference")
    
    # Invoice reference
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    invoice_date: Optional[date] = Field(None, description="Invoice date")
    
    @validator('unstructured')
    def validate_unstructured(cls, v):
        """Validate unstructured remittance information."""
        if v:
            for line in v:
                if len(line) > 140:
                    raise ValueError("Unstructured remittance line too long (max 140 chars)")
        return v


class PaymentInstruction(BaseModel):
    """Individual payment instruction."""
    instruction_id: str = Field(..., max_length=35, description="Instruction identification")
    end_to_end_id: str = Field(..., max_length=35, description="End-to-end identification")
    
    # Amount and currency
    instructed_amount: MonetaryAmount = Field(..., description="Instructed amount")
    
    # Parties
    debtor: Optional[PartyIdentification] = Field(None, description="Debtor information")
    debtor_account: Optional[AccountIdentification] = Field(None, description="Debtor account")
    debtor_agent: Optional[FinancialInstitution] = Field(None, description="Debtor agent")
    
    creditor: Optional[PartyIdentification] = Field(None, description="Creditor information")
    creditor_account: Optional[AccountIdentification] = Field(None, description="Creditor account")
    creditor_agent: Optional[FinancialInstitution] = Field(None, description="Creditor agent")
    
    # Payment details
    payment_type_info: Optional[PaymentTypeInformation] = Field(None, description="Payment type")
    remittance_info: Optional[RemittanceInformation] = Field(None, description="Remittance information")
    
    # Status and processing
    status: Optional[PaymentInstructionStatus] = Field(None, description="Payment status")
    requested_execution_date: Optional[date] = Field(None, description="Requested execution date")
    
    # Nigerian specific
    nigerian_processing: bool = Field(False, description="Nigerian domestic processing")
    cbn_reference: Optional[str] = Field(None, description="CBN reference number")


class GroupHeader(BaseModel):
    """Group header information for message batch."""
    message_id: str = Field(..., max_length=35, description="Message identification")
    creation_date_time: datetime = Field(..., description="Creation date and time")
    number_of_transactions: int = Field(..., ge=1, description="Number of transactions")
    control_sum: Optional[Decimal] = Field(None, description="Control sum")
    
    # Initiating party
    initiating_party: PartyIdentification = Field(..., description="Initiating party")
    
    # Message priority and processing
    group_status: Optional[str] = Field(None, description="Group status")
    settlement_method: Optional[str] = Field("CLRG", description="Settlement method")
    
    @validator('control_sum')
    def validate_control_sum(cls, v, values):
        """Validate control sum matches transaction amounts."""
        # In practice, this would validate against actual transaction amounts
        if v is not None and v < 0:
            raise ValueError("Control sum cannot be negative")
        return v


class PaymentMessage(BaseModel):
    """ISO 20022 Payment Message (pain.001 - CustomerCreditTransferInitiation)."""
    # Message identification
    message_type: ISO20022MessageType = Field(..., description="ISO 20022 message type")
    message_version: str = Field("001.001.03", description="Message version")
    
    # Group header
    group_header: GroupHeader = Field(..., description="Group header")
    
    # Payment information
    payment_instructions: List[PaymentInstruction] = Field(..., description="Payment instructions")
    
    # Nigerian context
    nigerian_context: bool = Field(False, description="Nigerian banking context")
    cbn_compliance: bool = Field(False, description="CBN compliance required")
    
    # Validation metadata
    validation_timestamp: Optional[datetime] = Field(None, description="Validation timestamp")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    
    @validator('payment_instructions')
    def validate_payment_instructions(cls, v, values):
        """Validate payment instructions consistency."""
        if not v:
            raise ValueError("At least one payment instruction required")
        
        # Check count matches group header
        if 'group_header' in values:
            expected_count = values['group_header'].number_of_transactions
            if len(v) != expected_count:
                raise ValueError(f"Payment instruction count {len(v)} doesn't match group header {expected_count}")
        
        return v


class CashManagementMessage(BaseModel):
    """ISO 20022 Cash Management Message (camt.053 - BankToCustomerStatement)."""
    # Message identification
    message_type: ISO20022MessageType = Field(..., description="ISO 20022 message type")
    message_version: str = Field("001.002.00", description="Message version")
    
    # Group header
    group_header: GroupHeader = Field(..., description="Group header")
    
    # Statement information
    statement_id: str = Field(..., max_length=35, description="Statement identification")
    account: AccountIdentification = Field(..., description="Account identification")
    
    # Balance information
    opening_balance: MonetaryAmount = Field(..., description="Opening balance")
    closing_balance: MonetaryAmount = Field(..., description="Closing balance")
    
    # Statement period
    from_date: date = Field(..., description="Statement from date")
    to_date: date = Field(..., description="Statement to date")
    
    # Entries (transactions)
    entries: List[Dict[str, Any]] = Field(default_factory=list, description="Statement entries")
    
    # Nigerian context
    nigerian_context: bool = Field(False, description="Nigerian banking context")
    bank_agent: Optional[FinancialInstitution] = Field(None, description="Reporting bank")
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        """Validate statement date range."""
        if 'from_date' in values and v < values['from_date']:
            raise ValueError("To date cannot be before from date")
        return v


class ISO20022Message(BaseModel):
    """Generic ISO 20022 message container."""
    # Message envelope
    message_type: ISO20022MessageType = Field(..., description="Message type")
    message_id: str = Field(..., max_length=35, description="Message identifier")
    creation_timestamp: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    # Message content (polymorphic)
    payment_message: Optional[PaymentMessage] = Field(None, description="Payment message content")
    cash_mgmt_message: Optional[CashManagementMessage] = Field(None, description="Cash management message")
    
    # Processing metadata
    processing_status: str = Field("pending", description="Processing status")
    validation_results: Dict[str, Any] = Field(default_factory=dict, description="Validation results")
    
    # Nigerian banking context
    nigerian_processing: bool = Field(False, description="Nigerian domestic processing")
    cbn_reporting_required: bool = Field(False, description="CBN reporting required")
    
    @validator('message_id')
    def validate_message_id(cls, v):
        """Validate message ID format."""
        if not re.match(r'^[A-Za-z0-9\-_/]+$', v):
            raise ValueError("Message ID contains invalid characters")
        return v


class NigerianBankingContext(BaseModel):
    """Nigerian banking system context and requirements."""
    # CBN requirements
    cbn_compliance: bool = Field(True, description="CBN compliance required")
    nibss_integration: bool = Field(True, description="NIBSS integration required")
    
    # Processing preferences
    local_currency_preference: bool = Field(True, description="Prefer Naira for domestic")
    working_days_only: bool = Field(True, description="Process on working days only")
    
    # Regulatory settings
    kyc_required: bool = Field(True, description="KYC verification required")
    aml_screening: bool = Field(True, description="AML screening required")
    transaction_limits: Dict[str, Decimal] = Field(default_factory=dict, description="Transaction limits")
    
    # Reporting requirements
    cbn_daily_reporting: bool = Field(True, description="CBN daily reporting")
    ndic_reporting: bool = Field(True, description="NDIC reporting for deposits")
    
    # System integration
    swift_enabled: bool = Field(False, description="SWIFT network enabled")
    rtgs_access: bool = Field(False, description="RTGS access available")
    nip_integration: bool = Field(True, description="NIP (Nigerian Instant Payment) integration")
    
    def get_transaction_limit(self, transaction_type: str, currency: str = "NGN") -> Optional[Decimal]:
        """Get transaction limit for specific type and currency."""
        key = f"{transaction_type}_{currency}"
        return self.transaction_limits.get(key)
    
    def set_transaction_limit(self, transaction_type: str, currency: str, limit: Decimal):
        """Set transaction limit for specific type and currency."""
        key = f"{transaction_type}_{currency}"
        self.transaction_limits[key] = limit


class ValidationResult(BaseModel):
    """ISO 20022 message validation result."""
    valid: bool = Field(..., description="Overall validation result")
    message_type: ISO20022MessageType = Field(..., description="Validated message type")
    
    # Validation details
    schema_valid: bool = Field(..., description="Schema validation result")
    business_rules_valid: bool = Field(..., description="Business rules validation")
    nigerian_compliance_valid: bool = Field(True, description="Nigerian compliance validation")
    
    # Issues and warnings
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    info: List[str] = Field(default_factory=list, description="Validation information")
    
    # Processing metadata
    validation_timestamp: datetime = Field(default_factory=datetime.now, description="Validation timestamp")
    validator_version: str = Field("1.0.0", description="Validator version")
    
    # Performance metrics
    validation_time_ms: Optional[float] = Field(None, description="Validation time in milliseconds")
    
    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add validation info."""
        self.info.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'valid': self.valid,
            'message_type': self.message_type.value,
            'schema_valid': self.schema_valid,
            'business_rules_valid': self.business_rules_valid,
            'nigerian_compliance_valid': self.nigerian_compliance_valid,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'validation_time_ms': self.validation_time_ms,
            'validation_timestamp': self.validation_timestamp.isoformat()
        }