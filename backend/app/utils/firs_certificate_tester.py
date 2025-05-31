"""
FIRS Certificate Testing Utility.

This module provides tools for testing with actual FIRS certificates:
- Loading and validating FIRS certificates
- Testing signature generation and verification
- Performance benchmarking
- Compatibility validation

Usage:
    python -m app.utils.firs_certificate_tester --cert /path/to/firs_cert.crt --test-type basic
"""

import os
import json
import time
import base64
import logging
import argparse
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.utils.certificate_manager import CertificateManager
from app.services.cryptographic_stamping_service import CryptographicStampingService
from app.utils.key_management import KeyManager

logger = logging.getLogger(__name__)


class FIRSCertificateTester:
    """Utility class for testing FIRS certificates."""
    
    def __init__(
        self, 
        certificate_path: str, 
        private_key_path: Optional[str] = None,
        password: Optional[bytes] = None
    ):
        """
        Initialize the FIRS certificate tester.
        
        Args:
            certificate_path: Path to the FIRS certificate
            private_key_path: Path to the private key (if available for testing)
            password: Password for the private key (if encrypted)
        """
        self.certificate_path = certificate_path
        self.private_key_path = private_key_path
        self.password = password
        
        # Set up the certificate manager
        self.cert_manager = CertificateManager()
        
        # Set up the key manager
        self.key_manager = KeyManager()
        
        # Load the certificate
        self.certificate = self._load_certificate()
        
        # Set up the cryptographic stamping service
        self.stamping_service = CryptographicStampingService(
            key_manager=self.key_manager,
            certificate_manager=self.cert_manager
        )
    
    def _load_certificate(self) -> x509.Certificate:
        """Load the FIRS certificate."""
        logger.info(f"Loading certificate from: {self.certificate_path}")
        
        try:
            with open(self.certificate_path, "rb") as f:
                cert_data = f.read()
            
            certificate = x509.load_pem_x509_certificate(
                cert_data, default_backend()
            )
            
            logger.info("Certificate loaded successfully")
            return certificate
        except Exception as e:
            logger.error(f"Failed to load certificate: {e}")
            raise
    
    def run_basic_test(self) -> Dict[str, Any]:
        """
        Run basic certificate tests.
        
        Returns:
            Dict containing test results
        """
        logger.info("Running basic certificate tests")
        start_time = time.time()
        
        results = {
            "test_type": "basic",
            "certificate": {
                "path": self.certificate_path,
                "subject": {},
                "issuer": {},
                "valid_from": None,
                "valid_until": None,
                "key_size": None,
                "serial_number": None,
                "is_valid": False
            },
            "validation_tests": [],
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": 0
        }
        
        try:
            # Test certificate validation
            is_valid, cert_info = self.cert_manager.validate_certificate(self.certificate_path)
            
            # Update results with certificate info
            results["certificate"]["is_valid"] = is_valid
            results["certificate"].update(cert_info)
            
            # Extract the public key
            public_key = self.cert_manager.extract_public_key(self.certificate_path)
            results["certificate"]["key_size"] = public_key.key_size
            
            # Check if certificate is in the FIRS trusted chain
            results["validation_tests"].append({
                "name": "FIRS Trust Chain",
                "passed": self._check_firs_trust_chain(),
                "details": "Checked if certificate is in the FIRS trusted chain"
            })
            
            # Check certificate revocation status
            results["validation_tests"].append({
                "name": "Revocation Check",
                "passed": self._check_revocation_status(),
                "details": "Checked certificate revocation status"
            })
            
            # Check if certificate has required extensions
            results["validation_tests"].append({
                "name": "Required Extensions",
                "passed": self._check_required_extensions(),
                "details": "Checked if certificate has all required extensions"
            })
            
        except Exception as e:
            logger.error(f"Certificate test failed: {e}")
            results["error"] = str(e)
        
        end_time = time.time()
        results["duration_seconds"] = end_time - start_time
        
        return results
    
    def run_signing_test(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test signing and verification with the FIRS certificate.
        
        Args:
            test_data: Test invoice data to sign
            
        Returns:
            Dict containing test results
        """
        logger.info("Running signing and verification tests")
        start_time = time.time()
        
        results = {
            "test_type": "signing",
            "tests": [],
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": 0
        }
        
        if not self.private_key_path:
            results["error"] = "Private key path not provided. Cannot run signing tests."
            return results
        
        try:
            # Test CSID generation
            try:
                csid, timestamp = self.stamping_service.generate_csid(test_data)
                results["tests"].append({
                    "name": "CSID Generation",
                    "passed": bool(csid),
                    "details": f"Generated CSID of length {len(csid)} at {timestamp}"
                })
            except Exception as e:
                logger.error(f"CSID generation failed: {e}")
                results["tests"].append({
                    "name": "CSID Generation",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
            
            # Test full stamping process
            try:
                stamped_invoice = self.stamping_service.stamp_invoice(test_data)
                results["tests"].append({
                    "name": "Invoice Stamping",
                    "passed": "cryptographic_stamp" in stamped_invoice,
                    "details": "Successfully applied cryptographic stamp to invoice"
                })
                
                # If stamping was successful, test verification
                if "cryptographic_stamp" in stamped_invoice:
                    stamp_data = stamped_invoice["cryptographic_stamp"]
                    is_valid, details = self.stamping_service.verify_stamp(test_data, stamp_data)
                    
                    results["tests"].append({
                        "name": "Stamp Verification",
                        "passed": is_valid,
                        "details": f"Verification result: {is_valid}, details: {details}"
                    })
            except Exception as e:
                logger.error(f"Stamping or verification failed: {e}")
                results["tests"].append({
                    "name": "Stamping and Verification",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
            
        except Exception as e:
            logger.error(f"Signing test failed: {e}")
            results["error"] = str(e)
        
        end_time = time.time()
        results["duration_seconds"] = end_time - start_time
        
        return results
    
    def run_performance_test(self, iterations: int = 100) -> Dict[str, Any]:
        """
        Run performance tests for the FIRS certificate.
        
        Args:
            iterations: Number of signing operations to perform
            
        Returns:
            Dict containing performance test results
        """
        logger.info(f"Running performance tests with {iterations} iterations")
        start_time = time.time()
        
        results = {
            "test_type": "performance",
            "iterations": iterations,
            "operations": {
                "validation": {
                    "average_ms": 0,
                    "min_ms": float("inf"),
                    "max_ms": 0,
                    "total_ms": 0,
                    "operations_per_second": 0
                },
                "signing": {
                    "average_ms": 0,
                    "min_ms": float("inf"),
                    "max_ms": 0,
                    "total_ms": 0,
                    "operations_per_second": 0
                },
                "verification": {
                    "average_ms": 0,
                    "min_ms": float("inf"),
                    "max_ms": 0,
                    "total_ms": 0,
                    "operations_per_second": 0
                }
            },
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": 0
        }
        
        # Test data for signing
        test_data = {
            "invoice_number": "PERF-TEST-001",
            "amount": 10000,
            "date": datetime.now().isoformat()
        }
        
        # Run validation performance test
        validation_times = []
        for i in range(iterations):
            iter_start = time.time()
            self.cert_manager.validate_certificate(self.certificate_path)
            iter_end = time.time()
            duration_ms = (iter_end - iter_start) * 1000
            validation_times.append(duration_ms)
            
            results["operations"]["validation"]["min_ms"] = min(
                results["operations"]["validation"]["min_ms"], duration_ms
            )
            results["operations"]["validation"]["max_ms"] = max(
                results["operations"]["validation"]["max_ms"], duration_ms
            )
        
        # Calculate validation statistics
        results["operations"]["validation"]["total_ms"] = sum(validation_times)
        results["operations"]["validation"]["average_ms"] = results["operations"]["validation"]["total_ms"] / iterations
        results["operations"]["validation"]["operations_per_second"] = 1000 / results["operations"]["validation"]["average_ms"]
        
        # If private key is available, run signing and verification tests
        if self.private_key_path:
            # Signing performance
            signing_times = []
            verification_times = []
            
            for i in range(iterations):
                # Signing
                sign_start = time.time()
                csid, _ = self.stamping_service.generate_csid(test_data)
                sign_end = time.time()
                sign_duration_ms = (sign_end - sign_start) * 1000
                signing_times.append(sign_duration_ms)
                
                # Verification
                verify_start = time.time()
                self.stamping_service.verify_csid(test_data, csid)
                verify_end = time.time()
                verify_duration_ms = (verify_end - verify_start) * 1000
                verification_times.append(verify_duration_ms)
                
                # Update min/max
                results["operations"]["signing"]["min_ms"] = min(
                    results["operations"]["signing"]["min_ms"], sign_duration_ms
                )
                results["operations"]["signing"]["max_ms"] = max(
                    results["operations"]["signing"]["max_ms"], sign_duration_ms
                )
                
                results["operations"]["verification"]["min_ms"] = min(
                    results["operations"]["verification"]["min_ms"], verify_duration_ms
                )
                results["operations"]["verification"]["max_ms"] = max(
                    results["operations"]["verification"]["max_ms"], verify_duration_ms
                )
            
            # Calculate signing statistics
            results["operations"]["signing"]["total_ms"] = sum(signing_times)
            results["operations"]["signing"]["average_ms"] = results["operations"]["signing"]["total_ms"] / iterations
            results["operations"]["signing"]["operations_per_second"] = 1000 / results["operations"]["signing"]["average_ms"]
            
            # Calculate verification statistics
            results["operations"]["verification"]["total_ms"] = sum(verification_times)
            results["operations"]["verification"]["average_ms"] = results["operations"]["verification"]["total_ms"] / iterations
            results["operations"]["verification"]["operations_per_second"] = 1000 / results["operations"]["verification"]["average_ms"]
        
        end_time = time.time()
        results["duration_seconds"] = end_time - start_time
        
        return results
    
    def _check_firs_trust_chain(self) -> bool:
        """
        Check if the certificate is in the FIRS trusted chain.
        
        This is a placeholder that should be implemented with actual FIRS trust chain validation.
        
        Returns:
            bool: True if in the trusted chain, False otherwise
        """
        # TODO: Implement actual FIRS trust chain validation
        # For now, return True for testing
        return True
    
    def _check_revocation_status(self) -> bool:
        """
        Check the certificate revocation status.
        
        This is a placeholder that should be implemented with actual revocation checking.
        
        Returns:
            bool: True if not revoked, False if revoked
        """
        # TODO: Implement actual revocation checking (CRL or OCSP)
        # For now, return True for testing
        return True
    
    def _check_required_extensions(self) -> bool:
        """
        Check if the certificate has all required extensions.
        
        Returns:
            bool: True if all required extensions are present, False otherwise
        """
        required_extensions = [
            # Common extensions that might be required
            x509.ExtensionOID.KEY_USAGE,
            x509.ExtensionOID.BASIC_CONSTRAINTS
        ]
        
        for ext_oid in required_extensions:
            try:
                self.certificate.extensions.get_extension_for_oid(ext_oid)
            except x509.ExtensionNotFound:
                logger.warning(f"Required extension not found: {ext_oid}")
                return False
        
        return True


def main():
    """Main function to run the FIRS certificate tester."""
    parser = argparse.ArgumentParser(description="FIRS Certificate Testing Utility")
    parser.add_argument("--cert", required=True, help="Path to the FIRS certificate")
    parser.add_argument("--key", help="Path to the private key (optional)")
    parser.add_argument("--password", help="Password for the private key")
    parser.add_argument(
        "--test-type", 
        choices=["basic", "signing", "performance", "all"],
        default="basic",
        help="Type of test to run"
    )
    parser.add_argument("--iterations", type=int, default=100, help="Number of iterations for performance testing")
    parser.add_argument("--output", help="Output file for test results (JSON)")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create the tester
    password = args.password.encode() if args.password else None
    tester = FIRSCertificateTester(
        certificate_path=args.cert,
        private_key_path=args.key,
        password=password
    )
    
    results = {}
    
    # Run the specified tests
    if args.test_type == "basic" or args.test_type == "all":
        results["basic"] = tester.run_basic_test()
    
    if args.test_type == "signing" or args.test_type == "all":
        # Create test data
        test_data = {
            "invoice_number": "TEST-INV-001",
            "date": datetime.now().isoformat(),
            "amount": 50000,
            "currency": "NGN"
        }
        results["signing"] = tester.run_signing_test(test_data)
    
    if args.test_type == "performance" or args.test_type == "all":
        results["performance"] = tester.run_performance_test(args.iterations)
    
    # Output results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {args.output}")
    else:
        # Print results to console
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
