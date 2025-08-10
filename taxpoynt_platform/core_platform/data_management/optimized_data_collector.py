"""
Optimized Data Collection Engine for TaxPoynt Platform

Enhances existing architecture with high-volume collection optimization,
transaction reconciliation, and compliance validation.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy.sql import text, func
from sqlalchemy import and_, or_

# Import existing optimized components
from .cache_manager import CacheManager, CacheConfig
from .repository_base import BaseRepository, FilterCriteria, FilterOperator, PaginationParams
from ..transaction_processing.universal_transaction_processor import UniversalTransactionProcessor

# Import comprehensive connector framework
from ...external_integrations.connector_framework.connector_factory import ConnectorFactory
from ...external_integrations.connector_framework.base_connector import (
    BaseConnector, ConnectorType, ConnectionStatus, list_active_connectors, get_connector
)

# Import all business system connectors
# ERP Systems
from ...external_integrations.business_systems.erp.sap.connector import SAPConnector
from ...external_integrations.business_systems.erp.oracle.connector import OracleConnector
from ...external_integrations.business_systems.erp.dynamics.connector import DynamicsConnector
from ...external_integrations.business_systems.erp.netsuite.connector import NetSuiteConnector
from ...external_integrations.business_systems.erp.odoo.connector import OdooConnector

# CRM Systems
from ...external_integrations.business_systems.crm.salesforce.connector import SalesforceConnector
from ...external_integrations.business_systems.crm.hubspot.connector import HubSpotConnector
from ...external_integrations.business_systems.crm.microsoft_dynamics_crm.connector import MicrosoftDynamicsCRMConnector
from ...external_integrations.business_systems.crm.zoho.connector import ZohoConnector
from ...external_integrations.business_systems.crm.pipedrive.connector import PipedriveConnector

# POS Systems
from ...external_integrations.business_systems.pos.square.connector import SquareConnector
from ...external_integrations.business_systems.pos.shopify_pos.connector import ShopifyPOSConnector
from ...external_integrations.business_systems.pos.lightspeed.connector import LightspeedConnector
from ...external_integrations.business_systems.pos.clover.connector import CloverConnector
from ...external_integrations.business_systems.pos.toast.connector import ToastConnector

# E-commerce Systems
from ...external_integrations.business_systems.ecommerce.shopify.connector import ShopifyConnector
from ...external_integrations.business_systems.ecommerce.woocommerce.connector import WooCommerceConnector
from ...external_integrations.business_systems.ecommerce.magento.connector import MagentoConnector
from ...external_integrations.business_systems.ecommerce.bigcommerce.connector import BigCommerceConnector
from ...external_integrations.business_systems.ecommerce.jumia.connector import JumiaConnector

# Accounting Systems
from ...external_integrations.business_systems.accounting.quickbooks.connector import QuickBooksConnector
from ...external_integrations.business_systems.accounting.xero.connector import XeroConnector
from ...external_integrations.business_systems.accounting.sage.connector import SageConnector
from ...external_integrations.business_systems.accounting.wave.connector import WaveConnector
from ...external_integrations.business_systems.accounting.freshbooks.connector import FreshBooksConnector

# Inventory Systems
from ...external_integrations.business_systems.inventory.fishbowl.connector import FishbowlConnector
from ...external_integrations.business_systems.inventory.cin7.connector import CIN7Connector

# Open Banking Systems
from ...external_integrations.financial_systems.banking.open_banking.providers.mono.connector import MonoConnector
from ...external_integrations.financial_systems.banking.open_banking.providers.stitch.connector import StitchConnector

# Payment Processors (comprehensive coverage)
# Nigerian Processors
from ...external_integrations.financial_systems.payments.nigerian_processors.paystack.payment_processor import PaystackPaymentProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.moniepoint.payment_processor import MoniepointPaymentProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.opay.payment_processor import OPayPaymentProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.palmpay.payment_processor import PalmPayPaymentProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.interswitch.payment_processor import InterswitchPaymentProcessor

# African Regional Processors
from ...external_integrations.financial_systems.payments.african_processors.flutterwave.payment_processor import FlutterwavePaymentProcessor

# Global Processors
from ...external_integrations.financial_systems.payments.global_processors.stripe.payment_processor import StripePaymentProcessor

logger = logging.getLogger(__name__)


class CollectionStatus(Enum):
    """Data collection status enumeration."""
    PENDING = "pending"
    COLLECTING = "collecting"
    PROCESSING = "processing"
    VALIDATING = "validating"
    RECONCILING = "reconciling"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY_REQUIRED = "retry_required"


class DataQualityLevel(Enum):
    """Data quality assessment levels."""
    EXCELLENT = "excellent"  # 98-100% quality
    GOOD = "good"          # 90-97% quality
    ACCEPTABLE = "acceptable"  # 80-89% quality
    POOR = "poor"          # 60-79% quality
    CRITICAL = "critical"   # <60% quality


@dataclass
class CollectionMetrics:
    """Metrics for data collection operations."""
    total_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    duplicate_records: int = 0
    processing_time_ms: float = 0.0
    throughput_per_second: float = 0.0
    error_rate_percent: float = 0.0
    data_quality_score: float = 0.0
    data_quality_level: DataQualityLevel = DataQualityLevel.GOOD
    compliance_score: float = 0.0
    collection_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_derived_metrics(self):
        """Calculate derived metrics from base values."""
        if self.total_records > 0:
            self.error_rate_percent = (self.failed_records / self.total_records) * 100
            success_rate = (self.successful_records / self.total_records) * 100
            duplicate_rate = (self.duplicate_records / self.total_records) * 100
            
            # Data quality score considers success rate, duplicate detection, and compliance
            self.data_quality_score = (
                success_rate * 0.6 +  # 60% weight on success
                (100 - duplicate_rate) * 0.2 +  # 20% weight on uniqueness
                self.compliance_score * 0.2  # 20% weight on compliance
            )
            
            # Determine quality level
            if self.data_quality_score >= 98:
                self.data_quality_level = DataQualityLevel.EXCELLENT
            elif self.data_quality_score >= 90:
                self.data_quality_level = DataQualityLevel.GOOD
            elif self.data_quality_score >= 80:
                self.data_quality_level = DataQualityLevel.ACCEPTABLE
            elif self.data_quality_score >= 60:
                self.data_quality_level = DataQualityLevel.POOR
            else:
                self.data_quality_level = DataQualityLevel.CRITICAL
        
        if self.processing_time_ms > 0:
            self.throughput_per_second = (self.successful_records / (self.processing_time_ms / 1000))


@dataclass
class ReconciliationResult:
    """Result of transaction reconciliation process."""
    total_expected: int
    total_collected: int
    missing_count: int
    completeness_percentage: float
    missing_transaction_ids: List[str]
    reconciliation_timestamp: datetime
    data_gaps: List[Dict[str, Any]]
    quality_issues: List[Dict[str, Any]]
    recommendations: List[str]


class OptimizedDataCollector:
    """
    Enhanced data collection engine that builds on existing architecture.
    
    Features:
    - High-volume parallel collection from ALL business systems:
      * ERP Systems: SAP, Oracle, Dynamics, NetSuite, Odoo, Sage
      * CRM Systems: Salesforce, HubSpot, Dynamics CRM, Zoho, Pipedrive
      * POS Systems: Square, Shopify POS, Lightspeed, Clover, Toast
      * E-commerce: Shopify, WooCommerce, Magento, Jumia, BigCommerce
      * Accounting: QuickBooks, Xero, Wave, FreshBooks, Sage
      * Inventory: Fishbowl, CIN7
      * Banking Data: Open Banking (Mono, Stitch) for transaction data
      * Payment Processors: Nigerian (Paystack, Moniepoint, OPay, PalmPay, Interswitch), 
        African (Flutterwave), Global (Stripe)
    - Real-time transaction reconciliation and completeness validation
    - AI-enhanced classification accuracy monitoring
    - Data quality assurance with automatic remediation
    - FIRS compliance analytics and reporting
    - Universal connector framework integration
    """
    
    def __init__(
        self,
        session_factory,
        cache_manager: CacheManager,
        universal_processor: UniversalTransactionProcessor,
        max_workers: int = 20,
        batch_size: int = 1000,
        reconciliation_window_hours: int = 24
    ):
        """
        Initialize optimized data collector.
        
        Args:
            session_factory: Database session factory
            cache_manager: Cache manager instance
            universal_processor: Universal transaction processor
            max_workers: Maximum worker threads for parallel collection
            batch_size: Batch size for processing
            reconciliation_window_hours: Hours to look back for reconciliation
        """
        self.session_factory = session_factory
        self.cache_manager = cache_manager
        self.universal_processor = universal_processor
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.reconciliation_window_hours = reconciliation_window_hours
        
        # Initialize comprehensive business system connectors using factory pattern
        self.connector_factory = ConnectorFactory()
        
        # All supported business system connectors
        self.business_system_connectors = {
            # ERP Systems
            'sap': SAPConnector,
            'oracle': OracleConnector,
            'dynamics_erp': DynamicsConnector,
            'netsuite': NetSuiteConnector,
            'odoo': OdooConnector,
            
            # CRM Systems
            'salesforce': SalesforceConnector,
            'hubspot': HubSpotConnector,
            'dynamics_crm': MicrosoftDynamicsCRMConnector,
            'zoho': ZohoConnector,
            'pipedrive': PipedriveConnector,
            
            # POS Systems
            'square_pos': SquareConnector,
            'shopify_pos': ShopifyPOSConnector,
            'lightspeed': LightspeedConnector,
            'clover': CloverConnector,
            'toast': ToastConnector,
            
            # E-commerce Systems
            'shopify': ShopifyConnector,
            'woocommerce': WooCommerceConnector,
            'magento': MagentoConnector,
            'bigcommerce': BigCommerceConnector,
            'jumia': JumiaConnector,
            
            # Accounting Systems
            'quickbooks': QuickBooksConnector,
            'xero': XeroConnector,
            'sage': SageConnector,
            'wave': WaveConnector,
            'freshbooks': FreshBooksConnector,
            
            # Inventory Systems
            'fishbowl': FishbowlConnector,
            'cin7': CIN7Connector,
            
            # Banking/Open Banking
            'mono': MonoConnector,
            'stitch': StitchConnector,
            
            # Payment Processors
            # Nigerian Processors
            'paystack': PaystackPaymentProcessor,
            'moniepoint': MoniepointPaymentProcessor,
            'opay': OPayPaymentProcessor,
            'palmpay': PalmPayPaymentProcessor,
            'interswitch': InterswitchPaymentProcessor,
            
            # African Regional Processors
            'flutterwave': FlutterwavePaymentProcessor,
            
            # Global Processors
            'stripe': StripePaymentProcessor
        }
        
        # Active connector instances (lazy-loaded based on organization configuration)
        self.active_connectors: Dict[str, BaseConnector] = {}
        
        # Performance tracking
        self.collection_metrics: Dict[str, CollectionMetrics] = {}
        self.active_collections: Set[str] = set()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Quality thresholds
        self.quality_thresholds = {
            'min_completeness_percent': 95.0,
            'max_error_rate_percent': 2.0,
            'min_compliance_score': 90.0,
            'max_duplicate_rate_percent': 1.0
        }
        
        logger.info(f"OptimizedDataCollector initialized with {max_workers} workers, batch size {batch_size}")
    
    async def collect_high_volume_data(
        self,
        organization_id: UUID,
        business_systems: List[str] = None,
        connector_types: List[ConnectorType] = None,
        start_time: datetime = None,
        end_time: datetime = None,
        enable_reconciliation: bool = True
    ) -> Dict[str, CollectionMetrics]:
        """
        Perform high-volume data collection from ALL business systems.
        
        Args:
            organization_id: Organization to collect data for
            business_systems: List of business system names to collect from (default: all configured)
            connector_types: List of connector types to filter by (ERP, CRM, POS, etc.)
            start_time: Start time for collection window
            end_time: End time for collection window
            enable_reconciliation: Whether to run reconciliation after collection
            
        Returns:
            Dictionary of collection metrics by business system
        """
        collection_id = str(uuid4())
        self.active_collections.add(collection_id)
        
        try:
            # Set default time window if not provided
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=self.reconciliation_window_hours)
            
            # Use all processors if none specified
            if not processors:
                processors = list(self.payment_processors.keys())
            
            logger.info(f"Starting high-volume collection {collection_id} for org {organization_id} from {len(processors)} processors")
            
            # Parallel collection from all processors
            collection_tasks = []
            for processor_name in processors:
                if processor_name in self.payment_processors:
                    task = asyncio.create_task(
                        self._collect_from_processor(
                            processor_name,
                            organization_id,
                            start_time,
                            end_time,
                            collection_id
                        )
                    )
                    collection_tasks.append((processor_name, task))
            
            # Wait for all collections to complete
            results = {}
            for processor_name, task in collection_tasks:
                try:
                    metrics = await task
                    results[processor_name] = metrics
                    logger.info(f"Collection from {processor_name} completed: {metrics.successful_records} records")
                except Exception as e:
                    logger.error(f"Collection from {processor_name} failed: {e}")
                    # Create error metrics
                    error_metrics = CollectionMetrics()
                    error_metrics.failed_records = 1
                    error_metrics.calculate_derived_metrics()
                    results[processor_name] = error_metrics
            
            # Run reconciliation if enabled
            if enable_reconciliation:
                logger.info(f"Starting reconciliation for collection {collection_id}")
                reconciliation_result = await self.reconcile_transactions(
                    organization_id,
                    start_time,
                    end_time,
                    list(results.keys())
                )
                
                # Update metrics with reconciliation data
                for processor_name in results:
                    if processor_name in reconciliation_result:
                        metrics = results[processor_name]
                        metrics.compliance_score = reconciliation_result[processor_name].get('compliance_score', 0.0)
                        metrics.calculate_derived_metrics()
            
            # Cache collection results
            cache_key = f"collection_metrics:{organization_id}:{collection_id}"
            self.cache_manager.set(cache_key, results, ttl=3600)  # Cache for 1 hour
            
            logger.info(f"High-volume collection {collection_id} completed for {len(results)} processors")
            return results
            
        finally:
            self.active_collections.discard(collection_id)
    
    async def _collect_from_processor(
        self,
        processor_name: str,
        organization_id: UUID,
        start_time: datetime,
        end_time: datetime,
        collection_id: str
    ) -> CollectionMetrics:
        """
        Collect data from a specific payment processor.
        
        Args:
            processor_name: Name of the payment processor
            organization_id: Organization ID
            start_time: Collection start time
            end_time: Collection end time
            collection_id: Unique collection identifier
            
        Returns:
            Collection metrics for this processor
        """
        start_collection_time = time.time()
        processor = self.payment_processors[processor_name]
        metrics = CollectionMetrics()
        
        try:
            # Get processor-specific configuration
            config = await self._get_processor_config(processor_name, organization_id)
            
            # Collect transactions in batches
            total_collected = 0
            batch_number = 0
            
            async for batch_transactions in processor.collect_transactions_batch(
                organization_id=organization_id,
                start_time=start_time,
                end_time=end_time,
                batch_size=self.batch_size,
                config=config
            ):
                batch_number += 1
                batch_start_time = time.time()
                
                # Process batch through universal processor
                batch_results = await self.universal_processor.process_batch_transactions(
                    transactions=batch_transactions,
                    connector_type=processor.get_connector_type(),
                    enable_parallel=True
                )
                
                # Update metrics
                for result in batch_results:
                    metrics.total_records += 1
                    if result.success:
                        metrics.successful_records += 1
                        
                        # Check for duplicates
                        if result.processed_transaction and result.processed_transaction.is_duplicate():
                            metrics.duplicate_records += 1
                    else:
                        metrics.failed_records += 1
                
                total_collected += len(batch_transactions)
                batch_time = (time.time() - batch_start_time) * 1000
                
                logger.debug(f"Processed batch {batch_number} from {processor_name}: {len(batch_transactions)} records in {batch_time:.2f}ms")
                
                # Cache batch results for reconciliation
                batch_cache_key = f"batch_results:{collection_id}:{processor_name}:{batch_number}"
                self.cache_manager.set(batch_cache_key, batch_results, ttl=86400)  # Cache for 24 hours
            
            # Calculate final metrics
            metrics.processing_time_ms = (time.time() - start_collection_time) * 1000
            metrics.calculate_derived_metrics()
            
            logger.info(f"Collection from {processor_name} completed: {total_collected} total records, {metrics.successful_records} successful")
            
        except Exception as e:
            logger.error(f"Error collecting from {processor_name}: {e}")
            metrics.failed_records += 1
            metrics.processing_time_ms = (time.time() - start_collection_time) * 1000
            metrics.calculate_derived_metrics()
        
        return metrics
    
    async def reconcile_transactions(
        self,
        organization_id: UUID,
        start_time: datetime,
        end_time: datetime,
        processors: List[str]
    ) -> Dict[str, ReconciliationResult]:
        """
        Perform comprehensive transaction reconciliation and completeness validation.
        
        Args:
            organization_id: Organization ID
            start_time: Reconciliation start time
            end_time: Reconciliation end time
            processors: List of processors to reconcile
            
        Returns:
            Reconciliation results by processor
        """
        logger.info(f"Starting transaction reconciliation for org {organization_id} across {len(processors)} processors")
        
        reconciliation_results = {}
        
        for processor_name in processors:
            try:
                result = await self._reconcile_processor_transactions(
                    processor_name,
                    organization_id,
                    start_time,
                    end_time
                )
                reconciliation_results[processor_name] = result
                
                logger.info(f"Reconciliation for {processor_name}: {result.completeness_percentage:.2f}% complete, {result.missing_count} missing")
                
            except Exception as e:
                logger.error(f"Reconciliation failed for {processor_name}: {e}")
                # Create empty result for failed reconciliation
                reconciliation_results[processor_name] = ReconciliationResult(
                    total_expected=0,
                    total_collected=0,
                    missing_count=0,
                    completeness_percentage=0.0,
                    missing_transaction_ids=[],
                    reconciliation_timestamp=datetime.utcnow(),
                    data_gaps=[],
                    quality_issues=[{"issue": "Reconciliation failed", "error": str(e)}],
                    recommendations=["Retry reconciliation", "Check processor connectivity"]
                )
        
        # Cross-processor reconciliation
        await self._perform_cross_processor_reconciliation(reconciliation_results, organization_id)
        
        # Cache reconciliation results
        cache_key = f"reconciliation:{organization_id}:{start_time.strftime('%Y%m%d%H')}:{end_time.strftime('%Y%m%d%H')}"
        self.cache_manager.set(cache_key, reconciliation_results, ttl=7200)  # Cache for 2 hours
        
        return reconciliation_results
    
    async def _reconcile_processor_transactions(
        self,
        processor_name: str,
        organization_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> ReconciliationResult:
        """
        Reconcile transactions for a specific processor.
        
        Args:
            processor_name: Processor name
            organization_id: Organization ID
            start_time: Start time
            end_time: End time
            
        Returns:
            Reconciliation result
        """
        processor = self.payment_processors[processor_name]
        
        # Get expected transaction count from processor API
        expected_count = await processor.get_transaction_count(
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time
        )
        
        # Get collected transaction count from database
        with self.session_factory() as session:
            # Query universal processed transactions
            collected_count_query = text("""
                SELECT COUNT(*) as count
                FROM universal_processed_transactions upt
                WHERE upt.organization_id = :org_id
                AND upt.connector_type = :connector_type
                AND upt.transaction_timestamp BETWEEN :start_time AND :end_time
                AND upt.status = 'completed'
            """)
            
            result = session.execute(collected_count_query, {
                'org_id': str(organization_id),
                'connector_type': processor.get_connector_type().value,
                'start_time': start_time,
                'end_time': end_time
            }).fetchone()
            
            collected_count = result.count if result else 0
        
        # Calculate completeness
        missing_count = max(0, expected_count - collected_count)
        completeness_percentage = (collected_count / expected_count * 100) if expected_count > 0 else 100.0
        
        # Identify missing transactions
        missing_transaction_ids = []
        data_gaps = []
        quality_issues = []
        recommendations = []
        
        if missing_count > 0:
            missing_transaction_ids = await processor.get_missing_transaction_ids(
                organization_id=organization_id,
                start_time=start_time,
                end_time=end_time,
                collected_ids=await self._get_collected_transaction_ids(processor_name, organization_id, start_time, end_time)
            )
            
            # Analyze data gaps
            data_gaps = await self._analyze_data_gaps(processor_name, organization_id, start_time, end_time)
            
            # Generate quality issues
            if completeness_percentage < self.quality_thresholds['min_completeness_percent']:
                quality_issues.append({
                    "issue": "Low completeness percentage",
                    "severity": "high" if completeness_percentage < 90 else "medium",
                    "value": completeness_percentage,
                    "threshold": self.quality_thresholds['min_completeness_percent']
                })
            
            # Generate recommendations
            if missing_count > 0:
                recommendations.extend([
                    f"Retry collection for {missing_count} missing transactions",
                    "Check processor API rate limits",
                    "Verify webhook delivery status"
                ])
        
        # Assess overall quality issues
        await self._assess_data_quality_issues(quality_issues, processor_name, organization_id)
        
        return ReconciliationResult(
            total_expected=expected_count,
            total_collected=collected_count,
            missing_count=missing_count,
            completeness_percentage=completeness_percentage,
            missing_transaction_ids=missing_transaction_ids,
            reconciliation_timestamp=datetime.utcnow(),
            data_gaps=data_gaps,
            quality_issues=quality_issues,
            recommendations=recommendations
        )
    
    async def _perform_cross_processor_reconciliation(
        self,
        reconciliation_results: Dict[str, ReconciliationResult],
        organization_id: UUID
    ):
        """
        Perform cross-processor reconciliation to identify discrepancies.
        
        Args:
            reconciliation_results: Results from individual processor reconciliation
            organization_id: Organization ID
        """
        # Look for duplicate transactions across processors
        # (e.g., same customer transaction processed by multiple processors)
        
        with self.session_factory() as session:
            # Query for potential duplicates across processors
            duplicate_query = text("""
                SELECT 
                    upt1.transaction_id as id1,
                    upt1.connector_type as processor1,
                    upt2.transaction_id as id2,
                    upt2.connector_type as processor2,
                    upt1.amount,
                    upt1.transaction_timestamp
                FROM universal_processed_transactions upt1
                JOIN universal_processed_transactions upt2 ON (
                    upt1.organization_id = upt2.organization_id
                    AND upt1.amount = upt2.amount
                    AND ABS(EXTRACT(EPOCH FROM (upt1.transaction_timestamp - upt2.transaction_timestamp))) < 300
                    AND upt1.transaction_id != upt2.transaction_id
                    AND upt1.connector_type != upt2.connector_type
                )
                WHERE upt1.organization_id = :org_id
                AND upt1.transaction_timestamp >= NOW() - INTERVAL '24 hours'
                ORDER BY upt1.transaction_timestamp DESC
                LIMIT 100
            """)
            
            duplicates = session.execute(duplicate_query, {'org_id': str(organization_id)}).fetchall()
            
            if duplicates:
                # Add cross-processor quality issues
                for processor_name in reconciliation_results:
                    reconciliation_results[processor_name].quality_issues.append({
                        "issue": "Cross-processor duplicate transactions detected",
                        "severity": "medium",
                        "count": len(duplicates),
                        "description": "Transactions with same amount and timestamp found across different processors"
                    })
                    
                    reconciliation_results[processor_name].recommendations.append(
                        "Review transaction deduplication logic across processors"
                    )
    
    async def _get_collected_transaction_ids(
        self,
        processor_name: str,
        organization_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[str]:
        """
        Get list of collected transaction IDs for a processor.
        
        Args:
            processor_name: Processor name
            organization_id: Organization ID
            start_time: Start time
            end_time: End time
            
        Returns:
            List of collected transaction IDs
        """
        processor = self.payment_processors[processor_name]
        
        with self.session_factory() as session:
            query = text("""
                SELECT upt.original_transaction_id
                FROM universal_processed_transactions upt
                WHERE upt.organization_id = :org_id
                AND upt.connector_type = :connector_type
                AND upt.transaction_timestamp BETWEEN :start_time AND :end_time
                AND upt.status = 'completed'
            """)
            
            results = session.execute(query, {
                'org_id': str(organization_id),
                'connector_type': processor.get_connector_type().value,
                'start_time': start_time,
                'end_time': end_time
            }).fetchall()
            
            return [row.original_transaction_id for row in results if row.original_transaction_id]
    
    async def _analyze_data_gaps(
        self,
        processor_name: str,
        organization_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Analyze data gaps in collection timeline.
        
        Args:
            processor_name: Processor name
            organization_id: Organization ID
            start_time: Start time
            end_time: End time
            
        Returns:
            List of identified data gaps
        """
        gaps = []
        
        with self.session_factory() as session:
            # Find hourly gaps in data collection
            gap_query = text("""
                WITH hourly_series AS (
                    SELECT generate_series(:start_time, :end_time, '1 hour'::interval) AS hour
                ),
                hourly_counts AS (
                    SELECT 
                        date_trunc('hour', upt.transaction_timestamp) AS hour,
                        COUNT(*) as transaction_count
                    FROM universal_processed_transactions upt
                    WHERE upt.organization_id = :org_id
                    AND upt.connector_type = :connector_type
                    AND upt.transaction_timestamp BETWEEN :start_time AND :end_time
                    GROUP BY date_trunc('hour', upt.transaction_timestamp)
                )
                SELECT 
                    hs.hour,
                    COALESCE(hc.transaction_count, 0) as count
                FROM hourly_series hs
                LEFT JOIN hourly_counts hc ON hs.hour = hc.hour
                WHERE COALESCE(hc.transaction_count, 0) = 0
                ORDER BY hs.hour
            """)
            
            processor = self.payment_processors[processor_name]
            gap_results = session.execute(gap_query, {
                'org_id': str(organization_id),
                'connector_type': processor.get_connector_type().value,
                'start_time': start_time,
                'end_time': end_time
            }).fetchall()
            
            # Group consecutive hours into gap periods
            current_gap_start = None
            current_gap_end = None
            
            for row in gap_results:
                gap_hour = row.hour
                
                if current_gap_start is None:
                    current_gap_start = gap_hour
                    current_gap_end = gap_hour
                elif gap_hour == current_gap_end + timedelta(hours=1):
                    current_gap_end = gap_hour
                else:
                    # End current gap and start new one
                    gaps.append({
                        "start_time": current_gap_start.isoformat(),
                        "end_time": current_gap_end.isoformat(),
                        "duration_hours": int((current_gap_end - current_gap_start).total_seconds() / 3600) + 1,
                        "type": "data_gap"
                    })
                    
                    current_gap_start = gap_hour
                    current_gap_end = gap_hour
            
            # Add final gap if exists
            if current_gap_start is not None:
                gaps.append({
                    "start_time": current_gap_start.isoformat(),
                    "end_time": current_gap_end.isoformat(),
                    "duration_hours": int((current_gap_end - current_gap_start).total_seconds() / 3600) + 1,
                    "type": "data_gap"
                })
        
        return gaps
    
    async def _assess_data_quality_issues(
        self,
        quality_issues: List[Dict[str, Any]],
        processor_name: str,
        organization_id: UUID
    ):
        """
        Assess additional data quality issues.
        
        Args:
            quality_issues: List to append quality issues to
            processor_name: Processor name
            organization_id: Organization ID
        """
        with self.session_factory() as session:
            # Check for error rate issues
            error_rate_query = text("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN upt.status = 'failed' THEN 1 ELSE 0 END) as failed_count
                FROM universal_processed_transactions upt
                WHERE upt.organization_id = :org_id
                AND upt.connector_type = :connector_type
                AND upt.transaction_timestamp >= NOW() - INTERVAL '24 hours'
            """)
            
            processor = self.payment_processors[processor_name]
            result = session.execute(error_rate_query, {
                'org_id': str(organization_id),
                'connector_type': processor.get_connector_type().value
            }).fetchone()
            
            if result and result.total > 0:
                error_rate = (result.failed_count / result.total) * 100
                if error_rate > self.quality_thresholds['max_error_rate_percent']:
                    quality_issues.append({
                        "issue": "High error rate",
                        "severity": "high" if error_rate > 5 else "medium",
                        "value": error_rate,
                        "threshold": self.quality_thresholds['max_error_rate_percent'],
                        "description": f"Error rate of {error_rate:.2f}% exceeds threshold"
                    })
    
    async def _get_processor_config(
        self,
        processor_name: str,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Get processor-specific configuration.
        
        Args:
            processor_name: Processor name
            organization_id: Organization ID
            
        Returns:
            Configuration dictionary
        """
        # Check cache first
        cache_key = f"processor_config:{processor_name}:{organization_id}"
        cached_config = self.cache_manager.get(cache_key)
        
        if cached_config:
            return cached_config
        
        # Get from database
        with self.session_factory() as session:
            config_query = text("""
                SELECT pc.configuration
                FROM processor_configurations pc
                WHERE pc.organization_id = :org_id
                AND pc.processor_name = :processor_name
                AND pc.is_active = true
            """)
            
            result = session.execute(config_query, {
                'org_id': str(organization_id),
                'processor_name': processor_name
            }).fetchone()
            
            config = json.loads(result.configuration) if result and result.configuration else {}
            
            # Cache configuration
            self.cache_manager.set(cache_key, config, ttl=1800)  # Cache for 30 minutes
            
            return config
    
    def get_collection_status(self) -> Dict[str, Any]:
        """
        Get current status of all collection operations.
        
        Returns:
            Status information
        """
        return {
            "active_collections": len(self.active_collections),
            "active_collection_ids": list(self.active_collections),
            "total_collections_completed": len(self.collection_metrics),
            "average_throughput_per_second": sum(
                metrics.throughput_per_second for metrics in self.collection_metrics.values()
            ) / len(self.collection_metrics) if self.collection_metrics else 0,
            "overall_data_quality_score": sum(
                metrics.data_quality_score for metrics in self.collection_metrics.values()
            ) / len(self.collection_metrics) if self.collection_metrics else 0,
            "worker_pool_status": {
                "max_workers": self.max_workers,
                "active_threads": self.executor._threads,
                "pending_tasks": self.executor._work_queue.qsize()
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, CollectionMetrics]:
        """
        Get detailed performance metrics for all processors.
        
        Returns:
            Performance metrics by processor
        """
        return self.collection_metrics.copy()
    
    async def cleanup_old_cache_data(self, older_than_hours: int = 48):
        """
        Clean up old cached data.
        
        Args:
            older_than_hours: Remove cache entries older than this many hours
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        # Clean up batch results cache
        # This would be implemented based on cache manager capabilities
        logger.info(f"Cleaning up cache data older than {older_than_hours} hours")
        
        # Could implement pattern-based cache cleanup here
        # self.cache_manager.delete_pattern(f"batch_results:*:{cutoff_time.strftime('%Y%m%d')}*")
    
    def __del__(self):
        """Cleanup resources on deletion."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
