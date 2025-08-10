"""
SI Services Transformation Package

This package contains data transformation services for the System Integrator (SI) role,
handling the conversion and normalization of ERP data to standardized formats.
"""

from .erp_to_standard import (
    ERPToStandardTransformer,
    StandardInvoiceFormat,
    ERPSystem,
    OdooTransformer,
    SAPTransformer,
    GenericTransformer
)

from .field_mapper import (
    FieldMapper,
    MappingProfile,
    FieldMapping,
    MappingType,
    TransformationFunctions
)

from .data_enricher import (
    DataEnricher,
    EnrichmentResult,
    EnrichmentRule,
    EnrichmentSource,
    DatabaseLookupService,
    ExternalAPIService,
    CalculationEngine,
    InferenceEngine
)

from .currency_converter import (
    CurrencyConverter,
    CurrencyConversionResult,
    ExchangeRate,
    CurrencyCode,
    CBNExchangeRateProvider,
    ExternalAPIProvider,
    DatabaseRateProvider
)

from .unit_normalizer import (
    UnitNormalizer,
    NormalizationResult,
    UnitDefinition,
    UnitCategory,
    BaseUnit,
    UnitRegistry
)

from .transformation_orchestrator import (
    TransformationOrchestrator,
    TransformationConfig,
    TransformationResult,
    TransformationStage
)

__all__ = [
    # ERP to Standard
    "ERPToStandardTransformer",
    "StandardInvoiceFormat", 
    "ERPSystem",
    "OdooTransformer",
    "SAPTransformer",
    "GenericTransformer",
    
    # Field Mapper
    "FieldMapper",
    "MappingProfile",
    "FieldMapping",
    "MappingType",
    "TransformationFunctions",
    
    # Data Enricher
    "DataEnricher",
    "EnrichmentResult",
    "EnrichmentRule",
    "EnrichmentSource",
    "DatabaseLookupService",
    "ExternalAPIService",
    "CalculationEngine",
    "InferenceEngine",
    
    # Currency Converter
    "CurrencyConverter",
    "CurrencyConversionResult",
    "ExchangeRate",
    "CurrencyCode",
    "CBNExchangeRateProvider",
    "ExternalAPIProvider",
    "DatabaseRateProvider",
    
    # Unit Normalizer
    "UnitNormalizer",
    "NormalizationResult",
    "UnitDefinition",
    "UnitCategory",
    "BaseUnit",
    "UnitRegistry",
    
    # Transformation Orchestrator
    "TransformationOrchestrator",
    "TransformationConfig",
    "TransformationResult",
    "TransformationStage"
]