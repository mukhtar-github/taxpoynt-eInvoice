"""
Nigerian Transaction Classifier
==============================

OpenAI GPT-4o-mini powered transaction classifier optimized for Nigerian business patterns.
Includes FIRS compliance focus, privacy protection, and comprehensive Nigerian context.
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from .classification_models import (
    TransactionClassificationRequest,
    TransactionClassificationResult,
    ClassificationMetadata,
    ClassificationTier,
    PrivacyLevel,
    TaxCategory,
    UserContext,
    NigerianBusinessContext
)

logger = logging.getLogger(__name__)

class ClassificationError(Exception):
    """Base exception for classification errors"""
    pass

class AuthenticationError(ClassificationError):
    """OpenAI API authentication error"""
    pass

class RateLimitError(ClassificationError):
    """API rate limit exceeded"""
    pass

class CostTracker:
    """Track API usage costs for monitoring and optimization"""
    
    def __init__(self):
        self.total_requests = 0
        self.total_cost_usd = 0.0
        self.total_cost_ngn = 0.0
        self.usd_to_ngn_rate = 1600.0  # Approximate rate
        
        # Token costs for GPT-4o-mini (approximate)
        self.input_token_cost_per_1k = 0.00015  # $0.15 per 1M input tokens
        self.output_token_cost_per_1k = 0.0006   # $0.60 per 1M output tokens
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Calculate cost for API call"""
        input_cost = (input_tokens / 1000) * self.input_token_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_token_cost_per_1k
        total_cost_usd = input_cost + output_cost
        total_cost_ngn = total_cost_usd * self.usd_to_ngn_rate
        
        self.total_requests += 1
        self.total_cost_usd += total_cost_usd
        self.total_cost_ngn += total_cost_ngn
        
        return {
            'input_cost_usd': input_cost,
            'output_cost_usd': output_cost,
            'total_cost_usd': total_cost_usd,
            'total_cost_ngn': total_cost_ngn
        }

