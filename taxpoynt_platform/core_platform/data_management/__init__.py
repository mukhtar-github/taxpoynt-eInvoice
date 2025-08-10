"""
Data Management Package for TaxPoynt Platform

Enterprise-grade data management with multi-tenant support, caching,
backup orchestration, and migration capabilities for 100K+ invoice processing.

This package provides:
- Database abstraction layer (SQLite/PostgreSQL)
- Multi-tenant data isolation and management
- Distributed caching with Redis integration
- Automated backup orchestration with cloud storage
- Zero-downtime database migrations
- Repository pattern with caching and filtering

Usage:
    from taxpoynt_platform.core_platform.data_management import (
        DataManagementService,
        DatabaseAbstractionLayer,
        MultiTenantManager,
        CacheManager,
        BackupOrchestrator,
        MigrationEngine,
        BaseRepository
    )
    
    # Initialize data management service
    data_service = DataManagementService(config)
    
    # Access individual components
    db_layer = data_service.database_layer
    tenant_manager = data_service.tenant_manager
    cache_manager = data_service.cache_manager
"""

import logging
from typing import Any, Dict, Optional, List
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass

# Core components
from .database_abstraction import (
    DatabaseAbstractionLayer,
    DatabaseAbstractionFactory,
    DatabaseEngine,
    DatabaseError,
    ConnectionError,
    QueryError,
    create_database_layer,
    get_database_layer
)

from .multi_tenant_manager import (
    MultiTenantManager,
    TenantConfig,
    TenantMetrics,
    TenantContext,
    TenantIsolationLevel,
    TenantTier,
    get_tenant_manager,
    initialize_tenant_manager
)

from .cache_manager import (
    CacheManager,
    CacheConfig,
    CacheMetrics,
    CacheStrategy,
    CacheLevel,
    SerializationFormat,
    CircuitBreaker,
    MemoryCache,
    get_cache_manager,
    initialize_cache_manager
)

from .backup_orchestrator import (
    BackupOrchestrator,
    BackupConfig,
    BackupJob,
    BackupMetrics,
    BackupType,
    BackupStatus,
    StorageBackend,
    CompressionType,
    get_backup_orchestrator,
    initialize_backup_orchestrator
)

from .migration_engine import (
    MigrationEngine,
    MigrationMetadata,
    MigrationExecution,
    MigrationStatus,
    MigrationDirection,
    MigrationStrategy,
    BaseMigration,
    SQLMigration,
    PythonMigration,
    get_migration_engine,
    initialize_migration_engine
)

from .repository_base import (
    BaseRepository,
    ReadOnlyRepository,
    FilterCriteria,
    SortCriteria,
    PaginationParams,
    PaginatedResult,
    SortDirection,
    FilterOperator,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    create_filter,
    create_sort,
    create_pagination
)

logger = logging.getLogger(__name__)


@dataclass
class DataManagementConfig:
    """Configuration for data management service."""
    # Database configuration
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_timeout: int = 20
    
    # Cache configuration
    redis_url: Optional[str] = None
    cache_enabled: bool = True
    cache_default_ttl: int = 3600
    cache_max_memory_size: int = 1000
    
    # Backup configuration
    backup_enabled: bool = True
    backup_local_path: str = "/tmp/taxpoynt_backups"
    backup_s3_bucket: Optional[str] = None
    backup_retention_days: int = 30
    
    # Migration configuration
    migrations_path: str = "migrations"
    migration_timeout_minutes: int = 120
    
    # Performance settings
    enable_metrics: bool = True
    log_slow_queries: bool = True
    slow_query_threshold: float = 1.0


