"""
Advanced Cross-Platform Data Mapping for CRM Integrations.

This module provides sophisticated data mapping capabilities that can transform
data between different CRM platforms and the TaxPoynt invoice format, with
support for custom field mappings and transformation rules.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field
from enum import Enum
import re

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    """Supported field types for data mapping."""
    STRING = "string"
    NUMBER = "number"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"
    ARRAY = "array"
    OBJECT = "object"


class TransformationRule(str, Enum):
    """Available transformation rules."""
    NONE = "none"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    CAPITALIZE = "capitalize"
    STRIP_SPACES = "strip_spaces"
    FORMAT_PHONE = "format_phone"
    FORMAT_EMAIL = "format_email"
    CONVERT_CURRENCY = "convert_currency"
    PARSE_DATE = "parse_date"
    EXTRACT_DOMAIN = "extract_domain"
    CONCATENATE = "concatenate"
    SPLIT = "split"
    CUSTOM = "custom"


@dataclass
class FieldMapping:
    """Represents a field mapping configuration."""
    source_field: str
    target_field: str
    field_type: FieldType = FieldType.STRING
    required: bool = False
    default_value: Any = None
    transformation_rules: List[TransformationRule] = field(default_factory=list)
    validation_pattern: Optional[str] = None
    custom_transformer: Optional[str] = None
    description: Optional[str] = None


@dataclass
class PlatformMapping:
    """Represents a complete platform mapping configuration."""
    platform_name: str
    platform_version: str
    field_mappings: List[FieldMapping]
    global_transformations: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataTransformer:
    """Handles data transformation between different CRM platforms."""
    
    def __init__(self):
        """Initialize the data transformer."""
        self.custom_transformers: Dict[str, Callable] = {}
        self.currency_rates: Dict[str, Decimal] = {
            "USD": Decimal("1.0"),
            "NGN": Decimal("0.0013"),  # Example rate
            "EUR": Decimal("1.08"),
            "GBP": Decimal("1.27")
        }
    
    def register_custom_transformer(self, name: str, transformer: Callable):
        """Register a custom transformation function."""
        self.custom_transformers[name] = transformer
    
    def transform_field(
        self,
        value: Any,
        mapping: FieldMapping,
        context: Dict[str, Any] = None
    ) -> Any:
        """
        Transform a single field value according to mapping rules.
        
        Args:
            value: The source value to transform
            mapping: Field mapping configuration
            context: Additional context for transformation
            
        Returns:
            Transformed value
        """
        if context is None:
            context = {}
        
        # Handle None/empty values
        if value is None or (isinstance(value, str) and not value.strip()):
            if mapping.required and mapping.default_value is not None:
                value = mapping.default_value
            elif mapping.required:
                raise ValueError(f"Required field '{mapping.target_field}' is missing")
            else:
                return mapping.default_value
        
        # Apply type conversion
        try:
            value = self._convert_type(value, mapping.field_type)
        except Exception as e:
            logger.warning(f"Type conversion failed for field '{mapping.source_field}': {e}")
            if mapping.default_value is not None:
                value = mapping.default_value
            else:
                raise
        
        # Apply transformation rules
        for rule in mapping.transformation_rules:
            try:
                value = self._apply_transformation_rule(value, rule, context)
            except Exception as e:
                logger.warning(f"Transformation rule '{rule}' failed for field '{mapping.source_field}': {e}")
        
        # Apply custom transformer
        if mapping.custom_transformer and mapping.custom_transformer in self.custom_transformers:
            try:
                value = self.custom_transformers[mapping.custom_transformer](value, context)
            except Exception as e:
                logger.warning(f"Custom transformer '{mapping.custom_transformer}' failed: {e}")
        
        # Validate result
        if mapping.validation_pattern:
            if not re.match(mapping.validation_pattern, str(value)):
                raise ValueError(f"Field '{mapping.target_field}' validation failed")
        
        return value
    
    def _convert_type(self, value: Any, field_type: FieldType) -> Any:
        """Convert value to specified type."""
        if field_type == FieldType.STRING:
            return str(value) if value is not None else ""
        
        elif field_type == FieldType.NUMBER:
            if isinstance(value, (int, float)):
                return int(value)
            return int(float(str(value).replace(",", "")))
        
        elif field_type == FieldType.DECIMAL:
            if isinstance(value, Decimal):
                return value
            return Decimal(str(value).replace(",", ""))
        
        elif field_type == FieldType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1", "on")
            return bool(value)
        
        elif field_type == FieldType.DATE:
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, str):
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
                raise ValueError(f"Unable to parse date: {value}")
            return value
        
        elif field_type == FieldType.DATETIME:
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                # Try common datetime formats
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"]:
                    try:
                        dt = datetime.strptime(value, fmt)
                        # Ensure timezone info
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        return dt
                    except ValueError:
                        continue
                raise ValueError(f"Unable to parse datetime: {value}")
            return value
        
        elif field_type == FieldType.EMAIL:
            email = str(value).strip().lower()
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise ValueError(f"Invalid email format: {email}")
            return email
        
        elif field_type == FieldType.PHONE:
            phone = re.sub(r'[^\d+]', '', str(value))
            if not phone.startswith('+') and len(phone) >= 10:
                phone = '+234' + phone[-10:]  # Default to Nigeria
            return phone
        
        elif field_type == FieldType.CURRENCY:
            # Extract numeric value from currency string
            currency_str = str(value).replace(",", "").replace("$", "").replace("€", "").replace("£", "")
            return Decimal(currency_str)
        
        elif field_type == FieldType.ARRAY:
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                # Try to parse as JSON array
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass
                # Split by common delimiters
                return [item.strip() for item in value.split(",")]
            return [value]
        
        elif field_type == FieldType.OBJECT:
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return {"value": value}
            return {"value": value}
        
        return value
    
    def _apply_transformation_rule(
        self,
        value: Any,
        rule: TransformationRule,
        context: Dict[str, Any]
    ) -> Any:
        """Apply a specific transformation rule."""
        if rule == TransformationRule.NONE:
            return value
        
        elif rule == TransformationRule.UPPERCASE:
            return str(value).upper()
        
        elif rule == TransformationRule.LOWERCASE:
            return str(value).lower()
        
        elif rule == TransformationRule.CAPITALIZE:
            return str(value).title()
        
        elif rule == TransformationRule.STRIP_SPACES:
            return str(value).strip()
        
        elif rule == TransformationRule.FORMAT_PHONE:
            phone = re.sub(r'[^\d+]', '', str(value))
            if phone.startswith('+234') and len(phone) == 14:
                return f"+234 {phone[4:7]} {phone[7:10]} {phone[10:]}"
            return phone
        
        elif rule == TransformationRule.FORMAT_EMAIL:
            return str(value).strip().lower()
        
        elif rule == TransformationRule.CONVERT_CURRENCY:
            # Convert currency based on context
            from_currency = context.get("source_currency", "USD")
            to_currency = context.get("target_currency", "NGN")
            
            if from_currency != to_currency:
                rate = self.currency_rates.get(to_currency, Decimal("1")) / self.currency_rates.get(from_currency, Decimal("1"))
                return Decimal(str(value)) * rate
            return value
        
        elif rule == TransformationRule.PARSE_DATE:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        
        elif rule == TransformationRule.EXTRACT_DOMAIN:
            if '@' in str(value):
                return str(value).split('@')[1]
            return value
        
        elif rule == TransformationRule.CONCATENATE:
            # Concatenate with other fields from context
            parts = [str(value)]
            concat_fields = context.get("concatenate_fields", [])
            for field in concat_fields:
                if field in context:
                    parts.append(str(context[field]))
            separator = context.get("separator", " ")
            return separator.join(parts)
        
        elif rule == TransformationRule.SPLIT:
            delimiter = context.get("split_delimiter", ",")
            index = context.get("split_index", 0)
            parts = str(value).split(delimiter)
            if 0 <= index < len(parts):
                return parts[index].strip()
            return value
        
        return value


class CrossPlatformMapper:
    """Main class for cross-platform CRM data mapping."""
    
    def __init__(self):
        """Initialize the cross-platform mapper."""
        self.transformer = DataTransformer()
        self.platform_mappings: Dict[str, PlatformMapping] = {}
        self._load_default_mappings()
    
    def _load_default_mappings(self):
        """Load default platform mappings."""
        # HubSpot mapping
        hubspot_mappings = [
            FieldMapping("properties.dealname", "deal_title", FieldType.STRING, required=True),
            FieldMapping("properties.amount", "deal_amount", FieldType.DECIMAL, default_value=Decimal("0")),
            FieldMapping("properties.dealstage", "deal_stage", FieldType.STRING),
            FieldMapping("properties.closedate", "expected_close_date", FieldType.DATE),
            FieldMapping("properties.createdate", "created_at_source", FieldType.DATETIME),
            FieldMapping("id", "external_deal_id", FieldType.STRING, required=True),
        ]
        
        self.platform_mappings["hubspot"] = PlatformMapping(
            platform_name="HubSpot",
            platform_version="v3",
            field_mappings=hubspot_mappings
        )
        
        # Salesforce mapping
        salesforce_mappings = [
            FieldMapping("Name", "deal_title", FieldType.STRING, required=True),
            FieldMapping("Amount", "deal_amount", FieldType.DECIMAL, default_value=Decimal("0")),
            FieldMapping("StageName", "deal_stage", FieldType.STRING),
            FieldMapping("CloseDate", "expected_close_date", FieldType.DATE),
            FieldMapping("CreatedDate", "created_at_source", FieldType.DATETIME),
            FieldMapping("Id", "external_deal_id", FieldType.STRING, required=True),
            FieldMapping("Account.Name", "customer_name", FieldType.STRING),
            FieldMapping("Account.Phone", "customer_phone", FieldType.PHONE, transformation_rules=[TransformationRule.FORMAT_PHONE]),
        ]
        
        self.platform_mappings["salesforce"] = PlatformMapping(
            platform_name="Salesforce",
            platform_version="v58.0",
            field_mappings=salesforce_mappings
        )
    
    def register_platform_mapping(self, mapping: PlatformMapping):
        """Register a new platform mapping."""
        self.platform_mappings[mapping.platform_name.lower()] = mapping
    
    def map_data(
        self,
        source_data: Dict[str, Any],
        source_platform: str,
        target_format: str = "taxpoynt",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Map data from source platform to target format.
        
        Args:
            source_data: Source data to transform
            source_platform: Source platform name
            target_format: Target format (default: taxpoynt)
            context: Additional context for transformation
            
        Returns:
            Transformed data
        """
        if context is None:
            context = {}
        
        platform_key = source_platform.lower()
        if platform_key not in self.platform_mappings:
            raise ValueError(f"Platform mapping not found for: {source_platform}")
        
        mapping = self.platform_mappings[platform_key]
        transformed_data = {}
        
        # Apply field mappings
        for field_mapping in mapping.field_mappings:
            try:
                # Extract source value using dot notation
                source_value = self._get_nested_value(source_data, field_mapping.source_field)
                
                # Transform the value
                transformed_value = self.transformer.transform_field(
                    source_value, field_mapping, context
                )
                
                # Set the target value using dot notation
                self._set_nested_value(transformed_data, field_mapping.target_field, transformed_value)
                
            except Exception as e:
                logger.warning(f"Field mapping failed for '{field_mapping.source_field}': {e}")
                if field_mapping.required:
                    raise
        
        # Apply global transformations
        for transform_name, transform_config in mapping.global_transformations.items():
            try:
                self._apply_global_transformation(transformed_data, transform_name, transform_config)
            except Exception as e:
                logger.warning(f"Global transformation '{transform_name}' failed: {e}")
        
        # Add metadata
        transformed_data["_mapping_metadata"] = {
            "source_platform": mapping.platform_name,
            "platform_version": mapping.platform_version,
            "mapped_at": datetime.now(timezone.utc).isoformat(),
            "mapping_version": "1.0"
        }
        
        return transformed_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dictionary using dot notation."""
        keys = path.split(".")
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _apply_global_transformation(
        self,
        data: Dict[str, Any],
        transform_name: str,
        transform_config: Dict[str, Any]
    ):
        """Apply global transformation to the entire data structure."""
        if transform_name == "add_computed_fields":
            # Add computed fields based on configuration
            for field_name, computation in transform_config.items():
                if computation["type"] == "concatenate":
                    fields = computation.get("fields", [])
                    separator = computation.get("separator", " ")
                    values = []
                    for field in fields:
                        value = self._get_nested_value(data, field)
                        if value:
                            values.append(str(value))
                    self._set_nested_value(data, field_name, separator.join(values))
        
        elif transform_name == "normalize_currency":
            # Normalize all currency fields to a specific currency
            target_currency = transform_config.get("target_currency", "NGN")
            currency_fields = transform_config.get("fields", [])
            
            for field in currency_fields:
                value = self._get_nested_value(data, field)
                if value is not None:
                    # Apply currency conversion logic here
                    self._set_nested_value(data, field, value)
    
    def get_mapping_schema(self, platform: str) -> Dict[str, Any]:
        """Get the mapping schema for a platform."""
        platform_key = platform.lower()
        if platform_key not in self.platform_mappings:
            raise ValueError(f"Platform mapping not found for: {platform}")
        
        mapping = self.platform_mappings[platform_key]
        
        schema = {
            "platform": mapping.platform_name,
            "version": mapping.platform_version,
            "fields": []
        }
        
        for field_mapping in mapping.field_mappings:
            schema["fields"].append({
                "source_field": field_mapping.source_field,
                "target_field": field_mapping.target_field,
                "type": field_mapping.field_type.value,
                "required": field_mapping.required,
                "default_value": field_mapping.default_value,
                "transformations": [rule.value for rule in field_mapping.transformation_rules],
                "description": field_mapping.description
            })
        
        return schema
    
    def validate_mapping(self, platform: str, sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a mapping against sample data."""
        try:
            result = self.map_data(sample_data, platform)
            return {
                "valid": True,
                "mapped_fields": len([k for k in result.keys() if not k.startswith("_")]),
                "sample_result": result
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "mapped_fields": 0
            }


# Global instance
cross_platform_mapper = CrossPlatformMapper()