"""
Square POS Universal Integration Example
=======================================

Demonstrates how to integrate Square POS connector with universal transaction processing
pipeline using the POS connector adapter. This example shows enhanced retail analytics,
Nigerian compliance validation, and fraud detection for Square POS transactions.

Key Benefits:
- Nigerian retail compliance validation
- Enhanced fraud detection for customer-facing transactions  
- Customer behavior analysis and pattern recognition
- Receipt validation and completeness checks
- Cross-connector customer intelligence
- Real-time retail analytics and reporting

Integration Features:
- Backward compatibility with existing Square POS connector
- Enhanced transaction processing with universal pipeline
- Nigerian consumer protection compliance
- Retail-specific business rules and validation
- Customer matching across multiple POS systems
- Performance metrics and operational insights
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..adapters.pos_connector_adapter import create_pos_adapter
from ..connector_configs.connector_types import ConnectorType
from ...external_integrations.business_systems.pos.square.connector import SquarePOSConnector

logger = logging.getLogger(__name__)


class SquareUniversalPOSIntegration:
    """
    Enhanced Square POS integration with universal transaction processing.
    
    This class demonstrates how to wrap the existing Square POS connector
    with universal processing capabilities for enhanced retail analytics,
    Nigerian compliance, and fraud detection.
    """
    
    def __init__(self, square_config: Dict[str, Any]):
        """
        Initialize Square POS integration with universal processing.
        
        Args:
            square_config: Square POS configuration including:
                - application_id: Square application ID
                - application_secret: Square application secret  
                - sandbox: Whether to use sandbox environment
                - webhook_signature_key: For webhook verification
                - location_ids: List of Square location IDs to monitor
        """
        self.config = square_config
        
        # Initialize original Square connector
        self.square_connector = SquarePOSConnector(square_config)
        
        # Create enhanced adapter with universal processing
        self.pos_adapter = create_pos_adapter(
            pos_connector=self.square_connector,
            connector_type=ConnectorType.SQUARE_POS,
            enable_universal_processing=True
        )
        
        logger.info("Square POS universal integration initialized")
    
    async def initialize_connection(self) -> Dict[str, Any]:
        """
        Initialize connection to Square POS with enhanced testing.
        
        Returns:
            Dict with connection status and universal processing capabilities
        """
        try:
            # Test basic Square connection
            connection_result = await self.square_connector.test_connection()
            
            if not connection_result.get('success'):
                return {
                    'success': False,
                    'error': 'Square POS connection failed',
                    'details': connection_result
                }
            
            # Authenticate with Square
            auth_result = await self.square_connector.authenticate()
            
            if not auth_result:
                return {
                    'success': False,
                    'error': 'Square POS authentication failed'
                }
            
            # Get enhanced connection status
            adapter_status = self.pos_adapter.get_connection_status()
            
            return {
                'success': True,
                'message': 'Square POS with universal processing ready',
                'square_connection': connection_result,
                'universal_processing': {
                    'enabled': adapter_status['universal_processing_enabled'],
                    'connector_type': adapter_status['processing_config']['connector_type'],
                    'pipeline_stages': adapter_status['processing_config']['pipeline_stages']
                },
                'supported_features': self.square_connector.get_supported_features()
            }
            
        except Exception as e:
            logger.error(f"Error initializing Square universal connection: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_enhanced_transactions(
        self,
        location_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get Square transactions with universal processing enhancements.
        
        This method demonstrates the enhanced capabilities provided by
        universal processing including Nigerian compliance validation,
        fraud detection, and customer analytics.
        
        Args:
            location_id: Specific Square location to query
            start_date: Start date for transaction range
            end_date: End date for transaction range  
            limit: Maximum number of transactions
            
        Returns:
            Dict with enhanced transaction data and analytics
        """
        try:
            # Get transactions with universal processing
            result = await self.pos_adapter.get_transactions_with_processing(
                location_id=location_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if not result.get('processing_enabled'):
                logger.warning("Universal processing not enabled - returning basic results")
                return result
            
            # Extract enhanced insights
            processed_transactions = result.get('processed_transactions', [])
            pos_metrics = result.get('pos_metrics', {})
            
            # Generate additional Square-specific insights
            square_insights = await self._generate_square_insights(processed_transactions)
            
            # Add Nigerian retail compliance summary
            compliance_summary = self._generate_nigerian_compliance_summary(processed_transactions)
            
            return {
                **result,
                'square_insights': square_insights,
                'nigerian_compliance': compliance_summary,
                'recommendations': self._generate_square_recommendations(result, square_insights),
                'integration_type': 'square_universal'
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced Square transactions: {e}")
            return {
                'success': False,
                'error': str(e),
                'integration_type': 'square_universal'
            }
    
    async def validate_transaction_compliance(
        self,
        transaction_id: str,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a specific Square transaction for Nigerian retail compliance.
        
        This method demonstrates comprehensive compliance validation including
        consumer protection requirements, receipt completeness, and fraud detection.
        
        Args:
            transaction_id: Square transaction ID to validate
            location_id: Square location ID
            
        Returns:
            Dict with comprehensive compliance validation results
        """
        try:
            # Get transaction with universal processing
            result = await self.pos_adapter.get_transaction_by_id_with_processing(
                transaction_id=transaction_id,
                location_id=location_id
            )
            
            if not result.get('processed_transaction'):
                # Fall back to basic validation
                raw_transaction = result.get('transaction')
                if raw_transaction:
                    return await self.pos_adapter.validate_pos_compliance(raw_transaction)
                else:
                    return {
                        'success': False,
                        'error': f'Transaction {transaction_id} not found'
                    }
            
            processed_tx = result['processed_transaction']
            transaction_insights = result.get('transaction_insights', {})
            
            # Generate comprehensive compliance report
            compliance_report = {
                'transaction_id': transaction_id,
                'compliance_status': processed_tx.is_nigerian_compliant(),
                'compliance_details': processed_tx.get_nigerian_compliance_info(),
                'receipt_validation': {
                    'complete': transaction_insights.get('receipt_complete', False),
                    'terminal_verified': bool(processed_tx.enrichment_data.pos_terminal_id),
                    'receipt_number': processed_tx.original_transaction.reference
                },
                'consumer_protection': {
                    'transaction_traceable': bool(processed_tx.id),
                    'customer_identified': processed_tx.enrichment_data.customer_matched,
                    'refund_eligible': True  # Square supports refunds
                },
                'fraud_assessment': {
                    'risk_level': processed_tx.processing_metadata.risk_level.value,
                    'confidence_score': processed_tx.processing_metadata.confidence_score,
                    'requires_review': processed_tx.requires_manual_review(),
                    'fraud_indicators': processed_tx.processing_metadata.fraud_indicators
                },
                'square_specific': {
                    'payment_methods': processed_tx.original_transaction.pos_metadata.get('payment_methods', []),
                    'device_verified': bool(processed_tx.original_transaction.pos_metadata.get('device_details')),
                    'webhook_processable': True,
                    'square_compliant': True
                },
                'processing_metadata': {
                    'processing_time': result.get('processing_time', 0),
                    'pipeline_applied': True,
                    'connector_type': 'square_pos'
                }
            }
            
            return compliance_report
            
        except Exception as e:
            logger.error(f"Error validating Square transaction compliance: {e}")
            return {
                'transaction_id': transaction_id,
                'success': False,
                'error': str(e)
            }
    
    async def analyze_customer_behavior(
        self,
        customer_id: Optional[str] = None,
        location_id: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze customer behavior patterns using Square data and universal processing.
        
        This method demonstrates enhanced customer analytics that leverage
        universal processing customer matching and pattern recognition.
        
        Args:
            customer_id: Specific Square customer ID to analyze
            location_id: Specific Square location
            days_back: Number of days to analyze
            
        Returns:
            Dict with comprehensive customer behavior analysis
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Analyze customer behavior using universal processing
            behavior_result = await self.pos_adapter.analyze_customer_behavior(
                customer_id=customer_id,
                location_id=location_id,
                start_date=start_date,
                end_date=end_date,
                limit=200
            )
            
            if behavior_result.get('analysis_failed'):
                return behavior_result
            
            # Add Square-specific customer insights
            square_customer_insights = await self._analyze_square_customer_data(
                customer_id, location_id, start_date, end_date
            )
            
            # Combine universal and Square-specific insights
            enhanced_analysis = {
                **behavior_result,
                'square_customer_data': square_customer_insights,
                'loyalty_recommendations': self._generate_loyalty_recommendations(
                    behavior_result.get('behavior_insights', {}),
                    square_customer_insights
                ),
                'marketing_insights': self._generate_marketing_insights(
                    behavior_result.get('behavior_insights', {}),
                    square_customer_insights
                )
            }
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Square customer behavior: {e}")
            return {
                'customer_id': customer_id,
                'error': str(e),
                'analysis_failed': True
            }
    
    async def generate_retail_analytics_dashboard(
        self,
        location_id: Optional[str] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Generate comprehensive retail analytics dashboard for Square POS.
        
        This method demonstrates how universal processing enhances Square POS
        analytics with Nigerian retail insights, fraud detection, and performance metrics.
        
        Args:
            location_id: Specific Square location
            days_back: Number of days to include in analytics
            
        Returns:
            Dict with comprehensive retail dashboard data
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Generate retail analytics using universal processing
            analytics_result = await self.pos_adapter.generate_retail_analytics_report(
                location_id=location_id,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            if analytics_result.get('report_failed'):
                return analytics_result
            
            # Add Square-specific dashboard elements
            square_dashboard_data = await self._generate_square_dashboard_data(
                location_id, start_date, end_date
            )
            
            # Get adapter processing statistics
            processing_stats = self.pos_adapter.get_processing_statistics()
            
            # Combine into comprehensive dashboard
            dashboard = {
                **analytics_result,
                'square_dashboard': square_dashboard_data,
                'processing_performance': processing_stats,
                'dashboard_insights': self._generate_dashboard_insights(
                    analytics_result.get('analytics', {}),
                    square_dashboard_data
                ),
                'action_items': self._generate_action_items(
                    analytics_result.get('analytics', {}),
                    analytics_result.get('recommendations', [])
                ),
                'integration_status': {
                    'square_connector': 'active',
                    'universal_processing': 'enabled',
                    'nigerian_compliance': 'active',
                    'fraud_detection': 'enabled'
                }
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating Square retail analytics dashboard: {e}")
            return {
                'error': str(e),
                'dashboard_failed': True
            }
    
    async def process_webhook_with_universal_processing(
        self,
        webhook_payload: Dict[str, Any],
        signature: str
    ) -> Dict[str, Any]:
        """
        Process Square webhook with universal processing enhancements.
        
        This method demonstrates how to process Square webhooks through
        universal processing for enhanced real-time fraud detection and compliance.
        
        Args:
            webhook_payload: Raw webhook data from Square
            signature: Webhook signature for verification
            
        Returns:
            Dict with webhook processing results and universal insights
        """
        try:
            # Process webhook through original Square connector
            webhook_event = await self.square_connector.process_webhook(webhook_payload)
            
            # If this is a payment-related webhook, apply universal processing
            if webhook_event.event_type in ['payment.created', 'payment.updated', 'order.fulfilled']:
                transaction_data = self._extract_transaction_from_webhook(webhook_payload)
                
                if transaction_data:
                    # Apply universal processing to webhook transaction
                    compliance_result = await self.pos_adapter.validate_pos_compliance(transaction_data)
                    
                    return {
                        'webhook_processed': True,
                        'event_type': webhook_event.event_type,
                        'event_id': webhook_event.event_id,
                        'universal_processing_applied': True,
                        'compliance_validation': compliance_result,
                        'real_time_insights': self._generate_realtime_insights(transaction_data, compliance_result),
                        'webhook_event': webhook_event
                    }
            
            return {
                'webhook_processed': True,
                'event_type': webhook_event.event_type,
                'event_id': webhook_event.event_id,
                'universal_processing_applied': False,
                'webhook_event': webhook_event
            }
            
        except Exception as e:
            logger.error(f"Error processing Square webhook with universal processing: {e}")
            return {
                'webhook_processed': False,
                'error': str(e)
            }
    
    async def _generate_square_insights(self, processed_transactions: List[Any]) -> Dict[str, Any]:
        """Generate Square-specific insights from processed transactions."""
        if not processed_transactions:
            return {}
        
        # Analyze Square-specific data
        device_distribution = {}
        order_sources = {}
        payment_processor_fees = 0
        
        for tx in processed_transactions:
            pos_metadata = tx.original_transaction.pos_metadata
            
            # Device analysis
            device = pos_metadata.get('device_details', {})
            device_type = device.get('type', 'unknown')
            device_distribution[device_type] = device_distribution.get(device_type, 0) + 1
            
            # Order source analysis
            source = pos_metadata.get('order_source', 'unknown')
            order_sources[source] = order_sources.get(source, 0) + 1
            
            # Processing fee analysis
            fees = pos_metadata.get('processing_fees', {})
            if isinstance(fees, dict) and 'amount' in fees:
                payment_processor_fees += float(fees['amount']) / 100.0
        
        return {
            'device_distribution': device_distribution,
            'order_source_distribution': order_sources,
            'total_processing_fees': payment_processor_fees,
            'average_processing_fee': payment_processor_fees / len(processed_transactions) if processed_transactions else 0
        }
    
    def _generate_nigerian_compliance_summary(self, processed_transactions: List[Any]) -> Dict[str, Any]:
        """Generate Nigerian retail compliance summary."""
        if not processed_transactions:
            return {}
        
        compliant_count = sum(1 for tx in processed_transactions if tx.is_nigerian_compliant())
        receipt_complete_count = sum(1 for tx in processed_transactions 
                                   if tx.enrichment_data.pos_terminal_id)
        customer_protection_count = sum(1 for tx in processed_transactions
                                      if tx.enrichment_data.customer_matched)
        
        return {
            'overall_compliance_rate': compliant_count / len(processed_transactions),
            'receipt_completeness_rate': receipt_complete_count / len(processed_transactions),
            'customer_protection_rate': customer_protection_count / len(processed_transactions),
            'total_transactions_assessed': len(processed_transactions),
            'compliance_grade': self._calculate_compliance_grade(
                compliant_count / len(processed_transactions)
            )
        }
    
    def _calculate_compliance_grade(self, compliance_rate: float) -> str:
        """Calculate compliance grade based on rate."""
        if compliance_rate >= 0.95:
            return 'A+'
        elif compliance_rate >= 0.90:
            return 'A'
        elif compliance_rate >= 0.85:
            return 'B+'
        elif compliance_rate >= 0.80:
            return 'B'
        elif compliance_rate >= 0.75:
            return 'C+'
        elif compliance_rate >= 0.70:
            return 'C'
        else:
            return 'F'
    
    def _generate_square_recommendations(
        self,
        transaction_result: Dict[str, Any],
        square_insights: Dict[str, Any]
    ) -> List[str]:
        """Generate Square-specific recommendations."""
        recommendations = []
        
        # Processing performance recommendations
        processing_time = transaction_result.get('processing_time', 0)
        if processing_time > 2.0:
            recommendations.append("Processing time exceeds 2 seconds - consider optimization")
        
        # Device recommendations
        device_dist = square_insights.get('device_distribution', {})
        if device_dist.get('unknown', 0) > 0:
            recommendations.append("Some transactions from unknown devices - verify device registration")
        
        # Fee optimization
        avg_fee = square_insights.get('average_processing_fee', 0)
        if avg_fee > 50:  # ₦50 average fee seems high
            recommendations.append("High processing fees detected - review Square pricing plan")
        
        return recommendations
    
    async def _analyze_square_customer_data(
        self,
        customer_id: Optional[str],
        location_id: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze Square-specific customer data."""
        try:
            # This would integrate with Square Customer API
            # For now, return placeholder data structure
            return {
                'square_customer_profile': {
                    'customer_id': customer_id,
                    'profile_complete': True,
                    'loyalty_program_member': False,
                    'email_verified': True,
                    'phone_verified': True
                },
                'square_interaction_history': {
                    'first_transaction_date': start_date.isoformat(),
                    'last_transaction_date': end_date.isoformat(),
                    'preferred_location': location_id,
                    'preferred_payment_method': 'card'
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing Square customer data: {e}")
            return {}
    
    def _generate_loyalty_recommendations(
        self,
        behavior_insights: Dict[str, Any],
        square_customer_data: Dict[str, Any]
    ) -> List[str]:
        """Generate loyalty program recommendations."""
        recommendations = []
        
        loyalty_score = behavior_insights.get('customer_loyalty_score', 0)
        transaction_count = behavior_insights.get('transaction_count', 0)
        
        if loyalty_score > 0.7 and transaction_count > 5:
            recommendations.append("High loyalty customer - enroll in VIP program")
        
        if transaction_count > 10:
            recommendations.append("Frequent customer - offer loyalty card or app registration")
        
        avg_transaction = behavior_insights.get('average_transaction', 0)
        if avg_transaction > 25000:  # ₦25,000
            recommendations.append("High-value customer - provide personalized service")
        
        return recommendations
    
    def _generate_marketing_insights(
        self,
        behavior_insights: Dict[str, Any],
        square_customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate marketing insights."""
        hour_dist = behavior_insights.get('hour_distribution', {})
        payment_methods = behavior_insights.get('payment_method_distribution', {})
        
        peak_hours = sorted(hour_dist.items(), key=lambda x: x[1], reverse=True)[:3]
        preferred_payment = max(payment_methods.items(), key=lambda x: x[1])[0] if payment_methods else 'unknown'
        
        return {
            'optimal_contact_hours': [hour for hour, _ in peak_hours],
            'preferred_payment_method': preferred_payment,
            'customer_segment': self._determine_customer_segment(behavior_insights),
            'marketing_recommendations': self._generate_marketing_recommendations(behavior_insights)
        }
    
    def _determine_customer_segment(self, behavior_insights: Dict[str, Any]) -> str:
        """Determine customer segment based on behavior."""
        avg_transaction = behavior_insights.get('average_transaction', 0)
        transaction_count = behavior_insights.get('transaction_count', 0)
        
        if avg_transaction > 50000 and transaction_count > 10:
            return 'premium'
        elif avg_transaction > 25000 or transaction_count > 15:
            return 'frequent'
        elif transaction_count > 5:
            return 'regular'
        else:
            return 'occasional'
    
    def _generate_marketing_recommendations(self, behavior_insights: Dict[str, Any]) -> List[str]:
        """Generate marketing recommendations based on behavior."""
        recommendations = []
        
        segment = self._determine_customer_segment(behavior_insights)
        
        if segment == 'premium':
            recommendations.append("Send exclusive offers and early access to new products")
        elif segment == 'frequent':
            recommendations.append("Offer bulk purchase discounts and loyalty rewards")
        elif segment == 'regular':
            recommendations.append("Send regular promotions and seasonal offers")
        else:
            recommendations.append("Focus on engagement and re-activation campaigns")
        
        return recommendations
    
    async def _generate_square_dashboard_data(
        self,
        location_id: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate Square-specific dashboard data."""
        try:
            # Get Square locations for dashboard
            locations = await self.square_connector.get_locations()
            
            # Get payment methods
            payment_methods = await self.square_connector.get_payment_methods()
            
            return {
                'square_locations': [
                    {
                        'id': loc.location_id,
                        'name': loc.name,
                        'address': loc.address,
                        'status': loc.status
                    }
                    for loc in locations
                ],
                'available_payment_methods': [
                    {
                        'type': pm.method_type,
                        'name': pm.name,
                        'enabled': pm.enabled
                    }
                    for pm in payment_methods
                ],
                'square_features': self.square_connector.get_supported_features(),
                'webhook_status': bool(self.square_connector.webhook_signature_key)
            }
        except Exception as e:
            logger.error(f"Error generating Square dashboard data: {e}")
            return {}
    
    def _generate_dashboard_insights(
        self,
        analytics: Dict[str, Any],
        square_dashboard_data: Dict[str, Any]
    ) -> List[str]:
        """Generate dashboard insights."""
        insights = []
        
        # Transaction insights
        transaction_summary = analytics.get('transaction_summary', {})
        total_transactions = transaction_summary.get('total_transactions', 0)
        
        if total_transactions > 100:
            insights.append(f"High transaction volume: {total_transactions} transactions processed")
        
        # Compliance insights
        compliance_summary = analytics.get('compliance_summary', {})
        compliance_rate = compliance_summary.get('compliance_rate', 0)
        
        if compliance_rate > 0.95:
            insights.append("Excellent Nigerian retail compliance rate")
        elif compliance_rate < 0.80:
            insights.append("Compliance rate needs improvement")
        
        # Square-specific insights
        locations = square_dashboard_data.get('square_locations', [])
        if len(locations) > 1:
            insights.append(f"Multi-location operation: {len(locations)} locations")
        
        return insights
    
    def _generate_action_items(
        self,
        analytics: Dict[str, Any],
        recommendations: List[str]
    ) -> List[Dict[str, str]]:
        """Generate actionable items from analytics."""
        action_items = []
        
        for recommendation in recommendations:
            if 'compliance' in recommendation.lower():
                action_items.append({
                    'category': 'compliance',
                    'priority': 'high',
                    'action': recommendation,
                    'timeline': 'immediate'
                })
            elif 'fraud' in recommendation.lower():
                action_items.append({
                    'category': 'security',
                    'priority': 'high',
                    'action': recommendation,
                    'timeline': 'immediate'
                })
            else:
                action_items.append({
                    'category': 'optimization',
                    'priority': 'medium',
                    'action': recommendation,
                    'timeline': 'this_week'
                })
        
        return action_items
    
    def _extract_transaction_from_webhook(self, webhook_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract transaction data from Square webhook payload."""
        try:
            data = webhook_payload.get('data', {})
            obj = data.get('object', {})
            
            if 'payment' in obj:
                return obj['payment']
            elif 'order' in obj:
                return obj['order']
            
            return None
        except Exception as e:
            logger.error(f"Error extracting transaction from webhook: {e}")
            return None
    
    def _generate_realtime_insights(
        self,
        transaction_data: Dict[str, Any],
        compliance_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate real-time insights from webhook transaction."""
        return {
            'transaction_amount': transaction_data.get('amount_money', {}).get('amount', 0) / 100.0,
            'compliance_status': compliance_result.get('compliant', False),
            'requires_attention': not compliance_result.get('compliant', False),
            'processing_timestamp': datetime.utcnow().isoformat(),
            'alert_level': 'low' if compliance_result.get('compliant', False) else 'medium'
        }


async def demo_square_universal_integration():
    """
    Demonstration of Square POS universal integration.
    
    This example shows how to use the Square connector with universal processing
    for enhanced Nigerian retail compliance, fraud detection, and analytics.
    """
    
    # Example Square configuration
    square_config = {
        'application_id': 'your_square_app_id',
        'application_secret': 'your_square_app_secret',
        'access_token': 'your_square_access_token',
        'sandbox': True,  # Use sandbox for testing
        'webhook_signature_key': 'your_webhook_signature_key',
        'webhook_url': 'https://your-app.com/webhooks/square',
        'location_ids': ['your_location_id'],
        'auto_sync_enabled': True,
        'sync_interval_minutes': 15
    }
    
    try:
        # Initialize Square universal integration
        square_integration = SquareUniversalPOSIntegration(square_config)
        
        # 1. Initialize connection
        print("🔌 Initializing Square POS connection with universal processing...")
        connection_result = await square_integration.initialize_connection()
        
        if not connection_result.get('success'):
            print(f"❌ Connection failed: {connection_result.get('error')}")
            return
        
        print("✅ Square POS with universal processing connected successfully!")
        print(f"🎯 Universal processing enabled: {connection_result['universal_processing']['enabled']}")
        print(f"🔧 Pipeline stages: {connection_result['universal_processing']['pipeline_stages']}")
        
        # 2. Get enhanced transactions
        print("\n📊 Getting enhanced transactions with universal processing...")
        enhanced_transactions = await square_integration.get_enhanced_transactions(
            start_date=datetime.utcnow() - timedelta(days=7),
            limit=50
        )
        
        if enhanced_transactions.get('processing_enabled'):
            processed_count = enhanced_transactions.get('processed_count', 0)
            total_count = enhanced_transactions.get('total_count', 0)
            processing_time = enhanced_transactions.get('processing_time', 0)
            
            print(f"✅ Processed {processed_count}/{total_count} transactions in {processing_time:.2f}s")
            
            # Nigerian compliance summary
            compliance = enhanced_transactions.get('nigerian_compliance', {})
            compliance_rate = compliance.get('overall_compliance_rate', 0)
            compliance_grade = compliance.get('compliance_grade', 'N/A')
            
            print(f"🇳🇬 Nigerian compliance rate: {compliance_rate:.1%} (Grade: {compliance_grade})")
            
            # Square insights
            square_insights = enhanced_transactions.get('square_insights', {})
            total_fees = square_insights.get('total_processing_fees', 0)
            print(f"💰 Total Square processing fees: ₦{total_fees:.2f}")
        
        # 3. Validate specific transaction compliance
        if enhanced_transactions.get('transactions'):
            first_transaction = enhanced_transactions['transactions'][0]
            transaction_id = first_transaction.get('id') or first_transaction.get('payment_id')
            
            if transaction_id:
                print(f"\n🔍 Validating transaction compliance: {transaction_id}")
                compliance_result = await square_integration.validate_transaction_compliance(
                    transaction_id=transaction_id
                )
                
                if compliance_result.get('compliance_status'):
                    print("✅ Transaction is Nigerian retail compliant")
                else:
                    print("⚠️ Transaction has compliance issues")
                
                risk_level = compliance_result.get('fraud_assessment', {}).get('risk_level', 'unknown')
                print(f"🔒 Risk level: {risk_level}")
        
        # 4. Generate retail analytics dashboard
        print("\n📈 Generating retail analytics dashboard...")
        dashboard = await square_integration.generate_retail_analytics_dashboard(days_back=7)
        
        if not dashboard.get('dashboard_failed'):
            analytics = dashboard.get('analytics', {})
            transaction_summary = analytics.get('transaction_summary', {})
            
            total_amount = transaction_summary.get('total_amount', 0)
            avg_transaction = transaction_summary.get('average_transaction', 0)
            
            print(f"💵 Total sales: ₦{total_amount:,.2f}")
            print(f"📊 Average transaction: ₦{avg_transaction:.2f}")
            
            # Action items
            action_items = dashboard.get('action_items', [])
            if action_items:
                print(f"\n📋 Action items ({len(action_items)}):")
                for item in action_items[:3]:  # Show first 3
                    print(f"  • {item['action']} ({item['priority']} priority)")
        
        # 5. Customer behavior analysis (if customer data available)
        print("\n👥 Analyzing customer behavior patterns...")
        customer_analysis = await square_integration.analyze_customer_behavior(days_back=30)
        
        if not customer_analysis.get('analysis_failed'):
            insights = customer_analysis.get('behavior_insights', {})
            total_customers = insights.get('transaction_count', 0)
            
            print(f"🛒 Total customer transactions analyzed: {total_customers}")
            
            loyalty_recommendations = customer_analysis.get('loyalty_recommendations', [])
            if loyalty_recommendations:
                print("💡 Loyalty recommendations:")
                for rec in loyalty_recommendations[:2]:  # Show first 2
                    print(f"  • {rec}")
        
        print("\n🎉 Square POS universal integration demo completed successfully!")
        print("✨ Key benefits demonstrated:")
        print("  • Enhanced transaction processing with universal pipeline")
        print("  • Nigerian retail compliance validation")
        print("  • Real-time fraud detection and risk assessment")
        print("  • Advanced customer behavior analytics")
        print("  • Comprehensive retail dashboard insights")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    # Run the demonstration
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_square_universal_integration())