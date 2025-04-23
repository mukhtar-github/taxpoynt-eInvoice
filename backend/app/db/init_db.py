from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.services.user_service import create_user, get_user_by_email
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


def init_db(db: Session) -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create initial admin user if it doesn't exist
    admin_email = "admin@taxpoynt.com"
    user = get_user_by_email(db, email=admin_email)
    if not user:
        user_in = UserCreate(
            email=admin_email,
            password="AdminPassword123",  # Change in production
            full_name="Default Admin",
            is_active=True,
        )
        create_user(db, user_in, role=UserRole.ADMIN) 