"""
Connection Manager Service

Manages connections to various business systems (ERP, CRM, POS) for System Integrator role.
Handles connection pooling, lifecycle management, and connection state monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import ssl
import weakref

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class SystemType(Enum):
    """Supported system types"""
    ODOO = "odoo"
    SAP = "sap"
    ORACLE = "oracle"
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    DYNAMICS = "dynamics"
    CUSTOM_ERP = "custom_erp"


@dataclass
class ConnectionConfig:
    """Configuration for system connection"""
    system_id: str
    system_type: SystemType
    host: str
    port: int
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    ssl_enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    pool_size: int = 5
    pool_max_overflow: int = 10
    health_check_interval: int = 60
    connection_ttl: int = 3600
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionStatus:
    """Current status of a connection"""
    system_id: str
    state: ConnectionState
    connected_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    health_score: float = 1.0
    active_sessions: int = 0
    total_requests: int = 0
    failed_requests: int = 0


class ConnectionPool:
    """Connection pool for a specific system"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connections: List[Any] = []
        self.available_connections: asyncio.Queue = asyncio.Queue(maxsize=config.pool_size)
        self.active_connections: Set[Any] = set()
        self.created_count = 0
        self.lock = asyncio.Lock()
        
    async def get_connection(self):
        """Get connection from pool"""
        try:
            # Try to get available connection first
            connection = await asyncio.wait_for(
                self.available_connections.get(),
                timeout=self.config.timeout
            )
            
            if await self._validate_connection(connection):
                self.active_connections.add(connection)
                return connection
            else:
                # Connection is stale, create new one
                await self._close_connection(connection)
                
        except asyncio.TimeoutError:
            pass
        
        # Create new connection if pool allows
        async with self.lock:
            if self.created_count < self.config.pool_size + self.config.pool_max_overflow:
                connection = await self._create_connection()
                if connection:
                    self.created_count += 1
                    self.active_connections.add(connection)
                    return connection
        
        raise ConnectionError(f"Unable to get connection for {self.config.system_id}")
    
    async def return_connection(self, connection):
        """Return connection to pool"""
        if connection in self.active_connections:
            self.active_connections.remove(connection)
            
            if await self._validate_connection(connection):
                try:
                    await self.available_connections.put(connection)
                except asyncio.QueueFull:
                    await self._close_connection(connection)
                    async with self.lock:
                        self.created_count -= 1
            else:
                await self._close_connection(connection)
                async with self.lock:
                    self.created_count -= 1
    
    async def _create_connection(self):
        """Create new connection based on system type"""
        try:
            if self.config.system_type == SystemType.ODOO:
                return await self._create_odoo_connection()
            elif self.config.system_type == SystemType.SAP:
                return await self._create_sap_connection()
            else:
                # Generic connection
                return await self._create_generic_connection()
        except Exception as e:
            logger.error(f"Failed to create connection for {self.config.system_id}: {e}")
            return None
    
    async def _create_odoo_connection(self):
        """Create Odoo connection"""
        import odoorpc
        
        odoo = odoorpc.ODOO(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.timeout
        )
        
        # Authenticate using credentials
        # TODO: Integrate with Auth Coordinator for enhanced authentication management
        if self.config.username and self.config.password:
            odoo.login(self.config.database, self.config.username, self.config.password)
        
        return odoo
    
    async def _create_sap_connection(self):
        """Create SAP connection"""
        # TODO: Implement SAP connection logic
        return {"type": "sap", "host": self.config.host, "connected": True}
    
    async def _create_generic_connection(self):
        """Create generic connection"""
        return {
            "type": "generic",
            "host": self.config.host,
            "port": self.config.port,
            "connected": True,
            "created_at": datetime.now()
        }
    
    async def _validate_connection(self, connection) -> bool:
        """Validate if connection is still alive"""
        try:
            if hasattr(connection, 'version'):
                # Odoo connection
                version = connection.version
                return bool(version)
            elif isinstance(connection, dict):
                # Generic connection
                return connection.get("connected", False)
            return True
        except:
            return False
    
    async def _close_connection(self, connection):
        """Close connection"""
        try:
            if hasattr(connection, 'logout'):
                connection.logout()
        except:
            pass
    
    async def close_all(self):
        """Close all connections in pool"""
        # Close available connections
        while not self.available_connections.empty():
            try:
                connection = await self.available_connections.get()
                await self._close_connection(connection)
            except:
                pass
        
        # Close active connections
        for connection in list(self.active_connections):
            await self._close_connection(connection)
        
        self.active_connections.clear()
        self.created_count = 0


