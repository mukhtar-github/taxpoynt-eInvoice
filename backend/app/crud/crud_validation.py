from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session # type: ignore

from app.models.validation import ValidationRule, ValidationRecord
from app.schemas.validation import ValidationRule as ValidationRuleSchema


class CRUDValidationRule:
    def create(self, db: Session, *, obj_in: ValidationRuleSchema) -> ValidationRule:
        obj_in_data = obj_in.dict(exclude_unset=True)
        db_obj = ValidationRule(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: UUID) -> Optional[ValidationRule]:
        return db.query(ValidationRule).filter(ValidationRule.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, active_only: bool = True
    ) -> List[ValidationRule]:
        query = db.query(ValidationRule)
        if active_only:
            query = query.filter(ValidationRule.active == True)
        return query.offset(skip).limit(limit).all()

    def update(
        self, db: Session, *, db_obj: ValidationRule, obj_in: Dict[str, Any]
    ) -> ValidationRule:
        for field in obj_in:
            if field in obj_in:
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: UUID) -> ValidationRule:
        obj = db.query(ValidationRule).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def deactivate(self, db: Session, *, id: UUID) -> ValidationRule:
        obj = db.query(ValidationRule).get(id)
        if obj:
            obj.active = False
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj


class CRUDValidationRecord:
    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> ValidationRecord:
        db_obj = ValidationRecord(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: UUID) -> Optional[ValidationRecord]:
        return db.query(ValidationRecord).filter(ValidationRecord.id == id).first()

    def get_by_irn(self, db: Session, irn: str) -> List[ValidationRecord]:
        return db.query(ValidationRecord).filter(ValidationRecord.irn == irn).all()

    def get_by_integration(
        self, db: Session, integration_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ValidationRecord]:
        return (
            db.query(ValidationRecord)
            .filter(ValidationRecord.integration_id == integration_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


validation_rule = CRUDValidationRule()
validation_record = CRUDValidationRecord() 