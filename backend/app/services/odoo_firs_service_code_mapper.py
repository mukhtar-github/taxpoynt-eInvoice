"""
Odoo to FIRS Service Code Mapper

This module provides mapping functionality between Odoo product categories
and FIRS service codes, enhancing the ERP-first integration strategy.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio

from app.core.config import settings
from app.services.firs_service import firs_service
from app.utils.text_similarity import calculate_similarity

logger = logging.getLogger(__name__)


class OdooFIRSServiceCodeMapper:
    """
    Maps Odoo product categories and descriptions to the appropriate FIRS service codes.
    
    This class provides functionality to:
    1. Retrieve and cache FIRS service codes
    2. Map Odoo product categories to FIRS service codes
    3. Suggest appropriate service codes based on product description
    4. Maintain custom mappings for frequently used categories
    """
    
    def __init__(self):
        """Initialize the service code mapper."""
        self.service_codes = {}
        self.category_mappings = {}
        self.last_updated = None
        self.cache_file = os.path.join(
            settings.REFERENCE_DATA_DIR, 
            'mappings', 
            'odoo_firs_service_code_mappings.json'
        )
        
        # Load cache if available
        self._load_cache()
    
    async def _ensure_service_codes_loaded(self) -> bool:
        """
        Ensure service codes are loaded, fetching from FIRS API if needed.
        
        Returns:
            bool: True if service codes were loaded successfully
        """
        if self.service_codes:
            return True
        
        try:
            # Get service codes from FIRS service
            service_codes_data = await firs_service.get_service_codes()
            
            if not service_codes_data:
                logger.warning("No service codes returned from FIRS API")
                return False
            
            # Process and index service codes for efficient lookups
            self.service_codes = {}
            for code_data in service_codes_data:
                code = code_data.get("code")
                if not code:
                    continue
                    
                self.service_codes[code] = {
                    "name": code_data.get("name", ""),
                    "description": code_data.get("description", ""),
                    "search_terms": self._generate_search_terms(code_data)
                }
            
            self.last_updated = datetime.now()
            logger.info(f"Loaded {len(self.service_codes)} service codes from FIRS API")
            
            # Save to cache
            self._save_cache()
            return True
            
        except Exception as e:
            logger.error(f"Error loading service codes: {str(e)}")
            return False
    
    def _generate_search_terms(self, code_data: Dict[str, Any]) -> List[str]:
        """
        Generate search terms for service code matching from code data.
        
        Args:
            code_data: Service code data dictionary
            
        Returns:
            List[str]: List of search terms
        """
        search_terms = []
        
        # Add code
        code = code_data.get("code", "")
        if code:
            search_terms.append(code.lower())
        
        # Add name
        name = code_data.get("name", "")
        if name:
            search_terms.append(name.lower())
            # Add individual words from name
            for word in name.lower().split():
                if len(word) > 2 and word not in search_terms:
                    search_terms.append(word)
        
        # Add description
        description = code_data.get("description", "")
        if description:
            # Add key words from description
            for word in description.lower().split():
                if len(word) > 3 and word not in search_terms:
                    search_terms.append(word)
        
        return search_terms
    
    def _load_cache(self) -> bool:
        """
        Load mappings and service codes from cache file.
        
        Returns:
            bool: True if cache was loaded successfully
        """
        try:
            if not os.path.exists(self.cache_file):
                logger.info("Cache file does not exist, will create on first save")
                return False
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            self.service_codes = cache_data.get("service_codes", {})
            self.category_mappings = cache_data.get("category_mappings", {})
            
            timestamp = cache_data.get("last_updated")
            if timestamp:
                self.last_updated = datetime.fromisoformat(timestamp)
            
            logger.info(f"Loaded {len(self.service_codes)} service codes and "
                       f"{len(self.category_mappings)} category mappings from cache")
            return True
            
        except Exception as e:
            logger.error(f"Error loading cache: {str(e)}")
            return False
    
    def _save_cache(self) -> bool:
        """
        Save mappings and service codes to cache file.
        
        Returns:
            bool: True if cache was saved successfully
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            cache_data = {
                "service_codes": self.service_codes,
                "category_mappings": self.category_mappings,
                "last_updated": self.last_updated.isoformat() if self.last_updated else None
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Saved {len(self.service_codes)} service codes and "
                       f"{len(self.category_mappings)} category mappings to cache")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")
            return False
    
    async def refresh_service_codes(self) -> bool:
        """
        Force refresh of service codes from FIRS API.
        
        Returns:
            bool: True if service codes were refreshed successfully
        """
        # Clear current service codes to force reload
        self.service_codes = {}
        return await self._ensure_service_codes_loaded()
    
    async def map_category(self, category: str, service_code: str) -> bool:
        """
        Map an Odoo product category to a FIRS service code.
        
        Args:
            category: Odoo product category name
            service_code: FIRS service code
            
        Returns:
            bool: True if mapping was successful
        """
        # Ensure service codes are loaded
        if not self.service_codes:
            await self._ensure_service_codes_loaded()
        
        # Validate service code
        if service_code not in self.service_codes:
            logger.warning(f"Invalid service code: {service_code}")
            return False
        
        # Add or update mapping
        self.category_mappings[category.lower()] = service_code
        self._save_cache()
        
        logger.info(f"Mapped category '{category}' to service code '{service_code}' "
                   f"({self.service_codes[service_code]['name']})")
        return True
    
    def get_mapping(self, category: str) -> Optional[str]:
        """
        Get the mapped service code for a category.
        
        Args:
            category: Odoo product category name
            
        Returns:
            Optional[str]: Mapped service code or None if not found
        """
        return self.category_mappings.get(category.lower())
    
    async def suggest_service_code(
        self, 
        product_name: str, 
        category: str = "", 
        description: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest the best matching FIRS service code for an Odoo product.
        
        Args:
            product_name: Name of the product
            category: Category of the product (optional)
            description: Description of the product (optional)
            
        Returns:
            Optional[Dict[str, Any]]: Best matching service code with details or None
        """
        # Ensure service codes are loaded
        if not self.service_codes:
            success = await self._ensure_service_codes_loaded()
            if not success:
                logger.error("Failed to load service codes")
                return None
        
        # First check for exact category match
        if category:
            category_lower = category.lower()
            if category_lower in self.category_mappings:
                code = self.category_mappings[category_lower]
                if code in self.service_codes:
                    return {
                        "code": code,
                        "name": self.service_codes[code].get("name", ""),
                        "description": self.service_codes[code].get("description", ""),
                        "match_type": "category_mapping",
                        "confidence": 1.0
                    }
        
        # Prepare search text
        search_text = f"{product_name} {category} {description}".lower()
        
        # Find matches using text similarity
        matches = []
        for code, data in self.service_codes.items():
            name = data.get("name", "")
            search_terms = data.get("search_terms", [])
            
            # Calculate similarity scores
            name_score = calculate_similarity(search_text, name.lower()) if name else 0
            term_score = 0
            for term in search_terms:
                term_similarity = calculate_similarity(search_text, term)
                term_score = max(term_score, term_similarity)
            
            # Combined score (weighted more toward name match)
            score = (name_score * 0.7) + (term_score * 0.3)
            
            if score > 0.3:  # Only include reasonable matches
                matches.append({
                    "code": code,
                    "name": name,
                    "description": data.get("description", ""),
                    "score": score
                })
        
        # Return the best match
        if matches:
            matches.sort(key=lambda x: x["score"], reverse=True)
            best_match = matches[0]
            return {
                "code": best_match["code"],
                "name": best_match["name"],
                "description": best_match["description"],
                "match_type": "similarity",
                "confidence": best_match["score"]
            }
        
        # No good match found
        return None
    
    async def get_suggestions(
        self, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get service code suggestions based on a search query.
        
        Args:
            query: Search text
            limit: Maximum number of suggestions to return
            
        Returns:
            List[Dict[str, Any]]: List of suggested service codes with details
        """
        # Ensure service codes are loaded
        if not self.service_codes:
            success = await self._ensure_service_codes_loaded()
            if not success:
                logger.error("Failed to load service codes")
                return []
        
        query = query.lower()
        matches = []
        
        for code, data in self.service_codes.items():
            name = data.get("name", "").lower()
            search_terms = data.get("search_terms", [])
            
            # Calculate similarity
            similarity = calculate_similarity(query, name)
            
            # Check terms for better matches
            for term in search_terms:
                term_similarity = calculate_similarity(query, term)
                similarity = max(similarity, term_similarity)
            
            if similarity > 0.3:  # Only include reasonable matches
                matches.append({
                    "code": code,
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "confidence": similarity
                })
        
        # Sort by similarity and limit results
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:limit]
    
    def get_service_code_details(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific service code.
        
        Args:
            code: FIRS service code
            
        Returns:
            Optional[Dict[str, Any]]: Service code details or None if not found
        """
        if not self.service_codes or code not in self.service_codes:
            return None
            
        data = self.service_codes[code]
        return {
            "code": code,
            "name": data.get("name", ""),
            "description": data.get("description", "")
        }
    
    def get_category_mappings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all category to service code mappings with details.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of category mappings with service code details
        """
        result = {}
        
        for category, code in self.category_mappings.items():
            if code in self.service_codes:
                result[category] = {
                    "code": code,
                    "name": self.service_codes[code].get("name", ""),
                    "description": self.service_codes[code].get("description", "")
                }
        
        return result


# Create a singleton instance for easy importing
odoo_firs_service_code_mapper = OdooFIRSServiceCodeMapper()
