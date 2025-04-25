from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.integration import Integration, IntegrationHistory
from app.schemas.integration import IntegrationCreate, IntegrationUpdate, IntegrationHistoryCreate


def get(db: Session, integration_id: UUID) -> Optional[Integration]:
    return db.query(Integration).filter(Integration.id == integration_id).first()


def get_by_client_id(db: Session, client_id: UUID) -> List[Integration]:
    return db.query(Integration).filter(Integration.client_id == client_id).all()


def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[Integration]:
    return db.query(Integration).offset(skip).limit(limit).all()


def create(db: Session, *, obj_in: IntegrationCreate, user_id: UUID) -> Integration:
    db_obj = Integration(
        client_id=obj_in.client_id,
        name=obj_in.name,
        description=obj_in.description,
        config=obj_in.config,
        created_by=user_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, *, db_obj: Integration, obj_in: IntegrationUpdate, user_id: UUID) -> Integration:
    update_data = obj_in.dict(exclude_unset=True)
    
    # Create history record if config is being updated
    if "config" in update_data:
        history_in = IntegrationHistoryCreate(
            integration_id=db_obj.id,
            changed_by=user_id,
            previous_config=db_obj.config,
            new_config=update_data["config"],
            change_reason=update_data.get("change_reason")
        )
        create_history(db, obj_in=history_in)
    
    for field, value in update_data.items():
        if field != "change_reason":  # Skip this field as it's not part of the Integration model
            setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete(db: Session, *, integration_id: UUID) -> Integration:
    obj = db.query(Integration).get(integration_id)
    if obj:
        db.delete(obj)
        db.commit()
    return obj


def get_history(db: Session, integration_id: UUID) -> List[IntegrationHistory]:
    return db.query(IntegrationHistory).filter(
        IntegrationHistory.integration_id == integration_id
    ).order_by(IntegrationHistory.changed_at.desc()).all()


def create_history(db: Session, *, obj_in: IntegrationHistoryCreate) -> IntegrationHistory:
    db_obj = IntegrationHistory(
        integration_id=obj_in.integration_id,
        changed_by=obj_in.changed_by,
        previous_config=obj_in.previous_config,
        new_config=obj_in.new_config,
        change_reason=obj_in.change_reason
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj 