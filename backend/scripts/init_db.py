import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.init_db import init_db
from app.db.session import SessionLocal


def main() -> None:
    """
    Initialize the database
    """
    db = SessionLocal()
    init_db(db)
    print("Database initialized")


if __name__ == "__main__":
    main() 