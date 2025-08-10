"""
SAP Universal Integration Example
=================================

Example implementation showing how to integrate an existing SAP ERP connector
with the universal transaction processing pipeline using the ERP connector adapter.

This demonstrates the migration strategy from legacy ERP connectors to the
universal processing architecture while maintaining backward compatibility.

Benefits Demonstrated:
- Enhanced data validation with Nigerian compliance rules
- Standardized risk assessment and fraud detection
- Improved customer matching and transaction categorization
- Consistent processing across all business systems
- Maintained compatibility with existing SAP connector interface

Usage Example:
```python
# Initialize SAP connector with universal processing
sap_connector = create_sap_universal_connector(sap_config)

# Get invoices with enhanced processing
result = await sap_connector.get_invoices_with_processing(limit=50)

# Access both original and processed data
original_invoices = result['invoices']
processed_invoices = result['processed_invoices']
processing_results = result['processing_results']
```
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..adapters.erp_connector_adapter import ERPConnectorAdapter, create_erp_adapter
from ..connector_configs.connector_types import ConnectorType
from ....external_integrations.business_systems.erp.sap.connector import SAPConnector

logger = logging.getLogger(__name__)


class SAPUniversalConnector:
    """
    Enhanced SAP connector that combines the original SAP connector with 
    universal transaction processing capabilities.
    
    This class demonstrates how to gradually migrate ERP connectors to use
    the universal processing pipeline while maintaining full backward compatibility.
    """
    
    def __init__(self, sap_config: Dict[str, Any], enable_universal_processing: bool = True):
        """
        Initialize SAP connector with universal processing capabilities.
        
        Args:
            sap_config: SAP connection configuration
            enable_universal_processing: Enable universal processing pipeline
        """
        # Initialize original SAP connector
        self.sap_connector = SAPConnector(sap_config)
        
        # Wrap with universal processing adapter
        self.universal_adapter = create_erp_adapter(
            erp_connector=self.sap_connector,
            connector_type=ConnectorType.ERP_SAP,
            enable_universal_processing=enable_universal_processing
        )
        
        self.config = sap_config
        self.enable_universal_processing = enable_universal_processing
        
        logger.info(f"Initialized SAP Universal Connector with universal processing {'enabled' if enable_universal_processing else 'disabled'}")
    
    # Enhanced methods that use universal processing
    
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
        Get invoices with universal processing applied.
        
        This method provides enhanced invoice retrieval with:
        - Nigerian compliance validation
        - Risk assessment and fraud detection
        - Customer matching and enrichment
        - Transaction categorization
        - Duplicate detection
        
        Returns:
            Dict containing original invoices, processed invoices, and processing metadata
        """
        return await self.universal_adapter.get_invoices_with_processing(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            document_type=document_type,
            include_attachments=include_attachments,
            data_source=data_source
        )
    
    async def get_invoice_by_id_with_processing(
        self,
        invoice_id: str
    ) -> Dict[str, Any]:
        """
        Get a specific invoice with universal processing applied.
        
        Returns:
            Dict containing original invoice, processed invoice, and processing result
        """
        return await self.universal_adapter.get_invoice_by_id_with_processing(invoice_id)
    
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
        return await self.universal_adapter.search_invoices_with_processing(
            customer_name=customer_name,
            invoice_number=invoice_number,
            amount_range=amount_range,
            date_range=date_range,
            limit=limit
        )
    
    async def validate_and_transform_for_firs_enhanced(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """
        Enhanced FIRS validation and transformation using universal processing.
        
        This method provides improved FIRS compliance by:
        - Running Nigerian business rules validation
        - Applying universal data quality checks
        - Enhancing invoice data with processing insights
        - Providing detailed compliance reporting
        
        Returns:
            Dict with enhanced validation results and transformed data
        """
        return await self.universal_adapter.validate_and_transform_for_firs(
            invoice_data, target_format
        )
    
    # Backward compatibility - delegate to original connector
    
    async def test_connection(self):
        """Test SAP connection - delegates to original connector."""
        return await self.universal_adapter.test_connection()
    
    async def authenticate(self):
        """Authenticate with SAP - delegates to original connector."""
        return await self.universal_adapter.authenticate()
    
    async def get_invoices(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        document_type: Optional[str] = None,
        include_attachments: bool = False,
        data_source: str = 'billing'
    ) -> List[Dict[str, Any]]:
        """
        Original get_invoices method for backward compatibility.
        
        Note: This method returns only the original invoice data without
        universal processing enhancements. Use get_invoices_with_processing()
        for enhanced functionality.
        """
        return await self.sap_connector.get_invoices(
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            document_type=document_type,
            include_attachments=include_attachments,
            data_source=data_source
        )
    
    async def get_invoice_by_id(self, invoice_id: str) -> Dict[str, Any]:
        """Original get_invoice_by_id method for backward compatibility."""
        return await self.sap_connector.get_invoice_by_id(invoice_id)
    
    async def search_invoices(
        self,
        customer_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        amount_range: Optional[tuple] = None,
        date_range: Optional[tuple] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Original search_invoices method for backward compatibility."""
        return await self.sap_connector.search_invoices(
            customer_name=customer_name,
            invoice_number=invoice_number,
            amount_range=amount_range,
            date_range=date_range,
            limit=limit
        )
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Original FIRS transformation method for backward compatibility."""
        return await self.sap_connector.transform_to_firs_format(invoice_data, target_format)
    
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Original validation method for backward compatibility."""
        return await self.sap_connector.validate_invoice_data(invoice_data)
    
    async def get_partners(
        self,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get business partners - delegates to original connector."""
        return await self.universal_adapter.get_partners(search_term, limit, offset)
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration - delegates to original connector."""
        return await self.universal_adapter.get_tax_configuration()
    
    async def disconnect(self):
        """Disconnect from SAP - delegates to original connector."""
        return await self.universal_adapter.disconnect()
    
    def is_connected(self) -> bool:
        """Check connection status - delegates to original connector."""
        return self.universal_adapter.is_connected()
    
    # Enhanced status and statistics methods
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get enhanced connection status including universal processing statistics."""
        return self.universal_adapter.get_connection_status()
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get detailed processing statistics from universal adapter."""
        return self.universal_adapter.get_processing_statistics()
    
    # Utility methods for demonstration
    
    async def demonstrate_processing_comparison(
        self,
        invoice_id: str
    ) -> Dict[str, Any]:
        """
        Demonstrate the difference between original and universal processing.
        
        This method fetches the same invoice using both approaches and compares
        the results to show the value added by universal processing.
        """
        try:
            # Get invoice using original method
            original_result = await self.get_invoice_by_id(invoice_id)
            
            # Get invoice using universal processing
            enhanced_result = await self.get_invoice_by_id_with_processing(invoice_id)
            
            return {
                'invoice_id': invoice_id,
                'original_result': original_result,
                'enhanced_result': enhanced_result,
                'processing_improvements': {
                    'validation_applied': enhanced_result.get('processing_result', {}).get('success', False),
                    'risk_assessment': enhanced_result.get('processed_invoice', {}).get('risk_assessment', {}),
                    'customer_matching': enhanced_result.get('processed_invoice', {}).get('customer_info', {}),
                    'nigerian_compliance': enhanced_result.get('processed_invoice', {}).get('nigerian_compliance_info', {}),
                    'processing_time': enhanced_result.get('processing_time', 0.0)
                },
                'value_added': [
                    "Nigerian regulatory compliance validation",
                    "Enhanced risk assessment and fraud detection",
                    "Automatic customer matching and enrichment",
                    "Transaction categorization and pattern recognition",
                    "Standardized data quality checks",
                    "Processing performance metrics"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in processing comparison: {e}")
            return {
                'invoice_id': invoice_id,
                'error': str(e),
                'comparison_failed': True
            }
    
    async def get_nigerian_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Generate a Nigerian compliance report for SAP invoices.
        
        This method demonstrates how universal processing enables comprehensive
        compliance reporting across all transactions.
        """
        try:
            # Default to last 30 days if no date range provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Get invoices with universal processing
            result = await self.get_invoices_with_processing(
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            processed_invoices = result.get('processed_invoices', [])
            
            if not processed_invoices:
                return {
                    'period': f"{start_date.date()} to {end_date.date()}",
                    'total_invoices': 0,
                    'compliance_summary': {},
                    'message': 'No processed invoices found for the specified period'
                }
            
            # Analyze compliance
            total_count = len(processed_invoices)
            compliant_count = sum(1 for inv in processed_invoices if inv.is_nigerian_compliant())
            high_risk_count = sum(1 for inv in processed_invoices if inv.requires_manual_review())
            ready_for_firs = sum(1 for inv in processed_invoices if inv.is_ready_for_invoice())
            
            # Collect regulatory flags
            all_flags = []
            for inv in processed_invoices:
                if hasattr(inv, 'enrichment_data') and inv.enrichment_data.regulatory_flags:
                    all_flags.extend(inv.enrichment_data.regulatory_flags)
            
            flag_summary = {}
            for flag in all_flags:
                flag_summary[flag] = flag_summary.get(flag, 0) + 1
            
            return {
                'period': f"{start_date.date()} to {end_date.date()}",
                'total_invoices': total_count,
                'compliance_summary': {
                    'compliant_invoices': compliant_count,
                    'compliance_rate': compliant_count / total_count if total_count > 0 else 0,
                    'high_risk_invoices': high_risk_count,
                    'risk_rate': high_risk_count / total_count if total_count > 0 else 0,
                    'firs_ready_invoices': ready_for_firs,
                    'firs_ready_rate': ready_for_firs / total_count if total_count > 0 else 0
                },
                'regulatory_flags': flag_summary,
                'recommendations': self._generate_compliance_recommendations(
                    compliant_count, high_risk_count, total_count, flag_summary
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {
                'error': str(e),
                'report_failed': True
            }
    
    def _generate_compliance_recommendations(
        self,
        compliant_count: int,
        high_risk_count: int,
        total_count: int,
        flag_summary: Dict[str, int]
    ) -> List[str]:
        """Generate compliance recommendations based on analysis."""
        recommendations = []
        
        compliance_rate = compliant_count / total_count if total_count > 0 else 0
        risk_rate = high_risk_count / total_count if total_count > 0 else 0
        
        if compliance_rate < 0.8:
            recommendations.append("Compliance rate is below 80%. Review SAP invoice data quality and Nigerian business rules configuration.")
        
        if risk_rate > 0.1:
            recommendations.append("High risk transaction rate exceeds 10%. Implement additional validation checks in SAP system.")
        
        if 'VAT_CALCULATION_ERROR' in flag_summary:
            recommendations.append("VAT calculation errors detected. Verify SAP tax configuration matches Nigerian VAT rate of 7.5%.")
        
        if 'MISSING_CUSTOMER_INFO' in flag_summary:
            recommendations.append("Customer information gaps found. Ensure SAP customer master data is complete.")
        
        if not recommendations:
            recommendations.append("Compliance performance is good. Continue monitoring and consider implementing proactive compliance checks.")
        
        return recommendations


def create_sap_universal_connector(
    sap_config: Dict[str, Any],
    enable_universal_processing: bool = True
) -> SAPUniversalConnector:
    """
    Factory function to create a SAP connector with universal processing capabilities.
    
    Args:
        sap_config: SAP connection configuration
        enable_universal_processing: Enable universal processing pipeline
        
    Returns:
        SAPUniversalConnector instance
    """
    return SAPUniversalConnector(sap_config, enable_universal_processing)


# Example usage and testing functions

async def example_sap_universal_usage():
    """
    Example demonstrating how to use the SAP universal connector.
    
    This function shows typical usage patterns and the benefits of
    universal processing for SAP ERP integration.
    """
    # Sample SAP configuration
    sap_config = {
        'base_url': 'https://your-sap-system.com',
        'username': 'your_username',
        'password': 'your_password',
        'use_oauth': False,
        'verify_ssl': True
    }
    
    # Create SAP connector with universal processing
    sap_connector = create_sap_universal_connector(sap_config)
    
    try:
        # Test connection
        connection_result = await sap_connector.test_connection()
        if not connection_result.success:
            print(f"Connection failed: {connection_result.message}")
            return
        
        print("✅ SAP connection successful")
        
        # Get invoices with enhanced processing
        print("\n📊 Fetching invoices with universal processing...")
        invoices_result = await sap_connector.get_invoices_with_processing(limit=10)
        
        print(f"📈 Processing Results:")
        print(f"  - Total invoices: {invoices_result['total_count']}")
        print(f"  - Successfully processed: {invoices_result['processed_count']}")
        print(f"  - Processing time: {invoices_result['processing_time']:.2f}s")
        print(f"  - Universal processing: {'✅ Enabled' if invoices_result['processing_enabled'] else '❌ Disabled'}")
        
        # Show processing benefits
        if invoices_result['processed_invoices']:
            sample_processed = invoices_result['processed_invoices'][0]
            print(f"\n🎯 Sample Processing Benefits:")
            print(f"  - Risk assessment: {sample_processed.get_risk_assessment()['level']}")
            print(f"  - Confidence score: {sample_processed.processing_metadata.confidence_score:.2f}")
            print(f"  - Nigerian compliant: {'✅' if sample_processed.is_nigerian_compliant() else '❌'}")
            print(f"  - Ready for FIRS: {'✅' if sample_processed.is_ready_for_invoice() else '❌'}")
        
        # Generate compliance report
        print("\n📋 Generating Nigerian compliance report...")
        compliance_report = await sap_connector.get_nigerian_compliance_report(limit=50)
        
        if 'compliance_summary' in compliance_report:
            summary = compliance_report['compliance_summary']
            print(f"🏛️ Compliance Summary:")
            print(f"  - Compliance rate: {summary['compliance_rate']:.1%}")
            print(f"  - FIRS ready rate: {summary['firs_ready_rate']:.1%}")
            print(f"  - High risk rate: {summary['risk_rate']:.1%}")
        
        # Show processing statistics
        print("\n📊 Processing Statistics:")
        stats = sap_connector.get_processing_statistics()
        adapter_stats = stats.get('adapter_stats', {})
        print(f"  - Total processed: {adapter_stats.get('total_processed', 0)}")
        print(f"  - Universal processed: {adapter_stats.get('universal_processed', 0)}")
        print(f"  - Average processing time: {adapter_stats.get('average_processing_time', 0):.3f}s")
        
        print("\n✅ SAP Universal Processing demonstration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        logger.error(f"SAP universal processing example failed: {e}")
    
    finally:
        # Clean up connection
        await sap_connector.disconnect()


if __name__ == "__main__":
    import asyncio
    
    # Run the example
    asyncio.run(example_sap_universal_usage())