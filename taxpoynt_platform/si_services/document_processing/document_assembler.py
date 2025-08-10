"""
Document Assembler Service

Handles assembly of complex documents from multiple components.
Combines different document parts into cohesive invoice documents.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class DocumentAssembler:
    """Assemble complex documents from components"""
    
    def __init__(self):
        self.assembly_templates = {}
    
    async def assemble_invoice_document(
        self,
        header_data: Dict[str, Any],
        line_items: List[Dict[str, Any]],
        footer_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assemble complete invoice document from components
        
        Args:
            header_data: Invoice header information
            line_items: List of invoice line items
            footer_data: Optional footer information
            
        Returns:
            Assembled invoice document
        """
        assembled_document = {
            "document_type": "invoice",
            "assembled_at": datetime.now().isoformat(),
            "header": header_data,
            "line_items": line_items,
            "footer": footer_data or {},
            "total_lines": len(line_items),
            "assembly_status": "completed"
        }
        
        # Add calculated totals
        assembled_document["totals"] = await self._calculate_totals(line_items)
        
        return assembled_document
    
    async def _calculate_totals(self, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate document totals from line items"""
        subtotal = sum(item.get("amount", 0) for item in line_items)
        tax_amount = sum(item.get("tax_amount", 0) for item in line_items)
        
        return {
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": subtotal + tax_amount,
            "currency": line_items[0].get("currency", "NGN") if line_items else "NGN"
        }
    
    async def validate_document_structure(self, document: Dict[str, Any]) -> bool:
        """Validate assembled document structure"""
        required_sections = ["header", "line_items", "totals"]
        return all(section in document for section in required_sections)
    
    async def add_metadata(
        self, 
        document: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add metadata to assembled document"""
        document["metadata"] = {
            **metadata,
            "assembly_version": "1.0",
            "last_modified": datetime.now().isoformat()
        }
        return document