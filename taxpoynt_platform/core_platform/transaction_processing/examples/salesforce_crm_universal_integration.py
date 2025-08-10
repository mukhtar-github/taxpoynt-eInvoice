"""
Salesforce CRM Universal Integration Example
===========================================

Demonstrates how to integrate Salesforce CRM connector with universal transaction processing
pipeline using the CRM connector adapter. This example shows enhanced business analytics,
Nigerian compliance validation, and deal intelligence for Salesforce opportunities.

Key Benefits:
- Nigerian business compliance validation (CAC registration, TIN verification)
- Enhanced deal scoring and opportunity intelligence
- Sales pipeline optimization and revenue forecasting
- Company registration verification and business licensing checks
- Cross-CRM customer and company intelligence
- Real-time business analytics and performance insights

Integration Features:
- Backward compatibility with existing Salesforce CRM connector
- Enhanced deal processing with universal pipeline
- Nigerian business registration compliance
- Deal-specific business rules and validation
- Company matching across multiple CRM systems
- Sales performance metrics and operational insights
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..adapters.crm_connector_adapter import create_crm_adapter
from ..connector_configs.connector_types import ConnectorType
from ...external_integrations.business_systems.crm.salesforce.connector import SalesforceCRMConnector

logger = logging.getLogger(__name__)


class SalesforceUniversalCRMIntegration:
    """
    Enhanced Salesforce CRM integration with universal transaction processing.
    
    This class demonstrates how to wrap the existing Salesforce CRM connector
    with universal processing capabilities for enhanced business analytics,
    Nigerian compliance, and deal intelligence.
    """
    
    def __init__(self, salesforce_config: Dict[str, Any]):
        """
        Initialize Salesforce CRM integration with universal processing.
        
        Args:
            salesforce_config: Salesforce CRM configuration including:
                - client_id: Salesforce connected app client ID
                - client_secret: Salesforce connected app client secret
                - username: Salesforce username (for username-password flow)
                - password: Salesforce password
                - security_token: Salesforce security token
                - instance_url: Salesforce instance URL
                - api_version: Salesforce API version (e.g., v58.0)
                - environment: production or sandbox
        """
        self.config = salesforce_config
        
        # Initialize original Salesforce connector
        self.salesforce_connector = SalesforceCRMConnector(salesforce_config)
        
        # Create enhanced adapter with universal processing
        self.crm_adapter = create_crm_adapter(
            crm_connector=self.salesforce_connector,
            connector_type=ConnectorType.SALESFORCE_CRM,
            enable_universal_processing=True
        )
        
        logger.info("Salesforce CRM universal integration initialized")
    
    async def initialize_connection(self) -> Dict[str, Any]:
        """
        Initialize connection to Salesforce CRM with enhanced testing.
        
        Returns:
            Dict with connection status and universal processing capabilities
        """
        try:
            # Test basic Salesforce connection
            connection_result = await self.salesforce_connector.test_connection()
            
            if not connection_result.get('success'):
                return {
                    'success': False,
                    'error': 'Salesforce CRM connection failed',
                    'details': connection_result
                }
            
            # Authenticate with Salesforce
            auth_result = await self.salesforce_connector.authenticate()
            
            if not auth_result:
                return {
                    'success': False,
                    'error': 'Salesforce CRM authentication failed'
                }
            
            # Get enhanced connection status
            adapter_status = self.crm_adapter.get_connection_status()
            
            return {
                'success': True,
                'message': 'Salesforce CRM with universal processing ready',
                'salesforce_connection': connection_result,
                'universal_processing': {
                    'enabled': adapter_status['universal_processing_enabled'],
                    'connector_type': adapter_status['processing_config']['connector_type'],
                    'pipeline_stages': adapter_status['processing_config']['pipeline_stages']
                },
                'salesforce_info': {
                    'instance_url': self.config.get('instance_url'),
                    'api_version': self.config.get('api_version'),
                    'environment': self.config.get('environment', 'production'),
                    'supported_features': self.salesforce_connector.supported_features
                }
            }
            
        except Exception as e:
            logger.error(f"Error initializing Salesforce universal connection: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_enhanced_opportunities(
        self,
        stage_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        amount_range: Optional[Dict[str, float]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get Salesforce opportunities with universal processing enhancements.
        
        This method demonstrates the enhanced capabilities provided by
        universal processing including Nigerian business compliance validation,
        deal intelligence, and sales analytics.
        
        Args:
            stage_filter: Filter by opportunity stage (e.g., 'Closed Won', 'Negotiation')
            start_date: Start date for opportunity range
            end_date: End date for opportunity range
            amount_range: Filter by opportunity amount (min_amount, max_amount)
            limit: Maximum number of opportunities
            
        Returns:
            Dict with enhanced opportunity data and analytics
        """
        try:
            # Get opportunities with universal processing
            result = await self.crm_adapter.get_deals_with_processing(
                stage_filter=stage_filter,
                start_date=start_date,
                end_date=end_date,
                amount_range=amount_range,
                limit=limit
            )
            
            if not result.get('processing_enabled'):
                logger.warning("Universal processing not enabled - returning basic results")
                return result
            
            # Extract enhanced insights
            processed_deals = result.get('processed_deals', [])
            crm_metrics = result.get('crm_metrics', {})
            
            # Generate additional Salesforce-specific insights
            salesforce_insights = await self._generate_salesforce_insights(processed_deals)
            
            # Add Nigerian business compliance summary
            compliance_summary = self._generate_nigerian_business_compliance_summary(processed_deals)
            
            return {
                **result,
                'salesforce_insights': salesforce_insights,
                'nigerian_business_compliance': compliance_summary,
                'recommendations': self._generate_salesforce_recommendations(result, salesforce_insights),
                'integration_type': 'salesforce_universal'
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced Salesforce opportunities: {e}")
            return {
                'success': False,
                'error': str(e),
                'integration_type': 'salesforce_universal'
            }
    
    async def validate_opportunity_compliance(
        self,
        opportunity_id: str
    ) -> Dict[str, Any]:
        """
        Validate a specific Salesforce opportunity for Nigerian business compliance.
        
        This method demonstrates comprehensive compliance validation including
        CAC registration verification, business licensing, and deal risk assessment.
        
        Args:
            opportunity_id: Salesforce opportunity ID to validate
            
        Returns:
            Dict with comprehensive compliance validation results
        """
        try:
            # Get opportunity with universal processing
            result = await self.crm_adapter.get_deal_by_id_with_processing(
                deal_id=opportunity_id
            )
            
            if not result.get('processed_deal'):
                # Fall back to basic validation
                raw_deal = result.get('deal')
                if raw_deal:
                    return await self.crm_adapter.validate_business_compliance(raw_deal)
                else:
                    return {
                        'success': False,
                        'error': f'Opportunity {opportunity_id} not found'
                    }
            
            processed_deal = result['processed_deal']
            deal_insights = result.get('deal_insights', {})
            
            # Generate comprehensive compliance report
            compliance_report = {
                'opportunity_id': opportunity_id,
                'compliance_status': processed_deal.is_nigerian_compliant(),
                'compliance_details': processed_deal.get_nigerian_compliance_info(),
                'company_validation': {
                    'company_matched': processed_deal.enrichment_data.company_matched,
                    'registration_verified': processed_deal.enrichment_data.company_registration_verified,
                    'tax_compliance': processed_deal.enrichment_data.tax_compliance_verified,
                    'business_license': deal_insights.get('business_license_status', 'unknown')
                },
                'deal_assessment': {
                    'value_category': deal_insights.get('deal_value_category', 'unknown'),
                    'risk_level': processed_deal.processing_metadata.risk_level.value,
                    'confidence_score': processed_deal.processing_metadata.confidence_score,
                    'requires_review': processed_deal.requires_manual_review()
                },
                'salesforce_specific': {
                    'opportunity_stage': processed_deal.original_transaction.crm_metadata.get('deal_stage'),
                    'probability': processed_deal.original_transaction.crm_metadata.get('probability', 0),
                    'sales_rep': processed_deal.original_transaction.crm_metadata.get('sales_rep'),
                    'account_verified': bool(processed_deal.original_transaction.crm_metadata.get('account_details')),
                    'products_specified': bool(processed_deal.original_transaction.crm_metadata.get('products')),
                    'forecast_category': processed_deal.original_transaction.crm_metadata.get('forecast_category')
                },
                'processing_metadata': {
                    'processing_time': result.get('processing_time', 0),
                    'pipeline_applied': True,
                    'connector_type': 'salesforce_crm'
                }
            }
            
            return compliance_report
            
        except Exception as e:
            logger.error(f"Error validating Salesforce opportunity compliance: {e}")
            return {
                'opportunity_id': opportunity_id,
                'success': False,
                'error': str(e)
            }
    
    async def analyze_sales_pipeline(
        self,
        sales_rep_filter: Optional[str] = None,
        team_filter: Optional[str] = None,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze Salesforce sales pipeline using universal processing insights.
        
        This method demonstrates enhanced pipeline analytics that leverage
        universal processing deal intelligence and pattern recognition.
        
        Args:
            sales_rep_filter: Specific Salesforce sales rep to analyze
            team_filter: Specific sales team to analyze
            days_back: Number of days to analyze
            
        Returns:
            Dict with comprehensive sales pipeline analysis
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Analyze sales pipeline using universal processing
            pipeline_result = await self.crm_adapter.analyze_sales_pipeline(
                team_filter=team_filter,
                start_date=start_date,
                end_date=end_date,
                limit=500
            )
            
            if pipeline_result.get('analysis_failed'):
                return pipeline_result
            
            # Add Salesforce-specific pipeline insights
            salesforce_pipeline_insights = await self._analyze_salesforce_pipeline_data(
                sales_rep_filter, team_filter, start_date, end_date
            )
            
            # Combine universal and Salesforce-specific insights
            enhanced_analysis = {
                **pipeline_result,
                'salesforce_pipeline_data': salesforce_pipeline_insights,
                'quota_analysis': self._analyze_quota_performance(
                    pipeline_result.get('pipeline_insights', {}),
                    salesforce_pipeline_insights
                ),
                'forecasting_insights': self._generate_forecasting_insights(
                    pipeline_result.get('pipeline_insights', {}),
                    salesforce_pipeline_insights
                )
            }
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Salesforce sales pipeline: {e}")
            return {
                'sales_rep_filter': sales_rep_filter,
                'team_filter': team_filter,
                'error': str(e),
                'analysis_failed': True
            }
    
    async def generate_business_intelligence_dashboard(
        self,
        report_type: str = 'comprehensive',
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive business intelligence dashboard for Salesforce CRM.
        
        This method demonstrates how universal processing enhances Salesforce CRM
        analytics with Nigerian business insights, compliance tracking, and performance metrics.
        
        Args:
            report_type: Type of report ('comprehensive', 'compliance', 'performance')
            days_back: Number of days to include in analytics
            
        Returns:
            Dict with comprehensive business intelligence dashboard data
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Generate business analytics using universal processing
            analytics_result = await self.crm_adapter.generate_business_analytics_report(
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            if analytics_result.get('report_failed'):
                return analytics_result
            
            # Add Salesforce-specific dashboard elements
            salesforce_dashboard_data = await self._generate_salesforce_dashboard_data(
                start_date, end_date
            )
            
            # Get adapter processing statistics
            processing_stats = self.crm_adapter.get_processing_statistics()
            
            # Combine into comprehensive dashboard
            dashboard = {
                **analytics_result,
                'salesforce_dashboard': salesforce_dashboard_data,
                'processing_performance': processing_stats,
                'dashboard_insights': self._generate_dashboard_insights(
                    analytics_result.get('analytics', {}),
                    salesforce_dashboard_data
                ),
                'action_items': self._generate_action_items(
                    analytics_result.get('analytics', {}),
                    analytics_result.get('recommendations', [])
                ),
                'integration_status': {
                    'salesforce_connector': 'active',
                    'universal_processing': 'enabled',
                    'nigerian_compliance': 'active',
                    'business_intelligence': 'enabled'
                }
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating Salesforce business intelligence dashboard: {e}")
            return {
                'error': str(e),
                'dashboard_failed': True
            }
    
    async def get_account_compliance_report(
        self,
        account_id: Optional[str] = None,
        account_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report for Salesforce accounts.
        
        This method demonstrates how to analyze Nigerian business compliance
        for companies in Salesforce using universal processing insights.
        
        Args:
            account_id: Specific Salesforce account ID
            account_name: Specific Salesforce account name
            
        Returns:
            Dict with account compliance analysis
        """
        try:
            # Get account data from Salesforce
            account_filters = {}
            if account_id:
                account_filters['id'] = account_id
            if account_name:
                account_filters['name'] = account_name
            
            accounts = await self.salesforce_connector.get_accounts(account_filters)
            
            if not accounts:
                return {
                    'success': False,
                    'error': 'No accounts found matching criteria',
                    'criteria': {'account_id': account_id, 'account_name': account_name}
                }
            
            # Analyze compliance for each account
            compliance_reports = []
            for account in accounts:
                # Get opportunities for this account
                opportunity_filters = {
                    'account_id': account.get('id'),
                    'start_date': datetime.utcnow() - timedelta(days=365)  # Last year
                }
                
                account_opportunities = await self.crm_adapter.get_deals_with_processing(
                    limit=200,
                    **opportunity_filters
                )
                
                processed_deals = account_opportunities.get('processed_deals', [])
                
                # Generate account compliance analysis
                account_compliance = {
                    'account_id': account.get('id'),
                    'account_name': account.get('name'),
                    'compliance_summary': self._analyze_account_compliance(account, processed_deals),
                    'deal_analysis': self._analyze_account_deals(processed_deals),
                    'risk_assessment': self._assess_account_risk(account, processed_deals),
                    'recommendations': self._generate_account_recommendations(account, processed_deals)
                }
                
                compliance_reports.append(account_compliance)
            
            return {
                'success': True,
                'total_accounts': len(accounts),
                'compliance_reports': compliance_reports,
                'summary': self._generate_overall_compliance_summary(compliance_reports),
                'report_generated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating account compliance report: {e}")
            return {
                'success': False,
                'error': str(e),
                'criteria': {'account_id': account_id, 'account_name': account_name}
            }
    
    async def _generate_salesforce_insights(self, processed_deals: List[Any]) -> Dict[str, Any]:
        """Generate Salesforce-specific insights from processed deals."""
        if not processed_deals:
            return {}
        
        # Analyze Salesforce-specific data
        stage_distribution = {}
        forecast_categories = {}
        lead_sources = {}
        total_forecast_value = 0
        
        for deal in processed_deals:
            crm_metadata = deal.original_transaction.crm_metadata
            
            # Stage analysis
            stage = crm_metadata.get('deal_stage', 'unknown')
            stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
            
            # Forecast category analysis
            forecast_cat = crm_metadata.get('forecast_category', 'unknown')
            forecast_categories[forecast_cat] = forecast_categories.get(forecast_cat, 0) + 1
            
            # Lead source analysis
            lead_source = crm_metadata.get('lead_source', 'unknown')
            lead_sources[lead_source] = lead_sources.get(lead_source, 0) + 1
            
            # Forecast value calculation
            probability = crm_metadata.get('probability', 0)
            total_forecast_value += deal.amount * (probability / 100.0)
        
        return {
            'stage_distribution': stage_distribution,
            'forecast_category_distribution': forecast_categories,
            'lead_source_distribution': lead_sources,
            'total_forecast_value': total_forecast_value,
            'average_forecast_value': total_forecast_value / len(processed_deals) if processed_deals else 0
        }
    
    def _generate_nigerian_business_compliance_summary(self, processed_deals: List[Any]) -> Dict[str, Any]:
        """Generate Nigerian business compliance summary for deals."""
        if not processed_deals:
            return {}
        
        compliant_count = sum(1 for deal in processed_deals if deal.is_nigerian_compliant())
        company_verified_count = sum(1 for deal in processed_deals 
                                   if deal.enrichment_data.company_registration_verified)
        tax_compliant_count = sum(1 for deal in processed_deals
                                if deal.enrichment_data.tax_compliance_verified)
        
        return {
            'overall_compliance_rate': compliant_count / len(processed_deals),
            'company_verification_rate': company_verified_count / len(processed_deals),
            'tax_compliance_rate': tax_compliant_count / len(processed_deals),
            'total_deals_assessed': len(processed_deals),
            'compliance_grade': self._calculate_business_compliance_grade(
                compliant_count / len(processed_deals)
            )
        }
    
    def _calculate_business_compliance_grade(self, compliance_rate: float) -> str:
        """Calculate business compliance grade based on rate."""
        if compliance_rate >= 0.95:
            return 'Excellent'
        elif compliance_rate >= 0.85:
            return 'Good'
        elif compliance_rate >= 0.75:
            return 'Satisfactory'
        elif compliance_rate >= 0.65:
            return 'Needs Improvement'
        else:
            return 'Poor'
    
    def _generate_salesforce_recommendations(
        self,
        deal_result: Dict[str, Any],
        salesforce_insights: Dict[str, Any]
    ) -> List[str]:
        """Generate Salesforce-specific recommendations."""
        recommendations = []
        
        # Processing performance recommendations
        processing_time = deal_result.get('processing_time', 0)
        if processing_time > 3.0:
            recommendations.append("Processing time exceeds 3 seconds - consider optimization")
        
        # Stage distribution recommendations
        stage_dist = salesforce_insights.get('stage_distribution', {})
        if stage_dist.get('Prospecting', 0) > stage_dist.get('Closed Won', 0) * 5:
            recommendations.append("High ratio of prospecting to closed deals - improve qualification")
        
        # Forecast accuracy recommendations
        forecast_value = salesforce_insights.get('total_forecast_value', 0)
        if forecast_value == 0:
            recommendations.append("No forecast value calculated - review opportunity probability settings")
        
        return recommendations
    
    async def _analyze_salesforce_pipeline_data(
        self,
        sales_rep_filter: Optional[str],
        team_filter: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze Salesforce-specific pipeline data."""
        try:
            # This would integrate with additional Salesforce APIs
            # For now, return placeholder data structure
            return {
                'salesforce_pipeline_metrics': {
                    'total_opportunities': 0,
                    'pipeline_coverage': 0.0,
                    'forecast_accuracy': 0.0,
                    'sales_cycle_length': 0
                },
                'territory_analysis': {
                    'top_territories': [],
                    'territory_performance': {}
                },
                'product_analysis': {
                    'top_products': [],
                    'product_mix': {}
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing Salesforce pipeline data: {e}")
            return {}
    
    def _analyze_quota_performance(
        self,
        pipeline_insights: Dict[str, Any],
        salesforce_pipeline_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze quota performance for sales teams."""
        total_pipeline_value = pipeline_insights.get('total_pipeline_value', 0)
        sales_rep_performance = pipeline_insights.get('sales_rep_performance', {})
        
        quota_analysis = {}
        for rep, performance in sales_rep_performance.items():
            rep_value = performance.get('value', 0)
            quota_analysis[rep] = {
                'pipeline_value': rep_value,
                'quota_attainment': rep_value / 1000000 if rep_value > 0 else 0,  # Assume ₦1M quota
                'deals_count': performance.get('count', 0)
            }
        
        return {
            'total_pipeline_vs_quota': total_pipeline_value / 10000000 if total_pipeline_value > 0 else 0,  # Assume ₦10M team quota
            'individual_performance': quota_analysis,
            'quota_recommendations': self._generate_quota_recommendations(quota_analysis)
        }
    
    def _generate_quota_recommendations(self, quota_analysis: Dict[str, Any]) -> List[str]:
        """Generate quota performance recommendations."""
        recommendations = []
        
        for rep, performance in quota_analysis.items():
            attainment = performance.get('quota_attainment', 0)
            if attainment < 0.5:
                recommendations.append(f"{rep}: Below 50% quota attainment - needs immediate attention")
            elif attainment > 1.2:
                recommendations.append(f"{rep}: Exceeding quota by 20% - consider quota adjustment")
        
        return recommendations
    
    def _generate_forecasting_insights(
        self,
        pipeline_insights: Dict[str, Any],
        salesforce_pipeline_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate sales forecasting insights."""
        pipeline_velocity = pipeline_insights.get('pipeline_velocity', {})
        velocity_days = pipeline_velocity.get('velocity_days', 0)
        
        return {
            'sales_cycle_analysis': {
                'average_cycle_days': velocity_days,
                'cycle_trend': pipeline_velocity.get('trend', 'unknown'),
                'forecast_confidence': 'high' if velocity_days < 45 else 'medium' if velocity_days < 90 else 'low'
            },
            'revenue_forecast': {
                'current_quarter_projection': pipeline_insights.get('total_pipeline_value', 0) * 0.3,
                'next_quarter_projection': pipeline_insights.get('total_pipeline_value', 0) * 0.5,
                'forecast_accuracy_confidence': 0.75  # Placeholder confidence score
            }
        }
    
    async def _generate_salesforce_dashboard_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate Salesforce-specific dashboard data."""
        try:
            # Get Salesforce organization info
            # This would use Salesforce REST API organization endpoint
            return {
                'salesforce_org_info': {
                    'instance_url': self.config.get('instance_url'),
                    'api_version': self.config.get('api_version'),
                    'environment': self.config.get('environment', 'production'),
                    'features_enabled': self.salesforce_connector.supported_features
                },
                'data_quality_metrics': {
                    'complete_opportunities': 0.95,  # Placeholder
                    'account_data_completeness': 0.88,  # Placeholder
                    'contact_data_completeness': 0.92   # Placeholder
                },
                'integration_health': {
                    'api_calls_remaining': 100000,  # Placeholder
                    'last_sync_time': datetime.utcnow().isoformat(),
                    'sync_status': 'healthy'
                }
            }
        except Exception as e:
            logger.error(f"Error generating Salesforce dashboard data: {e}")
            return {}
    
    def _generate_dashboard_insights(
        self,
        analytics: Dict[str, Any],
        salesforce_dashboard_data: Dict[str, Any]
    ) -> List[str]:
        """Generate dashboard insights."""
        insights = []
        
        # Deal insights
        deal_summary = analytics.get('deal_summary', {})
        total_deals = deal_summary.get('total_deals', 0)
        
        if total_deals > 50:
            insights.append(f"High deal volume: {total_deals} opportunities processed")
        
        # Win rate insights
        win_rate = deal_summary.get('win_rate', 0)
        if win_rate > 0.3:
            insights.append(f"Strong win rate: {win_rate:.1%}")
        elif win_rate < 0.15:
            insights.append("Low win rate - review qualification process")
        
        # Compliance insights
        compliance_summary = analytics.get('compliance_summary', {})
        compliance_rate = compliance_summary.get('compliance_rate', 0)
        
        if compliance_rate > 0.9:
            insights.append("Excellent Nigerian business compliance rate")
        elif compliance_rate < 0.7:
            insights.append("Business compliance rate needs improvement")
        
        # Salesforce-specific insights
        org_info = salesforce_dashboard_data.get('salesforce_org_info', {})
        environment = org_info.get('environment', 'unknown')
        if environment == 'sandbox':
            insights.append("Running in Salesforce sandbox environment")
        
        return insights
    
    def _generate_action_items(
        self,
        analytics: Dict[str, Any],
        recommendations: List[str]
    ) -> List[Dict[str, str]]:
        """Generate actionable items from analytics."""
        action_items = []
        
        for recommendation in recommendations:
            if any(keyword in recommendation.lower() for keyword in ['compliance', 'cac', 'tax']):
                action_items.append({
                    'category': 'compliance',
                    'priority': 'high',
                    'action': recommendation,
                    'timeline': 'immediate',
                    'owner': 'compliance_team'
                })
            elif any(keyword in recommendation.lower() for keyword in ['quota', 'performance']):
                action_items.append({
                    'category': 'sales_performance',
                    'priority': 'high',
                    'action': recommendation,
                    'timeline': 'this_week',
                    'owner': 'sales_manager'
                })
            else:
                action_items.append({
                    'category': 'optimization',
                    'priority': 'medium',
                    'action': recommendation,
                    'timeline': 'this_month',
                    'owner': 'sales_ops'
                })
        
        return action_items
    
    def _analyze_account_compliance(
        self,
        account: Dict[str, Any],
        processed_deals: List[Any]
    ) -> Dict[str, Any]:
        """Analyze compliance for a specific account."""
        return {
            'company_registration': {
                'name_verified': bool(account.get('name')),
                'registration_number': bool(account.get('registration_number')),
                'industry_classified': bool(account.get('industry'))
            },
            'deal_compliance': {
                'total_deals': len(processed_deals),
                'compliant_deals': sum(1 for deal in processed_deals if deal.is_nigerian_compliant()),
                'compliance_rate': sum(1 for deal in processed_deals if deal.is_nigerian_compliant()) / len(processed_deals) if processed_deals else 0
            }
        }
    
    def _analyze_account_deals(self, processed_deals: List[Any]) -> Dict[str, Any]:
        """Analyze deals for a specific account."""
        if not processed_deals:
            return {}
        
        total_value = sum(deal.amount for deal in processed_deals)
        won_deals = [d for d in processed_deals if d.original_transaction.crm_metadata.get('deal_stage', '').lower() in ['closed won', 'won']]
        
        return {
            'total_deal_value': float(total_value),
            'total_deals': len(processed_deals),
            'won_deals': len(won_deals),
            'win_rate': len(won_deals) / len(processed_deals) if processed_deals else 0,
            'average_deal_size': float(total_value / len(processed_deals)) if processed_deals else 0
        }
    
    def _assess_account_risk(
        self,
        account: Dict[str, Any],
        processed_deals: List[Any]
    ) -> Dict[str, Any]:
        """Assess risk for a specific account."""
        high_risk_deals = sum(1 for deal in processed_deals 
                             if deal.processing_metadata.risk_level.value in ['high', 'critical'])
        
        return {
            'risk_level': 'high' if high_risk_deals > len(processed_deals) * 0.2 else 'medium' if high_risk_deals > 0 else 'low',
            'high_risk_deal_count': high_risk_deals,
            'risk_factors': self._identify_risk_factors(account, processed_deals)
        }
    
    def _identify_risk_factors(
        self,
        account: Dict[str, Any],
        processed_deals: List[Any]
    ) -> List[str]:
        """Identify risk factors for an account."""
        risk_factors = []
        
        if not account.get('registration_number'):
            risk_factors.append("Missing company registration number")
        
        if not account.get('tax_id'):
            risk_factors.append("Missing tax identification number")
        
        high_value_deals = [d for d in processed_deals if d.amount > 5000000]  # ₦5M+
        if len(high_value_deals) > 3:
            risk_factors.append("Multiple high-value transactions")
        
        return risk_factors
    
    def _generate_account_recommendations(
        self,
        account: Dict[str, Any],
        processed_deals: List[Any]
    ) -> List[str]:
        """Generate recommendations for an account."""
        recommendations = []
        
        if not account.get('registration_number'):
            recommendations.append("Collect and verify company registration number")
        
        if not account.get('tax_id'):
            recommendations.append("Obtain tax identification number for compliance")
        
        if processed_deals:
            compliance_rate = sum(1 for deal in processed_deals if deal.is_nigerian_compliant()) / len(processed_deals)
            if compliance_rate < 0.8:
                recommendations.append("Improve deal compliance documentation")
        
        return recommendations
    
    def _generate_overall_compliance_summary(self, compliance_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate overall compliance summary from all account reports."""
        if not compliance_reports:
            return {}
        
        total_accounts = len(compliance_reports)
        compliant_accounts = sum(1 for report in compliance_reports 
                               if report.get('compliance_summary', {}).get('deal_compliance', {}).get('compliance_rate', 0) >= 0.8)
        
        return {
            'total_accounts_assessed': total_accounts,
            'compliant_accounts': compliant_accounts,
            'overall_compliance_rate': compliant_accounts / total_accounts if total_accounts > 0 else 0,
            'compliance_grade': self._calculate_business_compliance_grade(compliant_accounts / total_accounts if total_accounts > 0 else 0)
        }


async def demo_salesforce_universal_integration():
    """
    Demonstration of Salesforce CRM universal integration.
    
    This example shows how to use the Salesforce connector with universal processing
    for enhanced Nigerian business compliance, deal intelligence, and sales analytics.
    """
    
    # Example Salesforce configuration
    salesforce_config = {
        'client_id': 'your_salesforce_client_id',
        'client_secret': 'your_salesforce_client_secret',
        'username': 'your_salesforce_username',
        'password': 'your_salesforce_password',
        'security_token': 'your_salesforce_security_token',
        'instance_url': 'https://your-instance.salesforce.com',
        'api_version': 'v58.0',
        'environment': 'sandbox'  # or 'production'
    }
    
    try:
        # Initialize Salesforce universal integration
        salesforce_integration = SalesforceUniversalCRMIntegration(salesforce_config)
        
        # 1. Initialize connection
        print("🔌 Initializing Salesforce CRM connection with universal processing...")
        connection_result = await salesforce_integration.initialize_connection()
        
        if not connection_result.get('success'):
            print(f"❌ Connection failed: {connection_result.get('error')}")
            return
        
        print("✅ Salesforce CRM with universal processing connected successfully!")
        print(f"🎯 Universal processing enabled: {connection_result['universal_processing']['enabled']}")
        print(f"🔧 Pipeline stages: {connection_result['universal_processing']['pipeline_stages']}")
        print(f"🏢 Environment: {connection_result['salesforce_info']['environment']}")
        
        # 2. Get enhanced opportunities
        print("\n📊 Getting enhanced opportunities with universal processing...")
        enhanced_opportunities = await salesforce_integration.get_enhanced_opportunities(
            start_date=datetime.utcnow() - timedelta(days=30),
            limit=50
        )
        
        if enhanced_opportunities.get('processing_enabled'):
            processed_count = enhanced_opportunities.get('processed_count', 0)
            total_count = enhanced_opportunities.get('total_count', 0)
            processing_time = enhanced_opportunities.get('processing_time', 0)
            
            print(f"✅ Processed {processed_count}/{total_count} opportunities in {processing_time:.2f}s")
            
            # Nigerian business compliance summary
            compliance = enhanced_opportunities.get('nigerian_business_compliance', {})
            compliance_rate = compliance.get('overall_compliance_rate', 0)
            compliance_grade = compliance.get('compliance_grade', 'N/A')
            
            print(f"🇳🇬 Nigerian business compliance rate: {compliance_rate:.1%} (Grade: {compliance_grade})")
            
            # Salesforce insights
            salesforce_insights = enhanced_opportunities.get('salesforce_insights', {})
            forecast_value = salesforce_insights.get('total_forecast_value', 0)
            print(f"💰 Total forecast value: ₦{forecast_value:,.2f}")
        
        # 3. Validate specific opportunity compliance
        if enhanced_opportunities.get('deals'):
            first_deal = enhanced_opportunities['deals'][0]
            opportunity_id = first_deal.get('id') or first_deal.get('opportunity_id')
            
            if opportunity_id:
                print(f"\n🔍 Validating opportunity compliance: {opportunity_id}")
                compliance_result = await salesforce_integration.validate_opportunity_compliance(
                    opportunity_id=opportunity_id
                )
                
                if compliance_result.get('compliance_status'):
                    print("✅ Opportunity is Nigerian business compliant")
                else:
                    print("⚠️ Opportunity has compliance issues")
                
                risk_level = compliance_result.get('deal_assessment', {}).get('risk_level', 'unknown')
                print(f"🔒 Risk level: {risk_level}")
        
        # 4. Analyze sales pipeline
        print("\n📈 Analyzing sales pipeline...")
        pipeline_analysis = await salesforce_integration.analyze_sales_pipeline(days_back=90)
        
        if not pipeline_analysis.get('analysis_failed'):
            insights = pipeline_analysis.get('pipeline_insights', {})
            
            total_value = insights.get('total_pipeline_value', 0)
            deal_count = insights.get('deal_count', 0)
            velocity = insights.get('pipeline_velocity', {})
            
            print(f"💵 Total pipeline value: ₦{total_value:,.2f}")
            print(f"📊 Total deals in pipeline: {deal_count}")
            print(f"⚡ Pipeline velocity: {velocity.get('velocity_days', 0):.1f} days")
            
            # Quota analysis
            quota_analysis = pipeline_analysis.get('quota_analysis', {})
            quota_attainment = quota_analysis.get('total_pipeline_vs_quota', 0)
            print(f"🎯 Quota attainment: {quota_attainment:.1%}")
        
        # 5. Generate business intelligence dashboard
        print("\n📊 Generating business intelligence dashboard...")
        dashboard = await salesforce_integration.generate_business_intelligence_dashboard(
            report_type='comprehensive',
            days_back=30
        )
        
        if not dashboard.get('dashboard_failed'):
            analytics = dashboard.get('analytics', {})
            deal_summary = analytics.get('deal_summary', {})
            
            total_deals = deal_summary.get('total_deals', 0)
            win_rate = deal_summary.get('win_rate', 0)
            
            print(f"🏆 Total deals analyzed: {total_deals}")
            print(f"📊 Win rate: {win_rate:.1%}")
            
            # Action items
            action_items = dashboard.get('action_items', [])
            if action_items:
                print(f"\n📋 Action items ({len(action_items)}):")
                for item in action_items[:3]:  # Show first 3
                    print(f"  • {item['action']} ({item['priority']} priority)")
        
        # 6. Account compliance report (if accounts available)
        print("\n🏢 Generating account compliance report...")
        compliance_report = await salesforce_integration.get_account_compliance_report()
        
        if compliance_report.get('success'):
            total_accounts = compliance_report.get('total_accounts', 0)
            summary = compliance_report.get('summary', {})
            overall_rate = summary.get('overall_compliance_rate', 0)
            
            print(f"🏬 Total accounts assessed: {total_accounts}")
            print(f"✅ Overall compliance rate: {overall_rate:.1%}")
        
        print("\n🎉 Salesforce CRM universal integration demo completed successfully!")
        print("✨ Key benefits demonstrated:")
        print("  • Enhanced opportunity processing with universal pipeline")
        print("  • Nigerian business compliance validation")
        print("  • Advanced sales pipeline analytics and forecasting")
        print("  • Company registration and tax compliance verification")
        print("  • Comprehensive business intelligence dashboards")
        print("  • Account-level compliance reporting")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    # Run the demonstration
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_salesforce_universal_integration())