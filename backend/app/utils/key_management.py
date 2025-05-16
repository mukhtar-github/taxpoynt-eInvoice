"""
Key management utilities for FIRS e-Invoice system.

This module provides comprehensive key management functions for:
- Key generation (RSA, Ed25519)
- Key storage and retrieval
- Key rotation
- Certificate management
- Secure key handling
"""

import os
import base64
import logging
import secrets
import datetime
from pathlib import Path
from typing import Dict, Tuple, Union, Optional, Any, List

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa, ed25519
from cryptography.exceptions import InvalidSignature
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Key Management System for cryptographic operations in the FIRS e-Invoice system.
    
    This class handles all aspects of key lifecycle:
    - Generation: Creating new signing and encryption keys
    - Storage: Securely storing keys with proper permissions
    - Retrieval: Loading keys for cryptographic operations
    - Rotation: Managing key lifecycle and rotation schedules
    - Backup: Creating secure backups of critical keys
    """
    
    KEY_TYPES = ["signing", "encryption", "verification"]
    KEY_ALGORITHMS = ["rsa-2048", "rsa-4096", "ed25519"]
    
    def __init__(
        self,
        keys_dir: Optional[str] = None,
        key_password: Optional[str] = None
    ):
        """
        Initialize the Key Manager.
        
        Args:
            keys_dir: Directory for key storage
            key_password: Password for key encryption
        """
        self.keys_dir = keys_dir or os.environ.get(
            "KEYS_DIRECTORY", 
            settings.KEYS_DIRECTORY if hasattr(settings, "KEYS_DIRECTORY") else None
        )
        
        if not self.keys_dir:
            self.keys_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../keys")
        
        # Ensure keys directory exists
        Path(self.keys_dir).mkdir(parents=True, exist_ok=True)
        
        # Password for encrypting private keys
        self.key_password = key_password or os.environ.get(
            "KEY_PASSWORD", 
            settings.KEY_PASSWORD if hasattr(settings, "KEY_PASSWORD") else None
        )
    
    def generate_key_pair(
        self, 
        key_type: str, 
        algorithm: str = "rsa-2048",
        key_name: Optional[str] = None,
        overwrite: bool = False
    ) -> Tuple[str, str]:
        """
        Generate a new key pair (private and public keys).
        
        Args:
            key_type: Type of key (signing, encryption, verification)
            algorithm: Key algorithm and size (rsa-2048, rsa-4096, ed25519)
            key_name: Custom name for the key files
            overwrite: Whether to overwrite existing keys
            
        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        if key_type not in self.KEY_TYPES:
            raise ValueError(f"Invalid key type. Must be one of: {', '.join(self.KEY_TYPES)}")
        
        if algorithm not in self.KEY_ALGORITHMS:
            raise ValueError(f"Invalid algorithm. Must be one of: {', '.join(self.KEY_ALGORITHMS)}")
        
        # Generate a default key name if not provided
        if not key_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            key_name = f"{key_type}_{algorithm}_{timestamp}"
        
        private_key_path = os.path.join(self.keys_dir, f"{key_name}.key")
        public_key_path = os.path.join(self.keys_dir, f"{key_name}.pub")
        
        # Check if files already exist
        if not overwrite and (os.path.exists(private_key_path) or os.path.exists(public_key_path)):
            raise FileExistsError(f"Key files already exist for {key_name}")
        
        # Generate the key pair based on algorithm
        if algorithm.startswith("rsa"):
            key_size = int(algorithm.split("-")[1])
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Serialize the private key with password encryption if available
            encryption = serialization.BestAvailableEncryption(self.key_password.encode()) if self.key_password else serialization.NoEncryption()
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption
            )
            
            # Serialize the public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        
        elif algorithm == "ed25519":
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Serialize the private key
            encryption = serialization.BestAvailableEncryption(self.key_password.encode()) if self.key_password else serialization.NoEncryption()
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption
            )
            
            # Serialize the public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Write the keys to files with secure permissions
        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        os.chmod(private_key_path, 0o600)  # Read/write for owner only
        
        with open(public_key_path, 'wb') as f:
            f.write(public_pem)
        os.chmod(public_key_path, 0o644)  # Read for all, write for owner
        
        logger.info(f"Generated {algorithm} key pair: {key_name}")
        return private_key_path, public_key_path
    
    def load_private_key(self, key_path: str, password: Optional[str] = None) -> Any:
        """
        Load a private key from file.
        
        Args:
            key_path: Path to the private key file
            password: Password to decrypt the key (if needed)
            
        Returns:
            Private key object
        """
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Private key file not found: {key_path}")
        
        try:
            with open(key_path, "rb") as key_file:
                key_data = key_file.read()
                
            pw = (password or self.key_password).encode() if (password or self.key_password) else None
            return serialization.load_pem_private_key(
                key_data,
                password=pw,
                backend=default_backend()
            )
        except Exception as e:
            logger.error(f"Failed to load private key: {str(e)}")
            raise ValueError(f"Failed to load private key: {str(e)}")
    
    def load_public_key(self, key_path: str) -> Any:
        """
        Load a public key from file.
        
        Args:
            key_path: Path to the public key file
            
        Returns:
            Public key object
        """
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Public key file not found: {key_path}")
        
        try:
            with open(key_path, "rb") as key_file:
                key_data = key_file.read()
                
            return serialization.load_pem_public_key(
                key_data,
                backend=default_backend()
            )
        except Exception as e:
            logger.error(f"Failed to load public key: {str(e)}")
            raise ValueError(f"Failed to load public key: {str(e)}")
    
    def generate_certificate(
        self,
        private_key_path: str,
        subject_name: Dict[str, str],
        valid_days: int = 365,
        cert_name: Optional[str] = None
    ) -> str:
        """
        Generate a self-signed X.509 certificate.
        
        Args:
            private_key_path: Path to private key file
            subject_name: Certificate subject information (org, common name, etc.)
            valid_days: Certificate validity period in days
            cert_name: Optional custom name for certificate file
            
        Returns:
            Path to the generated certificate file
        """
        private_key = self.load_private_key(private_key_path)
        
        # Build certificate subject
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, subject_name.get("country", "NG")),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, subject_name.get("state", "")),
            x509.NameAttribute(NameOID.LOCALITY_NAME, subject_name.get("locality", "")),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, subject_name.get("organization", "TaxPoynt")),
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name.get("common_name", "taxpoynt.com"))
        ])
        
        # Certificate validity period
        now = datetime.datetime.utcnow()
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            subject
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now
        ).not_valid_after(
            now + datetime.timedelta(days=valid_days)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Determine certificate filename
        if not cert_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            cert_name = f"cert_{timestamp}.crt"
        
        cert_path = os.path.join(self.keys_dir, cert_name)
        
        # Write certificate to file
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        logger.info(f"Generated self-signed certificate: {cert_name}")
        return cert_path
    
    def load_certificate(self, cert_path: str) -> x509.Certificate:
        """
        Load an X.509 certificate from file.
        
        Args:
            cert_path: Path to certificate file
            
        Returns:
            Certificate object
        """
        if not os.path.exists(cert_path):
            raise FileNotFoundError(f"Certificate file not found: {cert_path}")
        
        try:
            with open(cert_path, "rb") as cert_file:
                cert_data = cert_file.read()
            
            return x509.load_pem_x509_certificate(cert_data, default_backend())
        except Exception as e:
            logger.error(f"Failed to load certificate: {str(e)}")
            raise ValueError(f"Failed to load certificate: {str(e)}")
    
    def list_keys(self, key_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available keys in the keys directory.
        
        Args:
            key_type: Optional filter by key type
            
        Returns:
            List of key information dictionaries
        """
        keys = []
        
        for filename in os.listdir(self.keys_dir):
            file_path = os.path.join(self.keys_dir, filename)
            
            # Skip directories and non-key files
            if os.path.isdir(file_path) or not (filename.endswith('.key') or filename.endswith('.pub') or filename.endswith('.crt')):
                continue
            
            key_info = self._parse_key_filename(filename)
            
            # Filter by key type if specified
            if key_type and key_info.get('type') != key_type:
                continue
            
            # Add file information
            key_info['path'] = file_path
            key_info['size'] = os.path.getsize(file_path)
            key_info['last_modified'] = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            
            keys.append(key_info)
        
        return keys
    
    def _parse_key_filename(self, filename: str) -> Dict[str, str]:
        """
        Parse information from a key filename.
        
        Args:
            filename: Key filename
            
        Returns:
            Dictionary with key information
        """
        name, ext = os.path.splitext(filename)
        
        key_info = {
            'filename': filename,
            'extension': ext[1:],  # Remove the leading dot
            'full_name': name
        }
        
        # Try to parse structured filenames (type_algorithm_timestamp)
        parts = name.split('_')
        if len(parts) >= 3:
            key_info['type'] = parts[0]
            key_info['algorithm'] = parts[1]
            key_info['timestamp'] = '_'.join(parts[2:])  # Join remaining parts in case of underscores in timestamp
        
        return key_info
    
    def rotate_key(self, key_path: str, valid_days: int = 365) -> Tuple[str, str]:
        """
        Rotate a key by generating a new one and archiving the old one.
        
        Args:
            key_path: Path to the key to rotate
            valid_days: Validity period for new certificate (if applicable)
            
        Returns:
            Tuple of (new_key_path, archive_path)
        """
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Key file not found: {key_path}")
        
        # Parse key information
        filename = os.path.basename(key_path)
        key_info = self._parse_key_filename(filename)
        
        # Determine if this is a private key
        is_private = key_path.endswith('.key')
        
        # Find corresponding public key if this is a private key
        public_key_path = None
        if is_private:
            public_key_path = key_path[:-4] + '.pub'
            if not os.path.exists(public_key_path):
                logger.warning(f"No corresponding public key found for {key_path}")
                public_key_path = None
        
        # Generate a new key pair
        if key_info.get('type') and key_info.get('algorithm'):
            new_key_name = f"{key_info['type']}_{key_info['algorithm']}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            new_private_key_path, new_public_key_path = self.generate_key_pair(
                key_type=key_info['type'],
                algorithm=key_info['algorithm'],
                key_name=new_key_name
            )
            
            # Archive the old key(s)
            archive_dir = os.path.join(self.keys_dir, "archive")
            Path(archive_dir).mkdir(parents=True, exist_ok=True)
            
            archive_path = os.path.join(archive_dir, filename)
            os.rename(key_path, archive_path)
            
            if public_key_path and os.path.exists(public_key_path):
                public_archive_path = os.path.join(archive_dir, os.path.basename(public_key_path))
                os.rename(public_key_path, public_archive_path)
            
            logger.info(f"Rotated key: {filename} -> {os.path.basename(new_private_key_path)}")
            return new_private_key_path, archive_path
        else:
            raise ValueError(f"Cannot determine key type and algorithm from filename: {filename}")
    
    def backup_keys(self, backup_dir: Optional[str] = None) -> str:
        """
        Create a backup of all keys.
        
        Args:
            backup_dir: Directory to store backup (default: keys_dir/backup)
            
        Returns:
            Path to backup directory
        """
        if not backup_dir:
            backup_dir = os.path.join(self.keys_dir, "backup", datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        for filename in os.listdir(self.keys_dir):
            file_path = os.path.join(self.keys_dir, filename)
            
            # Skip directories and non-key files
            if os.path.isdir(file_path):
                continue
            
            # Copy the file to backup directory
            backup_path = os.path.join(backup_dir, filename)
            with open(file_path, "rb") as src, open(backup_path, "wb") as dst:
                dst.write(src.read())
            
            # Maintain the same permissions
            os.chmod(backup_path, os.stat(file_path).st_mode)
        
        logger.info(f"Created backup of all keys in {backup_dir}")
        return backup_dir


# Create a singleton instance for easy import
key_manager = KeyManager()


def get_key_manager() -> KeyManager:
    """
    Get or create the key manager instance.
    
    Returns:
        KeyManager instance
    """
    return key_manager
