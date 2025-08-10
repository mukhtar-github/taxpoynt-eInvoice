"""
Transformation Orchestrator Service

This service orchestrates the complete data transformation pipeline,
coordinating all transformation services to convert ERP data to FIRS-compliant format.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import asyncio

from .erp_to_standard import (
    ERPToStandardTransformer, 
    ERPSystem, 
    StandardInvoiceFormat
)
from .field_mapper import (
    FieldMapper,
    MappingProfile,
    MappingType
)
from .data_enricher import (
    DataEnricher,
    EnrichmentResult
)
from .currency_converter import (
    CurrencyConverter,
    CurrencyConversionResult
)
from .unit_normalizer import (
    UnitNormalizer,
    NormalizationResult
)

logger = logging.getLogger(__name__)


class TransformationStage(Enum):
    """Stages of the transformation pipeline"""
    INITIAL_VALIDATION = "initial_validation"
    ERP_TO_STANDARD = "erp_to_standard"
    FIELD_MAPPING = "field_mapping"
    DATA_ENRICHMENT = "data_enrichment"
    CURRENCY_CONVERSION = "currency_conversion"
    UNIT_NORMALIZATION = "unit_normalization"
    FINAL_VALIDATION = "final_validation"
    FIRS_FORMATTING = "firs_formatting"


@dataclass
class TransformationConfig:
    """Configuration for transformation pipeline"""
    source_erp_system: ERPSystem
    target_currency: str = "NGN"
    target_country: str = "Nigeria"
    enrich_data: bool = True
    normalize_units: bool = True
    convert_currency: bool = True
    strict_validation: bool = True
    include_metadata: bool = True
    custom_mapping_profile: Optional[str] = None


@dataclass
class TransformationResult:
    """Result of complete transformation pipeline"""
    success: bool
    transformed_data: Optional[Dict[str, Any]]
    firs_invoice: Optional[Dict[str, Any]]
    original_data: Dict[str, Any]
    transformation_log: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    processing_time: float


class TransformationOrchestrator:
    """
    Main orchestrator for the complete data transformation pipeline
    
    Coordinates all transformation services to convert ERP data to FIRS-compliant format
    """
    
    def __init__(self, db_connection=None):
        """Initialize the transformation orchestrator"""
        self.erp_transformer = ERPToStandardTransformer()
        self.field_mapper = FieldMapper()
        self.data_enricher = DataEnricher(db_connection)
        self.currency_converter = CurrencyConverter(db_connection)
        self.unit_normalizer = UnitNormalizer()
        
        # Load default mapping profiles
        self.field_mapper.load_default_profiles()
        
        # Initialize transformation statistics
        self.transformation_stats = {
            "total_transformations": 0,
            "successful_transformations": 0,
            "failed_transformations": 0,
            "average_processing_time": 0.0
        }
        
        logger.info("Transformation orchestrator initialized")
    
    async def transform_invoice(
        self,
        erp_data: Dict[str, Any],
        config: TransformationConfig
    ) -> TransformationResult:
        """
        Execute complete transformation pipeline for an invoice
        
        Args:
            erp_data: Raw ERP invoice data
            config: Transformation configuration
            
        Returns:
            Complete transformation result
        """
        start_time = datetime.now()
        transformation_log = []
        errors = []
        warnings = []
        
        try:
            logger.info(f"Starting transformation pipeline for {config.source_erp_system.value} invoice")
            
            # Stage 1: Initial Validation
            validation_result = await self._stage_initial_validation(erp_data, config)
            transformation_log.append(validation_result)
            
            if not validation_result["success"]:
                errors.extend(validation_result.get("errors", []))
                if config.strict_validation:
                    return self._create_error_result(erp_data, transformation_log, errors, warnings, start_time)
            
            # Stage 2: ERP to Standard Format
            standard_result = await self._stage_erp_to_standard(erp_data, config)
            transformation_log.append(standard_result)
            
            if not standard_result["success"]:
                errors.extend(standard_result.get("errors", []))
                return self._create_error_result(erp_data, transformation_log, errors, warnings, start_time)
            
            current_data = standard_result["data"]
            
            # Stage 3: Field Mapping (if custom profile specified)
            if config.custom_mapping_profile:
                mapping_result = await self._stage_field_mapping(current_data, config)
                transformation_log.append(mapping_result)
                
                if mapping_result["success"]:
                    current_data = mapping_result["data"]
                else:
                    warnings.extend(mapping_result.get("warnings", []))
            
            # Stage 4: Data Enrichment
            if config.enrich_data:
                enrichment_result = await self._stage_data_enrichment(current_data, config)
                transformation_log.append(enrichment_result)
                
                if enrichment_result["success"]:
                    current_data = enrichment_result["data"]
                else:
                    warnings.extend(enrichment_result.get("warnings", []))
            
            # Stage 5: Currency Conversion
            if config.convert_currency:
                currency_result = await self._stage_currency_conversion(current_data, config)
                transformation_log.append(currency_result)
                
                if currency_result["success"]:
                    current_data = currency_result["data"]
                else:
                    warnings.extend(currency_result.get("warnings", []))
            
            # Stage 6: Unit Normalization
            if config.normalize_units:
                normalization_result = await self._stage_unit_normalization(current_data, config)
                transformation_log.append(normalization_result)
                
                if normalization_result["success"]:
                    current_data = normalization_result["data"]
                else:
                    warnings.extend(normalization_result.get("warnings", []))
            
            # Stage 7: FIRS Formatting
            firs_result = await self._stage_firs_formatting(current_data, config)
            transformation_log.append(firs_result)
            
            if not firs_result["success"]:
                errors.extend(firs_result.get("errors", []))
                return self._create_error_result(erp_data, transformation_log, errors, warnings, start_time)
            
            firs_invoice = firs_result["data"]
            
            # Stage 8: Final Validation
            final_validation_result = await self._stage_final_validation(firs_invoice, config)
            transformation_log.append(final_validation_result)
            
            if not final_validation_result["success"] and config.strict_validation:
                errors.extend(final_validation_result.get("errors", []))
                return self._create_error_result(erp_data, transformation_log, errors, warnings, start_time)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update statistics
            self._update_statistics(processing_time, True)
            
            # Create success result
            metadata = self._generate_transformation_metadata(
                erp_data, current_data, firs_invoice, config, transformation_log, processing_time
            )
            
            result = TransformationResult(
                success=True,
                transformed_data=current_data,
                firs_invoice=firs_invoice,
                original_data=erp_data,
                transformation_log=transformation_log,
                errors=errors,
                warnings=warnings,
                metadata=metadata,
                processing_time=processing_time
            )
            
            logger.info(f"Transformation pipeline completed successfully in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Transformation pipeline failed: {str(e)}")
            errors.append(f"Pipeline error: {str(e)}")
            return self._create_error_result(erp_data, transformation_log, errors, warnings, start_time)
    
    async def _stage_initial_validation(
        self,
        erp_data: Dict[str, Any],
        config: TransformationConfig
    ) -> Dict[str, Any]:
        """Stage 1: Initial validation of input data"""
        try:
            logger.debug("Executing initial validation stage")
            
            stage_start = datetime.now()
            errors = []
            warnings = []
            
            # Basic structure validation
            if not isinstance(erp_data, dict):
                errors.append("Input data must be a dictionary")
            
            if not erp_data:
                errors.append("Input data cannot be empty")
            
            # ERP system specific validation
            if config.source_erp_system == ERPSystem.ODOO:
                required_fields = ["name", "partner_id", "invoice_line_ids"]
                missing_fields = [field for field in required_fields if field not in erp_data]
                if missing_fields:
                    errors.append(f"Missing required Odoo fields: {missing_fields}")
            
            elif config.source_erp_system == ERPSystem.SAP:
                required_fields = ["BillingDocument", "SoldToParty", "TransactionCurrency"]
                missing_fields = [field for field in required_fields if field not in erp_data]
                if missing_fields:
                    errors.append(f"Missing required SAP fields: {missing_fields}")
            
            processing_time = (datetime.now() - stage_start).total_seconds()
            
            return {
                "stage": TransformationStage.INITIAL_VALIDATION.value,
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "processing_time": processing_time,
                "data": erp_data
            }
            
        except Exception as e:
            logger.error(f"Initial validation stage failed: {str(e)}")
            return {
                "stage": TransformationStage.INITIAL_VALIDATION.value,
                "success": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "processing_time": 0.0,
                "data": None
            }
    
    async def _stage_erp_to_standard(
        self,
        erp_data: Dict[str, Any],
        config: TransformationConfig
    ) -> Dict[str, Any]:
        """Stage 2: Transform ERP data to standard format"""
        try:
            logger.debug("Executing ERP to standard transformation stage")
            
            stage_start = datetime.now()
            
            # Transform using ERP transformer
            standard_format = self.erp_transformer.transform(erp_data, config.source_erp_system)
            
            processing_time = (datetime.now() - stage_start).total_seconds()
            
            return {
                "stage": TransformationStage.ERP_TO_STANDARD.value,
                "success": True,
                "errors": [],
                "warnings": [],
                "processing_time": processing_time,
                "data": standard_format.__dict__
            }
            
        except Exception as e:
            logger.error(f"ERP to standard transformation failed: {str(e)}")
            return {
                "stage": TransformationStage.ERP_TO_STANDARD.value,
                "success": False,
                "errors": [f"ERP transformation error: {str(e)}"],
                "warnings": [],
                "processing_time": 0.0,
                "data": None
            }
    
    async def _stage_field_mapping(
        self,
        data: Dict[str, Any],
        config: TransformationConfig
    ) -> Dict[str, Any]:
        """Stage 3: Apply custom field mapping"""
        try:
            logger.debug("Executing field mapping stage")
            
            stage_start = datetime.now()
            
            # Apply field mapping
            mapped_data = self.field_mapper.map_fields(
                data, 
                config.source_erp_system.value,
                config.custom_mapping_profile or "default"
            )
            
            processing_time = (datetime.now() - stage_start).total_seconds()
            
            return {
                "stage": TransformationStage.FIELD_MAPPING.value,
                "success": True,
                "errors": [],
                "warnings": [],
                "processing_time": processing_time,
                "data": mapped_data
            }
            
        except Exception as e:
            logger.error(f"Field mapping stage failed: {str(e)}")
            return {
                "stage": TransformationStage.FIELD_MAPPING.value,
                "success": False,
                "errors": [],
                "warnings": [f"Field mapping warning: {str(e)}"],
                "processing_time": 0.0,
                "data": data  # Return original data on failure
            }
    
    async def _stage_data_enrichment(
        self,
        data: Dict[str, Any],
        config: TransformationConfig
    ) -> Dict[str, Any]:
        """Stage 4: Enrich data with missing information"""
        try:
            logger.debug("Executing data enrichment stage")
            
            stage_start = datetime.now()
            
            # Enrich data
            enrichment_result = await self.data_enricher.enrich_data(data)
            
            processing_time = (datetime.now() - stage_start).total_seconds()
            
            return {
                "stage": TransformationStage.DATA_ENRICHMENT.value,
                "success": enrichment_result.success,
                "errors": enrichment_result.errors if not enrichment_result.success else [],
                "warnings": [],
                "processing_time": processing_time,
                "data": enrichment_result.enriched_data,
                "enrichment_summary": self.data_enricher.get_enrichment_summary(enrichment_result)
            }
            
        except Exception as e:
            logger.error(f"Data enrichment stage failed: {str(e)}")
            return {
                "stage": TransformationStage.DATA_ENRICHMENT.value,
                "success": False,
                "errors": [],
                "warnings": [f"Data enrichment warning: {str(e)}"],
                "processing_time": 0.0,
                "data": data  # Return original data on failure
            }
    
    async def _stage_currency_conversion(
        self,
        data: Dict[str, Any],
        config: TransformationConfig
    ) -> Dict[str, Any]:
        """Stage 5: Convert currency if needed"""
        try:
            logger.debug("Executing currency conversion stage")
            
            stage_start = datetime.now()
            
            current_currency = data.get("currency_code", "NGN")
            
            # Only convert if currencies are different
            if current_currency != config.target_currency:
                converted_data = await self.currency_converter.convert_invoice_amounts(
                    data, config.target_currency
                )
                
                processing_time = (datetime.now() - stage_start).total_seconds()
                
                return {
                    "stage": TransformationStage.CURRENCY_CONVERSION.value,
                    "success": True,
                    "errors": [],
                    "warnings": [],
                    "processing_time": processing_time,
                    "data": converted_data,
                    "conversion_details": {
                        "from_currency": current_currency,
                        "to_currency": config.target_currency,
                        "conversion_applied": True
                    }
                }
            else:
                processing_time = (datetime.now() - stage_start).total_seconds()
                
                return {
                    "stage": TransformationStage.CURRENCY_CONVERSION.value,
                    "success": True,
                    "errors": [],
                    "warnings": [],
                    "processing_time": processing_time,
                    "data": data,
                    "conversion_details": {
                        "from_currency": current_currency,
                        "to_currency": config.target_currency,
                        "conversion_applied": False
                    }
                }
            
        except Exception as e:
            logger.error(f"Currency conversion stage failed: {str(e)}")
            return {
                "stage": TransformationStage.CURRENCY_CONVERSION.value,
                "success": False,
                "errors": [],
                "warnings": [f"Currency conversion warning: {str(e)}"],
                "processing_time": 0.0,
                "data": data  # Return original data on failure
            }
    
    async def _stage_unit_normalization(
        self,
        data: Dict[str, Any],
        config: TransformationConfig
    ) -> Dict[str, Any]:
        """Stage 6: Normalize units of measure"""
        try:
            logger.debug("Executing unit normalization stage")
            
            stage_start = datetime.now()
            
            # Normalize units
            normalized_data = self.unit_normalizer.normalize_invoice_quantities(data)
            
            processing_time = (datetime.now() - stage_start).total_seconds()
            
            return {
                "stage": TransformationStage.UNIT_NORMALIZATION.value,
                "success": True,
                "errors": [],
                "warnings": [],
                "processing_time": processing_time,
                "data": normalized_data
            }
            
        except Exception as e:
            logger.error(f"Unit normalization stage failed: {str(e)}")
            return {
                "stage": TransformationStage.UNIT_NORMALIZATION.value,
                "success": False,
                "errors": [],
                "warnings": [f"Unit normalization warning: {str(e)}"],
                "processing_time": 0.0,
                "data": data  # Return original data on failure
            }
    
    async def _stage_firs_formatting(
        self,
        data: Dict[str, Any],
        config: TransformationConfig
    ) -> Dict[str, Any]:
        """Stage 7: Format data for FIRS compliance"""
        try:
            logger.debug("Executing FIRS formatting stage")
            
            stage_start = datetime.now()
            
            # Convert to FIRS format
            firs_invoice = self._convert_to_firs_format(data, config)
            
            processing_time = (datetime.now() - stage_start).total_seconds()
            
            return {
                "stage": TransformationStage.FIRS_FORMATTING.value,
                "success": True,
                "errors": [],
                "warnings": [],
                "processing_time": processing_time,
                "data": firs_invoice
            }
            
        except Exception as e:
            logger.error(f"FIRS formatting stage failed: {str(e)}")
            return {
                "stage": TransformationStage.FIRS_FORMATTING.value,
                "success": False,
                "errors": [f"FIRS formatting error: {str(e)}"],
                "warnings": [],
                "processing_time": 0.0,
                "data": None
            }
    
    async def _stage_final_validation(
        self,
        firs_invoice: Dict[str, Any],
        config: TransformationConfig
    ) -> Dict[str, Any]:
        """Stage 8: Final validation of FIRS invoice"""
        try:
            logger.debug("Executing final validation stage")
            
            stage_start = datetime.now()
            errors = []
            warnings = []
            
            # FIRS compliance validation
            required_fields = [
                "invoice_number", "invoice_date", "supplier_tin", "supplier_name",
                "customer_name", "currency_code", "total_amount", "line_items"
            ]
            
            missing_fields = [field for field in required_fields if field not in firs_invoice]
            if missing_fields:
                errors.append(f"Missing required FIRS fields: {missing_fields}")
            
            # Business rules validation
            if firs_invoice.get("total_amount", 0) <= 0:
                errors.append("Total amount must be greater than zero")
            
            if not firs_invoice.get("line_items", []):
                errors.append("Invoice must have at least one line item")
            
            # Nigerian specific validation
            if firs_invoice.get("currency_code") != "NGN":
                warnings.append("Non-NGN currency detected")
            
            processing_time = (datetime.now() - stage_start).total_seconds()
            
            return {
                "stage": TransformationStage.FINAL_VALIDATION.value,
                "success": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "processing_time": processing_time,
                "data": firs_invoice
            }
            
        except Exception as e:
            logger.error(f"Final validation stage failed: {str(e)}")
            return {
                "stage": TransformationStage.FINAL_VALIDATION.value,
                "success": False,
                "errors": [f"Final validation error: {str(e)}"],
                "warnings": [],
                "processing_time": 0.0,
                "data": None
            }
    
    def _convert_to_firs_format(self, data: Dict[str, Any], config: TransformationConfig) -> Dict[str, Any]:
        """Convert standardized data to FIRS-compliant format"""
        # This is a simplified conversion - in practice, this would be more comprehensive
        firs_invoice = {
            "invoice_number": data.get("invoice_number", ""),
            "invoice_date": data.get("invoice_date", ""),
            "due_date": data.get("due_date"),
            "supplier_tin": data.get("supplier_tin", ""),
            "supplier_name": data.get("supplier_name", ""),
            "supplier_address": data.get("supplier_address", {}),
            "customer_tin": data.get("customer_tin"),
            "customer_name": data.get("customer_name", ""),
            "customer_address": data.get("customer_address", {}),
            "currency_code": data.get("currency_code", config.target_currency),
            "total_amount": data.get("total_amount", 0),
            "tax_amount": data.get("tax_amount", 0),
            "discount_amount": data.get("discount_amount", 0),
            "line_items": data.get("line_items", []),
            "payment_terms": data.get("payment_terms"),
            "invoice_type": data.get("invoice_type", "standard"),
            "exchange_rate": data.get("exchange_rate"),
            "transformation_metadata": {
                "source_system": config.source_erp_system.value,
                "transformation_date": datetime.now().isoformat(),
                "target_country": config.target_country
            }
        }
        
        return firs_invoice
    
    def _create_error_result(
        self,
        original_data: Dict[str, Any],
        transformation_log: List[Dict[str, Any]],
        errors: List[str],
        warnings: List[str],
        start_time: datetime
    ) -> TransformationResult:
        """Create an error result"""
        processing_time = (datetime.now() - start_time).total_seconds()
        self._update_statistics(processing_time, False)
        
        return TransformationResult(
            success=False,
            transformed_data=None,
            firs_invoice=None,
            original_data=original_data,
            transformation_log=transformation_log,
            errors=errors,
            warnings=warnings,
            metadata={"processing_time": processing_time, "failure_reason": "Pipeline error"},
            processing_time=processing_time
        )
    
    def _generate_transformation_metadata(
        self,
        original_data: Dict[str, Any],
        transformed_data: Dict[str, Any],
        firs_invoice: Dict[str, Any],
        config: TransformationConfig,
        transformation_log: List[Dict[str, Any]],
        processing_time: float
    ) -> Dict[str, Any]:
        """Generate comprehensive transformation metadata"""
        return {
            "transformation_id": f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "source_system": config.source_erp_system.value,
            "target_format": "FIRS",
            "transformation_date": datetime.now().isoformat(),
            "processing_time": processing_time,
            "stages_executed": len(transformation_log),
            "configuration": {
                "target_currency": config.target_currency,
                "target_country": config.target_country,
                "enrich_data": config.enrich_data,
                "normalize_units": config.normalize_units,
                "convert_currency": config.convert_currency,
                "strict_validation": config.strict_validation
            },
            "data_summary": {
                "original_line_items": len(original_data.get("line_items", [])),
                "transformed_line_items": len(transformed_data.get("line_items", [])),
                "firs_line_items": len(firs_invoice.get("line_items", [])),
                "original_currency": original_data.get("currency_code", "Unknown"),
                "target_currency": config.target_currency
            },
            "quality_metrics": {
                "completeness_score": self._calculate_completeness_score(firs_invoice),
                "transformation_accuracy": self._calculate_transformation_accuracy(original_data, firs_invoice)
            }
        }
    
    def _calculate_completeness_score(self, firs_invoice: Dict[str, Any]) -> float:
        """Calculate data completeness score"""
        required_fields = [
            "invoice_number", "invoice_date", "supplier_tin", "supplier_name",
            "customer_name", "currency_code", "total_amount", "line_items"
        ]
        
        present_fields = sum(1 for field in required_fields if firs_invoice.get(field))
        return (present_fields / len(required_fields)) * 100
    
    def _calculate_transformation_accuracy(self, original: Dict[str, Any], transformed: Dict[str, Any]) -> float:
        """Calculate transformation accuracy score"""
        # Compare key numerical fields
        original_total = float(original.get("total_amount", 0))
        transformed_total = float(transformed.get("total_amount", 0))
        
        if original_total == 0:
            return 100.0 if transformed_total == 0 else 0.0
        
        accuracy = (1 - abs(original_total - transformed_total) / original_total) * 100
        return max(0.0, accuracy)
    
    def _update_statistics(self, processing_time: float, success: bool):
        """Update transformation statistics"""
        self.transformation_stats["total_transformations"] += 1
        
        if success:
            self.transformation_stats["successful_transformations"] += 1
        else:
            self.transformation_stats["failed_transformations"] += 1
        
        # Update average processing time
        total = self.transformation_stats["total_transformations"]
        current_avg = self.transformation_stats["average_processing_time"]
        new_avg = ((current_avg * (total - 1)) + processing_time) / total
        self.transformation_stats["average_processing_time"] = new_avg
    
    async def batch_transform(
        self,
        invoices: List[Dict[str, Any]],
        config: TransformationConfig,
        max_concurrent: int = 5
    ) -> List[TransformationResult]:
        """
        Transform multiple invoices concurrently
        
        Args:
            invoices: List of ERP invoice data
            config: Transformation configuration
            max_concurrent: Maximum concurrent transformations
            
        Returns:
            List of transformation results
        """
        logger.info(f"Starting batch transformation of {len(invoices)} invoices")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def transform_with_semaphore(invoice_data):
            async with semaphore:
                return await self.transform_invoice(invoice_data, config)
        
        # Execute transformations concurrently
        tasks = [transform_with_semaphore(invoice) for invoice in invoices]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch transformation failed for invoice {i}: {str(result)}")
                final_results.append(self._create_error_result(
                    invoices[i], [], [f"Batch error: {str(result)}"], [], datetime.now()
                ))
            else:
                final_results.append(result)
        
        successful = sum(1 for r in final_results if r.success)
        logger.info(f"Batch transformation completed: {successful}/{len(invoices)} successful")
        
        return final_results
    
    def get_transformation_statistics(self) -> Dict[str, Any]:
        """Get transformation statistics"""
        stats = self.transformation_stats.copy()
        
        if stats["total_transformations"] > 0:
            stats["success_rate"] = (stats["successful_transformations"] / stats["total_transformations"]) * 100
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def get_supported_systems(self) -> List[str]:
        """Get list of supported ERP systems"""
        return self.erp_transformer.get_supported_systems()
    
    def get_available_mapping_profiles(self) -> List[Dict[str, str]]:
        """Get available mapping profiles"""
        return self.field_mapper.get_available_profiles()