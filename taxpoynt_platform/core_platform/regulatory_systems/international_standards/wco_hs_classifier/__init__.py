"""
WCO Harmonized System (HS) Code Classifier
==========================================
Classifies products and services according to World Customs Organization (WCO) 
Harmonized System standards as required for Nigerian FIRS e-invoicing compliance.

Components:
- hs_classifier.py: Core HS code classification engine
- hs_database.py: HS code database and lookup system
- nigerian_hs_rules.py: Nigerian-specific HS code customizations
- ai_classifier.py: AI-powered product classification
- models.py: HS code data models and structures

Features:
- 6-digit HS code classification (international standard)
- Nigerian tariff schedule integration
- AI-powered product description analysis
- Multi-language product name support
- Validation against FIRS requirements
"""

from .hs_classifier import HSClassifier, HSClassificationResult
from .models import HSCode, ProductClassification, HSClassificationError

__all__ = [
    'HSClassifier',
    'HSClassificationResult', 
    'HSCode',
    'ProductClassification',
    'HSClassificationError'
]