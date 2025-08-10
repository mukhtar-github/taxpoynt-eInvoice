"""
Data Transformer - Universal Connector Framework
Universal data transformation system for external system connectors.
Handles data format conversion, field mapping, validation, and normalization.
"""

import asyncio
import logging
import json
import xml.etree.ElementTree as ET
import csv
import io
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import re

from .base_connector import DataFormat

logger = logging.getLogger(__name__)

class TransformationType(Enum):
    FORMAT_CONVERSION = "format_conversion"
    FIELD_MAPPING = "field_mapping"
    VALUE_TRANSFORMATION = "value_transformation"
    DATA_VALIDATION = "data_validation"
    DATA_ENRICHMENT = "data_enrichment"
    DATA_FILTERING = "data_filtering"
    DATA_AGGREGATION = "data_aggregation"

class ValidationLevel(Enum):
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"
    NONE = "none"

@dataclass
class FieldMapping:
    source_field: str
    target_field: str
    transformation_function: Optional[str] = None
    default_value: Optional[Any] = None
    required: bool = False
    validation_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TransformationRule:
    rule_id: str
    name: str
    transformation_type: TransformationType
    condition: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TransformationProfile:
    profile_id: str
    name: str
    description: str
    source_format: DataFormat
    target_format: DataFormat
    field_mappings: List[FieldMapping] = field(default_factory=list)
    transformation_rules: List[TransformationRule] = field(default_factory=list)
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TransformationResult:
    success: bool
    transformed_data: Optional[Any] = None
    original_data: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    applied_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    transformation_time_ms: float = 0.0

