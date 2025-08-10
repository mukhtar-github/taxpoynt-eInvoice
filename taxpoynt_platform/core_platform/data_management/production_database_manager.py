"""
Production-Scale Database Management System for TaxPoynt Platform

Builds upon existing architecture patterns while adding enterprise-grade
features for production scalability, security, and compliance.

Transfers and enhances capabilities from backend/app/db/session.py,
backend/app/services/batch_transmission_service.py, and other optimized components.
"""

import asyncio
import logging
import time
import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Union, Callable, Type, TypeVar, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager, contextmanager
from concurrent.futures import ThreadPoolExecutor
import threading
from functools import wraps

# Database imports
from sqlalchemy import create_engine, text, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
from sqlalchemy.engine import Engine
from sqlalchemy.engine.events import event
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

# Monitoring and observability
import psutil
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Import existing optimized components
from .cache_manager import CacheManager, CacheConfig
from .repository_base import BaseRepository
from .backup_orchestrator import BackupOrchestrator
from .migration_engine import MigrationEngine
from .multi_tenant_manager import MultiTenantManager

logger = logging.getLogger(__name__)

# Type definitions
ModelType = TypeVar('ModelType')


class DatabaseHealth(Enum):
    """Database health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


class ConnectionPoolStatus(Enum):
    """Connection pool status."""
    OPTIMAL = "optimal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXHAUSTED = "exhausted"


@dataclass
class DatabaseMetrics:
    """Comprehensive database metrics."""
    # Connection metrics
    active_connections: int = 0
    idle_connections: int = 0
    total_connections: int = 0
    max_connections: int = 0
    connection_wait_time_ms: float = 0.0
    
    # Query performance metrics
    avg_query_time_ms: float = 0.0
    slow_queries_count: int = 0
    failed_queries_count: int = 0
    total_queries_count: int = 0
    
    # Transaction metrics
    active_transactions: int = 0
    committed_transactions: int = 0
    rolled_back_transactions: int = 0
    
    # Resource metrics
    database_size_mb: float = 0.0
    cache_hit_ratio: float = 0.0
    index_usage_ratio: float = 0.0
    
    # Health indicators
    health_status: DatabaseHealth = DatabaseHealth.HEALTHY
    pool_status: ConnectionPoolStatus = ConnectionPoolStatus.OPTIMAL
    last_backup: Optional[datetime] = None
    replication_lag_ms: float = 0.0
    
    # Cost optimization metrics
    storage_cost_estimate: float = 0.0
    compute_cost_estimate: float = 0.0
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DatabaseConfiguration:
    """Production database configuration."""
    # Basic connection settings
    database_url: str
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    
    # Performance settings
    query_timeout: int = 30
    slow_query_threshold_ms: float = 1000.0
    enable_query_logging: bool = True
    enable_performance_insights: bool = True
    
    # Security settings
    ssl_mode: str = "require"
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    ssl_ca_path: Optional[str] = None
    
    # Backup settings
    backup_enabled: bool = True
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    backup_retention_days: int = 30
    point_in_time_recovery: bool = True
    
    # Monitoring settings
    enable_metrics: bool = True
    metrics_collection_interval: int = 60  # seconds
    enable_alerting: bool = True
    
    # Cost optimization
    enable_auto_scaling: bool = False
    enable_data_archiving: bool = True
    archival_threshold_days: int = 365
    
    @classmethod
    def from_environment(cls) -> 'DatabaseConfiguration':
        """Create configuration from environment variables."""
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            query_timeout=int(os.getenv("DB_QUERY_TIMEOUT", "30")),
            slow_query_threshold_ms=float(os.getenv("DB_SLOW_QUERY_THRESHOLD", "1000")),
            ssl_mode=os.getenv("DB_SSL_MODE", "require"),
            ssl_cert_path=os.getenv("DB_SSL_CERT_PATH"),
            ssl_key_path=os.getenv("DB_SSL_KEY_PATH"),
            ssl_ca_path=os.getenv("DB_SSL_CA_PATH"),
            backup_enabled=os.getenv("DB_BACKUP_ENABLED", "true").lower() == "true",
            backup_retention_days=int(os.getenv("DB_BACKUP_RETENTION_DAYS", "30")),
            enable_metrics=os.getenv("DB_ENABLE_METRICS", "true").lower() == "true",
            enable_alerting=os.getenv("DB_ENABLE_ALERTING", "true").lower() == "true"
        )


class CircuitBreaker:
    """
    Enhanced circuit breaker for database operations.
    Transferred from backend/app/services/batch_transmission_service.py and improved.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self._lock = threading.RLock()
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                else:
                    raise Exception("Database circuit breaker is open")
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(f"Database circuit breaker opened after {self.failure_count} failures")


