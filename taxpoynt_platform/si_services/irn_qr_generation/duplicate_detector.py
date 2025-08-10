"""
Duplicate Detector

Prevents duplicate IRN generation and detects potential duplicates.
Maintains IRN registry and performs collision detection.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Set, Optional, List, Tuple
from dataclasses import dataclass
import threading


@dataclass
class IRNRecord:
    """IRN record for duplicate detection"""
    irn_value: str
    invoice_hash: str
    organization_id: str
    created_at: datetime
    invoice_data_summary: Dict[str, Any]


class DuplicateDetector:
    """Detect and prevent duplicate IRNs"""
    
    def __init__(self, max_cache_size: int = 100000):
        self.irn_registry: Dict[str, IRNRecord] = {}
        self.invoice_hash_registry: Dict[str, str] = {}  # hash -> irn_value
        self.lock = threading.Lock()
        self.max_cache_size = max_cache_size
    
    def check_duplicate_irn(self, irn_value: str) -> Optional[IRNRecord]:
        """
        Check if IRN already exists
        
        Args:
            irn_value: IRN to check
            
        Returns:
            Existing IRN record if duplicate found, None otherwise
        """
        with self.lock:
            return self.irn_registry.get(irn_value)
    
    def check_duplicate_invoice(self, invoice_data: Dict[str, Any]) -> Optional[str]:
        """
        Check if invoice data already has an IRN
        
        Args:
            invoice_data: Invoice data to check
            
        Returns:
            Existing IRN if duplicate invoice found, None otherwise
        """
        invoice_hash = self._generate_invoice_hash(invoice_data)
        
        with self.lock:
            return self.invoice_hash_registry.get(invoice_hash)
    
    def register_irn(
        self,
        irn_value: str,
        invoice_data: Dict[str, Any],
        organization_id: str
    ) -> bool:
        """
        Register new IRN in the system
        
        Args:
            irn_value: Generated IRN
            invoice_data: Invoice data
            organization_id: Organization identifier
            
        Returns:
            True if successfully registered, False if duplicate
        """
        with self.lock:
            # Check for IRN duplicate
            if irn_value in self.irn_registry:
                return False
            
            # Generate invoice hash
            invoice_hash = self._generate_invoice_hash(invoice_data)
            
            # Check for invoice duplicate
            if invoice_hash in self.invoice_hash_registry:
                return False
            
            # Create record
            irn_record = IRNRecord(
                irn_value=irn_value,
                invoice_hash=invoice_hash,
                organization_id=organization_id,
                created_at=datetime.now(),
                invoice_data_summary=self._create_invoice_summary(invoice_data)
            )
            
            # Register
            self.irn_registry[irn_value] = irn_record
            self.invoice_hash_registry[invoice_hash] = irn_value
            
            # Cleanup if cache is full
            self._cleanup_if_needed()
            
            return True
    
    def find_similar_invoices(
        self,
        invoice_data: Dict[str, Any],
        organization_id: str,
        similarity_threshold: float = 0.8
    ) -> List[Tuple[str, float, IRNRecord]]:
        """
        Find invoices with high similarity (potential duplicates)
        
        Args:
            invoice_data: Invoice data to compare
            organization_id: Organization identifier
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of (irn_value, similarity_score, irn_record) tuples
        """
        similar_invoices = []
        target_summary = self._create_invoice_summary(invoice_data)
        
        with self.lock:
            for irn_value, irn_record in self.irn_registry.items():
                # Only check within same organization
                if irn_record.organization_id != organization_id:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(
                    target_summary,
                    irn_record.invoice_data_summary
                )
                
                if similarity >= similarity_threshold:
                    similar_invoices.append((irn_value, similarity, irn_record))
        
        # Sort by similarity (highest first)
        similar_invoices.sort(key=lambda x: x[1], reverse=True)
        
        return similar_invoices
    
    def get_organization_irns(
        self,
        organization_id: str,
        days_back: Optional[int] = None
    ) -> List[IRNRecord]:
        """Get all IRNs for an organization"""
        cutoff_date = None
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.lock:
            org_irns = []
            for irn_record in self.irn_registry.values():
                if irn_record.organization_id == organization_id:
                    if cutoff_date is None or irn_record.created_at >= cutoff_date:
                        org_irns.append(irn_record)
            
            return org_irns
    
    def remove_irn(self, irn_value: str) -> bool:
        """Remove IRN from registry"""
        with self.lock:
            if irn_value not in self.irn_registry:
                return False
            
            irn_record = self.irn_registry[irn_value]
            
            # Remove from both registries
            del self.irn_registry[irn_value]
            if irn_record.invoice_hash in self.invoice_hash_registry:
                del self.invoice_hash_registry[irn_record.invoice_hash]
            
            return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get duplicate detection statistics"""
        with self.lock:
            return {
                "total_irns": len(self.irn_registry),
                "total_invoice_hashes": len(self.invoice_hash_registry),
                "cache_utilization": len(self.irn_registry) / self.max_cache_size * 100,
                "registry_size_mb": self._estimate_registry_size() / (1024 * 1024)
            }
    
    def _generate_invoice_hash(self, invoice_data: Dict[str, Any]) -> str:
        """Generate consistent hash for invoice data"""
        # Extract key fields that identify unique invoices
        key_fields = {
            'customer_id': str(invoice_data.get('customer_id', '')),
            'invoice_number': str(invoice_data.get('invoice_number', '')),
            'invoice_date': str(invoice_data.get('invoice_date', '')),
            'total_amount': str(invoice_data.get('total_amount', '')),
            'currency': str(invoice_data.get('currency', 'NGN'))
        }
        
        # Create deterministic string
        hash_string = json.dumps(key_fields, sort_keys=True)
        
        # Generate SHA256 hash
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def _create_invoice_summary(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create invoice summary for similarity comparison"""
        return {
            'customer_name': str(invoice_data.get('customer_name', '')).lower().strip(),
            'invoice_number': str(invoice_data.get('invoice_number', '')),
            'total_amount': float(invoice_data.get('total_amount', 0)),
            'currency': str(invoice_data.get('currency', 'NGN')),
            'item_count': len(invoice_data.get('line_items', [])),
            'date': str(invoice_data.get('invoice_date', ''))
        }
    
    def _calculate_similarity(self, summary1: Dict[str, Any], summary2: Dict[str, Any]) -> float:
        """Calculate similarity score between two invoice summaries"""
        similarity_score = 0.0
        total_weight = 0.0
        
        # Field weights for similarity calculation
        field_weights = {
            'customer_name': 0.3,
            'total_amount': 0.25,
            'invoice_number': 0.2,
            'currency': 0.1,
            'item_count': 0.1,
            'date': 0.05
        }
        
        for field, weight in field_weights.items():
            if field in summary1 and field in summary2:
                field_similarity = self._calculate_field_similarity(
                    summary1[field], summary2[field], field
                )
                similarity_score += field_similarity * weight
                total_weight += weight
        
        return similarity_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_field_similarity(self, value1: Any, value2: Any, field_type: str) -> float:
        """Calculate similarity for individual fields"""
        if value1 == value2:
            return 1.0
        
        if field_type == 'customer_name':
            # String similarity using simple character overlap
            str1, str2 = str(value1), str(value2)
            if not str1 or not str2:
                return 0.0
            
            # Simple Jaccard similarity for strings
            set1 = set(str1.lower().split())
            set2 = set(str2.lower().split())
            
            if not set1 and not set2:
                return 1.0
            
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            return intersection / union if union > 0 else 0.0
        
        elif field_type == 'total_amount':
            # Numeric similarity with tolerance
            try:
                num1, num2 = float(value1), float(value2)
                if num1 == 0 and num2 == 0:
                    return 1.0
                
                diff = abs(num1 - num2)
                avg = (num1 + num2) / 2
                
                return max(0, 1 - (diff / avg)) if avg > 0 else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        elif field_type == 'item_count':
            # Integer similarity
            try:
                int1, int2 = int(value1), int(value2)
                if int1 == int2:
                    return 1.0
                
                diff = abs(int1 - int2)
                max_val = max(int1, int2)
                
                return max(0, 1 - (diff / max_val)) if max_val > 0 else 1.0
            except (ValueError, TypeError):
                return 0.0
        
        return 0.0  # Default for other field types
    
    def _cleanup_if_needed(self):
        """Clean up old entries if cache is full"""
        if len(self.irn_registry) > self.max_cache_size:
            # Remove oldest 10% of entries
            entries_to_remove = int(self.max_cache_size * 0.1)
            
            # Sort by creation time
            sorted_entries = sorted(
                self.irn_registry.items(),
                key=lambda x: x[1].created_at
            )
            
            # Remove oldest entries
            for i in range(entries_to_remove):
                irn_value, irn_record = sorted_entries[i]
                del self.irn_registry[irn_value]
                if irn_record.invoice_hash in self.invoice_hash_registry:
                    del self.invoice_hash_registry[irn_record.invoice_hash]
    
    def _estimate_registry_size(self) -> int:
        """Estimate memory usage of registry"""
        # Rough estimation
        avg_irn_size = 50  # bytes
        avg_hash_size = 64  # bytes
        avg_summary_size = 200  # bytes
        
        total_size = len(self.irn_registry) * (avg_irn_size + avg_hash_size + avg_summary_size)
        return total_size