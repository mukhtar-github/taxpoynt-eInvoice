"""
Scheduled tasks for IRN management.

This module contains scheduled tasks that automate various IRN-related
operations, such as expiring outdated IRNs.
"""
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.irn import IRNRecord, IRNStatus

logger = logging.getLogger(__name__)


def expire_outdated_irns() -> Dict[str, Any]:
    """
    Update all expired but not marked IRNs to expired status.
    
    This task should be scheduled to run periodically (e.g., daily).
    
    Returns:
        Dict with task results (count of updated IRNs)
    """
    db = SessionLocal()
    try:
        # Current timestamp
        now = datetime.utcnow()
        
        # Find all IRNs that are expired but not marked as such
        expired_query = (
            db.query(IRNRecord)
            .filter(
                IRNRecord.valid_until < now,
                IRNRecord.status != IRNStatus.EXPIRED,
                IRNRecord.status != IRNStatus.REVOKED
            )
        )
        
        expired_count = expired_query.count()
        
        if expired_count > 0:
            # Update all expired IRNs
            expired_query.update(
                {"status": IRNStatus.EXPIRED},
                synchronize_session=False
            )
            db.commit()
            
            logger.info(f"Successfully expired {expired_count} outdated IRNs")
        else:
            logger.info("No outdated IRNs found to expire")
        
        return {
            "success": True,
            "message": f"Successfully expired {expired_count} outdated IRNs",
            "details": {
                "expired_count": expired_count
            }
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error expiring outdated IRNs: {str(e)}")
        return {
            "success": False,
            "message": f"Error expiring outdated IRNs: {str(e)}",
            "details": {"error": str(e)}
        }
    finally:
        db.close()


def clean_up_validation_records(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Clean up old validation records to prevent database bloat.
    
    Args:
        days_to_keep: Number of days of validation records to keep
        
    Returns:
        Dict with task results (count of deleted records)
    """
    from app.models.irn import IRNValidationRecord
    from datetime import timedelta
    
    db = SessionLocal()
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Find count of old validation records
        old_records_count = (
            db.query(IRNValidationRecord)
            .filter(IRNValidationRecord.validation_date < cutoff_date)
            .count()
        )
        
        if old_records_count > 0:
            # Delete old validation records
            db.query(IRNValidationRecord) \
                .filter(IRNValidationRecord.validation_date < cutoff_date) \
                .delete(synchronize_session=False)
            
            db.commit()
            
            logger.info(f"Successfully deleted {old_records_count} old validation records")
        else:
            logger.info("No old validation records found to delete")
        
        return {
            "success": True,
            "message": f"Successfully deleted {old_records_count} old validation records",
            "details": {
                "deleted_count": old_records_count,
                "days_kept": days_to_keep
            }
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Error cleaning up validation records: {str(e)}")
        return {
            "success": False,
            "message": f"Error cleaning up validation records: {str(e)}",
            "details": {"error": str(e)}
        }
    finally:
        db.close()
