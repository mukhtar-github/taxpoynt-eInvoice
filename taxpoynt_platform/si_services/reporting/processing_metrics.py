"""
Processing Metrics Service

This module tracks and reports processing performance statistics for SI services,
including throughput, latency, error rates, resource utilization, and operational efficiency.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics
from pathlib import Path
from collections import defaultdict, deque
import psutil
import threading

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of processing metrics"""
    THROUGHPUT = "throughput"
    LATENCY = "latency" 
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    QUEUE_DEPTH = "queue_depth"
    SUCCESS_RATE = "success_rate"
    PROCESSING_TIME = "processing_time"
    BATCH_EFFICIENCY = "batch_efficiency"


class MetricUnit(Enum):
    """Units for metrics"""
    RECORDS_PER_SECOND = "records/sec"
    RECORDS_PER_MINUTE = "records/min"
    MILLISECONDS = "ms"
    SECONDS = "sec"
    PERCENTAGE = "%"
    COUNT = "count"
    BYTES = "bytes"
    MEGABYTES = "MB"
    GIGABYTES = "GB"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    metric_type: MetricType
    unit: MetricUnit
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series of metric points"""
    metric_name: str
    metric_type: MetricType
    unit: MetricUnit
    points: List[MetricPoint] = field(default_factory=list)
    retention_period: timedelta = field(default_factory=lambda: timedelta(days=7))


@dataclass
class PerformanceAlert:
    """Performance-related alert"""
    alert_id: str
    severity: AlertSeverity
    metric_type: MetricType
    threshold_violated: str
    current_value: float
    threshold_value: float
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False


@dataclass
class ProcessingJob:
    """Information about a processing job for metrics tracking"""
    job_id: str
    job_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    records_processed: int = 0
    records_failed: int = 0
    status: str = "running"
    processing_node: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemResourceMetrics:
    """System resource utilization metrics"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_recv_mb: float
    network_io_sent_mb: float
    active_connections: int
    load_average: Tuple[float, float, float]


@dataclass
class ThroughputMetrics:
    """Throughput performance metrics"""
    period_start: datetime
    period_end: datetime
    total_records_processed: int
    successful_records: int
    failed_records: int
    average_throughput: float
    peak_throughput: float
    throughput_unit: MetricUnit
    by_job_type: Dict[str, int] = field(default_factory=dict)
    by_source_system: Dict[str, int] = field(default_factory=dict)


@dataclass
class LatencyMetrics:
    """Latency performance metrics"""
    period_start: datetime
    period_end: datetime
    average_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    by_operation: Dict[str, float] = field(default_factory=dict)


