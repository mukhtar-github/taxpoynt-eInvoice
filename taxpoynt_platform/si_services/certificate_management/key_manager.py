"""
Key Manager

Handles cryptographic key management for System Integrator role.
Provides key generation, storage, rotation, and secure operations.
"""

import os
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64


class KeyManager:
    """Manage cryptographic keys for certificate operations"""
    
    def __init__(self, key_storage_path: Optional[str] = None):
        self.key_storage_path = key_storage_path or "/tmp/keys"
        self.default_key_size = 2048
        self.logger = logging.getLogger(__name__)
        
        # Ensure key storage directory exists
        os.makedirs(self.key_storage_path, exist_ok=True)
    
    def generate_rsa_key_pair(
        self,
        key_size: Optional[int] = None,
        public_exponent: int = 65537
    ) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair
        
        Args:
            key_size: Key size in bits
            public_exponent: Public exponent for key generation
            
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        try:
            key_size = key_size or self.default_key_size
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=public_exponent,
                key_size=key_size,
                backend=default_backend()
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize to PEM format
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            self.logger.info(f"Generated RSA key pair with {key_size} bits")
            
            return private_key_pem, public_key_pem
            
        except Exception as e:
            self.logger.error(f"Error generating RSA key pair: {str(e)}")
            raise
    
    def generate_encrypted_key_pair(
        self,
        passphrase: str,
        key_size: Optional[int] = None
    ) -> Tuple[bytes, bytes]:
        """
        Generate encrypted RSA key pair
        
        Args:
            passphrase: Passphrase for key encryption
            key_size: Key size in bits
            
        Returns:
            Tuple of (encrypted_private_key_pem, public_key_pem)
        """
        try:
            key_size = key_size or self.default_key_size
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Encrypt private key with passphrase
            encrypted_private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode())
            )
            
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            self.logger.info(f"Generated encrypted RSA key pair with {key_size} bits")
            
            return encrypted_private_key_pem, public_key_pem
            
        except Exception as e:
            self.logger.error(f"Error generating encrypted key pair: {str(e)}")
            raise
    
    def store_key(
        self,
        key_data: bytes,
        key_name: str,
        key_type: str = "private",
        encrypted: bool = False
    ) -> str:
        """
        Store key to secure storage
        
        Args:
            key_data: Key data in PEM format
            key_name: Name for the key
            key_type: Type of key (private, public, certificate)
            encrypted: Whether the key is encrypted
            
        Returns:
            Path to stored key file
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = "key" if key_type == "private" else "pub" if key_type == "public" else "crt"
            filename = f"{key_name}_{key_type}_{timestamp}.{extension}"
            
            if encrypted:
                filename = f"encrypted_{filename}"
            
            key_path = os.path.join(self.key_storage_path, filename)
            
            # Write key to file with secure permissions
            with open(key_path, 'wb') as key_file:
                key_file.write(key_data)
            
            # Set secure file permissions (read/write for owner only)
            os.chmod(key_path, 0o600)
            
            self.logger.info(f"Stored {key_type} key: {filename}")
            
            return key_path
            
        except Exception as e:
            self.logger.error(f"Error storing key: {str(e)}")
            raise
    
    def load_key(self, key_path: str, passphrase: Optional[str] = None) -> bytes:
        """
        Load key from storage
        
        Args:
            key_path: Path to key file
            passphrase: Passphrase for encrypted keys
            
        Returns:
            Key data in PEM format
        """
        try:
            if not os.path.exists(key_path):
                raise FileNotFoundError(f"Key file not found: {key_path}")
            
            with open(key_path, 'rb') as key_file:
                key_data = key_file.read()
            
            # If passphrase provided, verify key can be loaded
            if passphrase:
                try:
                    serialization.load_pem_private_key(
                        key_data,
                        password=passphrase.encode(),
                        backend=default_backend()
                    )
                except Exception as e:
                    raise ValueError(f"Invalid passphrase for encrypted key: {str(e)}")
            
            self.logger.info(f"Loaded key from: {key_path}")
            
            return key_data
            
        except Exception as e:
            self.logger.error(f"Error loading key: {str(e)}")
            raise
    
    def rotate_key_pair(
        self,
        old_key_name: str,
        new_key_name: str,
        key_size: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Rotate key pair (generate new, archive old)
        
        Args:
            old_key_name: Name of key to rotate
            new_key_name: Name for new key
            key_size: Size for new key
            
        Returns:
            Tuple of (new_private_key_path, new_public_key_path)
        """
        try:
            # Generate new key pair
            private_key_pem, public_key_pem = self.generate_rsa_key_pair(key_size)
            
            # Store new keys
            private_key_path = self.store_key(private_key_pem, new_key_name, "private")
            public_key_path = self.store_key(public_key_pem, new_key_name, "public")
            
            # Archive old keys (if they exist)
            self._archive_old_keys(old_key_name)
            
            self.logger.info(f"Rotated key pair: {old_key_name} -> {new_key_name}")
            
            return private_key_path, public_key_path
            
        except Exception as e:
            self.logger.error(f"Error rotating key pair: {str(e)}")
            raise
    
    def encrypt_data(self, data: bytes, public_key_pem: bytes) -> bytes:
        """
        Encrypt data using RSA public key
        
        Args:
            data: Data to encrypt
            public_key_pem: Public key in PEM format
            
        Returns:
            Encrypted data
        """
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=default_backend()
            )
            
            # Encrypt data
            encrypted_data = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return encrypted_data
            
        except Exception as e:
            self.logger.error(f"Error encrypting data: {str(e)}")
            raise
    
    def decrypt_data(
        self,
        encrypted_data: bytes,
        private_key_pem: bytes,
        passphrase: Optional[str] = None
    ) -> bytes:
        """
        Decrypt data using RSA private key
        
        Args:
            encrypted_data: Data to decrypt
            private_key_pem: Private key in PEM format
            passphrase: Passphrase for encrypted private key
            
        Returns:
            Decrypted data
        """
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=passphrase.encode() if passphrase else None,
                backend=default_backend()
            )
            
            # Decrypt data
            decrypted_data = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Error decrypting data: {str(e)}")
            raise
    
    def generate_symmetric_key(self, key_length: int = 32) -> bytes:
        """
        Generate symmetric key for bulk encryption
        
        Args:
            key_length: Key length in bytes (32 for AES-256)
            
        Returns:
            Symmetric key
        """
        return secrets.token_bytes(key_length)
    
    def derive_key_from_password(
        self,
        password: str,
        salt: Optional[bytes] = None,
        key_length: int = 32,
        iterations: int = 100000
    ) -> Tuple[bytes, bytes]:
        """
        Derive key from password using PBKDF2
        
        Args:
            password: Password to derive from
            salt: Salt for key derivation (generated if not provided)
            key_length: Derived key length
            iterations: Number of iterations
            
        Returns:
            Tuple of (derived_key, salt)
        """
        try:
            if salt is None:
                salt = secrets.token_bytes(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=key_length,
                salt=salt,
                iterations=iterations,
                backend=default_backend()
            )
            
            derived_key = kdf.derive(password.encode())
            
            return derived_key, salt
            
        except Exception as e:
            self.logger.error(f"Error deriving key from password: {str(e)}")
            raise
    
    def list_stored_keys(self) -> List[Dict[str, Any]]:
        """List all stored keys"""
        try:
            keys = []
            
            for filename in os.listdir(self.key_storage_path):
                if filename.endswith(('.key', '.pub', '.crt')):
                    key_path = os.path.join(self.key_storage_path, filename)
                    stat = os.stat(key_path)
                    
                    keys.append({
                        'filename': filename,
                        'path': key_path,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'is_encrypted': filename.startswith('encrypted_')
                    })
            
            return sorted(keys, key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing stored keys: {str(e)}")
            return []
    
    def _archive_old_keys(self, key_name: str):
        """Archive old keys by moving to archive directory"""
        try:
            archive_dir = os.path.join(self.key_storage_path, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            
            # Find and move old keys
            for filename in os.listdir(self.key_storage_path):
                if filename.startswith(key_name) and not filename.startswith("archive"):
                    old_path = os.path.join(self.key_storage_path, filename)
                    new_path = os.path.join(archive_dir, f"archived_{filename}")
                    
                    os.rename(old_path, new_path)
                    self.logger.info(f"Archived old key: {filename}")
                    
        except Exception as e:
            self.logger.warning(f"Error archiving old keys: {str(e)}")
    
    def validate_key_strength(self, private_key_pem: bytes) -> Dict[str, Any]:
        """
        Validate key strength and security
        
        Args:
            private_key_pem: Private key to validate
            
        Returns:
            Validation results
        """
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=default_backend()
            )
            
            key_size = private_key.key_size
            public_exponent = private_key.public_key().public_numbers().e
            
            # Security assessment
            is_strong = key_size >= 2048
            is_secure_exponent = public_exponent == 65537
            
            return {
                'key_size': key_size,
                'public_exponent': public_exponent,
                'is_strong': is_strong,
                'is_secure_exponent': is_secure_exponent,
                'security_level': 'strong' if is_strong and is_secure_exponent else 'weak',
                'recommendations': [] if is_strong and is_secure_exponent else [
                    'Use at least 2048-bit keys' if not is_strong else '',
                    'Use public exponent 65537' if not is_secure_exponent else ''
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error validating key strength: {str(e)}")
            raise