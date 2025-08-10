"""
CRM Connector Adapter
====================

Adapter that bridges existing CRM connectors with the universal transaction
processing pipeline. This enables CRM systems to benefit from standardized
processing, Nigerian business compliance, and enhanced deal/opportunity intelligence.

The adapter handles:
- Converting CRM deal/opportunity data to universal transaction format
- Applying business-specific rules and validation for Nigerian companies
- Enhanced lead scoring and opportunity fraud detection
- Nigerian business registration and compliance validation
- Deal pipeline analysis and revenue recognition
- Cross-CRM customer and company intelligence

Supported CRM Systems:
- Salesforce CRM
- HubSpot CRM
- Microsoft Dynamics 365 CRM
- Zoho CRM
- Pipedrive CRM
- Nigerian local CRM systems

Migration Strategy:
Phase 1: Wrap existing CRM connectors with universal processing
Phase 2: Enhanced business intelligence and Nigerian compliance
Phase 3: Cross-CRM opportunity intelligence and pipeline optimization
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import asyncio

from ..connector_configs.connector_types import ConnectorType
from ..connector_configs.processing_config import get_processing_config
from ..processing_stages.stage_definitions import get_default_pipeline_for_connector
from ..models.universal_transaction import UniversalTransaction
from ..models.universal_processed_transaction import UniversalProcessedTransaction
from ...external_integrations.connector_framework.base_crm_connector import BaseCRMConnector

logger = logging.getLogger(__name__)


class CRMConnectorAdapter:
    """
    Adapter that wraps existing CRM connectors to use universal transaction processing.
    
    This adapter provides enhanced capabilities for business transaction processing:
    - Nigerian business compliance validation (CAC registration, TIN validation)
    - Deal pipeline optimization and revenue recognition
    - Enhanced fraud detection for B2B transactions
    - Lead scoring and opportunity intelligence
    - Customer relationship analysis and insights
    - Cross-CRM company and contact matching
    """
    
    def __init__(
        self,
        crm_connector: BaseCRMConnector,
        connector_type: ConnectorType,
        enable_universal_processing: bool = True
    ):
        """
        Initialize the CRM connector adapter.
        
        Args:
            crm_connector: Existing CRM connector instance
            connector_type: Type of CRM connector
            enable_universal_processing: Enable universal processing pipeline
        """
        self.crm_connector = crm_connector
        self.connector_type = connector_type
        self.enable_universal_processing = enable_universal_processing
        
        # Get processing configuration for this CRM connector type
        self.processing_config = get_processing_config(connector_type)
        self.processing_pipeline = get_default_pipeline_for_connector(connector_type)
        
        # Initialize universal processor components (lazy loading)
        self._universal_processor = None
        
        # CRM-specific tracking
        self.stats = {
            'total_deals': 0,
            'universal_processed': 0,
            'direct_processed': 0,
            'fraud_detected': 0,
            'companies_validated': 0,
            'pipeline_analyzed': 0,
            'processing_errors': 0,
            'average_processing_time': 0.0,
            'revenue_forecasted': 0.0
        }
        
        logger.info(f"Initialized CRM adapter for {connector_type.value} with universal processing {'enabled' if enable_universal_processing else 'disabled'}")
    
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
    
    async def get_deals_with_processing(
        self,
        stage_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        amount_range: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Get CRM deals/opportunities with universal processing applied.
        
        This method enhances the original get_deals method by applying
        business-specific validation, fraud detection, and Nigerian compliance checks.
        
        Args:
            stage_filter: Filter by deal stage (e.g., 'closed-won', 'negotiation')
            start_date: Start date for deal range
            end_date: End date for deal range
            limit: Maximum number of deals to return
            offset: Pagination offset
            amount_range: Filter by deal amount (min_amount, max_amount)
            
        Returns:
            Dict containing both raw and processed deal data
        """
        start_time = datetime.utcnow()
        
        try:
            # Build filters for CRM connector
            filters = {}
            if stage_filter:
                filters['stage'] = stage_filter
            if start_date:
                filters['start_date'] = start_date
            if end_date:
                filters['end_date'] = end_date
            if amount_range:
                filters['amount_range'] = amount_range
            
            # Get raw deal data from CRM connector
            raw_deals = await self.crm_connector.get_deals(
                filters=filters,
                limit=limit,
                offset=offset
            )
            
            if not self.enable_universal_processing or not self.universal_processor:
                # Return raw data if universal processing is disabled
                self.stats['direct_processed'] += len(raw_deals)
                return {
                    'deals': raw_deals,
                    'processed_deals': [],
                    'processing_enabled': False,
                    'total_count': len(raw_deals)
                }
            
            # Convert CRM deals to universal transaction format
            universal_transactions = []
            for deal in raw_deals:
                try:
                    universal_tx = self._convert_crm_deal_to_universal(deal)
                    universal_transactions.append(universal_tx)
                except Exception as e:
                    logger.error(f"Failed to convert CRM deal to universal format: {e}")
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
            self._update_stats(len(raw_deals), len(processed_results), processing_time)
            
            # Analyze CRM-specific metrics
            crm_metrics = self._analyze_crm_metrics(processed_results)
            
            return {
                'deals': raw_deals,
                'processed_deals': [r.processed_transaction for r in processed_results if r.processed_transaction],
                'processing_results': processed_results,
                'processing_enabled': True,
                'total_count': len(raw_deals),
                'processed_count': len(processed_results),
                'processing_time': processing_time,
                'connector_type': self.connector_type.value,
                'crm_metrics': crm_metrics
            }
            
        except Exception as e:
            logger.error(f"Error in get_deals_with_processing: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    async def get_deal_by_id_with_processing(
        self,
        deal_id: str
    ) -> Dict[str, Any]:
        """
        Get a specific CRM deal by ID with universal processing applied.
        
        Args:
            deal_id: Deal/opportunity identifier
            
        Returns:
            Dict containing raw and processed deal data with CRM analytics
        """
        start_time = datetime.utcnow()
        
        try:
            # Get raw deal data
            raw_deal = await self.crm_connector.get_deal_by_id(deal_id)
            
            if not self.enable_universal_processing or not self.universal_processor:
                return {
                    'deal': raw_deal,
                    'processed_deal': None,
                    'processing_enabled': False
                }
            
            # Convert to universal transaction format
            universal_tx = self._convert_crm_deal_to_universal(raw_deal)
            
            # Process through universal pipeline
            processing_result = await self.universal_processor.process_transaction(
                universal_tx,
                self.connector_type,
                None,  # No historical context for single deal
                self.processing_config
            )
            
            # Update statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_stats(1, 1 if processing_result.success else 0, processing_time)
            
            # Analyze individual deal
            deal_insights = {}
            if processing_result.success and processing_result.processed_transaction:
                deal_insights = self._analyze_single_deal(processing_result.processed_transaction)
            
            return {
                'deal': raw_deal,
                'processed_deal': processing_result.processed_transaction if processing_result.success else None,
                'processing_result': processing_result,
                'processing_enabled': True,
                'processing_time': processing_time,
                'connector_type': self.connector_type.value,
                'deal_insights': deal_insights
            }
            
        except Exception as e:
            logger.error(f"Error in get_deal_by_id_with_processing: {e}")
            self.stats['processing_errors'] += 1
            raise
    
    async def validate_business_compliance(
        self,
        deal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate CRM deal for Nigerian business compliance.
        
        This method applies specific Nigerian business regulations including
        CAC registration validation, TIN verification, and business licensing.
        
        Args:
            deal_data: CRM deal data to validate
            
        Returns:
            Dict with business compliance validation results
        """
        try:
            # Convert to universal transaction for validation
            universal_tx = self._convert_crm_deal_to_universal(deal_data)
            
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
                        'original_data': deal_data
                    }
                
                # Extract compliance information
                processed_deal = processing_result.processed_transaction
                compliance_info = processed_deal.get_nigerian_compliance_info()
                company_validation = self._validate_company_registration(deal_data)
                
                return {
                    'compliant': processed_deal.is_nigerian_compliant(),
                    'compliance_level': compliance_info['compliance_level'],
                    'regulatory_flags': compliance_info['regulatory_flags'],
                    'company_validation': company_validation,
                    'business_license_status': self._check_business_licensing(deal_data),
                    'fraud_assessment': processed_deal.get_risk_assessment(),
                    'processing_applied': True,
                    'original_data': deal_data
                }
            else:
                # Basic validation without universal processing
                return {
                    'compliant': True,  # Default assumption
                    'company_validation': self._validate_company_registration(deal_data),
                    'business_license_status': self._check_business_licensing(deal_data),
                    'processing_applied': False,
                    'original_data': deal_data
                }
                
        except Exception as e:
            logger.error(f"Error in validate_business_compliance: {e}")
            return {
                'compliant': False,
                'error': str(e),
                'original_data': deal_data
            }
    
    async def analyze_sales_pipeline(
        self,
        team_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 500
    ) -> Dict[str, Any]:
        """
        Analyze sales pipeline using universal processing insights.
        
        This method provides enhanced pipeline analytics for sales operations
        by leveraging universal processing deal intelligence and pattern recognition.
        
        Returns:
            Dict with sales pipeline analysis and recommendations
        """
        try:
            # Get deals with universal processing
            deals_result = await self.get_deals_with_processing(
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            processed_deals = deals_result.get('processed_deals', [])
            
            if not processed_deals:
                return {
                    'analysis_period': f"{start_date} to {end_date}" if start_date and end_date else "recent",
                    'total_deals': 0,
                    'pipeline_insights': {},
                    'recommendations': []
                }
            
            # Filter by team if specified
            if team_filter:
                team_deals = [
                    deal for deal in processed_deals
                    if deal.enrichment_data.sales_team == team_filter
                ]
            else:
                team_deals = processed_deals
            
            # Analyze pipeline patterns
            pipeline_analysis = self._analyze_pipeline_patterns(team_deals)
            
            return {
                'team_filter': team_filter or 'all_teams',
                'analysis_period': f"{start_date} to {end_date}" if start_date and end_date else "recent",
                'total_deals': len(team_deals),
                'pipeline_insights': pipeline_analysis,
                'recommendations': self._generate_pipeline_recommendations(pipeline_analysis),
                'crm_connector': self.connector_type.value
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_sales_pipeline: {e}")
            return {
                'team_filter': team_filter,
                'error': str(e),
                'analysis_failed': True
            }
    
    async def generate_business_analytics_report(
        self,
        report_type: str = 'comprehensive',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate comprehensive business analytics report using universal processing insights.
        
        This method provides detailed business performance metrics enhanced by
        universal processing intelligence.
        
        Args:
            report_type: Type of report ('comprehensive', 'compliance', 'performance')
            start_date: Report start date
            end_date: Report end date
            limit: Maximum deals to analyze
            
        Returns:
            Dict with comprehensive business analytics
        """
        try:
            # Default to last 30 days if no date range provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Get deals with universal processing
            deals_result = await self.get_deals_with_processing(
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            processed_deals = deals_result.get('processed_deals', [])
            crm_metrics = deals_result.get('crm_metrics', {})
            
            if not processed_deals:
                return {
                    'period': f"{start_date.date()} to {end_date.date()}",
                    'report_type': report_type,
                    'total_deals': 0,
                    'analytics': {},
                    'message': 'No processed deals found for the specified period'
                }
            
            # Generate analytics based on report type
            analytics = {}
            
            if report_type in ['comprehensive', 'performance']:
                analytics.update({
                    'deal_summary': self._generate_deal_summary(processed_deals),
                    'revenue_analysis': self._generate_revenue_analysis(processed_deals),
                    'pipeline_performance': self._generate_pipeline_performance(processed_deals),
                    'team_performance': self._generate_team_performance(processed_deals)
                })
            
            if report_type in ['comprehensive', 'compliance']:
                analytics.update({
                    'compliance_summary': self._generate_business_compliance_summary(processed_deals),
                    'risk_analysis': self._generate_business_risk_analysis(processed_deals),
                    'regulatory_insights': self._generate_regulatory_insights(processed_deals)
                })
            
            if report_type == 'comprehensive':
                analytics.update({
                    'crm_metrics': crm_metrics,
                    'customer_insights': self._generate_customer_insights(processed_deals),
                    'market_insights': self._generate_market_insights(processed_deals)
                })
            
            return {
                'period': f"{start_date.date()} to {end_date.date()}",
                'report_type': report_type,
                'total_deals': len(processed_deals),
                'connector_type': self.connector_type.value,
                'analytics': analytics,
                'recommendations': self._generate_business_recommendations(analytics)
            }
            
        except Exception as e:
            logger.error(f"Error generating business analytics report: {e}")
            return {
                'period': f"{start_date.date()} to {end_date.date()}" if start_date and end_date else "unknown",
                'report_type': report_type,
                'error': str(e),
                'report_failed': True
            }
    
    def _convert_crm_deal_to_universal(
        self,
        crm_deal: Dict[str, Any]
    ) -> UniversalTransaction:
        """
        Convert CRM deal data to universal transaction format.
        
        This method maps CRM-specific fields to standardized universal transaction fields.
        """
        # Extract common fields with CRM-specific mapping
        deal_id = (
            crm_deal.get('id') or 
            crm_deal.get('deal_id') or 
            crm_deal.get('opportunity_id') or
            'unknown'
        )
        
        # Parse deal amount
        amount = 0.0
        amount_field = (
            crm_deal.get('amount') or
            crm_deal.get('value') or
            crm_deal.get('deal_value') or
            crm_deal.get('expected_revenue') or
            0
        )
        
        if isinstance(amount_field, (int, float)):
            amount = float(amount_field)
        elif isinstance(amount_field, str):
            try:
                amount = float(amount_field.replace(',', '').replace('$', '').replace('₦', ''))
            except ValueError:
                amount = 0.0
        
        # Parse deal close date
        close_date = (
            crm_deal.get('close_date') or 
            crm_deal.get('expected_close_date') or 
            crm_deal.get('deal_date') or
            crm_deal.get('created_date')
        )
        
        if isinstance(close_date, str):
            try:
                transaction_date = datetime.fromisoformat(close_date.replace('Z', '+00:00'))
            except ValueError:
                transaction_date = datetime.utcnow()
        elif isinstance(close_date, datetime):
            transaction_date = close_date
        else:
            transaction_date = datetime.utcnow()
        
        # Extract deal description
        description = (
            crm_deal.get('name') or
            crm_deal.get('deal_name') or
            crm_deal.get('opportunity_name') or
            crm_deal.get('title') or
            f"CRM Deal {deal_id}"
        )
        
        # Extract currency (default to NGN for Nigerian businesses)
        currency = crm_deal.get('currency', 'NGN')
        
        # Extract company/account information
        account_info = crm_deal.get('account', {}) or crm_deal.get('company', {})
        company_name = account_info.get('name') or crm_deal.get('company_name')
        
        # Create universal transaction
        return UniversalTransaction(
            id=str(deal_id),
            amount=amount,
            currency=currency,
            date=transaction_date,
            description=description,
            
            # CRM-specific fields
            account_number=account_info.get('id') or account_info.get('account_id'),
            reference=crm_deal.get('deal_number') or crm_deal.get('opportunity_number'),
            category='sales',
            
            # CRM metadata
            crm_metadata={
                'deal_stage': crm_deal.get('stage') or crm_deal.get('deal_stage'),
                'probability': crm_deal.get('probability', 0),
                'lead_source': crm_deal.get('lead_source') or crm_deal.get('source'),
                'sales_rep': crm_deal.get('owner', {}).get('name') or crm_deal.get('assigned_to'),
                'sales_rep_id': crm_deal.get('owner', {}).get('id') or crm_deal.get('owner_id'),
                'forecast_category': crm_deal.get('forecast_category'),
                'campaign_source': crm_deal.get('campaign_source'),
                'products': crm_deal.get('products', []) or crm_deal.get('line_items', []),
                'competitors': crm_deal.get('competitors', []),
                'deal_type': crm_deal.get('type') or crm_deal.get('deal_type'),
                'next_step': crm_deal.get('next_step'),
                'created_date': crm_deal.get('created_date'),
                'last_modified_date': crm_deal.get('last_modified_date'),
                'close_reason': crm_deal.get('close_reason'),
                'account_details': account_info,
                'contact_details': crm_deal.get('contact', {}) or crm_deal.get('primary_contact', {})
            },
            
            # Source information
            source_system=self.connector_type.value,
            source_connector='crm_adapter',
            raw_data=crm_deal
        )
    
    def _validate_company_registration(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate company registration for Nigerian businesses."""
        account_info = deal_data.get('account', {}) or deal_data.get('company', {})
        
        validations = {
            'company_name_provided': bool(account_info.get('name')),
            'registration_number_provided': bool(account_info.get('registration_number')),
            'tax_id_provided': bool(account_info.get('tax_id') or account_info.get('tin')),
            'business_address_provided': bool(account_info.get('billing_address') or account_info.get('address'))
        }
        
        validation_score = sum(validations.values()) / len(validations)
        
        return {
            'validations': validations,
            'validation_score': validation_score,
            'cac_compliant': validation_score >= 0.75  # At least 3 out of 4 validations
        }
    
    def _check_business_licensing(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check business licensing requirements for Nigerian companies."""
        account_info = deal_data.get('account', {}) or deal_data.get('company', {})
        
        license_checks = {
            'business_license_provided': bool(account_info.get('business_license')),
            'industry_specific_license': bool(account_info.get('industry_license')),
            'tax_clearance_certificate': bool(account_info.get('tax_clearance')),
            'corporate_compliance': bool(account_info.get('corporate_affairs_commission'))
        }
        
        license_score = sum(license_checks.values()) / len(license_checks)
        
        return {
            'license_checks': license_checks,
            'license_score': license_score,
            'licensing_compliant': license_score >= 0.50  # At least 2 out of 4 checks
        }
    
    def _analyze_crm_metrics(self, processing_results: List[Any]) -> Dict[str, Any]:
        """Analyze CRM-specific metrics from processing results."""
        if not processing_results:
            return {}
        
        high_value_deals = sum(1 for r in processing_results 
                              if r.processed_transaction and r.processed_transaction.amount > 1000000)  # ₦1M+
        
        companies_validated = sum(1 for r in processing_results
                                 if r.processed_transaction and 
                                 r.processed_transaction.enrichment_data.company_matched)
        
        pipeline_analyzed = sum(1 for r in processing_results
                               if r.processed_transaction and 
                               r.processed_transaction.enrichment_data.sales_stage)
        
        return {
            'high_value_deal_rate': high_value_deals / len(processing_results) if processing_results else 0,
            'company_validation_rate': companies_validated / len(processing_results) if processing_results else 0,
            'pipeline_analysis_rate': pipeline_analyzed / len(processing_results) if processing_results else 0,
            'total_processed': len(processing_results)
        }
    
    def _analyze_single_deal(self, processed_deal: UniversalProcessedTransaction) -> Dict[str, Any]:
        """Analyze insights for a single processed deal."""
        return {
            'risk_level': processed_deal.processing_metadata.risk_level.value,
            'confidence_score': processed_deal.processing_metadata.confidence_score,
            'company_matched': processed_deal.enrichment_data.company_matched,
            'deal_value_category': self._categorize_deal_value(processed_deal.amount),
            'compliance_status': processed_deal.enrichment_data.nigerian_compliance_level,
            'requires_review': processed_deal.requires_manual_review(),
            'processing_notes': processed_deal.processing_metadata.processing_notes
        }
    
    def _categorize_deal_value(self, amount: float) -> str:
        """Categorize deal value into business segments."""
        if amount >= 10000000:  # ₦10M+
            return 'enterprise'
        elif amount >= 1000000:  # ₦1M+
            return 'high_value'
        elif amount >= 100000:  # ₦100K+
            return 'mid_market'
        elif amount >= 10000:  # ₦10K+
            return 'small_business'
        else:
            return 'micro_business'
    
    def _analyze_pipeline_patterns(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Analyze sales pipeline patterns from processed deals."""
        if not deals:
            return {}
        
        # Calculate pipeline metrics
        total_value = sum(deal.amount for deal in deals)
        avg_deal_size = total_value / len(deals) if deals else 0
        
        # Analyze deal stages
        stage_distribution = {}
        for deal in deals:
            stage = deal.original_transaction.crm_metadata.get('deal_stage', 'unknown')
            stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
        
        # Analyze sales reps
        rep_performance = {}
        for deal in deals:
            rep = deal.original_transaction.crm_metadata.get('sales_rep', 'unknown')
            if rep not in rep_performance:
                rep_performance[rep] = {'count': 0, 'value': 0}
            rep_performance[rep]['count'] += 1
            rep_performance[rep]['value'] += deal.amount
        
        return {
            'total_pipeline_value': float(total_value),
            'average_deal_size': float(avg_deal_size),
            'deal_count': len(deals),
            'stage_distribution': stage_distribution,
            'sales_rep_performance': rep_performance,
            'pipeline_velocity': self._calculate_pipeline_velocity(deals)
        }
    
    def _calculate_pipeline_velocity(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Calculate pipeline velocity metrics."""
        if not deals:
            return {}
        
        # Simple velocity calculation based on deal dates
        date_sorted_deals = sorted(deals, key=lambda d: d.date)
        if len(date_sorted_deals) < 2:
            return {'velocity_days': 0, 'trend': 'insufficient_data'}
        
        first_date = date_sorted_deals[0].date
        last_date = date_sorted_deals[-1].date
        days_span = (last_date - first_date).days
        
        velocity_days = days_span / len(deals) if days_span > 0 else 0
        
        return {
            'velocity_days': velocity_days,
            'trend': 'accelerating' if velocity_days < 30 else 'steady' if velocity_days < 60 else 'slow'
        }
    
    def _generate_pipeline_recommendations(self, pipeline_analysis: Dict[str, Any]) -> List[str]:
        """Generate pipeline optimization recommendations."""
        recommendations = []
        
        avg_deal_size = pipeline_analysis.get('average_deal_size', 0)
        deal_count = pipeline_analysis.get('deal_count', 0)
        velocity = pipeline_analysis.get('pipeline_velocity', {})
        
        if avg_deal_size < 500000:  # ₦500K
            recommendations.append("Focus on upselling to increase average deal size")
        
        if deal_count < 10:
            recommendations.append("Increase lead generation to build stronger pipeline")
        
        velocity_days = velocity.get('velocity_days', 0)
        if velocity_days > 60:
            recommendations.append("Improve sales process efficiency to accelerate deal closure")
        
        return recommendations
    
    def _generate_deal_summary(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate deal summary analytics."""
        if not deals:
            return {}
        
        total_value = sum(deal.amount for deal in deals)
        won_deals = [d for d in deals if d.original_transaction.crm_metadata.get('deal_stage', '').lower() in ['closed-won', 'won']]
        won_value = sum(deal.amount for deal in won_deals)
        
        return {
            'total_deals': len(deals),
            'total_pipeline_value': float(total_value),
            'won_deals': len(won_deals),
            'won_value': float(won_value),
            'win_rate': len(won_deals) / len(deals) if deals else 0,
            'average_deal_size': float(total_value / len(deals)) if deals else 0
        }
    
    def _generate_revenue_analysis(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate revenue analysis."""
        if not deals:
            return {}
        
        won_deals = [d for d in deals if d.original_transaction.crm_metadata.get('deal_stage', '').lower() in ['closed-won', 'won']]
        forecasted_deals = [d for d in deals if d.original_transaction.crm_metadata.get('probability', 0) > 50]
        
        actual_revenue = sum(deal.amount for deal in won_deals)
        forecasted_revenue = sum(deal.amount * (deal.original_transaction.crm_metadata.get('probability', 0) / 100) for deal in forecasted_deals)
        
        return {
            'actual_revenue': float(actual_revenue),
            'forecasted_revenue': float(forecasted_revenue),
            'revenue_recognition': float(actual_revenue + forecasted_revenue * 0.7),  # Conservative forecast
            'currency': deals[0].currency if deals else 'NGN'
        }
    
    def _generate_pipeline_performance(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate pipeline performance metrics."""
        return self._analyze_pipeline_patterns(deals)
    
    def _generate_team_performance(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate sales team performance analysis."""
        if not deals:
            return {}
        
        team_stats = {}
        for deal in deals:
            rep = deal.original_transaction.crm_metadata.get('sales_rep', 'unknown')
            if rep not in team_stats:
                team_stats[rep] = {'deals': 0, 'value': 0, 'won': 0}
            
            team_stats[rep]['deals'] += 1
            team_stats[rep]['value'] += deal.amount
            
            if deal.original_transaction.crm_metadata.get('deal_stage', '').lower() in ['closed-won', 'won']:
                team_stats[rep]['won'] += 1
        
        # Calculate win rates
        for rep in team_stats:
            team_stats[rep]['win_rate'] = team_stats[rep]['won'] / team_stats[rep]['deals'] if team_stats[rep]['deals'] > 0 else 0
        
        return team_stats
    
    def _generate_business_compliance_summary(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate business compliance summary."""
        if not deals:
            return {}
        
        compliant_deals = sum(1 for deal in deals if deal.is_nigerian_compliant())
        company_validated = sum(1 for deal in deals if deal.enrichment_data.company_matched)
        
        return {
            'compliance_rate': compliant_deals / len(deals),
            'company_validation_rate': company_validated / len(deals),
            'total_assessed': len(deals)
        }
    
    def _generate_business_risk_analysis(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate business risk analysis."""
        if not deals:
            return {}
        
        high_risk = sum(1 for deal in deals if deal.processing_metadata.risk_level.value in ['high', 'critical'])
        requires_review = sum(1 for deal in deals if deal.requires_manual_review())
        
        return {
            'high_risk_deals': high_risk,
            'manual_review_required': requires_review,
            'risk_detection_rate': high_risk / len(deals),
            'overall_risk_level': 'low' if high_risk / len(deals) < 0.05 else 'medium' if high_risk / len(deals) < 0.15 else 'high'
        }
    
    def _generate_regulatory_insights(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate regulatory compliance insights."""
        if not deals:
            return {}
        
        # Analyze regulatory compliance patterns
        cac_compliant = sum(1 for deal in deals if deal.enrichment_data.company_registration_verified)
        tax_compliant = sum(1 for deal in deals if deal.enrichment_data.tax_compliance_verified)
        
        return {
            'cac_compliance_rate': cac_compliant / len(deals),
            'tax_compliance_rate': tax_compliant / len(deals),
            'regulatory_recommendations': self._generate_regulatory_recommendations(deals)
        }
    
    def _generate_regulatory_recommendations(self, deals: List[UniversalProcessedTransaction]) -> List[str]:
        """Generate regulatory compliance recommendations."""
        recommendations = []
        
        if not deals:
            return recommendations
        
        cac_rate = sum(1 for deal in deals if deal.enrichment_data.company_registration_verified) / len(deals)
        tax_rate = sum(1 for deal in deals if deal.enrichment_data.tax_compliance_verified) / len(deals)
        
        if cac_rate < 0.8:
            recommendations.append("Improve CAC registration verification for business customers")
        
        if tax_rate < 0.8:
            recommendations.append("Enhance tax compliance verification process")
        
        return recommendations
    
    def _generate_customer_insights(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate customer insights from deals."""
        if not deals:
            return {}
        
        # Analyze customer segments by deal value
        segments = {'enterprise': 0, 'high_value': 0, 'mid_market': 0, 'small_business': 0, 'micro_business': 0}
        
        for deal in deals:
            segment = self._categorize_deal_value(deal.amount)
            segments[segment] += 1
        
        return {
            'customer_segments': segments,
            'total_customers': len(set(deal.enrichment_data.customer_id for deal in deals if deal.enrichment_data.customer_id))
        }
    
    def _generate_market_insights(self, deals: List[UniversalProcessedTransaction]) -> Dict[str, Any]:
        """Generate market insights from deal data."""
        if not deals:
            return {}
        
        # Analyze industries and lead sources
        lead_sources = {}
        industries = {}
        
        for deal in deals:
            source = deal.original_transaction.crm_metadata.get('lead_source', 'unknown')
            lead_sources[source] = lead_sources.get(source, 0) + 1
            
            industry = deal.original_transaction.crm_metadata.get('account_details', {}).get('industry', 'unknown')
            industries[industry] = industries.get(industry, 0) + 1
        
        return {
            'lead_source_distribution': lead_sources,
            'industry_distribution': industries
        }
    
    def _generate_business_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate business recommendations from analytics."""
        recommendations = []
        
        deal_summary = analytics.get('deal_summary', {})
        compliance_summary = analytics.get('compliance_summary', {})
        risk_analysis = analytics.get('risk_analysis', {})
        
        # Deal performance recommendations
        win_rate = deal_summary.get('win_rate', 0)
        if win_rate < 0.2:
            recommendations.append("Low win rate - review qualification and sales process")
        
        # Compliance recommendations
        compliance_rate = compliance_summary.get('compliance_rate', 0)
        if compliance_rate < 0.8:
            recommendations.append("Improve Nigerian business compliance verification")
        
        # Risk recommendations
        risk_rate = risk_analysis.get('risk_detection_rate', 0)
        if risk_rate > 0.1:
            recommendations.append("High risk detection rate - enhance due diligence process")
        
        return recommendations
    
    def _update_stats(self, total_count: int, processed_count: int, processing_time: float):
        """Update adapter statistics."""
        self.stats['total_deals'] += total_count
        self.stats['universal_processed'] += processed_count
        
        # Update average processing time
        if self.stats['total_deals'] > 0:
            total_time = self.stats['average_processing_time'] * (self.stats['total_deals'] - total_count)
            total_time += processing_time
            self.stats['average_processing_time'] = total_time / self.stats['total_deals']
    
    # Delegate other methods to original connector
    async def test_connection(self):
        """Delegate to original connector."""
        return await self.crm_connector.test_connection()
    
    async def authenticate(self):
        """Delegate to original connector."""
        return await self.crm_connector.authenticate()
    
    async def get_accounts(self, filters: Optional[Dict[str, Any]] = None):
        """Delegate to original connector."""
        return await self.crm_connector.get_accounts(filters)
    
    async def get_contacts(self, filters: Optional[Dict[str, Any]] = None):
        """Delegate to original connector."""
        return await self.crm_connector.get_contacts(filters)
    
    async def disconnect(self):
        """Delegate to original connector."""
        return await self.crm_connector.disconnect()
    
    def is_connected(self) -> bool:
        """Delegate to original connector."""
        return self.crm_connector.is_connected()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get enhanced connection status including adapter statistics."""
        base_status = self.crm_connector.get_connection_status()
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


def create_crm_adapter(
    crm_connector: BaseCRMConnector,
    connector_type: ConnectorType,
    enable_universal_processing: bool = True
) -> CRMConnectorAdapter:
    """
    Factory function to create a CRM connector adapter.
    
    Args:
        crm_connector: Existing CRM connector instance
        connector_type: Type of CRM connector
        enable_universal_processing: Whether to enable universal processing
        
    Returns:
        CRMConnectorAdapter instance
    """
    return CRMConnectorAdapter(
        crm_connector=crm_connector,
        connector_type=connector_type,
        enable_universal_processing=enable_universal_processing
    )