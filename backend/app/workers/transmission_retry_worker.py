"""
Transmission Retry Worker

Background worker for automatically retrying failed transmissions
with configurable backoff strategies.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.transmission import TransmissionRecord, TransmissionStatus
from app.services.firs_app.transmission_service import FIRSTransmissionService

logger = logging.getLogger(__name__)

class TransmissionRetryWorker:
    """
    Worker to automatically retry failed or pending transmissions.
    Uses exponential backoff for retries.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the retry worker.
        
        Args:
            db: Optional database session, will create one if not provided
        """
        self.db = db or SessionLocal()
        self.firs_service = FIRSTransmissionService(self.db)
        
    async def process_pending_retries(self, max_items: int = 50) -> int:
        """
        Process all pending retries that are due to be retried.
        
        Args:
            max_items: Maximum number of items to process in one batch
            
        Returns:
            Number of transmissions processed
        """
        try:
            # Find transmissions that need retry
            retry_candidates = self._find_retry_candidates(max_items)
            
            if not retry_candidates:
                logger.info("No transmissions found for retry")
                return 0
                
            logger.info(f"Found {len(retry_candidates)} transmissions to retry")
            
            # Process each candidate
            retry_count = 0
            for transmission in retry_candidates:
                try:
                    # Check if retry should be attempted now
                    if self._should_retry_now(transmission):
                        logger.info(f"Retrying transmission {transmission.id}")
                        
                        # Initialize the appropriate service based on destination
                        if transmission.transmission_metadata.get("destination") == "FIRS":
                            # Attempt the retry
                            success, response = await self.firs_service.transmit_to_firs(
                                transmission_id=transmission.id,
                                retrying=True
                            )
                            
                            if success:
                                logger.info(f"Retry successful for transmission {transmission.id}")
                            else:
                                logger.warning(f"Retry failed for transmission {transmission.id}: {response.get('error', 'Unknown error')}")
                                
                            retry_count += 1
                        else:
                            logger.warning(f"Unsupported destination: {transmission.transmission_metadata.get('destination')}")
                            continue
                    else:
                        logger.debug(f"Transmission {transmission.id} not yet due for retry")
                        
                except Exception as e:
                    logger.error(f"Error retrying transmission {transmission.id}: {str(e)}")
                    self._mark_retry_failed(transmission, str(e))
                    
            return retry_count
                
        except Exception as e:
            logger.error(f"Error in process_pending_retries: {str(e)}")
            return 0
        finally:
            # Ensure session is committed
            self.db.commit()
            
    def _find_retry_candidates(self, limit: int = 50) -> List[TransmissionRecord]:
        """
        Find transmissions that are eligible for retry.
        
        Returns:
            List of transmission records ready for retry
        """
        return self.db.query(TransmissionRecord).filter(
            and_(
                or_(
                    TransmissionRecord.status == TransmissionStatus.FAILED,
                    TransmissionRecord.status == TransmissionStatus.PENDING
                ),
                TransmissionRecord.retry_count < TransmissionRecord.max_retries
            )
        ).order_by(TransmissionRecord.last_retry_time).limit(limit).all()
        
    def _should_retry_now(self, transmission: TransmissionRecord) -> bool:
        """
        Determine if a transmission should be retried now based on its
        backoff schedule.
        
        Args:
            transmission: The transmission record
            
        Returns:
            True if should retry now, False otherwise
        """
        # If no previous retry, or immediate retry, retry now
        if not transmission.last_retry_time or transmission.retry_delay_seconds == 0:
            return True
            
        # Calculate next retry time using exponential backoff
        current_retry_count = transmission.retry_count
        retry_delay = transmission.retry_delay_seconds * (2 ** current_retry_count)
        
        next_retry_time = transmission.last_retry_time + timedelta(seconds=retry_delay)
        
        # Check if next retry time has passed
        return datetime.utcnow() >= next_retry_time
        
    def _mark_retry_failed(self, transmission: TransmissionRecord, error: str) -> None:
        """
        Mark a retry attempt as failed in the database.
        
        Args:
            transmission: The transmission record
            error: Error message
        """
        # Update retry history
        metadata = transmission.transmission_metadata or {}
        retry_history = metadata.get('retry_history', [])
        
        retry_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'attempt': transmission.retry_count + 1,
            'status': 'failed',
            'error': error
        }
        
        retry_history.append(retry_entry)
        metadata['retry_history'] = retry_history
        
        # Update transmission record
        transmission.retry_count += 1
        transmission.last_retry_time = datetime.utcnow()
        transmission.status = TransmissionStatus.FAILED
        transmission.transmission_metadata = metadata
        
        self.db.commit()
        
    async def run_forever(self, interval_seconds: int = 60):
        """
        Run the retry worker indefinitely, processing retries at regular intervals.
        
        Args:
            interval_seconds: Seconds to wait between processing batches
        """
        logger.info(f"Starting transmission retry worker with {interval_seconds}s interval")
        
        while True:
            try:
                processed = await self.process_pending_retries()
                logger.info(f"Processed {processed} transmission retries")
            except Exception as e:
                logger.error(f"Error in retry worker: {str(e)}")
                
            # Wait for next interval
            await asyncio.sleep(interval_seconds)


async def start_retry_worker():
    """Start the retry worker as a background task."""
    worker = TransmissionRetryWorker()
    await worker.run_forever()
    

if __name__ == "__main__":
    # For testing or standalone execution
    asyncio.run(start_retry_worker())
