"""
Database Abstraction Layer for TaxPoynt Platform

Provides unified database operations across SQLite (development) and PostgreSQL (production)
with Railway platform optimizations and multi-engine support.
"""

import logging
import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Type, Union, Generator
from uuid import UUID
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.sql import text as sql_text
import time
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseEngine(Enum):
    """Supported database engines."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class DatabaseError(Exception):
    """Base database error."""
    pass


class ConnectionError(DatabaseError):
    """Database connection error."""
    pass


class QueryError(DatabaseError):
    """Database query error."""
    pass


class DatabaseAbstractionLayer:
    """
    Unified database abstraction layer supporting multiple engines
    with optimizations for different deployment environments.
    """
    
    def __init__(self, database_url: str, **kwargs):
        """
        Initialize database abstraction layer.
        
        Args:
            database_url: Database connection URL
            **kwargs: Additional engine configuration
        """
        self.database_url = database_url
        self.engine_type = self._detect_engine_type(database_url)
        self.engine = None
        self.session_factory = None
        self._connection_pool_config = kwargs
        
        # Performance tracking
        self._query_count = 0
        self._slow_query_threshold = 1.0  # seconds
        
        self._initialize_engine()
        
    def _detect_engine_type(self, database_url: str) -> DatabaseEngine:
        """Detect database engine from URL."""
        if database_url.startswith("sqlite"):
            return DatabaseEngine.SQLITE
        elif database_url.startswith("postgresql"):
            return DatabaseEngine.POSTGRESQL
        else:
            raise DatabaseError(f"Unsupported database URL: {database_url}")
    
    def _get_engine_config(self) -> Dict[str, Any]:
        """Get engine configuration based on environment and engine type."""
        config = {}
        
        if self.engine_type == DatabaseEngine.SQLITE:
            # SQLite configuration for development/testing
            config.update({
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 20
                },
                "echo": os.getenv("APP_ENV") == "development"
            })
        
        elif self.engine_type == DatabaseEngine.POSTGRESQL:
            # PostgreSQL configuration with Railway optimizations
            base_config = {
                "poolclass": QueuePool,
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 20,
                "pool_recycle": 300,  # 5 minutes
                "pool_pre_ping": True,
                "connect_args": {
                    "connect_timeout": 10,
                    "server_side_cursors": True
                }
            }
            
            # Railway-specific optimizations
            if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_DEPLOYMENT"):
                base_config.update({
                    "pool_size": 3,  # Smaller pool for Railway
                    "max_overflow": 5,
                    "pool_timeout": 10,
                    "connect_args": {
                        "connect_timeout": 5,
                        "server_side_cursors": True
                    }
                })
            
            config.update(base_config)
        
        # Override with user-provided config
        config.update(self._connection_pool_config)
        
        return config
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with appropriate configuration."""
        try:
            config = self._get_engine_config()
            self.engine = create_engine(self.database_url, **config)
            
            # Setup event listeners for monitoring
            self._setup_event_listeners()
            
            # Create session factory
            self.session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            self._test_connection()
            
            logger.info(f"Database engine initialized: {self.engine_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise ConnectionError(f"Database initialization failed: {e}")
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring."""
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            self._query_count += 1
            
            if total > self._slow_query_threshold:
                logger.warning(f"Slow query detected ({total:.2f}s): {statement[:100]}...")
    
    def _test_connection(self):
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                if self.engine_type == DatabaseEngine.SQLITE:
                    conn.execute(sql_text("SELECT 1"))
                elif self.engine_type == DatabaseEngine.POSTGRESQL:
                    conn.execute(sql_text("SELECT version()"))
            
            logger.info("Database connection test successful")
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise ConnectionError(f"Database connection test failed: {e}")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic cleanup.
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error, rolling back: {e}")
            raise QueryError(f"Database operation failed: {e}")
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """
        Get database session directly (caller must manage lifecycle).
        
        Returns:
            Session: SQLAlchemy session
        """
        return self.session_factory()
    
    def execute_raw_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute raw SQL query with parameters.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(sql_text(query), params or {})
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            logger.error(f"Raw query execution failed: {e}")
            raise QueryError(f"Query execution failed: {e}")
    
    def execute_raw_dml(self, query: str, params: Optional[Dict] = None) -> int:
        """
        Execute raw DML (INSERT, UPDATE, DELETE) query.
        
        Args:
            query: DML query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(sql_text(query), params or {})
                    return result.rowcount
                    
        except Exception as e:
            logger.error(f"DML query execution failed: {e}")
            raise QueryError(f"DML execution failed: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            Dictionary containing database info
        """
        info = {
            "engine_type": self.engine_type.value,
            "database_url": self.database_url.split("@")[-1] if "@" in self.database_url else self.database_url,
            "query_count": self._query_count
        }
        
        try:
            if self.engine_type == DatabaseEngine.POSTGRESQL:
                with self.engine.connect() as conn:
                    # Get PostgreSQL version
                    version_result = conn.execute(sql_text("SELECT version()"))
                    info["version"] = version_result.scalar()
                    
                    # Get connection count
                    conn_result = conn.execute(sql_text(
                        "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                    ))
                    info["active_connections"] = conn_result.scalar()
            
            elif self.engine_type == DatabaseEngine.SQLITE:
                with self.engine.connect() as conn:
                    # Get SQLite version
                    version_result = conn.execute(sql_text("SELECT sqlite_version()"))
                    info["version"] = f"SQLite {version_result.scalar()}"
                    
        except Exception as e:
            logger.warning(f"Could not retrieve database info: {e}")
            info["info_error"] = str(e)
        
        return info
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check.
        
        Returns:
            Dictionary containing health status
        """
        start_time = time.time()
        health = {
            "status": "unknown",
            "response_time_ms": 0,
            "error": None
        }
        
        try:
            # Test basic connectivity
            with self.engine.connect() as conn:
                conn.execute(sql_text("SELECT 1"))
            
            health["status"] = "healthy"
            health["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
            health["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
            
            logger.error(f"Database health check failed: {e}")
        
        return health
    
    def optimize_for_environment(self):
        """Apply environment-specific optimizations."""
        try:
            if self.engine_type == DatabaseEngine.POSTGRESQL:
                # PostgreSQL-specific optimizations
                with self.engine.connect() as conn:
                    # Set optimal connection parameters
                    conn.execute(sql_text("SET statement_timeout = '30s'"))
                    conn.execute(sql_text("SET lock_timeout = '10s'"))
                    conn.execute(sql_text("SET idle_in_transaction_session_timeout = '60s'"))
                    
                    # Railway-specific settings
                    if os.getenv("RAILWAY_ENVIRONMENT"):
                        conn.execute(sql_text("SET work_mem = '4MB'"))
                        conn.execute(sql_text("SET maintenance_work_mem = '16MB'"))
            
            elif self.engine_type == DatabaseEngine.SQLITE:
                # SQLite-specific optimizations
                with self.engine.connect() as conn:
                    conn.execute(sql_text("PRAGMA journal_mode = WAL"))
                    conn.execute(sql_text("PRAGMA synchronous = NORMAL"))
                    conn.execute(sql_text("PRAGMA cache_size = 1000"))
                    conn.execute(sql_text("PRAGMA temp_store = MEMORY"))
            
            logger.info("Database optimizations applied successfully")
            
        except Exception as e:
            logger.warning(f"Could not apply database optimizations: {e}")
    
    def close(self):
        """Close database engine and cleanup resources."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine closed")


class DatabaseAbstractionFactory:
    """Factory for creating database abstraction instances."""
    
    _instances: Dict[str, DatabaseAbstractionLayer] = {}
    
    @classmethod
    def create_database_layer(
        cls,
        database_url: str,
        instance_name: str = "default",
        **kwargs
    ) -> DatabaseAbstractionLayer:
        """
        Create or retrieve database abstraction layer instance.
        
        Args:
            database_url: Database connection URL
            instance_name: Name for this instance
            **kwargs: Additional engine configuration
            
        Returns:
            DatabaseAbstractionLayer instance
        """
        if instance_name not in cls._instances:
            cls._instances[instance_name] = DatabaseAbstractionLayer(
                database_url, **kwargs
            )
        
        return cls._instances[instance_name]
    
    @classmethod
    def get_instance(cls, instance_name: str = "default") -> Optional[DatabaseAbstractionLayer]:
        """Get existing database layer instance."""
        return cls._instances.get(instance_name)
    
    @classmethod
    def close_all(cls):
        """Close all database layer instances."""
        for instance in cls._instances.values():
            instance.close()
        cls._instances.clear()


# Convenience functions for backward compatibility
def create_database_layer(database_url: str, **kwargs) -> DatabaseAbstractionLayer:
    """Create database abstraction layer."""
    return DatabaseAbstractionFactory.create_database_layer(database_url, **kwargs)


def get_database_layer(instance_name: str = "default") -> Optional[DatabaseAbstractionLayer]:
    """Get database abstraction layer instance."""
    return DatabaseAbstractionFactory.get_instance(instance_name)