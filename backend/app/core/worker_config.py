"""
Celery worker configuration and management for TaxPoynt eInvoice.

This module provides worker process configuration with:
- Specialized workers for different queue types
- Auto-scaling based on queue depth
- Resource management and monitoring
- Development and production configurations
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WorkerConfig:
    """Configuration for a Celery worker process."""
    name: str
    queues: List[str]
    concurrency: int
    prefetch_multiplier: int
    max_tasks_per_child: Optional[int] = 1000
    pool_type: str = "prefork"  # prefork, gevent, eventlet, solo
    optimization: str = "speed"  # speed, fair
    time_limit: int = 300  # 5 minutes
    soft_time_limit: int = 240  # 4 minutes
    log_level: str = "INFO"
    autoscale: Optional[tuple] = None  # (max, min) concurrency


class WorkerManager:
    """Manager for Celery worker configurations."""
    
    def __init__(self, environment: str = "development"):
        """
        Initialize worker manager.
        
        Args:
            environment: Environment (development, staging, production)
        """
        self.environment = environment
        self.worker_configs = self._get_worker_configs()
    
    def _get_worker_configs(self) -> Dict[str, WorkerConfig]:
        """
        Get worker configurations based on environment.
        
        Returns:
            Dict mapping worker names to configurations
        """
        if self.environment == "production":
            return self._get_production_configs()
        elif self.environment == "staging":
            return self._get_staging_configs()
        else:
            return self._get_development_configs()
    
    def _get_production_configs(self) -> Dict[str, WorkerConfig]:
        """Get production worker configurations."""
        return {
            "worker_firs_critical": WorkerConfig(
                name="worker_firs_critical",
                queues=["firs_critical"],
                concurrency=4,
                prefetch_multiplier=1,
                max_tasks_per_child=500,
                pool_type="prefork",
                optimization="speed",
                time_limit=600,  # 10 minutes for critical tasks
                soft_time_limit=540,
                autoscale=(8, 2)  # Scale between 2-8 workers
            ),
            
            "worker_pos_realtime": WorkerConfig(
                name="worker_pos_realtime", 
                queues=["pos_high", "pos_standard"],
                concurrency=6,
                prefetch_multiplier=1,
                max_tasks_per_child=1000,
                pool_type="prefork",
                optimization="speed",
                time_limit=300,
                soft_time_limit=240,
                autoscale=(12, 3)  # Scale between 3-12 workers
            ),
            
            "worker_firs_standard": WorkerConfig(
                name="worker_firs_standard",
                queues=["firs_high"],
                concurrency=4,
                prefetch_multiplier=2,
                max_tasks_per_child=1000,
                pool_type="prefork",
                optimization="fair",
                time_limit=300,
                soft_time_limit=240,
                autoscale=(8, 2)  # Scale between 2-8 workers
            ),
            
            "worker_crm": WorkerConfig(
                name="worker_crm",
                queues=["crm_high", "crm_standard"],
                concurrency=3,
                prefetch_multiplier=2,
                max_tasks_per_child=1000,
                pool_type="prefork",
                optimization="fair",
                time_limit=300,
                soft_time_limit=240,
                autoscale=(6, 1)  # Scale between 1-6 workers
            ),
            
            "worker_batch": WorkerConfig(
                name="worker_batch",
                queues=["batch_high", "batch_standard"],
                concurrency=2,
                prefetch_multiplier=1,
                max_tasks_per_child=500,
                pool_type="prefork",
                optimization="fair",
                time_limit=1800,  # 30 minutes for batch operations
                soft_time_limit=1740,
                autoscale=(4, 1)  # Scale between 1-4 workers
            ),
            
            "worker_maintenance": WorkerConfig(
                name="worker_maintenance",
                queues=["maintenance", "default"],
                concurrency=1,
                prefetch_multiplier=1,
                max_tasks_per_child=100,
                pool_type="prefork",
                optimization="fair",
                time_limit=3600,  # 1 hour for maintenance tasks
                soft_time_limit=3540,
                autoscale=None  # No autoscaling for maintenance
            )
        }
    
    def _get_staging_configs(self) -> Dict[str, WorkerConfig]:
        """Get staging worker configurations (reduced resource usage)."""
        return {
            "worker_firs": WorkerConfig(
                name="worker_firs",
                queues=["firs_critical", "firs_high"],
                concurrency=2,
                prefetch_multiplier=1,
                max_tasks_per_child=500,
                pool_type="prefork",
                optimization="fair",
                time_limit=300,
                soft_time_limit=240,
                autoscale=(4, 1)
            ),
            
            "worker_integrations": WorkerConfig(
                name="worker_integrations",
                queues=["pos_high", "pos_standard", "crm_high", "crm_standard"],
                concurrency=2,
                prefetch_multiplier=2,
                max_tasks_per_child=1000,
                pool_type="prefork",
                optimization="fair",
                time_limit=300,
                soft_time_limit=240,
                autoscale=(4, 1)
            ),
            
            "worker_general": WorkerConfig(
                name="worker_general",
                queues=["batch_high", "batch_standard", "maintenance", "default"],
                concurrency=1,
                prefetch_multiplier=1,
                max_tasks_per_child=500,
                pool_type="prefork",
                optimization="fair",
                time_limit=1800,
                soft_time_limit=1740,
                autoscale=None
            )
        }
    
    def _get_development_configs(self) -> Dict[str, WorkerConfig]:
        """Get development worker configurations (single worker for simplicity)."""
        return {
            "worker_dev": WorkerConfig(
                name="worker_dev",
                queues=[
                    "firs_critical", "firs_high", "pos_high", "pos_standard",
                    "crm_high", "crm_standard", "batch_high", "batch_standard", 
                    "maintenance", "default"
                ],
                concurrency=2,
                prefetch_multiplier=1,
                max_tasks_per_child=100,
                pool_type="prefork",
                optimization="fair",
                time_limit=300,
                soft_time_limit=240,
                autoscale=None
            )
        }
    
    def get_worker_command(self, worker_name: str) -> List[str]:
        """
        Generate Celery worker command for a specific worker.
        
        Args:
            worker_name: Name of the worker configuration
            
        Returns:
            List of command arguments for starting the worker
            
        Raises:
            ValueError: If worker_name is not found
        """
        if worker_name not in self.worker_configs:
            raise ValueError(f"Worker '{worker_name}' not found in configurations")
        
        config = self.worker_configs[worker_name]
        
        cmd = [
            "celery", "worker",
            "--app=app.core.celery:celery_app",
            f"--hostname={config.name}@%h",
            f"--queues={','.join(config.queues)}",
            f"--concurrency={config.concurrency}",
            f"--prefetch-multiplier={config.prefetch_multiplier}",
            f"--pool={config.pool_type}",
            f"--optimization={config.optimization}",
            f"--time-limit={config.time_limit}",
            f"--soft-time-limit={config.soft_time_limit}",
            f"--loglevel={config.log_level}",
        ]
        
        if config.max_tasks_per_child:
            cmd.append(f"--max-tasks-per-child={config.max_tasks_per_child}")
        
        if config.autoscale:
            max_workers, min_workers = config.autoscale
            cmd.append(f"--autoscale={max_workers},{min_workers}")
        
        return cmd
    
    def get_all_worker_commands(self) -> Dict[str, List[str]]:
        """
        Get commands for all configured workers.
        
        Returns:
            Dict mapping worker names to command lists
        """
        return {
            name: self.get_worker_command(name) 
            for name in self.worker_configs.keys()
        }
    
    def generate_supervisor_config(self) -> str:
        """
        Generate Supervisor configuration for all workers.
        
        Returns:
            Supervisor configuration as string
        """
        config_lines = []
        
        # Generate configuration for each worker
        for name, config in self.worker_configs.items():
            cmd = " ".join(self.get_worker_command(name))
            
            config_lines.extend([
                f"[program:{name}]",
                f"command={cmd}",
                f"directory=/app",
                f"user=www-data",
                f"numprocs=1",
                f"stdout_logfile=/var/log/celery/{name}.log",
                f"stderr_logfile=/var/log/celery/{name}.error.log",
                f"autostart=true",
                f"autorestart=true",
                f"startsecs=10",
                f"stopwaitsecs=600",
                f"killasgroup=true",
                f"priority=999",
                "",
            ])
        
        # Add group configuration
        worker_names = ",".join(self.worker_configs.keys())
        config_lines.extend([
            "[group:taxpoynt_workers]",
            f"programs={worker_names}",
            "priority=999",
            "",
        ])
        
        return "\n".join(config_lines)
    
    def generate_systemd_services(self) -> Dict[str, str]:
        """
        Generate systemd service files for all workers.
        
        Returns:
            Dict mapping worker names to service file contents
        """
        services = {}
        
        for name, config in self.worker_configs.items():
            cmd = " ".join(self.get_worker_command(name))
            
            service_content = f"""[Unit]
