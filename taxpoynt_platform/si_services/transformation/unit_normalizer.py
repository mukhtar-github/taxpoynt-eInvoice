"""
Unit Normalizer Service

This service normalizes units of measure and quantities across different
ERP systems to ensure consistency in FIRS e-invoice submissions.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
import re
import logging

logger = logging.getLogger(__name__)


class UnitCategory(Enum):
    """Categories of units of measure"""
    LENGTH = "length"
    WEIGHT = "weight"
    VOLUME = "volume"
    AREA = "area"
    TIME = "time"
    QUANTITY = "quantity"
    ENERGY = "energy"
    TEMPERATURE = "temperature"
    CURRENCY = "currency"
    PIECE = "piece"


class BaseUnit(Enum):
    """Base units for each category (SI units where applicable)"""
    METER = "m"         # Length
    KILOGRAM = "kg"     # Weight
    LITER = "l"         # Volume
    SQUARE_METER = "m2"  # Area
    SECOND = "s"        # Time
    PIECE = "pcs"       # Quantity
    JOULE = "j"         # Energy
    CELSIUS = "c"       # Temperature
    NAIRA = "ngn"       # Currency


@dataclass
class UnitDefinition:
    """Definition of a unit of measure"""
    code: str
    name: str
    category: UnitCategory
    base_unit: str
    conversion_factor: Decimal
    aliases: List[str]
    is_base_unit: bool = False


@dataclass
class NormalizationResult:
    """Result of unit normalization"""
    original_quantity: Decimal
    original_unit: str
    normalized_quantity: Decimal
    normalized_unit: str
    conversion_factor: Decimal
    category: str
    success: bool
    error_message: Optional[str] = None


class UnitRegistry:
    """Registry of all supported units and their definitions"""
    
    def __init__(self):
        self.units: Dict[str, UnitDefinition] = {}
        self.aliases: Dict[str, str] = {}
        self._initialize_units()
    
    def _initialize_units(self):
        """Initialize the unit registry with standard units"""
        
        # Length units
        self._add_unit(UnitDefinition("m", "Meter", UnitCategory.LENGTH, "m", Decimal("1.0"), 
                                     ["meter", "metre", "meters", "metres"], True))
        self._add_unit(UnitDefinition("cm", "Centimeter", UnitCategory.LENGTH, "m", Decimal("0.01"), 
                                     ["centimeter", "centimetre", "cm", "cms"]))
        self._add_unit(UnitDefinition("mm", "Millimeter", UnitCategory.LENGTH, "m", Decimal("0.001"), 
                                     ["millimeter", "millimetre", "mm", "mms"]))
        self._add_unit(UnitDefinition("km", "Kilometer", UnitCategory.LENGTH, "m", Decimal("1000"), 
                                     ["kilometer", "kilometre", "km", "kms"]))
        self._add_unit(UnitDefinition("in", "Inch", UnitCategory.LENGTH, "m", Decimal("0.0254"), 
                                     ["inch", "inches", "in", "\""]))
        self._add_unit(UnitDefinition("ft", "Foot", UnitCategory.LENGTH, "m", Decimal("0.3048"), 
                                     ["foot", "feet", "ft", "'"]))
        self._add_unit(UnitDefinition("yd", "Yard", UnitCategory.LENGTH, "m", Decimal("0.9144"), 
                                     ["yard", "yards", "yd"]))
        
        # Weight units
        self._add_unit(UnitDefinition("kg", "Kilogram", UnitCategory.WEIGHT, "kg", Decimal("1.0"), 
                                     ["kilogram", "kilograms", "kg", "kgs"], True))
        self._add_unit(UnitDefinition("g", "Gram", UnitCategory.WEIGHT, "kg", Decimal("0.001"), 
                                     ["gram", "grams", "g", "gms"]))
        self._add_unit(UnitDefinition("mg", "Milligram", UnitCategory.WEIGHT, "kg", Decimal("0.000001"), 
                                     ["milligram", "milligrams", "mg", "mgs"]))
        self._add_unit(UnitDefinition("t", "Tonne", UnitCategory.WEIGHT, "kg", Decimal("1000"), 
                                     ["tonne", "tonnes", "ton", "tons", "t"]))
        self._add_unit(UnitDefinition("lb", "Pound", UnitCategory.WEIGHT, "kg", Decimal("0.453592"), 
                                     ["pound", "pounds", "lb", "lbs"]))
        self._add_unit(UnitDefinition("oz", "Ounce", UnitCategory.WEIGHT, "kg", Decimal("0.0283495"), 
                                     ["ounce", "ounces", "oz"]))
        
        # Volume units
        self._add_unit(UnitDefinition("l", "Liter", UnitCategory.VOLUME, "l", Decimal("1.0"), 
                                     ["liter", "litre", "liters", "litres", "l"], True))
        self._add_unit(UnitDefinition("ml", "Milliliter", UnitCategory.VOLUME, "l", Decimal("0.001"), 
                                     ["milliliter", "millilitre", "ml", "mls"]))
        self._add_unit(UnitDefinition("cl", "Centiliter", UnitCategory.VOLUME, "l", Decimal("0.01"), 
                                     ["centiliter", "centilitre", "cl", "cls"]))
        self._add_unit(UnitDefinition("m3", "Cubic Meter", UnitCategory.VOLUME, "l", Decimal("1000"), 
                                     ["cubic meter", "cubic metre", "m3", "m³"]))
        self._add_unit(UnitDefinition("gal", "Gallon", UnitCategory.VOLUME, "l", Decimal("3.78541"), 
                                     ["gallon", "gallons", "gal"]))
        self._add_unit(UnitDefinition("pt", "Pint", UnitCategory.VOLUME, "l", Decimal("0.473176"), 
                                     ["pint", "pints", "pt"]))
        
        # Area units
        self._add_unit(UnitDefinition("m2", "Square Meter", UnitCategory.AREA, "m2", Decimal("1.0"), 
                                     ["square meter", "square metre", "m2", "m²", "sqm"], True))
        self._add_unit(UnitDefinition("cm2", "Square Centimeter", UnitCategory.AREA, "m2", Decimal("0.0001"), 
                                     ["square centimeter", "square centimetre", "cm2", "cm²"]))
        self._add_unit(UnitDefinition("ha", "Hectare", UnitCategory.AREA, "m2", Decimal("10000"), 
                                     ["hectare", "hectares", "ha"]))
        self._add_unit(UnitDefinition("ac", "Acre", UnitCategory.AREA, "m2", Decimal("4046.86"), 
                                     ["acre", "acres", "ac"]))
        
        # Quantity/Piece units
        self._add_unit(UnitDefinition("pcs", "Pieces", UnitCategory.PIECE, "pcs", Decimal("1.0"), 
                                     ["piece", "pieces", "pcs", "pc", "each", "ea", "unit", "units"], True))
        self._add_unit(UnitDefinition("dz", "Dozen", UnitCategory.PIECE, "pcs", Decimal("12"), 
                                     ["dozen", "dozens", "dz"]))
        self._add_unit(UnitDefinition("gr", "Gross", UnitCategory.PIECE, "pcs", Decimal("144"), 
                                     ["gross", "gr"]))
        self._add_unit(UnitDefinition("pr", "Pair", UnitCategory.PIECE, "pcs", Decimal("2"), 
                                     ["pair", "pairs", "pr"]))
        self._add_unit(UnitDefinition("set", "Set", UnitCategory.PIECE, "pcs", Decimal("1"), 
                                     ["set", "sets"]))
        self._add_unit(UnitDefinition("box", "Box", UnitCategory.PIECE, "pcs", Decimal("1"), 
                                     ["box", "boxes", "carton", "cartons"]))
        self._add_unit(UnitDefinition("pack", "Pack", UnitCategory.PIECE, "pcs", Decimal("1"), 
                                     ["pack", "packs", "package", "packages", "pkg"]))
        
        # Time units
        self._add_unit(UnitDefinition("hr", "Hour", UnitCategory.TIME, "s", Decimal("3600"), 
                                     ["hour", "hours", "hr", "hrs"]))
        self._add_unit(UnitDefinition("min", "Minute", UnitCategory.TIME, "s", Decimal("60"), 
                                     ["minute", "minutes", "min", "mins"]))
        self._add_unit(UnitDefinition("s", "Second", UnitCategory.TIME, "s", Decimal("1.0"), 
                                     ["second", "seconds", "s", "sec"], True))
        self._add_unit(UnitDefinition("day", "Day", UnitCategory.TIME, "s", Decimal("86400"), 
                                     ["day", "days"]))
        self._add_unit(UnitDefinition("week", "Week", UnitCategory.TIME, "s", Decimal("604800"), 
                                     ["week", "weeks", "wk"]))
        self._add_unit(UnitDefinition("month", "Month", UnitCategory.TIME, "s", Decimal("2629746"), 
                                     ["month", "months", "mo"]))
        self._add_unit(UnitDefinition("year", "Year", UnitCategory.TIME, "s", Decimal("31556952"), 
                                     ["year", "years", "yr"]))
    
    def _add_unit(self, unit_def: UnitDefinition):
        """Add a unit definition to the registry"""
        self.units[unit_def.code.lower()] = unit_def
        
        # Add aliases
        for alias in unit_def.aliases:
            self.aliases[alias.lower()] = unit_def.code.lower()
    
    def get_unit(self, unit_code: str) -> Optional[UnitDefinition]:
        """Get unit definition by code or alias"""
        unit_code_lower = unit_code.lower().strip()
        
        # Try direct lookup first
        if unit_code_lower in self.units:
            return self.units[unit_code_lower]
        
        # Try alias lookup
        if unit_code_lower in self.aliases:
            canonical_code = self.aliases[unit_code_lower]
            return self.units[canonical_code]
        
        return None
    
    def get_units_by_category(self, category: UnitCategory) -> List[UnitDefinition]:
        """Get all units in a category"""
        return [unit for unit in self.units.values() if unit.category == category]
    
    def register_custom_unit(self, unit_def: UnitDefinition):
        """Register a custom unit"""
        self._add_unit(unit_def)
        logger.info(f"Registered custom unit: {unit_def.code}")


class UnitNormalizer:
    """Main service for unit normalization"""
    
    def __init__(self):
        self.registry = UnitRegistry()
        self.quantity_patterns = [
            r'^(\d+\.?\d*)\s*([a-zA-Z]+\d*[²³]?)$',  # Standard: "5 kg", "10.5 m²"
            r'^(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*([a-zA-Z]+)$',  # Dimensions: "5 x 10 m"
            r'^(\d+\.?\d*)/(\d+\.?\d*)\s*([a-zA-Z]+)$',  # Fractions: "1/2 kg"
        ]
    
    def parse_quantity_and_unit(self, input_string: str) -> Tuple[Optional[Decimal], Optional[str]]:
        """Parse quantity and unit from input string"""
        input_string = input_string.strip()
        
        # Try different patterns
        for pattern in self.quantity_patterns:
            match = re.match(pattern, input_string, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) == 2:  # Standard format
                    quantity_str, unit_str = groups
                    try:
                        quantity = Decimal(quantity_str)
                        return quantity, unit_str.strip()
                    except:
                        continue
                
                elif len(groups) == 3:  # Dimensions or fractions
                    if 'x' in input_string.lower():
                        # Dimensions - multiply
                        try:
                            quantity = Decimal(groups[0]) * Decimal(groups[1])
                            return quantity, groups[2].strip()
                        except:
                            continue
                    else:
                        # Fraction - divide
                        try:
                            quantity = Decimal(groups[0]) / Decimal(groups[1])
                            return quantity, groups[2].strip()
                        except:
                            continue
        
        # If no pattern matches, try to extract numbers and text separately
        numbers = re.findall(r'\d+\.?\d*', input_string)
        text = re.sub(r'\d+\.?\d*', '', input_string).strip()
        
        if numbers and text:
            try:
                quantity = Decimal(numbers[0])
                return quantity, text
            except:
                pass
        
        return None, None
    
    def normalize_unit_code(self, unit_code: str) -> Optional[str]:
        """Normalize unit code to standard form"""
        unit_def = self.registry.get_unit(unit_code)
        return unit_def.code if unit_def else None
    
    def convert_to_base_unit(self, quantity: Decimal, unit_code: str) -> Optional[NormalizationResult]:
        """Convert quantity to base unit for its category"""
        unit_def = self.registry.get_unit(unit_code)
        if not unit_def:
            return NormalizationResult(
                original_quantity=quantity,
                original_unit=unit_code,
                normalized_quantity=quantity,
                normalized_unit=unit_code,
                conversion_factor=Decimal("1.0"),
                category="unknown",
                success=False,
                error_message=f"Unknown unit: {unit_code}"
            )
        
        # Convert to base unit
        normalized_quantity = quantity * unit_def.conversion_factor
        
        # Round to appropriate precision
        normalized_quantity = normalized_quantity.quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )
        
        return NormalizationResult(
            original_quantity=quantity,
            original_unit=unit_code,
            normalized_quantity=normalized_quantity,
            normalized_unit=unit_def.base_unit,
            conversion_factor=unit_def.conversion_factor,
            category=unit_def.category.value,
            success=True
        )
    
    def convert_between_units(self, quantity: Decimal, from_unit: str, to_unit: str) -> Optional[NormalizationResult]:
        """Convert quantity from one unit to another"""
        from_unit_def = self.registry.get_unit(from_unit)
        to_unit_def = self.registry.get_unit(to_unit)
        
        if not from_unit_def or not to_unit_def:
            return NormalizationResult(
                original_quantity=quantity,
                original_unit=from_unit,
                normalized_quantity=quantity,
                normalized_unit=to_unit,
                conversion_factor=Decimal("1.0"),
                category="unknown",
                success=False,
                error_message=f"Unknown unit: {from_unit if not from_unit_def else to_unit}"
            )
        
        # Check if units are compatible (same category)
        if from_unit_def.category != to_unit_def.category:
            return NormalizationResult(
                original_quantity=quantity,
                original_unit=from_unit,
                normalized_quantity=quantity,
                normalized_unit=to_unit,
                conversion_factor=Decimal("1.0"),
                category="incompatible",
                success=False,
                error_message=f"Incompatible units: {from_unit} ({from_unit_def.category.value}) to {to_unit} ({to_unit_def.category.value})"
            )
        
        # Convert from source unit to base unit, then to target unit
        base_quantity = quantity * from_unit_def.conversion_factor
        target_quantity = base_quantity / to_unit_def.conversion_factor
        
        # Calculate overall conversion factor
        conversion_factor = from_unit_def.conversion_factor / to_unit_def.conversion_factor
        
        # Round to appropriate precision
        target_quantity = target_quantity.quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )
        
        return NormalizationResult(
            original_quantity=quantity,
            original_unit=from_unit,
            normalized_quantity=target_quantity,
            normalized_unit=to_unit,
            conversion_factor=conversion_factor,
            category=from_unit_def.category.value,
            success=True
        )
    
    def normalize_line_item(self, line_item: Dict[str, Any], target_units: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Normalize units in a line item"""
        normalized_item = line_item.copy()
        
        # Parse quantity and unit
        quantity_field = line_item.get("quantity", 0)
        unit_field = line_item.get("unit", line_item.get("uom", "pcs"))
        
        if isinstance(quantity_field, str):
            # Try to parse combined quantity and unit string
            parsed_qty, parsed_unit = self.parse_quantity_and_unit(quantity_field)
            if parsed_qty is not None and parsed_unit is not None:
                quantity_field = parsed_qty
                unit_field = parsed_unit
        
        # Convert to Decimal for precise calculations
        try:
            quantity = Decimal(str(quantity_field))
        except:
            quantity = Decimal("0")
        
        # Normalize unit
        normalized_unit = self.normalize_unit_code(unit_field)
        if normalized_unit:
            normalized_item["unit"] = normalized_unit
            normalized_item["uom"] = normalized_unit
        
        # Convert to target unit if specified
        if target_units and "quantity" in target_units:
            target_unit = target_units["quantity"]
            conversion_result = self.convert_between_units(quantity, unit_field, target_unit)
            if conversion_result and conversion_result.success:
                normalized_item["quantity"] = float(conversion_result.normalized_quantity)
                normalized_item["unit"] = target_unit
                normalized_item["uom"] = target_unit
                normalized_item["original_quantity"] = float(quantity)
                normalized_item["original_unit"] = unit_field
                normalized_item["conversion_factor"] = float(conversion_result.conversion_factor)
        
        # Handle weight and volume fields if present
        for field, unit_key in [("weight", "weight_unit"), ("volume", "volume_unit")]:
            if field in line_item and unit_key in line_item:
                try:
                    field_quantity = Decimal(str(line_item[field]))
                    field_unit = line_item[unit_key]
                    
                    # Normalize to base unit
                    result = self.convert_to_base_unit(field_quantity, field_unit)
                    if result and result.success:
                        normalized_item[field] = float(result.normalized_quantity)
                        normalized_item[unit_key] = result.normalized_unit
                        normalized_item[f"original_{field}"] = float(field_quantity)
                        normalized_item[f"original_{unit_key}"] = field_unit
                except:
                    pass
        
        return normalized_item
    
    def normalize_invoice_quantities(self, invoice_data: Dict[str, Any], target_units: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Normalize all quantities and units in an invoice"""
        normalized_invoice = invoice_data.copy()
        
        logger.info("Starting invoice unit normalization")
        
        # Normalize line items
        if "line_items" in invoice_data:
            normalized_items = []
            for item in invoice_data["line_items"]:
                normalized_item = self.normalize_line_item(item, target_units)
                normalized_items.append(normalized_item)
            
            normalized_invoice["line_items"] = normalized_items
        
        # Add normalization metadata
        normalized_invoice["unit_normalization"] = {
            "normalized": True,
            "normalization_date": str(Decimal(str(__import__('time').time()))),
            "target_units": target_units or {}
        }
        
        return normalized_invoice
    
    def get_unit_suggestions(self, partial_unit: str, limit: int = 5) -> List[Dict[str, str]]:
        """Get unit suggestions for partial input"""
        partial_lower = partial_unit.lower()
        suggestions = []
        
        # Search in unit codes and aliases
        for code, unit_def in self.registry.units.items():
            if partial_lower in code or any(partial_lower in alias for alias in unit_def.aliases):
                suggestions.append({
                    "code": unit_def.code,
                    "name": unit_def.name,
                    "category": unit_def.category.value,
                    "aliases": unit_def.aliases[:3]  # First 3 aliases
                })
                
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    def validate_unit_compatibility(self, units: List[str]) -> Dict[str, Any]:
        """Validate if units are compatible for operations"""
        unit_defs = []
        unknown_units = []
        
        for unit in units:
            unit_def = self.registry.get_unit(unit)
            if unit_def:
                unit_defs.append(unit_def)
            else:
                unknown_units.append(unit)
        
        if unknown_units:
            return {
                "compatible": False,
                "error": f"Unknown units: {', '.join(unknown_units)}"
            }
        
        if len(unit_defs) < 2:
            return {"compatible": True, "category": unit_defs[0].category.value if unit_defs else None}
        
        # Check if all units are in the same category
        categories = {unit_def.category for unit_def in unit_defs}
        if len(categories) == 1:
            return {
                "compatible": True,
                "category": list(categories)[0].value,
                "base_unit": unit_defs[0].base_unit
            }
        else:
            return {
                "compatible": False,
                "error": f"Incompatible unit categories: {', '.join(cat.value for cat in categories)}"
            }
    
    def get_supported_units(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of supported units, optionally filtered by category"""
        units = []
        
        for unit_def in self.registry.units.values():
            if category is None or unit_def.category.value == category:
                units.append({
                    "code": unit_def.code,
                    "name": unit_def.name,
                    "category": unit_def.category.value,
                    "base_unit": unit_def.base_unit,
                    "is_base_unit": unit_def.is_base_unit,
                    "aliases": unit_def.aliases
                })
        
        # Sort by category and then by name
        units.sort(key=lambda x: (x["category"], x["name"]))
        return units
    
    def export_unit_definitions(self) -> Dict[str, Any]:
        """Export all unit definitions for backup or sharing"""
        export_data = {
            "units": {},
            "aliases": self.registry.aliases,
            "export_date": str(Decimal(str(__import__('time').time())))
        }
        
        for code, unit_def in self.registry.units.items():
            export_data["units"][code] = {
                "name": unit_def.name,
                "category": unit_def.category.value,
                "base_unit": unit_def.base_unit,
                "conversion_factor": str(unit_def.conversion_factor),
                "aliases": unit_def.aliases,
                "is_base_unit": unit_def.is_base_unit
            }
        
        return export_data