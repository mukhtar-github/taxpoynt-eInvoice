"""
Sequence Manager

Manages IRN sequence numbers and ensures sequential generation.
Handles sequence allocation, tracking, and persistence.
"""

import asyncio
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import threading


@dataclass
class SequenceInfo:
    """Sequence information structure"""
    sequence_id: str
    current_value: int
    max_value: int
    prefix: str
    date_created: date
    last_used: datetime


class SequenceManager:
    """Manage IRN sequence numbers"""
    
    def __init__(self):
        self.sequences: Dict[str, SequenceInfo] = {}
        self.lock = threading.Lock()
        self.default_max_value = 999999999  # 9 digits
    
    async def get_next_sequence(
        self,
        organization_id: str,
        sequence_type: str = "IRN",
        date_key: Optional[date] = None
    ) -> int:
        """
        Get next sequence number for organization
        
        Args:
            organization_id: Organization identifier
            sequence_type: Type of sequence (IRN, QR, etc.)
            date_key: Date for sequence (defaults to today)
            
        Returns:
            Next sequence number
        """
        if date_key is None:
            date_key = date.today()
        
        sequence_id = self._generate_sequence_id(organization_id, sequence_type, date_key)
        
        with self.lock:
            if sequence_id not in self.sequences:
                self.sequences[sequence_id] = SequenceInfo(
                    sequence_id=sequence_id,
                    current_value=0,
                    max_value=self.default_max_value,
                    prefix=f"{sequence_type}_{date_key.strftime('%Y%m%d')}",
                    date_created=date_key,
                    last_used=datetime.now()
                )
            
            sequence_info = self.sequences[sequence_id]
            
            # Check if sequence is exhausted
            if sequence_info.current_value >= sequence_info.max_value:
                raise ValueError(f"Sequence {sequence_id} exhausted")
            
            # Increment and return
            sequence_info.current_value += 1
            sequence_info.last_used = datetime.now()
            
            return sequence_info.current_value
    
    async def reserve_sequence_block(
        self,
        organization_id: str,
        block_size: int,
        sequence_type: str = "IRN"
    ) -> List[int]:
        """
        Reserve a block of sequence numbers for bulk operations
        
        Args:
            organization_id: Organization identifier
            block_size: Number of sequences to reserve
            sequence_type: Type of sequence
            
        Returns:
            List of reserved sequence numbers
        """
        sequence_id = self._generate_sequence_id(organization_id, sequence_type, date.today())
        
        with self.lock:
            if sequence_id not in self.sequences:
                await self.get_next_sequence(organization_id, sequence_type)
            
            sequence_info = self.sequences[sequence_id]
            
            # Check if enough sequences available
            available = sequence_info.max_value - sequence_info.current_value
            if available < block_size:
                raise ValueError(f"Not enough sequences available. Requested: {block_size}, Available: {available}")
            
            # Reserve block
            start_value = sequence_info.current_value + 1
            end_value = start_value + block_size - 1
            
            sequence_info.current_value = end_value
            sequence_info.last_used = datetime.now()
            
            return list(range(start_value, end_value + 1))
    
    def get_sequence_status(
        self,
        organization_id: str,
        sequence_type: str = "IRN",
        date_key: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """Get current sequence status"""
        if date_key is None:
            date_key = date.today()
        
        sequence_id = self._generate_sequence_id(organization_id, sequence_type, date_key)
        
        with self.lock:
            if sequence_id not in self.sequences:
                return None
            
            sequence_info = self.sequences[sequence_id]
            
            return {
                "sequence_id": sequence_info.sequence_id,
                "current_value": sequence_info.current_value,
                "max_value": sequence_info.max_value,
                "remaining": sequence_info.max_value - sequence_info.current_value,
                "prefix": sequence_info.prefix,
                "date_created": sequence_info.date_created.isoformat(),
                "last_used": sequence_info.last_used.isoformat(),
                "utilization_percentage": (sequence_info.current_value / sequence_info.max_value) * 100
            }
    
    def list_sequences(self, organization_id: str) -> List[Dict[str, Any]]:
        """List all sequences for an organization"""
        with self.lock:
            org_sequences = []
            for sequence_id, sequence_info in self.sequences.items():
                if organization_id in sequence_id:
                    org_sequences.append({
                        "sequence_id": sequence_info.sequence_id,
                        "current_value": sequence_info.current_value,
                        "max_value": sequence_info.max_value,
                        "prefix": sequence_info.prefix,
                        "date_created": sequence_info.date_created.isoformat(),
                        "last_used": sequence_info.last_used.isoformat()
                    })
            
            return org_sequences
    
    def reset_sequence(
        self,
        organization_id: str,
        sequence_type: str = "IRN",
        date_key: Optional[date] = None,
        new_max_value: Optional[int] = None
    ) -> bool:
        """Reset sequence to start value"""
        if date_key is None:
            date_key = date.today()
        
        sequence_id = self._generate_sequence_id(organization_id, sequence_type, date_key)
        
        with self.lock:
            if sequence_id in self.sequences:
                sequence_info = self.sequences[sequence_id]
                sequence_info.current_value = 0
                if new_max_value:
                    sequence_info.max_value = new_max_value
                sequence_info.last_used = datetime.now()
                return True
            
            return False
    
    def cleanup_old_sequences(self, days_old: int = 30) -> int:
        """Clean up sequences older than specified days"""
        cutoff_date = date.today().replace(day=date.today().day - days_old)
        cleaned_count = 0
        
        with self.lock:
            sequences_to_remove = []
            for sequence_id, sequence_info in self.sequences.items():
                if sequence_info.date_created < cutoff_date:
                    sequences_to_remove.append(sequence_id)
            
            for sequence_id in sequences_to_remove:
                del self.sequences[sequence_id]
                cleaned_count += 1
        
        return cleaned_count
    
    def _generate_sequence_id(self, organization_id: str, sequence_type: str, date_key: date) -> str:
        """Generate unique sequence identifier"""
        date_str = date_key.strftime("%Y%m%d")
        return f"{organization_id}_{sequence_type}_{date_str}"
    
    def export_sequence_state(self) -> Dict[str, Any]:
        """Export current sequence state for persistence"""
        with self.lock:
            export_data = {}
            for sequence_id, sequence_info in self.sequences.items():
                export_data[sequence_id] = {
                    "current_value": sequence_info.current_value,
                    "max_value": sequence_info.max_value,
                    "prefix": sequence_info.prefix,
                    "date_created": sequence_info.date_created.isoformat(),
                    "last_used": sequence_info.last_used.isoformat()
                }
            
            return {
                "sequences": export_data,
                "exported_at": datetime.now().isoformat()
            }
    
    def import_sequence_state(self, import_data: Dict[str, Any]) -> bool:
        """Import sequence state from persistence"""
        try:
            with self.lock:
                sequences_data = import_data.get("sequences", {})
                
                for sequence_id, data in sequences_data.items():
                    self.sequences[sequence_id] = SequenceInfo(
                        sequence_id=sequence_id,
                        current_value=data["current_value"],
                        max_value=data["max_value"],
                        prefix=data["prefix"],
                        date_created=datetime.fromisoformat(data["date_created"]).date(),
                        last_used=datetime.fromisoformat(data["last_used"])
                    )
                
                return True
        except (KeyError, ValueError) as e:
            return False