class ProductionDatabaseManager:
    """
    Production-scale database management system.
    
    Transfers and enhances patterns from:
    - backend/app/db/session.py (connection management)
    - backend/app/services/batch_transmission_service.py (circuit breakers)
    - backend/app/cache/irn_cache.py (caching patterns)
    - backend/app/middleware/rate_limit.py (rate limiting)
    
    Adds enterprise features:
    - Comprehensive monitoring and observability
    - Disaster recovery and backup automation
    - Advanced security and compliance
    - Cost optimization and resource management
    - Multi-tenant data isolation
    """
    
    def __init__(
        self,
        config: DatabaseConfiguration,
        cache_manager: Optional[CacheManager] = None,
        backup_orchestrator: Optional[BackupOrchestrator] = None,
        migration_engine: Optional[MigrationEngine] = None,
        tenant_manager: Optional[MultiTenantManager] = None
    ):
        """
        Initialize production database manager.
        
        Args:
            config: Database configuration
            cache_manager: Cache manager instance
            backup_orchestrator: Backup orchestrator instance
            migration_engine: Migration engine instance
            tenant_manager: Multi-tenant manager instance
        """
        self.config = config
        self.cache_manager = cache_manager
        self.backup_orchestrator = backup_orchestrator
        self.migration_engine = migration_engine
        self.tenant_manager = tenant_manager
        
        # Initialize core components
        self.engine = self._create_optimized_engine()
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        
        # Circuit breakers for different operation types
        self.circuit_breakers = {
            'read': CircuitBreaker(failure_threshold=10, recovery_timeout=30),
            'write': CircuitBreaker(failure_threshold=5, recovery_timeout=60),
            'migration': CircuitBreaker(failure_threshold=2, recovery_timeout=300)
        }
        
        # Metrics and monitoring
        self.metrics = DatabaseMetrics()
        self.metrics_registry = CollectorRegistry()
        self._setup_prometheus_metrics()
        
        # Performance tracking
        self.query_tracker = {}
        self.slow_queries = []
        self.active_sessions = set()
        
        # Thread safety
        self._metrics_lock = threading.RLock()
        
        # Background tasks
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="db-mgr")
        self.monitoring_task = None
        
        logger.info("ProductionDatabaseManager initialized successfully")
    
    def _create_optimized_engine(self) -> Engine:
        """
        Create optimized database engine with production settings.
        Enhanced from backend/app/db/session.py patterns.
        """
        # Build connection arguments
        connect_args = {
            "connect_timeout": 10,
            "application_name": "taxpoynt_platform",
            "options": "-c statement_timeout=30000"  # 30 second statement timeout
        }
        
        # Add SSL configuration if specified
        if self.config.ssl_mode != "disable":
            connect_args["sslmode"] = self.config.ssl_mode
            
            if self.config.ssl_cert_path:
                connect_args["sslcert"] = self.config.ssl_cert_path
            if self.config.ssl_key_path:
                connect_args["sslkey"] = self.config.ssl_key_path
            if self.config.ssl_ca_path:
                connect_args["sslrootcert"] = self.config.ssl_ca_path
        
        # Determine pool class based on environment
        pool_class = QueuePool if "railway" not in self.config.database_url.lower() else NullPool
        
        # Create engine with optimized settings
        engine = create_engine(
            self.config.database_url,
            poolclass=pool_class,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            connect_args=connect_args,
            echo=self.config.enable_query_logging,
            echo_pool=False,  # Disable pool logging in production
            future=True  # Use SQLAlchemy 2.0 API
        )
        
        # Set up event listeners for monitoring
        self._setup_engine_events(engine)
        
        return engine
    
    def _setup_engine_events(self, engine: Engine):
        """Set up SQLAlchemy event listeners for monitoring."""
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                execution_time = (time.time() - context._query_start_time) * 1000
                
                # Track slow queries
                if execution_time > self.config.slow_query_threshold_ms:
                    self.slow_queries.append({
                        'statement': statement[:500],  # Truncate long statements
                        'execution_time_ms': execution_time,
                        'timestamp': datetime.utcnow()
                    })
                    
                    # Keep only recent slow queries
                    if len(self.slow_queries) > 100:
                        self.slow_queries = self.slow_queries[-50:]
                
                # Update metrics
                with self._metrics_lock:
                    self.metrics.total_queries_count += 1
                    if execution_time > self.config.slow_query_threshold_ms:
                        self.metrics.slow_queries_count += 1
        
        @event.listens_for(engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            # Set connection-level configurations
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = 30000")  # 30 seconds
                cursor.execute("SET idle_in_transaction_session_timeout = 300000")  # 5 minutes
        
        @event.listens_for(engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            with self._metrics_lock:
                self.metrics.active_connections += 1
        
        @event.listens_for(engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            with self._metrics_lock:
                if self.metrics.active_connections > 0:
                    self.metrics.active_connections -= 1
    
    def _setup_prometheus_metrics(self):
        """Set up Prometheus metrics for monitoring."""
        if not self.config.enable_metrics:
            return
        
        self.prometheus_metrics = {
            'db_connections_active': Gauge(
                'db_connections_active',
                'Number of active database connections',
                registry=self.metrics_registry
            ),
            'db_query_duration': Histogram(
                'db_query_duration_seconds',
                'Database query execution time',
                registry=self.metrics_registry
            ),
            'db_queries_total': Counter(
                'db_queries_total',
                'Total number of database queries',
                ['status'],
                registry=self.metrics_registry
            ),
            'db_transactions_total': Counter(
                'db_transactions_total',
                'Total number of database transactions',
                ['status'],
                registry=self.metrics_registry
            ),
            'db_slow_queries_total': Counter(
                'db_slow_queries_total',
                'Total number of slow database queries',
                registry=self.metrics_registry
            )
        }
    
    @asynccontextmanager
    async def get_session(self, tenant_id: Optional[UUID] = None) -> Session:
        """
        Get database session with automatic cleanup and tenant context.
        Enhanced from backend/app/db/session.py patterns.
        
        Args:
            tenant_id: Optional tenant ID for multi-tenant operations
            
        Yields:
            Database session
        """
        session = None
        session_id = str(uuid4())
        
        try:
            # Create session with circuit breaker protection
            session = await self.circuit_breakers['read'].call(
                self.session_factory
            )
            
            # Set tenant context if provided
            if tenant_id and self.tenant_manager:
                self.tenant_manager.set_tenant_context(session, tenant_id)
            
            # Track active session
            self.active_sessions.add(session_id)
            
            yield session
            
        except Exception as e:
            if session:
                session.rollback()
                logger.error(f"Session {session_id} rolled back due to error: {e}")
            raise
        
        finally:
            if session:
                session.close()
            
            self.active_sessions.discard(session_id)
    
    @contextmanager
    def get_sync_session(self, tenant_id: Optional[UUID] = None) -> Session:
        """
        Get synchronous database session with automatic cleanup.
        
        Args:
            tenant_id: Optional tenant ID for multi-tenant operations
            
        Yields:
            Database session
        """
        session = None
        session_id = str(uuid4())
        
        try:
            session = self.session_factory()
            
            # Set tenant context if provided
            if tenant_id and self.tenant_manager:
                self.tenant_manager.set_tenant_context(session, tenant_id)
            
            # Track active session
            self.active_sessions.add(session_id)
            
            yield session
            
        except Exception as e:
            if session:
                session.rollback()
                logger.error(f"Sync session {session_id} rolled back due to error: {e}")
            raise
        
        finally:
            if session:
                session.close()
            
            self.active_sessions.discard(session_id)
    
    async def execute_with_retry(
        self,
        operation: Callable,
        operation_type: str = 'read',
        max_retries: int = 3,
        retry_delay: float = 1.0,
        *args,
        **kwargs
    ):
        """
        Execute database operation with retry logic and circuit breaker protection.
        
        Args:
            operation: Database operation to execute
            operation_type: Type of operation (read/write/migration)
            max_retries: Maximum number of retries
            retry_delay: Initial retry delay in seconds
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
        """
        circuit_breaker = self.circuit_breakers.get(operation_type, self.circuit_breakers['read'])
        
        for attempt in range(max_retries + 1):
            try:
                return await circuit_breaker.call(operation, *args, **kwargs)
            
            except (OperationalError, DisconnectionError) as e:
                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Database operation failed after {max_retries + 1} attempts: {e}")
                    raise
            
            except Exception as e:
                logger.error(f"Non-retryable database error: {e}")
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive database health check.
        
        Returns:
            Health check results
        """
        health_data = {
            "status": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Basic connectivity check
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                health_data["checks"]["connectivity"] = {
                    "status": "healthy",
                    "response_time_ms": 0  # Would track actual response time
                }
            
            # Pool status check
            pool_status = self._check_connection_pool_health()
            health_data["checks"]["connection_pool"] = pool_status
            
            # Replication lag check (if applicable)
            replication_status = await self._check_replication_health()
            health_data["checks"]["replication"] = replication_status
            
            # Backup status check
            if self.backup_orchestrator:
                backup_status = await self.backup_orchestrator.get_backup_status()
                health_data["checks"]["backup"] = backup_status
            
            # Overall status determination
            all_healthy = all(
                check.get("status") == "healthy"
                for check in health_data["checks"].values()
            )
            
            health_data["status"] = "healthy" if all_healthy else "degraded"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_data["status"] = "unhealthy"
            health_data["error"] = str(e)
        
        return health_data
    
    def _check_connection_pool_health(self) -> Dict[str, Any]:
        """Check connection pool health status."""
        try:
            pool = self.engine.pool
            
            status_data = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
            # Determine pool status
            utilization = (status_data["checked_out"] / (status_data["size"] + status_data["overflow"])) * 100
            
            if utilization < 50:
                pool_status = "healthy"
            elif utilization < 80:
                pool_status = "warning"
            else:
                pool_status = "critical"
            
            return {
                "status": pool_status,
                "utilization_percent": utilization,
                "metrics": status_data
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_replication_health(self) -> Dict[str, Any]:
        """Check database replication health."""
        try:
            async with self.get_session() as session:
                # Check if this is a replica
                result = await session.execute(text("SELECT pg_is_in_recovery()"))
                is_replica = result.scalar()
                
                if is_replica:
                    # Check replication lag
                    lag_result = await session.execute(text("""
                        SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))::int
                    """))
                    lag_seconds = lag_result.scalar() or 0
                    
                    status = "healthy" if lag_seconds < 5 else "warning" if lag_seconds < 30 else "critical"
                    
                    return {
                        "status": status,
                        "is_replica": True,
                        "lag_seconds": lag_seconds
                    }
                else:
                    return {
                        "status": "healthy",
                        "is_replica": False,
                        "lag_seconds": 0
                    }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def collect_metrics(self) -> DatabaseMetrics:
        """
        Collect comprehensive database metrics.
        
        Returns:
            Updated database metrics
        """
        try:
            async with self.get_session() as session:
                # Connection metrics
                conn_result = await session.execute(text("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """))
                
                conn_data = conn_result.fetchone()
                
                with self._metrics_lock:
                    self.metrics.total_connections = conn_data.total_connections
                    self.metrics.active_connections = conn_data.active_connections
                    self.metrics.idle_connections = conn_data.idle_connections
                
                # Database size
                size_result = await session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           pg_database_size(current_database()) as size_bytes
                """))
                
                size_data = size_result.fetchone()
                self.metrics.database_size_mb = size_data.size_bytes / (1024 * 1024)
                
                # Cache hit ratio
                cache_result = await session.execute(text("""
                    SELECT 
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
                    FROM pg_statio_user_tables
                """))
                
                cache_ratio = cache_result.scalar()
                if cache_ratio is not None:
                    self.metrics.cache_hit_ratio = cache_ratio
            
            # Update Prometheus metrics if enabled
            if self.config.enable_metrics and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics['db_connections_active'].set(self.metrics.active_connections)
            
            # Determine health status
            self.metrics.health_status = self._determine_health_status()
            self.metrics.pool_status = self._determine_pool_status()
            
            self.metrics.timestamp = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            self.metrics.health_status = DatabaseHealth.CRITICAL
        
        return self.metrics
    
    def _determine_health_status(self) -> DatabaseHealth:
        """Determine overall database health status."""
        # Check connection pool utilization
        if self.metrics.total_connections > 0:
            utilization = (self.metrics.active_connections / self.metrics.total_connections) * 100
            
            if utilization > 90:
                return DatabaseHealth.CRITICAL
            elif utilization > 75:
                return DatabaseHealth.DEGRADED
        
        # Check cache hit ratio
        if self.metrics.cache_hit_ratio < 80:
            return DatabaseHealth.DEGRADED
        
        # Check slow queries
        recent_slow_queries = len([
            q for q in self.slow_queries
            if q['timestamp'] > datetime.utcnow() - timedelta(minutes=5)
        ])
        
        if recent_slow_queries > 10:
            return DatabaseHealth.DEGRADED
        
        return DatabaseHealth.HEALTHY
    
    def _determine_pool_status(self) -> ConnectionPoolStatus:
        """Determine connection pool status."""
        if hasattr(self.engine, 'pool'):
            pool = self.engine.pool
            total_capacity = pool.size() + pool.overflow()
            used_connections = pool.checkedout()
            
            if total_capacity > 0:
                utilization = (used_connections / total_capacity) * 100
                
                if utilization > 95:
                    return ConnectionPoolStatus.EXHAUSTED
                elif utilization > 85:
                    return ConnectionPoolStatus.CRITICAL
                elif utilization > 70:
                    return ConnectionPoolStatus.WARNING
        
        return ConnectionPoolStatus.OPTIMAL
    
    async def start_monitoring(self):
        """Start background monitoring tasks."""
        if self.config.enable_metrics and not self.monitoring_task:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Database monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            
            self.monitoring_task = None
            logger.info("Database monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                await self.collect_metrics()
                await asyncio.sleep(self.config.metrics_collection_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def run_migration(self, target_revision: Optional[str] = None) -> Dict[str, Any]:
        """
        Run database migrations with enhanced safety checks.
        
        Args:
            target_revision: Target migration revision
            
        Returns:
            Migration result
        """
        if not self.migration_engine:
            raise ValueError("Migration engine not configured")
        
        try:
            # Run migration with circuit breaker protection
            result = await self.circuit_breakers['migration'].call(
                self.migration_engine.run_migrations,
                target_revision=target_revision
            )
            
            logger.info(f"Database migration completed successfully: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            raise
    
    async def create_backup(self, backup_type: str = "full") -> Dict[str, Any]:
        """
        Create database backup.
        
        Args:
            backup_type: Type of backup (full, incremental)
            
        Returns:
            Backup result
        """
        if not self.backup_orchestrator:
            raise ValueError("Backup orchestrator not configured")
        
        try:
            result = await self.backup_orchestrator.create_backup(
                backup_type=backup_type
            )
            
            # Update metrics
            self.metrics.last_backup = datetime.utcnow()
            
            logger.info(f"Database backup created successfully: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """
        Get detailed performance statistics.
        
        Returns:
            Performance statistics
        """
        return {
            "metrics": {
                "active_connections": self.metrics.active_connections,
                "total_connections": self.metrics.total_connections,
                "database_size_mb": self.metrics.database_size_mb,
                "cache_hit_ratio": self.metrics.cache_hit_ratio,
                "health_status": self.metrics.health_status.value,
                "pool_status": self.metrics.pool_status.value
            },
            "slow_queries": {
                "count": len(self.slow_queries),
                "recent_queries": self.slow_queries[-10:] if self.slow_queries else []
            },
            "active_sessions": len(self.active_sessions),
            "circuit_breakers": {
                name: {
                    "state": breaker.state,
                    "failure_count": breaker.failure_count
                }
                for name, breaker in self.circuit_breakers.items()
            }
        }
    
    async def optimize_database(self) -> Dict[str, Any]:
        """
        Run database optimization tasks.
        
        Returns:
            Optimization results
        """
        optimization_results = {
            "vacuum_results": [],
            "reindex_results": [],
            "analyze_results": []
        }
        
        try:
            async with self.get_session() as session:
                # Run VACUUM ANALYZE on user tables
                tables_result = await session.execute(text("""
                    SELECT schemaname, tablename
                    FROM pg_tables
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY schemaname, tablename
                """))
                
                for table_row in tables_result:
                    schema_name = table_row.schemaname
                    table_name = table_row.tablename
                    full_table_name = f"{schema_name}.{table_name}"
                    
                    try:
                        # VACUUM ANALYZE
                        await session.execute(text(f"VACUUM ANALYZE {full_table_name}"))
                        optimization_results["vacuum_results"].append({
                            "table": full_table_name,
                            "status": "success"
                        })
                    
                    except Exception as e:
                        optimization_results["vacuum_results"].append({
                            "table": full_table_name,
                            "status": "failed",
                            "error": str(e)
                        })
                
                # Update table statistics
                await session.execute(text("ANALYZE"))
                optimization_results["analyze_results"].append({
                    "operation": "analyze_all",
                    "status": "success"
                })
            
            logger.info("Database optimization completed")
        
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            optimization_results["error"] = str(e)
        
        return optimization_results
    
    def close(self):
        """Close database manager and cleanup resources."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        
        if self.engine:
            self.engine.dispose()
        
        logger.info("ProductionDatabaseManager closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass


# Factory functions for common configurations
def create_database_manager(
    database_url: str,
    enable_monitoring: bool = True,
    enable_backups: bool = True,
    enable_multi_tenant: bool = True
) -> ProductionDatabaseManager:
    """
    Factory function to create production database manager.
    
    Args:
        database_url: Database connection URL
        enable_monitoring: Enable monitoring and metrics
        enable_backups: Enable backup orchestration
        enable_multi_tenant: Enable multi-tenant support
        
    Returns:
        Configured ProductionDatabaseManager instance
    """
    # Create configuration
    config = DatabaseConfiguration(
        database_url=database_url,
        enable_metrics=enable_monitoring,
        backup_enabled=enable_backups
    )
    
    # Create optional components
    cache_manager = CacheManager(CacheConfig()) if enable_monitoring else None
    backup_orchestrator = BackupOrchestrator() if enable_backups else None
    migration_engine = MigrationEngine()
    tenant_manager = MultiTenantManager() if enable_multi_tenant else None
    
    return ProductionDatabaseManager(
        config=config,
        cache_manager=cache_manager,
        backup_orchestrator=backup_orchestrator,
        migration_engine=migration_engine,
        tenant_manager=tenant_manager
    )


def create_railway_optimized_manager(database_url: str) -> ProductionDatabaseManager:
    """
    Create database manager optimized for Railway deployment.
    
    Args:
        database_url: Railway database URL
        
    Returns:
        Railway-optimized ProductionDatabaseManager instance
    """
    config = DatabaseConfiguration(
        database_url=database_url,
        pool_size=3,  # Smaller pool for Railway
        max_overflow=5,
        pool_timeout=10,
        pool_recycle=300,  # Shorter recycle time
        query_timeout=20,  # Shorter timeout
        enable_metrics=True,
        backup_enabled=True
    )
    
    # Create lightweight components for Railway
    cache_manager = CacheManager(CacheConfig(
        max_memory_cache_size=500,  # Smaller cache
        default_ttl_seconds=1800   # 30 minutes
    ))
    
    return ProductionDatabaseManager(
        config=config,
        cache_manager=cache_manager
    )