@dataclass
class ErrorMetrics:
    """Error rate and failure metrics"""
    period_start: datetime
    period_end: datetime
    total_operations: int
    failed_operations: int
    error_rate_percent: float
    error_by_type: Dict[str, int] = field(default_factory=dict)
    error_by_system: Dict[str, int] = field(default_factory=dict)
    most_common_errors: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class PerformanceReport:
    """Comprehensive performance metrics report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    throughput_metrics: ThroughputMetrics
    latency_metrics: LatencyMetrics
    error_metrics: ErrorMetrics
    resource_metrics: List[SystemResourceMetrics] = field(default_factory=list)
    active_alerts: List[PerformanceAlert] = field(default_factory=list)
    performance_score: float = 0.0
    trends: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricsConfig:
    """Configuration for metrics collection"""
    collection_interval_seconds: int = 30
    retention_days: int = 7
    enable_system_metrics: bool = True
    enable_application_metrics: bool = True
    enable_real_time_alerts: bool = True
    throughput_alert_threshold: float = 100.0  # records/sec
    latency_alert_threshold_ms: float = 5000.0
    error_rate_alert_threshold: float = 5.0  # percent
    cpu_alert_threshold: float = 80.0  # percent
    memory_alert_threshold: float = 85.0  # percent
    storage_path: Optional[str] = None
    export_format: str = "json"


class ProcessingMetricsService:
    """
    Service for collecting, analyzing, and reporting processing performance metrics
    """
    
    def __init__(self, config: MetricsConfig):
        self.config = config
        self.metric_series: Dict[str, MetricSeries] = {}
        self.active_jobs: Dict[str, ProcessingJob] = {}
        self.completed_jobs: deque = deque(maxlen=10000)
        self.alerts: Dict[str, PerformanceAlert] = {}
        self.resource_metrics: deque = deque(maxlen=10000)
        
        # Metric collection state
        self.is_collecting = False
        self.collection_task: Optional[asyncio.Task] = None
        self.system_monitor_task: Optional[asyncio.Task] = None
        
        # Thread-safe metric buffers
        self._metric_buffer = deque(maxlen=10000)
        self._buffer_lock = threading.Lock()
        
        # Setup storage
        if config.storage_path:
            self.storage_path = Path(config.storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = None
        
        # Initialize metric series
        self._initialize_metric_series()
    
    def _initialize_metric_series(self) -> None:
        """Initialize metric series for different metric types"""
        for metric_type in MetricType:
            series_name = f"system_{metric_type.value}"
            self.metric_series[series_name] = MetricSeries(
                metric_name=series_name,
                metric_type=metric_type,
                unit=self._get_default_unit(metric_type)
            )
    
    def _get_default_unit(self, metric_type: MetricType) -> MetricUnit:
        """Get default unit for metric type"""
        unit_mapping = {
            MetricType.THROUGHPUT: MetricUnit.RECORDS_PER_SECOND,
            MetricType.LATENCY: MetricUnit.MILLISECONDS,
            MetricType.ERROR_RATE: MetricUnit.PERCENTAGE,
            MetricType.RESOURCE_USAGE: MetricUnit.PERCENTAGE,
            MetricType.QUEUE_DEPTH: MetricUnit.COUNT,
            MetricType.SUCCESS_RATE: MetricUnit.PERCENTAGE,
            MetricType.PROCESSING_TIME: MetricUnit.SECONDS,
            MetricType.BATCH_EFFICIENCY: MetricUnit.PERCENTAGE
        }
        return unit_mapping.get(metric_type, MetricUnit.COUNT)
    
    async def start_collection(self) -> None:
        """Start metrics collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        logger.info("Starting metrics collection")
        
        # Start metric collection task
        self.collection_task = asyncio.create_task(self._metric_collection_loop())
        
        # Start system monitoring if enabled
        if self.config.enable_system_metrics:
            self.system_monitor_task = asyncio.create_task(self._system_monitoring_loop())
    
    async def stop_collection(self) -> None:
        """Stop metrics collection"""
        if not self.is_collecting:
            return
        
        self.is_collecting = False
        logger.info("Stopping metrics collection")
        
        # Cancel tasks
        if self.collection_task:
            self.collection_task.cancel()
        
        if self.system_monitor_task:
            self.system_monitor_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(
            *[t for t in [self.collection_task, self.system_monitor_task] if t],
            return_exceptions=True
        )
        
        # Flush remaining metrics
        await self._flush_metric_buffer()
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: MetricType,
        unit: MetricUnit = None,
        tags: Dict[str, str] = None,
        timestamp: datetime = None
    ) -> None:
        """Record a metric data point"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            if unit is None:
                unit = self._get_default_unit(metric_type)
            
            metric_point = MetricPoint(
                timestamp=timestamp,
                value=value,
                metric_type=metric_type,
                unit=unit,
                tags=tags or {},
                metadata={}
            )
            
            # Add to thread-safe buffer
            with self._buffer_lock:
                self._metric_buffer.append((metric_name, metric_point))
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {e}")
    
    def start_job_tracking(self, job_id: str, job_type: str, **metadata) -> None:
        """Start tracking a processing job"""
        try:
            job = ProcessingJob(
                job_id=job_id,
                job_type=job_type,
                start_time=datetime.now(),
                processing_node=self._get_node_id(),
                metadata=metadata
            )
            
            self.active_jobs[job_id] = job
            
            # Record job start metric
            self.record_metric(
                f"job_started_{job_type}",
                1.0,
                MetricType.COUNT,
                tags={"job_id": job_id, "job_type": job_type}
            )
            
        except Exception as e:
            logger.error(f"Failed to start job tracking for {job_id}: {e}")
    
    def complete_job_tracking(
        self,
        job_id: str,
        records_processed: int = 0,
        records_failed: int = 0,
        status: str = "completed"
    ) -> None:
        """Complete tracking for a processing job"""
        try:
            job = self.active_jobs.get(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found in active jobs")
                return
            
            # Update job details
            job.end_time = datetime.now()
            job.records_processed = records_processed
            job.records_failed = records_failed
            job.status = status
            
            # Calculate processing metrics
            duration = (job.end_time - job.start_time).total_seconds()
            throughput = records_processed / duration if duration > 0 else 0
            error_rate = (records_failed / records_processed * 100) if records_processed > 0 else 0
            
            # Record completion metrics
            self.record_metric(
                f"job_completed_{job.job_type}",
                1.0,
                MetricType.COUNT,
                tags={"job_id": job_id, "job_type": job.job_type, "status": status}
            )
            
            self.record_metric(
                f"throughput_{job.job_type}",
                throughput,
                MetricType.THROUGHPUT,
                tags={"job_id": job_id, "job_type": job.job_type}
            )
            
            self.record_metric(
                f"processing_time_{job.job_type}",
                duration,
                MetricType.PROCESSING_TIME,
                tags={"job_id": job_id, "job_type": job.job_type}
            )
            
            if records_failed > 0:
                self.record_metric(
                    f"error_rate_{job.job_type}",
                    error_rate,
                    MetricType.ERROR_RATE,
                    tags={"job_id": job_id, "job_type": job.job_type}
                )
            
            # Move to completed jobs
            self.completed_jobs.append(job)
            del self.active_jobs[job_id]
            
        except Exception as e:
            logger.error(f"Failed to complete job tracking for {job_id}: {e}")
    
    def record_operation_latency(
        self,
        operation_name: str,
        latency_ms: float,
        success: bool = True,
        tags: Dict[str, str] = None
    ) -> None:
        """Record latency for an operation"""
        try:
            self.record_metric(
                f"latency_{operation_name}",
                latency_ms,
                MetricType.LATENCY,
                MetricUnit.MILLISECONDS,
                tags=tags
            )
            
            # Record success/failure
            success_value = 1.0 if success else 0.0
            self.record_metric(
                f"success_rate_{operation_name}",
                success_value,
                MetricType.SUCCESS_RATE,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Failed to record operation latency: {e}")
    
    async def generate_performance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PerformanceReport:
        """Generate a comprehensive performance report"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(hours=24)
        if not end_date:
            end_date = datetime.now()
        
        report_id = f"perf_{start_date.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Calculate throughput metrics
            throughput_metrics = await self._calculate_throughput_metrics(start_date, end_date)
            
            # Calculate latency metrics
            latency_metrics = await self._calculate_latency_metrics(start_date, end_date)
            
            # Calculate error metrics
            error_metrics = await self._calculate_error_metrics(start_date, end_date)
            
            # Get resource metrics
            resource_metrics = self._get_resource_metrics(start_date, end_date)
            
            # Get active alerts
            active_alerts = self._get_active_alerts()
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(
                throughput_metrics, latency_metrics, error_metrics
            )
            
            # Generate trends
            trends = await self._calculate_trends()
            
            # Generate recommendations
            recommendations = self._generate_performance_recommendations(
                throughput_metrics, latency_metrics, error_metrics, active_alerts
            )
            
            # Calculate summary stats
            summary_stats = self._calculate_summary_stats(
                throughput_metrics, latency_metrics, error_metrics
            )
            
            report = PerformanceReport(
                report_id=report_id,
                generated_at=datetime.now(),
                period_start=start_date,
                period_end=end_date,
                throughput_metrics=throughput_metrics,
                latency_metrics=latency_metrics,
                error_metrics=error_metrics,
                resource_metrics=resource_metrics,
                active_alerts=active_alerts,
                performance_score=performance_score,
                trends=trends,
                recommendations=recommendations,
                summary_stats=summary_stats
            )
            
            # Export if configured
            if self.storage_path:
                await self._export_performance_report(report)
            
            logger.info(f"Generated performance report {report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            raise
    
    async def _metric_collection_loop(self) -> None:
        """Main metric collection loop"""
        while self.is_collecting:
            try:
                await self._flush_metric_buffer()
                await self._check_alert_conditions()
                await self._cleanup_old_metrics()
                
                await asyncio.sleep(self.config.collection_interval_seconds)
                
            except Exception as e:
                logger.error(f"Metric collection loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _system_monitoring_loop(self) -> None:
        """System resource monitoring loop"""
        while self.is_collecting:
            try:
                resource_metrics = self._collect_system_metrics()
                self.resource_metrics.append(resource_metrics)
                
                # Record system metrics
                self.record_metric(
                    "system_cpu_usage",
                    resource_metrics.cpu_usage_percent,
                    MetricType.RESOURCE_USAGE,
                    MetricUnit.PERCENTAGE
                )
                
                self.record_metric(
                    "system_memory_usage",
                    resource_metrics.memory_usage_percent,
                    MetricType.RESOURCE_USAGE,
                    MetricUnit.PERCENTAGE
                )
                
                self.record_metric(
                    "system_disk_usage",
                    resource_metrics.disk_usage_percent,
                    MetricType.RESOURCE_USAGE,
                    MetricUnit.PERCENTAGE
                )
                
                await asyncio.sleep(self.config.collection_interval_seconds)
                
            except Exception as e:
                logger.error(f"System monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    def _collect_system_metrics(self) -> SystemResourceMetrics:
        """Collect current system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0
            
            # Network I/O
            net_io = psutil.net_io_counters()
            net_recv_mb = net_io.bytes_recv / (1024 * 1024) if net_io else 0
            net_sent_mb = net_io.bytes_sent / (1024 * 1024) if net_io else 0
            
            # Network connections
            connections = len(psutil.net_connections())
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = (0.0, 0.0, 0.0)
            
            return SystemResourceMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_io_recv_mb=net_recv_mb,
                network_io_sent_mb=net_sent_mb,
                active_connections=connections,
                load_average=load_avg
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemResourceMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_io_recv_mb=0.0,
                network_io_sent_mb=0.0,
                active_connections=0,
                load_average=(0.0, 0.0, 0.0)
            )
    
    async def _flush_metric_buffer(self) -> None:
        """Flush metrics from buffer to series"""
        try:
            with self._buffer_lock:
                metrics_to_process = list(self._metric_buffer)
                self._metric_buffer.clear()
            
            for metric_name, metric_point in metrics_to_process:
                # Get or create metric series
                if metric_name not in self.metric_series:
                    self.metric_series[metric_name] = MetricSeries(
                        metric_name=metric_name,
                        metric_type=metric_point.metric_type,
                        unit=metric_point.unit
                    )
                
                # Add point to series
                series = self.metric_series[metric_name]
                series.points.append(metric_point)
                
                # Maintain retention
                cutoff_time = datetime.now() - series.retention_period
                series.points = [p for p in series.points if p.timestamp > cutoff_time]
            
        except Exception as e:
            logger.error(f"Failed to flush metric buffer: {e}")
    
    async def _check_alert_conditions(self) -> None:
        """Check for alert conditions"""
        if not self.config.enable_real_time_alerts:
            return
        
        try:
            current_time = datetime.now()
            
            # Check throughput alerts
            throughput_series = self.metric_series.get("system_throughput")
            if throughput_series and throughput_series.points:
                recent_points = [
                    p for p in throughput_series.points 
                    if (current_time - p.timestamp).total_seconds() < 300  # Last 5 minutes
                ]
                
                if recent_points:
                    avg_throughput = statistics.mean(p.value for p in recent_points)
                    if avg_throughput < self.config.throughput_alert_threshold:
                        await self._create_alert(
                            "low_throughput",
                            AlertSeverity.WARNING,
                            MetricType.THROUGHPUT,
                            f"Low throughput: {avg_throughput:.2f}",
                            avg_throughput,
                            self.config.throughput_alert_threshold
                        )
            
            # Check latency alerts
            latency_series = self.metric_series.get("system_latency")
            if latency_series and latency_series.points:
                recent_points = [
                    p for p in latency_series.points 
                    if (current_time - p.timestamp).total_seconds() < 300
                ]
                
                if recent_points:
                    avg_latency = statistics.mean(p.value for p in recent_points)
                    if avg_latency > self.config.latency_alert_threshold_ms:
                        await self._create_alert(
                            "high_latency",
                            AlertSeverity.WARNING,
                            MetricType.LATENCY,
                            f"High latency: {avg_latency:.2f}ms",
                            avg_latency,
                            self.config.latency_alert_threshold_ms
                        )
            
            # Check resource alerts
            if self.resource_metrics:
                latest_resource = self.resource_metrics[-1]
                
                if latest_resource.cpu_usage_percent > self.config.cpu_alert_threshold:
                    await self._create_alert(
                        "high_cpu_usage",
                        AlertSeverity.CRITICAL,
                        MetricType.RESOURCE_USAGE,
                        f"High CPU usage: {latest_resource.cpu_usage_percent:.1f}%",
                        latest_resource.cpu_usage_percent,
                        self.config.cpu_alert_threshold
                    )
                
                if latest_resource.memory_usage_percent > self.config.memory_alert_threshold:
                    await self._create_alert(
                        "high_memory_usage",
                        AlertSeverity.CRITICAL,
                        MetricType.RESOURCE_USAGE,
                        f"High memory usage: {latest_resource.memory_usage_percent:.1f}%",
                        latest_resource.memory_usage_percent,
                        self.config.memory_alert_threshold
                    )
            
        except Exception as e:
            logger.error(f"Failed to check alert conditions: {e}")
    
    async def _create_alert(
        self,
        alert_type: str,
        severity: AlertSeverity,
        metric_type: MetricType,
        message: str,
        current_value: float,
        threshold_value: float
    ) -> None:
        """Create a performance alert"""
        try:
            alert_id = f"{alert_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Check if similar alert already exists
            existing_alert = None
            for alert in self.alerts.values():
                if (alert.metric_type == metric_type and 
                    alert.threshold_violated == alert_type and
                    not alert.resolved_at):
                    existing_alert = alert
                    break
            
            if existing_alert:
                # Update existing alert
                existing_alert.current_value = current_value
                existing_alert.triggered_at = datetime.now()
            else:
                # Create new alert
                alert = PerformanceAlert(
                    alert_id=alert_id,
                    severity=severity,
                    metric_type=metric_type,
                    threshold_violated=alert_type,
                    current_value=current_value,
                    threshold_value=threshold_value,
                    message=message,
                    triggered_at=datetime.now()
                )
                
                self.alerts[alert_id] = alert
                logger.warning(f"Performance alert created: {message}")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metric data"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)
            
            # Clean up metric series
            for series in self.metric_series.values():
                series.points = [p for p in series.points if p.timestamp > cutoff_time]
            
            # Clean up resource metrics
            while (self.resource_metrics and 
                   self.resource_metrics[0].timestamp < cutoff_time):
                self.resource_metrics.popleft()
            
            # Clean up completed jobs
            while (self.completed_jobs and 
                   self.completed_jobs[0].end_time and
                   self.completed_jobs[0].end_time < cutoff_time):
                self.completed_jobs.popleft()
            
            # Clean up resolved alerts
            alerts_to_remove = []
            for alert_id, alert in self.alerts.items():
                if (alert.resolved_at and 
                    alert.resolved_at < cutoff_time):
                    alerts_to_remove.append(alert_id)
            
            for alert_id in alerts_to_remove:
                del self.alerts[alert_id]
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
    
    async def _calculate_throughput_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ThroughputMetrics:
        """Calculate throughput metrics for the period"""
        
        # Filter completed jobs for the period
        period_jobs = [
            job for job in self.completed_jobs
            if (job.end_time and 
                start_date <= job.end_time <= end_date)
        ]
        
        total_records = sum(job.records_processed for job in period_jobs)
        successful_records = sum(
            job.records_processed - job.records_failed 
            for job in period_jobs
        )
        failed_records = sum(job.records_failed for job in period_jobs)
        
        # Calculate average throughput
        period_duration_hours = (end_date - start_date).total_seconds() / 3600
        average_throughput = total_records / period_duration_hours if period_duration_hours > 0 else 0
        
        # Calculate peak throughput (highest throughput in any hour)
        peak_throughput = 0.0
        current_hour = start_date.replace(minute=0, second=0, microsecond=0)
        
        while current_hour < end_date:
            hour_end = current_hour + timedelta(hours=1)
            hour_jobs = [
                job for job in period_jobs
                if current_hour <= job.end_time < hour_end
            ]
            
            hour_records = sum(job.records_processed for job in hour_jobs)
            peak_throughput = max(peak_throughput, hour_records)
            
            current_hour = hour_end
        
        # Group by job type
        by_job_type = defaultdict(int)
        for job in period_jobs:
            by_job_type[job.job_type] += job.records_processed
        
        # Group by source system (from metadata)
        by_source_system = defaultdict(int)
        for job in period_jobs:
            source = job.metadata.get("source_system", "unknown")
            by_source_system[source] += job.records_processed
        
        return ThroughputMetrics(
            period_start=start_date,
            period_end=end_date,
            total_records_processed=total_records,
            successful_records=successful_records,
            failed_records=failed_records,
            average_throughput=average_throughput,
            peak_throughput=peak_throughput,
            throughput_unit=MetricUnit.RECORDS_PER_MINUTE,
            by_job_type=dict(by_job_type),
            by_source_system=dict(by_source_system)
        )
    
    async def _calculate_latency_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> LatencyMetrics:
        """Calculate latency metrics for the period"""
        
        # Get latency measurements from metric series
        latency_values = []
        by_operation = defaultdict(list)
        
        for series_name, series in self.metric_series.items():
            if series.metric_type == MetricType.LATENCY:
                period_points = [
                    p for p in series.points
                    if start_date <= p.timestamp <= end_date
                ]
                
                values = [p.value for p in period_points]
                latency_values.extend(values)
                
                # Group by operation (from series name)
                operation = series_name.replace("latency_", "")
                by_operation[operation].extend(values)
        
        if not latency_values:
            return LatencyMetrics(
                period_start=start_date,
                period_end=end_date,
                average_latency_ms=0.0,
                median_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                min_latency_ms=0.0,
                max_latency_ms=0.0
            )
        
        # Calculate percentiles
        sorted_latencies = sorted(latency_values)
        
        def percentile(data, p):
            k = (len(data) - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return data[f]
            return data[f] * (c - k) + data[c] * (k - f)
        
        import math
        
        average_latency = statistics.mean(latency_values)
        median_latency = statistics.median(latency_values)
        p95_latency = percentile(sorted_latencies, 0.95)
        p99_latency = percentile(sorted_latencies, 0.99)
        min_latency = min(latency_values)
        max_latency = max(latency_values)
        
        # Calculate by operation
        operation_averages = {}
        for operation, values in by_operation.items():
            if values:
                operation_averages[operation] = statistics.mean(values)
        
        return LatencyMetrics(
            period_start=start_date,
            period_end=end_date,
            average_latency_ms=average_latency,
            median_latency_ms=median_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            by_operation=operation_averages
        )
    
    async def _calculate_error_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ErrorMetrics:
        """Calculate error metrics for the period"""
        
        # Filter completed jobs for the period
        period_jobs = [
            job for job in self.completed_jobs
            if (job.end_time and 
                start_date <= job.end_time <= end_date)
        ]
        
        total_operations = len(period_jobs)
        failed_operations = sum(1 for job in period_jobs if job.status == "failed")
        error_rate = (failed_operations / total_operations * 100) if total_operations > 0 else 0
        
        # Group errors by type (from job status/metadata)
        error_by_type = defaultdict(int)
        error_by_system = defaultdict(int)
        
        for job in period_jobs:
            if job.status == "failed":
                error_type = job.metadata.get("error_type", "unknown")
                error_by_type[error_type] += 1
                
                source_system = job.metadata.get("source_system", "unknown")
                error_by_system[source_system] += 1
        
        # Most common errors
        most_common_errors = sorted(
            error_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return ErrorMetrics(
            period_start=start_date,
            period_end=end_date,
            total_operations=total_operations,
            failed_operations=failed_operations,
            error_rate_percent=error_rate,
            error_by_type=dict(error_by_type),
            error_by_system=dict(error_by_system),
            most_common_errors=most_common_errors
        )
    
    def _get_resource_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[SystemResourceMetrics]:
        """Get resource metrics for the period"""
        return [
            metric for metric in self.resource_metrics
            if start_date <= metric.timestamp <= end_date
        ]
    
    def _get_active_alerts(self) -> List[PerformanceAlert]:
        """Get currently active alerts"""
        return [
            alert for alert in self.alerts.values()
            if not alert.resolved_at
        ]
    
    def _calculate_performance_score(
        self,
        throughput_metrics: ThroughputMetrics,
        latency_metrics: LatencyMetrics,
        error_metrics: ErrorMetrics
    ) -> float:
        """Calculate overall performance score (0-100)"""
        try:
            # Throughput score (based on meeting threshold)
            throughput_score = min(100, 
                (throughput_metrics.average_throughput / self.config.throughput_alert_threshold) * 100
            ) if self.config.throughput_alert_threshold > 0 else 100
            
            # Latency score (inverse relationship)
            latency_score = max(0, 100 - 
                (latency_metrics.average_latency_ms / self.config.latency_alert_threshold_ms) * 100
            ) if self.config.latency_alert_threshold_ms > 0 else 100
            
            # Error score (inverse of error rate)
            error_score = max(0, 100 - error_metrics.error_rate_percent * 10)
            
            # Weighted average
            performance_score = (
                throughput_score * 0.4 +
                latency_score * 0.4 +
                error_score * 0.2
            )
            
            return min(100, max(0, performance_score))
            
        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return 0.0
    
    async def _calculate_trends(self) -> Dict[str, str]:
        """Calculate performance trends"""
        trends = {}
        
        try:
            # Calculate trends for key metrics over the last week
            week_ago = datetime.now() - timedelta(days=7)
            
            for metric_name, series in self.metric_series.items():
                if series.metric_type in [MetricType.THROUGHPUT, MetricType.LATENCY, MetricType.ERROR_RATE]:
                    recent_points = [
                        p for p in series.points
                        if p.timestamp > week_ago
                    ]
                    
                    if len(recent_points) >= 2:
                        # Simple linear trend calculation
                        first_half = recent_points[:len(recent_points)//2]
                        second_half = recent_points[len(recent_points)//2:]
                        
                        first_avg = statistics.mean(p.value for p in first_half)
                        second_avg = statistics.mean(p.value for p in second_half)
                        
                        change_percent = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
                        
                        if change_percent > 5:
                            trends[metric_name] = "improving"
                        elif change_percent < -5:
                            trends[metric_name] = "declining"
                        else:
                            trends[metric_name] = "stable"
            
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
        
        return trends
    
    def _generate_performance_recommendations(
        self,
        throughput_metrics: ThroughputMetrics,
        latency_metrics: LatencyMetrics,
        error_metrics: ErrorMetrics,
        active_alerts: List[PerformanceAlert]
    ) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        try:
            # Throughput recommendations
            if throughput_metrics.average_throughput < self.config.throughput_alert_threshold:
                recommendations.append(
                    "Throughput is below threshold. Consider scaling processing resources."
                )
            
            # Latency recommendations
            if latency_metrics.average_latency_ms > self.config.latency_alert_threshold_ms:
                recommendations.append(
                    "High latency detected. Review processing logic and database queries."
                )
            
            if latency_metrics.p99_latency_ms > latency_metrics.average_latency_ms * 3:
                recommendations.append(
                    "High latency variance detected. Investigate outlier operations."
                )
            
            # Error rate recommendations
            if error_metrics.error_rate_percent > self.config.error_rate_alert_threshold:
                recommendations.append(
                    "Error rate is above threshold. Review error handling and data validation."
                )
            
            # Most common errors
            if error_metrics.most_common_errors:
                top_error = error_metrics.most_common_errors[0]
                recommendations.append(
                    f"Most common error: {top_error[0]} ({top_error[1]} occurrences). Prioritize fixing this issue."
                )
            
            # Alert-based recommendations
            critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
            if critical_alerts:
                recommendations.append(
                    f"Critical alerts active: {len(critical_alerts)}. Immediate attention required."
                )
            
            # Resource-based recommendations
            if any(a.metric_type == MetricType.RESOURCE_USAGE for a in active_alerts):
                recommendations.append(
                    "Resource usage alerts detected. Consider scaling infrastructure."
                )
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
        
        return recommendations
    
    def _calculate_summary_stats(
        self,
        throughput_metrics: ThroughputMetrics,
        latency_metrics: LatencyMetrics,
        error_metrics: ErrorMetrics
    ) -> Dict[str, Any]:
        """Calculate summary statistics"""
        try:
            period_hours = (throughput_metrics.period_end - throughput_metrics.period_start).total_seconds() / 3600
            
            return {
                "period_duration_hours": period_hours,
                "total_records_processed": throughput_metrics.total_records_processed,
                "average_throughput_per_hour": throughput_metrics.average_throughput,
                "peak_throughput_per_hour": throughput_metrics.peak_throughput,
                "success_rate_percent": 100 - error_metrics.error_rate_percent,
                "average_latency_seconds": latency_metrics.average_latency_ms / 1000,
                "active_jobs": len(self.active_jobs),
                "completed_jobs": len([j for j in self.completed_jobs if j.status == "completed"]),
                "failed_jobs": len([j for j in self.completed_jobs if j.status == "failed"]),
                "active_alerts": len(self._get_active_alerts()),
                "data_volume_processed_gb": throughput_metrics.total_records_processed * 0.001  # Estimate
            }
        except Exception as e:
            logger.error(f"Failed to calculate summary stats: {e}")
            return {}
    
    def _get_node_id(self) -> str:
        """Get current processing node identifier"""
        import socket
        return socket.gethostname()
    
    async def _export_performance_report(self, report: PerformanceReport) -> None:
        """Export performance report to storage"""
        if not self.storage_path:
            return
        
        try:
            filename = f"{report.report_id}.{self.config.export_format}"
            filepath = self.storage_path / filename
            
            if self.config.export_format == "json":
                report_dict = self._performance_report_to_dict(report)
                with open(filepath, 'w') as f:
                    json.dump(report_dict, f, indent=2, default=str)
            
            logger.info(f"Exported performance report to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export performance report: {e}")
    
    def _performance_report_to_dict(self, report: PerformanceReport) -> Dict[str, Any]:
        """Convert performance report to dictionary"""
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "performance_score": report.performance_score,
            "throughput_metrics": {
                "total_records_processed": report.throughput_metrics.total_records_processed,
                "successful_records": report.throughput_metrics.successful_records,
                "failed_records": report.throughput_metrics.failed_records,
                "average_throughput": report.throughput_metrics.average_throughput,
                "peak_throughput": report.throughput_metrics.peak_throughput,
                "by_job_type": report.throughput_metrics.by_job_type,
                "by_source_system": report.throughput_metrics.by_source_system
            },
            "latency_metrics": {
                "average_latency_ms": report.latency_metrics.average_latency_ms,
                "median_latency_ms": report.latency_metrics.median_latency_ms,
                "p95_latency_ms": report.latency_metrics.p95_latency_ms,
                "p99_latency_ms": report.latency_metrics.p99_latency_ms,
                "by_operation": report.latency_metrics.by_operation
            },
            "error_metrics": {
                "total_operations": report.error_metrics.total_operations,
                "failed_operations": report.error_metrics.failed_operations,
                "error_rate_percent": report.error_metrics.error_rate_percent,
                "error_by_type": report.error_metrics.error_by_type,
                "error_by_system": report.error_metrics.error_by_system,
                "most_common_errors": report.error_metrics.most_common_errors
            },
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "metric_type": alert.metric_type.value,
                    "message": alert.message,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "triggered_at": alert.triggered_at.isoformat()
                }
                for alert in report.active_alerts
            ],
            "trends": report.trends,
            "recommendations": report.recommendations,
            "summary_stats": report.summary_stats
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        try:
            current_time = datetime.now()
            
            # Recent throughput (last 5 minutes)
            recent_jobs = [
                job for job in self.completed_jobs
                if (job.end_time and 
                    (current_time - job.end_time).total_seconds() < 300)
            ]
            
            recent_throughput = sum(job.records_processed for job in recent_jobs) / 5  # per minute
            
            # Active job count
            active_job_count = len(self.active_jobs)
            
            # Latest resource metrics
            latest_resource = self.resource_metrics[-1] if self.resource_metrics else None
            
            # Active alert count
            active_alert_count = len(self._get_active_alerts())
            
            return {
                "timestamp": current_time.isoformat(),
                "active_jobs": active_job_count,
                "recent_throughput": recent_throughput,
                "active_alerts": active_alert_count,
                "cpu_usage_percent": latest_resource.cpu_usage_percent if latest_resource else 0,
                "memory_usage_percent": latest_resource.memory_usage_percent if latest_resource else 0,
                "disk_usage_percent": latest_resource.disk_usage_percent if latest_resource else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return {}
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            alert = self.alerts.get(alert_id)
            if alert:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            alert = self.alerts.get(alert_id)
            if alert:
                alert.resolved_at = datetime.now()
                logger.info(f"Alert {alert_id} resolved")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False


# Factory function for creating processing metrics service
def create_processing_metrics_service(config: Optional[MetricsConfig] = None) -> ProcessingMetricsService:
    """Factory function to create a processing metrics service"""
    if config is None:
        config = MetricsConfig()
    
    return ProcessingMetricsService(config)