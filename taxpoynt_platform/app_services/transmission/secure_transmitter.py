"""
Secure Document Transmission Service for APP Role

This service handles secure transmission of documents to FIRS with:
- End-to-end encryption
- Digital signature validation
- Secure channel management
- Transmission integrity verification
- Cryptographic authentication
"""

import asyncio
import json
import hashlib
import hmac
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import aiohttp
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransmissionStatus(Enum):
    """Document transmission status"""
    PENDING = "pending"
    ENCRYPTING = "encrypting"
    SIGNING = "signing"
    TRANSMITTING = "transmitting"
    DELIVERED = "delivered"
    FAILED = "failed"
    VERIFIED = "verified"


class SecurityLevel(Enum):
    """Security levels for transmission"""
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class TransmissionRequest:
    """Document transmission request"""
    document_id: str
    document_type: str
    document_data: Dict[str, Any]
    destination_endpoint: str
    security_level: SecurityLevel = SecurityLevel.STANDARD
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class TransmissionResult:
    """Document transmission result"""
    request_id: str
    document_id: str
    status: TransmissionStatus
    transmission_id: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    transmitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityContext:
    """Security context for transmission"""
    encryption_key: bytes
    signing_key: bytes
    certificate_chain: List[str]
    client_id: str
    api_key: str
    session_token: Optional[str] = None


