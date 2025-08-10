"""
Storage Orchestrator - Core Platform Infrastructure
Comprehensive storage management system for the TaxPoynt platform.
Orchestrates storage systems, policies, backup, and data lifecycle management.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class StorageType(Enum):
    DATABASE = "database"
    OBJECT_STORAGE = "object_storage"
    FILE_STORAGE = "file_storage"
    CACHE = "cache"
    QUEUE = "queue"
    LOG_STORAGE = "log_storage"
    BACKUP_STORAGE = "backup_storage"
    ARCHIVE_STORAGE = "archive_storage"

class StorageClass(Enum):
    HOT = "hot"           # Frequent access, high performance
    WARM = "warm"         # Infrequent access, medium performance
    COLD = "cold"         # Rare access, low cost
    ARCHIVE = "archive"   # Long-term retention
    GLACIER = "glacier"   # Deep archive

class StorageStatus(Enum):
    AVAILABLE = "available"
    PROVISIONING = "provisioning"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAILED = "failed"
    RETIRING = "retiring"

class ReplicationStrategy(Enum):
    NONE = "none"
    ASYNC = "async"
    SYNC = "sync"
    MULTI_REGION = "multi_region"
    CROSS_ZONE = "cross_zone"

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"

@dataclass
class StorageQuota:
    storage_type: StorageType
    limit_gb: float
    used_gb: float = 0.0
    reserved_gb: float = 0.0
    soft_limit_gb: Optional[float] = None
    burst_limit_gb: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StorageVolume:
    id: str
    name: str
    storage_type: StorageType
    storage_class: StorageClass
    size_gb: float
    tenant_id: str
    service_id: str
    mount_path: Optional[str] = None
    encryption_enabled: bool = True
    compression_enabled: bool = False
    replication_strategy: ReplicationStrategy = ReplicationStrategy.ASYNC
    status: StorageStatus = StorageStatus.PROVISIONING
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_access: Optional[datetime] = None

@dataclass
class BackupPolicy:
    id: str
    name: str
    storage_types: List[StorageType]
    backup_type: BackupType
    schedule_cron: str
    retention_days: int
    encryption_enabled: bool = True
    compression_enabled: bool = True
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BackupJob:
    id: str
    policy_id: str
    volume_id: str
    backup_type: BackupType
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    size_gb: Optional[float] = None
    backup_location: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LifecycleRule:
    id: str
    name: str
    storage_types: List[StorageType]
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StorageMetrics:
    timestamp: datetime
    volume_id: str
    storage_type: StorageType
    used_gb: float
    available_gb: float
    iops: int
    throughput_mbps: float
    latency_ms: float
    error_rate_percent: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class StorageProvider(ABC):
    @abstractmethod
    async def create_volume(self, volume: StorageVolume) -> bool:
        pass
    
    @abstractmethod
    async def delete_volume(self, volume_id: str) -> bool:
        pass
    
    @abstractmethod
    async def resize_volume(self, volume_id: str, new_size_gb: float) -> bool:
        pass
    
    @abstractmethod
    async def create_backup(self, volume_id: str, backup_job: BackupJob) -> bool:
        pass
    
    @abstractmethod
    async def restore_backup(self, backup_id: str, target_volume_id: str) -> bool:
        pass
    
    @abstractmethod
    async def get_storage_metrics(self, volume_id: str) -> Optional[StorageMetrics]:
        pass

class DatabaseStorageProvider(StorageProvider):
    async def create_volume(self, volume: StorageVolume) -> bool:
        try:
            logger.info(f"Creating database volume: {volume.name} ({volume.size_gb}GB)")
            # Database-specific volume creation
            # This would interact with database providers (PostgreSQL, Redis, etc.)
            return True
        except Exception as e:
            logger.error(f"Failed to create database volume: {e}")
            return False
    
    async def delete_volume(self, volume_id: str) -> bool:
        try:
            logger.info(f"Deleting database volume: {volume_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete database volume: {e}")
            return False
    
    async def resize_volume(self, volume_id: str, new_size_gb: float) -> bool:
        try:
            logger.info(f"Resizing database volume {volume_id} to {new_size_gb}GB")
            return True
        except Exception as e:
            logger.error(f"Failed to resize database volume: {e}")
            return False
    
    async def create_backup(self, volume_id: str, backup_job: BackupJob) -> bool:
        try:
            logger.info(f"Creating database backup for volume: {volume_id}")
            backup_job.backup_location = f"/backups/db/{volume_id}/{backup_job.id}.sql"
            backup_job.size_gb = 2.5  # Simulated
            return True
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return False
    
    async def restore_backup(self, backup_id: str, target_volume_id: str) -> bool:
        try:
            logger.info(f"Restoring database backup {backup_id} to volume {target_volume_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore database backup: {e}")
            return False
    
    async def get_storage_metrics(self, volume_id: str) -> Optional[StorageMetrics]:
        try:
            # Simulate database storage metrics
            return StorageMetrics(
                timestamp=datetime.utcnow(),
                volume_id=volume_id,
                storage_type=StorageType.DATABASE,
                used_gb=15.5,
                available_gb=84.5,
                iops=1200,
                throughput_mbps=150.0,
                latency_ms=2.5,
                error_rate_percent=0.1
            )
        except Exception as e:
            logger.error(f"Failed to get database storage metrics: {e}")
            return None

class ObjectStorageProvider(StorageProvider):
    async def create_volume(self, volume: StorageVolume) -> bool:
        try:
            logger.info(f"Creating object storage volume: {volume.name}")
            # Object storage bucket/container creation
            return True
        except Exception as e:
            logger.error(f"Failed to create object storage volume: {e}")
            return False
    
    async def delete_volume(self, volume_id: str) -> bool:
        try:
            logger.info(f"Deleting object storage volume: {volume_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete object storage volume: {e}")
            return False
    
    async def resize_volume(self, volume_id: str, new_size_gb: float) -> bool:
        try:
            logger.info(f"Resizing object storage volume {volume_id} to {new_size_gb}GB")
            # Object storage typically doesn't need explicit resizing
            return True
        except Exception as e:
            logger.error(f"Failed to resize object storage volume: {e}")
            return False
    
    async def create_backup(self, volume_id: str, backup_job: BackupJob) -> bool:
        try:
            logger.info(f"Creating object storage backup for volume: {volume_id}")
            backup_job.backup_location = f"s3://backups/objects/{volume_id}/{backup_job.id}.tar.gz"
            backup_job.size_gb = 10.2  # Simulated
            return True
        except Exception as e:
            logger.error(f"Failed to create object storage backup: {e}")
            return False
    
    async def restore_backup(self, backup_id: str, target_volume_id: str) -> bool:
        try:
            logger.info(f"Restoring object storage backup {backup_id} to volume {target_volume_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore object storage backup: {e}")
            return False
    
    async def get_storage_metrics(self, volume_id: str) -> Optional[StorageMetrics]:
        try:
            # Simulate object storage metrics
            return StorageMetrics(
                timestamp=datetime.utcnow(),
                volume_id=volume_id,
                storage_type=StorageType.OBJECT_STORAGE,
                used_gb=45.2,
                available_gb=954.8,
                iops=500,
                throughput_mbps=200.0,
                latency_ms=5.0,
                error_rate_percent=0.05
            )
        except Exception as e:
            logger.error(f"Failed to get object storage metrics: {e}")
            return None

class FileStorageProvider(StorageProvider):
    async def create_volume(self, volume: StorageVolume) -> bool:
        try:
            logger.info(f"Creating file storage volume: {volume.name}")
            # File system volume creation
            return True
        except Exception as e:
            logger.error(f"Failed to create file storage volume: {e}")
            return False
    
    async def delete_volume(self, volume_id: str) -> bool:
        try:
            logger.info(f"Deleting file storage volume: {volume_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file storage volume: {e}")
            return False
    
    async def resize_volume(self, volume_id: str, new_size_gb: float) -> bool:
        try:
            logger.info(f"Resizing file storage volume {volume_id} to {new_size_gb}GB")
            return True
        except Exception as e:
            logger.error(f"Failed to resize file storage volume: {e}")
            return False
    
    async def create_backup(self, volume_id: str, backup_job: BackupJob) -> bool:
        try:
            logger.info(f"Creating file storage backup for volume: {volume_id}")
            backup_job.backup_location = f"/backups/files/{volume_id}/{backup_job.id}.tar.gz"
            backup_job.size_gb = 5.8  # Simulated
            return True
        except Exception as e:
            logger.error(f"Failed to create file storage backup: {e}")
            return False
    
    async def restore_backup(self, backup_id: str, target_volume_id: str) -> bool:
        try:
            logger.info(f"Restoring file storage backup {backup_id} to volume {target_volume_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore file storage backup: {e}")
            return False
    
    async def get_storage_metrics(self, volume_id: str) -> Optional[StorageMetrics]:
        try:
            # Simulate file storage metrics
            return StorageMetrics(
                timestamp=datetime.utcnow(),
                volume_id=volume_id,
                storage_type=StorageType.FILE_STORAGE,
                used_gb=25.3,
                available_gb=74.7,
                iops=800,
                throughput_mbps=100.0,
                latency_ms=1.5,
                error_rate_percent=0.02
            )
        except Exception as e:
            logger.error(f"Failed to get file storage metrics: {e}")
            return None

class StorageOrchestrator:
    def __init__(self):
        self.volumes: Dict[str, StorageVolume] = {}
        self.backup_policies: Dict[str, BackupPolicy] = {}
        self.backup_jobs: Dict[str, BackupJob] = {}
        self.lifecycle_rules: Dict[str, LifecycleRule] = {}
        self.providers: Dict[StorageType, StorageProvider] = {}
        self.quotas: Dict[str, Dict[StorageType, StorageQuota]] = {}
        self.metrics_history: List[StorageMetrics] = []
        
        # Initialize providers
        self._initialize_providers()
        
        # Load default policies
        self._load_default_policies()
    
    def _initialize_providers(self):
        """Initialize storage providers"""
        self.providers = {
            StorageType.DATABASE: DatabaseStorageProvider(),
            StorageType.OBJECT_STORAGE: ObjectStorageProvider(),
            StorageType.FILE_STORAGE: FileStorageProvider(),
            StorageType.CACHE: DatabaseStorageProvider(),  # Redis/Memcached
            StorageType.LOG_STORAGE: ObjectStorageProvider(),
            StorageType.BACKUP_STORAGE: ObjectStorageProvider(),
            StorageType.ARCHIVE_STORAGE: ObjectStorageProvider()
        }
    
    def _load_default_policies(self):
        """Load default backup policies and lifecycle rules"""
        default_backup_policies = [
            BackupPolicy(
                id="database_daily_backup",
                name="Daily Database Backup",
                storage_types=[StorageType.DATABASE],
                backup_type=BackupType.INCREMENTAL,
                schedule_cron="0 2 * * *",  # Daily at 2 AM
                retention_days=30
            ),
            BackupPolicy(
                id="database_weekly_full_backup",
                name="Weekly Full Database Backup",
                storage_types=[StorageType.DATABASE],
                backup_type=BackupType.FULL,
                schedule_cron="0 1 * * 0",  # Weekly on Sunday at 1 AM
                retention_days=90
            ),
            BackupPolicy(
                id="file_storage_backup",
                name="File Storage Backup",
                storage_types=[StorageType.FILE_STORAGE],
                backup_type=BackupType.SNAPSHOT,
                schedule_cron="0 3 * * *",  # Daily at 3 AM
                retention_days=7
            )
        ]
        
        for policy in default_backup_policies:
            self.backup_policies[policy.id] = policy
        
        # Default lifecycle rules
        default_lifecycle_rules = [
            LifecycleRule(
                id="hot_to_warm_transition",
                name="Hot to Warm Storage Transition",
                storage_types=[StorageType.OBJECT_STORAGE, StorageType.FILE_STORAGE],
                conditions={
                    "age_days": 30,
                    "access_frequency": "low"
                },
                actions=[
                    {"action": "transition", "storage_class": "warm"}
                ]
            ),
            LifecycleRule(
                id="warm_to_cold_transition",
                name="Warm to Cold Storage Transition",
                storage_types=[StorageType.OBJECT_STORAGE],
                conditions={
                    "age_days": 90,
                    "storage_class": "warm"
                },
                actions=[
                    {"action": "transition", "storage_class": "cold"}
                ]
            ),
            LifecycleRule(
                id="archive_old_logs",
                name="Archive Old Log Files",
                storage_types=[StorageType.LOG_STORAGE],
                conditions={
                    "age_days": 365
                },
                actions=[
                    {"action": "transition", "storage_class": "archive"}
                ]
            )
        ]
        
        for rule in default_lifecycle_rules:
            self.lifecycle_rules[rule.id] = rule
    
    async def create_volume(self, volume_config: Dict[str, Any]) -> Optional[StorageVolume]:
        """Create a new storage volume"""
        try:
            volume = StorageVolume(
                id=volume_config.get('id', f"vol_{int(time.time())}"),
                name=volume_config['name'],
                storage_type=StorageType(volume_config['storage_type']),
                storage_class=StorageClass(volume_config.get('storage_class', 'hot')),
                size_gb=volume_config['size_gb'],
                tenant_id=volume_config['tenant_id'],
                service_id=volume_config['service_id'],
                mount_path=volume_config.get('mount_path'),
                encryption_enabled=volume_config.get('encryption_enabled', True),
                compression_enabled=volume_config.get('compression_enabled', False),
                replication_strategy=ReplicationStrategy(volume_config.get('replication_strategy', 'async')),
                tags=volume_config.get('tags', {}),
                metadata=volume_config.get('metadata', {})
            )
            
            # Check quota
            if not await self._check_storage_quota(volume.tenant_id, volume.storage_type, volume.size_gb):
                logger.warning(f"Storage quota exceeded for tenant {volume.tenant_id}")
                return None
            
            # Create volume using appropriate provider
            if volume.storage_type in self.providers:
                provider = self.providers[volume.storage_type]
                if await provider.create_volume(volume):
                    volume.status = StorageStatus.AVAILABLE
                    self.volumes[volume.id] = volume
                    
                    # Update quota usage
                    await self._update_quota_usage(volume.tenant_id, volume.storage_type, volume.size_gb)
                    
                    logger.info(f"Created storage volume: {volume.id}")
                    return volume
                else:
                    logger.error(f"Failed to create volume with provider: {volume.storage_type}")
                    return None
            else:
                logger.error(f"No provider for storage type: {volume.storage_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create storage volume: {e}")
            return None
    
    async def delete_volume(self, volume_id: str) -> bool:
        """Delete a storage volume"""
        try:
            if volume_id not in self.volumes:
                logger.warning(f"Volume not found: {volume_id}")
                return False
            
            volume = self.volumes[volume_id]
            
            # Delete using appropriate provider
            if volume.storage_type in self.providers:
                provider = self.providers[volume.storage_type]
                if await provider.delete_volume(volume_id):
                    # Update quota usage
                    await self._update_quota_usage(volume.tenant_id, volume.storage_type, -volume.size_gb)
                    
                    # Remove volume
                    del self.volumes[volume_id]
                    
                    logger.info(f"Deleted storage volume: {volume_id}")
                    return True
                else:
                    logger.error(f"Failed to delete volume with provider: {volume.storage_type}")
                    return False
            else:
                logger.error(f"No provider for storage type: {volume.storage_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete storage volume: {e}")
            return False
    
    async def resize_volume(self, volume_id: str, new_size_gb: float) -> bool:
        """Resize a storage volume"""
        try:
            if volume_id not in self.volumes:
                logger.warning(f"Volume not found: {volume_id}")
                return False
            
            volume = self.volumes[volume_id]
            old_size = volume.size_gb
            size_difference = new_size_gb - old_size
            
            # Check quota for size increase
            if size_difference > 0:
                if not await self._check_storage_quota(volume.tenant_id, volume.storage_type, size_difference):
                    logger.warning(f"Storage quota exceeded for resize: {volume_id}")
                    return False
            
            # Resize using appropriate provider
            if volume.storage_type in self.providers:
                provider = self.providers[volume.storage_type]
                if await provider.resize_volume(volume_id, new_size_gb):
                    # Update volume size
                    volume.size_gb = new_size_gb
                    
                    # Update quota usage
                    await self._update_quota_usage(volume.tenant_id, volume.storage_type, size_difference)
                    
                    logger.info(f"Resized storage volume {volume_id}: {old_size}GB -> {new_size_gb}GB")
                    return True
                else:
                    logger.error(f"Failed to resize volume with provider: {volume.storage_type}")
                    return False
            else:
                logger.error(f"No provider for storage type: {volume.storage_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to resize storage volume: {e}")
            return False
    
    async def _check_storage_quota(self, tenant_id: str, storage_type: StorageType, size_gb: float) -> bool:
        """Check if storage allocation would exceed quota"""
        try:
            if tenant_id not in self.quotas:
                await self._initialize_tenant_quotas(tenant_id)
            
            tenant_quotas = self.quotas.get(tenant_id, {})
            if storage_type in tenant_quotas:
                quota = tenant_quotas[storage_type]
                if quota.used_gb + size_gb > quota.limit_gb:
                    # Check if burst is allowed
                    if quota.burst_limit_gb and quota.used_gb + size_gb <= quota.burst_limit_gb:
                        return True
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to check storage quota: {e}")
            return False
    
    async def _initialize_tenant_quotas(self, tenant_id: str):
        """Initialize storage quotas for a tenant"""
        try:
            # Default quotas based on tier (in real implementation, query tenant service)
            default_quotas = {
                StorageType.DATABASE: StorageQuota(StorageType.DATABASE, 100.0),  # 100GB
                StorageType.OBJECT_STORAGE: StorageQuota(StorageType.OBJECT_STORAGE, 1000.0),  # 1TB
                StorageType.FILE_STORAGE: StorageQuota(StorageType.FILE_STORAGE, 500.0),  # 500GB
                StorageType.CACHE: StorageQuota(StorageType.CACHE, 50.0),  # 50GB
                StorageType.LOG_STORAGE: StorageQuota(StorageType.LOG_STORAGE, 200.0),  # 200GB
                StorageType.BACKUP_STORAGE: StorageQuota(StorageType.BACKUP_STORAGE, 2000.0),  # 2TB
            }
            
            self.quotas[tenant_id] = default_quotas
        except Exception as e:
            logger.error(f"Failed to initialize tenant quotas: {e}")
    
    async def _update_quota_usage(self, tenant_id: str, storage_type: StorageType, size_gb: float):
        """Update quota usage for a tenant"""
        try:
            if tenant_id not in self.quotas:
                await self._initialize_tenant_quotas(tenant_id)
            
            if tenant_id in self.quotas and storage_type in self.quotas[tenant_id]:
                quota = self.quotas[tenant_id][storage_type]
                quota.used_gb = max(0.0, quota.used_gb + size_gb)
                
        except Exception as e:
            logger.error(f"Failed to update quota usage: {e}")
    
    async def create_backup_job(self, volume_id: str, policy_id: str) -> Optional[BackupJob]:
        """Create a backup job for a volume"""
        try:
            if volume_id not in self.volumes:
                logger.warning(f"Volume not found: {volume_id}")
                return None
            
            if policy_id not in self.backup_policies:
                logger.warning(f"Backup policy not found: {policy_id}")
                return None
            
            volume = self.volumes[volume_id]
            policy = self.backup_policies[policy_id]
            
            backup_job = BackupJob(
                id=f"backup_{int(time.time())}_{volume_id}",
                policy_id=policy_id,
                volume_id=volume_id,
                backup_type=policy.backup_type,
                started_at=datetime.utcnow()
            )
            
            # Execute backup using appropriate provider
            if volume.storage_type in self.providers:
                provider = self.providers[volume.storage_type]
                backup_job.status = "running"
                
                if await provider.create_backup(volume_id, backup_job):
                    backup_job.status = "completed"
                    backup_job.completed_at = datetime.utcnow()
                else:
                    backup_job.status = "failed"
                    backup_job.error_message = "Provider backup creation failed"
                
                self.backup_jobs[backup_job.id] = backup_job
                logger.info(f"Created backup job: {backup_job.id} (status: {backup_job.status})")
                return backup_job
            else:
                logger.error(f"No provider for storage type: {volume.storage_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create backup job: {e}")
            return None
    
    async def restore_from_backup(self, backup_id: str, target_volume_id: str) -> bool:
        """Restore a volume from backup"""
        try:
            if backup_id not in self.backup_jobs:
                logger.warning(f"Backup job not found: {backup_id}")
                return False
            
            if target_volume_id not in self.volumes:
                logger.warning(f"Target volume not found: {target_volume_id}")
                return False
            
            backup_job = self.backup_jobs[backup_id]
            target_volume = self.volumes[target_volume_id]
            
            # Restore using appropriate provider
            if target_volume.storage_type in self.providers:
                provider = self.providers[target_volume.storage_type]
                success = await provider.restore_backup(backup_id, target_volume_id)
                
                if success:
                    logger.info(f"Restored backup {backup_id} to volume {target_volume_id}")
                else:
                    logger.error(f"Failed to restore backup {backup_id}")
                
                return success
            else:
                logger.error(f"No provider for storage type: {target_volume.storage_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False
    
    async def apply_lifecycle_rules(self) -> Dict[str, Any]:
        """Apply lifecycle rules to volumes"""
        try:
            results = {
                'processed_volumes': 0,
                'applied_rules': [],
                'transitions': []
            }
            
            for volume_id, volume in self.volumes.items():
                for rule_id, rule in self.lifecycle_rules.items():
                    if not rule.enabled or volume.storage_type not in rule.storage_types:
                        continue
                    
                    # Check conditions
                    if await self._evaluate_lifecycle_conditions(volume, rule.conditions):
                        # Apply actions
                        for action in rule.actions:
                            if action['action'] == 'transition':
                                new_storage_class = StorageClass(action['storage_class'])
                                if volume.storage_class != new_storage_class:
                                    volume.storage_class = new_storage_class
                                    results['transitions'].append({
                                        'volume_id': volume_id,
                                        'rule_id': rule_id,
                                        'new_storage_class': new_storage_class.value
                                    })
                                    logger.info(f"Applied lifecycle transition: {volume_id} -> {new_storage_class.value}")
                        
                        results['applied_rules'].append(rule_id)
                
                results['processed_volumes'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to apply lifecycle rules: {e}")
            return {}
    
    async def _evaluate_lifecycle_conditions(self, volume: StorageVolume, conditions: Dict[str, Any]) -> bool:
        """Evaluate lifecycle rule conditions for a volume"""
        try:
            # Check age condition
            if 'age_days' in conditions:
                age_days = (datetime.utcnow() - volume.created_at).days
                if age_days < conditions['age_days']:
                    return False
            
            # Check storage class condition
            if 'storage_class' in conditions:
                required_class = StorageClass(conditions['storage_class'])
                if volume.storage_class != required_class:
                    return False
            
            # Check access frequency (simulated)
            if 'access_frequency' in conditions:
                # In real implementation, this would check actual access patterns
                # For now, simulate based on last_access
                if volume.last_access:
                    days_since_access = (datetime.utcnow() - volume.last_access).days
                    if conditions['access_frequency'] == 'low' and days_since_access < 30:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to evaluate lifecycle conditions: {e}")
            return False
    
    async def get_storage_utilization(self) -> Dict[str, Any]:
        """Get storage utilization across all volumes"""
        try:
            utilization = {
                'total_volumes': len(self.volumes),
                'total_size_gb': sum(vol.size_gb for vol in self.volumes.values()),
                'by_storage_type': {},
                'by_storage_class': {},
                'by_tenant': {}
            }
            
            # Group by storage type
            for storage_type in StorageType:
                type_volumes = [vol for vol in self.volumes.values() if vol.storage_type == storage_type]
                utilization['by_storage_type'][storage_type.value] = {
                    'count': len(type_volumes),
                    'total_size_gb': sum(vol.size_gb for vol in type_volumes),
                    'average_size_gb': sum(vol.size_gb for vol in type_volumes) / len(type_volumes) if type_volumes else 0
                }
            
            # Group by storage class
            for storage_class in StorageClass:
                class_volumes = [vol for vol in self.volumes.values() if vol.storage_class == storage_class]
                utilization['by_storage_class'][storage_class.value] = {
                    'count': len(class_volumes),
                    'total_size_gb': sum(vol.size_gb for vol in class_volumes)
                }
            
            # Group by tenant
            tenant_usage = {}
            for volume in self.volumes.values():
                if volume.tenant_id not in tenant_usage:
                    tenant_usage[volume.tenant_id] = {
                        'volume_count': 0,
                        'total_size_gb': 0.0,
                        'by_storage_type': {}
                    }
                
                tenant_usage[volume.tenant_id]['volume_count'] += 1
                tenant_usage[volume.tenant_id]['total_size_gb'] += volume.size_gb
                
                storage_type = volume.storage_type.value
                if storage_type not in tenant_usage[volume.tenant_id]['by_storage_type']:
                    tenant_usage[volume.tenant_id]['by_storage_type'][storage_type] = 0.0
                tenant_usage[volume.tenant_id]['by_storage_type'][storage_type] += volume.size_gb
            
            utilization['by_tenant'] = tenant_usage
            
            return utilization
            
        except Exception as e:
            logger.error(f"Failed to get storage utilization: {e}")
            return {}
    
    async def get_tenant_storage_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get storage usage for a specific tenant"""
        try:
            tenant_volumes = [vol for vol in self.volumes.values() if vol.tenant_id == tenant_id]
            
            usage = {
                'tenant_id': tenant_id,
                'total_volumes': len(tenant_volumes),
                'total_size_gb': sum(vol.size_gb for vol in tenant_volumes),
                'volumes_by_type': {},
                'quotas': {}
            }
            
            # Group volumes by type
            for volume in tenant_volumes:
                storage_type = volume.storage_type.value
                if storage_type not in usage['volumes_by_type']:
                    usage['volumes_by_type'][storage_type] = {
                        'count': 0,
                        'total_size_gb': 0.0,
                        'volumes': []
                    }
                
                usage['volumes_by_type'][storage_type]['count'] += 1
                usage['volumes_by_type'][storage_type]['total_size_gb'] += volume.size_gb
                usage['volumes_by_type'][storage_type]['volumes'].append({
                    'id': volume.id,
                    'name': volume.name,
                    'size_gb': volume.size_gb,
                    'storage_class': volume.storage_class.value,
                    'status': volume.status.value
                })
            
            # Add quota information
            if tenant_id in self.quotas:
                for storage_type, quota in self.quotas[tenant_id].items():
                    usage['quotas'][storage_type.value] = {
                        'limit_gb': quota.limit_gb,
                        'used_gb': quota.used_gb,
                        'available_gb': quota.limit_gb - quota.used_gb,
                        'utilization_percent': (quota.used_gb / quota.limit_gb * 100) if quota.limit_gb > 0 else 0
                    }
            
            return usage
            
        except Exception as e:
            logger.error(f"Failed to get tenant storage usage: {e}")
            return {}
    
    async def start_monitoring(self, interval: int = 300):
        """Start continuous storage monitoring"""
        try:
            logger.info("Starting storage monitoring")
            
            while True:
                # Collect metrics from all volumes
                for volume_id in self.volumes:
                    volume = self.volumes[volume_id]
                    if volume.storage_type in self.providers:
                        provider = self.providers[volume.storage_type]
                        try:
                            metrics = await provider.get_storage_metrics(volume_id)
                            if metrics:
                                self.metrics_history.append(metrics)
                                
                                # Update last access time for volumes with activity
                                if metrics.iops > 0:
                                    volume.last_access = datetime.utcnow()
                        except Exception as e:
                            logger.error(f"Failed to collect metrics for volume {volume_id}: {e}")
                
                # Keep only last 1000 metrics
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Apply lifecycle rules
                await self.apply_lifecycle_rules()
                
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error(f"Storage monitoring failed: {e}")
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage system statistics"""
        try:
            return {
                'total_volumes': len(self.volumes),
                'volumes_by_status': {
                    status.value: len([vol for vol in self.volumes.values() if vol.status == status])
                    for status in StorageStatus
                },
                'volumes_by_type': {
                    storage_type.value: len([vol for vol in self.volumes.values() if vol.storage_type == storage_type])
                    for storage_type in StorageType
                },
                'total_backup_policies': len(self.backup_policies),
                'active_backup_policies': len([p for p in self.backup_policies.values() if p.enabled]),
                'total_backup_jobs': len(self.backup_jobs),
                'successful_backups': len([j for j in self.backup_jobs.values() if j.status == "completed"]),
                'failed_backups': len([j for j in self.backup_jobs.values() if j.status == "failed"]),
                'total_lifecycle_rules': len(self.lifecycle_rules),
                'active_lifecycle_rules': len([r for r in self.lifecycle_rules.values() if r.enabled]),
                'metrics_collected': len(self.metrics_history)
            }
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {}

# Global storage orchestrator instance
storage_orchestrator = StorageOrchestrator()

async def initialize_storage_orchestrator():
    """Initialize the storage orchestrator"""
    try:
        logger.info("Storage orchestrator initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize storage orchestrator: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_storage_orchestrator()
        
        # Example usage
        # Create database volume
        volume_config = {
            'name': 'einvoice_database',
            'storage_type': 'database',
            'storage_class': 'hot',
            'size_gb': 50.0,
            'tenant_id': 'tenant_001',
            'service_id': 'einvoice_service',
            'encryption_enabled': True
        }
        
        volume = await storage_orchestrator.create_volume(volume_config)
        if volume:
            print(f"Created volume: {volume.id}")
            
            # Create backup
            backup = await storage_orchestrator.create_backup_job(volume.id, "database_daily_backup")
            if backup:
                print(f"Created backup: {backup.id}")
            
            # Get utilization
            utilization = await storage_orchestrator.get_storage_utilization()
            print(f"Storage utilization: {json.dumps(utilization, indent=2)}")
            
            # Get tenant usage
            usage = await storage_orchestrator.get_tenant_storage_usage("tenant_001")
            print(f"Tenant usage: {json.dumps(usage, indent=2)}")
    
    asyncio.run(main())