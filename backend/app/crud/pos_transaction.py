"""
CRUD operations for POS transactions.

This module provides database CRUD operations for managing POS transaction
data with optimized queries for partitioned tables.
"""

from typing import List, Optional, Union, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.pos_connection import POSTransaction, POSConnection
from app.schemas.pos import POSTransactionCreate


def create_pos_transaction(
    db: Session, 
    transaction_in: POSTransactionCreate,
    connection_id: UUID
) -> POSTransaction:
    """
    Create a new POS transaction record.
    
    Args:
        db: Database session
        transaction_in: Transaction creation data
        connection_id: ID of the POS connection
    
    Returns:
        Created POS transaction
    """
    # Convert transaction data to database model format
    db_transaction = POSTransaction(
        connection_id=connection_id,
        external_transaction_id=transaction_in.transaction_id,
        transaction_amount=Decimal(str(transaction_in.amount)),
        tax_amount=Decimal(str(transaction_in.tax_info.get("amount", 0))) if transaction_in.tax_info else None,
        items=transaction_in.items,
        customer_data=transaction_in.customer_info,
        transaction_timestamp=transaction_in.timestamp,
        transaction_metadata={
            "currency": transaction_in.currency,
            "payment_method": transaction_in.payment_method,
            "location_id": transaction_in.location_id,
            "receipt_number": transaction_in.receipt_number,
            "receipt_url": transaction_in.receipt_url,
            "platform_data": transaction_in.platform_data
        },
        created_at=datetime.utcnow()
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_pos_transaction(db: Session, transaction_id: UUID) -> Optional[POSTransaction]:
    """
    Get a POS transaction by ID.
    
    Args:
        db: Database session
        transaction_id: ID of the transaction
    
    Returns:
        POS transaction if found, None otherwise
    """
    return db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()


def get_pos_transaction_by_external_id(
    db: Session, 
    connection_id: UUID, 
    external_transaction_id: str
) -> Optional[POSTransaction]:
    """
    Get a POS transaction by external transaction ID and connection.
    
    Args:
        db: Database session
        connection_id: ID of the POS connection
        external_transaction_id: External transaction ID from POS platform
    
    Returns:
        POS transaction if found, None otherwise
    """
    return db.query(POSTransaction).filter(
        and_(
            POSTransaction.connection_id == connection_id,
            POSTransaction.external_transaction_id == external_transaction_id
        )
    ).first()


def get_pos_transactions_by_connection(
    db: Session,
    connection_id: UUID,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    invoice_generated: Optional[bool] = None,
    invoice_transmitted: Optional[bool] = None
) -> List[POSTransaction]:
    """
    Get POS transactions for a connection with optional filtering.
    
    Args:
        db: Database session
        connection_id: ID of the POS connection
        skip: Number of records to skip
        limit: Maximum number of records to return
        start_date: Filter transactions after this date
        end_date: Filter transactions before this date
        invoice_generated: Filter by invoice generation status
        invoice_transmitted: Filter by invoice transmission status
    
    Returns:
        List of POS transactions
    """
    query = db.query(POSTransaction).filter(POSTransaction.connection_id == connection_id)
    
    # Date range filtering - important for partitioned tables
    if start_date:
        query = query.filter(POSTransaction.transaction_timestamp >= start_date)
    
    if end_date:
        query = query.filter(POSTransaction.transaction_timestamp <= end_date)
    
    # Status filtering
    if invoice_generated is not None:
        query = query.filter(POSTransaction.invoice_generated == invoice_generated)
    
    if invoice_transmitted is not None:
        query = query.filter(POSTransaction.invoice_transmitted == invoice_transmitted)
    
    return query.order_by(desc(POSTransaction.transaction_timestamp)).offset(skip).limit(limit).all()


def get_pos_transactions_by_user(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[POSTransaction]:
    """
    Get POS transactions for all user's connections.
    
    Args:
        db: Database session
        user_id: ID of the user
        skip: Number of records to skip
        limit: Maximum number of records to return
        start_date: Filter transactions after this date
        end_date: Filter transactions before this date
    
    Returns:
        List of POS transactions
    """
    query = db.query(POSTransaction).join(POSConnection).filter(
        POSConnection.user_id == user_id
    )
    
    if start_date:
        query = query.filter(POSTransaction.transaction_timestamp >= start_date)
    
    if end_date:
        query = query.filter(POSTransaction.transaction_timestamp <= end_date)
    
    return query.order_by(desc(POSTransaction.transaction_timestamp)).offset(skip).limit(limit).all()


def update_pos_transaction(
    db: Session,
    transaction_id: UUID,
    update_data: Dict[str, Any]
) -> Optional[POSTransaction]:
    """
    Update a POS transaction.
    
    Args:
        db: Database session
        transaction_id: ID of the transaction to update
        update_data: Update data
    
    Returns:
        Updated POS transaction if found, None otherwise
    """
    db_transaction = get_pos_transaction(db, transaction_id)
    if not db_transaction:
        return None
    
    for field, value in update_data.items():
        if hasattr(db_transaction, field):
            setattr(db_transaction, field, value)
    
    db_transaction.updated_at = datetime.utcnow()
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def mark_invoice_generated(
    db: Session,
    transaction_id: UUID,
    invoice_id: UUID
) -> Optional[POSTransaction]:
    """
    Mark a transaction as having generated an invoice.
    
    Args:
        db: Database session
        transaction_id: ID of the transaction
        invoice_id: ID of the generated invoice
    
    Returns:
        Updated POS transaction if found, None otherwise
    """
    return update_pos_transaction(
        db,
        transaction_id,
        {
            "invoice_generated": True,
            "invoice_id": invoice_id,
            "updated_at": datetime.utcnow()
        }
    )


def mark_invoice_transmitted(
    db: Session,
    transaction_id: UUID
) -> Optional[POSTransaction]:
    """
    Mark a transaction's invoice as transmitted to FIRS.
    
    Args:
        db: Database session
        transaction_id: ID of the transaction
    
    Returns:
        Updated POS transaction if found, None otherwise
    """
    return update_pos_transaction(
        db,
        transaction_id,
        {
            "invoice_transmitted": True,
            "updated_at": datetime.utcnow()
        }
    )


def add_processing_error(
    db: Session,
    transaction_id: UUID,
    error_data: Dict[str, Any]
) -> Optional[POSTransaction]:
    """
    Add processing error information to a transaction.
    
    Args:
        db: Database session
        transaction_id: ID of the transaction
        error_data: Error information
    
    Returns:
        Updated POS transaction if found, None otherwise
    """
    db_transaction = get_pos_transaction(db, transaction_id)
    if not db_transaction:
        return None
    
    # Add timestamp to error data
    error_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        **error_data
    }
    
    # Append to existing errors or create new list
    current_errors = db_transaction.processing_errors or []
    current_errors.append(error_entry)
    
    return update_pos_transaction(
        db,
        transaction_id,
        {"processing_errors": current_errors}
    )


def get_pending_invoice_transactions(
    db: Session,
    connection_id: Optional[UUID] = None,
    limit: int = 100
) -> List[POSTransaction]:
    """
    Get transactions that need invoice generation.
    
    Args:
        db: Database session
        connection_id: Optional filter by connection ID
        limit: Maximum number of records to return
    
    Returns:
        List of transactions pending invoice generation
    """
    query = db.query(POSTransaction).filter(
        POSTransaction.invoice_generated == False
    )
    
    if connection_id:
        query = query.filter(POSTransaction.connection_id == connection_id)
    
    return query.order_by(asc(POSTransaction.transaction_timestamp)).limit(limit).all()


def get_transactions_for_transmission(
    db: Session,
    connection_id: Optional[UUID] = None,
    limit: int = 100
) -> List[POSTransaction]:
    """
    Get transactions with generated invoices that need transmission.
    
    Args:
        db: Database session
        connection_id: Optional filter by connection ID
        limit: Maximum number of records to return
    
    Returns:
        List of transactions ready for transmission
    """
    query = db.query(POSTransaction).filter(
        and_(
            POSTransaction.invoice_generated == True,
            POSTransaction.invoice_transmitted == False
        )
    )
    
    if connection_id:
        query = query.filter(POSTransaction.connection_id == connection_id)
    
    return query.order_by(asc(POSTransaction.transaction_timestamp)).limit(limit).all()


def get_transaction_metrics_by_connection(
    db: Session,
    connection_id: UUID,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    Get transaction metrics for a connection within a date range.
    
    Args:
        db: Database session
        connection_id: ID of the POS connection
        start_date: Start of date range
        end_date: End of date range
    
    Returns:
        Dictionary containing transaction metrics
    """
    base_query = db.query(POSTransaction).filter(
        and_(
            POSTransaction.connection_id == connection_id,
            POSTransaction.transaction_timestamp >= start_date,
            POSTransaction.transaction_timestamp <= end_date
        )
    )
    
    # Total transactions and amount
    total_count = base_query.count()
    total_amount = base_query.with_entities(
        func.sum(POSTransaction.transaction_amount)
    ).scalar() or 0
    
    # Invoice generation metrics
    invoices_generated = base_query.filter(
        POSTransaction.invoice_generated == True
    ).count()
    
    invoices_transmitted = base_query.filter(
        POSTransaction.invoice_transmitted == True
    ).count()
    
    # Processing errors
    transactions_with_errors = base_query.filter(
        POSTransaction.processing_errors.isnot(None)
    ).count()
    
    return {
        "total_transactions": total_count,
        "total_amount": float(total_amount),
        "average_amount": float(total_amount / total_count) if total_count > 0 else 0,
        "invoices_generated": invoices_generated,
        "invoices_transmitted": invoices_transmitted,
        "transactions_with_errors": transactions_with_errors,
        "invoice_generation_rate": (invoices_generated / total_count * 100) if total_count > 0 else 0,
        "transmission_rate": (invoices_transmitted / total_count * 100) if total_count > 0 else 0,
        "error_rate": (transactions_with_errors / total_count * 100) if total_count > 0 else 0
    }


def get_daily_transaction_summary(
    db: Session,
    connection_id: UUID,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """
    Get daily transaction summary for a connection within a date range.
    
    Args:
        db: Database session
        connection_id: ID of the POS connection
        start_date: Start of date range
        end_date: End of date range
    
    Returns:
        List of daily summaries
    """
    # Use raw SQL for efficient aggregation on partitioned table
    query = text("""
        SELECT 
            DATE(transaction_timestamp) as transaction_date,
            COUNT(*) as transaction_count,
            SUM(transaction_amount) as total_amount,
            AVG(transaction_amount) as avg_amount,
            SUM(CASE WHEN invoice_generated = true THEN 1 ELSE 0 END) as invoices_generated,
            SUM(CASE WHEN invoice_transmitted = true THEN 1 ELSE 0 END) as invoices_transmitted
        FROM pos_transactions 
        WHERE connection_id = :connection_id 
            AND transaction_timestamp >= :start_date 
            AND transaction_timestamp <= :end_date
        GROUP BY DATE(transaction_timestamp)
        ORDER BY transaction_date
    """)
    
    result = db.execute(
        query,
        {
            "connection_id": str(connection_id),
            "start_date": start_date,
            "end_date": end_date
        }
    )
    
    return [
        {
            "date": row.transaction_date.isoformat(),
            "transaction_count": row.transaction_count,
            "total_amount": float(row.total_amount or 0),
            "avg_amount": float(row.avg_amount or 0),
            "invoices_generated": row.invoices_generated,
            "invoices_transmitted": row.invoices_transmitted
        }
        for row in result
    ]


def delete_pos_transaction(db: Session, transaction_id: UUID) -> bool:
    """
    Delete a POS transaction.
    
    Args:
        db: Database session
        transaction_id: ID of the transaction to delete
    
    Returns:
        True if transaction was deleted, False if not found
    """
    db_transaction = get_pos_transaction(db, transaction_id)
    if not db_transaction:
        return False
    
    db.delete(db_transaction)
    db.commit()
    return True


def bulk_create_pos_transactions(
    db: Session,
    transactions_data: List[Dict[str, Any]],
    connection_id: UUID
) -> List[POSTransaction]:
    """
    Bulk create POS transactions for efficient batch processing.
    
    Args:
        db: Database session
        transactions_data: List of transaction data dictionaries
        connection_id: ID of the POS connection
    
    Returns:
        List of created POS transactions
    """
    db_transactions = []
    
    for transaction_data in transactions_data:
        db_transaction = POSTransaction(
            connection_id=connection_id,
            external_transaction_id=transaction_data["external_transaction_id"],
            transaction_amount=Decimal(str(transaction_data["transaction_amount"])),
            tax_amount=Decimal(str(transaction_data.get("tax_amount", 0))),
            items=transaction_data.get("items"),
            customer_data=transaction_data.get("customer_data"),
            transaction_timestamp=transaction_data["transaction_timestamp"],
            transaction_metadata=transaction_data.get("transaction_metadata"),
            created_at=datetime.utcnow()
        )
        db_transactions.append(db_transaction)
    
    db.add_all(db_transactions)
    db.commit()
    
    # Refresh all objects to get IDs
    for db_transaction in db_transactions:
        db.refresh(db_transaction)
    
    return db_transactions


def count_transactions_by_connection(
    db: Session,
    connection_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> int:
    """
    Count transactions for a connection with optional date filtering.
    
    Args:
        db: Database session
        connection_id: ID of the POS connection
        start_date: Optional start date filter
        end_date: Optional end date filter
    
    Returns:
        Total number of transactions
    """
    query = db.query(POSTransaction).filter(POSTransaction.connection_id == connection_id)
    
    if start_date:
        query = query.filter(POSTransaction.transaction_timestamp >= start_date)
    
    if end_date:
        query = query.filter(POSTransaction.transaction_timestamp <= end_date)
    
    return query.count()