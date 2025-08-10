"""
Bulk Processor

Handles bulk IRN and QR code generation using granular components.
Provides batch processing, job tracking, and validation for multiple invoices.
"""

import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .irn_generator import IRNGenerator
from .qr_code_generator import QRCodeGenerator
from .sequence_manager import SequenceManager
from .duplicate_detector import DuplicateDetector
from .irn_validator import IRNValidator, ValidationLevel


class BulkJobStatus(Enum):
    """Bulk job status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BulkJobResult:
    """Result of bulk processing job"""
    job_id: str
    status: BulkJobStatus
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    errors: List[str]
    warnings: List[str]
    results: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime] = None


class BulkProcessor:
    """Bulk IRN and QR code processor using granular components"""
    
    def __init__(self, max_batch_size: int = 1000):
        self.irn_generator = IRNGenerator()
        self.qr_generator = QRCodeGenerator()
        self.sequence_manager = SequenceManager()
        self.duplicate_detector = DuplicateDetector()
        self.irn_validator = IRNValidator()
        
        self.max_batch_size = max_batch_size
        self.active_jobs: Dict[str, BulkJobResult] = {}
        
        self.logger = logging.getLogger(__name__)
    
    async def process_bulk_irn_generation(
        self,
        invoice_data_list: List[Dict[str, Any]],
        organization_id: str,
        job_id: Optional[str] = None,
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> BulkJobResult:
        """
        Process bulk IRN generation for multiple invoices
        
        Args:
            invoice_data_list: List of invoice data dictionaries
            organization_id: Organization identifier
            job_id: Optional job ID (generated if not provided)
            validation_level: Level of validation to perform
            
        Returns:
            Bulk job result with processing details
        """
        if not job_id:
            job_id = f"bulk_{uuid.uuid4().hex[:8]}"
        
        # Validate batch size
        if len(invoice_data_list) > self.max_batch_size:
            raise ValueError(f"Batch size {len(invoice_data_list)} exceeds maximum {self.max_batch_size}")
        
        # Initialize job result
        job_result = BulkJobResult(
            job_id=job_id,
            status=BulkJobStatus.PENDING,
            total_items=len(invoice_data_list),
            processed_items=0,
            successful_items=0,
            failed_items=0,
            errors=[],
            warnings=[],
            results=[],
            started_at=datetime.now()
        )
        
        self.active_jobs[job_id] = job_result
        
        try:
            job_result.status = BulkJobStatus.IN_PROGRESS
            
            # Reserve sequence block for bulk operation
            sequence_numbers = await self.sequence_manager.reserve_sequence_block(
                organization_id=organization_id,
                block_size=len(invoice_data_list)
            )
            
            # Process each invoice
            for idx, invoice_data in enumerate(invoice_data_list):
                try:
                    result = await self._process_single_invoice(
                        invoice_data=invoice_data,
                        organization_id=organization_id,
                        sequence_number=sequence_numbers[idx],
                        validation_level=validation_level
                    )
                    
                    job_result.results.append(result)
                    job_result.processed_items += 1
                    
                    if result.get("success", False):
                        job_result.successful_items += 1
                    else:
                        job_result.failed_items += 1
                        if "error" in result:
                            job_result.errors.append(f"Invoice {idx}: {result['error']}")
                    
                    # Add warnings if any
                    if "warnings" in result:
                        job_result.warnings.extend(result["warnings"])
                
                except Exception as e:
                    self.logger.error(f"Error processing invoice {idx}: {str(e)}")
                    job_result.failed_items += 1
                    job_result.errors.append(f"Invoice {idx}: {str(e)}")
                    job_result.results.append({
                        "success": False,
                        "error": str(e),
                        "invoice_index": idx
                    })
                
                # Update progress
                job_result.processed_items += 1
            
            job_result.status = BulkJobStatus.COMPLETED
            job_result.completed_at = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Bulk job {job_id} failed: {str(e)}")
            job_result.status = BulkJobStatus.FAILED
            job_result.errors.append(f"Bulk job failed: {str(e)}")
            job_result.completed_at = datetime.now()
        
        return job_result
    
    async def _process_single_invoice(
        self,
        invoice_data: Dict[str, Any],
        organization_id: str,
        sequence_number: int,
        validation_level: ValidationLevel
    ) -> Dict[str, Any]:
        """Process single invoice for IRN and QR generation"""
        try:
            # Check for duplicate invoice
            existing_irn = self.duplicate_detector.check_duplicate_invoice(invoice_data)
            if existing_irn:
                return {
                    "success": False,
                    "error": f"Duplicate invoice detected. Existing IRN: {existing_irn}",
                    "duplicate_irn": existing_irn
                }
            
            # Generate IRN
            irn_value, verification_code, hash_value = self.irn_generator.generate_irn(invoice_data)
            
            # Validate generated IRN
            validation_result = self.irn_validator.validate_irn(
                irn_value=irn_value,
                verification_code=verification_code,
                validation_level=validation_level
            )
            
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "error": f"IRN validation failed: {', '.join(validation_result.errors)}",
                    "validation_errors": validation_result.errors
                }
            
            # Generate QR code
            qr_data = self.qr_generator.generate_qr_data(
                irn_value=irn_value,
                verification_code=verification_code,
                invoice_data=invoice_data
            )
            
            qr_string = self.qr_generator.generate_qr_string(
                irn_value=irn_value,
                verification_code=verification_code,
                invoice_data=invoice_data
            )
            
            # Register IRN to prevent duplicates
            registration_success = self.duplicate_detector.register_irn(
                irn_value=irn_value,
                invoice_data=invoice_data,
                organization_id=organization_id
            )
            
            if not registration_success:
                return {
                    "success": False,
                    "error": "Failed to register IRN (possible duplicate)"
                }
            
            result = {
                "success": True,
                "irn_value": irn_value,
                "verification_code": verification_code,
                "hash_value": hash_value,
                "sequence_number": sequence_number,
                "qr_data": qr_data,
                "qr_string": qr_string,
                "validation_info": {
                    "level": validation_result.validation_level.value,
                    "warnings": validation_result.warnings
                },
                "generated_at": datetime.now().isoformat()
            }
            
            # Add warnings if any
            if validation_result.warnings:
                result["warnings"] = validation_result.warnings
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing single invoice: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_job_status(self, job_id: str) -> Optional[BulkJobResult]:
        """Get status of bulk processing job"""
        return self.active_jobs.get(job_id)
    
    def list_active_jobs(self) -> List[str]:
        """List all active job IDs"""
        return list(self.active_jobs.keys())
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a bulk processing job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in [BulkJobStatus.PENDING, BulkJobStatus.IN_PROGRESS]:
                job.status = BulkJobStatus.CANCELLED
                job.completed_at = datetime.now()
                return True
        return False
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up completed jobs older than specified hours"""
        cutoff_time = datetime.now().replace(hour=datetime.now().hour - max_age_hours)
        cleaned_count = 0
        
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if (job.status in [BulkJobStatus.COMPLETED, BulkJobStatus.FAILED, BulkJobStatus.CANCELLED] 
                and job.completed_at 
                and job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            cleaned_count += 1
        
        return cleaned_count
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics across all jobs"""
        total_jobs = len(self.active_jobs)
        
        status_counts = {}
        total_processed = 0
        total_successful = 0
        total_failed = 0
        
        for job in self.active_jobs.values():
            status_counts[job.status.value] = status_counts.get(job.status.value, 0) + 1
            total_processed += job.processed_items
            total_successful += job.successful_items
            total_failed += job.failed_items
        
        success_rate = (total_successful / total_processed * 100) if total_processed > 0 else 0
        
        return {
            "total_jobs": total_jobs,
            "status_distribution": status_counts,
            "total_items_processed": total_processed,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "overall_success_rate": success_rate,
            "duplicate_detection_stats": self.duplicate_detector.get_statistics(),
            "sequence_manager_active": len(self.sequence_manager.list_sequences("all"))
        }