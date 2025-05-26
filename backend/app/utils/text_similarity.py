"""
Text Similarity Utilities

This module provides functions for calculating text similarity scores,
which are used in various mapping and suggestion features.
"""

import re
from typing import List, Set, Dict, Any, Tuple
from difflib import SequenceMatcher


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings using a combination
    of methods for better accuracy.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize text
    text1 = _normalize_text(text1)
    text2 = _normalize_text(text2)
    
    # Handle exact match
    if text1 == text2:
        return 1.0
    
    # Calculate sequence matcher similarity (good for overall string similarity)
    sequence_similarity = SequenceMatcher(None, text1, text2).ratio()
    
    # Calculate word overlap similarity (good for partial matches)
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return sequence_similarity
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    jaccard_similarity = len(intersection) / len(union) if union else 0.0
    
    # Combine scores with higher weight on sequence similarity
    combined_score = (sequence_similarity * 0.7) + (jaccard_similarity * 0.3)
    
    return combined_score


def calculate_multi_similarity(text: str, candidates: List[str]) -> List[Tuple[str, float]]:
    """
    Calculate similarity between a text and multiple candidate texts.
    
    Args:
        text: Text to compare
        candidates: List of candidate texts to compare against
        
    Returns:
        List[Tuple[str, float]]: List of (candidate, score) pairs sorted by score
    """
    results = []
    
    for candidate in candidates:
        score = calculate_similarity(text, candidate)
        results.append((candidate, score))
    
    # Sort by score in descending order
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results


def find_best_match(text: str, candidates: List[str], threshold: float = 0.3) -> Tuple[str, float]:
    """
    Find the best matching text from a list of candidates.
    
    Args:
        text: Text to find match for
        candidates: List of candidate texts to match against
        threshold: Minimum similarity score to consider a match
        
    Returns:
        Tuple[str, float]: Best matching text and its similarity score,
                           or ("", 0.0) if no match above threshold
    """
    if not text or not candidates:
        return "", 0.0
    
    # Calculate similarities
    similarities = calculate_multi_similarity(text, candidates)
    
    # Return best match if above threshold
    if similarities and similarities[0][1] >= threshold:
        return similarities[0]
    
    return "", 0.0


def _normalize_text(text: str) -> str:
    """
    Normalize text by converting to lowercase, removing punctuation
    and extra whitespace.
    
    Args:
        text: Text to normalize
        
    Returns:
        str: Normalized text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation except hyphens and underscores
    text = re.sub(r'[^\w\s\-_]', '', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Trim leading/trailing whitespace
    text = text.strip()
    
    return text
