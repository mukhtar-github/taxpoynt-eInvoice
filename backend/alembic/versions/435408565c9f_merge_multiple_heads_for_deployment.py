"""Merge multiple heads for deployment

Revision ID: 435408565c9f
Revises: 8ae8e4368e31, add_signature_settings
Create Date: 2025-06-24 10:34:28.022861

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '435408565c9f'
down_revision = ('8ae8e4368e31', 'add_signature_settings')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
