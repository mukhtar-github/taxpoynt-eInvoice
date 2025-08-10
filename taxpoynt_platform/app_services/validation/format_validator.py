"""
Document Format Validation Service for APP Role

This service handles document format validation including:
- JSON schema validation
- XML structure validation
- Data type validation
- Field format validation
- Document structure validation
"""

import json
import xml.etree.ElementTree as ET
import jsonschema
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from decimal import Decimal, InvalidOperation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FormatType(Enum):
    """Document format types"""
    JSON = "json"
    XML = "xml"
    MIXED = "mixed"


class FieldType(Enum):
    """Field data types"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    CURRENCY = "currency"


class FormatSeverity(Enum):
    """Format validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class FormatValidationResult:
    """Individual format validation result"""
    field_path: str
    field_type: FieldType
    severity: FormatSeverity
    message: str
    expected_format: Optional[str] = None
    actual_value: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormatValidationReport:
    """Document format validation report"""
    document_id: str
    format_type: FormatType
    validation_timestamp: datetime
    is_valid: bool
    schema_version: str
    total_fields: int
    valid_fields: int
    invalid_fields: int
    results: List[FormatValidationResult] = field(default_factory=list)
    errors: List[FormatValidationResult] = field(default_factory=list)
    warnings: List[FormatValidationResult] = field(default_factory=list)
    info: List[FormatValidationResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FormatValidator:
    """
    Document format validation service for APP role
    
    Handles:
    - JSON schema validation
    - XML structure validation  
    - Data type validation
    - Field format validation
    - Document structure validation
    """
    
    def __init__(self, schema_version: str = "1.0"):
        self.schema_version = schema_version
        
        # Load document schemas
        self.schemas = self._load_schemas()
        
        # Format patterns
        self.format_patterns = {
            FieldType.EMAIL: r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            FieldType.PHONE: r'^\+?[\d\s\-\(\)]+$',
            FieldType.URL: r'^https?://[^\s/$.?#].[^\s]*$',
            FieldType.DATE: r'^\d{4}-\d{2}-\d{2}$',
            FieldType.DATETIME: r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$',
            FieldType.CURRENCY: r'^\d+(\.\d{1,2})?$'
        }
        
        # Field validators
        self.field_validators = {
            FieldType.STRING: self._validate_string,
            FieldType.NUMBER: self._validate_number,
            FieldType.INTEGER: self._validate_integer,
            FieldType.BOOLEAN: self._validate_boolean,
            FieldType.ARRAY: self._validate_array,
            FieldType.OBJECT: self._validate_object,
            FieldType.DATE: self._validate_date,
            FieldType.DATETIME: self._validate_datetime,
            FieldType.EMAIL: self._validate_email,
            FieldType.PHONE: self._validate_phone,
            FieldType.URL: self._validate_url,
            FieldType.CURRENCY: self._validate_currency
        }
        
        # Metrics
        self.metrics = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'validation_time': 0.0,
            'format_errors': {},
            'field_errors': {}
        }
    
    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load document schemas"""
        return {
            'invoice': {
                'type': 'object',
                'required': ['document_id', 'document_type', 'invoice_number', 'invoice_date', 'supplier', 'customer', 'items', 'subtotal', 'total_amount', 'currency'],
                'properties': {
                    'document_id': {'type': 'string', 'format': 'uuid'},
                    'document_type': {'type': 'string', 'enum': ['invoice']},
                    'invoice_number': {'type': 'string', 'minLength': 1, 'maxLength': 50},
                    'invoice_series': {'type': 'string', 'maxLength': 10},
                    'invoice_date': {'type': 'string', 'format': 'date'},
                    'due_date': {'type': 'string', 'format': 'date'},
                    'currency': {'type': 'string', 'enum': ['NGN']},
                    'subtotal': {'type': 'number', 'minimum': 0},
                    'tax_amount': {'type': 'number', 'minimum': 0},
                    'total_amount': {'type': 'number', 'minimum': 0},
                    'supplier': {
                        'type': 'object',
                        'required': ['name', 'tin', 'address'],
                        'properties': {
                            'name': {'type': 'string', 'minLength': 1, 'maxLength': 200},
                            'tin': {'type': 'string', 'pattern': r'^\d{8}-\d{4}$'},
                            'vat_number': {'type': 'string', 'pattern': r'^\d{8}-\d{4}$'},
                            'phone': {'type': 'string', 'format': 'phone'},
                            'email': {'type': 'string', 'format': 'email'},
                            'address': {
                                'type': 'object',
                                'required': ['street', 'city', 'state', 'country'],
                                'properties': {
                                    'street': {'type': 'string', 'minLength': 1, 'maxLength': 200},
                                    'city': {'type': 'string', 'minLength': 1, 'maxLength': 100},
                                    'state': {'type': 'string', 'minLength': 2, 'maxLength': 2},
                                    'country': {'type': 'string', 'enum': ['NG']},
                                    'postal_code': {'type': 'string', 'pattern': r'^\d{6}$'}
                                }
                            }
                        }
                    },
                    'customer': {
                        'type': 'object',
                        'required': ['name', 'address'],
                        'properties': {
                            'name': {'type': 'string', 'minLength': 1, 'maxLength': 200},
                            'tin': {'type': 'string', 'pattern': r'^\d{8}-\d{4}$'},
                            'vat_number': {'type': 'string', 'pattern': r'^\d{8}-\d{4}$'},
                            'phone': {'type': 'string', 'format': 'phone'},
                            'email': {'type': 'string', 'format': 'email'},
                            'address': {
                                'type': 'object',
                                'required': ['street', 'city', 'state', 'country'],
                                'properties': {
                                    'street': {'type': 'string', 'minLength': 1, 'maxLength': 200},
                                    'city': {'type': 'string', 'minLength': 1, 'maxLength': 100},
                                    'state': {'type': 'string', 'minLength': 2, 'maxLength': 2},
                                    'country': {'type': 'string', 'enum': ['NG']},
                                    'postal_code': {'type': 'string', 'pattern': r'^\d{6}$'}
                                }
                            }
                        }
                    },
                    'items': {
                        'type': 'array',
                        'minItems': 1,
                        'items': {
                            'type': 'object',
                            'required': ['description', 'quantity', 'unit_price', 'total_price'],
                            'properties': {
                                'description': {'type': 'string', 'minLength': 1, 'maxLength': 500},
                                'quantity': {'type': 'number', 'minimum': 0},
                                'unit_price': {'type': 'number', 'minimum': 0},
                                'total_price': {'type': 'number', 'minimum': 0},
                                'unit': {'type': 'string', 'maxLength': 50},
                                'tax_rate': {'type': 'number', 'minimum': 0, 'maximum': 1},
                                'tax_amount': {'type': 'number', 'minimum': 0}
                            }
                        }
                    },
                    'vat': {
                        'type': 'object',
                        'properties': {
                            'rate': {'type': 'number', 'enum': [0.0, 0.075]},
                            'amount': {'type': 'number', 'minimum': 0}
                        }
                    },
                    'wht': {
                        'type': 'object',
                        'properties': {
                            'rate': {'type': 'number', 'minimum': 0, 'maximum': 1},
                            'amount': {'type': 'number', 'minimum': 0},
                            'type': {'type': 'string', 'enum': ['dividend', 'interest', 'rent', 'royalty', 'technical_service', 'professional_service', 'construction', 'consultancy', 'transport', 'commission']}
                        }
                    },
                    'payment_terms': {'type': 'string', 'maxLength': 200},
                    'notes': {'type': 'string', 'maxLength': 1000}
                }
            },
            'credit_note': {
                'type': 'object',
                'required': ['document_id', 'document_type', 'credit_note_number', 'credit_note_date', 'original_invoice_number', 'supplier', 'customer', 'items', 'subtotal', 'total_amount', 'currency'],
                'properties': {
                    'document_id': {'type': 'string', 'format': 'uuid'},
                    'document_type': {'type': 'string', 'enum': ['credit_note']},
                    'credit_note_number': {'type': 'string', 'minLength': 1, 'maxLength': 50},
                    'credit_note_date': {'type': 'string', 'format': 'date'},
                    'original_invoice_number': {'type': 'string', 'minLength': 1, 'maxLength': 50},
                    'reason': {'type': 'string', 'minLength': 1, 'maxLength': 500},
                    'currency': {'type': 'string', 'enum': ['NGN']},
                    'subtotal': {'type': 'number', 'minimum': 0},
                    'tax_amount': {'type': 'number', 'minimum': 0},
                    'total_amount': {'type': 'number', 'minimum': 0}
                }
            },
            'debit_note': {
                'type': 'object',
                'required': ['document_id', 'document_type', 'debit_note_number', 'debit_note_date', 'original_invoice_number', 'supplier', 'customer', 'items', 'subtotal', 'total_amount', 'currency'],
                'properties': {
                    'document_id': {'type': 'string', 'format': 'uuid'},
                    'document_type': {'type': 'string', 'enum': ['debit_note']},
                    'debit_note_number': {'type': 'string', 'minLength': 1, 'maxLength': 50},
                    'debit_note_date': {'type': 'string', 'format': 'date'},
                    'original_invoice_number': {'type': 'string', 'minLength': 1, 'maxLength': 50},
                    'reason': {'type': 'string', 'minLength': 1, 'maxLength': 500},
                    'currency': {'type': 'string', 'enum': ['NGN']},
                    'subtotal': {'type': 'number', 'minimum': 0},
                    'tax_amount': {'type': 'number', 'minimum': 0},
                    'total_amount': {'type': 'number', 'minimum': 0}
                }
            }
        }
    
    async def validate_document_format(self, document: Dict[str, Any]) -> FormatValidationReport:
        """
        Validate document format against schema
        
        Args:
            document: Document data to validate
            
        Returns:
            FormatValidationReport with validation results
        """
        import time
        start_time = time.time()
        
        # Initialize report
        report = FormatValidationReport(
            document_id=document.get('document_id', 'unknown'),
            format_type=FormatType.JSON,
            validation_timestamp=datetime.utcnow(),
            is_valid=True,
            schema_version=self.schema_version,
            total_fields=0,
            valid_fields=0,
            invalid_fields=0
        )
        
        try:
            # Determine document type
            document_type = document.get('document_type', 'invoice')
            
            # Get appropriate schema
            schema = self.schemas.get(document_type)
            if not schema:
                report.results.append(FormatValidationResult(
                    field_path='document_type',
                    field_type=FieldType.STRING,
                    severity=FormatSeverity.ERROR,
                    message=f'Unknown document type: {document_type}',
                    expected_format='invoice, credit_note, debit_note',
                    actual_value=str(document_type)
                ))
                report.is_valid = False
                return report
            
            # Validate against JSON schema
            await self._validate_json_schema(document, schema, report)
            
            # Validate field formats
            await self._validate_field_formats(document, report)
            
            # Validate document structure
            await self._validate_document_structure(document, report)
            
            # Validate business rules
            await self._validate_business_rules(document, report)
            
            # Categorize results
            self._categorize_results(report)
            
            # Calculate totals
            report.total_fields = len(report.results)
            report.valid_fields = len([r for r in report.results if r.severity in [FormatSeverity.INFO]])
            report.invalid_fields = len([r for r in report.results if r.severity in [FormatSeverity.ERROR, FormatSeverity.CRITICAL]])
            
            # Determine overall validity
            report.is_valid = len(report.errors) == 0
            
            # Update metrics
            self.metrics['total_validations'] += 1
            if report.is_valid:
                self.metrics['successful_validations'] += 1
            else:
                self.metrics['failed_validations'] += 1
            
            self.metrics['validation_time'] += time.time() - start_time
            
            logger.info(f"Format validation completed for {report.document_id}: "
                       f"{'VALID' if report.is_valid else 'INVALID'} "
                       f"({report.valid_fields}/{report.total_fields} fields valid)")
            
        except Exception as e:
            report.is_valid = False
            report.results.append(FormatValidationResult(
                field_path='system',
                field_type=FieldType.OBJECT,
                severity=FormatSeverity.CRITICAL,
                message=f'Format validation system error: {str(e)}'
            ))
            
            logger.error(f"Format validation error for {report.document_id}: {e}")
        
        return report
    
    async def _validate_json_schema(self, document: Dict[str, Any], schema: Dict[str, Any], report: FormatValidationReport):
        """Validate document against JSON schema"""
        try:
            # Create custom format checker
            format_checker = jsonschema.FormatChecker()
            
            # Add custom format validators
            @format_checker.checks('phone')
            def check_phone(instance):
                return re.match(self.format_patterns[FieldType.PHONE], instance) is not None
            
            @format_checker.checks('uuid')
            def check_uuid(instance):
                import uuid
                try:
                    uuid.UUID(instance)
                    return True
                except ValueError:
                    return False
            
            # Validate schema
            validator = jsonschema.Draft7Validator(schema, format_checker=format_checker)
            errors = list(validator.iter_errors(document))
            
            for error in errors:
                field_path = '.'.join(str(p) for p in error.absolute_path) if error.absolute_path else 'root'
                
                # Determine field type
                field_type = FieldType.STRING
                if 'type' in error.schema:
                    type_mapping = {
                        'string': FieldType.STRING,
                        'number': FieldType.NUMBER,
                        'integer': FieldType.INTEGER,
                        'boolean': FieldType.BOOLEAN,
                        'array': FieldType.ARRAY,
                        'object': FieldType.OBJECT
                    }
                    field_type = type_mapping.get(error.schema['type'], FieldType.STRING)
                
                # Create validation result
                result = FormatValidationResult(
                    field_path=field_path,
                    field_type=field_type,
                    severity=FormatSeverity.ERROR,
                    message=error.message,
                    expected_format=str(error.schema) if error.schema else None,
                    actual_value=str(error.instance) if error.instance else None
                )
                
                # Add suggestion based on error type
                if error.validator == 'required':
                    result.suggestion = f'Add required field: {field_path}'
                elif error.validator == 'type':
                    result.suggestion = f'Convert {field_path} to {error.schema["type"]}'
                elif error.validator == 'pattern':
                    result.suggestion = f'Fix {field_path} format to match pattern: {error.schema["pattern"]}'
                elif error.validator == 'minLength':
                    result.suggestion = f'Increase {field_path} length to at least {error.schema["minLength"]}'
                elif error.validator == 'maxLength':
                    result.suggestion = f'Reduce {field_path} length to at most {error.schema["maxLength"]}'
                elif error.validator == 'minimum':
                    result.suggestion = f'Increase {field_path} value to at least {error.schema["minimum"]}'
                elif error.validator == 'maximum':
                    result.suggestion = f'Reduce {field_path} value to at most {error.schema["maximum"]}'
                elif error.validator == 'enum':
                    result.suggestion = f'Use one of: {", ".join(map(str, error.schema["enum"]))}'
                
                report.results.append(result)
                
        except jsonschema.SchemaError as e:
            report.results.append(FormatValidationResult(
                field_path='schema',
                field_type=FieldType.OBJECT,
                severity=FormatSeverity.CRITICAL,
                message=f'Invalid schema: {str(e)}'
            ))
        except Exception as e:
            report.results.append(FormatValidationResult(
                field_path='validation',
                field_type=FieldType.OBJECT,
                severity=FormatSeverity.CRITICAL,
                message=f'Schema validation error: {str(e)}'
            ))
    
    async def _validate_field_formats(self, document: Dict[str, Any], report: FormatValidationReport):
        """Validate individual field formats"""
        await self._validate_fields_recursive(document, '', report)
    
    async def _validate_fields_recursive(self, obj: Any, path: str, report: FormatValidationReport):
        """Recursively validate field formats"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{path}.{key}" if path else key
                await self._validate_fields_recursive(value, field_path, report)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                field_path = f"{path}[{i}]"
                await self._validate_fields_recursive(item, field_path, report)
        else:
            # Validate leaf value
            await self._validate_field_value(obj, path, report)
    
    async def _validate_field_value(self, value: Any, field_path: str, report: FormatValidationReport):
        """Validate individual field value"""
        # Determine field type based on path and value
        field_type = self._determine_field_type(field_path, value)
        
        # Get appropriate validator
        validator = self.field_validators.get(field_type)
        if validator:
            try:
                is_valid, message, suggestion = await validator(value, field_path)
                
                if not is_valid:
                    report.results.append(FormatValidationResult(
                        field_path=field_path,
                        field_type=field_type,
                        severity=FormatSeverity.ERROR,
                        message=message,
                        actual_value=str(value),
                        suggestion=suggestion
                    ))
                
            except Exception as e:
                report.results.append(FormatValidationResult(
                    field_path=field_path,
                    field_type=field_type,
                    severity=FormatSeverity.ERROR,
                    message=f'Field validation error: {str(e)}',
                    actual_value=str(value)
                ))
    
    def _determine_field_type(self, field_path: str, value: Any) -> FieldType:
        """Determine field type based on path and value"""
        # Special field type detection based on path
        if 'email' in field_path.lower():
            return FieldType.EMAIL
        elif 'phone' in field_path.lower():
            return FieldType.PHONE
        elif 'url' in field_path.lower() or 'website' in field_path.lower():
            return FieldType.URL
        elif 'date' in field_path.lower():
            if 'T' in str(value) or 'Z' in str(value):
                return FieldType.DATETIME
            return FieldType.DATE
        elif any(x in field_path.lower() for x in ['amount', 'price', 'total', 'subtotal']):
            return FieldType.CURRENCY
        
        # Type detection based on value
        if isinstance(value, str):
            return FieldType.STRING
        elif isinstance(value, bool):
            return FieldType.BOOLEAN
        elif isinstance(value, int):
            return FieldType.INTEGER
        elif isinstance(value, float):
            return FieldType.NUMBER
        elif isinstance(value, list):
            return FieldType.ARRAY
        elif isinstance(value, dict):
            return FieldType.OBJECT
        
        return FieldType.STRING
    
    # Field validators
    async def _validate_string(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate string field"""
        if not isinstance(value, str):
            return False, f'Expected string, got {type(value).__name__}', 'Convert to string'
        
        # Check for empty strings in required fields
        if not value.strip():
            return False, 'String cannot be empty', 'Provide a non-empty value'
        
        # Check for problematic characters
        if any(ord(char) > 127 for char in value):
            return False, 'String contains non-ASCII characters', 'Use ASCII characters only'
        
        return True, 'Valid string', None
    
    async def _validate_number(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate number field"""
        if not isinstance(value, (int, float)):
            try:
                float(value)
            except (ValueError, TypeError):
                return False, f'Expected number, got {type(value).__name__}', 'Convert to number'
        
        # Check for special values
        if isinstance(value, float) and (value != value):  # NaN check
            return False, 'Number cannot be NaN', 'Provide a valid number'
        
        if isinstance(value, float) and value in [float('inf'), float('-inf')]:
            return False, 'Number cannot be infinite', 'Provide a finite number'
        
        return True, 'Valid number', None
    
    async def _validate_integer(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate integer field"""
        if not isinstance(value, int):
            try:
                int(value)
            except (ValueError, TypeError):
                return False, f'Expected integer, got {type(value).__name__}', 'Convert to integer'
        
        return True, 'Valid integer', None
    
    async def _validate_boolean(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate boolean field"""
        if not isinstance(value, bool):
            return False, f'Expected boolean, got {type(value).__name__}', 'Convert to boolean (true/false)'
        
        return True, 'Valid boolean', None
    
    async def _validate_array(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate array field"""
        if not isinstance(value, list):
            return False, f'Expected array, got {type(value).__name__}', 'Convert to array'
        
        return True, 'Valid array', None
    
    async def _validate_object(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate object field"""
        if not isinstance(value, dict):
            return False, f'Expected object, got {type(value).__name__}', 'Convert to object'
        
        return True, 'Valid object', None
    
    async def _validate_date(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate date field"""
        if not isinstance(value, str):
            return False, f'Expected date string, got {type(value).__name__}', 'Convert to date string'
        
        # Check date format
        if not re.match(self.format_patterns[FieldType.DATE], value):
            return False, 'Invalid date format', 'Use YYYY-MM-DD format'
        
        # Validate date
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return False, 'Invalid date value', 'Provide a valid date'
        
        return True, 'Valid date', None
    
    async def _validate_datetime(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate datetime field"""
        if not isinstance(value, str):
            return False, f'Expected datetime string, got {type(value).__name__}', 'Convert to datetime string'
        
        # Check datetime format
        if not re.match(self.format_patterns[FieldType.DATETIME], value):
            return False, 'Invalid datetime format', 'Use ISO 8601 format'
        
        # Validate datetime
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return False, 'Invalid datetime value', 'Provide a valid datetime'
        
        return True, 'Valid datetime', None
    
    async def _validate_email(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate email field"""
        if not isinstance(value, str):
            return False, f'Expected email string, got {type(value).__name__}', 'Convert to email string'
        
        if not re.match(self.format_patterns[FieldType.EMAIL], value):
            return False, 'Invalid email format', 'Use valid email format (user@domain.com)'
        
        return True, 'Valid email', None
    
    async def _validate_phone(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate phone field"""
        if not isinstance(value, str):
            return False, f'Expected phone string, got {type(value).__name__}', 'Convert to phone string'
        
        if not re.match(self.format_patterns[FieldType.PHONE], value):
            return False, 'Invalid phone format', 'Use valid phone format'
        
        return True, 'Valid phone', None
    
    async def _validate_url(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate URL field"""
        if not isinstance(value, str):
            return False, f'Expected URL string, got {type(value).__name__}', 'Convert to URL string'
        
        if not re.match(self.format_patterns[FieldType.URL], value):
            return False, 'Invalid URL format', 'Use valid URL format (https://...)'
        
        return True, 'Valid URL', None
    
    async def _validate_currency(self, value: Any, field_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate currency field"""
        if not isinstance(value, (int, float, str)):
            return False, f'Expected currency value, got {type(value).__name__}', 'Convert to number'
        
        try:
            decimal_value = Decimal(str(value))
            if decimal_value < 0:
                return False, 'Currency value cannot be negative', 'Use positive value'
        except (InvalidOperation, ValueError):
            return False, 'Invalid currency format', 'Use decimal number format'
        
        return True, 'Valid currency', None
    
    async def _validate_document_structure(self, document: Dict[str, Any], report: FormatValidationReport):
        """Validate document structure"""
        # Check for circular references
        try:
            json.dumps(document)
        except ValueError as e:
            if 'circular reference' in str(e).lower():
                report.results.append(FormatValidationResult(
                    field_path='document',
                    field_type=FieldType.OBJECT,
                    severity=FormatSeverity.ERROR,
                    message='Document contains circular references',
                    suggestion='Remove circular references'
                ))
        
        # Check document depth
        max_depth = 10
        current_depth = self._calculate_object_depth(document)
        if current_depth > max_depth:
            report.results.append(FormatValidationResult(
                field_path='document',
                field_type=FieldType.OBJECT,
                severity=FormatSeverity.WARNING,
                message=f'Document structure too deep: {current_depth} levels',
                suggestion=f'Reduce nesting to under {max_depth} levels'
            ))
    
    def _calculate_object_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum depth of nested object"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_object_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._calculate_object_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    async def _validate_business_rules(self, document: Dict[str, Any], report: FormatValidationReport):
        """Validate business-specific format rules"""
        # Check invoice number format
        if 'invoice_number' in document:
            invoice_number = document['invoice_number']
            if isinstance(invoice_number, str):
                # Check for valid characters
                if not re.match(r'^[A-Za-z0-9\-_/]+$', invoice_number):
                    report.results.append(FormatValidationResult(
                        field_path='invoice_number',
                        field_type=FieldType.STRING,
                        severity=FormatSeverity.WARNING,
                        message='Invoice number contains special characters',
                        suggestion='Use only alphanumeric characters, hyphens, underscores, and slashes'
                    ))
        
        # Check currency consistency
        currency = document.get('currency', 'NGN')
        if currency != 'NGN':
            report.results.append(FormatValidationResult(
                field_path='currency',
                field_type=FieldType.STRING,
                severity=FormatSeverity.ERROR,
                message=f'Invalid currency: {currency}',
                expected_format='NGN',
                actual_value=currency,
                suggestion='Use NGN (Nigerian Naira)'
            ))
        
        # Check amount precision
        amount_fields = ['subtotal', 'tax_amount', 'total_amount']
        for field in amount_fields:
            if field in document:
                amount = document[field]
                if isinstance(amount, (int, float)):
                    # Check decimal places
                    amount_str = str(amount)
                    if '.' in amount_str:
                        decimal_places = len(amount_str.split('.')[1])
                        if decimal_places > 2:
                            report.results.append(FormatValidationResult(
                                field_path=field,
                                field_type=FieldType.CURRENCY,
                                severity=FormatSeverity.WARNING,
                                message=f'Amount has too many decimal places: {decimal_places}',
                                suggestion='Round to 2 decimal places'
                            ))
    
    def _categorize_results(self, report: FormatValidationReport):
        """Categorize validation results by severity"""
        for result in report.results:
            if result.severity == FormatSeverity.ERROR:
                report.errors.append(result)
            elif result.severity == FormatSeverity.WARNING:
                report.warnings.append(result)
            elif result.severity == FormatSeverity.INFO:
                report.info.append(result)
            else:  # CRITICAL
                report.errors.append(result)
    
    def validate_xml_format(self, xml_string: str) -> FormatValidationReport:
        """Validate XML format"""
        report = FormatValidationReport(
            document_id='xml_document',
            format_type=FormatType.XML,
            validation_timestamp=datetime.utcnow(),
            is_valid=True,
            schema_version=self.schema_version,
            total_fields=0,
            valid_fields=0,
            invalid_fields=0
        )
        
        try:
            # Parse XML
            root = ET.fromstring(xml_string)
            
            # Basic XML validation
            if root.tag:
                report.results.append(FormatValidationResult(
                    field_path='root',
                    field_type=FieldType.OBJECT,
                    severity=FormatSeverity.INFO,
                    message='XML is well-formed'
                ))
            
        except ET.ParseError as e:
            report.is_valid = False
            report.results.append(FormatValidationResult(
                field_path='xml',
                field_type=FieldType.STRING,
                severity=FormatSeverity.ERROR,
                message=f'XML parse error: {str(e)}',
                suggestion='Fix XML syntax errors'
            ))
        
        return report
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported document formats"""
        return list(self.schemas.keys())
    
    def get_schema(self, document_type: str) -> Optional[Dict[str, Any]]:
        """Get schema for document type"""
        return self.schemas.get(document_type)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get validation metrics"""
        return {
            **self.metrics,
            'success_rate': (
                self.metrics['successful_validations'] / 
                max(self.metrics['total_validations'], 1)
            ) * 100,
            'average_validation_time': (
                self.metrics['validation_time'] / 
                max(self.metrics['total_validations'], 1)
            )
        }


# Factory functions for easy setup
def create_format_validator(schema_version: str = "1.0") -> FormatValidator:
    """Create format validator instance"""
    return FormatValidator(schema_version)


async def validate_document_format(document: Dict[str, Any], schema_version: str = "1.0") -> FormatValidationReport:
    """Validate document format"""
    validator = create_format_validator(schema_version)
    return await validator.validate_document_format(document)


def validate_xml_document(xml_string: str) -> FormatValidationReport:
    """Validate XML document format"""
    validator = create_format_validator()
    return validator.validate_xml_format(xml_string)