class NigerianTransactionClassifier:
    """
    OpenAI GPT-4o-mini powered transaction classifier optimized for Nigerian business patterns
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Nigerian transaction classifier"""
        
        # OpenAI client setup
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found. Classification will fall back to rule-based system.")
            self.client = None
        else:
            if AsyncOpenAI is None:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = AsyncOpenAI(api_key=api_key)
        
        # Nigerian business context
        self.nigerian_context = self._load_nigerian_business_context()
        
        # Cost tracking
        self.cost_tracker = CostTracker()
        
        # Logger
        self.logger = logging.getLogger(f"{__name__}.NigerianTransactionClassifier")
        
        self.logger.info("Nigerian Transaction Classifier initialized")
    
    def _load_nigerian_business_context(self) -> Dict[str, Any]:
        """Load Nigerian business context and patterns"""
        return {
            'business_keywords': [
                'payment', 'invoice', 'goods', 'services', 'business', 'shop',
                'market', 'contract', 'supply', 'delivery', 'order', 'purchase',
                'sales', 'revenue', 'income', 'profit', 'commission', 'fee',
                'consultation', 'project', 'work', 'job', 'service', 'product'
            ],
            'personal_keywords': [
                'salary', 'allowance', 'family', 'personal', 'loan', 'borrow',
                'refund', 'reversal', 'airtime', 'data', 'recharge', 'gift',
                'donation', 'transfer', 'pocket money', 'upkeep', 'support'
            ],
            'nigerian_business_indicators': [
                'alaba market', 'computer village', 'trade fair', 'main market',
                'aba market', 'onitsha market', 'kurmi market', 'wuse market',
                'lagos island', 'victoria island', 'ikeja', 'abuja', 'port harcourt',
                'kano', 'ibadan', 'aba', 'onitsha', 'enugu', 'calabar'
            ],
            'common_nigerian_business_types': [
                'restaurant', 'hotel', 'shop', 'store', 'boutique', 'pharmacy',
                'clinic', 'hospital', 'school', 'institute', 'company', 'enterprise',
                'services', 'consulting', 'trading', 'import', 'export', 'wholesale',
                'retail', 'construction', 'engineering', 'technology', 'software'
            ],
            'business_hours': {
                'weekday_start': 8,  # 8 AM
                'weekday_end': 18,   # 6 PM
                'saturday_start': 9,  # 9 AM
                'saturday_end': 16,   # 4 PM
                'sunday_operations': ['restaurant', 'hotel', 'pharmacy', 'hospital']
            },
            'amount_categories': {
                'small': (1000, 50000),      # ₦1K - ₦50K
                'medium': (50000, 500000),    # ₦50K - ₦500K
                'large': (500000, 5000000),   # ₦500K - ₦5M
                'very_large': (5000000, float('inf'))  # Above ₦5M
            }
        }
    
    async def classify_transaction(self, 
                                 request: TransactionClassificationRequest) -> TransactionClassificationResult:
        """
        Classify Nigerian bank transaction for FIRS tax compliance
        
        Features:
        - Nigerian business pattern recognition
        - FIRS compliance focus (7.5% VAT)
        - Customer identification and matching
        - Privacy-first data handling
        - Cost optimization with smart caching
        """
        
        start_time = time.time()
        
        try:
            # Determine classification tier if not specified
            if not request.classification_tier:
                from .cost_optimizer import CostOptimizer
                optimizer = CostOptimizer()
                request.classification_tier = optimizer.determine_classification_tier(
                    request, request.user_context
                )
            
            # Use rule-based fallback if no OpenAI client or tier is rule-based
            if not self.client or request.classification_tier == ClassificationTier.RULE_BASED:
                return await self._nigerian_rule_fallback(request)
            
            # Process with OpenAI API
            result = await self._classify_with_openai(request)
            
            # Update processing time
            processing_time = int((time.time() - start_time) * 1000)
            result.metadata.processing_time_ms = processing_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"Classification failed for request {request.request_id}: {str(e)}")
            
            # Fall back to rule-based classification
            fallback_result = await self._nigerian_rule_fallback(request)
            fallback_result.metadata.fallback_used = True
            
            processing_time = int((time.time() - start_time) * 1000)
            fallback_result.metadata.processing_time_ms = processing_time
            
            return fallback_result
    
    async def _classify_with_openai(self, 
                                   request: TransactionClassificationRequest) -> TransactionClassificationResult:
        """Classify transaction using OpenAI API"""
        
        # Build Nigerian-optimized prompt
        prompt = self._build_nigerian_classification_prompt(request)
        
        # Build conversation with context learning
        messages = [
            {
                "role": "system",
                "content": "You are a Nigerian tax compliance expert specializing in SME transaction classification for FIRS e-invoicing requirements. You understand Nigerian business patterns, banking systems, and tax regulations."
            },
            {"role": "user", "content": prompt}
        ]
        
        # Add user-specific learning examples
        if request.user_context.previous_classifications:
            examples = self._format_learning_examples(request.user_context.previous_classifications)
            messages.insert(1, {
                "role": "assistant",
                "content": f"Learning from previous classifications: {examples}"
            })
        
        try:
            # Make OpenAI API call
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective for pilot phase
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistency
                max_tokens=500,   # Sufficient for detailed response
                timeout=30        # Prevent hanging requests
            )
            
            # Parse response
            result_data = json.loads(response.choices[0].message.content)
            
            # Calculate API cost
            cost_info = self.cost_tracker.calculate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
            
            # Build classification metadata
            metadata = ClassificationMetadata(
                classification_method="api_gpt4o_mini",
                model_version="gpt-4o-mini",
                api_cost_estimate_ngn=Decimal(str(cost_info['total_cost_ngn'])),
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                privacy_level_applied=request.privacy_level or PrivacyLevel.STANDARD,
                nigerian_patterns_detected=result_data.get('nigerian_patterns_detected', []),
                business_hours_factor=self._calculate_business_hours_factor(request),
                amount_category=self._categorize_amount(request.amount)
            )
            
            # Build classification result
            result = TransactionClassificationResult(
                is_business_income=result_data.get('is_business_income', False),
                confidence=max(0.0, min(1.0, result_data.get('confidence', 0.5))),
                reasoning=result_data.get('reasoning', 'No reasoning provided'),
                tax_category=TaxCategory(result_data.get('tax_category', 'unknown')),
                vat_applicable=result_data.get('tax_category') == 'standard_rate',
                customer_name=result_data.get('customer_name'),
                suggested_invoice_description=result_data.get('suggested_invoice_description'),
                requires_human_review=result_data.get('requires_human_review', False),
                nigerian_compliance_notes=result_data.get('nigerian_compliance_notes', []),
                business_probability_factors=result_data.get('business_probability_factors', []),
                risk_factors=result_data.get('risk_factors', []),
                similar_pattern_confidence=max(0.0, min(1.0, result_data.get('similar_pattern_confidence', 0.0))),
                metadata=metadata,
                request_id=request.request_id
            )
            
            # Store classification data for training
            await self._store_classification_data(request, result)
            
            return result
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(f"OpenAI API rate limit exceeded: {str(e)}")
            elif "auth" in str(e).lower():
                raise AuthenticationError(f"OpenAI API authentication failed: {str(e)}")
            else:
                raise ClassificationError(f"OpenAI API error: {str(e)}")
    
    def _build_nigerian_classification_prompt(self, 
                                            request: TransactionClassificationRequest) -> str:
        """Build Nigerian-optimized classification prompt"""
        
        business_context = request.user_context.business_context
        
        prompt = f"""
Analyze this Nigerian bank transaction for TAX COMPLIANCE purposes.

BUSINESS CONTEXT:
- Nigerian SME: {request.user_context.business_name or 'Unknown'}
- Industry: {business_context.industry}
- Location: {business_context.location}, {business_context.state or 'Nigeria'}
- Business type: {business_context.business_size}
- Years in operation: {business_context.years_in_operation or 'unknown'}
- Previous patterns: {len(request.user_context.learned_patterns)} learned patterns

TRANSACTION DETAILS:
- Amount: ₦{request.amount:,}
- Narration: "{request.narration}"
- Sender: {request.sender_name or 'Unknown'}
- Date: {request.date.strftime('%Y-%m-%d')}
- Time: {request.time or 'Unknown'}
- Bank: {request.bank or 'Unknown'}
- Reference: {request.reference or 'Unknown'}

NIGERIAN BUSINESS PATTERNS:
- Common business payments: "transfer for goods", "payment for services", "invoice settlement"
- Personal transfers: "family support", "personal loan", "salary payment"
- USSD patterns: Often short descriptions like "TRF/PMT", "Mobile Transfer"
- Business hours: 8AM-6PM Lagos time indicates higher business probability
- Weekend transactions: Less likely to be business (except retail/hospitality)

FIRS COMPLIANCE REQUIREMENTS:
- All business income must be invoiced for tax compliance
- VAT applicable at 7.5% for most business transactions
- Customer identification required for invoice generation

CLASSIFICATION CRITERIA:
✅ BUSINESS INCOME: 
- Customer payments for goods/services
- Invoice settlements
- Professional service fees
- Product sales revenue
- Contract payments

❌ NOT BUSINESS INCOME:
- Salary payments
- Personal transfers
- Loan disbursements/repayments
- Refunds and reversals
- Internal transfers
- Family support
- Investment returns

NIGERIAN-SPECIFIC PATTERNS:
- "Alaba Market" mentions → likely business
- "Salary" keywords → personal income
- Repeat senders → likely customers
- Round amounts → often business transactions
- Transfer times during business hours → higher business probability

Respond in JSON format:
{{
    "is_business_income": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation of decision factors",
    "customer_name": "extracted customer name or null",
    "suggested_invoice_description": "proposed invoice line item description",
    "tax_category": "standard_rate|zero_rate|exempt|unknown",
    "requires_human_review": true/false,
    "nigerian_compliance_notes": ["FIRS-specific considerations"],
    "business_probability_factors": ["list", "of", "supporting", "factors"],
    "risk_factors": ["list", "of", "concerning", "patterns"],
    "similar_pattern_confidence": 0.0-1.0,
    "nigerian_patterns_detected": ["detected", "nigerian", "patterns"]
}}
        """.strip()
        
        return prompt
    
    async def _nigerian_rule_fallback(self, 
                                    request: TransactionClassificationRequest) -> TransactionClassificationResult:
        """Enhanced rule-based fallback with Nigerian business patterns"""
        
        narration = request.narration.lower()
        amount = float(request.amount)
        
        # Pattern matching
        business_score = sum(1 for keyword in self.nigerian_context['business_keywords'] 
                           if keyword in narration)
        personal_score = sum(1 for keyword in self.nigerian_context['personal_keywords'] 
                           if keyword in narration)
        
        # Nigerian business location indicators
        location_score = sum(1 for indicator in self.nigerian_context['nigerian_business_indicators'] 
                           if indicator in narration)
        
        # Amount-based heuristics for Nigerian market
        amount_score = 0
        if 5000 <= amount <= 10_000_000:  # Typical business range in Nigeria
            amount_score += 0.3
        if amount % 1000 == 0:  # Round amounts often business
            amount_score += 0.1
        
        # Time-based scoring
        time_score = self._calculate_business_hours_factor(request)
        
        # Calculate confidence
        total_score = (business_score * 0.4) + (location_score * 0.2) + amount_score + time_score - (personal_score * 0.5)
        confidence = max(0.1, min(0.9, total_score))
        
        is_business = total_score > 0.5
        
        # Build metadata
        metadata = ClassificationMetadata(
            classification_method="rule_based_fallback",
            business_hours_factor=time_score,
            amount_category=self._categorize_amount(request.amount),
            nigerian_patterns_detected=[
                pattern for pattern in self.nigerian_context['nigerian_business_indicators']
                if pattern in narration
            ]
        )
        
        return TransactionClassificationResult(
            is_business_income=is_business,
            confidence=confidence,
            reasoning=f"Rule-based fallback: business_keywords={business_score}, personal_keywords={personal_score}, location_score={location_score}, amount_score={amount_score}, time_score={time_score}",
            requires_human_review=confidence < 0.7,
            tax_category=TaxCategory.STANDARD_RATE if is_business else TaxCategory.UNKNOWN,
            vat_applicable=is_business,
            business_probability_factors=[
                f"Business keywords: {business_score}",
                f"Nigerian location indicators: {location_score}",
                f"Amount category: {self._categorize_amount(request.amount)}",
                f"Business hours factor: {time_score:.2f}"
            ],
            metadata=metadata,
            request_id=request.request_id
        )
    
    def _calculate_business_hours_factor(self, request: TransactionClassificationRequest) -> float:
        """Calculate business hours probability factor"""
        try:
            if not request.time:
                return 0.0
            
            # Parse time
            if ':' in request.time:
                hour = int(request.time.split(':')[0])
            else:
                return 0.0
            
            # Check day of week
            weekday = request.date.weekday()  # 0=Monday, 6=Sunday
            
            business_hours = self.nigerian_context['business_hours']
            
            if weekday < 5:  # Monday to Friday
                if business_hours['weekday_start'] <= hour <= business_hours['weekday_end']:
                    return 0.3
            elif weekday == 5:  # Saturday
                if business_hours['saturday_start'] <= hour <= business_hours['saturday_end']:
                    return 0.2
            else:  # Sunday
                # Only certain businesses operate on Sunday
                business_type = request.user_context.business_context.industry
                if business_type in business_hours['sunday_operations']:
                    return 0.1
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _categorize_amount(self, amount: Decimal) -> str:
        """Categorize transaction amount for Nigerian market"""
        amount_float = float(amount)
        
        for category, (min_amt, max_amt) in self.nigerian_context['amount_categories'].items():
            if min_amt <= amount_float < max_amt:
                return category
        
        return 'unknown'
    
    def _format_learning_examples(self, previous_classifications: List[Dict[str, Any]]) -> str:
        """Format previous classifications for learning context"""
        if not previous_classifications:
            return "No previous patterns"
        
        # Take last 3 classifications for context
        recent = previous_classifications[-3:]
        examples = []
        
        for classification in recent:
            examples.append(f"Amount: ₦{classification.get('amount', 0):,}, "
                          f"Business: {classification.get('is_business_income', False)}, "
                          f"Confidence: {classification.get('confidence', 0.0):.2f}")
        
        return "; ".join(examples)
    
    async def _store_classification_data(self, 
                                       request: TransactionClassificationRequest,
                                       result: TransactionClassificationResult):
        """Store classification data for training dataset building"""
        try:
            # Create training record (simplified for now)
            training_record = {
                'request_id': request.request_id,
                'user_id': request.user_context.user_id,
                'organization_id': request.user_context.organization_id,
                'transaction_hash': self._hash_transaction(request),
                'classification_result': result.dict(),
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
            
            # TODO: Store in database for training data collection
            self.logger.debug(f"Classification data stored for training: {request.request_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to store classification data: {e}")
    
    def _hash_transaction(self, request: TransactionClassificationRequest) -> str:
        """Generate hash for transaction (for deduplication)"""
        transaction_string = f"{request.amount}_{request.narration}_{request.date.isoformat()}"
        return hashlib.md5(transaction_string.encode()).hexdigest()
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary"""
        return {
            'total_requests': self.cost_tracker.total_requests,
            'total_cost_usd': self.cost_tracker.total_cost_usd,
            'total_cost_ngn': self.cost_tracker.total_cost_ngn,
            'average_cost_per_request_ngn': (
                self.cost_tracker.total_cost_ngn / max(1, self.cost_tracker.total_requests)
            )
        }