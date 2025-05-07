"""Merge API credentials and SQLite schemas

Revision ID: a75141235163
Revises: 005_add_api_credentials, 999_dev_sqlite_schema
Create Date: 2025-05-07 11:22:42.346542

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a75141235163'
down_revision = ('005_add_api_credentials', '999_dev_sqlite_schema')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
