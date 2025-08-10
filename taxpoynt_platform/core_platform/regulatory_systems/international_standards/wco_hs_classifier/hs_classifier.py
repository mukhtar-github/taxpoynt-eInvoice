"""
WCO Harmonized System Classifier
================================
Core HS code classification engine for product categorization according to 
World Customs Organization standards with Nigerian FIRS compliance.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import re
from difflib import SequenceMatcher

from .models import (
    HSCode, ProductClassification, HSClassificationResult, 
    HSClassificationError, HSConfidenceLevel, HSChapterSection,
    HSSearchCriteria, HSValidationResult
)
from .hs_database import HSDatabase


class HSClassifier:
    """
    WCO Harmonized System product classifier.
    
    Features:
    - Keyword-based HS code classification
    - AI-enhanced product description analysis
    - Nigerian tariff schedule integration
    - Multi-method classification (exact, fuzzy, AI)
    - FIRS compliance validation
    - Confidence scoring and alternative suggestions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize HS classifier.
        
        Args:
            config: Classifier configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize HS database
        self.hs_db = HSDatabase()
        
        # Classification settings
        self.min_confidence_threshold = self.config.get('min_confidence', 0.7)
        self.enable_fuzzy_matching = self.config.get('fuzzy_matching', True)
        self.enable_ai_classification = self.config.get('ai_classification', True)
        self.nigerian_focus = self.config.get('nigerian_focus', True)
        
        # Keyword scoring weights
        self.keyword_weights = {
            'exact_match': 1.0,
            'partial_match': 0.7,
            'synonym_match': 0.6,
            'category_match': 0.5,
            'fuzzy_match': 0.4
        }
        
        self.logger.info("HS Classifier initialized")
    
    def classify_product(self, product: ProductClassification) -> HSClassificationResult:
        """
        Classify product and assign HS code.
        
        Args:
            product: Product classification request
            
        Returns:
            HSClassificationResult: Classification results with HS code
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Classifying product: {product.product_name}")
            
            # 1. Try exact keyword matching first
            exact_result = self._exact_keyword_classification(product)
            if exact_result and exact_result.confidence_score >= 0.9:
                exact_result.processing_time_ms = (time.time() - start_time) * 1000
                return exact_result
            
            # 2. Try fuzzy matching
            fuzzy_result = None
            if self.enable_fuzzy_matching:
                fuzzy_result = self._fuzzy_classification(product)
            
            # 3. Try AI-enhanced classification
            ai_result = None
            if self.enable_ai_classification:
                ai_result = self._ai_classification(product)
            
            # 4. Select best result
            best_result = self._select_best_classification(
                [exact_result, fuzzy_result, ai_result]
            )
            
            if not best_result:
                best_result = self._create_failed_result(
                    "No suitable HS code classification found",
                    product
                )
            
            # 5. Validate FIRS compliance
            if best_result.hs_code:
                best_result = self._validate_firs_compliance(best_result)
            
            best_result.processing_time_ms = (time.time() - start_time) * 1000
            return best_result
            
        except Exception as e:
            self.logger.error(f"HS classification error: {str(e)}")
            return self._create_failed_result(f"Classification error: {str(e)}", product)
    
    def validate_hs_code(self, hs_code: str) -> HSValidationResult:
        """
        Validate HS code format and existence.
        
        Args:
            hs_code: HS code to validate
            
        Returns:
            HSValidationResult: Validation results
        """
        result = HSValidationResult(hs_code=hs_code, is_valid=False, format_valid=False, 
                                   code_exists=False, nigeria_applicable=False)
        
        try:
            # 1. Format validation
            if self._validate_hs_format(hs_code):
                result.format_valid = True
            else:
                result.errors.append("Invalid HS code format. Expected: XXXX.XX")
                return result
            
            # 2. Database lookup
            hs_record = self.hs_db.get_hs_code(hs_code)
            if hs_record:
                result.code_exists = True
                result.nigeria_applicable = True  # All codes in our DB are Nigeria-applicable
                result.is_valid = True
            else:
                result.errors.append("HS code not found in database")
                # Suggest similar codes
                suggestions = self._suggest_similar_codes(hs_code)
                result.suggestions.extend(suggestions)
                
        except Exception as e:
            result.errors.append(f"Validation error: {str(e)}")
            
        return result
    
    def search_hs_codes(self, criteria: HSSearchCriteria) -> List[HSCode]:
        """
        Search HS codes by various criteria.
        
        Args:
            criteria: Search criteria
            
        Returns:
            List[HSCode]: Matching HS codes
        """
        return self.hs_db.search_codes(criteria)
    
    def get_hs_code(self, code: str) -> Optional[HSCode]:
        """
        Get HS code details by code.
        
        Args:
            code: HS code (XXXX.XX format)
            
        Returns:
            Optional[HSCode]: HS code details if found
        """
        return self.hs_db.get_hs_code(code)
    
    def _exact_keyword_classification(self, product: ProductClassification) -> Optional[HSClassificationResult]:
        """Classify using exact keyword matching."""
        # Prepare search keywords
        keywords = [product.product_name.lower()]
        if product.product_description:
            keywords.append(product.product_description.lower())
        keywords.extend([kw.lower() for kw in product.suggested_keywords])
        
        # Search for exact matches in HS database
        best_match = None
        best_score = 0.0
        alternatives = []
        
        for keyword in keywords:
            matches = self.hs_db.search_by_keyword(keyword)
            for match in matches:
                score = self._calculate_keyword_score(keyword, match)
                if score > best_score:
                    if best_match:
                        alternatives.append(best_match)
                    best_match = match
                    best_score = score
                elif score > 0.6:
                    alternatives.append(match)
        
        if best_match and best_score >= 0.7:
            return HSClassificationResult(
                success=True,
                hs_code=best_match,
                confidence_level=self._score_to_confidence_level(best_score),
                confidence_score=best_score,
                classification_method="exact_keyword",
                matched_keywords=[kw for kw in keywords if self._keyword_matches_hs(kw, best_match)],
                alternative_codes=alternatives[:3],
                firs_compliant=True,
                processing_time_ms=0  # Will be set by caller
            )
        
        return None
    
    def _fuzzy_classification(self, product: ProductClassification) -> Optional[HSClassificationResult]:
        """Classify using fuzzy string matching."""
        if not self.enable_fuzzy_matching:
            return None
            
        product_text = f"{product.product_name} {product.product_description or ''}".lower()
        
        best_match = None
        best_score = 0.0
        alternatives = []
        
        # Get all HS codes for fuzzy matching
        all_codes = self.hs_db.get_all_codes()
        
        for hs_code in all_codes:
            # Create searchable text from HS code
            hs_text = f"{hs_code.description} {hs_code.tariff or ''}".lower()
            
            # Calculate fuzzy similarity
            similarity = SequenceMatcher(None, product_text, hs_text).ratio()
            
            # Boost score for keyword matches
            for keyword in product.suggested_keywords:
                if keyword.lower() in hs_text:
                    similarity += 0.1
            
            if similarity > best_score:
                if best_match:
                    alternatives.append(best_match)
                best_match = hs_code
                best_score = similarity
            elif similarity > 0.5:
                alternatives.append(hs_code)
        
        if best_match and best_score >= 0.6:
            return HSClassificationResult(
                success=True,
                hs_code=best_match,
                confidence_level=self._score_to_confidence_level(best_score),
                confidence_score=best_score,
                classification_method="fuzzy_matching",
                matched_keywords=[],
                alternative_codes=alternatives[:3],
                firs_compliant=True,
                processing_time_ms=0
            )
        
        return None
    
    def _ai_classification(self, product: ProductClassification) -> Optional[HSClassificationResult]:
        """Classify using AI-enhanced analysis."""
        # Placeholder for AI classification
        # In production, this would use ML models trained on product-to-HS mappings
        
        # For now, implement rule-based intelligent classification
        return self._rule_based_intelligent_classification(product)
    
    def _rule_based_intelligent_classification(self, product: ProductClassification) -> Optional[HSClassificationResult]:
        """Rule-based intelligent classification with business logic."""
        product_name = product.product_name.lower()
        description = (product.product_description or "").lower()
        combined_text = f"{product_name} {description}"
        
        # Nigerian business-focused classification rules
        classification_rules = [
            # Technology products
            {
                'keywords': ['computer', 'laptop', 'smartphone', 'tablet', 'software'],
                'hs_codes': ['8471.30', '8517.12', '8543.70'],
                'confidence': 0.8
            },
            # Food and beverages
            {
                'keywords': ['rice', 'wheat', 'flour', 'milk', 'oil', 'sugar'],
                'hs_codes': ['1006.30', '1001.90', '1101.00', '0401.10', '1507.90', '1701.99'],
                'confidence': 0.85
            },
            # Textiles and clothing
            {
                'keywords': ['shirt', 'dress', 'fabric', 'cotton', 'clothing', 'garment'],
                'hs_codes': ['6109.10', '6204.20', '5208.30', '5201.00'],
                'confidence': 0.8
            },
            # Pharmaceuticals
            {
                'keywords': ['medicine', 'drug', 'pharmaceutical', 'tablet', 'capsule', 'vaccine'],
                'hs_codes': ['3004.90', '3003.90', '3002.20'],
                'confidence': 0.9
            },
            # Construction materials
            {
                'keywords': ['cement', 'steel', 'iron', 'aluminum', 'pipe', 'wire'],
                'hs_codes': ['2523.29', '7213.10', '7208.10', '7601.10', '7306.30', '7217.10'],
                'confidence': 0.75
            }
        ]
        
        best_match = None
        best_score = 0.0
        
        for rule in classification_rules:
            # Check if any keywords match
            matches = sum(1 for kw in rule['keywords'] if kw in combined_text)
            if matches > 0:
                match_ratio = matches / len(rule['keywords'])
                score = rule['confidence'] * match_ratio
                
                if score > best_score:
                    # Get the first (most common) HS code for this category
                    hs_code_str = rule['hs_codes'][0]
                    hs_code = self.hs_db.get_hs_code(hs_code_str)
                    if hs_code:
                        best_match = hs_code
                        best_score = score
        
        if best_match and best_score >= 0.6:
            return HSClassificationResult(
                success=True,
                hs_code=best_match,
                confidence_level=self._score_to_confidence_level(best_score),
                confidence_score=best_score,
                classification_method="ai_rule_based",
                reasoning=f"Matched business rules for product category",
                firs_compliant=True,
                processing_time_ms=0
            )
        
        return None
    
    def _select_best_classification(self, results: List[Optional[HSClassificationResult]]) -> Optional[HSClassificationResult]:
        """Select the best classification result from multiple methods."""
        valid_results = [r for r in results if r is not None]
        
        if not valid_results:
            return None
        
        # Sort by confidence score
        valid_results.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Return highest confidence result
        return valid_results[0]
    
    def _validate_firs_compliance(self, result: HSClassificationResult) -> HSClassificationResult:
        """Validate HS classification against FIRS requirements."""
        if not result.hs_code:
            return result
        
        # Check if HS code is in FIRS-approved format
        if not self._validate_hs_format(result.hs_code.code):
            result.firs_compliant = False
            result.compliance_notes.append("HS code format not FIRS-compliant")
        
        # Check for controlled substances
        if result.hs_code.controlled_substance:
            result.compliance_notes.append("Product may require special permits")
        
        # Check import restrictions
        if result.hs_code.requires_permit:
            result.compliance_notes.append("Product requires import permit")
        
        return result
    
    def _create_failed_result(self, error_message: str, product: ProductClassification) -> HSClassificationResult:
        """Create failed classification result."""
        return HSClassificationResult(
            success=False,
            hs_code=None,
            confidence_level=HSConfidenceLevel.MANUAL,
            confidence_score=0.0,
            classification_method="failed",
            errors=[error_message],
            firs_compliant=False,
            processing_time_ms=0
        )
    
    def _calculate_keyword_score(self, keyword: str, hs_code: HSCode) -> float:
        """Calculate relevance score for keyword match."""
        score = 0.0
        keyword = keyword.lower()
        
        # Check description
        if keyword in hs_code.description.lower():
            score += self.keyword_weights['exact_match']
        
        # Check tariff
        if hs_code.tariff and keyword in hs_code.tariff.lower():
            score += self.keyword_weights['partial_match']
        
        # Partial matches
        words = keyword.split()
        for word in words:
            if word in hs_code.description.lower():
                score += self.keyword_weights['partial_match'] / len(words)
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _keyword_matches_hs(self, keyword: str, hs_code: HSCode) -> bool:
        """Check if keyword matches HS code."""
        keyword = keyword.lower()
        text = f"{hs_code.description} {hs_code.tariff or ''}".lower()
        return keyword in text
    
    def _score_to_confidence_level(self, score: float) -> HSConfidenceLevel:
        """Convert numeric score to confidence level."""
        if score >= 0.9:
            return HSConfidenceLevel.HIGH
        elif score >= 0.7:
            return HSConfidenceLevel.MEDIUM
        elif score >= 0.5:
            return HSConfidenceLevel.LOW
        else:
            return HSConfidenceLevel.MANUAL
    
    def _validate_hs_format(self, hs_code: str) -> bool:
        """Validate HS code format (XXXX.XX)."""
        pattern = r'^\d{4}\.\d{2}$'
        return bool(re.match(pattern, hs_code))
    
    def _suggest_similar_codes(self, hs_code: str) -> List[str]:
        """Suggest similar HS codes for invalid code."""
        # Extract chapter and try to find similar codes
        if len(hs_code) >= 2:
            try:
                chapter = int(hs_code[:2])
                similar_codes = self.hs_db.get_codes_by_chapter(chapter)
                return [code.code for code in similar_codes[:5]]
            except ValueError:
                pass
        
        return []