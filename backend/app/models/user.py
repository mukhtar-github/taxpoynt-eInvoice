from sqlalchemy import Boolean, Column, Integer, String, Enum
import enum
from app.db.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SI_USER = "si_user"  # System Integrator User


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.SI_USER) 