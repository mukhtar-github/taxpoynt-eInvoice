"""
Universal Transaction Processing - Core Platform Component
========================================================

Enterprise-grade universal transaction processing system for ALL external connector types.
This is the cornerstone of TaxPoynt's unified processing architecture that ensures every
transaction, regardless of source, meets the same quality and compliance standards.

Strategic Benefits:
- Single processing standard across Banking, ERP, POS, CRM, E-commerce
- Connector-specific business rules and Nigerian compliance
- Unified fraud detection and risk assessment  
- Cross-connector customer intelligence
- Consistent invoice generation readiness

Supported Integrations:
- Banking: Open Banking, USSD (MTN, Airtel, Glo, 9mobile), NIBSS
- ERP: SAP, Oracle, Dynamics, NetSuite, Odoo
- CRM: Salesforce, HubSpot, Dynamics CRM, Zoho
- POS: Retail, hospitality, e-commerce terminals
- E-commerce: Shopify, WooCommerce, Magento, Jumia
- Accounting: QuickBooks, Xero, Wave, FreshBooks, Sage

This package provides:
- Universal transaction processor with connector-aware processing
- Connector-specific configurations and business rules
- Processing pipeline stages (validation, detection, enrichment)
- Universal transaction models and result types
- Performance optimization and enterprise monitoring

Usage:
    from taxpoynt_platform.core_platform.transaction_processing import (
        UniversalTransactionProcessor,
        ConnectorType,
        ConnectorProcessingConfig,
        UniversalProcessedTransaction,
        ProcessingStage,
        create_universal_transaction_processor
    )
    
    # Initialize universal processor
    processor = create_universal_transaction_processor(
        validator, duplicate_detector, amount_validator,
        business_rule_engine, pattern_matcher
    )
    
    # Process transaction from any connector type
    result = await processor.process_transaction(
        transaction, ConnectorType.ERP_SAP
    )
    
    # Process mixed batch from multiple connectors
    mixed_transactions = [
        (bank_tx, ConnectorType.BANKING_OPEN_BANKING),
        (erp_tx, ConnectorType.ERP_SAP),
        (pos_tx, ConnectorType.POS_RETAIL)
    ]
    results = await processor.process_mixed_batch_transactions(mixed_transactions)
"""

import logging
from typing import Dict, List, Optional, Any, Union

# Core processor
from .universal_transaction_processor import (
    UniversalTransactionProcessor,
    UniversalProcessingResult,
    create_universal_transaction_processor
)

# Configuration system
from .connector_configs.connector_types import ConnectorType
from .connector_configs.processing_config import (
    ConnectorProcessingConfig,
    ProcessingProfile,
    get_default_processing_configs
)

# Processing stages
from .processing_stages.stage_definitions import (
    ProcessingStage,
    ProcessingPipeline
)

# Universal models
from .models.universal_processed_transaction import (
    UniversalProcessedTransaction,
    ProcessingStatus,
    ProcessingMetadata,
    EnrichmentData,
    TransactionRisk
)

# Validation framework
from .validation.universal_validator import (
    UniversalTransactionValidator,
    ValidationResult
)

# Detection framework  
from .detection.universal_duplicate_detector import (
    UniversalDuplicateDetector,
    DuplicateResult
)

# Business rules
from .rules.universal_business_rule_engine import (
    UniversalBusinessRuleEngine,
    BusinessRuleEngineResult
)

# Pattern matching
from .matching.universal_pattern_matcher import (
    UniversalPatternMatcher,
    PatternResult
)

logger = logging.getLogger(__name__)


