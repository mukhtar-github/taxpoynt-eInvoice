"""
ERP Connector Adapter
=====================

Adapter that bridges existing ERP connectors with the universal transaction
processing pipeline. This allows gradual migration of ERP connectors to use
the standardized processing while maintaining compatibility with existing code.

The adapter handles:
- Converting ERP-specific data formats to universal transaction format
- Mapping ERP connector methods to universal processing pipeline
- Maintaining backward compatibility during migration
- Providing enhanced processing capabilities through universal pipeline

Migration Strategy:
Phase 1: Wrap existing connectors with universal processing
Phase 2: Gradually replace direct ERP calls with universal pipeline
Phase 3: Full migration to universal architecture
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import asyncio

from ..connector_configs.connector_types import ConnectorType
from ..connector_configs.processing_config import get_processing_config
from ..processing_stages.stage_definitions import get_default_pipeline_for_connector
from ..models.universal_transaction import UniversalTransaction
from ..models.universal_processed_transaction import UniversalProcessedTransaction
from ...external_integrations.connector_framework.base_erp_connector import BaseERPConnector

logger = logging.getLogger(__name__)


class ERPConnectorAdapter:
    """
    Adapter that wraps existing ERP connectors to use universal transaction processing.
    
    This adapter serves as a bridge between the legacy ERP connector interface
    and the new universal processing pipeline, enabling gradual migration while
    providing immediate benefits from standardized processing.
    """
    
    def __init__(
        self,
        erp_connector: BaseERPConnector,
        connector_type: ConnectorType,
        enable_universal_processing: bool = True
    ):
        """
        Initialize the ERP connector adapter.
        
        Args:
            erp_connector: Existing ERP connector instance
            connector_type: Type of ERP connector
            enable_universal_processing: Enable universal processing pipeline
        """
        self.erp_connector = erp_connector
        self.connector_type = connector_type
        self.enable_universal_processing = enable_universal_processing
        
        # Get processing configuration for this connector type
        self.processing_config = get_processing_config(connector_type)
        self.processing_pipeline = get_default_pipeline_for_connector(connector_type)
        
        # Initialize universal processor components (lazy loading)
        self._universal_processor = None
        
        # Performance tracking
        self.stats = {
            'total_processed': 0,
            'universal_processed': 0,
            'direct_processed': 0,
            'processing_errors': 0,
            'average_processing_time': 0.0
        }
        
        logger.info(f"Initialized ERP adapter for {connector_type.value} with universal processing {'enabled' if enable_universal_processing else 'disabled'}")
    
    @property
    def universal_processor(self):
        """Lazy load universal processor to avoid circular imports."""
        if self._universal_processor is None and self.enable_universal_processing:
            try:
                from .. import get_transaction_processing_service
                service = get_transaction_processing_service()
                if service and service.processor:
                    self._universal_processor = service.processor
                else:
                    logger.warning("Universal transaction processing service not available")
            except ImportError:
                logger.warning("Could not import universal transaction processing service")
        return self._universal_processor
    
    async def get_invoices_with_processing(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        document_type: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'billing'
    ) -> Dict[str, Any]:
        """
        Get invoices from ERP system with universal processing applied.
        
        This method enhances the original get_invoices method by applying
        the universal transaction processing pipeline to the results.
        
        Returns:
            Dict containing both raw and processed invoice data
        """
        start_time = datetime.utcnow()
        
        try:
            # Get raw invoice data from ERP connector
            raw_invoices = await self.erp_connector.get_invoices(
                limit=limit,
                offset=offset,
                start_date=start_date,
                end_date=end_date,
                document_type=document_type,
                include_attachments=include_attachments,
                data_source=data_source
            )
            
            if not self.enable_universal_processing or not self.universal_processor:
                # Return raw data if universal processing is disabled
                self.stats['direct_processed'] += len(raw_invoices)
                return {
                    'invoices': raw_invoices,
                    'processed_invoices': [],
                    'processing_enabled': False,
                    'total_count': len(raw_invoices)
                }
            
            # Convert ERP invoices to universal transaction format
            universal_transactions = []
            for invoice in raw_invoices:
                try:
                    universal_tx = self._convert_erp_invoice_to_universal_transaction(invoice)
                    universal_transactions.append(universal_tx)
                except Exception as e:
                    logger.error(f"Failed to convert ERP invoice to universal format: {e}")
                    continue
            
            # Process through universal pipeline
            processed_results = []
            if universal_transactions:
                processing_results = await self.universal_processor.process_batch_transactions(
                    universal_transactions,
                    self.connector_type,
                    self.processing_config
                )
                
                processed_results = [
                    result for result in processing_results if result.success
                ]
            
            # Update statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_stats(len(raw_invoices), len(processed_results), processing_time)
            
            return {
                'invoices': raw_invoices,
                'processed_invoices': [r.processed_transaction for r in processed_results if r.processed_transaction],
                'processing_results': processed_results,
                'processing_enabled': True,
                'total_count': len(raw_invoices),
                'processed_count': len(processed_results),
                'processing_time': processing_time,
                'connector_type': self.connector_type.value
            }
            
        except Exception as e:
            logger.error(f"Error in get_invoices_with_processing: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    async def get_invoice_by_id_with_processing(
        self,
        invoice_id: Union[int, str]
    ) -> Dict[str, Any]:
        """
        Get a specific invoice by ID with universal processing applied.
        
        Args:
            invoice_id: Invoice identifier
            
        Returns:
            Dict containing raw and processed invoice data
        """
        start_time = datetime.utcnow()
        
        try:
            # Get raw invoice data
            raw_invoice = await self.erp_connector.get_invoice_by_id(invoice_id)
            
            if not self.enable_universal_processing or not self.universal_processor:
                return {
                    'invoice': raw_invoice,
                    'processed_invoice': None,
                    'processing_enabled': False
                }
            
            # Convert to universal transaction format
            universal_tx = self._convert_erp_invoice_to_universal_transaction(raw_invoice)
            
            # Process through universal pipeline
            processing_result = await self.universal_processor.process_transaction(
                universal_tx,
                self.connector_type,
                None,  # No historical context for single transaction
                self.processing_config
            )
            
            # Update statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_stats(1, 1 if processing_result.success else 0, processing_time)
            
            return {
                'invoice': raw_invoice,
                'processed_invoice': processing_result.processed_transaction if processing_result.success else None,
                'processing_result': processing_result,
                'processing_enabled': True,
                'processing_time': processing_time,
                'connector_type': self.connector_type.value
            }
            
        except Exception as e:
            logger.error(f"Error in get_invoice_by_id_with_processing: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    async def search_invoices_with_processing(
        self,
        customer_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search invoices with universal processing applied.
        
        Returns:
            Dict containing search results with processing enhancements
        """
        try:
            # Get raw search results
            raw_invoices = await self.erp_connector.search_invoices(
                customer_name=customer_name,
                invoice_number=invoice_number,
                amount_range=amount_range,
                date_range=date_range,
                limit=limit
            )
            
            if not self.enable_universal_processing or not self.universal_processor:
                return {
                    'search_results': raw_invoices,
                    'processed_results': [],
                    'processing_enabled': False,
                    'total_count': len(raw_invoices)
                }
            
            # Apply universal processing to search results
            result = await self._process_invoice_batch(raw_invoices)
            
            # Add search metadata
            result.update({
                'search_criteria': {
                    'customer_name': customer_name,
                    'invoice_number': invoice_number,
                    'amount_range': amount_range,
                    'date_range': date_range,
                    'limit': limit
                },
                'search_results': raw_invoices  # Keep original results
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in search_invoices_with_processing: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    async def validate_and_transform_for_firs(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """
        Validate and transform invoice data for FIRS submission using universal processing.
        
        This method leverages universal processing for validation and Nigerian
        compliance checking before applying ERP-specific FIRS transformation.
        
        Args:
            invoice_data: Invoice data to validate and transform
            target_format: Target FIRS format
            
        Returns:
            Dict with validation results and transformed data
        """
        try:
            # Convert to universal transaction for validation
            universal_tx = self._convert_erp_invoice_to_universal_transaction(invoice_data)
            
            if self.enable_universal_processing and self.universal_processor:
                # Process through universal pipeline for validation
                processing_result = await self.universal_processor.process_transaction(
                    universal_tx,
                    self.connector_type
                )
                
                if not processing_result.success:
                    return {
                        'success': False,
                        'validation_errors': processing_result.errors,
                        'warnings': processing_result.warnings,
                        'original_data': invoice_data
                    }
                
                # Use processed transaction for enhanced transformation
                enhanced_invoice_data = self._merge_processed_data_with_original(
                    invoice_data, processing_result.processed_transaction
                )
            else:
                enhanced_invoice_data = invoice_data
            
            # Apply ERP-specific FIRS transformation
            transformation_result = await self.erp_connector.transform_to_firs_format(
                enhanced_invoice_data, target_format
            )
            
            return {
                'success': True,
                'transformed_data': transformation_result,
                'original_data': invoice_data,
                'enhanced_data': enhanced_invoice_data,
                'processing_applied': self.enable_universal_processing,
                'target_format': target_format,
                'connector_type': self.connector_type.value
            }
            
        except Exception as e:
            logger.error(f"Error in validate_and_transform_for_firs: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_data': invoice_data
            }
    
    def _convert_erp_invoice_to_universal_transaction(
        self,
        erp_invoice: Dict[str, Any]
    ) -> UniversalTransaction:
        """
        Convert ERP invoice data to universal transaction format.
        
        This method maps ERP-specific fields to standardized universal transaction fields.
        """
        # Extract common fields with ERP-specific mapping
        transaction_id = (
            erp_invoice.get('id') or 
            erp_invoice.get('invoice_id') or 
            erp_invoice.get('document_number') or 
            erp_invoice.get('billing_document_id')
        )
        
        amount = (
            erp_invoice.get('total_amount') or
            erp_invoice.get('amount') or
            erp_invoice.get('net_amount') or
            erp_invoice.get('gross_amount') or
            0.0
        )
        
        # Parse transaction date
        transaction_date = erp_invoice.get('invoice_date') or erp_invoice.get('document_date')
        if isinstance(transaction_date, str):
            try:
                transaction_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
            except ValueError:
                transaction_date = datetime.utcnow()
        elif not isinstance(transaction_date, datetime):
            transaction_date = datetime.utcnow()
        
        description = (
            erp_invoice.get('description') or
            erp_invoice.get('invoice_description') or
            erp_invoice.get('document_text') or
            f"ERP Invoice {transaction_id}"
        )
        
        currency = erp_invoice.get('currency', 'NGN')
        
        # Create universal transaction
        return UniversalTransaction(
            id=str(transaction_id),
            amount=float(amount),
            currency=currency,
            date=transaction_date,
            description=description,
            
            # ERP-specific fields
            account_number=erp_invoice.get('customer_account') or erp_invoice.get('sold_to_party'),
            reference=erp_invoice.get('reference_number') or erp_invoice.get('purchase_order'),
            category=erp_invoice.get('document_type') or 'invoice',
            
            # Additional ERP metadata
            erp_metadata={
                'invoice_number': erp_invoice.get('invoice_number'),
                'customer_code': erp_invoice.get('customer_code') or erp_invoice.get('sold_to_party'),
                'cost_center': erp_invoice.get('cost_center'),
                'profit_center': erp_invoice.get('profit_center'),
                'company_code': erp_invoice.get('company_code'),
                'business_area': erp_invoice.get('business_area'),
                'document_type': erp_invoice.get('document_type'),
                'posting_date': erp_invoice.get('posting_date'),
                'due_date': erp_invoice.get('due_date'),
                'payment_terms': erp_invoice.get('payment_terms'),
                'tax_amount': erp_invoice.get('tax_amount'),
                'vat_amount': erp_invoice.get('vat_amount'),
                'line_items': erp_invoice.get('line_items', [])
            },
            
            # Source information
            source_system=self.connector_type.value,
            source_connector='erp_adapter',
            raw_data=erp_invoice
        )
    
    def _merge_processed_data_with_original(
        self,
        original_data: Dict[str, Any],
        processed_transaction: UniversalProcessedTransaction
    ) -> Dict[str, Any]:
        """
        Merge processed transaction enhancements with original ERP data.
        
        This creates an enhanced version of the original invoice data that includes
        insights and validations from the universal processing pipeline.
        """
        enhanced_data = original_data.copy()
        
        # Add processing metadata
        enhanced_data['processing_metadata'] = {
            'processed': True,
            'processing_timestamp': processed_transaction.processing_metadata.processing_timestamp.isoformat(),
            'confidence_score': processed_transaction.processing_metadata.confidence_score,
            'risk_level': processed_transaction.processing_metadata.risk_level.value,
            'validation_passed': processed_transaction.processing_metadata.validation_passed,
            'processing_notes': processed_transaction.processing_metadata.processing_notes or []
        }
        
        # Add enrichment data
        if processed_transaction.enrichment_data:
            enrichment = processed_transaction.enrichment_data
            enhanced_data['enrichment'] = {
                'customer_matched': enrichment.customer_matched,
                'customer_confidence': enrichment.customer_confidence,
                'primary_category': enrichment.primary_category,
                'business_purpose': enrichment.business_purpose,
                'merchant_identified': enrichment.merchant_identified
            }
            
            # Enhance customer information if available
            if enrichment.customer_matched and enrichment.customer_name:
                enhanced_data['enhanced_customer_info'] = {
                    'id': enrichment.customer_id,
                    'name': enrichment.customer_name,
                    'type': enrichment.customer_type,
                    'confidence': enrichment.customer_confidence
                }
        
        # Add validation results
        if processed_transaction.validation_result:
            enhanced_data['validation_info'] = {
                'is_valid': processed_transaction.validation_result.is_valid,
                'issues_count': len(processed_transaction.validation_result.issues) if processed_transaction.validation_result.issues else 0,
                'critical_issues': processed_transaction.validation_result.critical_count,
                'warnings': processed_transaction.validation_result.warnings_count
            }
        
        return enhanced_data
    
    async def _process_invoice_batch(self, invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of invoices through universal pipeline."""
        if not invoices:
            return {
                'invoices': [],
                'processed_invoices': [],
                'processing_enabled': False,
                'total_count': 0
            }
        
        start_time = datetime.utcnow()
        
        # Convert to universal transactions
        universal_transactions = []
        for invoice in invoices:
            try:
                universal_tx = self._convert_erp_invoice_to_universal_transaction(invoice)
                universal_transactions.append(universal_tx)
            except Exception as e:
                logger.error(f"Failed to convert invoice to universal format: {e}")
                continue
        
        # Process through universal pipeline
        processed_results = []
        if universal_transactions and self.universal_processor:
            processing_results = await self.universal_processor.process_batch_transactions(
                universal_transactions,
                self.connector_type,
                self.processing_config
            )
            
            processed_results = [
                result for result in processing_results if result.success
            ]
        
        # Update statistics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        self._update_stats(len(invoices), len(processed_results), processing_time)
        
        return {
            'invoices': invoices,
            'processed_invoices': [r.processed_transaction for r in processed_results if r.processed_transaction],
            'processing_results': processed_results,
            'processing_enabled': True,
            'total_count': len(invoices),
            'processed_count': len(processed_results),
            'processing_time': processing_time,
            'connector_type': self.connector_type.value
        }
    
    def _update_stats(self, total_count: int, processed_count: int, processing_time: float):
        """Update adapter statistics."""
        self.stats['total_processed'] += total_count
        self.stats['universal_processed'] += processed_count
        
        # Update average processing time
        if self.stats['total_processed'] > 0:
            total_time = self.stats['average_processing_time'] * (self.stats['total_processed'] - total_count)
            total_time += processing_time
            self.stats['average_processing_time'] = total_time / self.stats['total_processed']
    
    # Delegate other methods to original connector
    async def test_connection(self):
        """Delegate to original connector."""
        return await self.erp_connector.test_connection()
    
    async def authenticate(self):
        """Delegate to original connector."""
        return await self.erp_connector.authenticate()
    
    async def get_partners(self, search_term: Optional[str] = None, limit: int = 100, offset: int = 0):
        """Delegate to original connector."""
        return await self.erp_connector.get_partners(search_term, limit, offset)
    
    async def get_tax_configuration(self):
        """Delegate to original connector."""
        return await self.erp_connector.get_tax_configuration()
    
    async def disconnect(self):
        """Delegate to original connector."""
        return await self.erp_connector.disconnect()
    
    def is_connected(self) -> bool:
        """Delegate to original connector."""
        return self.erp_connector.is_connected()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get enhanced connection status including adapter statistics."""
        base_status = self.erp_connector.get_connection_status()
        base_status.update({
            'universal_processing_enabled': self.enable_universal_processing,
            'adapter_stats': self.stats,
            'processing_config': {
                'connector_type': self.connector_type.value,
                'profile': self.processing_config.profile.value if self.processing_config else None,
                'pipeline_stages': len(self.processing_pipeline.stage_configs) if self.processing_pipeline else 0
            }
        })
        return base_status
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get detailed processing statistics."""
        return {
            'adapter_stats': self.stats.copy(),
            'connector_type': self.connector_type.value,
            'universal_processing_enabled': self.enable_universal_processing,
            'processing_config_profile': self.processing_config.profile.value if self.processing_config else None
        }


def create_erp_adapter(
    erp_connector: BaseERPConnector,
    connector_type: ConnectorType,
    enable_universal_processing: bool = True
) -> ERPConnectorAdapter:
    """
    Factory function to create an ERP connector adapter.
    
    Args:
        erp_connector: Existing ERP connector instance
        connector_type: Type of ERP connector
        enable_universal_processing: Whether to enable universal processing
        
    Returns:
        ERPConnectorAdapter instance
    """
    return ERPConnectorAdapter(
        erp_connector=erp_connector,
        connector_type=connector_type,
        enable_universal_processing=enable_universal_processing
    )