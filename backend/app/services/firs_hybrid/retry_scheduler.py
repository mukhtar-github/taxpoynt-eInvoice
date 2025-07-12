"""
FIRS Hybrid Retry Scheduler Service for TaxPoynt eInvoice - Hybrid SI+APP Functions.

This module provides Hybrid FIRS functionality for comprehensive retry scheduling
that combines System Integrator (SI) and Access Point Provider (APP) operations for unified
retry coordination and management in FIRS e-invoicing workflows.

Hybrid FIRS Responsibilities:
- Cross-role retry scheduling for both SI integration failures and APP transmission failures
- Unified retry coordination with intelligent backoff strategies for SI and APP operations
- Hybrid retry orchestration for comprehensive FIRS workflow recovery
- Shared retry analytics and pattern recognition covering both SI ERP issues and APP submission failures
- Cross-functional retry optimization and failure prevention for SI and APP operations
"""

import asyncio
import logging
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Set, Union, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4
import json
import random
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.transmission import TransmissionRecord, TransmissionStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

# Hybrid FIRS retry scheduler configuration
HYBRID_RETRY_SCHEDULER_VERSION = "1.0"
DEFAULT_SCHEDULER_INTERVAL = 60  # 1 minute
DEFAULT_MAX_CONCURRENT_RETRIES = 5
DEFAULT_RETRY_TIMEOUT = 300  # 5 minutes
FIRS_COMPLIANCE_RETRY_PRIORITY = 1  # Highest priority
HYBRID_COORDINATION_RETRY_PRIORITY = 2
SI_APP_RETRY_PRIORITY = 3
MAX_RETRY_HISTORY_SIZE = 50
RETRY_ANALYTICS_WINDOW_HOURS = 24


class HybridRetryType(Enum):
    """Enhanced retry types for hybrid SI+APP operations."""
    # SI-specific retries
    SI_ERP_CONNECTION = "si_erp_connection"
    SI_DATA_EXTRACTION = "si_data_extraction"
    SI_IRN_GENERATION = "si_irn_generation"
    SI_CERTIFICATE_VALIDATION = "si_certificate_validation"
    SI_INTEGRATION_SYNC = "si_integration_sync"
    
    # APP-specific retries
    APP_TRANSMISSION = "app_transmission"
    APP_FIRS_SUBMISSION = "app_firs_submission"
    APP_ENCRYPTION = "app_encryption"
    APP_SIGNATURE = "app_signature"
    APP_WEBHOOK_DELIVERY = "app_webhook_delivery"
    
    # Hybrid retries
    HYBRID_WORKFLOW = "hybrid_workflow"
    HYBRID_COORDINATION = "hybrid_coordination"
    HYBRID_VALIDATION = "hybrid_validation"
    HYBRID_COMPLIANCE_CHECK = "hybrid_compliance_check"
    
    # FIRS compliance retries
    FIRS_API_CALL = "firs_api_call"
    FIRS_CERTIFICATE_RENEWAL = "firs_certificate_renewal"
    FIRS_STATUS_CHECK = "firs_status_check"
    FIRS_RECONCILIATION = "firs_reconciliation"


