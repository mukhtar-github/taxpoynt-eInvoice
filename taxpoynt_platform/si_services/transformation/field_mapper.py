"""
Field Mapper Service

This service provides dynamic field mapping between different ERP systems
and the standardized FIRS e-invoice format, allowing flexible data transformation.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MappingType(Enum):
    """Types of field mappings"""
    DIRECT = "direct"           # Direct field mapping
    NESTED = "nested"           # Nested object field mapping
    CALCULATED = "calculated"   # Calculated field using function
    CONSTANT = "constant"       # Constant value
    CONDITIONAL = "conditional" # Conditional mapping based on criteria


@dataclass
class FieldMapping:
    """Field mapping configuration"""
    source_field: str
    target_field: str
    mapping_type: MappingType
    default_value: Any = None
    transformation_function: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    nested_path: Optional[List[str]] = None
    required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class MappingProfile:
    """Complete mapping profile for an ERP system"""
    profile_name: str
    erp_system: str
    version: str
    mappings: List[FieldMapping] = field(default_factory=list)
    preprocessing_rules: Optional[Dict[str, Any]] = None
    postprocessing_rules: Optional[Dict[str, Any]] = None


class TransformationFunctions:
    """Collection of transformation functions for field mapping"""
    
    @staticmethod
    def to_upper(value: Any) -> str:
        """Convert value to uppercase"""
        return str(value).upper() if value else ""
    
    @staticmethod
    def to_lower(value: Any) -> str:
        """Convert value to lowercase"""
        return str(value).lower() if value else ""
    
    @staticmethod
    def format_currency(value: Any) -> float:
        """Format currency value"""
        if isinstance(value, str):
            # Remove currency symbols and format
            cleaned = value.replace("₦", "").replace("$", "").replace(",", "").strip()
            return float(cleaned) if cleaned else 0.0
        return float(value) if value else 0.0
    
    @staticmethod
    def format_date(value: Any, from_format: str = "%Y-%m-%d", to_format: str = "%Y-%m-%d") -> str:
        """Format date from one format to another"""
        from datetime import datetime
        if isinstance(value, str):
            try:
                date_obj = datetime.strptime(value, from_format)
                return date_obj.strftime(to_format)
            except ValueError:
                return value
        return str(value) if value else ""
    
    @staticmethod
    def normalize_tin(value: Any) -> str:
        """Normalize TIN format"""
        if not value:
            return ""
        tin = str(value).replace("-", "").replace(" ", "").upper()
        return tin[:10] if len(tin) >= 10 else tin
    
    @staticmethod
    def concatenate_address(address_data: Dict[str, Any]) -> str:
        """Concatenate address fields"""
        if isinstance(address_data, str):
            return address_data
        
        parts = []
        for key in ["street", "city", "state", "country"]:
            if address_data.get(key):
                parts.append(str(address_data[key]))
        return ", ".join(parts)
    
    @staticmethod
    def calculate_tax_rate(tax_amount: float, base_amount: float) -> float:
        """Calculate tax rate percentage"""
        if base_amount and base_amount > 0:
            return (tax_amount / base_amount) * 100
        return 0.0
    
    @staticmethod
    def extract_phone(contact_data: Any) -> str:
        """Extract phone number from contact data"""
        if isinstance(contact_data, dict):
            return contact_data.get("phone", contact_data.get("mobile", ""))
        return str(contact_data) if contact_data else ""


class FieldMapper:
    """Dynamic field mapper for ERP data transformation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.profiles: Dict[str, MappingProfile] = {}
        self.transformation_functions: Dict[str, Callable] = {}
        self._load_transformation_functions()
        
        if config_path:
            self.load_profiles_from_file(config_path)
    
    def _load_transformation_functions(self):
        """Load available transformation functions"""
        tf = TransformationFunctions()
        self.transformation_functions = {
            "to_upper": tf.to_upper,
            "to_lower": tf.to_lower,
            "format_currency": tf.format_currency,
            "format_date": tf.format_date,
            "normalize_tin": tf.normalize_tin,
            "concatenate_address": tf.concatenate_address,
            "calculate_tax_rate": tf.calculate_tax_rate,
            "extract_phone": tf.extract_phone
        }
    
    def register_transformation_function(self, name: str, func: Callable):
        """Register a custom transformation function"""
        self.transformation_functions[name] = func
    
    def add_mapping_profile(self, profile: MappingProfile):
        """Add a mapping profile"""
        self.profiles[f"{profile.erp_system}_{profile.version}"] = profile
        logger.info(f"Added mapping profile: {profile.profile_name}")
    
    def get_profile(self, erp_system: str, version: str = "default") -> Optional[MappingProfile]:
        """Get mapping profile for ERP system"""
        key = f"{erp_system}_{version}"
        return self.profiles.get(key)
    
    def _get_nested_value(self, data: Dict[str, Any], path: List[str]) -> Any:
        """Get value from nested dictionary using path"""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], path: List[str], value: Any):
        """Set value in nested dictionary using path"""
        current = data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _apply_transformation(self, value: Any, function_name: str, **kwargs) -> Any:
        """Apply transformation function to value"""
        if function_name in self.transformation_functions:
            func = self.transformation_functions[function_name]
            try:
                if kwargs:
                    return func(value, **kwargs)
                return func(value)
            except Exception as e:
                logger.error(f"Error applying transformation {function_name}: {str(e)}")
                return value
        return value
    
    def _evaluate_conditions(self, data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """Evaluate mapping conditions"""
        for field, expected_value in conditions.items():
            actual_value = self._get_nested_value(data, field.split('.'))
            if actual_value != expected_value:
                return False
        return True
    
    def _apply_mapping(self, source_data: Dict[str, Any], mapping: FieldMapping) -> Any:
        """Apply a single field mapping"""
        if mapping.mapping_type == MappingType.CONSTANT:
            return mapping.default_value
        
        if mapping.mapping_type == MappingType.CONDITIONAL:
            if mapping.conditions and not self._evaluate_conditions(source_data, mapping.conditions):
                return mapping.default_value
        
        # Get source value
        if mapping.nested_path:
            source_value = self._get_nested_value(source_data, mapping.nested_path)
        else:
            source_value = source_data.get(mapping.source_field)
        
        if source_value is None:
            return mapping.default_value
        
        # Apply transformation if specified
        if mapping.transformation_function:
            source_value = self._apply_transformation(source_value, mapping.transformation_function)
        
        return source_value
    
    def map_fields(self, source_data: Dict[str, Any], erp_system: str, version: str = "default") -> Dict[str, Any]:
        """Map fields from source ERP data to standard format"""
        profile = self.get_profile(erp_system, version)
        if not profile:
            raise ValueError(f"No mapping profile found for {erp_system} version {version}")
        
        logger.info(f"Mapping fields using profile: {profile.profile_name}")
        
        # Apply preprocessing rules if specified
        if profile.preprocessing_rules:
            source_data = self._apply_preprocessing(source_data, profile.preprocessing_rules)
        
        mapped_data = {}
        
        # Apply field mappings
        for mapping in profile.mappings:
            try:
                mapped_value = self._apply_mapping(source_data, mapping)
                
                # Set value in target structure
                if '.' in mapping.target_field:
                    target_path = mapping.target_field.split('.')
                    self._set_nested_value(mapped_data, target_path, mapped_value)
                else:
                    mapped_data[mapping.target_field] = mapped_value
                
                # Validate if required
                if mapping.required and mapped_value is None:
                    logger.warning(f"Required field {mapping.target_field} is None")
                    
            except Exception as e:
                logger.error(f"Error mapping field {mapping.source_field}: {str(e)}")
                if mapping.required:
                    raise
        
        # Apply postprocessing rules if specified
        if profile.postprocessing_rules:
            mapped_data = self._apply_postprocessing(mapped_data, profile.postprocessing_rules)
        
        return mapped_data
    
    def _apply_preprocessing(self, data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Apply preprocessing rules to source data"""
        # Implementation for preprocessing rules
        return data
    
    def _apply_postprocessing(self, data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Apply postprocessing rules to mapped data"""
        # Implementation for postprocessing rules
        return data
    
    def create_odoo_profile(self) -> MappingProfile:
        """Create default Odoo mapping profile"""
        mappings = [
            FieldMapping("name", "invoice_number", MappingType.DIRECT, required=True),
            FieldMapping("date_invoice", "invoice_date", MappingType.DIRECT, required=True),
            FieldMapping("partner_id.vat", "customer_tin", MappingType.NESTED, 
                        nested_path=["partner_id", "vat"], transformation_function="normalize_tin"),
            FieldMapping("partner_id.name", "customer_name", MappingType.NESTED,
                        nested_path=["partner_id", "name"], required=True),
            FieldMapping("company_id.vat", "supplier_tin", MappingType.NESTED,
                        nested_path=["company_id", "vat"], transformation_function="normalize_tin"),
            FieldMapping("company_id.name", "supplier_name", MappingType.NESTED,
                        nested_path=["company_id", "name"], required=True),
            FieldMapping("amount_total", "total_amount", MappingType.DIRECT,
                        transformation_function="format_currency"),
            FieldMapping("amount_tax", "tax_amount", MappingType.DIRECT,
                        transformation_function="format_currency"),
            FieldMapping("currency_id.name", "currency_code", MappingType.NESTED,
                        nested_path=["currency_id", "name"], default_value="NGN")
        ]
        
        return MappingProfile(
            profile_name="Odoo Default",
            erp_system="odoo",
            version="default",
            mappings=mappings
        )
    
    def create_sap_profile(self) -> MappingProfile:
        """Create default SAP mapping profile"""
        mappings = [
            FieldMapping("VBELN", "invoice_number", MappingType.DIRECT, required=True),
            FieldMapping("FKDAT", "invoice_date", MappingType.DIRECT, required=True),
            FieldMapping("KUNAG_VAT", "customer_tin", MappingType.DIRECT,
                        transformation_function="normalize_tin"),
            FieldMapping("KUNAG_NAME", "customer_name", MappingType.DIRECT, required=True),
            FieldMapping("BUKRS_VAT", "supplier_tin", MappingType.DIRECT,
                        transformation_function="normalize_tin"),
            FieldMapping("BUKRS_NAME", "supplier_name", MappingType.DIRECT, required=True),
            FieldMapping("NETWR", "total_amount", MappingType.DIRECT,
                        transformation_function="format_currency"),
            FieldMapping("MWSBP", "tax_amount", MappingType.DIRECT,
                        transformation_function="format_currency"),
            FieldMapping("WAERK", "currency_code", MappingType.DIRECT, default_value="NGN")
        ]
        
        return MappingProfile(
            profile_name="SAP Default",
            erp_system="sap",
            version="default",
            mappings=mappings
        )
    
    def load_default_profiles(self):
        """Load default mapping profiles"""
        self.add_mapping_profile(self.create_odoo_profile())
        self.add_mapping_profile(self.create_sap_profile())
    
    def save_profiles_to_file(self, file_path: str):
        """Save mapping profiles to JSON file"""
        profiles_data = {}
        for key, profile in self.profiles.items():
            profiles_data[key] = {
                "profile_name": profile.profile_name,
                "erp_system": profile.erp_system,
                "version": profile.version,
                "mappings": [
                    {
                        "source_field": m.source_field,
                        "target_field": m.target_field,
                        "mapping_type": m.mapping_type.value,
                        "default_value": m.default_value,
                        "transformation_function": m.transformation_function,
                        "conditions": m.conditions,
                        "nested_path": m.nested_path,
                        "required": m.required,
                        "validation_rules": m.validation_rules
                    }
                    for m in profile.mappings
                ],
                "preprocessing_rules": profile.preprocessing_rules,
                "postprocessing_rules": profile.postprocessing_rules
            }
        
        with open(file_path, 'w') as f:
            json.dump(profiles_data, f, indent=2)
        
        logger.info(f"Saved {len(profiles_data)} profiles to {file_path}")
    
    def load_profiles_from_file(self, file_path: str):
        """Load mapping profiles from JSON file"""
        try:
            with open(file_path, 'r') as f:
                profiles_data = json.load(f)
            
            for key, profile_data in profiles_data.items():
                mappings = []
                for mapping_data in profile_data.get("mappings", []):
                    mapping = FieldMapping(
                        source_field=mapping_data["source_field"],
                        target_field=mapping_data["target_field"],
                        mapping_type=MappingType(mapping_data["mapping_type"]),
                        default_value=mapping_data.get("default_value"),
                        transformation_function=mapping_data.get("transformation_function"),
                        conditions=mapping_data.get("conditions"),
                        nested_path=mapping_data.get("nested_path"),
                        required=mapping_data.get("required", False),
                        validation_rules=mapping_data.get("validation_rules")
                    )
                    mappings.append(mapping)
                
                profile = MappingProfile(
                    profile_name=profile_data["profile_name"],
                    erp_system=profile_data["erp_system"],
                    version=profile_data["version"],
                    mappings=mappings,
                    preprocessing_rules=profile_data.get("preprocessing_rules"),
                    postprocessing_rules=profile_data.get("postprocessing_rules")
                )
                
                self.profiles[key] = profile
            
            logger.info(f"Loaded {len(profiles_data)} profiles from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading profiles from {file_path}: {str(e)}")
            raise
    
    def get_available_profiles(self) -> List[Dict[str, str]]:
        """Get list of available mapping profiles"""
        return [
            {
                "key": key,
                "name": profile.profile_name,
                "erp_system": profile.erp_system,
                "version": profile.version
            }
            for key, profile in self.profiles.items()
        ]