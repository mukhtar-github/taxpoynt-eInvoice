"""
Authentication Seal Repository Service for APP Role

This service handles storage and management of authentication seals including:
- Seal persistence and retrieval
- Seal lifecycle management
- Seal indexing and searching
- Seal backup and recovery
- Seal audit and compliance
"""

import asyncio
import json
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from pathlib import Path
import hashlib
import uuid

from .seal_generator import AuthenticationSeal, SealType, SealAlgorithm, SealStatus, SealMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    """Storage backend types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"
    FILE_SYSTEM = "file_system"


class SealQueryFilter(Enum):
    """Seal query filter types"""
    BY_DOCUMENT_ID = "by_document_id"
    BY_SEAL_TYPE = "by_seal_type"
    BY_ALGORITHM = "by_algorithm"
    BY_STATUS = "by_status"
    BY_DATE_RANGE = "by_date_range"
    BY_EXPIRY = "by_expiry"
    BY_ISSUER = "by_issuer"


@dataclass
class SealSearchCriteria:
    """Criteria for searching seals"""
    document_id: Optional[str] = None
    seal_type: Optional[SealType] = None
    algorithm: Optional[SealAlgorithm] = None
    status: Optional[SealStatus] = None
    issuer: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "DESC"


@dataclass
class SealSearchResult:
    """Result of seal search"""
    seals: List[AuthenticationSeal]
    total_count: int
    page_size: int
    page_offset: int
    has_more: bool
    search_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SealAuditEvent:
    """Audit event for seal operations"""
    event_id: str
    seal_id: str
    document_id: str
    operation: str
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class RepositoryStats:
    """Repository statistics"""
    total_seals: int
    seals_by_type: Dict[str, int]
    seals_by_status: Dict[str, int]
    seals_by_algorithm: Dict[str, int]
    expired_seals: int
    seals_created_today: int
    seals_created_this_week: int
    seals_created_this_month: int
    storage_size: int
    last_backup: Optional[datetime] = None
    last_cleanup: Optional[datetime] = None


class SealRepository:
    """
    Authentication seal repository service for APP role
    
    Handles:
    - Seal persistence and retrieval
    - Seal lifecycle management
    - Seal indexing and searching
    - Seal backup and recovery
    - Seal audit and compliance
    """
    
    def __init__(self, 
                 storage_backend: StorageBackend = StorageBackend.SQLITE,
                 database_path: str = "seal_repository.db",
                 enable_audit: bool = True,
                 auto_cleanup: bool = True,
                 backup_interval: int = 3600):  # 1 hour
        self.storage_backend = storage_backend
        self.database_path = database_path
        self.enable_audit = enable_audit
        self.auto_cleanup = auto_cleanup
        self.backup_interval = backup_interval
        
        # Database connection
        self.db_connection: Optional[aiosqlite.Connection] = None
        
        # In-memory cache for frequently accessed seals
        self.seal_cache: Dict[str, AuthenticationSeal] = {}
        self.cache_size_limit = 1000
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.backup_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            'total_operations': 0,
            'store_operations': 0,
            'retrieve_operations': 0,
            'search_operations': 0,
            'delete_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_operation_time': 0.0
        }
    
    async def start(self):
        """Start the repository service"""
        # Initialize database
        await self._init_database()
        
        # Start background tasks
        if self.auto_cleanup:
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        self.backup_task = asyncio.create_task(self._periodic_backup())
        
        logger.info("Seal repository started")
    
    async def stop(self):
        """Stop the repository service"""
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.backup_task:
            self.backup_task.cancel()
        
        # Close database connection
        if self.db_connection:
            await self.db_connection.close()
        
        logger.info("Seal repository stopped")
    
    async def _init_database(self):
        """Initialize database"""
        if self.storage_backend == StorageBackend.SQLITE:
            await self._init_sqlite_database()
        else:
            raise ValueError(f"Unsupported storage backend: {self.storage_backend}")
    
    async def _init_sqlite_database(self):
        """Initialize SQLite database"""
        self.db_connection = await aiosqlite.connect(self.database_path)
        
        # Create seals table
        await self.db_connection.execute('''
            CREATE TABLE IF NOT EXISTS seals (
                seal_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                seal_type TEXT NOT NULL,
                seal_value TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                issuer TEXT,
                version TEXT,
                certificate_thumbprint TEXT,
                key_id TEXT,
                verification_data TEXT,
                metadata TEXT
            )
        ''')
        
        # Create audit table
        if self.enable_audit:
            await self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS seal_audit (
                    event_id TEXT PRIMARY KEY,
                    seal_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    user_id TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')
        
        # Create indexes
        await self.db_connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_seals_document_id ON seals(document_id)
        ''')
        
        await self.db_connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_seals_type ON seals(seal_type)
        ''')
        
        await self.db_connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_seals_status ON seals(status)
        ''')
        
        await self.db_connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_seals_created_at ON seals(created_at)
        ''')
        
        await self.db_connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_seals_expires_at ON seals(expires_at)
        ''')
        
        if self.enable_audit:
            await self.db_connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_audit_seal_id ON seal_audit(seal_id)
            ''')
            
            await self.db_connection.execute('''
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON seal_audit(timestamp)
            ''')
        
        await self.db_connection.commit()
        logger.info("SQLite database initialized")
    
    async def store_seal(self, seal: AuthenticationSeal, user_id: Optional[str] = None) -> bool:
        """
        Store authentication seal
        
        Args:
            seal: Authentication seal to store
            user_id: User performing the operation
            
        Returns:
            True if successful, False otherwise
        """
        import time
        start_time = time.time()
        
        try:
            # Store in database
            await self.db_connection.execute('''
                INSERT OR REPLACE INTO seals (
                    seal_id, document_id, seal_type, seal_value, algorithm, status,
                    created_at, updated_at, expires_at, issuer, version,
                    certificate_thumbprint, key_id, verification_data, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                seal.seal_id,
                seal.document_id,
                seal.seal_type.value,
                seal.seal_value,
                seal.algorithm.value,
                seal.status.value,
                seal.created_at,
                seal.updated_at,
                seal.metadata.expires_at,
                seal.metadata.issuer,
                seal.metadata.version,
                seal.metadata.certificate_thumbprint,
                seal.metadata.key_id,
                json.dumps(seal.verification_data),
                json.dumps(asdict(seal.metadata))
            ))
            
            await self.db_connection.commit()
            
            # Update cache
            self._update_cache(seal)
            
            # Log audit event
            if self.enable_audit:
                await self._log_audit_event(
                    seal.seal_id,
                    seal.document_id,
                    "STORE",
                    user_id,
                    {"seal_type": seal.seal_type.value, "algorithm": seal.algorithm.value}
                )
            
            # Update metrics
            self.metrics['total_operations'] += 1
            self.metrics['store_operations'] += 1
            self._update_average_time(time.time() - start_time)
            
            logger.info(f"Seal stored successfully: {seal.seal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store seal {seal.seal_id}: {e}")
            return False
    
    async def retrieve_seal(self, seal_id: str, user_id: Optional[str] = None) -> Optional[AuthenticationSeal]:
        """
        Retrieve authentication seal by ID
        
        Args:
            seal_id: Seal identifier
            user_id: User performing the operation
            
        Returns:
            Authentication seal if found, None otherwise
        """
        import time
        start_time = time.time()
        
        try:
            # Check cache first
            if seal_id in self.seal_cache:
                self.metrics['cache_hits'] += 1
                seal = self.seal_cache[seal_id]
                
                # Log audit event
                if self.enable_audit:
                    await self._log_audit_event(
                        seal_id,
                        seal.document_id,
                        "RETRIEVE",
                        user_id,
                        {"source": "cache"}
                    )
                
                return seal
            
            self.metrics['cache_misses'] += 1
            
            # Retrieve from database
            cursor = await self.db_connection.execute('''
                SELECT * FROM seals WHERE seal_id = ?
            ''', (seal_id,))
            
            row = await cursor.fetchone()
            
            if row:
                seal = self._row_to_seal(row)
                
                # Update cache
                self._update_cache(seal)
                
                # Log audit event
                if self.enable_audit:
                    await self._log_audit_event(
                        seal_id,
                        seal.document_id,
                        "RETRIEVE",
                        user_id,
                        {"source": "database"}
                    )
                
                # Update metrics
                self.metrics['total_operations'] += 1
                self.metrics['retrieve_operations'] += 1
                self._update_average_time(time.time() - start_time)
                
                return seal
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve seal {seal_id}: {e}")
            return None
    
    async def search_seals(self, criteria: SealSearchCriteria, user_id: Optional[str] = None) -> SealSearchResult:
        """
        Search authentication seals
        
        Args:
            criteria: Search criteria
            user_id: User performing the operation
            
        Returns:
            Search result with matching seals
        """
        import time
        start_time = time.time()
        
        try:
            # Build query
            query, params = self._build_search_query(criteria)
            
            # Execute query
            cursor = await self.db_connection.execute(query, params)
            rows = await cursor.fetchall()
            
            # Convert rows to seals
            seals = [self._row_to_seal(row) for row in rows]
            
            # Get total count
            count_query = self._build_count_query(criteria)
            count_cursor = await self.db_connection.execute(count_query[0], count_query[1])
            total_count = (await count_cursor.fetchone())[0]
            
            # Create result
            result = SealSearchResult(
                seals=seals,
                total_count=total_count,
                page_size=criteria.limit,
                page_offset=criteria.offset,
                has_more=criteria.offset + len(seals) < total_count,
                search_time=time.time() - start_time
            )
            
            # Log audit event
            if self.enable_audit:
                await self._log_audit_event(
                    "SEARCH",
                    "",
                    "SEARCH",
                    user_id,
                    {"criteria": asdict(criteria), "results": len(seals)}
                )
            
            # Update metrics
            self.metrics['total_operations'] += 1
            self.metrics['search_operations'] += 1
            self._update_average_time(time.time() - start_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search seals: {e}")
            return SealSearchResult(
                seals=[],
                total_count=0,
                page_size=criteria.limit,
                page_offset=criteria.offset,
                has_more=False,
                search_time=time.time() - start_time
            )
    
    async def delete_seal(self, seal_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete authentication seal
        
        Args:
            seal_id: Seal identifier
            user_id: User performing the operation
            
        Returns:
            True if successful, False otherwise
        """
        import time
        start_time = time.time()
        
        try:
            # Get seal info for audit
            seal = await self.retrieve_seal(seal_id, user_id)
            if not seal:
                return False
            
            # Delete from database
            await self.db_connection.execute('''
                DELETE FROM seals WHERE seal_id = ?
            ''', (seal_id,))
            
            await self.db_connection.commit()
            
            # Remove from cache
            if seal_id in self.seal_cache:
                del self.seal_cache[seal_id]
            
            # Log audit event
            if self.enable_audit:
                await self._log_audit_event(
                    seal_id,
                    seal.document_id,
                    "DELETE",
                    user_id,
                    {"seal_type": seal.seal_type.value}
                )
            
            # Update metrics
            self.metrics['total_operations'] += 1
            self.metrics['delete_operations'] += 1
            self._update_average_time(time.time() - start_time)
            
            logger.info(f"Seal deleted successfully: {seal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete seal {seal_id}: {e}")
            return False
    
    async def update_seal_status(self, seal_id: str, new_status: SealStatus, user_id: Optional[str] = None) -> bool:
        """
        Update seal status
        
        Args:
            seal_id: Seal identifier
            new_status: New status
            user_id: User performing the operation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update in database
            await self.db_connection.execute('''
                UPDATE seals SET status = ?, updated_at = ? WHERE seal_id = ?
            ''', (new_status.value, datetime.utcnow(), seal_id))
            
            await self.db_connection.commit()
            
            # Update cache
            if seal_id in self.seal_cache:
                self.seal_cache[seal_id].status = new_status
                self.seal_cache[seal_id].updated_at = datetime.utcnow()
            
            # Log audit event
            if self.enable_audit:
                await self._log_audit_event(
                    seal_id,
                    "",
                    "UPDATE_STATUS",
                    user_id,
                    {"new_status": new_status.value}
                )
            
            logger.info(f"Seal status updated: {seal_id} -> {new_status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update seal status {seal_id}: {e}")
            return False
    
    async def get_seals_by_document(self, document_id: str, user_id: Optional[str] = None) -> List[AuthenticationSeal]:
        """Get all seals for a document"""
        criteria = SealSearchCriteria(document_id=document_id, limit=1000)
        result = await self.search_seals(criteria, user_id)
        return result.seals
    
    async def get_expired_seals(self, user_id: Optional[str] = None) -> List[AuthenticationSeal]:
        """Get all expired seals"""
        criteria = SealSearchCriteria(expires_before=datetime.utcnow(), limit=1000)
        result = await self.search_seals(criteria, user_id)
        return result.seals
    
    async def cleanup_expired_seals(self, user_id: Optional[str] = None) -> int:
        """Clean up expired seals"""
        try:
            # Get expired seals
            expired_seals = await self.get_expired_seals(user_id)
            
            # Delete expired seals
            deleted_count = 0
            for seal in expired_seals:
                if await self.delete_seal(seal.seal_id, user_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} expired seals")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired seals: {e}")
            return 0
    
    async def get_repository_stats(self) -> RepositoryStats:
        """Get repository statistics"""
        try:
            # Total seals
            cursor = await self.db_connection.execute('SELECT COUNT(*) FROM seals')
            total_seals = (await cursor.fetchone())[0]
            
            # Seals by type
            cursor = await self.db_connection.execute('''
                SELECT seal_type, COUNT(*) FROM seals GROUP BY seal_type
            ''')
            seals_by_type = dict(await cursor.fetchall())
            
            # Seals by status
            cursor = await self.db_connection.execute('''
                SELECT status, COUNT(*) FROM seals GROUP BY status
            ''')
            seals_by_status = dict(await cursor.fetchall())
            
            # Seals by algorithm
            cursor = await self.db_connection.execute('''
                SELECT algorithm, COUNT(*) FROM seals GROUP BY algorithm
            ''')
            seals_by_algorithm = dict(await cursor.fetchall())
            
            # Expired seals
            cursor = await self.db_connection.execute('''
                SELECT COUNT(*) FROM seals WHERE expires_at < ?
            ''', (datetime.utcnow(),))
            expired_seals = (await cursor.fetchone())[0]
            
            # Seals created today
            today = datetime.utcnow().date()
            cursor = await self.db_connection.execute('''
                SELECT COUNT(*) FROM seals WHERE DATE(created_at) = ?
            ''', (today,))
            seals_created_today = (await cursor.fetchone())[0]
            
            # Seals created this week
            week_ago = datetime.utcnow() - timedelta(days=7)
            cursor = await self.db_connection.execute('''
                SELECT COUNT(*) FROM seals WHERE created_at >= ?
            ''', (week_ago,))
            seals_created_this_week = (await cursor.fetchone())[0]
            
            # Seals created this month
            month_ago = datetime.utcnow() - timedelta(days=30)
            cursor = await self.db_connection.execute('''
                SELECT COUNT(*) FROM seals WHERE created_at >= ?
            ''', (month_ago,))
            seals_created_this_month = (await cursor.fetchone())[0]
            
            # Storage size
            storage_size = Path(self.database_path).stat().st_size if Path(self.database_path).exists() else 0
            
            return RepositoryStats(
                total_seals=total_seals,
                seals_by_type=seals_by_type,
                seals_by_status=seals_by_status,
                seals_by_algorithm=seals_by_algorithm,
                expired_seals=expired_seals,
                seals_created_today=seals_created_today,
                seals_created_this_week=seals_created_this_week,
                seals_created_this_month=seals_created_this_month,
                storage_size=storage_size
            )
            
        except Exception as e:
            logger.error(f"Failed to get repository stats: {e}")
            return RepositoryStats(
                total_seals=0,
                seals_by_type={},
                seals_by_status={},
                seals_by_algorithm={},
                expired_seals=0,
                seals_created_today=0,
                seals_created_this_week=0,
                seals_created_this_month=0,
                storage_size=0
            )
    
    def _build_search_query(self, criteria: SealSearchCriteria) -> Tuple[str, List[Any]]:
        """Build search query"""
        query = "SELECT * FROM seals WHERE 1=1"
        params = []
        
        if criteria.document_id:
            query += " AND document_id = ?"
            params.append(criteria.document_id)
        
        if criteria.seal_type:
            query += " AND seal_type = ?"
            params.append(criteria.seal_type.value)
        
        if criteria.algorithm:
            query += " AND algorithm = ?"
            params.append(criteria.algorithm.value)
        
        if criteria.status:
            query += " AND status = ?"
            params.append(criteria.status.value)
        
        if criteria.issuer:
            query += " AND issuer = ?"
            params.append(criteria.issuer)
        
        if criteria.created_after:
            query += " AND created_at >= ?"
            params.append(criteria.created_after)
        
        if criteria.created_before:
            query += " AND created_at <= ?"
            params.append(criteria.created_before)
        
        if criteria.expires_after:
            query += " AND expires_at >= ?"
            params.append(criteria.expires_after)
        
        if criteria.expires_before:
            query += " AND expires_at <= ?"
            params.append(criteria.expires_before)
        
        # Add ordering
        query += f" ORDER BY {criteria.sort_by} {criteria.sort_order}"
        
        # Add pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([criteria.limit, criteria.offset])
        
        return query, params
    
    def _build_count_query(self, criteria: SealSearchCriteria) -> Tuple[str, List[Any]]:
        """Build count query"""
        query = "SELECT COUNT(*) FROM seals WHERE 1=1"
        params = []
        
        if criteria.document_id:
            query += " AND document_id = ?"
            params.append(criteria.document_id)
        
        if criteria.seal_type:
            query += " AND seal_type = ?"
            params.append(criteria.seal_type.value)
        
        if criteria.algorithm:
            query += " AND algorithm = ?"
            params.append(criteria.algorithm.value)
        
        if criteria.status:
            query += " AND status = ?"
            params.append(criteria.status.value)
        
        if criteria.issuer:
            query += " AND issuer = ?"
            params.append(criteria.issuer)
        
        if criteria.created_after:
            query += " AND created_at >= ?"
            params.append(criteria.created_after)
        
        if criteria.created_before:
            query += " AND created_at <= ?"
            params.append(criteria.created_before)
        
        if criteria.expires_after:
            query += " AND expires_at >= ?"
            params.append(criteria.expires_after)
        
        if criteria.expires_before:
            query += " AND expires_at <= ?"
            params.append(criteria.expires_before)
        
        return query, params
    
    def _row_to_seal(self, row) -> AuthenticationSeal:
        """Convert database row to authentication seal"""
        metadata = SealMetadata(
            seal_id=row[0],
            seal_type=SealType(row[2]),
            algorithm=SealAlgorithm(row[4]),
            created_at=datetime.fromisoformat(row[6]),
            expires_at=datetime.fromisoformat(row[8]) if row[8] else None,
            issuer=row[9],
            version=row[10],
            certificate_thumbprint=row[11],
            key_id=row[12],
            additional_data=json.loads(row[14]) if row[14] else {}
        )
        
        return AuthenticationSeal(
            seal_id=row[0],
            document_id=row[1],
            seal_type=SealType(row[2]),
            seal_value=row[3],
            algorithm=SealAlgorithm(row[4]),
            status=SealStatus(row[5]),
            metadata=metadata,
            verification_data=json.loads(row[13]) if row[13] else {},
            created_at=datetime.fromisoformat(row[6]),
            updated_at=datetime.fromisoformat(row[7])
        )
    
    def _update_cache(self, seal: AuthenticationSeal):
        """Update seal cache"""
        # Remove oldest entries if cache is full
        if len(self.seal_cache) >= self.cache_size_limit:
            # Remove oldest entry
            oldest_key = min(self.seal_cache.keys(), key=lambda k: self.seal_cache[k].created_at)
            del self.seal_cache[oldest_key]
        
        self.seal_cache[seal.seal_id] = seal
    
    async def _log_audit_event(self, seal_id: str, document_id: str, operation: str, 
                             user_id: Optional[str], details: Dict[str, Any]):
        """Log audit event"""
        if not self.enable_audit:
            return
        
        try:
            event = SealAuditEvent(
                event_id=str(uuid.uuid4()),
                seal_id=seal_id,
                document_id=document_id,
                operation=operation,
                user_id=user_id,
                details=details
            )
            
            await self.db_connection.execute('''
                INSERT INTO seal_audit (
                    event_id, seal_id, document_id, operation, user_id,
                    timestamp, details, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.seal_id,
                event.document_id,
                event.operation,
                event.user_id,
                event.timestamp,
                json.dumps(event.details),
                event.ip_address,
                event.user_agent
            ))
            
            await self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def _update_average_time(self, operation_time: float):
        """Update average operation time"""
        total_ops = self.metrics['total_operations']
        current_avg = self.metrics['average_operation_time']
        self.metrics['average_operation_time'] = (
            (current_avg * (total_ops - 1) + operation_time) / total_ops
        )
    
    async def _periodic_cleanup(self):
        """Periodic cleanup task"""
        while True:
            try:
                await asyncio.sleep(self.backup_interval)
                await self.cleanup_expired_seals()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _periodic_backup(self):
        """Periodic backup task"""
        while True:
            try:
                await asyncio.sleep(self.backup_interval)
                await self._backup_database()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic backup: {e}")
    
    async def _backup_database(self):
        """Backup database"""
        try:
            backup_path = f"{self.database_path}.backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # For SQLite, we can use the backup API
            if self.storage_backend == StorageBackend.SQLITE:
                backup_conn = await aiosqlite.connect(backup_path)
                await self.db_connection.backup(backup_conn)
                await backup_conn.close()
            
            logger.info(f"Database backed up to {backup_path}")
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get repository metrics"""
        return {
            **self.metrics,
            'cache_size': len(self.seal_cache),
            'cache_hit_rate': (
                self.metrics['cache_hits'] / 
                max(self.metrics['cache_hits'] + self.metrics['cache_misses'], 1)
            ) * 100,
            'storage_backend': self.storage_backend.value,
            'database_path': self.database_path
        }


# Factory functions for easy setup
def create_seal_repository(storage_backend: StorageBackend = StorageBackend.SQLITE,
                         database_path: str = "seal_repository.db",
                         enable_audit: bool = True) -> SealRepository:
    """Create seal repository instance"""
    return SealRepository(storage_backend, database_path, enable_audit)


def create_search_criteria(document_id: Optional[str] = None,
                         seal_type: Optional[SealType] = None,
                         status: Optional[SealStatus] = None,
                         limit: int = 100) -> SealSearchCriteria:
    """Create search criteria"""
    return SealSearchCriteria(
        document_id=document_id,
        seal_type=seal_type,
        status=status,
        limit=limit
    )


async def create_and_start_repository(storage_backend: StorageBackend = StorageBackend.SQLITE,
                                    database_path: str = "seal_repository.db") -> SealRepository:
    """Create and start seal repository"""
    repository = create_seal_repository(storage_backend, database_path)
    await repository.start()
    return repository