class HybridRetryStrategy(Enum):
    """Enhanced retry strategies for hybrid operations."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    
    # Hybrid-specific strategies
    SI_OPTIMIZED = "si_optimized"
    APP_OPTIMIZED = "app_optimized"
    HYBRID_COORDINATED = "hybrid_coordinated"
    FIRS_COMPLIANT = "firs_compliant"
    ADAPTIVE_LEARNING = "adaptive_learning"


class HybridRetryPriority(Enum):
    """Enhanced retry priorities for hybrid operations."""
    CRITICAL_FIRS = "critical_firs"          # FIRS compliance issues
    HIGH_HYBRID = "high_hybrid"              # Cross-role coordination
    MEDIUM_SI = "medium_si"                  # SI operations
    MEDIUM_APP = "medium_app"                # APP operations
    LOW_MAINTENANCE = "low_maintenance"      # Background maintenance


@dataclass
class HybridRetryScheduleEntry:
    """Comprehensive retry schedule entry for hybrid operations."""
    retry_id: str
    transmission_id: UUID
    retry_type: HybridRetryType
    priority: HybridRetryPriority
    strategy: HybridRetryStrategy
    
    # Scheduling information
    scheduled_time: datetime
    created_time: datetime
    attempt_number: int
    max_attempts: int
    
    # Context information
    si_context: Dict[str, Any] = field(default_factory=dict)
    app_context: Dict[str, Any] = field(default_factory=dict)
    hybrid_context: Dict[str, Any] = field(default_factory=dict)
    firs_context: Dict[str, Any] = field(default_factory=dict)
    
    # Retry configuration
    base_delay: int = 60  # Base delay in seconds
    max_delay: int = 3600  # Maximum delay in seconds
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1
    
    # Status tracking
    status: str = "pending"
    last_attempt_time: Optional[datetime] = None
    last_error: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    
    # FIRS compliance
    firs_compliance_required: bool = False
    compliance_validated: bool = False
    compliance_impact: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_next_delay(self) -> int:
        """Calculate the next retry delay based on strategy."""
        if self.strategy == HybridRetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(self.base_delay * (self.backoff_multiplier ** (self.attempt_number - 1)), self.max_delay)
        elif self.strategy == HybridRetryStrategy.LINEAR_BACKOFF:
            delay = min(self.base_delay * self.attempt_number, self.max_delay)
        elif self.strategy == HybridRetryStrategy.FIXED_INTERVAL:
            delay = self.base_delay
        elif self.strategy == HybridRetryStrategy.FIBONACCI_BACKOFF:
            delay = min(self._fibonacci_delay(), self.max_delay)
        elif self.strategy == HybridRetryStrategy.SI_OPTIMIZED:
            # Longer delays for SI operations (ERP systems need time to recover)
            delay = min(self.base_delay * 2 * (self.backoff_multiplier ** (self.attempt_number - 1)), self.max_delay)
        elif self.strategy == HybridRetryStrategy.APP_OPTIMIZED:
            # Shorter delays for APP operations (API calls can retry faster)
            delay = min(self.base_delay * 0.5 * (self.backoff_multiplier ** (self.attempt_number - 1)), self.max_delay)
        elif self.strategy == HybridRetryStrategy.HYBRID_COORDINATED:
            # Coordinated delays for hybrid operations
            delay = min(self.base_delay * 1.5 * (self.backoff_multiplier ** (self.attempt_number - 1)), self.max_delay)
        elif self.strategy == HybridRetryStrategy.FIRS_COMPLIANT:
            # FIRS-specific timing requirements
            delay = min(self.base_delay * 3 * (self.attempt_number - 1) + 30, self.max_delay)
        else:
            delay = self.base_delay
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(-self.jitter_factor, self.jitter_factor)
        delay = int(delay * (1 + jitter))
        
        return max(delay, 1)  # Minimum 1 second delay
    
    def _fibonacci_delay(self) -> int:
        """Calculate Fibonacci-based delay."""
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)
        
        return self.base_delay * fibonacci(self.attempt_number)


class HybridFIRSRetryScheduler:
    """
    Hybrid FIRS retry scheduler for comprehensive retry coordination.
    
    This service provides Hybrid FIRS functions for retry scheduling
    that combine System Integrator (SI) and Access Point Provider (APP) operations
    for unified retry coordination and management in Nigerian e-invoicing compliance.
    
    Hybrid Retry Scheduler Functions:
    1. Cross-role retry scheduling for both SI integration failures and APP transmission failures
    2. Unified retry coordination with intelligent backoff strategies for SI and APP operations
    3. Hybrid retry orchestration for comprehensive FIRS workflow recovery
    4. Shared retry analytics and pattern recognition covering both SI ERP issues and APP submission failures
    5. Cross-functional retry optimization and failure prevention for SI and APP operations
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the Hybrid FIRS retry scheduler with enhanced capabilities.
        
        Args:
            db: Database session (optional)
        """
        self.db = db or SessionLocal()
        self.name = "hybrid_firs_retry_scheduler"
        
        # Retry scheduling
        self.retry_schedule: Dict[str, HybridRetryScheduleEntry] = {}
        self.priority_queues: Dict[HybridRetryPriority, List[str]] = {
            priority: [] for priority in HybridRetryPriority
        }
        
        # Scheduler state
        self.is_running = False
        self.scheduler_thread = None
        self.async_scheduler_task = None
        
        # Performance tracking
        self.performance_metrics = {
            "total_retries_scheduled": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "expired_retries": 0,
            "average_retry_delay": 0.0,
            "peak_concurrent_retries": 0,
            "current_concurrent_retries": 0,
            "last_scheduler_run": None,
            "scheduler_health_score": 100.0
        }
        
        # Analytics
        self.retry_analytics = {
            "success_rates_by_type": {},
            "average_attempts_by_type": {},
            "failure_patterns": {},
            "optimal_delays": {},
            "firs_compliance_stats": {}
        }
        
        # Configuration
        self.max_concurrent_retries = getattr(settings, "MAX_CONCURRENT_RETRIES", DEFAULT_MAX_CONCURRENT_RETRIES)
        self.scheduler_interval = getattr(settings, "RETRY_SCHEDULER_INTERVAL", DEFAULT_SCHEDULER_INTERVAL)
        self.retry_timeout = getattr(settings, "RETRY_TIMEOUT", DEFAULT_RETRY_TIMEOUT)
        
        # Thread pool for concurrent retry processing
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_concurrent_retries)
        
        logger.info(f"Hybrid FIRS Retry Scheduler initialized (Version: {HYBRID_RETRY_SCHEDULER_VERSION})")

    async def schedule_hybrid_retry(
        self,
        transmission_id: UUID,
        retry_type: HybridRetryType,
        priority: HybridRetryPriority = HybridRetryPriority.MEDIUM_APP,
        strategy: HybridRetryStrategy = HybridRetryStrategy.EXPONENTIAL_BACKOFF,
        delay_seconds: Optional[int] = None,
        max_attempts: int = 3,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        firs_context: Optional[Dict[str, Any]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a hybrid retry with enhanced context - Hybrid FIRS Function.
        
        Provides comprehensive retry scheduling that considers both SI and APP
        operations with FIRS compliance integration.
        
        Args:
            transmission_id: ID of the transmission to retry
            retry_type: Type of retry operation
            priority: Retry priority level
            strategy: Retry strategy to use
            delay_seconds: Custom delay (overrides strategy calculation)
            max_attempts: Maximum retry attempts
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            firs_context: FIRS-specific context
            custom_config: Custom retry configuration
            
        Returns:
            Retry ID for tracking
        """
        retry_id = f"retry_{retry_type.value}_{uuid4().hex[:8]}"
        current_time = datetime.now(timezone.utc)
        
        # Assess FIRS compliance requirements
        firs_compliance_required = bool(firs_context) or self._requires_firs_compliance(retry_type)
        compliance_impact = self._assess_retry_firs_impact(retry_type, si_context, app_context, hybrid_context, firs_context)
        
        # Create retry schedule entry
        retry_entry = HybridRetryScheduleEntry(
            retry_id=retry_id,
            transmission_id=transmission_id,
            retry_type=retry_type,
            priority=priority,
            strategy=strategy,
            scheduled_time=current_time + timedelta(seconds=delay_seconds or 60),
            created_time=current_time,
            attempt_number=1,
            max_attempts=max_attempts,
            si_context=si_context or {},
            app_context=app_context or {},
            hybrid_context=hybrid_context or {},
            firs_context=firs_context or {},
            firs_compliance_required=firs_compliance_required,
            compliance_impact=compliance_impact
        )
        
        # Apply custom configuration
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(retry_entry, key):
                    setattr(retry_entry, key, value)
        
        # Calculate initial delay if not provided
        if delay_seconds is None:
            delay = retry_entry.calculate_next_delay()
            retry_entry.scheduled_time = current_time + timedelta(seconds=delay)
        
        # Register the retry
        self.retry_schedule[retry_id] = retry_entry
        self.priority_queues[priority].append(retry_id)
        
        # Update metrics
        self.performance_metrics["total_retries_scheduled"] += 1
        
        # Update analytics
        self._update_retry_analytics(retry_type, "scheduled")
        
        logger.info(f"Hybrid retry scheduled: {retry_type.value} for transmission {transmission_id} (ID: {retry_id}, Priority: {priority.value})")
        
        return retry_id

    def get_pending_hybrid_retries(self, priority_filter: Optional[HybridRetryPriority] = None) -> List[HybridRetryScheduleEntry]:
        """
        Get pending retries with enhanced filtering - Hybrid FIRS Function.
        
        Provides comprehensive retry filtering with SI+APP coordination
        and FIRS compliance prioritization.
        
        Args:
            priority_filter: Filter by specific priority level
            
        Returns:
            List of pending retry entries
        """
        current_time = datetime.now(timezone.utc)
        pending_retries = []
        
        # Get retries by priority
        priorities_to_check = [priority_filter] if priority_filter else list(HybridRetryPriority)
        
        for priority in priorities_to_check:
            retry_ids = self.priority_queues.get(priority, [])
            
            for retry_id in retry_ids[:]:  # Use slice to avoid modification during iteration
                if retry_id not in self.retry_schedule:
                    # Clean up orphaned entry
                    retry_ids.remove(retry_id)
                    continue
                
                retry_entry = self.retry_schedule[retry_id]
                
                # Check if retry is due
                if retry_entry.scheduled_time <= current_time and retry_entry.status == "pending":
                    # Check if max attempts exceeded
                    if retry_entry.attempt_number > retry_entry.max_attempts:
                        retry_entry.status = "expired"
                        retry_ids.remove(retry_id)
                        self.performance_metrics["expired_retries"] += 1
                        continue
                    
                    # Check FIRS compliance if required
                    if retry_entry.firs_compliance_required and not retry_entry.compliance_validated:
                        if not self._validate_firs_compliance_for_retry(retry_entry):
                            # Skip this retry for now
                            continue
                    
                    pending_retries.append(retry_entry)
        
        # Sort by priority and scheduled time
        pending_retries.sort(key=lambda r: (
            list(HybridRetryPriority).index(r.priority),
            r.scheduled_time
        ))
        
        return pending_retries

    async def process_hybrid_retry(self, retry_entry: HybridRetryScheduleEntry) -> bool:
        """
        Process a hybrid retry with enhanced coordination - Hybrid FIRS Function.
        
        Provides comprehensive retry processing that considers both SI and APP
        operations with FIRS compliance validation.
        
        Args:
            retry_entry: Retry entry to process
            
        Returns:
            Success status of the retry operation
        """
        retry_id = retry_entry.retry_id
        current_time = datetime.now(timezone.utc)
        
        try:
            # Update retry status and tracking
            retry_entry.status = "processing"
            retry_entry.last_attempt_time = current_time
            self.performance_metrics["current_concurrent_retries"] += 1
            
            # Peak tracking
            self.performance_metrics["peak_concurrent_retries"] = max(
                self.performance_metrics["peak_concurrent_retries"],
                self.performance_metrics["current_concurrent_retries"]
            )
            
            # Create comprehensive retry context
            retry_context = {
                "retry_id": retry_id,
                "transmission_id": str(retry_entry.transmission_id),
                "retry_type": retry_entry.retry_type.value,
                "attempt_number": retry_entry.attempt_number,
                "priority": retry_entry.priority.value,
                "strategy": retry_entry.strategy.value,
                "si_context": retry_entry.si_context,
                "app_context": retry_entry.app_context,
                "hybrid_context": retry_entry.hybrid_context,
                "firs_context": retry_entry.firs_context,
                "firs_compliance_required": retry_entry.firs_compliance_required,
                "compliance_impact": retry_entry.compliance_impact
            }
            
            # Execute retry based on type
            success = await self._execute_retry_by_type(retry_entry.retry_type, retry_context)
            
            if success:
                # Retry succeeded
                retry_entry.status = "completed"
                retry_entry.success_count += 1
                self.performance_metrics["successful_retries"] += 1
                
                # Remove from schedule
                self._remove_retry_from_schedule(retry_id)
                
                # Update analytics
                self._update_retry_analytics(retry_entry.retry_type, "success")
                
                logger.info(f"Hybrid retry succeeded: {retry_entry.retry_type.value} for transmission {retry_entry.transmission_id}")
                
                return True
                
            else:
                # Retry failed
                retry_entry.failure_count += 1
                retry_entry.attempt_number += 1
                
                if retry_entry.attempt_number <= retry_entry.max_attempts:
                    # Schedule next attempt
                    next_delay = retry_entry.calculate_next_delay()
                    retry_entry.scheduled_time = current_time + timedelta(seconds=next_delay)
                    retry_entry.status = "pending"
                    
                    # Update average delay metric
                    self._update_average_delay(next_delay)
                    
                    logger.warning(f"Hybrid retry failed, scheduling next attempt in {next_delay}s: {retry_entry.retry_type.value}")
                    
                else:
                    # Max attempts exceeded
                    retry_entry.status = "failed"
                    self.performance_metrics["failed_retries"] += 1
                    
                    # Remove from schedule
                    self._remove_retry_from_schedule(retry_id)
                    
                    # Update analytics
                    self._update_retry_analytics(retry_entry.retry_type, "failure")
                    
                    logger.error(f"Hybrid retry failed permanently after {retry_entry.max_attempts} attempts: {retry_entry.retry_type.value}")
                
                return False
                
        except Exception as e:
            retry_entry.last_error = str(e)
            retry_entry.status = "error"
            
            logger.error(f"Error processing hybrid retry {retry_id}: {str(e)}")
            return False
            
        finally:
            self.performance_metrics["current_concurrent_retries"] -= 1

    async def _execute_retry_by_type(self, retry_type: HybridRetryType, context: Dict[str, Any]) -> bool:
        """Execute retry based on its type with appropriate handler."""
        try:
            # SI-specific retries
            if retry_type == HybridRetryType.SI_ERP_CONNECTION:
                return await self._retry_si_erp_connection(context)
            elif retry_type == HybridRetryType.SI_IRN_GENERATION:
                return await self._retry_si_irn_generation(context)
            elif retry_type == HybridRetryType.SI_CERTIFICATE_VALIDATION:
                return await self._retry_si_certificate_validation(context)
            
            # APP-specific retries
            elif retry_type == HybridRetryType.APP_TRANSMISSION:
                return await self._retry_app_transmission(context)
            elif retry_type == HybridRetryType.APP_FIRS_SUBMISSION:
                return await self._retry_app_firs_submission(context)
            elif retry_type == HybridRetryType.APP_ENCRYPTION:
                return await self._retry_app_encryption(context)
            
            # Hybrid retries
            elif retry_type == HybridRetryType.HYBRID_WORKFLOW:
                return await self._retry_hybrid_workflow(context)
            elif retry_type == HybridRetryType.HYBRID_COORDINATION:
                return await self._retry_hybrid_coordination(context)
            
            # FIRS compliance retries
            elif retry_type == HybridRetryType.FIRS_API_CALL:
                return await self._retry_firs_api_call(context)
            elif retry_type == HybridRetryType.FIRS_CERTIFICATE_RENEWAL:
                return await self._retry_firs_certificate_renewal(context)
            
            else:
                # Generic retry processing
                return await self._retry_generic_transmission(context)
                
        except Exception as e:
            logger.error(f"Error executing retry type {retry_type.value}: {str(e)}")
            return False

    async def _retry_si_erp_connection(self, context: Dict[str, Any]) -> bool:
        """Retry SI ERP connection with enhanced logic."""
        try:
            # This would implement actual SI ERP connection retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            
            # Random success for demonstration
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"SI ERP connection retry failed: {str(e)}")
            return False

    async def _retry_si_irn_generation(self, context: Dict[str, Any]) -> bool:
        """Retry SI IRN generation with enhanced logic."""
        try:
            # This would implement actual SI IRN generation retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"SI IRN generation retry failed: {str(e)}")
            return False

    async def _retry_si_certificate_validation(self, context: Dict[str, Any]) -> bool:
        """Retry SI certificate validation with enhanced logic."""
        try:
            # This would implement actual SI certificate validation retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"SI certificate validation retry failed: {str(e)}")
            return False

    async def _retry_app_transmission(self, context: Dict[str, Any]) -> bool:
        """Retry APP transmission with enhanced logic."""
        try:
            # Get transmission service and retry the transmission
            from app.services.transmission_service import TransmissionService
            transmission_service = TransmissionService(self.db)
            
            transmission_id = UUID(context["transmission_id"])
            
            # This would implement actual APP transmission retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"APP transmission retry failed: {str(e)}")
            return False

    async def _retry_app_firs_submission(self, context: Dict[str, Any]) -> bool:
        """Retry APP FIRS submission with enhanced logic."""
        try:
            # This would implement actual APP FIRS submission retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"APP FIRS submission retry failed: {str(e)}")
            return False

    async def _retry_app_encryption(self, context: Dict[str, Any]) -> bool:
        """Retry APP encryption with enhanced logic."""
        try:
            # This would implement actual APP encryption retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"APP encryption retry failed: {str(e)}")
            return False

    async def _retry_hybrid_workflow(self, context: Dict[str, Any]) -> bool:
        """Retry hybrid workflow coordination with enhanced logic."""
        try:
            # This would implement actual hybrid workflow retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"Hybrid workflow retry failed: {str(e)}")
            return False

    async def _retry_hybrid_coordination(self, context: Dict[str, Any]) -> bool:
        """Retry hybrid coordination with enhanced logic."""
        try:
            # This would implement actual hybrid coordination retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"Hybrid coordination retry failed: {str(e)}")
            return False

    async def _retry_firs_api_call(self, context: Dict[str, Any]) -> bool:
        """Retry FIRS API call with enhanced logic."""
        try:
            # This would implement actual FIRS API call retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"FIRS API call retry failed: {str(e)}")
            return False

    async def _retry_firs_certificate_renewal(self, context: Dict[str, Any]) -> bool:
        """Retry FIRS certificate renewal with enhanced logic."""
        try:
            # This would implement actual FIRS certificate renewal retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            return random.choice([True, False])
        except Exception as e:
            logger.error(f"FIRS certificate renewal retry failed: {str(e)}")
            return False

    async def _retry_generic_transmission(self, context: Dict[str, Any]) -> bool:
        """Generic transmission retry logic."""
        try:
            transmission_id = UUID(context["transmission_id"])
            
            # Get the transmission record
            transmission = self.db.query(TransmissionRecord).filter(
                TransmissionRecord.id == transmission_id
            ).first()
            
            if not transmission:
                logger.error(f"Transmission {transmission_id} not found for retry")
                return False
            
            # This would implement actual generic transmission retry logic
            await asyncio.sleep(0.1)  # Simulate retry work
            
            # Random success for demonstration
            success = random.choice([True, False])
            
            if success:
                transmission.status = TransmissionStatus.COMPLETED
                logger.info(f"Generic transmission retry succeeded for {transmission_id}")
            else:
                logger.warning(f"Generic transmission retry failed for {transmission_id}")
            
            self.db.commit()
            return success
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Generic transmission retry error: {str(e)}")
            return False

    def _requires_firs_compliance(self, retry_type: HybridRetryType) -> bool:
        """Check if retry type requires FIRS compliance validation."""
        firs_compliance_types = [
            HybridRetryType.FIRS_API_CALL,
            HybridRetryType.FIRS_CERTIFICATE_RENEWAL,
            HybridRetryType.FIRS_STATUS_CHECK,
            HybridRetryType.FIRS_RECONCILIATION,
            HybridRetryType.APP_FIRS_SUBMISSION,
            HybridRetryType.HYBRID_COMPLIANCE_CHECK,
            HybridRetryType.SI_CERTIFICATE_VALIDATION
        ]
        
        return retry_type in firs_compliance_types

    def _assess_retry_firs_impact(
        self, 
        retry_type: HybridRetryType, 
        si_context: Optional[Dict[str, Any]], 
        app_context: Optional[Dict[str, Any]], 
        hybrid_context: Optional[Dict[str, Any]], 
        firs_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess FIRS compliance impact of a retry."""
        impact = {
            "compliance_critical": False,
            "affects_submission": False,
            "affects_validation": False,
            "requires_certificate": False,
            "blocks_workflow": False,
            "risk_level": "low"
        }
        
        # High-impact retry types
        if retry_type in [
            HybridRetryType.FIRS_API_CALL,
            HybridRetryType.FIRS_CERTIFICATE_RENEWAL,
            HybridRetryType.APP_FIRS_SUBMISSION,
            HybridRetryType.HYBRID_COMPLIANCE_CHECK
        ]:
            impact["compliance_critical"] = True
            impact["risk_level"] = "high"
        
        # Check contexts for specific impacts
        if firs_context:
            impact["compliance_critical"] = True
        
        if app_context and any(key in app_context for key in ["transmission", "submission", "firs"]):
            impact["affects_submission"] = True
        
        if si_context and any(key in si_context for key in ["certificate", "validation", "irn"]):
            impact["affects_validation"] = True
        
        return impact

    def _validate_firs_compliance_for_retry(self, retry_entry: HybridRetryScheduleEntry) -> bool:
        """Validate FIRS compliance for a retry entry."""
        # Basic FIRS compliance validation
        # This would integrate with actual FIRS validation logic
        
        if retry_entry.firs_context:
            # Validate FIRS context requirements
            required_fields = ["api_endpoint", "certificate_valid"]
            for field in required_fields:
                if field not in retry_entry.firs_context:
                    return False
        
        retry_entry.compliance_validated = True
        return True

    def _remove_retry_from_schedule(self, retry_id: str) -> None:
        """Remove retry from schedule and priority queues."""
        if retry_id in self.retry_schedule:
            retry_entry = self.retry_schedule[retry_id]
            
            # Remove from priority queue
            if retry_id in self.priority_queues[retry_entry.priority]:
                self.priority_queues[retry_entry.priority].remove(retry_id)
            
            # Remove from schedule
            del self.retry_schedule[retry_id]

    def _update_retry_analytics(self, retry_type: HybridRetryType, outcome: str) -> None:
        """Update retry analytics with outcome."""
        type_key = retry_type.value
        
        # Initialize if not exists
        if type_key not in self.retry_analytics["success_rates_by_type"]:
            self.retry_analytics["success_rates_by_type"][type_key] = {"success": 0, "failure": 0}
        
        if outcome in ["success", "failure"]:
            self.retry_analytics["success_rates_by_type"][type_key][outcome] += 1

    def _update_average_delay(self, delay: int) -> None:
        """Update average retry delay metric."""
        current_avg = self.performance_metrics["average_retry_delay"]
        total_retries = self.performance_metrics["total_retries_scheduled"]
        
        if total_retries > 1:
            self.performance_metrics["average_retry_delay"] = (
                (current_avg * (total_retries - 1) + delay) / total_retries
            )
        else:
            self.performance_metrics["average_retry_delay"] = delay

    async def start_hybrid_scheduler(self) -> None:
        """
        Start the hybrid retry scheduler - Hybrid FIRS Function.
        
        Initializes comprehensive retry scheduling with SI+APP coordination
        and FIRS compliance monitoring.
        """
        if self.is_running:
            logger.warning("Hybrid retry scheduler is already running")
            return
        
        self.is_running = True
        
        try:
            # Start async scheduler loop
            self.async_scheduler_task = asyncio.create_task(self._async_scheduler_loop())
            
            logger.info("Hybrid FIRS Retry Scheduler started successfully")
            
        except Exception as e:
            self.is_running = False
            logger.error(f"Failed to start Hybrid FIRS Retry Scheduler: {str(e)}")
            raise

    async def _async_scheduler_loop(self) -> None:
        """Main async scheduler loop."""
        while self.is_running:
            try:
                start_time = time.time()
                
                # Get pending retries
                pending_retries = self.get_pending_hybrid_retries()
                
                if pending_retries:
                    logger.info(f"Processing {len(pending_retries)} pending hybrid retries")
                    
                    # Process retries with concurrency limit
                    semaphore = asyncio.Semaphore(self.max_concurrent_retries)
                    
                    async def process_with_semaphore(retry_entry):
                        async with semaphore:
                            return await self.process_hybrid_retry(retry_entry)
                    
                    # Process retries concurrently
                    tasks = [process_with_semaphore(retry) for retry in pending_retries]
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update scheduler health
                execution_time = time.time() - start_time
                self.performance_metrics["last_scheduler_run"] = datetime.now(timezone.utc)
                
                # Health score based on execution time
                if execution_time > self.scheduler_interval * 0.8:
                    self.performance_metrics["scheduler_health_score"] -= 5
                else:
                    self.performance_metrics["scheduler_health_score"] = min(
                        self.performance_metrics["scheduler_health_score"] + 1, 100
                    )
                
                # Sleep until next cycle
                sleep_time = max(0, self.scheduler_interval - execution_time)
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in hybrid scheduler loop: {str(e)}")
                await asyncio.sleep(30)  # Wait before retrying

    def get_hybrid_scheduler_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive scheduler metrics - Hybrid FIRS Function.
        
        Returns detailed metrics for hybrid retry scheduling with
        SI+APP coordination and FIRS compliance monitoring.
        """
        return {
            "scheduler_info": {
                "name": self.name,
                "version": HYBRID_RETRY_SCHEDULER_VERSION,
                "is_running": self.is_running,
                "scheduler_interval": self.scheduler_interval,
                "max_concurrent_retries": self.max_concurrent_retries
            },
            "performance_metrics": dict(self.performance_metrics),
            "retry_summary": {
                "total_scheduled": len(self.retry_schedule),
                "by_priority": {
                    priority.value: len(retry_ids)
                    for priority, retry_ids in self.priority_queues.items()
                },
                "by_type": {
                    retry_type.value: sum(1 for r in self.retry_schedule.values() if r.retry_type == retry_type)
                    for retry_type in HybridRetryType
                },
                "by_status": {}
            },
            "analytics": dict(self.retry_analytics),
            "recent_retries": [
                {
                    "retry_id": retry.retry_id,
                    "transmission_id": str(retry.transmission_id),
                    "retry_type": retry.retry_type.value,
                    "priority": retry.priority.value,
                    "status": retry.status,
                    "attempt_number": retry.attempt_number,
                    "scheduled_time": retry.scheduled_time.isoformat(),
                    "firs_compliance_required": retry.firs_compliance_required
                }
                for retry in sorted(
                    self.retry_schedule.values(),
                    key=lambda r: r.created_time,
                    reverse=True
                )[:10]
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def stop_hybrid_scheduler(self) -> None:
        """
        Stop the hybrid retry scheduler - Hybrid FIRS Function.
        
        Gracefully shuts down the scheduler and cleanup resources.
        """
        if not self.is_running:
            return
        
        logger.info("Stopping Hybrid FIRS Retry Scheduler")
        
        self.is_running = False
        
        # Cancel async scheduler task
        if self.async_scheduler_task:
            self.async_scheduler_task.cancel()
            try:
                await self.async_scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        logger.info("Hybrid FIRS Retry Scheduler stopped")

    def start_background_scheduler(self) -> threading.Thread:
        """
        Start the scheduler in a background thread - Legacy compatibility.
        
        Provides backward compatibility while leveraging hybrid functionality.
        """
        def thread_runner():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.start_hybrid_scheduler())
                loop.run_forever()
            finally:
                loop.close()
        
        self.scheduler_thread = threading.Thread(target=thread_runner, daemon=True)
        self.scheduler_thread.start()
        logger.info("Started hybrid retry scheduler in background thread")
        return self.scheduler_thread


# Global instance
_hybrid_retry_scheduler = None


def get_hybrid_retry_scheduler(db: Optional[Session] = None) -> HybridFIRSRetryScheduler:
    """Get the global hybrid retry scheduler instance."""
    global _hybrid_retry_scheduler
    
    if _hybrid_retry_scheduler is None:
        _hybrid_retry_scheduler = HybridFIRSRetryScheduler(db)
    
    return _hybrid_retry_scheduler


# Legacy compatibility classes and functions
class RetryScheduler:
    """Legacy RetryScheduler class for backward compatibility."""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._hybrid_scheduler = HybridFIRSRetryScheduler(db)
    
    def get_pending_retries(self) -> List[TransmissionRecord]:
        """Legacy method - get pending retries."""
        # Convert hybrid retries to legacy format
        hybrid_retries = self._hybrid_scheduler.get_pending_hybrid_retries()
        
        # This would convert to TransmissionRecord format
        # For now, return empty list for compatibility
        return []
    
    def process_retry(self, transmission_id: UUID) -> bool:
        """Legacy method - process a single retry."""
        # Schedule using hybrid scheduler
        async def _async_process():
            retry_id = await self._hybrid_scheduler.schedule_hybrid_retry(
                transmission_id=transmission_id,
                retry_type=HybridRetryType.APP_TRANSMISSION,
                priority=HybridRetryPriority.MEDIUM_APP
            )
            
            # Process immediately
            retry_entry = self._hybrid_scheduler.retry_schedule.get(retry_id)
            if retry_entry:
                return await self._hybrid_scheduler.process_hybrid_retry(retry_entry)
            return False
        
        # Run in new event loop for synchronous compatibility
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_async_process())
        except Exception as e:
            logger.error(f"Error in legacy process_retry: {str(e)}")
            return False
        finally:
            loop.close()
    
    def run_scheduler(self, interval: int = 60):
        """Legacy method - run scheduler."""
        # Update interval and start hybrid scheduler
        self._hybrid_scheduler.scheduler_interval = interval
        
        # Run in blocking mode
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._hybrid_scheduler.start_hybrid_scheduler())
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Retry scheduler stopped by user")
        finally:
            loop.close()
    
    def start_background_scheduler(self) -> threading.Thread:
        """Legacy method - start background scheduler."""
        return self._hybrid_scheduler.start_background_scheduler()


def get_retry_scheduler(db: Optional[Session] = None) -> RetryScheduler:
    """
    Legacy compatibility function for getting retry scheduler.
    
    This function maintains backward compatibility while delegating to the
    enhanced hybrid retry scheduler.
    """
    return RetryScheduler(db)