class ConnectionManager:
    """Main connection manager for all system integrations"""
    
    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self.status_registry: Dict[str, ConnectionStatus] = {}
        self.configs: Dict[str, ConnectionConfig] = {}
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.connection_callbacks: Dict[str, List[callable]] = {}
        self.connection_tester = None  # Will be injected for comprehensive testing
        self.auth_coordinator = None  # Will be injected for authentication
    
    def set_connection_tester(self, connection_tester):
        """Inject connection tester dependency for comprehensive testing"""
        self.connection_tester = connection_tester
    
    def set_auth_coordinator(self, auth_coordinator):
        """Inject auth coordinator dependency for authentication"""
        self.auth_coordinator = auth_coordinator
        
    async def register_system(self, config: ConnectionConfig) -> bool:
        """
        Register a new system for connection management
        
        Args:
            config: System connection configuration
            
        Returns:
            Success status
        """
        try:
            system_id = config.system_id
            
            # Store configuration
            self.configs[system_id] = config
            
            # Create connection pool
            self.pools[system_id] = ConnectionPool(config)
            
            # Initialize status
            self.status_registry[system_id] = ConnectionStatus(
                system_id=system_id,
                state=ConnectionState.DISCONNECTED
            )
            
            # Start health check task
            self.health_check_tasks[system_id] = asyncio.create_task(
                self._health_check_loop(system_id)
            )
            
            logger.info(f"Registered system: {system_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register system {config.system_id}: {e}")
            return False
    
    async def unregister_system(self, system_id: str) -> bool:
        """
        Unregister system and cleanup resources
        
        Args:
            system_id: System identifier
            
        Returns:
            Success status
        """
        try:
            # Cancel health check task
            if system_id in self.health_check_tasks:
                self.health_check_tasks[system_id].cancel()
                del self.health_check_tasks[system_id]
            
            # Close all connections
            if system_id in self.pools:
                await self.pools[system_id].close_all()
                del self.pools[system_id]
            
            # Cleanup registries
            self.configs.pop(system_id, None)
            self.status_registry.pop(system_id, None)
            self.connection_callbacks.pop(system_id, None)
            
            logger.info(f"Unregistered system: {system_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister system {system_id}: {e}")
            return False
    
    @asynccontextmanager
    async def get_connection(self, system_id: str):
        """
        Get connection for system with automatic cleanup
        
        Args:
            system_id: System identifier
            
        Yields:
            System connection
        """
        if system_id not in self.pools:
            raise ValueError(f"System {system_id} not registered")
        
        pool = self.pools[system_id]
        status = self.status_registry[system_id]
        
        connection = None
        try:
            # Update status
            status.state = ConnectionState.CONNECTING
            
            # Get connection from pool
            connection = await pool.get_connection()
            
            # Update status
            status.state = ConnectionState.CONNECTED
            status.connected_at = datetime.now()
            status.last_activity = datetime.now()
            status.active_sessions += 1
            status.total_requests += 1
            
            # Trigger callbacks
            await self._trigger_callbacks(system_id, "connection_acquired", connection)
            
            yield connection
            
        except Exception as e:
            status.state = ConnectionState.FAILED
            status.error_message = str(e)
            status.failed_requests += 1
            logger.error(f"Connection error for {system_id}: {e}")
            raise
        finally:
            if connection:
                # Return connection to pool
                await pool.return_connection(connection)
                status.active_sessions -= 1
                status.last_activity = datetime.now()
                
                # Trigger callbacks
                await self._trigger_callbacks(system_id, "connection_released", connection)
    
    async def test_connection(self, system_id: str) -> Dict[str, Any]:
        """
        Test connection to specific system.
        Uses injected connection tester for comprehensive testing if available,
        otherwise performs basic connection pool test.
        
        Args:
            system_id: System identifier
            
        Returns:
            Test result with details
        """
        try:
            # If comprehensive connection tester is available, use it
            if self.connection_tester and system_id in self.configs:
                config = self.configs[system_id]
                integration_data = {
                    "id": system_id,
                    "config": {
                        "type": config.system_type.value,
                        "host": config.host,
                        "port": config.port,
                        "ssl_enabled": config.ssl_enabled,
                        "timeout": config.timeout,
                        **config.connection_params
                    }
                }
                return self.connection_tester.test_integration_connection(integration_data)
            
            # Otherwise, perform basic connection pool test
            async with self.get_connection(system_id) as connection:
                test_result = await self._perform_connection_test(system_id, connection)
                
                return {
                    "success": True,
                    "system_id": system_id,
                    "test_result": test_result,
                    "tested_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "system_id": system_id,
                "error": str(e),
                "tested_at": datetime.now().isoformat()
            }
    
    async def _perform_connection_test(self, system_id: str, connection) -> Dict[str, Any]:
        """Perform connection-specific test"""
        config = self.configs[system_id]
        
        if config.system_type == SystemType.ODOO:
            # Test Odoo connection
            version = connection.version
            return {
                "version": version,
                "database": connection.env.cr.dbname,
                "user_id": connection.env.uid
            }
        else:
            # Generic test
            return {"status": "connected", "type": config.system_type.value}
    
    async def get_system_status(self, system_id: str) -> Optional[ConnectionStatus]:
        """Get status for specific system"""
        return self.status_registry.get(system_id)
    
    async def get_all_statuses(self) -> Dict[str, ConnectionStatus]:
        """Get status for all registered systems"""
        return self.status_registry.copy()
    
    async def add_connection_callback(self, system_id: str, event: str, callback: callable):
        """Add callback for connection events"""
        if system_id not in self.connection_callbacks:
            self.connection_callbacks[system_id] = []
        
        self.connection_callbacks[system_id].append((event, callback))
    
    async def _trigger_callbacks(self, system_id: str, event: str, data: Any):
        """Trigger registered callbacks"""
        if system_id in self.connection_callbacks:
            for cb_event, callback in self.connection_callbacks[system_id]:
                if cb_event == event:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(system_id, data)
                        else:
                            callback(system_id, data)
                    except Exception as e:
                        logger.error(f"Callback error for {system_id}.{event}: {e}")
    
    async def _health_check_loop(self, system_id: str):
        """Continuous health check for system"""
        config = self.configs[system_id]
        status = self.status_registry[system_id]
        
        while True:
            try:
                await asyncio.sleep(config.health_check_interval)
                
                # Perform health check
                health_result = await self.test_connection(system_id)
                
                if health_result["success"]:
                    status.health_score = min(1.0, status.health_score + 0.1)
                    status.retry_count = 0
                else:
                    status.health_score = max(0.0, status.health_score - 0.2)
                    status.retry_count += 1
                    status.error_message = health_result.get("error")
                
                # Update state based on health
                if status.health_score < 0.3:
                    status.state = ConnectionState.FAILED
                elif status.health_score < 0.7:
                    status.state = ConnectionState.RECONNECTING
                else:
                    status.state = ConnectionState.CONNECTED
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error for {system_id}: {e}")
                status.health_score = max(0.0, status.health_score - 0.3)
    
    async def shutdown(self):
        """Shutdown connection manager and cleanup all resources"""
        # Cancel all health check tasks
        for task in self.health_check_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.health_check_tasks:
            await asyncio.gather(*self.health_check_tasks.values(), return_exceptions=True)
        
        # Close all connection pools
        for pool in self.pools.values():
            await pool.close_all()
        
        # Clear all registries
        self.pools.clear()
        self.status_registry.clear()
        self.configs.clear()
        self.health_check_tasks.clear()
        self.connection_callbacks.clear()
        
        logger.info("Connection manager shutdown complete")


# Global instance
connection_manager = ConnectionManager()


async def register_system(config: ConnectionConfig) -> bool:
    """Register system with global connection manager"""
    return await connection_manager.register_system(config)


async def get_connection(system_id: str):
    """Get connection from global connection manager"""
    async with connection_manager.get_connection(system_id) as connection:
        yield connection


async def test_system_connection(system_id: str) -> Dict[str, Any]:
    """Test connection for system"""
    return await connection_manager.test_connection(system_id)