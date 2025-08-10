"""
TaxPoynt Transaction Classification Engine
==========================================

Centralized AI-powered transaction classification system optimized for Nigerian business patterns.
Supports API-based classification with fallback to rule-based systems.

Key Features:
- Nigerian business pattern recognition
- OpenAI GPT-4o-mini integration
- Cost optimization and smart caching
- Privacy-first data handling
- FIRS compliance focus
"""

from .classification_models import (
    TransactionClassificationRequest,
    TransactionClassificationResult,
    UserContext,
    NigerianBusinessContext,
    ClassificationMetadata,
    ClassificationTier,
    PrivacyLevel
)

from .nigerian_classifier import (
    NigerianTransactionClassifier,
    ClassificationError,
    AuthenticationError,
    RateLimitError
)

from .cost_optimizer import (
    CostOptimizer,
    OptimizationStrategy,
    CostEstimate
)

from .privacy_protection import (
    APIPrivacyProtection,
    DataAnonymizer,
    PIIRedactor
)

from .cache_manager import (
    ClassificationCacheManager,
    CacheKey,
    CacheEntry
)

from .rule_fallback import (
    NigerianRuleFallback,
    BusinessIndicator,
    PatternMatcher
)

from .usage_tracker import (
    ClassificationUsageTracker,
    UsageMetrics,
    CostAnalytics
)

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"

__all__ = [
    # Core Models
    "TransactionClassificationRequest",
    "TransactionClassificationResult", 
    "UserContext",
    "NigerianBusinessContext",
    "ClassificationMetadata",
    "ClassificationTier",
    "PrivacyLevel",
    
    # Main Classifier
    "NigerianTransactionClassifier",
    "ClassificationError",
    "AuthenticationError", 
    "RateLimitError",
    
    # Cost Optimization
    "CostOptimizer",
    "OptimizationStrategy",
    "CostEstimate",
    
    # Privacy Protection
    "APIPrivacyProtection",
    "DataAnonymizer",
    "PIIRedactor",
    
    # Caching
    "ClassificationCacheManager",
    "CacheKey",
    "CacheEntry",
    
    # Rule-based Fallback
    "NigerianRuleFallback",
    "BusinessIndicator",
    "PatternMatcher",
    
    # Usage Tracking
    "ClassificationUsageTracker",
    "UsageMetrics",
    "CostAnalytics"
]