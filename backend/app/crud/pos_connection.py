"""
CRUD operations for POS connections and transactions.

This module provides database CRUD operations for managing POS connection
configurations and transaction data.
"""

from typing import List, Optional, Union, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta

from app.models.pos_connection import POSConnection, POSTransaction, POSType
from app.schemas.pos import POSConnectionCreate, POSConnectionUpdate
from app.core.encryption import encrypt_credentials, decrypt_credentials


def create_pos_connection(
    db: Session, 
    connection_in: POSConnectionCreate, 
    user_id: UUID,
    organization_id: UUID
) -> POSConnection:
    """
    Create a new POS connection.
    
    Args:
        db: Database session
        connection_in: POS connection creation data
        user_id: ID of the user creating the connection
        organization_id: ID of the organization
    
    Returns:
        Created POS connection
    """
    # Encrypt credentials before storing
    credentials_data = {
        "access_token": connection_in.access_token,
        "refresh_token": connection_in.refresh_token,
        "application_id": connection_in.application_id,
        "merchant_id": connection_in.merchant_id,
        "environment": connection_in.environment
    }
    
    credentials_encrypted = encrypt_credentials(credentials_data)
    
    # Create connection settings
    connection_settings = {
        "auto_invoice_generation": connection_in.auto_invoice_generation,
        "real_time_sync": connection_in.real_time_sync,
        "environment": connection_in.environment,
        **(connection_in.metadata or {})
    }
    
    db_connection = POSConnection(
        user_id=user_id,
        organization_id=organization_id,
        pos_type=POSType(connection_in.platform),
        location_name=connection_in.name,
        credentials_encrypted=credentials_encrypted,
        connection_settings=connection_settings,
        webhook_url=connection_in.webhook_url,
        webhook_secret=connection_in.webhook_secret,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


def get_pos_connection(db: Session, connection_id: UUID) -> Optional[POSConnection]:
    """
    Get a POS connection by ID.
    
    Args:
        db: Database session
        connection_id: ID of the connection
    
    Returns:
        POS connection if found, None otherwise
    """
    return db.query(POSConnection).filter(POSConnection.id == connection_id).first()


def get_pos_connection_by_user(
    db: Session, 
    user_id: UUID, 
    connection_id: UUID
) -> Optional[POSConnection]:
    """
    Get a POS connection by ID for a specific user.
    
    Args:
        db: Database session
        user_id: ID of the user
        connection_id: ID of the connection
    
    Returns:
        POS connection if found and belongs to user, None otherwise
    """
    return db.query(POSConnection).filter(
        and_(
            POSConnection.id == connection_id,
            POSConnection.user_id == user_id
        )
    ).first()


def get_pos_connections_by_user(
    db: Session, 
    user_id: UUID, 
    skip: int = 0, 
    limit: int = 100,
    pos_type: Optional[POSType] = None,
    is_active: Optional[bool] = None
) -> List[POSConnection]:
    """
    Get all POS connections for a user with optional filtering.
    
    Args:
        db: Database session
        user_id: ID of the user
        skip: Number of records to skip
        limit: Maximum number of records to return
        pos_type: Filter by POS type
        is_active: Filter by active status
    
    Returns:
        List of POS connections
    """
    query = db.query(POSConnection).filter(POSConnection.user_id == user_id)
    
    if pos_type:
        query = query.filter(POSConnection.pos_type == pos_type)
    
    if is_active is not None:
        query = query.filter(POSConnection.is_active == is_active)
    
    return query.order_by(desc(POSConnection.created_at)).offset(skip).limit(limit).all()


def get_pos_connections_by_organization(
    db: Session, 
    organization_id: UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[POSConnection]:
    """
    Get all POS connections for an organization.
    
    Args:
        db: Database session
        organization_id: ID of the organization
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of POS connections
    """
    return db.query(POSConnection).filter(
        POSConnection.organization_id == organization_id
    ).order_by(desc(POSConnection.created_at)).offset(skip).limit(limit).all()


def update_pos_connection(
    db: Session, 
    connection_id: UUID, 
    connection_update: Union[POSConnectionUpdate, Dict[str, Any]]
) -> Optional[POSConnection]:
    """
    Update a POS connection.
    
    Args:
        db: Database session
        connection_id: ID of the connection to update
        connection_update: Update data
    
    Returns:
        Updated POS connection if found, None otherwise
    """
    db_connection = get_pos_connection(db, connection_id)
    if not db_connection:
        return None
    
    update_data = (
        connection_update.dict(exclude_unset=True) 
        if hasattr(connection_update, "dict") 
        else connection_update
    )
    
    # Handle connection settings update
    if any(key in update_data for key in ["auto_invoice_generation", "real_time_sync", "metadata"]):
        current_settings = db_connection.connection_settings or {}
        
        if "auto_invoice_generation" in update_data:
            current_settings["auto_invoice_generation"] = update_data.pop("auto_invoice_generation")
        
        if "real_time_sync" in update_data:
            current_settings["real_time_sync"] = update_data.pop("real_time_sync")
        
        if "metadata" in update_data:
            metadata = update_data.pop("metadata")
            current_settings.update(metadata or {})
        
        db_connection.connection_settings = current_settings
    
    # Update other fields
    for field, value in update_data.items():
        if hasattr(db_connection, field):
            setattr(db_connection, field, value)
    
    db_connection.updated_at = datetime.utcnow()
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


def update_pos_connection_sync_time(db: Session, connection_id: UUID) -> Optional[POSConnection]:
    """
    Update the last sync time for a POS connection.
    
    Args:
        db: Database session
        connection_id: ID of the connection
    
    Returns:
        Updated POS connection if found, None otherwise
    """
    db_connection = get_pos_connection(db, connection_id)
    if not db_connection:
        return None
    
    db_connection.last_sync_at = datetime.utcnow()
    db_connection.updated_at = datetime.utcnow()
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


def delete_pos_connection(db: Session, connection_id: UUID) -> bool:
    """
    Delete a POS connection and all related transactions.
    
    Args:
        db: Database session
        connection_id: ID of the connection to delete
    
    Returns:
        True if connection was deleted, False if not found
    """
    db_connection = get_pos_connection(db, connection_id)
    if not db_connection:
        return False
    
    # The cascade="all, delete-orphan" in the model will handle
    # deletion of related transactions automatically
    db.delete(db_connection)
    db.commit()
    return True


def activate_pos_connection(db: Session, connection_id: UUID) -> Optional[POSConnection]:
    """
    Activate a POS connection.
    
    Args:
        db: Database session
        connection_id: ID of the connection
    
    Returns:
        Updated POS connection if found, None otherwise
    """
    return update_pos_connection(
        db, 
        connection_id, 
        {"is_active": True, "updated_at": datetime.utcnow()}
    )


def deactivate_pos_connection(db: Session, connection_id: UUID) -> Optional[POSConnection]:
    """
    Deactivate a POS connection.
    
    Args:
        db: Database session
        connection_id: ID of the connection
    
    Returns:
        Updated POS connection if found, None otherwise
    """
    return update_pos_connection(
        db, 
        connection_id, 
        {"is_active": False, "updated_at": datetime.utcnow()}
    )


def get_active_pos_connections(db: Session, user_id: UUID) -> List[POSConnection]:
    """
    Get all active POS connections for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
    
    Returns:
        List of active POS connections
    """
    return db.query(POSConnection).filter(
        and_(
            POSConnection.user_id == user_id,
            POSConnection.is_active == True
        )
    ).order_by(desc(POSConnection.created_at)).all()


def get_pos_connections_by_type(
    db: Session, 
    user_id: UUID, 
    pos_type: POSType
) -> List[POSConnection]:
    """
    Get all POS connections of a specific type for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
        pos_type: Type of POS platform
    
    Returns:
        List of POS connections of the specified type
    """
    return db.query(POSConnection).filter(
        and_(
            POSConnection.user_id == user_id,
            POSConnection.pos_type == pos_type
        )
    ).order_by(desc(POSConnection.created_at)).all()


def get_pos_connection_credentials(db: Session, connection_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get decrypted credentials for a POS connection.
    
    Args:
        db: Database session
        connection_id: ID of the connection
    
    Returns:
        Decrypted credentials if connection found, None otherwise
    """
    db_connection = get_pos_connection(db, connection_id)
    if not db_connection or not db_connection.credentials_encrypted:
        return None
    
    try:
        return decrypt_credentials(db_connection.credentials_encrypted)
    except Exception:
        # Log the error but don't expose it
        return None


def count_pos_connections_by_user(db: Session, user_id: UUID) -> int:
    """
    Count total POS connections for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
    
    Returns:
        Total number of POS connections
    """
    return db.query(POSConnection).filter(POSConnection.user_id == user_id).count()


def count_active_pos_connections_by_user(db: Session, user_id: UUID) -> int:
    """
    Count active POS connections for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
    
    Returns:
        Number of active POS connections
    """
    return db.query(POSConnection).filter(
        and_(
            POSConnection.user_id == user_id,
            POSConnection.is_active == True
        )
    ).count()