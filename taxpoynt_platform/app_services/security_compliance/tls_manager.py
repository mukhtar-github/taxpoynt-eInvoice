"""
TLS Manager Service for APP Role

This service manages TLS 1.3 secure communications including:
- TLS 1.3 connection establishment and management
- Certificate validation and management
- Secure channel configuration
- Connection pooling and reuse
- TLS session management and resumption
"""

import ssl
import socket
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import certifi
import hashlib
import json

from cryptography.x509 import load_pem_x509_certificate, Certificate
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TLSVersion(Enum):
    """Supported TLS versions"""
    TLS_1_2 = "TLSv1.2"
    TLS_1_3 = "TLSv1.3"


class CipherSuite(Enum):
    """TLS 1.3 cipher suites"""
    AES_256_GCM_SHA384 = "TLS_AES_256_GCM_SHA384"
    AES_128_GCM_SHA256 = "TLS_AES_128_GCM_SHA256"
    CHACHA20_POLY1305_SHA256 = "TLS_CHACHA20_POLY1305_SHA256"


class ConnectionState(Enum):
    """Connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    CLOSED = "closed"


class SecurityLevel(Enum):
    """Security levels for TLS connections"""
    MINIMUM = "minimum"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class TLSConfiguration:
    """TLS configuration settings"""
    version: TLSVersion = TLSVersion.TLS_1_3
    cipher_suites: List[CipherSuite] = field(default_factory=lambda: [
        CipherSuite.AES_256_GCM_SHA384,
        CipherSuite.AES_128_GCM_SHA256
    ])
    security_level: SecurityLevel = SecurityLevel.HIGH
    verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED
    check_hostname: bool = True
    ca_bundle_path: Optional[str] = None
    client_cert_path: Optional[str] = None
    client_key_path: Optional[str] = None
    session_timeout: int = 300
    handshake_timeout: int = 30
    enable_session_resumption: bool = True
    enable_sni: bool = True
    enable_alpn: bool = True
    alpn_protocols: List[str] = field(default_factory=lambda: ['h2', 'http/1.1'])


@dataclass
class CertificateInfo:
    """Certificate information"""
    subject: str
    issuer: str
    serial_number: str
    not_before: datetime
    not_after: datetime
    fingerprint: str
    signature_algorithm: str
    key_size: int
    san_domains: List[str] = field(default_factory=list)
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class TLSConnectionInfo:
    """TLS connection information"""
    connection_id: str
    remote_host: str
    remote_port: int
    tls_version: str
    cipher_suite: str
    server_certificate: CertificateInfo
    client_certificate: Optional[CertificateInfo] = None
    session_resumed: bool = False
    handshake_time: float = 0.0
    established_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    bytes_sent: int = 0
    bytes_received: int = 0
    state: ConnectionState = ConnectionState.DISCONNECTED


@dataclass
class TLSSession:
    """TLS session data"""
    session_id: str
    session_data: bytes
    created_at: datetime
    last_used: datetime
    hostname: str
    port: int
    expiry: datetime


@dataclass
class SecurityEvent:
    """Security event for audit"""
    event_id: str
    event_type: str
    severity: str
    connection_id: Optional[str]
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)


class TLSManager:
    """
    TLS manager service for APP role
    
    Handles:
    - TLS 1.3 connection establishment and management
    - Certificate validation and management
    - Secure channel configuration
    - Connection pooling and reuse
    - TLS session management and resumption
    """
    
    def __init__(self, 
                 config: Optional[TLSConfiguration] = None,
                 max_connections: int = 100,
                 connection_timeout: int = 30):
        self.config = config or TLSConfiguration()
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        
        # Connection management
        self.active_connections: Dict[str, TLSConnectionInfo] = {}
        self.connection_pool: Dict[str, List[ssl.SSLSocket]] = defaultdict(list)
        self.session_cache: Dict[str, TLSSession] = {}
        
        # Security events
        self.security_events: List[SecurityEvent] = []
        
        # SSL context
        self.ssl_context: Optional[ssl.SSLContext] = None
        self._setup_ssl_context()
        
        # HTTP session with TLS
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Metrics
        self.metrics = {
            'total_connections': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'handshake_failures': 0,
            'certificate_errors': 0,
            'session_resumptions': 0,
            'average_handshake_time': 0.0,
            'connections_by_host': defaultdict(int),
            'cipher_usage': defaultdict(int),
            'tls_version_usage': defaultdict(int)
        }
    
    def _setup_ssl_context(self):
        """Setup SSL context with TLS 1.3 configuration"""
        try:
            # Create SSL context
            if self.config.version == TLSVersion.TLS_1_3:
                self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
                self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
            else:
                self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            # Configure verification
            self.ssl_context.verify_mode = self.config.verify_mode
            self.ssl_context.check_hostname = self.config.check_hostname
            
            # Load CA bundle
            if self.config.ca_bundle_path:
                self.ssl_context.load_verify_locations(self.config.ca_bundle_path)
            else:
                # Use certifi bundle
                self.ssl_context.load_verify_locations(certifi.where())
            
            # Load client certificate if provided
            if self.config.client_cert_path and self.config.client_key_path:
                self.ssl_context.load_cert_chain(
                    self.config.client_cert_path,
                    self.config.client_key_path
                )
            
            # Configure cipher suites for TLS 1.3
            if self.config.version == TLSVersion.TLS_1_3:
                cipher_list = ':'.join([cs.value for cs in self.config.cipher_suites])
                self.ssl_context.set_ciphers('TLSv1.3')
            
            # Configure ALPN
            if self.config.enable_alpn:
                self.ssl_context.set_alpn_protocols(self.config.alpn_protocols)
            
            # Security level
            if self.config.security_level == SecurityLevel.MAXIMUM:
                self.ssl_context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            
            logger.info("SSL context configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup SSL context: {e}")
            raise
    
    async def establish_connection(self, 
                                 hostname: str,
                                 port: int,
                                 timeout: Optional[int] = None) -> TLSConnectionInfo:
        """
        Establish TLS connection to remote host
        
        Args:
            hostname: Remote hostname
            port: Remote port
            timeout: Connection timeout
            
        Returns:
            TLSConnectionInfo with connection details
        """
        connection_id = f"{hostname}:{port}:{int(time.time())}"
        start_time = time.time()
        timeout = timeout or self.connection_timeout
        
        try:
            # Check for existing pooled connection
            pool_key = f"{hostname}:{port}"
            if pool_key in self.connection_pool and self.connection_pool[pool_key]:
                socket_conn = self.connection_pool[pool_key].pop()
                if self._is_connection_alive(socket_conn):
                    logger.info(f"Reusing pooled connection to {hostname}:{port}")
                    return self._create_connection_info(connection_id, hostname, port, socket_conn, 0.0)
            
            # Create new connection
            logger.info(f"Establishing new TLS connection to {hostname}:{port}")
            
            # Create socket
            sock = socket.create_connection((hostname, port), timeout)
            
            # Check for session resumption
            session_key = f"{hostname}:{port}"
            session_data = None
            if self.config.enable_session_resumption and session_key in self.session_cache:
                cached_session = self.session_cache[session_key]
                if cached_session.expiry > datetime.utcnow():
                    session_data = cached_session.session_data
                    logger.info(f"Attempting session resumption for {hostname}:{port}")
            
            # Wrap with TLS
            tls_socket = self.ssl_context.wrap_socket(
                sock,
                server_hostname=hostname if self.config.enable_sni else None,
                session=session_data
            )
            
            # Perform TLS handshake
            tls_socket.do_handshake()
            handshake_time = time.time() - start_time
            
            # Check if session was resumed
            session_resumed = session_data is not None and tls_socket.session_reused
            if session_resumed:
                self.metrics['session_resumptions'] += 1
                logger.info(f"Session resumed for {hostname}:{port}")
            
            # Store session for future resumption
            if not session_resumed and self.config.enable_session_resumption:
                session = TLSSession(
                    session_id=f"{hostname}:{port}:{int(time.time())}",
                    session_data=tls_socket.session,
                    created_at=datetime.utcnow(),
                    last_used=datetime.utcnow(),
                    hostname=hostname,
                    port=port,
                    expiry=datetime.utcnow() + timedelta(seconds=self.config.session_timeout)
                )
                self.session_cache[session_key] = session
            
            # Create connection info
            connection_info = self._create_connection_info(
                connection_id, hostname, port, tls_socket, handshake_time, session_resumed
            )
            
            # Store active connection
            self.active_connections[connection_id] = connection_info
            
            # Update metrics
            self.metrics['total_connections'] += 1
            self.metrics['successful_connections'] += 1
            self.metrics['connections_by_host'][hostname] += 1
            self.metrics['cipher_usage'][connection_info.cipher_suite] += 1
            self.metrics['tls_version_usage'][connection_info.tls_version] += 1
            
            # Update average handshake time
            total_connections = self.metrics['successful_connections']
            current_avg = self.metrics['average_handshake_time']
            self.metrics['average_handshake_time'] = (
                (current_avg * (total_connections - 1) + handshake_time) / total_connections
            )
            
            # Log security event
            await self._log_security_event(
                "TLS_CONNECTION_ESTABLISHED",
                "info",
                connection_id,
                f"TLS connection established to {hostname}:{port}",
                {
                    'tls_version': connection_info.tls_version,
                    'cipher_suite': connection_info.cipher_suite,
                    'session_resumed': session_resumed,
                    'handshake_time': handshake_time
                }
            )
            
            logger.info(f"TLS connection established to {hostname}:{port} "
                       f"(ID: {connection_id}, Version: {connection_info.tls_version}, "
                       f"Cipher: {connection_info.cipher_suite})")
            
            return connection_info
            
        except ssl.SSLError as e:
            self.metrics['failed_connections'] += 1
            self.metrics['handshake_failures'] += 1
            
            await self._log_security_event(
                "TLS_HANDSHAKE_FAILURE",
                "error",
                connection_id,
                f"TLS handshake failed for {hostname}:{port}: {str(e)}",
                {'error': str(e), 'hostname': hostname, 'port': port}
            )
            
            logger.error(f"TLS handshake failed for {hostname}:{port}: {e}")
            raise
            
        except Exception as e:
            self.metrics['failed_connections'] += 1
            
            await self._log_security_event(
                "TLS_CONNECTION_FAILURE",
                "error",
                connection_id,
                f"TLS connection failed for {hostname}:{port}: {str(e)}",
                {'error': str(e), 'hostname': hostname, 'port': port}
            )
            
            logger.error(f"TLS connection failed for {hostname}:{port}: {e}")
            raise
    
    async def create_http_session(self, **kwargs) -> aiohttp.ClientSession:
        """
        Create HTTP session with TLS configuration
        
        Returns:
            aiohttp.ClientSession with TLS configuration
        """
        if self.http_session and not self.http_session.closed:
            return self.http_session
        
        # Create connector with TLS configuration
        connector = aiohttp.TCPConnector(
            ssl=self.ssl_context,
            limit=self.max_connections,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True,
            **kwargs
        )
        
        # Create session
        timeout = aiohttp.ClientTimeout(total=self.connection_timeout)
        self.http_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'TaxPoynt-APP/1.0'}
        )
        
        logger.info("HTTP session with TLS configuration created")
        return self.http_session
    
    async def make_secure_request(self, 
                                method: str,
                                url: str,
                                **kwargs) -> aiohttp.ClientResponse:
        """
        Make secure HTTP request with TLS
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            aiohttp.ClientResponse
        """
        session = await self.create_http_session()
        
        try:
            response = await session.request(method, url, **kwargs)
            
            # Log successful request
            await self._log_security_event(
                "SECURE_REQUEST_SUCCESS",
                "info",
                None,
                f"Secure {method} request to {url} successful",
                {'method': method, 'url': url, 'status': response.status}
            )
            
            return response
            
        except aiohttp.ClientSSLError as e:
            self.metrics['certificate_errors'] += 1
            
            await self._log_security_event(
                "SECURE_REQUEST_SSL_ERROR",
                "error",
                None,
                f"SSL error in {method} request to {url}: {str(e)}",
                {'method': method, 'url': url, 'error': str(e)}
            )
            
            logger.error(f"SSL error in {method} request to {url}: {e}")
            raise
            
        except Exception as e:
            await self._log_security_event(
                "SECURE_REQUEST_ERROR",
                "error",
                None,
                f"Error in {method} request to {url}: {str(e)}",
                {'method': method, 'url': url, 'error': str(e)}
            )
            
            logger.error(f"Error in {method} request to {url}: {e}")
            raise
    
    def _create_connection_info(self, 
                              connection_id: str,
                              hostname: str,
                              port: int,
                              tls_socket: ssl.SSLSocket,
                              handshake_time: float,
                              session_resumed: bool = False) -> TLSConnectionInfo:
        """Create connection info from TLS socket"""
        # Get TLS information
        tls_version = tls_socket.version()
        cipher_suite = tls_socket.cipher()[0] if tls_socket.cipher() else "Unknown"
        
        # Get server certificate
        server_cert_der = tls_socket.getpeercert_chain()[0].public_bytes(serialization.Encoding.DER)
        server_cert = load_pem_x509_certificate(
            server_cert_der, 
            default_backend()
        ) if server_cert_der else None
        
        server_cert_info = self._extract_certificate_info(server_cert) if server_cert else None
        
        # Get client certificate if present
        client_cert_info = None
        try:
            client_cert_der = tls_socket.getpeercert(binary_form=True)
            if client_cert_der:
                client_cert = load_pem_x509_certificate(client_cert_der, default_backend())
                client_cert_info = self._extract_certificate_info(client_cert)
        except:
            pass
        
        return TLSConnectionInfo(
            connection_id=connection_id,
            remote_host=hostname,
            remote_port=port,
            tls_version=tls_version,
            cipher_suite=cipher_suite,
            server_certificate=server_cert_info,
            client_certificate=client_cert_info,
            session_resumed=session_resumed,
            handshake_time=handshake_time,
            state=ConnectionState.CONNECTED
        )
    
    def _extract_certificate_info(self, certificate: Certificate) -> CertificateInfo:
        """Extract information from X.509 certificate"""
        try:
            # Get SAN domains
            san_domains = []
            try:
                san_extension = certificate.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                ).value
                san_domains = [name.value for name in san_extension]
            except:
                pass
            
            return CertificateInfo(
                subject=certificate.subject.rfc4514_string(),
                issuer=certificate.issuer.rfc4514_string(),
                serial_number=str(certificate.serial_number),
                not_before=certificate.not_valid_before,
                not_after=certificate.not_valid_after,
                fingerprint=hashlib.sha256(
                    certificate.public_bytes(serialization.Encoding.DER)
                ).hexdigest(),
                signature_algorithm=certificate.signature_algorithm_oid._name,
                key_size=certificate.public_key().key_size,
                san_domains=san_domains,
                is_valid=datetime.utcnow() < certificate.not_valid_after
            )
            
        except Exception as e:
            logger.error(f"Error extracting certificate info: {e}")
            return CertificateInfo(
                subject="Unknown",
                issuer="Unknown",
                serial_number="Unknown",
                not_before=datetime.utcnow(),
                not_after=datetime.utcnow(),
                fingerprint="Unknown",
                signature_algorithm="Unknown",
                key_size=0,
                is_valid=False,
                validation_errors=[str(e)]
            )
    
    def _is_connection_alive(self, socket_conn: ssl.SSLSocket) -> bool:
        """Check if connection is still alive"""
        try:
            # Try to peek at the socket
            socket_conn.settimeout(1)
            data = socket_conn.recv(1, socket.MSG_PEEK)
            return True
        except:
            return False
    
    async def close_connection(self, connection_id: str):
        """Close TLS connection"""
        if connection_id in self.active_connections:
            connection_info = self.active_connections[connection_id]
            
            try:
                # Move to connection pool if possible
                pool_key = f"{connection_info.remote_host}:{connection_info.remote_port}"
                if len(self.connection_pool[pool_key]) < 5:  # Max 5 connections per host
                    # This would need the actual socket reference in a real implementation
                    pass
                
                # Remove from active connections
                del self.active_connections[connection_id]
                
                await self._log_security_event(
                    "TLS_CONNECTION_CLOSED",
                    "info",
                    connection_id,
                    f"TLS connection closed: {connection_id}",
                    {'host': connection_info.remote_host, 'port': connection_info.remote_port}
                )
                
                logger.info(f"TLS connection closed: {connection_id}")
                
            except Exception as e:
                logger.error(f"Error closing connection {connection_id}: {e}")
    
    async def cleanup_expired_sessions(self):
        """Clean up expired TLS sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_key, session in self.session_cache.items():
            if session.expiry <= current_time:
                expired_sessions.append(session_key)
        
        for session_key in expired_sessions:
            del self.session_cache[session_key]
            
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired TLS sessions")
    
    async def validate_certificate_chain(self, hostname: str, port: int) -> Dict[str, Any]:
        """Validate certificate chain for hostname"""
        try:
            # Create connection to get certificate chain
            sock = socket.create_connection((hostname, port), self.connection_timeout)
            context = ssl.create_default_context()
            
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_chain = ssock.getpeercert_chain()
                
                validation_results = []
                for i, cert_der in enumerate(cert_chain):
                    cert = load_pem_x509_certificate(cert_der.public_bytes(serialization.Encoding.DER), default_backend())
                    cert_info = self._extract_certificate_info(cert)
                    
                    validation_results.append({
                        'position': i,
                        'subject': cert_info.subject,
                        'issuer': cert_info.issuer,
                        'is_valid': cert_info.is_valid,
                        'not_before': cert_info.not_before.isoformat(),
                        'not_after': cert_info.not_after.isoformat(),
                        'fingerprint': cert_info.fingerprint
                    })
                
                return {
                    'hostname': hostname,
                    'port': port,
                    'chain_length': len(cert_chain),
                    'certificates': validation_results,
                    'is_valid': all(cert['is_valid'] for cert in validation_results)
                }
                
        except Exception as e:
            logger.error(f"Certificate validation failed for {hostname}:{port}: {e}")
            return {
                'hostname': hostname,
                'port': port,
                'error': str(e),
                'is_valid': False
            }
    
    async def _log_security_event(self, 
                                event_type: str,
                                severity: str,
                                connection_id: Optional[str],
                                description: str,
                                details: Dict[str, Any]):
        """Log security event"""
        event = SecurityEvent(
            event_id=f"{event_type}_{int(time.time())}_{len(self.security_events)}",
            event_type=event_type,
            severity=severity,
            connection_id=connection_id,
            description=description,
            details=details
        )
        
        self.security_events.append(event)
        
        # Keep only recent events
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-5000:]
    
    async def close(self):
        """Close TLS manager and cleanup resources"""
        # Close HTTP session
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
        
        # Close active connections
        for connection_id in list(self.active_connections.keys()):
            await self.close_connection(connection_id)
        
        # Clear connection pool
        self.connection_pool.clear()
        
        # Clear session cache
        self.session_cache.clear()
        
        logger.info("TLS Manager closed and resources cleaned up")
    
    def get_connection_info(self, connection_id: str) -> Optional[TLSConnectionInfo]:
        """Get connection information"""
        return self.active_connections.get(connection_id)
    
    def list_active_connections(self) -> List[TLSConnectionInfo]:
        """List all active connections"""
        return list(self.active_connections.values())
    
    def get_security_events(self, 
                          event_type: Optional[str] = None,
                          severity: Optional[str] = None,
                          limit: int = 100) -> List[SecurityEvent]:
        """Get security events"""
        events = self.security_events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        return events[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get TLS manager metrics"""
        return {
            **self.metrics,
            'active_connections': len(self.active_connections),
            'pooled_connections': sum(len(conns) for conns in self.connection_pool.values()),
            'cached_sessions': len(self.session_cache),
            'security_events': len(self.security_events),
            'success_rate': (
                self.metrics['successful_connections'] / 
                max(self.metrics['total_connections'], 1)
            ) * 100 if self.metrics['total_connections'] > 0 else 0
        }


# Factory functions for easy setup
def create_tls_manager(config: Optional[TLSConfiguration] = None,
                      max_connections: int = 100) -> TLSManager:
    """Create TLS manager instance"""
    return TLSManager(config, max_connections)


def create_tls_configuration(version: TLSVersion = TLSVersion.TLS_1_3,
                           security_level: SecurityLevel = SecurityLevel.HIGH,
                           **kwargs) -> TLSConfiguration:
    """Create TLS configuration"""
    return TLSConfiguration(
        version=version,
        security_level=security_level,
        **kwargs
    )


async def establish_secure_connection(hostname: str,
                                    port: int,
                                    config: Optional[TLSConfiguration] = None) -> TLSConnectionInfo:
    """Establish secure TLS connection"""
    manager = create_tls_manager(config)
    return await manager.establish_connection(hostname, port)


async def make_secure_http_request(method: str,
                                 url: str,
                                 config: Optional[TLSConfiguration] = None,
                                 **kwargs) -> aiohttp.ClientResponse:
    """Make secure HTTP request"""
    manager = create_tls_manager(config)
    return await manager.make_secure_request(method, url, **kwargs)


def get_tls_security_summary(manager: TLSManager) -> Dict[str, Any]:
    """Get TLS security summary"""
    metrics = manager.get_metrics()
    recent_events = manager.get_security_events(limit=10)
    
    return {
        'total_connections': metrics['total_connections'],
        'active_connections': metrics['active_connections'],
        'success_rate': metrics['success_rate'],
        'tls_1_3_usage': metrics['tls_version_usage'].get('TLSv1.3', 0),
        'session_resumptions': metrics['session_resumptions'],
        'recent_security_events': len(recent_events),
        'certificate_errors': metrics['certificate_errors'],
        'handshake_failures': metrics['handshake_failures']
    }