class DataTransformer:
    """Universal data transformation system"""
    
    def __init__(self):
        self.profiles: Dict[str, TransformationProfile] = {}
        self.transformation_functions: Dict[str, Callable] = {}
        self.validation_functions: Dict[str, Callable] = {}
        
        # Initialize built-in transformation functions
        self._initialize_builtin_functions()
        
        # Load default profiles
        self._load_default_profiles()
    
    def _initialize_builtin_functions(self):
        """Initialize built-in transformation and validation functions"""
        
        # Built-in transformation functions
        self.transformation_functions.update({
            'uppercase': lambda x: str(x).upper(),
            'lowercase': lambda x: str(x).lower(),
            'strip': lambda x: str(x).strip(),
            'to_string': lambda x: str(x),
            'to_int': lambda x: int(float(str(x))) if x is not None else None,
            'to_float': lambda x: float(str(x)) if x is not None else None,
            'to_decimal': lambda x: Decimal(str(x)) if x is not None else None,
            'to_bool': lambda x: str(x).lower() in ('true', '1', 'yes', 'on') if x is not None else None,
            'format_date': lambda x: self._format_date(x),
            'format_datetime': lambda x: self._format_datetime(x),
            'normalize_phone': lambda x: self._normalize_phone(x),
            'normalize_email': lambda x: str(x).lower().strip() if x else None,
            'extract_numbers': lambda x: re.sub(r'[^0-9.]', '', str(x)) if x else None,
            'remove_special_chars': lambda x: re.sub(r'[^a-zA-Z0-9\s]', '', str(x)) if x else None,
            'truncate': lambda x, length=255: str(x)[:length] if x else None,
            'pad_left': lambda x, width=10, char='0': str(x).ljust(width, char) if x else None,
            'pad_right': lambda x, width=10, char=' ': str(x).rjust(width, char) if x else None,
            'currency_to_cents': lambda x: int(float(str(x)) * 100) if x is not None else None,
            'cents_to_currency': lambda x: float(int(x)) / 100 if x is not None else None,
            'split_string': lambda x, delimiter=',': str(x).split(delimiter) if x else [],
            'join_list': lambda x, delimiter=',': delimiter.join(str(item) for item in x) if isinstance(x, list) else str(x),
            'hash_value': lambda x: str(hash(str(x))) if x is not None else None,
            'generate_uuid': lambda x: str(__import__('uuid').uuid4()),
            'current_timestamp': lambda x: datetime.utcnow().isoformat()
        })
        
        # Built-in validation functions
        self.validation_functions.update({
            'required': lambda x: x is not None and str(x).strip() != '',
            'email': lambda x: self._validate_email(x),
            'phone': lambda x: self._validate_phone(x),
            'numeric': lambda x: self._validate_numeric(x),
            'date': lambda x: self._validate_date(x),
            'url': lambda x: self._validate_url(x),
            'min_length': lambda x, min_len=1: len(str(x)) >= min_len if x else False,
            'max_length': lambda x, max_len=255: len(str(x)) <= max_len if x else True,
            'regex': lambda x, pattern: re.match(pattern, str(x)) is not None if x else False,
            'in_list': lambda x, valid_values: str(x) in valid_values if x else False,
            'range': lambda x, min_val, max_val: min_val <= float(str(x)) <= max_val if x else False
        })
    
    def _load_default_profiles(self):
        """Load default transformation profiles"""
        default_profiles = [
            TransformationProfile(
                profile_id="json_to_xml",
                name="JSON to XML Converter",
                description="Convert JSON data to XML format",
                source_format=DataFormat.JSON,
                target_format=DataFormat.XML,
                transformation_rules=[
                    TransformationRule(
                        rule_id="json_xml_conversion",
                        name="JSON to XML Conversion",
                        transformation_type=TransformationType.FORMAT_CONVERSION,
                        parameters={'root_element': 'root'}
                    )
                ]
            ),
            TransformationProfile(
                profile_id="xml_to_json",
                name="XML to JSON Converter",
                description="Convert XML data to JSON format",
                source_format=DataFormat.XML,
                target_format=DataFormat.JSON,
                transformation_rules=[
                    TransformationRule(
                        rule_id="xml_json_conversion",
                        name="XML to JSON Conversion",
                        transformation_type=TransformationType.FORMAT_CONVERSION
                    )
                ]
            ),
            TransformationProfile(
                profile_id="csv_to_json",
                name="CSV to JSON Converter",
                description="Convert CSV data to JSON format",
                source_format=DataFormat.CSV,
                target_format=DataFormat.JSON,
                transformation_rules=[
                    TransformationRule(
                        rule_id="csv_json_conversion",
                        name="CSV to JSON Conversion",
                        transformation_type=TransformationType.FORMAT_CONVERSION,
                        parameters={'delimiter': ',', 'has_header': True}
                    )
                ]
            ),
            TransformationProfile(
                profile_id="data_normalization",
                name="Data Normalization Profile",
                description="Normalize common data fields",
                source_format=DataFormat.JSON,
                target_format=DataFormat.JSON,
                field_mappings=[
                    FieldMapping(
                        source_field="email",
                        target_field="email",
                        transformation_function="normalize_email",
                        validation_rules=["required", "email"]
                    ),
                    FieldMapping(
                        source_field="phone",
                        target_field="phone",
                        transformation_function="normalize_phone",
                        validation_rules=["phone"]
                    ),
                    FieldMapping(
                        source_field="name",
                        target_field="name",
                        transformation_function="strip",
                        validation_rules=["required", "max_length:100"]
                    )
                ]
            )
        ]
        
        for profile in default_profiles:
            self.profiles[profile.profile_id] = profile
    
    def add_transformation_profile(self, profile: TransformationProfile) -> bool:
        """Add a transformation profile"""
        try:
            self.profiles[profile.profile_id] = profile
            logger.info(f"Added transformation profile: {profile.profile_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add transformation profile: {e}")
            return False
    
    def get_transformation_profile(self, profile_id: str) -> Optional[TransformationProfile]:
        """Get transformation profile by ID"""
        return self.profiles.get(profile_id)
    
    def list_transformation_profiles(self) -> List[TransformationProfile]:
        """List all transformation profiles"""
        return list(self.profiles.values())
    
    def add_transformation_function(self, name: str, function: Callable) -> bool:
        """Add a custom transformation function"""
        try:
            self.transformation_functions[name] = function
            logger.info(f"Added transformation function: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add transformation function: {e}")
            return False
    
    def add_validation_function(self, name: str, function: Callable) -> bool:
        """Add a custom validation function"""
        try:
            self.validation_functions[name] = function
            logger.info(f"Added validation function: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add validation function: {e}")
            return False
    
    async def transform_data(self, data: Any, profile_id: str, 
                           custom_parameters: Optional[Dict[str, Any]] = None) -> TransformationResult:
        """Transform data using the specified profile"""
        start_time = datetime.utcnow()
        
        try:
            profile = self.profiles.get(profile_id)
            if not profile:
                return TransformationResult(
                    success=False,
                    original_data=data,
                    errors=[f"Transformation profile not found: {profile_id}"]
                )
            
            result = TransformationResult(
                success=True,
                original_data=data,
                transformed_data=data
            )
            
            # Apply transformation rules in priority order
            rules = sorted(profile.transformation_rules, key=lambda r: r.priority)
            
            for rule in rules:
                if not rule.enabled:
                    continue
                
                # Check condition if specified
                if rule.condition and not self._evaluate_condition(result.transformed_data, rule.condition):
                    continue
                
                # Apply transformation based on type
                if rule.transformation_type == TransformationType.FORMAT_CONVERSION:
                    result = await self._apply_format_conversion(result, rule, profile)
                elif rule.transformation_type == TransformationType.FIELD_MAPPING:
                    result = await self._apply_field_mapping(result, profile.field_mappings)
                elif rule.transformation_type == TransformationType.VALUE_TRANSFORMATION:
                    result = await self._apply_value_transformation(result, rule)
                elif rule.transformation_type == TransformationType.DATA_VALIDATION:
                    result = await self._apply_data_validation(result, profile)
                elif rule.transformation_type == TransformationType.DATA_ENRICHMENT:
                    result = await self._apply_data_enrichment(result, rule)
                elif rule.transformation_type == TransformationType.DATA_FILTERING:
                    result = await self._apply_data_filtering(result, rule)
                elif rule.transformation_type == TransformationType.DATA_AGGREGATION:
                    result = await self._apply_data_aggregation(result, rule)
                
                if not result.success:
                    break
                
                result.applied_rules.append(rule.rule_id)
            
            # Apply field mappings if not already applied
            if profile.field_mappings and not any(r.transformation_type == TransformationType.FIELD_MAPPING for r in rules):
                result = await self._apply_field_mapping(result, profile.field_mappings)
            
            # Calculate transformation time
            end_time = datetime.utcnow()
            result.transformation_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            transformation_time = (end_time - start_time).total_seconds() * 1000
            
            logger.error(f"Data transformation failed: {e}")
            return TransformationResult(
                success=False,
                original_data=data,
                errors=[str(e)],
                transformation_time_ms=transformation_time
            )
    
    async def _apply_format_conversion(self, result: TransformationResult, rule: TransformationRule, 
                                     profile: TransformationProfile) -> TransformationResult:
        """Apply format conversion transformation"""
        try:
            source_format = profile.source_format
            target_format = profile.target_format
            data = result.transformed_data
            
            if source_format == target_format:
                return result
            
            # JSON to XML
            if source_format == DataFormat.JSON and target_format == DataFormat.XML:
                if isinstance(data, (dict, list)):
                    root_element = rule.parameters.get('root_element', 'root')
                    xml_data = self._json_to_xml(data, root_element)
                    result.transformed_data = xml_data
                else:
                    result.errors.append("Invalid JSON data for XML conversion")
                    result.success = False
            
            # XML to JSON
            elif source_format == DataFormat.XML and target_format == DataFormat.JSON:
                if isinstance(data, str):
                    json_data = self._xml_to_json(data)
                    result.transformed_data = json_data
                else:
                    result.errors.append("Invalid XML data for JSON conversion")
                    result.success = False
            
            # CSV to JSON
            elif source_format == DataFormat.CSV and target_format == DataFormat.JSON:
                if isinstance(data, str):
                    delimiter = rule.parameters.get('delimiter', ',')
                    has_header = rule.parameters.get('has_header', True)
                    json_data = self._csv_to_json(data, delimiter, has_header)
                    result.transformed_data = json_data
                else:
                    result.errors.append("Invalid CSV data for JSON conversion")
                    result.success = False
            
            # JSON to CSV
            elif source_format == DataFormat.JSON and target_format == DataFormat.CSV:
                if isinstance(data, (list, dict)):
                    delimiter = rule.parameters.get('delimiter', ',')
                    csv_data = self._json_to_csv(data, delimiter)
                    result.transformed_data = csv_data
                else:
                    result.errors.append("Invalid JSON data for CSV conversion")
                    result.success = False
            
            else:
                result.warnings.append(f"Unsupported format conversion: {source_format.value} to {target_format.value}")
            
            return result
            
        except Exception as e:
            result.errors.append(f"Format conversion failed: {e}")
            result.success = False
            return result
    
    async def _apply_field_mapping(self, result: TransformationResult, 
                                 field_mappings: List[FieldMapping]) -> TransformationResult:
        """Apply field mapping transformation"""
        try:
            if not isinstance(result.transformed_data, dict):
                result.warnings.append("Field mapping requires dictionary data")
                return result
            
            source_data = result.transformed_data
            mapped_data = {}
            
            for mapping in field_mappings:
                # Get source value
                source_value = self._get_nested_value(source_data, mapping.source_field)
                
                # Apply transformation function if specified
                if mapping.transformation_function and mapping.transformation_function in self.transformation_functions:
                    transform_func = self.transformation_functions[mapping.transformation_function]
                    try:
                        source_value = transform_func(source_value)
                    except Exception as e:
                        result.warnings.append(f"Transformation function '{mapping.transformation_function}' failed for field '{mapping.source_field}': {e}")
                
                # Use default value if source is None/empty and default is provided
                if (source_value is None or source_value == '') and mapping.default_value is not None:
                    source_value = mapping.default_value
                
                # Apply validation rules
                for rule in mapping.validation_rules:
                    if not self._validate_field_value(source_value, rule):
                        if mapping.required:
                            result.errors.append(f"Validation failed for required field '{mapping.target_field}': {rule}")
                            result.success = False
                        else:
                            result.warnings.append(f"Validation failed for field '{mapping.target_field}': {rule}")
                
                # Set target value
                self._set_nested_value(mapped_data, mapping.target_field, source_value)
            
            result.transformed_data = mapped_data
            return result
            
        except Exception as e:
            result.errors.append(f"Field mapping failed: {e}")
            result.success = False
            return result
    
    async def _apply_value_transformation(self, result: TransformationResult, rule: TransformationRule) -> TransformationResult:
        """Apply value transformation"""
        try:
            function_name = rule.parameters.get('function')
            field_path = rule.parameters.get('field')
            
            if not function_name or function_name not in self.transformation_functions:
                result.warnings.append(f"Transformation function not found: {function_name}")
                return result
            
            if isinstance(result.transformed_data, dict) and field_path:
                # Transform specific field
                current_value = self._get_nested_value(result.transformed_data, field_path)
                transform_func = self.transformation_functions[function_name]
                
                try:
                    new_value = transform_func(current_value, **rule.parameters.get('function_args', {}))
                    self._set_nested_value(result.transformed_data, field_path, new_value)
                except Exception as e:
                    result.warnings.append(f"Value transformation failed for field '{field_path}': {e}")
            else:
                # Transform entire data
                transform_func = self.transformation_functions[function_name]
                try:
                    result.transformed_data = transform_func(result.transformed_data, **rule.parameters.get('function_args', {}))
                except Exception as e:
                    result.errors.append(f"Value transformation failed: {e}")
                    result.success = False
            
            return result
            
        except Exception as e:
            result.errors.append(f"Value transformation rule failed: {e}")
            result.success = False
            return result
    
    async def _apply_data_validation(self, result: TransformationResult, profile: TransformationProfile) -> TransformationResult:
        """Apply data validation"""
        try:
            if profile.validation_level == ValidationLevel.NONE:
                return result
            
            validation_errors = []
            validation_warnings = []
            
            # Validate using field mappings
            for mapping in profile.field_mappings:
                if isinstance(result.transformed_data, dict):
                    field_value = self._get_nested_value(result.transformed_data, mapping.target_field)
                    
                    for rule in mapping.validation_rules:
                        if not self._validate_field_value(field_value, rule):
                            error_msg = f"Validation failed for field '{mapping.target_field}': {rule}"
                            
                            if mapping.required or profile.validation_level == ValidationLevel.STRICT:
                                validation_errors.append(error_msg)
                            else:
                                validation_warnings.append(error_msg)
            
            result.errors.extend(validation_errors)
            result.warnings.extend(validation_warnings)
            
            if validation_errors and profile.validation_level == ValidationLevel.STRICT:
                result.success = False
            
            return result
            
        except Exception as e:
            result.errors.append(f"Data validation failed: {e}")
            result.success = False
            return result
    
    async def _apply_data_enrichment(self, result: TransformationResult, rule: TransformationRule) -> TransformationResult:
        """Apply data enrichment"""
        try:
            enrichment_type = rule.parameters.get('type')
            
            if enrichment_type == 'add_timestamp':
                if isinstance(result.transformed_data, dict):
                    field_name = rule.parameters.get('field', 'timestamp')
                    result.transformed_data[field_name] = datetime.utcnow().isoformat()
            
            elif enrichment_type == 'add_uuid':
                if isinstance(result.transformed_data, dict):
                    field_name = rule.parameters.get('field', 'id')
                    import uuid
                    result.transformed_data[field_name] = str(uuid.uuid4())
            
            elif enrichment_type == 'calculate_field':
                # Calculate field based on other fields
                formula = rule.parameters.get('formula')
                target_field = rule.parameters.get('target_field')
                
                if formula and target_field and isinstance(result.transformed_data, dict):
                    try:
                        # Simple formula evaluation (security risk in production - use safer method)
                        calculated_value = eval(formula, {"__builtins__": {}}, result.transformed_data)
                        result.transformed_data[target_field] = calculated_value
                    except Exception as e:
                        result.warnings.append(f"Formula calculation failed: {e}")
            
            return result
            
        except Exception as e:
            result.warnings.append(f"Data enrichment failed: {e}")
            return result
    
    async def _apply_data_filtering(self, result: TransformationResult, rule: TransformationRule) -> TransformationResult:
        """Apply data filtering"""
        try:
            filter_condition = rule.parameters.get('condition')
            
            if isinstance(result.transformed_data, list):
                # Filter list items
                if filter_condition:
                    filtered_data = []
                    for item in result.transformed_data:
                        if self._evaluate_condition(item, filter_condition):
                            filtered_data.append(item)
                    result.transformed_data = filtered_data
            
            elif isinstance(result.transformed_data, dict):
                # Filter dictionary fields
                fields_to_remove = rule.parameters.get('remove_fields', [])
                for field in fields_to_remove:
                    if field in result.transformed_data:
                        del result.transformed_data[field]
            
            return result
            
        except Exception as e:
            result.warnings.append(f"Data filtering failed: {e}")
            return result
    
    async def _apply_data_aggregation(self, result: TransformationResult, rule: TransformationRule) -> TransformationResult:
        """Apply data aggregation"""
        try:
            if not isinstance(result.transformed_data, list):
                result.warnings.append("Data aggregation requires list data")
                return result
            
            aggregation_type = rule.parameters.get('type')
            field = rule.parameters.get('field')
            
            if aggregation_type == 'count':
                result.transformed_data = {'count': len(result.transformed_data)}
            
            elif aggregation_type == 'sum' and field:
                total = sum(float(item.get(field, 0)) for item in result.transformed_data if isinstance(item, dict))
                result.transformed_data = {'sum': total}
            
            elif aggregation_type == 'group_by' and field:
                groups = {}
                for item in result.transformed_data:
                    if isinstance(item, dict) and field in item:
                        key = item[field]
                        if key not in groups:
                            groups[key] = []
                        groups[key].append(item)
                result.transformed_data = groups
            
            return result
            
        except Exception as e:
            result.warnings.append(f"Data aggregation failed: {e}")
            return result
    
    # Helper methods for format conversion
    def _json_to_xml(self, data: Union[Dict, List], root_element: str = 'root') -> str:
        """Convert JSON to XML"""
        try:
            def dict_to_xml(d, parent_element):
                for key, value in d.items():
                    element = ET.SubElement(parent_element, str(key))
                    if isinstance(value, dict):
                        dict_to_xml(value, element)
                    elif isinstance(value, list):
                        for item in value:
                            item_element = ET.SubElement(element, 'item')
                            if isinstance(item, dict):
                                dict_to_xml(item, item_element)
                            else:
                                item_element.text = str(item)
                    else:
                        element.text = str(value)
            
            root = ET.Element(root_element)
            
            if isinstance(data, dict):
                dict_to_xml(data, root)
            elif isinstance(data, list):
                for item in data:
                    item_element = ET.SubElement(root, 'item')
                    if isinstance(item, dict):
                        dict_to_xml(item, item_element)
                    else:
                        item_element.text = str(item)
            
            return ET.tostring(root, encoding='unicode')
            
        except Exception as e:
            logger.error(f"JSON to XML conversion failed: {e}")
            return f"<error>Conversion failed: {e}</error>"
    
    def _xml_to_json(self, xml_data: str) -> Union[Dict, List]:
        """Convert XML to JSON"""
        try:
            def xml_to_dict(element):
                result = {}
                
                # Add attributes
                if element.attrib:
                    result['@attributes'] = element.attrib
                
                # Add text content
                if element.text and element.text.strip():
                    if len(element) == 0:
                        return element.text.strip()
                    result['#text'] = element.text.strip()
                
                # Add child elements
                for child in element:
                    child_data = xml_to_dict(child)
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = child_data
                
                return result if result else None
            
            root = ET.fromstring(xml_data)
            return xml_to_dict(root)
            
        except Exception as e:
            logger.error(f"XML to JSON conversion failed: {e}")
            return {'error': f'Conversion failed: {e}'}
    
    def _csv_to_json(self, csv_data: str, delimiter: str = ',', has_header: bool = True) -> List[Dict]:
        """Convert CSV to JSON"""
        try:
            reader = csv.reader(io.StringIO(csv_data), delimiter=delimiter)
            
            if has_header:
                headers = next(reader)
                return [dict(zip(headers, row)) for row in reader]
            else:
                return [{'column_' + str(i): value for i, value in enumerate(row)} for row in reader]
                
        except Exception as e:
            logger.error(f"CSV to JSON conversion failed: {e}")
            return [{'error': f'Conversion failed: {e}'}]
    
    def _json_to_csv(self, json_data: Union[List[Dict], Dict], delimiter: str = ',') -> str:
        """Convert JSON to CSV"""
        try:
            if isinstance(json_data, dict):
                json_data = [json_data]
            
            if not json_data:
                return ""
            
            # Get all unique keys
            all_keys = set()
            for item in json_data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=sorted(all_keys), delimiter=delimiter)
            
            writer.writeheader()
            for item in json_data:
                if isinstance(item, dict):
                    writer.writerow(item)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"JSON to CSV conversion failed: {e}")
            return f"error,Conversion failed: {e}"
    
    # Helper methods for data manipulation
    def _get_nested_value(self, data: Dict, field_path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        try:
            keys = field_path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            return value
            
        except Exception:
            return None
    
    def _set_nested_value(self, data: Dict, field_path: str, value: Any):
        """Set nested value in dictionary using dot notation"""
        try:
            keys = field_path.split('.')
            current = data
            
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            current[keys[-1]] = value
            
        except Exception as e:
            logger.error(f"Failed to set nested value: {e}")
    
    def _evaluate_condition(self, data: Any, condition: str) -> bool:
        """Evaluate a simple condition against data"""
        try:
            # Simple condition evaluation (in production, use safer method)
            # This is a security risk - implement proper condition parser
            return eval(condition, {"__builtins__": {}}, data if isinstance(data, dict) else {"data": data})
        except Exception:
            return False
    
    def _validate_field_value(self, value: Any, rule: str) -> bool:
        """Validate field value against rule"""
        try:
            # Parse rule (e.g., "max_length:100", "required", "email")
            if ':' in rule:
                rule_name, rule_params = rule.split(':', 1)
                params = rule_params.split(',')
            else:
                rule_name = rule
                params = []
            
            if rule_name in self.validation_functions:
                validation_func = self.validation_functions[rule_name]
                
                if params:
                    # Convert string parameters to appropriate types
                    converted_params = []
                    for param in params:
                        try:
                            # Try to convert to number
                            if '.' in param:
                                converted_params.append(float(param))
                            else:
                                converted_params.append(int(param))
                        except ValueError:
                            converted_params.append(param)
                    
                    return validation_func(value, *converted_params)
                else:
                    return validation_func(value)
            
            return True
            
        except Exception as e:
            logger.error(f"Field validation failed: {e}")
            return False
    
    # Built-in transformation helper functions
    def _format_date(self, value: Any) -> Optional[str]:
        """Format date value"""
        try:
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, date):
                return value.strftime('%Y-%m-%d')
            elif isinstance(value, str):
                # Try to parse and reformat
                parsed_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return parsed_date.strftime('%Y-%m-%d')
            return None
        except Exception:
            return str(value) if value else None
    
    def _format_datetime(self, value: Any) -> Optional[str]:
        """Format datetime value"""
        try:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                # Try to parse and reformat
                parsed_datetime = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return parsed_datetime.isoformat()
            return None
        except Exception:
            return str(value) if value else None
    
    def _normalize_phone(self, value: Any) -> Optional[str]:
        """Normalize phone number"""
        try:
            if not value:
                return None
            
            # Remove all non-digit characters
            digits = re.sub(r'[^0-9]', '', str(value))
            
            # Basic phone number formatting (customize as needed)
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            else:
                return digits
                
        except Exception:
            return str(value) if value else None
    
    # Built-in validation helper functions
    def _validate_email(self, value: Any) -> bool:
        """Validate email format"""
        try:
            if not value:
                return False
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(email_pattern, str(value)) is not None
        except Exception:
            return False
    
    def _validate_phone(self, value: Any) -> bool:
        """Validate phone number format"""
        try:
            if not value:
                return False
            # Remove all non-digit characters
            digits = re.sub(r'[^0-9]', '', str(value))
            return 10 <= len(digits) <= 15
        except Exception:
            return False
    
    def _validate_numeric(self, value: Any) -> bool:
        """Validate numeric value"""
        try:
            float(str(value))
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_date(self, value: Any) -> bool:
        """Validate date format"""
        try:
            if isinstance(value, (date, datetime)):
                return True
            elif isinstance(value, str):
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return True
            return False
        except Exception:
            return False
    
    def _validate_url(self, value: Any) -> bool:
        """Validate URL format"""
        try:
            if not value:
                return False
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            return re.match(url_pattern, str(value)) is not None
        except Exception:
            return False
    
    def get_transformer_statistics(self) -> Dict[str, Any]:
        """Get transformer statistics"""
        try:
            return {
                'total_profiles': len(self.profiles),
                'transformation_functions': len(self.transformation_functions),
                'validation_functions': len(self.validation_functions),
                'available_functions': {
                    'transformation': list(self.transformation_functions.keys()),
                    'validation': list(self.validation_functions.keys())
                }
            }
        except Exception as e:
            logger.error(f"Statistics generation failed: {e}")
            return {}

# Global data transformer instance
data_transformer = DataTransformer()

async def initialize_data_transformer():
    """Initialize the data transformer"""
    try:
        logger.info("Data transformer initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize data transformer: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_data_transformer()
        
        # Example usage
        test_data = {
            "name": "  John Doe  ",
            "email": "JOHN.DOE@EXAMPLE.COM",
            "phone": "(555) 123-4567",
            "age": "30"
        }
        
        # Transform using normalization profile
        result = await data_transformer.transform_data(test_data, "data_normalization")
        
        print(f"Transformation successful: {result.success}")
        print(f"Original data: {result.original_data}")
        print(f"Transformed data: {result.transformed_data}")
        print(f"Errors: {result.errors}")
        print(f"Warnings: {result.warnings}")
        
        # Get statistics
        stats = data_transformer.get_transformer_statistics()
        print(f"Transformer statistics: {stats}")
    
    asyncio.run(main())