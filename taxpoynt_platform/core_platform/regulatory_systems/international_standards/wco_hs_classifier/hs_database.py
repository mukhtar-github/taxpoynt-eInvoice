"""
HS Code Database
===============
Database interface for WCO Harmonized System codes with Nigerian tariff schedule.
Provides lookup, search, and caching functionality for HS classification.
"""
import logging
from typing import Dict, Any, List, Optional, Set
from functools import lru_cache
import json
from pathlib import Path

from .models import HSCode, HSSearchCriteria, HSChapterSection


class HSDatabase:
    """
    HS Code database interface with Nigerian tariff schedule.
    
    Features:
    - Nigerian customs tariff schedule
    - Fast lookup and search operations
    - LRU caching for performance
    - Keyword indexing
    - Chapter and section organization
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize HS database.
        
        Args:
            db_path: Optional path to HS database file
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # In-memory storage (in production, this would be a proper database)
        self._hs_codes: Dict[str, HSCode] = {}
        self._keyword_index: Dict[str, Set[str]] = {}
        self._chapter_index: Dict[int, List[str]] = {}
        
        # Load initial data
        self._load_nigerian_hs_data()
        self._build_indexes()
        
        self.logger.info(f"HS Database initialized with {len(self._hs_codes)} codes")
    
    def get_hs_code(self, code: str) -> Optional[HSCode]:
        """
        Get HS code by code string.
        
        Args:
            code: HS code (XXXX.XX format)
            
        Returns:
            Optional[HSCode]: HS code if found
        """
        return self._hs_codes.get(code)
    
    @lru_cache(maxsize=1000)
    def search_by_keyword(self, keyword: str) -> List[HSCode]:
        """
        Search HS codes by keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List[HSCode]: Matching HS codes
        """
        keyword = keyword.lower().strip()
        matching_codes = set()
        
        # Direct keyword lookup
        if keyword in self._keyword_index:
            matching_codes.update(self._keyword_index[keyword])
        
        # Partial keyword matching
        for indexed_keyword, codes in self._keyword_index.items():
            if keyword in indexed_keyword or indexed_keyword in keyword:
                matching_codes.update(codes)
        
        # Convert codes to HSCode objects
        result = []
        for code in matching_codes:
            hs_code = self._hs_codes.get(code)
            if hs_code:
                result.append(hs_code)
        
        # Sort by relevance (exact matches first)
        result.sort(key=lambda x: self._calculate_relevance(keyword, x), reverse=True)
        
        return result[:50]  # Limit results
    
    def search_codes(self, criteria: HSSearchCriteria) -> List[HSCode]:
        """
        Search HS codes by multiple criteria.
        
        Args:
            criteria: Search criteria
            
        Returns:
            List[HSCode]: Matching HS codes
        """
        results = list(self._hs_codes.values())
        
        # Apply filters
        if criteria.keyword:
            keyword_results = self.search_by_keyword(criteria.keyword)
            keyword_codes = {hs.code for hs in keyword_results}
            results = [hs for hs in results if hs.code in keyword_codes]
        
        if criteria.description_contains:
            desc_filter = criteria.description_contains.lower()
            results = [hs for hs in results if desc_filter in hs.description.lower()]
        
        if criteria.chapter:
            results = [hs for hs in results if hs.chapter == criteria.chapter]
        
        if criteria.section:
            results = [hs for hs in results if hs.section == criteria.section]
        
        if criteria.tariff_category:
            category_filter = criteria.tariff_category.lower()
            results = [hs for hs in results 
                      if hs.tariff_category and category_filter in hs.tariff_category.lower()]
        
        if criteria.requires_permit is not None:
            results = [hs for hs in results if hs.requires_permit == criteria.requires_permit]
        
        if criteria.controlled_substance is not None:
            results = [hs for hs in results if hs.controlled_substance == criteria.controlled_substance]
        
        # Apply limit
        return results[:criteria.limit]
    
    def get_codes_by_chapter(self, chapter: int) -> List[HSCode]:
        """
        Get all HS codes for a specific chapter.
        
        Args:
            chapter: HS chapter number (1-99)
            
        Returns:
            List[HSCode]: HS codes in chapter
        """
        if chapter not in self._chapter_index:
            return []
        
        return [self._hs_codes[code] for code in self._chapter_index[chapter]]
    
    def get_all_codes(self) -> List[HSCode]:
        """Get all HS codes in database."""
        return list(self._hs_codes.values())
    
    def add_hs_code(self, hs_code: HSCode) -> bool:
        """
        Add HS code to database.
        
        Args:
            hs_code: HS code to add
            
        Returns:
            bool: True if added successfully
        """
        try:
            self._hs_codes[hs_code.code] = hs_code
            self._update_indexes(hs_code)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add HS code {hs_code.code}: {str(e)}")
            return False
    
    def _load_nigerian_hs_data(self):
        """Load Nigerian HS code data."""
        # This would load from a real database or file in production
        # For now, we'll include sample Nigerian HS codes based on FIRS documentation
        
        sample_codes = [
            # Pharmaceuticals
            {
                "code": "2915.31",
                "heading_no": "29.15",
                "description": "Ethyl acetate - Saturated acyclic monocarboxylic acids and their derivatives",
                "tariff": "Ethyl acetate",
                "tariff_category": "MEDICAL, VETERINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
                "section": HSChapterSection.SECTION_VI,
                "chapter": 29,
                "duty_rate": 5.0,
                "vat_applicable": True
            },
            {
                "code": "2916.39",
                "heading_no": "29.16", 
                "description": "Others - unsaturated Acyclic monocarboxylic acids",
                "tariff": "Others",
                "tariff_category": "MEDICAL, VETERINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
                "section": HSChapterSection.SECTION_VI,
                "chapter": 29,
                "duty_rate": 5.0,
                "vat_applicable": True
            },
            {
                "code": "3004.90",
                "heading_no": "30.04",
                "description": "Other medicaments - consisting of mixed or unmixed products for therapeutic or prophylactic uses",
                "tariff": "Other medicaments",
                "tariff_category": "MEDICAL, VETERINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
                "section": HSChapterSection.SECTION_VI,
                "chapter": 30,
                "duty_rate": 5.0,
                "vat_applicable": True
            },
            
            # Technology products
            {
                "code": "8471.30",
                "heading_no": "84.71",
                "description": "Portable automatic data processing machines, weighing not more than 10 kg",
                "tariff": "Laptop computers",
                "tariff_category": "INFORMATION AND COMMUNICATION TECHNOLOGY",
                "section": HSChapterSection.SECTION_XVI,
                "chapter": 84,
                "duty_rate": 10.0,
                "vat_applicable": True
            },
            {
                "code": "8517.12",
                "heading_no": "85.17",
                "description": "Telephones for cellular networks or for other wireless networks",
                "tariff": "Mobile phones",
                "tariff_category": "INFORMATION AND COMMUNICATION TECHNOLOGY",
                "section": HSChapterSection.SECTION_XVI,
                "chapter": 85,
                "duty_rate": 10.0,
                "vat_applicable": True
            },
            
            # Food products
            {
                "code": "1006.30",
                "heading_no": "10.06",
                "description": "Semi-milled or wholly milled rice, whether or not polished or glazed",
                "tariff": "Processed rice",
                "tariff_category": "AGRICULTURAL PRODUCTS AND FOOD",
                "section": HSChapterSection.SECTION_II,
                "chapter": 10,
                "duty_rate": 15.0,
                "vat_applicable": True
            },
            {
                "code": "1001.90",
                "heading_no": "10.01",
                "description": "Other wheat and meslin",
                "tariff": "Wheat",
                "tariff_category": "AGRICULTURAL PRODUCTS AND FOOD",
                "section": HSChapterSection.SECTION_II,
                "chapter": 10,
                "duty_rate": 15.0,
                "vat_applicable": True
            },
            
            # Textiles
            {
                "code": "6109.10",
                "heading_no": "61.09",
                "description": "T-shirts, singlets and other vests, knitted or crocheted, of cotton",
                "tariff": "Cotton t-shirts",
                "tariff_category": "TEXTILES AND CLOTHING",
                "section": HSChapterSection.SECTION_XI,
                "chapter": 61,
                "duty_rate": 20.0,
                "vat_applicable": True
            },
            {
                "code": "5208.30",
                "heading_no": "52.08",
                "description": "Woven fabrics of cotton, containing 85% or more by weight of cotton, weighing more than 200 g/m²",
                "tariff": "Cotton fabrics",
                "tariff_category": "TEXTILES AND CLOTHING", 
                "section": HSChapterSection.SECTION_XI,
                "chapter": 52,
                "duty_rate": 20.0,
                "vat_applicable": True
            },
            
            # Construction materials
            {
                "code": "2523.29",
                "heading_no": "25.23",
                "description": "Other portland cement",
                "tariff": "Portland cement",
                "tariff_category": "CONSTRUCTION MATERIALS",
                "section": HSChapterSection.SECTION_V,
                "chapter": 25,
                "duty_rate": 15.0,
                "vat_applicable": True
            },
            {
                "code": "7213.10",
                "heading_no": "72.13", 
                "description": "Concrete reinforcing bars and rods, containing indentations, ribs, grooves or other deformations",
                "tariff": "Steel reinforcement bars",
                "tariff_category": "CONSTRUCTION MATERIALS",
                "section": HSChapterSection.SECTION_XV,
                "chapter": 72,
                "duty_rate": 10.0,
                "vat_applicable": True
            }
        ]
        
        for code_data in sample_codes:
            try:
                hs_code = HSCode(**code_data)
                self._hs_codes[hs_code.code] = hs_code
            except Exception as e:
                self.logger.error(f"Failed to load HS code {code_data.get('code')}: {str(e)}")
    
    def _build_indexes(self):
        """Build search indexes for fast lookup."""
        self._keyword_index.clear()
        self._chapter_index.clear()
        
        for code, hs_code in self._hs_codes.items():
            # Build keyword index
            keywords = self._extract_keywords(hs_code)
            for keyword in keywords:
                if keyword not in self._keyword_index:
                    self._keyword_index[keyword] = set()
                self._keyword_index[keyword].add(code)
            
            # Build chapter index
            chapter = hs_code.chapter
            if chapter not in self._chapter_index:
                self._chapter_index[chapter] = []
            self._chapter_index[chapter].append(code)
    
    def _update_indexes(self, hs_code: HSCode):
        """Update indexes when adding new HS code."""
        # Update keyword index
        keywords = self._extract_keywords(hs_code)
        for keyword in keywords:
            if keyword not in self._keyword_index:
                self._keyword_index[keyword] = set()
            self._keyword_index[keyword].add(hs_code.code)
        
        # Update chapter index
        chapter = hs_code.chapter
        if chapter not in self._chapter_index:
            self._chapter_index[chapter] = []
        if hs_code.code not in self._chapter_index[chapter]:
            self._chapter_index[chapter].append(hs_code.code)
    
    def _extract_keywords(self, hs_code: HSCode) -> Set[str]:
        """Extract searchable keywords from HS code."""
        keywords = set()
        
        # Extract from description
        desc_words = hs_code.description.lower().split()
        keywords.update(word.strip('.,;:()[]{}') for word in desc_words if len(word) > 2)
        
        # Extract from tariff
        if hs_code.tariff:
            tariff_words = hs_code.tariff.lower().split()
            keywords.update(word.strip('.,;:()[]{}') for word in tariff_words if len(word) > 2)
        
        # Extract from category
        if hs_code.tariff_category:
            category_words = hs_code.tariff_category.lower().split()
            keywords.update(word.strip('.,;:()[]{}') for word in category_words if len(word) > 2)
        
        # Remove common stop words
        stop_words = {'and', 'or', 'the', 'of', 'for', 'with', 'by', 'in', 'on', 'at', 'to', 'from'}
        keywords = {kw for kw in keywords if kw not in stop_words and len(kw) > 2}
        
        return keywords
    
    def _calculate_relevance(self, search_term: str, hs_code: HSCode) -> float:
        """Calculate relevance score for search result."""
        search_term = search_term.lower()
        score = 0.0
        
        # Exact matches in description
        if search_term in hs_code.description.lower():
            score += 2.0
        
        # Exact matches in tariff
        if hs_code.tariff and search_term in hs_code.tariff.lower():
            score += 1.5
        
        # Word matches
        search_words = search_term.split()
        description_words = hs_code.description.lower().split()
        
        for search_word in search_words:
            for desc_word in description_words:
                if search_word == desc_word:
                    score += 1.0
                elif search_word in desc_word or desc_word in search_word:
                    score += 0.5
        
        return score