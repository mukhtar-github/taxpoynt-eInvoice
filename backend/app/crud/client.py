from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session # type: ignore

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


def get(db: Session, client_id: UUID) -> Optional[Client]:
    return db.query(Client).filter(Client.id == client_id).first()


def get_by_organization_id(db: Session, organization_id: UUID, skip: int = 0, limit: int = 100) -> List[Client]:
    return db.query(Client).filter(Client.organization_id == organization_id).offset(skip).limit(limit).all()


def create(db: Session, *, obj_in: ClientCreate) -> Client:
    db_obj = Client(
        organization_id=obj_in.organization_id,
        name=obj_in.name,
        tax_id=obj_in.tax_id,
        email=obj_in.email,
        phone=obj_in.phone,
        address=obj_in.address,
        industry=obj_in.industry
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, *, db_obj: Client, obj_in: ClientUpdate) -> Client:
    update_data = obj_in.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete(db: Session, *, client_id: UUID) -> Client:
    obj = db.query(Client).get(client_id)
    obj.status = "inactive"
    db.add(obj)
    db.commit()
    return obj 