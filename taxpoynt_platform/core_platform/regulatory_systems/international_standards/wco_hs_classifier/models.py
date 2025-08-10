"""
WCO HS Code Data Models
======================
Pydantic models for Harmonized System classification and validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class HSClassificationError(Exception):
    """Raised when HS code classification fails."""
    pass


class HSConfidenceLevel(str, Enum):
    """Classification confidence levels."""
    HIGH = "high"        # 90%+ confidence
    MEDIUM = "medium"    # 70-89% confidence  
    LOW = "low"         # 50-69% confidence
    MANUAL = "manual"    # Requires manual review


class HSChapterSection(str, Enum):
    """HS Code chapter sections (simplified for Nigerian trade)."""
    SECTION_I = "section_i"           # Live animals; animal products (01-05)
    SECTION_II = "section_ii"         # Vegetable products (06-14)
    SECTION_III = "section_iii"       # Animal/vegetable fats and oils (15)
    SECTION_IV = "section_iv"         # Prepared foodstuffs (16-24)
    SECTION_V = "section_v"           # Mineral products (25-27)
    SECTION_VI = "section_vi"         # Products of chemical industries (28-38)
    SECTION_VII = "section_vii"       # Plastics and rubber (39-40)
    SECTION_VIII = "section_viii"     # Raw hides, skins, leather (41-43)
    SECTION_IX = "section_ix"         # Wood and articles of wood (44-46)
    SECTION_X = "section_x"           # Pulp, paper (47-49)
    SECTION_XI = "section_xi"         # Textiles and textile articles (50-63)
    SECTION_XII = "section_xii"       # Footwear, headgear (64-67)
    SECTION_XIII = "section_xiii"     # Stone, ceramics, glass (68-70)
    SECTION_XIV = "section_xiv"       # Precious metals, jewelry (71)
    SECTION_XV = "section_xv"         # Base metals (72-83)
    SECTION_XVI = "section_xvi"       # Machinery, electrical equipment (84-85)
    SECTION_XVII = "section_xvii"     # Vehicles, aircraft, vessels (86-89)
    SECTION_XVIII = "section_xviii"   # Optical, medical instruments (90-92)
    SECTION_XIX = "section_xix"       # Arms and ammunition (93)
    SECTION_XX = "section_xx"         # Miscellaneous manufactured articles (94-96)
    SECTION_XXI = "section_xxi"       # Works of art, antiques (97-99)


class HSCode(BaseModel):
    """
    Harmonized System Code structure.
    
    Based on WCO 6-digit international standard with Nigerian extensions.
    """
    # Core HS code (6 digits international standard)
    code: str = Field(..., regex=r"^\d{4}\.\d{2}$", description="6-digit HS code (XXXX.XX format)")
    
    # Descriptive information
    heading_no: str = Field(..., description="HS heading number (XX.XX format)")
    description: str = Field(..., description="Official HS code description")
    tariff: Optional[str] = Field(None, description="Tariff description")
    
    # Nigerian-specific extensions
    tariff_category: Optional[str] = Field(None, description="Nigerian tariff category")
    duty_rate: Optional[Decimal] = Field(None, description="Import duty rate percentage")
    vat_applicable: bool = Field(True, description="Whether VAT applies to this product")
    
    # Classification metadata
    section: HSChapterSection = Field(..., description="HS chapter section")
    chapter: int = Field(..., ge=1, le=99, description="HS chapter number (01-99)")
    
    # Validation flags
    requires_permit: bool = Field(False, description="Product requires import permit")
    controlled_substance: bool = Field(False, description="Controlled or restricted item")
    
    @validator('code')
    def validate_hs_code_format(cls, v):
        """Validate HS code format."""
        if not v or len(v) != 7 or v[4] != '.':
            raise ValueError("HS code must be in XXXX.XX format")
        
        # Validate numeric parts
        try:
            heading = int(v[:4])
            subheading = int(v[5:])
        except ValueError:
            raise ValueError("HS code must contain only digits and one dot")
            
        if heading < 101 or heading > 9999:
            raise ValueError("HS heading must be between 0101 and 9999")
            
        if subheading < 0 or subheading > 99:
            raise ValueError("HS subheading must be between 00 and 99")
            
        return v
    
    @validator('chapter')
    def extract_chapter_from_code(cls, v, values):
        """Extract and validate chapter from HS code."""
        if 'code' in values:
            code_chapter = int(values['code'][:2])
            if v != code_chapter:
                raise ValueError(f"Chapter {v} doesn't match HS code chapter {code_chapter}")
        return v


class ProductClassification(BaseModel):
    """
    Product classification request and metadata.
    """
    # Product identification
    product_name: str = Field(..., min_length=2, description="Product name or description")
    product_description: Optional[str] = Field(None, description="Detailed product description")
    brand: Optional[str] = Field(None, description="Product brand")
    model: Optional[str] = Field(None, description="Product model/variant")
    
    # Business context
    business_sector: Optional[str] = Field(None, description="Business sector (retail, manufacturing, etc.)")
    use_case: Optional[str] = Field(None, description="Primary use case for the product")
    
    # Physical characteristics
    material: Optional[str] = Field(None, description="Primary material")
    weight: Optional[Decimal] = Field(None, description="Product weight in kg")
    dimensions: Optional[Dict[str, Decimal]] = Field(None, description="Product dimensions")
    
    # Value information
    unit_price: Optional[Decimal] = Field(None, description="Unit price in NGN")
    currency: str = Field("NGN", description="Price currency")
    
    # Classification hints
    suggested_keywords: List[str] = Field(default_factory=list, description="Keywords for classification")
    similar_products: List[str] = Field(default_factory=list, description="Similar product names")
    
    # Validation
    requires_manual_review: bool = Field(False, description="Flags for manual classification review")


class HSClassificationResult(BaseModel):
    """
    Result of HS code classification process.
    """
    # Classification outcome
    success: bool = Field(..., description="Whether classification was successful")
    hs_code: Optional[HSCode] = Field(None, description="Classified HS code")
    confidence_level: HSConfidenceLevel = Field(..., description="Classification confidence")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Numeric confidence score")
    
    # Alternative classifications
    alternative_codes: List[HSCode] = Field(default_factory=list, description="Alternative HS codes")
    
    # Classification details
    classification_method: str = Field(..., description="Method used for classification")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords that matched")
    reasoning: Optional[str] = Field(None, description="Classification reasoning")
    
    # Validation and compliance
    firs_compliant: bool = Field(True, description="Compliant with FIRS requirements")
    compliance_notes: List[str] = Field(default_factory=list, description="Compliance notes")
    
    # Processing metadata
    processing_time_ms: float = Field(..., description="Classification processing time")
    timestamp: datetime = Field(default_factory=datetime.now, description="Classification timestamp")
    
    # Error handling
    errors: List[str] = Field(default_factory=list, description="Classification errors")
    warnings: List[str] = Field(default_factory=list, description="Classification warnings")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            'success': self.success,
            'confidence_level': self.confidence_level.value,
            'confidence_score': self.confidence_score,
            'classification_method': self.classification_method,
            'processing_time_ms': self.processing_time_ms,
            'timestamp': self.timestamp.isoformat(),
            'firs_compliant': self.firs_compliant
        }
        
        if self.hs_code:
            result['hs_code'] = {
                'code': self.hs_code.code,
                'description': self.hs_code.description,
                'tariff_category': self.hs_code.tariff_category,
                'chapter': self.hs_code.chapter
            }
        
        if self.alternative_codes:
            result['alternatives'] = [
                {
                    'code': code.code,
                    'description': code.description,
                    'confidence': 'medium'  # Could be enhanced with per-alternative confidence
                }
                for code in self.alternative_codes[:3]  # Top 3 alternatives
            ]
        
        if self.errors:
            result['errors'] = self.errors
            
        if self.warnings:
            result['warnings'] = self.warnings
            
        return result


class HSSearchCriteria(BaseModel):
    """
    Criteria for searching HS codes.
    """
    # Search terms
    keyword: Optional[str] = Field(None, description="Keyword search")
    description_contains: Optional[str] = Field(None, description="Description contains text")
    
    # Code filters
    chapter: Optional[int] = Field(None, ge=1, le=99, description="Filter by chapter")
    section: Optional[HSChapterSection] = Field(None, description="Filter by section")
    heading_pattern: Optional[str] = Field(None, description="Heading number pattern")
    
    # Nigerian-specific filters
    tariff_category: Optional[str] = Field(None, description="Nigerian tariff category")
    requires_permit: Optional[bool] = Field(None, description="Filter by permit requirement")
    controlled_substance: Optional[bool] = Field(None, description="Filter controlled substances")
    
    # Result controls
    limit: int = Field(50, ge=1, le=500, description="Maximum results to return")
    include_alternatives: bool = Field(True, description="Include alternative matches")


class HSValidationResult(BaseModel):
    """
    Result of HS code validation.
    """
    is_valid: bool = Field(..., description="Whether HS code is valid")
    hs_code: str = Field(..., description="HS code being validated")
    
    # Validation details
    format_valid: bool = Field(..., description="Code format is valid")
    code_exists: bool = Field(..., description="Code exists in HS database")
    nigeria_applicable: bool = Field(..., description="Code applicable in Nigeria")
    
    # Error details
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    suggestions: List[str] = Field(default_factory=list, description="Correction suggestions")
    
    # Metadata
    validated_at: datetime = Field(default_factory=datetime.now, description="Validation timestamp")
    validator_version: str = Field("1.0", description="Validator version")