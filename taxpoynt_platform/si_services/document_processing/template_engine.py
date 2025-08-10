"""
Template Engine Service

Handles invoice template processing and customization.
Manages template rendering, customization, and dynamic content generation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class TemplateEngine:
    """Invoice template processing engine"""
    
    def __init__(self):
        self.template_cache = {}
        self.default_templates = {
            "standard": "standard_invoice_template",
            "minimal": "minimal_invoice_template", 
            "detailed": "detailed_invoice_template",
            "nigerian": "nigerian_localized_template"
        }
    
    async def render_template(
        self,
        template_name: str,
        invoice_data: Dict[str, Any],
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Render invoice template with data
        
        Args:
            template_name: Name of template to use
            invoice_data: Invoice data for rendering
            customizations: Optional template customizations
            
        Returns:
            Rendered template result
        """
        template = await self.load_template(template_name)
        
        # Apply customizations if provided
        if customizations:
            template = await self.apply_customizations(template, customizations)
        
        # Render template with data
        rendered_content = await self._render_content(template, invoice_data)
        
        return {
            "template_name": template_name,
            "rendered_content": rendered_content,
            "rendered_at": datetime.now().isoformat(),
            "data_hash": self._generate_data_hash(invoice_data),
            "customizations_applied": bool(customizations)
        }
    
    async def load_template(self, template_name: str) -> Dict[str, Any]:
        """Load template from storage or cache"""
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        # TODO: Load template from database or file system
        template = {
            "name": template_name,
            "structure": self.default_templates.get(template_name, "standard"),
            "fields": ["header", "line_items", "totals", "footer"],
            "formatting": {"currency": "NGN", "date_format": "%Y-%m-%d"},
            "loaded_at": datetime.now().isoformat()
        }
        
        self.template_cache[template_name] = template
        return template
    
    async def apply_customizations(
        self,
        template: Dict[str, Any],
        customizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply customizations to template"""
        customized_template = template.copy()
        
        # Apply field customizations
        if "fields" in customizations:
            customized_template["fields"] = customizations["fields"]
        
        # Apply formatting customizations
        if "formatting" in customizations:
            customized_template["formatting"].update(customizations["formatting"])
        
        # Apply styling customizations
        if "styling" in customizations:
            customized_template["styling"] = customizations["styling"]
        
        return customized_template
    
    async def _render_content(
        self,
        template: Dict[str, Any],
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Render template content with invoice data"""
        # TODO: Implement actual template rendering logic
        return {
            "html_content": f"<html>Rendered invoice for {invoice_data.get('invoice_id')}</html>",
            "json_content": json.dumps(invoice_data, indent=2),
            "template_fields": template.get("fields", []),
            "formatting_applied": template.get("formatting", {})
        }
    
    def _generate_data_hash(self, data: Dict[str, Any]) -> str:
        """Generate hash of invoice data for caching"""
        import hashlib
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def validate_template(self, template: Dict[str, Any]) -> bool:
        """Validate template structure"""
        required_fields = ["name", "structure", "fields"]
        return all(field in template for field in required_fields)
    
    async def list_available_templates(self) -> List[str]:
        """List all available templates"""
        return list(self.default_templates.keys())
    
    async def create_custom_template(
        self,
        template_name: str,
        template_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create new custom template"""
        if not await self.validate_template(template_config):
            raise ValueError("Invalid template configuration")
        
        template_config.update({
            "name": template_name,
            "created_at": datetime.now().isoformat(),
            "is_custom": True
        })
        
        # TODO: Save template to persistent storage
        self.template_cache[template_name] = template_config
        
        return template_config