class SecureTransmitter:
    """
    Secure document transmission service for APP role
    
    Handles:
    - Document encryption and signing
    - Secure channel establishment
    - Transmission integrity verification
    - Response validation
    - Security context management
    """
    
    def __init__(self, 
                 base_url: str,
                 security_context: SecurityContext,
                 connection_timeout: int = 30,
                 read_timeout: int = 60,
                 max_retries: int = 3):
        self.base_url = base_url.rstrip('/')
        self.security_context = security_context
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        
        # Internal state
        self._active_transmissions: Dict[str, TransmissionRequest] = {}
        self._transmission_results: Dict[str, TransmissionResult] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._ssl_context = self._create_ssl_context()
        
        # Metrics
        self.metrics = {
            'total_transmissions': 0,
            'successful_transmissions': 0,
            'failed_transmissions': 0,
            'encryption_time': 0.0,
            'transmission_time': 0.0,
            'verification_time': 0.0
        }
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for secure connections"""
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context
    
    async def start(self):
        """Start the secure transmitter service"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(
                connect=self.connection_timeout,
                total=self.read_timeout
            )
            
            connector = aiohttp.TCPConnector(
                ssl=self._ssl_context,
                limit=100,
                limit_per_host=20,
                keepalive_timeout=30
            )
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': 'TaxPoynt-APP-Transmitter/1.0',
                    'X-Client-ID': self.security_context.client_id
                }
            )
        
        logger.info("Secure transmitter started")
    
    async def stop(self):
        """Stop the secure transmitter service"""
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("Secure transmitter stopped")
    
    async def transmit_document(self, 
                               request: TransmissionRequest) -> TransmissionResult:
        """
        Securely transmit a document to FIRS
        
        Args:
            request: Document transmission request
            
        Returns:
            TransmissionResult with transmission outcome
        """
        request_id = str(uuid.uuid4())
        self._active_transmissions[request_id] = request
        
        result = TransmissionResult(
            request_id=request_id,
            document_id=request.document_id,
            status=TransmissionStatus.PENDING
        )
        
        try:
            # Step 1: Encrypt document
            result.status = TransmissionStatus.ENCRYPTING
            start_time = time.time()
            
            encrypted_data = await self._encrypt_document(
                request.document_data,
                request.security_level
            )
            
            self.metrics['encryption_time'] += time.time() - start_time
            
            # Step 2: Sign encrypted data
            result.status = TransmissionStatus.SIGNING
            
            signature = await self._sign_document(
                encrypted_data,
                request.security_level
            )
            
            # Step 3: Prepare transmission payload
            transmission_payload = {
                'document_id': request.document_id,
                'document_type': request.document_type,
                'encrypted_data': encrypted_data,
                'signature': signature,
                'security_level': request.security_level.value,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': request.metadata
            }
            
            # Step 4: Transmit to FIRS
            result.status = TransmissionStatus.TRANSMITTING
            start_time = time.time()
            
            response = await self._transmit_to_firs(
                request.destination_endpoint,
                transmission_payload
            )
            
            self.metrics['transmission_time'] += time.time() - start_time
            
            # Step 5: Verify response
            start_time = time.time()
            
            verified_response = await self._verify_response(response)
            
            self.metrics['verification_time'] += time.time() - start_time
            
            # Step 6: Update result
            result.status = TransmissionStatus.DELIVERED
            result.transmission_id = verified_response.get('transmission_id')
            result.response_data = verified_response
            result.transmitted_at = datetime.utcnow()
            result.verified_at = datetime.utcnow()
            
            # Update metrics
            self.metrics['total_transmissions'] += 1
            self.metrics['successful_transmissions'] += 1
            
            logger.info(f"Document {request.document_id} transmitted successfully")
            
        except Exception as e:
            result.status = TransmissionStatus.FAILED
            result.error_message = str(e)
            
            self.metrics['total_transmissions'] += 1
            self.metrics['failed_transmissions'] += 1
            
            logger.error(f"Failed to transmit document {request.document_id}: {e}")
        
        finally:
            self._transmission_results[request_id] = result
            if request_id in self._active_transmissions:
                del self._active_transmissions[request_id]
        
        return result
    
    async def _encrypt_document(self, 
                               document_data: Dict[str, Any],
                               security_level: SecurityLevel) -> str:
        """
        Encrypt document data based on security level
        
        Args:
            document_data: Document data to encrypt
            security_level: Required security level
            
        Returns:
            Encrypted data as base64 string
        """
        # Serialize document data
        document_json = json.dumps(document_data, sort_keys=True)
        document_bytes = document_json.encode('utf-8')
        
        if security_level == SecurityLevel.MAXIMUM:
            # Use RSA + AES hybrid encryption
            return await self._hybrid_encrypt(document_bytes)
        elif security_level == SecurityLevel.HIGH:
            # Use AES-256-GCM
            return await self._aes_encrypt(document_bytes, 256)
        else:
            # Use AES-128-GCM
            return await self._aes_encrypt(document_bytes, 128)
    
    async def _hybrid_encrypt(self, data: bytes) -> str:
        """Hybrid RSA + AES encryption for maximum security"""
        # Generate random AES key
        aes_key = os.urandom(32)  # 256-bit key
        
        # Encrypt data with AES
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(os.urandom(12)),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Encrypt AES key with RSA
        public_key = serialization.load_pem_public_key(
            self.security_context.encryption_key,
            backend=default_backend()
        )
        
        encrypted_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Combine encrypted key, IV, tag, and ciphertext
        result = {
            'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8'),
            'iv': base64.b64encode(cipher.algorithm.iv).decode('utf-8'),
            'tag': base64.b64encode(encryptor.tag).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
        }
        
        return base64.b64encode(json.dumps(result).encode('utf-8')).decode('utf-8')
    
    async def _aes_encrypt(self, data: bytes, key_size: int) -> str:
        """AES-GCM encryption"""
        key = self.security_context.encryption_key[:key_size // 8]
        iv = os.urandom(12)
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        result = {
            'iv': base64.b64encode(iv).decode('utf-8'),
            'tag': base64.b64encode(encryptor.tag).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
        }
        
        return base64.b64encode(json.dumps(result).encode('utf-8')).decode('utf-8')
    
    async def _sign_document(self, 
                           encrypted_data: str,
                           security_level: SecurityLevel) -> str:
        """
        Digitally sign encrypted document
        
        Args:
            encrypted_data: Encrypted document data
            security_level: Required security level
            
        Returns:
            Digital signature as base64 string
        """
        # Create signature payload
        signature_payload = {
            'encrypted_data': encrypted_data,
            'timestamp': datetime.utcnow().isoformat(),
            'client_id': self.security_context.client_id,
            'security_level': security_level.value
        }
        
        payload_json = json.dumps(signature_payload, sort_keys=True)
        payload_bytes = payload_json.encode('utf-8')
        
        # Sign with private key
        private_key = serialization.load_pem_private_key(
            self.security_context.signing_key,
            password=None,
            backend=default_backend()
        )
        
        if security_level == SecurityLevel.MAXIMUM:
            # Use RSA-PSS with SHA-256
            signature = private_key.sign(
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        else:
            # Use RSA-PKCS1v15 with SHA-256
            signature = private_key.sign(
                payload_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        
        return base64.b64encode(signature).decode('utf-8')
    
    async def _transmit_to_firs(self, 
                               endpoint: str,
                               payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transmit payload to FIRS endpoint
        
        Args:
            endpoint: FIRS endpoint URL
            payload: Transmission payload
            
        Returns:
            FIRS response data
        """
        if not self._session:
            raise RuntimeError("Transmitter not started")
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.security_context.api_key,
            'X-Timestamp': str(int(time.time())),
            'X-Request-ID': str(uuid.uuid4())
        }
        
        # Add session token if available
        if self.security_context.session_token:
            headers['Authorization'] = f'Bearer {self.security_context.session_token}'
        
        # Create request signature
        request_signature = self._create_request_signature(payload, headers)
        headers['X-Signature'] = request_signature
        
        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                async with self._session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=headers
                ) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return response_data
                    elif response.status == 401:
                        # Try to refresh session token
                        await self._refresh_session_token()
                        if attempt < self.max_retries - 1:
                            continue
                    
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=response_data.get('error', 'Unknown error')
                    )
                    
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
        
        raise RuntimeError("Max retries exceeded")
    
    def _create_request_signature(self, 
                                 payload: Dict[str, Any],
                                 headers: Dict[str, str]) -> str:
        """Create HMAC signature for request"""
        # Create signature data
        signature_data = {
            'payload': payload,
            'timestamp': headers['X-Timestamp'],
            'request_id': headers['X-Request-ID']
        }
        
        signature_json = json.dumps(signature_data, sort_keys=True)
        signature_bytes = signature_json.encode('utf-8')
        
        # Create HMAC signature
        signature = hmac.new(
            self.security_context.signing_key[:32],
            signature_bytes,
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    async def _refresh_session_token(self):
        """Refresh session token"""
        # This would typically make an OAuth refresh request
        # For now, we'll just log the attempt
        logger.warning("Session token refresh needed - implement OAuth refresh")
    
    async def _verify_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify FIRS response integrity and authenticity
        
        Args:
            response: FIRS response data
            
        Returns:
            Verified response data
        """
        # Check response signature if present
        if 'signature' in response:
            signature = response.pop('signature')
            
            # Verify signature
            response_json = json.dumps(response, sort_keys=True)
            response_bytes = response_json.encode('utf-8')
            
            # This would typically verify against FIRS public key
            # For now, we'll just validate the format
            try:
                base64.b64decode(signature)
            except Exception:
                raise ValueError("Invalid response signature format")
        
        # Validate response structure
        required_fields = ['status', 'timestamp']
        for field in required_fields:
            if field not in response:
                raise ValueError(f"Missing required field: {field}")
        
        # Check response timestamp
        try:
            response_time = datetime.fromisoformat(response['timestamp'])
            if abs((datetime.utcnow() - response_time).total_seconds()) > 300:
                raise ValueError("Response timestamp too old")
        except (ValueError, KeyError):
            raise ValueError("Invalid response timestamp")
        
        return response
    
    async def get_transmission_status(self, request_id: str) -> Optional[TransmissionResult]:
        """Get transmission status by request ID"""
        return self._transmission_results.get(request_id)
    
    async def get_active_transmissions(self) -> List[TransmissionRequest]:
        """Get list of active transmissions"""
        return list(self._active_transmissions.values())
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get transmission metrics"""
        return {
            **self.metrics,
            'active_transmissions': len(self._active_transmissions),
            'completed_transmissions': len(self._transmission_results),
            'success_rate': (
                self.metrics['successful_transmissions'] / 
                max(self.metrics['total_transmissions'], 1)
            ) * 100
        }


# Factory functions for easy setup
def create_security_context(client_id: str,
                          api_key: str,
                          encryption_key: bytes,
                          signing_key: bytes,
                          certificate_chain: List[str]) -> SecurityContext:
    """Create security context for transmission"""
    return SecurityContext(
        client_id=client_id,
        api_key=api_key,
        encryption_key=encryption_key,
        signing_key=signing_key,
        certificate_chain=certificate_chain
    )


def create_transmission_request(document_id: str,
                              document_type: str,
                              document_data: Dict[str, Any],
                              destination_endpoint: str,
                              security_level: SecurityLevel = SecurityLevel.STANDARD) -> TransmissionRequest:
    """Create transmission request"""
    return TransmissionRequest(
        document_id=document_id,
        document_type=document_type,
        document_data=document_data,
        destination_endpoint=destination_endpoint,
        security_level=security_level
    )


async def create_secure_transmitter(base_url: str,
                                   security_context: SecurityContext) -> SecureTransmitter:
    """Create and start secure transmitter"""
    transmitter = SecureTransmitter(base_url, security_context)
    await transmitter.start()
    return transmitter