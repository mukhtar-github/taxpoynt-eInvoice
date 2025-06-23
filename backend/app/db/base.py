# Import all models here that should be included in the database
from app.db.base_class import Base  # noqa

# Import all models to ensure they're registered with SQLAlchemy
from app.models import *  # noqa