Description=Celery Worker {name}
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/etc/default/taxpoynt
WorkingDirectory=/app
ExecStart={cmd}
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
            services[f"{name}.service"] = service_content
        
        return services
    
    def get_monitoring_info(self) -> Dict[str, Any]:
        """
        Get monitoring information for all workers.
        
        Returns:
            Dict containing worker monitoring details
        """
        return {
            "environment": self.environment,
            "total_workers": len(self.worker_configs),
            "workers": {
                name: {
                    "queues": config.queues,
                    "concurrency": config.concurrency,
                    "pool_type": config.pool_type,
                    "autoscale": config.autoscale,
                    "time_limits": {
                        "hard": config.time_limit,
                        "soft": config.soft_time_limit
                    }
                }
                for name, config in self.worker_configs.items()
            }
        }


# ==================== HELPER FUNCTIONS ====================

def get_environment() -> str:
    """Get current environment from environment variables."""
    return os.getenv("APP_ENV", "development").lower()


def create_worker_manager() -> WorkerManager:
    """Create worker manager for current environment."""
    environment = get_environment()
    return WorkerManager(environment)


def get_recommended_worker_count() -> int:
    """
    Get recommended worker count based on system resources.
    
    Returns:
        Recommended number of worker processes
    """
    try:
        import psutil
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Conservative estimate: 1-2 workers per CPU core
        # Adjust based on available memory
        if memory_gb < 2:
            return min(2, cpu_count)
        elif memory_gb < 4:
            return min(4, cpu_count)
        else:
            return min(cpu_count * 2, 16)  # Cap at 16 workers
            
    except ImportError:
        # Fall back to basic calculation if psutil not available
        try:
            import multiprocessing
            return min(multiprocessing.cpu_count(), 4)
        except:
            return 2  # Safe default


# ==================== EXPORT ====================

__all__ = [
    "WorkerConfig", 
    "WorkerManager", 
    "create_worker_manager",
    "get_environment",
    "get_recommended_worker_count"
]