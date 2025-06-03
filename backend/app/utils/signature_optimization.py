"""
Signature Generation Optimization Module for TaxPoynt eInvoice.

This module provides optimized signature generation functionality:
- Parallel signature processing for batch operations
- Performance optimizations for cryptographic operations
- Profiling and metrics collection for signature generation
"""

import time
import logging
import threading
import multiprocessing
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache

from app.utils.crypto_signing import sign_invoice, CSIDVersion, SigningAlgorithm

logger = logging.getLogger(__name__)

# Thread-local storage for performance metrics
_thread_local = threading.local()

def _initialize_metrics():
    """Initialize thread-local metrics if not already done."""
    if not hasattr(_thread_local, 'metrics'):
        _thread_local.metrics = {
            'total_signatures': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
        }

def _update_metrics(execution_time: float):
    """Update performance metrics with a new signature generation time."""
    _initialize_metrics()
    _thread_local.metrics['total_signatures'] += 1
    _thread_local.metrics['total_time'] += execution_time
    _thread_local.metrics['avg_time'] = _thread_local.metrics['total_time'] / _thread_local.metrics['total_signatures']
    _thread_local.metrics['min_time'] = min(_thread_local.metrics['min_time'], execution_time)
    _thread_local.metrics['max_time'] = max(_thread_local.metrics['max_time'], execution_time)

def get_metrics() -> Dict[str, Any]:
    """Get current signature generation performance metrics."""
    _initialize_metrics()
    return dict(_thread_local.metrics)

def reset_metrics():
    """Reset performance metrics."""
    if hasattr(_thread_local, 'metrics'):
        _thread_local.metrics = {
            'total_signatures': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
        }

def optimized_sign_invoice(
    invoice_data: Dict,
    version: Any = CSIDVersion.V2_0,
    algorithm: Any = SigningAlgorithm.RSA_PSS_SHA256,
    collect_metrics: bool = True
) -> Dict:
    """
    Sign an invoice with optimized performance.
    
    Args:
        invoice_data: Original invoice data
        version: CSID version to use
        algorithm: Signing algorithm to use
        collect_metrics: Whether to collect performance metrics
        
    Returns:
        Invoice data with CSID added
    """
    start_time = time.time()
    
    # Call the actual signing function
    signed_invoice = sign_invoice(invoice_data, version, algorithm)
    
    # Update metrics if enabled
    if collect_metrics:
        execution_time = time.time() - start_time
        _update_metrics(execution_time)
    
    return signed_invoice

def batch_sign_invoices(
    invoices: List[Dict],
    max_workers: Optional[int] = None,
    use_processes: bool = False,
    version: Any = CSIDVersion.V2_0,
    algorithm: Any = SigningAlgorithm.RSA_PSS_SHA256
) -> List[Dict]:
    """
    Sign multiple invoices in parallel using a thread or process pool.
    
    Args:
        invoices: List of invoice data dictionaries
        max_workers: Maximum number of worker threads/processes (default: CPU count)
        use_processes: If True, use ProcessPoolExecutor instead of ThreadPoolExecutor
        version: CSID version to use for all invoices
        algorithm: Signing algorithm to use for all invoices
        
    Returns:
        List of signed invoices
    """
    if not max_workers:
        max_workers = multiprocessing.cpu_count()
    
    # Choose executor based on parameter
    Executor = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    
    # Create a worker pool and submit tasks
    with Executor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                optimized_sign_invoice,
                invoice,
                version,
                algorithm,
                False  # Disable metrics collection in worker threads
            )
            for invoice in invoices
        ]
        
        # Gather results
        return [future.result() for future in futures]

def get_recommended_batch_size() -> int:
    """
    Get recommended batch size for signature operations based on system specs.
    
    Returns:
        Recommended batch size
    """
    cpu_count = multiprocessing.cpu_count()
    
    # Simple heuristic: 50 invoices per CPU core, capped at 500
    recommended = min(cpu_count * 50, 500)
    return recommended
