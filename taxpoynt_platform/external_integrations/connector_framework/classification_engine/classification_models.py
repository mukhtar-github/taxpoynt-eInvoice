"""
Classification Engine Data Models
=================================

Pydantic models for type-safe transaction classification with Nigerian business patterns.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from decimal import Decimal

class ClassificationTier(str, Enum):
    """Classification processing tier for cost optimization"""
    RULE_BASED = "rule_based"           # Free rule-based for obvious cases
    API_LITE = "api_lite"              # GPT-3.5-turbo for simple cases
    API_PREMIUM = "api_premium"        # GPT-4o-mini for complex cases
    API_ADVANCED = "api_advanced"      # GPT-4 for very complex cases

class PrivacyLevel(str, Enum):
    """Privacy protection level for data handling"""
    STANDARD = "standard"              # Anonymized API calls
    HIGH = "high"                      # Enhanced anonymization
    MAXIMUM = "maximum"                # Local processing only

class TaxCategory(str, Enum):
    """Nigerian tax categories for FIRS compliance"""
    STANDARD_RATE = "standard_rate"    # 7.5% VAT
    ZERO_RATE = "zero_rate"           # 0% VAT (essential goods)
    EXEMPT = "exempt"                  # VAT exempt
    UNKNOWN = "unknown"                # Requires manual review

class BusinessType(str, Enum):
    """Nigerian business type categories"""
    RETAIL = "retail"
    WHOLESALE = "wholesale"
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    HOSPITALITY = "hospitality"
    TECHNOLOGY = "technology"
    AGRICULTURE = "agriculture"
    CONSTRUCTION = "construction"
    TRANSPORT = "transport"
    FINANCIAL = "financial"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    GENERAL = "general"

class TransactionSource(str, Enum):
    """Source of the transaction data"""
    OPEN_BANKING = "open_banking"
    PAYMENT_PROCESSOR = "payment_processor"
    BANK_STATEMENT = "bank_statement"
    MANUAL_ENTRY = "manual_entry"
    ERP_SYSTEM = "erp_system"
    POS_SYSTEM = "pos_system"

class NigerianBusinessContext(BaseModel):
    """Nigerian business context for enhanced classification"""
    
    industry: BusinessType = BusinessType.GENERAL
    location: str = "Nigeria"
    state: Optional[str] = None
    business_size: str = "sme"  # sme, enterprise, large
    registration_type: Optional[str] = None  # limited, partnership, sole_proprietorship
    years_in_operation: Optional[int] = None
    primary_market: str = "domestic"  # domestic, export, mixed
    seasonal_patterns: List[str] = Field(default_factory=list)
    typical_transaction_ranges: Dict[str, Decimal] = Field(default_factory=dict)
    common_suppliers: List[str] = Field(default_factory=list)
    common_customers: List[str] = Field(default_factory=list)
    business_hours: Dict[str, str] = Field(default_factory=dict)
    weekend_operations: bool = False
    
    class Config:
        use_enum_values = True

class UserContext(BaseModel):
    """User context for personalized classification"""
    
    user_id: str
    organization_id: str
    business_name: Optional[str] = None
    business_context: NigerianBusinessContext = Field(default_factory=NigerianBusinessContext)
    previous_classifications: List[Dict[str, Any]] = Field(default_factory=list)
    correction_history: List[Dict[str, Any]] = Field(default_factory=list)
    learned_patterns: Dict[str, Any] = Field(default_factory=dict)
    accuracy_score: float = 0.0
    trust_level: float = 0.5  # 0.0 to 1.0
    subscription_tier: str = "starter"
    privacy_preferences: PrivacyLevel = PrivacyLevel.STANDARD
    
    @validator('trust_level')
    def validate_trust_level(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('trust_level must be between 0.0 and 1.0')
        return v
    
    @validator('accuracy_score')
    def validate_accuracy_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('accuracy_score must be between 0.0 and 1.0')
        return v

class TransactionClassificationRequest(BaseModel):
    """Request for transaction classification"""
    
    # Transaction details
    transaction_id: str
    amount: Decimal
    narration: str
    sender_name: Optional[str] = None
    sender_account: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_account: Optional[str] = None
    date: datetime
    time: Optional[str] = None
    bank: Optional[str] = None
    reference: Optional[str] = None
    transaction_type: str = "credit"  # credit, debit
    source: TransactionSource = TransactionSource.OPEN_BANKING
    
    # Context
    user_context: UserContext
    request_id: str = Field(default_factory=lambda: f"req_{int(datetime.now().timestamp())}")
    
    # Processing preferences
    classification_tier: Optional[ClassificationTier] = None
    privacy_level: Optional[PrivacyLevel] = None
    force_api_classification: bool = False
    include_reasoning: bool = True
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('amount must be positive')
        return v
    
    @validator('narration')
    def validate_narration(cls, v):
        if not v or not v.strip():
            raise ValueError('narration cannot be empty')
        return v.strip()
    
    class Config:
        use_enum_values = True

class ClassificationMetadata(BaseModel):
    """Metadata about the classification process"""
    
    classification_method: str  # api_gpt4o_mini, rule_based_fallback, etc.
    model_version: Optional[str] = None
    processing_time_ms: int = 0
    api_cost_estimate_ngn: Decimal = Decimal('0.0')
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cache_hit: bool = False
    fallback_used: bool = False
    privacy_level_applied: PrivacyLevel = PrivacyLevel.STANDARD
    
    # Nigerian-specific metadata
    nigerian_patterns_detected: List[str] = Field(default_factory=list)
    business_hours_factor: float = 0.0
    amount_category: str = "unknown"  # small, medium, large
    regional_indicators: List[str] = Field(default_factory=list)
    
    # Quality metrics
    confidence_calibration: float = 0.0
    pattern_match_strength: float = 0.0
    user_feedback_prediction: Optional[bool] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class TransactionClassificationResult(BaseModel):
    """Result of transaction classification"""
    
    # Classification decision
    is_business_income: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    
    # Nigerian compliance
    tax_category: TaxCategory = TaxCategory.UNKNOWN
    vat_applicable: bool = False
    vat_rate: Decimal = Decimal('0.075')  # 7.5% Nigerian VAT
    
    # Customer identification
    customer_name: Optional[str] = None
    customer_match_confidence: float = 0.0
    new_customer_suggested: bool = False
    
    # Invoice generation
    suggested_invoice_description: Optional[str] = None
    suggested_invoice_amount: Optional[Decimal] = None
    invoice_line_items: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Review flags
    requires_human_review: bool = False
    review_reasons: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    
    # Nigerian business insights
    nigerian_compliance_notes: List[str] = Field(default_factory=list)
    business_probability_factors: List[str] = Field(default_factory=list)
    seasonal_pattern_detected: Optional[str] = None
    similar_pattern_confidence: float = 0.0
    
    # Processing metadata
    metadata: ClassificationMetadata
    request_id: str
    
    # Quality assurance
    validation_passed: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('confidence must be between 0.0 and 1.0')
        return v
    
    @validator('customer_match_confidence')
    def validate_customer_match_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('customer_match_confidence must be between 0.0 and 1.0')
        return v
    
    @validator('similar_pattern_confidence')
    def validate_similar_pattern_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('similar_pattern_confidence must be between 0.0 and 1.0')
        return v
    
    class Config:
        use_enum_values = True

class BatchClassificationRequest(BaseModel):
    """Request for batch transaction classification"""
    
    transactions: List[TransactionClassificationRequest]
    user_context: UserContext
    batch_id: str = Field(default_factory=lambda: f"batch_{int(datetime.now().timestamp())}")
    
    # Batch processing options
    max_concurrent: int = 5
    stop_on_error: bool = False
    optimize_costs: bool = True
    
    # Progress tracking
    progress_callback_url: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('transactions')
    def validate_transactions(cls, v):
        if not v:
            raise ValueError('transactions list cannot be empty')
        if len(v) > 1000:
            raise ValueError('maximum 1000 transactions per batch')
        return v

class BatchClassificationResult(BaseModel):
    """Result of batch transaction classification"""
    
    batch_id: str
    total_transactions: int
    successful_classifications: int
    failed_classifications: int
    
    results: List[TransactionClassificationResult]
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Batch statistics
    total_processing_time_ms: int = 0
    average_processing_time_ms: float = 0.0
    total_api_cost_ngn: Decimal = Decimal('0.0')
    cache_hit_rate: float = 0.0
    
    # Quality metrics
    average_confidence: float = 0.0
    business_income_percentage: float = 0.0
    human_review_percentage: float = 0.0
    
    started_at: datetime
    completed_at: datetime = Field(default_factory=datetime.utcnow)

class ClassificationFeedback(BaseModel):
    """User feedback on classification results"""
    
    request_id: str
    user_id: str
    original_result: TransactionClassificationResult
    
    # User corrections
    corrected_is_business_income: Optional[bool] = None
    corrected_customer_name: Optional[str] = None
    corrected_tax_category: Optional[TaxCategory] = None
    corrected_description: Optional[str] = None
    
    # User assessment
    user_confidence_rating: float = Field(ge=1.0, le=5.0)  # 1-5 scale
    accuracy_rating: float = Field(ge=1.0, le=5.0)  # 1-5 scale
    usefulness_rating: float = Field(ge=1.0, le=5.0)  # 1-5 scale
    
    # Comments
    user_comments: Optional[str] = None
    improvement_suggestions: List[str] = Field(default_factory=list)
    
    # Learning signals
    pattern_confirmation: bool = False
    new_pattern_identified: bool = False
    pattern_description: Optional[str] = None
    
    feedback_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True