class TransactionProcessingService:
    """
    High-level service interface for universal transaction processing.
    
    This service provides a simplified interface for integrating universal
    transaction processing into other TaxPoynt platform services.
    """
    
    def __init__(self):
        """Initialize transaction processing service."""
        self.processor: Optional[UniversalTransactionProcessor] = None
        self._initialized = False
        
        # Service metrics
        self.total_processed = 0
        self.success_rate = 0.0
        self.connector_metrics = {}
        
        logger.info("Transaction processing service created")
    
    def initialize(
        self,
        processing_configs: Optional[Dict[ConnectorType, ConnectorProcessingConfig]] = None
    ) -> None:
        """
        Initialize the transaction processing service.
        
        Args:
            processing_configs: Optional custom processing configurations
        """
        if self._initialized:
            logger.warning("Transaction processing service already initialized")
            return
        
        try:
            # Import and initialize required components
            from .validation.universal_validator import UniversalTransactionValidator
            from .detection.universal_duplicate_detector import UniversalDuplicateDetector
            from .validation.universal_amount_validator import UniversalAmountValidator
            from .rules.universal_business_rule_engine import UniversalBusinessRuleEngine
            from .matching.universal_pattern_matcher import UniversalPatternMatcher
            
            # Create component instances
            validator = UniversalTransactionValidator()
            duplicate_detector = UniversalDuplicateDetector()
            amount_validator = UniversalAmountValidator()
            business_rule_engine = UniversalBusinessRuleEngine()
            pattern_matcher = UniversalPatternMatcher()
            
            # Create universal processor
            self.processor = create_universal_transaction_processor(
                validator,
                duplicate_detector,
                amount_validator,
                business_rule_engine,
                pattern_matcher,
                processing_configs
            )
            
            self._initialized = True
            logger.info("Transaction processing service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize transaction processing service: {e}")
            raise
    
    async def process_single_transaction(
        self,
        transaction: Any,
        connector_type: ConnectorType,
        custom_config: Optional[ConnectorProcessingConfig] = None
    ) -> UniversalProcessingResult:
        """Process a single transaction."""
        if not self._initialized or not self.processor:
            raise Exception("Transaction processing service not initialized")
        
        return await self.processor.process_transaction(
            transaction, connector_type, None, custom_config
        )
    
    async def process_batch_transactions(
        self,
        transactions: List[Any],
        connector_type: ConnectorType,
        custom_config: Optional[ConnectorProcessingConfig] = None
    ) -> List[UniversalProcessingResult]:
        """Process batch of transactions from same connector."""
        if not self._initialized or not self.processor:
            raise Exception("Transaction processing service not initialized")
        
        return await self.processor.process_batch_transactions(
            transactions, connector_type, custom_config
        )
    
    async def process_mixed_batch(
        self,
        mixed_transactions: List[tuple[Any, ConnectorType]]
    ) -> List[UniversalProcessingResult]:
        """Process transactions from multiple connector types."""
        if not self._initialized or not self.processor:
            raise Exception("Transaction processing service not initialized")
        
        return await self.processor.process_mixed_batch_transactions(mixed_transactions)
    
    def get_processing_statistics(
        self, 
        connector_type: Optional[ConnectorType] = None
    ) -> Dict[str, Any]:
        """Get processing statistics."""
        if not self.processor:
            return {}
        
        return self.processor.get_processing_statistics(connector_type)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "initialized": self._initialized,
            "processor_available": self.processor is not None,
            "total_processed": self.total_processed,
            "success_rate": self.success_rate
        }


# Global service instance
_transaction_processing_service: Optional[TransactionProcessingService] = None


def get_transaction_processing_service() -> Optional[TransactionProcessingService]:
    """Get global transaction processing service instance."""
    return _transaction_processing_service


def initialize_transaction_processing_service(
    processing_configs: Optional[Dict[ConnectorType, ConnectorProcessingConfig]] = None
) -> TransactionProcessingService:
    """Initialize global transaction processing service."""
    global _transaction_processing_service
    _transaction_processing_service = TransactionProcessingService()
    _transaction_processing_service.initialize(processing_configs)
    return _transaction_processing_service


def close_transaction_processing_service():
    """Close global transaction processing service."""
    global _transaction_processing_service
    if _transaction_processing_service:
        _transaction_processing_service = None


# Package exports
__all__ = [
    # Core service
    "TransactionProcessingService",
    "get_transaction_processing_service",
    "initialize_transaction_processing_service",
    "close_transaction_processing_service",
    
    # Universal processor
    "UniversalTransactionProcessor",
    "UniversalProcessingResult",
    "create_universal_transaction_processor",
    
    # Configuration
    "ConnectorType",
    "ConnectorProcessingConfig",
    "ProcessingProfile",
    "get_default_processing_configs",
    
    # Processing pipeline
    "ProcessingStage",
    "ProcessingPipeline",
    
    # Models
    "UniversalProcessedTransaction",
    "ProcessingStatus",
    "ProcessingMetadata",
    "EnrichmentData",
    "TransactionRisk",
    
    # Components
    "UniversalTransactionValidator",
    "ValidationResult",
    "UniversalDuplicateDetector",
    "DuplicateResult",
    "UniversalBusinessRuleEngine",
    "BusinessRuleEngineResult",
    "UniversalPatternMatcher",
    "PatternResult"
]