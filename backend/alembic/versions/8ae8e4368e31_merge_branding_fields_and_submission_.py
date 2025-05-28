"""merge_branding_fields_and_submission_retries

Revision ID: 8ae8e4368e31
Revises: 012_org_branding, 97d2d22910b1
Create Date: 2025-05-28 12:09:37.822604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ae8e4368e31'
down_revision = ('012_org_branding', '97d2d22910b1')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
