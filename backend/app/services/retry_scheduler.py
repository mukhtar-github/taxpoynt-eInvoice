"""
Retry Scheduler for TaxPoynt eInvoice APP functionality.

This module provides a background job scheduler to process delayed retries
with exponential backoff for transmission operations.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.transmission import TransmissionRecord, TransmissionStatus

logger = logging.getLogger(__name__)

class RetryScheduler:
    """
    Handles scheduling and processing of delayed transmission retries.
    Implements exponential backoff for failed transmissions.
    """
    
    def __init__(self, db: Session = None):
        """Initialize the retry scheduler with an optional database session."""
        self.db = db or SessionLocal()
    
    def get_pending_retries(self) -> List[TransmissionRecord]:
        """
        Get all transmissions that are in RETRYING status and are due for retry.
        
        Returns:
            List of transmission records that should be retried now
        """
        now = datetime.utcnow()
        
        # Find transmissions in RETRYING status
        retrying_transmissions = (
            self.db.query(TransmissionRecord)
            .filter(TransmissionRecord.status == TransmissionStatus.RETRYING)
            .all()
        )
        
        # Filter for those that are due for retry based on last_retry_time and calculated delay
        due_for_retry = []
        
        for transmission in retrying_transmissions:
            metadata = transmission.transmission_metadata or {}
            retry_strategy = metadata.get('retry_strategy', {})
            
            # Get the current delay from metadata (or default to 0)
            current_delay = retry_strategy.get('current_delay', 0)
            
            # Check if enough time has passed since last retry
            if transmission.last_retry_time:
                retry_due_time = transmission.last_retry_time + timedelta(seconds=current_delay)
                if now >= retry_due_time:
                    due_for_retry.append(transmission)
        
        return due_for_retry
    
    def process_retry(self, transmission_id: UUID) -> bool:
        """
        Process a single transmission retry.
        
        Args:
            transmission_id: ID of the transmission to retry
            
        Returns:
            Success status of the retry operation
        """
        try:
            # Get the transmission service
            from app.services.transmission_service import TransmissionService
            transmission_service = TransmissionService(self.db)
            
            # Get the transmission record
            transmission = (
                self.db.query(TransmissionRecord)
                .filter(TransmissionRecord.id == transmission_id)
                .first()
            )
            
            if not transmission:
                logger.error(f"Transmission {transmission_id} not found for retry")
                return False
                
            if transmission.status != TransmissionStatus.RETRYING:
                logger.warning(f"Transmission {transmission_id} is not in RETRYING status")
                return False
                
            # Here we would implement the actual retry logic
            # This would typically involve resending the transmission to the FIRS API
            # For now, let's just update the status for demonstration
            
            # Update retry history
            metadata = transmission.transmission_metadata or {}
            retry_history = metadata.get('retry_history', [])
            
            if retry_history:
                # Update the last retry entry with completed status
                last_retry = retry_history[-1]
                last_retry['status'] = 'completed'
                last_retry['completed_at'] = datetime.utcnow().isoformat()
                
                metadata['retry_history'] = retry_history
                transmission.transmission_metadata = metadata
            
            # For demonstration, randomly succeed or fail the retry
            # In production, this would be the result of the actual transmission attempt
            import random
            success = random.choice([True, False])
            
            if success:
                transmission.status = TransmissionStatus.COMPLETED
                logger.info(f"Transmission {transmission_id} retry succeeded")
            else:
                transmission.status = TransmissionStatus.FAILED
                logger.warning(f"Transmission {transmission_id} retry failed")
            
            self.db.commit()
            return success
            
        except Exception as e:
            logger.error(f"Error processing retry for transmission {transmission_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def run_scheduler(self, interval: int = 60):
        """
        Run the retry scheduler as a continuous background process.
        
        Args:
            interval: Sleep interval between retry checks in seconds
        """
        logger.info(f"Starting retry scheduler with interval {interval} seconds")
        
        try:
            while True:
                try:
                    # Get transmissions due for retry
                    retries = self.get_pending_retries()
                    
                    if retries:
                        logger.info(f"Found {len(retries)} transmissions due for retry")
                        
                        # Process each retry
                        for transmission in retries:
                            self.process_retry(transmission.id)
                    
                    # Sleep until next check
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error in retry scheduler: {str(e)}")
                    # Sleep and continue
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.info("Retry scheduler stopped by user")
        finally:
            if self.db:
                self.db.close()
                
    def start_background_scheduler(self):
        """Start the scheduler in a background thread."""
        import threading
        
        thread = threading.Thread(target=self.run_scheduler, daemon=True)
        thread.start()
        logger.info("Started retry scheduler in background thread")
        return thread


# Singleton instance for app-wide use
retry_scheduler = None

def get_retry_scheduler(db: Session = None) -> RetryScheduler:
    """Get or create the retry scheduler singleton."""
    global retry_scheduler
    
    if retry_scheduler is None:
        retry_scheduler = RetryScheduler(db)
        
    return retry_scheduler