class DataManagementService:
    """
    Unified data management service orchestrating all data components.
    
    This service provides a single entry point for all data management
    operations, ensuring proper initialization and coordination between
    database, caching, backup, and migration systems.
    """
    
    def __init__(self, config: DataManagementConfig):
        """
        Initialize data management service.
        
        Args:
            config: Data management configuration
        """
        self.config = config
        self._initialized = False
        
        # Component references
        self.database_layer: Optional[DatabaseAbstractionLayer] = None
        self.tenant_manager: Optional[MultiTenantManager] = None
        self.cache_manager: Optional[CacheManager] = None
        self.backup_orchestrator: Optional[BackupOrchestrator] = None
        self.migration_engine: Optional[MigrationEngine] = None
        
        # Performance tracking
        self._start_time = datetime.utcnow()
        self._operation_count = 0
        
        logger.info("Data management service created")
    
    def initialize(self) -> None:
        """Initialize all data management components."""
        if self._initialized:
            logger.warning("Data management service already initialized")
            return
        
        try:
            # 1. Initialize database layer
            self._initialize_database()
            
            # 2. Initialize cache manager
            self._initialize_cache()
            
            # 3. Initialize tenant manager
            self._initialize_tenant_manager()
            
            # 4. Initialize backup orchestrator
            self._initialize_backup()
            
            # 5. Initialize migration engine
            self._initialize_migration_engine()
            
            # 6. Perform health checks
            self._perform_initialization_health_checks()
            
            self._initialized = True
            logger.info("Data management service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize data management service: {e}")
            self.close()
            raise
    
    def _initialize_database(self):
        """Initialize database abstraction layer."""
        try:
            database_config = {
                "pool_size": self.config.database_pool_size,
                "max_overflow": self.config.database_max_overflow,
                "pool_timeout": self.config.database_timeout
            }
            
            self.database_layer = DatabaseAbstractionFactory.create_database_layer(
                self.config.database_url,
                "default",
                **database_config
            )
            
            # Apply environment optimizations
            self.database_layer.optimize_for_environment()
            
            logger.info("Database layer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database layer: {e}")
            raise
    
    def _initialize_cache(self):
        """Initialize cache manager."""
        if not self.config.cache_enabled:
            logger.info("Cache manager disabled by configuration")
            return
        
        try:
            cache_config = CacheConfig(
                redis_url=self.config.redis_url,
                default_ttl_seconds=self.config.cache_default_ttl,
                max_memory_cache_size=self.config.cache_max_memory_size,
                enable_metrics=self.config.enable_metrics
            )
            
            self.cache_manager = initialize_cache_manager(cache_config)
            
            logger.info("Cache manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            # Cache is not critical, continue without it
            self.cache_manager = None
    
    def _initialize_tenant_manager(self):
        """Initialize tenant manager."""
        try:
            self.tenant_manager = initialize_tenant_manager(
                self.database_layer,
                self.cache_manager
            )
            
            logger.info("Tenant manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize tenant manager: {e}")
            raise
    
    def _initialize_backup(self):
        """Initialize backup orchestrator."""
        if not self.config.backup_enabled:
            logger.info("Backup orchestrator disabled by configuration")
            return
        
        try:
            backup_config = BackupConfig(
                local_backup_path=self.config.backup_local_path,
                aws_s3_bucket=self.config.backup_s3_bucket,
                retention_days=self.config.backup_retention_days
            )
            
            self.backup_orchestrator = initialize_backup_orchestrator(
                backup_config,
                self.database_layer,
                self.tenant_manager
            )
            
            logger.info("Backup orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize backup orchestrator: {e}")
            # Backup is not critical for startup, continue without it
            self.backup_orchestrator = None
    
    def _initialize_migration_engine(self):
        """Initialize migration engine."""
        try:
            self.migration_engine = initialize_migration_engine(
                self.database_layer,
                self.tenant_manager,
                self.config.migrations_path
            )
            
            logger.info("Migration engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize migration engine: {e}")
            # Migration engine is not critical for runtime, continue without it
            self.migration_engine = None
    
    def _perform_initialization_health_checks(self):
        """Perform health checks after initialization."""
        health_status = self.health_check()
        
        if health_status["status"] != "healthy":
            logger.warning(f"Data management service health check failed: {health_status}")
        
        # Check for critical issues
        if not self.database_layer:
            raise Exception("Database layer is required but not initialized")
        
        if not self.tenant_manager:
            raise Exception("Tenant manager is required but not initialized")
    
    def set_tenant_context(self, tenant_id: UUID, organization_id: UUID, user_id: Optional[UUID] = None):
        """Set tenant context for all components."""
        if not self._initialized:
            raise Exception("Data management service not initialized")
        
        # Set tenant context in tenant manager
        if self.tenant_manager:
            self.tenant_manager.set_tenant_context(tenant_id, organization_id, user_id)
        
        # Set tenant context in cache manager
        if self.cache_manager:
            self.cache_manager.set_tenant_context(tenant_id, organization_id)
    
    def clear_tenant_context(self):
        """Clear tenant context from all components."""
        if self.tenant_manager:
            self.tenant_manager.clear_tenant_context()
    
    def create_repository(self, model_class, create_schema=None, update_schema=None) -> BaseRepository:
        """
        Create a repository instance for a model.
        
        Args:
            model_class: SQLAlchemy model class
            create_schema: Optional create schema type
            update_schema: Optional update schema type
            
        Returns:
            Repository instance
        """
        if not self._initialized:
            raise Exception("Data management service not initialized")
        
        if not self.database_layer:
            raise Exception("Database layer not available")
        
        def session_factory():
            return self.database_layer.get_session_direct()
        
        return BaseRepository(
            model=model_class,
            session_factory=session_factory,
            tenant_manager=self.tenant_manager,
            cache_manager=self.cache_manager
        )
    
    def run_migrations(self, tenant_id: Optional[UUID] = None, dry_run: bool = False) -> List[Any]:
        """Run pending database migrations."""
        if not self.migration_engine:
            raise Exception("Migration engine not available")
        
        return self.migration_engine.run_migrations(tenant_id=tenant_id, dry_run=dry_run)
    
    def schedule_backup(self, backup_type: BackupType = BackupType.FULL, tenant_id: Optional[UUID] = None) -> str:
        """Schedule a backup job."""
        if not self.backup_orchestrator:
            raise Exception("Backup orchestrator not available")
        
        return self.backup_orchestrator.schedule_backup(backup_type, tenant_id)
    
    def get_tenant_metrics(self, tenant_id: UUID) -> Optional[TenantMetrics]:
        """Get metrics for specific tenant."""
        if not self.tenant_manager:
            return None
        
        return self.tenant_manager.get_tenant_metrics(tenant_id)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        metrics = {
            "service_uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds(),
            "operation_count": self._operation_count,
            "initialized": self._initialized
        }
        
        # Database metrics
        if self.database_layer:
            metrics["database"] = self.database_layer.get_database_info()
        
        # Cache metrics
        if self.cache_manager:
            metrics["cache"] = self.cache_manager.get_metrics()
        
        # Tenant manager metrics
        if self.tenant_manager:
            metrics["tenant_manager"] = self.tenant_manager.get_performance_stats()
        
        # Backup metrics
        if self.backup_orchestrator:
            metrics["backup"] = self.backup_orchestrator.get_metrics()
        
        return metrics
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        component_statuses = []
        
        # Database health
        if self.database_layer:
            db_health = self.database_layer.health_check()
            health["components"]["database"] = db_health
            component_statuses.append(db_health["status"])
        
        # Cache health
        if self.cache_manager:
            cache_health = self.cache_manager.health_check()
            health["components"]["cache"] = cache_health
            # Cache is not critical, don't affect overall status
        
        # Backup health
        if self.backup_orchestrator:
            backup_health = self.backup_orchestrator.health_check()
            health["components"]["backup"] = backup_health
            # Backup is not critical for runtime
        
        # Migration engine health
        if self.migration_engine:
            migration_health = self.migration_engine.health_check()
            health["components"]["migration"] = migration_health
            # Migration engine is not critical for runtime
        
        # Overall status
        if "unhealthy" in component_statuses:
            health["status"] = "unhealthy"
        elif "degraded" in component_statuses:
            health["status"] = "degraded"
        
        return health
    
    def close(self):
        """Close and cleanup all components."""
        try:
            if self.backup_orchestrator:
                self.backup_orchestrator.close()
            
            if self.cache_manager:
                self.cache_manager.close()
            
            if self.tenant_manager:
                self.tenant_manager.close()
            
            if self.database_layer:
                self.database_layer.close()
            
            # Clear global instances
            DatabaseAbstractionFactory.close_all()
            
            self._initialized = False
            logger.info("Data management service closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing data management service: {e}")


# Global data management service instance
_data_management_service: Optional[DataManagementService] = None


def get_data_management_service() -> Optional[DataManagementService]:
    """Get global data management service instance."""
    return _data_management_service


def initialize_data_management_service(config: DataManagementConfig) -> DataManagementService:
    """Initialize global data management service."""
    global _data_management_service
    _data_management_service = DataManagementService(config)
    _data_management_service.initialize()
    return _data_management_service


def close_data_management_service():
    """Close global data management service."""
    global _data_management_service
    if _data_management_service:
        _data_management_service.close()
        _data_management_service = None


# Package exports
__all__ = [
    # Core service
    "DataManagementService",
    "DataManagementConfig",
    "get_data_management_service",
    "initialize_data_management_service",
    "close_data_management_service",
    
    # Database abstraction
    "DatabaseAbstractionLayer",
    "DatabaseAbstractionFactory",
    "DatabaseEngine",
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "create_database_layer",
    "get_database_layer",
    
    # Multi-tenant management
    "MultiTenantManager",
    "TenantConfig",
    "TenantMetrics",
    "TenantContext",
    "TenantIsolationLevel",
    "TenantTier",
    "get_tenant_manager",
    "initialize_tenant_manager",
    
    # Cache management
    "CacheManager",
    "CacheConfig",
    "CacheMetrics",
    "CacheStrategy",
    "CacheLevel",
    "SerializationFormat",
    "CircuitBreaker",
    "MemoryCache",
    "get_cache_manager",
    "initialize_cache_manager",
    
    # Backup orchestration
    "BackupOrchestrator",
    "BackupConfig",
    "BackupJob",
    "BackupMetrics",
    "BackupType",
    "BackupStatus",
    "StorageBackend",
    "CompressionType",
    "get_backup_orchestrator",
    "initialize_backup_orchestrator",
    
    # Migration engine
    "MigrationEngine",
    "MigrationMetadata",
    "MigrationExecution",
    "MigrationStatus",
    "MigrationDirection",
    "MigrationStrategy",
    "BaseMigration",
    "SQLMigration",
    "PythonMigration",
    "get_migration_engine",
    "initialize_migration_engine",
    
    # Repository pattern
    "BaseRepository",
    "ReadOnlyRepository",
    "FilterCriteria",
    "SortCriteria",
    "PaginationParams",
    "PaginatedResult",
    "SortDirection",
    "FilterOperator",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "create_filter",
    "create_sort",
    "create_pagination"
]