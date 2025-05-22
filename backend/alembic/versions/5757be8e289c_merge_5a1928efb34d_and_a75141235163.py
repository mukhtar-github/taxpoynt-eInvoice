"""merge 5a1928efb34d and a75141235163

Revision ID: 5757be8e289c
Revises: 5a1928efb34d, a75141235163
Create Date: 2025-05-22 14:46:26.129112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5757be8e289c'
down_revision = ('5a1928efb34d', 'a75141235163')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
