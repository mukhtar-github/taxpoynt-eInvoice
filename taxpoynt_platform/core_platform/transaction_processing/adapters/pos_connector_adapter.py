"""
POS Connector Adapter
=====================

Adapter that bridges existing POS connectors with the universal transaction
processing pipeline. This enables POS systems to benefit from standardized
processing, Nigerian retail compliance, and enhanced fraud detection.

The adapter handles:
- Converting POS-specific transaction formats to universal transaction format
- Applying retail-specific business rules and validation
- Enhanced fraud detection for customer-facing transactions
- Nigerian consumer protection compliance
- Receipt validation and completeness checks
- Customer behavior analysis and pattern recognition

Supported POS Systems:
- Square POS
- Shopify POS  
- Lightspeed Retail
- Clover POS
- Toast POS (hospitality)
- Moniepoint POS (Nigerian)
- OPay POS (Nigerian)
- PalmPay POS (Nigerian)

Migration Strategy:
Phase 1: Wrap existing POS connectors with universal processing
Phase 2: Enhanced retail analytics and Nigerian compliance
Phase 3: Cross-POS customer intelligence and fraud prevention
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
import asyncio

from ..connector_configs.connector_types import ConnectorType
from ..connector_configs.processing_config import get_processing_config
from ..processing_stages.stage_definitions import get_default_pipeline_for_connector
from ..models.universal_transaction import UniversalTransaction
from ..models.universal_processed_transaction import UniversalProcessedTransaction
from ...external_integrations.connector_framework.base_pos_connector import BasePOSConnector

logger = logging.getLogger(__name__)


class POSConnectorAdapter:
    """
    Adapter that wraps existing POS connectors to use universal transaction processing.
    
    This adapter provides enhanced capabilities for retail transaction processing:
    - Nigerian retail compliance validation
    - Consumer protection rule enforcement
    - Enhanced fraud detection for customer transactions
    - Receipt completeness verification
    - Customer behavior analysis
    - Cross-POS intelligence and pattern recognition
    """
    
    def __init__(
        self,
        pos_connector: BasePOSConnector,
        connector_type: ConnectorType,
        enable_universal_processing: bool = True
    ):
        """
        Initialize the POS connector adapter.
        
        Args:
            pos_connector: Existing POS connector instance
            connector_type: Type of POS connector
            enable_universal_processing: Enable universal processing pipeline
        """
        self.pos_connector = pos_connector
        self.connector_type = connector_type
        self.enable_universal_processing = enable_universal_processing
        
        # Get processing configuration for this POS connector type
        self.processing_config = get_processing_config(connector_type)
        self.processing_pipeline = get_default_pipeline_for_connector(connector_type)
        
        # Initialize universal processor components (lazy loading)
        self._universal_processor = None
        
        # POS-specific tracking
        self.stats = {
            'total_transactions': 0,
            'universal_processed': 0,
            'direct_processed': 0,
            'fraud_detected': 0,
            'receipts_validated': 0,
            'customer_matched': 0,
            'processing_errors': 0,
            'average_processing_time': 0.0
        }
        
        logger.info(f"Initialized POS adapter for {connector_type.value} with universal processing {'enabled' if enable_universal_processing else 'disabled'}")
    
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
    
    async def get_transactions_with_processing(
        self,
        location_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        payment_methods: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get POS transactions with universal processing applied.
        
        This method enhances the original get_transactions method by applying
        retail-specific validation, fraud detection, and Nigerian compliance checks.
        
        Returns:
            Dict containing both raw and processed transaction data
        """
        start_time = datetime.utcnow()
        
        try:
            # Get raw transaction data from POS connector
            raw_transactions = await self.pos_connector.get_transactions(
                location_id=location_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset,
                payment_methods=payment_methods
            )
            
            if not self.enable_universal_processing or not self.universal_processor:
                # Return raw data if universal processing is disabled
                self.stats['direct_processed'] += len(raw_transactions)
                return {
                    'transactions': raw_transactions,
                    'processed_transactions': [],
                    'processing_enabled': False,
                    'total_count': len(raw_transactions)
                }
            
            # Convert POS transactions to universal transaction format
            universal_transactions = []
            for transaction in raw_transactions:
                try:
                    universal_tx = self._convert_pos_transaction_to_universal(transaction)
                    universal_transactions.append(universal_tx)
                except Exception as e:
                    logger.error(f"Failed to convert POS transaction to universal format: {e}")
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
            self._update_stats(len(raw_transactions), len(processed_results), processing_time)
            
            # Analyze POS-specific metrics
            pos_metrics = self._analyze_pos_metrics(processed_results)
            
            return {
                'transactions': raw_transactions,
                'processed_transactions': [r.processed_transaction for r in processed_results if r.processed_transaction],
                'processing_results': processed_results,
                'processing_enabled': True,
                'total_count': len(raw_transactions),
                'processed_count': len(processed_results),
                'processing_time': processing_time,
                'connector_type': self.connector_type.value,
                'pos_metrics': pos_metrics
            }
            
        except Exception as e:
            logger.error(f"Error in get_transactions_with_processing: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    async def get_transaction_by_id_with_processing(
        self,
        transaction_id: str,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a specific POS transaction by ID with universal processing applied.
        
        Args:
            transaction_id: Transaction identifier
            location_id: Location/store identifier
            
        Returns:
            Dict containing raw and processed transaction data with POS analytics
        """
        start_time = datetime.utcnow()
        
        try:
            # Get raw transaction data
            raw_transaction = await self.pos_connector.get_transaction_by_id(
                transaction_id, location_id
            )
            
            if not self.enable_universal_processing or not self.universal_processor:
                return {
                    'transaction': raw_transaction,
                    'processed_transaction': None,
                    'processing_enabled': False
                }
            
            # Convert to universal transaction format
            universal_tx = self._convert_pos_transaction_to_universal(raw_transaction)
            
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
            
            # Analyze individual transaction
            transaction_insights = {}
            if processing_result.success and processing_result.processed_transaction:
                transaction_insights = self._analyze_single_transaction(processing_result.processed_transaction)
            
            return {
                'transaction': raw_transaction,
                'processed_transaction': processing_result.processed_transaction if processing_result.success else None,
                'processing_result': processing_result,
                'processing_enabled': True,
                'processing_time': processing_time,
                'connector_type': self.connector_type.value,
                'transaction_insights': transaction_insights
            }
            
        except Exception as e:
            logger.error(f"Error in get_transaction_by_id_with_processing: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    async def validate_pos_compliance(
        self,
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate POS transaction for Nigerian retail compliance.
        
        This method applies specific Nigerian retail regulations and consumer
        protection requirements to POS transactions.
        
        Args:
            transaction_data: POS transaction data to validate
            
        Returns:
            Dict with compliance validation results
        """
        try:
            # Convert to universal transaction for validation
            universal_tx = self._convert_pos_transaction_to_universal(transaction_data)
            
            if self.enable_universal_processing and self.universal_processor:
                # Process through universal pipeline for comprehensive validation
                processing_result = await self.universal_processor.process_transaction(
                    universal_tx,
                    self.connector_type
                )
                
                if not processing_result.success:
                    return {
                        'compliant': False,
                        'validation_errors': processing_result.errors,
                        'warnings': processing_result.warnings,
                        'original_data': transaction_data
                    }
                
                # Extract compliance information
                processed_tx = processing_result.processed_transaction
                compliance_info = processed_tx.get_nigerian_compliance_info()
                receipt_validation = self._validate_receipt_completeness(transaction_data)
                
                return {
                    'compliant': processed_tx.is_nigerian_compliant(),
                    'compliance_level': compliance_info['compliance_level'],
                    'regulatory_flags': compliance_info['regulatory_flags'],
                    'receipt_validation': receipt_validation,
                    'consumer_protection_status': self._check_consumer_protection(transaction_data),
                    'fraud_assessment': processed_tx.get_risk_assessment(),
                    'processing_applied': True,
                    'original_data': transaction_data
                }
            else:
                # Basic validation without universal processing
                return {
                    'compliant': True,  # Default assumption
                    'receipt_validation': self._validate_receipt_completeness(transaction_data),
                    'consumer_protection_status': self._check_consumer_protection(transaction_data),
                    'processing_applied': False,
                    'original_data': transaction_data
                }
                
        except Exception as e:
            logger.error(f"Error in validate_pos_compliance: {e}")
            return {
                'compliant': False,
                'error': str(e),
                'original_data': transaction_data
            }
    
    async def analyze_customer_behavior(
        self,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Analyze customer behavior patterns using universal processing insights.
        
        This method provides enhanced customer analytics for retail operations
        by leveraging universal processing customer matching and pattern recognition.
        
        Returns:
            Dict with customer behavior analysis and recommendations
        """
        try:
            # Get customer transactions
            transactions_result = await self.get_transactions_with_processing(
                location_id=location_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            processed_transactions = transactions_result.get('processed_transactions', [])
            
            if not processed_transactions:
                return {
                    'customer_id': customer_id,
                    'analysis_period': f"{start_date} to {end_date}" if start_date and end_date else "recent",
                    'total_transactions': 0,
                    'behavior_insights': {},
                    'recommendations': []
                }
            
            # Filter by customer if specified
            if customer_id:
                customer_transactions = [
                    tx for tx in processed_transactions
                    if tx.enrichment_data.customer_id == customer_id
                ]
            else:
                customer_transactions = processed_transactions
            
            # Analyze behavior patterns
            behavior_analysis = self._analyze_customer_patterns(customer_transactions)
            
            return {
                'customer_id': customer_id or 'all_customers',
                'analysis_period': f"{start_date} to {end_date}" if start_date and end_date else "recent",
                'total_transactions': len(customer_transactions),
                'behavior_insights': behavior_analysis,
                'recommendations': self._generate_customer_recommendations(behavior_analysis),
                'pos_connector': self.connector_type.value
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_customer_behavior: {e}")
            return {
                'customer_id': customer_id,
                'error': str(e),
                'analysis_failed': True
            }
    
    async def generate_retail_analytics_report(
        self,
        location_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 500
    ) -> Dict[str, Any]:
        """
        Generate comprehensive retail analytics report using universal processing insights.
        
        This method provides detailed retail performance metrics enhanced by
        universal processing intelligence.
        
        Returns:
            Dict with comprehensive retail analytics
        """
        try:
            # Default to last 7 days if no date range provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            # Get transactions with universal processing
            transactions_result = await self.get_transactions_with_processing(
                location_id=location_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            processed_transactions = transactions_result.get('processed_transactions', [])
            pos_metrics = transactions_result.get('pos_metrics', {})
            
            if not processed_transactions:
                return {
                    'period': f"{start_date.date()} to {end_date.date()}",
                    'location_id': location_id,
                    'total_transactions': 0,
                    'analytics': {},
                    'message': 'No processed transactions found for the specified period'
                }
            
            # Generate comprehensive analytics
            analytics = {
                'transaction_summary': self._generate_transaction_summary(processed_transactions),
                'compliance_summary': self._generate_compliance_summary(processed_transactions),
                'fraud_analysis': self._generate_fraud_analysis(processed_transactions),
                'customer_insights': self._generate_customer_insights(processed_transactions),
                'payment_analysis': self._generate_payment_analysis(processed_transactions),
                'pos_metrics': pos_metrics,
                'operational_insights': self._generate_operational_insights(processed_transactions)
            }
            
            return {
                'period': f"{start_date.date()} to {end_date.date()}",
                'location_id': location_id or 'all_locations',
                'total_transactions': len(processed_transactions),
                'connector_type': self.connector_type.value,
                'analytics': analytics,
                'recommendations': self._generate_retail_recommendations(analytics)
            }
            
        except Exception as e:
            logger.error(f"Error generating retail analytics report: {e}")
            return {
                'period': f"{start_date.date()} to {end_date.date()}" if start_date and end_date else "unknown",
                'error': str(e),
                'report_failed': True
            }
    
    def _convert_pos_transaction_to_universal(
        self,
        pos_transaction: Dict[str, Any]
    ) -> UniversalTransaction:
        """
        Convert POS transaction data to universal transaction format.
        
        This method maps POS-specific fields to standardized universal transaction fields.
        """
        # Extract common fields with POS-specific mapping
        transaction_id = (
            pos_transaction.get('id') or 
            pos_transaction.get('transaction_id') or 
            pos_transaction.get('payment_id') or
            pos_transaction.get('order_id') or
            'unknown'
        )
        
        amount = float(
            pos_transaction.get('total_money', {}).get('amount', 0) or
            pos_transaction.get('amount_money', {}).get('amount', 0) or
            pos_transaction.get('total', 0) or
            pos_transaction.get('amount', 0) or
            0
        ) / 100.0  # Many POS systems store amounts in cents
        
        # Parse transaction date
        created_at = (
            pos_transaction.get('created_at') or 
            pos_transaction.get('transaction_date') or 
            pos_transaction.get('processed_at')
        )
        
        if isinstance(created_at, str):
            try:
                transaction_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except ValueError:
                transaction_date = datetime.utcnow()
        elif isinstance(created_at, datetime):
            transaction_date = created_at
        else:
            transaction_date = datetime.utcnow()
        
        description = (
            pos_transaction.get('note') or
            pos_transaction.get('description') or
            pos_transaction.get('receipt_number') or
            f"POS Sale {transaction_id}"
        )
        
        # Extract currency
        currency = 'NGN'  # Default for Nigerian retail
        if 'total_money' in pos_transaction:
            currency = pos_transaction['total_money'].get('currency', 'NGN')
        elif 'amount_money' in pos_transaction:
            currency = pos_transaction['amount_money'].get('currency', 'NGN')
        elif 'currency' in pos_transaction:
            currency = pos_transaction.get('currency', 'NGN')
        
        # Create universal transaction
        return UniversalTransaction(
            id=str(transaction_id),
            amount=amount,
            currency=currency,
            date=transaction_date,
            description=description,
            
            # POS-specific fields
            account_number=pos_transaction.get('customer_id'),
            reference=pos_transaction.get('receipt_number') or pos_transaction.get('order_number'),
            category='retail',
            
            # POS metadata
            pos_metadata={
                'receipt_number': pos_transaction.get('receipt_number'),
                'terminal_id': pos_transaction.get('device', {}).get('id') or pos_transaction.get('terminal_id'),
                'location_id': pos_transaction.get('location_id'),
                'cashier_id': pos_transaction.get('team_member_id') or pos_transaction.get('employee_id'),
                'payment_methods': pos_transaction.get('tenders', []) or [pos_transaction.get('payment_method', {})],
                'line_items': pos_transaction.get('itemizations', []) or pos_transaction.get('line_items', []),
                'tax_money': pos_transaction.get('tax_money', {}),
                'tip_money': pos_transaction.get('tip_money', {}),
                'discount_money': pos_transaction.get('discount_money', {}),
                'processing_fees': pos_transaction.get('processing_fee_money', {}),
                'refunds': pos_transaction.get('refunds', []),
                'order_source': pos_transaction.get('source', {}).get('name', 'POS'),
                'device_details': pos_transaction.get('device', {}),
                'customer_details': pos_transaction.get('customer', {})
            },
            
            # Source information
            source_system=self.connector_type.value,
            source_connector='pos_adapter',
            raw_data=pos_transaction
        )
    
    def _validate_receipt_completeness(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that POS transaction has complete receipt information."""
        required_fields = ['receipt_number', 'amount', 'date', 'payment_method']
        missing_fields = []
        
        for field in required_fields:
            if not transaction_data.get(field):
                missing_fields.append(field)
        
        # Check for line items
        has_line_items = bool(
            transaction_data.get('itemizations') or 
            transaction_data.get('line_items') or
            transaction_data.get('items')
        )
        
        return {
            'complete': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'has_line_items': has_line_items,
            'receipt_compliant': len(missing_fields) == 0 and has_line_items
        }
    
    def _check_consumer_protection(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check Nigerian consumer protection compliance."""
        protections = {
            'receipt_provided': bool(transaction_data.get('receipt_number')),
            'refund_policy_available': bool(transaction_data.get('refund_policy')),
            'customer_rights_disclosed': bool(transaction_data.get('consumer_rights')),
            'transaction_traceable': bool(transaction_data.get('id') or transaction_data.get('transaction_id'))
        }
        
        compliance_score = sum(protections.values()) / len(protections)
        
        return {
            'protections': protections,
            'compliance_score': compliance_score,
            'compliant': compliance_score >= 0.75  # At least 3 out of 4 protections
        }
    
    def _analyze_pos_metrics(self, processing_results: List[Any]) -> Dict[str, Any]:
        """Analyze POS-specific metrics from processing results."""
        if not processing_results:
            return {}
        
        fraud_detected = sum(1 for r in processing_results 
                            if r.processed_transaction and r.processed_transaction.requires_manual_review())
        
        receipts_complete = sum(1 for r in processing_results
                               if r.processed_transaction and 
                               r.processed_transaction.enrichment_data.pos_terminal_id)
        
        customer_matched = sum(1 for r in processing_results
                              if r.processed_transaction and 
                              r.processed_transaction.enrichment_data.customer_matched)
        
        return {
            'fraud_detection_rate': fraud_detected / len(processing_results) if processing_results else 0,
            'receipt_completeness_rate': receipts_complete / len(processing_results) if processing_results else 0,
            'customer_match_rate': customer_matched / len(processing_results) if processing_results else 0,
            'total_processed': len(processing_results)
        }
    
    def _analyze_single_transaction(self, processed_tx: UniversalProcessedTransaction) -> Dict[str, Any]:
        """Analyze insights for a single processed transaction."""
        return {
            'risk_level': processed_tx.processing_metadata.risk_level.value,
            'confidence_score': processed_tx.processing_metadata.confidence_score,
            'customer_matched': processed_tx.enrichment_data.customer_matched,
            'receipt_complete': bool(processed_tx.enrichment_data.pos_terminal_id),
            'compliance_status': processed_tx.enrichment_data.nigerian_compliance_level,
            'requires_review': processed_tx.requires_manual_review(),
            'processing_notes': processed_tx.processing_metadata.processing_notes
        }
    
    def _analyze_customer_patterns(self, transactions: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Analyze customer behavior patterns from processed transactions."""
        if not transactions:
            return {}
        
        # Calculate basic metrics
        total_amount = sum(tx.amount for tx in transactions)
        avg_transaction = total_amount / len(transactions) if transactions else 0
        
        # Analyze payment methods
        payment_methods = {}
        for tx in transactions:
            payment_method = tx.original_transaction.pos_metadata.get('payment_methods', [])
            if payment_method:
                method_name = payment_method[0].get('type', 'unknown') if isinstance(payment_method, list) else 'unknown'
                payment_methods[method_name] = payment_methods.get(method_name, 0) + 1
        
        # Analyze timing patterns
        hour_distribution = {}
        for tx in transactions:
            hour = tx.date.hour
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
        
        return {
            'transaction_count': len(transactions),
            'total_spent': float(total_amount),
            'average_transaction': float(avg_transaction),
            'payment_method_distribution': payment_methods,
            'hour_distribution': hour_distribution,
            'customer_loyalty_score': min(len(transactions) / 10.0, 1.0)  # Simple loyalty metric
        }
    
    def _generate_customer_recommendations(self, behavior_analysis: Dict[str, Any]) -> List[str]:
        """Generate customer-focused recommendations based on behavior analysis."""
        recommendations = []
        
        avg_transaction = behavior_analysis.get('average_transaction', 0)
        transaction_count = behavior_analysis.get('transaction_count', 0)
        loyalty_score = behavior_analysis.get('customer_loyalty_score', 0)
        
        if avg_transaction > 50000:  # ₦50,000
            recommendations.append("High-value customer: Consider VIP treatment and exclusive offers")
        
        if transaction_count > 10:
            recommendations.append("Frequent customer: Implement loyalty program benefits")
        
        if loyalty_score > 0.7:
            recommendations.append("Loyal customer: Focus on retention and upselling opportunities")
        
        return recommendations
    
    def _generate_transaction_summary(self, transactions: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate transaction summary analytics."""
        if not transactions:
            return {}
        
        total_amount = sum(tx.amount for tx in transactions)
        valid_transactions = sum(1 for tx in transactions if tx.is_valid())
        
        return {
            'total_transactions': len(transactions),
            'total_amount': float(total_amount),
            'average_transaction': float(total_amount / len(transactions)),
            'valid_transaction_rate': valid_transactions / len(transactions),
            'currency': transactions[0].currency if transactions else 'NGN'
        }
    
    def _generate_compliance_summary(self, transactions: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate compliance summary for Nigerian retail regulations."""
        if not transactions:
            return {}
        
        compliant_count = sum(1 for tx in transactions if tx.is_nigerian_compliant())
        receipt_complete = sum(1 for tx in transactions if tx.enrichment_data.pos_terminal_id)
        
        return {
            'compliance_rate': compliant_count / len(transactions),
            'receipt_completeness_rate': receipt_complete / len(transactions),
            'total_assessed': len(transactions)
        }
    
    def _generate_fraud_analysis(self, transactions: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate fraud analysis summary."""
        if not transactions:
            return {}
        
        high_risk = sum(1 for tx in transactions if tx.processing_metadata.risk_level.value in ['high', 'critical'])
        requires_review = sum(1 for tx in transactions if tx.requires_manual_review())
        
        return {
            'high_risk_transactions': high_risk,
            'manual_review_required': requires_review,
            'fraud_detection_rate': high_risk / len(transactions),
            'overall_risk_level': 'low' if high_risk / len(transactions) < 0.05 else 'medium' if high_risk / len(transactions) < 0.15 else 'high'
        }
    
    def _generate_customer_insights(self, transactions: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate customer insights from processed transactions."""
        if not transactions:
            return {}
        
        matched_customers = sum(1 for tx in transactions if tx.enrichment_data.customer_matched)
        unique_customers = len(set(tx.enrichment_data.customer_id for tx in transactions if tx.enrichment_data.customer_id))
        
        return {
            'customer_match_rate': matched_customers / len(transactions),
            'unique_customers': unique_customers,
            'repeat_customer_rate': (len(transactions) - unique_customers) / len(transactions) if unique_customers > 0 else 0
        }
    
    def _generate_payment_analysis(self, transactions: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate payment method analysis."""
        if not transactions:
            return {}
        
        payment_methods = {}
        for tx in transactions:
            methods = tx.original_transaction.pos_metadata.get('payment_methods', [])
            if methods:
                method = methods[0].get('type', 'unknown') if isinstance(methods, list) else 'unknown'
                payment_methods[method] = payment_methods.get(method, 0) + 1
        
        return {
            'payment_method_distribution': payment_methods,
            'cash_transactions': payment_methods.get('cash', 0),
            'card_transactions': payment_methods.get('card', 0) + payment_methods.get('credit_card', 0),
            'digital_transactions': payment_methods.get('digital', 0) + payment_methods.get('mobile', 0)
        }
    
    def _generate_operational_insights(self, transactions: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate operational insights for retail management."""
        if not transactions:
            return {}
        
        # Analyze transaction timing
        hour_distribution = {}
        for tx in transactions:
            hour = tx.date.hour
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
        
        peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else 12
        
        return {
            'peak_hour': peak_hour,
            'hourly_distribution': hour_distribution,
            'average_processing_time': sum(tx.processing_metadata.processing_duration for tx in transactions) / len(transactions)
        }
    
    def _generate_retail_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations for retail operations."""
        recommendations = []
        
        transaction_summary = analytics.get('transaction_summary', {})
        compliance_summary = analytics.get('compliance_summary', {})
        fraud_analysis = analytics.get('fraud_analysis', {})
        
        # Compliance recommendations
        compliance_rate = compliance_summary.get('compliance_rate', 0)
        if compliance_rate < 0.9:
            recommendations.append("Improve Nigerian retail compliance - rate below 90%")
        
        # Fraud recommendations
        fraud_rate = fraud_analysis.get('fraud_detection_rate', 0)
        if fraud_rate > 0.05:
            recommendations.append("High fraud detection rate - review security procedures")
        
        # Operational recommendations
        avg_transaction = transaction_summary.get('average_transaction', 0)
        if avg_transaction < 5000:  # ₦5,000
            recommendations.append("Low average transaction value - consider upselling strategies")
        
        return recommendations
    
    def _update_stats(self, total_count: int, processed_count: int, processing_time: float):
        """Update adapter statistics."""
        self.stats['total_transactions'] += total_count
        self.stats['universal_processed'] += processed_count
        
        # Update average processing time
        if self.stats['total_transactions'] > 0:
            total_time = self.stats['average_processing_time'] * (self.stats['total_transactions'] - total_count)
            total_time += processing_time
            self.stats['average_processing_time'] = total_time / self.stats['total_transactions']
    
    # Delegate other methods to original connector
    async def test_connection(self):
        """Delegate to original connector."""
        return await self.pos_connector.test_connection()
    
    async def authenticate(self):
        """Delegate to original connector."""
        return await self.pos_connector.authenticate()
    
    async def get_locations(self):
        """Delegate to original connector."""
        return await self.pos_connector.get_locations()
    
    async def get_inventory_items(self, location_id: Optional[str] = None):
        """Delegate to original connector."""
        return await self.pos_connector.get_inventory_items(location_id)
    
    async def process_webhook(self, webhook_data: Dict[str, Any], signature: str):
        """Delegate to original connector."""
        return await self.pos_connector.process_webhook(webhook_data, signature)
    
    async def disconnect(self):
        """Delegate to original connector."""
        return await self.pos_connector.disconnect()
    
    def is_connected(self) -> bool:
        """Delegate to original connector."""
        return self.pos_connector.is_connected()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get enhanced connection status including adapter statistics."""
        base_status = self.pos_connector.get_connection_status()
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


def create_pos_adapter(
    pos_connector: BasePOSConnector,
    connector_type: ConnectorType,
    enable_universal_processing: bool = True
) -> POSConnectorAdapter:
    """
    Factory function to create a POS connector adapter.
    
    Args:
        pos_connector: Existing POS connector instance
        connector_type: Type of POS connector
        enable_universal_processing: Whether to enable universal processing
        
    Returns:
        POSConnectorAdapter instance
    """
    return POSConnectorAdapter(
        pos_connector=pos_connector,
        connector_type=connector_type,
        enable_universal_processing=enable_universal_processing
    )